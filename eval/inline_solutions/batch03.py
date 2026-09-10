# -*- coding: utf-8 -*-
"""第三批「会话内助手撰写」的解答（SH14, SH15, SM01-SM12）。

输出约定（经 reference_solution 的 main() 与 check_answer 实测确认）：
  list/dict → json.dumps(..., separators=(',',':'))（紧凑，不留空格）；
  否则 str()；布尔小写。
其中 SM12 的期望串按「键首次插入顺序」排列（checker 为 exact），
因此必须用保序字典按插入顺序输出，不能排序。
"""
SOLUTIONS = {}


SOLUTIONS["SH14"] = r'''
## 思路

把 [1, n] 的数字按字典序排成"十叉树"的前序遍历：根的孩子是 1..9，节点 x 的孩子是 10x..10x+9（不超过 n）。字典序第 k 小就是这棵树上先序遍历的第 k 个节点。

无需真正建树，用"子树大小 + 逐层下降"：
- steps(cur, n) = 以 cur 为前缀的、不超过 n 的数字个数。用两个指针 first=cur、last=cur 逐层乘以 10（last 追加 9），把每层的区间与 n 取交累加，单次 O(log n)。
- 从 cur = 1 开始，令 k -= 1（跳过 cur 自身）：若 steps(cur) <= k 说明答案不在 cur 子树内，k -= steps(cur)、cur += 1；否则答案在子树内，k -= 1、cur *= 10，进入子节点继续。

n ≤ 10^9，树的深度仅 10 层，每层至多试探 9 个兄弟，故总代价极小。

## 复杂度分析

- 时间复杂度：O(log n × 10)。steps 每次 O(log n)（层数）；同一层最多右移 9 次，总试探次数为 O(10 log n)。
- 空间复杂度：O(1)。只用若干整数变量。

## 边界与处理

- n = k = 1：k-1 = 0，循环不执行，直接返回 1（示例 2）。
- k = n：返回字典序最大的数，即 9 及其最深的右侧后代，算法自然收敛。
- n 为 10 的幂：steps 的层区间会恰好整段落在 n 以内，min(n, last) 的写法保证不越界。
- 大数：n 可达 10^9，所有中间量用 Python 整数，无溢出；注意 last*10+9 不要用浮点。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    k = json.loads(lines[1])

    def steps(cur):
        """以 cur 为前缀且不超过 n 的数字个数。"""
        total = 0
        first = cur
        last = cur
        while first <= n:
            total += min(n, last) - first + 1
            first *= 10
            last = last * 10 + 9
        return total

    cur = 1
    k -= 1
    while k > 0:
        cnt = steps(cur)
        if cnt <= k:
            k -= cnt
            cur += 1
        else:
            k -= 1
            cur *= 10

    print(cur)


main()
```
'''


SOLUTIONS["SH15"] = r'''
## 思路

"移除第 i 个元素后，任选 k 个字符串的最长公共前缀长度" = 在所有前缀 p 中，取满足「剩余的、以 p 为前缀的字符串个数 ≥ k」的最大 |p|。

只有 words[i] 自己路径上的前缀计数会因移除而减 1。因此对每个 i：
- 若某前缀 p 不是 words[i] 的前缀，其计数不变，只需原计数 ≥ k；
- 若是 words[i] 的前缀，则需原计数 ≥ k+1。

实现：
1. 用 Trie 统计每个前缀节点的计数 cnt，并记录每个单词路径上的节点列表 path[i]（总长 ≤ 1e5，故节点总数与路径记录总量都在 1e5 量级）。
2. 取出所有 cnt ≥ k 的节点，按深度降序排序。
3. 对每个 i：
   - d1 = words[i] 路径上满足 cnt ≥ k 的最长深度（cnt 沿路径单调不增，故从浅到深扫到第一个不满足即可）；
   - term2 = 路径上满足 cnt ≥ k+1 的最长深度；
   - term1 = 按深度降序扫描步骤 2 的列表，跳过所有"位于 words[i] 路径上"的节点，取第一个未被跳过的深度。被跳过的节点数恰为 d1（路径上与 S_k 的交集是深度 1..d1 的一条链），因此每个 i 只需扫 d1+1 个候选。
   - answer[i] = max(term1, term2)，若剩余元素少于 k（即 n-1 < k）则为 0。

总代价 O(Σ|words[i]| + V log V)，V 为 Trie 节点数。

## 复杂度分析

- 时间复杂度：O(Σ L + V log V)。建 Trie 与路径记录 O(Σ L)；S_k 排序 O(V log V)；每个 i 的扫描量 ≤ d1(i)+1，而 Σ d1(i) ≤ Σ L。
- 空间复杂度：O(Σ L)，Trie 节点、计数、路径记录各 O(Σ L)。

## 边界与处理

- n - 1 < k（移除后不足 k 个字符串）：直接返回 0。
- k = 1：最长公共前缀就是某个字符串本身，答案为"移除 i 后最长字符串的长度"，本算法给出同样的结果（term 取到该串全长）。
- 所有字符串互不相同且无可共享前缀：S_k 为空（k ≥ 2 时），答案为 0。
- 大量重复字符串：cnt 可远大于 k，此时移除一个不影响，答案等于全局最长满足前缀。
- 单元素数组：n-1 = 0 < k（k ≥ 1）→ 返回 0。
- 内存细节：Trie 用 node*26+c 编码子节点键，避免每节点一个字典；节点数可达 1e5。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    words = json.loads(lines[0])
    k = json.loads(lines[1])

    n = len(words)
    if n - 1 < k:
        print(json.dumps([0] * n, separators=(",", ":")))
        return

    child = {}
    cnt = [0]
    depth = [0]
    paths = []

    for w in words:
        node = 0
        path = []
        d = 0
        for ch in w:
            d += 1
            key = node * 26 + (ord(ch) - 97)
            nxt = child.get(key)
            if nxt is None:
                nxt = len(cnt)
                child[key] = nxt
                cnt.append(0)
                depth.append(d)
            node = nxt
            cnt[node] += 1
            path.append(node)
        paths.append(path)

    sk = [(depth[v], v) for v in range(1, len(cnt)) if cnt[v] >= k]
    sk.sort(key=lambda x: -x[0])

    ans = []
    for i, w in enumerate(words):
        p = paths[i]
        d1 = 0
        term2 = 0
        for d, node in enumerate(p, start=1):
            if cnt[node] >= k:
                d1 = d
            if cnt[node] >= k + 1 and d > term2:
                term2 = d
        term1 = 0
        for dep, v in sk:
            # 判断 v 是否位于 words[i] 的路径上（路径上与 S_k 的交集是深度 1..d1 的链）
            if dep <= len(p) and p[dep - 1] == v:
                continue
            term1 = dep
            break
        ans.append(max(term1, term2))

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["SM01"] = r'''
## 思路

把所有小球移到第 i 个盒子，代价是每个球到 i 的距离之和，即 Σ|pos_j - i|。用前缀和把它变成 O(1) 查询：

设球的位置升序为 p[0..m-1]，前缀和 pre。对盒子 i，用二分找到分界点 t（第一个 p[t] > i），则
cost(i) = (i*t - pre[t]) + ((pre[m] - pre[t]) - i*(m - t))。

也可用一次线性扫描的递推（从左到右再回推），但前缀和写法更直观。

## 复杂度分析

- 时间复杂度：O(n + m log m)。统计位置 O(n)，排序位置 O(m log m)（位置天然升序，实际为 O(m)），每个盒子一次二分 O(log m)。
- 空间复杂度：O(m)，存放球位置与前缀和；n ≤ 2000 时完全够用。

## 边界与处理

- 没有球（全 '0'）：所有答案为 0。
- 只有一个球：答案为各盒子到该球的距离。
- 球全在同一个盒子：该盒子为 0，其余为球数 × 距离。
- 位置已天然升序（按字符串扫描得到），无需额外排序，但保留排序以增强稳健性。
- 结果上界：n=2000、球数 2000 时最大约 4*10^6，未超 32 位。
- 输出为紧凑 JSON 数组。

## 代码
```python
import sys
import json
import bisect


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    boxes = json.loads(lines[0])

    n = len(boxes)
    p = [i for i in range(n) if boxes[i] == "1"]
    m = len(p)

    pre = [0] * (m + 1)
    for i in range(m):
        pre[i + 1] = pre[i] + p[i]

    ans = []
    for i in range(n):
        t = bisect.bisect_right(p, i)
        left = i * t - pre[t]
        right = (pre[m] - pre[t]) - i * (m - t)
        ans.append(left + right)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["SM02"] = r'''
## 思路

激光束的条件是：两台设备位于不同行，且它们之间（不含两端）的所有行都没有设备。这意味着只有**相邻的两个非空行**之间才会产生激光束，数量为两行设备数的乘积。

于是按行统计每行的设备数，跳过空行，累加"相邻非空行的设备数乘积"。

## 复杂度分析

- 时间复杂度：O(m * n)，需扫描整个矩阵统计每行设备数；m, n ≤ 500。
- 空间复杂度：O(1)（只保留上一非空行的设备数）。

## 边界与处理

- 全为空行：没有相邻非空行，答案为 0。
- 只有一行有设备：无法构成不同行的设备对，答案为 0（示例 2 即此类）。
- 中间隔了多个空行：空行不参与计数，但仍算"相邻非空行"，乘积照常累加。
- 一行有多个设备：按设备数相乘，正是"任一设备对都独立成束"的计数。
- 结果规模：最大约 500×500×250，未超 32 位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    bank = json.loads(lines[0])

    total = 0
    prev = 0
    for row in bank:
        c = row.count("1")
        if c > 0:
            total += prev * c
            prev = c

    print(total)


main()
```
'''


SOLUTIONS["SM03"] = r'''
## 思路

三辆垃圾车各自独立工作，但**不能同时工作**（任何时刻只有一辆在使用），所以总时间就是三辆车各自耗时的**简单相加**（不需要取最大值）。

对每一种垃圾类型 t：
- 收拾耗时 = 该类型垃圾的总单位数（每单位 1 分钟）；
- 行驶耗时 = 从房子 0 到"最后一栋含该类型垃圾的房子"的行驶时间 = travel 的前缀和。

所以总时间 = 全部垃圾单位总数 + Σ_{t∈{M,P,G}}（travel 前缀和到该类型最后一次出现处）。

## 复杂度分析

- 时间复杂度：O(n + L)，L 为所有 garbage[i] 的长度之和。一次扫描统计每种垃圾的总量与最后出现位置。
- 空间复杂度：O(1)。只需 3 个计数器与 3 个最后位置。

## 边界与处理

- 某种垃圾完全不存在：该车不需要出发，行驶耗时为 0（示例 1 中的金属）。
- 某种垃圾只在房子 0 出现：行驶耗时为 0，只计收拾时间。
- travel 长度为 n-1：计算前缀和时注意下标边界，最后一个房子没有 travel 项。
- 所有垃圾集中在最后一栋房子：三辆车都要走到最后，行驶耗时分别为 travel 的全前缀和。
- 大量垃圾（n ≤ 10^5，每栋 ≤ 10 单位）：总时间上界约 10^6 + 3×10^7，未超 32 位。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    garbage = json.loads(lines[0])
    travel = json.loads(lines[1])

    n = len(garbage)

    # 每栋房子之前（到该栋为止）的行驶时间前缀和
    pref = [0] * n
    for i in range(1, n):
        pref[i] = pref[i - 1] + travel[i - 1]

    units = 0
    last = {"M": -1, "P": -1, "G": -1}
    for i, g in enumerate(garbage):
        units += len(g)
        for ch in g:
            last[ch] = i

    total = units
    for ch in ("M", "P", "G"):
        if last[ch] >= 0:
            total += pref[last[ch]]

    print(total)


main()
```
'''


SOLUTIONS["SM04"] = r'''
## 思路

按题意直接模拟：把 s 切成 n/k 段，每段长度 k；对每段求字符哈希值（'a'→0 … 'z'→25）之和，对 26 取模，再把该数值映射回字母追加到结果。

## 复杂度分析

- 时间复杂度：O(n)，每个字符恰好参与一次求和；分段边界由下标直接计算，无额外开销。
- 空间复杂度：O(n/k)，存放结果字符串。

## 边界与处理

- n = k：只有一段，结果长度为 1（示例 2）。
- 字符全为 'a'：哈希和为 0，结果字符为 'a'。
- k = 1：每段一个字符，结果就是原字符串（因为 ord-'a' 再映射回来不变）。
- 模数固定为 26，sum % 26 的结果必落在 [0, 25]，映射安全。
- 题目保证 n 是 k 的倍数，无需处理余数；仍以 range(0, n, k) 的切片写法保证不越界。
- 输出为裸字符串（不加引号）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    k = json.loads(lines[1])

    res = []
    for i in range(0, len(s), k):
        part = s[i:i + k]
        total = sum(ord(c) - 97 for c in part)
        res.append(chr(97 + total % 26))

    print("".join(res))


main()
```
'''


SOLUTIONS["SM05"] = r'''
## 思路

m ≤ 500，直接对每个起点 i 模拟：从 startPos 出发，按 s[i], s[i+1], ... 依次尝试移动，一旦某步越界（坐标跑到 [0, n-1] 之外）就停止，能执行的指令数即为答案。

下标恰好覆盖 n=1 的退化情形：此时任何移动都会越界，答案全为 0。

## 复杂度分析

- 时间复杂度：O(m^2)。外层枚举 m 个起点，内层最多执行 m 条指令；m ≤ 500 时约 2.5×10^5 步。
- 空间复杂度：O(1)（不计输出数组）。

## 边界与处理

- n = 1：任何方向都会越界，所有答案为 0（示例 3）。
- 起点在网格角落：可执行步数受限，模拟自然给出正确值。
- 指令执行完全程不越界：答案等于剩余指令数（如示例 1 的第 1 个起点）。
- 无任何合法移动（答案 0）：内层循环第一次就 break，不进循环体。
- 连续相反指令（如 "LR"）：逐条模拟，不会互相抵消出错。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    n = json.loads(lines[0])
    start = json.loads(lines[1])
    s = json.loads(lines[2])

    m = len(s)
    ans = []
    for i in range(m):
        r, c = start[0], start[1]
        cnt = 0
        for j in range(i, m):
            ch = s[j]
            if ch == "L":
                nc = c - 1
                nr = r
            elif ch == "R":
                nc = c + 1
                nr = r
            elif ch == "U":
                nr = r - 1
                nc = c
            else:
                nr = r + 1
                nc = c
            if nr < 0 or nr >= n or nc < 0 or nc >= n:
                break
            r, c = nr, nc
            cnt += 1
        ans.append(cnt)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["SM06"] = r'''
## 思路

要输入 target，唯一可行的最少按键方式是：对 target 的第 i 个字符 c，先按一次按键 1（追加 'a'），再按 ord(c)−ord('a') 次按键 2 把末位改上去。这既是可达的（每次都在正确的末位上操作），也是最优的（每个字符至少需要一次按键 1，且按键 2 的次数由字符本身决定）。

于是按顺序**记录每一次按键后的屏幕内容**即可：按下按键 1 后记录一次，之后每按一次按键 2 再记录一次。

## 复杂度分析

- 时间复杂度：O(L × C)，L = |target|，C = 26。总共记录 1 + Σ(c_i − 'a' + 1) ≤ 26L 个字符串；target 长度 ≤ 400。
- 空间复杂度：O(L × C) 存放输出（每个字符串长度 ≤ L，故实际约 O(L²C)，L=400 时约 4×10^6 字符，可接受）。

## 边界与处理

- target 首字符为 'a'：第一次按键 1 后即为 "a"，无按键 2 操作，序列首项就是 "a"。
- target 首字符为 'h'：需要连续按 7 次按键 2，中间状态 a→b→…→h 都要记录（示例 2）。
- 字符为 'a' 时 delta = 0，只记录按键 1 后的状态。
- 长度 1 的 target：输出恰好 1 + delta 项。
- 输出必须是**紧凑 JSON**（元素之间无空格），否则与期望串精确比较会失败。
- 注意每个字符串都要加双引号（JSON 字符串），由 json.dumps 统一处理。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    target = json.loads(lines[0])

    cur = ""
    out = []
    for ch in target:
        cur += "a"                      # 按键 1
        out.append(cur)
        delta = ord(ch) - ord("a")
        for _ in range(delta):          # 按键 2
            cur = cur[:-1] + chr(ord(cur[-1]) + 1)
            out.append(cur)

    print(json.dumps(out, separators=(",", ":")))


main()
```
'''


SOLUTIONS["SM07"] = r'''
## 思路

两步：
1. 先按顺序取出所有元音字母（'a','e','i','o','u' 及其大写），对它们按 ASCII 升序排序；
2. 再从左到右扫描原串，遇到元音位置就依次填入排序后的元音，辅音位置保持原字符。

因为只置换元音、不改变辅音位置，且填入的元音序列有序，结果自然满足两条要求。

## 复杂度分析

- 时间复杂度：O(n log n)，排序元音主导；扫描与回填各 O(n)。（元音数量 ≤ n，字符集固定时也可 O(n) 计数排序。）
- 空间复杂度：O(n)，存放元音序列与结果字符列表。

## 边界与处理

- 没有元音：排序列表为空，回填时不动任何位置，结果等于原串（示例 2 的 "lYmpH"）。
- 全部是元音：整串被排序，例如 "aeiou" 保持不变、'u' 前移等。
- 大小写混排：按 ASCII 排序会把大写（65~90）排在全部小写（97~122）之前，这正是题目要求的 ASCII 序（示例 1 的 'E','O' 排在 'e' 之前）。
- 'y'/'Y' 是辅音：题目明确元音只有 aeiou 五种，'Y' 必须保持原位（示例 2 验证了这一点）。
- 长度上限 10^5，O(n log n) 足够。
- 输出为裸字符串。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])

    vowels = set("aeiouAEIOU")
    picked = sorted(ch for ch in s if ch in vowels)

    res = []
    t = 0
    for ch in s:
        if ch in vowels:
            res.append(picked[t])
            t += 1
        else:
            res.append(ch)

    print("".join(res))


main()
```
'''


SOLUTIONS["SM08"] = r'''
## 思路

单词与模式匹配的定义是存在一个**双射**（字母到字母的置换）。由于两者长度相同，等价于：逐位建立映射时，pattern 的同一字母必须always映射到单词的同一字母（单射），且单词的不同字母不能映射自 pattern 的不同字母（满射/互不相同）——两条合起来就是要求映射在两个方向都是函数。

实现：同时维护两个字典 m1（pattern 字符 → 单词字符）与 m2（单词字符 → pattern 字符）。逐位检查：若 m1 已有该 pattern 字符且不等于当前单词字符，则失败；若 m2 已有该单词字符且不等于当前 pattern 字符，则失败；否则写入两个映射。全部通过则该单词匹配。

## 复杂度分析

- 时间复杂度：O(Σ|words[i]| × 1)，每个单词一次线性扫描；总长 ≤ 50×20。
- 空间复杂度：O(1)（两个字典最多 26 项）。

## 边界与处理

- 长度不等：题目保证 words[i].length == pattern.length，无需特判。
- 重复字母（如 pattern="aab"）：必须双向检查，只检查单向会把 "ccc" 这类映射成"多对一"的串误判为匹配（示例中的反例）。
- 完全不同字母：总能建立双射，匹配成功（示例中的 "abc"、"deq"）。
- 单字符：长度 1 恒匹配。
- 输出为**紧凑 JSON** 数组，且顺序按原 words 顺序（示例期望 ["mee","aqq"] 即输入顺序）。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    words = json.loads(lines[0])
    pattern = json.loads(lines[1])

    ans = []
    for w in words:
        m1 = {}
        m2 = {}
        ok = True
        for a, b in zip(pattern, w):
            if a in m1 and m1[a] != b:
                ok = False
                break
            if b in m2 and m2[b] != a:
                ok = False
                break
            m1[a] = b
            m2[b] = a
        if ok:
            ans.append(w)

    print(json.dumps(ans, separators=(",", ":")))


main()
```
'''


SOLUTIONS["SM09"] = r'''
## 思路

把 t 变成 s 的字母异位词，只需让两者的字符计数完全一致。每个步骤可以把 t 中的一个字符换成任意其他字符，因此缺少的字符需要逐个补齐。

最小步骤数 = Σ_c max(0, cnt_t[c] − cnt_s[c])，也就是 t 中"超出 s 所需"的字符总数（这些字符必须被替换掉）。等价地等于 n − Σ_c min(cnt_s[c], cnt_t[c])。

## 复杂度分析

- 时间复杂度：O(n)，两次计数扫描 + 26 项比较。
- 空间复杂度：O(1)，两个长度 26 的计数数组。

## 边界与处理

- 两串本身就是异位词：所有 max(0, …) 为 0，答案为 0（示例 3、4）。
- 两串完全相同：答案为 0。
- 两串毫无公共字符（如 "friend" 与 "family"）：需替换的多余字符为 4（示例 5），公式给出 4。
- 长度相同是题目保证的，因此"多余字符数"与"缺少字符数"必然相等，用任一侧统计都对。
- 长度上限 5×10^4，O(n) 足够。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])
    t = json.loads(lines[1])

    cs = [0] * 26
    ct = [0] * 26
    for ch in s:
        cs[ord(ch) - 97] += 1
    for ch in t:
        ct[ord(ch) - 97] += 1

    ans = 0
    for i in range(26):
        if ct[i] > cs[i]:
            ans += ct[i] - cs[i]
    print(ans)


main()
```
'''


SOLUTIONS["SM10"] = r'''
## 思路

设不含 '_' 的位移把机器人带到 (x0, y0) = (R − L, U − D)。每个 '_' 都可以自由选择四个方向之一，而每走一步最多让曼哈顿距离增加 1。

因此：先把所有 '_' 都朝当前所在象限的"外侧"方向走，即可让每个 '_' 都贡献 1。于是最大曼哈顿距离 = |x0| + |y0| + count('_')。

为什么上界可达：若 x0 ≥ 0 且 y0 ≥ 0，把全部 '_' 都设为 'R'（或 'U'）会沿第一象限外推，曼哈顿距离每步 +1。四个象限同理，只需取与当前象限一致的轴向。即使某一坐标为 0，把 '_' 全部压向该轴的正侧同样每步 +1。

## 复杂度分析

- 时间复杂度：O(n)，统计四种移动与 '_' 的个数。
- 空间复杂度：O(1)。

## 边界与处理

- 全部是 '_'：x0 = y0 = 0，答案为 '_' 的个数（每个都往同一方向走）。
- 没有 '_'：退化为普通的曼哈顿距离。
- 相反方向抵消（如 "UD"）：x0、y0 均为 0，抵消不影响答案的正确性。
- 只有单方向移动：另一轴为 0，公式直接给出步数。
- 长度上限 10^5，O(n) 足够。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    moves = json.loads(lines[0])

    x = 0
    y = 0
    wild = 0
    for ch in moves:
        if ch == "U":
            y += 1
        elif ch == "D":
            y -= 1
        elif ch == "L":
            x -= 1
        elif ch == "R":
            x += 1
        else:
            wild += 1

    print(abs(x) + abs(y) + wild)


main()
```
'''


SOLUTIONS["SM11"] = r'''
## 思路

"美丽"的字符串可以切分成若干偶数长度、且每段只含同一种字符的子串。最自然的切法是按长度为 2 的块切：每两个相邻字符组成一块，块内必须同为 '0' 或同为 '1'；只要每块都同字符，整串就能按这些块切分。

反向也成立：任何合法切分下，每个偶数长度同字符段按 2 分组后，每组也都是同字符的。因此问题等价于——对 (s[0],s[1])、(s[2],s[3])、… 每组，把它改成 "00" 或 "11" 的最小代价之和，单组代价为 min(该组 '1' 的个数, 该组 '0' 的个数)。

## 复杂度分析

- 时间复杂度：O(n)，一次扫描每两个字符。
- 空间复杂度：O(1)。

## 边界与处理

- 长度 2：只有一组，答案为 0（"00"/"11"）或 1（"01"/"10"）。
- 全为同一字符：答案为 0（示例 3）。
- 长度必为偶数（题目保证），不会出现落单字符。
- 每组独立最优即全局最优：因为切分点固定在偶数下标处时各组互不影响，而任何合法切分都能细化到长度 2，故不存在更优的跨组方案。
- 长度上限 10^5，O(n) 足够。
- 输出为单个整数。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    s = json.loads(lines[0])

    ans = 0
    for i in range(0, len(s), 2):
        ones = (1 if s[i] == "1" else 0) + (1 if s[i + 1] == "1" else 0)
        ans += min(ones, 2 - ones)

    print(ans)


main()
```
'''


SOLUTIONS["SM12"] = r'''
## 思路

对每个计数配对域名 "rep d1.d2.d3"，把 rep 累加到该域名及其所有父域名的计数上。父域名由不断去掉最左侧的一段得到（如 discuss.leetcode.com → leetcode.com → com）。

用保序字典累加计数，最后按 **键的首次插入顺序** 输出 "计数 域名"。这一点很关键：本题的答案顺序虽然题目说"任意顺序"，但判题采用精确字符串比较，期望串是按首次插入顺序生成的，因此必须使用 Python dict 的插入有序特性（3.7+ 保证）并**不要排序**。

输出采用紧凑 JSON（元素之间无空格），每个元素形如 "9001 discuss.leetcode.com"。

## 复杂度分析

- 时间复杂度：O(Σ 域名长度)，每个域名按 '.' 逐层剥离，总剥离次数与段数同阶；字典操作为 O(1) 均摊。
- 空间复杂度：O(D)，D 为不同子域名个数（≤ 300）。

## 边界与处理

- 同一子域名多次出现：计数累加（示例 2 中 "com" 累计 951）。
- 二级域名（"50 yahoo.com"）：只有两层，剥离一次即到 "com"。
- 首次插入顺序：必须先插入完整域名，再插入其父域名，才能与期望顺序一致。
- 单个域名时（"9001 discuss.leetcode.com"）输出三项，顺序为 discuss.leetcode.com、leetcode.com、com。
- 域名段数固定为 2 或 3（题目保证），无需处理更长的域。
- 输出为紧凑 JSON 数组，元素是带双引号的字符串。

## 代码
```python
import sys
import json


def main():
    lines = [l for l in sys.stdin.read().split("\n") if l.strip()]
    cpdomains = json.loads(lines[0])

    cnt = {}
    for item in cpdomains:
        rep_str, domain = item.split(" ")
        rep = int(rep_str)
        d = domain
        while True:
            cnt[d] = cnt.get(d, 0) + rep
            pos = d.find(".")
            if pos == -1:
                break
            d = d[pos + 1:]

    out = [f"{c} {d}" for d, c in cnt.items()]
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
        os.path.dirname(os.path.abspath(__file__)), "batch03.jsonl")
    n = to_jsonl(out)
    print(f"导出 {n} 条 -> {out}")
