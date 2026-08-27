"""可执行验证（ERV, Executable Verification）与压力测试。

借鉴竞赛编程判题层级（AC/WA/TLE/RE/CE）与 ProcessBench / GenPRM 的
「以执行为金标准」思想：把每测试用例的执行结果细分为可判定的 verdict，
并支持在参考解上做差分压力测试，以降低「巧合格式通过」造成的误判。

- classify_case: 单个测试用例 -> AC/WA/TLE/RE/CE
- execution_verdict: 对解法跑全部用例，给出每用例 verdict 与汇总
- stress_verdict: （可选）对压力测试集评估，捕捉主测试集漏掉的错误
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from .problems import Problem, TestCase
from .sandbox import RunResult, run_code


@dataclass
class CaseVerdict:
    index: int
    verdict: str            # AC / WA / TLE / RE / CE
    expected: str
    actual: str
    exception: str = ""


@dataclass
class ExecVerdict:
    cases: List[CaseVerdict]
    passed: int
    total: int
    final_correct: bool
    first_failure: Optional[CaseVerdict]
    summary: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["first_failure"] = asdict(self.first_failure) if self.first_failure else None
        return d


def classify_case(res: RunResult, problem: Problem, tc: TestCase) -> CaseVerdict:
    """把一次沙盒执行映射为细粒度 verdict。"""
    exception = ""
    if res.timed_out:
        verdict = "TLE"
    elif not res.ok:
        # 语法错误单独记为 CE
        if re.search(r"SyntaxError|IndentationError", res.stderr or ""):
            verdict = "CE"
        else:
            verdict = "RE"
            m = re.search(r"(\w+Error):\s*(.*)", res.stderr or "")
            if m:
                exception = f"{m.group(1)}: {m.group(2)[:80]}"
    elif problem.check_answer(res.stdout, tc.expected):
        verdict = "AC"
    else:
        verdict = "WA"
    return CaseVerdict(
        index=tc.index if hasattr(tc, "index") else 0,
        verdict=verdict,
        expected=str(tc.expected),
        actual=(res.stdout or "").strip()[:200],
        exception=exception,
    )


def execution_verdict(
    problem: Problem, code: str, timeout: float = 5.0, tests: Optional[List[TestCase]] = None
) -> ExecVerdict:
    """对解法执行（默认）主测试用例，返回每用例 verdict 与汇总。"""
    tests = tests if tests is not None else problem.test_cases
    cases: List[CaseVerdict] = []
    for i, tc in enumerate(tests):
        res = run_code(code, tc.input, timeout=timeout)
        cv = classify_case(res, problem, tc)
        cv.index = i
        cases.append(cv)
    passed = sum(1 for c in cases if c.verdict == "AC")
    total = len(cases)
    final_correct = passed == total
    first_failure = next((c for c in cases if c.verdict != "AC"), None)
    # 汇总文本
    counts = {}
    for c in cases:
        counts[c.verdict] = counts.get(c.verdict, 0) + 1
    summary = " ".join(f"{k}:{v}" for k, v in counts.items()) or "无用例"
    return ExecVerdict(
        cases=cases,
        passed=passed,
        total=total,
        final_correct=final_correct,
        first_failure=first_failure,
        summary=summary,
    )


def stress_verdict(
    problem: Problem, code: str, timeout: float = 5.0
) -> Optional[ExecVerdict]:
    """（可选）差分压力测试：以参考解为 oracle，在每个压力输入上同时运行
    参考解(期望)与待测解(实际)，逐用例比较。待测解输出与参考解不一致即判
    WA/RE。这样无需为压力用例手工标注答案，且能捕捉「主测试集巧合通过」
    （coincidence）的样本——呼应 GenPRM / ProcessBench 的「以执行为金标准」
    与竞赛判题的隐藏用例思想。无压力输入时返回 None。
    """
    inputs = getattr(problem, "stress_inputs", None)
    if not inputs:
        return None
    cases: List[CaseVerdict] = []
    for i, inp in enumerate(inputs):
        oracle = run_code(problem.reference_solution, inp, timeout=timeout)
        actual = run_code(code, inp, timeout=timeout)
        if not oracle.ok:
            # 参考解自身异常（生成器瑕疵），该压力用例作废，跳过
            continue
        if not actual.ok:
            verdict = "RE"
            exception = (actual.stderr or "")[:80]
        elif actual.stdout.strip() == oracle.stdout.strip():
            verdict = "AC"
            exception = ""
        else:
            verdict = "WA"
            exception = ""
        cases.append(CaseVerdict(
            index=i,
            verdict=verdict,
            expected=oracle.stdout.strip()[:200],
            actual=(actual.stdout or "").strip()[:200],
            exception=exception,
        ))
    if not cases:
        return None
    passed = sum(1 for c in cases if c.verdict == "AC")
    total = len(cases)
    first_failure = next((c for c in cases if c.verdict != "AC"), None)
    counts: dict = {}
    for c in cases:
        counts[c.verdict] = counts.get(c.verdict, 0) + 1
    summary = " ".join(f"{k}:{v}" for k, v in counts.items())
    return ExecVerdict(
        cases=cases,
        passed=passed,
        total=total,
        final_correct=passed == total,
        first_failure=first_failure,
        summary=summary,
    )


def deep_erv_note(ev: ExecVerdict, sv: Optional[ExecVerdict]) -> str:
    """生成 ERV 解读文本，供评估器/UI 使用。"""
    parts = [f"主测试集 {ev.summary}"]
    if sv is not None:
        if sv.final_correct:
            parts.append(f"压力测试 {sv.summary}（一致，过程稳健）")
        else:
            parts.append(
                f"压力测试 {sv.summary}（与参考解不一致，主测试集存在巧合通过风险）"
            )
    return "；".join(parts)
