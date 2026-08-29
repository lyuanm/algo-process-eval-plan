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
import time
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
        # 无 Key 或显式要求时进入 Mock 模式
        self.use_mock = use_mock or (not _HAS_OPENAI) or (not os.getenv("HY3_API_KEY"))
        self._client = None
        if not self.use_mock and _HAS_OPENAI:
            try:
                self._client = OpenAI(
                    base_url=self.base_url, api_key=self.api_key, timeout=self.timeout
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
        for _ in range(max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore
                    temperature=temp,
                    top_p=tp,
                    extra_body={"chat_template_kwargs": {"reasoning_effort": re}},
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # pragma: no cover
                last_err = e
                time.sleep(1.5)
        return self._mock(messages, note=f"[Hy3 call failed: {last_err}]", tag="[Hy3/local]")

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
        for _ in range(max_retries):
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
                time.sleep(1.5)
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


def load_client_from_env() -> _ChatClient:
    """按 HY3_PROVIDER 选择客户端：local=开源 Hy3，cloud=腾讯云 Hunyuan。"""
    offline = (os.getenv("OFFLINE_MODE", "off").lower() in ("on", "1", "true"))
    provider = (os.getenv("HY3_PROVIDER", "local") or "local").lower()
    if provider == "cloud":
        return HunyuanCloudClient(use_mock=offline)
    return Hy3Client(use_mock=offline)
