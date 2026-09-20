#!/usr/bin/env python3
"""07 置信度路由：answer 决定「做什么」，confidence 决定「能不能自己做」。

stub 约定：state 里出现 AMBIGUOUS 时返回接近均摊的分布，confidence 会明显下降。

运行：
    /opt/ai-lab/jev/.venv/bin/python stub_server.py 8787 &
    /opt/ai-lab/jev/.venv/bin/python 07_confidence_routing.py
"""

import os

from typesafe_sdk import Choice, TypeSafeClient

os.environ.setdefault("TYPESAFE_API_KEY", "ts_stub_key")
os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8787")

# 阈值集中在一处，方便业务方 review
CONFIDENCE_FLOOR = 0.5
AUTO_EXECUTE_THRESHOLD = {"check_balance": 0.5, "approve_transfer": 0.9, "support": 0.6}

ACTIONS = Choice(
    instructions="What is the user trying to do?",
    criteria={
        "check_balance": "View account balance",
        "approve_transfer": "Approve the pending withdrawal request",
        "support": "Get help with an issue",
    },
)

MESSAGES = [
    "Show me my balance please.",
    "AMBIGUOUS something about my account and maybe a transfer and support",
]


def route(client: TypeSafeClient, message: str) -> None:
    response = client.system_one(state=message, questions={"action": ACTIONS})
    answer = response.choices["action"]
    print("输入        :", message)
    print("  choice      =", answer.choice)
    print("  confidence  =", answer.confidence)
    print("  probabilities =", answer.probabilities)

    if answer.confidence < CONFIDENCE_FLOOR:
        print("  -> 路由：转人工（模型自己说不确定）")
    elif answer.confidence >= AUTO_EXECUTE_THRESHOLD.get(answer.choice, 0.9):
        print("  -> 路由：自动执行 %s()" % answer.choice)
    else:
        print("  -> 路由：先向用户确认再执行 %s" % answer.choice)
    print()


with TypeSafeClient() as client:
    for message in MESSAGES:
        route(client, message)
