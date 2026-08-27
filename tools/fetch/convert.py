# -*- coding: utf-8 -*-
"""把 LeetCode 官方题目 + 官方题解代码 转换为标准题库 Problem 格式。

真实性保证：
  - 题目信息（标题/难度/描述/约束/官方样例）  ←  LeetCode 官方 questionData API
  - reference_solution 的核心逻辑            ←  LeetCode 官方题解文章中的 Python 代码（原样保留）
  - 外层仅添加"读 stdin → 解析参数 → 调用 Solution → 格式化输出"的机械 I/O 包装，
    不包含任何自编算法逻辑。
  - test_cases 期望值                        ←  用官方题解代码在官方样例上运行产生的输出
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple

# ---------- LeetCode 标准数据结构定义（序列化规则与 LeetCode 平台一致） ----------
LISTNODE = '''class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def _list_build(vals):
    head = cur = ListNode()
    for v in vals:
        cur.next = ListNode(v)
        cur = cur.next
    return head.next

def _list_show(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out

def _list_array_build(arr):
    return [_list_build(x) for x in arr]

def _list_array_show(arr):
    return [_list_show(x) for x in arr]
'''

TREENODE = '''class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def _tree_build(vals):
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    q = [root]
    i = 1
    while q and i < len(vals):
        node = q.pop(0)
        if i < len(vals) and vals[i] is not None:
            node.left = TreeNode(vals[i])
            q.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TreeNode(vals[i])
            q.append(node.right)
        i += 1
    return root

def _tree_show(root):
    if not root:
        return []
    out = []
    q = [root]
    while q:
        node = q.pop(0)
        out.append(node.val if node else None)
        if node:
            q.append(node.left)
            q.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out

def _tree_array_build(arr):
    return [_tree_build(x) for x in arr]

def _tree_array_show(arr):
    return [_tree_show(x) for x in arr]
'''

# ---------- I/O 包装层模板 ----------
WRAP_HEAD = (
    "import sys, json\n"
    "import itertools, functools, collections, math, bisect, string, heapq, random, operator\n"
    "from typing import *\n"
    "from collections import *\n"
    "from itertools import *\n"
    "from bisect import *\n"
    "from functools import *\n"
    "from math import *\n"
    "from string import *\n"
    "from operator import *\n"
    "{structs}"
    "{solution_code}\n"
    "def main():\n"
    "    _dec = json.JSONDecoder()\n"
    "    _text = sys.stdin.read()\n"
    "    _idx = 0\n"
    "    _args = []\n"
    "    while _idx < len(_text):\n"
    "        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n"
    "            _idx += 1\n"
    "        if _idx >= len(_text):\n"
    "            break\n"
    "        try:\n"
    "            _obj, _end = _dec.raw_decode(_text, _idx)\n"
    "            _args.append(_obj)\n"
    "            _idx = _end\n"
    "        except Exception:\n"
    "            _nl = _text.find('\\n', _idx)\n"
    "            if _nl == -1:\n"
    "                _idx = len(_text)\n"
    "            else:\n"
    "                _idx = _nl + 1\n"
    "    _sol = Solution()\n"
    "{convert_in}\n"
    "    _ret = _sol.{func}({call_args})\n"
    "{convert_out}\n"
    "    sys.stdout.write(_out)\n"
    "\n"
    "main()\n"
)

# 返回类型 → check_mode 映射
RET_CHECK_MODE = {
    "integer": "int",
    "float": "float",
    "boolean": "bool",
    "string": "str",
    "character": "str",
    "integer[]": "int_list",
    "float[]": "int_list",
    "character[]": "token_list",
    "string[]": "token_list",
    "ListNode": "token_list",
    "TreeNode": "token_list",
}


def parse_meta(meta_raw: str) -> Dict[str, Any]:
    """解析 metaData 字符串。"""
    m = json.loads(meta_raw)
    return m


def normalize_type(t: str) -> str:
    """归一化类型描述：integer[] -> integer[]; int[][] -> integer[][]"""
    t = t.strip()
    return t


def param_needs_convert(t: str) -> Optional[str]:
    """参数类型需要结构转换时返回构造函数名，否则 None。"""
    if t == "ListNode":
        return "_list_build"
    if t == "TreeNode":
        return "_tree_build"
    if t == "ListNode[]":
        return "_list_array_build"
    if t == "TreeNode[]":
        return "_tree_array_build"
    return None


def return_needs_convert(t: str) -> Optional[str]:
    if t == "ListNode":
        return "_list_show"
    if t == "TreeNode":
        return "_tree_show"
    return None


# ---------- 设计类题（操作序列）专用包装 ----------
WRAP_DESIGN = (
    "import sys, json\n"
    "import itertools, functools, collections, math, bisect, string, heapq, random, operator\n"
    "from typing import *\n"
    "from collections import *\n"
    "from itertools import *\n"
    "from bisect import *\n"
    "from functools import *\n"
    "from math import *\n"
    "from string import *\n"
    "from operator import *\n"
    "{structs}"
    "{solution_code}\n"
    "def main():\n"
    "    _lines = [x for x in sys.stdin.read().split('\\n') if x.strip() != '']\n"
    "    _ops = json.loads(_lines[0])\n"
    "    _args = json.loads(_lines[1]) if len(_lines) > 1 else []\n"
    "    _obj = None\n"
    "    _out = []\n"
    "    for _i, _op in enumerate(_ops):\n"
    "        _a = _args[_i] if _i < len(_args) else []\n"
    "        if _i == 0:\n"
    "            _obj = {cls}(*_a)\n"
    "            _out.append(None)\n"
    "        else:\n"
    "            _out.append(getattr(_obj, _op)(*_a))\n"
    "    print(json.dumps(_out, separators=(',', ':')))\n"
    "\n"
    "main()\n"
)


def build_design_solution(meta: Dict[str, Any], solution_code: str) -> str:
    """设计类题（如 LRU Cache）参考实现：按操作序列调用。"""
    cls = meta.get("classname") or meta.get("name", "Solution")
    code = solution_code.strip("\n")
    # 官方题解代码可能定义 class Xxx 与 meta.classname 不同，按代码实际类名
    m = re.search(r'class\s+(\w+)', code)
    if m:
        cls = m.group(1)
    return WRAP_DESIGN.format(structs="", solution_code=code + "\n", cls=cls)


def build_reference_solution(meta: Dict[str, Any], solution_code: str) -> str:
    """生成可运行参考实现 = 官方题解代码 + I/O 包装。"""
    if meta.get("classname"):
        return build_design_solution(meta, solution_code)
    # 函数名优先用 metaData 的（官方标准名）；代码中不存在时才用代码里第一个 def
    # （避开注释中的 def __init__ 等干扰）
    clean_code = "\n".join(l for l in solution_code.split("\n") if not l.strip().startswith("#"))
    code_names = re.findall(r'def\s+(\w+)\s*\(', clean_code)
    mname = meta.get("name", "")
    func = mname if (mname and mname in code_names) else (code_names[0] if code_names else mname)
    params = meta.get("params") or []
    structs = []
    ret_t = (meta.get("return") or {}).get("type", "")
    need_ln = any(p["type"].replace("[]", "") == "ListNode" for p in params) or ret_t.replace("[]", "") == "ListNode"
    need_tn = any(p["type"].replace("[]", "") == "TreeNode" for p in params) or ret_t.replace("[]", "") == "TreeNode"
    if need_ln:
        structs.append(LISTNODE)
    if need_tn:
        structs.append(TREENODE)
    structs_src = "\n".join(structs) + "\n"

    # 参数转换（按顺序）
    conv_in_lines = []
    call_args = []
    for i, p in enumerate(params):
        cnv = param_needs_convert(p["type"])
        if cnv:
            conv_in_lines.append(f"    _args[{i}] = {cnv}(_args[{i}])")
        call_args.append(f"_args[{i}]")
    convert_in = "\n".join(conv_in_lines)

    # 输出转换
    ret_t = (meta.get("return") or {}).get("type", "")
    if ret_t == "ListNode[]":
        convert_out = '    _out = json.dumps([_list_show(x) for x in _ret], separators=(",", ":"))'
    elif ret_t == "TreeNode[]":
        convert_out = '    _out = json.dumps([_tree_show(x) for x in _ret], separators=(",", ":"))'
    else:
        cnv_out = return_needs_convert(ret_t)
        if cnv_out:
            convert_out = f"    _out = json.dumps({cnv_out}(_ret), separators=(',', ':'))"
        else:
            convert_out = (
                "    if _ret is None:\n"
                "        _out = ''\n"
                "    elif isinstance(_ret, (list, dict)):\n"
                "        _out = json.dumps(_ret, separators=(',', ':'))\n"
                "    elif isinstance(_ret, bool):\n"
                "        _out = 'true' if _ret else 'false'\n"
                "    elif isinstance(_ret, float):\n"
                "        _out = repr(_ret)\n"
                "    else:\n"
                "        _out = str(_ret)"
            )

    return WRAP_HEAD.format(
        structs=structs_src,
        solution_code=solution_code.strip("\n") + "\n",
        convert_in=convert_in,
        func=func,
        call_args=", ".join(call_args),
        convert_out=convert_out,
    )


def pick_check_mode(meta: Dict[str, Any]) -> str:
    if meta.get("classname"):
        return "token_list"
    ret_t = (meta.get("return") or {}).get("type", "")
    if ret_t.endswith("[]"):
        return RET_CHECK_MODE.get(ret_t, "token_list")
    if ret_t in ("ListNode", "TreeNode"):
        return "token_list"
    if ret_t in ("integer", "float", "boolean", "string", "character"):
        return RET_CHECK_MODE[ret_t]
    return "exact"


def parse_example_inputs(example_testcases: str, n_params: int) -> List[List[Any]]:
    """流式解析官方样例输入（exampleTestcases），每 n_params 个参数为一组。"""
    dec = json.JSONDecoder()
    text = example_testcases or ""
    idx = 0
    groups: List[List[Any]] = []
    cur: List[Any] = []
    while idx < len(text):
        while idx < len(text) and text[idx] in " \t\r\n":
            idx += 1
        if idx >= len(text):
            break
        try:
            obj, end = dec.raw_decode(text, idx)
            cur.append(obj)
            idx = end
            if len(cur) == n_params:
                groups.append(cur)
                cur = []
        except Exception:
            nl = text.find("\n", idx)
            if nl == -1:
                idx = len(text)
            else:
                idx = nl + 1
    if cur:
        groups.append(cur)
    return groups


def json_param_to_str(v: Any) -> str:
    """把参数值转成我们题库的输入文本（json 紧凑形式，每参数一行）。"""
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    return json.dumps(v, separators=(",", ":"))
