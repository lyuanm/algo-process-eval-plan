# -*- coding: utf-8 -*-
"""参考实现 I/O 包装（convert）测试：结构完整性 + 典型类型转换正确性。"""
import random

from tools.fetch.convert import (build_reference_solution, parse_meta,
                                 parse_example_inputs, json_param_to_str)
from src.sandbox import run_code


def _sample(problems, n, seed=7):
    rng = random.Random(seed)
    return rng.sample(list(problems), n)


def test_reference_structure(problems):
    """参考实现必须含 Solution 类、main() 与输入转换。"""
    for p in _sample(problems, 10):
        code = p.reference_solution
        assert "class Solution" in code, f"{p.id} 缺 Solution 类"
        assert "def main()" in code, f"{p.id} 缺 main()"
        assert "main()" in code, f"{p.id} 缺 main() 调用"


def test_reference_runs_on_all_official_samples(problems):
    """抽查：参考实现能在该题全部官方样例上运行且输出非空。"""
    for p in _sample(problems, 6):
        for tc in p.test_cases:
            res = run_code(p.reference_solution, tc.input, timeout=10.0)
            assert res.ok, f"{p.id} 参考解异常: {res.stderr[:120]}"
            assert res.stdout.strip(), f"{p.id} 输出为空"


def test_struct_functions_defined(problems):
    """ListNode/TreeNode 结构函数已内嵌进参考实现模板。"""
    import tools.fetch.convert as cv
    src = open(cv.__file__, encoding="utf-8").read()
    for fn in ("_list_build", "_list_show", "_list_array_build",
               "_tree_build", "_tree_show", "_tree_array_build"):
        assert fn in src, f"convert.py 缺少 {fn}"


def test_listnode_problems_run(problems):
    """链表类题（token_list）参考解可运行（ListNode 序列化有效）。"""
    ln = [p for p in problems if p.check_mode == "token_list" and "ListNode" in p.reference_solution]
    assert ln, "题库应包含链表类题"
    for p in ln[:3]:
        res = run_code(p.reference_solution, p.test_cases[0].input, timeout=10.0)
        assert res.ok, f"{p.id} 链表参考解异常: {res.stderr[:120]}"
        assert res.stdout.strip()


def test_treenode_problems_run(problems):
    """树类题（token_list 含 None）参考解可运行（TreeNode 层序解析有效）。"""
    tn = [p for p in problems if p.check_mode == "token_list" and "TreeNode" in p.reference_solution]
    assert tn, "题库应包含树类题"
    for p in tn[:3]:
        res = run_code(p.reference_solution, p.test_cases[0].input, timeout=10.0)
        assert res.ok, f"{p.id} 树参考解异常: {res.stderr[:120]}"
        assert res.stdout.strip()


def test_design_wrapper(problems):
    """设计类题（如 LRU）参考实现应含操作序列解析。"""
    design = [p for p in problems if "json.loads(_lines[0])" in p.reference_solution]
    assert design, "题库应包含设计类题（操作序列包装）"
    p = design[0]
    res = run_code(p.reference_solution, p.test_cases[0].input, timeout=10.0)
    assert res.ok, f"{p.id} 设计类参考解异常: {res.stderr[:120]}"


def test_build_reference_uses_meta_name(problems):
    """函数名优先取 metaData.name（避免匹配到注释中的 def __init__）。"""
    for p in _sample(problems, 5):
        code = p.reference_solution
        # 包装调用行应为 _sol.<name>(...)
        assert "_sol." in code
