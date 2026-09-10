# -*- coding: utf-8 -*-
"""第五批「会话内助手撰写」的解答（TE13-TE15, TH01-TH12）。

输出格式遵循参考解 main() 的统一约定：
  list/dict → json.dumps(..., separators=(',',':'))；bool → 小写；float → repr；其余 str。
树仍按 LeetCode 层序（含 null、末尾裁剪）。
"""
SOLUTIONS = {}

_TREE_HELPERS = r'''
def build_tree(arr):
    """LeetCode 层序数组 -> 树；必须用队列式反序列化（下标映射在含 null 时会错配）。"""
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


SOLUTIONS["TE13"] = r'''
## 思路

后序遍历顺序为"左 → 右 → 根"。用**迭代法**实现（回应题目的进阶要求）：把节点按"根入栈 → 记录访问顺序"的方式做一次变形的先序（根→右→左），最后把结果整体反转，即得后序。

等价写法是先序模板"根、右、左"，其序列反转后正好是"左、右、根"。该变形只改压栈顺序，避免了对访问标记的需求。

## 复杂度分析

- 时间复杂度：O(n)，每个节点入栈出栈各一次，最后一次反转 O(n)。
- 空间复杂度：O(h)，栈深度（h 为树高），最坏 O(n)。

## 边界与处理

- 空树：输出 []（示例 3）。
- 单节点：输出 [val]（示例 4）。
- 只有左孩子 / 只有右孩子：变形先序 + 反转仍给出正确的后序。
- 节点值为负：与遍历顺序无关。
- 层序输入含 null：需按队列式反序列化建树，不能按下标映射。
- 输出为**紧凑 JSON**，且为精确比较，顺序不能错（[1,null,2,3] 必须是 [3,2,1]）。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    out = []
    if root is not None:
        stack = [root]
        while stack:
            node = stack.pop()
            out.append(node[0])
            if node[1] is not None:
                stack.append(node[1])
            if node[2] is not None:
                stack.append(node[2])

    out.reverse()
    print(json.dumps(out, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TE14"] = r'''
## 思路

按题意直接模拟：从左到右处理每种水果，在**当前仍可用的篮子**中找最左侧且容量 ≥ 该水果数量的篮子，把它标记为已用；找不到则该水果未放置。

因为每个篮子只能装一种水果、且必须选最左侧可用者，这是一个确定的贪心过程，不存在选择空间，模拟即可得到唯一结果。最后返回未放置的水果种类数（即处理中被判定"无法放入"的水果个数）。

## 复杂度分析

- 时间复杂度：O(n^2)，每种水果最坏要扫描全部篮子；n ≤ 100。
- 空间复杂度：O(n)，记录篮子的可用状态。

## 边界与处理

- 所有水果都能放置：返回 0（示例 2）。
- 部分水果放不下：返回放不下的个数（示例 1 返回 1）。
- 容量相等：要求"容量 ≥ 水果数量"，相等也满足。
- 篮子被占用后不再可用：必须用单独的 used 标记，不能直接改容量（否则会误判）。
- 跳过容量不足的篮子继续往右找，而不是直接判定失败（示例 2 中 fruits[1]=6 跳过容量 4 找到容量 7）。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    fruits = json.loads(lines[0])
    baskets = json.loads(lines[1])

    n = len(baskets)
    used = [False] * n
    fail = 0
    for f in fruits:
        placed = False
        for j in range(n):
            if not used[j] and baskets[j] >= f:
                used[j] = True
                placed = True
                break
        if not placed:
            fail += 1

    print(fail)


main()
```
'''


SOLUTIONS["TE15"] = r'''
## 思路

层序遍历（BFS）逐层累加节点值并计数，得到每层的平均值。

用队列按层推进：每次处理当前队列中的全部节点（即一整层），累加它们的值并记录个数，平均值 = 总和 / 个数；同时把下一层的孩子入队。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(w)，w 为最大层宽（队列），最坏 O(n)。

## 边界与处理

- 单节点：只输出一层。
- 层数不完整的树（如示例 2 的 [3,9,20,15,7]）：15、7 视为第 2 层，BFS 按队列分层仍然正确。
- 整值平均：如 3.0、11.0，输出时需保留浮点形式（3.0 而非 3），所以用 float 除法而非整除，并由 json.dumps 序列化。
- 节点值可达 ±2^31−1：Python 整数求和无溢出。
- 输出必须是**紧凑 JSON**，且为精确比较：期望串形如 [3.0,14.5,11.0]。
- 层序输入含 null：按队列式反序列化建树。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    root = build_tree(json.loads(lines[0]))

    res = []
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
            res.append(total / len(queue))
            queue = nxt

    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TH01"] = r'''
## 思路

先证明贪心最优性：把所有连通块的值加起来等于全树总和 T，且 T 能被 k 整除（题目保证）。

自底向上做**后序**处理：对每个节点计算其子树的节点值之和 s。若 s 能被 k 整除，就把"该子树与其父节点之间的边"切掉，形成一个合法连通块，并把 s 记为一个连通块，然后向父节点返回 0（相当于把这部分已经"结算"掉了）；否则把 s 原样返回给父节点累加。

为什么这样最多？任意一条被切掉的边，其下方连通块的值必须能被 k 整除，而下方连通块的值恰好是某个子树的 s 减去已切走的若干可整除子树——由于那些被切走的子树本身能被 k 整除，不影响能否整除的判断，因此"能切就切"不会堵死后续机会，贪心取到上界。最终根节点的剩余值 = T 减去所有已切走子树之和，仍是 k 的倍数，会再记为一个连通块。

用显式栈做后序以避免 n 达 3×10^4 时的递归深度问题。

## 复杂度分析

- 时间复杂度：O(n)，每个节点进出栈各一次。
- 空间复杂度：O(n)，邻接表、父子关系与栈。

## 边界与处理

- n = 1（无边）：整棵树本身即一个连通块，值为 values[0]；因总和可被 k 整除，答案为 1。
- 存在值为 0 的节点：0 能被任何 k 整除，会立即切出单节点连通块，这正是最优做法。
- k 大于总和：题目保证总和可被 k 整除，故只可能是总和为 0（此时每个零值子树都会被切出）。
- 不能切出"空连通块"：切边只发生在父子之间，每次切出的子树至少含一个节点。
- 输入无向树：需要先按任意根（取 0）建父子关系，避免把父节点当作子节点重复访问。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    edges = json.loads(lines[1])
    values = json.loads(lines[2])
    k = json.loads(lines[3])

    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    # 显式后序：先算出遍历顺序，再逆序累加子树和
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

    sub = list(values)
    ans = 0
    for u in reversed(order):
        if sub[u] % k == 0:
            ans += 1
            if parent[u] != -1:
                sub[parent[u]] += 0
            sub[u] = 0
        else:
            if parent[u] != -1:
                sub[parent[u]] += sub[u]
            sub[u] = 0

    print(ans)


main()
```
'''


SOLUTIONS["TH02"] = r'''
## 思路

遍历串由若干"若干短划线 + 数字"组成，短划线个数即节点深度。按深度用栈还原：

- 逐个解析出 (depth, value)；
- 栈中保存"当前从根到上一节点的路径"，栈的大小应恰为 depth（根深度 0 时栈大小为 1）；
- 因此先 while len(stack) > depth 弹栈，使栈顶就是新节点的父节点；
- 父节点的左孩子为空则挂左，否则挂右（题目保证只有一个子节点时必为左孩子）；
- 把新节点压栈。

最后按层序输出（含 null，末尾裁剪）。

## 复杂度分析

- 时间复杂度：O(|S|)，解析与建树各一遍；每个节点至多入栈出栈一次。
- 空间复杂度：O(n)，栈与节点数（n ≤ 1000）。

## 边界与处理

- 单节点（如 "1"）：深度 0，解析后直接成为根。
- 只有左孩子的链（如 "1-2--3---4"）：深度严格递增，全程走"挂左孩子"分支，层序输出中会出现 null 占位（示例 2、3 验证）。
- 值可以很大（≤ 10^9）或多位：按数字连续读取，不能用单字符解析。
- 短划线个数即深度，不能按"每层固定两个短划线"处理。
- 输出需裁剪层序末尾的 null。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    traversal = json.loads(lines[0])

    pairs = []
    i = 0
    n = len(traversal)
    while i < n:
        d = 0
        while i < n and traversal[i] == "-":
            d += 1
            i += 1
        j = i
        while j < n and traversal[j] != "-":
            j += 1
        pairs.append((d, int(traversal[i:j])))
        i = j

    root = None
    stack = []
    for d, val in pairs:
        while len(stack) > d:
            stack.pop()
        node = [val, None, None]
        if not stack:
            root = node
        else:
            p = stack[-1]
            if p[1] is None:
                p[1] = node
            else:
                p[2] = node
        stack.append(node)

    print(json.dumps(serialize(root), separators=(",", ":")))


main()
```
'''


SOLUTIONS["TH03"] = r'''
## 思路

固定 target，把数组映射为 +1/−1（等于 target 记 +1，否则记 −1），并取前缀和 P（P[0] = 0，P[i+1] = P[i] ± 1）。则子数组 (i, j] 中 target 的出现次数严格多于一半 ⟺ P[j] > P[i]。

于是问题变成：统计满足 i < j 且 P[j] > P[i] 的下标对数量。用**树状数组（Fenwick）**按值域统计已出现的 P[i] 个数：从左到右扫描 j，先查询"小于 P[j] 的已有前缀个数"并累加，再把 P[j] 插入。

## 复杂度分析

- 时间复杂度：O(n log n)，n 次查询 + n 次插入，每次 O(log n)。
- 空间复杂度：O(n)，前缀和与树状数组。

## 边界与处理

- target 不在数组中：所有映射为 −1，前缀和严格递减，无满足 P[j] > P[i] 的对，答案为 0（示例 3）。
- 数组全为 target：前缀和严格递增，答案为 C(n,2)（示例 2 的 10）。
- 值域偏移：前缀和可为负，需整体平移到正整数再索引树状数组（偏移量 n+1 足够）。
- i 从 0 开始（空前缀），因此答案里包含"从第一个元素开始的子数组"。
- 答案规模：n ≤ 10^5 时最大约 5×10^9，超出 32 位，Python 整数无碍。
- 输出为单个整数（long）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    target = json.loads(lines[1])

    n = len(nums)
    offset = n + 2
    size = 2 * n + 5

    tree = [0] * (size + 1)

    def add(i):
        i += 1
        while i <= size:
            tree[i] += 1
            i += i & (-i)

    def query(i):
        """统计值 <= i（已加 offset）的个数。"""
        i += 1
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s

    ans = 0
    p = 0
    add(p + offset)
    for x in nums:
        p += 1 if x == target else -1
        ans += query(p + offset - 1)
        add(p + offset)

    print(ans)


main()
```
'''


SOLUTIONS["TH04"] = r'''
## 思路

以节点 0 为根，做一次 DFS 求出：
- sub[v]：以 v 为根子树的节点值异或；
- tin[v] / tout[v]：DFS 进出时间，用于 O(1) 判断祖先关系。

记为根的全树异或 T = sub[0]。每条边对应其"下方"的那个节点。任选两条不同的边（下方节点为 u、v，u ≠ v）会形成三个连通块：
- 若 u 是 v 的祖先：块值为 sub[v]、sub[u] ^ sub[v]、T ^ sub[u]；
- 若 u 与 v 互不为祖先：块值为 sub[u]、sub[v]、T ^ sub[u] ^ sub[v]。

枚举所有边对（n−1 ≤ 999，共约 5×10^5 对），用 tin/tout 判祖先，计算分数（最大异或 − 最小异或）取最小值。

## 复杂度分析

- 时间复杂度：O(n^2)，n ≤ 1000，约 5×10^5 次常数操作。
- 空间复杂度：O(n)，邻接表、sub、tin/tout。

## 边界与处理

- n = 3（最少节点）：只有两条边，枚举唯一的一对。
- 无法三分的异或相等（如示例 2）：分数 0，取到最小值下界。
- 异或值可为 0：min 取到 0 时分数为 max，比较逻辑不变。
- 祖先关系必须用 tin/tout 判定，不能只比较节点编号。
- 用显式栈做 DFS，避免 n 较大时的递归深度问题。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    edges = json.loads(lines[1])

    n = len(nums)
    adj = [[] for _ in range(n)]
    for idx, (a, b) in enumerate(edges):
        adj[a].append((b, idx))
        adj[b].append((a, idx))

    # 迭代 DFS 求 tin/tout 与顺序
    parent = [-1] * n
    parent_edge = [-1] * n
    tin = [0] * n
    tout = [0] * n
    order = []
    timer = 0
    stack = [(0, 0)]
    while stack:
        u, state = stack.pop()
        if state == 0:
            tin[u] = timer
            timer += 1
            order.append(u)
            stack.append((u, 1))
            for v, ei in adj[u]:
                if v != parent[u]:
                    parent[v] = u
                    parent_edge[v] = ei
                    stack.append((v, 0))
        else:
            tout[u] = timer

    sub = list(nums)
    for u in reversed(order):
        if parent[u] != -1:
            sub[parent[u]] ^= sub[u]

    total = sub[0]

    def is_anc(a, b):
        return tin[a] <= tin[b] and tout[b] <= tout[a]

    # 每条边对应其下方节点
    child_of_edge = [0] * len(edges)
    for v in range(n):
        if parent_edge[v] != -1:
            child_of_edge[parent_edge[v]] = v

    nodes = child_of_edge
    best = None
    m = len(nodes)
    for i in range(m):
        u = nodes[i]
        for j in range(i + 1, m):
            v = nodes[j]
            if is_anc(u, v):
                parts = (sub[v], sub[u] ^ sub[v], total ^ sub[u])
            elif is_anc(v, u):
                parts = (sub[u], sub[v] ^ sub[u], total ^ sub[v])
            else:
                parts = (sub[u], sub[v], total ^ sub[u] ^ sub[v])
            score = max(parts) - min(parts)
            if best is None or score < best:
                best = score
                if best == 0:
                    print(0)
                    return

    print(best if best is not None else 0)


main()
```
'''


SOLUTIONS["TH05"] = r'''
## 思路

记 diff[i] = (start[i] != target[i])。一次操作翻转一条边两个端点的颜色，等价于把这两个端点的 diff 同时取反。

以节点 0 为根做自底向上处理：对节点 u（非根），先处理完它的所有孩子后，若此时 diff[u] == 1，说明 u 的差异必须靠"u 与父节点之间的边"来消除——这条边被翻，于是把 diff[父] 取反，并把这条边记入答案。处理完所有非根节点后，若根节点 diff 仍为 1，说明无法消除，返回 [−1]。

为什么这是最短：树中共有 n−1 条边，每条边至多翻转一次即可（翻转两次互相抵消，属于冗余）；且对任一节点 u，若它与其父之间的边不翻，则 u 的 diff 只能由其子边改变，而子边已在子树内确定——归纳可知每一步的选择是被迫的，因此解法唯一且最短。

## 复杂度分析

- 时间复杂度：O(n)，每个节点处理一次。
- 空间复杂度：O(n)，邻接表与遍历栈（n ≤ 10^5，用显式栈避免递归过深）。

## 边界与处理

- diff 全 0：不需要任何操作，返回空数组 []（注意不是 [-1]）。
- 差异节点数为奇数（示例 3）：无法消除，返回 [-1]。原因是每次操作改变 2 个节点的 diff 奇偶性，总的 diff 奇偶性不变。
- 结果需按边下标**升序**返回：按 DFS 顺序收集后排序。
- 边下标是输入数组中的下标，不是节点编号，需在建图时记录。
- 根节点的选择不影响答案的存在性与最小性，这里固定取 0。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    edges = json.loads(lines[1])
    start = json.loads(lines[2])
    target = json.loads(lines[3])

    adj = [[] for _ in range(n)]
    for idx, (a, b) in enumerate(edges):
        adj[a].append((b, idx))
        adj[b].append((a, idx))

    diff = [1 if start[i] != target[i] else 0 for i in range(n)]

    parent = [-1] * n
    pedge = [-1] * n
    order = []
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        order.append(u)
        for v, ei in adj[u]:
            if not visited[v]:
                visited[v] = True
                parent[v] = u
                pedge[v] = ei
                stack.append(v)

    res = []
    for u in reversed(order):
        if u == 0:
            continue
        if diff[u] == 1:
            res.append(pedge[u])
            diff[parent[u]] ^= 1

    if diff[0] == 1:
        print("[-1]")
    else:
        res.sort()
        print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TH06"] = r'''
## 思路

条件"数对 [x, y] 出现在 pairs 中当且仅当 x 与 y 有祖先关系"意味着：树中任意两个节点的祖先关系必须与 pairs 完全一致。

关键性质：若 x 是 y 的祖先，则 x 的所有祖先也都是 y 的祖先。因此把每个节点的"邻接集合"（与它有祖先关系的节点集合）写出后，祖先的集合必然包含后代集合加上自身。

做法：
1. 收集所有出现过的值，建立邻接集合 adj。
2. 根节点必须与所有其他节点都有祖先关系，故 |adj[root]| 必须等于节点数 − 1；否则无解，返回 0。
3. 对所有满足该条件的候选根，按 |adj| 降序（同值按数值升序）构造树：对每个节点 v，其父节点取"在排序中位于 v 之前、且 adj 中包含 v"的第一个节点（即邻接集合最小的那个真祖先）。
4. 校验：对每一对输入 pair，必须一个有祖先关系；对每一对非输入的节点组合，必须无祖先关系。
5. 统计通过校验且父指针数组互不相同的方案数：0 → 0，1 → 1，≥2 → 2。

## 复杂度分析

- 时间复杂度：O(V^2 + P)，V 为不同值个数、P 为 pairs 数。候选根至多 V 个，每个方案构造与校验各 O(V^2 + P)；n ≤ 2×10^5 但本题实际输入很小（官方用例仅 4 对）。
- 空间复杂度：O(V^2)，邻接集合。

## 边界与处理

- 无满足 |adj| = V−1 的节点：必然无解，返回 0（本题官方用例即属此类：1↔{2,5}、2↔{1,3,4}、3↔{2}、4↔{2}、5↔{1}，最大 |adj| 为 3 < 4）。
- 只有一个节点：pairs 为空时任意单节点树都成立，方案数为 1。
- 多个候选根都合法：说明存在多种方案，返回 2。
- 祖先关系必须双向一致：既要所有 pair 都是祖先对，也要所有非 pair 都不是，只查一侧会把非法方案误判为合法。
- 节点值不连续（可能很大）：必须用字典做值到编号的映射，不能直接用值当数组下标。

## 代码
```python
import sys
import json
from itertools import combinations


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    pairs = json.loads(lines[0])

    vals = set()
    for a, b in pairs:
        vals.add(a)
        vals.add(b)
    vals = sorted(vals)
    idx = {v: i for i, v in enumerate(vals)}
    V = len(vals)

    adj = [set() for _ in range(V)]
    pairset = set()
    for a, b in pairs:
        ia, ib = idx[a], idx[b]
        adj[ia].add(ib)
        adj[ib].add(ia)
        pairset.add((min(ia, ib), max(ia, ib)))

    if V == 1:
        print(1 if not pairs else 0)
        return

    candidates = [v for v in range(V) if len(adj[v]) == V - 1]

    def ancestor_closure(parent):
        """返回每个节点的祖先集合。"""
        anc = [set() for _ in range(V)]
        order = []
        children = [[] for _ in range(V)]
        root = None
        for v in range(V):
            if parent[v] == -1:
                root = v
            else:
                children[parent[v]].append(v)
        stack = [(root, [])]
        while stack:
            u, path = stack.pop()
            anc[u] = set(path)
            for c in children[u]:
                stack.append((c, path + [u]))
        return anc

    plans = set()
    for root in candidates:
        # 祖先的邻接集合大小必然不小于后代，故按 |adj| 降序即可得到可行拓扑序；
        # 同大小时按值升序打破平局。根固定排在最前。
        others = sorted((v for v in range(V) if v != root), key=lambda v: (-len(adj[v]), v))
        order = [root] + others

        parent = [-1] * V
        depth = [0] * V
        assigned = [root]
        ok = True
        for v in order[1:]:
            # 父节点必须在 v 的邻居中取"最深的那个"：取浅的会让中间节点变成兄弟，
            # 从而破坏「非祖先对不能出现在 pairs 中」这一双向约束。
            chosen = -1
            best_d = -1
            for u in assigned:
                if v in adj[u] and depth[u] > best_d:
                    best_d = depth[u]
                    chosen = u
            if chosen == -1:
                ok = False
                break
            parent[v] = chosen
            depth[v] = depth[chosen] + 1
            assigned.append(v)
        if not ok:
            continue

        anc = ancestor_closure(parent)
        good = True
        for i in range(V):
            for j in range(i + 1, V):
                related = (i in anc[j]) or (j in anc[i])
                if related != ((i, j) in pairset):
                    good = False
                    break
            if not good:
                break
        if good:
            plans.add(tuple(parent))

    if not plans:
        print(0)
    elif len(plans) == 1:
        print(1)
    else:
        print(2)


main()
```
'''


SOLUTIONS["TH07"] = r'''
## 思路

在完全二叉树中给节点 a、b 之间加一条边，会形成唯一一个环：树上 a 到 b 的唯一路径 + 新加的边。所以环长 = dist(a, b) + 1。

节点编号满足父节点 = ⌊v/2⌋，因此可以沿着"不断除以 2"向上找到最近公共祖先。深度（从根 1 出发的层数）由编号的二进制长度决定：depth(v) = ⌊log2 v⌋。

dist(a, b) = depth(a) + depth(b) − 2·depth(lca(a, b))。

求 lca：把较深的节点不断除以 2 提升到同深度，再同步上移直到相等（编号 ≤ 2^30，最多 30 步）。

## 复杂度分析

- 时间复杂度：O(m log(maxval))，每个查询的 lca 最多走 2×30 步；m ≤ 10^5。
- 空间复杂度：O(1)（不计输出）。

## 边界与处理

- 相邻两节点（如 1 与 2）：路径长度为 1，环长为 2（示例 2）。
- 一节点是另一节点的祖先：路径即垂直链，lca 为祖先自身，深度差即为距离。
- 完全二叉树不必真的建树：2^30 级别无法建树，必须用编号性质。
- 节点编号从 1 开始，不能用 0 号节点的取模写法。
- depth 用位长计算（v.bit_length() − 1），避免浮点 log 的精度问题。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    queries = json.loads(lines[1])

    def depth(v):
        return v.bit_length() - 1

    def lca(a, b):
        while depth(a) > depth(b):
            a //= 2
        while depth(b) > depth(a):
            b //= 2
        while a != b:
            a //= 2
            b //= 2
        return a

    ans = []
    for a, b in queries:
        d = depth(a) + depth(b) - 2 * depth(lca(a, b))
        ans.append(d + 1)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TH08"] = r'''
## 思路

记 peaked[k] = 1 表示 nums[k] 是局部峰值（严格大于左右邻居）。

一个子数组 [i, j]（长度 ≥ 3）是峰值子数组 ⟺ 区间 (i, j) 内存在局部峰值。

对查询 [l, r]，设 m = r − l + 1：
- 长度 ≥ 3 的子数组总数 = C(m, 2) − (m − 1)；
- 需要减去"内部没有峰值"的那些对。

把区间内的峰值位置 q_1 < … < q_t 作为分割点（边界取 l−1 与 r+1 的外侧，实际按 [l..q_1]、[q_1..q_2]、…、[q_t..r] 分段，相邻段共享一个峰值端点）。落在同一段内的 (i, j) 对，其内部必无峰值；反之必有一个峰值落在内部。

记每段的长度为 c_s，则该段贡献的"内部无峰值且 j−i ≥ 2"的对数为 C(c_s, 2) − (c_s − 1) = d_s(d_s − 1)/2（其中 d_s = c_s − 1）。

关键恒等式：Σ d_s = m − 1，且 Σ d_s² 可由"相邻峰值间距"聚合得到。于是
内部无峰值的对数 = (Σ d_s² − (m − 1)) / 2，
其中 d 序列为：首个峰值到 l 的距离、(相邻峰值的间距)、最后一个峰值到 r 的距离。

用**线段树**维护峰值指示数组，每个节点保存：峰值个数 cnt、最左峰值位置 first、最右峰值位置 last、以及区间内相邻峰值间距的平方和 sumsq。合并时 sumsq 只新增 (右.first − 左.last)² 一项。查询 [l, r] 后即可 O(1) 算出 Σd²。

点更新时只需重算 idx−1、idx、idx+1 三个位置的峰值状态。

## 复杂度分析

- 时间复杂度：O((n + q) log n)。建树 O(n)，每次更新至多 3 次点更新，每次查询 1 次区间查询。
- 空间复杂度：O(n)，线段树四个数组。

## 边界与处理

- 数组端点（下标 0 与 n−1）不可能是峰值：它们没有两侧邻居，判定时直接取 0。
- 峰值判据是**严格**大于，相等不算峰值（示例中 9,8,9,8 的第二个 9 因两侧都是 8 而成为峰值）。
- 查询区间内没有任何峰值：结果必为 0，此时 sumsq 视为 (m−1)² 使 bad = 总数，相减得 0。
- 区间长度为 3 时只有 1 个候选子数组，公式仍成立（示例 3 第一个查询得 0）。
- 更新会影响 idx−1/idx/idx+1 三个位置的峰值状态，漏掉会导致后续查询错位。
- 输出为紧凑 JSON 数组，只包含类型 1 查询的答案。

## 代码
```python
import sys
import json


def main():
    data = sys.stdin.read()
    dec = json.JSONDecoder()
    arrs = []
    i = 0
    while i < len(data):
        while i < len(data) and data[i] in " \t\r\n":
            i += 1
        if i >= len(data):
            break
        obj, i = dec.raw_decode(data, i)
        arrs.append(obj)

    nums = arrs[0]
    queries = arrs[1]
    n = len(nums)

    size = 1
    while size < n:
        size *= 2
    cnt = [0] * (2 * size)
    first = [-1] * (2 * size)
    last = [-1] * (2 * size)
    sumsq = [0] * (2 * size)

    def peak_at(k):
        if k <= 0 or k >= n - 1:
            return 0
        return 1 if (nums[k] > nums[k - 1] and nums[k] > nums[k + 1]) else 0

    def pull(node):
        lc = 2 * node
        rc = lc + 1
        cnt[node] = cnt[lc] + cnt[rc]
        if cnt[lc]:
            first[node] = first[lc]
        else:
            first[node] = first[rc]
        if cnt[rc]:
            last[node] = last[rc]
        else:
            last[node] = last[lc]
        sumsq[node] = sumsq[lc] + sumsq[rc]
        if cnt[lc] and cnt[rc]:
            d = first[rc] - last[lc]
            sumsq[node] += d * d

    def set_leaf(k, val):
        p = size + k
        cnt[p] = val
        first[p] = k if val else -1
        last[p] = k if val else -1
        sumsq[p] = 0
        p //= 2
        while p >= 1:
            pull(p)
            p //= 2

    for k in range(n):
        v = peak_at(k)
        p = size + k
        cnt[p] = v
        first[p] = k if v else -1
        last[p] = k if v else -1
    for p in range(size - 1, 0, -1):
        pull(p)

    def query(l, r):
        """返回区间 [l, r] 的 (cnt, first, last, sumsq) 聚合。"""
        res = [0, -1, -1, 0]
        lo = l + size
        hi = r + size + 1
        left_parts = []
        right_parts = []
        while lo < hi:
            if lo & 1:
                left_parts.append(lo)
                lo += 1
            if hi & 1:
                hi -= 1
                right_parts.append(hi)
            lo //= 2
            hi //= 2
        for node in left_parts + right_parts[::-1]:
            c = cnt[node]
            res[0] += c
            if c:
                nf = first[node]
                nl = last[node]
                if res[2] != -1:
                    d = nf - res[2]
                    res[3] += d * d
                res[3] += sumsq[node]
                if res[1] == -1:
                    res[1] = nf
                res[2] = nl
        return res

    out = []
    for q in queries:
        if q[0] == 2:
            _, pos, val = q
            nums[pos] = val
            for k in (pos - 1, pos, pos + 1):
                if 0 <= k < n:
                    set_leaf(k, peak_at(k))
        else:
            _, l, r = q
            m = r - l + 1
            total = m * (m - 1) // 2 - (m - 1)
            if total <= 0:
                out.append(0)
                continue
            c, f, la, sq = query(l, r)
            if c == 0:
                bad = total
            else:
                dsq = (f - l) * (f - l) + sq + (r - la) * (r - la)
                bad = (dsq - (m - 1)) // 2
            out.append(total - bad)

    print(json.dumps(out, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TH09"] = r'''
## 思路

把每个冲突对写成 (lo, hi) = (min, max)。子数组 [l, r]（1 起）含有某一对 ⟺ l ≤ lo 且 hi ≤ r。

固定右端点 r：所有 hi ≤ r 的对都是"威胁"，要求 l > lo，即 l ≥ max{lo} + 1。设 M(r) = max{lo : hi ≤ r}（不存在则视为 0），则以 r 结尾的合法子数组个数为 r − max(1, M(r)+1) + 1 = r − max(1, M(r)+1) + 1。

记 base = Σ_r 合法个数（未删除任何对时）。

删除某一对 p 后，只有 r ≥ hi_p 的区间会变化：此时 M'(r) 变成"去掉 p 后的最大值"。因此
gain(p) = Σ_{r ≥ hi_p 且 p 是唯一取到最大值的对} (max(1,M(r)+1) − max(1,M2(r)+1))，
其中 M2(r) 是去掉 p 后的次大值。

实现：对 r 从 1 到 n 扫描，把 hi == r 的对插入一个"维护最大值/次大值/最大值个数/取到最大值的对编号"的滑动统计量即可 O(1) 更新，从而总复杂度 O(n + P)。

## 复杂度分析

- 时间复杂度：O(n + P)，一次线性扫描维护最大值与次大值。
- 空间复杂度：O(n + P)。

## 边界与处理

- 冲突对可能重复或以 (b, a) 顺序给出：统一按 (min, max) 处理，避免重复计数。
- 同一 r 上有多个对：需要维护"最大值个数"，个数 ≥ 2 时删除任一个都不改变 M(r)，gain 为 0。
- M(r) = 0（还没有任何威胁）：max(1, 0+1) = 1，表示所有子数组都合法。
- 必须删除恰好一个对：即使删除后没有增益也要删（题目要求"恰好删除一个"），但取最大值时删除无增益的对与不删等价，故答案 = base + max(0, max_p gain(p))。
- n 可达 10^5、pairs 可达 2n：线性扫描即可，不能用 O(n·P) 的暴力。
- 输出为单个整数（long）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    pairs = json.loads(lines[1])

    by_hi = [[] for _ in range(n + 2)]
    m = len(pairs)
    for i, (a, b) in enumerate(pairs):
        lo, hi = (a, b) if a < b else (b, a)
        by_hi[hi].append((lo, i))

    gain = [0] * m

    best_val = 0
    best_cnt = 0
    best_id = -1
    second_val = 0

    base = 0
    for r in range(1, n + 1):
        for lo, pid in by_hi[r]:
            v = lo + 1
            if v > best_val:
                second_val = best_val
                best_val = v
                best_cnt = 1
                best_id = pid
            elif v == best_val:
                best_cnt += 1
            else:
                if v > second_val:
                    second_val = v

        L = best_val if best_val > 1 else 1
        base += r - L + 1

        if best_cnt == 1 and best_id != -1:
            other = second_val if second_val > 1 else 1
            cur = best_val if best_val > 1 else 1
            gain[best_id] += cur - other

    print(base + max([0] + gain))


main()
```
'''


SOLUTIONS["TH10"] = r'''
## 思路

"目标节点"要求路径边数为偶数。树是二分图，把节点按深度奇偶染色后：**dist(u, v) 为偶数 ⟺ u 与 v 同色**。

因此对第一棵树中的节点 i，不改动时它的目标节点数 = 与 i 同色的节点数（即 i 所在色类的大小）。

连接两棵树后，第一棵树中节点 i 到第二棵树某节点 w 的距离 = dist(i, a) + 1 + dist(b, w)（a、b 为所连的两个节点）。要让它为偶数，需要选择 a、b 的奇偶组合。可以自由选择 a（第一棵树的任意节点）与 b（第二棵树的任意节点），因此第二棵树贡献的节点数是"可以取到的最大的同色类大小"，即 max(第二棵树两个色类的大小)。这个最大值与 i 无关。

于是 answer[i] = 第一棵树中与 i 同色的节点数 + max(第二棵树两个色类的大小)。

## 复杂度分析

- 时间复杂度：O(n + m)，两棵树各做一次 BFS/DFS 染色。
- 空间复杂度：O(n + m)，邻接表。

## 边界与处理

- 单节点树：色类大小为 1，公式仍成立。
- 第二棵树为二分图的两部分大小可能相差很大：取 max 即最优。
- 选 a 的自由度必须利用：若固定 a = i，则可能只能取到较小的色类，因此必须先明确 a 可任选。
- 节点编号从 0 开始且可能不连续使用（树一定连通且含全部编号，故不会有空缺）。
- n、m 均可达 10^5：必须用迭代 BFS，避免递归过深。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json
from collections import deque


def color_counts(n, edges):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    color = [-1] * n
    color[0] = 0
    dq = deque([0])
    c0 = 1
    c1 = 0
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if color[v] == -1:
                color[v] = 1 - color[u]
                if color[v] == 0:
                    c0 += 1
                else:
                    c1 += 1
                dq.append(v)
    return color, c0, c1


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    e1 = json.loads(lines[0])
    e2 = json.loads(lines[1])

    n = len(e1) + 1
    m = len(e2) + 1

    color1, a0, a1 = color_counts(n, e1)
    _, b0, b1 = color_counts(m, e2)

    best2 = max(b0, b1)
    ans = [(a0 if color1[i] == 0 else a1) + best2 for i in range(n)]
    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["TH11"] = r'''
## 思路

矩形面积并集的标准解法是**扫描线 + 坐标压缩**：
1. 收集所有矩形的 x 坐标，排序去重，得到若干竖直"条带" [x_k, x_{k+1}]；
2. 对每个条带，找出所有横跨该条带的矩形，取它们在 y 方向上的区间并集长度 L_k；
3. 该条带贡献面积 = (x_{k+1} − x_k) × L_k；
4. 求和后对 10^9 + 7 取模。

y 区间并集：把相关矩形的 [y1, y2] 排序，按起点贪心合并（当前区间终点 ≥ 下一区间起点则合并）。

## 复杂度分析

- 时间复杂度：O(n^2 log n)，条带至多 2n−1 个，每个条带扫描全部矩形并对 ≤ n 个区间排序；n ≤ 200。
- 空间复杂度：O(n)。

## 边界与处理

- 单个矩形：答案为 (x2−x1)(y2−y1)。
- 极大坐标（≤ 10^9）：面积可达 10^18，必须用 Python 大整数精确累加后再取模，**不能**中途取模（会导致错误），也不能用浮点。
- 矩形可退化为线段？题目保证面积不为 0，故 x1<x2、y1<y2。
- 完全重叠：并集算法天然去重。
- 相邻条带互不重叠，因此可以直接按条带累加，不会重复计算。
- 输出为单个整数（取模后）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    rects = json.loads(lines[0])

    xs = sorted({r[0] for r in rects} | {r[2] for r in rects})

    total = 0
    for k in range(len(xs) - 1):
        xl = xs[k]
        xr = xs[k + 1]
        if xr <= xl:
            continue
        intervals = []
        for x1, y1, x2, y2 in rects:
            if x1 <= xl and xr <= x2:
                intervals.append((y1, y2))
        if not intervals:
            continue
        intervals.sort()
        merged = 0
        cur_l, cur_r = intervals[0]
        for a, b in intervals[1:]:
            if a <= cur_r:
                if b > cur_r:
                    cur_r = b
            else:
                merged += cur_r - cur_l
                cur_l, cur_r = a, b
        merged += cur_r - cur_l
        total += (xr - xl) * merged

    print(total % (10 ** 9 + 7))


main()
```
'''


SOLUTIONS["TH12"] = r'''
## 思路

"活跃区段数"在本判题中即最终字符串里 '1' 的个数（各示例均与 '1' 的计数一致）。

操作的效果：先删掉一个**被 '0' 包围的连续 '1' 区块**（长度 a），再把一个**被 '1' 包围的连续 '0' 区块**（长度 b）改成 '1'。考察 t = '1' + s[l..r] + '1'：

- 把 t 切成极长的同字符段，首尾两段都是 '1'（虚拟边界与真实 '1' 可能并在一起）。只有既不在首段也不在末段的 '1' 段才是"被 '0' 包围"，可被删除。
- 删除中间某个 '1' 段（长度 a）后，它左右两侧的 '0' 段（长度 b1、b2）会合并成一段长度 b1 + a + b2 的 '0'，且该段两侧都是 '1'（恰好是被删段两侧的 '1' 段），因此可以整段填成 '1'。

于是对某个可删的 '1' 段，两种选择：
- 填合并后的 0 段：净变化 = −a + (b1 + a + b2) = b1 + b2；
- 填其它任意一个原本就被 '1' 包围的 0 段（长度为 c）：净变化 = c − a。

取所有组合的最大值（若没有可删的 '1' 段，则无法操作，变化为 0）。

答案为"原串 '1' 的个数 + max(0, 最大净变化)"。

## 复杂度分析

- 时间复杂度：O(n + Σ(r−l+1))，每个查询对子串做一次线性扫描。官方用例 n ≤ 7；若 n 与查询数都取到 10^5，需要换成按段统计的线段树才能达到 O((n+q) log n)，本实现未做该优化。
- 空间复杂度：O(1)（不计输入）。

## 边界与处理

- 子串内没有"被 '0' 包围的 '1' 段"：无法操作，答案为原串 '1' 的个数（示例 3 的 [1,3]、示例 4 的 [1,3]）。
- 整个子串都是 '0'：无法操作（没有可删的 '1' 段）。
- 虚拟边界 '1' 不参与计数，但参与"是否被包围"的判断——这正是把 t 两端补 '1' 的原因。
- 填 0 段时不能超过子串范围：合并段与其它 0 段都在 t 内，天然受限。
- 净变化可能为负（c < a 且 b1+b2 < 0 不可能，因为 b1、b2 ≥ 1），故至少可选填合并段获得 b1+b2 ≥ 2 > 0；仍取 max(0, ·) 以覆盖"无可删段"的情形。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    queries = json.loads(lines[1])

    base = s.count("1")

    ans = []
    for l, r in queries:
        t = "1" + s[l:r + 1] + "1"
        n = len(t)

        runs = []
        i = 0
        while i < n:
            j = i
            while j < n and t[j] == t[i]:
                j += 1
            runs.append((t[i], i, j - 1))
            i = j

        zero_lens = [e - s0 + 1 for ch, s0, e in runs if ch == "0"]
        M = max(zero_lens) if zero_lens else 0

        best = 0
        for idx, (ch, s0, e) in enumerate(runs):
            if ch != "1":
                continue
            if idx == 0 or idx == len(runs) - 1:
                continue  # 与虚拟边界相连，不被 '0' 包围
            a = e - s0 + 1
            b1 = runs[idx - 1][2] - runs[idx - 1][1] + 1
            b2 = runs[idx + 1][2] - runs[idx + 1][1] + 1
            cand = max(b1 + b2, M - a)
            if cand > best:
                best = cand

        ans.append(base + best)

    print(json.dumps(ans, separators=(",", ":")))


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
        os.path.dirname(os.path.abspath(__file__)), "batch05.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
