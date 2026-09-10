# -*- coding: utf-8 -*-
"""第六批「会话内助手撰写」的解答（TH13-TH15, TM01-TM12）。"""
SOLUTIONS = {}

_TREE_HELPERS = r'''
def build_tree(arr):
    """LeetCode 层序数组 -> 树（队列式反序列化，含 null 时下标映射会错配）。"""
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
    """层序输出：先输出根，再每弹出一个节点就输出其两个孩子（null 也输出、不入队）。"""
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


SOLUTIONS["TH13"] = r'''
## 思路

设全树总和为 S。若最终分成 cnt 个价值相等的连通块，每个价值必为 d = S / cnt，因此 d 必须是 S 的约数、cnt = S / d。

对 S 的每个约数 d，用自底向上的贪心判断能否切成价值均为 d 的块：后序遍历，若某子树的节点值之和恰好等于 d，就把该子树整块切下（计数 +1）并向父节点返回 0；否则把和原样返回给父节点。遍历结束后，若 切出的块数 × d == S，说明该 d 可行。

正确性：切块必须"整块"，且一旦某子树的和恰为 d，把它切下不会影响其它部分能否凑成 d（因为它的贡献已完全归入一个合法块）。因此能切就切是最优的，切出的块数达到该 d 下的上界 S/d。

对所有可行 d 取最大块数，答案 = 最大块数 − 1（删边数 = 块数 − 1；若整棵树本来就等于 d 则块数为 1、删 0 条边）。

## 复杂度分析

- 时间复杂度：O(τ(S) · n)，τ(S) 为 S 的约数个数。S ≤ 2×10^4×50 = 10^6，约数最多 240 个，n ≤ 2×10^4 → 最坏约 5×10^6 次操作，可接受。用显式栈避免递归过深。
- 空间复杂度：O(n)，邻接表与遍历栈。

## 边界与处理

- n = 1、无边：只能整棵树为一块，删 0 条边（示例 2）。
- 所有节点值相同：d 取单个节点的值即可切成 n 块，答案 n−1。
- d = S（整棵树一块）：必然可行，作为答案下界 0。
- d 必须整除 S，只需枚举 S 的约数，不要盲目从小到大试所有整数。
- 切块时必须用"和恰好等于 d"的判断，不能只判断"能被 d 整除"——后者会把 2d 的块误当合法块，导致块数虚高。
- 输入是无向树，需先按根建父子关系，避免把父节点当子节点重复计算。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    edges = json.loads(lines[1])

    n = len(nums)
    total = sum(nums)

    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    parent = [-1] * n
    order = []
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                stack.append(v)

    divisors = []
    d = 1
    while d * d <= total:
        if total % d == 0:
            divisors.append(d)
            if d != total // d:
                divisors.append(total // d)
        d += 1
    divisors.sort()

    best_blocks = 1
    for d in divisors:
        cnt = 0
        sub = list(nums)
        for u in reversed(order):
            if sub[u] == d:
                cnt += 1
                sub[u] = 0
            if parent[u] != -1:
                sub[parent[u]] += sub[u]
        if cnt * d == total and cnt > best_blocks:
            best_blocks = cnt

    print(best_blocks - 1)


main()
```
'''


SOLUTIONS["TH14"] = r'''
## 思路

正方形并集被水平线 y = c 分成上下两部分，要求两面积相等，取满足条件的最小 c。

关键性质：并集面积关于 c 的累积函数 F(c) = "y ≤ c 部分的并集面积"是分段线性的——在任意两个相邻的"正方形上下边 y 坐标"之间，参与的正方形集合与它们的 x 区间并集宽度都不变，因此 F 在该区间内是斜率为常数的直线。

做法：
1. 收集所有正方形的 y1、y2，排序去重，形成若干水平条带；
2. 对每个条带 [ya, yb]：筛出完全覆盖该条带的正方形（y1 ≤ ya 且 yb ≤ y2），求它们 x 区间并集的总宽度 w，则该条带贡献面积 w·(yb − ya)；
3. 按 y 从小到大累加面积，找到首个使累加面积 ≥ 总面积一半的条带，在该条带内按线性插值求出精确的 y。

## 复杂度分析

- 时间复杂度：O(B · n log n)，B 为条带数（≤ 2n−1），每条带筛出活动矩形并对 ≤ n 个 x 区间排序。本题 n ≤ 5×10^4，因此该实现只适合中小规模输入；若需处理最大规模，应对 x 区间并集改用线段树 + 滑动窗口，可优化到 O(n log n)。
- 空间复杂度：O(n)。

## 边界与处理

- 总面积可能为 0？题目保证边长 ≥ 1，故总面积 > 0。
- 只有一条水平线可选（两个正方形高度区间不重叠，如示例 1）：累积恰好在中点处达到一半，返回该 y。
- 正方形重叠：x 区间并集必须先合并再求长度，否则会重复计数（示例 2 即依赖此性质）。
- 恰好落在条带边界：用线性插值，`half - acc` 为 0 时直接返回该边界值，保证取到"最小"的 y。
- 坐标可达 10^9、面积可达 10^15：用 Python 大整数/高精度浮点累加，避免精度损失；插值用浮点除法输出。
- 输出为浮点数（与期望值误差 1e-5 内即可）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    squares = json.loads(lines[0])

    ys = sorted({s[1] for s in squares} | {s[1] + s[2] for s in squares})

    # 先算出每个条带的面积与总并集面积
    bands = []
    for k in range(len(ys) - 1):
        ya, yb = ys[k], ys[k + 1]
        if yb <= ya:
            continue
        intervals = []
        for x, y, l in squares:
            if y <= ya and yb <= y + l:
                intervals.append((x, x + l))
        if not intervals:
            continue
        intervals.sort()
        width = 0
        cl, cr = intervals[0]
        for a, b in intervals[1:]:
            if a <= cr:
                if b > cr:
                    cr = b
            else:
                width += cr - cl
                cl, cr = a, b
        width += cr - cl
        if width > 0:
            bands.append((ya, yb, width))

    total = sum((yb - ya) * w for ya, yb, w in bands)

    acc = 0.0
    half = total / 2.0
    ans = float(ys[0]) if ys else 0.0
    for ya, yb, w in bands:
        seg = (yb - ya) * w
        if acc + seg >= half:
            ans = ya + (half - acc) / w
            break
        acc += seg
    else:
        if bands:
            ans = float(bands[-1][1])

    print(ans)


main()
```
'''


SOLUTIONS["TH15"] = r'''
## 思路

按定义给每个节点打上坐标：根为 (row 0, col 0)，左孩子 (row+1, col−1)，右孩子 (row+1, col+1)。DFS 收集所有 (col, row, val) 三元组。

排序规则：先按 col 升序；同一列内按 row 升序；同一行同一列（只在非完美树中出现）按 val 升序。之后按 col 分组输出。

注意题目要求"同列内按从上到下排序，若同行同列则按值排序"，因此排序键就是 (col, row, val)。

## 复杂度分析

- 时间复杂度：O(n log n)，n 个节点排序；n ≤ 1000。
- 空间复杂度：O(n)，三元组数组。

## 边界与处理

- 单节点：输出 [[val]]。
- 完美二叉树：不会出现同行同列，排序键的第三项不起作用。
- 非完美树：可能出现同行同列（如示例 2 的 (2,0) 上同时有 5 和 6），必须按值升序。
- 列索引可为负：排序用整体升序即可，无需偏移。
- 节点值范围 0~1000：无符号问题。
- 输出为**紧凑 JSON** 的二维数组，且为精确比较。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    items = []
    if root is not None:
        stack = [(root, 0, 0)]
        while stack:
            node, r, c = stack.pop()
            items.append((c, r, node[0]))
            if node[1] is not None:
                stack.append((node[1], r + 1, c - 1))
            if node[2] is not None:
                stack.append((node[2], r + 1, c + 1))

    items.sort()

    res = []
    cur_col = None
    for c, r, v in items:
        if c != cur_col:
            res.append([])
            cur_col = c
        res[-1].append(v)

    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TM01"] = r'''
## 思路

求"层数最深的叶子节点之和"，即最后一层所有节点值之和。用 BFS 逐层遍历，记录每一层的节点值之和，最后保留的那一层即为答案。

注意"最深的一层"即最后一层（该层节点必然是叶子，因为下面没有层），因此直接取最后一层的和即可。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(w)，w 为最大层宽。

## 边界与处理

- 单节点：该节点就是最深叶子，返回其值。
- 只有左链或右链：最后一层只有一个节点，返回其值。
- 节点值可达 10^4 且节点数最多 10^4：和最大约 10^8，未超 32 位。
- 层序输入含 null：需按队列式反序列化建树，null 不生成节点，不会虚增层数。
- 输出为单个整数。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    ans = 0
    if root is not None:
        queue = [root]
        while queue:
            total = 0
            nxt = []
            for node in queue:
                total += node[0]
                if node[1] is not None:
                    nxt.append(node[1])
                if node[2] is not None:
                    nxt.append(node[2])
            ans = total
            queue = nxt

    print(ans)


main()
```
'''


SOLUTIONS["TM02"] = r'''
## 思路

要求把每个节点的值改成"树中所有 ≥ 该节点值的节点值之和"。对 BST 而言，按**中序的逆序**（右 → 根 → 左）遍历正好是从大到小访问所有节点，因此只需在遍历过程中维护一个累加和 running，把当前节点替换为 running（累加它自身之后的值）。

正确性：BST 的逆中序访问顺序是降序，故访问到某节点时，running 恰好是"所有 ≥ 它的值"之和（含它自己）。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(h)，迭代栈深度（用显式栈时为 O(h)）。

## 边界与处理

- 单节点：结果为该节点值本身（≥ 它自己的只有它）。
- 空树：输出 []。
- 节点最大者：替换后等于它自己（没有更大的值）。
- 节点值可为负：累加仍成立，无需特判。
- 树可能退化成链：必须用显式栈，避免递归深度限制（节点数可达 10^4）。
- 输出为层序数组，序列化规则见公共函数（null 也输出、不入队、末尾裁剪）。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    running = 0
    cur = root
    stack = []
    while cur is not None or stack:
        while cur is not None:
            stack.append(cur)
            cur = cur[2]
        node = stack.pop()
        running += node[0]
        node[0] = running
        cur = node[1]

    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TM03"] = r'''
## 思路

与上一题同解：BST 的"逆中序"（右 → 根 → 左）访问顺序等价于按值降序。遍历时维护 running = 已访问节点值之和，把当前节点改写为 running。

因为访问到某节点时，所有比它大的节点（含它自己）都已访问过，所以 running 恰好等于"树中 ≥ 该节点值的所有节点值之和"。

## 复杂度分析

- 时间复杂度：O(n)。
- 空间复杂度：O(h)，显式栈深度。

## 边界与处理

- 空树：输出 []。
- 单节点：输出其自身值。
- 节点值非负（0~100）：累加单调不减。
- 只有右孩子（如 [0,null,1]）：逆中序先把右孩子访问完，根得到"1 + 0 = 1"，右孩子得到 1，输出 [1,null,1]（与示例 2 一致）。
- 链状 BST：必须用显式栈，避免递归深度问题。
- 输出为层序数组（null 也输出、不入队、末尾裁剪）。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    running = 0
    cur = root
    stack = []
    while cur is not None or stack:
        while cur is not None:
            stack.append(cur)
            cur = cur[2]
        node = stack.pop()
        running += node[0]
        node[0] = running
        cur = node[1]

    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TM04"] = r'''
## 思路

遍历整棵树，对每个节点检查其**祖父节点**（父节点的父节点）的值是否为偶数，是则把该节点的值计入答案。

用带"父节点引用"的迭代遍历：栈中压入 (当前节点, 父节点值)。由于祖父值在向下走两层后即可确定，可在压栈时把祖父值一并传下去：压栈 (node, parent_val, grand_val)，处理 node 时用 grand_val 判断。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(h)，栈深度。

## 边界与处理

- 只有 1 层或 2 层的树：不存在祖父节点，答案为 0（示例 2 的单节点即此类）。
- 祖父值为 0：0 是偶数，子节点应被计入（不要用真值判断，必须显式 `% 2 == 0`）。
- 节点值均为正（1~100）：不会出现负值干扰。
- 树可能退化成链：用显式栈避免递归过深。
- 每个节点只被计入一次：遍历时按"当前节点"累加，不重复。
- 输出为单个整数。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    ans = 0
    if root is not None:
        stack = [(root, None, None)]
        while stack:
            node, pval, gval = stack.pop()
            if gval is not None and gval % 2 == 0:
                ans += node[0]
            if node[1] is not None:
                stack.append((node[1], node[0], pval))
            if node[2] is not None:
                stack.append((node[2], node[0], pval))

    print(ans)


main()
```
'''


SOLUTIONS["TM05"] = r'''
## 思路

按题意模拟：初始排列 P = [1, 2, …, m]。对每个 query，找到它在 P 中的下标并记入答案，然后把它移到最前面。

m 与查询数都不超过 1000，直接用列表维护即可：查找下标 O(m)，删除并插入到头部 O(m)，总代价 O(m·q) ≤ 10^6。

（若规模更大，可用"逆序编号 + 树状数组"把每次操作降到 O(log(n+q))：把初始元素放在末尾，新移到前面的元素占用递减的空位，用 BIT 统计前缀中已放置元素个数即可得到下标。）

## 复杂度分析

- 时间复杂度：O(m·q)，m、q ≤ 1000。
- 空间复杂度：O(m)，维护排列。

## 边界与处理

- 查询值与当前排列首元素相同：下标为 0，移动后排列不变。
- 重复查询同一个值：每次都要重新找当前下标（示例 1 的 1 查询两次分别得到 1，示例 2 的 2 得到 2、0）。
- m = 1：下标恒为 0。
- 查询值必在 1..m 内，不存在越界；仍用 index() 的返回值，天然安全。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    queries = json.loads(lines[0])
    m = json.loads(lines[1])

    perm = list(range(1, m + 1))
    pos = {v: i for i, v in enumerate(perm)}

    ans = []
    for q in queries:
        i = pos[q]
        ans.append(i)
        # 把 q 移到最前面：它之前的元素整体后移一位
        if i > 0:
            for v in perm[:i]:
                pos[v] += 1
            perm.pop(i)
            perm.insert(0, q)
            pos[q] = 0

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TM06"] = r'''
## 思路

最大二叉树的递归定义：区间 [l, r] 内取最大值作为根，左半区间递归为左子树，右半区间递归为右子树（最大值唯一，故结构唯一）。

实现：为避免每次线性找最大值导致 O(n²)，用**单调栈**一次构造：从左到右扫描，维护一个递减栈；对每个新元素，弹出所有比它小的栈顶，把最后弹出的节点作为它的左孩子；若栈非空，把它的右孩子置为新元素，压栈。栈底即整棵树的最大值（根）。

两种写法结果一致。本题 n ≤ 1000，也可直接递归找最大值，但栈写法更稳健（不依赖递归深度）。

## 复杂度分析

- 时间复杂度：O(n)，每个元素入栈出栈各一次。
- 空间复杂度：O(n)，栈与节点。

## 边界与处理

- 单元素：直接成为根。
- 空数组：输出 []（题目保证长度 ≥ 1，仍作保护）。
- 严格递减（如 [3,2,1]）：退化为只有右孩子的链，输出 [3,null,2,null,1]（示例 2）。
- 元素互不相同（题目保证），无需处理相等时的取舍。
- 元素可为 0：0 是合法值，不能用真值判断是否为空。
- 输出为层序数组（null 也输出、不入队、末尾裁剪）。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    nodes = [[v, None, None] for v in nums]
    stack = []
    for node in nodes:
        last = None
        while stack and stack[-1][0] < node[0]:
            last = stack.pop()
        node[1] = last
        if stack:
            stack[-1][2] = node
        stack.append(node)

    root = stack[0] if stack else None
    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TM07"] = r'''
## 思路

最简单可靠的做法是按层遍历统计节点个数，O(n)。题目"进阶"提到可以做到优于 O(n)：利用完全二叉树的编号性质（节点按层序填满），通过比较左右子树高度判断最后一层的分界，可在 O(log²n) 内求出。

本题优先保证正确性与稳健性：节点数 ≤ 5×10^4，O(n) 完全够用，且不受"最后一层是否填满"等边界影响。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(w)，w 为最大层宽（BFS 队列）。

## 边界与处理

- 空树：返回 0（示例 2）。
- 单节点：返回 1（示例 3）。
- 完全但未填满最后一层：BFS 统计不受影响，不需要额外判断。
- 层序输入含 null：按队列式反序列化，null 不生成节点，不会多计。
- 节点值 0 是合法的，不能用真值判断节点是否存在。
- 输出为单个整数。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    cnt = 0
    if root is not None:
        queue = [root]
        while queue:
            node = queue.pop(0)
            cnt += 1
            if node[1] is not None:
                queue.append(node[1])
            if node[2] is not None:
                queue.append(node[2])

    print(cnt)


main()
```
'''


SOLUTIONS["TM08"] = r'''
## 思路

按层遍历，对每个**奇数层**（根所在层为第 0 层），把该层节点的值收集后整体反转再写回。偶数层不动。

因为完美二叉树每层节点数是固定的，按层收集与写回的对应关系明确：第 k 层第 i 个节点接收该层原第 (len−1−i) 个值。

## 复杂度分析

- 时间复杂度：O(n)，每层收集与回写各一次。
- 空间复杂度：O(w)，最大层宽。

## 边界与处理

- 单节点（只有第 0 层）：没有奇数层，原样返回。
- 三层完美树：只反转第 1 层（示例 1、2）。
- 四层完美树：第 1、3 层都要反转（示例 3）。
- 层宽必须是 2^k：题目保证是完美二叉树，按层切片天然对齐。
- 值可以为 0：不能跳过 0。
- 必须在原地修改节点值，再序列化整棵树。
- 输出为层序数组（null 也输出、不入队、末尾裁剪）。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    level = 0
    queue = [root] if root is not None else []
    while queue:
        nxt = []
        for node in queue:
            if node[1] is not None:
                nxt.append(node[1])
            if node[2] is not None:
                nxt.append(node[2])
        if nxt and (level + 1) % 2 == 1:
            vals = [n[0] for n in nxt]
            vals.reverse()
            for n, v in zip(nxt, vals):
                n[0] = v
        queue = nxt
        level += 1

    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TM09"] = r'''
## 思路

BST 的中序遍历序列是严格升序的，因此第 k 小的元素就是中序遍历的第 k 个节点值。

用迭代中序（显式栈）遍历，计数到 k 即返回，无需遍历完（提前退出）。

## 复杂度分析

- 时间复杂度：O(h + k)，最多访问 h + k 个节点；h 为树高，k ≤ n ≤ 10^4。
- 空间复杂度：O(h)，栈深度。

## 边界与处理

- k = 1：返回最小值（最左侧节点）。
- k = n：返回最大值（最右侧节点）。
- 只有右孩子的树（如 [3,1,4,null,2]）：中序仍正确给出升序序列。
- 节点值可为 0：不能以 0 作为"未找到"的哨兵，用独立计数器判断。
- k 由题目保证有效（1 ≤ k ≤ n），不会越界。
- 输出为单个整数。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))
    k = json.loads(lines[1])

    ans = None
    cnt = 0
    stack = []
    cur = root
    while cur is not None or stack:
        while cur is not None:
            stack.append(cur)
            cur = cur[1]
        node = stack.pop()
        cnt += 1
        if cnt == k:
            ans = node[0]
            break
        cur = node[2]

    print(ans)


main()
```
'''


SOLUTIONS["TM10"] = r'''
## 思路

n ≤ 1000，直接枚举所有子数组 [i, j]，统计其中 target 的出现次数，若严格大于长度的一半则计数加一。

统计可用增量方式：固定 i，向右扩展 j 的同时维护 target 的计数，内层每步 O(1)。

## 复杂度分析

- 时间复杂度：O(n^2)，子数组总数约 n(n+1)/2 ≈ 5×10^5。
- 空间复杂度：O(1)（不计输入）。

## 边界与处理

- target 不在数组中：计数恒为 0，没有子数组满足，返回 0（示例 3）。
- 数组全为 target：所有子数组都满足，答案为 n(n+1)/2（示例 2 的 10）。
- 单元素数组且等于 target：长度 1，出现 1 次 > 0.5，满足，返回 1。
- 严格大于：偶数长度时恰好一半不算（如长度 2 出现 1 次不满足）。
- 元素值可达 10^9：比较用相等判断，不涉及数值运算。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    target = json.loads(lines[1])

    n = len(nums)
    ans = 0
    for i in range(n):
        cnt = 0
        for j in range(i, n):
            if nums[j] == target:
                cnt += 1
            if cnt * 2 > (j - i + 1):
                ans += 1

    print(ans)


main()
```
'''


SOLUTIONS["TM11"] = r'''
## 思路

自底向上递归：对每个节点返回二元组 (子树内最深叶子的深度, 覆盖该子树全部最深叶子的最近公共祖先节点)。

合并规则：
- 左、右子树深度相等 → 当前节点就是答案（最深叶子分布在两侧，最近公共祖先是当前节点）；
- 左深 > 右深 → 继承左子树的结果；
- 右深 > 左深 → 继承右子树的结果。
- 叶子节点自身深度视为 0，返回 (0, 自身)。

## 复杂度分析

- 时间复杂度：O(n)，每个节点处理一次。
- 空间复杂度：O(h)，递归/栈深度；用显式后序栈避免深树递归限制。

## 边界与处理

- 单节点：它本身就是最深的"叶子"，返回自己（示例 2）。
- 只有一条深链：最深的叶子唯一，答案是它自己（示例 3 返回 [2]）。
- 两侧深度相等：返回当前节点（示例 1 中节点 2 左右都是深度 3 的叶子，返回 2）。
- 节点值可重复？题目保证值唯一，不影响判定（判定只依赖结构）。
- 输出是**子树**的层序数组（如 [2,7,4] 表示以 2 为根的子树）。
- 输出需裁剪层序末尾 null。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    if root is None:
        print("[]")
        return

    # 显式后序
    order = []
    stack = [root]
    while stack:
        node = stack.pop()
        order.append(node)
        if node[1] is not None:
            stack.append(node[1])
        if node[2] is not None:
            stack.append(node[2])

    d = {}
    who = {}
    for node in reversed(order):
        l, r = node[1], node[2]
        dl = d[id(l)] if l is not None else -1
        dr = d[id(r)] if r is not None else -1
        if l is None and r is None:
            d[id(node)] = 0
            who[id(node)] = node
        elif dl == dr:
            d[id(node)] = dl + 1
            who[id(node)] = node
        elif dl > dr:
            d[id(node)] = dl + 1
            who[id(node)] = who[id(l)]
        else:
            d[id(node)] = dr + 1
            who[id(node)] = who[id(r)]

    print(json.dumps(serialize(who[id(root)]), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TM12"] = r'''
## 思路

要求"最底层最左边"的节点值。BFS 逐层遍历，记录每一层最左边的节点值（即该层队列的第一个节点），遍历到最后一层时该值即为答案。

也可以在 BFS 时按"先右后左"把孩子入队，最后一个被访问的节点即最底层最左节点，但按层记录更直观。

## 复杂度分析

- 时间复杂度：O(n)。
- 空间复杂度：O(w)，最大层宽。

## 边界与处理

- 单节点：返回该节点值（示例 1 的 [2,1,3] 最左下层是 1）。
- 只有右孩子：最底层最左即该右孩子（示例 2 返回 7）。
- 节点值可为负（−2^31 ~ 2^31−1）：不能用 0 或真值作为哨兵，需在遍历中显式赋值。
- 题目保证至少有一个节点，无空树情形；代码仍保护。
- 层序输入含 null：按队列式反序列化。
- 输出为单个整数。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    ans = None
    queue = [root] if root is not None else []
    while queue:
        ans = queue[0][0]
        nxt = []
        for node in queue:
            if node[1] is not None:
                nxt.append(node[1])
            if node[2] is not None:
                nxt.append(node[2])
        queue = nxt

    print(ans if ans is not None else 0)


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
        os.path.dirname(os.path.abspath(__file__)), "batch06.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
