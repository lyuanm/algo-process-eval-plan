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


def test_hash_mention_as_alternative_not_flagged():
    """回归：把哈希表当「备选/对比方案」提及，不应误判为「方法名实不符」。

    全量跑批（513 题）中曾因此规则误报 7/12 题，把过程正确率从 75% 压到 25%。
    """
    ev = RuleBasedProcessEvaluator()
    p = _mk_problem()
    reasonings = [
        "## 思路\n本题可用哈希表，但排序后双指针更简单，故不使用哈希表。\n## 复杂度分析\nO(n log n)。\n## 边界与处理\n无。",
        "## 思路\n直接遍历求和即可，无需哈希表。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。",
        "## 思路\n若使用字典统计则需 O(n) 额外空间，本题用计数数组即可。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。",
        "## 思路\n维护一个变量累加。相比哈希表方案，空间更优。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。",
    ]
    for reasoning in reasonings:
        r = ev.evaluate(p, _mk_solution(CORRECT_CODE, reasoning))
        assert r.final_correct is True
        assert r.process_valid is True, f"误报 concept_error：{reasoning}"


def test_hash_claim_consistent_when_code_uses_hash():
    """明确声称用哈希且代码确实用了 -> 判定一致（不误报）。"""
    ev = RuleBasedProcessEvaluator()
    p = _mk_problem()
    code = """import sys
from collections import Counter
a = int(sys.stdin.readline()); b = int(sys.stdin.readline())
freq = Counter([a, b])
print(sum(k * v for k, v in freq.items()))
"""
    r = ev.evaluate(p, _mk_solution(
        code, "## 思路\n使用哈希表统计频次后求和。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。"))
    assert r.final_correct is True
    assert r.process_valid is True


def test_step_verdicts_consistent_with_overall_verdict():
    """回归：总体判定「过程不成立」时，error_step 指向的步骤不得仍显示通过。

    步骤判定原先在失败归因之前生成，只有复杂度冲突会即时回写，于是答案错误
    （归因 step 4）的题目会出现「四步全绿却判定过程不成立」的自相矛盾结果，
    看板上尤其显眼，直接损害结果可信度。
    """
    ev = RuleBasedProcessEvaluator()
    p = _mk_problem()
    reasoning = "## 思路\n直接求和。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。"

    # 答案错误 -> 归因到 step 4（代码实现），该步必须标记为不通过
    r = ev.evaluate(p, _mk_solution(WRONG_CODE, reasoning))
    assert r.process_valid is False and r.error_step == 4
    sv4 = next(s for s in r.step_verdicts if s.step == 4)
    assert sv4.ok is False, "归因到 step 4，但该步仍显示通过"
    assert sv4.reason != "无明显问题"

    # 方法名实不符 -> 归因到 step 1（思路/建模），该步同样必须标记为不通过
    r_hash = ev.evaluate(p, _mk_solution(
        CORRECT_CODE, "## 思路\n使用哈希表记录。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。"))
    assert r_hash.process_valid is False and r_hash.error_step == 1
    sv1 = next(s for s in r_hash.step_verdicts if s.step == 1)
    assert sv1.ok is False, "归因到 step 1，但该步仍显示通过"

    # 不变量：过程不成立 <=> 存在失败步骤，且 error_step 必在其中
    for res in (r, r_hash, ev.evaluate(p, _mk_solution(CORRECT_CODE, reasoning))):
        bad = {s.step for s in res.step_verdicts if not s.ok}
        if res.process_valid:
            assert not bad, f"过程判定成立却有失败步骤：{bad}"
        else:
            assert bad, "过程判定不成立却没有任何步骤被标记为失败"
            assert res.error_step in bad, "error_step 未落在失败步骤集合内"
