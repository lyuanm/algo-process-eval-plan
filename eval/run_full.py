"""全量评测：对题库全部题目执行 「真实 Hy3 求解 -> 沙盒可执行验证 -> 过程评估」，
并汇总最终指标（供 Web 看板与报告消费）。

三个阶段彼此解耦，各自带断点续跑缓存，因此可以分开/重复执行而不重复烧 API：

  A. 求解  solve_all()  —— 并发调用 Hy3 生成四段式解题过程
             缓存：eval/results/hy3_solutions.jsonl      （key = problem_id）
             日志：eval/logs/solve_trace.jsonl           （完整 prompt + 原始回答，成功失败都记）
  B. 评估  evaluate_all() —— 并发执行 沙盒 ERV + 过程评估器
             缓存：eval/results/full_eval_<backend>.jsonl（key = problem_id）
             日志：eval/logs/eval_trace.jsonl            （逐用例 verdict + 四步骤判定 + 归因）
  C. 汇总  summarize()  —— 产出 eval/results/full_summary.json

用法：
  # 小规模试跑（先验证链路，再全量）
  python eval/run_full.py --limit 12 --workers 8

  # 全量（513 题）
  #   注意 --api-timeout：hard 题推理链长，实测单题生成最长 1066s。默认 180s 会让
  #   hard 题整题超时失败（日志里表现为 Mock 降级 + Request timed out.），必须调大。
  python eval/run_full.py --workers 6 --eval-workers 6 --api-timeout 1800 --deep-erv

  # 只补跑上轮未完成的题（缓存命中的题自动跳过），并加大超时
  python eval/run_full.py --skip-eval --workers 6 --api-timeout 3600

  # 复用已缓存的 Hy3 解答，只换评估后端重跑阶段 B
  python eval/run_full.py --backend llm --workers 4 --skip-solve

  # 只重新汇总
  python eval/run_full.py --summary-only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src import runlog  # noqa: E402
from src.hy3_client import (  # noqa: E402
    FatalAPIError,
    backoff_sleep,
    load_client_from_env,
)
from src.problems import load_problems  # noqa: E402
from src.process_evaluator import build_evaluator  # noqa: E402
from src.solver import Solution, build_prompt, parse_solution, solve_problem  # noqa: E402
from src.taxonomy import ERROR_TYPES, VERDICT_TYPES  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES_DIR = os.path.join(ROOT, "eval", "results")
SOL_CACHE = os.path.join(RES_DIR, "hy3_solutions.jsonl")

_print_lock = threading.Lock()

# hy3_client 在调用失败时会降级返回一段 Mock 文本（非空），必须显式识别并视为失败，
# 否则会被当成「有效解答」写进缓存，污染全量指标。
MOCK_MARK = "[OFFLINE MOCK"


def is_valid_solution(raw: str) -> bool:
    """判断是否为真实模型输出（排除空响应与 Mock 降级文本）。"""
    return bool(raw and raw.strip()) and MOCK_MARK not in raw


_MOCK_REASON = re.compile(r"\[Hy3 call failed: (.*?)\]", re.S)


def mock_reason(raw: str) -> str:
    """从 Mock 降级文本里提取真实失败原因。

    hy3_client 调用失败时会返回一段 Mock 文本，真正的原因（超时 / 429 / 5xx）
    被塞在 `[Hy3 call failed: ...]` 里。原先只打印笼统的「API 调用失败」，
    导致 hard 题批量失败时无法判断是网关限流还是单请求超时——而这两者的处置
    方式完全不同（前者降并发，后者加超时）。
    """
    m = _MOCK_REASON.search(raw or "")
    return (m.group(1).strip()[:160] or "原因未知") if m else "原因未知"


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def read_jsonl(path: str):
    """读取 jsonl 缓存，容忍被中断截断的残行。

    全量跑批是长任务（数小时），进程若被中途终止，最后一行可能是写了一半的
    残行。此处跳过无法解析的行而不是让整个缓存不可读，保证断点续跑始终可用。
    """
    if not os.path.exists(path):
        return []
    out, bad = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                bad += 1
    if bad:
        log(f"  [缓存] {os.path.basename(path)} 跳过 {bad} 行损坏数据（疑似上次中断截断）")
    return out


# ---------------------------------------------------------------- 阶段 A：求解
def solve_all(problems, ids, limit, workers, cache_path, max_try=3, quiet=True,
              api_timeout=None, model=None):
    """并发求解；返回 {problem_id: raw}。已缓存的题跳过（断点续跑）。"""
    cached = {}
    for r in read_jsonl(cache_path):
        if is_valid_solution(r.get("raw", "")):
            cached[r["problem_id"]] = r["raw"]
        else:
            log(f"  [A/求解] 丢弃无效缓存 {r.get('problem_id')}（空响应或 Mock 降级）")

    targets = ids or sorted(problems)
    if limit and not ids:
        targets = targets[:limit]
    todo = [t for t in targets if t not in cached]
    log(f"[A/求解] 目标 {len(targets)} 题，已缓存 {len(targets) - len(todo)} 题，待求解 {len(todo)} 题（{workers} 路并发）")
    if not todo:
        return cached

    client = load_client_from_env(timeout=api_timeout, model=model)
    used_model = getattr(client, "model", None) or (model or os.getenv("HY3_MODEL", "hy3"))
    log(f"[A/求解] 模型：{used_model}")
    if getattr(client, "use_mock", False):
        log("[A/求解] ⚠️ 未检测到有效凭证，将进入离线 Mock —— 结果不代表真实模型能力")

    fh = open(cache_path, "a", encoding="utf-8")
    lock = threading.Lock()
    done_n = [0]
    t0 = time.time()
    if getattr(client, "use_mock", False):
        log("[A/求解] ⚠️ 未检测到有效凭证，将进入离线 Mock —— 结果不代表真实模型能力")

    fh = open(cache_path, "a", encoding="utf-8")
    lock = threading.Lock()
    done_n = [0]
    t0 = time.time()

    def work(pid):
        prob = problems[pid]
        prompt = build_prompt(prob)
        attempts = []
        best = ("", 0.0, 0)  # (raw, 该次耗时, 第几次成功)

        def rec(n, status, reason, dt, raw):
            attempts.append({
                "n": n, "status": status, "reason": reason,
                "elapsed": round(dt, 1), "response_chars": len(raw or ""),
                "response_head": (raw or "")[:200],
            })

        for attempt in range(1, max_try + 1):
            t = time.time()
            try:
                sol = solve_problem(client, prob)
                raw = (sol.raw or "").strip()
            except FatalAPIError:
                # 账号级错误（欠费/凭证失效）——重试无意义，交给调用方终止整轮
                raise
            except Exception as e:  # 网络/解析异常都重试
                dt = time.time() - t
                rec(attempt, "exception", f"{type(e).__name__}: {e}", dt, "")
                log(f"  [{pid}] 第{attempt}次异常 {type(e).__name__}: {e}")
                if attempt < max_try:
                    backoff_sleep(attempt, base=2.0)
                continue
            dt = time.time() - t
            if is_valid_solution(raw):
                rec(attempt, "ok", "", dt, raw)
                best = (raw, dt, attempt)
                break
            status = "mock_degraded" if raw else "empty"
            reason = mock_reason(raw) if raw else "服务端返回空内容"
            rec(attempt, status, reason, dt, raw)
            # 超时是确定性失败：同一超时预算下重试只会再烧掉一遍等长的时间。
            # 实测 180s 超时叠加两层重试，单题最坏占用约 18 分钟，是吞吐崩塌的根因；
            # 这里立即放弃并留档，交由后续「加大 --api-timeout」的定向补跑处理。
            if "timed out" in reason.lower() or "timeout" in reason.lower():
                log(f"  [{pid}] 第{attempt}次超时（{reason}）——超时重试无意义，放弃本轮回补")
                break
            log(f"  [{pid}] 第{attempt}次{runlog.STATUS_LABEL[status]}（{reason}），重试")
            if attempt < max_try:  # 最后一次失败后无需再等待
                backoff_sleep(attempt, base=2.0)

        raw, dt, n = best
        final_status = "ok" if raw else (attempts[-1]["status"] if attempts else "empty")
        # 成功与失败都留档：失败记录是事后判断「要不要调并发/超时」的唯一依据
        runlog.log_solve(prob, prompt, attempts, final_status, raw, model=used_model)
        if raw:
            return pid, raw, dt, n
        return pid, "", 0.0, max_try

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, pid): pid for pid in todo}
        for fut in as_completed(futs):
            try:
                pid, raw, dt, attempt = fut.result()
            except FatalAPIError as e:
                # 立刻终止本轮：账号级错误下继续跑只会对剩余题目逐题白跑重试，
                # 既浪费时间又把日志淹没。已完成的题都在缓存里，充值后可原地续跑。
                log(f"[A/求解] ✗ 终止本轮：{e}")
                log(f"[A/求解] 已完成 {len(cached)} 题已落缓存，问题解决后可直接续跑")
                for f in futs:
                    f.cancel()
                return cached
            if raw:
                cached[pid] = raw
                with lock:
                    fh.write(json.dumps({
                        "problem_id": pid, "raw": raw, "elapsed": round(dt, 1),
                        "attempts": attempt, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                        # 记录产出该解答的模型：额度不足时会中途切换模型补跑，
                        # 混合来源必须逐题可区分，否则无法说明指标出自哪个模型。
                        "model": used_model,
                    }, ensure_ascii=False) + "\n")
                    fh.flush()
            done_n[0] += 1
            n = done_n[0]
            # 串行（workers=1）时逐题打印：一次只跑一题的场景下，每题一行日志是
            # 唯一能观察进度的窗口（按 5 题一打印会长时间静默，无法判断是否卡死）。
            interval = 1 if workers == 1 else 5
            if n % interval == 0 or n == len(todo):
                el = time.time() - t0
                eta = (len(todo) - n) / (n / el) / 60 if el > 0 else 0
                log(f"  [A/求解] {n}/{len(todo)} {'✓' if raw else '✗'} {pid} "
                    f"{dt:.0f}s(第{attempt}次)  已用 {el/60:.1f}min  预计剩余 {eta:.1f}min")
    fh.close()
    empty = [p for p in todo if not cached.get(p)]
    log(f"[A/求解] 完成，成功 {len(todo) - len(empty)}，空响应 {len(empty)}"
        + (f"：{', '.join(empty[:20])}" if empty else ""))
    return cached


# ---------------------------------------------------------------- 阶段 B：评估
def evaluate_all(problems, raws, backend, workers, out_path, timeout, deep_erv, judge_samples):
    """并发评估；返回逐题结果列表。已缓存的题跳过。"""
    cached = {r["problem_id"]: r for r in read_jsonl(out_path)}
    targets = [p for p in sorted(problems) if p in raws and p not in cached]
    log(f"[B/评估] 后端={backend} 可评估 {sum(1 for p in problems if p in raws)} 题，已缓存 {len(cached)}，待评估 {len(targets)}（{workers} 路并发）")

    client = load_client_from_env() if backend == "llm" else None
    fh = open(out_path, "a", encoding="utf-8")
    lock = threading.Lock()
    done_n = [0]
    t0 = time.time()

    def work(pid):
        prob = problems[pid]
        evaluator = build_evaluator(backend, client, timeout=timeout,
                                    judge_samples=judge_samples, use_stress=deep_erv)
        sol = parse_solution(raws[pid])
        sol.problem_id = prob.id
        sol.sample_id = f"FULL_{pid}"
        sol.source = "live"
        t = time.time()
        try:
            res = evaluator.evaluate(prob, sol)
        except Exception as e:
            log(f"  [{pid}] 评估异常 {type(e).__name__}: {e}")
            return None
        rec = res.to_dict()
        rec.update({"difficulty": prob.difficulty, "domain": prob.domain,
                    "title": prob.title, "eval_sec": round(time.time() - t, 2)})
        # 完整留存判定依据：逐用例 verdict + 四步骤 + 归因 + 被评估的模型输出
        runlog.log_eval(prob, rec, raws[pid])
        return rec

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, pid): pid for pid in targets}
        for fut in as_completed(futs):
            rec = fut.result()
            if rec:
                cached[rec["problem_id"]] = rec
                with lock:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fh.flush()
            done_n[0] += 1
            n = done_n[0]
            if n % 25 == 0 or n == len(targets):
                el = time.time() - t0
                eta = (len(targets) - n) / (n / el) / 60 if el > 0 else 0
                log(f"  [B/评估] {n}/{len(targets)}  已用 {el/60:.1f}min  预计剩余 {eta:.1f}min")
    fh.close()
    return list(cached.values())


# ---------------------------------------------------------------- 阶段 C：汇总
def summarize(recs, problems, backend, out_path, solve_cache_note=""):
    n = len(recs)
    if n == 0:
        log("[C/汇总] 无评估结果")
        return {}

    def rate(k):
        return round(sum(1 for r in recs if r.get(k)) / n, 4)

    final_ok = sum(1 for r in recs if r.get("final_correct"))
    proc_ok = sum(1 for r in recs if r.get("process_valid"))
    # 「答案对但过程不成立」——本系统的核心增量价值
    lucky = sum(1 for r in recs if r.get("final_correct") and not r.get("process_valid"))
    wrong = [r for r in recs if not r.get("final_correct")]

    by_diff, by_domain = defaultdict(list), defaultdict(list)
    for r in recs:
        by_diff[r.get("difficulty") or "?"].append(r)
        by_domain[r.get("domain") or "?"].append(r)

    def group_stat(rows):
        m = len(rows)
        return {
            "n": m,
            "final_acc": round(sum(1 for r in rows if r.get("final_correct")) / m, 4),
            "process_rate": round(sum(1 for r in rows if r.get("process_valid")) / m, 4),
            "lucky_pass": sum(1 for r in rows if r.get("final_correct") and not r.get("process_valid")),
        }

    err_counter = Counter(r.get("error_type") or "none" for r in recs if not r.get("process_valid"))
    step_counter = Counter(r.get("error_step") for r in recs if not r.get("process_valid") and r.get("error_step"))
    verdict_counter = Counter(r.get("first_failure_verdict") or "none" for r in recs)
    category_counter = Counter(r.get("error_type") or "none" for r in recs)

    eval_secs = [r.get("eval_sec", 0) for r in recs if r.get("eval_sec")]

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "backend": backend,
        "total": n,
        "bank_total": len(problems),
        "coverage": round(n / len(problems), 4),
        "final_correct": final_ok,
        "final_acc": rate("final_correct"),
        "process_valid": proc_ok,
        "process_rate": rate("process_valid"),
        "lucky_pass": lucky,
        "lucky_rate": round(lucky / n, 4),
        "process_only_fail": sum(1 for r in recs if r.get("process_valid") is False),
        "wrong_count": len(wrong),
        "by_difficulty": {d: group_stat(by_diff[d]) for d in ["easy", "medium", "hard"] if by_diff.get(d)},
        "by_domain": {d: group_stat(v) for d, v in sorted(by_domain.items(), key=lambda kv: -len(kv[1]))},
        "error_type_dist": dict(err_counter.most_common()),
        "error_type_names": {k: ERROR_TYPES.get(k, k) for k in err_counter},
        "error_step_dist": {str(k): v for k, v in sorted(step_counter.items())},
        "first_failure_verdict_dist": dict(verdict_counter.most_common()),
        "error_category_dist": dict(category_counter.most_common()),
        "eval_sec_median": round(statistics.median(eval_secs), 2) if eval_secs else None,
        "eval_sec_total": round(sum(eval_secs), 1),
        "note": solve_cache_note,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    log(f"[C/汇总] 总题数 {n}｜答案准确率 {summary['final_acc']:.1%}｜过程正确率 {summary['process_rate']:.1%}"
        f"｜答案对但过程错 {lucky} 题 -> {os.path.relpath(out_path)}")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8, help="求解并发（API 侧）")
    ap.add_argument("--eval-workers", type=int, default=6, help="评估并发（沙盒子进程侧）")
    ap.add_argument("--backend", choices=["rule", "llm"], default="rule")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--timeout", type=float, default=8.0)
    ap.add_argument("--api-timeout", type=int, default=None,
                    help="求解阶段单次 API 请求超时（秒），默认沿用客户端的 180；"
                         "hard 题推理耗时长，全量跑批建议 1800")
    ap.add_argument("--model", default=None,
                    help="覆盖求解所用模型（默认取 HY3_MODEL）。额度耗尽时用它切换备用"
                         "模型补跑剩余题目；实际使用的模型会逐题写入缓存与日志")
    ap.add_argument("--no-proxy", action="store_true",
                    help="强制绕过 HTTP(S)_PROXY。默认已会自动探活并跳过不可达的代理，"
                         "此开关用于代理存活但仍需直连的场景")
    ap.add_argument("--deep-erv", action="store_true", help="启用差分压力测试（更严的过程判定）")
    ap.add_argument("--judge-samples", type=int, default=1)
    ap.add_argument("--skip-solve", action="store_true", help="跳过阶段 A，复用已缓存解答")
    ap.add_argument("--skip-eval", action="store_true", help="跳过阶段 B，复用已缓存评估")
    ap.add_argument("--summary-only", action="store_true", help="只重新汇总")
    ap.add_argument("--problems", default=os.path.join(ROOT, "data", "problems.json"))
    args = ap.parse_args()

    if args.no_proxy:
        os.environ["HY3_NO_PROXY"] = "on"

    os.makedirs(RES_DIR, exist_ok=True)
    problems = {p.id: p for p in load_problems(args.problems)}
    eval_path = os.path.join(RES_DIR, f"full_eval_{args.backend}.jsonl")
    sum_path = os.path.join(RES_DIR, f"full_summary_{args.backend}.json")

    if args.summary_only:
        recs = read_jsonl(eval_path)
        summarize(recs, problems, args.backend, sum_path)
        return

    t_all = time.time()
    if args.skip_solve:
        raws = {r["problem_id"]: r["raw"] for r in read_jsonl(SOL_CACHE)
                if is_valid_solution(r.get("raw", ""))}
        log(f"[A/求解] 跳过，从缓存加载 {len(raws)} 题解答")
    else:
        raws = solve_all(problems, args.ids, args.limit, args.workers, SOL_CACHE,
                         api_timeout=args.api_timeout, model=args.model)

    if args.skip_eval:
        recs = read_jsonl(eval_path)
        log(f"[B/评估] 跳过，从缓存加载 {len(recs)} 条结果")
    else:
        recs = evaluate_all(problems, raws, args.backend, args.eval_workers, eval_path,
                            args.timeout, args.deep_erv, args.judge_samples)

    summarize(recs, problems, args.backend, sum_path,
              solve_cache_note=f"{len(raws)} 题解答已缓存")
    log(f"[完成] 总耗时 {(time.time() - t_all)/60:.1f} 分钟")


if __name__ == "__main__":
    main()
