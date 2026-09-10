# -*- coding: utf-8 -*-
"""把「由会话内助手撰写」的解答导入跑批缓存与日志。

背景：外部模型（Hy3/hy4-preview/glm-5.3-flash）额度耗尽后，剩余题目改由本会话的助手
直接撰写解答。这类解答与 API 产出的解答在**性质上不同**——同一个会话、可以反复修改，
因此必须逐题标注来源，否则交付物里「513 题的指标」会掩盖「其中一部分并非来自被测
模型」这一事实，指标含义会被根本性误读。

本脚本只做导入与格式校验，不做任何改写：
  - 校验解答是否含四段式结构与可执行代码块（不合规则拒绝导入，避免污染评估器输入）
  - 追加到 eval/results/hy3_solutions.jsonl（断点续跑缓存）
  - 同步写 eval/logs/solve_trace.jsonl（全量日志），model 字段标为 --model
  - elapsed 记为 null：非 API 调用，没有可比的生成耗时，不得混入耗时统计

用法：
  python tools/import_inline_solutions.py solutions.jsonl --model assistant-inline
  python tools/import_inline_solutions.py solutions.jsonl --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

from src import runlog  # noqa: E402
from src.problems import load_problems  # noqa: E402
from src.solver import build_prompt, parse_solution  # noqa: E402

RES_DIR = os.path.join(ROOT, "eval", "results")
SOL_CACHE = os.path.join(RES_DIR, "hy3_solutions.jsonl")

SECTIONS = ("思路", "复杂度", "边界", "代码")


def read_jsonl(path):
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
                continue
    return out


def validate(pid: str, raw: str) -> list:
    """返回问题清单（空表示通过）。"""
    problems = []
    for name in SECTIONS:
        if not re.search(rf"^#+\s*.*{name}", raw, re.M):
            problems.append(f"缺少「{name}」章节")
    sol = parse_solution(raw)
    if not sol.code.strip():
        problems.append("缺少可执行代码块")
    else:
        if "```" in sol.code:
            problems.append("代码块内嵌套 ``` 会截断解析")
        try:
            compile(sol.code, f"<{pid}>", "exec")
        except SyntaxError as e:
            problems.append(f"代码语法错误：{e.msg} (line {e.lineno})")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="待导入的 jsonl（每行 {problem_id, raw}）")
    ap.add_argument("--model", default="assistant-inline",
                    help="写入缓存/日志的模型标识，务必如实标注来源")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="覆盖缓存中已有的同题号解答（用于修正先前导入的错误解答）")
    args = ap.parse_args()

    problems = {p.id: p for p in load_problems(os.path.join(ROOT, "data", "problems.json"))}
    already = {r["problem_id"] for r in read_jsonl(SOL_CACHE) if (r.get("raw") or "").strip()}

    rows = read_jsonl(args.src)
    print(f"待导入 {len(rows)} 条（缓存已有 {len(already)} 题）")

    ok, skipped, bad = [], [], []
    for r in rows:
        pid, raw = r.get("problem_id"), (r.get("raw") or "")
        if pid not in problems:
            bad.append((pid, ["题号不在题库中"]))
            continue
        if pid in already and not args.force:
            skipped.append(pid)
            continue
        errs = validate(pid, raw)
        (bad if errs else ok).append((pid, errs) if errs else pid)

    if bad:
        print(f"\n✗ {len(bad)} 条未通过校验，已拒绝导入：")
        for pid, errs in bad[:20]:
            print(f"   {pid}: {'; '.join(errs)}")
    if skipped:
        print(f"⊘ 跳过已缓存 {len(skipped)} 题：{' '.join(skipped[:20])}")

    print(f"\n可导入 {len(ok)} 条")
    if args.dry_run or not ok:
        return 1 if bad else 0

    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    by_id = {r["problem_id"]: r for r in rows}

    if args.force:
        # 覆盖模式：重写缓存，用新解答替换同题号的旧记录（保持顺序稳定）
        fixed = {pid: by_id[pid]["raw"] for pid in ok}
        kept = []
        for r in read_jsonl(SOL_CACHE):
            pid = r.get("problem_id")
            if pid in fixed:
                r = dict(r)
                r["raw"] = fixed[pid]
                r["model"] = args.model
                r["inline"] = True
                r["ts"] = ts
            kept.append(r)
        with open(SOL_CACHE, "w", encoding="utf-8") as f:
            for r in kept:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"✓ 已覆盖 {len(fixed)} 条（缓存总 {len(kept)} 条）")
    else:
        with open(SOL_CACHE, "a", encoding="utf-8") as f:
            for pid in ok:
                f.write(json.dumps({
                    "problem_id": pid, "raw": by_id[pid]["raw"], "elapsed": None,
                    "attempts": 1, "ts": ts, "model": args.model,
                    "inline": True,
                }, ensure_ascii=False) + "\n")
                f.flush()
        print(f"✓ 已导入 {len(ok)} 条 -> {os.path.relpath(SOL_CACHE)}")

    # 日志一律追加（保留修订历史，不覆盖既有记录）
    for pid in ok:
        raw = by_id[pid]["raw"]
        p = problems[pid]
        runlog.log_solve(
            p, build_prompt(p),
            [{"n": 1, "status": "ok",
              "reason": "由会话内助手直接撰写（未调用外部 API）"
                        + ("，本次为修订版" if args.force else ""),
              "elapsed": None, "response_chars": len(raw),
              "response_head": raw[:200]}],
            "ok", raw, model=args.model, inline=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
