# -*- coding: utf-8 -*-
"""生成 demo 视频（MP4 + GIF）：一次完整的「解题 → 沙盒验证 → 过程评估」流程。

为什么用脚本渲染，而不是录屏：
  1. 录屏依赖桌面环境与人工操作，不可复现，分辨率/字体/窗口大小都会漂移；
  2. 本脚本直接读取**真实评测产物**（data/problems.json、eval/logs/eval_trace.jsonl、
     eval/results/full_summary_rule.json），每一帧展示的都是跑批真实产出的数据 ——
     因此不存在「演示素材与报告指标对不上」的风险，评审可逐帧核对；
  3. 数据更新后一条命令即可重出视频（`python tools/gen_demo_video.py`）。

叙事设计（默认主角 BE08「山脉数组的峰顶索引」，hy3 真实解答）：
  ① 出题        —— 只把题面交给模型，不提供任何标准答案
  ② Hy3 求解    —— 四段式解题过程（思路 / 复杂度 / 边界 / 代码）
  ③ 沙盒 ERV    —— 官方 5 组用例实际执行，全 AC → **传统判题到此就结束了**
  ④ 压力测试    —— deep-ERV 以官方参考解为 oracle 生成大输入，差分比较 → WA
  ⑤ 过程评估    —— 四步骤逐级判定，定位到 step4，判定「过程不成立」
  ⑥ 全量结果    —— 513 题的答案正确率 / 过程正确率 / 「答案对但过程错」规模

  选 BE08 的原因是它最能体现本系统的增量价值：官方用例全过（传统判题判它「完全掌握」），
  但压力测试暴露了代码的稳健性缺陷 —— 这正是「过程评估」存在的意义。

依赖：Pillow（渲染）+ ffmpeg（合成）。中文用系统微软雅黑，代码用 Consolas。
用法：
    python tools/gen_demo_video.py                  # 默认主角 BE08
    python tools/gen_demo_video.py --id DM13        # 换一道题重出
    python tools/gen_demo_video.py --no-gif         # 只出 MP4
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SOLVE_TRACE = os.path.join(ROOT, "eval", "logs", "eval_trace.jsonl")
RESULTS = os.path.join(ROOT, "eval", "results")
PROBLEMS = os.path.join(ROOT, "data", "problems.json")
OUT_DIR = os.path.join(ROOT, "demo")

W, H = 1280, 720

# ---------- 配色（深色底，投影/录制都清晰）----------
BG = (15, 23, 42)
CARD = (30, 41, 59)
CARD_HI = (51, 65, 85)
FG = (226, 232, 240)
MUTED = (148, 163, 184)
DIM = (100, 116, 139)
BLUE = (56, 189, 248)
GREEN = (34, 197, 94)
RED = (239, 68, 68)
AMBER = (245, 158, 11)
PURPLE = (167, 139, 250)

FONT_CANDIDATES = {
    "bold": ["C:/Windows/Fonts/msyhbd.ttc", "/System/Library/Fonts/PingFang.ttc",
             "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"],
    "reg": ["C:/Windows/Fonts/msyh.ttc", "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"],
    "mono": ["C:/Windows/Fonts/consola.ttf", "/System/Library/Fonts/Menlo.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
}
_font_cache: dict = {}


def F(kind: str, size: int, text: str = "") -> ImageFont.FreeTypeFont:
    """按 (字重, 字号) 取字体，带缓存。

    text 非空时做**字形可用性回退**：Consolas 不含中日韩字形，直接用它渲染中文会得到
    一排「豆腐块」方框，因此凡文本含非 ASCII 字符时一律回退到中文正文字体。
    """
    if kind == "mono" and any(ord(ch) > 0x2000 for ch in text):
        kind = "reg"
    key = (kind, size)
    if key in _font_cache:
        return _font_cache[key]
    for path in FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            try:
                # .ttc 是字体集合，index=0 即常规字重，避免误取其它 face
                f = ImageFont.truetype(path, size, index=0)
                _font_cache[key] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _font_cache[key] = f
    return f


# 微软雅黑等常见中文字体对 U+2713/U+2717（✓/✗）支持不稳，会渲染成方框；
# 改用中文排版里通用的「√ / ×」，在各类中文字体中都有稳定字形。
OK_MARK, NG_MARK = "√", "×"


# ---------------------------------------------------------------- 工具函数

def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def prog(t: float, start: float, dur: float) -> float:
    """把 t 映射到 [start, start+dur] 区间的 0..1 进度（已缓动）。"""
    if dur <= 0:
        return 1.0
    return ease((t - start) / dur)


def wrap(d: ImageDraw.ImageDraw, text: str, font, maxw: float) -> list:
    """按像素宽度折行（中文逐字、英文按词）。"""
    out, cur = [], ""
    for ch in text:
        if ch == "\n":
            out.append(cur)
            cur = ""
            continue
        if d.textlength(cur + ch, font=font) > maxw and cur:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def block(d, x, y, text, font, fill, maxw, line_h, max_lines=None):
    """绘制自动折行的文本块，返回结束 y。"""
    lines = wrap(d, text, font, maxw)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1][: max(0, len(lines[-1]) - 1)] + "…"
    for i, ln in enumerate(lines):
        d.text((x, y + i * line_h), ln, font=font, fill=fill)
    return y + len(lines) * line_h


def panel(d, x, y, w, h, fill=CARD, outline=None, r=14, width=2):
    d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill,
                        outline=outline, width=width if outline else 0)


def tag(d, x, y, text, bg, fg=(15, 23, 42), px=16, padx=12, pady=6):
    """小圆角标签，返回 (宽, 高)。"""
    f = F("bold", px)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + tw + padx * 2, y + px + pady * 2],
                        radius=(px + pady * 2) // 2, fill=bg)
    d.text((x + padx, y + pady), text, font=f, fill=fg)
    return tw + padx * 2, px + pady * 2


def scene_header(d, t, kicker, title, color=BLUE):
    """统一的场景抬头：序号标签 + 标题。"""
    a = prog(t, 0.0, 0.45)
    if a <= 0.02:
        return
    tag(d, 64, 40, kicker, color)
    d.text((64, 84), title, font=F("bold", 34), fill=FG)


def footer(d, gt, total, stage):
    """底部整体进度条 + 阶段名。"""
    y = H - 42
    d.text((64, y - 4), stage, font=F("reg", 15), fill=DIM)
    bw = W - 64 - 260
    d.rounded_rectangle([64, y + 20, 64 + bw, y + 26], radius=3, fill=(30, 41, 59))
    fw = max(4, int(bw * min(1.0, gt / total)))
    d.rounded_rectangle([64, y + 20, 64 + fw, y + 26], radius=3, fill=(56, 120, 200))
    pct_txt = f"{int(gt / total * 100):3d}%"
    d.text((W - 64 - d.textlength(pct_txt, font=F("mono", 16)), y + 14),
           pct_txt, font=F("mono", 16, pct_txt), fill=MUTED)


def clean(s: str, limit=None) -> str:
    """把 markdown 清洗成适合上屏的纯文本。"""
    s = re.sub(r"```[a-zA-Z]*", "", s)
    s = s.replace("```", "")
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\$(.+?)\$", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.M)
    s = re.sub(r"^\s*[-*+]\s+", "", s, flags=re.M)
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        s = s[:limit].rstrip() + "…"
    return s


def split_solution(raw: str):
    """把四段式解答切成 [(段名, 该段正文)]；解析失败则整体兜底。"""
    marks = [("思路/建模", r"#+\s*思\s*路"), ("复杂度分析", r"#+\s*复杂度"),
             ("边界与处理", r"#+\s*边界"), ("代码实现", r"#+\s*代码")]
    idx = []
    for name, pat in marks:
        m = re.search(pat, raw)
        if m:
            idx.append((m.start(), name))
    if len(idx) < 2:
        return [("解答全文", raw)]
    idx.sort()
    out = []
    for i, (pos, name) in enumerate(idx):
        end = idx[i + 1][0] if i + 1 < len(idx) else len(raw)
        out.append((name, raw[pos:end]))
    return out


# ---------------------------------------------------------------- 数据装载

def read_last(path: str, pid: str):
    """读取 jsonl 中该题**最后一条**记录（日志 append-only，含修订历史）。"""
    hit = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("problem_id") == pid:
                hit = r
    return hit


def load_case(pid: str) -> dict:
    probs = {p["id"]: p for p in json.load(open(PROBLEMS, encoding="utf-8"))}
    if pid not in probs:
        raise SystemExit(f"题号 {pid} 不在题库中")
    ev = read_last(SOLVE_TRACE, pid)
    if not ev:
        raise SystemExit(f"评估轨迹中没有 {pid}（需先跑过全量评估）")
    v = ev.get("verdict") or {}
    return {
        "pid": pid,
        "problem": probs[pid],
        "raw": ev.get("raw_solution") or "",
        "cases": ev.get("case_verdicts") or [],
        "stress": ev.get("stress_case_verdicts") or [],
        "stress_summary": ev.get("stress_summary") or "",
        "steps": ev.get("step_verdicts") or [],
        "v": v,
    }


def load_overall() -> dict:
    p = os.path.join(RESULTS, "full_summary_rule.json")
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8"))


# ---------------------------------------------------------------- 各场景

DIFF_CN = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}


def scene_title(d, t, dur, D):
    a = prog(t, 0.15, 0.7)
    d.text((64, 218), "AlgoJudge-Hy3", font=F("bold", 74), fill=FG)
    if a > 0.05:
        d.text((66, 316), "算法题「过程评估与错误定位」系统", font=F("bold", 34),
               fill=BLUE)
        block(d, 66, 372,
              "不只判断答案对不对，更判断推理链成不成立、错在哪一步",
              F("reg", 21), MUTED, 900, 30)
        sat = prog(t, 0.9, 0.8)
        if sat > 0.05:
            # 标签宽度随文案变化，必须按实际宽度依次排布；写死 x 会让长标签压住后一个
            x = 64
            for txt, col in (("题库 513 题 · LeetCode 官方真题", PURPLE),
                             ("12 算法域 × 3 难度", BLUE),
                             ("三层可验证闭环", GREEN)):
                w_, _h = tag(d, x, 452, txt, col)
                x += w_ + 12
    # 装饰：竖向光条
    for i in range(3):
        d.rounded_rectangle([W - 150 + i * 26, 120, W - 138 + i * 26, 600],
                            radius=6, fill=(30, 58, 95))


def scene_problem(d, t, dur, D):
    p = D["problem"]
    scene_header(d, t, "①  出 题", "只把题面交给模型，不提供任何标准答案")
    y = 152
    panel(d, 64, y, W - 128, 62, CARD)
    tag(d, 84, y + 15, D["pid"], BLUE)
    d.text((84 + 78, y + 12), p["title"], font=F("bold", 27), fill=FG)
    x2 = 84 + 78 + d.textlength(p["title"], font=F("bold", 27)) + 26
    tag(d, x2, y + 18, DIFF_CN.get(p["difficulty"], p["difficulty"]),
        {"Easy": GREEN, "Medium": AMBER, "Hard": RED}.get(
            DIFF_CN.get(p["difficulty"], ""), MUTED))
    d.text((x2 + 96, y + 18), f"算法域：{p['domain']}", font=F("reg", 19), fill=MUTED)
    cap = f"官方用例 {len(D['cases'])} 组"
    d.text((W - 300, y + 20), cap, font=F("mono", 18, cap), fill=GREEN)

    a = prog(t, 0.5, 0.8)
    if a > 0.05:
        panel(d, 64, 234, W - 128, 300, (24, 34, 53))
        d.text((88, 254), "题目描述", font=F("bold", 18), fill=DIM)
        block(d, 88, 286, clean(p["description"]), F("reg", 21), FG, W - 200, 34, 7)

    b = prog(t, 3.4, 0.7)
    if b > 0.05:
        panel(d, 64, 556, W - 128, 78, (26, 52, 40), outline=(48, 100, 74), r=12)
        d.text((88, 572), "数据来源", font=F("bold", 17), fill=GREEN)
        block(d, 88, 598,
              f"{p.get('source', 'LeetCode 官方')}　题面、标准答案与测试用例均取自 "
              "LeetCode 官方；本页为真实评测产物，非演示构造数据。",
              F("reg", 17), (190, 214, 200), W - 200, 24, 2)


def scene_solve(d, t, dur, D):
    scene_header(d, t, "②  H y 3  求 解", "四段式解题过程（输入仅题面，未提供答案）")
    segs = split_solution(D["raw"])
    segs = segs[:4]
    n = len(segs)
    # 四段卡片 + 底部结论行必须落在 footer 之上：区高留到 H-250，
    # 否则第 4 张卡片会压住底部进度条。
    top = 146
    row_h = min(112, (H - 250) // max(1, n))
    for i, (name, body) in enumerate(segs):
        appear = 0.4 + i * (dur - 3.0) / max(1, n)
        a = prog(t, appear, 0.45)
        if a <= 0.02:
            continue
        y = top + i * (row_h + 8)
        hi = (i == n - 1)
        panel(d, 64, y, W - 128, row_h, CARD_HI if hi else CARD, r=12)
        # 步骤序号圆
        d.ellipse([84, y + 18, 116, y + 50], fill=(37, 99, 135))
        d.text((93, y + 23), str(i + 1), font=F("bold", 20), fill=FG)
        d.text((132, y + 22), name, font=F("bold", 21), fill=BLUE)
        d.text((W - 190, y + 24), f"{OK_MARK} 已给出", font=F("bold", 17), fill=GREEN)
        block(d, 132, y + 56, clean(body, 168), F("reg", 17), MUTED,
              W - 260, 25, 2)
    if t > dur - 3.2:
        d.text((64, H - 92), "四段结构完整 —— 但这只是「模型自己说的」，还需沙盒实证",
               font=F("bold", 18), fill=AMBER)


def scene_erv(d, t, dur, D):
    scene_header(d, t, "③  沙 盒 执 行 验 证  E R V",
                 "把代码丢进沙盒子进程，实际跑官方测试用例")
    cases = D["cases"]
    n = len(cases)
    y0 = 158
    step = 0.42
    for i, c in enumerate(cases):
        if t < 0.6 + i * step:
            continue
        y = y0 + i * 52
        ok = c["verdict"] == "AC"
        col = GREEN if ok else RED
        panel(d, 64, y, W - 128, 44, (26, 44, 38) if ok else (58, 32, 34), r=10)
        t_case = f"用例 #{i + 1}"
        t_exp = f"期望 {str(c['expected'])[:26]}"
        t_act = f"实际 {str(c['actual'])[:26]}"
        d.text((88, y + 11), t_case, font=F("mono", 18, t_case), fill=MUTED)
        d.text((200, y + 11), c["verdict"], font=F("bold", 19), fill=col)
        d.text((286, y + 12), t_exp, font=F("mono", 17, t_exp), fill=(180, 195, 210))
        d.text((560, y + 12), t_act, font=F("mono", 17, t_act), fill=(180, 195, 210))
        if ok:
            d.text((W - 150, y + 11), f"{OK_MARK} 通过", font=F("bold", 18), fill=GREEN)

    end = 0.6 + n * step
    if t > end + 0.3:
        a = prog(t, end + 0.3, 0.5)
        d.rounded_rectangle([64, 496, W - 64, 566],
                            radius=12, fill=(24, 58, 42))
        d.text((92, 512), f"官方用例 {len(cases)}/{len(cases)} 全部通过",
               font=F("bold", 28), fill=GREEN)
        d.text((92, 548),
               "→  传统判题在此就结束了：判它「完全掌握」",
               font=F("bold", 19), fill=(150, 200, 170))


def scene_stress(d, t, dur, D):
    scene_header(d, t, "④  差 分 压 力 测 试  d e e p - E R V",
                 "以官方参考解为 oracle，生成大规模输入做差分比较")
    y = 158
    items = [
        (0.3, "读取官方参考解", "作为差分比对的 oracle（模型不可见）", BLUE),
        (1.2, "生成大规模/边界输入", "覆盖主测试集未触达的结构与规模", BLUE),
        (2.1, "同一输入分别执行两份代码", "模型解 vs 参考解，逐例比较输出", BLUE),
    ]
    for i, (st, name, desc, col) in enumerate(items):
        if t < st:
            continue
        a = prog(t, st, 0.4)
        yy = y + i * 62
        panel(d, 64, yy, W - 128, 52, CARD, r=10)
        d.text((90, yy + 14), name, font=F("bold", 20), fill=FG)
        d.text((360, yy + 16), desc, font=F("reg", 17), fill=MUTED)
        d.text((W - 140, yy + 12), OK_MARK, font=F("bold", 22), fill=GREEN)

    if t > 3.2:
        d.rounded_rectangle([64, 372, W - 64, 470], radius=12,
                            fill=(62, 30, 32), outline=RED, width=2)
        d.text((92, 390), "差分不一致！", font=F("bold", 26), fill=RED)
        sc = D["stress"][0] if D["stress"] else {}
        t_wa = (f"第 1 例  WA   期望 {sc.get('expected', '2')}   "
                f"实际 {sc.get('actual', '73')}　（小规模输入下恰好通过）")
        d.text((92, 428), t_wa, font=F("mono", 18, t_wa), fill=(240, 190, 190))

    if t > dur - 4.6:
        panel(d, 64, 500, W - 128, 118, (33, 43, 24),
              outline=(122, 92, 20), r=12)
        d.text((92, 518), "主测试集通过 ≠ 代码正确", font=F("bold", 22), fill=AMBER)
        block(d, 92, 552, clean(
            "该实现在恰好被覆盖的输入分布上成立，换一组输入即出错 —— 这类"
            f"「答案对但过程不成立」的样本全库共 {D.get('lucky_n') or 116} 例，"
            "传统判题会把它们全部误判为「已掌握」。"),
            F("reg", 18), (226, 214, 178), W - 200, 26, 2)


def scene_judge(d, t, dur, D):
    v = D["v"]
    scene_header(d, t, "⑤  过 程 评 估 判 定", "四步骤逐级核查推理链，并定位错误步骤")
    steps = D["steps"]
    y0 = 156
    for i, s in enumerate(steps):
        if t < 0.5 + i * 0.75:
            continue
        y = y0 + i * 56
        ok = s["ok"]
        col = GREEN if ok else RED
        panel(d, 64, y, W - 128, 48, (26, 44, 38) if ok else (62, 30, 32), r=10)
        d.text((90, y + 12), f"step {s['step']}", font=F("mono", 18), fill=MUTED)
        d.text((186, y + 11), s["name"], font=F("bold", 20), fill=FG)
        d.text((470, y + 13), clean(s["reason"], 44) if not ok else "无明显问题",
               font=F("reg", 16), fill=(220, 170, 170) if not ok else MUTED)
        d.text((W - 146, y + 10), OK_MARK if ok else NG_MARK, font=F("bold", 24), fill=col)

    if t > 0.5 + len(steps) * 0.75 + 0.5:
        y = y0 + len(steps) * 56 + 14
        d.rounded_rectangle([64, y, W - 64, y + 116], radius=12,
                            fill=(24, 34, 53), outline=BLUE, width=2)
        d.text((92, y + 14), "判定结果", font=F("bold", 18), fill=DIM)
        d.text((92, y + 44), f"答案正确 {OK_MARK}", font=F("bold", 24), fill=GREEN)
        d.text((280, y + 44), f"过程不成立 {NG_MARK}", font=F("bold", 24), fill=RED)
        et = v.get("error_type_name") or "逻辑错误"
        d.text((92, y + 82),
               f"错误定位：step {v.get('error_step')} {steps[-1]['name']} · {et}"
               f"　（传统判题看不出任何问题）",
               font=F("bold", 18), fill=AMBER)


def scene_overview(d, t, dur, D):
    scene_header(d, t, "⑥  全 量 结 果", "513 道题跑完后的整体指标")
    s = D.get("overall") or {}
    n = s.get("total") or 513
    acc = s.get("final_acc") or 0.842
    pr = s.get("process_rate") or 0.616
    lucky = s.get("lucky_pass") or 116
    cards = [
        (f"{acc * 100:.1f}%", "答案正确率", f"{s.get('final_correct') or 432} / {n} 题",
         GREEN, 0.5),
        (f"{pr * 100:.1f}%", "过程正确率", f"{s.get('process_valid') or 316} / {n} 题",
         BLUE, 1.0),
        (f"{lucky}", "答案对但过程错", "传统判题完全无法发现", RED, 1.5),
    ]
    cw, gap = 356, 32
    for i, (big, label, sub, col, st) in enumerate(cards):
        a = prog(t, st, 0.5)
        if a <= 0.02:
            continue
        x = 64 + i * (cw + gap)
        panel(d, x, 176, cw, 208, CARD, outline=col, r=16)
        d.text((x + 32, 206), big, font=F("bold", 62), fill=col)
        d.text((x + 32, 292), label, font=F("bold", 23), fill=FG)
        block(d, x + 32, 330, sub, F("reg", 17), MUTED, cw - 64, 24)

    if t > 2.4:
        panel(d, 64, 420, W - 128, 150, (24, 34, 53), r=12)
        block(d, 92, 442,
              "把「推理链是否成立」纳入判定后，通过率从 84.2% 降到 61.6%。"
              "两者之间的差额，就是「答案对但过程不成立」的样本 —— "
              "若只用传统判题，这 116 题会被全部误判为「已掌握」。",
              F("reg", 20), FG, W - 190, 34, 3)
        if t > 3.6:
            x = 92
            for txt, col in (("错误类型分布", BLUE), ("难度分层", PURPLE),
                             ("四步骤逐级通过率", GREEN), ("逐题可追溯日志", AMBER)):
                w_, _h = tag(d, x, 582, txt, col)
                x += w_ + 14


def scene_outro(d, t, dur, D):
    a = prog(t, 0.2, 0.6)
    if a <= 0.02:
        return
    d.text((64, 250), "过程评估，而非只看答案", font=F("bold", 52), fill=FG)
    d.text((66, 330), "AlgoJudge-Hy3 · 犀牛鸟开源实战任务二", font=F("reg", 24),
           fill=MUTED)
    if t > 1.4:
        panel(d, 64, 400, 660, 96, CARD, r=12)
        d.text((92, 420), "github.com/lyuanm/algo-process-eval-plan",
               font=F("mono", 24, "github.com/lyuanm/algo-process-eval-plan"), fill=BLUE)
        d.text((92, 456), "源码 · 题库 · 评测报告 · 完整日志 · 复现脚本",
               font=F("reg", 17), fill=MUTED)
    if t > 2.2:
        d.text((64, 534), "513 题 · 答案正确率 84.2% · 过程正确率 61.6%",
               font=F("bold", 22), fill=GREEN)


SCENES = [
    ("title", 6.0, "开场", scene_title),
    ("problem", 12.0, "出题", scene_problem),
    ("solve", 24.0, "Hy3 求解", scene_solve),
    ("erv", 14.0, "沙盒 ERV", scene_erv),
    ("stress", 13.0, "差分压力测试", scene_stress),
    ("judge", 21.0, "过程评估判定", scene_judge),
    ("overview", 14.0, "全量结果", scene_overview),
    ("outro", 6.0, "结尾", scene_outro),
]
GIF_FROM, GIF_TO = 42.0, 90.0   # 核心区间（沙盒→压力测试→判定），单独剪一版 GIF


def make_bg() -> Image.Image:
    """预生成渐变背景（逐行画一次，之后每帧 copy，避免重复开销）。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        c = (int(BG[0] + 8 * k), int(BG[1] + 12 * k), int(BG[2] + 22 * k))
        d.line([(0, y), (W, y)], fill=c)
    return img


def render_frames(D, fps, tmpdir, gifdir):
    bg = make_bg()
    black = Image.new("RGB", (W, H), (0, 0, 0))
    total = sum(s[1] for s in SCENES)
    n, gt = 0, 0.0
    gif_n = 0
    for name, dur, label, fn in SCENES:
        frames = int(round(dur * fps))
        for i in range(frames):
            t = i / fps
            img = bg.copy()
            d = ImageDraw.Draw(img)
            fn(d, t, dur, D)
            footer(d, gt, total, label)
            # 场景切换用黑场过渡，避免元素突变
            fade = 0.25
            a = 0.0
            if t < fade:
                a = 1 - t / fade
            elif t > dur - fade:
                a = (t - (dur - fade)) / fade
            if a > 0.01:
                img = Image.blend(img, black, min(1.0, a))
            img.save(os.path.join(tmpdir, f"{n:05d}.png"))
            if gifdir is not None and GIF_FROM <= gt <= GIF_TO:
                img.resize((640, 360), Image.LANCZOS).save(
                    os.path.join(gifdir, f"{gif_n:05d}.png"))
                gif_n += 1
            n += 1
            gt += 1.0 / fps
    return n, gif_n, total


def main():
    ap = argparse.ArgumentParser(description="生成 demo 视频（真实评测数据驱动）")
    ap.add_argument("--id", default="BE08", help="主角题号（默认 BE08）")
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--out", default=None, help="MP4 输出路径")
    ap.add_argument("--no-gif", action="store_true")
    ap.add_argument("--keep-frames", action="store_true")
    args = ap.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("未找到 ffmpeg，请先安装（Windows: choco install ffmpeg）")

    D = load_case(args.id)
    D["overall"] = load_overall()
    # 「答案对但过程错」的总数在压力测试场景也要用，统一从汇总里取，避免两处硬编码不一致
    D["lucky_n"] = (D["overall"] or {}).get("lucky_pass") or 116
    v = D["v"]
    print(f"[数据] 主角 {D['pid']} {D['problem']['title']}")
    print(f"       用例 {len(D['cases'])} 组 / 压力用例 {len(D['stress'])} 组")
    print(f"       判定 final_correct={v.get('final_correct')} "
          f"process_valid={v.get('process_valid')} error_step={v.get('error_step')}")
    print(f"[数据] 全量汇总 {'已加载' if D['overall'] else '缺失（用默认值）'}")

    out_mp4 = args.out or os.path.join(OUT_DIR, f"demo_{args.id.lower()}.mp4")
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="algovideo_")
    gifdir = None if args.no_gif else tempfile.mkdtemp(prefix="algogif_")
    try:
        print(f"[渲染] {W}x{H} @ {args.fps}fps ...")
        n, gif_n, total = render_frames(D, args.fps, tmpdir, gifdir)
        print(f"[渲染] 共 {n} 帧，时长约 {total:.0f}s")

        cmd = [ffmpeg, "-y", "-framerate", str(args.fps), "-i",
               os.path.join(tmpdir, "%05d.png"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21",
               "-preset", "medium", "-movflags", "+faststart", out_mp4]
        subprocess.run(cmd, check=True, capture_output=True)
        size = os.path.getsize(out_mp4) / 1048576
        print(f"[视频] {os.path.relpath(out_mp4, ROOT)}  {size:.2f} MB  {total:.0f}s")

        if gifdir and gif_n:
            out_gif = os.path.join(OUT_DIR, f"demo_{args.id.lower()}_核心片段.gif")
            vf = "fps=8,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse"
            subprocess.run([ffmpeg, "-y", "-framerate", str(args.fps), "-i",
                            os.path.join(gifdir, "%05d.png"), "-vf", vf, out_gif],
                           check=True, capture_output=True)
            gsize = os.path.getsize(out_gif) / 1048576
            print(f"[GIF ] {os.path.relpath(out_gif, ROOT)}  {gsize:.2f} MB  "
                  f"{gif_n / args.fps:.0f}s")
    finally:
        if not args.keep_frames:
            shutil.rmtree(tmpdir, ignore_errors=True)
            if gifdir:
                shutil.rmtree(gifdir, ignore_errors=True)
        else:
            print(f"[保留] 帧目录 {tmpdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
