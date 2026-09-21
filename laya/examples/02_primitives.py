"""02 - 三种决策原语：一次 forward 同时问 choice / score / noul。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 02_primitives.py          # 自动选设备
    LAYA_DEVICE=cpu /opt/ai-lab/laya/.venv/bin/python 02_primitives.py
第一次运行会下载 843 MB 的英文 checkpoint（缓存到 ~/.cache/huggingface）。
"""
import json
import os
import time

import laya

DEVICE = os.environ.get("LAYA_DEVICE") or None

state = {
    "from": "user@acme.com",
    "subject": "Duplicate charge on invoice #4411",
    "body": ("Hi, we were billed twice for March. Our finance team needs this "
             "corrected before month end or we will have to cancel our plan."),
}
questions = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this request?",
        "criteria": {
            "billing": "invoices, payments, refunds",
            "technical": "bugs, outages, system errors",
            "sales": "pricing, new contracts",
            "other": "everything else",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical deadline or blocking issue"],
    },
    "churn_risk": {
        "type": "noul",
        "instructions": "Does the user threaten to cancel or leave?",
    },
    "refund_requested": {
        "type": "noul",
        "instructions": "Does the user explicitly request a refund?",
    },
}

t0 = time.time()
agent = laya.load("convaiinnovations/laya", device=DEVICE)
print("加载完成，device=%s，耗时 %.1f s" % (agent.device, time.time() - t0))
print("模型配置 rl_agent_config.json:", json.dumps(
    {k: v for k, v in agent.cfg.items() if k != "act_costs"}, ensure_ascii=False))
print()

t0 = time.time()
result = agent.predict(state, questions)
dt = (time.time() - t0) * 1000
print("一次 forward 同时回答 4 个问题，用时 %.1f ms，输入 %d tokens"
      % (dt, result["usage"]["input_tokens"]))
print()

answers = result["answers"]
print("department.choice        =", answers["department"]["choice"])
print("department.probabilities =", answers["department"]["probabilities"])
print("department.confidence    =", answers["department"]["confidence"])
print("urgency.score            =", answers["urgency"]["score"], "/ 2.0")
print("urgency.probabilities    =", answers["urgency"]["probabilities"])
print("churn_risk.noul          =", answers["churn_risk"]["noul"])
print("refund_requested.noul    =", answers["refund_requested"]["noul"])
print()
print("完整返回值：")
print(json.dumps(result, ensure_ascii=False, indent=2))
