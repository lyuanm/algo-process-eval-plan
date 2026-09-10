# -*- coding: utf-8 -*-
"""第七批「会话内助手撰写」的解答（TM13-TM15, XE01-XE13）。"""
SOLUTIONS = {}

_TREE_HELPERS = r'''
def build_tree(arr):
    """LeetCode 层序数组 -> 树（队列式反序列化）。"""
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


SOLUTIONS["TM13"] = r'''
## 思路

BST 的**逆中序**遍历（右 → 根 → 左）等价于按节点值降序访问。在遍历过程中维护 running = 已访问节点值之和（即所有比当前节点大的值之和），把当前节点值改写为 running。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(h)，显式栈深度。

## 边界与处理

- 空树：输出 []。
- 单节点：输出其自身值。
- 节点值可为负：累加逻辑与符号无关。
- 链状 BST：必须用显式栈，避免递归深度问题。
- 必须用"先加后写"：若先写 running 再加当前值，当前节点会漏掉自己。
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


SOLUTIONS["TM14"] = r'''
## 思路

要使 |A.val − B.val| 最大且 A 是 B 的祖先，对每个节点 B 只需知道"从根到 B 的路径上出现过的最小值与最大值"：答案候选为 |B.val − minPath| 与 |B.val − maxPath| 的较大者。

因此一次自顶向下遍历即可：向下传递路径上的最小值与最大值，在每个节点更新答案。

## 复杂度分析

- 时间复杂度：O(n)，每个节点访问一次。
- 空间复杂度：O(h)，栈深度。

## 边界与处理

- 单节点路径：不存在"不同节点"的祖先对，题目保证节点数 ≥ 2，故必有解。
- 根为最小值/最大值：极端路径差会被正确捕捉。
- 节点值可达 10^5 且可为负：差值用绝对值计算。
- 必须是"祖先-后代"对，不能取同层节点：路径 min/max 天然只包含祖先。
- 链状树：用显式栈避免递归过深（节点数可达 5000）。
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
        stack = [(root, root[0], root[0])]
        while stack:
            node, lo, hi = stack.pop()
            v = node[0]
            if abs(v - lo) > ans:
                ans = abs(v - lo)
            if abs(v - hi) > ans:
                ans = abs(v - hi)
            nlo = lo if lo < v else v
            nhi = hi if hi > v else v
            if node[1] is not None:
                stack.append((node[1], nlo, nhi))
            if node[2] is not None:
                stack.append((node[2], nlo, nhi))

    print(ans)


main()
```
'''


SOLUTIONS["TM15"] = r'''
## 思路

两棵都是 BST，各自的中序遍历即为升序序列。分别取出两棵树的中序列表，再做一次归并（或直接拼接后整体排序）即可。

归并写法是 O(n+m)，比排序更优且天然稳定。

## 复杂度分析

- 时间复杂度：O(n + m)，两次中序 + 一次归并。
- 空间复杂度：O(n + m)，两个中序数组与结果数组。

## 边界与处理

- 两棵树都为空：输出 []。
- 一棵为空：输出另一棵的中序序列。
- 存在重复值（如示例 2 的两个 8）：题目未要求去重，重复值都要保留。
- 节点值可为负：与排序无关。
- 树可能退化成链：用显式栈中序，避免递归深度问题。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json
''' + _TREE_HELPERS + r'''

def inorder(root):
    res = []
    stack = []
    cur = root
    while cur is not None or stack:
        while cur is not None:
            stack.append(cur)
            cur = cur[1]
        node = stack.pop()
        res.append(node[0])
        cur = node[2]
    return res


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    r1 = build_tree(json.loads(lines[0]))
    r2 = build_tree(json.loads(lines[1]))

    a = inorder(r1)
    b = inorder(r2)

    res = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            res.append(a[i])
            i += 1
        else:
            res.append(b[j])
            j += 1
    res.extend(a[i:])
    res.extend(b[j:])

    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XE01"] = r'''
## 思路

题目要求对每个 nums[i] 找到最小的 ans 使 ans OR (ans + 1) == nums[i]。

性质：ans 与 ans+1 的关系是"低位连续的 1 全部进位"，因此 ans | (ans+1) 的二进制形如「高位与 ans 相同，之后跟着一串 1」。具体地，若 ans 的低 k 位全为 1（k ≥ 0），则 ans+1 会把第 k 位从 0 变 1、低 k 位清零，于是 OR 结果 = (ans 去掉低 k 位后的部分) 后面补上 k+1 个 1。

因为 nums[i] ≤ 1000，直接从小到大枚举 ans（0..nums[i]）并验证即可，取第一个满足的；都不满足则 -1。

## 复杂度分析

- 时间复杂度：O(n · max(nums))，n ≤ 100、nums[i] ≤ 1000 → 最多 10^5 次常数运算。
- 空间复杂度：O(1)（不计输出）。

## 边界与处理

- 不存在解的情形：如 nums[i] = 2，返回 -1（示例 1 第一个元素）。
- 最小的解为 0：n = 1 时 0 | 1 = 1 成立，但 nums 由质数组成（≥ 2），不会出现。
- 枚举上界：ans 不可能大于 nums[i]（因为 ans | (ans+1) ≥ ans），枚举到 nums[i] 即可。
- 结果必须逐元素独立判断，不能因为某个元素无解就整体返回 -1。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    ans = []
    for target in nums:
        found = -1
        for cand in range(0, target + 1):
            if (cand | (cand + 1)) == target:
                found = cand
                break
        ans.append(found)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XE02"] = r'''
## 思路

n ≤ 12，子集总数最多 4096 个，直接枚举所有子集（用位掩码 0..2^n−1），对每个子集求元素的异或和并累加即可。

## 复杂度分析

- 时间复杂度：O(2^n · n)，最坏 4096×12 ≈ 5×10^4。
- 空间复杂度：O(1)（枚举掩码，不需存子集）。

## 边界与处理

- 空子集：异或和为 0，也要计入（它不贡献值），枚举从掩码 0 开始天然包含。
- 元素相同但下标不同：题目要求分别计数，位掩码枚举天然按元素区分。
- 单元素数组：答案为 0 + nums[0]。
- 元素范围 1~20，异或结果不超过 31，求和不超过 4096×31，远小于 32 位上限。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    n = len(nums)
    total = 0
    for mask in range(1 << n):
        x = 0
        m = mask
        i = 0
        while m:
            if m & 1:
                x ^= nums[i]
            m >>= 1
            i += 1
        total += x

    print(total)


main()
```
'''


SOLUTIONS["XE03"] = r'''
## 思路

遍历下标 i，判断 i 的二进制表示中 1 的个数是否恰为 k；用 bin(i).count('1') 或 i.bit_count() 统计，满足则累加 nums[i]。

## 复杂度分析

- 时间复杂度：O(n log n)，n ≤ 1000，每个下标统计位数最多 10 次。
- 空间复杂度：O(1)。

## 边界与处理

- k = 0：只有下标 0 满足（0 的二进制没有 1），返回 nums[0]。
- k 大于下标的最高位数：没有满足的下标，返回 0。
- 下标 0：0 的置位数为 0，k=0 时应被计入。
- 元素值正数（≥ 1），无需考虑负数。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = json.loads(lines[1])

    total = 0
    for i, v in enumerate(nums):
        if bin(i).count("1") == k:
            total += v

    print(total)


main()
```
'''


SOLUTIONS["XE04"] = r'''
## 思路

已知 arr[i] XOR arr[i+1] = encoded[i]，两边同时异或 arr[i] 得 arr[i+1] = arr[i] XOR encoded[i]。从 arr[0] = first 出发逐个递推即可。

## 复杂度分析

- 时间复杂度：O(n)，一次线性递推。
- 空间复杂度：O(n)，结果数组。

## 边界与处理

- encoded 长度为 0：只有 arr[0] = first，输出 [first]（题目保证长度 ≥ 2，仍作保护）。
- 非负整数：异或不会产生负值。
- 数值上界：编码值可到 10^5 量级，Python 整数无溢出。
- 必须严格按顺序递推，不能用并行或乱序方式。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    encoded = json.loads(lines[0])
    first = json.loads(lines[1])

    arr = [first]
    for e in encoded:
        arr.append(arr[-1] ^ e)

    print(json.dumps(arr, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XE05"] = r'''
## 思路

遍历数组，把所有偶数按位或起来。初值取 0（0 与任何数异或/或都不改变该数）。

## 复杂度分析

- 时间复杂度：O(n)。
- 空间复杂度：O(1)。

## 边界与处理

- 数组中没有偶数：初值 0 保持，返回 0（示例 2）。
- 只有 1 个偶数：返回该偶数本身。
- 判断偶数用 v % 2 == 0 或 v & 1 == 0；注意 0 是偶数（题目元素 ≥ 1，不会出现）。
- 元素 ≤ 100，结果 ≤ 127。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    res = 0
    for v in nums:
        if v % 2 == 0:
            res |= v

    print(res)


main()
```
'''


SOLUTIONS["XE06"] = r'''
## 思路

把 start 变成 goal 的最少位翻转次数，等于两者二进制表示中不相同位的个数，即 popcount(start XOR goal)。

理由：每一位相互独立，取值不同的位必须翻一次，取值相同的位翻偶数次（最少 0 次）。

## 复杂度分析

- 时间复杂度：O(log max(start, goal))，最多约 30 位。
- 空间复杂度：O(1)。

## 边界与处理

- start == goal：异或为 0，返回 0。
- 前导零也要参与：异或运算会自然把它们计入（如 3 与 4 的差异包含最高位）。
- 数值可达 10^9（约 30 位），Python 整数安全。
- 不能用 while 逐位右移并只处理到较大值：用异或后统计位数最简洁且不会漏位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    start = json.loads(lines[0])
    goal = json.loads(lines[1])

    print(bin(start ^ goal).count("1"))


main()
```
'''


SOLUTIONS["XE07"] = r'''
## 思路

由于 allowed 中的字符互不相同，可以用一个集合（或 26 位掩码）表示允许的字符集。对每个 word，检查其所有字符是否都在集合中；全部在内则计数加一。

用位掩码更快：把 allowed 映射成整数 mask，再把每个 word 的字符集也映射成整数，判断 (word_mask & ~allowed_mask) == 0。

## 复杂度分析

- 时间复杂度：O(Σ|words[i]| + |allowed|)，每个字符一次 O(1) 位运算。
- 空间复杂度：O(1)（两个 26 位整数）。

## 边界与处理

- word 为空串：没有任何字符，平凡满足（题目长度 ≥ 1，不会出现）。
- allowed 含全部 26 个字母：所有 word 都一致。
- 字符重复（如 "aaab"）：用集合/掩码判断，重复不影响结果。
- 大小写：题目只含小写字母。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    allowed = json.loads(lines[0])
    words = json.loads(lines[1])

    mask = 0
    for ch in allowed:
        mask |= 1 << (ord(ch) - 97)

    cnt = 0
    for w in words:
        m = 0
        for ch in w:
            m |= 1 << (ord(ch) - 97)
        if m & ~mask == 0:
            cnt += 1

    print(cnt)


main()
```
'''


SOLUTIONS["XE08"] = r'''
## 思路

两个字符串"相似"的定义是字符集合相同（与重复次数和顺序无关）。因此把每个字符串映射为其字符集合（用 26 位掩码表示），相同的掩码归为一组；组内元素两两构成相似对，贡献 C(cnt, 2)。

## 复杂度分析

- 时间复杂度：O(Σ|words[i]|)，构造掩码线性；分组统计 O(n)。
- 空间复杂度：O(n)，掩码计数表（也可退化为哈希表）。

## 边界与处理

- 只有一个字符串：不存在下标对，返回 0。
- 全部互不相似（如示例 3）：返回 0。
- 重复字符（"aabb"、"ab"、"ba"）：三者的字符集都是 {a,b}，应两两配对，贡献 C(3,2)=3（示例 2）。
- 空字符串：字符集为空，会自成一组（题目长度 ≥ 1，不会出现）。
- 计数规模：n ≤ 100 时对数最大 4950，未超 32 位。
- 输出为单个整数。

## 代码
```python
import sys
import json
from collections import Counter


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    words = json.loads(lines[0])

    cnt = Counter()
    for w in words:
        m = 0
        for ch in w:
            m |= 1 << (ord(ch) - 97)
        cnt[m] += 1

    ans = 0
    for c in cnt.values():
        ans += c * (c - 1) // 2

    print(ans)


main()
```
'''


SOLUTIONS["XE09"] = r'''
## 思路

题目要求"第二次出现的位置最靠前"的字母。因此从左到右扫描，遇到某个字符第二次出现时，它就是答案——因为后续字母的第二次出现位置必然更靠后。

实现：用一个集合记录已出现过的字符；扫描时若当前字符已在集合中，立即输出并结束。

## 复杂度分析

- 时间复杂度：O(n)，n ≤ 100。
- 空间复杂度：O(1)（最多 26 个字符）。

## 边界与处理

- 相邻重复（如 "abcdd"）：直接在最后一位命中，返回 'd'（示例 2）。
- 某字母出现三次：第一次遇到"第二次出现"即返回，不会跳到第三次。
- 只有一个重复字母：必然返回它（题目保证存在重复字母）。
- 输出为裸字符（不带引号）。
- 注意判定条件是"第二次出现的下标最小"，而不是"首次出现最早"，用"遇到即返回"恰好实现该语义。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])

    seen = set()
    for ch in s:
        if ch in seen:
            print(ch)
            return
        seen.add(ch)


main()
```
'''


SOLUTIONS["XE10"] = r'''
## 思路

峰值定义：严格大于左右相邻元素，且不能是首尾元素。因此只需检查下标 1..len−2，判断 mountain[i] > mountain[i−1] 且 mountain[i] > mountain[i+1]。

题目允许任意顺序返回，按要求按下标升序输出即可。

## 复杂度分析

- 时间复杂度：O(n)。
- 空间复杂度：O(1)（不计输出）。

## 边界与处理

- 长度为 3：只检查下标 1（示例 1 因相等而不算峰值，返回 []）。
- 相邻元素相等：不满足"严格大于"，不算峰值。
- 首尾元素即使是局部极值也不算峰值，因此循环范围必须是 [1, n−2]。
- 可能有多个峰值，全部收集（示例 2 返回 [1,3]）。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    m = json.loads(lines[0])

    ans = []
    for i in range(1, len(m) - 1):
        if m[i] > m[i - 1] and m[i] > m[i + 1]:
            ans.append(i)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XE11"] = r'''
## 思路

"二进制表示仅包含置位位"意味着该数的二进制全是 1，形如 2^k − 1。要找 ≥ n 的最小这样的数：

设 n 的二进制位数为 L（即 L = n.bit_length()），则 2^L − 1 是位数恰为 L 的全 1 数，它一定 ≥ n（因为 n < 2^L）。而所有位数小于 L 的全 1 数都 < n，故答案就是 2^L − 1。

注意当 n 本身就是全 1 数时，2^L − 1 == n，公式同样正确（示例 3）。

## 复杂度分析

- 时间复杂度：O(1)（位长计算）。
- 空间复杂度：O(1)。

## 边界与处理

- n 本身就是全 1 数（3、7、15）：返回 n 自身。
- n = 1：返回 1。
- n 为 2 的幂（如 8）：位数 4 → 返回 15。
- 不能用"从 n 开始逐个 +1 检查"的方式，虽然 n ≤ 1000 也能过，但公式法更精确。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])

    print((1 << n.bit_length()) - 1)


main()
```
'''


SOLUTIONS["XE12"] = r'''
## 思路

汉明距离 = 两个数二进制中不同位的个数 = popcount(x XOR y)。逐位异或后统计 1 的个数即可。

## 复杂度分析

- 时间复杂度：O(log max(x, y))，最多约 31 位。
- 空间复杂度：O(1)。

## 边界与处理

- x == y：距离 0。
- 一个为 0：距离等于另一个数的置位数。
- 数值可达 2^31−1：Python 整数无溢出，bin().count('1') 精确。
- 不要用"先转成等长二进制字符串再逐位比较"的写法，异或更简洁且不会漏掉前导零差异。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    x = json.loads(lines[0])
    y = json.loads(lines[1])

    print(bin(x ^ y).count("1"))


main()
```
'''


SOLUTIONS["XE13"] = r'''
## 思路

分给 3 位小朋友，每人 0..limit 颗，且总和恰为 n。直接三重循环枚举 a、b 后由 c = n − a − b 推出第三位，校验 0 ≤ c ≤ limit 即可，复杂度 O(limit²)。

n ≤ 50、limit ≤ 50，最多 2601 次判断。

## 复杂度分析

- 时间复杂度：O(limit²)，limit ≤ 50 → 最多 2601 次。
- 空间复杂度：O(1)。

## 边界与处理

- limit ≥ n：等价于不加限制的隔板法 C(n+2, 2)（示例 2 的 n=limit=3 → 10）。
- limit 很小（如 limit = 1、n = 5）：无解，返回 0。
- 小朋友可以得 0 颗：枚举从 0 开始，不能从 1 开始。
- 第三位必须显式校验 ≤ limit，只靠 c ≥ 0 不够。
- n、limit ≤ 50 时方案数最多约 1326，远小于 32 位上限。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    limit = json.loads(lines[1])

    cnt = 0
    for a in range(0, limit + 1):
        for b in range(0, limit + 1):
            c = n - a - b
            if 0 <= c <= limit:
                cnt += 1

    print(cnt)


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
        os.path.dirname(os.path.abspath(__file__)), "batch07.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
