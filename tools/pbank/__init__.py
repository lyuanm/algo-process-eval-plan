"""pbank 包：按 domain 分模块的题集来源。gen_problems.py 会聚合所有 PROBLEMS。

为支持增量开发，未创建的模块会被安全跳过（Missing optional module）。
"""
from __future__ import annotations
import importlib

_MODULE_NAMES = [
    "arrays_easy", "arrays_medium", "arrays_hard",
    "strings_easy", "strings_medium", "strings_hard",
    "pointers_easy", "pointers_medium", "pointers_hard",
    "binarysearch_easy", "binarysearch_medium", "binarysearch_hard",
    "linkedlist_easy", "linkedlist_medium", "linkedlist_hard",
    "tree_easy", "tree_medium", "tree_hard",
    "graph_easy", "graph_medium", "graph_hard",
    "dp_easy", "dp_medium", "dp_hard",
    "math_easy", "math_medium", "math_hard",
    "heap_greedy_easy", "heap_greedy_medium", "heap_greedy_hard",
    "heapgreedy_easy", "heapgreedy_medium", "heapgreedy_hard",
    "stackqueue_easy", "stackqueue_medium", "stackqueue_hard",
    "backtrackbit_easy", "backtrackbit_medium", "backtrackbit_hard",
]

ALL_MODULES = []
for _name in _MODULE_NAMES:
    try:
        ALL_MODULES.append(importlib.import_module("tools.pbank." + _name))
    except ModuleNotFoundError:
        pass


def collect():
    out = []
    for m in ALL_MODULES:
        out.extend(getattr(m, "PROBLEMS", []))
    return out
