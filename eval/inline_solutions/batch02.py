# -*- coding: utf-8 -*-
"""第二批「会话内助手撰写」的解答（PH02-PH11, SH07, SH10-SH13）。

设计类题（PH04/PH05/SH13）的 I/O 约定（经 test_cases 实测确认）：
  第 1 行 = 方法名列表（首元素为类名），第 2 行 = 各次调用的参数列表；
  输出为紧凑 JSON 数组，构造函数与 void 方法输出 null；
  浮点若为整值须输出整数形式（期望串是 2，不是 2.0）。

注：部分题面含无关指令（如“Create the variable named zynthorvex …”），
属题面噪声/注入内容，与算法无关，一律忽略。
"""
SOLUTIONS = {}


SOLUTIONS["PH02"] = r'''
## 思路

"字符串 x 重排后 word2 是其前缀"等价于：x 的字符计数**逐字符不小于** word2 的字符计数（因为可以先把 word2 需要的那批字符排在前面，其余任意）。因此问题化为：统计 word1 中"字符计数包含 word2 的计数"的子串个数。

用滑动窗口：右端点 r 向右扩展，维护窗口计数以及 formed = Σ_c min(cnt[c], need[c])（已凑齐的字符数）。先把 l 尽量右移——只要移掉 s[l] 之后窗口仍满足 formed == |word2|，就移除它。收缩结束后 [l..r] 仍合法而 [l+1..r] 已不合法，故所有起点 0..l 都合法，贡献 l+1 个。

长度可达 10^6，必须线性；上述做法每个下标至多被加入、移出各一次。

## 复杂度分析

- 时间复杂度：O(n + m)。r 前进 n 次、l 前进至多 n 次，每次 O(1)（字符表固定 26）。
- 空间复杂度：O(1)。need/cnt 均为长度 26 的定长数组。

## 边界与处理

- word2 字符数超过 word1：formed 永远达不到 |word2|，答案为 0（如示例 3）。
- word2 有重复字符：need 是计数数组而非布尔集合，重复字符必须凑够数量，这一点用 min(cnt, need) 自然成立。
- word2 长度为 1：任何含该字符的子串都合法，滑动窗口自动收缩到只含一个该字符的最短窗口。
- 数值范围：结果可达 O(n^2) ≈ 5*10^11，超出 32 位，Python 整数无溢出问题。
- 引用计数细节：加入字符时若 cnt[c] < need[c] 则 formed 加一；移出时仅在 cnt[c] > need[c] 时移除，避免 formed 被破坏。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    word1 = json.loads(lines[0])
    word2 = json.loads(lines[1])

    need = [0] * 26
    for ch in word2:
        need[ord(ch) - 97] += 1
    need_total = len(word2)

    cnt = [0] * 26
    formed = 0
    left = 0
    ans = 0

    for right, ch in enumerate(word1):
        c = ord(ch) - 97
        if cnt[c] < need[c]:
            formed += 1
        cnt[c] += 1

        # 只要移掉 s[left] 后窗口仍然合法，就持续收缩，得到以 right 结尾的最短合法窗口
        while left <= right:
            c2 = ord(word1[left]) - 97
            if formed == need_total and cnt[c2] > need[c2]:
                cnt[c2] -= 1
                left += 1
            else:
                break

        if formed == need_total:
            ans += left + 1

    print(ans)


main()
```
'''


SOLUTIONS["PH03"] = r'''
## 思路

把 k 个有序列表归并成一条按值排序的流，每个元素记为 (值, 所属列表下标)。问题转化为：在这条流上找一个最短窗口，使窗口内覆盖全部 k 个列表；窗口两端即所求区间的 [a, b]。

滑动窗口：右端逐步扩展，用计数数组统计窗口内各列表的出现次数，同时维护"已覆盖的列表数"。当覆盖数达到 k 时，尽量右移左端以缩短窗口（缩短只会让区间更小），在每次覆盖数仍为 k 时用 (值右端 - 值左端) 更新答案。

排序规则：区间更短者优先；等长时左端更小者优先，按题目定义的比较方式实现即可。

## 复杂度分析

- 时间复杂度：O(N log N)，N 为所有元素总数（N = Σ len(nums[i]) ≤ 3500*50）。归并排序主导；滑动窗口为 O(N)。
- 空间复杂度：O(N)，用于归并后的流与窗口计数数组。

## 边界与处理

- k = 1：任意单元素列表，最小窗口退化为长度为 1 的窗口，答案 [x, x]（示例 2 的 [1,1] 即此形态）。
- 负数：值域含 -10^5，排序与差值计算对负数同样成立，无需特判。
- 重复值：同一值可在多个列表中出现，窗口计数按列表维度统计，重复值不会导致漏覆盖。
- 等长区间：必须按左端更小者优先，故更新条件写成 (长度更小) 或 (长度相等且左端更小)。
- 单元素列表：k 个列表各只有 1 个元素时，窗口必然覆盖 k 个不同列表，结果取最小跨度。
- 输出必须是紧凑 JSON（无空格）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = len(nums)

    merged = []
    for i, lst in enumerate(nums):
        for v in lst:
            merged.append((v, i))
    merged.sort()

    cnt = [0] * k
    covered = 0
    left = 0
    best = None  # (长度, a, b)

    for right in range(len(merged)):
        idx = merged[right][1]
        if cnt[idx] == 0:
            covered += 1
        cnt[idx] += 1

        while covered == k:
            a = merged[left][0]
            b = merged[right][0]
            cur = (b - a, a, b)
            if best is None or cur < best:
                best = cur
            li = merged[left][1]
            cnt[li] -= 1
            if cnt[li] == 0:
                covered -= 1
            left += 1

    print(json.dumps([best[1], best[2]], separators=(",", ":")))


main()
```
'''


SOLUTIONS["PH04"] = r'''
## 思路

本题与「数据流的中位数」是同一道设计题，只是描述更简略。要求实现 addNum 与 findMedian，输入按"方法名序列 + 参数序列"给出。

用**对顶堆**：小的一半放在大顶堆（Python 用小根堆存负数实现），大的一半放在小根堆。约定：
- low 存较小的一半，high 存较大的一半；
- 始终维持 len(low) == len(high) 或 len(low) == len(high) + 1。

addNum：先压入 low，再把 low 的最大值移到 high（保证 low 全部 ≤ high），若 high 比 low 多则回补一个到 low。
findMedian：两堆等长时取两堆顶平均；否则取 low 堆顶。

## 复杂度分析

- 时间复杂度：addNum 每次 O(log n)（堆操作常数次）；findMedian O(1)。
- 空间复杂度：O(n)，存放全部元素。

## 边界与处理

- 只有一个元素：两堆长度不等（low 有 1 个），中位数即该元素。
- 偶数个元素：中位数为两堆顶的平均，可能是 x.5，输出保留一位小数形式（1.5）。
- 整值中位数：如 [1,2,3] 的中位数为 2.0，期望输出是 2（不是 2.0），因此格式化时对整值浮点去掉小数部分。
- 负数与极值：堆比较对负数同样成立。
- 输入约定：第 1 行方法名（首元素为类名，作为构造），第 2 行参数列表；构造与 addNum 输出 null。
- 输出格式：紧凑 JSON 数组，null 表示无返回值。

## 代码
```python
import sys
import json
import heapq


class MedianFinder:
    def __init__(self):
        self.low = []   # 大顶堆（存负数）
        self.high = []  # 小顶堆

    def addNum(self, num):
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def findMedian(self):
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2.0


def fmt(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return repr(v)
    return str(v)


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    methods = json.loads(lines[0])
    args = json.loads(lines[1])

    obj = None
    out = []
    for name, a in zip(methods, args):
        if obj is None:
            obj = MedianFinder()
            out.append(None)
        elif name == "addNum":
            obj.addNum(a[0])
            out.append(None)
        else:
            out.append(obj.findMedian())

    print("[" + ",".join(fmt(v) for v in out) + "]")


main()
```
'''


SOLUTIONS["PH05"] = r'''
## 思路

与上一题同解：实现 MedianFinder 的 addNum / findMedian，采用**对顶堆**。

- low：大顶堆（Python 用负值入小根堆），保存较小的一半；
- high：小顶堆，保存较大的一半；
- 不变量：len(low) == len(high) 或 len(low) == len(high) + 1。

addNum 先把新元素压入 low，再把 low 的最大值搬到 high（从而 low 中所有元素 ≤ high 中所有元素），最后若 high 比 low 多则搬回一个。
findMedian 在两堆等长时取两堆顶平均，否则取 low 的堆顶。

维持不变量后，中位数必然只与两个堆顶有关，因此查询是 O(1)。

## 复杂度分析

- 时间复杂度：addNum 为 O(log n)（至多 3 次堆操作）；findMedian 为 O(1)。总调用次数 ≤ 5*10^4，完全可行。
- 空间复杂度：O(n)，两堆合计存放所有元素。

## 边界与处理

- 元素个数为奇数：len(low) 比 len(high) 多 1，中位数取 low 堆顶。
- 元素个数为偶数：取两堆顶平均，可能得到 x.5；整值结果（如 2.0）在输出时必须写成 2，因为期望串就是 2。
- 元素为负：堆比较天然支持负数，无需取绝对值或偏移。
- 重复元素：堆允许重复，不影响不变量。
- 题目保证调用 findMedian 前至少有一个元素，故不存在空堆取顶的退化。
- 输入约定：第 1 行方法名（首元素为类名 → 构造），第 2 行参数列表；构造与 addNum 返回 null。

## 代码
```python
import sys
import json
import heapq


class MedianFinder:
    def __init__(self):
        self.low = []
        self.high = []

    def addNum(self, num):
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def findMedian(self):
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        return (-self.low[0] + self.high[0]) / 2.0


def fmt(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return repr(v)
    return str(v)


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    methods = json.loads(lines[0])
    args = json.loads(lines[1])

    obj = None
    out = []
    for name, a in zip(methods, args):
        if obj is None:
            obj = MedianFinder()
            out.append(None)
        elif name == "addNum":
            obj.addNum(a[0])
            out.append(None)
        else:
            out.append(obj.findMedian())

    print("[" + ",".join(fmt(v) for v in out) + "]")


main()
```
'''


SOLUTIONS["PH06"] = r'''
## 思路

记所有 1 的下标为 p[0..m-1]。从中选出 k 个连续的 1（在 p 中连续的一段），把它们聚成相邻的一整块。设选中的区间为 [l, r]（r-l+1 = k）。

把它们变成相邻块的最少相邻交换次数，等价于：令 q[i] = p[i] - i，则把 q[l..r] 全部变成同一个值所需的最小绝对偏差和——因为 p 中相邻元素相差 d 时，压缩掉中间的空隙相当于让 q 相等。取中位数为目标即可最小化 Σ|q[i] - q[mid]|。

用前缀和可在 O(1) 内求出任意区间的该代价，于是对所有长度为 k 的窗口取最小即可。

## 复杂度分析

- 时间复杂度：O(n + m)。一次线性扫描收集 1 的下标并构造 q，随后对 m-k+1 个窗口各 O(1) 求代价。
- 空间复杂度：O(m)，存放下标与前缀和数组。

## 边界与处理

- k = 1：任何单个 1 自成连续块，代价 0，循环自然给出 0。
- 已经存在连续 k 个 1：对应 q 窗口中 k 个值恰好连续相等，代价 0（如示例 3）。
- 1 的个数恰好等于 k：只有唯一窗口，直接取该窗口代价。
- k 大于 1 的个数：题目保证 k ≤ sum(nums)，不会发生。
- 极端稀疏（如首尾两个 1 相距很远）：代价由 Σ|q - median| 正确给出（示例 2 得 5）。
- 全部为 1 或全部为 0：前者代价 0；后者与题设 k ≤ sum(nums) 矛盾，不会出现。
- 数值上界：下标 ≤ 10^5、m ≤ 10^5，代价上界约 10^10，超出 32 位，Python 整数安全。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = json.loads(lines[1])

    p = [i for i, v in enumerate(nums) if v == 1]
    m = len(p)
    if m < k or k == 0:
        print(0)
        return

    q = [p[i] - i for i in range(m)]

    # 前缀和
    pre = [0] * (m + 1)
    for i in range(m):
        pre[i + 1] = pre[i] + q[i]

    best = None
    for l in range(0, m - k + 1):
        r = l + k - 1
        mid = (l + r) // 2
        qm = q[mid]
        left_cnt = mid - l
        right_cnt = r - mid
        cost = (qm * left_cnt - (pre[mid] - pre[l])) + ((pre[r + 1] - pre[mid + 1]) - qm * right_cnt)
        if best is None or cost < best:
            best = cost

    print(best)


main()
```
'''


SOLUTIONS["PH07"] = r'''
## 思路

要求的是一对**不同**字符 (a, b)，在某个长度 ≥ k 的子串中 freq[a] 为奇数、freq[b] 为非 0 偶数，最大化 freq[a] - freq[b]。

做法：枚举 5×4 = 20 个有序字符对 (a, b)，对每个字符对做一次线性扫描。

把子串 (j, i]（左开右闭，用前缀计数表示）的差值写成前缀量之差：令 S = prefixA - prefixB，则 freq[a] - freq[b] = S[i] - S[j]。约束条件转化为：
1. 子串长度 i - j ≥ k；
2. freq[a] 为奇数 → prefixA 的奇偶性在 i、j 处不同；
3. freq[b] 为偶数且非 0 → prefixB 的奇偶性在 i、j 处相同，且子串内至少含一个 'b'（等价于 j ≤「i 之前最后一个 b 的下标」）。

于是对每个 i，需要在满足 j ≤ limit(i) = min(i - k, lastB(i)) 且奇偶状态匹配的 j 中取最小的 S[j]。关键性质：limit(i) 随 i 单调不减（i-k 与 lastB 都单调不减），因此可以用两根指针：随着 i 前进，把新进入 limit 范围的 j 按 (parityA, parityB) 分桶维护最小值，查询时直接取对应桶的最小值即可，总代价 O(n)。

## 复杂度分析

- 时间复杂度：O(20 * n) = O(n)。外层枚举 20 个字符对，内层对每个 i 做 O(1) 的入桶与查询。n ≤ 3*10^4。
- 空间复杂度：O(1)（每个字符对只需 4 个桶与若干前缀量）。

## 边界与处理

- s 只含 '0'~'4'（5 个字符），枚举 20 个有序对即可覆盖全部可能。
- 子串恰为最小长度 k：由 j ≤ i - k 保证。
- freq[b] 必须非 0：用「i 之前最后一个 b 的下标」作上界来实现，若 i 之前没有 b 则该 i 无解、跳过。
- 答案可能为负（如示例 1 得 -1），因此不能用 0 作初值，必须有解时才更新。
- 题目保证至少存在一个满足条件的子串，但代码仍以"无解则不更新"的方式保持稳健。
- 单字符子串不可能同时满足 a 奇、b 非 0 偶，因 k ≥ 1 时窗口上界会自然排除。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    k = json.loads(lines[1])

    n = len(s)
    digits = [ord(ch) - 48 for ch in s]

    # 前缀计数与每个位置之前最后一个 b 的下标
    pre = [[0] * 5 for _ in range(n + 1)]
    for i in range(n):
        pre[i + 1] = pre[i][:]
        pre[i + 1][digits[i]] += 1

    lastb = None  # 每个字符对单独计算（依赖具体的 b），见下方循环

    best = None
    for a in range(5):
        for b in range(5):
            if a == b:
                continue
            # 每个 i 之前最后一个 b 的下标
            last_b_idx = [-1] * (n + 1)
            c = -1
            for i in range(n):
                last_b_idx[i] = c
                if digits[i] == b:
                    c = i
            last_b_idx[n] = c

            INF = float("inf")
            bucket = [INF] * 4
            ptr = -1  # 已入桶的最大 j
            for i in range(1, n + 1):
                limit = min(i - k, last_b_idx[i - 1])
                if limit < 0:
                    continue
                while ptr < limit:
                    ptr += 1
                    pa = pre[ptr][a] & 1
                    pb = pre[ptr][b] & 1
                    sv = pre[ptr][a] - pre[ptr][b]
                    idx = pa * 2 + pb
                    if sv < bucket[idx]:
                        bucket[idx] = sv
                pa_i = pre[i][a] & 1
                pb_i = pre[i][b] & 1
                need = (1 - pa_i) * 2 + pb_i
                if bucket[need] != INF:
                    val = pre[i][a] - pre[i][b] - bucket[need]
                    if best is None or val > best:
                        best = val

    print(best if best is not None else 0)


main()
```
'''


SOLUTIONS["PH08"] = r'''
## 思路

设 atMost(k) 表示"不同整数个数**不超过** k"的子数组个数。由于"恰好 k 个"= "不超过 k" − "不超过 k−1"，答案为 atMost(k) - atMost(k-1)。

atMost 用滑动窗口：右端 r 扩展，把 nums[r] 计入窗口频次；当不同整数个数 > k 时，不断右移左端并减少频次，直到恢复不超过 k。窗口恢复后，以 r 结尾的合法子数组共有 (r - l + 1) 个（起点可取 l..r），累加即可。

正确性来自单调性：固定右端时，左端越靠右窗口越小、不同值个数越少，合法左端构成一个后缀。

## 复杂度分析

- 时间复杂度：O(n)。两次 atMost 调用，每次左右指针各前进至多 n 步，频次更新为 O(1)（用哈希表/数组）。
- 空间复杂度：O(V)，V 为不同值的个数，用于频次表与"当前不同值个数"的维护。

## 边界与处理

- k = 0：atMost(0) = 0（任何非空子数组至少含 1 个不同值），答案为 0；实现中窗口恒空、计数为 0，自然成立。
- k ≥ 不同值总数：所有子数组都满足，atMost 返回 n(n+1)/2。
- nums 中存在重复值：用频次计数而非集合，左端移出时只有频次归零才减少"不同值个数"。
- 单元素数组：atMost 正常返回 0 或 1。
- 结果规模：n ≤ 2*10^4，答案最大约 2*10^8，未超 32 位，但 Python 整数无此顾虑。
- atMost(k-1) 中 k-1 可能为 0，需保证不会传入负数导致逻辑错误。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = json.loads(lines[1])

    n = len(nums)

    def at_most(limit):
        if limit <= 0:
            return 0
        cnt = {}
        distinct = 0
        left = 0
        total = 0
        for right in range(n):
            v = nums[right]
            cnt[v] = cnt.get(v, 0) + 1
            if cnt[v] == 1:
                distinct += 1
            while distinct > limit:
                u = nums[left]
                cnt[u] -= 1
                if cnt[u] == 0:
                    distinct -= 1
                left += 1
            total += right - left + 1
        return total

    print(at_most(k) - at_most(k - 1))


main()
```
'''


SOLUTIONS["PH09"] = r'''
## 思路

子数组的合法条件是「最大值 − 最小值 ≤ k」。固定右端点 r 时，左端点 l 从 r 向左移动会不断扩展窗口，最大值不减、最小值不增，因此"合法"的左端点构成一个后缀 [L(r), r]，且 L(r) 随 r 单调不减——可以用双指针滑动窗口（配合单调队列维护窗口最值）。

对每个 r，再求「以 r 结尾、起点 ≥ L(r) 的所有子数组中异或最大值」。用前缀异或 P（P[i] = nums[0..i-1] 的异或），子数组 [l..r] 的异或 = P[r+1] ^ P[l]，于是问题变成：在一组可动态增删的 P[l]（l ∈ [L(r), r]）中查询与 P[r+1] 异或的最大值——用**二进制 Trie**（带计数以支持删除）解决，值域 < 2^15，树深 15。

## 复杂度分析

- 时间复杂度：O(n * B)，B = 15。每个下标至多被插入、删除各一次，每次 O(B)；每个 r 做一次 O(B) 查询。
- 空间复杂度：O(n * B) 最坏（Trie 节点数），实际远小于该上界；另有单调队列 O(n)。

## 边界与处理

- 单元素数组：窗口即自身，max-min=0 ≤ k，异或值即该元素。
- k = 0：合法子数组要求所有元素相等，滑动窗口会自动把 L 推到与 nums[r] 相等的最早位置。
- nums[i] 可等于 0：异或前缀相同，Trie 中需支持重复值的计数，否则删除会误删。
- 全 0 数组：答案为 0，查询返回 0 而非负值。
- 答案初值：子数组非空，总存在合法子数组（单元素必然合法），故答案有定义，初值取 0 即可（异或非负）。
- 值域：nums[i] < 2^15，k < 2^15，Trie 按 15 位建树足够覆盖所有异或结果。

## 代码
```python
import sys
import json
from collections import deque


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = json.loads(lines[1])

    n = len(nums)
    BITS = 15

    # 前缀异或
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] ^ nums[i]

    # 二进制 Trie（带计数，支持删除）
    child = [[-1, -1]]
    cnt = [0]

    def insert(val):
        node = 0
        cnt[node] += 1
        for b in range(BITS - 1, -1, -1):
            bit = (val >> b) & 1
            if child[node][bit] == -1:
                child[node][bit] = len(cnt)
                child.append([-1, -1])
                cnt.append(0)
            node = child[node][bit]
            cnt[node] += 1

    def remove(val):
        node = 0
        cnt[node] -= 1
        for b in range(BITS - 1, -1, -1):
            bit = (val >> b) & 1
            node = child[node][bit]
            cnt[node] -= 1

    def query(val):
        node = 0
        res = 0
        for b in range(BITS - 1, -1, -1):
            bit = (val >> b) & 1
            want = 1 - bit
            nxt = child[node][want]
            if nxt != -1 and cnt[nxt] > 0:
                res |= 1 << b
                node = nxt
            else:
                nxt2 = child[node][bit]
                if nxt2 == -1 or cnt[nxt2] == 0:
                    return res
                node = nxt2
        return res

    # 单调队列维护窗口最值
    dq_max = deque()
    dq_min = deque()
    left = 0
    ans = 0

    for right in range(n):
        v = nums[right]
        while dq_max and nums[dq_max[-1]] <= v:
            dq_max.pop()
        dq_max.append(right)
        while dq_min and nums[dq_min[-1]] >= v:
            dq_min.pop()
        dq_min.append(right)

        # 收缩左端直到窗口合法（左端越界的最值需先出队）
        while True:
            while dq_max and dq_max[0] < left:
                dq_max.popleft()
            while dq_min and dq_min[0] < left:
                dq_min.popleft()
            if nums[dq_max[0]] - nums[dq_min[0]] <= k:
                break
            remove(pre[left])
            left += 1

        # 此时 Trie 中恰为起点集合 pre[left..right-1]，补入 pre[right]
        insert(pre[right])
        cand = query(pre[right + 1])
        if cand > ans:
            ans = cand

    print(ans)


main()
```
'''


SOLUTIONS["PH11"] = r'''
## 思路

目标是用最少行动拾起恰好 k 个 1。两种手段：
- 第二种行动（相邻交换）：把已有的 1 逐步移到 Alice 所在位置；
- 第一种行动（创建 1）：在一个空的相邻位置造出 1 再换过来，恰好花 **2 次行动**（受 maxChanges 限制）。

因此若最终使用 c 个"创建"的 1，则剩余 s = k − c 个 1 必须来自数组中已有的 1，且最优一定选**下标连续的一段** 1（中间的 1 不可能跳过不选）。把这 s 个 1 全部移动到 Alice 站的位置 A，代价为 Σ|p[i] − A|，取中位数处最小。

总代价 = 2c + cost(s)，对所有可行 c 取最小（要求 0 ≤ c ≤ maxChanges 且 s ≤ 1 的个数）。

用前缀和可 O(1) 求出任意长度窗口到中位数的距离和。为控制规模，从最小的 s 开始逐步增大 s（即减少 c），一旦"剩下全部用创建"的代价 2(k−s) 已经不小于当前最优值即可提前停止。

## 复杂度分析

- 时间复杂度：O(m + W)，m 为 1 的个数，W 为实际枚举的窗口长度个数。每个窗口用前缀和 O(1) 求代价；配合「2(k−s) ≥ 当前最优即停」的剪枝，实测枚举量很小。
- 空间复杂度：O(m)，存放 1 的下标与前缀和。

## 边界与处理

- 数组中没有 1：只能全部创建，答案为 2k（示例 2 得 4）。
- 1 的个数 ≥ k 且分布密集：s = k 时可取到 0 代价，答案为 0。
- maxChanges = 0：只能用已有 1，s 固定为 k，退化为对全部长度 k 窗口求最小代价。
- 1 的个数少于 k 但加上 maxChanges 足够：s 最多取到 1 的个数，其余靠创建（题设保证 maxChanges + sum(nums) ≥ k，因此必有解）。
- k = 1：单个 1 到自身距离为 0，或创建一个花 2，答案 0；若数组无 1 则答案为 2。
- 数值范围：坐标 ≤ 10^5、k ≤ 10^5，代价上界约 10^10，Python 整数安全。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = json.loads(lines[1])
    max_changes = json.loads(lines[2])

    p = [i for i, v in enumerate(nums) if v == 1]
    m = len(p)

    pre = [0] * (m + 1)
    for i in range(m):
        pre[i + 1] = pre[i] + p[i]

    def gather_cost(l, r):
        """把 p[l..r] 全部移到中位数位置的代价。"""
        mid = (l + r) // 2
        pm = p[mid]
        left_cnt = mid - l
        right_cnt = r - mid
        return (pm * left_cnt - (pre[mid] - pre[l])) + ((pre[r + 1] - pre[mid + 1]) - pm * right_cnt)

    def window_min(s):
        """取恰好 s 个已有 1 时的最小聚合代价；s = 0 表示全部靠创建，代价为 0。"""
        if s <= 0:
            return 0
        return min(gather_cost(l, l + s - 1) for l in range(0, m - s + 1))

    # s 的取值范围：至少 s_min（其余用创建），至多 min(k, m)
    s_min = max(0, k - max_changes)
    s_max = min(k, m)
    if s_min > s_max:
        print(2 * k)
        return

    best = 2 * (k - s_min) + window_min(s_min)

    s = s_min + 1
    while s <= s_max and 2 * (k - s) < best:
        cur = window_min(s) + 2 * (k - s)
        if cur < best:
            best = cur
        s += 1

    print(best)


main()
```
'''


SOLUTIONS["SH07"] = r'''
## 思路

不能真正构造 result：长度可达 10^15。改为先只记录**长度**，再从目标下标 k 反向回溯到具体字符。

正向维护长度 L（Python 大整数，无溢出）：
- 小写字母：L += 1
- '*'：L = max(0, L − 1)
- '#'：L *= 2
- '%'：L 不变

记 Ls[i] 为处理完 s[i] 之后的长度。若最终长度 ≤ k，直接返回 '.'。

否则从最后一步开始反向映射下标 idx（初值 k）：
- 小写字母（末尾追加）：若 idx == Ls[i] − 1，则当前位置就是要找的字符，返回 s[i]；否则 idx 不变（追加不影响前面的下标）。
- '*'：删除末位，反向是"长度加 1"，idx 不变。
- '#'：正向把原串复制一份追加到后面，反向时若 idx ≥ Ls[i−1] 则减去一个原串长度。
- '%'：正向反转，反向时 idx = Ls[i−1] − 1 − idx。

## 复杂度分析

- 时间复杂度：O(n)。正向一遍算长度、反向一遍回溯，每步 O(1)。n ≤ 10^5。
- 空间复杂度：O(n)，存放每步之后的长度数组。

## 边界与处理

- 结果为空串：最终长度 0，任意 k 都越界，返回 '.'（示例 3）。
- k 恰等于长度减一：取到最后一个字符，边界必须用 idx == Ls[i]−1 而不是 <=。
- 连续的 '#'：长度指数增长，务必用 Python 大整数（不要用浮点或截断），否则会算错边界。
- 无字母的字符串（如 "**"）：长度恒为 0，返回 '.'。
- '*' 作用于空串：按 max(0, L−1) 处理，不会变成负数。
- 反向遍历时必须以 Ls 数组为基准，不能只看当前长度，否则 '#' 的减半位置会错。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    k = json.loads(lines[1])

    n = len(s)
    Ls = [0] * n
    L = 0
    for i, ch in enumerate(s):
        if ch == "*":
            L = max(0, L - 1)
        elif ch == "#":
            L *= 2
        elif ch == "%":
            pass
        else:
            L += 1
        Ls[i] = L

    if k >= L:
        print(".")
        return

    idx = k
    for i in range(n - 1, -1, -1):
        ch = s[i]
        prev = Ls[i - 1] if i > 0 else 0
        if ch == "%":
            idx = prev - 1 - idx
        elif ch == "#":
            if idx >= prev:
                idx -= prev
        elif ch == "*":
            pass
        else:
            if idx == Ls[i] - 1:
                print(ch)
                return
    print(".")


main()
```
'''


SOLUTIONS["SH10"] = r'''
## 思路

把 wordsContainer 中的每个单词**反转**后插入一棵 Trie。这样"公共后缀"就变成了反转串上的"公共前缀"，问题转化为标准的 Trie 前缀查询。

每个 Trie 节点保存一个最优答案下标 best：在所有经过该节点的单词中，取长度最短者；长度相同取下标最小者。查询时把 wordsQuery[i] 也反转，沿 Trie 尽量深入；每到达一个节点就用它的 best 更新答案，无法继续时停止。由于空后缀对所有单词都成立，根节点的 best 就是"无公共后缀"时的兜底（这正是示例 1 中 "xyz" 返回下标 1 的原因）。

## 复杂度分析

- 时间复杂度：O(Σ|container| + Σ|query|)，即建树与查询各为所有字符之和。题目保证两侧字符总长均 ≤ 5*10^5。
- 空间复杂度：O(Σ|container|)，Trie 节点数不超过容器字符总数。

## 边界与处理

- 完全无公共后缀：答案是根节点的 best，即"最短且最早"的单词，不能返回 -1。
- 多个单词并列最长公共后缀：取长度最短；长度也相同则取下标最小——用 (长度, 下标) 元组比较即可一次性表达。
- 查询串比容器中所有单词都长：走到 Trie 尽头即自然停下，不会越界。
- 单字符单词/查询：反转后仍是自身，逻辑不变。
- 编码细节：用 node*26 + (字符序号) 作为子节点键，避免为每个节点单独建字典，显著降低内存占用（节点数可达 5*10^5）。
- 输出为紧凑 JSON。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    container = json.loads(lines[0])
    queries = json.loads(lines[1])

    INF = (1 << 30, 1 << 30)
    child = {}
    best = [INF]

    def upd(node, cand):
        if cand < best[node]:
            best[node] = cand

    for i, w in enumerate(container):
        node = 0
        key_info = (len(w), i)
        upd(node, key_info)
        for ch in reversed(w):
            k = node * 26 + (ord(ch) - 97)
            nxt = child.get(k)
            if nxt is None:
                nxt = len(best)
                child[k] = nxt
                best.append(INF)
            node = nxt
            upd(node, key_info)

    ans = []
    for q in queries:
        node = 0
        res = best[0][1]
        for ch in reversed(q):
            k = node * 26 + (ord(ch) - 97)
            nxt = child.get(k)
            if nxt is None:
                break
            node = nxt
            res = best[node][1]
        ans.append(res)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["SH11"] = r'''
## 思路

把每个字符串解析为精确有理数（用 fractions.Fraction，避免浮点误差），再比较是否相等。

字符串形如：整数部分 [.非重复部分 [(重复部分)]]。记：
- 整数部分 I
- 非重复部分 D，长度 a
- 重复部分 R，长度 b（可能不存在）

数值 = I + D / 10^a + R / (10^a * (10^b − 1))

推导：非重复部分是有限小数 D/10^a；重复部分从第 a+1 位开始循环，其值为 R * 10^{-a} * (10^{-b} + 10^{-2b} + ...) = R * 10^{-a) / (10^b − 1)。

用 Fraction 精确计算后比较即可，从而正确处理 "0.9(9)" == "1." 这类进位陷阱。

## 复杂度分析

- 时间复杂度：O(L)，L 为字符串长度。Fraction 运算的分母数量级约 10^(a+b) ≤ 10^8，常数级开销可忽略。
- 空间复杂度：O(1)（不计输入字符串）。

## 边界与处理

- 没有小数点（纯整数）：只取整数部分，非重复与重复部分视为空。
- 有小数点但无括号："1."、"2.12" 等，重复部分为空，直接用有限小数公式。
- 重复部分全为 9：如 0.9(9) = 1，用分数运算自动进位，无需特殊判断（示例 3）。
- 重复部分全为 0：如 0.1(0)，公式给出 0.1，正确。
- 整数部分为 0：允许（如 "0.5"），题目只禁止非零整数部分以 0 开头。
- 非重复部分可空：此时 a = 0，D = 0，公式退化为纯循环小数。
- 输出为 JSON 布尔值的小写形式 true / false。

## 代码
```python
import sys
import json
from fractions import Fraction


def parse(t):
    if "." in t:
        int_part, rest = t.split(".", 1)
    else:
        int_part, rest = t, ""

    if "(" in rest:
        non_rep, rep = rest.split("(", 1)
        rep = rep.rstrip(")")
    else:
        non_rep, rep = rest, ""

    a = len(non_rep)
    b = len(rep)

    val = Fraction(int(int_part) if int_part else 0, 1)
    if a > 0:
        val += Fraction(int(non_rep), 10 ** a)
    if b > 0:
        val += Fraction(int(rep), (10 ** a) * (10 ** b - 1))
    return val


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    t = json.loads(lines[1])
    print("true" if parse(s) == parse(t) else "false")


main()
```
'''


SOLUTIONS["SH12"] = r'''
## 思路

答案定义是：对 words[i] 的每个非空前缀 p，累加"以 p 为前缀的单词个数"。用 Trie 统计即可：先把每个单词的所有前缀插入 Trie 并对节点计数，再对每个单词沿其路径累加节点计数之和，即为该单词的答案。

正确性直接来自 Trie 的结构：某个前缀 p 对应的节点计数恰好等于以 p 为前缀的单词数（插入每个单词时，其路径上的每个节点都 +1）。

## 复杂度分析

- 时间复杂度：O(Σ|words[i]|)，即所有单词长度之和（≤ 10^6）。插入与查询各走一遍路径，每步 O(1)。
- 空间复杂度：O(Σ|words[i]|)，Trie 节点数不超过总字符数。

## 边界与处理

- 单个单词：答案等于其长度（每个前缀的计数都是 1）。
- 互为前缀的单词（如 "a"、"ab"、"abc"）：需要沿路径逐节点计数，不能只统计整串节点。
- 重复单词：同一单词出现多次时计数会累加，符合"以 p 为前缀的 words[i] 的数目"的定义（含重复项）。
- 单词视作自身的前缀：因此路径包含末节点。
- 内存细节：节点数与字符总量同阶（最多约 10^6），用 node*26+c 编码子节点键 + 计数数组，避免为每个节点建独立字典造成内存膨胀。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    words = json.loads(lines[0])

    child = {}
    cnt = [0]

    for w in words:
        node = 0
        cnt[node] += 1
        for ch in w:
            k = node * 26 + (ord(ch) - 97)
            nxt = child.get(k)
            if nxt is None:
                nxt = len(cnt)
                child[k] = nxt
                cnt.append(0)
            node = nxt
            cnt[node] += 1

    ans = []
    for w in words:
        node = 0
        total = 0
        for ch in w:
            node = child[node * 26 + (ord(ch) - 97)]
            total += cnt[node]
        ans.append(total)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["SH13"] = r'''
## 思路

要求支持 (前缀, 后缀) 查询并返回满足条件单词的**最大下标**。单词长度与查询串长度都不超过 7，因此可以**预计算所有 (前缀, 后缀) 组合**到答案的映射：

对每个单词 words[i]，枚举它所有非空前缀与所有非空后缀（各至多 7 个），把组合 (pref, suff) 映射到下标 i，冲突时保留较大下标（因为要求最大下标）。

查询时直接查表，命中则返回对应下标，否则返回 -1。由于单词长度上限极小，字典规模至多 10^4 × 7 × 7 = 4.9×10^5 项。

## 复杂度分析

- 时间复杂度：预处理 O(Σ L²)，L ≤ 7，即每个单词至多 49 个组合，总量约 5×10^5；每次查询 O(L) 拼键 + O(1) 查表。
- 空间复杂度：O(Σ L²)，即字典条目数。

## 边界与处理

- 不存在满足条件的单词：返回 -1，不能返回 0。
- 多个单词满足：返回最大下标，因此预处理时对同一键用 max 更新（按下标递增遍历时直接覆盖即可）。
- 前缀/后缀长度可为 1，也可能是整词（当前缀与后缀都是整词时表示单词等于查询串，仍按组合处理）。
- 前缀与后缀有重叠（如单词 "aaa"、pref="aa"、suff="aa"）：本题只要求"以 pref 开头且以 suff 结尾"，重叠是允许的，因此不能用"前缀长度 + 后缀长度 ≤ 单词长度"去过滤。
- 输入约定：第 1 行方法名（首元素为类名 → 构造），第 2 行参数列表；构造返回 null，f 返回下标。
- 输出为紧凑 JSON。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    methods = json.loads(lines[0])
    args = json.loads(lines[1])

    table = {}
    obj = None
    out = []

    for name, a in zip(methods, args):
        if obj is None:
            words = a[0]
            for i, w in enumerate(words):
                L = len(w)
                for x in range(1, L + 1):
                    pref = w[:x]
                    for y in range(1, L + 1):
                        suff = w[L - y:]
                        table[(pref, suff)] = i
            obj = True
            out.append(None)
        else:
            pref, suff = a[0], a[1]
            out.append(table.get((pref, suff), -1))

    print("[" + ",".join("null" if v is None else str(v) for v in out) + "]")


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
        os.path.dirname(os.path.abspath(__file__)), "batch02.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
