// 14 踩坑实测：JS SDK 的 timeout 单位是毫秒，Python 是秒。
//
// 从 Python 示例照抄 timeout: 10 到 JS 里，等于「10 毫秒超时」，
// 请求几乎必然超时；而 Python 里 timeout=10 是 10 秒，属于合理值。
//
// 运行：node 14_pitfall_timeout.mjs

const { TypeSafeClient, noul } = await import("@typesafe-ai/sdk");

const client = new TypeSafeClient({
  apiKey: "ts_invalid_key_for_demo",
  timeout: 10, // 单位是毫秒，等价于 0.01 秒
  retry: { maxRetries: 0 },
});

console.log("客户端 timeout(毫秒) =", client.timeout);

try {
  await client.systemOne({ state: "hello", questions: { q: noul("Is this a test?") } });
} catch (error) {
  console.log("异常:", error.constructor.name, "->", String(error).slice(0, 140));
}
