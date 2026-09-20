#!/usr/bin/env python3
"""05 重试策略：stub 前两次返回 503，SDK 自动退避重试并最终成功。

启动带抖动的 stub：
    STUB_FLAKY=1 /opt/ai-lab/jev/.venv/bin/python stub_server.py 8788 &
    /opt/ai-lab/jev/.venv/bin/python 05_retry.py
"""

import logging
import os
import time

from typesafe_sdk import Noul, RetryPolicy, TypeSafeClient

os.environ["TYPESAFE_API_KEY"] = "ts_stub_key"
os.environ["TYPESAFE_BASE_URL"] = "http://127.0.0.1:8788"
os.environ["TYPESAFE_LOG_LEVEL"] = "warning"
logging.basicConfig(level=logging.WARNING, format="[sdk] %(levelname)s %(message)s")

policy = RetryPolicy(
    max_retries=4,
    backoff_initial=0.2,
    backoff_max=1.0,
    backoff_jitter=0.0,
    http_statuses={429, 500, 502, 503, 504},
    respect_retry_after=True,
    timeout=10.0,
)
print("重试策略：", policy)

started = time.perf_counter()
with TypeSafeClient(retry=policy) as client:
    response = client.system_one(
        state="I was charged twice. Please help.",
        questions={"billing": Noul(instructions="Is this about billing?")},
    )
elapsed = time.perf_counter() - started

print()
print("最终成功：billing.noul =", response.answers["billing"].noul)
print("客户端耗时 %.2f 秒（含 2 次 503 重试与退避等待）" % elapsed)
print()
print("RetryPolicy 默认值：")
default = RetryPolicy()
for field in ("max_retries", "backoff_initial", "backoff_max", "backoff_jitter", "http_statuses", "respect_retry_after", "api_connection_error", "api_timeout_error", "timeout"):
    print("  %-20s = %s" % (field, getattr(default, field)))
