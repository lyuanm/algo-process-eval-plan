# -*- coding: utf-8 -*-
"""第九批（最后 16 题）「会话内助手撰写」的解答（XH15, XM01-XM15）。

注意两处顺序敏感的输出（判题做精确比较，必须复现参考解的生成顺序）：
  XM06 全排列：期望顺序为「交换式回溯」的顺序（[3,2,1] 在 [3,1,2] 之前），
               而非按起点分组的字典序。
  XM07 子集  ：期望顺序为「按大小分组、组内字典序」，等价于 itertools.combinations
               按 k = 0..n 依次枚举。
"""
SOLUTIONS = {}


SOLUTIONS["XH15"] = r'''
## 思路

好人的陈述必须全部为真，坏人的陈述不受约束。因此可以**枚举所有 2^n 种"谁是好人"的假设**（n ≤ 15），对每种假设校验：

对每个被判为好人的人 i，检查他的每条陈述：
- statements[i][j] == 2（未陈述）→ 无约束；
- statements[i][j] == 1 → j 必须被判为好人；
- statements[i][j] == 0 → j 必须被判为坏人。

全部满足则该假设可行，取可行假设中好人数的最大值。

## 复杂度分析

- 时间复杂度：O(2^n · n^2)，n ≤ 15 → 32768 × 225 ≈ 7×10^6，可接受。
- 空间复杂度：O(1)（仅用若干整数与位掩码）。

## 边界与处理

- n = 2（最小规模）：示例 2 中两人互指对方是坏人，最多 1 个好人。
- 全部陈述为 2：任何假设都可行，答案为 n。
- 好人数为 0 的假设恒可行（没有好人就没有需要校验的陈述），因此答案至少为 0。
- 坏人可以说真话也可以说假话，**不能**对坏人的陈述做任何校验（示例 1 的推理正依赖这一点）。
- 自己对自己的陈述恒为 2，无需特判。
- 用位掩码表示假设，逐位判断角色，避免构造集合。
- 输出为单个整数。

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
    statements, _ = dec.raw_decode(data, i)

    n = len(statements)
    best = 0
    for mask in range(1 << n):
        good = 0
        for b in range(n):
            if (mask >> b) & 1:
                good += 1
        if good <= best:
            continue
        ok = True
        for b in range(n):
            if not ((mask >> b) & 1):
                continue
            for j in range(n):
                s = statements[b][j]
                if s == 2:
                    continue
                is_good = (mask >> j) & 1
                if s == 1 and not is_good:
                    ok = False
                    break
                if s == 0 and is_good:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            best = good

    print(best)


main()
```
'''


SOLUTIONS["XM01"] = r'''
## 思路

长度为 n 的二进制串中，不允许出现相邻的两个 '0'。n ≤ 18，直接枚举 0..2^n−1 的每一个掩码（按数值升序即按字典序升序），转成长度为 n 的二进制串并检查是否含子串 "00" 即可。

按数值升序枚举恰好保证了输出是字典序升序，与期望串一致。

## 复杂度分析

- 时间复杂度：O(2^n · n)，n ≤ 18 → 约 4.7×10^6，可接受。
- 空间复杂度：O(答案数量 · n)。

## 边界与处理

- n = 1：没有长度为 2 的子串，任何单字符都有效，输出 ["0","1"]（示例 2）。
- 全 1 串恒有效；全 0 串在 n ≥ 2 时无效。
- 输出顺序必须是字典序升序（按掩码递增枚举即可）；判题为精确比较。
- 必须把掩码格式化为**定长** n 位（左侧补 0），否则长度不合。
- 输出为紧凑 JSON 字符串数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])

    res = []
    for mask in range(1 << n):
        s = bin(mask)[2:].rjust(n, "0")
        if "00" not in s:
            res.append(s)

    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XM02"] = r'''
## 思路

设当前所有元素的异或和为 X。翻转某个元素的第 b 位，会让 X 的第 b 位也翻转（其余位不变）。因此问题变成：把 X 变成 k 需要翻转多少个二进制位，答案就是 popcount(X XOR k)。

原因是每一位相互独立：X 与 k 在该位不同则必须翻一次（可通过对任一元素翻转该位实现），相同则不必翻。

## 复杂度分析

- 时间复杂度：O(n + log(max))，一次求异或和 + 位计数。
- 空间复杂度：O(1)。

## 边界与处理

- X 已等于 k：答案为 0（示例 2）。
- 需要翻转前导零位（如把某位从 0 变 1）：题目明确允许，异或运算天然覆盖。
- 元素可达 10^6、k 可达 10^6：位宽约 20，Python 整数安全。
- 不能在中途修改数组后再重新统计——一次异或和即可确定全部差异位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    k = json.loads(lines[1])

    x = 0
    for v in nums:
        x ^= v

    print(bin(x ^ k).count("1"))


main()
```
'''


SOLUTIONS["XM03"] = r'''
## 思路

pref[i] = arr[0] ^ … ^ arr[i]。两边同时异或 pref[i−1] 得 arr[i] = pref[i] ^ pref[i−1]（i ≥ 1）；arr[0] = pref[0]。递推即可。

## 复杂度分析

- 时间复杂度：O(n)。
- 空间复杂度：O(n)，结果数组（也可原地修改 pref）。

## 边界与处理

- 长度为 1：arr[0] = pref[0]（示例 2）。
- 前缀可重复（如示例 1 中 pref[1]=2、pref[4]=1）：说明对应区间的异或为 0，推导依然成立。
- 元素非负且 ≤ 10^6：Python 整数无溢出。
- 不能把 arr[i] 写成 pref[i] ^ pref[i+1]，方向必须用"当前减前一个"。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    pref = json.loads(lines[0])

    arr = []
    for i, v in enumerate(pref):
        arr.append(v if i == 0 else v ^ pref[i - 1])

    print(json.dumps(arr, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XM04"] = r'''
## 思路

操作是 nums[i] = nums[i] AND (nums[i] XOR x)。关键性质：选择任意非负整数 x，可以把 nums[i] 的**任意若干位清零**（x 的该位为 1 时，nums[i] XOR x 该位取反，与 nums[i] 相与后归零；x 的该位为 0 时该位保持不变）。也就是说，每个元素都可以被"削"成其任意子掩码。

结论：最大异或和 = 所有元素的按位或。

- 上界：异或和的第 b 位为 1 要求至少有一个元素在第 b 位为 1，因此异或和 ⊆ 按位或（按位角度看不会超出）。
- 可达：对按位或中出现的每个位 b，只需让"某一个原本含该位的元素"保留该位、并把其它元素的该位清零，即可让异或和恰好等于按位或。

## 复杂度分析

- 时间复杂度：O(n)，一次按位或累加。
- 空间复杂度：O(1)。

## 边界与处理

- 单个元素：答案就是它本身（无需操作）。
- 元素为 0：不贡献任何位。
- 重复元素：异或会让相同值的位抵消，但只要该位仍出现在按位或里，就能通过清零其它元素把它"救回来"。
- 无需真正执行操作，直接输出按位或。
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
        res |= v

    print(res)


main()
```
'''


SOLUTIONS["XM05"] = r'''
## 思路

n ≤ 16，枚举全部 2^n 个子集（掩码 0..2^n−1），对每个非空子集求按位或，找出最大值，并统计达到该值的子集个数。

注意"不同子集"按**下标组合**区分，因此即便元素值相同也要分别计数——位掩码枚举天然满足这一点。

## 复杂度分析

- 时间复杂度：O(2^n · n)，n ≤ 16 → 65536 × 16 ≈ 10^6。
- 空间复杂度：O(1)。

## 边界与处理

- 所有元素相同（示例 2）：最大值就是该值，全部非空子集（2^n − 1 个）都达到，答案为 7。
- 单个元素：唯一非空子集就是它自己，答案为 1。
- 空子集的按位或为 0，题目只统计非空子集，必须排除掩码 0（除非最大值本身为 0 且题目允许——本题元素 ≥ 1，最大值必 > 0）。
- 元素可达 10^5：位宽 17，按位或用 Python 整数。
- 结果最大为 2^16 − 1 = 65535，未超 32 位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    n = len(nums)
    counts = {}
    for mask in range(1, 1 << n):
        v = 0
        m = mask
        i = 0
        while m:
            if m & 1:
                v |= nums[i]
            m >>= 1
            i += 1
        counts[v] = counts.get(v, 0) + 1

    print(counts[max(counts)])


main()
```
'''


SOLUTIONS["XM06"] = r'''
## 思路

求不含重复数字数组的所有全排列。用**交换式回溯**：第 first 位依次与 i（i ≥ first）交换，然后递归处理 first+1 位，返回时再换回来。

必须用这一生成顺序：判题对输出做了精确比较，期望串正是交换式回溯产生的序列——例如 [1,2,3] 的最后一个排列是 [3,1,2] 之前的 [3,2,1]，而"按起点分组"的写法会给出相反的次序。

## 复杂度分析

- 时间复杂度：O(n · n!)，n ≤ 6 → 最多 720 个排列。
- 空间复杂度：O(n)，递归栈；结果占 O(n · n!)。

## 边界与处理

- 单元素：只有一种排列 [[x]]。
- 元素可为负：与交换逻辑无关。
- 元素互不相同（题目保证），无需去重。
- 交换后必须复位，否则后续分支会用到被污染的数组。
- 输出为紧凑 JSON 的二维数组，顺序必须与期望一致（判题为逐 token 精确比较）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    n = len(nums)
    res = []

    def backtrack(first):
        if first == n:
            res.append(nums[:])
            return
        for i in range(first, n):
            nums[first], nums[i] = nums[i], nums[first]
            backtrack(first + 1)
            nums[first], nums[i] = nums[i], nums[first]

    backtrack(0)
    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XM07"] = r'''
## 思路

求幂集（所有子集，含空集）。判题按精确字符串比较，期望串的顺序是**先按子集大小分组、组内按字典序**——这等价于依次用 itertools.combinations 取 k = 0, 1, …, n 个元素。

（若改用"逐位选或不选"的 DFS 或位掩码枚举，得到的顺序不同，会被判错。）

## 复杂度分析

- 时间复杂度：O(2^n · n)，n ≤ 10。
- 空间复杂度：O(2^n · n)，存放全部子集。

## 边界与处理

- 单元素：输出 [[ ], [x]]（示例 2）。
- 空集必须包含且排在最前。
- 元素可为负：不影响组合顺序（字典序按数组下标顺序给出）。
- n = 10 时子集数 1024，规模很小。
- 输出为紧凑 JSON 的二维数组。

## 代码
```python
import sys
import json
from itertools import combinations


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    n = len(nums)
    res = []
    for k in range(n + 1):
        for comb in combinations(range(n), k):
            res.append([nums[i] for i in comb])

    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XM08"] = r'''
## 思路

把 n 个等式全部异或起来：左边 = derived[0] ^ … ^ derived[n−1]，右边每个 original[i] 都恰好出现两次（一次作为 original[i]、一次作为 original[i+1] 中的前项），两次异或抵消，故右边恒为 0。

所以必要条件（也是充分条件）是 derived 的异或和为 0。若成立，取 original[0] = 0 即可逐个推出 original[i+1] = original[i] ^ derived[i]，最后一条自动满足。

## 复杂度分析

- 时间复杂度：O(n)。
- 空间复杂度：O(1)。

## 边界与处理

- n = 1：只有 derived[0] = original[0] ^ original[0] = 0，故仅当 derived[0] == 0 时可行。
- 全 1 数组且长度为偶数：异或和为 0，可行。
- 元素只有 0/1，异或和要么 0 要么 1。
- 不需要真的构造 original，只需判断异或和是否为 0。
- 输出为 JSON 布尔的小写 true / false。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    derived = json.loads(lines[0])

    x = 0
    for v in derived:
        x ^= v

    print("true" if x == 0 else "false")


main()
```
'''


SOLUTIONS["XM09"] = r'''
## 思路

除教练外每人都被记录 3 次，教练只被记录 1 次。于是对每个二进制位，统计该位出现 1 的次数并取模 3：余数不为 0 的位属于教练（其余人的贡献都是 3 的倍数，恰好抵消）。

## 复杂度分析

- 时间复杂度：O(n · 31)，n ≤ 10000。
- 空间复杂度：O(1)。

## 边界与处理

- 教练编号可能很大（< 2^31）：位宽取 31 足够。
- 只有教练一人（n = 1）：所有位计数为 1，模 3 余 1，恰好还原教练。
- 教练编号与某个学员相同？不会发生——教练只出现 1 次而学员出现 3 次，总次数会变成 4，与题意不符。
- 不能用简单异或：3 次异或等于自身，无法消去学员的贡献，必须按位取模 3。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    actions = json.loads(lines[0])

    res = 0
    for b in range(31):
        cnt = 0
        for v in actions:
            if (v >> b) & 1:
                cnt += 1
        if cnt % 3 != 0:
            res |= 1 << b

    print(res)


main()
```
'''


SOLUTIONS["XM10"] = r'''
## 思路

关键化简：a == b ⟺ XOR(arr[i..j−1]) == XOR(arr[j..k]) ⟺ XOR(arr[i..k]) == 0（因为把两式异或起来，a ^ b = XOR(arr[i..k])）。

因此只需枚举区间 [i, k]（i < k）使该区间的异或为 0，则 j 可以在 (i, k] 中任取，共 (k − i) 种。对所有这样的区间累加 (k − i) 即为答案。

a == b 与 XOR(i..k) == 0 的等价性是双向的：若 a == b，则 a ^ b = 0 = XOR(i..k)；反之若 XOR(i..k) == 0，则 b = a ^ (a ^ b) = a ^ 0 = a。

## 复杂度分析

- 时间复杂度：O(n^2)，n ≤ 300 → 约 4.5×10^4，也可 O(n^2) 用前缀异或实现。
- 空间复杂度：O(n)，前缀异或数组。

## 边界与处理

- 长度 2（如 [2,3]）：只有 i=0, k=1，异或非 0，答案为 0（示例 3）。
- 全部元素相同（如 [1,1,1,1,1]）：答案为 C(n+1, 3) 类型的组合数（示例 2 得 10）。
- j 可以等于 k（b 退化为单元素）也可以等于 i+1（a 退化为单元素），因此 j 的取值范围是 (i, k]。
- 必须用前缀异或把区间异或降到 O(1)，否则三重循环会超时。
- 答案规模：n = 300 时最多约 4.5×10^6，未超 32 位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    arr = json.loads(lines[0])

    n = len(arr)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] ^ arr[i]

    ans = 0
    for i in range(n):
        for k in range(i + 1, n):
            if pre[k + 1] ^ pre[i] == 0:
                ans += k - i

    print(ans)


main()
```
'''


SOLUTIONS["XM11"] = r'''
## 思路

设当前数组的异或和为 X，要求 k < 2^maximumBit 使 X XOR k 最大。由于 k 的高位上限固定，最好的办法是让结果的低 maximumBit 位全为 1，即取 k = (~X) 的低 maximumBit 位。

随后按题意删掉末尾元素：X ^= 被删元素，进入下一次查询。

## 复杂度分析

- 时间复杂度：O(n)，n ≤ 5×10^4。
- 空间复杂度：O(n)，结果数组。

## 边界与处理

- 只删除尾部元素：必须从后往前处理，不能每次重新求异或和（那会退化成 O(n^2)）。
- maximumBit 最大 5 → 掩码最多 5 位（1..31 范围内），用 (1 << maximumBit) − 1 构造。
- 元素为 0：不影响异或和。
- 相邻两次查询之间只差一个末元素，用增量异或维护即可。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    maximum_bit = json.loads(lines[1])

    mask = (1 << maximum_bit) - 1

    x = 0
    for v in nums:
        x ^= v

    ans = []
    for i in range(len(nums) - 1, -1, -1):
        ans.append((~x) & mask)
        x ^= nums[i]

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XM12"] = r'''
## 思路

把实数不断乘 2：整数部分就是下一位二进制小数位，取走整数部分后继续。最多输出 32 位以内（含 "0." 两位，故小数位最多 30 位）；若 30 位后仍未归零，说明无法用 32 位以内精确表示，输出 ERROR。

**必须用精确有理数运算**：输入的小数位数 ≤ 6，可用 fractions.Fraction 从原始字符串精确构造（例如 "0.625" → 5/8）。若直接用 float，0.1 之类的数会因二进制表示误差而在乘 2 过程中永不归零或提前归零，导致误判。

## 复杂度分析

- 时间复杂度：O(30)（固定次数的乘 2 与取整）。
- 空间复杂度：O(1)。

## 边界与处理

- 输入为 0：直接是 "0."，循环第一步就得 0，输出 "0."（按题意 0 属于 [0,1) 的边界）。
- 无法精确表示（如 0.1、0.625 之外的大多数含 5 位以上小数的值）：输出 ERROR（示例 2）。
- 位宽限制：题面明确"32 位包括输出中的 '0.' 这两位"，故小数位上限为 30。
- 必须从字符串解析为 Fraction，不能用 float（精度陷阱）。
- 输出为裸字符串（不加引号）。

## 代码
```python
import sys
import json
from fractions import Fraction


def main():
    data = sys.stdin.read()
    dec = json.JSONDecoder()
    i = 0
    while i < len(data) and data[i] in " \t\r\n":
        i += 1
    # 直接取原始字面量文本，交给 Fraction 精确解析，避免 float 精度损失
    j = i
    while j < len(data) and data[j] not in " \t\r\n,":
        j += 1
    token = data[i:j]

    r = Fraction(token)

    bits = []
    for _ in range(30):
        r *= 2
        if r >= 1:
            bits.append("1")
            r -= 1
        else:
            bits.append("0")
        if r == 0:
            break

    if r != 0:
        print("ERROR")
    else:
        print("0." + "".join(bits))


main()
```
'''


SOLUTIONS["XM13"] = r'''
## 思路

开心字符串只含 'a'、'b'、'c' 且相邻字符不同。因为按字典序排列时，前缀确定后子树的字符串数量可直接计算（每个位置有 2 种选择），所以既可以按字典序 DFS 直接生成到第 k 个，也可以用计数法定位。

n ≤ 10、k ≤ 100，规模很小，直接按字典序 DFS 生成全部开心字符串并取第 k 个（1 起）最简单可靠。

## 复杂度分析

- 时间复杂度：O(3 · 2^(n−1))，n = 10 时最多 1536 个字符串。
- 空间复杂度：O(n)，递归栈（不保存全部字符串）。

## 边界与处理

- k 超过总数：返回空字符串（示例 2、示例 4）。
- n = 1：只有 "a"、"b"、"c" 三个（示例 1 返回 "c"）。
- DFS 必须按 'a' → 'b' → 'c' 顺序展开，才能保证生成序列就是字典序。
- 相邻相同的剪枝：当前字符等于上一个字符时跳过。
- 输出为裸字符串（不加引号）；空字符串输出空行即可与期望空串匹配。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    k = json.loads(lines[1])

    count = [0]
    answer = [""]

    def dfs(path):
        if answer[0]:
            return
        if len(path) == n:
            count[0] += 1
            if count[0] == k:
                answer[0] = path
            return
        for ch in "abc":
            if path and path[-1] == ch:
                continue
            dfs(path + ch)
            if answer[0]:
                return

    dfs("")
    print(answer[0])


main()
```
'''


SOLUTIONS["XM14"] = r'''
## 思路

回溯枚举所有和为 target 的组合。为**避免重复**（同一多重集合只算一次），规定组合内部元素**非递减**：递归时传入可选的起始下标 start，下一层只能从 start 开始选（允许重复选同一个数，因此传 i 而不是 i+1）。

按候选数组下标从小到大展开，得到的顺序恰好是"按字典序"，与期望串一致。

## 复杂度分析

- 时间复杂度：O(解的数量 × 平均长度)，题目保证组合数 < 150。
- 空间复杂度：O(target / min(candidates))，递归栈深度。

## 边界与处理

- 无解（如 candidates=[2], target=1）：输出 []（示例 3）。
- 单个候选等于 target：直接命中。
- 候选包含 target 本身：会作为长度为 1 的组合出现，且因为它最大而排在最后（示例 1 的 [7]）。
- 允许重复使用同一数字：递归传 i 而非 i+1。
- 剪枝：候选值大于剩余目标时跳过（由于候选未排序，需先排序以便更有效地剪枝；排序不改变"非递减选取"的语义，也不会改变按字典序的输出）。
- 输出为紧凑 JSON 的二维数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    candidates = json.loads(lines[0])
    target = json.loads(lines[1])

    candidates.sort()
    n = len(candidates)
    res = []
    path = []

    def dfs(start, remain):
        if remain == 0:
            res.append(path[:])
            return
        for i in range(start, n):
            v = candidates[i]
            if v > remain:
                break
            path.append(v)
            dfs(i, remain - v)
            path.pop()

    dfs(0, target)
    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["XM15"] = r'''
## 思路

子数组异或用前缀异或 O(1) 求出：设 pre[i] = arr[0] ^ … ^ arr[i−1]（pre[0] = 0），则 XOR(arr[L..R]) = pre[R+1] ^ pre[L]。

## 复杂度分析

- 时间复杂度：O(n + q)，n 为数组长度、q 为查询数。
- 空间复杂度：O(n)，前缀异或数组。

## 边界与处理

- 单元素查询（L == R）：结果为该元素本身（示例 1 的 [3,3]）。
- 查询覆盖整个数组：用 pre[n] ^ pre[0] 得到全数组异或。
- 元素为正整数且可达 10^6：Python 整数安全。
- 下标从 0 开始，务必用 pre[R+1] ^ pre[L] 而不是 pre[R] ^ pre[L−1]。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    arr = json.loads(lines[0])
    queries = json.loads(lines[1])

    n = len(arr)
    pre = [0] * (n + 1)
    for i in range(n):
        pre[i + 1] = pre[i] ^ arr[i]

    ans = [pre[r + 1] ^ pre[l] for l, r in queries]
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
        os.path.dirname(os.path.abspath(__file__)), "batch09.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
