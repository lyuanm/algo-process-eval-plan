"""生成 data/problems.json —— 聚合 pbank 各模块（真实 LeetCode 官方题源）全部题目。

题源：LeetCode 官方题库（题目 API） + LeetCode 官方题解文章（答案代码）。
每题均提供：
  - 题目描述 / 输入输出格式 / 约束（来自官方题面）
  - reference_solution：官方题解代码 + I/O 包装（stdin 读 / stdout 写），即"标准答案"
  - check_mode：内置自动判定模式（int / int_list / bool / str / token_list / float ...）
  - test_cases：官方样例，expected 由官方题解代码运行产生
  - solution_url / problem_url：真实来源链接
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from tools.pbank import collect  # noqa: E402

OUT = os.path.join(ROOT, "data", "problems.json")


def main():
    problems = collect()
    # 去重（按 id）
    seen = set()
    uniq = []
    for p in problems:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        uniq.append(p)
    # 按 id 排序（字母序稳定输出）
    uniq.sort(key=lambda p: p["id"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=1)
    from collections import Counter
    c = Counter(p["difficulty"] for p in uniq)
    print(f"已写出 {len(uniq)} 题 -> {OUT}")
    print(f"难度分布: {dict(c)}")
    # 自动挂载差分压力输入（deep-ERV 依赖），失败不阻塞
    try:
        from tools.gen_stress import main as gen_stress_main
        import sys as _sys
        gen_stress_main()
    except Exception as e:
        print(f"压力输入生成跳过：{e}")


if __name__ == "__main__":
    main()
