# -*- coding: utf-8 -*-
"""LeetCode 官方题解真实题目（动态规划 · easy，15 题）。
题目与答案均来自 LeetCode 官方（题目 API + 官方题解文章）。
"""
from ._base import mk

PDE01 = mk(
    "DE01",
    "\u6bd4\u7279\u4f4d\u8ba1\u6570",
    "LeetCode 338",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u4f60\u4e00\u4e2a\u6574\u6570 n \uff0c\u5bf9\u4e8e\u00a00 <= i <= n \u4e2d\u7684\u6bcf\u4e2a i \uff0c\u8ba1\u7b97\u5176\u4e8c\u8fdb\u5236\u8868\u793a\u4e2d 1 \u7684\u4e2a\u6570 \uff0c\u8fd4\u56de\u4e00\u4e2a\u957f\u5ea6\u4e3a n + 1 \u7684\u6570\u7ec4 ans \u4f5c\u4e3a\u7b54\u6848\u3002\n\n\u4e0d\u8981\u4f7f\u7528\u5185\u7f6e\u51fd\u6570\u6765\u89e3\u51b3\uff08\u4f8b\u5982\uff0cC++ \u4e2d\u7684 __builtin_popcount\uff09\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1an = 2\n\u8f93\u51fa\uff1a[0,1,1]\n\u89e3\u91ca\uff1a\n0 --> 0\n1 --> 1\n2 --> 10\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1an = 5\n\u8f93\u51fa\uff1a[0,1,1,2,1,2]\n\u89e3\u91ca\uff1a\n0 --> 0\n1 --> 1\n2 --> 10\n3 --> 11\n4 --> 100\n5 --> 101\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t0 <= n <= 105\n\n\u00a0\n\n\u8fdb\u9636\uff1a\n\n\t\u5f88\u5bb9\u6613\u5c31\u80fd\u5b9e\u73b0\u65f6\u95f4\u590d\u6742\u5ea6\u4e3a O(n log n) \u7684\u89e3\u51b3\u65b9\u6848\uff0c\u4f60\u53ef\u4ee5\u5728\u7ebf\u6027\u65f6\u95f4\u590d\u6742\u5ea6 O(n) \u5185\u7528\u4e00\u8d9f\u626b\u63cf\u89e3\u51b3\u6b64\u95ee\u9898\u5417\uff1f",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1an\u3002",
    "\u8f93\u51fa integer[] \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def countBits(self, n: int) -> List[int]:\n        def countOnes(x: int) -> int:\n            ones = 0\n            while x > 0:\n                x &= (x - 1)\n                ones += 1\n            return ones\n        \n        bits = [countOnes(i) for i in range(n + 1)]\n        return bits\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.countBits(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int_list",
    [["2", "[0,1,1]"], ["5", "[0,1,1,2,1,2]"]],
    ["bit-manipulation", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE01["solution_url"] = "https://leetcode.cn/problems/counting-bits/solution/bi-te-wei-ji-shu-by-leetcode-solution-0t1i/"
PDE01["problem_url"] = "https://leetcode.cn/problems/counting-bits/"

PDE02 = mk(
    "DE02",
    "\u6bd4\u7279\u4f4d\u8ba1\u6570",
    "LeetCode LCR 003",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u5b9a\u4e00\u4e2a\u975e\u8d1f\u6574\u6570 n\u00a0\uff0c\u8bf7\u8ba1\u7b97 0 \u5230 n \u4e4b\u95f4\u7684\u6bcf\u4e2a\u6570\u5b57\u7684\u4e8c\u8fdb\u5236\u8868\u793a\u4e2d 1 \u7684\u4e2a\u6570\uff0c\u5e76\u8f93\u51fa\u4e00\u4e2a\u6570\u7ec4\u3002\n\n\u00a0\n\n\u793a\u4f8b 1:\n\n```\n\u8f93\u5165: n = 2\n\u8f93\u51fa: [0,1,1]\n\u89e3\u91ca:\n0 --> 0\n1 --> 1\n2 --> 10\n```\n\n\u793a\u4f8b\u00a02:\n\n```\n\u8f93\u5165: n = 5\n\u8f93\u51fa: [0,1,1,2,1,2]\n\u89e3\u91ca:\n0 --> 0\n1 --> 1\n2 --> 10\n3 --> 11\n4 --> 100\n5 --> 101\n```\n\n\u00a0\n\n\u8bf4\u660e :\n\n\t0 <= n <= 105\n\n\u00a0\n\n\u8fdb\u9636:\n\n\t\u7ed9\u51fa\u65f6\u95f4\u590d\u6742\u5ea6\u4e3a\u00a0O(n*sizeof(integer))\u00a0\u7684\u89e3\u7b54\u975e\u5e38\u5bb9\u6613\u3002\u4f46\u4f60\u53ef\u4ee5\u5728\u7ebf\u6027\u65f6\u95f4\u00a0O(n)\u00a0\u5185\u7528\u4e00\u8d9f\u626b\u63cf\u505a\u5230\u5417\uff1f\n\n\t\u8981\u6c42\u7b97\u6cd5\u7684\u7a7a\u95f4\u590d\u6742\u5ea6\u4e3a\u00a0O(n)\u00a0\u3002\n\n\t\u4f60\u80fd\u8fdb\u4e00\u6b65\u5b8c\u5584\u89e3\u6cd5\u5417\uff1f\u8981\u6c42\u5728C++\u6216\u4efb\u4f55\u5176\u4ed6\u8bed\u8a00\u4e2d\u4e0d\u4f7f\u7528\u4efb\u4f55\u5185\u7f6e\u51fd\u6570\uff08\u5982 C++ \u4e2d\u7684\u00a0__builtin_popcount\u00a0\uff09\u6765\u6267\u884c\u6b64\u64cd\u4f5c\u3002\n\n\u00a0\n\n\u6ce8\u610f\uff1a\u672c\u9898\u4e0e\u4e3b\u7ad9 338\u00a0\u9898\u76f8\u540c\uff1ahttps://leetcode.cn/problems/counting-bits/",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1an\u3002",
    "\u8f93\u51fa integer[] \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def countBits(self, n: int) -> List[int]:\n        def countOnes(x: int) -> int:\n            ones = 0\n            while x > 0:\n                x &= (x - 1)\n                ones += 1\n            return ones\n        \n        bits = [countOnes(i) for i in range(n + 1)]\n        return bits\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.countBits(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int_list",
    [["2", "[0,1,1]"], ["5", "[0,1,1,2,1,2]"]],
    ["bit-manipulation", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE02["solution_url"] = "https://leetcode.cn/problems/w3tCBm/solution/qian-n-ge-shu-zi-er-jin-zhi-zhong-1-de-g-fkjq/"
PDE02["problem_url"] = "https://leetcode.cn/problems/w3tCBm/"

PDE03 = mk(
    "DE03",
    "\u6768\u8f89\u4e09\u89d2",
    "LeetCode 118",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u5b9a\u4e00\u4e2a\u975e\u8d1f\u6574\u6570\u00a0numRows\uff0c\u751f\u6210\u300c\u6768\u8f89\u4e09\u89d2\u300d\u7684\u524d\u00a0numRows\u00a0\u884c\u3002\n\n\u5728\u300c\u6768\u8f89\u4e09\u89d2\u300d\u4e2d\uff0c\u6bcf\u4e2a\u6570\u662f\u5b83\u5de6\u4e0a\u65b9\u548c\u53f3\u4e0a\u65b9\u7684\u6570\u7684\u548c\u3002\n\n\u00a0\n\n\u793a\u4f8b 1:\n\n```\n\u8f93\u5165: numRows = 5\n\u8f93\u51fa: [[1],[1,1],[1,2,1],[1,3,3,1],[1,4,6,4,1]]\n```\n\n\u793a\u4f8b\u00a02:\n\n```\n\u8f93\u5165: numRows = 1\n\u8f93\u51fa: [[1]]\n```\n\n\u00a0\n\n\u63d0\u793a:\n\n\t1 <= numRows <= 30",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1anumRows\u3002",
    "\u8f93\u51fa list<list<integer>> \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def generate(self, numRows: int) -> List[List[int]]:\n        ret = list()\n        for i in range(numRows):\n            row = list()\n            for j in range(0, i + 1):\n                if j == 0 or j == i:\n                    row.append(1)\n                else:\n                    row.append(ret[i - 1][j] + ret[i - 1][j - 1])\n            ret.append(row)\n        return ret\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.generate(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "exact",
    [["5", "[[1],[1,1],[1,2,1],[1,3,3,1],[1,4,6,4,1]]"], ["1", "[[1]]"]],
    ["array", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE03["solution_url"] = "https://leetcode.cn/problems/pascals-triangle/solution/yang-hui-san-jiao-by-leetcode-solution-lew9/"
PDE03["problem_url"] = "https://leetcode.cn/problems/pascals-triangle/"

PDE04 = mk(
    "DE04",
    "\u9664\u6570\u535a\u5f08",
    "LeetCode 1025",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7231\u4e3d\u4e1d\u548c\u9c8d\u52c3\u4e00\u8d77\u73a9\u6e38\u620f\uff0c\u4ed6\u4eec\u8f6e\u6d41\u884c\u52a8\u3002\u7231\u4e3d\u4e1d\u5148\u624b\u5f00\u5c40\u3002\n\n\u6700\u521d\uff0c\u9ed1\u677f\u4e0a\u6709\u4e00\u4e2a\u6570\u5b57\u00a0n\u00a0\u3002\u5728\u6bcf\u4e2a\u73a9\u5bb6\u7684\u56de\u5408\uff0c\u73a9\u5bb6\u9700\u8981\u6267\u884c\u4ee5\u4e0b\u64cd\u4f5c\uff1a\n\n\t\u9009\u51fa\u4efb\u4e00\u6574\u6570\u00a0x\uff0c\u6ee1\u8db3\u00a00 < x < n\u00a0\u4e14\u00a0n % x == 0\u00a0\u3002\n\n\t\u7528 n - x\u00a0\u66ff\u6362\u9ed1\u677f\u4e0a\u7684\u6570\u5b57\u00a0n \u3002\n\n\u5982\u679c\u73a9\u5bb6\u65e0\u6cd5\u6267\u884c\u8fd9\u4e9b\u64cd\u4f5c\uff0c\u5c31\u4f1a\u8f93\u6389\u6e38\u620f\u3002\n\n\u53ea\u6709\u5728\u7231\u4e3d\u4e1d\u5728\u6e38\u620f\u4e2d\u53d6\u5f97\u80dc\u5229\u65f6\u624d\u8fd4\u56de\u00a0true\u00a0\u3002\u5047\u8bbe\u4e24\u4e2a\u73a9\u5bb6\u90fd\u4ee5\u6700\u4f73\u72b6\u6001\u53c2\u4e0e\u6e38\u620f\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1an = 2\n\u8f93\u51fa\uff1atrue\n\u89e3\u91ca\uff1a\u7231\u4e3d\u4e1d\u9009\u62e9 1\uff0c\u9c8d\u52c3\u65e0\u6cd5\u8fdb\u884c\u64cd\u4f5c\u3002\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1an = 3\n\u8f93\u51fa\uff1afalse\n\u89e3\u91ca\uff1a\u7231\u4e3d\u4e1d\u9009\u62e9 1\uff0c\u9c8d\u52c3\u4e5f\u9009\u62e9 1\uff0c\u7136\u540e\u7231\u4e3d\u4e1d\u65e0\u6cd5\u8fdb\u884c\u64cd\u4f5c\u3002\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t1 <= n <= 1000",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1an\u3002",
    "\u8f93\u51fa boolean \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def divisorGame(self, N: int) -> bool:\n        return N%2==0\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.divisorGame(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "bool",
    [["2", "true"], ["3", "false"]],
    ["brainteaser", "math", "dynamic-programming", "game-theory", "impartial-game", "\u52a8\u6001\u89c4\u5212"],
    )
PDE04["solution_url"] = "https://leetcode.cn/problems/divisor-game/solution/python3gui-na-fa-by-pandawakaka/"
PDE04["problem_url"] = "https://leetcode.cn/problems/divisor-game/"

PDE05 = mk(
    "DE05",
    "\u4f7f\u7528\u6700\u5c0f\u82b1\u8d39\u722c\u697c\u68af",
    "LeetCode LCR 088",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u6570\u7ec4\u7684\u6bcf\u4e2a\u4e0b\u6807\u4f5c\u4e3a\u4e00\u4e2a\u9636\u68af\uff0c\u7b2c i \u4e2a\u9636\u68af\u5bf9\u5e94\u7740\u4e00\u4e2a\u975e\u8d1f\u6570\u7684\u4f53\u529b\u82b1\u8d39\u503c\u00a0cost[i]\uff08\u4e0b\u6807\u4ece 0 \u5f00\u59cb\uff09\u3002\n\n\u6bcf\u5f53\u722c\u4e0a\u4e00\u4e2a\u9636\u68af\u90fd\u8981\u82b1\u8d39\u5bf9\u5e94\u7684\u4f53\u529b\u503c\uff0c\u4e00\u65e6\u652f\u4ed8\u4e86\u76f8\u5e94\u7684\u4f53\u529b\u503c\uff0c\u5c31\u53ef\u4ee5\u9009\u62e9\u5411\u4e0a\u722c\u4e00\u4e2a\u9636\u68af\u6216\u8005\u722c\u4e24\u4e2a\u9636\u68af\u3002\n\n\u8bf7\u627e\u51fa\u8fbe\u5230\u697c\u5c42\u9876\u90e8\u7684\u6700\u4f4e\u82b1\u8d39\u3002\u5728\u5f00\u59cb\u65f6\uff0c\u4f60\u53ef\u4ee5\u9009\u62e9\u4ece\u4e0b\u6807\u4e3a 0 \u6216 1 \u7684\u5143\u7d20\u4f5c\u4e3a\u521d\u59cb\u9636\u68af\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1acost = [10, 15, 20]\n\u8f93\u51fa\uff1a15\n\u89e3\u91ca\uff1a\u6700\u4f4e\u82b1\u8d39\u662f\u4ece cost[1] \u5f00\u59cb\uff0c\u7136\u540e\u8d70\u4e24\u6b65\u5373\u53ef\u5230\u9636\u68af\u9876\uff0c\u4e00\u5171\u82b1\u8d39 15 \u3002\n```\n\n\u00a0\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1acost = [1, 100, 1, 1, 1, 100, 1, 1, 100, 1]\n\u8f93\u51fa\uff1a6\n\u89e3\u91ca\uff1a\u6700\u4f4e\u82b1\u8d39\u65b9\u5f0f\u662f\u4ece cost[0] \u5f00\u59cb\uff0c\u9010\u4e2a\u7ecf\u8fc7\u90a3\u4e9b 1 \uff0c\u8df3\u8fc7 cost[3] \uff0c\u4e00\u5171\u82b1\u8d39 6 \u3002\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t2 <= cost.length <= 1000\n\n\t0 <= cost[i] <= 999\n\n\u00a0\n\n\u6ce8\u610f\uff1a\u672c\u9898\u4e0e\u4e3b\u7ad9 746\u00a0\u9898\u76f8\u540c\uff1a\u00a0https://leetcode.cn/problems/min-cost-climbing-stairs/",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1acost\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def minCostClimbingStairs(self, cost: List[int]) -> int:\n        n = len(cost)\n        dp = [0] * (n + 1)\n        for i in range(2, n + 1):\n            dp[i] = min(dp[i - 1] + cost[i - 1], dp[i - 2] + cost[i - 2])\n        return dp[n]\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.minCostClimbingStairs(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["[10,15,20]", "15"]],
    ["array", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE05["solution_url"] = "https://leetcode.cn/problems/GzCJIP/solution/pa-lou-ti-de-zui-shao-cheng-ben-by-leetc-xx4h/"
PDE05["problem_url"] = "https://leetcode.cn/problems/GzCJIP/"

PDE06 = mk(
    "DE06",
    "\u6700\u957f\u76f8\u90bb\u4e0d\u76f8\u7b49\u5b50\u5e8f\u5217 I",
    "LeetCode 2900",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u5b9a\u4e00\u4e2a\u5b57\u7b26\u4e32\u6570\u7ec4\u00a0words\u00a0\uff0c\u548c\u4e00\u4e2a\u00a0\u4e8c\u8fdb\u5236\u00a0\u6570\u7ec4\u00a0groups\u00a0\uff0c\u4e24\u4e2a\u6570\u7ec4\u957f\u5ea6\u90fd\u662f\u00a0n\u00a0\u3002\n\n\u5982\u679c\u00a0words\u00a0\u7684\u4e00\u4e2a \u5b50\u5e8f\u5217 \u662f\u4ea4\u66ff\u7684\uff0c\u90a3\u4e48\u5bf9\u4e8e\u5e8f\u5217\u4e2d\u7684\u4efb\u610f\u4e24\u4e2a\u8fde\u7eed\u5b57\u7b26\u4e32\uff0c\u5b83\u4eec\u5728\u00a0groups\u00a0\u4e2d\u76f8\u540c\u7d22\u5f15\u7684\u5bf9\u5e94\u5143\u7d20\u662f \u4e0d\u540c \u7684\uff08\u4e5f\u5c31\u662f\u8bf4\uff0c\u4e0d\u80fd\u6709\u8fde\u7eed\u7684 0 \u6216 1\uff09\uff0c\n\n\u4f60\u9700\u8981\u4ece\u00a0words\u00a0\u4e2d\u9009\u51fa\u00a0\u6700\u957f\u4ea4\u66ff\u5b50\u5e8f\u5217\u3002\n\n\u8fd4\u56de\u9009\u51fa\u7684\u5b50\u5e8f\u5217\u3002\u5982\u679c\u6709\u591a\u4e2a\u7b54\u6848\uff0c\u8fd4\u56de \u4efb\u610f \u4e00\u4e2a\u3002\n\n\u6ce8\u610f\uff1awords\u00a0\u4e2d\u7684\u5143\u7d20\u662f\u4e0d\u540c\u7684\u00a0\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1awords = [\"e\",\"a\",\"b\"], groups = [0,0,1]\n\u8f93\u51fa\uff1a[\"e\",\"b\"]\n\u89e3\u91ca\uff1a\u4e00\u4e2a\u53ef\u884c\u7684\u5b50\u5e8f\u5217\u662f [0,2] \uff0c\u56e0\u4e3a groups[0] != groups[2] \u3002\n\u6240\u4ee5\u4e00\u4e2a\u53ef\u884c\u7684\u7b54\u6848\u662f [words[0],words[2]] = [\"e\",\"b\"] \u3002\n\u53e6\u4e00\u4e2a\u53ef\u884c\u7684\u5b50\u5e8f\u5217\u662f [1,2] \uff0c\u56e0\u4e3a groups[1] != groups[2] \u3002\n\u5f97\u5230\u7b54\u6848\u4e3a [words[1],words[2]] = [\"a\",\"b\"] \u3002\n\u8fd9\u4e5f\u662f\u4e00\u4e2a\u53ef\u884c\u7684\u7b54\u6848\u3002\n\u7b26\u5408\u9898\u610f\u7684\u6700\u957f\u5b50\u5e8f\u5217\u7684\u957f\u5ea6\u4e3a 2 \u3002\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1awords = [\"a\",\"b\",\"c\",\"d\"], groups = [1,0,1,1]\n\u8f93\u51fa\uff1a[\"a\",\"b\",\"c\"]\n\u89e3\u91ca\uff1a\u4e00\u4e2a\u53ef\u884c\u7684\u5b50\u5e8f\u5217\u4e3a [0,1,2] \u56e0\u4e3a groups[0] != groups[1] \u4e14 groups[1] != groups[2] \u3002\n\u6240\u4ee5\u4e00\u4e2a\u53ef\u884c\u7684\u7b54\u6848\u662f [words[0],words[1],words[2]] = [\"a\",\"b\",\"c\"] \u3002\n\u53e6\u4e00\u4e2a\u53ef\u884c\u7684\u5b50\u5e8f\u5217\u4e3a [0,1,3] \u56e0\u4e3a groups[0] != groups[1] \u4e14 groups[1] != groups[3] \u3002\n\u5f97\u5230\u7b54\u6848\u4e3a [words[0],words[1],words[3]] = [\"a\",\"b\",\"d\"] \u3002\n\u8fd9\u4e5f\u662f\u4e00\u4e2a\u53ef\u884c\u7684\u7b54\u6848\u3002\n\u7b26\u5408\u9898\u610f\u7684\u6700\u957f\u5b50\u5e8f\u5217\u7684\u957f\u5ea6\u4e3a 3 \u3002\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t1 <= n == words.length == groups.length <= 100\n\n\t1 <= words[i].length <= 10\n\n\tgroups[i]\u00a0\u662f\u00a00\u00a0\u6216\u00a01\u3002\n\n\twords\u00a0\u4e2d\u7684\u5b57\u7b26\u4e32 \u4e92\u4e0d\u76f8\u540c\u00a0\u3002\n\n\twords[i]\u00a0\u53ea\u5305\u542b\u5c0f\u5199\u82f1\u6587\u5b57\u6bcd\u3002",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1awords\u3001groups\u3002",
    "\u8f93\u51fa list<string> \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def getLongestSubsequence(self, words: List[str], groups: List[int]) -> List[str]:\n        n = len(words)\n        dp = [1] * n\n        prev = [-1] * n\n        max_len, end_index = 1, 0\n\n        for i in range(1, n):\n            best_len, best_prev = 1, -1\n            for j in range(i - 1, -1, -1):\n                if groups[i] != groups[j] and dp[j] + 1 > best_len:\n                    best_len, best_prev = dp[j] + 1, j\n            dp[i] = best_len\n            prev[i] = best_prev\n            if dp[i] > max_len:\n                max_len, end_index = dp[i], i\n\n        res = []\n        i = end_index\n        while i != -1:\n            res.append(words[i])\n            i = prev[i]\n        return res[::-1]\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.getLongestSubsequence(_args[0], _args[1])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "exact",
    [["[\"c\"]\n[0]", "[\"c\"]"], ["[\"d\"]\n[1]", "[\"d\"]"]],
    ["greedy", "array", "string", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE06["solution_url"] = "https://leetcode.cn/problems/longest-unequal-adjacent-groups-subsequence-i/solution/zui-chang-xiang-lin-bu-xiang-deng-zi-xu-8vlf3/"
PDE06["problem_url"] = "https://leetcode.cn/problems/longest-unequal-adjacent-groups-subsequence-i/"

PDE07 = mk(
    "DE07",
    "\u6768\u8f89\u4e09\u89d2 II",
    "LeetCode 119",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u5b9a\u4e00\u4e2a\u975e\u8d1f\u7d22\u5f15 rowIndex\uff0c\u8fd4\u56de\u300c\u6768\u8f89\u4e09\u89d2\u300d\u7684\u7b2c rowIndex\u00a0\u884c\u3002\n\n\u5728\u300c\u6768\u8f89\u4e09\u89d2\u300d\u4e2d\uff0c\u6bcf\u4e2a\u6570\u662f\u5b83\u5de6\u4e0a\u65b9\u548c\u53f3\u4e0a\u65b9\u7684\u6570\u7684\u548c\u3002\n\n\u00a0\n\n\u793a\u4f8b 1:\n\n```\n\u8f93\u5165: rowIndex = 3\n\u8f93\u51fa: [1,3,3,1]\n```\n\n\u793a\u4f8b 2:\n\n```\n\u8f93\u5165: rowIndex = 0\n\u8f93\u51fa: [1]\n```\n\n\u793a\u4f8b 3:\n\n```\n\u8f93\u5165: rowIndex = 1\n\u8f93\u51fa: [1,1]\n```\n\n\u00a0\n\n\u63d0\u793a:\n\n\t0\n\n\u00a0\n\n\u8fdb\u9636\uff1a\n\n\u4f60\u53ef\u4ee5\u4f18\u5316\u4f60\u7684\u7b97\u6cd5\u5230 O(rowIndex) \u7a7a\u95f4\u590d\u6742\u5ea6\u5417\uff1f",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1arowIndex\u3002",
    "\u8f93\u51fa list<integer> \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def getRow(self, rowIndex: int) -> List[int]:\n        C = [[1] * (i + 1) for i in range(rowIndex + 1)]\n        for i in range(0, rowIndex + 1):\n            for j in range(1, i):\n                C[i][j] = C[i - 1][j - 1] + C[i - 1][j]\n        return C[rowIndex]\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.getRow(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "exact",
    [["3", "[1,3,3,1]"], ["0", "[1]"], ["1", "[1,1]"]],
    ["array", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE07["solution_url"] = "https://leetcode.cn/problems/pascals-triangle-ii/solution/yang-hui-san-jiao-ii-by-leetcode-solutio-shuk/"
PDE07["problem_url"] = "https://leetcode.cn/problems/pascals-triangle-ii/"

PDE08 = mk(
    "DE08",
    "\u4f7f\u7528\u6700\u5c0f\u82b1\u8d39\u722c\u697c\u68af",
    "LeetCode 746",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u4f60\u4e00\u4e2a\u6574\u6570\u6570\u7ec4 cost \uff0c\u5176\u4e2d cost[i] \u662f\u4ece\u697c\u68af\u7b2c i \u4e2a\u53f0\u9636\u5411\u4e0a\u722c\u9700\u8981\u652f\u4ed8\u7684\u8d39\u7528\u3002\u4e00\u65e6\u4f60\u652f\u4ed8\u6b64\u8d39\u7528\uff0c\u5373\u53ef\u9009\u62e9\u5411\u4e0a\u722c\u4e00\u4e2a\u6216\u8005\u4e24\u4e2a\u53f0\u9636\u3002\n\n\u4f60\u53ef\u4ee5\u9009\u62e9\u4ece\u4e0b\u6807\u4e3a 0 \u6216\u4e0b\u6807\u4e3a 1 \u7684\u53f0\u9636\u5f00\u59cb\u722c\u697c\u68af\u3002\n\n\u8bf7\u4f60\u8ba1\u7b97\u5e76\u8fd4\u56de\u8fbe\u5230\u697c\u68af\u9876\u90e8\u7684\u6700\u4f4e\u82b1\u8d39\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1acost = [10,15,20]\n\u8f93\u51fa\uff1a15\n\u89e3\u91ca\uff1a\u4f60\u5c06\u4ece\u4e0b\u6807\u4e3a 1 \u7684\u53f0\u9636\u5f00\u59cb\u3002\n- \u652f\u4ed8 15 \uff0c\u5411\u4e0a\u722c\u4e24\u4e2a\u53f0\u9636\uff0c\u5230\u8fbe\u697c\u68af\u9876\u90e8\u3002\n\u603b\u82b1\u8d39\u4e3a 15 \u3002\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1acost = [1,100,1,1,1,100,1,1,100,1]\n\u8f93\u51fa\uff1a6\n\u89e3\u91ca\uff1a\u4f60\u5c06\u4ece\u4e0b\u6807\u4e3a 0 \u7684\u53f0\u9636\u5f00\u59cb\u3002\n- \u652f\u4ed8 1 \uff0c\u5411\u4e0a\u722c\u4e24\u4e2a\u53f0\u9636\uff0c\u5230\u8fbe\u4e0b\u6807\u4e3a 2 \u7684\u53f0\u9636\u3002\n- \u652f\u4ed8 1 \uff0c\u5411\u4e0a\u722c\u4e24\u4e2a\u53f0\u9636\uff0c\u5230\u8fbe\u4e0b\u6807\u4e3a 4 \u7684\u53f0\u9636\u3002\n- \u652f\u4ed8 1 \uff0c\u5411\u4e0a\u722c\u4e24\u4e2a\u53f0\u9636\uff0c\u5230\u8fbe\u4e0b\u6807\u4e3a 6 \u7684\u53f0\u9636\u3002\n- \u652f\u4ed8 1 \uff0c\u5411\u4e0a\u722c\u4e00\u4e2a\u53f0\u9636\uff0c\u5230\u8fbe\u4e0b\u6807\u4e3a 7 \u7684\u53f0\u9636\u3002\n- \u652f\u4ed8 1 \uff0c\u5411\u4e0a\u722c\u4e24\u4e2a\u53f0\u9636\uff0c\u5230\u8fbe\u4e0b\u6807\u4e3a 9 \u7684\u53f0\u9636\u3002\n- \u652f\u4ed8 1 \uff0c\u5411\u4e0a\u722c\u4e00\u4e2a\u53f0\u9636\uff0c\u5230\u8fbe\u697c\u68af\u9876\u90e8\u3002\n\u603b\u82b1\u8d39\u4e3a 6 \u3002\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t2 <= cost.length <= 1000\n\n\t0 <= cost[i] <= 999",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1acost\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def minCostClimbingStairs(self, cost: List[int]) -> int:\n        n = len(cost)\n        dp = [0] * (n + 1)\n        for i in range(2, n + 1):\n            dp[i] = min(dp[i - 1] + cost[i - 1], dp[i - 2] + cost[i - 2])\n        return dp[n]\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.minCostClimbingStairs(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["[10,15,20]", "15"], ["[1,100,1,1,1,100,1,1,100,1]", "6"]],
    ["array", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE08["solution_url"] = "https://leetcode.cn/problems/min-cost-climbing-stairs/solution/shi-yong-zui-xiao-hua-fei-pa-lou-ti-by-l-ncf8/"
PDE08["problem_url"] = "https://leetcode.cn/problems/min-cost-climbing-stairs/"

PDE09 = mk(
    "DE09",
    "\u6590\u6ce2\u90a3\u5951\u6570",
    "LeetCode 509",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u6590\u6ce2\u90a3\u5951\u6570\u00a0\uff08\u901a\u5e38\u7528\u00a0F(n) \u8868\u793a\uff09\u5f62\u6210\u7684\u5e8f\u5217\u79f0\u4e3a \u6590\u6ce2\u90a3\u5951\u6570\u5217 \u3002\u8be5\u6570\u5217\u7531\u00a00 \u548c 1 \u5f00\u59cb\uff0c\u540e\u9762\u7684\u6bcf\u4e00\u9879\u6570\u5b57\u90fd\u662f\u524d\u9762\u4e24\u9879\u6570\u5b57\u7684\u548c\u3002\u4e5f\u5c31\u662f\uff1a\n\n```\nF(0) = 0\uff0cF(1)\u00a0= 1\nF(n) = F(n - 1) + F(n - 2)\uff0c\u5176\u4e2d n > 1\n```\n\n\u7ed9\u5b9a\u00a0n \uff0c\u8bf7\u8ba1\u7b97 F(n) \u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1an = 2\n\u8f93\u51fa\uff1a1\n\u89e3\u91ca\uff1aF(2) = F(1) + F(0) = 1 + 0 = 1\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1an = 3\n\u8f93\u51fa\uff1a2\n\u89e3\u91ca\uff1aF(3) = F(2) + F(1) = 1 + 1 = 2\n```\n\n\u793a\u4f8b 3\uff1a\n\n```\n\u8f93\u5165\uff1an = 4\n\u8f93\u51fa\uff1a3\n\u89e3\u91ca\uff1aF(4) = F(3) + F(2) = 2 + 1 = 3\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t0 <= n <= 30",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1an\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def fib(self, n: int) -> int:\n        if n < 2:\n            return n\n        \n        p, q, r = 0, 0, 1\n        for i in range(2, n + 1):\n            p, q = q, r\n            r = p + q\n        \n        return r\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.fib(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["2", "1"], ["3", "2"], ["4", "3"]],
    ["recursion", "memoization", "math", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE09["solution_url"] = "https://leetcode.cn/problems/fibonacci-number/solution/fei-bo-na-qi-shu-by-leetcode-solution-o4ze/"
PDE09["problem_url"] = "https://leetcode.cn/problems/fibonacci-number/"

PDE10 = mk(
    "DE10",
    "\u7b2c N \u4e2a\u6cf0\u6ce2\u90a3\u5951\u6570",
    "LeetCode 1137",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u6cf0\u6ce2\u90a3\u5951\u5e8f\u5217\u00a0Tn\u00a0\u5b9a\u4e49\u5982\u4e0b\uff1a\u00a0\n\nT0 = 0, T1 = 1, T2 = 1, \u4e14\u5728 n >= 0\u00a0\u7684\u6761\u4ef6\u4e0b Tn+3 = Tn + Tn+1 + Tn+2\n\n\u7ed9\u4f60\u6574\u6570\u00a0n\uff0c\u8bf7\u8fd4\u56de\u7b2c n \u4e2a\u6cf0\u6ce2\u90a3\u5951\u6570\u00a0Tn \u7684\u503c\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1an = 4\n\u8f93\u51fa\uff1a4\n\u89e3\u91ca\uff1a\nT_3 = 0 + 1 + 1 = 2\nT_4 = 1 + 1 + 2 = 4\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1an = 25\n\u8f93\u51fa\uff1a1389537\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t0 <= n <= 37\n\n\t\u7b54\u6848\u4fdd\u8bc1\u662f\u4e00\u4e2a 32 \u4f4d\u6574\u6570\uff0c\u5373\u00a0answer <= 2^31 - 1\u3002",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1an\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def tribonacci(self, n: int) -> int:\n        if n == 0:\n            return 0\n        if n <= 2:\n            return 1\n        \n        p = 0\n        q = r = 1\n        for i in range(3, n + 1):\n            s = p + q + r\n            p, q, r = q, r, s\n        return s\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.tribonacci(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["4", "4"], ["25", "1389537"]],
    ["memoization", "math", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE10["solution_url"] = "https://leetcode.cn/problems/n-th-tribonacci-number/solution/di-n-ge-tai-bo-na-qi-shu-by-leetcode-sol-kn16/"
PDE10["problem_url"] = "https://leetcode.cn/problems/n-th-tribonacci-number/"

PDE11 = mk(
    "DE11",
    "\u4e70\u5356\u80a1\u7968\u7684\u6700\u4f73\u65f6\u673a",
    "LeetCode 121",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u5b9a\u4e00\u4e2a\u6570\u7ec4 prices \uff0c\u5b83\u7684\u7b2c\u00a0i \u4e2a\u5143\u7d20\u00a0prices[i] \u8868\u793a\u4e00\u652f\u7ed9\u5b9a\u80a1\u7968\u7b2c i \u5929\u7684\u4ef7\u683c\u3002\n\n\u4f60\u53ea\u80fd\u9009\u62e9 \u67d0\u4e00\u5929 \u4e70\u5165\u8fd9\u53ea\u80a1\u7968\uff0c\u5e76\u9009\u62e9\u5728 \u672a\u6765\u7684\u67d0\u4e00\u4e2a\u4e0d\u540c\u7684\u65e5\u5b50 \u5356\u51fa\u8be5\u80a1\u7968\u3002\u8bbe\u8ba1\u4e00\u4e2a\u7b97\u6cd5\u6765\u8ba1\u7b97\u4f60\u6240\u80fd\u83b7\u53d6\u7684\u6700\u5927\u5229\u6da6\u3002\n\n\u8fd4\u56de\u4f60\u53ef\u4ee5\u4ece\u8fd9\u7b14\u4ea4\u6613\u4e2d\u83b7\u53d6\u7684\u6700\u5927\u5229\u6da6\u3002\u5982\u679c\u4f60\u4e0d\u80fd\u83b7\u53d6\u4efb\u4f55\u5229\u6da6\uff0c\u8fd4\u56de 0 \u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1a[7,1,5,3,6,4]\n\u8f93\u51fa\uff1a5\n\u89e3\u91ca\uff1a\u5728\u7b2c 2 \u5929\uff08\u80a1\u7968\u4ef7\u683c = 1\uff09\u7684\u65f6\u5019\u4e70\u5165\uff0c\u5728\u7b2c 5 \u5929\uff08\u80a1\u7968\u4ef7\u683c = 6\uff09\u7684\u65f6\u5019\u5356\u51fa\uff0c\u6700\u5927\u5229\u6da6 = 6-1 = 5 \u3002\n     \u6ce8\u610f\u5229\u6da6\u4e0d\u80fd\u662f 7-1 = 6, \u56e0\u4e3a\u5356\u51fa\u4ef7\u683c\u9700\u8981\u5927\u4e8e\u4e70\u5165\u4ef7\u683c\uff1b\u540c\u65f6\uff0c\u4f60\u4e0d\u80fd\u5728\u4e70\u5165\u524d\u5356\u51fa\u80a1\u7968\u3002\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1aprices = [7,6,4,3,1]\n\u8f93\u51fa\uff1a0\n\u89e3\u91ca\uff1a\u5728\u8fd9\u79cd\u60c5\u51b5\u4e0b, \u6ca1\u6709\u4ea4\u6613\u5b8c\u6210, \u6240\u4ee5\u6700\u5927\u5229\u6da6\u4e3a 0\u3002\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t1 5\n\n\t0 4",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1aprices\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\n# \u6b64\u65b9\u6cd5\u4f1a\u8d85\u65f6\nclass Solution:\n    def maxProfit(self, prices: List[int]) -> int:\n        ans = 0\n        for i in range(len(prices)):\n            for j in range(i + 1, len(prices)):\n                ans = max(ans, prices[j] - prices[i])\n        return ans\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.maxProfit(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["[7,1,5,3,6,4]", "5"], ["[7,6,4,3,1]", "0"]],
    ["array", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE11["solution_url"] = "https://leetcode.cn/problems/best-time-to-buy-and-sell-stock/solution/121-mai-mai-gu-piao-de-zui-jia-shi-ji-by-leetcode-/"
PDE11["problem_url"] = "https://leetcode.cn/problems/best-time-to-buy-and-sell-stock/"

PDE12 = mk(
    "DE12",
    "\u8fde\u7eed\u5929\u6570\u7684\u6700\u9ad8\u9500\u552e\u989d",
    "LeetCode LCR 161",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u67d0\u516c\u53f8\u6bcf\u65e5\u9500\u552e\u989d\u8bb0\u4e8e\u6574\u6570\u6570\u7ec4 sales\uff0c\u8bf7\u8fd4\u56de\u6240\u6709 \u8fde\u7eed \u4e00\u6216\u591a\u5929\u9500\u552e\u989d\u603b\u548c\u7684\u6700\u5927\u503c\u3002\n\n\u8981\u6c42\u5b9e\u73b0\u65f6\u95f4\u590d\u6742\u5ea6\u4e3a O(n) \u7684\u7b97\u6cd5\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1asales = [-2,1,-3,4,-1,2,1,-5,4]\n\u8f93\u51fa\uff1a6\n\u89e3\u91ca\uff1a[4,-1,2,1] \u6b64\u8fde\u7eed\u56db\u5929\u7684\u9500\u552e\u603b\u989d\u6700\u9ad8\uff0c\u4e3a 6\u3002\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1asales = [5,4,-1,7,8]\n\u8f93\u51fa\uff1a23\n\u89e3\u91ca\uff1a[5,4,-1,7,8] \u6b64\u8fde\u7eed\u4e94\u5929\u7684\u9500\u552e\u603b\u989d\u6700\u9ad8\uff0c\u4e3a 23\u3002\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t1 <=\u00a0arr.length <= 10^5\n\n\t-100 <= arr[i] <= 100\n\n\u6ce8\u610f\uff1a\u672c\u9898\u4e0e\u4e3b\u7ad9 53 \u9898\u76f8\u540c\uff1ahttps://leetcode.cn/problems/maximum-subarray/",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1asales\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\r\n    def maxSales(self, sales: List[int]) -> int:\r\n        for i in range(1, len(sales)):\r\n            sales[i] += max(sales[i - 1], 0)\r\n        return max(sales)\r\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.maxSales(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["[-2,1,-3,4,-1,2,1,-5,4]", "6"], ["[5,4,-1,7,8]", "23"]],
    ["array", "divide-and-conquer", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE12["solution_url"] = "https://leetcode.cn/problems/lian-xu-zi-shu-zu-de-zui-da-he-lcof/solution/mian-shi-ti-42-lian-xu-zi-shu-zu-de-zui-da-he-do-2/"
PDE12["problem_url"] = "https://leetcode.cn/problems/lian-xu-zi-shu-zu-de-zui-da-he-lcof/"

PDE13 = mk(
    "DE13",
    "\u8fde\u7eed\u6570\u5217",
    "LeetCode \u9762\u8bd5\u9898 16.17",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u5b9a\u4e00\u4e2a\u6574\u6570\u6570\u7ec4\uff0c\u627e\u51fa\u603b\u548c\u6700\u5927\u7684\u8fde\u7eed\u6570\u5217\uff0c\u5e76\u8fd4\u56de\u603b\u548c\u3002\n\n\u793a\u4f8b\uff1a\n\n```\n\u8f93\u5165\uff1a [-2,1,-3,4,-1,2,1,-5,4]\n\u8f93\u51fa\uff1a 6\n\u89e3\u91ca\uff1a \u8fde\u7eed\u5b50\u6570\u7ec4 [4,-1,2,1] \u7684\u548c\u6700\u5927\uff0c\u4e3a 6\u3002\n```\n\n\u8fdb\u9636\uff1a\n\n\u5982\u679c\u4f60\u5df2\u7ecf\u5b9e\u73b0\u590d\u6742\u5ea6\u4e3a O(n) \u7684\u89e3\u6cd5\uff0c\u5c1d\u8bd5\u4f7f\u7528\u66f4\u4e3a\u7cbe\u5999\u7684\u5206\u6cbb\u6cd5\u6c42\u89e3\u3002",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1anums\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def maxSubArray(self, nums: List[int]) -> int:\n        maxsum, sum = float('-inf'), float('-inf')\n        for i in nums:\n            sum = max(sum + i, i)\n            maxsum = max(sum, maxsum)\n        return maxsum\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.maxSubArray(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["[-2,1,-3,4,-1,2,1,-5,4]", "6"]],
    ["array", "divide-and-conquer", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE13["solution_url"] = "https://leetcode.cn/problems/contiguous-sequence-lcci/solution/fen-xi-python3-c-by-z1m/"
PDE13["problem_url"] = "https://leetcode.cn/problems/contiguous-sequence-lcci/"

PDE14 = mk(
    "DE14",
    "\u722c\u697c\u68af",
    "LeetCode 70",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u5047\u8bbe\u4f60\u6b63\u5728\u722c\u697c\u68af\u3002\u9700\u8981 n\u00a0\u9636\u4f60\u624d\u80fd\u5230\u8fbe\u697c\u9876\u3002\n\n\u6bcf\u6b21\u4f60\u53ef\u4ee5\u722c 1 \u6216 2 \u4e2a\u53f0\u9636\u3002\u4f60\u6709\u591a\u5c11\u79cd\u4e0d\u540c\u7684\u65b9\u6cd5\u53ef\u4ee5\u722c\u5230\u697c\u9876\u5462\uff1f\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1an = 2\n\u8f93\u51fa\uff1a2\n\u89e3\u91ca\uff1a\u6709\u4e24\u79cd\u65b9\u6cd5\u53ef\u4ee5\u722c\u5230\u697c\u9876\u3002\n1. 1 \u9636 + 1 \u9636\n2. 2 \u9636\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1an = 3\n\u8f93\u51fa\uff1a3\n\u89e3\u91ca\uff1a\u6709\u4e09\u79cd\u65b9\u6cd5\u53ef\u4ee5\u722c\u5230\u697c\u9876\u3002\n1. 1 \u9636 + 1 \u9636 + 1 \u9636\n2. 1 \u9636 + 2 \u9636\n3. 2 \u9636 + 1 \u9636\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t1 <= n <= 45",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1an\u3002",
    "\u8f93\u51fa integer \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def climbStairs(self, n: int) -> int:\n        a, b = 1, 1\n        for _ in range(n - 1):\n            a, b = b, a + b\n        return b\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.climbStairs(_args[0])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "int",
    [["2", "2"], ["3", "3"]],
    ["memoization", "math", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE14["solution_url"] = "https://leetcode.cn/problems/climbing-stairs/solution/70-pa-lou-ti-dong-tai-gui-hua-qing-xi-tu-ruwa/"
PDE14["problem_url"] = "https://leetcode.cn/problems/climbing-stairs/"

PDE15 = mk(
    "DE15",
    "\u5224\u65ad\u5b50\u5e8f\u5217",
    "LeetCode 392",
    "easy",
    "\u52a8\u6001\u89c4\u5212",
    "\u7ed9\u5b9a\u5b57\u7b26\u4e32 s \u548c t \uff0c\u5224\u65ad s \u662f\u5426\u4e3a t \u7684\u5b50\u5e8f\u5217\u3002\n\n\u5b57\u7b26\u4e32\u7684\u4e00\u4e2a\u5b50\u5e8f\u5217\u662f\u539f\u59cb\u5b57\u7b26\u4e32\u5220\u9664\u4e00\u4e9b\uff08\u4e5f\u53ef\u4ee5\u4e0d\u5220\u9664\uff09\u5b57\u7b26\u800c\u4e0d\u6539\u53d8\u5269\u4f59\u5b57\u7b26\u76f8\u5bf9\u4f4d\u7f6e\u5f62\u6210\u7684\u65b0\u5b57\u7b26\u4e32\u3002\uff08\u4f8b\u5982\uff0c\"ace\"\u662f\"abcde\"\u7684\u4e00\u4e2a\u5b50\u5e8f\u5217\uff0c\u800c\"aec\"\u4e0d\u662f\uff09\u3002\n\n\u8fdb\u9636\uff1a\n\n\u5982\u679c\u6709\u5927\u91cf\u8f93\u5165\u7684 S\uff0c\u79f0\u4f5c S1, S2, ... , Sk \u5176\u4e2d k >= 10\u4ebf\uff0c\u4f60\u9700\u8981\u4f9d\u6b21\u68c0\u67e5\u5b83\u4eec\u662f\u5426\u4e3a T \u7684\u5b50\u5e8f\u5217\u3002\u5728\u8fd9\u79cd\u60c5\u51b5\u4e0b\uff0c\u4f60\u4f1a\u600e\u6837\u6539\u53d8\u4ee3\u7801\uff1f\n\n\u81f4\u8c22\uff1a\n\n\u7279\u522b\u611f\u8c22 @pbrother\u00a0\u6dfb\u52a0\u6b64\u95ee\u9898\u5e76\u4e14\u521b\u5efa\u6240\u6709\u6d4b\u8bd5\u7528\u4f8b\u3002\n\n\u00a0\n\n\u793a\u4f8b 1\uff1a\n\n```\n\u8f93\u5165\uff1as = \"abc\", t = \"ahbgdc\"\n\u8f93\u51fa\uff1atrue\n```\n\n\u793a\u4f8b 2\uff1a\n\n```\n\u8f93\u5165\uff1as = \"axc\", t = \"ahbgdc\"\n\u8f93\u51fa\uff1afalse\n```\n\n\u00a0\n\n\u63d0\u793a\uff1a\n\n\t0\n\n\t0\n\n\t\u4e24\u4e2a\u5b57\u7b26\u4e32\u90fd\u53ea\u7531\u5c0f\u5199\u5b57\u7b26\u7ec4\u6210\u3002",
    "\u6bcf\u884c\u4e00\u4e2a\u53c2\u6570\uff08JSON \u683c\u5f0f\uff09\uff0c\u4f9d\u6b21\u4e3a\uff1as\u3001t\u3002",
    "\u8f93\u51fa boolean \u7c7b\u578b\u7ed3\u679c\uff08JSON \u5e8f\u5217\u5316\uff09\u3002",
    "",
    "import sys, json\nimport itertools, functools, collections, math, bisect, string, heapq, random, operator\nfrom typing import *\nfrom collections import *\nfrom itertools import *\nfrom bisect import *\nfrom functools import *\nfrom math import *\nfrom string import *\nfrom operator import *\n\nclass Solution:\n    def isSubsequence(self, s: str, t: str) -> bool:\n        n, m = len(s), len(t)\n        i = j = 0\n        while i < n and j < m:\n            if s[i] == t[j]:\n                i += 1\n            j += 1\n        return i == n\n\ndef main():\n    _dec = json.JSONDecoder()\n    _text = sys.stdin.read()\n    _idx = 0\n    _args = []\n    while _idx < len(_text):\n        while _idx < len(_text) and _text[_idx] in ' \\t\\r\\n':\n            _idx += 1\n        if _idx >= len(_text):\n            break\n        try:\n            _obj, _end = _dec.raw_decode(_text, _idx)\n            _args.append(_obj)\n            _idx = _end\n        except Exception:\n            _nl = _text.find('\\n', _idx)\n            if _nl == -1:\n                _idx = len(_text)\n            else:\n                _idx = _nl + 1\n    _sol = Solution()\n\n    _ret = _sol.isSubsequence(_args[0], _args[1])\n    if _ret is None:\n        _out = ''\n    elif isinstance(_ret, (list, dict)):\n        _out = json.dumps(_ret, separators=(',', ':'))\n    elif isinstance(_ret, bool):\n        _out = 'true' if _ret else 'false'\n    elif isinstance(_ret, float):\n        _out = repr(_ret)\n    else:\n        _out = str(_ret)\n    sys.stdout.write(_out)\n\nmain()\n",
    "bool",
    [["\"abc\"\n\"ahbgdc\"", "true"], ["\"axc\"\n\"ahbgdc\"", "false"]],
    ["two-pointers", "string", "dynamic-programming", "\u52a8\u6001\u89c4\u5212"],
    )
PDE15["solution_url"] = "https://leetcode.cn/problems/is-subsequence/solution/pan-duan-zi-xu-lie-by-leetcode-solution/"
PDE15["problem_url"] = "https://leetcode.cn/problems/is-subsequence/"

PROBLEMS = [PDE01, PDE02, PDE03, PDE04, PDE05, PDE06, PDE07, PDE08, PDE09, PDE10, PDE11, PDE12, PDE13, PDE14, PDE15]