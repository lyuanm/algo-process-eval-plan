# -*- coding: utf-8 -*-
"""参考解与官方样例自洽（抽样，全量见 tools/verify_all.py）+ 压力 oracle 一致性。"""
import random

from src.sandbox import run_code
from src.problems import TestCase, verify_problem_testcases


def _sample(problems, n, seed=42):
    rng = random.Random(seed)
    return rng.sample(list(problems), n)


def test_sample_reference_solutions(problems):
    """抽查 8 道题的参考解在官方样例上全部通过。"""
    for p in _sample(problems, 8):
        r = verify_problem_testcases(p, timeout=8.0)
        assert r["all_passed"], f"{p.id} {p.title}: {r['passed']}/{r['total']}"


def test_stress_oracle_consistent(problems):
    """压力输入上参考解自身可运行且输出非空（oracle 有效）。"""
    checked = 0
    for p in _sample(problems, 8):
        for inp in p.stress_inputs[:1]:
            res = run_code(p.reference_solution, inp, timeout=10.0)
            assert res.ok, f"{p.id} 参考解在压力输入上失败: {res.stderr[:100]}"
            assert res.stdout.strip(), f"{p.id} 参考解压力输出为空"
            checked += 1
    assert checked > 0, "压力输入为空，deep-ERV 未生效"


def test_check_modes_supported(problems):
    """check_mode 均在支持集合内。"""
    from src.problems import _CHECKERS
    for p in problems:
        assert p.check_mode in _CHECKERS, f"{p.id} 未知 check_mode: {p.check_mode}"
