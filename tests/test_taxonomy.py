# -*- coding: utf-8 -*-
"""错误分类体系（taxonomy）测试。"""
from src.taxonomy import COARSE_CATEGORY, ERROR_TYPES


def test_all_error_types_have_description():
    for et in ("misread_problem", "concept_error", "calculation_error",
               "condition_omission", "step_skip", "logic_error",
               "complexity_error", "format_error", "hallucination",
               "boundary_error"):
        assert et in ERROR_TYPES, f"缺少错误类型 {et}"
        assert ERROR_TYPES[et], f"{et} 缺少中文描述"


def test_coarse_mapping_consistent():
    for et, coarse in COARSE_CATEGORY.items():
        assert coarse in ("understanding", "execution", "reasoning", "analysis"), (et, coarse)
    # 细类 → 粗类的典型对应
    assert COARSE_CATEGORY["logic_error"] == "execution"
    assert COARSE_CATEGORY["complexity_error"] == "analysis"
    assert COARSE_CATEGORY["concept_error"] == "understanding"


def test_evaluator_outputs_known_types():
    """评估器实际产出的 error_type 都应可描述。"""
    from src.process_evaluator import RuleBasedProcessEvaluator
    from src.problems import Problem, TestCase
    from src.solver import Solution

    p = Problem(id="T", title="t", difficulty="easy", domain="数组/哈希",
                description="求和", input_format="x", output_format="y",
                constraints="", reference_solution="",
                checker_src="", check_mode="int",
                test_cases=[TestCase("1\n2", "3")],
                tags=[], source="LeetCode 1", stress_inputs=[])
    sol = Solution(problem_id="T", reasoning="## 思路\n哈希。\n## 复杂度分析\nO(n)。\n## 边界与处理\n无。",
                   code="import sys\nprint(int(sys.stdin.readline()) - int(sys.stdin.readline()))", raw="")
    r = RuleBasedProcessEvaluator().evaluate(p, sol)
    assert r.error_type in ERROR_TYPES, f"未知 error_type: {r.error_type}"
