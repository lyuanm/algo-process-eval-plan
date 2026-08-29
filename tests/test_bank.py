# -*- coding: utf-8 -*-
"""题库数据层测试：数量、难度均衡、每题完整性。"""
from collections import Counter


def test_bank_size(problems):
    assert len(problems) >= 500, f"题库应 >=500 题，当前 {len(problems)}"


def test_bank_difficulty_balance(problems):
    c = Counter(p.difficulty for p in problems)
    assert all(c.get(d, 0) >= 150 for d in ("easy", "medium", "hard")), dict(c)


def test_every_problem_complete(problems):
    for p in problems:
        assert p.id and p.title and p.source, p.id
        assert p.description and p.input_format and p.output_format, p.id
        assert p.reference_solution, p.id
        assert p.check_mode, p.id
        assert p.test_cases, f"{p.id} 无测试用例"


def test_every_problem_source_traceable(problems):
    for p in problems:
        assert p.source.startswith("LeetCode"), f"{p.id} source 应为 LeetCode 题号"


def test_every_problem_has_stress_inputs(problems):
    # deep-ERV 依赖压力输入；设计类/特殊约束题允许缺失
    no_stress = [p.id for p in problems if not p.stress_inputs]
    assert len(no_stress) <= 170, f"压力输入缺失过多: {len(no_stress)}"


def test_unique_ids(problems):
    ids = [p.id for p in problems]
    assert len(ids) == len(set(ids)), "存在重复题 ID"
