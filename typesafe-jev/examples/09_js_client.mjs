// 09 JavaScript/TypeScript SDK：一次请求问三种原语，答案类型由问题推导。
//
// 运行（Node.js >= 20）：
//     node 09_js_client.mjs                     // 打本地 stub
//     TYPESAFE_BASE_URL=https://api.typesafe.ai TYPESAFE_API_KEY=<key> node 09_js_client.mjs
//
// 依赖：npm install -g @typesafe-ai/sdk （本机已全局安装 0.6.0）

process.env.TYPESAFE_BASE_URL ??= "http://127.0.0.1:8787";
process.env.TYPESAFE_API_KEY ??= "ts_stub_key";

const { TypeSafeClient, choice, noul, score } = await import("@typesafe-ai/sdk");

const client = new TypeSafeClient();

const response = await client.systemOne({
  state: {
    message:
      "Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP.",
    plan: "growth",
  },
  questions: {
    is_urgent: noul("Does `message` convey urgency?", {
      true: "Explicitly time-sensitive",
      false: "No urgency expressed",
    }),
    department: choice("Which team should handle this?", {
      billing: "Charges, invoices, payment problems",
      integrations: "Third-party integrations that fail to connect",
      account: "Login, permissions, account settings",
    }),
    severity: score("How severe is the reported issue?", [
      "Cosmetic; no impact to functionality",
      "Broken or degraded feature, but workaround exists",
      "Blocking issue; no workaround exists",
    ]),
  },
});

console.log("model       :", response.model);
console.log("usage       :", response.usage);
console.log("is_urgent   :", response.answers.is_urgent.noul);
console.log("department  :", response.answers.department.choice, "confidence=", response.answers.department.confidence);
console.log("severity    :", response.answers.severity.score, "legend=", response.answers.severity.legend);
console.log("完整响应    :", JSON.stringify(response, null, 2));

// 列出账号可用模型（alias 会随版本推进而变，线上建议记录实际命中的版本号）
const models = await client.models.list();
console.log("可用模型    :", models.map((m) => `${m.name} (${m.release_date})`).join(", "));

// 错误处理：SDK 用 throw 抛出类型化异常
try {
  const bad = new TypeSafeClient({ apiKey: "ts_invalid_key_for_demo", baseURL: "https://api.typesafe.ai", retry: { maxRetries: 0 } });
  await bad.systemOne({ state: "hello", questions: { q: noul("Is this a test?") } });
} catch (error) {
  console.log("异常类型    :", error.constructor.name);
  console.log("异常内容    :", String(error).slice(0, 200));
}
