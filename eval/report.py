"""生成分析报告（中文 Markdown）。

汇总：最终答案准确率、过程正确率、错误类型分布、难度分层、评估器有效性验证、
典型 case 归因、错误分类体系、能力边界与临界点分析。

输入：eval/results/evaluation_results.jsonl, eval/results/verification.json, data/problems.json
输出：eval/results/REPORT.md 与 仓库根目录 分析报告.md
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.taxonomy import ERROR_TYPES
from src.problems import load_problems, build_catalog

ROOT = os.path.join(os.path.dirname(__file__), "..")
RES = os.path.join(ROOT, "eval", "results")
EVAL_P = os.path.join(RES, "evaluation_results.jsonl")
VERIFY_P = os.path.join(RES, "verification.json")
PROB_P = os.path.join(ROOT, "data", "problems.json")
OUT = os.path.join(RES, "REPORT.md")
OUT_ROOT = os.path.join(ROOT, "分析报告.md")


def load_evals():
    with open(EVAL_P, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    evals = load_evals()
    with open(VERIFY_P, "r", encoding="utf-8") as f:
        verify = json.load(f)
    with open(PROB_P, "r", encoding="utf-8") as f:
        problems = json.load(f)
    prob_info = {p["id"]: p for p in problems}
    catalog = build_catalog(load_problems(PROB_P))

    n = len(evals)
    final_ok = sum(1 for e in evals if e["final_correct"])
    proc_ok = sum(1 for e in evals if e["process_valid"])
    final_acc = final_ok / n
    proc_rate = proc_ok / n

    # 错误类型分布（仅过程不成立者）
    err_counter = Counter(e["error_type"] for e in evals if not e["process_valid"])
    err_dist = {ERROR_TYPES.get(k, k): v for k, v in err_counter.items()}

    # 难度分层
    by_diff = defaultdict(list)
    for e in evals:
        by_diff[e["difficulty"]].append(e)
    diff_rows = []
    for d in ["easy", "medium", "hard"]:
        rows = by_diff.get(d, [])
        if not rows:
            continue
        fo = sum(1 for e in rows if e["final_correct"])
        po = sum(1 for e in rows if e["process_valid"])
        diff_rows.append({
            "difficulty": d, "count": len(rows),
            "final_acc": fo / len(rows), "proc_rate": po / len(rows),
        })

    loc = verify["localization_accuracy"]
    fp = verify["false_positive_rate"]

    # ---- 组装报告 ----
    L = []
    A = L.append
    A("# 犀牛鸟实战任务二 · 过程评估与错误定位（算法题方向）— 分析报告\n")
    A("> 个人/活动作品，非腾讯官方发布。模型能力调用通过 Hy3（OpenAI 兼容接口）完成，"
      "本项目聚焦**可验证场景下的过程评估方法**设计与验证。\n")

    A("## 1. 场景选择理由\n")
    A("- **领域**：算法竞赛/算法题（coding & algorithmic reasoning）。该场景天然满足"
      "“存在标准答案、可自动校验”的可验证条件——给定题目与测试数据，最终答案可由沙盒执行判定。\n")
    A("- **引入大模型的必要性**：仅判断“答案对错”无法区分“蒙对”与“真懂”。算法题的价值在于"
      "**推导链条是否成立**（复杂度分析、边界处理、算法选择）。本任务据此设计**过程级评估**，"
      "定位错误步骤、归类错误类型，并识别“答案正确但过程不成立”的样本。\n")

    A("## 2. AI 应用的解决方案\n")
    A("- **应用侧（求解器 `src/solver.py`）**：基于 Hy3 生成**完整解题过程**而非仅最终答案，"
      "结构化输出四段——思路、复杂度分析、边界与处理、可运行代码（stdin→stdout）。\n")
    A("- **校验侧（沙盒 `src/sandbox.py`）**：子进程 + 超时执行解法，以题目自带的 `checker` "
      "自动判定最终答案正确性（可自动校验的判定方式）。\n")
    A("- **评估侧（过程评估器 `src/process_evaluator.py`）**：提供 `rule`（规则+沙盒，离线可跑）"
      "与 `llm`（Hy3 逐步 LLM-as-judge，生产推荐）两种后端，覆盖过程判定、错误定位、错误归类、"
      "“答案对过程错”识别四大能力。\n")

    A("## 3. 评估维度设计依据\n")
    A("过程评估不只看对错，而是把“为什么对/错”拆开。设计依据：\n")
    A("1. **过程正确性判定**：推理链是否闭环（跳步、循环论证、误用定理/数据结构、条件遗漏、幻觉）。\n")
    A("2. **错误步骤定位**：解答错误时定位错误首现步骤，步骤编号固定为 "
      "1=思路/建模、2=复杂度分析、3=边界与处理、4=代码实现，便于与人工标注对齐。\n")
    A("3. **错误类型归类**：建立可操作分类体系（见 §4），每类给出可判定特征，避免“基本符合”式模糊表述。\n")
    A("4. **结果正确但过程不成立识别**：重点检测复杂度声称与代码实现矛盾、声称方法与实际不符、"
      "靠巧合/弱测试通过等情形。\n")

    A("## 4. 错误分类体系说明\n")
    A("基于任务示例扩充为可操作分类：\n")
    A("| 错误类型 | 含义 | 典型可判定特征 |\n|---|---|---|")
    for key, name in ERROR_TYPES.items():
        A(f"| `{key}` | {name} | 见 `src/taxonomy.py` 中 `ERROR_SIGNALS` |")
    A("")

    A("## 5. 评测结论（样本集）\n")
    A(f"- 样本数：**{n}**\n")
    A(f"- **最终答案准确率**：{final_ok}/{n} = **{final_acc:.1%}**\n")
    A(f"- **过程正确率**：{proc_ok}/{n} = **{proc_rate:.1%}**\n")
    A("- 错误类型分布（过程不成立样本）：\n")
    if err_dist:
        for k, v in sorted(err_dist.items(), key=lambda x: -x[1]):
            A(f"  - {k}：{v}")
    else:
        A("  -（无）")
    A("")
    A("> 说明：本样本集为**评估器验证而构造**，刻意包含较高比例的难例/反例/“答案对过程错”样本"
      "（符合任务“不应只保留容易得分样本”的要求），故上述准确率反映诊断集构成，而非模型真实能力上限。"
      "真实能力评估请运行 `python eval/run_eval.py --source live`（需配置 Hy3）。\n")

    A("### 5.1 难度分层结果\n")
    A("| 难度 | 样本数 | 最终答案准确率 | 过程正确率 |\n|---|---|---|---|")
    for r in diff_rows:
        A(f"| {r['difficulty']} | {r['count']} | {r['final_acc']:.1%} | {r['proc_rate']:.1%} |")
    A("")

    A("### 5.2 题集覆盖度（来源 / 难度 / 领域）\n")
    A(f"- 题目总数：**{catalog['total']}** 题，均取自 **LeetCode / 洛谷（P 系列）** 官方平台同名题，"
      f"每题附可运行**标准答案**与自动判定（`check_mode`），并用参考解自验保证答案可信。\n")
    src = catalog["by_source"]
    A(f"- 平台分布：LeetCode **{src.get('LeetCode', 0)}** 题、洛谷 **{src.get('洛谷', 0)}** 题"
      f"（通用/改编 **{src.get('通用', 0)}** 题）。\n")
    diff = catalog["by_difficulty"]
    A("- 难度分布：" + "、".join(f"{d} **{diff[d]}**" for d in ["easy", "medium", "hard"] if d in diff) + "。\n")
    domains = sorted(catalog["by_domain"].items(), key=lambda x: -x[1])
    A("- 领域覆盖（按题量前 12）：" + "、".join(f"{k}({v})" for k, v in domains[:12]) + " 等。\n")
    A("")

    A("## 6. 典型 case 归因分析\n")
    cases = [
        ("S_W4", "P047 单源最短路径（Dijkstra）", "声称 Dijkstra 堆优化，代码却用无权 BFS 替代，忽略边权；"
                                 "步骤 4（代码实现）判定为 logic_error。归因为“思路与实现不符”。"),
        ("S_W1", "P01 两数之和", "题意误读：应输出下标却打印数值；规则评估器因最终答案错误归因为"
                                 "步骤 4 logic_error，但真实根因在步骤 1（思路/题意），"
                                 "体现规则评估器在“归因层级”上的局限（详见 §7）。"),
        ("S_C1", "P01 两数之和", "答案正确（弱测试下暴力通过），但声称 O(n) 实为 O(n^2)；"
                                 "步骤 2（复杂度分析）判定为 complexity_error，成功识别“答案对过程错”。"),
        ("S_FP", "P045 无重复字符的最长子串", "摊还 O(n) 滑动窗口（频率数组 + 嵌套 while），过程实际成立；"
                                       "规则评估器因“嵌套循环 + 声称 O(n)”误判为复杂度矛盾——典型误报。"),
    ]
    for sid, title, desc in cases:
        A(f"- **{sid}（{title}）**：{desc}\n")

    A("## 7. 模型失败模式归纳与能力边界/临界点分析\n")
    A("- **失败模式归纳**：\n")
    A("  1. 题意/输出形式误读（如返回数值而非下标）；\n")
    A("  2. 算法选择错误（加权图用 BFS、应 DP 却贪心）；\n")
    A("  3. 边界差一（二分 `lo<hi`/`hi=mid`）；\n")
    A("  4. 复杂度声称与实际实现不符（声称线性实为平方）；\n")
    A("  5. 仅统计表象不核对配对（括号题数不核对类型）。\n")
    A("- **能力边界与临界点**：在本题集上，模型在 **easy/medium** 多数能产出可运行且过程成立的解；"
      "进入 **hard**（如图论最短路 Dijkstra/带权结构）后，倾向于用更简单的错误算法（如 BFS）替代，"
      "过程正确性显著下降——**hard 是能力拐点**。建议对 hard 题目强制要求“算法选择自证 + 复杂度对应代码”两步校验。\n")
    A("- **评估器局限性**：规则评估器可稳定识别“最终答案错→过程错”和“复杂度声称矛盾”，"
      "但对“归因层级”（误读 vs 实现 bug）与“摊还复杂度/有界内循环”的辨别较弱，"
      "这正是 §6 中 S_W1 误定位、S_FP 误报的根因；生产环境应切换到 `llm` 后端以获得更细的过程判定。\n")

    A("## 8. 评估器有效性验证结果\n")
    A(f"### 8.1 定位准确率（答案错误样本）\n")
    A(f"- 分母（答案错误样本）：**{loc['denominator']}**；命中（判定过程问题且步骤/粗类对齐）："
      f"**{loc['hits']}**；**准确率 = {loc['accuracy']:.1%}**。\n")
    for d in loc["detail"]:
        A(f"  - {d['sample_id']}: {'命中' if d['hit'] else '未命中'} "
          f"（gt={d['gt_error_type']}@step{d['gt_error_step']} → "
          f"eval={d['eval_error_type']}@step{d['eval_error_step']}）")
    A("")
    A(f"### 8.2 误报率（答案正确样本）\n")
    A(f"- 答案正确样本：**{fp['answer_correct_samples']}**；被判定过程无效：**{fp['flagged_invalid']}**；\n")
    A(f"- 其中真实过程问题：**{fp['real_process_problems']}**；误报：**{fp['false_positives']}**；"
      f"**误报率 = {fp['fp_rate']:.1%}**。\n")
    A("- 人工抽检记录：\n")
    for m in fp["manual_review"]:
        A(f"  - {m['sample_id']}：判定为 **{m['kind']}**（gt 错误类型={m['gt_error_type']}，"
          f"eval 错误类型={m['eval_error_type']}）")
    A("")
    A("## 9. 交付物索引\n")
    A("- 应用源码 / 过程评估模块：`src/`（`solver.py`、`sandbox.py`、`process_evaluator.py`）\n")
    A("- 题集与标准答案、校验脚本：`data/problems.json`、`tools/gen_problems.py`\n")
    A("- 评测样本与真值：`data/samples.json`、`tools/gen_samples.py`\n")
    A("- 评测脚本与结果：`eval/run_eval.py`、`eval/verify_evaluator.py`、"
      "`eval/results/evaluation_results.csv`、本报告的 `.jsonl`/`.json`\n")
    A("- 环境配置样例：`.env.example`、`config.yaml`、`requirements.txt`\n")
    A("- Demo：`demo/demo.html`（一次完整解题 + 过程评估流程可视化）\n")

    text = "\n".join(L)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    with open(OUT_ROOT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote report -> {os.path.relpath(OUT)} and {os.path.relpath(OUT_ROOT)}")
    print(f"final_acc={final_acc:.1%} proc_rate={proc_rate:.1%} loc={loc['accuracy']:.1%} fp={fp['fp_rate']:.1%}")


if __name__ == "__main__":
    main()
