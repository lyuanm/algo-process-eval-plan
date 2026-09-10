# -*- coding: utf-8 -*-
"""全量跑批的完整日志留存（append-only）。

留存目标：把「Hy3 返回的答案」与「项目模型的判断检测」全过程落盘，做到事后可复核。
  - 求解侧  solve_trace.jsonl ：完整 prompt、逐次尝试的原始响应与失败原因
  - 评估侧  eval_trace.jsonl  ：逐用例 verdict（期望/实际/异常）、四步骤判定、
                                错误归因、压力测试差分结果

两个关键设计取舍：

1) **成功与失败都写**。断点续跑用的缓存（hy3_solutions.jsonl）只存成功结果，因为
   它只服务于「不重复烧 API」；但失败记录（Mock 降级 / 超时 / 空响应）恰恰是回答
   「为什么某题跑不出来、要不要调并发或超时」的唯一依据，必须单独留存。

2) **append-only + 每行 flush**。跑批是数小时的长任务，随时可能被中断；逐行追加的
   jsonl 即使进程被杀，已写记录依然完整可读（读取侧另有残行容忍）。

落盘的是机器可读的 jsonl；人可读的 markdown 由 tools/gen_run_logs.py 渲染。
"""
from __future__ import annotations

import json
import os
import threading
import time
from collections import Counter
from typing import Dict, List, Optional

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LOG_DIR = os.path.join(ROOT, "eval", "logs")

SOLVE_TRACE = os.path.join(LOG_DIR, "solve_trace.jsonl")
EVAL_TRACE = os.path.join(LOG_DIR, "eval_trace.jsonl")

_locks: Dict[str, threading.Lock] = {}
_lock_guard = threading.Lock()

# 求解尝试的终态分类，供人可读日志分组统计
STATUS_LABEL = {
    "ok": "成功",
    "mock_degraded": "Mock 降级（网关调用失败）",
    "empty": "空响应",
    "exception": "异常抛出",
}

# 早期缓存记录没有 model 字段，那批解答都是用默认模型 hy3 产出的
LEGACY_MODEL = "hy3"


def solution_provenance(sol_cache_path: str) -> Dict[str, int]:
    """统计解答缓存中各模型的题量，返回 {模型名: 题数}（按题数降序）。

    全量跑批会因额度/容量问题中途换模型，同一份结果集因此可能来自多个模型。
    交付物**必须**显式披露这一构成——否则「513 题的答案正确率 85%」会被读成
    「某一个模型在 513 题上的表现」，而实际是多个模型的混合结果，含义完全不同。
    """
    counts: Counter = Counter()
    for r in read_jsonl(sol_cache_path):
        counts[r.get("model") or LEGACY_MODEL] += 1
    return dict(counts.most_common())


def _lock_for(path: str) -> threading.Lock:
    with _lock_guard:
        if path not in _locks:
            _locks[path] = threading.Lock()
    return _locks[path]


def append_jsonl(path: str, rec: Dict) -> None:
    """线程安全地追加一行 jsonl（立即 flush，保证进程被中断也不丢已写记录）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False)
    with _lock_for(path):
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()


def read_jsonl(path: str) -> List[Dict]:
    """读取 jsonl，跳过被中断截断的残行（与 run_full.read_jsonl 语义一致）。"""
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
                pass
    return out


def log_solve(
    problem,
    prompt: str,
    attempts: List[Dict],
    final_status: str,
    raw: str,
    ts: Optional[str] = None,
    backfilled: bool = False,
    model: Optional[str] = None,
    inline: bool = False,
) -> None:
    """记录一道题的求解全过程（含每一次尝试）。

    attempts 每项形如 {"n":1,"status":"mock_degraded","reason":"Request timed out.",
                       "elapsed":180.2,"response_chars":0}
    backfilled=True 表示该条由已有解答缓存补导出（缺逐次尝试明细），用于在日志里
    显式区分「跑批实时记录」与「事后补录」，避免读者误以为失败尝试也被完整保留。

    model 记录**实际调用**的模型名。额度耗尽时会中途切换模型（如 hy3 → hy4-preview）
    继续跑剩余题目，同一份结果集因此可能来自多个模型；日志若不逐题标注模型，
    就无法说明某一批指标究竟出自哪个模型。

    inline=True 表示该解答由会话内助手直接撰写、未经外部 API 调用。这类解答与 API
    产出在性质上不同（同会话、可反复修改），必须显式区分。
    """
    append_jsonl(SOLVE_TRACE, {
        "problem_id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "domain": problem.domain,
        "source": "hy3",
        "model": model or os.getenv("HY3_MODEL", "hy3"),
        "inline": inline,
        "final_status": final_status,
        "attempt_count": len(attempts),
        "attempts": attempts,
        "prompt": prompt,
        "prompt_chars": len(prompt),
        "raw_response": raw,
        "response_chars": len(raw or ""),
        "backfilled": backfilled,
        "ts": ts or time.strftime("%Y-%m-%d %H:%M:%S"),
    })


def log_eval(problem, rec: Dict, raw_solution: str, ts: Optional[str] = None) -> None:
    """记录一道题的完整评估判定（题目上下文 + 逐用例 verdict + 四步骤 + 归因）。"""
    append_jsonl(EVAL_TRACE, {
        "problem_id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "domain": problem.domain,
        "ts": ts or time.strftime("%Y-%m-%d %H:%M:%S"),
        # 题目上下文：让日志自包含，单看一条即可复核判定是否合理
        "problem_context": {
            "description": problem.description,
            "input_format": problem.input_format,
            "output_format": problem.output_format,
            "constraints": problem.constraints,
            "test_case_count": len(problem.test_cases),
        },
        # 判定结论
        "verdict": {
            "final_correct": rec.get("final_correct"),
            "passed_cases": rec.get("passed_cases"),
            "total_cases": rec.get("total_cases"),
            "verdict_summary": rec.get("verdict_summary"),
            "first_failure_verdict": rec.get("first_failure_verdict"),
            "process_valid": rec.get("process_valid"),
            "error_step": rec.get("error_step"),
            "error_type": rec.get("error_type"),
            "error_type_name": rec.get("error_type_name"),
            "note": rec.get("note"),
            "backend": rec.get("backend"),
            "confidence": rec.get("confidence"),
            "eval_sec": rec.get("eval_sec"),
        },
        # 判定依据：逐用例明细 + 压力测试差分
        "case_verdicts": rec.get("case_verdicts") or [],
        "stress_summary": rec.get("stress_summary"),
        "stress_case_verdicts": rec.get("stress_case_verdicts") or [],
        # 判定对象：被评估的模型输出本身
        "step_verdicts": rec.get("step_verdicts") or [],
        "raw_solution": raw_solution,
        "solution_chars": len(raw_solution or ""),
    })
