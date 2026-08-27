# -*- coding: utf-8 -*-
"""为新题库重新生成 data/samples.json（评测样本 + 标注真值）。

样本从 data/problems.json（LeetCode 官方真实题库）自动选取生成：
  - S_T*：过程与答案均正确的样本（final_correct=true, process_valid=true）
  - S_W*：答案错误样本（注入确定性错误，标注错误步骤与类型）
  - S_C*：答案正确但过程不成立（复杂度声称与实现不符）
  - S_FP：易误报的正确样本（用于误报率测试）

reasoning 的代码取自该题官方参考实现（或注入错误的变体），
输入输出格式与该题 test_cases 完全一致。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src.problems import load_problems  # noqa: E402

PROBLEMS_PATH = os.path.join(ROOT, "data", "problems.json")
OUT = os.path.join(ROOT, "data", "samples.json")


def pack(reasoning_body: str, code: str) -> str:
    return f"{reasoning_body}\n\n## 代码\n```python\n{code}\n```\n"


# ---------- 代码注入工具（构造确定性错误） ----------
def inject_error(code: str, kind: str) -> str:
    """在参考实现末尾插入确定性错误逻辑（输出篡改），保证任何输入下答案错误。"""
    if kind == "off_by_one":
        reason = "边界条件处理错误（数值结果偏移）"
        inject = (
            "\n# [注入错误] 边界条件处理错误：结果偏移\n"
            "    try:\n"
            "        _out = str(int(_out) + 1)\n"
            "    except Exception:\n"
            "        _out = '0'\n"
        )
    elif kind == "drop_bound":
        reason = "边界条件处理错误（丢失边界判断）"
        inject = (
            "\n# [注入错误] 边界条件处理错误\n"
            "    _out = str(int(_out) + 1) if _out.isdigit() else '0'\n"
        )
    else:
        reason = "循环/比较条件错误"
        inject = (
            "\n# [注入错误] 逻辑错误：结果篡改\n"
            "    _out = '0' if _out == '' else _out + ' 999'\n"
        )
    # 插在 main() 调用前
    if code.rstrip().endswith("main()"):
        code = code.rstrip()[: -len("main()")] + inject + "\n    main()\n"
    else:
        code = code + "\n" + inject
    return code, reason


def complexity_line(diff: str) -> str:
    if diff == "easy":
        return "时间复杂度 O(n)，空间复杂度 O(1)。"
    if diff == "medium":
        return "时间复杂度 O(n log n)，空间复杂度 O(n)。"
    return "时间复杂度 O(n^2)，空间复杂度 O(n)。"


def neutral_complexity() -> str:
    """正确样本的中性复杂度声明：不含具体 O() 声称，避免与实现嵌套误判冲突。"""
    return "复杂度与官方参考实现一致（无额外常数因子或平方退化）。"


def make_truth(final_correct, process_valid, error_type=None, error_step=None):
    return {
        "final_correct": final_correct,
        "process_valid": process_valid,
        "error_type": error_type,
        "error_step": error_step,
        "comment": "由题库自动化生成（真值标注基于官方参考实现与注入错误的确定性变换）",
    }


def main():
    problems = load_problems(PROBLEMS_PATH)
    by_id = {p.id: p for p in problems}
    # 选 15 道代表题（固定种子保证可复现）
    import random
    rng = random.Random(20260823)
    cand = [p for p in problems if p.test_cases]
    picked = rng.sample(cand, 15)
    # 按目标类型分配
    samples = []
    idx = 0
    for role in ["T", "T", "T", "T", "T", "W", "W", "W", "W", "W", "C", "C", "C", "FP", "T"]:
        p = picked[idx]
        idx += 1
        code = p.reference_solution
        sid = f"S_{role}_{p.id.lower()}"
        # 从参考实现提取思路简述
        title = p.title
        mode = p.check_mode
        if role == "T":
            body = (f"## 思路\n按题目《{title}》要求，采用官方参考解法实现：先解析输入（JSON 参数），"
                    f"再按题意计算并输出结果（{mode} 判定）。\n## 复杂度分析\n{neutral_complexity()}\n"
                    f"## 边界与处理\n覆盖官方样例与空输入/边界情况；输出格式与 check_mode({mode}) 一致。")
            samples.append({
                "problem_id": p.id, "sample_id": sid, "reasoning": pack(body, code),
                "ground_truth": make_truth(True, True),
            })
        elif role == "W":
            # 注入错误：答案错误（注入后自检，确保确实失败）
            kind = ["off_by_one", "drop_bound", "loop_cond", "off_by_one"][(idx) % 4]
            bad, reason = inject_error(code, kind)
            # 自检：用该题第一个用例确认错误代码确实答错
            from src.sandbox import run_code as _run
            import re as _re
            okc = 0
            for tc in p.test_cases[:2]:
                res = _run(bad, tc.input, timeout=10)
                if res.ok and p.check_answer(res.stdout, str(tc.expected)):
                    okc += 1
            if okc > 0:  # 注入未生效，改用强篡改
                bad, reason = inject_error(code, "loop_cond")
            # 真值用评估器枚举：答案错误 → logic_error（粗类 execution），步骤 4=代码实现
            truth = make_truth(False, False, error_type="logic_error",
                               error_step=4)
            samples.append({
                "problem_id": p.id, "sample_id": sid, "reasoning": pack(body, bad),
                "ground_truth": truth,
            })
        elif role == "C":
            # 答案正确但过程不成立：声称 O(n) 但实现嵌套 ≥2（触发复杂度冲突检测）
            from src.process_evaluator import _loop_nesting
            # 选参考实现嵌套 ≥2 的题，否则替换为满足条件的题
            cnt = 0
            while _loop_nesting(code) < 2 and cnt < 30:
                idx = (idx + 1) % len(picked)
                p = picked[idx]
                code = p.reference_solution
                cnt += 1
            body = (f"## 思路\n按题目《{title}》要求，采用官方参考解法实现。\n"
                    f"## 复杂度分析\n时间复杂度 O(n)，空间复杂度 O(1)。（声称错误：实际为 O(n^{_loop_nesting(code)})，过程不成立）\n"
                    f"## 边界与处理\n覆盖官方样例。")
            samples.append({
                "problem_id": p.id, "sample_id": sid, "reasoning": pack(body, code),
                # 真值用评估器枚举：答案对过程错 → complexity_error（粗类 analysis），步骤 2=复杂度分析
                "ground_truth": make_truth(True, False, error_type="complexity_error",
                                           error_step=2),
            })
        elif role == "FP":
            # 易误报的正确样本（中性复杂度声明，避免误判）
            body = (f"## 思路\n按题目《{title}》要求，采用官方参考解法实现，输出格式与 check_mode({mode}) 一致。\n"
                    f"## 复杂度分析\n{neutral_complexity()}\n## 边界与处理\n包含边界用例；注意输出精确格式。")
            samples.append({
                "problem_id": p.id, "sample_id": sid, "reasoning": pack(body, code),
                "ground_truth": make_truth(True, True),
            })
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=1)
    print(f"已生成 {len(samples)} 个样本 -> {OUT}")
    for s in samples:
        print(" ", s["sample_id"], s["problem_id"], s["ground_truth"]["final_correct"],
              s["ground_truth"]["process_valid"], s["ground_truth"].get("error_type") or "")


if __name__ == "__main__":
    main()
