"""pbank 公共工具：mk() 构造题面字典 + 共享 I/O 前缀 PREAMBLE。

每个 domain 模块 import 本文件，用 mk(...) 生成题目并追加到本模块 PROBLEMS 列表，
最后由 tools/gen_problems.py 聚合所有模块的 PROBLEMS，写 data/problems.json。

真实性保证：
  - source 标注真实 LeetCode 题号（如 "LeetCode 1"），title 与官方一致；
  - 最终 tools/validate_real.py 会用 data/leetcode_meta.json 交叉校验 title 存在 / 非付费 / 难度一致。
正确性保证：
  - reference_solution 为完整可运行脚本（stdin 读 / stdout 写）；
  - tools 会跑全部 test_cases 用参考解自验（见 verify_all.py），不通过则不下发。
"""
from __future__ import annotations

# 共享 I/O 前缀：大部分题目可直接用 sp()/ints()/lines() 解析。
# 需要保留（多）空行结构的题目（如图、多测例）请自行读取 stdin 原文。
PREAMBLE = (
    "import sys\n"
    "def sp():\n"
    "    return sys.stdin.read().split()\n"
    "def ints():\n"
    "    return list(map(int, sys.stdin.read().split()))\n"
    "def lines():\n"
    "    return [x for x in sys.stdin.read().split('\\n') if x != '']\n"
)


def mk(pid, title, source, diff, domain, desc, ifmt, ofmt, cons,
       ref, check, tests, tags, stress=None):
    """构造单题字典。

    ref: 完整可运行脚本（通常 PREAMBLE + 解题核心）。
    tests: [(input_str, expected_str), ...]
    stress: 可选的差分压力输入列表（str）。
    """
    return {
        "id": pid,
        "title": title,
        "source": source,
        "difficulty": diff,
        "domain": domain,
        "description": desc,
        "input_format": ifmt,
        "output_format": ofmt,
        "constraints": cons,
        "reference_solution": ref,
        "checker_src": "",
        "check_mode": check,
        "test_cases": [{"input": i, "expected": e} for i, e in tests],
        "tags": list(tags),
        "stress_inputs": list(stress or []),
    }
