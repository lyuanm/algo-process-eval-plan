# -*- coding: utf-8 -*-
"""预检：用当前评估器重跑已有解答，校验「步骤判定 ⟺ 总体判定」的一致性不变量。

背景：阶段 B 的评估缓存 full_eval_rule.jsonl 是修复前产出的，其中 31 条记录出现
「四步全绿却判定过程不成立」的自相矛盾（step_verdicts 在失败归因之前生成，只有
复杂度冲突会即时回写）。修复（_align_step_verdicts）之后，这些旧记录必须整体丢弃
重建，否则缓存命中会让修复完全失效。

本脚本不写任何正式缓存文件，只在临时路径上跑一遍，用于在全量跑批结束前确认修复
在**真实数据**上生效（单元测试只覆盖了构造样本）。

用法：
  python tools/preflight_consistency.py [--limit 96] [--workers 6] [--deep-erv]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.problems import load_problems  # noqa: E402
from src.process_evaluator import build_evaluator  # noqa: E402
from src.solver import parse_solution  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES_DIR = os.path.join(ROOT, "eval", "results")
SOL_CACHE = os.path.join(RES_DIR, "hy3_solutions.jsonl")


def read_jsonl(path):
    """容忍被中断截断的残行（与 run_full.read_jsonl 保持一致的语义）。"""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只取前 N 题（0=全部已缓存题）")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=8.0)
    ap.add_argument("--deep-erv", action="store_true")
    args = ap.parse_args()

    problems = {p.id: p for p in load_problems(os.path.join(ROOT, "data", "problems.json"))}
    raws = {}
    for r in read_jsonl(SOL_CACHE):
        raw = (r.get("raw") or "").strip()
        if raw and "[OFFLINE MOCK" not in raw:
            raws[r["problem_id"]] = raw

    ids = sorted(raws)
    if args.limit:
        ids = ids[: args.limit]
    print(f"预检对象：{len(ids)} 题（解答缓存共 {len(raws)} 题）｜deep-erv={args.deep_erv}")

    t0 = time.time()

    def work(pid):
        ev = build_evaluator("rule", None, timeout=args.timeout, use_stress=args.deep_erv)
        sol = parse_solution(raws[pid])
        sol.problem_id = pid
        try:
            return ev.evaluate(problems[pid], sol).to_dict()
        except Exception as e:  # pragma: no cover
            return {"problem_id": pid, "_err": f"{type(e).__name__}: {e}"}

    recs, errs = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for fut in as_completed([ex.submit(work, p) for p in ids]):
            r = fut.result()
            (errs if r.get("_err") else recs).append(r)

    # ---- 不变量 1：过程不成立 ⟺ 至少一步不通过，且 error_step 必在其中 ----
    # 注意：评估记录的字段名是 step_verdicts（ProcessEvalResult.to_dict），
    # 看板数据里的 "steps" 是 gen_dashboard 归一化后的别名，此处不可混用。
    v1 = []
    for r in recs:
        sv = r.get("step_verdicts") or []
        steps = {s.get("step"): s.get("ok") for s in sv}
        if not steps:
            v1.append((r["problem_id"], "缺少步骤判定数据", r.get("error_step")))
        elif r.get("process_valid") is False:
            if all(steps.values()):
                v1.append((r["problem_id"], "全部步骤通过却判定过程不成立", r.get("error_step")))
            elif r.get("error_step") not in steps:
                v1.append((r["problem_id"], "error_step 不在步骤集合内", r.get("error_step")))
            elif steps.get(r.get("error_step")) is True:
                v1.append((r["problem_id"], "error_step 指向的步骤仍标记通过", r.get("error_step")))
        else:
            if not all(steps.values()):
                bad = [k for k, ok in steps.items() if not ok]
                v1.append((r["problem_id"], f"判定过程成立但步骤 {bad} 未通过", None))

    # ---- 不变量 2：答案对但过程错（lucky_pass）必须真的答案对 ----
    v2 = [r["problem_id"] for r in recs
          if r.get("final_correct") and r.get("process_valid") and r.get("error_type")]

    n = len(recs)
    final_ok = sum(1 for r in recs if r.get("final_correct"))
    proc_ok = sum(1 for r in recs if r.get("process_valid"))
    lucky = sum(1 for r in recs if r.get("final_correct") and not r.get("process_valid"))
    secs = [r.get("eval_sec", 0) for r in recs if r.get("eval_sec")]

    print(f"\n评估完成 {n} 题，异常 {len(errs)} 题，耗时 {time.time()-t0:.1f}s")
    print(f"答案准确率 {final_ok/n:.1%}｜过程正确率 {proc_ok/n:.1%}｜答案对但过程错 {lucky} 题")
    if secs:
        print(f"单题评估耗时 中位 {statistics.median(secs):.2f}s  最大 {max(secs):.2f}s")
    print(f"\n★ 一致性不变量违规：{len(v1)} 条")
    for pid, why, es in v1[:15]:
        print(f"   {pid}: {why}（error_step={es}）")
    print(f"★ 判定成立却残留 error_type 的题：{len(v2)} 条 {v2[:10]}")

    ok = not v1 and not v2 and not errs
    print("\n" + ("✅ 预检通过：修复在真实数据上生效" if ok else "❌ 预检未通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
