# -*- coding: utf-8 -*-
"""端到端评测 smoke 测试：samples+rule 全流程可运行并产出结果文件。"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "eval"))
PY = sys.executable

import run_eval  # noqa: E402


def test_output_paths_isolate_source_and_backend():
    """回归：结果文件路径必须同时区分 source 与 backend。

    曾经 live 与 samples 共用 `evaluation_results.jsonl`，一次 live 冒烟测试就覆盖掉
    含人工真值的 15 个诊断样本结果，使 verify_evaluator.py 静默退化为「0 样本、指标 None」，
    README 中「定位准确率 100% / 误报率 0%」的结论随之失效且无人察觉。
    """
    samples_rule, _ = run_eval.output_paths("rule", "samples")
    live_rule, _ = run_eval.output_paths("rule", "live")
    samples_llm, _ = run_eval.output_paths("llm", "samples")
    live_llm, _ = run_eval.output_paths("llm", "live")

    paths = [samples_rule, live_rule, samples_llm, live_llm]
    assert len(set(paths)) == 4, f"结果路径发生碰撞：{paths}"

    # samples+rule 是 verify_evaluator.py / report.py / gen_demo.py 依赖的约定路径
    assert samples_rule.endswith("evaluation_results.jsonl")
    assert live_rule.endswith("evaluation_results_live.jsonl")
    assert samples_llm.endswith("evaluation_results_llm.jsonl")
    assert live_llm.endswith("evaluation_results_live_llm.jsonl")


def test_run_eval_rule_smoke(tmp_path):
    out_jsonl = os.path.join(ROOT, "eval", "results", "evaluation_results.jsonl")
    proc = subprocess.run(
        [PY, os.path.join(ROOT, "eval", "run_eval.py"),
         "--source", "samples", "--backend", "rule"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, proc.stderr[-800:]
    assert os.path.exists(out_jsonl)
    with open(out_jsonl, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) >= 10, f"评估结果过少: {len(lines)}"
    rec = json.loads(lines[0])
    for key in ("sample_id", "problem_id", "final_correct", "process_valid",
                "error_step", "error_type", "backend"):
        assert key in rec, f"结果缺少字段 {key}"


def test_run_eval_live_limit_smoke(tmp_path):
    """live 少量题接口：--limit 2 --ids 指定题均可运行（rule 后端）。

    本用例校验的是「live 选题管道」（--limit 随机取题 / --ids 指定题）是否接通，
    与真实模型能力无关，因此强制 OFFLINE_MODE 走 Mock 求解：否则它会串行调用
    Hy3 实时求解，在机器同时跑全量跑批（16 路并发）时必然撞上 300s 超时，
    变成与代码无关的偶发失败。真实 API 链路由全量跑批与人工验证覆盖。
    """
    env = dict(os.environ, OFFLINE_MODE="on")
    for extra in (["--limit", "2", "--seed", "7"], ["--ids", "AE01", "ME02"]):
        proc = subprocess.run(
            [PY, os.path.join(ROOT, "eval", "run_eval.py"),
             "--source", "live", "--backend", "rule"] + extra,
            cwd=ROOT, capture_output=True, text=True, timeout=300, env=env,
        )
        assert proc.returncode == 0, proc.stderr[-800:]
        assert "[live]" in proc.stdout
