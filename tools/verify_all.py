"""正确性自检：对每个题跑 reference_solution 于全部 test_cases，确认标准答案自洽。

用法：
  python tools/verify_all.py            # 检查全部已加载模块
  python tools/verify_all.py AE AM AH   # 仅检查 id 以 AE/AM/AH 开头的题
输出：每题通过数/总数，末尾汇总失败清单（若有）。
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from src.problems import Problem, TestCase, verify_problem_testcases
from tools.pbank import collect

PREFIXES = sys.argv[1:]


def to_prob(p):
    return Problem(
        id=p["id"], title=p["title"], difficulty=p["difficulty"], domain=p["domain"],
        description=p["description"], input_format=p["input_format"], output_format=p["output_format"],
        constraints=p["constraints"], reference_solution=p["reference_solution"],
        checker_src=p.get("checker_src", ""), check_mode=p.get("check_mode", "exact"),
        test_cases=[TestCase(t["input"], str(t["expected"])) for t in p["test_cases"]],
        tags=p.get("tags", []), source=p.get("source", ""),
        stress_inputs=list(p.get("stress_inputs", [])),
    )


def main():
    problems = collect()
    if PREFIXES:
        problems = [p for p in problems if any(p["id"].upper().startswith(x.upper()) for x in PREFIXES)]
    print(f"待检题目数：{len(problems)}")
    fails = []
    for p in problems:
        r = verify_problem_testcases(to_prob(p), timeout=8.0)
        flag = "OK " if r["all_passed"] else "FAIL"
        print(f"  [{flag}] {p['id']:6} {p['source']:12} {p['title']}  ({r['passed']}/{r['total']})")
        if not r["all_passed"]:
            fails.append((p["id"], p["title"], r["details"]))
    print("\n==== 汇总 ====")
    print(f"总数 {len(problems)}，通过 {len(problems) - len(fails)}，失败 {len(fails)}")
    for pid, title, det in fails:
        print(f"  ✗ {pid} {title}")
        for d in det:
            if not d["passed"]:
                print(f"      case {d['case']}: {d['stderr']}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
