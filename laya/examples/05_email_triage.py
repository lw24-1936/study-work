"""05 - 邮件场景：先清洗正文（去引用/签名/免责声明），再做分类 + 钓鱼判定。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 05_email_triage.py
"""
import json
import os

from laya import Router, clean_email_body, email_questions, email_state

RAW_BODY = """Hi support team,

We were charged twice for the March invoice. Please refund the duplicate charge today.

Thanks,
John Doe
Head of Finance, Acme Corp

On Mon, 15 Sep 2026 at 09:12, Support <support@vendor.com> wrote:
> Hello John,
> Your invoice for March has been issued, please review it.
> Kind regards,
> The Support Team

This email and any files transmitted with it are confidential and intended solely
for the use of the addressee. If you have received this email in error please
notify the sender.
"""

print("=== clean_email_body 的效果 ===")
cleaned = clean_email_body(RAW_BODY)
print("  原文 %d 字符 -> 清洗后 %d 字符" % (len(RAW_BODY), len(cleaned)))
print("  清洗后全文：")
for line in cleaned.splitlines():
    print("    |", line)
print("  引用段被丢弃：", "wrote:" not in cleaned)
print("  签名被丢弃  ：", "Head of Finance" not in cleaned)
print("  免责声明被丢弃：", "confidential" not in cleaned)
print()

state = email_state(subject="Duplicate charge on invoice #4411", body=RAW_BODY,
                    sender="john.doe@acme.com")
print("=== email_state 生成的 state ===")
print(json.dumps(state, ensure_ascii=False, indent=2))
print()

router = Router(device=os.environ.get("LAYA_DEVICE") or None)
router.preload(["english"])            # 只加载英文 checkpoint（见 04 里的说明）

emails = {
    "重复扣费（正常工单）": state,
    "钓鱼邮件": email_state(
        subject="Urgent: verify your account within 24 hours",
        body=("Dear customer, your account will be suspended. Click http://acme-secure-login.top "
              "and confirm your password and card number to keep access."),
        sender="security@acme-secure-login.top"),
    "推广邮件": email_state(
        subject="We noticed you might like our new product",
        body="Buy now and get 30% off. Unsubscribe link below. Limited offer, act fast!",
        sender="noreply@bulk-sender.example"),
}

for name, st in emails.items():
    res = router.predict(st, email_questions())
    a = res["answers"]
    print("--- %s ---" % name)
    print("  category   :", a["category"]["choice"], a["category"]["probabilities"])
    print("  is_phishing:", a["is_phishing"]["noul"], " confidence %.4f" % a["is_phishing"]["confidence"])
    print("  is_spam    :", a["is_spam"]["noul"])
    print("  urgency    :", a["urgency"]["score"], "/ 2.0")
    print("  needs_reply:", a["needs_reply"]["noul"])
    print()

print("=== 按结果决定动作 ===")
st = emails["钓鱼邮件"]
a = router.predict(st, email_questions())["answers"]
if a["is_phishing"]["noul"] >= 0.8:
    print("  隔离邮件 + 通知安全团队（P(phishing)=%.3f）" % a["is_phishing"]["noul"])
else:
    print("  投递到 %s 队列" % a["category"]["choice"])
