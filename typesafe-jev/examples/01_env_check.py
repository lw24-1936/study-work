#!/usr/bin/env python3
"""01 环境自检：确认 SDK 版本、默认配置与答案对象的字段。

运行：
    /opt/ai-lab/jev/.venv/bin/python 01_env_check.py
"""

import typesafe_sdk
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient, constants

print("typesafe-sdk 版本 :", typesafe_sdk.__version__)
print("默认 base_url     :", constants.DEFAULT_BASE_URL)
print("默认模型          :", constants.DEFAULT_MODEL)
print("默认超时          :", constants.DEFAULT_TIMEOUT, "秒")
print()
print("客户端读取的环境变量：")
print("  API Key      ->", constants.API_KEY_ENV)
print("  base_url     ->", constants.BASE_URL_ENV)
print("  默认模型     ->", constants.DEFAULT_MODEL_ENV)
print("  日志级别     ->", constants.LOG_LEVEL_ENV)
print()

# 三个原语对象的序列化结果，就是发给 API 的 questions 字段
questions = {
    "is_urgent": Noul(instructions="Does this convey urgency?", criteria={"true": "Explicitly time-sensitive", "false": "No urgency expressed"}),
    "department": Choice(instructions="Which team should handle this?", criteria={"billing": "Payment issues", "technical": "Bugs and integrations"}),
    "severity": Score(instructions="How severe is the reported issue?", criteria=["Cosmetic", "Degraded but workaround exists", "Blocking"]),
}
for name, question in questions.items():
    print("%-12s -> %s" % (name, question.model_dump_json()))

# 构造函数会立刻校验 API Key：没设置环境变量时抛 TypeSafeError
try:
    TypeSafeClient(api_key="   ")
except Exception as exc:
    print()
    print("未提供 API Key 时：", type(exc).__name__, "-", exc)
