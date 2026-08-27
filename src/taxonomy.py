"""错误分类体系（Error Taxonomy）。

任务要求建立错误分类体系，例如：题意误读、概念理解错误、计算错误、
条件遗漏、跳步推导、格式不符等。这里在任务示例基础上扩充为可操作的
分类，并为每个类别给出可判定的特征，供 LLM-as-judge 与规则评估器共用。
"""

# 错误类型 -> 中文名
ERROR_TYPES = {
    "misread_problem": "题意误读",
    "concept_error": "概念理解错误",
    "calculation_error": "计算错误",
    "condition_omission": "条件遗漏",
    "step_skip": "跳步推导",
    "logic_error": "逻辑错误",
    "complexity_error": "复杂度/效率错误",
    "format_error": "格式不符",
    "hallucination": "幻觉/虚构",
    "boundary_error": "边界处理错误",
}

# 每个错误类型的可操作判定特征（供评估器使用）
ERROR_SIGNALS = {
    "misread_problem": [
        "把输入规模/含义理解错（如把 n 当成值而非长度）",
        "忽略输出要求（如要求返回索引却返回数值）",
        "混淆题意中的相等/包含/相邻等关系",
    ],
    "concept_error": [
        "误用数据结构特性（如认为无序数组可二分）",
        "对算法前提理解错误（如 Dijkstra 用于负权边）",
        "错误使用语言/库语义（如 sort 稳定性、深浅拷贝）",
    ],
    "calculation_error": [
        "算术/下标越界或差一错误（off-by-one）",
        "累加/累乘初值或更新式写错",
        "取模、整除、浮点比较处理错误",
    ],
    "condition_omission": [
        "遗漏题目给定的约束条件（如去重、正整数、非空）",
        "未处理特殊取值（0、负数、相等元素）",
        "忽略输入为空/单元素等退化情况",
    ],
    "step_skip": [
        "推理链中存在未说明的跳跃（如直接给出结论无推导）",
        "关键归纳/状态转移缺失证明或说明",
        "用'显然''易得'替代必要推导",
    ],
    "logic_error": [
        "状态转移或循环不变量错误",
        "贪心/DP 决策错误",
        "边界更新或指针移动方向错误",
    ],
    "complexity_error": [
        "声称的复杂度与实际代码不符（如声称 O(n) 但嵌套循环 O(n^2)）",
        "复杂度分析遗漏外层循环或递归深度",
    ],
    "format_error": [
        "输出格式与要求不符（多余空格、缺括号、顺序错）",
        "未按约定解析/输出（如未处理多组用例）",
    ],
    "hallucination": [
        "虚构不存在的 API/函数/定理",
        "捏造复杂度或正确性结论",
        "引用不存在的测试用例结果",
    ],
    "boundary_error": [
        "空输入/单元素/满容量未处理",
        "整数溢出或极端值未考虑",
        "首尾元素、重复元素未正确处理",
    ],
}

# 粗粒度归类（用于验证阶段的误差容忍与统计）
COARSE_CATEGORY = {
    "misread_problem": "understanding",
    "concept_error": "understanding",
    "calculation_error": "execution",
    "condition_omission": "execution",
    "step_skip": "reasoning",
    "logic_error": "execution",
    "complexity_error": "analysis",
    "format_error": "execution",
    "hallucination": "reasoning",
    "boundary_error": "execution",
}


def describe(error_type: str) -> str:
    name = ERROR_TYPES.get(error_type, error_type)
    signals = ERROR_SIGNALS.get(error_type, [])
    if not signals:
        return name
    return f"{name}：{'; '.join(signals)}"


# ----------------------------- 执行 verdict 层级 -----------------------------
# 借鉴竞赛编程「可执行验证(ERV)」的判题层级（AC/WA/TLE/RE/CE），
# 参考 Wei et al. (arXiv:2506.22954) 与 arXiv:2606.05228 的失败模式划分。
VERDICT_TYPES = {
    "AC": "Accepted · 通过（输出与期望一致）",
    "WA": "Wrong Answer · 输出错误",
    "TLE": "Time Limit Exceeded · 超时（疑似复杂度/效率问题）",
    "RE": "Runtime Error · 运行异常（越界/除零/类型等）",
    "CE": "Compile Error · 语法/编译错误",
}


# verdict -> 候选错误细类（供规则评估器在缺乏 LLM 时做可判定归因）
VERDICT_HINTS = {
    "TLE": ["complexity_error"],
    "RE": ["boundary_error", "condition_omission", "calculation_error"],
    "WA": ["logic_error", "calculation_error", "concept_error", "misread_problem"],
    "CE": ["format_error"],
}


# ----------------------------- 两级分类体系（粗类 -> 细类） -----------------------------
# 融合任务要求的基础分类与 Wei et al. (arXiv:2506.22954) 的层次化
# 竞赛编程错误分类（通用错误 + 领域专用错误）。
TAXONOMY_TREE = [
    {
        "coarse": "understanding", "name": "题意理解",
        "fine": [
            ("misread_problem", "题意误读：误解输入规模/输出要求/关系语义"),
            ("concept_error", "概念理解错误：误用数据结构/算法前提/语言语义"),
        ],
    },
    {
        "coarse": "approach", "name": "思路与建模",
        "fine": [
            ("concept_error", "方法选择错误：思路阶段选错算法或建模方式"),
            ("step_skip", "跳步推导：推理链存在未说明的跳跃"),
            ("hallucination", "幻觉/虚构：虚构 API/定理/结论"),
        ],
    },
    {
        "coarse": "analysis", "name": "复杂度分析",
        "fine": [
            ("complexity_error", "复杂度/效率错误：声称与实现不符或分析遗漏"),
        ],
    },
    {
        "coarse": "execution", "name": "实现与执行",
        "fine": [
            ("logic_error", "逻辑错误：状态转移/循环不变量/指针方向错误"),
            ("calculation_error", "计算错误：算术/下标/取模/浮点处理错误"),
            ("condition_omission", "条件遗漏：遗漏约束或退化情况"),
            ("boundary_error", "边界处理错误：空/单元素/极值/溢出未处理"),
            ("format_error", "格式不符：输出格式或解析方式不符"),
        ],
    },
]


def coarse_of(error_type: str) -> str:
    return COARSE_CATEGORY.get(error_type, "execution")
