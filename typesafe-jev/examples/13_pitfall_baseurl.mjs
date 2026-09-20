// 13 踩坑实测：把 baseURL 写成 baseUrl（小写 rl）。
//
// JS SDK 的配置字段是 baseURL；写成 baseUrl 时该键不被识别、静默忽略，
// 客户端会落到默认的 https://api.typesafe.ai，请求打到真实服务而不是本地 stub。
// 这类错拼没有报错、没有警告，是最难发现的一类问题。
//
// 运行：node 13_pitfall_baseurl.mjs

const { TypeSafeClient, noul } = await import("@typesafe-ai/sdk");

const client = new TypeSafeClient({
  apiKey: "ts_invalid_key_for_demo",
  baseUrl: "http://127.0.0.1:8787", // 错：应为 baseURL
  retry: { maxRetries: 0 },
});

console.log("本意连接 : http://127.0.0.1:8787");
console.log("实际连接 :", client.baseURL);

try {
  await client.systemOne({ state: "hello", questions: { q: noul("Is this a test?") } });
} catch (error) {
  console.log("异常     :", error.constructor.name, String(error).slice(0, 120));
}
