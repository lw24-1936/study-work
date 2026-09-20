#!/usr/bin/env python3
"""02 同步客户端：一次请求问完 Noul / Choice / Score 三种原语。

打的是本地 stub（默认 http://127.0.0.1:8787），不消耗真实额度。
把 TYPESAFE_BASE_URL 换成 https://api.typesafe.ai 并配置真实 TYPESAFE_API_KEY，
同一段代码就是生产用法。

运行：
    /opt/ai-lab/jev/.venv/bin/python stub_server.py 8787 &
    /opt/ai-lab/jev/.venv/bin/python 02_sync_three_primitives.py
"""

import os

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

os.environ.setdefault("TYPESAFE_API_KEY", "ts_stub_key")
os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8787")

TICKET = {
    "message": "Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP.",
    "plan": "growth",
}

with TypeSafeClient(timeout=5.0) as client:
    response = client.system_one(
        state=TICKET,
        questions={
            "is_urgent": Noul(
                instructions="Does `message` convey urgency?",
                criteria={"true": "Explicitly time-sensitive, such as an ASAP request", "false": "No urgency expressed"},
            ),
            "department": Choice(
                instructions="Which team should handle this?",
                criteria={
                    "billing": "Charges, invoices, payment problems",
                    "integrations": "Third-party integrations that fail to connect",
                    "account": "Login, permissions, account settings",
                },
            ),
            "severity": Score(
                instructions="How severe is the reported issue?",
                criteria=[
                    "Cosmetic; no impact to functionality",
                    "Broken or degraded feature, but workaround exists",
                    "Blocking issue; no workaround exists",
                ],
            ),
        },
    )

print("model        :", response.model)
print("usage        :", response.usage)
print("request_id   :", response.request_id)
print()
print("按类型分组读取：")
print("  nouls    :", response.nouls)
print("  choices  :", response.choices)
print("  scores   :", response.scores)
print()
print("按问题名逐一读取：")
print("  is_urgent.noul          =", response.answers["is_urgent"].noul)
print("  department.choice       =", response.answers["department"].choice)
print("  department.confidence   =", response.answers["department"].confidence)
print("  department.probabilities=", response.answers["department"].probabilities)
print("  severity.score          =", response.answers["severity"].score)
print("  severity.legend         =", response.answers["severity"].legend)
print()
print("原始 JSON 响应体：")
print(response.raw_http_response.text)

# 代码里做决策：概率属于「数据」，阈值属于「业务」
if response.nouls["is_urgent"].noul > 0.8 and response.choices["department"].choice == "integrations":
    print()
    print("决策：升级到 integrations 值班工程师")
