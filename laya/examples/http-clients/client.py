#!/usr/bin/env python3
"""外部调用客户端（只用标准库，不需要 laya / torch / venv）。

在任意一台能连到服务的机器上跑：
    export LAYA_API_KEY=...                  # 服务端设了 key 才需要
    python3 client.py --url http://192.168.1.167:8077 --text "请把 3 月的账单退款"
    python3 client.py --url http://127.0.0.1:8077 --text "..." --raw      # 打印完整 JSON

设计要点（和别人的调用方式对接时踩过的）：
  * 用 urllib 而不是 requests：目标机器上不一定有 pip 环境，标准库最省事；
  * state 既可以是字符串，也可以是 dict（这里传 {"message": ...}，和服务端默认问题集对齐）；
  * 一定要处理 HTTP 错误码：401 是 key 不对，503 是模型还没加载完（服务在 preload 中）。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def call(url, text, key=None, model=None, timeout=60.0):
    payload = {"state": {"message": text}}
    if model:
        payload["model"] = model
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url.rstrip("/") + "/decide", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if key:
        req.add_header("X-API-Key", key)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 401：key 错；422：请求体不符合 schema；503：模型没加载完
        detail = e.read().decode("utf-8", "replace")[:300]
        raise SystemExit("HTTP %s: %s" % (e.code, detail))
    except urllib.error.URLError as e:
        raise SystemExit("连不上服务（%s）。检查 IP/端口，以及服务端是否 LAYA_HOST=0.0.0.0。" % e.reason)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="服务地址，例如 http://192.168.1.167:8077")
    ap.add_argument("--text", required=True, help="要分诊的文本")
    ap.add_argument("--model", default=None, choices=["english", "multilingual", "typed-decisions"])
    ap.add_argument("--key", default=os.environ.get("LAYA_API_KEY"))
    ap.add_argument("--raw", action="store_true")
    args = ap.parse_args()

    res = call(args.url, args.text, key=args.key, model=args.model)
    if args.raw:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    a = res["answers"]
    print("路由模型   : %s（%s）" % (res["routing"]["model"], res["routing"]["reason"]))
    print("部门       : %s（置信度 %.4f）" % (a["department"]["choice"], a["department"]["confidence"]))
    print("紧急度     : %.2f  %s" % (a["urgency"]["score"], a["urgency"].get("legend", {})))
    print("流失风险   : %s（置信度 %.4f）" % (a["churn_risk"]["noul"], a["churn_risk"]["confidence"]))
    print("tokens     : 输入 %d" % res["usage"]["input_tokens"])
    print("服务端耗时 : %.1f ms（不含网络往返）" % res["latency_ms"])


if __name__ == "__main__":
    main()
