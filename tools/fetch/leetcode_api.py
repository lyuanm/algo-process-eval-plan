# -*- coding: utf-8 -*-
"""LeetCode 中国站官方 API 客户端。

数据来源（100% 官方）：
  1. questionData        —— 题目（标题/难度/描述/官方样例/codeSnippets/metaData）
  2. questionSolutionArticles —— 官方题解文章列表
  3. solutionDetailArticle     —— 官方题解文章全文（含官方代码，语言标记 ```Python）

用法：
    api = LeetCodeCN()
    q = api.get_question("two-sum")          # 题目详情（带缓存）
    art = api.get_official_solution("two-sum")  # 官方题解文章（带缓存）
"""
import json
import os
import re
import time
import urllib.request

GRAPHQL_URL = "https://leetcode.cn/graphql/"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fetch_cache")
CACHE_DIR = os.path.abspath(CACHE_DIR)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def _safe_name(s):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', s)


class LeetCodeCN:
    def __init__(self, delay=1.2, cache=True):
        self.delay = delay
        self.cache = cache
        os.makedirs(CACHE_DIR, exist_ok=True)

    # ---------- 底层请求 ----------
    def _post(self, payload, referer):
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            GRAPHQL_URL, data=body, method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": UA,
                "Referer": referer,
                "Origin": "https://leetcode.cn",
                "Accept": "application/json",
            })
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 + attempt * 2)
        raise RuntimeError("unreachable")

    def _cached(self, name, fetcher):
        path = os.path.join(CACHE_DIR, name + ".json")
        if self.cache and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        data = fetcher()
        time.sleep(self.delay)  # 节流，避免 429
        if self.cache:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        return data

    # ---------- 题目详情 ----------
    def get_question(self, slug):
        """题目详情：title/difficulty/content/exampleTestcases/codeSnippets/metaData/中文标题"""
        def fetcher():
            payload = {
                "operationName": "questionData",
                "variables": {"titleSlug": slug},
                "query": """query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId questionFrontendId title titleSlug translatedTitle
    difficulty isPaidOnly content translatedContent
    exampleTestcases sampleTestCase metaData
    codeSnippets { lang langSlug code }
    topicTags { name slug translatedName }
  }
}""",
            }
            d = self._post(payload, f"https://leetcode.cn/problems/{slug}/")
            q = d.get("data", {}).get("question")
            if q is None:
                raise RuntimeError(f"question not found: {slug}")
            return q
        return self._cached("q_" + _safe_name(slug), fetcher)

    # ---------- 官方题解文章列表 ----------
    def get_official_article_list(self, slug):
        """返回官方题解文章列表（可能有多篇，第一篇通常为官方）"""
        def fetcher():
            payload = {
                "operationName": "questionSolutionArticles",
                "variables": {"questionSlug": slug, "first": 8, "skip": 0,
                              "orderBy": "DEFAULT", "userInput": "", "tagSlugs": []},
                "query": """query questionSolutionArticles($questionSlug: String!, $skip: Int, $first: Int, $orderBy: SolutionArticleOrderBy, $userInput: String, $tagSlugs: [String!]) {
  questionSolutionArticles(questionSlug: $questionSlug, skip: $skip, first: $first, orderBy: $orderBy, userInput: $userInput, tagSlugs: $tagSlugs) {
    edges { node { title slug } }
  }
}""",
            }
            d = self._post(payload, f"https://leetcode.cn/problems/{slug}/solution/")
            return d.get("data", {}).get("questionSolutionArticles", {}).get("edges", [])
        return self._cached("slist_" + _safe_name(slug), fetcher)

    # ---------- 题解文章全文 ----------
    def get_article(self, article_slug):
        """题解文章全文（markdown，含官方代码块）"""
        def fetcher():
            payload = {
                "operationName": "solutionDetailArticle",
                "variables": {"slug": article_slug, "orderBy": "DEFAULT"},
                "query": """query solutionDetailArticle($slug: String!, $orderBy: SolutionArticleOrderBy!) {
  solutionArticle(slug: $slug, orderBy: $orderBy) {
    title slug content
    question { questionTitleSlug }
  }
}""",
            }
            d = self._post(payload, f"https://leetcode.cn/problems/solution/{article_slug}/")
            art = d.get("data", {}).get("solutionArticle")
            if art is None:
                raise RuntimeError(f"article not found: {article_slug}")
            return art
        return self._cached("art_" + _safe_name(article_slug), fetcher)

    # ---------- 组合：官方题解（提取 Python 代码） ----------
    def get_official_python(self, slug):
        """返回 (article_title, [python代码列表], article_url)。
        优先官方题解文章（标题含 leetcode-solution），否则取列表第一篇。
        找不到 Python 代码返回 (None, [], None)。
        """
        try:
            edges = self.get_official_article_list(slug)
        except Exception:
            return None, [], None
        if not edges:
            return None, [], None
        # 优先官方题解
        ordered = sorted(edges, key=lambda e: 0 if "leetcode-solution" in e["node"]["slug"] else 1)
        for e in ordered:
            art_slug = e["node"]["slug"]
            try:
                art = self.get_article(art_slug)
            except Exception:
                continue
            codes = extract_python_blocks(art["content"])
            if codes:
                return art["title"], codes, art_slug
        return None, [], None


def extract_python_blocks(md):
    """从题解 markdown 中提取所有 Python 代码块（支持 ```Python [xxx]、```python3 等）。"""
    blocks = []
    for m in re.finditer(r'```(?:Python|python3?)\s*\[?[^\n]*?\n(.*?)```', md, re.S):
        code = m.group(1).strip("\n")
        if code and ("class Solution" in code or "def " in code):
            blocks.append(code)
    # 兜底：```python 裸围栏
    if not blocks:
        for m in re.finditer(r'```(?:python3?)\s*\n(.*?)```', md, re.S):
            code = m.group(1).strip("\n")
            if code and "def " in code:
                blocks.append(code)
    return blocks
