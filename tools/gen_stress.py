# -*- coding: utf-8 -*-
"""为题库生成差分压力输入（stress_inputs），让 deep-ERV 真正生效。

方法：从每题官方样例的输入结构推断参数形状并放大（数组长度/字符串长度/数值范围），
生成大尺寸压力输入；用该题官方参考解运行验证（不超时、输出非空）后才挂载。
stress_verdict 运行时以参考解为 oracle 逐用例差分比较，无需预存期望值。

运行：python tools/gen_stress.py [--max-per-problem N]
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sandbox import run_code  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBLEMS_PATH = os.path.join(ROOT, "data", "problems.json")

# 压力规模：对任何常见复杂度（线性/平方/立方）都能在超时内跑完
N_ARRAY = 80          # 一维数组长度
N_MATRIX_ROWS = 60     # 矩阵行数
N_MATRIX_COLS = 8      # 矩阵列数
N_STR = 80            # 字符串长度
N_TREE = 63            # 树层序节点数（完全二叉深度 6，避免退化链/递归溢出）
BIG_INT_LO, BIG_INT_HI = 10 ** 6, 10 ** 9
ELEM_LO, ELEM_HI = -10 ** 4, 10 ** 4


def parse_input_values(text: str):
    """流式解析输入文本为参数列表（JSON 值）。"""
    dec = json.JSONDecoder()
    idx, vals = 0, []
    while idx < len(text):
        while idx < len(text) and text[idx] in " \t\r\n":
            idx += 1
        if idx >= len(text):
            break
        try:
            obj, end = dec.raw_decode(text, idx)
            vals.append(obj)
            idx = end
        except Exception:
            nl = text.find("\n", idx)
            idx = len(text) if nl == -1 else nl + 1
    return vals


def is_design_ops(vals):
    """设计类题：第一个参数是纯字符串数组（操作序列），跳过压力生成。"""
    return bool(vals) and isinstance(vals[0], list) and vals[0] and all(isinstance(x, str) for x in vals[0])


def _int_range(sample):
    """从样例值推断元素值域（含扩展），保持题目约束（排列/值域受限）。"""
    if isinstance(sample, int):
        lo = hi = sample
    else:
        nums = [x for x in sample if isinstance(x, (int, float)) and not isinstance(x, bool)]
        if not nums:
            return ELEM_LO, ELEM_HI
        lo, hi = min(nums), max(nums)
    span = max(abs(hi), abs(lo), 1)
    return lo - span, hi + span


def scale_elem(v, rng, lo, hi):
    if isinstance(v, bool):
        return rng.choice([True, False])
    if isinstance(v, int):
        return rng.randint(lo, hi)
    if isinstance(v, float):
        return round(rng.uniform(lo, hi), 2)
    if isinstance(v, str):
        return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(rng.randint(5, 20)))
    return v


def _balanced_tree(n_nodes):
    """生成平衡二叉树层序数组（完全二叉取前 n 个，避免退化链触发递归深度）。"""
    import math
    depth = int(math.log2(n_nodes + 1))
    total = (1 << (depth + 1)) - 1
    arr = []
    for i in range(total):
        arr.append(i + 1)
    out = [arr[0]]
    idx = 1
    for i in range(total):
        left = 2 * i + 1
        right = 2 * i + 2
        if left < total:
            out.append(arr[left] if left < n_nodes else None)
            idx += 1
        if right < total:
            out.append(arr[right] if right < n_nodes else None)
            idx += 1
        if idx >= n_nodes:
            break
    return out


def scale_value(v, rng):
    if isinstance(v, bool):
        return rng.choice([True, False])
    if isinstance(v, int):
        return rng.randint(1, 200) if abs(v) < 1000 else rng.randint(1000, 100000)
    if isinstance(v, float):
        return round(rng.uniform(-10 ** 4, 10 ** 4), 2)
    if isinstance(v, str):
        return "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")
                       for _ in range(N_STR))
    if isinstance(v, list):
        if v and isinstance(v[0], list):  # 二维（矩阵/字符串数组等）
            rows = N_MATRIX_ROWS
            cols = N_MATRIX_COLS if not v[0] else len(v[0])
            lo, hi = _int_range(v[0])
            return [[scale_elem(v[0][0] if v[0] else 0, rng, lo, hi) for _ in range(cols)] for _ in range(rows)]
        if v and isinstance(v[0], int) and None in v:  # 树层序（含 null）
            return _balanced_tree(N_TREE)
        lo, hi = _int_range(v)
        n = N_ARRAY
        return [scale_elem(v[0] if v else 0, rng, lo, hi) for _ in range(n)]
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-problem", type=int, default=1)
    ap.add_argument("--seed", type=int, default=20260829)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    with open(PROBLEMS_PATH, "r", encoding="utf-8") as f:
        problems = json.load(f)

    n_mounted = n_skip = n_fail = 0
    for p in problems:
        if p.get("stress_inputs"):
            n_mounted += len(p["stress_inputs"])
            continue
        if not p.get("test_cases"):
            n_skip += 1
            continue
        vals = parse_input_values(p["test_cases"][0]["input"])
        if not vals or is_design_ops(vals):
            n_skip += 1
            continue
        added = []
        for _ in range(args.max_per_problem):
            scaled = [scale_value(v, rng) for v in vals]
            inp = "\n".join(
                json.dumps(x, ensure_ascii=False, separators=(",", ":")) if not isinstance(x, str)
                else json.dumps(x, ensure_ascii=False) for x in scaled
            )
            res = run_code(p["reference_solution"], inp, timeout=10.0)
            if res.ok and res.stdout.strip():
                added.append(inp)
            else:
                n_fail += 1
        p["stress_inputs"] = added
        n_mounted += len(added)
        if n_mounted % 100 == 0:
            print(f"  ...已挂载 {n_mounted} 个压力输入", flush=True)

    with open(PROBLEMS_PATH, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=1)
    print(f"完成：挂载 {n_mounted} 个压力输入（跳过设计类/无样例 {n_skip}，参考解异常 {n_fail}）")


if __name__ == "__main__":
    main()
