"""13 - 批量打标：读 JSONL、逐条决策、可断点续跑、统计吞吐。

Laya 的一次 forward 能并行回答「一条 state 上的多个问题」，但多条 state 之间是循环的，
所以批量任务要自己写循环 + 进度 + 续跑。这个脚本就是最小可用的生产者。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 13_batch_labeling.py            # 生成 input.jsonl 并处理
    /opt/ai-lab/laya/.venv/bin/python 13_batch_labeling.py --resume   # 中断后再跑，跳过已完成
"""
import json
import os
import random
import sys

from laya import Router

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(HERE, "batch_input.jsonl")
OUTPUT = os.path.join(HERE, "batch_output.jsonl")

TEMPLATES = [
    "We were charged twice for {month}, please refund the duplicate.",
    "The {feature} page returns HTTP 500 since the last deploy.",
    "How do I migrate data from {vendor} to your platform?",
    "Please cancel our {plan} plan at the end of the month.",
    "What is the price difference between {plan} and enterprise?",
    "Our {integration} integration stopped syncing yesterday.",
]
MONTHS = ["January", "February", "March", "April", "May", "June"]
FEATURES = ["export", "reporting", "billing", "settings", "import"]
VENDORS = ["Salesforce", "HubSpot", "Zendesk", "Intercom"]
PLANS = ["starter", "growth", "team", "pro"]
INTEGRATIONS = ["Slack", "Jira", "Okta", "Snowflake"]

QUESTIONS = {
    "intent": {
        "type": "choice",
        "instructions": "What does the customer want in `message`?",
        "criteria": {
            "refund": "money returned or a duplicate charge reversed",
            "technical_help": "a bug, outage or integration problem",
            "billing_question": "a question about an invoice, plan or payment method",
            "information": "general information, pricing or how-to",
            "cancellation": "wants to cancel or downgrade",
            "other": "none of the other options fits",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is the request in `message`?",
        "criteria": ["no time pressure", "needs attention soon", "blocking issue or hard deadline"],
    },
    "needs_reply": {"type": "noul", "instructions": "Does the sender expect a reply?"},
}


def build_input(n=120, seed=7):
    rnd = random.Random(seed)
    with open(INPUT, "w", encoding="utf-8") as f:
        for i in range(n):
            text = rnd.choice(TEMPLATES).format(
                month=rnd.choice(MONTHS), feature=rnd.choice(FEATURES),
                vendor=rnd.choice(VENDORS), plan=rnd.choice(PLANS),
                integration=rnd.choice(INTEGRATIONS))
            f.write(json.dumps({"id": "t%04d" % i, "message": text}, ensure_ascii=False) + "\n")
    print("已生成 %d 条输入：%s" % (n, INPUT))


def done_ids():
    if not os.path.exists(OUTPUT):
        return set()
    ids = set()
    with open(OUTPUT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ids.add(json.loads(line)["id"])
    return ids


def main(resume=False):
    if not os.path.exists(INPUT):
        build_input()
    rows = [json.loads(l) for l in open(INPUT, encoding="utf-8") if l.strip()]
    already = done_ids() if resume else set()
    if already:
        print("续跑：跳过已完成 %d 条" % len(already))
    todo = [r for r in rows if r["id"] not in already]
    print("待处理 %d 条" % len(todo))

    router = Router(device=os.environ.get("LAYA_DEVICE") or None)
    router.preload(["english"])        # 两步写法，见 04_presets_triage.py 里的说明
    mode = "a" if already else "w"
    import time
    t0 = time.time()
    with open(OUTPUT, mode, encoding="utf-8") as out:
        for i, row in enumerate(todo, 1):
            res = router.predict({"message": row["message"]}, QUESTIONS)
            a = res["answers"]
            out.write(json.dumps({
                "id": row["id"],
                "message": row["message"],
                "intent": a["intent"]["choice"],
                "intent_confidence": a["intent"]["confidence"],
                "urgency": a["urgency"]["score"],
                "needs_reply": a["needs_reply"]["noul"],
                "model": res["routing"]["model"],
                "routing_reason": res["routing"]["reason"],
                "latency_ms": res["latency_ms"] if "latency_ms" in res else None,
            }, ensure_ascii=False) + "\n")
            out.flush()
            if i % 20 == 0 or i == len(todo):
                dt = time.time() - t0
                print("  已处理 %d/%d（%.2f s，%.1f 条/秒，%d tokens/条）"
                      % (i, len(todo), dt, i / dt, res["usage"]["input_tokens"]), flush=True)
    dt = time.time() - t0
    print("完成：%d 条，用时 %.1f s，吞吐 %.1f 条/秒" % (len(todo), dt, len(todo) / dt))
    print()

    # 汇总：各 intent 的条数与平均置信度，低置信度单独列出来送人工
    stats, low_conf = {}, []
    for line in open(OUTPUT, encoding="utf-8"):
        r = json.loads(line)
        s = stats.setdefault(r["intent"], {"n": 0, "conf": 0.0, "urgent": 0})
        s["n"] += 1
        s["conf"] += r["intent_confidence"]
        s["urgent"] += int(r["urgency"] >= 2.0)
        if r["intent_confidence"] < 0.5:
            low_conf.append(r)
    print("=== 结果分布 ===")
    for intent, s in sorted(stats.items(), key=lambda kv: -kv[1]["n"]):
        print("  %-18s %3d 条  平均置信度 %.3f  高紧急 %d 条"
              % (intent, s["n"], s["conf"] / s["n"], s["urgent"]))
    print("低置信度（<0.5）需要人工的：%d 条" % len(low_conf))
    for r in low_conf[:5]:
        print("   %s  %s  conf=%.3f" % (r["id"], r["message"][:52], r["intent_confidence"]))


if __name__ == "__main__":
    main(resume="--resume" in sys.argv)
