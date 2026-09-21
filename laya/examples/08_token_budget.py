"""08 - token 预算：选项多了会怎样，head_max_len/max_len 怎么调。

Laya 把一条输入切成两段预算：
    head_max_len  留给「问题类型 + 指令 + 所有选项」的 token 数（英文默认 192，多语言/typed-decisions 默认 256）
    max_len       整条序列上限（英文默认 512，多语言/typed-decisions 默认 1024），剩下的给 state
选项共享 head_max_len：选项越多，每个选项分到的 token 越少。laya 不会把选项丢掉，而是
逐个把选项截断到 (head_max_len - 16) // 选项数 个 token（下限 4），所以选项描述会被拦腰砍掉，
模型看到的选项变成难以区分的碎片——这是高基数（50+ 选项）选择题的真正失败原因。

跑法：
    HF_ENDPOINT=https://hf-mirror.com /opt/ai-lab/laya/.venv/bin/python 08_token_budget.py
"""
import os
import time

import laya
from laya.common import render_options

DEVICE = os.environ.get("LAYA_DEVICE") or None

agent = laya.load("convaiinnovations/laya", device=DEVICE)
tok = agent.tok
print("英文 checkpoint 默认：max_len=%s  head_max_len=%s"
      % (agent.cfg.get("max_len"), agent.cfg.get("head_max_len")))
print()


def options(n, wordy=False):
    out = {}
    for i in range(n):
        label = "intent_%02d" % i
        out[label] = ("a fairly long description of intent %02d that consumes tokens" % i
                      if wordy else "intent %02d" % i)
    return out


def head_token_cost(n, wordy=False, head_max_len=192):
    """复算 build_sequence 里给选项分配了多少 token、每个选项最终能留几个 token。"""
    q = {"t": "choice", "ins": "Which intent is this?", "crit": options(n, wordy)}
    opts = render_options(q)
    ids = []
    for text in opts:
        ids.append([tok.mask_token_id] + tok(" " + text, add_special_tokens=False)["input_ids"][:48])
    total = sum(len(o) for o in ids)
    budget = head_max_len - total
    per = min(48, max(4, (head_max_len - 16) // max(1, len(ids))))
    return total, budget, per


print("=== 选项数与 head 预算（head_max_len=192） ===")
print("%-8s %-16s %-14s %s" % ("选项数", "选项原始占用", "剩余给指令", "每选项保留 token"))
for n in (4, 10, 30, 50, 77, 120):
    total, budget, per = head_token_cost(n)
    print("%-8d %-16d %-14d %d" % (n, total, budget, per))
print()

print("=== 截断后模型实际看到的选项文本（77 个选项，每选项只留 4 个 token） ===")
n = 77
total, budget, per = head_token_cost(n)
q = {"t": "choice", "ins": "Which intent is this?", "crit": options(n)}
opts = render_options(q)
shown = 0
for text in opts:
    ids = [tok.mask_token_id] + tok(" " + text, add_special_tokens=False)["input_ids"][:48]
    kept = ids[:per]
    print("  原选项 %-18s -> 截断后保留 %s" % (text, repr(tok.decode(kept))))
    shown += 1
    if shown == 5:
        break
print("  ...（其余 %d 个选项同理，都只剩开头几个 token）" % (len(opts) - shown))
print("  换成真实的长标签更能看出问题：")
real = {"billing": "invoices, payments, refunds and duplicate charges",
        "technical": "bugs, outages, integrations and system errors",
        "sales": "pricing, demos, new purchases and contract renewals"}
for label, desc in real.items():
    text = "%s: %s" % (label, desc)
    ids = [tok.mask_token_id] + tok(" " + text, add_special_tokens=False)["input_ids"]
    print("    %-60s -> 4 个 token 后只剩 %s" % (text, repr(tok.decode(ids[:4]))))
print("  对比：4 个选项时每选项可留 44 token，整句描述都能看到。")
print()

print("=== 修法一：抬高 head_max_len / max_len ===")
for head in (192, 256, 512, 1024):
    total, budget, per = head_token_cost(n, head_max_len=head)
    print("  head_max_len=%-5d -> 每选项保留 %d token" % (head, per))
agent.cfg["head_max_len"] = 512
agent.cfg["max_len"] = 1024
state = {"request": "route this to the right intent"}
t0 = time.time()
res = agent.predict(state, {"intent": {"type": "choice", "instructions": "Which intent?",
                                       "criteria": options(n)}})
print("  抬高后实际跑一次：%.0f ms，输入 %d tokens，答案 = %s"
      % ((time.time() - t0) * 1000, res["usage"]["input_tokens"],
         res["answers"]["intent"]["choice"]))
print()

print("=== 修法二：两级选择（先大类，再具体项）——每级选项数都很小 ===")
agent.cfg["head_max_len"] = 192
agent.cfg["max_len"] = 512
coarse = {"type": "choice", "instructions": "Which group does this request belong to?",
          "criteria": {"group_a": "intents intent_00 to intent_19",
                       "group_b": "intents intent_20 to intent_39",
                       "group_c": "intents intent_40 to intent_59",
                       "group_d": "intents intent_60 to intent_76"}}
first = agent.predict(state, {"group": coarse})["answers"]["group"]
group_index = {"group_a": 0, "group_b": 1, "group_c": 2, "group_d": 3}[first["choice"]]
fine = {"intent_%02d" % i: "intent %02d" % i
        for i in range(group_index * 20, min(group_index * 20 + 20, n))}
second = agent.predict(state, {"intent": {"type": "choice", "instructions": "Which intent?",
                                          "criteria": fine}})["answers"]["intent"]
print("  第一级 = %s %s" % (first["choice"], first["probabilities"]))
print("  第二级 = %s（候选 %d 个）%s" % (second["choice"], len(fine), second["probabilities"]))
print()

print("=== 选项多到放不进 max_len 时 laya 会直接报错（而不是静默出错） ===")
agent.cfg["head_max_len"] = 192
agent.cfg["max_len"] = 64             # 故意把总长压到比 head 还短
try:
    agent.predict(state, {"intent": {"type": "choice", "instructions": "Which intent?",
                                     "criteria": options(30)}})
    print("  没有报错")
except ValueError as exc:
    print("  ValueError:", exc)
agent.cfg["max_len"] = 512
print()

print("=== 状态文本超长时的截断行为 ===")
long_state = {"body": " ".join(["duplicate charge refund"] * 500)}
res = agent.predict(long_state, {"department": {"type": "choice",
                                               "instructions": "Which department?",
                                               "criteria": {"billing": "payments and refunds",
                                                            "other": "everything else"}}})
print("  状态 %d 字符（约 %d tokens）时，实际送进模型 %d tokens（max_len=%d 封顶）"
      % (len(long_state["body"]), len(tok(long_state["body"])["input_ids"]),
         res["usage"]["input_tokens"], agent.cfg["max_len"]))
print("  build_sequence 默认 truncate_left=False：保留 state 的前一段，砍掉尾部。")
print("  需要保留结尾（例如「请立即退款」写在最后）时，只能自己先把 state 截短再传进来。")
