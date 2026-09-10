/**
 * 看板自检：在 Node 中用最小 DOM 桩真实执行 dashboard.html 的渲染脚本。
 *
 * 为什么需要它：`node --check` 只能验证语法，无法发现运行时错误——例如汇总数据里
 * 缺了某个字段、某个 getElementById 指向了不存在的容器，页面会静默白屏，
 * 而这恰恰是「打开看板才发现」的典型事故。本脚本把渲染逻辑真正跑一遍，
 * 逐容器报告是否被填充，并在任何渲染函数抛错时以非零码退出（可用于 CI）。
 *
 * 用法：node tools/check_dashboard.js demo/dashboard.html
 */
const fs = require("fs");
const path = require("path");

const file = process.argv[2] || path.join(__dirname, "..", "demo", "dashboard.html");
const html = fs.readFileSync(file, "utf-8");

// ---- 取出内联数据与渲染脚本 ----
const dataMatch = html.match(
  /<script id="DATA" type="application\/json">([\s\S]*?)<\/script>/
);
if (!dataMatch) {
  console.error("✗ 未找到内联 DATA 块");
  process.exit(1);
}
const scripts = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)];
if (!scripts.length) {
  console.error("✗ 未找到渲染脚本");
  process.exit(1);
}

let DATA;
try {
  DATA = JSON.parse(dataMatch[1]);
} catch (e) {
  console.error("✗ 内联 JSON 无法解析：" + e.message);
  process.exit(1);
}

// ---- 最小 DOM 桩 ----
const written = new Map();
const missing = [];

function makeEl(id) {
  const el = {
    _id: id,
    _html: "",
    textContent: "",
    style: {},
    dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
  };
  Object.defineProperty(el, "innerHTML", {
    get: () => el._html,
    set: (v) => {
      el._html = String(v);
      written.set(id, el._html.length);
    },
  });
  return el;
}

const els = new Map();
const document = {
  getElementById(id) {
    if (!els.has(id)) {
      // 脚本只会访问模板里声明过的容器；访问未声明的 id 说明模板与脚本不一致
      if (!html.includes(`id="${id}"`)) missing.push(id);
      const el = makeEl(id);
      // 内联数据容器：真实浏览器中 textContent 即 JSON 文本
      if (id === "DATA") el.textContent = dataMatch[1];
      els.set(id, el);
    }
    return els.get(id);
  },
  querySelectorAll: () => [],
};

// ---- 执行渲染脚本 ----
let error = null;
try {
  const fn = new Function("document", "window", "console", scripts[scripts.length - 1][1]);
  fn(document, { addEventListener() {} }, console);
} catch (e) {
  error = e;
}

// ---- 报告 ----
const EXPECTED = [
  "kpis", "models", "diff", "domain", "etype", "estep", "verdict",
  "stepfunnel", "stepbars", "cross", "dlucky", "perf", "value", "rows",
];

console.log(`看板自检：${path.basename(file)}`);
console.log(`  数据：${DATA.items ? DATA.items.length : 0} 题 · 后端 ${DATA.backend || "?"}`);

let fail = 0;
for (const id of EXPECTED) {
  const n = written.get(id);
  if (n === undefined) {
    console.log(`  ✗ #${id} 未被渲染（脚本未写入该容器）`);
    fail++;
  } else if (n === 0) {
    console.log(`  ✗ #${id} 渲染为空`);
    fail++;
  } else {
    console.log(`  ✓ #${id} 已渲染（${n} 字符）`);
  }
}

if (missing.length) {
  console.log(`  ✗ 脚本访问了模板中不存在的容器：${[...new Set(missing)].join(", ")}`);
  fail++;
}

if (error) {
  console.log(`  ✗ 渲染脚本抛错：${error.message}`);
  console.log(error.stack.split("\n").slice(0, 4).join("\n"));
  fail++;
}

// 关键指标不得为空
const s = DATA.summary || {};
if (!s.total) {
  console.log("  ✗ 汇总数据缺失 total");
  fail++;
}

if (fail) {
  console.log(`\n结果：失败（${fail} 项）`);
  process.exit(1);
}
console.log("\n结果：全部容器渲染正常");
