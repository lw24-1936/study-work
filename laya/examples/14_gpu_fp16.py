"""14 - 4 GB 显存（GTX 1050）上把模型塞进 GPU：先 load，再 model.half()。

背景（本机实测）：
  - laya 构建模型用的是 encoder/config.json 里的 dtype（fp32），421M 参数在卡上占 1.63 GB；
    加载瞬间的临时副本把 reserved 顶到 1.74 GB，第一次前向之后 reserved 到 2.50 GB。
  - 4 GB 的卡装得下「一个」checkpoint，装不下 Router(preload=True) 的三个
    （实测三个全加载后 allocated 2.99 GB / reserved 4.16 GB，直接 OOM，
      laya 会打印 warning 并退回 CPU 跑）。
  - torch.set_default_dtype(torch.float16) 没用：transformers 是按 config 里的 dtype 建模型的，
     验证过设置之后参数 dtype 仍然是 torch.float32。

可行的做法：load 之后手动把模型转成 fp16（agent.model.half()）。
显存从 1.63 GB 降到 0.86 GB，峰值 1.74 GB，前向结果与 fp32 一致。

跑法：
    HF_ENDPOINT=https://hf-mirror.com /opt/ai-lab/laya/.venv/bin/python 14_gpu_fp16.py
    LAYA_DEVICE=cpu /opt/ai-lab/laya/.venv/bin/python 14_gpu_fp16.py    # 只做对照
"""
import os
import time

import torch

import laya

DEVICE = os.environ.get("LAYA_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
USE_HALF = os.environ.get("LAYA_HALF", "1") == "1"

state = {"body": "We were charged twice for March, please refund the duplicate charge."}
questions = {
    "department": {"type": "choice", "instructions": "Which department should handle this?",
                   "criteria": {"billing": "invoices, payments, refunds",
                                "technical": "bugs, outages", "other": "everything else"}},
    "urgency": {"type": "score", "instructions": "How urgent is this?",
                "criteria": ["not urgent", "soon", "critical deadline"]},
    "churn_risk": {"type": "noul", "instructions": "Does the user threaten to cancel?"},
}


def gb(x):
    return "%.2f GB" % (x / 1e9)


def mem(tag):
    if torch.cuda.is_available():
        print("  [%s] allocated=%s reserved=%s"
              % (tag, gb(torch.cuda.memory_allocated()), gb(torch.cuda.memory_reserved())))


t0 = time.time()
agent = laya.load("convaiinnovations/laya", device=DEVICE)
print("load 完成：device=%s  laya 的 autocast dtype=%s  耗时 %.1f s"
      % (agent.device, agent.dtype, time.time() - t0))
print("参数实际 dtype：", next(agent.model.parameters()).dtype)
mem("load 之后")

if agent.device.type == "cuda" and USE_HALF:
    agent.model.half()
    print("已执行 agent.model.half()，参数 dtype：",
          next(agent.model.parameters()).dtype)
    mem("half() 之后")

agent.predict(state, questions)                       # 预热（第一次前向有一次性开销）
mem("第一次前向之后")

times = []
for _ in range(10):
    t0 = time.time()
    res = agent.predict(state, questions)
    times.append((time.time() - t0) * 1000)
times.sort()
print("三次问题一次前向：p50=%.0f ms  min=%.0f ms" % (times[len(times) // 2], times[0]))
print("答案：department=%s  urgency=%.3f  churn_risk=%.3f"
      % (res["answers"]["department"]["choice"], res["answers"]["urgency"]["score"],
         res["answers"]["churn_risk"]["noul"]))
if agent.device.type == "cuda":
    print("峰值显存：", gb(torch.cuda.max_memory_allocated()))
