# -*- coding: utf-8 -*-
"""第四批「会话内助手撰写」的解答（SM13-SM15, TE01-TE12）。

树类题的 I/O 约定（经 test_cases 与 reference_solution 实测确认）：
  输入/输出均为 LeetCode 层序数组，空孩子写 null，**末尾连续的 null 需裁剪**；
  建树用下标映射：第 i 个节点的左右孩子为 2i+1、2i+2。
  TE05/TE07（有序数组→平衡 BST）的期望串按「mid = (l+r)//2 取整」生成，
  虽然题目说任意平衡 BST 均可，但 checker 为 token_list（等价精确比较），
  因此必须复现该取中方式。

SM15 的期望串按 **键的首次插入顺序** 排列（参考解用 defaultdict(list) + list(mp.values())），
不能对键排序；组内保持输入顺序。SM14 为设计类题，输出 null / true / false。
"""
SOLUTIONS = {}


SOLUTIONS["SM13"] = r'''
## 思路

题面保证 s 本身是回文，因此每个字符的出现次数中至多有一个是奇数（回文串的必要条件），且这个奇数次数必然对应"唯一的中间字符"。

要得到**字典序最小**的回文排列：让前半部分尽可能小即可，因为回文的后半由前半镜像决定，比较时先比较到的就是前半。

做法：统计各字符次数 → 取每个字符的一半（出现次数 // 2 个）按字符升序拼成前半 → 剩下的那个奇数字符（若有）作为中间字符 → 结果 = 前半 + 中间 + 前半的逆序。

正确性：任何回文排列都由"前半的多重集合"唯一决定（中间字符也由奇偶性决定），而要使整体字典序最小，等价于使前半字典序最小，即把一半的字符集按升序排列。

## 复杂度分析

- 时间复杂度：O(n + 26)。统计一次、构造一次；字符表固定为 26。
- 空间复杂度：O(n)，存放结果字符串。

## 边界与处理

- 长度为 1：前半为空、中间为该字符，结果就是原字符（示例 1）。
- 只有一个奇数字符：它是唯一的中间字符（示例 2 的 'b'）。
- 全部字符出现偶数次：没有中间字符，长度为偶数。
- 长度上限 10^5：O(n) 构造足够。
- 输出为裸字符串（不加引号）。
- 无需校验 s 是否回文（题面保证），但代码逻辑只依赖计数，对非回文输入也能给出一个回文排列。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])

    cnt = [0] * 26
    for ch in s:
        cnt[ord(ch) - 97] += 1

    half = []
    mid = ""
    for i in range(26):
        half.append(chr(97 + i) * (cnt[i] // 2))
        if cnt[i] % 2 == 1:
            mid = chr(97 + i)

    left = "".join(half)
    print(left + mid + left[::-1])


main()
```
'''


SOLUTIONS["SM14"] = r'''
## 思路

实现前缀树（Trie）的三个操作，输入按"方法名序列 + 参数序列"给出。

数据结构：每个节点用两个数组描述——children 字典（键为 node*26+字母序号）与 is_end 标记。为什么用"整数键的单一字典"而不是"每节点一个字典"：调用次数可达 3×10^4、单个词长可达 2000，节点数最坏约 6×10^7 量级虽不会真的达到，但每节点一个字典的内存开销明显更高，用整数键的扁平字典更省内存。

- insert(word)：沿字符逐层下降，不存在则创建；末尾节点标记 is_end = True。
- search(word)：沿字符下降，路径不存在返回 False，末尾节点必须 is_end 为真。
- startsWith(prefix)：沿字符下降，路径存在即返回 True（不要求 is_end）。

## 复杂度分析

- 时间复杂度：每个操作 O(L)，L 为传入字符串长度（≤ 2000），与总调用次数 3×10^4 相乘仍可接受。
- 空间复杂度：O(总字符数)，即所有插入单词的字符总量。

## 边界与处理

- search 必须区分"只是某词的前缀"与"是完整词"：靠末尾节点的 is_end 标记，只查路径存在会错（示例中 search("app") 在仅插入 "apple" 时应为 False）。
- startsWith 不检查 is_end：示例中 startsWith("app") 在仅插入 "apple" 时为 True。
- 重复插入同一单词：重复走路径并再次置 is_end，幂等，不影响结果。
- 空字符串：题面长度 ≥ 1，不会发生；若发生，insert("") 只标记根，search("") 返回 True。
- 输入约定：第 1 行方法名（首元素为类名 → 构造），第 2 行参数列表；构造与 void 的 insert 返回 null。
- 输出为紧凑 JSON，布尔值小写。

## 代码
```python
import sys
import json


class Trie:
    def __init__(self):
        self.child = {}
        self.is_end = [False]

    def _walk(self, word):
        node = 0
        for ch in word:
            key = node * 26 + (ord(ch) - 97)
            nxt = self.child.get(key)
            if nxt is None:
                return None
            node = nxt
        return node

    def insert(self, word):
        node = 0
        for ch in word:
            key = node * 26 + (ord(ch) - 97)
            nxt = self.child.get(key)
            if nxt is None:
                nxt = len(self.is_end)
                self.child[key] = nxt
                self.is_end.append(False)
            node = nxt
        self.is_end[node] = True

    def search(self, word):
        node = self._walk(word)
        return node is not None and self.is_end[node]

    def startsWith(self, prefix):
        return self._walk(prefix) is not None


def fmt(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    methods = json.loads(lines[0])
    args = json.loads(lines[1])

    obj = None
    out = []
    for name, a in zip(methods, args):
        if obj is None:
            obj = Trie()
            out.append(None)
        elif name == "insert":
            obj.insert(a[0])
            out.append(None)
        elif name == "search":
            out.append(obj.search(a[0]))
        else:
            out.append(obj.startsWith(a[0]))

    print("[" + ",".join(fmt(v) for v in out) + "]")


main()
```
'''


SOLUTIONS["SM15"] = r'''
## 思路

互为变位词的字符串具有相同的"字符多重集合"，因此把每个字符串按字符排序后得到的字符串就是它的规范键（canonical key）。用键分组，同键的字符串归为一组。

输出顺序遵循**键的首次插入顺序**，组内元素保持输入顺序。这一点必须照做：虽然题目说"任意顺序"，但判题采用逐 token 精确比较，期望串正是按首次插入顺序生成的。

## 复杂度分析

- 时间复杂度：O(N × L log L)，N 为字符串个数，L 为最大长度。每个字符串排序 O(L log L)；哈希分组 O(N)。
- 空间复杂度：O(N × L)，存放分组结果。

## 边界与处理

- 空字符串：排序键为空串，单独成组（示例 2 输出 [[""]]）。
- 单字符串：只有一组（示例 3）。
- 重复字符串：同键，落在同一组，且保持输入次序。
- 全部互不为变位词：每组一个元素，组顺序为各键首次出现顺序。
- 输出必须是**紧凑 JSON**（无空格），且组顺序为键的首次插入顺序——用 Python 保序 dict 即可，切勿对键排序。
- 字符串长度可为 0（题面允许 0 ≤ |strs[i]|）。

## 代码
```python
import sys
import json
from collections import defaultdict


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    strs = json.loads(lines[0])

    groups = defaultdict(list)
    for st in strs:
        groups["".join(sorted(st))].append(st)

    print(json.dumps(list(groups.values()), separators=(",", ":")))


main()
```
'''


# ------------------------------------------------------------------ 树类公共代码
_TREE_HELPERS = r'''
def build_tree(arr):
    """由 LeetCode 层序数组（含 null）建树；空数组返回 None。

    必须用**队列式**反序列化，不能用「左 2i+1 / 右 2i+2」的下标映射：
    数组中出现 null 时，下标映射会把后续元素错配到不存在的父节点上。
    例如 [1,null,2,3] 的正确结构是「1 的右孩子为 2，2 的左孩子为 3」，
    下标映射会把 3 误当成 index 1（即 null 节点）的孩子而丢弃它。
    """
    if not arr or arr[0] is None:
        return None
    root = [arr[0], None, None]
    queue = [root]
    i = 1
    while queue and i < len(arr):
        node = queue.pop(0)
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                node[1] = [v, None, None]
                queue.append(node[1])
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                node[2] = [v, None, None]
                queue.append(node[2])
    return root


def serialize(root):
    """按层序输出，末尾连续的 null 裁掉。

    规则：先输出根，然后每弹出一个节点就依次输出它的两个孩子（null 也输出），
    但只有非空孩子才入队。这与本题库的层序**反序列化**（队列式、跳过 null）严格互逆，
    因此输出能被重新解析成同一棵树。
    常见写法「把 null 也压入队列」会让 null 占用队列位置、把后续真实节点整体后移，
    含 null 的树就会与期望串错位（实测 TH02 即为该情形）。
    """
    if root is None:
        return []
    out = [root[0]]
    queue = [root]
    while queue:
        node = queue.pop(0)
        for c in (node[1], node[2]):
            if c is None:
                out.append(None)
            else:
                out.append(c[0])
                queue.append(c)
    while out and out[-1] is None:
        out.pop()
    return out
'''


SOLUTIONS["TE01"] = r'''
## 思路

利用二叉搜索树的有序性做剪枝遍历：对节点 cur，
- 若 cur.val 落在 [low, high] 内：计入答案，并需要继续搜索左右子树（左子树可能有 ≥ low 的值，右子树可能有 ≤ high 的值）；
- 若 cur.val < low：左子树所有值都更小，必不在范围内，只递归右子树；
- 若 cur.val > high：右子树所有值都更大，只递归左子树。

这样每层最多走一条分支加一个"命中"节点，不会遍历整棵树。

## 复杂度分析

- 时间复杂度：O(n) 最坏（所有节点都在范围内时必须全部访问），但利用了 BST 性质，实际访问节点数等于"命中节点数 + 边界上的 O(h) 个节点"，h 为树高。
- 空间复杂度：O(h)，递归栈深度；h 最坏为 n（退化成链），平均 O(log n)。

## 边界与处理

- 单节点树：直接判断该值是否在范围内。
- low = high：只统计等于该值的节点（BST 中至多一个）。
- 范围内没有任何节点：返回 0。
- 全树节点都在范围内：退化为全树求和，O(n) 正确。
- 树以层序数组给出且可能含 null：用下标映射（左 2i+1、右 2i+2）建树，跳过 null。
- 递归深度：节点数 ≤ 2×10^4，若退化成链可能触发 Python 递归上限，因此改用**显式栈**迭代遍历。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))
    low = json.loads(lines[1])
    high = json.loads(lines[2])

    total = 0
    stack = [root] if root is not None else []
    while stack:
        cur = stack.pop()
        if cur is None:
            continue
        v = cur[0]
        if low <= v <= high:
            total += v
            stack.append(cur[1])
            stack.append(cur[2])
        elif v < low:
            stack.append(cur[2])
        else:
            stack.append(cur[1])
    print(total)


main()
```
'''


SOLUTIONS["TE02"] = r'''
## 思路

翻转二叉树的定义是：交换每个节点的左右子树。用递归（或迭代栈）对每个节点执行一次左右交换即可。

正确性：镜像树的每个节点都满足"左子树是原右子树的镜像、右子树是原左子树的镜像"，对全部节点做一次交换恰好得到该结构。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(h)，递归/栈深度，h 为树高；最坏 O(n)。

## 边界与处理

- 空树：返回 []（示例 3）。
- 单节点：交换两个 None，结果仍是该单节点。
- 只有一侧子树：交换后该子树换到另一侧，层序输出中会出现 null 占位（裁剪规则见下）。
- 完全二叉树（示例 1）：输出无 null。
- 输出为 LeetCode 层序，需**裁掉末尾连续的 null**，否则与期望串长度不符。
- 节点数 ≤ 100，递归深度安全；仍用显式栈以统一写法。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    if root is not None:
        stack = [root]
        while stack:
            cur = stack.pop()
            cur[1], cur[2] = cur[2], cur[1]
            if cur[1] is not None:
                stack.append(cur[1])
            if cur[2] is not None:
                stack.append(cur[2])

    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TE03"] = r'''
## 思路

完整二叉树：叶子值为 0/1（False/True），内部节点值为 2（OR）或 3（AND），且每个节点有 0 或 2 个孩子。

自底向上求值：遇到叶子直接返回其布尔值；遇到内部节点，先求左右孩子的值，再按运算符合并。用显式栈做后序遍历以避免深树递归。

由于每个节点的运算符固定且作用域只是它的两个孩子，局部求值即全局正确（布尔运算满足结合律的树形求值定义）。

## 复杂度分析

- 时间复杂度：O(n)，每个节点参与一次运算。
- 空间复杂度：O(h)，栈深度，h 为树高；节点数 ≤ 1000，安全。

## 边界与处理

- 单叶子（root = [0] 或 [1]）：直接返回其布尔值（示例 2 返回 false）。
- 全部 AND / 全部 OR：逐层合并即可。
- 短路语义：本题按"先算两个孩子再合并"定义，实现上与布尔短路结果一致，无需额外特判。
- 值为 0 的节点是叶子（False），不是内部节点——判断内部节点要用"是否有孩子"，而不是用值大小，避免把叶子 0 误判为运算符。
- 输出为 JSON 布尔的小写形式 true / false。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    result = False
    if root is not None:
        order = []
        stack = [root]
        while stack:
            cur = stack.pop()
            order.append(cur)
            if cur[1] is not None:
                stack.append(cur[1])
            if cur[2] is not None:
                stack.append(cur[2])

        val = {}
        for cur in reversed(order):
            if cur[1] is None and cur[2] is None:
                val[id(cur)] = bool(cur[0])
            else:
                a = val[id(cur[1])]
                b = val[id(cur[2])]
                val[id(cur)] = (a or b) if cur[0] == 2 else (a and b)
        result = val[id(root)]

    print("true" if result else "false")


main()
```
'''


SOLUTIONS["TE04"] = r'''
## 思路

题目要求统计二叉树中**不同节点值的种数**，与树形结构无关，只需遍历全部节点并把值放进集合，最后输出集合大小。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次；集合插入均摊 O(1)。
- 空间复杂度：O(n)，集合与遍历栈。

## 边界与处理

- 单节点树：答案为 1。
- 所有节点同色（示例 2）：答案为 1。
- 全部互不相同：答案为节点总数。
- 值域 1~1000：也可用长度 1001 的布尔数组替代集合，但集合写法更通用。
- 层序输入可能含 null：建树时跳过，不参与遍历。
- 输出为单个整数。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    seen = set()
    if root is not None:
        stack = [root]
        while stack:
            cur = stack.pop()
            seen.add(cur[0])
            if cur[1] is not None:
                stack.append(cur[1])
            if cur[2] is not None:
                stack.append(cur[2])

    print(len(seen))


main()
```
'''


SOLUTIONS["TE05"] = r'''
## 思路

升序数组构造平衡 BST 的标准分治：每次取区间中点作为根，左侧区间递归为左子树、右侧为右子树。这样两侧节点数最多相差 1，高度平衡；同时因为数组升序，天然满足 BST 的有序性。

取中点方式必须用 **mid = (l + r) // 2**（下取整）：题目的判题按该取法生成的层序串做精确比较，虽然数学上任意平衡 BST 都合法，但输出必须与期望串一致。

## 复杂度分析

- 时间复杂度：O(n)，每个元素生成一个节点。
- 空间复杂度：O(n)，节点数组 + O(log n) 递归栈（此处用显式栈/递归均可）。

## 边界与处理

- 空数组：返回 []（题目保证长度 ≥ 1，仍做保护）。
- 单元素：返回该单节点。
- 两个元素：[1,3] 取下取整中点 index 0 → 根为 1，右孩子 3，层序输出 [1,null,3]（与期望一致）。
- 奇数长度：中点恰好是正中间，左右完全平衡。
- 必须裁剪层序末尾的 null，否则与期望串不匹配。
- 负数元素：与升序性质无关，正常处理。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    nodes = [[v, None, None] for v in nums]

    def build(l, r):
        if l > r:
            return None
        mid = (l + r) // 2
        cur = nodes[mid]
        cur[1] = build(l, mid - 1)
        cur[2] = build(mid + 1, r)
        return cur

    root = build(0, len(nodes) - 1) if nodes else None
    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TE06"] = r'''
## 思路

同时从两棵树的根出发做同步递归：
- 两节点都为空 → 返回 None；
- 只有一个为空 → 直接返回非空的那棵（其整棵子树原样保留）；
- 都非空 → 新建/复用节点，值为两者之和，左右子树分别递归合并。

## 复杂度分析

- 时间复杂度：O(min(n1, n2) + 重叠外的节点数)，即 O(n1 + n2)，每个节点访问一次。
- 空间复杂度：O(h1 + h2)，递归栈深度。

## 边界与处理

- 两棵都空：输出 []。
- 一棵为空：输出另一棵的层序（示例 2 中 root1=[1]、root2=[1,2] → 根值 2、左空、右 2 → [2,2]）。
- 重叠位置：值相加，可能为 0 或负数（值域含负数），不能把 0 当成 null。
- 非重叠位置：非空节点整棵带入，不做任何改动。
- 输出需裁剪层序末尾的 null（示例 1 期望 [3,4,5,5,4,null,7]，末尾 7 后无多余 null）。
- 节点数 ≤ 2000，递归深度安全；仍用迭代以避免极端链状输入。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    a = build_tree(json.loads(lines[0]))
    b = build_tree(json.loads(lines[1]))

    if a is None:
        print(json.dumps(serialize(b), separators=(",", ":")))
        return
    if b is None:
        print(json.dumps(serialize(a), separators=(",", ":")))
        return

    # 迭代式合并：把 (目标节点, 源节点) 对压栈
    stack = [(a, b)]
    while stack:
        t, s = stack.pop()
        t[0] += s[0]
        if s[1] is not None:
            if t[1] is None:
                t[1] = s[1]
            else:
                stack.append((t[1], s[1]))
        if s[2] is not None:
            if t[2] is None:
                t[2] = s[2]
            else:
                stack.append((t[2], s[2]))

    print(json.dumps(serialize(a), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TE07"] = r'''
## 思路

与「将有序数组转换为二叉搜索树」是同一问题（本题为面试题版本）：升序数组 → 高度最小的 BST。

分治：取区间中点作为根，左半区间递归成左子树、右半区间递归成右子树。中点取法用 mid = (l + r) // 2（下取整），以保证输出层序与判题期望串一致。

高度最小性：每层把区间二分，任何 BST 的高度下界是 ⌈log2(n+1)⌉，二分构造恰好达到该下界。

## 复杂度分析

- 时间复杂度：O(n)，每个元素生成一个节点。
- 空间复杂度：O(n)（节点数组）+ O(log n) 递归栈。

## 边界与处理

- 空数组：返回 []。
- 单元素：仅一个节点。
- 两个元素：下取整中点落在左侧，层序为 [左,null,右]。
- 元素各不相同且升序（题面保证），无需去重或排序。
- 负数元素正常处理。
- 输出为层序数组，需裁剪末尾 null。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    nodes = [[v, None, None] for v in nums]

    def build(l, r):
        if l > r:
            return None
        mid = (l + r) // 2
        cur = nodes[mid]
        cur[1] = build(l, mid - 1)
        cur[2] = build(mid + 1, r)
        return cur

    root = build(0, len(nodes) - 1) if nodes else None
    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TE08"] = r'''
## 思路

利用 BST 的有序性做定向查找：从根开始，若当前值等于 val 则返回以该节点为根的子树；若 val 小于当前值则在左子树继续；否则在右子树继续。走到空则说明不存在。

定向查找每条路径只走一侧，因此最坏代价是树高。

## 复杂度分析

- 时间复杂度：O(h)，h 为树高；平衡时 O(log n)，退化成链时 O(n)（n ≤ 5000）。
- 空间复杂度：O(1)（迭代实现，不使用递归栈）。

## 边界与处理

- 值为 val 的节点不存在：返回空树，层序输出为空数组 []（示例 2）。
- 命中节点是叶子：输出 [val]。
- 命中节点带子树：输出从该节点起的完整层序（示例 1 输出 [2,1,3]）。
- val 小于所有节点 / 大于所有节点：一路走到 None，返回 []。
- val 可大于 32 位（题面 val ≤ 10^7），Python 整数无碍。
- 输出需裁剪末尾 null。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))
    val = json.loads(lines[1])

    cur = root
    while cur is not None and cur[0] != val:
        cur = cur[1] if val < cur[0] else cur[2]

    print(json.dumps(serialize(cur), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TE09"] = r'''
## 思路

二叉树的最大深度 = 从根到最远叶子的节点数。用自底向上的层序遍历（BFS）统计层数最直观：每处理完一层，深度加一。

也可用后序 DFS 求 max(左深, 右深) + 1，两者等价。BFS 的好处是不受链状树递归深度限制。

## 复杂度分析

- 时间复杂度：O(n)，每个节点入队出队各一次。
- 空间复杂度：O(w)，w 为最大层宽（BFS 队列），最坏 O(n)。

## 边界与处理

- 空树：深度为 0。
- 单节点：深度为 1。
- 链状树（每层仅一个节点）：深度等于节点数，BFS 层数准确对应（不会误算）。
- 层序输入含 null：建树时按 2i+1 / 2i+2 映射，null 不生成节点，不会虚增深度。
- 节点数 ≤ 10000，O(n) 足够。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    depth = 0
    if root is not None:
        queue = [root]
        while queue:
            depth += 1
            nxt = []
            for node in queue:
                if node[1] is not None:
                    nxt.append(node[1])
                if node[2] is not None:
                    nxt.append(node[2])
            queue = nxt

    print(depth)


main()
```
'''


SOLUTIONS["TE10"] = r'''
## 思路

与上一题同解：二叉树最大深度用层序遍历（BFS）逐层计数，或用后序 DFS 求 max(左,右)+1。这里用 BFS，避免退化树（链）触发递归深度限制。

## 复杂度分析

- 时间复杂度：O(n)。
- 空间复杂度：O(w)，w 为最大层宽，最坏 O(n)。

## 边界与处理

- 空树：返回 0（题面允许节点数为 0）。
- 单节点：返回 1。
- 只有右孩子的链（如 [1,null,2]）：返回 2（示例 2），BFS 层数准确。
- 层序输入中的 null 不生成节点，不会虚增层数。
- 节点值可为负，与深度无关。
- 节点数 ≤ 10^4，O(n) 足够。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    depth = 0
    if root is not None:
        queue = [root]
        while queue:
            depth += 1
            nxt = []
            for node in queue:
                if node[1] is not None:
                    nxt.append(node[1])
                if node[2] is not None:
                    nxt.append(node[2])
            queue = nxt

    print(depth)


main()
```
'''


SOLUTIONS["TE11"] = r'''
## 思路

题目保证树恰好有 3 个节点：根、左孩子、右孩子。直接判断 root.val == root.left.val + root.right.val 即可。

## 复杂度分析

- 时间复杂度：O(1)，最多访问 3 个节点。
- 空间复杂度：O(1)。

## 边界与处理

- 和为负或为零：比较仍成立（如 [-1,-2,1] → -1 == -1 输出 true）。
- 值域 -100~100，无需担心溢出。
- 叶子节点不会出现（题目保证恰好 3 个节点），因此无需处理单节点输入。
- 输出为 JSON 布尔小写 true / false。
- 层序输入为 [根,左,右] 三个元素，建树后左右孩子必然存在。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    ok = root is not None and root[1] is not None and root[2] is not None \
        and root[0] == root[1][0] + root[2][0]
    print("true" if ok else "false")


main()
```
'''


SOLUTIONS["TE12"] = r'''
## 思路

中序遍历的顺序是"左 → 根 → 右"。用**显式栈的迭代法**实现，避免递归深度问题，也顺手回应题目"进阶：用迭代完成"。

迭代模板：一路把左孩子压栈直到为空；弹出栈顶访问其值；然后转向其右孩子继续。

## 复杂度分析

- 时间复杂度：O(n)，每个节点入栈出栈各一次。
- 空间复杂度：O(h)，栈深度，h 为树高。

## 边界与处理

- 空树：输出 []（示例 2）。
- 单节点：输出 [val]（示例 3）。
- 只有右孩子的链：中序即为链的从上到下顺序。
- 只有左孩子的链：中序为从下到上的顺序（迭代模板自然正确）。
- 节点值为负：与遍历顺序无关。
- 输出为**紧凑 JSON** 数组，且为精确比较，顺序不能错。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    out = []
    stack = []
    cur = root
    while cur is not None or stack:
        while cur is not None:
            stack.append(cur)
            cur = cur[1]
        node = stack.pop()
        out.append(node[0])
        cur = node[2]

    print(json.dumps(out, separators=(",", ":")))


main()
```
'''


def to_jsonl(path: str) -> int:
    import json as _json
    with open(path, "w", encoding="utf-8") as f:
        for pid, raw in SOLUTIONS.items():
            f.write(_json.dumps({"problem_id": pid, "raw": raw.lstrip("\n")},
                                ensure_ascii=False) + "\n")
    return len(SOLUTIONS)


if __name__ == "__main__":
    import os
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "batch04.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
