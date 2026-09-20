#!/usr/bin/env python3
"""03 异步客户端：高并发场景下批量评估多条 state。

AsyncTypeSafeClient 复用同一条 HTTP 连接池，asyncio.gather 并发发出多条请求，
适合离线批量打标（几十万条语料）这类吞吐优先的场景。

运行：
    /opt/ai-lab/jev/.venv/bin/python stub_server.py 8787 &
    /opt/ai-lab/jev/.venv/bin/python 03_async_client.py
"""

import asyncio
import os
import time

from typesafe_sdk import AsyncTypeSafeClient, Choice, RetryPolicy

os.environ.setdefault("TYPESAFE_API_KEY", "ts_stub_key")
os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8787")

TICKETS = [
    "My running shoes arrived in the wrong size. Can I swap them for a size 10?",
    "I was charged twice for the same order, please refund one of them.",
    "The tracking number you sent does not work, where is my package?",
]


async def classify(client: AsyncTypeSafeClient, ticket: str) -> tuple[str, str, float]:
    response = await client.system_one(
        state=ticket,
        questions={
            "department": Choice(
                instructions="Which team should handle this?",
                criteria={
                    "returns": "Exchanges, wrong or damaged items",
                    "shipping": "Delivery status, delays, lost packages",
                    "billing": "Charges, invoices, payment problems",
                },
            )
        },
    )
    answer = response.choices["department"]
    return ticket[:32], answer.choice, answer.confidence


async def main() -> None:
    started = time.perf_counter()
    async with AsyncTypeSafeClient(retry=RetryPolicy(max_retries=1)) as client:
        results = await asyncio.gather(*[classify(client, ticket) for ticket in TICKETS])
    elapsed = (time.perf_counter() - started) * 1000
    for text, choice, confidence in results:
        print("%-34s -> %-9s confidence=%.4f" % (text, choice, confidence))
    print()
    print("%d 条语料并发完成，总耗时 %.0f ms" % (len(results), elapsed))


asyncio.run(main())
