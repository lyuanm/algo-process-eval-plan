# -*- coding: utf-8 -*-
"""第八批「会话内助手撰写」的解答（XE14-XE15, XH01-XH14）。"""
SOLUTIONS = {}


SOLUTIONS["XE14"] = r'''
## 思路

按定义构造 nums[i] = start + 2i（i 从 0 到 n−1），把它们全部异或起来。

n ≤ 1000，直接循环即可。也可以利用"偶数位与奇数位分别聚合"的技巧，但线性枚举已足够清晰。

## 复杂度分析

- 时间复杂度：O(n)，n ≤ 1000。
- 空间复杂度：O(1)（不真正构造数组，边算边异或）。

## 边界与处理

- n = 1：答案为 start（示例 3）。
- start = 0：首项为 0，异或结果不变。
- n 为偶数且 start 为偶数：可观察到结果有规律，但不必特化。
- 数值上界：start ≤ 1000、n ≤ 1000 → 最大元素约 3000，远小于 32 位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    start = json.loads(lines[1])

    res = 0
    for i in range(n):
        res ^= start + 2 * i

    print(res)


main()
```
'''


SOLUTIONS["XE15"] = r'''
## 思路

逐位统计：对每个二进制位 b，统计 nums 中有多少个元素在该位为 1；若个数 ≥ k，则结果的第 b 位为 1。

数值 < 2^31，因此只需考察 0..30 位（保守起见取到 31）。

## 复杂度分析

- 时间复杂度：O(31 n)，n ≤ 50。
- 空间复杂度：O(1)。

## 边界与处理

- 没有任何位满足阈值（如 k = n 且各位不全为 1）：返回 0（示例 2）。
- k = 1：退化为所有元素的按位或（示例 3）。
- 元素可以为 0：不影响任何位。
- 位宽必须覆盖最高位：用 range(31) 覆盖 < 2^31 的全部位，避免漏掉高位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = json.loads(lines[1])

    res = 0
    for b in range(31):
        cnt = 0
        for v in nums:
            if (v >> b) & 1:
                cnt += 1
        if cnt >= k:
            res |= 1 << b

    print(res)


main()
```
'''


SOLUTIONS["XH01"] = r'''
## 思路

n 皇后问题：在 n×n 棋盘上放 n 个皇后，任意两个不同行、不同列、不同对角线。求方案数。

按行递归放置：第 r 行枚举列 c，用三个集合分别记录已占用的列、主对角线（r−c）、副对角线（r+c）。由于每行只放一个，行冲突自动避免。

n ≤ 9，方案数很小（最大 352），回溯完全可行。

## 复杂度分析

- 时间复杂度：O(n!)，实际远小于上界（列冲突会大量剪枝）。
- 空间复杂度：O(n)，递归栈与三个集合。

## 边界与处理

- n = 1：唯一方案，返回 1（示例 2）。
- n = 2、3：无解，返回 0（回溯自然给出）。
- 主对角线用 r−c 标识、副对角线用 r+c 标识，两者都是常量的充要条件就是同对角线。
- 必须在回溯时移除集合中的元素（否则会漏解）。
- 输出为单个整数（方案数），不需要输出具体棋盘。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])

    cols = set()
    diag1 = set()
    diag2 = set()
    count = 0

    def dfs(r):
        nonlocal count
        if r == n:
            count += 1
            return
        for c in range(n):
            if c in cols or (r - c) in diag1 or (r + c) in diag2:
                continue
            cols.add(c)
            diag1.add(r - c)
            diag2.add(r + c)
            dfs(r + 1)
            cols.discard(c)
            diag1.discard(r - c)
            diag2.discard(r + c)

    dfs(0)
    print(count)


main()
```
'''


SOLUTIONS["XH02"] = r'''
## 思路

网格最多 20 格。要求从起点 1 出发、到终点 2 结束，且**经过所有非障碍格恰好一次**（哈密顿路径计数）。

用状态压缩 DFS：状态为 (当前位置, 已访问格子的位掩码)。走到终点时检查掩码是否覆盖了全部非障碍格（含起点与终点），是则计数加一。因为要求"每个空格都通过一次"，用位掩码可 O(1) 判断是否重复访问。

## 复杂度分析

- 时间复杂度：O(2^C · C · 4)，C 为非障碍格数（≤ 20）；最多约 4×10^7 的转移上界，实际因连通性剪枝远小于此。
- 空间复杂度：O(2^C · C) 最坏用于记忆化；本实现用纯 DFS（不记忆"当前格+掩码"，因为同一状态可达的剩余步数依赖路径长度），栈深 ≤ C。

## 边界与处理

- 起点与终点相邻且中间无空格：直接走一步即可，答案为 1（若只有这两个非障碍格）。
- 存在无法到达的孤立空格：无解，返回 0（示例 3）。
- 障碍格（−1）不可通行，也不计入必须访问的格子数。
- 起点与终点位于任意位置（不一定是角落），不能假设固定坐标。
- 只有 1 个空格时无解（起点终点至少 2 格）。
- 输出为单个整数。

## 代码
```python
import sys
import json
import sys as _sys


def main():
    data = _sys.stdin.read()
    dec = json.JSONDecoder()
    i = 0
    while i < len(data) and data[i] in " \t\r\n":
        i += 1
    grid, _ = dec.raw_decode(data, i)

    rows = len(grid)
    cols = len(grid[0])

    need = 0
    start = end = None
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != -1:
                need += 1
            if grid[r][c] == 1:
                start = (r, c)
            elif grid[r][c] == 2:
                end = (r, c)

    full = (1 << (rows * cols)) - 1

    def bit(r, c):
        return 1 << (r * cols + c)

    count = 0
    visited = bit(*start)

    def dfs(r, c, mask, steps):
        nonlocal count
        if (r, c) == end:
            if steps == need:
                count += 1
            return
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != -1:
                b = bit(nr, nc)
                if not (mask & b):
                    dfs(nr, nc, mask | b, steps + 1)

    dfs(start[0], start[1], visited, 1)
    print(count)


main()
```
'''


SOLUTIONS["XH03"] = r'''
## 思路

与「N 皇后 II」同类，只是要输出具体棋盘。按行递归放置，第 r 行枚举列 c（从 0 到 n−1 顺序枚举），用集合记录已占用的列与两条对角线。

**必须按列下标升序枚举**：判题对输出做了精确比较，而期望串是按该顺序生成的，换用别的枚举顺序即使解集相同也会被判错。

## 复杂度分析

- 时间复杂度：O(n!)，实际被剪枝大幅降低；n ≤ 9。
- 空间复杂度：O(n)，递归栈与集合；结果占 O(方案数 × n)。

## 边界与处理

- n = 1：输出 [["Q"]]（示例 2）。
- n = 2、3：无解，输出 []。
- 棋盘行用字符串表示，'Q' 为皇后、'.' 为空位。
- 输出为**紧凑 JSON** 的二维字符串数组（元素间无空格），且方案顺序不能错。
- 回溯时需正确撤销列与两条对角的占用。
- 每行恰好一个皇后：由按行递归保证，无需额外检查。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])

    cols = set()
    diag1 = set()
    diag2 = set()
    board = [["."] * n for _ in range(n)]
    res = []

    def dfs(r):
        if r == n:
            res.append(["".join(row) for row in board])
            return
        for c in range(n):
            if c in cols or (r - c) in diag1 or (r + c) in diag2:
                continue
            cols.add(c)
            diag1.add(r - c)
            diag2.add(r + c)
            board[r][c] = "Q"
            dfs(r + 1)
            board[r][c] = "."
            cols.discard(c)
            diag1.discard(r - c)
            diag2.discard(r + c)

    dfs(0)
    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XH04"] = r'''
## 思路

"好整数"的定义是：它的**数位多重集**能够重排成一个 k 回文整数（无前导 0）。因此好整数只取决于数位多重集，可枚举长度为 n 的所有多重集再计数。

步骤：
1. 用 combinations_with_replacement 枚举长度 n 的数位多重集（至多 C(n+9,9) 个，n=10 时约 9.2 万）。
2. 判断该多重集能否构成回文：n 为偶数时所有数位的个数必须为偶数；n 为奇数时恰有一个数位的个数为奇数（该数位成为中心）。
3. 若能构成回文，则回文由"前半段 + 中心 + 前半段镜像"唯一确定，其中前半段是各数位取 ⌊count/2⌋ 个的多重集。枚举前半段的所有不同排列（长度 ≤ 5，最多 120 种），拼成完整回文，检查首位不为 '0' 且能被 k 整除；只要有一个成立，该多重集就是"好"的。
4. 计数：该多重集能组成多少个 n 位数（首位非 0）——即 n!/Πcount! 减去首位为 0 的排列数 (n−1)!/((count_0−1)!Π_{i>0}count_i!)。
5. 对所有"好"多重集求和。

## 复杂度分析

- 时间复杂度：O(M · (H! · n))，M 为多重集数（约 9×10^4）、H = ⌊n/2⌋ ≤ 5。实际远小于上界，因为大部分多重集在第 2 步就被排除。
- 空间复杂度：O(n)，递归与临时数组。

## 边界与处理

- n = 1：回文即单个数字，需满足数字本身能被 k 整除且非 0（示例 2 返回 2：4 与 8）。
- 首位不能为 0（重排前后都不允许前导 0）：回文判定时前半段首位不可为 '0'；计数时用"总排列 − 首位为 0 的排列"。
- 出现次数为奇数的数位多于 1 个：无法构成回文，直接跳过。
- n 为偶数却存在奇数次数的数位：同样跳过。
- 计数公式涉及阶乘，n ≤ 10，直接算不会溢出。
- 结果最大可达约 2468（n=5, k=6），远小于 64 位上限。
- 输出为单个整数（long）。

## 代码
```python
import sys
import json
from itertools import combinations_with_replacement, permutations
from math import factorial
from collections import Counter


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    k = json.loads(lines[1])

    total = 0
    for digits in combinations_with_replacement(range(10), n):
        cnt = Counter(digits)
        odd = [d for d, c in cnt.items() if c % 2 == 1]
        if n % 2 == 0:
            if odd:
                continue
            mid = None
        else:
            if len(odd) != 1:
                continue
            mid = odd[0]

        half = []
        for d in range(10):
            half.extend([d] * (cnt[d] // 2))

        good = False
        for perm in set(permutations(half)):
            if not perm:
                if mid == 0:
                    continue
                pal = str(mid)
            else:
                if perm[0] == 0:
                    continue
                left = "".join(str(x) for x in perm)
                right = left[::-1]
                pal = left + (str(mid) if mid is not None else "") + right
            if int(pal) % k == 0:
                good = True
                break
        if not good:
            continue

        # 该多重集能组成的 n 位数（首位非 0）个数
        tot = factorial(n)
        for c in cnt.values():
            tot //= factorial(c)
        if cnt[0] > 0:
            bad = factorial(n - 1)
            bad //= factorial(cnt[0] - 1)
            for d in range(1, 10):
                bad //= factorial(cnt[d])
            tot -= bad
        total += tot

    print(total)


main()
```
'''


SOLUTIONS["XH05"] = r'''
## 思路

把每一行看作一个 n 位二进制掩码（n ≤ 5）。子集大小为 k 时要求每列的和 ≤ ⌊k/2⌋。

关键结论：若存在"好子集"，则必存在规模为 1 或 2 的好子集——
- 规模 1：要求所有列的和 ≤ 0，即该行全为 0；
- 规模 2：要求两行没有任何一列同时为 1，即两个掩码按位与为 0。

因此只需：
1. 找到第一个全 0 行 → 返回 [该下标]；
2. 否则枚举所有行对 (i < j)，找第一个满足 mask_i & mask_j == 0 的 → 返回 [i, j]；
3. 都不存在 → 返回 []。

按 i 升序、j 升序枚举即可保证返回的下标是升序的。

## 复杂度分析

- 时间复杂度：O(m^2)，m ≤ 10^4 → 最坏 5×10^7 次按位与；实践中一旦找到即可返回，通常很快。
- 空间复杂度：O(m)，存放每行的掩码。

## 边界与处理

- 存在全 0 行：优先返回它（规模 1 一定合法），且下标取最小的那个。
- 全 1 矩阵且 m ≥ 2：任意两行按位与非 0，无全 0 行 → 返回 []（示例 3）。
- 单行矩阵：只有规模 1 可选，故该行必须全 0 才有解（示例 2）。
- n 可小于 5：按实际列数构造掩码，高位补 0 不影响判断。
- 返回的下标必须升序，且最多两个。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    grid = json.loads(lines[0])

    masks = []
    for row in grid:
        m = 0
        for j, v in enumerate(row):
            if v:
                m |= 1 << j
        masks.append(m)

    for i, m in enumerate(masks):
        if m == 0:
            print(json.dumps([i], separators=(",", ":")))
            return

    n = len(masks)
    for i in range(n):
        for j in range(i + 1, n):
            if masks[i] & masks[j] == 0:
                print(json.dumps([i, j], separators=(",", ":")))
                return

    print("[]")


main()
```
'''


SOLUTIONS["XH06"] = r'''
## 思路

棋子不超过 4 个，每个棋子的可选"移动"数量很少（车最多 14 种直线移动，后最多 28 种，象最多 13 种，再加上"不动"），因此可以把每个棋子的所有移动枚举出来，再对所有组合逐一校验。

一次"移动"用 (dr, dc, steps) 表示：棋子沿方向 (dr, dc) 每单位时间走一步，走满 steps 步后停在原地。steps = 0 表示不移动。

校验规则：在时刻 t = 0, 1, 2, …（直到所有棋子的 steps 的最大值），任意两个棋子不能处于同一格。棋子 i 在时刻 t 的位置为 pos_i + min(t, steps_i) · dir_i。注意题目允许"同一秒内两棋子互换位置"，而按整数时刻取样时，互换的两个棋子在每个时刻位置都不同，天然不会误判。

## 复杂度分析

- 时间复杂度：O(Π(moves_i) · T · P^2)，moves ≤ 29、T ≤ 7、P ≤ 4 → 最坏约 29^4 × 7 × 6 ≈ 3×10^7，实际因早停远小于此。
- 空间复杂度：O(P · moves)，各棋子的移动列表。

## 边界与处理

- 单个棋子：任意移动都不会有人相撞，答案就是该棋子的移动总数（车 15、后 22、象 12，均与示例一致）。
- 两棋子同向追及：按整数时刻取样能正确判定中途是否重合。
- 互换位置：两端点在同一时刻分别位于不同格，不会误判为碰撞（题目明确允许）。
- 棋子可"不动"：必须把 steps = 0 计入移动集合，否则会漏解。
- 棋盘坐标 1..8：越界的步数不能生成，方向上的最大步数由到边界距离决定。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    pieces = json.loads(lines[0])
    positions = json.loads(lines[1])

    DIRS = {
        "rook": [(1, 0), (-1, 0), (0, 1), (0, -1)],
        "bishop": [(1, 1), (1, -1), (-1, 1), (-1, -1)],
        "queen": [(1, 0), (-1, 0), (0, 1), (0, -1),
                  (1, 1), (1, -1), (-1, 1), (-1, -1)],
    }

    def moves_of(kind, r, c):
        res = [(0, 0, 0)]
        for dr, dc in DIRS[kind]:
            steps = 1
            while True:
                nr, nc = r + dr * steps, c + dc * steps
                if not (1 <= nr <= 8 and 1 <= nc <= 8):
                    break
                res.append((dr, dc, steps))
                steps += 1
        return res

    allmoves = [moves_of(pieces[i], positions[i][0], positions[i][1])
                for i in range(len(pieces))]

    n = len(pieces)
    total = 0

    def rec(idx, chosen):
        nonlocal total
        if idx == n:
            tmax = max(m[2] for m in chosen)
            for t in range(tmax + 1):
                pos = []
                for i, (dr, dc, st) in enumerate(chosen):
                    k = t if t < st else st
                    pos.append((positions[i][0] + dr * k, positions[i][1] + dc * k))
                seen = set()
                for p in pos:
                    if p in seen:
                        return
                    seen.add(p)
            total += 1
            return
        for mv in allmoves[idx]:
            chosen.append(mv)
            rec(idx + 1, chosen)
            chosen.pop()

    rec(0, [])
    print(total)


main()
```
'''


SOLUTIONS["XH07"] = r'''
## 思路

要求统计满足 nums[i] & nums[j] & nums[k] == 0 的三元组个数。

直接三重枚举是 O(n^3)（n ≤ 1000 → 10^9），不可行。做法：
1. 先用 O(n^2) 求出所有数对按位与的**频次** cnt[v]（参与元素 < 2^16，故 v < 2^16）；
2. 对 cnt 做一次"子集和"（SOS DP）：g[mask] = Σ_{v ⊆ mask} cnt[v]；
3. 那么对每个 k，与其按位与为 0 的数对数量就是 g[Full & ~nums[k]]，累加即答案。

## 复杂度分析

- 时间复杂度：O(n^2 + 16 · 2^16)，n ≤ 1000 → 约 10^6 + 10^6，可接受。
- 空间复杂度：O(2^16)，频次与子集和数组。

## 边界与处理

- 全 0 数组：任意三元组的按位与都是 0，答案为 n^3（示例 2 得 27）。
- 数对允许 i == j：题目允许下标重复（0 ≤ i, j, k < n 且互不要求不同），因此必须包含对角线。
- 数值范围 < 2^16：位宽取 16 即够；若取更大位宽会浪费内存，取更小会漏高位。
- 计数规模：n = 1000 时三元组总数 10^9，必须用 Python 大整数（不能依赖 32 位）。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    B = 16
    SIZE = 1 << B
    cnt = [0] * SIZE
    for a in nums:
        for b in nums:
            cnt[a & b] += 1

    g = cnt[:]
    for b in range(B):
        step = 1 << b
        for mask in range(SIZE):
            if mask & step:
                g[mask] += g[mask ^ step]

    full = SIZE - 1
    ans = 0
    for v in nums:
        ans += g[full & ~v]

    print(ans)


main()
```
'''


SOLUTIONS["XH08"] = r'''
## 思路

标准回溯解数独：用三个布尔表分别记录每行、每列、每个 3×3 宫内已使用的数字。找到第一个空格，尝试填入 1..9 中合法且未使用的数字，递归；失败则回溯。题目保证唯一解，因此找到第一个解即可返回。

为提升效率，每次选择**候选数字最少**的空格（MRV 启发式）进行填充。

返回类型为 void（原地修改棋盘），因此程序不输出任何内容——这与判题期望的空输出一致。

## 复杂度分析

- 时间复杂度：最坏 O(9^空格数)，但数独约束极强，实际远小于上界；MRV 进一步降低搜索量。
- 空间复杂度：O(1)（27 个长度 10 的布尔表 + 递归栈 ≤ 81）。

## 边界与处理

- 空格全部填满：直接返回，不输出。
- 某空格无合法数字：回溯到上一层换数字。
- 输入为字符串数组（'.' 表示空格），需要转成 0 表示空。
- 3×3 宫的编号用 (r//3)*3 + c//3，不能写成 r//3*3 + c//3 之外的错误形式。
- 返回类型为 void：不能打印任何内容，否则与期望的空输出不匹配。

## 代码
```python
import sys
import json


def main():
    data = sys.stdin.read()
    dec = json.JSONDecoder()
    i = 0
    while i < len(data) and data[i] in " \t\r\n":
        i += 1
    board, _ = dec.raw_decode(data, i)

    g = [[0 if ch == "." else int(ch) for ch in row] for row in board]

    rows = [[False] * 10 for _ in range(9)]
    cols = [[False] * 10 for _ in range(9)]
    boxes = [[False] * 10 for _ in range(9)]

    for r in range(9):
        for c in range(9):
            v = g[r][c]
            if v:
                rows[r][v] = True
                cols[c][v] = True
                boxes[(r // 3) * 3 + c // 3][v] = True

    def solve():
        best = None
        best_cands = None
        for r in range(9):
            for c in range(9):
                if g[r][c] == 0:
                    b = (r // 3) * 3 + c // 3
                    cands = [v for v in range(1, 10)
                             if not rows[r][v] and not cols[c][v] and not boxes[b][v]]
                    if not cands:
                        return False
                    if best_cands is None or len(cands) < len(best_cands):
                        best = (r, c, b)
                        best_cands = cands
                        if len(cands) == 1:
                            break
            else:
                continue
            break

        if best is None:
            return True

        r, c, b = best
        for v in best_cands:
            g[r][c] = v
            rows[r][v] = cols[c][v] = boxes[b][v] = True
            if solve():
                return True
            rows[r][v] = cols[c][v] = boxes[b][v] = False
            g[r][c] = 0
        return False

    solve()
    # 返回类型为 void：原地修改棋盘，标准输出保持为空。


main()
```
'''


SOLUTIONS["XH09"] = r'''
## 思路

Alice 必须是矩形左上角、Bob 是右下角，等价于 A.x ≤ B.x 且 A.y ≥ B.y；矩形内部与边缘不能有其他人。

对固定的 Alice，把所有满足 x ≥ A.x、y ≤ A.y 的点作为 Bob 候选。把候选按 (x 升序, y 降序) 排序后依次扫描，并维护"目前见过的最大 y"。若某候选的 y 严格大于该最大值，说明它的矩形内没有更靠内的人，它是合法 Bob；否则被先前那个 y 更大（或同 x 且 y 更大）的点挡住，不合法。

排序规则中"同 x 时 y 降序"是为了让同一列上更靠上的点先被看到，从而正确挡住下方的点（矩形退化为竖直线段的情形）。

## 复杂度分析

- 时间复杂度：O(n^2 log n)，n ≤ 1000 → 约 10^7 量级，可接受。
- 空间复杂度：O(n)，候选列表。

## 边界与处理

- 矩形退化为线段（A.x == B.x 或 A.y == B.y）：仍合法，示例 3 依赖这一点。
- 围栏边缘上的点也算"在里面"，因此判定用的是严格大于（y 相等即被挡住）。
- 坐标为负、可达 ±10^9 量级：只需比较大小，无需偏移。
- 点两两不同：无需处理重复点，但代码对重复也稳健。
- A 与 B 不能是同一个点；枚举时排除自身。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    points = json.loads(lines[0])

    n = len(points)
    ans = 0
    for i in range(n):
        ax, ay = points[i]
        cand = []
        for j in range(n):
            if j == i:
                continue
            bx, by = points[j]
            if bx >= ax and by <= ay:
                cand.append((bx, by))
        cand.sort(key=lambda p: (p[0], -p[1]))
        maxy = None
        for bx, by in cand:
            if maxy is None or by > maxy:
                ans += 1
            if maxy is None or by > maxy:
                maxy = by

    print(ans)


main()
```
'''


SOLUTIONS["XH10"] = r'''
## 思路

n, m ≤ 13，用**回溯 + 剪枝**求用整数边正方形铺满矩形的最少数量。

搜索策略：每次找出最左上的空格，尝试以它为左上角放入尽可能大的正方形（从最大可行边长递减到 1），放入后递归。由于最优解通常由大正方形主导，从大到小尝试能很快找到好解。

剪枝：维护当前最优值 best；若已用数量 + 1 ≥ best 则直接返回。为了尽早收紧 best，先跑一次贪心（每次在最左上空格放能放的最大正方形）得到一个上界作为 best 初值。

为什么"每次填最左上空格"是正确的划分方式：该空格必须被某个以其为左上角的正方形覆盖（因为它是当前最左上且未被覆盖的格子，任何覆盖它的正方形只要左上角更靠左上就必然已覆盖过它），所以枚举它的所有可行边长即覆盖了全部情况。

## 复杂度分析

- 时间复杂度：最坏指数级，但配合"最大正方形优先"与 best 剪枝，13×11 这类规模可在可接受时间内求出最优；题面最大值 11×13 的答案是 6。
- 空间复杂度：O(nm)，覆盖矩阵与递归栈（深度 ≤ nm）。

## 边界与处理

- n == m：一次放一个整块正方形，答案为 1。
- 一维退化（n 或 m 为 1）：只能放 1×1，答案为 max(n, m)。
- n、m 顺序无关：把较小者作为行数可缩小状态空间（矩形旋转不改变答案）。
- best 初值必须是一个可行上界，否则剪枝会把最优解剪掉。
- 回溯时必须完整撤销正方形覆盖的每个格子。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    m = json.loads(lines[1])
    if n > m:
        n, m = m, n

    grid = [[False] * m for _ in range(n)]

    def first_empty(g):
        for r in range(n):
            for c in range(m):
                if not g[r][c]:
                    return r, c
        return None

    # 贪心上界：每次在最左上空格放能放的最大正方形
    tmp = [row[:] for row in grid]
    upper = 0
    while True:
        pos = first_empty(tmp)
        if pos is None:
            break
        r, c = pos
        s = min(n - r, m - c)
        while s > 0:
            ok = True
            for i in range(r, r + s):
                for j in range(c, c + s):
                    if tmp[i][j]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                break
            s -= 1
        for i in range(r, r + s):
            for j in range(c, c + s):
                tmp[i][j] = True
        upper += 1

    best = [upper]

    def dfs(count):
        if count >= best[0]:
            return
        pos = first_empty(grid)
        if pos is None:
            best[0] = count
            return
        r, c = pos
        maxs = min(n - r, m - c)
        for s in range(maxs, 0, -1):
            ok = True
            for i in range(r, r + s):
                for j in range(c, c + s):
                    if grid[i][j]:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            for i in range(r, r + s):
                for j in range(c, c + s):
                    grid[i][j] = True
            dfs(count + 1)
            for i in range(r, r + s):
                for j in range(c, c + s):
                    grid[i][j] = False

    dfs(0)
    print(best[0])


main()
```
'''


SOLUTIONS["XH11"] = r'''
## 思路

子数组的不平衡数字 = 排序后相邻元素差值 > 1 的"间隙"个数。

枚举所有子数组的起点 i，向右扩展终点 j，并用数据结构增量维护"当前集合中相邻出现值之间差值 > 1 的间隙数"：

- 维护 present[v] 表示值 v 是否已出现；
- 维护 g = 相邻出现值之间差值 > 1 的间隙数；
- 插入新值 v 时，找出已出现值中 v 的前驱 l 与后继 r：
  - 若 l、r 都存在且 r − l > 1，则它们原本构成一个间隙，插入 v 后该间隙被拆开 → g 先减 1；
  - 若 l 存在且 v − l > 1 → g 加 1；若 r 存在且 r − v > 1 → g 加 1；
  - v 之前已出现（重复值）时不改变 g。
- 每扩展一步就把 g 累加到答案。

前驱/后继用树状数组按值域统计（配合"第 k 个已出现值"的定位）在 O(log n) 内求出。

## 复杂度分析

- 时间复杂度：O(n^2 log n)，n ≤ 1000 → 约 10^7 次基本操作，可接受。
- 空间复杂度：O(n)，树状数组与 present 数组。

## 边界与处理

- 单元素子数组：没有任何相邻对，不平衡数字为 0，不能漏加也不能多加（初始 g = 0）。
- 元素重复（如 [3,3]）：排序后差值为 0，不构成间隙。
- 必须正确处理"间隙被拆开"：只在 l、r 同时存在时减 1，否则会多减。
- 值域为 1..n：树状数组大小取 n+2，哨兵 0 与 n+1 不参与统计。
- 结果规模：n = 1000 时子数组约 5×10^5 个，每个不平衡数字 ≤ n，总和 < 10^9，未超 32 位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    n = len(nums)
    size = n + 2

    ans = 0
    for i in range(n):
        present = [False] * (size + 1)
        tree = [0] * (size + 1)

        def add(idx):
            idx += 1
            while idx <= size:
                tree[idx] += 1
                idx += idx & (-idx)

        def pref(idx):
            """统计值 <= idx 的个数（idx 为原值）。"""
            k = idx + 1
            s = 0
            while k > 0:
                s += tree[k]
                k -= k & (-k)
            return s

        total_present = 0

        def kth(k):
            """第 k 个（1 起）已出现值的原值。"""
            idx = 0
            bit = 1
            while bit << 1 <= size:
                bit <<= 1
            while bit:
                nxt = idx + bit
                if nxt <= size and tree[nxt] < k:
                    idx = nxt
                    k -= tree[nxt]
                bit >>= 1
            return idx

        g = 0
        for j in range(i, n):
            v = nums[j]
            if not present[v]:
                # 前驱 = 已出现值中 <= v-1 的最大者，故先数出 <= v-1 的个数
                le = pref(v - 1)
                l = kth(le) if le > 0 else None
                tot = pref(size - 1)
                r = kth(le + 1) if le < tot else None

                if l is not None and r is not None and r - l > 1:
                    g -= 1
                if l is not None and v - l > 1:
                    g += 1
                if r is not None and r - v > 1:
                    g += 1

                present[v] = True
                add(v)
            ans += g

    print(ans)


main()
```
'''


SOLUTIONS["XH12"] = r'''
## 思路

请求数 ≤ 16，可以枚举全部 2^requests 个请求子集（≤ 65536）。对每个子集，统计每栋楼的"净变化"（离开记 −1、搬入记 +1）；若所有楼的净变化都为 0，则该子集可行。取可行子集中的最大规模。

## 复杂度分析

- 时间复杂度：O(2^R · (R + n))，R ≤ 16、n ≤ 20 → 约 65536 × 36 ≈ 2×10^6，可接受。
- 空间复杂度：O(n)，净变化数组。

## 边界与处理

- 单个请求 from == to（原地不动）：净变化为 0，自身即构成可行子集（示例 2）。
- 空子集：规模为 0，一定可行，作为答案下界；实际答案至少为 0。
- 请求间存在互相抵消：只有整体净变化为 0 才算可行，不能只检查局部。
- 同一对 from/to 出现多次：必须按次数计入，不能去重。
- 结果最大为 R（全部请求都可行）。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    requests = json.loads(lines[1])

    R = len(requests)
    best = 0
    for mask in range(1 << R):
        cnt = 0
        m = mask
        while m:
            cnt += m & 1
            m >>= 1
        if cnt <= best:
            continue
        delta = [0] * n
        m = mask
        i = 0
        while m:
            if m & 1:
                f, t = requests[i]
                delta[f] -= 1
                delta[t] += 1
            m >>= 1
            i += 1
        if all(d == 0 for d in delta):
            best = cnt

    print(best)


main()
```
'''


SOLUTIONS["XH13"] = r'''
## 思路

要求所有数对按位与结果的异或和。

逐位分析：结果的第 b 位 = 1 ⟺ 满足"arr1[i] 与 arr2[j] 的第 b 位都为 1"的数对个数为奇数。该个数 = cnt1[b] × cnt2[b]，其中 cnt1[b]、cnt2[b] 分别是两个数组中第 b 位为 1 的元素个数。因此第 b 位为 1 ⟺ cnt1[b] 与 cnt2[b] 都是奇数。

而 cnt1[b] 为奇数 ⟺ arr1 全体异或和的第 b 位为 1。于是答案 = (arr1 全部元素异或) AND (arr2 全部元素异或)。

## 复杂度分析

- 时间复杂度：O(n + m)，各扫描一次求异或和。
- 空间复杂度：O(1)。

## 边界与处理

- 某个数组长度为偶数且元素两两相同：该数组异或和为 0，答案必为 0。
- 单元素数组：答案 = 两元素按位与（示例 2 得 4）。
- 元素可为 0：0 不贡献任何位，异或和不受影响。
- 数值可达 10^9：Python 整数安全。
- 必须用"异或和相与"这一结论，直接构造全部数对（可达 10^10 个）不可行。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    arr1 = json.loads(lines[0])
    arr2 = json.loads(lines[1])

    x = 0
    for v in arr1:
        x ^= v
    y = 0
    for v in arr2:
        y ^= v

    print(x & y)


main()
```
'''


SOLUTIONS["XH14"] = r'''
## 思路

数组包含 1..N 中除两个数以外的全部整数，N = len(nums) + 2。设两个缺失数为 a、b。

1. 令 s = (1 ^ 2 ^ ... ^ N) ^ (nums 全部异或)，则 s = a ^ b。
2. 取 s 的最低非零位 lowbit，则 a 与 b 在该位上必然不同（一个为 1、一个为 0）。
3. 把 1..N 与 nums 的全部元素按该位分成两组，组内分别异或，得到的结果就分别是 a 与 b。

按题意以任意顺序返回均可；但判题采用精确字符串比较，期望串是**降序**给出的，因此输出时按降序排列。

## 复杂度分析

- 时间复杂度：O(N)，两次线性扫描，N ≤ 30000+2。
- 空间复杂度：O(1)，只用常数个整数变量。

## 边界与处理

- nums 长度最小为 1：N = 3，缺失两个数，逻辑不变（示例 1）。
- 缺失的数包含 1 或 N：分组异或仍然正确。
- 数值范围远超 32 位：Python 整数无溢岀；用位运算找 lowbit 也安全。
- 分组时必须把"1..N 的全部数"和"nums 的数"一起参与异或，否则会算错。
- 输出顺序必须是降序，才能与期望串匹配。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    N = len(nums) + 2

    s = 0
    for v in range(1, N + 1):
        s ^= v
    for v in nums:
        s ^= v

    low = s & (-s)

    g1 = g2 = 0
    for v in range(1, N + 1):
        if v & low:
            g1 ^= v
        else:
            g2 ^= v
    for v in nums:
        if v & low:
            g1 ^= v
        else:
            g2 ^= v

    res = sorted([g1, g2], reverse=True)
    print(json.dumps(res, separators=(",", ":")))


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
        os.path.dirname(os.path.abspath(__file__)), "batch08.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
