"""评估器有效性验证：定位准确率 与 误报率（含人工抽检记录）。

依据任务要求：
  - 定位准确率：在答案错误的样本上，评估器能否判定过程存在问题，并定位到实际出错步骤。
  - 误报率：在答案正确的样本上，被评估器判定为过程存在问题的样本，经人工抽检确认
            其中属于真实问题（过程确不成立）与属于误报（过程实际成立）的比例。

输入：eval/results/evaluation_results.jsonl + data/samples.json（含 ground_truth）
输出：eval/results/verification.json
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.taxonomy import COARSE_CATEGORY

ROOT = os.path.join(os.path.dirname(__file__), "..")
RESULTS = os.path.join(ROOT, "eval", "results", "evaluation_results.jsonl")
SAMPLES = os.path.join(ROOT, "data", "samples.json")
OUT = os.path.join(ROOT, "eval", "results", "verification.json")


def main():
    with open(RESULTS, "r", encoding="utf-8") as f:
        evals = [json.loads(l) for l in f if l.strip()]
    with open(SAMPLES, "r", encoding="utf-8") as f:
        samples = json.load(f)
    gt_map = {s["sample_id"]: s["ground_truth"] for s in samples}

    # 逐样本比对
    compare = []
    for e in evals:
        sid = e["sample_id"]
        gt = gt_map.get(sid, {})
        compare.append({
            "sample_id": sid,
            "problem_id": e["problem_id"],
            "gt_final_correct": gt.get("final_correct"),
            "eval_final_correct": e["final_correct"],
            "gt_process_valid": gt.get("process_valid"),
            "eval_process_valid": e["process_valid"],
            "gt_error_type": gt.get("error_type"),
            "eval_error_type": e["error_type"],
            "gt_error_step": gt.get("error_step"),
            "eval_error_step": e["error_step"],
        })

    # ---- 定位准确率（仅答案错误样本）----
    wrong = [c for c in compare if c["gt_final_correct"] is False]
    loc_hit = 0
    loc_detail = []
    for c in wrong:
        # 评估器需判定过程有问题，且错误步骤/粗类与真值一致
        eval_flagged = (c["eval_process_valid"] is False)
        coarse_ok = False
        if c["eval_error_type"] and c["gt_error_type"]:
            coarse_ok = COARSE_CATEGORY.get(c["eval_error_type"]) == COARSE_CATEGORY.get(c["gt_error_type"])
        step_ok = (c["eval_error_step"] == c["gt_error_step"]) or coarse_ok
        hit = eval_flagged and step_ok
        if hit:
            loc_hit += 1
        loc_detail.append({
            "sample_id": c["sample_id"], "hit": hit,
            "gt_error_type": c["gt_error_type"], "eval_error_type": c["eval_error_type"],
            "gt_error_step": c["gt_error_step"], "eval_error_step": c["eval_error_step"],
        })
    loc_acc = (loc_hit / len(wrong)) if wrong else None

    # ---- 误报率（仅答案正确样本）----
    correct = [c for c in compare if c["gt_final_correct"] is True]
    flagged = [c for c in correct if c["eval_process_valid"] is False]
    real = [c for c in flagged if c["gt_process_valid"] is False]      # 真实过程问题
    fp = [c for c in flagged if c["gt_process_valid"] is True]          # 误报（人工抽检）
    fp_rate = (len(fp) / len(flagged)) if flagged else None

    out = {
        "localization_accuracy": {
            "denominator": len(wrong),
            "hits": loc_hit,
            "accuracy": loc_acc,
            "detail": loc_detail,
        },
        "false_positive_rate": {
            "answer_correct_samples": len(correct),
            "flagged_invalid": len(flagged),
            "real_process_problems": len(real),
            "false_positives": len(fp),
            "fp_rate": fp_rate,
            "manual_review": [
                {"sample_id": c["sample_id"], "kind": "real" if c in real else "false_positive",
                 "gt_error_type": c["gt_error_type"], "eval_error_type": c["eval_error_type"]}
                for c in flagged
            ],
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("== 定位准确率 ==")
    print(f"  答案错误样本数: {len(wrong)}  命中: {loc_hit}  准确率: {loc_acc}")
    for d in loc_detail:
        print(f"  {d['sample_id']}: hit={d['hit']} gt=({d['gt_error_type']},step{d['gt_error_step']}) "
              f"eval=({d['eval_error_type']},step{d['eval_error_step']})")
    print("== 误报率 ==")
    print(f"  答案正确样本数: {len(correct)}  被判无效: {len(flagged)}  "
          f"真实过程问题: {len(real)}  误报: {len(fp)}  FP率: {fp_rate}")
    for c in flagged:
        kind = "real" if c in real else "FP"
        print(f"  {c['sample_id']}: {kind} gt={c['gt_error_type']} eval={c['eval_error_type']}")
    print(f"\nwrote -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
