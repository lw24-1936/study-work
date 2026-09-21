"""03 - Router：先看路由决策（不跑前向），再真的跑一次多语言请求。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 03_router.py
第一次运行会下载英文（843 MB）+ 多语言（644 MB）两个 checkpoint。
"""
import json
import os
import time

from laya import Router, detect_script, is_english
from laya.lang import analyse, guess_latin_language

state = {"body": "I was charged twice for March, please refund the duplicate."}
questions = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this request?",
        "criteria": {"billing": "invoices, payments, refunds",
                     "technical": "bugs, outages, system errors",
                     "other": "everything else"},
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical deadline or blocking issue"],
    },
}

print("=== 1. 纯 Python 的语言/文字系统检测（<1 ms，不加载模型，不跑前向） ===")
samples = {
    "英文": "I was charged twice for March, please refund the duplicate payment.",
    "德文": "Der Kunde wurde zweimal belastet, bitte erstatten Sie die Zahlung.",
    "法文": "Le client a été facturé deux fois, veuillez rembourser.",
    "印地文": "मुझसे दो बार शुल्क लिया गया, कृपया पैसे वापस करें।",
    "中文": "客户被重复扣费了两次，请立即退款。",
    "韩文": "고객이 두 번 청구되었습니다. 환불해 주세요.",
    "泰文": "ลูกค้าถูกเรียกเก็บเงินซ้ำสองครั้ง กรุณาคืนเงิน",
}
for name, text in samples.items():
    det = analyse({"body": text})
    t0 = time.time()
    script = detect_script(text)
    dt_us = (time.time() - t0) * 1e6
    print("  %-6s script=%-12s language=%-6s is_english=%-5s 非拉丁占比=%.2f"
          "  detect_script 耗时 %.0f us"
          % (name, script, det["language"], det["is_english"], det["non_latin_fraction"], dt_us))
print("  停用词启发式（guess_latin_language）单独调用：",
      guess_latin_language(samples["德文"]), "/", is_english(samples["德文"]))

print()
print("=== 2. route()：只做决策，不加载、不推理 ===")
router = Router()          # 此时一个模型都没加载
print("  router.loaded =", router.loaded, " (空列表 = 还没加载任何 checkpoint)")
cases = {
    "英文工单": {"body": samples["英文"]},
    "德文工单": {"body": samples["德文"]},
    "印地文工单": {"body": samples["印地文"]},
    "中文工单": {"body": samples["中文"]},
    "只有数字没有字母": {"amount": 12345},
}
for name, st in cases.items():
    d = router.route(st, questions)
    print("  %-16s -> model=%-13s repo=%s" % (name, d.model, d["repo"]))
    print("  %-16s    reason=%s" % ("", d.reason))
print("  显式指定：", router.route(state, questions, model="typed-decisions").reason)
print("  显式指定语言：", router.route(state, questions, lang="de").reason)

print()
print("=== 3. predict()：路由 + 一次前向，返回里带 routing 字段 ===")
t0 = time.time()
router.preload(["english", "multilingual"])
print("  preload 两个 checkpoint 用时 %.1f s，常驻：%s" % (time.time() - t0, router.loaded))
print()
for name, st in [("英文", {"body": samples["英文"]}), ("德文", {"body": samples["德文"]}),
                 ("印地文", {"body": samples["印地文"]}), ("中文", {"body": samples["中文"]})]:
    t0 = time.time()
    res = router.predict(st, questions)
    dt = (time.time() - t0) * 1000
    print("  [%s] %.0f ms" % (name, dt))
    print("     department =", res["answers"]["department"]["choice"],
          res["answers"]["department"]["probabilities"])
    print("     urgency    =", res["answers"]["urgency"]["score"])
    print("     routing    =", json.dumps(res["routing"], ensure_ascii=False))
print()
print("  router.loaded =", router.loaded)
