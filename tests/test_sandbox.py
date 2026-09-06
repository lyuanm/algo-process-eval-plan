# -*- coding: utf-8 -*-
"""沙盒执行环境测试：兼容模型常见的 `if __name__ == '__main__'` 守卫。"""
from src.sandbox import run_code


def test_main_guard_runs():
    """带 __main__ 守卫的代码（Hy3 常见输出风格）必须在沙盒中正常执行。"""
    code = """import sys

def main():
    a = int(sys.stdin.readline())
    b = int(sys.stdin.readline())
    print(a + b)

if __name__ == "__main__":
    main()
"""
    r = run_code(code, "1\n2", timeout=10)
    assert r.ok, f"带 main 守卫的代码执行失败: {r.stderr[:200]}"
    assert r.stdout.strip() == "3"


def test_no_main_guard_runs():
    """直接调用 main() 的代码（题库参考实现风格）同样正常。"""
    code = """import sys

def main():
    a = int(sys.stdin.readline())
    b = int(sys.stdin.readline())
    print(a + b)

main()
"""
    r = run_code(code, "3\n4", timeout=10)
    assert r.ok and r.stdout.strip() == "7"


def test_blocked_import_rejected():
    code = """import socket
print(1)
"""
    r = run_code(code, "", timeout=10)
    assert not r.ok
    assert "blocked" in (r.stderr or "").lower() or "blocked" in r.stderr
