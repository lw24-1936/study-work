#!/usr/bin/env python3
"""06 类型化响应：用 response_model 把答案提升成静态字段，写业务代码时不用再取字典。

运行：
    /opt/ai-lab/jev/.venv/bin/python stub_server.py 8787 &
    /opt/ai-lab/jev/.venv/bin/python 06_typed_response.py
"""

import os

from pydantic import BaseModel

from typesafe_sdk import ChoiceAnswer, NoulAnswer, ScoreAnswer, SystemOneResponse, TypeSafeClient
from typesafe_sdk import Choice, Noul, Score

os.environ.setdefault("TYPESAFE_API_KEY", "ts_stub_key")
os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8787")


class TicketResponse(SystemOneResponse):
    """继承 SystemOneResponse，把关注的问题提升为顶层字段。"""

    is_urgent: NoulAnswer
    department: ChoiceAnswer
    severity: ScoreAnswer


class Answers(BaseModel):
    department: ChoiceAnswer


class PlainResponse(BaseModel):
    """完全不继承 SDK 响应类型，只声明自己要用到的部分。"""

    answers: Answers


TICKET = "The export button crashes the settings page in Safari. It works in Chrome, but a few of our customers only use Safari."

questions = {
    "is_urgent": Noul(instructions="Does this convey urgency?"),
    "department": Choice(
        instructions="Which team should handle this?",
        criteria={"frontend": "UI rendering issues", "integrations": "Third-party connection issues"},
    ),
    "severity": Score(
        instructions="How severe is the reported issue?",
        criteria=["Cosmetic", "Degraded but workaround exists", "Blocking"],
    ),
}

with TypeSafeClient() as client:
    typed = client.system_one(TICKET, questions, response_model=TicketResponse)
    print("类型化响应：", type(typed).__name__)
    print("  typed.department.choice       =", typed.department.choice)
    print("  typed.department.confidence   =", typed.department.confidence)
    print("  typed.severity.score          =", typed.severity.score)
    print("  typed.severity.legend         =", typed.severity.legend)
    print("  typed.request_id              =", typed.request_id)
    assert typed.department == typed.choices["department"]
    print("  断言通过：typed.department 与 typed.choices['department'] 是同一个答案")
    print()

    plain = client.system_one(TICKET, questions, response_model=PlainResponse)
    print("自定义响应模型：", type(plain).__name__)
    print("  plain.answers.department.choice =", plain.answers.department.choice)
