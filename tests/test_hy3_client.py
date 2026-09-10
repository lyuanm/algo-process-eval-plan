# -*- coding: utf-8 -*-
"""Hy3 客户端重试语义测试。

背景（真实故障）：全量跑批中 hard 题成批失败，日志只显示笼统的「API 调用失败」。
补上真实原因日志后确认是 `Request timed out.`——题面长、推理链长的题，生成时间超过
timeout。这里锁定两条修复：
  1. 超时必须能与非超时异常区分（否则无法决定「重试」还是「上调超时」）；
  2. 超时不得重试——同一超时预算下重试只是再烧一遍等长的时间。
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import hy3_client  # noqa: E402


class _APITimeoutError(Exception):
    pass


class _APIConnectionError(Exception):
    pass


def test_is_timeout_error_detects_by_class_name_and_message():
    assert hy3_client.is_timeout_error(_APITimeoutError("x"))
    assert hy3_client.is_timeout_error(Exception("Request timed out."))
    assert hy3_client.is_timeout_error(Exception("ReadTimeout: ..."))


def test_is_timeout_error_rejects_transient_errors():
    """连接类异常应当重试（网络抖动可恢复），不能与超时混为一谈。"""
    assert not hy3_client.is_timeout_error(_APIConnectionError("connection reset"))
    assert not hy3_client.is_timeout_error(Exception("429 Too Many Requests"))
    assert not hy3_client.is_timeout_error(Exception("500 Internal Server Error"))


class _FakeCompletions:
    def __init__(self, calls, exc):
        self._calls = calls
        self._exc = exc

    def create(self, **kw):
        self._calls.append(kw)
        raise self._exc


class _FakeChat:
    def __init__(self, completions):
        self.completions = completions


class _FakeOpenAI:
    """桩：记录调用次数并始终抛指定异常。"""

    def __init__(self, calls, exc):
        self.chat = _FakeChat(_FakeCompletions(calls, exc))


def _client(monkeypatch, exc):
    monkeypatch.setenv("HY3_API_KEY", "k")
    monkeypatch.setattr(hy3_client, "_HAS_OPENAI", True)
    c = hy3_client.Hy3Client(timeout=180, use_mock=False)
    calls = []
    c._client = _FakeOpenAI(calls, exc)
    return c, calls


def test_chat_does_not_retry_on_timeout(monkeypatch):
    """超时应当只发一次请求就返回 Mock——原先会发满 max_retries 次。"""
    import time as _t

    monkeypatch.setattr(_t, "sleep", lambda *_: None)
    monkeypatch.setattr("src.hy3_client.backoff_sleep", lambda *a, **k: 0.0)
    c, calls = _client(monkeypatch, _APITimeoutError("Request timed out."))

    out = c.chat([{"role": "user", "content": "q"}], max_retries=3)
    assert len(calls) == 1, "超时不应重试"
    assert "[OFFLINE MOCK" in out, "失败时必须返回可识别的 Mock 文本"
    assert "Request timed out." in out, "失败原因必须写进 Mock 文本以供外层诊断"


def test_chat_retries_transient_errors(monkeypatch):
    """非超时异常仍应重试，避免一次网络抖动就丢掉一道题。"""
    monkeypatch.setattr("src.hy3_client.backoff_sleep", lambda *a, **k: 0.0)
    c, calls = _client(monkeypatch, _APIConnectionError("connection reset"))

    c.chat([{"role": "user", "content": "q"}], max_retries=3)
    assert len(calls) == 3, "连接类异常应重试到上限"


def test_sdk_level_retries_disabled():
    """必须关掉 OpenAI SDK 自带的隐式重试。

    否则重试在两个层级相乘（SDK 2 次 × 客户端 2 次 = 6 次请求），实测会把一次 180s
    超时放大成近 18 分钟，是吞吐崩塌的直接原因。
    """
    src = open(os.path.join(ROOT, "src", "hy3_client.py"), encoding="utf-8").read()
    assert "max_retries=0" in src


# --------------------------------------------------------------- 代理探活
import socket  # noqa: E402


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_tcp_alive_false_for_dead_port():
    """指向一个没人监听的端口，探活必须返回 False（而不是抛异常）。"""
    assert hy3_client._tcp_alive(f"http://127.0.0.1:{_free_port()}/", timeout=0.5) is False


def test_ensure_proxy_usable_clears_dead_proxy(monkeypatch):
    """已配置但端口无监听的代理必须被清除。

    真实故障：HTTPS_PROXY 指向 127.0.0.1:7897，但代理进程已退出，于是所有请求在
    TCP 连接阶段被本机拒绝（WinError 10061），日志只显示 `Connection error.`，
    被误判成网关故障甚至额度耗尽，排查方向被完全带偏。
    """
    monkeypatch.setattr(hy3_client, "_proxy_checked", False)
    monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{_free_port()}/")
    monkeypatch.delenv("HY3_NO_PROXY", raising=False)
    cleared = hy3_client.ensure_proxy_usable(force=True)
    assert "HTTPS_PROXY" in cleared
    assert os.environ.get("HTTPS_PROXY") is None


def test_ensure_proxy_usable_keeps_alive_proxy(monkeypatch):
    """仍然存活的代理不能被误删——其它端点可能确实需要它。

    注意 backlog 要给足：listen(1) 时第一次探活就会占满队列，
    第二次探活会被拒，从而误判成「代理已死」。
    """
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(16)
    try:
        monkeypatch.setattr(hy3_client, "_proxy_checked", False)
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{srv.getsockname()[1]}/")
        monkeypatch.delenv("HY3_NO_PROXY", raising=False)
        cleared = hy3_client.ensure_proxy_usable(force=True)
        assert "HTTPS_PROXY" not in cleared
        assert os.environ.get("HTTPS_PROXY") is not None
    finally:
        srv.close()


def test_ensure_proxy_usable_force_bypass(monkeypatch):
    """HY3_NO_PROXY=on 时应无条件清除代理，无需探活。"""
    monkeypatch.setattr(hy3_client, "_proxy_checked", False)
    monkeypatch.setenv("HTTPS_PROXY", "http://10.0.0.1:9999/")
    monkeypatch.setenv("HY3_NO_PROXY", "on")
    cleared = hy3_client.ensure_proxy_usable(force=True)
    assert "HTTPS_PROXY" in cleared
    assert os.environ.get("HTTPS_PROXY") is None


def test_ensure_proxy_usable_caches_result(monkeypatch):
    """结果按进程缓存：否则每构造一个客户端就重复探活并重复打印同一条告警。"""
    monkeypatch.setattr(hy3_client, "_proxy_checked", False)
    monkeypatch.setenv("HTTPS_PROXY", "http://10.0.0.1:9999/")
    monkeypatch.delenv("HY3_NO_PROXY", raising=False)
    first = hy3_client.ensure_proxy_usable()
    assert "HTTPS_PROXY" in first
    monkeypatch.setenv("HTTPS_PROXY", "http://10.0.0.1:9999/")
    assert hy3_client.ensure_proxy_usable() == [], "第二次调用应直接复用缓存结果"


# --------------------------------------------------------------- 错误分类
def test_is_rate_limit_error():
    """限流要能被单独识别，才能用更长的退避基准重试。"""
    assert hy3_client.is_rate_limit_error(
        Exception("Error code: 429 - {'type': 'rate_limit_error', 'code': '429006'}")
    )
    assert not hy3_client.is_rate_limit_error(Exception("Error code: 402 - arrears"))
    assert not hy3_client.is_rate_limit_error(_APIConnectionError("connection reset"))


def test_is_fatal_api_error_detects_arrears_but_not_transient():
    """账号欠费/凭证失效属于不可恢复错误；普通网络错误与限流不能被误判。"""
    arrears = Exception(
        "Error code: 402 - {'error': {'code': '403004', 'message': "
        "'The account associated with the API Key is in arrears and the accessed "
        "service ID has been isolated.'}}"
    )
    assert hy3_client.is_fatal_api_error(arrears)
    assert "欠费" in hy3_client.fatal_message(arrears)

    assert not hy3_client.is_fatal_api_error(_APIConnectionError("Connection error."))
    assert not hy3_client.is_fatal_api_error(Exception("Request timed out."))
    assert not hy3_client.is_fatal_api_error(Exception("Error code: 429 - rate_limit_error"))
