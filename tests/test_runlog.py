# -*- coding: utf-8 -*-
"""日志留存模块（src/runlog.py）测试。

关注点：日志必须**完整且抗中断**——它是事后复核「Hy3 是否真在只看题面的条件下作答」
以及「判定依据是否站得住」的唯一凭据，缺字段或丢记录都会让复核无法进行。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import runlog  # noqa: E402

STEP_NAMES_NO = None


class _P:
    """最小题目桩：只需日志用到的字段。"""

    def __init__(self, pid="AE01"):
        self.id = pid
        self.title = "测试题"
        self.difficulty = "easy"
        self.domain = "数组/哈希"
        self.description = "题面"
        self.input_format = "整数数组"
        self.output_format = "整数"
        self.constraints = "1 <= n <= 100"
        self.test_cases = [object(), object()]


def test_append_and_read_jsonl_roundtrip(tmp_path, monkeypatch):
    p = str(tmp_path / "t.jsonl")
    runlog.append_jsonl(p, {"a": 1})
    runlog.append_jsonl(p, {"a": 2})
    assert runlog.read_jsonl(p) == [{"a": 1}, {"a": 2}]


def test_read_jsonl_tolerates_truncated_line(tmp_path):
    """长任务被中断时最后一行可能是半截残行，必须跳过而不是整份日志不可读。"""
    p = tmp_path / "t.jsonl"
    p.write_text('{"a":1}\n{"a":2}\n{"a":半截', encoding="utf-8")
    assert runlog.read_jsonl(str(p)) == [{"a": 1}, {"a": 2}]
    assert runlog.read_jsonl(str(tmp_path / "none.jsonl")) == []


def test_log_solve_keeps_prompt_attempts_and_failure_reason(tmp_path, monkeypatch):
    """求解日志必须同时保留：完整 prompt、每次尝试的状态与失败原因、终态原始回答。"""
    monkeypatch.setattr(runlog, "SOLVE_TRACE", str(tmp_path / "solve.jsonl"))

    attempts = [
        {"n": 1, "status": "mock_degraded", "reason": "Request timed out.",
         "elapsed": 180.2, "response_chars": 0, "response_head": ""},
        {"n": 2, "status": "ok", "reason": "", "elapsed": 95.9,
         "response_chars": 1887, "response_head": "## 思路"},
    ]
    runlog.log_solve(_P(), "完整提示词文本", attempts, "ok", "## 思路\n...")

    rec = runlog.read_jsonl(str(tmp_path / "solve.jsonl"))[0]
    assert rec["problem_id"] == "AE01"
    assert rec["prompt"] == "完整提示词文本" and rec["prompt_chars"] == len("完整提示词文本")
    assert rec["final_status"] == "ok" and rec["attempt_count"] == 2
    assert [a["status"] for a in rec["attempts"]] == ["mock_degraded", "ok"]
    # 失败原因必须留存，否则无法判断该调并发（限流）还是调超时
    assert rec["attempts"][0]["reason"] == "Request timed out."
    assert rec["raw_response"].startswith("## 思路")
    assert rec["backfilled"] is False


def test_log_solve_marks_backfilled(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "SOLVE_TRACE", str(tmp_path / "solve.jsonl"))
    runlog.log_solve(_P(), "p", [], "ok", "raw", backfilled=True)
    assert runlog.read_jsonl(str(tmp_path / "solve.jsonl"))[0]["backfilled"] is True


def test_log_eval_keeps_verdict_basis_and_evaluated_output(tmp_path, monkeypatch):
    """评估日志必须保留判定依据（逐用例 verdict / 四步骤 / 归因）与被评估的原始回答。"""
    monkeypatch.setattr(runlog, "EVAL_TRACE", str(tmp_path / "eval.jsonl"))
    rec = {
        "final_correct": False, "passed_cases": 1, "total_cases": 2,
        "verdict_summary": "AC:1 WA:1", "first_failure_verdict": "WA",
        "process_valid": False, "error_step": 4, "error_type": "logic_error",
        "error_type_name": "逻辑错误", "note": "最终答案错误", "backend": "rule",
        "confidence": None, "eval_sec": 0.7,
        "case_verdicts": [{"index": 0, "verdict": "AC", "expected": "1", "actual": "1"},
                          {"index": 1, "verdict": "WA", "expected": "2", "actual": "3"}],
        "stress_summary": "AC:1", "stress_case_verdicts": [],
        "step_verdicts": [{"step": 4, "name": "代码实现", "ok": False, "reason": "逻辑错误——最终答案错误"}],
    }
    runlog.log_eval(_P(), rec, "被评估的原始回答")

    got = runlog.read_jsonl(str(tmp_path / "eval.jsonl"))[0]
    assert got["verdict"]["error_step"] == 4
    assert got["case_verdicts"][1]["verdict"] == "WA"
    assert got["raw_solution"] == "被评估的原始回答"
    # 题目上下文须自包含，单看一条日志即可复核判定是否合理
    assert got["problem_context"]["constraints"] == "1 <= n <= 100"
    assert got["problem_context"]["test_case_count"] == 2


def test_status_label_covers_all_emitted_statuses():
    """日志渲染会按 STATUS_LABEL 翻译状态；漏一个就会在看板/日志里显示成 None。"""
    for s in ("ok", "mock_degraded", "empty", "exception"):
        assert s in runlog.STATUS_LABEL, f"缺少状态 {s} 的中文标签"


def test_log_files_are_separate_from_resume_caches():
    """日志与断点续跑缓存必须是不同文件：缓存只存成功结果，日志连失败一起存。"""
    assert os.path.basename(runlog.SOLVE_TRACE) == "solve_trace.jsonl"
    assert os.path.basename(runlog.EVAL_TRACE) == "eval_trace.jsonl"
    assert "results" not in runlog.SOLVE_TRACE.replace("\\", "/").split("eval/")[-1]
