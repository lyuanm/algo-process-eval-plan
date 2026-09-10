"""生成全量评测看板：demo/dashboard.html。

消费 eval/run_full.py 的三份产物（Hy3 解答缓存、逐题评估、指标汇总），
输出自包含单文件页面，离线可直接打开。展示：

  ① 核心指标卡   答案准确率 / 过程正确率 / 答案对但过程错（本系统的增量价值）/ 覆盖率
  ② 难度分层     各难度的答案率 vs 过程率差距
  ③ 算法域分层   12 个算法域的通过情况
  ④ 错误归因     错误类型分布 + 错误步骤分布 + 沙盒 verdict（AC/WA/TLE/RE/CE）分布
  ⑤ 效率指标     单题生成耗时 / 评估耗时
  ⑥ 全量明细     513 题可筛选、可搜索、可展开查看 Hy3 完整过程与步骤级判定

运行：python tools/gen_dashboard.py            # 默认 rule 后端
      python tools/gen_dashboard.py --backend llm
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)

from src import runlog  # noqa: E402

RES_DIR = os.path.join(ROOT, "eval", "results")
OUT = os.path.join(ROOT, "demo", "dashboard.html")

REASON_LIMIT = 4000  # 单题过程截断长度，控制页面体积


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def split_reasoning(raw: str):
    """把 Hy3 原始输出拆成四段 + 代码（与题面四步骤对齐）。"""
    import re
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", raw, re.DOTALL)
    code = m.group(1).strip() if m else ""
    text = (raw[: m.start()] + raw[m.end():]).strip() if m else raw
    steps = {"思路/建模": "", "复杂度分析": "", "边界与处理": ""}
    for part in re.split(r"\n##\s*", "\n" + text):
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        head, body = lines[0], "\n".join(lines[1:]).strip()
        if "思路" in head or "建模" in head:
            steps["思路/建模"] += body + "\n"
        elif "复杂度" in head:
            steps["复杂度分析"] += body + "\n"
        elif "边界" in head or "处理" in head:
            steps["边界与处理"] += body + "\n"
    return steps, code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["rule", "llm"], default="rule")
    ap.add_argument("--problems", default=os.path.join(ROOT, "data", "problems.json"))
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    problems = {p["id"]: p for p in load_json(args.problems, [])}
    summary = load_json(os.path.join(RES_DIR, f"full_summary_{args.backend}.json"))
    evals = read_jsonl(os.path.join(RES_DIR, f"full_eval_{args.backend}.jsonl"))
    raws = {r["problem_id"]: r for r in read_jsonl(os.path.join(RES_DIR, "hy3_solutions.jsonl"))}

    if summary is None or not evals:
        raise SystemExit("缺少全量评测产物，请先运行：python eval/run_full.py --workers 8")

    items = []
    for e in sorted(evals, key=lambda x: x["problem_id"]):
        pid = e["problem_id"]
        meta = problems.get(pid, {})
        raw_rec = raws.get(pid, {})
        steps, code = split_reasoning(raw_rec.get("raw", ""))
        items.append({
            "id": pid,
            "title": e.get("title") or meta.get("title", ""),
            "difficulty": e.get("difficulty") or meta.get("difficulty", ""),
            "domain": e.get("domain") or meta.get("domain", ""),
            "source": meta.get("source", ""),
            "url": meta.get("problem_url", ""),
            "final_correct": bool(e.get("final_correct")),
            "process_valid": bool(e.get("process_valid")),
            "passed": e.get("passed_cases", 0),
            "total": e.get("total_cases", 0),
            "error_step": e.get("error_step"),
            "error_type": e.get("error_type"),
            "error_type_name": e.get("error_type_name"),
            "note": e.get("note", ""),
            "verdict": e.get("verdict_summary", ""),
            "stress": e.get("stress_summary", ""),
            "eval_sec": e.get("eval_sec"),
            "gen_sec": raw_rec.get("elapsed"),
            "attempts": raw_rec.get("attempts"),
            "model": raw_rec.get("model") or runlog.LEGACY_MODEL,
            "steps": [
                {"step": s["step"], "name": s["name"], "ok": s["ok"], "reason": s["reason"]}
                for s in e.get("step_verdicts", [])
            ],
            "reasoning": (raw_rec.get("raw", "") or "")[:REASON_LIMIT],
            "code": code[:REASON_LIMIT],
        })

    # 模型来源构成：跑批中途可能因额度/容量限制更换模型，必须逐题可追溯——
    # 否则「513 题的指标」会被误读成单一模型的能力，而实际是多模型混合结果。
    model_stats: dict = {}
    for it in items:
        g = model_stats.setdefault(it["model"], {"n": 0, "final_ok": 0, "proc_ok": 0, "lucky": 0})
        g["n"] += 1
        g["final_ok"] += 1 if it["final_correct"] else 0
        g["proc_ok"] += 1 if it["process_valid"] else 0
        g["lucky"] += 1 if (it["final_correct"] and not it["process_valid"]) else 0
    for g in model_stats.values():
        g["final_acc"] = round(g["final_ok"] / g["n"], 4) if g["n"] else 0.0
        g["process_rate"] = round(g["proc_ok"] / g["n"], 4) if g["n"] else 0.0
    model_dist = dict(sorted(model_stats.items(), key=lambda kv: -kv[1]["n"]))

    # 沙盒 verdict 全量计数（从每题 verdict_summary 字符串聚合）
    verdict_totals = {}
    for it in items:
        for chunk in (it["verdict"] or "").split():
            if ":" not in chunk:
                continue
            k, v = chunk.split(":", 1)
            try:
                verdict_totals[k] = verdict_totals.get(k, 0) + int(v)
            except ValueError:
                pass

    # 四步骤逐级通过率：把每题 step_verdicts 聚合，看推理链在哪一步开始崩
    step_pass = {str(i): {"ok": 0, "total": 0, "name": n} for i, n in
                 ((1, "思路/建模"), (2, "复杂度分析"), (3, "边界与处理"), (4, "代码实现"))}
    for it in items:
        for s in it["steps"]:
            k = str(s.get("step"))
            if k in step_pass:
                step_pass[k]["total"] += 1
                if s.get("ok"):
                    step_pass[k]["ok"] += 1
    for v in step_pass.values():
        v["rate"] = round(v["ok"] / v["total"], 4) if v["total"] else 0.0

    # 难度 × 错误类型 交叉（仅统计过程不成立的题，定位「哪档难度易犯哪类错」）
    cross = {}
    for it in items:
        if it["process_valid"]:
            continue
        d = it["difficulty"] or "?"
        et = (it["error_type_name"] or it["error_type"] or "未归因").split("：")[0]
        cross.setdefault(d, {})
        cross[d][et] = cross[d].get(et, 0) + 1

    # 各算法域「答案对但过程错」集中度（核心增量价值在哪些域更突出）
    domain_lucky = {k: {"n": v["n"], "lucky": v["lucky_pass"],
                        "rate": round(v["lucky_pass"] / v["n"], 4) if v["n"] else 0.0}
                    for k, v in (summary.get("by_domain") or {}).items()}

    gen_secs = [it["gen_sec"] for it in items if it.get("gen_sec")]
    data = {
        "generated_at": summary.get("generated_at", ""),
        "backend": args.backend,
        "model": "、".join(f"{k} ×{v['n']}" for k, v in model_dist.items()) or "—",
        "models": model_dist,
        "model_mixed": len(model_dist) > 1,
        "summary": summary,
        "verdict_totals": verdict_totals,
        "step_pass": step_pass,
        "diff_error_cross": cross,
        "domain_lucky": domain_lucky,
        "gen_sec_stats": {
            "median": round(sorted(gen_secs)[len(gen_secs) // 2], 1) if gen_secs else None,
            "total_min": round(sum(gen_secs) / 60, 1) if gen_secs else None,
            "max": round(max(gen_secs), 1) if gen_secs else None,
            "min": round(min(gen_secs), 1) if gen_secs else None,
            "mean": round(sum(gen_secs) / len(gen_secs), 1) if gen_secs else None,
        },
        "items": items,
    }

    tpl_path = os.path.join(HERE, "dashboard_template.html")
    with open(tpl_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    size_mb = os.path.getsize(args.out) / 1024 / 1024
    print(f"生成 {os.path.relpath(args.out)}（{len(items)} 题，{size_mb:.2f} MB）")


if __name__ == "__main__":
    main()
