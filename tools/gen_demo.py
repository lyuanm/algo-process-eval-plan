"""生成 data-driven 交互式 Web UI：demo/index.html。

读取真实评测数据（题集目录、样本、rule/llm 评测结果、验证指标、分类体系），
注入为内联 JSON，输出自包含、可离线打开的单文件页面。页面包含：
  - 概览：指标卡 + 错误类型/verdict 分布 + rule vs llm 一致性
  - 样本探查：按类别筛选，步骤级热力、错误定位高亮、rule/llm 对比、原始过程
  - 题集浏览：难度/来源/领域筛选与检索
  - 分类体系：两级错误分类 + verdict 层级参考

运行：python tools/gen_demo.py  ->  demo/index.html
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PROBLEMS = os.path.join(ROOT, "data", "problems.json")
SAMPLES = os.path.join(ROOT, "data", "samples.json")
RES_DIR = os.path.join(ROOT, "eval", "results")
OUT = os.path.join(ROOT, "demo", "index.html")

sys_path = ROOT
import sys as _sys
_sys.path.insert(0, ROOT)
from src.problems import load_problems, build_catalog  # noqa: E402
from src.taxonomy import TAXONOMY_TREE, VERDICT_TYPES  # noqa: E402


def parse_for_ui(raw: str):
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", raw, re.DOTALL)
    code = m.group(1).strip() if m else ""
    reasoning = raw
    if m:
        reasoning = (raw[: m.start()] + raw[m.end():]).strip()
    steps = {"思路/建模": "", "复杂度分析": "", "边界与处理": "", "代码实现": code}
    for p in re.split(r"##\s*", reasoning):
        if not p.strip():
            continue
        head = p.strip().splitlines()[0]
        body = "\n".join(p.strip().splitlines()[1:])
        if "思路" in head or "建模" in head:
            steps["思路/建模"] += body + "\n"
        elif "复杂度" in head:
            steps["复杂度分析"] += body + "\n"
        elif "边界" in head or "处理" in head:
            steps["边界与处理"] += body + "\n"
    return steps


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    problems = load_problems(PROBLEMS)
    catalog = build_catalog(problems)
    with open(SAMPLES, "r", encoding="utf-8") as f:
        samples = json.load(f)
    eval_rule = load_jsonl(os.path.join(RES_DIR, "evaluation_results.jsonl"))
    eval_llm = load_jsonl(os.path.join(RES_DIR, "evaluation_results_llm.jsonl"))
    verification = {}
    vpath = os.path.join(RES_DIR, "verification.json")
    if os.path.exists(vpath):
        with open(vpath, "r", encoding="utf-8") as f:
            verification = json.load(f)

    rule_by_id = {e["sample_id"]: e for e in eval_rule}
    llm_by_id = {e["sample_id"]: e for e in eval_llm}

    # 样本展示数据
    sample_views = []
    for s in samples:
        gt = s.get("ground_truth", {})
        if gt.get("final_correct") is False:
            kind = "wrong"
        elif gt.get("process_valid") is False:
            kind = "process_invalid"
        else:
            kind = "correct"
        steps = parse_for_ui(s["reasoning"])
        sample_views.append({
            "sample_id": s["sample_id"],
            "problem_id": s["problem_id"],
            "kind": kind,
            "gt": gt,
            "comment": gt.get("comment", ""),
            "steps": steps,
            "rule": rule_by_id.get(s["sample_id"]),
            "llm": llm_by_id.get(s["sample_id"]),
        })

    # rule vs llm 一致性
    agree_pv = 0
    agree_et = 0
    both = 0
    for sid in rule_by_id:
        if sid in llm_by_id:
            both += 1
            if rule_by_id[sid]["process_valid"] == llm_by_id[sid]["process_valid"]:
                agree_pv += 1
            if (rule_by_id[sid]["error_type"] or None) == (llm_by_id[sid]["error_type"] or None):
                agree_et += 1

    # 错误类型分布（以 rule 为主，含 llm 对照）
    et_rule = {}
    for e in eval_rule:
        et = e.get("error_type") or "none"
        et_rule[et] = et_rule.get(et, 0) + 1
    et_llm = {}
    for e in eval_llm:
        et = e.get("error_type") or "none"
        et_llm[et] = et_llm.get(et, 0) + 1

    # verdict 分布（解析 verdict_summary，如 "AC:3 WA:1"）
    verdict_counts = {}
    for e in eval_rule:
        for part in (e.get("verdict_summary") or "").split():
            if ":" in part:
                k, v = part.split(":", 1)
                try:
                    verdict_counts[k] = verdict_counts.get(k, 0) + int(v)
                except ValueError:
                    pass

    problem_views = [
        {
            "id": p.id, "title": p.title, "difficulty": p.difficulty,
            "domain": p.domain, "source": p.source, "tags": p.tags,
            "n_tests": len(p.test_cases), "n_stress": len(p.stress_inputs),
        }
        for p in problems
    ]

    DATA = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_problems": len(problems),
        "n_samples": len(samples),
        "has_llm": bool(eval_llm),
        "catalog": catalog,
        "verification": verification,
        "sample_views": sample_views,
        "et_rule": et_rule,
        "et_llm": et_llm,
        "verdict_counts": verdict_counts,
        "agreement": {"both": both, "process_valid": agree_pv, "error_type": agree_et},
        "problems": problem_views,
        "taxonomy": TAXONOMY_TREE,
        "verdict_types": VERDICT_TYPES,
    }

    html = TEMPLATE.replace("__DATA__", json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {len(sample_views)} samples / {len(problems)} problems -> {os.path.relpath(OUT)}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>混元算法题 · 过程评估与错误定位 · 交互报告</title>
<style>
:root{--bg:#f6f8fb;--card:#fff;--ink:#1f2329;--muted:#6b7280;--line:#e6e9ef;
 --blue:#2563eb;--green:#16a34a;--red:#dc2626;--amber:#d97706;--chip:#eef2ff;--violet:#7c3aed;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
 background:var(--bg);color:var(--ink);line-height:1.6}
.wrap{max-width:1100px;margin:0 auto;padding:22px 18px 70px}
h1{font-size:23px;margin:0 0 4px}
.sub{color:var(--muted);font-size:13.5px;margin-bottom:18px}
.pipeline{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 22px}
.stage{flex:1 1 200px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px;position:relative}
.stage .num{display:inline-flex;width:23px;height:23px;border-radius:50%;background:var(--blue);color:#fff;
 align-items:center;justify-content:center;font-size:12px;font-weight:700;margin-right:7px}
.stage h3{font-size:14px;margin:0 0 5px;display:inline}
.stage p{font-size:12px;color:var(--muted);margin:6px 0 0}
.tabs{display:flex;gap:8px;border-bottom:1px solid var(--line);margin-bottom:18px;flex-wrap:wrap}
.tab{padding:9px 14px;cursor:pointer;border:1px solid transparent;border-bottom:none;border-radius:8px 8px 0 0;
 font-size:14px;color:var(--muted)}
.tab.active{background:var(--card);border-color:var(--line);color:var(--blue);font-weight:600}
.panel{display:none}.panel.active{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.card h2{font-size:16px;margin:0 0 10px}
.grid{display:flex;gap:12px;flex-wrap:wrap}
.kpi{flex:1 1 150px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi .v{font-size:26px;font-weight:800}
.kpi .l{font-size:12.5px;color:var(--muted);margin-top:2px}
.kpi .d{font-size:11.5px;color:var(--muted);margin-top:6px}
.tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600;margin-right:5px}
.t-bad{background:#fee2e2;color:var(--red)}.t-good{background:#dcfce7;color:var(--green)}
.t-warn{background:#fef3c7;color:var(--amber)}.t-info{background:var(--chip);color:var(--blue)}
.t-vio{background:#ede9fe;color:var(--violet)}
pre{background:#0f172a;color:#e2e8f0;padding:12px 14px;border-radius:8px;overflow:auto;font-size:12.5px}
code{font-family:"SF Mono",Consolas,Menlo,monospace}
.mut{color:var(--muted);font-size:12.5px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.fbtn{padding:6px 12px;border:1px solid var(--line);border-radius:999px;background:var(--card);
 cursor:pointer;font-size:13px}.fbtn.active{background:var(--blue);color:#fff;border-color:var(--blue)}
.list{display:flex;flex-direction:column;gap:8px}
.item{display:flex;justify-content:space-between;align-items:center;padding:10px 13px;border:1px solid var(--line);
 border-radius:10px;background:var(--card);cursor:pointer}
.item:hover{border-color:var(--blue)}
.item .tt{font-size:14px}.item .mt{font-size:12px;color:var(--muted)}
.detail{margin-top:12px}
.steps{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:12px 0}
.step{border:1px solid var(--line);border-radius:10px;padding:11px;background:var(--card)}
.step.ok{border-left:4px solid var(--green)}.step.bad{border-left:4px solid var(--red)}
.step .h{font-weight:700;font-size:13.5px;display:flex;justify-content:space-between}
.step .b{font-size:12.5px;color:#374151;white-space:pre-wrap;max-height:160px;overflow:auto;margin-top:4px}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}
.search{padding:8px 11px;border:1px solid var(--line);border-radius:8px;width:100%;max-width:320px;font-size:13.5px}
.tbl{width:100%;border-collapse:collapse;font-size:13px}
.tbl th,.tbl td{border:1px solid var(--line);padding:7px 9px;text-align:left}
.tbl th{background:#f1f5f9}
.small{font-size:12px;color:var(--muted)}
svg{display:block}
.chiprow{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.pill{font-size:11.5px;background:var(--chip);color:var(--blue);padding:2px 8px;border-radius:999px}
.foot{color:var(--muted);font-size:12px;margin-top:22px;border-top:1px solid var(--line);padding-top:12px}
</style>
</head>
<body>
<div class="wrap">
  <h1>混元算法题 · 过程评估与错误定位 · 交互报告</h1>
  <div class="sub">数据驱动视图：题集覆盖度、样本级过程判定（步骤热力 / 错误定位）、rule 与 llm 后端对比、分类体系参考。
    <span id="meta" class="mut"></span></div>

  <div class="pipeline">
    <div class="stage"><span class="num">1</span><h3>题目</h3><p>算法题 + 可自动校验 checker（LeetCode/洛谷）</p></div>
    <div class="stage"><span class="num">2</span><h3>解题</h3><p>Hy3 产出完整过程：思路/复杂度/边界/代码</p></div>
    <div class="stage"><span class="num">3</span><h3>沙盒 ERV</h3><p>子进程执行，输出 AC/WA/TLE/RE/CE 细粒度 verdict</p></div>
    <div class="stage"><span class="num">4</span><h3>过程评估</h3><p>步骤判定 / 错误定位 / 错误归类 / 答案对过程错识别</p></div>
  </div>

  <div class="tabs">
    <div class="tab active" data-t="overview">概览</div>
    <div class="tab" data-t="samples">样本探查</div>
    <div class="tab" data-t="bank">题集浏览</div>
    <div class="tab" data-t="tax">分类体系</div>
  </div>

  <!-- 概览 -->
  <div class="panel active" id="overview">
    <div class="grid" id="kpis"></div>
    <div class="card">
      <h2>错误类型分布（过程不成立样本）</h2>
      <div id="chart_et" style="display:flex;gap:24px;flex-wrap:wrap"></div>
    </div>
    <div class="grid">
      <div class="card" style="flex:1 1 320px">
        <h2>执行 verdict 分布（ERV）</h2>
        <div id="chart_v"></div>
      </div>
      <div class="card" style="flex:1 1 320px">
        <h2>题集覆盖度</h2>
        <div id="chart_cat"></div>
      </div>
    </div>
    <div class="card" id="verify_card"></div>
  </div>

  <!-- 样本探查 -->
  <div class="panel" id="samples">
    <div class="filters" id="sample_filters"></div>
    <div class="grid">
      <div style="flex:1 1 320px"><div class="list" id="sample_list"></div></div>
      <div style="flex:1 1 480px" id="sample_detail"></div>
    </div>
  </div>

  <!-- 题集 -->
  <div class="panel" id="bank">
    <input class="search" id="bank_search" placeholder="检索 题号/标题/来源/标签…">
    <div class="filters" id="bank_filters"></div>
    <div class="list" id="bank_list"></div>
  </div>

  <!-- 分类体系 -->
  <div class="panel" id="tax">
    <div class="card">
      <h2>两级错误分类体系（粗类 → 细类）</h2>
      <div id="tax_tree"></div>
    </div>
    <div class="card">
      <h2>可执行验证 verdict 层级（AC/WA/TLE/RE/CE）</h2>
      <div id="tax_verdict"></div>
    </div>
  </div>

  <div class="foot">个人/活动作品，非腾讯官方发布。评估方法参考 ProcessBench(Zheng'24)、PRMBench(Song'25)、
    ThinkPRM(Khalifa'25)、GenPRM(Zhao'25)、JETTS(Zhou'25,ICML)、Wei'25 竞赛编程错误分类(arXiv:2506.22954) 等近年工作。</div>
</div>

<script id="DATA" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('DATA').textContent);
document.getElementById('meta').textContent = `（生成于 ${D.generated_at} · 题集 ${D.total_problems} 题 · 样本 ${D.n_samples} 条${D.has_llm?' · 含 LLM 评测':''}）`;

// 标签切换
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active'); document.getElementById(t.dataset.t).classList.add('active');
});

const ET_NAME = {none:'无（过程成立）',misread_problem:'题意误读',concept_error:'概念理解错误',
 calculation_error:'计算错误',condition_omission:'条件遗漏',step_skip:'跳步推导',logic_error:'逻辑错误',
 complexity_error:'复杂度/效率错误',format_error:'格式不符',hallucination:'幻觉/虚构',boundary_error:'边界处理错误'};
const VCOLOR = {AC:'#16a34a',WA:'#dc2626',TLE:'#d97706',RE:'#7c3aed',CE:'#0891b2'};
const KIND_NAME = {correct:'正确且过程成立',process_invalid:'答案对·过程错',wrong:'答案错误'};
const KIND_CLASS = {correct:'t-good',process_invalid:'t-warn',wrong:'t-bad'};

// 简易横向柱状图（返回 HTML 字符串）
function bar(items, color){
  const max = Math.max(1, ...items.map(i=>i.v));
  let html = '<div style="font-size:13px">';
  items.forEach(it=>{
    const w = Math.round(it.v/max*100);
    const label = it.label || it.k;
    html += `<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
      <div style="width:130px;color:#374151;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${label}</div>
      <div style="flex:1;background:#eef2f7;border-radius:4px;overflow:hidden">
        <div style="width:${w}%;background:${color};height:16px"></div></div>
      <div style="width:34px;text-align:right;color:#374151">${it.v}</div></div>`;
  });
  html += '</div>';
  return html;
}

// ---------- 概览 ----------
(function(){
  const v = D.verification || {};
  const la = (v.localization_accuracy||{});
  const fp = (v.false_positive_rate||{});
  const kpis = [
    {v:D.total_problems,l:'算法题总数',d:'LeetCode / 洛谷 官方题源'},
    {v:D.n_samples,l:'评测样本数',d:'含正确/过程错/误报/错误'},
    {v:(la.accuracy!=null?Math.round(la.accuracy*100)+'%':'—'),l:'错误定位准确率',d:`${la.hits||0}/${la.denominator||0} 命中（rule）`},
    {v:(fp.fp_rate!=null?Math.round(fp.fp_rate*100)+'%':'—'),l:'误报率',d:`${fp.false_positives||0}/${fp.flagged_invalid||0} 被判无效为误报`},
  ];
  if(D.has_llm && D.agreement.both){
    kpis.push({v:Math.round(D.agreement.process_valid/D.agreement.both*100)+'%',l:'rule/llm 过程判定一致',d:`${D.agreement.both} 条双评`});
  }
  document.getElementById('kpis').innerHTML = kpis.map(k=>
    `<div class="kpi"><div class="v">${k.v}</div><div class="l">${k.l}</div><div class="d">${k.d}</div></div>`).join('');

  const etItems = Object.entries(D.et_rule).map(([k,v])=>({k:ET_NAME[k]||k,v})).sort((a,b)=>b.v-a.v);
  const etHtml = `<div style="flex:1 1 320px"><div class="small" style="margin-bottom:4px">Rule 后端</div>${bar(etItems,'#2563eb')}</div>`;
  let llmHtml='';
  if(D.has_llm){
    const et2 = Object.entries(D.et_llm).map(([k,v])=>({k:ET_NAME[k]||k,v})).sort((a,b)=>b.v-a.v);
    llmHtml = `<div style="flex:1 1 320px"><div class="small" style="margin-bottom:4px">LLM 后端</div>${bar(et2,'#7c3aed')}</div>`;
  }
  document.getElementById('chart_et').innerHTML = etHtml + llmHtml;

  const vc = Object.entries(D.verdict_counts).map(([k,v])=>({k,label:k,v}));
  document.getElementById('chart_v').innerHTML = bar( vc.map(x=>({k:`${x.k}`,v:x.v})), '#0891b2');

  const cat = D.catalog;
  const diff = Object.entries(cat.by_difficulty||{}).map(([k,v])=>({k:k,v}));
  const src = Object.entries(cat.by_source||{}).map(([k,v])=>({k,v}));
  document.getElementById('chart_cat').innerHTML =
    `<div style="flex:1 1 200px"><div class="small">难度</div>${bar(diff,'#16a34a')}</div>`+
    `<div style="flex:1 1 200px"><div class="small">来源</div>${bar(src,'#d97706')}</div>`;

  let vc2='';
  if(v.localization_accuracy){
    const d = v.localization_accuracy;
    vc2 += `<p><span class="tag t-info">定位准确率 ${d.accuracy!=null?Math.round(d.accuracy*100)+'%':'—'}</span> ${d.hits||0}/${d.denominator||0} 答案错误样本正确定位。</p>`;
  }
  if(v.false_positive_rate){
    const f=v.false_positive_rate;
    vc2 += `<p><span class="tag t-warn">误报率 ${f.fp_rate!=null?Math.round(f.fp_rate*100)+'%':'—'}</span> ${f.flagged_invalid||0} 个答案正确样本被判无效，其中真实过程问题 ${f.real_process_problems||0}、误报 ${f.false_positives||0}。</p>`;
    vc2 += `<div class="mut">${f.manual_review.map(m=>`${m.sample_id}: ${m.kind==='real'?'真实过程问题':'误报'}（gt=${m.gt_error_type||'无'} / eval=${m.eval_error_type||'无'}）`).join('；')}</div>`;
  }
  document.getElementById('verify_card').innerHTML = '<h2>评估器有效性（验证集）</h2>'+vc2;
})();

// ---------- 样本探查 ----------
let curSampleFilter = 'all';
const SAMPLE_KINDS = [['all','全部'],['correct','正确且成立'],['process_invalid','答案对过程错'],['wrong','答案错误']];
function renderSampleFilters(){
  document.getElementById('sample_filters').innerHTML = SAMPLE_KINDS.map(([k,name])=>
    `<div class="fbtn ${k===curSampleFilter?'active':''}" data-k="${k}">${name}</div>`).join('');
  document.querySelectorAll('#sample_filters .fbtn').forEach(b=>b.onclick=()=>{
    curSampleFilter=b.dataset.k; renderSampleFilters(); renderSampleList();
  });
}
function renderSampleList(){
  const list = D.sample_views.filter(s=>curSampleFilter==='all'||s.kind===curSampleFilter);
  document.getElementById('sample_list').innerHTML = list.map(s=>{
    const ev = s.rule;
    const flagged = ev && ev.process_valid===false;
    const fc = s.llm && s.llm.process_valid===false;
    return `<div class="item" data-id="${s.sample_id}">
      <div><div class="tt">${s.sample_id} · ${s.problem_id}</div>
      <div class="mt">${KIND_NAME[s.kind]} · ${s.problem_id}</div></div>
      <div>${flagged?'<span class="tag t-bad">rule 过程错</span>':''}${fc?'<span class="tag t-vio">llm 过程错</span>':''}
      <span class="tag ${KIND_CLASS[s.kind]}">${ET_NAME[ev&&ev.error_type||'none']||'过程成立'}</span></div>
    </div>`;
  }).join('') || '<div class="mut">无样本</div>';
  document.querySelectorAll('#sample_list .item').forEach(it=>it.onclick=()=>renderSampleDetail(it.dataset.id));
}
function stepBlock(title, body, ok, reason){
  const cls = ok?'ok':'bad';
  return `<div class="step ${cls}"><div class="h"><span>${title}</span><span class="tag ${ok?'t-good':'t-bad'}">${ok?'成立':'问题'}</span></div>
    <div class="b">${body?escapeHtml(body):'（无）'}</div>${reason?`<div class="mut">评估：${escapeHtml(reason)}</div>`:''}</div>`;
}
function evalCard(title, e, color){
  if(!e) return `<div class="card" style="border-left:4px solid #cbd5e1"><h2>${title}</h2><div class="mut">无评测结果</div></div>`;
  const fc = e.final_correct?'t-good':'t-bad';
  const pv = e.process_valid===false?'t-bad':'t-good';
  return `<div class="card" style="border-left:4px solid ${color}">
    <h2>${title}</h2>
    <p class="kv"><b>最终答案</b><span class="tag ${fc}">${e.final_correct?'通过':'错误'}</span> <span class="mut">${e.passed_cases}/${e.total_cases}</span></p>
    <p class="kv"><b>过程</b><span class="tag ${pv}">${e.process_valid===false?'不成立':'成立'}</span></p>
    <p class="kv"><b>错误步骤</b>${e.error_step?('step '+e.error_step):'—'}</p>
    <p class="kv"><b>错误类型</b><span class="tag t-warn">${ET_NAME[e.error_type]||'无'}</span></p>
    <p class="kv"><b>verdict</b><span class="mut">${e.verdict_summary||'—'}</span></p>
    ${e.stress_summary?`<p class="kv"><b>差分压力</b><span class="tag t-info">${e.stress_summary}</span> <span class="mut">参考解为 oracle</span></p>`:''}
    ${e.confidence!=null?`<p class="kv"><b>置信度</b>${e.confidence}</p>`:''}
    <p class="mut">${escapeHtml(e.note||'')}</p>
  </div>`;
}
function renderSampleDetail(id){
  const s = D.sample_views.find(x=>x.sample_id===id);
  if(!s) return;
  const steps = [
    ['思路/建模', s.steps['思路/建模'], !s.rule||true, ''],
    ['复杂度分析', s.steps['复杂度分析'], !s.rule||true, ''],
    ['边界与处理', s.steps['边界与处理'], !s.rule||true, ''],
    ['代码实现', s.steps['代码实现'], !s.rule||true, ''],
  ];
  // 用 rule 的 step_verdicts 着色
  const sv = (s.rule&&s.rule.step_verdicts)||[];
  const svMap = {}; sv.forEach(x=>svMap[x.step]=x);
  const STEP_ORDER = [1,2,3,4]; const STEP_NAME={1:'思路/建模',2:'复杂度分析',3:'边界与处理',4:'代码实现'};
  let stepHtml='';
  STEP_ORDER.forEach((st,i)=>{
    const v=svMap[st]; const ok = v? v.ok : true; const reason = v? v.reason:'';
    stepHtml += stepBlock(STEP_NAME[st], steps[i][1], ok, ok? '':reason);
  });
  const head = `<div class="card"><div style="display:flex;justify-content:space-between;align-items:center">
    <h2>${s.sample_id} · ${s.problem_id}</h2><span class="tag ${KIND_CLASS[s.kind]}">${KIND_NAME[s.kind]}</span></div>
    <div class="mut">${escapeHtml(s.comment)}</div>
    <div class="chiprow"><span class="pill">真值过程: ${s.gt.process_valid===false?'不成立':'成立'}</span>
      <span class="pill">真值类型: ${ET_NAME[s.gt.error_type]||'无'}</span>
      <span class="pill">真值步骤: ${s.gt.error_step||'—'}</span></div>
    <h3 style="font-size:14px;margin:12px 0 4px">步骤级判定（rule 后端）</h3>
    <div class="steps">${stepHtml}</div>
    <div class="cmp">${evalCard('Rule 后端', s.rule, '#2563eb')}${evalCard('LLM 后端', s.llm, '#7c3aed')}</div>
    <h3 style="font-size:14px;margin:14px 0 4px">原始解题过程</h3>
    <pre>${escapeHtml(s.steps['思路/建模']+'\n\n'+s.steps['复杂度分析']+'\n\n'+s.steps['边界与处理']+'\n\n## 代码\n'+s.steps['代码实现'])}</pre>
  </div>`;
  document.getElementById('sample_detail').innerHTML = head;
}
function escapeHtml(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

// ---------- 题集 ----------
let curBankDiff='all', curBankSrc='all', bankQuery='';
function renderBankFilters(){
  const diffs=['all',...new Set(D.problems.map(p=>p.difficulty))];
  const srcs=['all',...new Set(D.problems.map(p=>p.source.includes('洛谷')?'洛谷':(p.source.includes('LeetCode')?'LeetCode':'通用')))];
  document.getElementById('bank_filters').innerHTML =
    diffs.map(d=>`<div class="fbtn ${d===curBankDiff?'active':''}" data-d="${d}">${d==='all'?'全部难度':d}</div>`).join('')+
    srcs.map(s=>`<div class="fbtn ${s===curBankSrc?'active':''}" data-s="${s}">${s==='all'?'全部来源':s}</div>`).join('');
  document.querySelectorAll('#bank_filters .fbtn').forEach(b=>b.onclick=()=>{
    if(b.dataset.d){curBankDiff=b.dataset.d;} if(b.dataset.s){curBankSrc=b.dataset.s;}
    renderBankFilters(); renderBank();
  });
}
function renderBank(){
  const q=bankQuery.trim().toLowerCase();
  const list = D.problems.filter(p=>{
    const src = p.source.includes('洛谷')?'洛谷':(p.source.includes('LeetCode')?'LeetCode':'通用');
    if(curBankDiff!=='all'&&p.difficulty!==curBankDiff) return false;
    if(curBankSrc!=='all'&&src!==curBankSrc) return false;
    if(q && !(p.id.toLowerCase().includes(q)||p.title.toLowerCase().includes(q)||p.source.toLowerCase().includes(q)||(p.tags||[]).join(' ').toLowerCase().includes(q))) return false;
    return true;
  });
  document.getElementById('bank_list').innerHTML = list.map(p=>
    `<div class="item"><div><div class="tt">${p.id} · ${escapeHtml(p.title)}</div>
     <div class="mt">${p.domain} · ${p.source} · ${p.n_tests} 用例${p.n_stress?' · '+p.n_stress+' 压力':''}</div></div>
     <div><span class="tag ${p.difficulty==='easy'?'t-good':p.difficulty==='medium'?'t-warn':'t-bad'}">${p.difficulty}</span>
     <span class="chiprow">${(p.tags||[]).slice(0,4).map(t=>`<span class="pill">${escapeHtml(t)}</span>`).join('')}</span></div></div>`).join('')
     || '<div class="mut">无匹配题目</div>';
}
document.getElementById('bank_search').oninput = e=>{bankQuery=e.target.value; renderBank();};

// ---------- 分类体系 ----------
(function(){
  document.getElementById('tax_tree').innerHTML = D.taxonomy.map(t=>{
    const fine = t.fine.map(([k,name])=>`<tr><td><code>${k}</code></td><td>${escapeHtml(name)}</td></tr>`).join('');
    return `<div style="margin-bottom:12px"><h3 style="font-size:14px;margin:6px 0">${t.name} <span class="mut">（${t.coarse}）</span></h3>
      <table class="tbl"><tr><th>细类</th><th>说明</th></tr>${fine}</table></div>`;
  }).join('');
  document.getElementById('tax_verdict').innerHTML =
    `<table class="tbl"><tr><th>Verdict</th><th>含义</th></tr>`+
    Object.entries(D.verdict_types).map(([k,v])=>`<tr><td><span class="tag t-info">${k}</span></td><td>${escapeHtml(v)}</td></tr>`).join('')+`</table>`;
})();

// 初始化
renderSampleFilters(); renderSampleList(); renderBankFilters(); renderBank();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
