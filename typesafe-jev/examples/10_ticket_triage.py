#!/usr/bin/env python3
"""10 应用场景实战：客服工单一次调用完成路由 + 升级判断 + 紧急度打分。

要点：
  1. 一次请求问全部问题，questions 并行评估，加问题几乎不增加延迟；
  2. 概率是给代码用的数据，阈值是业务决策，全部集中到一处；
  3. 高置信度自动执行，中置信度走人工复核，低置信度转人工。

运行：
    /opt/ai-lab/jev/.venv/bin/python stub_server.py 8787 &
    /opt/ai-lab/jev/.venv/bin/python 10_ticket_triage.py
"""

import os
from dataclasses import dataclass

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

os.environ.setdefault("TYPESAFE_API_KEY", "ts_stub_key")
os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8787")

# ---------------------------------------------------------------------------
# 问题与阈值集中定义，方便人工 review（TypeSafe 官方也建议这么做）
# ---------------------------------------------------------------------------
DEPARTMENT = Choice(
    instructions="Which team should handle this ticket?",
    criteria={
        "returns": "Exchanges, wrong or damaged items",
        "shipping": "Delivery status, delays, lost packages",
        "billing": "Charges, invoices, payment problems",
        "technical": "Product bugs and integration failures",
    },
)

REFUND_REQUESTED = Noul(
    instructions="Does the customer ask for money back?",
    criteria={"true": "Explicit request for a refund", "false": "No refund request"},
)

IS_ESCALATION = Noul(instructions="Does this message require a human to take over right now?")

FRUSTRATION = Score(
    instructions="How frustrated is the customer?",
    criteria=[
        "Neutral or matter-of-fact",
        "Annoyed but polite",
        "Clearly angry or threatening to churn",
    ],
)

SEVERITY = Score(
    instructions="How severe is the reported issue?",
    criteria=[
        "Cosmetic; no impact to functionality",
        "Broken or degraded feature, but workaround exists",
        "Blocking issue; no workaround exists",
    ],
)

TRIAGE_QUESTIONS = {
    "department": DEPARTMENT,
    "refund_requested": REFUND_REQUESTED,
    "is_escalation": IS_ESCALATION,
    "frustration": FRUSTRATION,
    "severity": SEVERITY,
}

LOW_CONFIDENCE_FLOOR = 0.5


@dataclass
class Triage:
    ticket_id: str
    department: str
    department_confidence: float
    refund_requested: float
    is_escalation: float
    priority: float
    route: str


def normalize(answer, question: Score) -> float:
    """把 0..N 的分值归一化到 0..1，便于加权。"""
    top_level = len(question.criteria) - 1
    return answer.score / top_level if top_level else 0.0


def triage(client: TypeSafeClient, ticket_id: str, ticket: dict) -> Triage:
    response = client.system_one(state=ticket, questions=TRIAGE_QUESTIONS)
    answers = response.answers

    department = answers["department"]
    severity = normalize(answers["severity"], SEVERITY)
    frustration = normalize(answers["frustration"], FRUSTRATION)

    # 复合打分：权重写在代码里，可读、可改、可单测
    priority = round(0.6 * severity + 0.3 * frustration + 0.1 * answers["is_escalation"].noul, 4)

    if department.confidence < LOW_CONFIDENCE_FLOOR:
        route = "human_review"
    elif answers["is_escalation"].noul > 0.8 or priority > 0.8:
        route = "escalate_oncall"
    elif answers["refund_requested"].noul > 0.8 and department.choice == "billing":
        route = "auto_refund_workflow"
    else:
        route = "auto_route"

    return Triage(
        ticket_id=ticket_id,
        department=department.choice,
        department_confidence=department.confidence,
        refund_requested=answers["refund_requested"].noul,
        is_escalation=answers["is_escalation"].noul,
        priority=priority,
        route=route,
    )


TICKETS = {
    "T-1001": {
        "message": "My running shoes arrived in the wrong size. Can I swap them for a size 10?",
        "order_total": 129.0,
    },
    "T-1002": {
        "message": "I was charged twice for the same order, please refund one of them.",
        "order_total": 258.0,
    },
    "T-1003": {
        "message": "The tracking number you sent does not work and nobody answers my emails. Where is my package?",
        "order_total": 89.0,
    },
}


def main() -> None:
    with TypeSafeClient(timeout=10.0) as client:
        for ticket_id, ticket in TICKETS.items():
            result = triage(client, ticket_id, ticket)
            print("%s  部门=%-9s conf=%.4f  退款=%.2f  升级=%.2f  优先级=%.3f  -> %s"
                  % (result.ticket_id, result.department, result.department_confidence,
                     result.refund_requested, result.is_escalation, result.priority, result.route))
    print()
    print("一次请求问完 5 个问题；问题之间互相独立、并行评估，加问题几乎不增加延迟。")


if __name__ == "__main__":
    main()
