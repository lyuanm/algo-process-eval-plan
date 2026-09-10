"""运行端到端过程评估：对样本集逐题执行 求解(或取样本) -> 沙盒校验 -> 过程评估。

产出：
  eval/results/evaluation_results.jsonl        逐样本完整评估结果（--source samples）
  eval/results/evaluation_results_live.jsonl   live 实时求解结果（--source live）
  eval/results/evaluation_results.csv          便于阅读的结果表格

用法：
  python eval/run_eval.py --source samples --backend rule
  python eval/run_eval.py --source live   # 调用 Hy3 实时求解（需 HY3_API_KEY）
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.problems import load_problems
from src.solver import parse_solution, Solution
from src.process_evaluator import build_evaluator, RuleBasedProcessEvaluator
from src.hy3_client import load_client_from_env

ROOT = os.path.join(os.path.dirname(__file__), "..")
PROBLEMS_PATH = os.path.join(ROOT, "data", "problems.json")
SAMPLES_PATH = os.path.join(ROOT, "data", "samples.json")
RESULTS_DIR = os.path.join(ROOT, "eval", "results")


def load_samples(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def select_live_targets(problems, ids, limit, seed):
    """live 模式选题：--ids 指定具体题；否则 --limit N 从题库随机取 N 题（演示少量题）。
    都不给时返回全部题。"""
    if ids:
        missing = [i for i in ids if i not in problems]
        if missing:
            raise SystemExit(f"指定的题不存在: {missing}")
        return list(ids)
    all_ids = sorted(problems)
    if limit and 0 < limit < len(all_ids):
        import random
        rng = random.Random(seed)
        return rng.sample(all_ids, limit)
    return all_ids


def _emit(jf, rows, res, prob, raw=""):
    """写一条评估记录到 jsonl 并打印。"""
    rec = res.to_dict()
    rec["difficulty"] = prob.difficulty
    rec["domain"] = prob.domain
    rec["title"] = prob.title
    if raw:
        rec["raw"] = raw  # Hy3/样本完整解题过程（评审与 UI 展示用）
    jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
    rows.append(rec)
    print(
        f"{res.sample_id} {prob.id} {prob.difficulty}: "
        f"final={res.final_correct} process_valid={res.process_valid} "
        f"err={res.error_type} step={res.error_step}"
    )


def output_paths(backend: str, source: str):
    """结果文件路径（jsonl, csv）。

    文件名必须**同时区分 backend 与 source**：
      - 区分 backend：便于 UI 做 rule vs llm 对比；
      - 区分 source：`--source live` 若与 `--source samples` 共用路径，会覆盖掉含人工真值的
        15 个诊断样本结果，而 verify_evaluator.py / report.py / gen_demo.py 都依赖后者，
        被覆盖后这些工具会静默退化为「0 样本、指标 None」，README 的准确率/误报率结论随之失效。
    """
    suffix = "" if backend == "rule" else f"_{backend}"
    if source == "live":
        suffix = f"_live{suffix}"
    return (os.path.join(RESULTS_DIR, f"evaluation_results{suffix}.jsonl"),
            os.path.join(RESULTS_DIR, f"evaluation_results{suffix}.csv"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["samples", "live"], default="samples")
    ap.add_argument("--backend", choices=["rule", "llm"], default="rule")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--judge-samples", type=int, default=1,
                    help="LLM 裁判自一致性采样次数（>1 启用多数投票）")
    ap.add_argument("--deep-erv", action="store_true",
                    help="启用差分压力测试（参考解为 oracle），规则与 LLM 后端均生效；"
                         "可捕捉主测试集「巧合通过」的样本，提升过程判定精度")
    ap.add_argument("--limit", type=int, default=None,
                    help="live 模式最多实时求解的题数（演示建议 3~5，避免 Hy3 输出全部题库）")
    ap.add_argument("--ids", nargs="*", default=[],
                    help="live 模式指定题 ID（如 --ids AE01 AE02 AE03；与 --limit 二选一）")
    ap.add_argument("--seed", type=int, default=20260824,
                    help="live 随机选题种子（默认固定，保证演示可复现）")
    ap.add_argument("--problems", default=PROBLEMS_PATH)
    ap.add_argument("--samples", default=SAMPLES_PATH)
    ap.add_argument("--quiet", action="store_true",
                    help="live 模式不打印 Hy3 完整解题过程（默认打印，供现场演示）")
    args = ap.parse_args()

    problems = {p.id: p for p in load_problems(args.problems)}
    # llm 后端或 live 实时求解都需要 Hy3 client（无 key 时自动降级为离线 Mock）；
    # 仅 samples+rule 无需联网，不创建 client。
    client = load_client_from_env() if (args.backend == "llm" or args.source == "live") else None
    evaluator = build_evaluator(
        args.backend, client, timeout=args.timeout,
        judge_samples=args.judge_samples, use_stress=args.deep_erv,
    )

    os.makedirs(RESULTS_DIR, exist_ok=True)
    jsonl_path, csv_path = output_paths(args.backend, args.source)

    # live：按 --ids/--limit 选题实时求解（少量题接口）
    if args.source == "live":
        targets = select_live_targets(problems, args.ids, args.limit, args.seed)
        print(f"[live] 将实时求解 {len(targets)} 题: {', '.join(targets[:12])}{' ...' if len(targets) > 12 else ''}")
        from src.solver import solve_problem
    else:
        samples = load_samples(args.samples)
        print(f"[samples] 将评估 {len(samples)} 个样本")

    rows = []
    with open(jsonl_path, "w", encoding="utf-8") as jf:
        if args.source == "live":
            for pid in targets:
                prob = problems[pid]
                print(f"\n{'='*70}\n[求解] {prob.id} {prob.title}（{prob.difficulty} · {prob.domain}）")
                print(f"{'='*70}")
                sol = solve_problem(client, prob)
                sol.sample_id = f"LIVE_{pid}"
                if not args.quiet:
                    print(f"\n[Hy3 解题过程]\n{(sol.raw or '').strip()}\n")
                print("-" * 70)
                res = evaluator.evaluate(prob, sol)
                _emit(jf, rows, res, prob, raw=sol.raw or "")
        else:
            for sample in samples:
                prob = problems[sample["problem_id"]]
                sol = parse_solution(sample["reasoning"])
                sol.problem_id = prob.id
                sol.sample_id = sample["sample_id"]
                sol.source = "sample"
                res = evaluator.evaluate(prob, sol)
                _emit(jf, rows, res, prob)

    # 写 CSV
    cols = [
        "sample_id", "problem_id", "title", "difficulty", "domain",
        "final_correct", "passed_cases", "total_cases", "process_valid",
        "error_step", "error_type", "error_type_name", "backend",
        "verdict_summary", "first_failure_verdict", "stress_summary", "confidence", "note",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as cf:
        w = csv.DictWriter(cf, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nwrote {len(rows)} evaluations -> {os.path.relpath(jsonl_path)}")


if __name__ == "__main__":
    main()
