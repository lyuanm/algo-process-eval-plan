# -*- coding: utf-8 -*-
"""评测样本自洽性：样本推理代码的运行结果与 ground_truth 一致。"""
import json
import os
import re

from src.problems import load_problems
from src.sandbox import run_code

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_samples_self_consistent(samples):
    problems = {p.id: p for p in load_problems(os.path.join(ROOT, "data", "problems.json"))}
    checked = 0
    for s in samples:
        p = problems.get(s["problem_id"])
        assert p is not None, f"样本引用的题不存在: {s['problem_id']}"
        m = re.search(r"```python\n(.*?)```", s["reasoning"], re.S)
        assert m, f"{s['sample_id']} 缺少代码块"
        code = m.group(1)
        okc = 0
        for tc in p.test_cases:
            res = run_code(code, tc.input, timeout=10.0)
            if res.ok and p.check_answer(res.stdout, str(tc.expected)):
                okc += 1
        assert (okc == len(p.test_cases)) == s["ground_truth"]["final_correct"], \
            f"{s['sample_id']} 代码结果与真值不符"
        checked += 1
    assert checked >= 10


def test_samples_ground_truth_schema(samples):
    for s in samples:
        gt = s["ground_truth"]
        assert "final_correct" in gt and "process_valid" in gt
        if gt["process_valid"] is False:
            assert gt["error_type"], f"{s['sample_id']} 过程无效但缺错误类型"
