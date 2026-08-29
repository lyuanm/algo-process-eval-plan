"""题目加载与答案校验。

数据格式见 data/problems.json：
  - 每题含 description / input_format / output_format / constraints
  - reference_solution：可运行的参考解（完整脚本，从 stdin 读、stdout 写）
  - check_mode：内置判定模式（见 _CHECKERS），优先于 checker_src
  - checker_src：可选的自定义 check(actual, expected) 源码
  - test_cases：[{input, expected}, ...]
  - source：题源标注（LeetCode N / 洛谷 PXXXX 等）

"可自动校验的判定方式"由 check_mode / checker_src 提供；run_eval 会先用
reference_solution 跑一遍所有 test_cases，确认题集自身标注正确（即标准答案可信）。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .sandbox import run_code


@dataclass
class TestCase:
    input: str
    expected: str


@dataclass
class Problem:
    id: str
    title: str
    difficulty: str  # easy / medium / hard
    domain: str
    description: str
    input_format: str
    output_format: str
    constraints: str
    reference_solution: str
    checker_src: str = ""
    check_mode: str = "exact"
    test_cases: List[TestCase] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source: str = ""
    stress_inputs: List[str] = field(default_factory=list)

    def custom_checker(self) -> Optional[Callable[[str, str], bool]]:
        if not self.checker_src:
            return None
        ns: Dict[str, Any] = {}
        exec(self.checker_src, ns)  # 题集为项目自带可信数据
        return ns.get("check")

    def check_answer(self, actual: str, expected: str) -> bool:
        fn = self.custom_checker()
        if fn is not None:
            try:
                return bool(fn(actual, expected))
            except Exception:
                pass
        mode = self.check_mode or "exact"
        checker = _CHECKERS.get(mode, _CHECKERS["exact"])
        try:
            return bool(checker(actual, expected))
        except Exception:
            return actual.strip() == expected.strip()


def _safe_int(s: str):
    s = s.strip()
    if s == "":
        raise ValueError("empty")
    return int(s)


def _safe_float(s: str):
    return float(s.strip())


def _ints(s: str):
    return [int(x) for x in s.split()]


_CHECKERS: Dict[str, Callable[[str, str], bool]] = {
    "int": lambda a, e: _safe_int(a) == _safe_int(e),
    "float": lambda a, e: abs(_safe_float(a) - _safe_float(e)) < 1e-6,
    "int_list": lambda a, e: _ints(a) == _ints(e),
    "int_list_sorted": lambda a, e: sorted(_ints(a)) == sorted(_ints(e)),
    "bool": lambda a, e: a.strip().lower() == e.strip().lower(),
    "str": lambda a, e: a.strip() == e.strip(),
    "token_list": lambda a, e: a.split() == e.split(),
    "exact": lambda a, e: a.strip() == e.strip(),
}


def load_problems(path: str) -> List[Problem]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    problems: List[Problem] = []
    for p in raw:
        problems.append(
            Problem(
                id=p["id"],
                title=p["title"],
                difficulty=p["difficulty"],
                domain=p["domain"],
                description=p["description"],
                input_format=p["input_format"],
                output_format=p["output_format"],
                constraints=p["constraints"],
                reference_solution=p["reference_solution"],
                checker_src=p.get("checker_src", ""),
                check_mode=p.get("check_mode", "exact"),
                test_cases=[TestCase(t["input"], str(t["expected"])) for t in p["test_cases"]],
                tags=p.get("tags", []),
                source=p.get("source", ""),
                stress_inputs=list(p.get("stress_inputs", [])),
            )
        )
    return problems


    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "difficulty": self.difficulty,
            "domain": self.domain,
            "description": self.description,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "constraints": self.constraints,
            "reference_solution": self.reference_solution,
            "checker_src": self.checker_src,
            "check_mode": self.check_mode,
            "test_cases": [{"input": t.input, "expected": t.expected} for t in self.test_cases],
            "tags": self.tags,
            "source": self.source,
            "stress_inputs": list(self.stress_inputs),
        }


def verify_problem_testcases(
    problem: Problem, timeout: float = 5.0
) -> Dict[str, Any]:
    """用参考解跑一遍题集，确认每题标准答案与用例自洽。"""
    passed = 0
    total = len(problem.test_cases)
    details = []
    for i, tc in enumerate(problem.test_cases):
        res = run_code(problem.reference_solution, tc.input, timeout=timeout)
        ok = res.ok and problem.check_answer(res.stdout, tc.expected)
        if ok:
            passed += 1
        details.append({"case": i + 1, "passed": ok, "stderr": res.stderr[:200]})
    return {
        "id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "domain": problem.domain,
        "source": problem.source,
        "total": total,
        "passed": passed,
        "all_passed": passed == total,
        "details": details,
    }


def build_catalog(problems: List[Problem]) -> Dict[str, Any]:
    """汇总题集覆盖度：平台 / 难度 / 领域分布。"""
    by_diff: Dict[str, int] = {}
    by_domain: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    for p in problems:
        by_diff[p.difficulty] = by_diff.get(p.difficulty, 0) + 1
        by_domain[p.domain] = by_domain.get(p.domain, 0) + 1
        key = "LeetCode" if "LeetCode" in p.source else ("洛谷" if "洛谷" in p.source else "通用")
        by_source[key] = by_source.get(key, 0) + 1
    return {
        "total": len(problems),
        "by_difficulty": by_diff,
        "by_domain": by_domain,
        "by_source": by_source,
    }
