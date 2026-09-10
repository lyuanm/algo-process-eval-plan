# -*- coding: utf-8 -*-
"""全量跑批脚本（eval/run_full.py）测试：缓存有效性判定 + 汇总指标计算。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "eval"))

import run_full  # noqa: E402


def test_is_valid_solution_filters_mock_and_empty():
    """Mock 降级文本与空响应都不得被当成有效解答，否则会污染全量指标。"""
    assert run_full.is_valid_solution("## 思路\n使用双指针。\n```python\nprint(1)\n```")
    assert not run_full.is_valid_solution("")
    assert not run_full.is_valid_solution("   \n  ")
    assert not run_full.is_valid_solution(
        "[OFFLINE MOCK [Hy3/local] - 未配置有效凭证，未产生真实解法]\n[Hy3 call failed: timeout]"
    )


def _rec(pid, final, proc, etype=None, estep=None, diff="easy", domain="数组/哈希", verdict="AC", sec=1.0):
    return {
        "problem_id": pid, "final_correct": final, "process_valid": proc,
        "error_type": etype, "error_step": estep, "difficulty": diff, "domain": domain,
        "first_failure_verdict": verdict, "eval_sec": sec, "title": pid, "note": "",
    }


def test_summarize_computes_core_metrics(tmp_path):
    """核心指标：答案率、过程率、「答案对但过程错」、分层与归因分布。"""
    recs = [
        _rec("A", True, True, diff="easy", sec=1.0),
        # 答案对但过程不成立 —— 本系统的核心增量
        _rec("B", True, False, etype="complexity_error", estep=2, diff="easy", sec=2.0),
        _rec("C", False, False, etype="logic_error", estep=4, diff="hard", domain="图", verdict="WA", sec=3.0),
    ]
    out = tmp_path / "summary.json"
    s = run_full.summarize(recs, {"A": 1, "B": 1, "C": 1, "D": 1}, "rule", str(out))

    assert s["total"] == 3
    assert s["bank_total"] == 4
    assert s["coverage"] == 0.75
    assert s["final_correct"] == 2 and s["final_acc"] == round(2 / 3, 4)
    assert s["process_valid"] == 1 and s["process_rate"] == round(1 / 3, 4)
    assert s["lucky_pass"] == 1, "应识别出 1 题「答案对但过程不成立」"
    assert s["wrong_count"] == 1
    assert s["by_difficulty"]["easy"]["n"] == 2
    assert s["by_difficulty"]["hard"]["lucky_pass"] == 0
    assert s["by_domain"]["图"]["final_acc"] == 0.0
    assert s["error_step_dist"] == {"2": 1, "4": 1}
    assert s["error_type_dist"]["complexity_error"] == 1
    assert s["eval_sec_median"] == 2.0
    assert os.path.exists(out)


def test_summarize_handles_empty():
    assert run_full.summarize([], {}, "rule", "unused.json") == {}


def test_read_jsonl_tolerates_truncated_line(tmp_path):
    """全量跑批是数小时的长任务，中途被终止时最后一行可能是半截残行；
    残行必须被跳过而不是让整个缓存不可读，否则断点续跑直接失效。"""
    p = tmp_path / "cache.jsonl"
    p.write_text(
        '{"problem_id":"A","raw":"ok"}\n'
        '{"problem_id":"B","raw":"ok"}\n'
        '{"problem_id":"C","raw":"半截',  # 中断截断
        encoding="utf-8",
    )
    recs = run_full.read_jsonl(str(p))
    assert [r["problem_id"] for r in recs] == ["A", "B"]

    assert run_full.read_jsonl(str(tmp_path / "missing.jsonl")) == []


def test_read_jsonl_skips_blank_lines(tmp_path):
    p = tmp_path / "cache.jsonl"
    p.write_text('{"problem_id":"A"}\n\n   \n{"problem_id":"B"}\n', encoding="utf-8")
    assert [r["problem_id"] for r in run_full.read_jsonl(str(p))] == ["A", "B"]


def test_mock_reason_surfaces_real_cause():
    """Mock 降级文本里嵌着真实失败原因，必须能被提取出来。

    原先失败日志只打印笼统的「API 调用失败」，导致 hard 题批量失败时无法区分
    「网关限流」（应降并发）与「单请求超时」（应加超时）——两者的处置方式相反，
    日志丢失原因就等于丧失了调参依据。
    """
    raw = (
        "[OFFLINE MOCK [Hy3/local] - 未配置有效凭证，未产生真实解法]\n"
        "[Hy3 call failed: Request timed out.]\n"
        "收到用户指令（前 80 字）：请给出解题过程"
    )
    assert run_full.mock_reason(raw) == "Request timed out."

    # 无失败原因 / 空文本时给出占位而不是抛异常
    assert run_full.mock_reason("[OFFLINE MOCK [Hy3/local] - x]") == "原因未知"
    assert run_full.mock_reason("") == "原因未知"

    # 原因过长时截断，避免污染日志行
    long_reason = "x" * 500
    assert len(run_full.mock_reason(f"[OFFLINE MOCK y]\n[Hy3 call failed: {long_reason}]")) == 160


def test_backoff_sleep_exponential_with_jitter_and_cap(monkeypatch):
    """重试退避必须指数增长且带抖动。

    原先固定 sleep(1.5) 在网关限流时会反复撞在同一限流窗口上，重试依旧失败；
    配合 180s 超时，单个题最坏可占用一个 worker 近 18 分钟，拖慢全量跑批吞吐。
    """
    from src.hy3_client import backoff_sleep

    slept = []
    monkeypatch.setattr("src.hy3_client.time.sleep", slept.append)

    delays = [backoff_sleep(i, base=1.5, cap=20.0) for i in range(5)]
    assert slept == delays, "返回值应与实际休眠秒数一致"

    for i, d in enumerate(delays):
        nominal = min(20.0, 1.5 * (2 ** i))
        assert nominal * 0.5 <= d <= nominal, f"第 {i} 次退避 {d} 超出抖动区间"

    assert delays[0] < delays[2], "退避应随尝试次数递增"
    assert all(d <= 20.0 for d in delays), "退避不得超过上限"
