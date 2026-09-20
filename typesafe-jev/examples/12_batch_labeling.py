#!/usr/bin/env python3
"""12 应用场景实战三：离线批量打标（并发闸门 + 重试 + 可续跑落盘）。

要点：
  1. 一个 AsyncTypeSafeClient 复用连接池，Semaphore 控制并发（不要裸 gather 打满限额）
  2. 每条结果带上 request_id 与命中的模型版本，便于回溯
  3. 结果按 JSONL 追加写盘，进程被中断后跳过已完成的行，可续跑

运行：
    /opt/ai-lab/jev/.venv/bin/python stub_server.py 8787 &
    /opt/ai-lab/jev/.venv/bin/python 12_batch_labeling.py
"""

import asyncio
import json
import os
import time

from typesafe_sdk import AsyncTypeSafeClient, Choice, RetryPolicy

os.environ.setdefault("TYPESAFE_API_KEY", "ts_stub_key")
os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8787")

OUT_PATH = os.environ.get("JEV_OUT_PATH", "/tmp/jev_labels.jsonl")
CONCURRENCY = 4

REVIEW_TOPIC = Choice(
    instructions="What is this review about?",
    criteria={
        "shipping": "Delivery speed, packaging, courier",
        "quality": "Product materials, workmanship, durability",
        "size": "Fits larger or smaller than expected",
        "service": "Support, returns, refunds",
        "other": "Anything not covered above",
    },
)

REVIEWS = {
    "r-001": "The shoes arrived two weeks late and the box was crushed.",
    "r-002": "I usually wear a 42 and these fit more like a 43.",
    "r-003": "Ordered on Monday, delivered on Tuesday. Impressive.",
    "r-004": "The sole started peeling off after three walks.",
    "r-005": "Support answered within an hour and sent a replacement.",
    "r-006": "AMBIGUOUS not sure how I feel about this purchase",
    "r-007": "The colour is exactly as shown on the website.",
    "r-008": "Returned them because I found a cheaper option elsewhere.",
}


def load_done(path: str) -> set[str]:
    """读取已完成的 id，用于断点续跑。"""
    if not os.path.exists(path):
        return set()
    done = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["id"])
            except (ValueError, KeyError):
                continue
    return done


async def label_one(client: AsyncTypeSafeClient, semaphore: asyncio.Semaphore, item_id: str, text: str) -> dict:
    async with semaphore:
        response = await client.system_one(state={"review": text}, questions={"topic": REVIEW_TOPIC})
    answer = response.choices["topic"]
    return {
        "id": item_id,
        "text": text,
        "topic": answer.choice,
        "confidence": answer.confidence,
        "probabilities": answer.probabilities,
        "model": response.model,
        "request_id": response.request_id,
        "usage": response.usage.model_dump(),
    }


async def main() -> None:
    done = load_done(OUT_PATH)
    pending = {key: value for key, value in REVIEWS.items() if key not in done}
    print("已完成 %d 条，本轮待处理 %d 条，并发上限 %d" % (len(done), len(pending), CONCURRENCY))
    if not pending:
        print("没有待处理数据，退出")
        return

    semaphore = asyncio.Semaphore(CONCURRENCY)
    retry = RetryPolicy(max_retries=3, backoff_initial=0.2, backoff_max=1.0)
    started = time.perf_counter()

    with open(OUT_PATH, "a", encoding="utf-8") as sink:
        async with AsyncTypeSafeClient(retry=retry) as client:
            tasks = [label_one(client, semaphore, key, value) for key, value in pending.items()]
            for coroutine in asyncio.as_completed(tasks):
                row = await coroutine
                sink.write(json.dumps(row, ensure_ascii=False) + "\n")
                sink.flush()
                flag = "低置信" if row["confidence"] < 0.5 else "已打标"
                print("  [%s] %-6s conf=%.4f  %s" % (flag, row["topic"], row["confidence"], row["text"][:44]))

    elapsed = (time.perf_counter() - started) * 1000
    print()
    print("本轮 %d 条完成，耗时 %.0f ms，结果写入 %s" % (len(pending), elapsed, OUT_PATH))
    low = [line for line in open(OUT_PATH, encoding="utf-8") if json.loads(line)["confidence"] < 0.5]
    print("全量低置信条目数：%d（这些就是该进人工复核的部分）" % len(low))


if __name__ == "__main__":
    asyncio.run(main())
