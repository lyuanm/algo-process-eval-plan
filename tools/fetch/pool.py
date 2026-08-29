# -*- coding: utf-8 -*-
"""规模化抓取（两阶段）：从 LeetCode 官方 API 建立 500 题真实题库池。

阶段一（detail）：抓题目详情（tags → 域、样例、中文题面）→ 存 pool.json
阶段二（solution）：分桶选出目标题后，为缺失 solution_code 的题抓官方题解

断点续跑：已完成的工作跳过（按 slug 缓存）。

运行：
  python tools/fetch/pool.py                        # 两阶段全跑
  python tools/fetch/pool.py --detail-only          # 只跑阶段一
  python tools/fetch/pool.py --solution-only        # 只跑阶段二
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.fetch.leetcode_api import LeetCodeCN
from tools.fetch.convert import parse_meta, parse_example_inputs

POOL_PATH = os.path.join(ROOT, "data", "fetch_cache", "pool.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0"

# LeetCode topicTags → 题库域（优先级从高到低）
DOMAIN_RULES = [
    ("动态规划", {"dynamic-programming", "memoization", "state-compression"}),
    ("树", {"tree", "binary-tree", "binary-search-tree", "n-ary-tree", "segment-tree",
            "binary-indexed-tree", "avl-tree"}),
    ("图", {"graph", "depth-first-search", "breadth-first-search", "union-find",
            "topological-sort", "minimum-spanning-tree", "shortest-path",
            "strongly-connected-component", "graph-theory", "network-flow"}),
    ("二分查找", {"binary-search"}),
    ("双指针/滑动窗口", {"two-pointers", "sliding-window"}),
    ("链表", {"linked-list"}),
    ("栈/队列", {"stack", "queue", "monotonic-stack", "monotonic-queue"}),
    ("堆/贪心", {"heap-priority-queue", "greedy", "game-theory"}),
    ("回溯/位运算", {"backtracking", "bit-manipulation", "enumeration"}),
    ("字符串", {"string", "string-matching", "rolling-hash", "suffix-array", "trie"}),
    ("数学", {"math", "number-theory", "geometry", "combinatorics",
              "probability-and-statistics", "randomized"}),
    ("数组/哈希", {"array", "hash-table", "prefix-sum", "simulation", "sorting",
                  "counting", "matrix", "iterator"}),
]


def domain_of(tags):
    ts = set(tags)
    for name, keys in DOMAIN_RULES:
        if ts & keys:
            return name
    return "数组/哈希"


def fetch_all_questions():
    req = urllib.request.Request("https://leetcode.cn/api/problems/all/",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    probs = []
    for p in data["stat_status_pairs"]:
        s = p["stat"]
        probs.append({
            "slug": s["question__title_slug"],
            "id": str(s["frontend_question_id"]),
            "difficulty": {1: "easy", 2: "medium", 3: "hard"}.get(p["difficulty"]["level"], "easy"),
            "paid": bool(p["paid_only"]),
            "acRate": s["total_acs"] / max(1, s["total_submitted"]),
        })
    return probs


def load_pool():
    if os.path.exists(POOL_PATH):
        with open(POOL_PATH, "r", encoding="utf-8") as f:
            return {p["slug"]: p for p in json.load(f)}
    return {}


def save_pool(pool):
    with open(POOL_PATH, "w", encoding="utf-8") as f:
        json.dump(list(pool.values()), f, ensure_ascii=False, indent=1)


def stage_detail(api, pool, limits):
    """阶段一：抓题目详情（tags/样例/题面）。"""
    print("拉取全部题目列表...")
    all_q = fetch_all_questions()
    free = [p for p in all_q if not p["paid"]]
    print(f"总题 {len(all_q)}，免费 {len(free)}")
    n_ok = n_skip = n_miss = 0
    t0 = time.time()
    for diff in ("easy", "medium", "hard"):
        cand = sorted([p for p in free if p["difficulty"] == diff],
                      key=lambda x: -x["acRate"])[:limits[diff]]
        print(f"===== {diff}: 候选 {len(cand)} 题 =====")
        for p in cand:
            slug = p["slug"]
            if slug in pool:
                n_skip += 1
                continue
            try:
                q = api.get_question(slug)
                if not q or q.get("isPaidOnly"):
                    n_miss += 1
                    continue
                tags = [t["slug"] for t in q.get("topicTags", [])]
                pool[slug] = {
                    "slug": slug,
                    "id": p["id"],
                    "title": q["title"],
                    "title_zh": q.get("translatedTitle", ""),
                    "difficulty": diff,
                    "acRate": round(p["acRate"], 4),
                    "tags": tags,
                    "domain": domain_of(tags),
                    "meta": q["metaData"],
                    "content": q.get("content", ""),
                    "translated_content": q.get("translatedContent", ""),
                    "example_testcases": q.get("exampleTestcases", ""),
                }
                n_ok += 1
                if n_ok % 50 == 0:
                    print(f"  ...阶段一已抓 {n_ok} 题，耗时 {time.time()-t0:.0f}s")
                    save_pool(pool)
            except Exception as e:
                n_miss += 1
        save_pool(pool)
    print(f"阶段一完成：新增 {n_ok}，跳过 {n_skip}，缺失 {n_miss}，池共 {len(pool)} 题")


def stage_solution(api, pool):
    """阶段二：按桶抓官方题解，每桶目标 TARGET_PER_BUCKET 题。"""
    BUCKET_TARGET = 25
    MAX_TRY_PER_BUCKET = 250
    buckets = defaultdict(list)
    for rec in pool.values():
        buckets[(rec["domain"], rec["difficulty"])].append(rec)

    t0 = time.time()
    n_ok_total = n_miss = 0
    for (dom, diff), lst in buckets.items():
        lst.sort(key=lambda r: -r.get("acRate", 0))
        # 已成功数
        ok = [r for r in lst if r.get("solution_code")]
        if len(ok) >= BUCKET_TARGET:
            continue
        tried = 0
        for rec in lst:
            if len(ok) >= BUCKET_TARGET:
                break
            if rec.get("solution_code"):
                continue  # 已计入 ok，无需重复
            tried += 1
            if tried > MAX_TRY_PER_BUCKET:
                break
            slug = rec["slug"]
            try:
                art_title, codes, art_slug = api.get_official_python(slug)
                if not codes:
                    n_miss += 1
                    continue
                rec["solution_code"] = codes[0]
                rec["solution_title"] = art_title or ""
                rec["solution_slug"] = art_slug or ""
                ok.append(rec)
                n_ok_total += 1
                if n_ok_total % 20 == 0:
                    print(f"  ...阶段二已抓 {n_ok_total} 题，耗时 {time.time()-t0:.0f}s", flush=True)
                    save_pool(pool)
            except Exception as e:
                n_miss += 1
        save_pool(pool)
        print(f"  桶 {dom}/{diff}: {len(ok)}/{BUCKET_TARGET} 题（候选 {len(lst)}）", flush=True)

    save_pool(pool)
    has = [r for r in pool.values() if r.get("solution_code")]
    c = Counter((r["domain"], r["difficulty"]) for r in has)
    print(f"阶段二完成：新增 {n_ok_total}，无题解 {n_miss}，含题解总数 {len(has)}")
    for k in sorted(c):
        print(" ", k, c[k], flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-easy", type=int, default=900)
    ap.add_argument("--limit-medium", type=int, default=900)
    ap.add_argument("--limit-hard", type=int, default=900)
    ap.add_argument("--detail-only", action="store_true")
    ap.add_argument("--solution-only", action="store_true")
    args = ap.parse_args()
    limits = {"easy": args.limit_easy, "medium": args.limit_medium, "hard": args.limit_hard}

    pool = load_pool()
    print(f"现有池: {len(pool)} 题")
    api = LeetCodeCN(delay=0.5)
    if not args.solution_only:
        stage_detail(api, pool, limits)
    if not args.detail_only:
        stage_solution(api, pool)


if __name__ == "__main__":
    main()
