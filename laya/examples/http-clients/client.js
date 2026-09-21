// 外部调用客户端（Node 18+ 的内置 fetch，不需要 npm install 任何东西）
//
// 跑法：
//     export LAYA_API_KEY=...
//     node client.js http://192.168.1.167:8077 "请把 3 月的账单退款"
//
// 本机实测：node v22 直接可用。

const [, , baseUrl, text, model] = process.argv;
if (!baseUrl || !text) {
  console.error('用法: node client.js <baseUrl> <text> [model]');
  console.error('      node client.js http://192.168.1.167:8077 "请把 3 月的账单退款"');
  process.exit(1);
}

const payload = { state: { message: text } };
if (model) payload.model = model;

const t0 = Date.now();
const resp = await fetch(baseUrl.replace(/\/+$/, '') + '/decide', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    ...(process.env.LAYA_API_KEY ? { 'X-API-Key': process.env.LAYA_API_KEY } : {}),
  },
  body: JSON.stringify(payload),
  signal: AbortSignal.timeout(60000),
});

const raw = await resp.text();
if (!resp.ok) {
  // 401 = key 错；422 = 请求体不合 schema；503 = 服务端还没 preload 完
  console.error(`HTTP ${resp.status}: ${raw.slice(0, 300)}`);
  process.exit(1);
}

const res = JSON.parse(raw);
const a = res.answers;
console.log(`路由模型   : ${res.routing.model}（${res.routing.reason}）`);
console.log(`部门       : ${a.department.choice}（置信度 ${a.department.confidence.toFixed(4)}）`);
console.log(`紧急度     : ${a.urgency.score.toFixed(2)}`);
console.log(`流失风险   : ${a.churn_risk.noul}（置信度 ${a.churn_risk.confidence.toFixed(4)}）`);
console.log(`服务端耗时 : ${res.latency_ms} ms ｜ 客户端总耗时 ${Date.now() - t0} ms（含网络往返）`);
