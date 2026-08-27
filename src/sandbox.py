"""沙盒执行校验器。

职责：把候选解法（完整 Python 脚本，从 stdin 读、向 stdout 写）在受控子进程中
执行，喂入测试用例输入，捕获输出，供答案校验使用。

实现要点：
- 使用子进程 + 超时，保证隔离与可控。
- 仅对"被评测代码模块"替换 __import__ 为受限导入（允许常见算法标准库），
  不影响 Python 自身导入机制（避免误伤 _io / importlib 等内部导入）。
- 生产环境对不可信代码应进一步使用容器（Docker）/ gVisor 等强隔离。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import os
from dataclasses import dataclass
from typing import Optional

# 允许算法题使用的标准库根模块（其余一律拦截）
_ALLOWED_IMPORT_ROOTS = (
    "sys", "re", "math", "heapq", "bisect", "collections", "functools",
    "itertools", "string", "typing", "json", "random", "datetime",
    "array", "operator", "copy", "cProfile", "pstats", "gc", "queue",
    "dataclasses", "decimal", "fractions", "statistics",
)

_HARNESS = '''import sys as _sys
import builtins as _bm

_ALLOWED = {allowed}
_real_import = _bm.__import__
def _safe_import(name, *a, **k):
    root = name.split('.')[0]
    if root in _ALLOWED:
        return _real_import(name, *a, **k)
    raise ImportError('blocked import: ' + name + '（沙盒仅允许标准算法库）')

_restricted = dict(_bm.__dict__)
_restricted['__import__'] = _safe_import
_user_globals = {{'__builtins__': _restricted}}
with open({code_path!r}, 'r', encoding='utf-8') as _f:
    _src = _f.read()
exec(_src, _user_globals)
'''


@dataclass
class RunResult:
    ok: bool               # 进程是否正常结束（无异常/超时）
    stdout: str
    stderr: str
    timed_out: bool
    exit_code: Optional[int]


def run_code(code: str, stdin_text: str, timeout: float = 5.0) -> RunResult:
    if timeout is None or timeout <= 0:
        timeout = 5.0
    code_file = harness_file = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, encoding="utf-8"
        ) as cf:
            cf.write(code)
            code_file = cf.name
        harness = _HARNESS.format(
            allowed=repr(set(_ALLOWED_IMPORT_ROOTS)), code_path=code_file
        )
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, encoding="utf-8"
        ) as hf:
            hf.write(harness)
            harness_file = hf.name
        proc = subprocess.run(
            [sys.executable, harness_file],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return RunResult(
            ok=(proc.returncode == 0),
            stdout=proc.stdout,
            stderr=proc.stderr,
            timed_out=False,
            exit_code=proc.returncode,
        )
    except subprocess.TimeoutExpired as e:
        return RunResult(
            ok=False,
            stdout=e.stdout or "",
            stderr=(e.stderr or "") + "\n[TIMEOUT]",
            timed_out=True,
            exit_code=None,
        )
    except Exception as e:  # pragma: no cover
        return RunResult(ok=False, stdout="", stderr=str(e), timed_out=False, exit_code=None)
    finally:
        for p in (code_file, harness_file):
            if p:
                try:
                    os.remove(p)
                except Exception:
                    pass
