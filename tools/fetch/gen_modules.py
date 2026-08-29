# -*- coding: utf-8 -*-
"""从 pool.json 生成 12 域 × 3 难度的 pbank 模块（每桶 14 题 = 504 题），
并自动运行验证。

参考实现 = LeetCode 官方题解代码 + I/O 包装（见 tools/fetch/convert.py）。
"""
import json
import os
import re
import sys
import html as _html
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.fetch.convert import (
    parse_meta, build_reference_solution, pick_check_mode,
    parse_example_inputs, json_param_to_str,
)
from src.sandbox import run_code

POOL_PATH = os.path.join(ROOT, "data", "fetch_cache", "pool.json")
PBANK_DIR = os.path.join(ROOT, "tools", "pbank")
BUCKET_SIZE = 15

# 域英文名 → 文件前缀 / ID 前缀 / 中文名
DOMAINS = [
    ("arrays", "A", "数组/哈希"),
    ("strings", "S", "字符串"),
    ("binarysearch", "B", "二分查找"),
    ("pointers", "P", "双指针/滑动窗口"),
    ("linkedlist", "L", "链表"),
    ("math", "M", "数学"),
    ("tree", "T", "树"),
    ("graph", "G", "图"),
    ("dp", "D", "动态规划"),
    ("heapgreedy", "H", "堆/贪心"),
    ("stackqueue", "K", "栈/队列"),
    ("backtrackbit", "X", "回溯/位运算"),
]
DIFF_SUFFIX = {"easy": "E", "medium": "M", "hard": "H"}


def html_to_text(h: str) -> str:
    if not h:
        return ""
    h = h.replace("<br/>", "\n").replace("<br>", "\n").replace("</p>", "\n").replace("</li>", "\n")
    h = re.sub(r'<pre>.*?</pre>', lambda m: "```\n" + _html.unescape(re.sub(r"<[^>]+>", "", m.group(0))).strip() + "\n```", h, flags=re.S)
    h = re.sub(r"<[^>]+>", "", h)
    h = _html.unescape(h)
    h = re.sub(r"[ \t]+\n", "\n", h)
    h = re.sub(r"\n{3,}", "\n\n", h)
    return h.strip()


def extract_constraints(text: str) -> str:
    """从题面纯文本中提取 Constraints 段。"""
    m = re.search(r"(?:Constraints|约束)\s*:\s*(.+)", text, re.S)
    if m:
        seg = m.group(1).strip()
        seg = re.split(r"\n\n", seg)[0]
        return seg[:800]
    return ""


def fmt_input_output(meta) -> tuple:
    """根据 metaData 生成输入/输出格式说明。"""
    params = meta.get("params", [])
    names = [p["name"] for p in params]
    ret = (meta.get("return") or {}).get("type", "integer")
    ifmt = "每行一个参数（JSON 格式），依次为：" + "、".join(names) + "。"
    ofmt = f"输出 {ret} 类型结果（JSON 序列化）。"
    return ifmt, ofmt


def build_problem(rec: dict, pid: str, domain_zh: str) -> dict:
    meta = parse_meta(rec["meta"])
    ref = build_reference_solution(meta, rec["solution_code"])
    test_cases = []
    if meta.get("classname"):
        # 设计类题：官方样例为「操作数组行 + 参数数组行」，整段作为输入
        for seg in [s for s in rec.get("example_testcases", "").strip().split("\n\n") if s.strip()]:
            res = run_code(ref, seg, timeout=10.0)
            if not res.ok:
                print(f"  !! {pid} 参考实现运行失败: {res.stderr[:120]}")
                continue
            test_cases.append({"input": seg, "expected": res.stdout.strip()})
    else:
        groups = parse_example_inputs(rec.get("example_testcases", ""), len(meta.get("params", [])))
        for g in groups:
            inp = "\n".join(json_param_to_str(v) for v in g)
            res = run_code(ref, inp, timeout=10.0)
            if not res.ok:
                print(f"  !! {pid} 参考实现运行失败: {res.stderr[:120]}")
                continue
            test_cases.append({"input": inp, "expected": res.stdout.strip()})
    if not test_cases:
        raise RuntimeError("参考实现无法通过官方样例")
    desc = html_to_text(rec.get("translated_content") or rec.get("content") or "")
    cons = extract_constraints(desc)
    ifmt, ofmt = fmt_input_output(meta)
    tags = [t for t in rec.get("tags", [])] + [domain_zh]
    return {
        "id": pid,
        "title": rec.get("title_zh") or rec["title"],
        "source": f"LeetCode {rec['id']}",
        "difficulty": rec["difficulty"],
        "domain": domain_zh,
        "description": desc,
        "input_format": ifmt,
        "output_format": ofmt,
        "constraints": cons,
        "reference_solution": ref,
        "checker_src": "",
        "check_mode": pick_check_mode(meta),
        "test_cases": test_cases,
        "tags": tags,
        "stress_inputs": [],
        "solution_url": f"https://leetcode.cn/problems/{rec['slug']}/solution/{rec.get('solution_slug', '')}/",
        "problem_url": f"https://leetcode.cn/problems/{rec['slug']}/",
    }


def main():
    with open(POOL_PATH, "r", encoding="utf-8") as f:
        pool = json.load(f)
    print(f"池共 {len(pool)} 题")

    # 分桶（仅含有官方题解的题）
    buckets = defaultdict(list)
    for rec in pool:
        if rec.get("solution_code"):
            buckets[(rec["domain"], rec["difficulty"])].append(rec)
    for k in buckets:
        buckets[k].sort(key=lambda r: -r.get("acRate", 0))

    # 分配：桶内按序尝试 build（带 build_ok 缓存），取前 BUCKET_SIZE 个可构建成功的题
    chosen = {}
    tried = 0
    for (dom, diff), lst in buckets.items():
        ok_list = []
        for rec in lst:
            if len(ok_list) >= BUCKET_SIZE:
                break
            if rec.get("build_ok"):
                ok_list.append(rec)
                continue
            if rec.get("build_fail"):
                continue
            tried += 1
            try:
                build_problem(rec, "", dom)
                rec["build_ok"] = True
                ok_list.append(rec)
            except Exception as e:
                rec["build_fail"] = str(e)[:100]
        chosen[(dom, diff)] = ok_list
    with open(POOL_PATH, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=1)
    print(f"构建尝试 {tried} 题（结果已缓存）")

    # 统计每域每难度可选题数与缺口
    print("===== 分桶统计（含官方题解） =====")
    total = 0
    missing_buckets = []
    for dom_en, pref, dom_zh in DOMAINS:
        row = []
        for diff, suf in DIFF_SUFFIX.items():
            n = len(buckets.get((dom_zh, diff), []))
            nsel = len(chosen.get((dom_zh, diff), []))
            if nsel < BUCKET_SIZE:
                missing_buckets.append((dom_en, dom_zh, diff, nsel, n))
            row.append(f"{diff}:{nsel}/{n}")
            total += nsel
        print(f"  {dom_en:12} " + " ".join(row))
    print(f"计划生成 {total} 题")
    if missing_buckets:
        print("缺口桶（目标 14）：")
        for dom_en, dom_zh, diff, nsel, n in missing_buckets:
            print(f"  - {dom_zh} {diff}: 仅 {nsel}/14（池内 {n} 题）")

    # 生成模块文件
    os.makedirs(PBANK_DIR, exist_ok=True)
    generated = 0
    for dom_en, pref, dom_zh in DOMAINS:
        for diff, suf in DIFF_SUFFIX.items():
            items = chosen.get((dom_zh, diff), [])
            # 先构建成功题列表（跳过无法处理的题）
            built = []
            for rec in items:
                try:
                    p = build_problem(rec, "", dom_zh)
                    p["_rec"] = rec
                    built.append(p)
                except Exception as e:
                    print(f"  !! 跳过 {rec['slug']}: {str(e)[:80]}")
            lines = []
            lines.append("# -*- coding: utf-8 -*-")
            lines.append(f'"""LeetCode 官方题解真实题目（{dom_zh} · {diff}，{len(built)} 题）。')
            lines.append("题目与答案均来自 LeetCode 官方（题目 API + 官方题解文章）。")
            lines.append('"""')
            lines.append("from ._base import mk\n")
            ok_ids = []
            for i, p in enumerate(built, 1):
                pid = f"{pref}{suf}{i:02d}"
                p["id"] = pid
                rec = p.pop("_rec")
                tests = [(t["input"], t["expected"]) for t in p["test_cases"]]
                lines.append(f'P{pid.upper()} = mk(')
                lines.append(f'    {json.dumps(p["id"])},')
                lines.append(f'    {json.dumps(p["title"])},')
                lines.append(f'    {json.dumps(p["source"])},')
                lines.append(f'    {json.dumps(p["difficulty"])},')
                lines.append(f'    {json.dumps(p["domain"])},')
                lines.append(f'    {json.dumps(p["description"])},')
                lines.append(f'    {json.dumps(p["input_format"])},')
                lines.append(f'    {json.dumps(p["output_format"])},')
                lines.append(f'    {json.dumps(p["constraints"])},')
                lines.append(f'    {json.dumps(p["reference_solution"])},')
                lines.append(f'    {json.dumps(p["check_mode"])},')
                lines.append(f'    {json.dumps(tests)},')
                lines.append(f'    {json.dumps(p["tags"])},')
                lines.append('    )')
                lines.append(f'P{pid.upper()}["solution_url"] = {json.dumps(p["solution_url"])}')
                lines.append(f'P{pid.upper()}["problem_url"] = {json.dumps(p["problem_url"])}')
                lines.append("")
                ok_ids.append(pid.upper())
                generated += 1
            fname = f"{dom_en}_{diff}.py"
            lines.append(f"PROBLEMS = [{', '.join('P' + i for i in ok_ids)}]")
            with open(os.path.join(PBANK_DIR, fname), "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"  写入 {fname} ({len(built)} 题)")
    print(f"共生成 {generated} 题")


if __name__ == "__main__":
    main()
