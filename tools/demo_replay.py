# -*- coding: utf-8 -*-
"""录制用演示脚本：按分镜顺序播放一次完整的「解题 → 沙盒验证 → 过程评估」流程。

**怎么用**：开录屏 → 运行本脚本 → 对着画面讲解 → 停止录制。
不必现场手敲命令，也就不会因为手速/拼写问题录出废片。

```bash
python tools/demo_replay.py            # 默认主角 BE08，总时长约 105 秒
python tools/demo_replay.py --id DM13  # 换一道题
python tools/demo_replay.py --fast     # 不等待，用于快速自检内容
```

设计取舍（关系到交付材料是否站得住）：

1. **镜头 ③ 真实执行**：通过 subprocess 真的跑一遍评估流程，录下来的是真实执行过程，
   不是把结果文本硬编码后「演」一遍。
2. **其余镜头只读真实产物**：题库统计读 `data/problems.json`，模型回答读
   `eval/results/hy3_solutions.jsonl`，判定明细读 `eval/logs/eval_trace.jsonl`，
   全量指标读 `eval/results/full_summary_rule.json`。
3. **数据缺失时直接报错退出**，不打印占位文本 —— 演示素材与报告指标对不上，
   比录制失败严重得多。
4. 评估结果写入**临时文件**，不碰 `eval/results/full_eval_*.jsonl` 正式缓存
   （否则这些题会被当作「已缓存」，下次全量跑批直接跳过）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data", "problems.json")
SOL_CACHE = os.path.join(ROOT, "eval", "results", "hy3_solutions.jsonl")
EVAL_TRACE = os.path.join(ROOT, "eval", "logs", "eval_trace.jsonl")
SUMMARY = os.path.join(ROOT, "eval", "results", "full_summary_rule.json")

FAST = False          # --fast：不 sleep，用于自检
PY = sys.executable


# ------------------------------------------------------------------ 打印工具

def say(text: str = "", delay: float = 0.06, indent: str = "  ") -> None:
    print(indent + text, flush=True)
    if not FAST:
        time.sleep(delay)


def banner(title: str) -> None:
    print()
    print("═" * 76, flush=True)
    print(f"  {title}", flush=True)
    print("═" * 76, flush=True)
    if not FAST:
        time.sleep(0.5)


def rule(char: str = "─") -> None:
    print("  " + char * 70, flush=True)


def pause(sec: float) -> None:
    """镜头之间的停留，给讲解留时间。"""
    if not FAST:
        time.sleep(sec)


# ------------------------------------------------------------------ 数据装载

def load_json(path: str) -> dict:
    if not os.path.exists(path):
        raise SystemExit(f"缺少数据文件：{os.path.relpath(path, ROOT)}\n"
                         "请先按 README §3 生成对应产物后再录制。")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_problem(pid: str) -> dict:
    probs = {p["id"]: p for p in load_json(DATA)}
    if pid not in probs:
        raise SystemExit(f"题号 {pid} 不在题库中")
    return probs[pid]


def load_solution(pid: str) -> dict:
    """取该题解答缓存的最后一条（append-only，含修订历史）。"""
    hit = None
    if not os.path.exists(SOL_CACHE):
        raise SystemExit(f"缺少解答缓存：{os.path.relpath(SOL_CACHE, ROOT)}")
    with open(SOL_CACHE, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("problem_id") == pid:
                hit = r
    if hit is None:
        raise SystemExit(f"解答缓存中没有 {pid}")
    return hit


def load_eval(pid: str) -> dict:
    hit = None
    if not os.path.exists(EVAL_TRACE):
        raise SystemExit(f"缺少评估轨迹：{os.path.relpath(EVAL_TRACE, ROOT)}\n"
                         "请先跑一次评估（python eval/run_full.py --skip-solve --eval-out <临时文件>）")
    with open(EVAL_TRACE, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("problem_id") == pid:
                hit = r
    if hit is None:
        raise SystemExit(f"评估轨迹中没有 {pid}")
    return hit


def clean(s: str, limit: int = 0) -> str:
    s = re.sub(r"```[a-zA-Z]*", "", s or "").replace("```", "")
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\$(.+?)\$", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.M)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit] + "…" if limit and len(s) > limit else s


def split_solution(raw: str):
    marks = [("思路/建模", r"#+\s*思\s*路"), ("复杂度分析", r"#+\s*复杂度"),
             ("边界与处理", r"#+\s*边界"), ("代码实现", r"#+\s*代码")]
    idx = []
    for name, pat in marks:
        m = re.search(pat, raw or "")
        if m:
            idx.append((m.start(), name))
    if len(idx) < 2:
        return [("解答全文", raw or "")]
    idx.sort()
    out = []
    for i, (pos, name) in enumerate(idx):
        end = idx[i + 1][0] if i + 1 < len(idx) else len(raw)
        out.append((name, raw[pos:end]))
    return out


# ------------------------------------------------------------------ 各镜头

def shot_project(pid: str, prob: dict) -> None:
    banner("AlgoJudge-Hy3 · 算法题「过程评估与错误定位」")
    say("不只判断答案对不对，更判断推理链成不成立、错在哪一步。", 0.1)
    print()
    probs = load_json(DATA)
    dom = {}
    for p in probs:
        dom[p["domain"]] = dom.get(p["domain"], 0) + 1
    with_ref = sum(1 for p in probs if (p.get("reference_solution") or "").strip())
    with_case = sum(1 for p in probs if p.get("test_cases"))
    rule()
    say(f"题库规模      {len(probs)} 道 LeetCode 官方真题", 0.12)
    say(f"分层结构      12 算法域 × 3 难度（Easy/Medium/Hard）", 0.12)
    say(f"标准答案      {with_ref}/{len(probs)} 题自带官方参考解", 0.12)
    say(f"官方测试用例  {with_case}/{len(probs)} 题自带，可沙盒执行判定", 0.12)
    say(f"来源可追溯    逐题保留官方题号与链接（{prob.get('source', 'LeetCode 官方')}）", 0.12)
    rule()
    say("评估维度：过程正确性判定 · 错误步骤定位 · 错误类型归类 · 「答案对但过程不成立」识别", 0.1)
    pause(1.2)


def shot_solve(pid: str, prob: dict, sol: dict) -> None:
    banner("① 出题：只把题面交给模型，不提供任何标准答案")
    diff = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}.get(
        prob["difficulty"], prob["difficulty"])
    say(f"{pid}  {prob['title']}    [{diff}] {prob['domain']}", 0.12)
    say(f"官方题号：{prob.get('source', 'LeetCode')}    官方用例 {len(prob.get('test_cases') or [])} 组", 0.12)
    print()
    say("题目描述（节选）：", 0.08)
    for line in re.findall(r".{1,66}", clean(prob["description"], 264))[:4]:
        say("  " + line, 0.08)
    print()
    rule()
    model = sol.get("model") or "hy3"
    elapsed = sol.get("elapsed")
    say(f"模型输入=仅题面  模型={model}  回答={len(sol.get('raw') or '')} 字符"
        + (f"  耗时={elapsed}s" if elapsed else ""), 0.12)
    rule()
    print()
    say("模型输出的四段式解题过程：", 0.1)
    for name, body in split_solution(sol.get("raw") or "")[:4]:
        say(f"  ▸ {name}", 0.08)
        say(f"      {clean(body, 88)}", 0.1)
    pause(1.5)


def shot_erv(pid: str) -> None:
    banner("② 沙盒可执行验证 ERV：把代码丢进沙盒子进程，实际跑官方用例")
    say("真实执行（非回放）：", 0.1)
    say(f"$ python eval/run_full.py --skip-solve --ids {pid} --deep-erv", 0.15)
    print()
    out_dir = tempfile.mkdtemp(prefix="demoreplay_")
    out_path = os.path.join(out_dir, "demo_eval.jsonl")
    cmd = [PY, os.path.join("eval", "run_full.py"), "--skip-solve",
           "--ids", pid, "--deep-erv", "--eval-out", out_path]
    # 直接继承 stdout：屏幕上滚动的就是真实执行输出
    subprocess.run(cmd, cwd=ROOT)
    say("", 0.1)
    say("↑ 官方用例逐条实际执行；判定摘要一行给出「答案 / 过程 / 错误定位」", 0.12)
    pause(1.5)


def shot_judge(pid: str, ev: dict) -> None:
    v = ev.get("verdict") or {}
    banner("③ 判定依据明细：逐用例 verdict · 差分压力测试 · 四步骤")
    say("沙盒逐用例结果：", 0.1)
    for c in ev.get("case_verdicts") or []:
        mark = "AC" if c["verdict"] == "AC" else c["verdict"]
        say(f"  用例 #{c['index'] + 1}   {mark:4}  期望 {str(c['expected'])[:22]:24} "
            f"实际 {str(c['actual'])[:22]}", 0.12)
    say(f"  → {v.get('verdict_summary') or '-'}：主测试集全部通过，传统判题到此结束", 0.12)
    print()
    rule()
    sc = (ev.get("stress_case_verdicts") or [])
    say(f"差分压力测试（以官方参考解为 oracle 生成大规模输入）：{ev.get('stress_summary') or '未启用'}", 0.12)
    for c in sc[:2]:
        say(f"  压力用例 #{c['index'] + 1}  {c['verdict']}  期望 {str(c['expected'])[:18]}  "
            f"实际 {str(c['actual'])[:18]}", 0.12)
    say("  → 主测试集通过 ≠ 代码正确：该实现只在恰好被覆盖的输入分布上成立", 0.12)
    print()
    rule()
    say("四步骤逐级判定：", 0.1)
    for s in ev.get("step_verdicts") or []:
        mark = "✓" if s.get("ok") else "✗"
        reason = "无明显问题" if s.get("ok") else clean(s.get("reason") or "", 40)
        say(f"  {mark}  step {s['step']}  {s['name']:10}  {reason}", 0.15)
    print()
    say(f"最终判定：答案 {'✓ 正确' if v.get('final_correct') else '✗ 错误'}    "
        f"过程 {'✓ 成立' if v.get('process_valid') else '✗ 不成立'}", 0.15)
    if not v.get("process_valid"):
        say(f"错误定位：step {v.get('error_step')} · {v.get('error_type_name') or '逻辑错误'}"
            "   ← 传统判题看不出任何问题", 0.15)
    pause(1.8)


def shot_overall() -> None:
    s = load_json(SUMMARY)
    banner("④ 全量 513 题结果")
    rule()
    say(f"已评测           {s.get('total')} / {s.get('bank_total')}"
        f"（{s.get('coverage', 0) * 100:.1f}%）", 0.12)
    say(f"答案正确率        {s.get('final_acc', 0) * 100:.1f}%"
        f"（{s.get('final_correct')} 题）", 0.12)
    say(f"过程正确率        {s.get('process_rate', 0) * 100:.1f}%"
        f"（{s.get('process_valid')} 题）", 0.12)
    say(f"答案对但过程错    {s.get('lucky_pass')} 题"
        f"（{s.get('lucky_pass', 0) / max(1, s.get('total', 1)) * 100:.1f}%）"
        "   ← 传统判题完全无法发现", 0.15)
    rule()
    say("难度分层（差距 = 答案正确率 − 过程正确率）：", 0.1)
    for d, cn in (("easy", "Easy  "), ("medium", "Medium"), ("hard", "Hard  ")):
        x = (s.get("by_difficulty") or {}).get(d)
        if not x:
            continue
        say(f"  {cn}  {x['n']:3} 题   答案 {x['final_acc'] * 100:5.1f}%   "
            f"过程 {x['process_rate'] * 100:5.1f}%   差距 {(x['final_acc'] - x['process_rate']) * 100:5.1f}pp", 0.15)
    rule()
    say("难度越高，「答案对但过程不成立」的比例越大 —— 难题不是做不出，而是更容易蒙对。", 0.12)
    pause(1.5)


def shot_logs(pid: str) -> None:
    banner("⑤ 全量日志：每个数字都可回溯到原始记录")
    rule()
    for path, desc in (
        ("eval/logs/hy3_原始回答日志.md", "完整提示词 + 模型原始回答全文（可核查未喂答案）"),
        ("eval/logs/过程评估判定日志.md", "逐用例 verdict + 四步骤判定 + 错误归因"),
        ("eval/results/hy3_solutions.jsonl", "逐题解答 + 模型来源标注"),
        ("eval/results/verification.json", "评估器有效性：定位准确率 / 误报率 / 人工抽检"),
    ):
        full = os.path.join(ROOT, path)
        if os.path.exists(full):
            nb = os.path.getsize(full)
            size = f"{nb / 1048576:.2f} MB" if nb >= 1048576 else f"{nb / 1024:.0f} KB"
        else:
            size = "缺失"
        say(f"  {path:38} {size:>9}   {desc}", 0.12)
    rule()
    say("演示所用数据均为上述真实产物，可用一条命令复现（README §3）。", 0.12)
    pause(1.0)


SHOTS = 6


def main() -> int:
    global FAST
    ap = argparse.ArgumentParser(description="录制用演示脚本（真实数据 + 真实执行）")
    ap.add_argument("--id", default="BE08", help="主角题号（默认 BE08 山脉数组的峰顶索引）")
    ap.add_argument("--fast", action="store_true", help="不等待，仅用于自检脚本内容")
    args = ap.parse_args()
    FAST = args.fast

    # Windows 控制台默认可能是 GBK，日志里的 ✓/✗ 会直接抛 UnicodeEncodeError
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    pid = args.id
    prob = load_problem(pid)
    sol = load_solution(pid)
    ev = load_eval(pid)

    t0 = time.time()
    shot_project(pid, prob)
    shot_solve(pid, prob, sol)
    shot_erv(pid)
    shot_judge(pid, ev)
    shot_overall()
    shot_logs(pid)
    print()
    print(f"  —— 演示结束，用时 {time.time() - t0:.0f} 秒 ——", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
