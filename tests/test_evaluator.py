# -*- coding: utf-8 -*-
"""规则评估器单元测试：步骤判定、错误定位、错误归类、「答案对过程错」识别。"""
import json

from src.process_evaluator import RuleBasedProcessEvaluator, _loop_nesting
from src.problems import Problem, TestCase
from src.solver import Solution, parse_solution


def _mk_problem(**kw):
    base = dict(
        id="TEST", title="测试题", difficulty="easy", domain="数组/哈希",
        description="求和", input_format="每行一个参数", output_format="整数",
        constraints="", reference_solution="",
        checker_src="", check_mode="int",
        test_cases=[TestCase("1\n2", "3"), TestCase("3\n4", "7")],
        tags=[], source="LeetCode 1", stress_inputs=[],
    )
    base.update(kw)
    return Problem(**base)


def _mk_solution(code, reasoning):
    sol = Solution(problem_id="TEST", reasoning=reasoning, code=code, raw=reasoning)
    sol.sample_id = "S"
    return sol


CORRECT_CODE = """import sys
a = int(sys.stdin.readline()); b = int(sys.stdin.readline())
print(a + b)
"""

WRONG_CODE = """import sys
a = int(sys.stdin.readline()); b = int(sys.stdin.readline())
print(a - b)
"""


def test_loop_nesting_detection():
    code = "for i in range(n):\n    for j in range(n):\n        x = i * j"
    assert _loop_nesting(code) == 2
    assert _loop_nesting("x = 1") == 0


def test_correct_solution_passes():
    ev = RuleBasedProcessEvaluator()
    p = _mk_problem()
    sol = _mk_solution(CORRECT_CODE, "## 思路\n直接求和。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。")
    r = ev.evaluate(p, sol)
    assert r.final_correct is True
    assert r.process_valid is True
    assert r.error_type is None


def test_wrong_solution_located_to_code_step():
    ev = RuleBasedProcessEvaluator()
    p = _mk_problem()
    sol = _mk_solution(WRONG_CODE, "## 思路\n直接求和。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。")
    r = ev.evaluate(p, sol)
    assert r.final_correct is False
    assert r.process_valid is False
    assert r.error_step == 4  # 代码实现
    assert r.error_type == "logic_error"


def test_complexity_conflict_detected():
    """声称 O(n) 但代码双层循环 → 复杂度步骤不成立（答案对、过程错）。"""
    ev = RuleBasedProcessEvaluator()
    p = _mk_problem(test_cases=[TestCase("2\n3", "6"), TestCase("4\n5", "20")])
    double_loop = """import sys
a = int(sys.stdin.readline()); b = int(sys.stdin.readline())
s = 0
for i in range(a):
    for j in range(b):
        s += 1
print(s)
"""
    sol = _mk_solution(double_loop, "## 思路\n双重循环累加。\n## 复杂度分析\n时间复杂度 O(n)。\n## 边界与处理\n无。")
    r = ev.evaluate(p, sol)
    assert r.final_correct is True
    assert r.process_valid is False
    assert r.error_step == 2  # 复杂度分析
    assert r.error_type == "complexity_error"


def test_hash_claim_but_no_hash_detected():
    ev = RuleBasedProcessEvaluator()
    p = _mk_problem()
    no_hash = CORRECT_CODE  # 未用哈希
    sol = _mk_solution(no_hash, "## 思路\n使用哈希表记录。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。")
    r = ev.evaluate(p, sol)
    assert r.final_correct is True
    assert r.process_valid is False
    assert r.error_type == "concept_error"


def test_stress_flags_coincidence():
    """差分压力测试能捕获「主测试集巧合通过」的坏代码。"""
    from src.verdict import stress_verdict
    p = _mk_problem(
        test_cases=[TestCase("1\n2", "3"), TestCase("3\n4", "7")],
        reference_solution=CORRECT_CODE,
        stress_inputs=["100000\n200000", "5\n8", "123456789\n1"],
    )
    # 只对主测试集的 (1,2) 和 (3,4) 输出正确、其余输出 a-b 的「巧合通过」代码
    coincident = """import sys
a = int(sys.stdin.readline()); b = int(sys.stdin.readline())
if (a, b) == (1, 2): print(3)
elif (a, b) == (3, 4): print(7)
else: print(a - b)
"""
    sv = stress_verdict(p, coincident, timeout=10.0)
    assert sv is not None and sv.final_correct is False, "压力测试未捕获巧合通过代码"
