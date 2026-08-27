"""生成 data/samples.json（评测样本集 + 人工标注真值）。

样本由"模型产出"视角构造，覆盖任务要求的：
  - 正确样本（含难例/反例，用于判别力与一致性验证）
  - 答案错误样本（定位错误步骤、错误类型）
  - 答案正确但过程不成立样本（复杂度声称与实现不符等）
  - 部分样本用于评估器有效性验证（定位准确率、误报率）

每个样本的 reasoning 含 ## 思路/## 复杂度分析/## 边界与处理/## 代码 四段，
代码置于 ```python 块中，供过程评估器解析。
ground_truth 为人工标注真值，用于计算评估器定位准确率与误报率。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "samples.json")

# 模板：把代码块拼进推理文本
def pack(reasoning_body: str, code: str) -> str:
    return f"{reasoning_body}\n\n## 代码\n```python\n{code}\n```\n"


# ---------------- 正确且过程成立（真负例，用于误报率分母/一致性）----------------
S_T1_body = """## 思路
升序数组上用双指针二分查找：每次取中点，等于则返回，小于则向右，大于则向左。
## 复杂度分析
时间复杂度 O(log n)，每次规模减半。
## 边界与处理
空输入/单元素、target 不存在返回 -1；下标越界已通过 lo<=hi 控制。"""
S_T1_code = """import sys
def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0]); arr = list(map(int, data[1:1 + n])); target = int(data[1 + n])
    lo, hi = 0, n - 1; ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            ans = mid; break
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    print(ans)
solve()"""

S_T2_body = """## 思路
把输入值序列建成链表，再用三指针（prev/cur/nxt）反转。
## 复杂度分析
时间复杂度 O(n)，每个节点访问一次。
## 边界与处理
空链表输出空行；单元素直接返回；注意反转时先保存 nxt 防止断链。"""
S_T2_code = """import sys
class ListNode:
    def __init__(self, v):
        self.val = v; self.next = None
def build(vals):
    head = cur = None
    for v in vals:
        nd = ListNode(v)
        if not head: head = cur = nd
        else: cur.next = nd; cur = nd
    return head
def reverse(head):
    prev = None; cur = head
    while cur:
        nxt = cur.next; cur.next = prev; prev = cur; cur = nxt
    return prev
def solve():
    data = sys.stdin.read().split()
    if not data:
        print(""); return
    vals = list(map(int, data))
    head = build(vals); head = reverse(head)
    out = []
    while head:
        out.append(str(head.val)); head = head.next
    print(" ".join(out))
solve()"""

S_T3_body = """## 思路
经典编辑距离 DP：dp[i][j] 表示 word1 前 i 个字符到 word2 前 j 个字符的最小操作数，
相等时继承左上，否则取左/上/左上三种操作的最小值加一。
## 复杂度分析
时间复杂度 O(mn)，空间复杂度 O(mn)。
## 边界与处理
空串时答案为另一串长度；下标从 1 起避免越界。"""
S_T3_code = """import sys
def solve():
    d = sys.stdin.read().split()
    if len(d) < 2: print(0); return
    w1, w2 = d[0], d[1]
    m = len(w1); n = len(w2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if w1[i - 1] == w2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    print(dp[m][n])
solve()"""

# ---------------- 答案正确但过程不成立（真实过程问题，评估器应识别）----------------
S_C1_body = """## 思路
用双重循环枚举所有下标对 (i,j)，检查其和是否等于 target。
## 复杂度分析
时间复杂度 O(n)，单次遍历即可。
## 边界与处理
保证每个元素只用一次。"""
S_C1_code = """import sys
def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0]); arr = list(map(int, data[1:1 + n])); target = int(data[1 + n])
    for i in range(n):
        for j in range(i + 1, n):
            if arr[i] + arr[j] == target:
                print(f"{i} {j}"); return
solve()"""

S_C3_body = """## 思路
从每个起点 i 向右扩展，用集合记录已出现字符，遇到重复即停止，更新最长长度。
## 复杂度分析
时间复杂度 O(n)，线性扫描。
## 边界与处理
空串返回 0；重复字符通过集合去重。"""
S_C3_code = """import sys
def solve():
    s = sys.stdin.read().strip()
    n = len(s); best = 0
    for i in range(n):
        seen = set()
        for j in range(i, n):
            if s[j] in seen:
                break
            seen.add(s[j])
        best = max(best, len(seen))
    print(best)
solve()"""

# ---------------- 误报样本：答案正确、过程也成立，但评估器易误判 ----------------
# 经典滑动窗口（频率数组），真实复杂度摊还 O(n)，但含嵌套 while，
# 规则评估器会把"嵌套循环 + 声称 O(n)"误判为复杂度矛盾 -> 误报。
S_FP_body = """## 思路
滑动窗口 + 固定大小(26)频率数组：右指针扩展，若当前字符频率超 1 则左指针收缩，
维护窗口内字符全不同。
## 复杂度分析
时间复杂度 O(n)，每个字符进出窗口各一次。
## 边界与处理
空串返回 0；重复字符通过左移窗口处理。"""
S_FP_code = """import sys
def solve():
    s = sys.stdin.read().strip()
    n = len(s)
    freq = [0] * 26
    left = 0; best = 0
    for right in range(n):
        c = ord(s[right]) - 97
        freq[c] += 1
        while freq[c] > 1:
            lc = ord(s[left]) - 97
            freq[lc] -= 1
            left += 1
        best = max(best, right - left + 1)
    print(best)
solve()"""

# ---------------- 答案错误样本（用于定位准确率）----------------
S_W1_body = """## 思路
遍历数组，用哈希表记录"已见过的数值"，遇到互补值就输出这两个数。
## 复杂度分析
时间复杂度 O(n)，单次遍历。
## 边界与处理
题目保证恰有一个答案。"""
S_W1_code = """import sys
def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0]); arr = list(map(int, data[1:1 + n])); target = int(data[1 + n])
    seen = {}
    for i, x in enumerate(arr):
        if target - x in seen:
            print(f"{seen[target - x]} {x}")  # 误：打印的是"数值"而非"下标"
            return
        seen[x] = i
solve()"""

S_W2_body = """## 思路
二分查找：每次取中点比较，小于目标向右、大于向左。
## 复杂度分析
时间复杂度 O(log n)。
## 边界与处理
target 不存在返回 -1。"""
S_W2_code = """import sys
def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0]); arr = list(map(int, data[1:1 + n])); target = int(data[1 + n])
    lo, hi = 0, n - 1; ans = -1
    while lo < hi:           # 误：应为 lo <= hi
        mid = (lo + hi) // 2
        if arr[mid] == target:
            ans = mid; break
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid           # 误：应为 hi = mid - 1
    print(ans)
solve()"""

S_W3_body = """## 思路
枚举每个起点 i，向右扩展统计互异字符数。
## 复杂度分析
时间复杂度 O(n)，线性。
## 边界与处理
重复字符停止扩展。"""
S_W3_code = """import sys
def solve():
    s = sys.stdin.read().strip()
    n = len(s); best = 0
    for i in range(n):
        seen = set()
        for j in range(i, n):
            seen.add(s[j])   # 误：重复字符仍加入，未停止扩展
        best = max(best, len(seen))
    print(best)
solve()"""

S_W4_body = """## 思路
最短路径用 Dijkstra 堆优化：优先队列按距离松弛邻边。
## 复杂度分析
时间复杂度 O((V+E) log V)。
## 边界与处理
不可达节点输出 -1。"""
S_W4_code = """import sys
from collections import deque
def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0]); m = int(data[1]); src = int(data[2])
    g = [[] for _ in range(n + 1)]; idx = 3
    for _ in range(m):
        u = int(data[idx]); v = int(data[idx + 1]); w = int(data[idx + 2]); idx += 3
        g[u].append(v); g[v].append(u)
    dist = [-1] * (n + 1); dist[src] = 0
    q = deque([src])
    while q:                 # 误：用无权 BFS 代替带权 Dijkstra
        u = q.popleft()
        for v in g[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                q.append(v)
    print(" ".join(str(dist[i]) for i in range(1, n + 1)))
solve()"""

S_W5_body = """## 思路
用栈匹配括号：遇左括号入栈，遇右括号与栈顶比较。
## 复杂度分析
时间复杂度 O(n)。
## 边界与处理
最后栈空则有效。"""
S_W5_code = """import sys
def solve():
    s = sys.stdin.read().strip()
    cnt = 0
    for ch in s:
        if ch in '([{':
            cnt += 1
        elif ch in ')]}':
            cnt -= 1
    print("True" if cnt == 0 else "False")   # 误：只统计个数，未检查类型与顺序
solve()"""

# 运行异常样本（展示 RE verdict 的可执行验证定位）
S_W6_body = """## 思路
遍历数组，遇到等于目标值的元素就尝试用其后第 n 个元素覆盖（错误写法）。
## 复杂度分析
时间复杂度 O(n)。
## 边界与处理
空输入返回 -1。"""
S_W6_code = """import sys
def solve():
    data = sys.stdin.read().split()
    if not data:
        return
    n = int(data[0]); arr = list(map(int, data[1:1 + n])); target = int(data[1 + n])
    for i in range(n):
        if arr[i] + arr[i + n] == target:   # 误：arr[i + n] 必然下标越界 -> RE
            print(i); return
    print(-1)
solve()"""


S_T4_body = """## 思路
双指针从两侧向中间夹逼：维护左右已见最大值，较矮一侧决定当前能接的雨水量。
## 复杂度分析
时间复杂度 O(n)，单次遍历。
## 边界与处理
空数组或单元素返回 0；两侧指针相遇即结束。"""

S_T5_body = """## 思路
双指针夹逼：每次移动较矮的指针，维护能盛的最大水量。
## 复杂度分析
时间复杂度 O(n)。
## 边界与处理
少于两元素直接比较得出 0 或唯一面积。"""

S_C4_body = """## 思路
先排序，固定一个数后用双指针找另外两数使和为 0，并跳过重复元素避免重复三元组。
## 复杂度分析
时间复杂度 O(n)，线性扫描即可。
## 边界与处理
排序后去重，保证每个值只作为固定点使用一次。"""


SAMPLES = [
    # 正确且过程成立
    {"problem_id": "P002", "sample_id": "S_T1", "reasoning": pack(S_T1_body, S_T1_code),
     "ground_truth": {"final_correct": True, "process_valid": True, "error_type": None, "error_step": None,
                      "comment": "标准二分，过程成立（真负例）"}},
    {"problem_id": "P036", "sample_id": "S_T2", "reasoning": pack(S_T2_body, S_T2_code),
     "ground_truth": {"final_correct": True, "process_valid": True, "error_type": None, "error_step": None,
                      "comment": "标准反转链表，过程成立（真负例）"}},
    {"problem_id": "P093", "sample_id": "S_T3", "reasoning": pack(S_T3_body, S_T3_code),
     "ground_truth": {"final_correct": True, "process_valid": True, "error_type": None, "error_step": None,
                      "comment": "标准编辑距离 DP，过程成立（真负例）"}},
    {"problem_id": "P044", "sample_id": "S_T4", "reasoning": pack(S_T4_body,
        """import sys
def solve():
    d = sys.stdin.read().split()
    if not d: print(0); return
    h = list(map(int, d))
    if not h: print(0); return
    l, r = 0, len(h) - 1; lm = rm = ans = 0
    while l < r:
        if h[l] < h[r]:
            lm = max(lm, h[l]); ans += lm - h[l]; l += 1
        else:
            rm = max(rm, h[r]); ans += rm - h[r]; r -= 1
    print(ans)
solve()"""),
     "ground_truth": {"final_correct": True, "process_valid": True, "error_type": None, "error_step": None,
                      "comment": "标准接雨水双指针，过程成立（真负例）"}},
    {"problem_id": "P011", "sample_id": "S_T5", "reasoning": pack(S_T5_body,
        """import sys
def solve():
    d = sys.stdin.read().split()
    if not d: print(0); return
    a = list(map(int, d))
    l, r = 0, len(a) - 1; ans = 0
    while l < r:
        ans = max(ans, (r - l) * min(a[l], a[r]))
        if a[l] < a[r]: l += 1
        else: r -= 1
    print(ans)
solve()"""),
     "ground_truth": {"final_correct": True, "process_valid": True, "error_type": None, "error_step": None,
                      "comment": "标准盛水容器双指针，过程成立（真负例）"}},
    # 答案正确但过程不成立（评估器应识别为真实过程问题）
    {"problem_id": "P001", "sample_id": "S_C1", "reasoning": pack(S_C1_body, S_C1_code),
     "ground_truth": {"final_correct": True, "process_valid": False, "error_type": "complexity_error", "error_step": 2,
                      "comment": "答案对（弱测试下暴力通过），但声称 O(n) 实为 O(n^2)，过程不成立"}},
    {"problem_id": "P045", "sample_id": "S_C3", "reasoning": pack(S_C3_body, S_C3_code),
     "ground_truth": {"final_correct": True, "process_valid": False, "error_type": "complexity_error", "error_step": 2,
                      "comment": "答案对，但声称 O(n) 实为 O(n^2) 枚举，过程不成立"}},
    {"problem_id": "P012", "sample_id": "S_C4", "reasoning": pack(S_C4_body,
        """import sys
def solve():
    d = sys.stdin.read().split()
    if not d: return
    a = sorted(map(int, d)); n = len(a); res = []
    for i in range(n):
        if i > 0 and a[i] == a[i - 1]: continue
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = a[i] + a[lo] + a[hi]
            if s < 0: lo += 1
            elif s > 0: hi -= 1
            else:
                res.append((a[i], a[lo], a[hi]))
                while lo < hi and a[lo] == a[lo + 1]: lo += 1
                while lo < hi and a[hi] == a[hi - 1]: hi -= 1
                lo += 1; hi -= 1
    res.sort()
    out = []
    for t in res: out += [str(t[0]), str(t[1]), str(t[2])]
    print(' '.join(out))
solve()"""),
     "ground_truth": {"final_correct": True, "process_valid": False, "error_type": "complexity_error", "error_step": 2,
                      "comment": "三数之和答案正确，但声称 O(n) 实为 O(n^2)（排序+双指针），过程不成立"}},
    # 误报样本：答案正确、过程也成立，规则评估器易误判
    {"problem_id": "P045", "sample_id": "S_FP", "reasoning": pack(S_FP_body, S_FP_code),
     "ground_truth": {"final_correct": True, "process_valid": True, "error_type": None, "error_step": None,
                      "comment": "摊还 O(n) 滑动窗口，过程成立；规则评估器因嵌套 while 误判为复杂度矛盾（预期误报）"}},
    # 答案错误样本
    {"problem_id": "P001", "sample_id": "S_W1", "reasoning": pack(S_W1_body, S_W1_code),
     "ground_truth": {"final_correct": False, "process_valid": False, "error_type": "misread_problem", "error_step": 1,
                      "comment": "题意误读：应输出下标却输出数值"}},
    {"problem_id": "P002", "sample_id": "S_W2", "reasoning": pack(S_W2_body, S_W2_code),
     "ground_truth": {"final_correct": False, "process_valid": False, "error_type": "logic_error", "error_step": 4,
                      "comment": "二分边界差一：lo<hi 且 hi=mid，单元素用例失败"}},
    {"problem_id": "P045", "sample_id": "S_W3", "reasoning": pack(S_W3_body, S_W3_code),
     "ground_truth": {"final_correct": False, "process_valid": False, "error_type": "complexity_error", "error_step": 2,
                      "comment": "重复字符未停止扩展导致结果偏大；且声称 O(n) 实为 O(n^2)"}},
    {"problem_id": "P047", "sample_id": "S_W4", "reasoning": pack(S_W4_body, S_W4_code),
     "ground_truth": {"final_correct": False, "process_valid": False, "error_type": "logic_error", "error_step": 4,
                      "comment": "用无权 BFS 代替带权 Dijkstra，思路与实现不符"}},
    {"problem_id": "P046", "sample_id": "S_W5", "reasoning": pack(S_W5_body, S_W5_code),
     "ground_truth": {"final_correct": False, "process_valid": False, "error_type": "logic_error", "error_step": 4,
                      "comment": "只统计括号个数，未检查类型与配对顺序"}},
    {"problem_id": "P001", "sample_id": "S_W6", "reasoning": pack(S_W6_body, S_W6_code),
     "ground_truth": {"final_correct": False, "process_valid": False, "error_type": "boundary_error", "error_step": 4,
                      "comment": "下标越界导致运行异常(RE)，边界处理缺失"}},
]


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(SAMPLES, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(SAMPLES)} samples -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
