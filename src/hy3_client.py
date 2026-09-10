"""大模型客户端（统一接口）。

支持两种接入方式，由 .env 中的 HY3_PROVIDER 切换：

1) local（默认）—— 开源 Hy3，通过 vLLM / SGLang 以 OpenAI 兼容接口提供
   官方仓库：https://github.com/Tencent-Hunyuan/Hy3
   配置：HY3_BASE_URL / HY3_API_KEY / HY3_MODEL

2) cloud —— 腾讯云 Hunyuan 商业 API（hunyuan.tencentcloudapi.com，TC3-HMAC-SHA256 签名）
   配置：HUNYUAN_SECRET_ID / HUNYUAN_SECRET_KEY / HUNYUAN_MODEL（如 hunyuan-pro）

两个客户端都实现相同的 chat(messages, ...) 接口，因此 process_evaluator / solver
无需关心底层用哪种模型，可直接替换。无有效凭证时自动降级为离线 Mock，
保证演示流程不中断。

腾讯云真实调用示例（由 HunyuanCloudClient 封装）：
    from tencentcloud.common import credential
    from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
    cred = credential.Credential(secret_id, secret_key)
    client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou")
    req = models.ChatCompletionsRequest()
    req.Model = "hunyuan-pro"
    req.Messages = [{"Role": "user", "Content": prompt}]
    req.Stream = False
    resp = client.ChatCompletions(req)
    text = resp.Choices[0].Message.Content
"""
from __future__ import annotations

import json
import os
import random
import socket
import time
import urllib.parse
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()  # 加载项目根目录 .env（若存在），使配置生效
except Exception:  # pragma: no cover
    pass

try:
    from openai import OpenAI  # type: ignore

    _HAS_OPENAI = True
except Exception:  # pragma: no cover
    _HAS_OPENAI = False


# 两个客户端共同满足的接口（结构化类型提示，运行时不强制）
class _ChatClient:
    def chat(self, messages, reasoning_effort=None, temperature=None,
             top_p=None, max_retries=2) -> str:
        raise NotImplementedError


_PROXY_ENV_KEYS = (
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
)


def _tcp_alive(url: str, timeout: float = 1.5) -> bool:
    """探测代理地址是否真的在监听。"""
    u = urllib.parse.urlparse(url if "://" in url else f"http://{url}")
    if not u.hostname:
        return False
    port = u.port or (443 if u.scheme == "https" else 80)
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((u.hostname, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


_proxy_checked = False


def ensure_proxy_usable(verbose: bool = False, force: bool = False) -> List[str]:
    """清掉「已配置但不可达」的代理环境变量，返回被清理的变量名。

    实测故障：环境里配了 `HTTPS_PROXY=http://127.0.0.1:7897/`，但该代理进程已经退出
    （端口无监听）。于是所有请求在 TCP 连接阶段就被本机拒绝（WinError 10061），
    日志里表现为一长串 `Connection error.`——看起来像网关故障或额度耗尽，
    实际却是本机代理挂了，排查方向会被完全带偏。

    而目标 `tokenhub.tencentmaas.com` 解析到国内 IP（112.53.10.247），本就不需要代理。
    因此「探活 + 只清理已死的代理」是安全的：一个连不上的代理绝无可用之处，
    而仍然存活的代理保留不动，避免影响确实需要代理的其它端点。

    结果按进程缓存（代理存活状态在一次跑批内不会变化），避免每构造一个客户端就
    重复探活、重复打印同一条告警。
    """
    global _proxy_checked
    if _proxy_checked and not force:
        return []
    _proxy_checked = True

    cleared = []
    if (os.getenv("HY3_NO_PROXY", "off").lower() in ("on", "1", "true")):
        for k in _PROXY_ENV_KEYS:
            if os.getenv(k):
                os.environ.pop(k, None)
                cleared.append(k)
        if verbose and cleared:
            print(f"[网络] 已按 HY3_NO_PROXY 强制绕过代理：{', '.join(cleared)}")
        return cleared

    for k in _PROXY_ENV_KEYS:
        v = os.getenv(k)
        if not v:
            continue
        if not _tcp_alive(v):
            os.environ.pop(k, None)
            cleared.append(k)
            if verbose:
                print(f"[网络] 代理 {v} 不可达（端口无监听），已自动绕过以免连接被拒")
    return cleared


def is_rate_limit_error(err: Exception) -> bool:
    """判断异常是否为网关限流/容量不足（可重试，但需要比常规错误更长的等待）。"""
    text = f"{type(err).__name__} {err}".lower()
    return "ratelimit" in text or "rate_limit" in text or "429" in text


class FatalAPIError(RuntimeError):
    """账号级致命错误：欠费 / 凭证失效 / 服务被隔离。

    这类错误重试、退避、换模型都无法恢复（实测 hy3 与 hy4-preview 返回同一个 402
    `403004`）。若不单独识别，跑批会对着剩余几百道题逐题重试 3 次，既浪费时间又把
    日志淹没在无意义的失败记录里；因此必须立即上抛并终止本轮。
    """


# 账号级错误特征：命中任意一条即视为不可恢复
_FATAL_HINTS = (
    "in arrears", "欠费", "403004", "has been isolated", "已被隔离",
    "insufficient balance", "余额不足", "payment required", "402",
    "invalid api key", "incorrect api key", "invalid_api_key", "authenticationerror",
    "account is not active", "disabled",
)


def is_fatal_api_error(err: Exception) -> bool:
    """判断异常是否为账号级致命错误（不可通过重试/换模型恢复）。"""
    text = f"{type(err).__name__} {err}".lower()
    return any(h in text for h in _FATAL_HINTS)


def fatal_message(err: Exception) -> str:
    """从错误中提取一段简明的中文说明，供日志与终端提示使用。"""
    text = str(err)
    if "403004" in text or "in arrears" in text.lower() or "欠费" in text:
        return ("账号已欠费，服务 ID 被隔离——请充值后在控制台重新启用服务。"
                "（此状态下切换模型无效：所有模型返回同一 402 错误）")
    if "invalid api key" in text.lower() or "incorrect api key" in text.lower():
        return "API Key 无效或已被吊销，请检查 .env 中的 HY3_API_KEY。"
    return f"账号级错误：{text[:200]}"


def is_timeout_error(err: Exception) -> bool:
    """判断异常是否为「请求超时」。

    超时是**确定性**失败：在同样的超时预算下重试只会再烧掉一遍等长的时间。实测日志中
    `Request timed out.` 就是 hard 题批量失败的真实原因（题面长、推理链长，生成时间
    超过 timeout），而非网关限流——因此重试是没有意义的，应当立即上抛以便外层调整
    超时或直接记录失败。
    """
    name = type(err).__name__.lower()
    text = str(err).lower()
    return "timeout" in name or "timeout" in text or "timed out" in text


_UNSUPPORTED_HINTS = (
    "unsupported", "not support", "invalid parameter", "unknown parameter",
    "unrecognized", "unexpected keyword", "chat_template_kwargs", "invalid_request_error",
    "reasoning_effort", "extra fields",
)


def _is_unsupported_param(err: Exception) -> bool:
    """判断异常是否由「请求里带了当前模型不支持的参数」引起。

    换模型时（hy3 → hy4-preview）私有参数可能不再被接受。这里只在同时出现 400 类
    状态码或明确的参数相关措辞时才判定，避免把网络错误误判成参数问题而白跑一次。
    """
    text = f"{type(err).__name__} {err}".lower()
    if "400" not in text and "bad request" not in text:
        # 部分 SDK 把 400 包成 InvalidRequestError，其类名已足够指示性
        if "invalidrequest" not in text:
            return False
    return any(h in text for h in _UNSUPPORTED_HINTS)


def backoff_sleep(attempt: int, base: float = 1.5, cap: float = 20.0) -> float:
    """指数退避 + 抖动，返回实际休眠秒数。

    原先固定 sleep(1.5) 在网关限流场景下往往撞在同一个限流窗口上，重试依然失败；
    叠加 180s 超时后，单个题最坏可占用一个 worker 近 18 分钟（180×2 + 3 次外层重试），
    全量跑批的吞吐会被少数硬题显著拖慢。指数退避 + 抖动可显著提高重试成功率。
    """
    delay = min(cap, base * (2 ** attempt)) * (0.5 + random.random() * 0.5)
    time.sleep(delay)
    return delay


class Hy3Client(_ChatClient):
    """开源 Hy3（OpenAI 兼容）。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: str = "high",
        temperature: float = 0.9,
        top_p: float = 1.0,
        timeout: int = 180,
        use_mock: bool = False,
    ):
        self.base_url = base_url or os.getenv("HY3_BASE_URL", "http://127.0.0.1:8000/v1")
        self.api_key = api_key or os.getenv("HY3_API_KEY", "EMPTY")
        self.model = model or os.getenv("HY3_MODEL", "hy3")
        self.reasoning_effort = reasoning_effort
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout
        # 探测标志：当前模型是否拒绝 reasoning_effort 透传参数（换模型后可能不支持）
        self._no_extra_body = False
        # 构造底层客户端之前先探活代理：环境里配了但已挂掉的代理会让所有请求在连接阶段
        # 被本机拒绝，日志里却只显示 Connection error.，极易被误判为网关故障或额度耗尽。
        # 放在 __init__ 而非工厂函数，是为了覆盖所有构造路径（含直接 new 客户端的场景）。
        ensure_proxy_usable(verbose=True)
        # 无 Key 或显式要求时进入 Mock 模式
        self.use_mock = use_mock or (not _HAS_OPENAI) or (not os.getenv("HY3_API_KEY"))
        self._client = None
        if not self.use_mock and _HAS_OPENAI:
            try:
                self._client = OpenAI(
                    base_url=self.base_url, api_key=self.api_key, timeout=self.timeout,
                    # 关掉 SDK 自带的隐式重试，否则重试会在两个层级相乘：
                    # SDK 2 次 × 本客户端的 max_retries 2 次 = 最坏 6 次请求。
                    # 实测这会把一次 180s 超时放大成近 18 分钟，是全量跑批吞吐崩塌的根因之一。
                    max_retries=0,
                )
            except Exception:  # pragma: no cover
                self._client = None
                self.use_mock = True

    def chat(
        self,
        messages: List[Dict[str, str]],
        reasoning_effort: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_retries: int = 2,
    ) -> str:
        if self.use_mock or self._client is None:
            return self._mock(messages, "[Hy3/local]")

        re = reasoning_effort or self.reasoning_effort
        temp = self.temperature if temperature is None else temperature
        tp = self.top_p if top_p is None else top_p

        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore
                    temperature=temp,
                    top_p=tp,
                    extra_body=self._extra_body(re),
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # pragma: no cover
                last_err = e
                # 账号级错误（欠费/凭证失效/服务被隔离）重试与换模型都无解，立即上抛：
                # 否则会对着剩余几百道题逐题白跑 3 次，日志也会被无意义失败淹没。
                if is_fatal_api_error(e):
                    raise FatalAPIError(fatal_message(e)) from e
                # reasoning_effort 通过 chat_template_kwargs 透传，属于模型侧私有参数：
                # 换模型（如 hy3 -> hy4-preview）后可能不被接受，网关通常回 400。
                # 此时退化为不带该参数重试一次，避免因一个可选参数丢掉整道题。
                if self._extra_body(re) and _is_unsupported_param(e):
                    self._no_extra_body = True
                    try:
                        resp = self._client.chat.completions.create(
                            model=self.model,
                            messages=messages,  # type: ignore
                            temperature=temp,
                            top_p=tp,
                        )
                        return resp.choices[0].message.content or ""
                    except Exception as e2:  # pragma: no cover
                        last_err = e2
                        if is_timeout_error(e2):
                            break
                if is_timeout_error(e):
                    break  # 超时确定性失败，重试只是再烧一遍等长的时间
                if attempt < max_retries - 1:
                    # 限流/容量不足是服务侧拥塞，常规的秒级退避往往仍在同一拥塞窗口内，
                    # 用更长的退避基准明显更容易成功。
                    backoff_sleep(attempt, base=6.0 if is_rate_limit_error(e) else 1.5)
        return self._mock(messages, note=f"[Hy3 call failed: {last_err}]", tag="[Hy3/local]")

    def _extra_body(self, reasoning_effort: str) -> Optional[Dict]:
        """reasoning_effort 透传体；若已探测到当前模型不支持则返回 None。"""
        if getattr(self, "_no_extra_body", False):
            return None
        return {"chat_template_kwargs": {"reasoning_effort": reasoning_effort}}

    def _mock(self, messages: List[Dict[str, str]], note: str = "", tag: str = "") -> str:
        user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                user_msg = m["content"]
                break
        return (
            f"[OFFLINE MOCK {tag} - 未配置有效凭证，未产生真实解法]\n"
            f"{note}\n"
            f"收到用户指令（前 80 字）：{user_msg[:80]}\n"
        )


class HunyuanCloudClient(_ChatClient):
    """腾讯云 Hunyuan 商业 API（hunyuan.tencentcloudapi.com，TC3 签名）。"""

    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        model: Optional[str] = None,
        region: str = "ap-guangzhou",
        temperature: float = 0.9,
        top_p: float = 1.0,
        timeout: int = 180,
        use_mock: bool = False,
    ):
        self.secret_id = secret_id or os.getenv("HUNYUAN_SECRET_ID", "")
        self.secret_key = secret_key or os.getenv("HUNYUAN_SECRET_KEY", "")
        self.model = model or os.getenv("HUNYUAN_MODEL", "hunyuan-pro")
        self.region = region or os.getenv("HUNYUAN_REGION", "ap-guangzhou")
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout
        self.use_mock = use_mock or (not self.secret_id) or (not self.secret_key)
        self._client = None
        self._models = None
        if not self.use_mock:
            try:
                from tencentcloud.common import credential  # type: ignore
                from tencentcloud.common.profile.client_profile import ClientProfile  # type: ignore
                from tencentcloud.common.profile.http_profile import HttpProfile  # type: ignore
                from tencentcloud.hunyuan.v20230901 import hunyuan_client, models  # type: ignore

                cred = credential.Credential(self.secret_id, self.secret_key)
                hp = HttpProfile()
                hp.endpoint = "hunyuan.tencentcloudapi.com"
                hp.reqTimeout = self.timeout
                cp = ClientProfile()
                cp.httpProfile = hp
                self._client = hunyuan_client.HunyuanClient(cred, self.region, cp)
                self._models = models
            except Exception:  # pragma: no cover
                self._client = None
                self._models = None
                self.use_mock = True

    def chat(
        self,
        messages: List[Dict[str, str]],
        reasoning_effort: Optional[str] = None,  # 腾讯云 Hunyuan 暂未使用该字段
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_retries: int = 2,
    ) -> str:
        if self.use_mock or self._client is None or self._models is None:
            return self._mock(messages, "[Hunyuan/cloud]")

        # 转换为腾讯云 Messages 格式（Role / Content 大写）
        tc_messages = [{"Role": m["role"], "Content": m["content"]} for m in messages]
        temp = self.temperature if temperature is None else temperature
        tp = self.top_p if top_p is None else top_p

        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                req = self._models.ChatCompletionsRequest()
                req.Model = self.model
                req.Messages = tc_messages
                req.Stream = False
                req.Temperature = temp
                req.TopP = tp
                resp = self._client.ChatCompletions(req)
                if resp.Choices and resp.Choices[0].Message:
                    return resp.Choices[0].Message.Content or ""
                return ""
            except Exception as e:  # pragma: no cover
                last_err = e
                if is_fatal_api_error(e):
                    raise FatalAPIError(fatal_message(e)) from e
                if is_timeout_error(e):
                    break  # 超时确定性失败，重试只是再烧一遍等长的时间
                if attempt < max_retries - 1:
                    backoff_sleep(attempt)
        return self._mock(messages, note=f"[Hunyuan call failed: {last_err}]", tag="[Hunyuan/cloud]")

    def _mock(self, messages: List[Dict[str, str]], note: str = "", tag: str = "") -> str:
        user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                user_msg = m["content"]
                break
        return (
            f"[OFFLINE MOCK {tag} - 未配置有效凭证，未产生真实解法]\n"
            f"{note}\n"
            f"收到用户指令（前 80 字）：{user_msg[:80]}\n"
        )


def load_client_from_env(model: Optional[str] = None,
                         timeout: Optional[int] = None) -> _ChatClient:
    """按 HY3_PROVIDER 选择客户端：local=开源 Hy3，cloud=腾讯云 Hunyuan。

    model 可显式覆盖默认模型（默认取 HY3_MODEL）。当某个模型的额度耗尽、需要切换备用
    模型跑完剩余题目时，混合来源的结果必须能被区分——调用方应把实际使用的模型名一并
    写进缓存与日志（见 run_full 的 model 字段与 runlog 的 model 字段）。

    timeout 可显式覆盖默认的 180s 请求超时。全量跑批中 hard 题的推理耗时可达
    500~1100s（实测 DH01=343.9s、DH06=538.3s、BH15=1065.8s），而单题只发一次 chat
    请求，因此默认超时偏小时 hard 题会整题失败并退化为 Mock；补跑缺口时应显式调大。
    """
    offline = (os.getenv("OFFLINE_MODE", "off").lower() in ("on", "1", "true"))
    provider = (os.getenv("HY3_PROVIDER", "local") or "local").lower()
    kw: Dict = {}
    if timeout is not None:
        kw["timeout"] = timeout
    if model:
        kw["model"] = model
    if provider == "cloud":
        return HunyuanCloudClient(use_mock=offline, **kw)  # type: ignore[arg-type]
    return Hy3Client(use_mock=offline, **kw)  # type: ignore[arg-type]
