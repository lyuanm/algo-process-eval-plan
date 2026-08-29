# -*- coding: utf-8 -*-
"""端到端评测 smoke 测试：samples+rule 全流程可运行并产出结果文件。"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


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
    """live 少量题接口：--limit 2 --ids 指定题均可运行（rule 后端 + mock 求解）。"""
    for extra in (["--limit", "2", "--seed", "7"], ["--ids", "AE01", "ME02"]):
        proc = subprocess.run(
            [PY, os.path.join(ROOT, "eval", "run_eval.py"),
             "--source", "live", "--backend", "rule"] + extra,
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        assert proc.returncode == 0, proc.stderr[-800:]
        assert "[live]" in proc.stdout
