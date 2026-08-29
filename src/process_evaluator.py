"""过程评估器：评估解题过程是否成立，并定位错误、归类错误类型。

实现两种后端（config.yaml 中 evaluator.backend 选择）：
  - rule：规则 + 沙盒「可执行验证(ERV)」的离线评估器，无需 Hy3 即可运行（演示/CI）。
  - llm ：以 Hy3 做逐步 LLM-as-judge，产出更细的过程判定（生产推荐）。

设计依据（近年论文）：
  - ProcessBench(Zheng'24) / PRMBench(Song'25)：以「最早错误步骤定位」为核心评估目标，
    并指出专用过程奖励模型(PRM)在逐步验证上优于通用 LLM-as-judge。
  - GenPRM(Zhao'25) / ThinkPRM(Khalifa'25)：把「代码执行结果」作为验证金标准，
    让验证器基于事实推理（而非猜测），并以更长的思维链/测试时缩放提升精度。
  - JETTS(Zhou'25, ICML) / MCTS-Judge：多次裁判 + 多数投票（测试时缩放）可提升裁判稳定性。
  - Wei'25(arXiv:2506.22954) 层次化竞赛编程错误分类 + 可执行验证判题层级
    （AC/WA/TLE/RE/CE），作为本评估器错误分类与 verdict 划分的参考。

步骤编号方案（评估器与人工标注共用）：
  step 1 = 思路/建模 ；step 2 = 复杂度分析 ；step 3 = 边界与处理 ；step 4 = 代码实现
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

from .problems import Problem
from .sandbox import run_code
from .solver import Solution
from .taxonomy import (
    COARSE_CATEGORY,
    ERROR_TYPES,
    TAXONOMY_TREE,
    VERDICT_TYPES,
    coarse_of,
    describe,
)
from .verdict import (
    CaseVerdict,
    deep_erv_note,
    execution_verdict,
    stress_verdict,
)

STEP_APPROACH = 1
STEP_COMPLEXITY = 2
STEP_BOUNDARY = 3
STEP_CODE = 4
STEP_NAMES = {1: "思路/建模", 2: "复杂度分析", 3: "边界与处理", 4: "代码实现"}


@dataclass
class StepVerdict:
    step: int
    name: str
    ok: bool
    reason: str


@dataclass
class ProcessEvalResult:
    problem_id: str
    sample_id: str
    final_correct: bool
    passed_cases: int
    total_cases: int
    process_valid: bool
    step_verdicts: List[StepVerdict]
    error_step: Optional[int]
    error_type: Optional[str]
    error_type_name: Optional[str]
    note: str
    backend: str
    verdict_summary: str = ""       # ERV 汇总（AC/WA/TLE/RE/CE 计数）
    first_failure_verdict: Optional[str] = None
    stress_summary: str = ""         # 压力测试差分汇总（与参考解一致性）
    confidence: Optional[float] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["step_verdicts"] = [asdict(s) for s in self.step_verdicts]
        return d


# ----------------------------- 工具函数 -----------------------------
def _loop_nesting(code: str) -> int:
    """粗略计算最大循环嵌套层数（用于复杂度一致性判断）。"""
    lines = code.splitlines()
    stack = []
    max_nest = 0
    for ln in lines:
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        while stack and stack[-1] >= indent:
            stack.pop()
        if re.match(r"\s*(for|while)\s+", ln):
            stack.append(indent)
            max_nest = max(max_nest, len(stack))
    return max_nest


def _claimed_complexity(reasoning: str) -> Optional[str]:
    m = re.search(r"O\(([^)]+)\)", reasoning)
    return m.group(1).strip() if m else None


def _uses_hash(reasoning: str, code: str) -> bool:
    return ("哈希" in reasoning or "hash" in reasoning.lower() or "字典" in reasoning) and (
        "dict" in code or "set(" in code or "{}" in code
    )


def _parse_reasoning_steps(reasoning: str):
    """把推理文本按四段拆分为步骤文本。"""
    steps = {
        STEP_APPROACH: "",
        STEP_COMPLEXITY: "",
        STEP_BOUNDARY: "",
        STEP_CODE: "",
    }
    text = reasoning
    parts = re.split(r"##\s*", text)
    for part in parts:
        if not part.strip():
            continue
        head = part.strip().splitlines()[0]
        body = "\n".join(part.strip().splitlines()[1:])
        if "思路" in head or "建模" in head:
            steps[STEP_APPROACH] += body + "\n"
        elif "复杂度" in head:
            steps[STEP_COMPLEXITY] += body + "\n"
        elif "边界" in head or "处理" in head:
            steps[STEP_BOUNDARY] += body + "\n"
        else:
            steps[STEP_APPROACH] += part + "\n"
    return steps


def _format_verdict_facts(ev) -> str:
    """把沙盒执行 verdict 格式化为裁判可读的事实文本（金标准）。"""
    lines = []
    for c in ev.cases:
        extra = f" | 异常：{c.exception}" if c.exception else ""
        lines.append(
            f"用例#{c.index + 1} [{c.verdict}] 期望={c.expected!r} 实际={c.actual!r}{extra}"
        )
    return "\n".join(lines)


# ----------------------------- 规则评估器 -----------------------------
class RuleBasedProcessEvaluator:
    """离线评估器：沙盒「可执行验证(ERV)」+ 规则启发式。生产环境建议切换 llm 后端。"""

    def __init__(self, timeout: float = 5.0, use_stress: bool = False):
        self.timeout = timeout
        self.use_stress = use_stress

    def evaluate(self, problem: Problem, solution: Solution) -> ProcessEvalResult:
        # 1) 沙盒 ERV -> 真实最终答案正确性 + 每用例 verdict
        ev = execution_verdict(problem, solution.code, timeout=self.timeout)
        sv = stress_verdict(problem, solution.code, timeout=self.timeout) if self.use_stress else None
        final_correct = ev.final_correct
        fv = ev.first_failure

        steps = _parse_reasoning_steps(solution.reasoning)
        nesting = _loop_nesting(solution.code)
        claimed = _claimed_complexity(solution.reasoning)

        step_verdicts: List[StepVerdict] = []
        error_step = None
        error_type = None
        process_valid = True
        note = ""

        linear_claim = bool(re.fullmatch(r"[a-z]", claimed)) if claimed else False
        complexity_conflict = bool(claimed) and linear_claim and nesting >= 2

        for sid in (STEP_APPROACH, STEP_COMPLEXITY, STEP_BOUNDARY, STEP_CODE):
            ok = True
            reason = "无明显问题"
            if sid == STEP_COMPLEXITY and complexity_conflict:
                ok = False
                reason = f"声称 O({claimed}) 但代码最大循环嵌套为 {nesting}（实际约 O(n^{nesting})）"
            step_verdicts.append(StepVerdict(sid, STEP_NAMES[sid], ok, reason))

        if not final_correct:
            process_valid = False
            if complexity_conflict:
                error_step = STEP_COMPLEXITY
                error_type = "complexity_error"
            else:
                error_step = STEP_CODE
                error_type = "logic_error"
            note = f"最终答案错误（主测试集 {ev.summary}）"
            if fv:
                note += f"；首错用例#{fv.index + 1}={fv.verdict}"
                if fv.exception:
                    note += f" 异常：{fv.exception}"
            if sv is not None and not sv.final_correct:
                note += "；压力测试亦未通过"
        else:
            if complexity_conflict:
                process_valid = False
                error_step = STEP_COMPLEXITY
                error_type = "complexity_error"
                note = "最终答案通过，但复杂度声称与代码实现不一致（过程不成立）。"
            elif _uses_hash(solution.reasoning, solution.code) is False and (
                "哈希" in solution.reasoning or "hash" in solution.reasoning.lower()
            ):
                process_valid = False
                error_step = STEP_APPROACH
                error_type = "concept_error"
                note = "声称使用哈希表，但代码未使用相应结构（方法名实不符）。"
            else:
                process_valid = True
                note = f"最终答案通过（{ev.summary}）"
                if sv is not None and not sv.final_correct:
                    process_valid = False
                    error_step = STEP_CODE
                    error_type = "logic_error"
                    note = "主测试集通过，但压力测试未通过（过程疑似巧合成立，稳健性不足）。"

        return ProcessEvalResult(
            problem_id=solution.problem_id,
            sample_id=getattr(solution, "sample_id", solution.problem_id),
            final_correct=final_correct,
            passed_cases=ev.passed,
            total_cases=ev.total,
            process_valid=process_valid,
            step_verdicts=step_verdicts,
            error_step=error_step,
            error_type=error_type,
            error_type_name=ERROR_TYPES.get(error_type) if error_type else None,
            note=note,
            backend="rule",
            verdict_summary=ev.summary,
            first_failure_verdict=fv.verdict if fv else None,
            stress_summary=sv.summary if sv is not None else "",
        )


# ----------------------------- LLM-as-judge 评估器 -----------------------------
LLM_RUBRIC = """你是一名算法竞赛题解答的 rigor 评审。下面给出一道题的标准信息与一份模型解答，
以及该解答在沙盒中的【真实执行结果】（可执行验证 ERV，作为金标准，请勿猜测对错）。

评估要点：
- 事实优先：以「真实执行结果」为准，不要凭空猜测最终答案是否正确。
- 过程正确性：推理链是否闭环（跳步、循环论证、误用数据结构/定理、条件遗漏、幻觉）。
- 错误步骤定位：若过程有问题，指出错误首次出现的步骤：
    1=思路/建模, 2=复杂度分析, 3=边界与处理, 4=代码实现。
- 错误类型（从下列选一，或 null）：
    misread_problem(题意误读), concept_error(概念理解错误), calculation_error(计算错误),
    condition_omission(条件遗漏), step_skip(跳步推导), logic_error(逻辑错误),
    complexity_error(复杂度/效率错误), format_error(格式不符), hallucination(幻觉/虚构),
    boundary_error(边界处理错误)。
- 特别地：识别「最终答案看似正确但过程不成立」的情况（复杂度声称与代码不符、
    声称方法与实际不符、靠巧合/硬编码通过、压力测试不稳定）。

题目标准信息：
标题：{title}
难度：{difficulty}
描述：{description}
约束：{constraints}

真实执行结果（用例 verdict：AC=通过 WA=输出错 TLE=超时 RE=运行异常 CE=编译错）：
{verdict_facts}

模型解答：
{raw}

仅输出如下 JSON（不要输出多余内容）：
{{"final_correct_guess": <bool>, "process_valid": <bool>, "error_step": <int|null>,
  "error_type": <str|null>, "confidence": <float 0~1>,
  "step_verdicts": [{{"step":<int>,"ok":<bool>,"reason":<str>}}],
  "note": <str>}}
"""


class LLMProcessEvaluator:
    """以 Hy3 做逐步 LLM-as-judge（生产推荐）。支持自一致性（多次裁判多数投票）。"""

    def __init__(self, client, timeout: float = 5.0, judge_samples: int = 1, use_stress: bool = False):
        self.client = client
        self.timeout = timeout
        self.judge_samples = max(1, int(judge_samples))
        self.use_stress = use_stress

    def _single_judge(self, problem: Problem, solution: Solution, ev, stress_facts: str) -> Optional[Dict]:
        facts = _format_verdict_facts(ev)
        if stress_facts:
            facts += "\n\n【差分压力测试】（以参考解为 oracle，待测解与参考解输出逐用例比较）：\n" + stress_facts
        prompt = LLM_RUBRIC.format(
            title=problem.title,
            difficulty=problem.difficulty,
            description=problem.description,
            constraints=problem.constraints,
            verdict_facts=facts,
            raw=solution.raw,
        )
        out = self.client.chat([{"role": "user", "content": prompt}], reasoning_effort="high")
        return self._parse_json(out)

    def evaluate(self, problem: Problem, solution: Solution) -> ProcessEvalResult:
        # 1) 沙盒 ERV -> 真实最终答案正确性（金标准，覆盖模型自述）
        ev = execution_verdict(problem, solution.code, timeout=self.timeout)
        final_correct = ev.final_correct
        fv = ev.first_failure

        # 1b) 差分压力测试（可选）：以参考解为 oracle，捕捉巧合通过
        sv = stress_verdict(problem, solution.code, timeout=self.timeout) if self.use_stress else None
        stress_facts = ""
        if sv is not None:
            for c in sv.cases:
                extra = f" | 异常：{c.exception}" if c.exception else ""
                stress_facts += (
                    f"压力用例#{c.index + 1} [{c.verdict}] "
                    f"参考解={c.expected!r} 待测解={c.actual!r}{extra}\n"
                )
            stress_facts += f"（压力汇总：{sv.summary}）"

        # 2) 多次裁判 + 多数投票（测试时缩放 / 自一致性）
        votes: List[Tuple[Optional[int], Optional[str]]] = []
        confs: List[float] = []
        best_step_verdicts: List[StepVerdict] = []
        best_note = ""
        for _ in range(self.judge_samples):
            parsed = self._single_judge(problem, solution, ev, stress_facts)
            if not parsed:
                continue
            et = parsed.get("error_type")
            et = et if et in ERROR_TYPES else None
            es = parsed.get("error_step")
            votes.append((es, et))
            confs.append(float(parsed.get("confidence", 0.5) or 0.5))
            if not best_step_verdicts:
                best_step_verdicts = [
                    StepVerdict(s.get("step", 0), STEP_NAMES.get(s.get("step", 0), "未知"),
                                bool(s.get("ok", True)), s.get("reason", ""))
                    for s in parsed.get("step_verdicts", [])
                ]
                best_note = parsed.get("note", "")

        if not votes:
            # 裁判完全失败：退回基于 ERV 的规则兜底
            return RuleBasedProcessEvaluator(self.timeout, use_stress=self.use_stress).evaluate(problem, solution)

        # 多数投票：以 (error_step, error_type) 整体计票，平票取置信度更高者
        pair_counter = Counter(votes)
        (error_step, error_type), _ = pair_counter.most_common(1)[0]
        if error_type is not None and error_type not in ERROR_TYPES:
            error_type = None
        avg_conf = sum(confs) / len(confs)

        process_valid = bool(error_type is None and error_step is None)
        # 若答案错误，则过程必存在问题
        if not final_correct:
            process_valid = False
            if error_type is None:
                error_type = "logic_error"
                error_step = error_step or STEP_CODE

        # 差分压力测试兜底：主测试集通过但压力不一致 -> 过程不稳健（巧合通过）
        stress_note = ""
        if sv is not None and not sv.final_correct:
            if final_correct and process_valid:
                process_valid = False
                error_type = error_type or "logic_error"
                error_step = error_step or STEP_CODE
                stress_note = "主测试集通过，但差分压力测试与参考解不一致（过程疑似巧合成立，稳健性不足）。"
            elif not final_correct:
                stress_note = "差分压力测试亦与参考解不一致，进一步佐证过程错误。"

        note = stress_note or best_note or f"LLM 裁判（{self.judge_samples} 次投票）结论。"

        return ProcessEvalResult(
            problem_id=solution.problem_id,
            sample_id=getattr(solution, "sample_id", solution.problem_id),
            final_correct=final_correct,
            passed_cases=ev.passed,
            total_cases=ev.total,
            process_valid=process_valid,
            step_verdicts=best_step_verdicts,
            error_step=error_step,
            error_type=error_type,
            error_type_name=ERROR_TYPES.get(error_type) if error_type else None,
            note=note,
            backend="llm",
            verdict_summary=ev.summary,
            first_failure_verdict=fv.verdict if fv else None,
            stress_summary=sv.summary if sv is not None else "",
            confidence=round(avg_conf, 3),
        )

    @staticmethod
    def _parse_json(text: str) -> Optional[Dict]:
        try:
            s = text[text.index("{") : text.rindex("}") + 1]
            return json.loads(s)
        except Exception:
            return None


def build_evaluator(backend: str, client=None, timeout: float = 5.0, judge_samples: int = 1, use_stress: bool = False):
    if backend == "llm" and client is not None:
        return LLMProcessEvaluator(client, timeout=timeout, judge_samples=judge_samples, use_stress=use_stress)
    return RuleBasedProcessEvaluator(timeout=timeout, use_stress=use_stress)
