"""04 - 内置工作流预设：triage_questions 直接拿来用。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 04_presets_triage.py
"""
import json
import os

import laya
from laya import Router, triage_questions

DEVICE = os.environ.get("LAYA_DEVICE") or None

print("=== 预设问题的结构（triage_questions） ===")
preset = triage_questions()
for qid, qdef in preset.items():
    crit = qdef.get("criteria")
    if isinstance(crit, dict):
        crit_desc = "choice，选项 " + " / ".join(crit)
    elif isinstance(crit, list):
        crit_desc = "score，%d 级" % len(crit)
    else:
        crit_desc = "noul（是/否）"
    print("  %-17s %-8s %s" % (qid, qdef["type"], crit_desc))
print()

tickets = [
    "I have been charged twice this month and nobody is answering my emails. "
    "If this is not fixed by Friday I am switching to your competitor.",
    "How do I add another seat to our team plan?",
    "Your API returns 502 on the /v2/export endpoint since the last release.",
]

router = Router(device=DEVICE)
# 注意：Router(preload=["english"]) 会让 __init__ 里的 `if preload:` 为真并调用
# self.preload()（不传 names），结果是三个 checkpoint 全部加载——4 GB 显存的卡会直接 OOM。
# 只加载指定 checkpoint 要用两步写法：
router.preload(["english"])
for i, ticket in enumerate(tickets, 1):
    res = router.predict({"message": ticket}, triage_questions())
    a = res["answers"]
    print("--- 工单 %d ---" % i)
    print("  文本        :", ticket[:72] + ("..." if len(ticket) > 72 else ""))
    print("  intent      :", a["intent"]["choice"], a["intent"]["probabilities"],
          "confidence", a["intent"]["confidence"])
    print("  is_urgent   :", a["is_urgent"]["noul"], "(confidence %.4f)" % a["is_urgent"]["confidence"])
    print("  frustration :", a["frustration"]["score"], "/ 3.0", a["frustration"]["probabilities"])
    print("  refund?     :", a["refund_requested"]["noul"])
    print("  churn_risk  :", a["churn_risk"]["noul"])
    print()

print("=== 按预设结论做分支（confidence 门控） ===")
ticket = tickets[0]
a = router.predict({"message": ticket}, triage_questions())["answers"]
intent = a["intent"]["choice"]
conf = a["intent"]["confidence"]
churn = a["churn_risk"]["noul"]
if conf >= 0.85 and churn < 0.5:
    action = "自动路由到 %s 队列" % intent
else:
    action = "转人工（intent confidence=%.2f, churn=%.2f）" % (conf, churn)
print("  判定结果：", action)
print()
print("  完整 answers：")
print(json.dumps(a, ensure_ascii=False, indent=2))
