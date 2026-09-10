"""由全量评测产物生成 Markdown 报告（最终结果的可读版本）。

输入：eval/results/full_summary_<backend>.json、full_eval_<backend>.jsonl、hy3_solutions.jsonl
输出：全量评测报告.md

运行：python tools/gen_full_report.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)

RES = os.path.join(ROOT, "eval", "results")
sys.path.insert(0, ROOT)
from src import runlog  # noqa: E402

STEP_NAMES = {1: "思路/建模", 2: "复杂度分析", 3: "边界与处理", 4: "代码实现"}
DIFF_CN = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
VERDICT_CN = {"AC": "通过", "WA": "答案错误", "TLE": "超时", "RE": "运行异常", "CE": "编译错误"}


def read_jsonl(path):
    """读取 jsonl，容忍被中断截断的残行（长任务断点续跑场景）。"""
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


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pct(x):
    return f"{x*100:.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="rule")
    ap.add_argument("--out", default=os.path.join(ROOT, "全量评测报告.md"))
    ap.add_argument("--workers", type=int, default=16, help="求解并发数（仅用于报告中标注）")
    ap.add_argument("--eval-workers", type=int, default=6, help="评估并发数（仅用于报告中标注）")
    args = ap.parse_args()

    s = load_json(os.path.join(RES, f"full_summary_{args.backend}.json"))
    evals = read_jsonl(os.path.join(RES, f"full_eval_{args.backend}.jsonl"))
    raws = {r["problem_id"]: r for r in read_jsonl(os.path.join(RES, "hy3_solutions.jsonl"))}
    if not s or not evals:
        raise SystemExit("缺少全量评测产物，请先运行 python eval/run_full.py --workers 8")

    n = s["total"]
    lucky = [e for e in evals if e["final_correct"] and not e["process_valid"]]
    wrong = [e for e in evals if not e["final_correct"]]
    gen_elapsed = sorted(r["elapsed"] for r in raws.values() if r.get("elapsed"))
    gen_med = f"{gen_elapsed[len(gen_elapsed)//2]:.1f}s" if gen_elapsed else "—"
    # 模型来源构成：跑批中途会因额度/容量问题换模型，报告必须披露混合来源，
    # 否则整份指标会被误读为单一模型的能力。
    provenance = runlog.solution_provenance(os.path.join(RES, "hy3_solutions.jsonl"))
    mixed = len(provenance) > 1
    model_desc = ("、".join(f"{k} {v} 题" for k, v in provenance.items())
                  if provenance else "—")
    # 沙盒 verdict 聚合
    vt = {}
    for e in evals:
        for c in (e.get("verdict_summary") or "").split():
            if ":" in c:
                k, v = c.split(":", 1)
                try:
                    vt[k] = vt.get(k, 0) + int(v)
                except ValueError:
                    pass

    # 四步骤逐级通过率：把每题过程判定按四步骤拆开，看推理链在哪一步开始崩
    step_pass = {i: {"ok": 0, "total": 0} for i in (1, 2, 3, 4)}
    for e in evals:
        for sv in e.get("step_verdicts") or []:
            k = sv.get("step")
            if k in step_pass:
                step_pass[k]["total"] += 1
                if sv.get("ok"):
                    step_pass[k]["ok"] += 1

    # 首次失败 verdict（按题去重，区别于逐用例聚合的 vt）
    ff = {}
    for e in evals:
        v = e.get("first_failure_verdict")
        if v:
            ff[v] = ff.get(v, 0) + 1

    # 难度 × 错误类型 交叉
    cross = {}
    for e in evals:
        if e.get("process_valid"):
            continue
        d = e.get("difficulty") or "?"
        et = (e.get("error_type_name") or e.get("error_type") or "未归因").split("：")[0]
        cross.setdefault(d, {})
        cross[d][et] = cross[d].get(et, 0) + 1

    L = []
    A = L.append
    A("# AlgoJudge 全量评测报告\n")
    A(f"> 题库：LeetCode 官方真题 **{s['bank_total']} 题**（12 算法域 × 3 难度）　"
      f"求解模型：**{model_desc}**（TokenHub / OpenAI 兼容网关）　评测后端：**{args.backend}**　"
      f"生成时间：{s['generated_at']}\n")
    A("> 全流程：大模型生成四段式解题过程 → 沙盒执行官方测试用例（ERV）→ 差分压力测试 → "
      "过程评估器判定推理链是否成立并定位错误步骤。\n")
    if mixed:
        A(f"> ⚠️ **模型来源为混合结果**：本次跑批因网关额度/容量限制中途更换模型，"
          f"共 {len(provenance)} 个模型参与（{model_desc}）。因此下列指标是"
          f"**多模型混合**表现，不能读作单一模型在 {s['bank_total']} 题上的能力。\n")

    A("## 一、核心指标\n")
    A("| 指标 | 数值 | 说明 |")
    A("|---|---|---|")
    A(f"| 已评测题数 | {n} / {s['bank_total']}（{pct(s['coverage'])}） | 全量覆盖 |")
    A(f"| **答案正确率** | **{pct(s['final_acc'])}**（{s['final_correct']} 题） | 通过题目全部官方用例 |")
    A(f"| **过程正确率** | **{pct(s['process_rate'])}**（{s['process_valid']} 题） | 推理链成立且通过压力测试 |")
    A(f"| 答案对但过程错 | {s['lucky_pass']} 题（{pct(s['lucky_rate'])}） | **传统判题无法发现，本系统的增量价值** |")
    A(f"| 答案错误 | {s['wrong_count']} 题 | 已定位到具体步骤与错误类型 |")
    A(f"| 单题生成耗时（中位） | {gen_med} | 仅统计**外部 API 调用**的解答；并发历经调整，末轮为 {args.workers} 路 |")
    A(f"| 单题评估耗时（中位） | {s.get('eval_sec_median')}s | 沙盒 ERV + 压力测试 + 规则判定 |")
    A("")
    A(f"**结论**：在 {n} 道题上，模型的答案正确率为 {pct(s['final_acc'])}；"
      f"但若把「推理链是否成立」纳入判定，通过率降至 {pct(s['process_rate'])}。"
      f"其中 {s['lucky_pass']} 题属于「答案对、过程不成立」——"
      f"这类样本若只用传统判题，会被误判为完全掌握。\n")
    if mixed:
        A("> 注：上述指标来自多个模型的混合解答，"
          "分模型指标见「模型来源构成」一节。\n")

    A("## 二、模型来源构成\n")
    if not mixed:
        A(f"本次全部解答由 **{model_desc}** 产出，不存在混合来源问题。\n")
    else:
        A("跑批期间网关出现额度/容量限制，为跑完剩余题目而更换了模型。"
          "下表给出**分模型**指标——可以看出各模型的真实表现，避免把混合结果误读成单一模型能力。\n")
        A("| 模型 | 题数 | 答案正确率 | 过程正确率 | 答案对但过程错 | 生成耗时中位 |")
        A("|---|---|---|---|---|---|")
        by_model = {}
        for e in evals:
            rec = raws.get(e["problem_id"])
            mk = (rec or {}).get("model") or runlog.LEGACY_MODEL
            by_model.setdefault(mk, []).append((e, (rec or {}).get("elapsed")))
        for mk, items in sorted(by_model.items(), key=lambda kv: -len(kv[1])):
            m = len(items)
            a_ok = sum(1 for e, _ in items if e.get("final_correct"))
            p_ok = sum(1 for e, _ in items if e.get("process_valid"))
            lk = sum(1 for e, _ in items
                     if e.get("final_correct") and not e.get("process_valid"))
            secs = sorted(x for _, x in items if x)
            med = f"{secs[len(secs)//2]:.1f}s" if secs else "—"
            A(f"| **{mk}** | {m} | {pct(a_ok/m)} | {pct(p_ok/m)} | {lk} | {med} |")
        A("")
        A("> 说明：不同模型在题目上的分配并非随机——额度耗尽后由备用模型接续跑剩余题目，"
          "因此各模型的题目集合（难度分布）不同，横向比较仅供参考。\n")

    A("## 三、难度分层\n")
    A("| 难度 | 题数 | 答案正确率 | 过程正确率 | 差距 | 答案对但过程错 |")
    A("|---|---|---|---|---|---|")
    for d in ["easy", "medium", "hard"]:
        x = s["by_difficulty"].get(d)
        if not x:
            continue
        A(f"| {DIFF_CN[d]} | {x['n']} | {pct(x['final_acc'])} | {pct(x['process_rate'])} | "
          f"{(x['final_acc']-x['process_rate'])*100:.1f}pp | {x['lucky_pass']} |")
    A("")

    A("## 四、算法域分层\n")
    A("| 算法域 | 题数 | 答案正确率 | 过程正确率 | 答案对但过程错 |")
    A("|---|---|---|---|---|")
    for d, x in sorted(s["by_domain"].items(), key=lambda kv: -kv[1]["final_acc"]):
        A(f"| {d} | {x['n']} | {pct(x['final_acc'])} | {pct(x['process_rate'])} | {x['lucky_pass']} |")
    A("")

    A("## 五、错误归因\n")
    A("### 5.1 错误类型分布（过程不成立题目）\n")
    A("| 错误类型 | 中文名 | 数量 | 占比 |")
    A("|---|---|---|---|")
    names = s.get("error_type_names", {})
    tot_err = sum(s["error_type_dist"].values()) or 1
    for k, v in s["error_type_dist"].items():
        A(f"| `{k}` | {names.get(k, k)} | {v} | {pct(v/tot_err)} |")
    A("")
    A("### 5.2 错误首次出现步骤\n")
    A("| 步骤 | 名称 | 数量 | 占比 |")
    A("|---|---|---|---|")
    tot_step = sum(s["error_step_dist"].values()) or 1
    for k, v in sorted(s["error_step_dist"].items(), key=lambda kv: int(kv[0])):
        A(f"| step {k} | {STEP_NAMES.get(int(k), k)} | {v} | {pct(v/tot_step)} |")
    A("")
    A("### 5.3 沙盒执行 verdict 分布（逐用例聚合）\n")
    A("| Verdict | 含义 | 用例数 | 占比 |")
    A("|---|---|---|---|")
    tot_v = sum(vt.values()) or 1
    for k, v in sorted(vt.items(), key=lambda kv: -kv[1]):
        A(f"| {k} | {VERDICT_CN.get(k, '')} | {v} | {pct(v/tot_v)} |")
    A("")
    if ff:
        A("### 5.4 首次失败 verdict（按题去重）\n")
        A("| Verdict | 含义 | 题数 | 占比 |")
        A("|---|---|---|---|")
        tot_ff = sum(ff.values()) or 1
        for k, v in sorted(ff.items(), key=lambda kv: -kv[1]):
            A(f"| {k} | {VERDICT_CN.get(k, '')} | {v} | {pct(v/tot_ff)} |")
        A("")
    A("### 5.5 四步骤逐级通过率\n")
    A("| 步骤 | 名称 | 通过题数 | 通过率 | 相对首步累计失守 |")
    A("|---|---|---|---|---|")
    base = step_pass[1]["total"] or 0
    for i in (1, 2, 3, 4):
        x = step_pass[i]
        if not x["total"]:
            continue
        r = x["ok"] / x["total"]
        A(f"| step {i} | {STEP_NAMES[i]} | {x['ok']} / {x['total']} | {pct(r)} | {base - x['ok']} |")
    A("")
    if cross:
        etypes = sorted({t for d in cross.values() for t in d})
        A("### 5.6 难度 × 错误类型 交叉\n")
        A("| 难度 | " + " | ".join(etypes) + " | 合计 |")
        A("|---" * (len(etypes) + 2) + "|")
        for d in ["easy", "medium", "hard"]:
            if d not in cross:
                continue
            row = cross[d]
            tot = sum(row.values())
            A(f"| {DIFF_CN[d]} | " + " | ".join(str(row.get(t, 0)) for t in etypes) + f" | {tot} |")
        A("")

    A("## 六、典型样本\n")
    if lucky:
        A("### 6.1 答案正确但过程不成立（传统判题会漏判）\n")
        for e in lucky[:5]:
            A(f"**{e['problem_id']} {e.get('title','')}**（{DIFF_CN.get(e.get('difficulty'),'')} · {e.get('domain','')}）")
            A(f"- 用例：{e['passed_cases']}/{e['total_cases']} 通过　沙盒 verdict：`{e.get('verdict_summary','')}`")
            A(f"- 定位：step {e['error_step']} {STEP_NAMES.get(e['error_step'],'')}　类型：`{e['error_type']}`（{e.get('error_type_name','')}）")
            A(f"- 判定说明：{e.get('note','')}")
            if e.get("stress_summary"):
                A(f"- 压力测试：`{e['stress_summary']}`")
            A("")
    if wrong:
        A("### 6.2 答案错误样本\n")
        for e in wrong[:5]:
            A(f"**{e['problem_id']} {e.get('title','')}**（{DIFF_CN.get(e.get('difficulty'),'')} · {e.get('domain','')}）")
            A(f"- 用例：{e['passed_cases']}/{e['total_cases']} 通过　verdict：`{e.get('verdict_summary','')}`")
            A(f"- 定位：step {e['error_step']} {STEP_NAMES.get(e['error_step'],'')}　类型：`{e['error_type']}`")
            A(f"- 判定说明：{e.get('note','')}")
            A("")

    A("## 七、效率\n")
    if gen_elapsed:
        A("| 指标 | 数值 |")
        A("|---|---|")
        A(f"| 单题生成耗时（中位 / 最快 / 最慢） | {gen_elapsed[len(gen_elapsed)//2]:.1f}s / {gen_elapsed[0]:.1f}s / {gen_elapsed[-1]:.1f}s |")
        A(f"| 全量生成累计 | {sum(gen_elapsed)/60:.1f} 分钟（{args.workers} 路并发） |")
        A(f"| 单题评估耗时（中位） | {s.get('eval_sec_median')}s |")
        A(f"| 全量评估累计 | {(s.get('eval_sec_total') or 0)/60:.1f} 分钟（{args.eval_workers} 路并发） |")
    A("")

    A("## 八、方法与可复现性\n")
    A("```bash")
    A("# 1) 全量跑批：Hy3 求解 + 沙盒验证 + 过程评估（带断点续跑缓存）")
    A(f"python eval/run_full.py --workers {args.workers} --eval-workers {args.eval_workers} --deep-erv")
    A("")
    A("# 2) 生成 Web 看板与报告")
    A("python tools/gen_dashboard.py     # -> demo/dashboard.html")
    A("node  tools/check_dashboard.js    # 看板自检（渲染脚本逐容器校验）")
    A("python tools/gen_full_report.py   # -> 全量评测报告.md")
    A("```")
    A("")
    A("- **题目与标准答案**：均来自 LeetCode 官方（题目元数据 + 官方题解 Python 代码），无 AI 自编题目。")
    A("- **可执行验证（ERV）**：把生成代码放进沙盒子进程，用题目官方测试用例实际执行，按 AC/WA/TLE/RE/CE 判定，"
      "执行结果是判定的金标准，不依赖模型自述。")
    A("- **差分压力测试**：以官方参考解为 oracle，用更大规模的输入比对输出，"
      "捕捉「主测试集巧合通过」的样本。")
    A("- **过程评估**：沙盒事实 → 复杂度声称一致性检测 → 方法声称一致性检测 → 步骤级定位（1 思路 / 2 复杂度 / 3 边界 / 4 代码）。")
    A("- **判定一致性**：步骤级判定与总体判定强制对齐——`process_valid=False` 时，"
      "`error_step` 指向的步骤必然被标记为不通过，不会出现「四步全绿却判定失败」的自相矛盾结果。")
    A("")
    A("## 九、已知局限\n")
    A("- 规则后端的方法一致性检测基于文本启发式，对「把哈希表作为备选方案提及」这类表述已做否定/对比语境过滤，"
      "但复杂表述仍可能漏判（宁可漏报、不误报）。")
    A("- 部分题目（设计类、无官方参考解可作 oracle）没有压力输入，仅依赖官方用例判定。")
    A("- 压力测试超时阈值固定，个别题因常数因子偏大可能被保守判为不稳健。")
    A("")
    A("---")
    A(f"*本报告由 `tools/gen_full_report.py` 自动生成，数据源：`eval/results/full_summary_{args.backend}.json`、"
      f"`full_eval_{args.backend}.jsonl`、`hy3_solutions.jsonl`。*")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"生成 {os.path.relpath(args.out)}（{len(L)} 行）")


if __name__ == "__main__":
    main()
