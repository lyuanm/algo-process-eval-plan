# -*- coding: utf-8 -*-
"""对导入的「会话内助手解答」跑一遍沙盒 ERV，报告逐题通过情况。

用途：这些解答是人工撰写的，必须先由沙盒客观判定对错，再交给过程评估器；
本工具只做执行验证（不写正式缓存），便于在批量导入后快速定位错误解答并修正。

用法：
  python tools/verify_inline.py                      # 校验全部 inline 解答
  python tools/verify_inline.py --batch eval/inline_solutions/batch04.jsonl
  python tools/verify_inline.py --ids TE12 TE05      # 指定题号
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)

from src.problems import load_problems  # noqa: E402
from src.solver import parse_solution  # noqa: E402
from src.verdict import execution_verdict  # noqa: E402

RES_DIR = os.path.join(ROOT, "eval", "results")
SOL_CACHE = os.path.join(RES_DIR, "hy3_solutions.jsonl")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=None, help="只校验该 jsonl 中列出的题号")
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--timeout", type=float, default=8.0)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    problems = {p.id: p for p in load_problems(os.path.join(ROOT, "data", "problems.json"))}
    rows = read_jsonl(SOL_CACHE)

    if args.ids:
        want = set(args.ids)
    elif args.batch:
        want = {r["problem_id"] for r in read_jsonl(args.batch)}
    else:
        want = {r["problem_id"] for r in rows if r.get("inline")}

    raw_map = {r["problem_id"]: r.get("raw", "") for r in rows}

    def chk(pid):
        try:
            code = parse_solution(raw_map[pid]).code
            ev = execution_verdict(problems[pid], code, timeout=args.timeout)
            return pid, ev.final_correct, ev.summary, ev.first_failure
        except Exception as e:  # pragma: no cover
            return pid, False, f"{type(e).__name__}", None

    todo = sorted(p for p in want if p in raw_map)
    t0 = time.time()
    ok = 0
    fails = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for pid, good, summary, ff in ex.map(chk, todo):
            if good:
                ok += 1
                continue
            detail = ""
            if ff is not None:
                detail = f" | 用例#{ff.index + 1} {ff.verdict} 期望={ff.expected!r} 实际={ff.actual!r} {ff.exception}"
            fails.append(pid)
            print(f"✗ {pid:6} {summary}{detail}")

    print(f"\n通过 {ok}/{len(todo)}  失败 {len(fails)}  耗时 {time.time()-t0:.1f}s")
    if fails:
        print("失败题号:", " ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
