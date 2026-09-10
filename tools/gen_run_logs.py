# -*- coding: utf-8 -*-
"""把跑批留存的 jsonl 日志渲染成人可读的 markdown，并补齐历史题目的日志。

产出（eval/logs/）：
  solve_trace.jsonl / eval_trace.jsonl  —— 跑批过程中实时追加的机器可读日志
  hy3_原始回答日志.md                    —— 每题：完整 prompt + Hy3 原始回答全文
  过程评估判定日志.md                    —— 每题：逐用例 verdict + 四步骤判定 + 错误归因

另外负责「补导出」：hy3_solutions.jsonl 里已缓存的解答没有经过新版日志代码，本脚本
会按同一格式补写 trace 记录（用 build_prompt 重新生成 prompt，并标记 backfilled=true），
这样日志能覆盖全量题目，而无需重跑烧 API。

用法：
  python tools/gen_run_logs.py              # 补导出 + 渲染
  python tools/gen_run_logs.py --no-backfill --render-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src import runlog  # noqa: E402
from src.problems import load_problems  # noqa: E402
from src.solver import build_prompt  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES_DIR = os.path.join(ROOT, "eval", "results")
SOL_CACHE = os.path.join(RES_DIR, "hy3_solutions.jsonl")
LOG_DIR = os.path.join(ROOT, "eval", "logs")

STEP_NAMES = {1: "思路/建模", 2: "复杂度分析", 3: "边界与处理", 4: "代码实现"}

DIFF_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def load_problems_map():
    return {p.id: p for p in load_problems(os.path.join(ROOT, "data", "problems.json"))}


def backfill(problems, verbose=True):
    """把已有解答缓存补写成 trace 记录，使日志覆盖全量。"""
    have = {r["problem_id"] for r in runlog.read_jsonl(runlog.SOLVE_TRACE)}
    added = 0
    for r in runlog.read_jsonl(SOL_CACHE):
        pid = r.get("problem_id")
        raw = (r.get("raw") or "").strip()
        if not pid or pid in have or not raw or "[OFFLINE MOCK" in raw:
            continue
        p = problems.get(pid)
        if p is None:
            continue
        runlog.log_solve(
            p, build_prompt(p),
            [{"n": r.get("attempts", 1), "status": "ok", "reason": "",
              "elapsed": r.get("elapsed"), "response_chars": len(raw),
              "response_head": raw[:200]}],
            "ok", raw, ts=r.get("ts"), backfilled=True,
        )
        added += 1
    if verbose:
        print(f"补导出 {added} 条历史求解日志（来自解答缓存）")
    return added


# ----------------------------------------------------------------- 渲染
def _fence(text: str, lang: str = "") -> str:
    """安全包裹代码块：内容含 ``` 时改用更长的围栏，避免提前截断。"""
    text = text or ""
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}{lang}\n{text.rstrip()}\n{fence}"


def _toc(rows, name_fn):
    lines = []
    for r in rows:
        lines.append(f"- [{name_fn(r)}](#{_anchor(name_fn(r))})")
    return "\n".join(lines)


def _anchor(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        elif ch in " \t":
            out.append("-")
    return "".join(out)


def _latest_per_problem(rows):
    """同一题只保留**最后一条**记录。

    jsonl 是 append-only 的：换模型重跑、修正解答（--force）、失败后补跑都会追加新记录，
    因此原始行数会大于题数。渲染人可读日志时按题去重，避免同一题出现多节造成误读；
    完整历史仍保留在 jsonl 中，可随时追溯。
    """
    latest = {}
    for r in rows:
        latest[r.get("problem_id")] = r
    return list(latest.values())


def render_solve_log(problems):
    raw = runlog.read_jsonl(runlog.SOLVE_TRACE)
    deduped = _latest_per_problem(raw)
    rows = [r for r in deduped if r.get("problem_id") in problems]
    rows.sort(key=lambda r: (DIFF_ORDER.get(r.get("difficulty"), 9), r.get("problem_id") or ""))

    ok = sum(1 for r in rows if r.get("final_status") == "ok")
    fails = [r for r in rows if r.get("final_status") != "ok"]
    reasons = Counter()
    for r in fails:
        for a in r.get("attempts") or []:
            if a.get("status") != "ok":
                reasons[a.get("reason") or a.get("status")] += 1

    A = []
    A.append("# Hy3 原始回答日志（全保留）\n")
    A.append("> 本日志完整留存求解阶段的输入与输出：发给 Hy3 的**完整提示词**、Hy3 返回的"
             "**原始回答全文**、每次尝试的耗时与失败原因。\n")
    A.append(f"> 覆盖 **{len(rows)} / {len(problems)}** 题｜成功 {ok}｜未完成 {len(fails)}\n")
    A.append("\n## 零、统计概览\n")
    A.append("| 指标 | 数值 |")
    A.append("|---|---|")
    A.append(f"| 日志覆盖题数 | {len(rows)} |")
    A.append(f"| 求解成功 | {ok} |")
    A.append(f"| 未完成（重试耗尽） | {len(fails)} |")
    if fails:
        A.append(f"| 未完成题号 | {', '.join(r['problem_id'] for r in fails)} |")
    attempts_total = sum(len(r.get("attempts") or []) for r in rows)
    A.append(f"| 累计尝试次数 | {attempts_total} |")
    resp_chars = sum(r.get("response_chars") or 0 for r in rows)
    A.append(f"| 回答总字符数 | {resp_chars:,} |")
    A.append("")
    if reasons:
        A.append("**失败原因分布**（每次尝试计一次）：\n")
        A.append("| 原因 | 次数 |")
        A.append("|---|---|")
        for k, v in reasons.most_common():
            A.append(f"| {k} | {v} |")
        A.append("")
    A.append("> 提示：`solve_trace.jsonl` 为同内容的机器可读版本，含 `response_head` 等字段便于批量筛查。\n")
    A.append("\n## 一、目录\n")
    A.append(_toc(rows, lambda r: f"{r['problem_id']} {r.get('title','')}"))
    A.append("\n---\n")

    cur = None
    for r in rows:
        if r.get("difficulty") != cur:
            cur = r.get("difficulty")
            A.append(f"\n# 难度：{cur}\n")
        pid = r["problem_id"]
        A.append(f"\n## {pid} {r.get('title','')}\n")
        A.append(f"- 领域：{r.get('domain','')}｜难度：{r.get('difficulty','')}"
                 f"｜模型：{r.get('model','')}"
                 f"｜终态：**{runlog.STATUS_LABEL.get(r.get('final_status'), r.get('final_status'))}**"
                 f"｜尝试 {r.get('attempt_count')} 次"
                 + ("（日志由解答缓存补导出）" if r.get("backfilled") else ""))
        A.append(f"- 记录时间：{r.get('ts','')}｜prompt {r.get('prompt_chars',0):,} 字符"
                 f"｜回答 {r.get('response_chars',0):,} 字符\n")
        atts = r.get("attempts") or []
        if atts:
            A.append("**尝试明细**\n")
            A.append("| 第几次 | 状态 | 耗时(s) | 回答字符数 | 失败原因 |")
            A.append("|---|---|---|---|---|")
            for a in atts:
                A.append(f"| {a.get('n')} | {runlog.STATUS_LABEL.get(a.get('status'), a.get('status'))} "
                         f"| {a.get('elapsed')} | {a.get('response_chars')} "
                         f"| {(a.get('reason') or '').replace('|','/') or '—'} |")
            A.append("")
        A.append("### 发给 Hy3 的完整提示词\n")
        A.append(_fence(r.get("prompt", "")))
        A.append("\n### Hy3 原始回答全文\n")
        raw = r.get("raw_response") or ""
        A.append(_fence(raw) if raw.strip() else "_（无有效回答：该题所有尝试均失败，详见上方尝试明细）_")
        A.append("\n---")

    out = os.path.join(LOG_DIR, "hy3_原始回答日志.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(A) + "\n")
    return out, len(rows), ok, len(fails)


def _check_consistency(rows):
    """校验「步骤判定 ⟺ 总体判定」不变量，违规明细写入日志头部，便于随时复核。"""
    bad = []
    for r in rows:
        v = r.get("verdict") or {}
        steps = {s.get("step"): s.get("ok") for s in (r.get("step_verdicts") or [])}
        if not steps:
            bad.append((r["problem_id"], "缺少步骤判定数据"))
        elif v.get("process_valid") is False:
            if all(steps.values()):
                bad.append((r["problem_id"], "全部步骤通过却判定过程不成立"))
            elif v.get("error_step") not in steps:
                bad.append((r["problem_id"], "error_step 不在步骤集合内"))
            elif steps.get(v.get("error_step")) is True:
                bad.append((r["problem_id"], "error_step 指向的步骤仍标记通过"))
        elif not all(steps.values()):
            bad.append((r["problem_id"], "判定过程成立但存在未通过步骤"))
    return bad


def render_eval_log(problems):
    rows = _latest_per_problem(runlog.read_jsonl(runlog.EVAL_TRACE))
    rows = [r for r in rows if r.get("problem_id") in problems]
    rows.sort(key=lambda r: (DIFF_ORDER.get(r.get("difficulty"), 9), r.get("problem_id") or ""))

    n = len(rows)
    final_ok = sum(1 for r in rows if (r.get("verdict") or {}).get("final_correct"))
    proc_ok = sum(1 for r in rows if (r.get("verdict") or {}).get("process_valid"))
    lucky = [r for r in rows if (r.get("verdict") or {}).get("final_correct")
             and not (r.get("verdict") or {}).get("process_valid")]
    et = Counter((r.get("verdict") or {}).get("error_type_name")
                 for r in rows if (r.get("verdict") or {}).get("process_valid") is False)
    es = Counter((r.get("verdict") or {}).get("error_step")
                 for r in rows if (r.get("verdict") or {}).get("process_valid") is False)
    vd = Counter()
    for r in rows:
        for c in r.get("case_verdicts") or []:
            vd[c.get("verdict")] += 1
    bad = _check_consistency(rows)

    A = []
    A.append("# 过程评估判定日志（全保留）\n")
    A.append("> 本日志完整留存判定过程：**逐用例 verdict**（期望/实际/异常）、"
             "**四步骤逐级判定**、**错误归因**、**差分压力测试**，以及被评估的模型原始回答。\n")
    A.append(f"> 覆盖 **{n} / {len(problems)}** 题｜后端 rule（沙盒 ERV + 规则判定）\n")

    A.append("\n## 零、统计概览\n")
    A.append("| 指标 | 数值 |")
    A.append("|---|---|")
    A.append(f"| 已判定题数 | {n} |")
    if n:
        A.append(f"| 答案正确率 | {final_ok}/{n} = {final_ok/n:.1%} |")
        A.append(f"| 过程正确率 | {proc_ok}/{n} = {proc_ok/n:.1%} |")
        A.append(f"| 答案对但过程错 | {len(lucky)} 题（{len(lucky)/n:.1%}） |")
    A.append(f"| 主测试集用例 verdict 分布 | " +
             "，".join(f"{k} {v}" for k, v in vd.most_common()) + " |")
    A.append("")
    if et:
        A.append("**错误类型分布**（过程不成立的题）：\n")
        A.append("| 错误类型 | 题数 |")
        A.append("|---|---|")
        for k, v in et.most_common():
            A.append(f"| {k} | {v} |")
        A.append("")
        A.append("**错误步骤分布**：\n")
        A.append("| 步骤 | 名称 | 题数 |")
        A.append("|---|---|---|")
        for k, v in sorted(es.items(), key=lambda kv: (kv[0] is None, kv[0])):
            A.append(f"| step {k} | {STEP_NAMES.get(k, '—')} | {v} |")
        A.append("")
    A.append("**判定一致性自检**（不变量：过程不成立 ⟺ 至少一步不通过，且 error_step 落在该步）：\n")
    A.append(f"- 违规记录：**{len(bad)}** 条" + ("　✅ 全部通过" if not bad else ""))
    for pid, why in bad[:20]:
        A.append(f"  - {pid}：{why}")
    A.append("")
    A.append("\n## 一、目录\n")
    A.append(_toc(rows, lambda r: f"{r['problem_id']} {r.get('title','')}"))
    A.append("\n---\n")

    cur = None
    for r in rows:
        if r.get("difficulty") != cur:
            cur = r.get("difficulty")
            A.append(f"\n# 难度：{cur}\n")
        v = r.get("verdict") or {}
        pid = r["problem_id"]
        A.append(f"\n## {pid} {r.get('title','')}\n")
        A.append(f"- 领域：{r.get('domain','')}｜难度：{r.get('difficulty','')}"
                 f"｜判定后端：{v.get('backend','')}｜判定耗时 {v.get('eval_sec')}s｜记录时间：{r.get('ts','')}")
        A.append(f"- **最终答案**：{'✅ 正确' if v.get('final_correct') else '❌ 错误'}"
                 f"（{v.get('passed_cases')}/{v.get('total_cases')} 用例通过"
                 f"｜{v.get('verdict_summary','')}）")
        A.append(f"- **过程判定**：{'✅ 成立' if v.get('process_valid') else '❌ 不成立'}"
                 + ("" if v.get("process_valid") else
                    f"，错误定位 **step {v.get('error_step')} {STEP_NAMES.get(v.get('error_step'),'')}**"
                    f"，类型 **{v.get('error_type_name') or v.get('error_type')}**"))
        A.append(f"- 判定说明：{v.get('note','')}\n")

        cases = r.get("case_verdicts") or []
        if cases:
            A.append("**主测试集逐用例明细**\n")
            A.append("| # | verdict | 期望输出 | 实际输出 | 异常 |")
            A.append("|---|---|---|---|---|")
            for c in cases:
                exp = str(c.get("expected", "")).replace("|", "/").replace("\n", " ")[:80]
                act = str(c.get("actual", "")).replace("|", "/").replace("\n", " ")[:80]
                exc = str(c.get("exception", "")).replace("|", "/")[:60] or "—"
                A.append(f"| {c.get('index',0)+1} | **{c.get('verdict')}** | `{exp}` | `{act}` | {exc} |")
            A.append("")
        scases = r.get("stress_case_verdicts") or []
        if scases:
            A.append(f"**差分压力测试**（{r.get('stress_summary','')}）\n")
            A.append("| # | verdict | 参考解 | 待测解 | 异常 |")
            A.append("|---|---|---|---|---|")
            for c in scases:
                exp = str(c.get("expected", "")).replace("|", "/").replace("\n", " ")[:80]
                act = str(c.get("actual", "")).replace("|", "/").replace("\n", " ")[:80]
                exc = str(c.get("exception", "")).replace("|", "/")[:60] or "—"
                A.append(f"| {c.get('index',0)+1} | **{c.get('verdict')}** | `{exp}` | `{act}` | {exc} |")
            A.append("")
        steps = r.get("step_verdicts") or []
        if steps:
            A.append("**四步骤逐级判定**\n")
            A.append("| 步骤 | 名称 | 判定 | 依据 |")
            A.append("|---|---|---|---|")
            for s in steps:
                A.append(f"| step {s.get('step')} | {s.get('name')} | "
                         f"{'✅ 通过' if s.get('ok') else '❌ 不通过'} | "
                         f"{str(s.get('reason','')).replace('|','/')} |")
            A.append("")
        ctx = r.get("problem_context") or {}
        if ctx.get("constraints"):
            A.append(f"**题目约束**：{str(ctx['constraints']).replace(chr(10),' ')[:200]}\n")
        A.append("### 被评估的 Hy3 原始回答\n")
        raw = r.get("raw_solution") or ""
        A.append(_fence(raw) if raw.strip() else "_（无）_")
        A.append("\n---")

    out = os.path.join(LOG_DIR, "过程评估判定日志.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(A) + "\n")
    return out, n, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-backfill", action="store_true")
    ap.add_argument("--render-only", action="store_true")
    args = ap.parse_args()

    problems = load_problems_map()
    if not args.no_backfill and not args.render_only:
        backfill(problems)

    s_out, s_n, s_ok, s_fail = render_solve_log(problems)
    e_out, e_n, bad = render_eval_log(problems)

    for p, n in ((s_out, s_n), (e_out, e_n)):
        print(f"生成 {os.path.relpath(p)}（{n} 题，{os.path.getsize(p)/1024/1024:.2f} MB）")
    print(f"求解日志：成功 {s_ok}｜未完成 {s_fail}")
    print(f"评估日志：判定一致性违规 {len(bad)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
