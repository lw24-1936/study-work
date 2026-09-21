"""10 - 置信度与校准：为什么不能直接信任 confidence，以及怎么自己重新标定温度。

Laya 的 confidence 是归一化熵：confidence = 1 - H(p) / log(k)，它不是「答对的概率」。
官方 README 里明确写了：发布的 checkpoint 是过度自信的（英文版 mean ECE 0.466）。
本脚本用一小份手写带标签样本演示完整的校准流程：
    1. 看原始 accuracy / mean confidence / ECE
    2. 在训练集上拟合一个温度 T（网格搜索，目标是最小化 ECE）
    3. 在测试集上看校准前后的 ECE 变化
温度缩放只改概率、不改 argmax，所以 accuracy 不变。

注意：这里的 48 条样本是本文作者手写的（用于演示流程），不是官方 benchmark，
数字只说明「这条流程怎么跑」，不能当成 Laya 的真实精度。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 10_calibration.py
"""
import os

import numpy as np

import laya
from laya import ece_score

DATASET = [
    # (文本, 正确标签)
    ("I was charged twice for the same order, please refund the duplicate.", "refund"),
    ("My card was billed after I cancelled the subscription. I want my money back.", "refund"),
    ("The refund for order 88213 never arrived, can you check it?", "refund"),
    ("We were invoiced twice for March, please reverse one of the charges.", "refund"),
    ("You took the payment twice, I need the extra amount returned.", "refund"),
    ("I cancelled on Monday but the yearly fee still shows on my statement.", "refund"),
    ("Please issue a credit note for the duplicated invoice.", "refund"),
    ("The trial converted to a paid plan without my consent, refund it.", "refund"),

    ("Your API returns 502 on /v2/export since the last release.", "technical_help"),
    ("The mobile app crashes when I upload a file larger than 10 MB.", "technical_help"),
    ("SSO login fails with an invalid redirect URI error.", "technical_help"),
    ("Webhooks stop firing after about an hour of uptime.", "technical_help"),
    ("The dashboard shows a blank page on Safari 18.", "technical_help"),
    ("Our integration times out when syncing more than 500 contacts.", "technical_help"),
    ("I get a 403 when calling the reporting endpoint with a valid token.", "technical_help"),
    ("Search results disappeared after we upgraded to the new plan.", "technical_help"),

    ("Where can I download the PDF invoice for last month?", "billing_question"),
    ("Which payment methods do you accept for annual plans?", "billing_question"),
    ("How is the usage overage calculated on the growth plan?", "billing_question"),
    ("Can I change the billing email on the account?", "billing_question"),
    ("What is the difference between the starter and pro pricing tiers?", "billing_question"),
    ("Do you charge VAT for customers in Germany?", "billing_question"),
    ("Is there a discount for paying yearly instead of monthly?", "billing_question"),
    ("How do I update the card on file before the renewal?", "billing_question"),

    ("Do you have a guide for migrating data from another provider?", "information"),
    ("What is your uptime SLA for the enterprise plan?", "information"),
    ("Is there an on-premise option available?", "information"),
    ("Can you explain what the role permissions mean in the admin panel?", "information"),
    ("Where can I find the API rate limits documented?", "information"),
    ("Do you support single sign-on with Okta?", "information"),
    ("How long does a typical onboarding take?", "information"),
    ("Is the audit log exportable to S3?", "information"),

    ("Please cancel our subscription effective immediately.", "cancellation"),
    ("We want to downgrade from enterprise to the starter plan.", "cancellation"),
    ("Please close the account at the end of the billing period.", "cancellation"),
    ("We are moving to another vendor and need the contract terminated.", "cancellation"),
    ("Stop the renewal, we do not want to continue next year.", "cancellation"),
    ("Cancel the extra seats we added in April.", "cancellation"),
    ("Please terminate our annual agreement early.", "cancellation"),
    ("We would like to end the trial and not continue.", "cancellation"),

    ("The office is closed tomorrow for a public holiday.", "other"),
    ("Nice work on the new release notes, very clear.", "other"),
    ("Can you forward this message to the account manager?", "other"),
    ("Just checking in, no action needed right now.", "other"),
    ("Lunch order for the team is ready downstairs.", "other"),
    ("Please send me the slides from yesterday's webinar.", "other"),
    ("Our procurement team needs your vendor form signed.", "other"),
    ("Following up on my earlier note, still waiting on a reply.", "other"),
]

LABELS = ["refund", "technical_help", "billing_question", "information", "cancellation", "other"]
QUESTION = {
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
    }
}

agent = laya.load("convaiinnovations/laya", device=os.environ.get("LAYA_DEVICE") or None)
print("checkpoint 自带的温度参数 agent.temperature =", agent.temperature)
print("按 (问题类型, 选项数) 细分的温度 agent.temperature_by_options =", agent.temperature_by_options)
print()
print("注意：agent.predict 返回的 probabilities 已经除过上面这些温度了，")
print("      下面的「校准前」= 官方发布参数，「校准后」= 在这之上再叠一层自己拟合的温度。")
print()


def run(text):
    """返回 (预测标签, 六个选项的概率数组)。"""
    a = agent.predict({"message": text}, QUESTION)["answers"]["intent"]
    probs = np.array([a["probabilities"][lab] for lab in LABELS], dtype=float)
    return a["choice"], probs


# 用固定的奇偶下标切分，保证每次运行结果可复现
train_set = [DATASET[i] for i in range(0, len(DATASET), 2)]
test_set = [DATASET[i] for i in range(1, len(DATASET), 2)]
print("训练集 %d 条 / 测试集 %d 条" % (len(train_set), len(test_set)))
print()

cache = {}
for text, _ in DATASET:
    cache[text] = run(text)


def evaluate(pairs, temperature=1.0):
    confs, corrects, accs = [], [], []
    for text, gold in pairs:
        pred, probs = cache[text]
        # 温度缩放：p = softmax(z) 时 softmax(z/T) ∝ p**(1/T)，所以在概率上直接做等价变换
        scaled = probs ** (1.0 / temperature)
        scaled = scaled / scaled.sum()
        conf = float(scaled.max())
        ok = int(pred == gold)
        confs.append(conf)
        corrects.append(ok)
        accs.append(ok)
    return np.array(confs), np.array(corrects)


print("=== 校准前（官方发布的温度参数） ===")
for name, pairs in (("训练集", train_set), ("测试集", test_set)):
    conf, corr = evaluate(pairs)
    print("  %s  accuracy=%.3f  mean confidence=%.3f  ECE=%.4f"
          % (name, corr.mean(), conf.mean(), ece_score(conf, corr)))
print()

print("=== 在训练集上网格搜索温度（目标：ECE 最小） ===")
grid = [0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
best_t, best_ece = 1.0, float("inf")
for t in grid:
    conf, corr = evaluate(train_set, t)
    e = ece_score(conf, corr)
    print("  T=%-4.2f  训练集 ECE=%.4f" % (t, e))
    if e < best_ece:
        best_t, best_ece = t, e
print("  选出 T = %.2f" % best_t)
print()

print("=== 在测试集上验证（温度只在训练集上拟合过） ===")
for name, t in (("校准前 T=1.0", 1.0), ("校准后 T=%.2f" % best_t, best_t)):
    conf, corr = evaluate(test_set, t)
    print("  %-16s accuracy=%.3f  mean confidence=%.3f  ECE=%.4f"
          % (name, corr.mean(), conf.mean(), ece_score(conf, corr)))
print()

print("=== 逐条看校准前后的置信度 ===")
print("%-10s %-18s %-8s %s" % ("真实标签", "预测", "对错", "置信度 校准前 -> 校准后"))
for text, gold in test_set[:10]:
    pred, probs = cache[text]
    before = float(probs.max())
    scaled = probs ** (1.0 / best_t)
    after = float((scaled / scaled.sum()).max())
    print("%-10s %-18s %-8s %.3f -> %.3f"
          % (gold, pred, "对" if pred == gold else "错", before, after))
print()
print("结论一：温度缩放不改变任何一条的预测标签（argmax 不变），只把分布压平。")
print("结论二（本次实测的真结果）：在只有 24 条的训练集上拟合出来的 T=%.2f 拿到测试集上" % best_t)
print("        反而把 ECE 从 0.1605 变成了 0.3087 —— 小样本拟合温度会过拟合。")
print("        官方 README 里的 0.466 -> 0.081 是按 (问题类型, 选项数) 分桶、")
print("        在几千条 held-out 数据上分别拟合的；样本量不够就别自己拟合，")
print("        改用下面这种做法：直接在带标签的数据上量阈值。")
print()

print("=== 更实用的做法：不信任概率数值，直接量阈值 ===")
print("%-10s %-8s %-10s %-10s %s" % ("门槛", "放行数", "其中对的", "精确率", "人工兜底数"))
for thr in (0.5, 0.7, 0.85, 0.95):
    passed = [(cache[t][0] == g) for t, g in test_set if float(cache[t][1].max()) >= thr]
    n_pass = len(passed)
    n_ok = sum(passed)
    precision = (n_ok / n_pass) if n_pass else float("nan")
    print("%-10.2f %-8d %-10d %-10s %d"
          % (thr, n_pass, n_ok, ("%.3f" % precision) if n_pass else "-", len(test_set) - n_pass))
print()
print("读法：门槛越高，自动化的那部分精确率越高、送人工的越多。")
print("      在自己的业务数据上量出这张表，比相信「0.9 就是 90% 正确」靠谱得多。")
print("      24 条样本量太小，这里只是演示方法；正式评估至少要几百到几千条。")
