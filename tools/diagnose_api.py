# -*- coding: utf-8 -*-
"""诊断：hard 题批量「Mock 降级」的真实原因。

现象：全量跑批中 AH02/AH07/AH08、BH02~BH11、DH03/DH05、BM07/BM09 等题连续 2~3 次
返回 Mock 降级，而 easy/medium 题基本一次成功。hy3_client 会把异常吞掉并返回 Mock
文本，日志只显示笼统的「API 调用失败」，无法判断到底是：

  (a) 单请求超时（推理链太长，超过 timeout）      -> 处置：调大 --api-timeout
  (b) 网关限流 429                                -> 处置：降低并发
  (c) 服务端 5xx / 网络抖动                       -> 处置：重试即可
  (d) max_tokens 被推理过程吃光导致 content 为空   -> 处置：显式设置 max_tokens

本脚本绕过 Mock 降级，直接打印原始异常与响应结构，用于定位。

用法：
  python tools/diagnose_api.py --ids AH07 BH02 DH03 --timeout 600
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from src.problems import load_problems  # noqa: E402
from src.solver import SOLVE_PROMPT  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="+", default=["AH07"])
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--retries", type=int, default=2)
    args = ap.parse_args()

    base_url = os.getenv("HY3_BASE_URL", "https://tokenhub.tencentmaas.com/v1")
    api_key = os.getenv("HY3_API_KEY", "")
    model = os.getenv("HY3_MODEL", "hy3")
    print(f"网关 {base_url}｜模型 {model}｜key={'已配置(' + str(len(api_key)) + '字符)' if api_key else '未配置'}｜超时 {args.timeout}s")

    try:
        from openai import OpenAI
    except ImportError:
        print("缺少 openai 依赖"); return 2

    client = OpenAI(base_url=base_url, api_key=api_key, timeout=args.timeout, max_retries=0)
    problems = {p.id: p for p in load_problems(os.path.join(ROOT, "data", "problems.json"))}

    for pid in args.ids:
        p = problems.get(pid)
        if p is None:
            print(f"\n=== {pid} 不在题库中"); continue
        prompt = SOLVE_PROMPT.format(
            title=p.title, difficulty=p.difficulty, domain=p.domain,
            description=p.description, input_format=p.input_format,
            output_format=p.output_format, constraints=p.constraints,
        )
        print(f"\n=== {pid} {p.title}｜{p.difficulty}｜{p.domain}｜prompt {len(prompt)} 字符")
        for k in range(1, args.retries + 1):
            t = time.time()
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9,
                    extra_body={"chat_template_kwargs": {"reasoning_effort": "high"}},
                )
            except Exception as e:
                print(f"  第{k}次 ✗ 异常 {type(e).__name__}: {str(e)[:300]}（耗时 {time.time()-t:.1f}s）")
                continue
            dt = time.time() - t
            ch = resp.choices[0]
            msg = ch.message
            content = (msg.content or "")
            reasoning = getattr(msg, "reasoning_content", None) or ""
            usage = getattr(resp, "usage", None)
            print(f"  第{k}次 ✓ 耗时 {dt:.1f}s｜finish_reason={ch.finish_reason}"
                  f"｜content {len(content)} 字符｜reasoning {len(reasoning)} 字符"
                  f"｜usage={usage}")
            if not content.strip():
                print(f"     ⚠️ content 为空 → 这正是被当成「Mock 降级」的原因")
                print(f"     reasoning 头部: {reasoning[:200]!r}")
            else:
                print(f"     content 头部: {content[:160]!r}")
                break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
