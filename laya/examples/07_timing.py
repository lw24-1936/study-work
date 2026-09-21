"""07 - 延迟与吞吐实测：单问题 / 批量问题 / CPU 与 GPU 对比。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    LAYA_DEVICE=cpu /opt/ai-lab/laya/.venv/bin/python 07_timing.py
    LAYA_DEVICE=cuda /opt/ai-lab/laya/.venv/bin/python 07_timing.py
"""
import os
import time

import torch

import laya

DEVICE = os.environ.get("LAYA_DEVICE") or None
MODEL = os.environ.get("LAYA_MODEL", "convaiinnovations/laya")
SUBFOLDER = os.environ.get("LAYA_SUBFOLDER") or None      # 例如 multilingual

state = {"body": "We were billed twice for March and need the duplicate charge refunded today."}


def make_questions(n):
    """生成 n 个问题，全部塞进同一次 forward。"""
    qs = {}
    for i in range(n):
        qs["department_%d" % i] = {
            "type": "choice",
            "instructions": "Which department should handle this request?",
            "criteria": {"billing": "invoices, payments, refunds",
                         "technical": "bugs, outages, system errors",
                         "other": "everything else"},
        }
    return qs


t0 = time.time()
agent = laya.load(MODEL, subfolder=SUBFOLDER, device=DEVICE)
print("模型：%s%s" % (MODEL, "/" + SUBFOLDER if SUBFOLDER else ""))
print("device=%s  dtype=%s  加载耗时 %.1f s"
      % (agent.device, agent.dtype, time.time() - t0))
print("cfg：max_len=%s head_max_len=%s" % (agent.cfg.get("max_len"), agent.cfg.get("head_max_len")))
print()

# 预热：第一次调用包含内核编译/内存分配，不计入统计
agent.predict(state, make_questions(1))

print("=== 同一次 forward 里塞 n 个问题 ===")
print("%-6s %-12s %-14s %s" % ("问题数", "总耗时", "每问题耗时", "输入 tokens"))
for n in (1, 5, 10, 50):
    qs = make_questions(n)
    t0 = time.time()
    res = agent.predict(state, qs)
    dt = time.time() - t0
    print("%-6d %-12s %-14s %d"
          % (n, "%.0f ms" % (dt * 1000), "%.1f ms" % (dt * 1000 / n), res["usage"]["input_tokens"]))

print()
print("=== 一次 forward 里塞 100 个不同问题 ===")
qs = make_questions(100)
t0 = time.time()
res = agent.predict(state, qs)
dt = time.time() - t0
print("100 个问题：%.0f ms，即 %.1f ms/问题，%d tokens"
      % (dt * 1000, dt * 1000 / 100, res["usage"]["input_tokens"]))
print("返回的答案个数：", len(res["answers"]))

print()
print("=== 同一批问题重复 20 次（看稳态延迟） ===")
qs = make_questions(4)
times = []
for _ in range(20):
    t0 = time.time()
    agent.predict(state, qs)
    times.append((time.time() - t0) * 1000)
times.sort()
print("min=%.0f ms  p50=%.0f ms  mean=%.0f ms  max=%.0f ms"
      % (times[0], times[len(times) // 2], sum(times) / len(times), times[-1]))

if agent.device.type == "cuda":
    print()
    print("GPU 显存占用：%.2f GB（torch.cuda.max_memory_allocated）"
          % (torch.cuda.max_memory_allocated() / 1e9))
