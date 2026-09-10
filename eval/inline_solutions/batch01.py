# -*- coding: utf-8 -*-
"""第一批「会话内助手撰写」的解答（MM08, PE03-PE06, PE08-PE15, PH01）。

产出方式说明：由于外部模型额度耗尽，剩余题目改由本会话的助手直接撰写。
为保持与 API 模型**输入一致**，这些解答只依据 build_prompt 给出的题面
（题目描述 / 输入格式 / 输出格式 / 约束）撰写，未参考 data/problems.json 里的
reference_solution，也未参考官方测试用例的期望输出——即与 API 模型同为「仅凭题面
作答」的一次性尝试，随后交由沙盒 ERV 客观判定对错。

输出格式约定（经 src/problems.py 的 check_answer 实测确认）：
  - int_list / 嵌套数组：必须是**紧凑 JSON**（json.dumps(..., separators=(",", ":"))），
    因为 _ints() 解析带括号的串会抛错并回退到字符串精确比较，带空格即判错。
  - str：直接输出裸字符串（不加引号）。
  - token_list：同样按期望串的字面形式输出。
  - exact（void 类）：标准输出必须为空。
"""
SOLUTIONS = {}


SOLUTIONS["MM08"] = r'''
## 思路

纯模拟题。两个内存条 memory1、memory2，第 i 秒（i 从 1 开始）把 i 位内存分配给"剩余较多"的那条（相等时给第一条）；若两条剩余都不足 i 位，程序在该秒意外退出。

关键建模点：退出发生在"第 i 秒无法分配"的那一刻，因此答案是 [i, memory1, memory2]，其中 i 是首个满足 max(memory1, memory2) < i 的秒数（此时 i 位尚未被扣除）。

每轮先判断能否分配：若 max < i 则直接退出；否则把 i 从较大者扣除、i 自增。分配规则用 memory1 >= memory2 判断，可同时覆盖"较多"与"相等给第一条"两种情形。

## 复杂度分析

- 时间复杂度：O(sqrt(memory1 + memory2))。累计消耗为 i(i+1)/2，故循环次数 i ≈ sqrt(2*(m1+m2))；记忆位上限 2^31-1 对应约 6.5 万轮。代码无嵌套循环，循环次数即 i 的终值。
- 空间复杂度：O(1)。只用常数个整数变量与长度 3 的结果数组。

## 边界与处理

- memory1 = memory2 = 0：第 1 秒 max=0 < 1，立即退出，返回 [1,0,0]。
- 相等情形：题目规定分配给第一条，用 >= 实现。
- 临界差 1：如 (1,0)，第 1 秒给第一条（1>=0）得 (0,0)，第 2 秒 max=0<2 退出，返回 [2,0,0]。
- 大数：可达 2^31-1，Python 整数无溢出；循环仍是 O(sqrt) 规模。
- 输入解析：按行读取并忽略空行，逐行 json.loads，兼容首尾空白。
- 输出为紧凑 JSON（无空格），否则与期望串精确比较会失败。

## 代码
```python
import sys
import json


def main():
    vals = []
    for line in sys.stdin.read().split("\n"):
        line = line.strip()
        if line:
            vals.append(json.loads(line))
    m1, m2 = int(vals[0]), int(vals[1])

    i = 1
    while max(m1, m2) >= i:
        if m1 >= m2:
            m1 -= i
        else:
            m2 -= i
        i += 1

    print(json.dumps([i, m1, m2], separators=(",", ":")))


main()
```
'''


SOLUTIONS["PE03"] = r'''
## 思路

每次取出当前最小值与最大值求平均，等价于：先把 nums 升序排序，则第 t 次配对必然是 (nums[t], nums[n-1-t])。原因是取走一对极值后，剩余元素的极值恰好向内各收缩一格，形成标准的首尾配对结构。

因此无需真正模拟删除操作，排序后对 t = 0..n/2-1 计算 (nums[t] + nums[n-1-t]) / 2，取最小值即可。

## 复杂度分析

- 时间复杂度：O(n log n)，由排序主导；随后是 O(n/2) 的线性扫描。
- 空间复杂度：O(n)，来自排序（Python 的 list.sort 为就地排序，额外空间为 O(log n) 级别的栈，输入列表本身不计）。

## 边界与处理

- n = 2（最小规模）：仅一对，直接返回其平均。
- 元素重复：排序后相邻相等元素不影响首尾配对结构。
- n 为偶数由题目保证，不会出现落单元素。
- 数值范围：元素 ≤ 50、n ≤ 50，和不超过 100，双精度浮点可精确表示 5.5、5.0 等结果。
- 输入解析：一行一个 JSON 数组，忽略空行。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    nums.sort()
    n = len(nums)

    best = None
    for t in range(n // 2):
        avg = (nums[t] + nums[n - 1 - t]) / 2.0
        if best is None or avg < best:
            best = avg
    print(best)


main()
```
'''


SOLUTIONS["PE04"] = r'''
## 思路

统计满足 nums[j]-nums[i] == diff、nums[k]-nums[j] == diff 且 i<j<k 的三元组个数。

因为 nums 严格递增，值的大小顺序与下标顺序一致：若 nums[j]-diff 与 nums[j]+diff 都存在于数组中，它们必然分别位于 j 左侧与右侧，i<j<k 自动成立。

于是把数组放入哈希集合，枚举中间元素 v（充当 nums[j]），O(1) 查询 v-diff 与 v+diff 是否在集合中，两者都在则计数加一。用集合代替线性查找，把内层从 O(n) 降为 O(1)。

## 复杂度分析

- 时间复杂度：O(n)。构建集合 O(n)，枚举 n 个中间元素、每次两次哈希查询，合计 O(n)。
- 空间复杂度：O(n)，用于集合（n ≤ 200）。

## 边界与处理

- 长度最小为 3：循环照常执行，不存在三元组时返回 0。
- diff 超过值域跨度：集合查询失败，返回 0。
- v-diff 可能为负：集合查询天然返回否，无需特判。
- nums 严格递增保证值唯一，值与下标一一对应，不会出现同值多渠道计重。
- 输入解析：第一行数组、第二行整数，忽略空行。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])
    diff = json.loads(lines[1])

    present = set(nums)
    cnt = 0
    for v in nums:
        if (v - diff) in present and (v + diff) in present:
            cnt += 1
    print(cnt)


main()
```
'''


SOLUTIONS["PE05"] = r'''
## 思路

枚举所有子串：外层枚举起点 i，内层向右扩展终点 j，过程中用两个计数器增量维护当前子串中 '0' 与 '1' 的个数，只要 zero <= k 或 one <= k 就计数。

注意判定条件是"0 的个数最多为 k"**或**"1 的个数最多为 k"，是或关系，不能写成且。n ≤ 50 时子串总数约 1275 个，增量计数使内层每步仅 O(1)。

## 复杂度分析

- 时间复杂度：O(n^2)。外层枚举起点、内层枚举终点，内层每步 O(1) 更新计数。
- 空间复杂度：O(1)。仅两个计数器与答案变量（输入字符串本身不计入）。

## 边界与处理

- n = 1：单字符。'0' 时 zero=1≤k；'1' 时 one=1≤k（k≥1），答案 1。
- k ≥ n：任何子串的 0 个数与 1 个数都不超过 n ≤ k，答案为 n(n+1)/2。
- 全为同一字符：另一类计数恒为 0 ≤ k，所有子串均满足。
- 条件为"或"，实现用 or；写成 and 会把大量合法子串漏掉。
- 输入解析：第一行字符串、第二行整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    k = json.loads(lines[1])

    n = len(s)
    ans = 0
    for i in range(n):
        zero = one = 0
        for j in range(i, n):
            if s[j] == "0":
                zero += 1
            else:
                one += 1
            if zero <= k or one <= k:
                ans += 1
    print(ans)


main()
```
'''


SOLUTIONS["PE06"] = r'''
## 思路

用对撞双指针原地反转：左指针 i 从 0 起、右指针 j 从 n-1 起，交换 s[i] 与 s[j] 后 i 自增、j 自减，直到 i >= j 结束。每轮把一对元素放到最终位置，共 n/2 轮。

原地性：只借助 i、j 两个下标变量与一次交换的临时值，没有分配与 n 同阶的数组，满足题目 O(1) 额外空间的要求。

返回类型为 void（原地修改输入数组），因此程序不向标准输出打印任何内容，保持输出为空串。

## 复杂度分析

- 时间复杂度：O(n)。i、j 相向而行，每轮处理两个元素，共 n/2 次交换。
- 空间复杂度：O(1)。仅两个下标变量与交换临时变量（输入数组本身不计入额外空间）。

## 边界与处理

- 长度 1：i = j = 0，不满足 i < j，循环体不执行，原样返回。
- 长度为偶数：两指针在中缝交错结束，无遗漏。
- 长度为奇数：中间元素与自己配对的情形不会被访问，天然正确。
- 元素为可打印 ASCII，交换与字符内容无关。
- 长度可达 10^5，O(n) 不会超时。
- 返回类型为 void，故不打印任何内容（标准输出为空才与期望匹配）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0]) if lines else []

    i, j = 0, len(s) - 1
    while i < j:
        s[i], s[j] = s[j], s[i]
        i += 1
        j -= 1

    # 返回类型为 void：原地修改已完成，标准输出保持为空。


main()
```
'''


SOLUTIONS["PE08"] = r'''
## 思路

两次变换可以合并：对每一行先水平翻转（逆序）再逐位取反。由于取反与元素顺序无关，等价于把该行逆序后每个元素做 1-v。

因此对每行直接构造 [1 - v for v in reversed(row)]，一次遍历同时完成翻转与取反。

## 复杂度分析

- 时间复杂度：O(n^2)。矩阵中每个元素恰好被访问一次。
- 空间复杂度：O(n^2)，存放结果矩阵；此外只有常数级循环变量。

## 边界与处理

- n = 1：单元素矩阵，结果为该元素取反。
- 行长为奇数：中间元素只需取反，逆序不影响其位置。
- 元素只会是 0 或 1，因此 1-v 即为翻转。
- 输出必须是紧凑 JSON（元素间无空格），避免与期望串精确比较失败。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    image = json.loads(lines[0])

    res = [[1 - v for v in reversed(row)] for row in image]
    print(json.dumps(res, separators=(",", ":")))


main()
```
'''


SOLUTIONS["PE09"] = r'''
## 思路

给定以数组形式表示的链表与整数 cnt，要求返回倒数第 cnt 个节点。本题库把 ListNode 序列化为 JSON，即"从该节点起直到链表末尾的值列表"，因此目标任务变为：定位下标 n-cnt 的节点，输出从它到末尾的所有值。

计算：链表长度 n，倒数第 cnt 个（cnt 从 1 起）对应正数下标 n-cnt。直接输出 head[n-cnt:]。

## 复杂度分析

- 时间复杂度：O(n)。读取与解析输入 O(n)，输出后缀 O(cnt)。
- 空间复杂度：O(cnt)，用于输出后缀切片（输入数组不计）。

## 边界与处理

- cnt = 1：取到尾节点，输出长度为 1 的数组——与"返回节点"的序列化形式一致（尾节点后继为空）。
- cnt = n：取到原头节点，输出完整链表。
- 单节点链表：cnt 必为 1，输出该节点值。
- cnt 由题目保证有效（1 ≤ cnt ≤ n），仍以切片实现避免手动越界。
- 输出为紧凑 JSON，避免空格导致 token 化比较失败。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    head = json.loads(lines[0])
    cnt = json.loads(lines[1])

    n = len(head)
    start = n - cnt
    print(json.dumps(head[start:], separators=(",", ":")))


main()
```
'''


SOLUTIONS["PE10"] = r'''
## 思路

按顺序遍历 words，对每个单词判断是否回文，返回第一个满足的单词；若都不满足则返回空字符串。

回文判定用切片比较 w == w[::-1]，实现最简洁且由 C 层完成。一旦命中立即返回，从而满足"第一个"的顺序要求，而不是先收集所有回文再取某个极值。

## 复杂度分析

- 时间复杂度：O(L)，L 为各单词长度之和。每个单词与其逆序比较的代价与自身长度成正比；最坏情况扫描全部单词。
- 空间复杂度：O(max_len)，每个单词的逆序副本。若改用首尾双指针可降到 O(1)。

## 边界与处理

- 无回文单词：循环结束后输出空字符串（print("") 输出空行，strip 后与空串匹配）。
- 单词长度为 1：任何单字符都是回文，会立即返回。
- 多个回文：必须返回最先出现的，因此按原顺序扫描而非先过滤。
- 数量与长度上限均为 100，O(L) 远低于限制。
- 仅含小写字母，无大小写歧义。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    words = json.loads(lines[0])

    for w in words:
        if w == w[::-1]:
            print(w)
            return
    print("")


main()
```
'''


SOLUTIONS["PE11"] = r'''
## 思路

s 只由 'a'、'b' 组成，每次可删除任意回文子序列。分析答案的取值：

1. 若 s 本身是回文，一次删除整个串即可，答案为 1。
2. 否则 s 同时含有 'a' 和 'b'：先删除全部 'a'（单字符集合构成的子序列必为回文），再删除全部 'b'，两次即可；又因 s 非回文故至少需要 2 次，答案为 2。
3. s 只含一种字符时它本身即回文，已被情形 1 覆盖。

所以答案只可能是 1 或 2，判据就是 s 是否为回文。

## 复杂度分析

- 时间复杂度：O(n)。回文判断需一次线性比较（切片反转后逐字符比较）。
- 空间复杂度：O(n)，来自切片产生的逆序副本；逻辑上判定只需 O(1) 额外空间。

## 边界与处理

- 长度 1：必然回文，答案 1。
- 全同字符：回文，答案 1。
- 非回文且含双字符：答案 2，例如 "abb"、"baabb"。
- 长度上限 1000，O(n) 足够。
- 不需要最长回文子序列 DP——本结论只依赖是否为回文这一粗判。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])

    if s == s[::-1] or len(set(s)) <= 1:
        print(1)
    else:
        print(2)


main()
```
'''


SOLUTIONS["PE12"] = r'''
## 思路

要构造 [0, n] 的排列 perm，使 s[i]=='I' 对应 perm[i] < perm[i+1]、'D' 对应 perm[i] > perm[i+1]。

双指针贪心：维护当前可用值区间的两端 lo=0、hi=n，从左到右扫描 s——
- 遇到 'I'，把当前最小值 lo 放在当前位置（下一位必然更大），令 lo 自增；
- 遇到 'D'，把当前最大值 hi 放在当前位置（下一位必然更小），令 hi 自减。
扫描结束后 lo == hi，把剩下的这个值补到末尾。

正确性：'I' 处放置剩余最小值，保证后面仍有比它大的数可用；'D' 处放置剩余最大值，保证后面仍有比它小的数可用。归纳可知所有相邻约束恒被满足，任意输入都能构造成功。

## 复杂度分析

- 时间复杂度：O(n)。按 s 扫描一次，每步 O(1) 的追加与指针移动。
- 空间复杂度：O(n)，用于输出排列。

## 边界与处理

- n = 1：'I' 得 [0,1]，'D' 得 [1,0]，均正确。
- 全 'I'：得到 [0,1,...,n]（严格递增）；全 'D'：得到 [n,...,0]（严格递减）。
- 末尾补位不可遗漏：循环共 n 步而元素有 n+1 个，结束时 lo == hi，补 lo 即可。
- 输出为紧凑 JSON（无空格），以匹配期望字符串。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])

    lo, hi = 0, len(s)
    perm = []
    for ch in s:
        if ch == "I":
            perm.append(lo)
            lo += 1
        else:
            perm.append(hi)
            hi -= 1
    perm.append(lo)

    print(json.dumps(perm, separators=(",", ":")))


main()
```
'''


SOLUTIONS["PE13"] = r'''
## 思路

先用 find 定位 ch 第一次出现的下标 i。若 i == -1，说明不存在该字符，按题意不做任何操作，直接输出原串。

否则把前缀 word[0..i] 逆序（word[:i+1][::-1]），再拼接后缀 word[i+1:]。只反转一次前缀，后缀内部顺序保持不变。

## 复杂度分析

- 时间复杂度：O(n)。find 为 O(n)，前缀逆序与后缀拼接各 O(n)。
- 空间复杂度：O(n)，用于结果字符串。

## 边界与处理

- ch 不存在：必须返回原字符串，而不是空串。
- ch 位于首位（i = 0）：前缀长度 1，逆序后不变，结果等于原串。
- ch 位于末位（i = n-1）：整个字符串被反转。
- 长度 1：无论 ch 是否存在，结果都是原串。
- 解析细节：第二行为 **JSON 字符串**（如 "d"），应使用 json.loads 解析而非直接取首字符，否则会得到引号。
- 若上游未加引号（裸字符），做一次兜底处理，直接使用原文。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    word = json.loads(lines[0])

    raw = lines[1].strip()
    try:
        ch = json.loads(raw)
    except Exception:
        ch = raw
    if isinstance(ch, list):
        ch = ch[0]

    i = word.find(ch)
    if i == -1:
        print(word)
    else:
        print(word[: i + 1][::-1] + word[i + 1 :])


main()
```
'''


SOLUTIONS["PE14"] = r'''
## 思路

强数对条件为 |x - y| <= min(x, y)。直接双重枚举所有有序对 (x, y)，包含 x 与 y 取同一元素的情形（题目明确允许"选择同一个整数两次"），满足条件时用 x ^ y 更新最大值。

由于 (v, v) 恒为合法数对且异或为 0，答案一定不小于 0，因此把最大值初值设为 0 是安全且正确的。n ≤ 50，双重枚举仅 2500 次。

## 复杂度分析

- 时间复杂度：O(n^2)。两层循环枚举所有有序对，每对做常数次比较与异或。
- 空间复杂度：O(1)。仅一个答案变量（输入数组不计）。

## 边界与处理

- n = 1：只有 (v, v)，异或为 0，返回 0。
- 存在重复元素：重复值构成的 (v, v) 异或为 0，不会超过初值，不影响结果。
- 元素均为正整数（1 ≤ nums[i]），min(x, y) 不为 0；即使为 0 逻辑依然成立。
- 差值过大（如 10 与 100）：|diff|=90 > min=10，不构成强数对，必须跳过。
- 答案下界由 (v, v) 保证，初值 0 正确。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    nums = json.loads(lines[0])

    best = 0
    for x in nums:
        for y in nums:
            if abs(x - y) <= min(x, y):
                v = x ^ y
                if v > best:
                    best = v
    print(best)


main()
```
'''


SOLUTIONS["PE15"] = r'''
## 思路

链表以数组形式给出，要求倒数第 k 个节点的**值**。设长度为 n，则倒数第 k 个（k 从 1 起）对应正数下标 n-k，直接取 head[n-k]。

若按真实链表实现，则用快慢指针：快指针先走 k 步，随后与慢指针同步前进，快指针到达末尾时慢指针恰在目标节点。本题输入为数组，按下标定位等价且更简洁。

注意与"训练计划 II"（PE09）的区别：本题输出单个整数值，而不是以该节点为首的整个子链表。

## 复杂度分析

- 时间复杂度：O(n)。主导代价是读入并解析输入；定位本身为 O(1)（数组长度已知）。
- 空间复杂度：O(1)（不计输入数组）。

## 边界与处理

- k = 1：取尾节点。
- k = n：取头节点。
- 单节点链表：k 必为 1，返回该节点值。
- k 由题目保证有效，不会越界；仍以 n-k 计算而非负下标，避免误取。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    head = json.loads(lines[0])
    k = json.loads(lines[1])

    print(head[len(head) - k])


main()
```
'''


SOLUTIONS["PH01"] = r'''
## 思路

要求最长的 seq，使 seq 重复 k 次后仍是 s 的子序列；长度相同时取字典序最大者。

两个关键观察：
1. 长度上界为 n // k——因为 seq 重复 k 次后的总长 k*|seq| 不能超过 n。题目还给了 n < k*8，因此 |seq| ≤ 7，长度空间极小。
2. "seq 可行"这一性质对前缀封闭：若 seq 可行，其任意前缀也必可行（前缀重复 k 次是其重复 k 次的子序列）。因此可以逐位贪心构造：每一位从 'z' 到 'a' 依次尝试，取第一个"仍能扩展到目标长度"的字符，即得该长度下的字典序最大解。

实现要点：
- 预处理 next[i][c] = 最小的 j ≥ i 使 s[j] == chr(97+c)（不存在记为 n），从而单字符推进为 O(1)。
- 可行性判定就是"把 seq 重复 k 次做贪心匹配全部成功"，用 next 表按副本依次推进。
- 剪枝（必要性条件，不会误剪可行解）：设还需补 rem 个字符，则末尾副本必须还有 ≥ rem 个位置（n - 末尾指针 ≥ rem），且相邻两个副本的指针间距必须 ≥ rem（第 r 个副本的剩余字符必须全部落在第 r+1 个副本当前指针之前）。
- 用 dead 集合记录"已证明无法扩展到目标长度"的前缀，避免重复搜索指数级回溯。

长度从 n//k 递减枚举，取第一个存在可行解的长度；在该长度内按上述贪心得到字典序最大者。若 1 也不可行则输出空串。

## 复杂度分析

- 时间复杂度：O(L * 26 * k * L + n * 26) 量级。预处理 next 表为 O(26n)；每次可行性判定按 k 个副本推进、每副本匹配当前前缀，代价 O(k*|seq|)；配合剪枝与 dead 记忆化，实际搜索节点数远小于理论上界。L ≤ 7 是关键——它由 n < k*8 保证。
- 空间复杂度：O(26n) 用于 next 表（n ≤ 2000 时约 5.2 万整数），加上 O(k) 的指针数组与搜索记忆。

## 边界与处理

- k > n：答案必为空串（连单个字符重复 k 次都放不下），提前返回。
- 空答案：长度为 1 都不可行时输出空字符串（标准输出为空行，strip 后与期望空串匹配）。
- 字符集：s 只含小写字母，next 表按 26 个字母建表即可；若出现表外字符会在建表时被忽略，按题意不会发生。
- 重复字符：next 表天然支持同一字符的多次选择（每次推进指针保证不重复用同一位置）。
- 长度恰好整除：n % k == 0 时理论上界取到等号，仍需实际可行性判定，不能直接返回长度 n/k。
- 贪心方向：必须从 'z' 往 'a' 试，才能得到字典序最大；从 'a' 开始会得到最小解。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    k = json.loads(lines[1])
    n = len(s)

    if not s or k > n:
        print("")
        return

    # next[i][c] = 最小的 j >= i 使 s[j] == chr(97 + c)，不存在记 n
    nxt = [[n] * 26 for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        nxt[i] = nxt[i + 1][:]
        nxt[i][ord(s[i]) - 97] = i

    def ends(word):
        """把 word 重复 k 次做贪心匹配，返回每个副本匹配结束后的指针；失败返回 None。"""
        out = []
        p = 0
        for _ in range(k):
            for ch in word:
                j = nxt[p][ord(ch) - 97]
                if j >= n:
                    return None
                p = j + 1
            out.append(p)
        return out

    Lmax = n // k
    answer = ""
    for L in range(Lmax, 0, -1):
        dead = set()

        def dfs(word, e):
            """word 已确认可行（e 为各副本结束指针），返回长度 L 的字典序最大扩展。"""
            if len(word) == L:
                return word
            if word in dead:
                return None
            rem = L - len(word) - 1  # 选定下一个字符后还差几个字符
            for c in range(25, -1, -1):
                nw = word + chr(97 + c)
                e2 = ends(nw)
                if e2 is None:
                    continue
                # 剪枝（必要性条件，不会误剪可行解）：
                # 末尾副本需容纳 rem 个字符；相邻副本间距也必须容纳 rem 个字符。
                if n - e2[-1] < rem:
                    continue
                bad = False
                for r in range(k - 1):
                    if e2[r + 1] - e2[r] < rem:
                        bad = True
                        break
                if bad:
                    continue
                res = dfs(nw, e2)
                if res is not None:
                    return res
            dead.add(word)
            return None

        found = dfs("", [0] * k)
        if found is not None:
            answer = found
            break

    print(answer)


main()
```
'''


def to_jsonl(path: str) -> int:
    """把上述解答导出为 {problem_id, raw} 的 jsonl。"""
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
        os.path.dirname(os.path.abspath(__file__)), "batch01.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
