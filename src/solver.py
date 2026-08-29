"""求解器：基于 Hy3 产出完整解题过程（而非仅最终答案）。

输出约定（供过程评估器解析）：
  ## 思路
  ...
  ## 复杂度分析
  时间：... 空间：...
  ## 边界与处理
  ...
  ## 代码
  ```python
  ...完整脚本（从 stdin 读、stdout 写）...
  ```
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .hy3_client import Hy3Client
from .problems import Problem

SOLVE_PROMPT = """你是一名资深算法竞赛选手。请针对下面的算法题，给出"完整解题过程"，不要只给最终答案。

要求：
1. ## 思路：说明建模方式、核心算法/数据结构选择及为什么正确。
2. ## 复杂度分析：给出时间复杂度与空间复杂度，并说明来源（与代码对应）。
3. ## 边界与处理：列出输入约束下的退化情况（空/单元素/重复/极值/负权/大数等）及处理方法。
4. ## 代码：给出可直接运行的 Python 脚本，从标准输入 stdin 读取（格式见"输入格式"），向标准输出 stdout 打印（格式见"输出格式"）。不要使用 input() 之外的交互；不要读取文件。

【题目】
{title}（难度：{difficulty}，领域：{domain}）

{description}

输入格式：
{input_format}

输出格式：
{output_format}

约束：
{constraints}
"""


@dataclass
class Solution:
    problem_id: str
    reasoning: str          # 自然语言过程（不含代码）
    code: str               # 解析出的可运行代码
    raw: str                # 模型原始输出
    source: str = "hy3"     # hy3 / sample


_CODE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def parse_solution(raw: str) -> Solution:
    """从模型输出中拆出推理文本与代码块。"""
    m = _CODE_RE.search(raw)
    code = m.group(1).strip() if m else ""
    reasoning = raw
    if m:
        # 去掉代码块，保留其余作为推理
        reasoning = (raw[: m.start()] + raw[m.end():]).strip()
    return Solution(
        problem_id="",
        reasoning=reasoning,
        code=code,
        raw=raw,
        source="hy3",
    )


def solve_problem(client: Hy3Client, problem: Problem) -> Solution:
    prompt = SOLVE_PROMPT.format(
        title=problem.title,
        difficulty=problem.difficulty,
        domain=problem.domain,
        description=problem.description,
        input_format=problem.input_format,
        output_format=problem.output_format,
        constraints=problem.constraints,
    )
    raw = client.chat(
        [{"role": "user", "content": prompt}],
        reasoning_effort="high",
    )
    sol = parse_solution(raw)
    sol.problem_id = problem.id
    return sol
