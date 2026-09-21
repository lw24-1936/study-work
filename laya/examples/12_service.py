"""12 - 把 Laya 包成 HTTP 服务：启动时 preload，请求时只跑检测 + 一次前向。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 12_service.py            # 默认 127.0.0.1:8077
    # 另开一个终端：
    curl -s localhost:8077/health
    curl -s -X POST localhost:8077/decide -H 'Content-Type: application/json' -d @payload.json

依赖：fastapi、uvicorn（pip install fastapi uvicorn）
"""
import os
import time
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from laya import Router

DEVICE = os.environ.get("LAYA_DEVICE") or None          # "cpu" / "cuda" / None(自动)
PORT = int(os.environ.get("LAYA_PORT", "8077"))

# 默认问题集：生产上把它换成你自己的 schema，或让调用方通过 questions 字段传入
DEFAULT_QUESTIONS = {
    "department": {
        "type": "choice",
        "instructions": "Which department should handle this request?",
        "criteria": {
            "billing": "invoices, payments, refunds",
            "technical": "bugs, outages, system errors",
            "sales": "pricing, new contracts",
            "other": "everything else",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical deadline or blocking issue"],
    },
    "churn_risk": {
        "type": "noul",
        "instructions": "Does the user threaten to cancel or leave?",
    },
}


class DecideRequest(BaseModel):
    state: Any
    questions: Optional[Dict[str, Any]] = None
    model: Optional[str] = None          # english / multilingual / typed-decisions


app = FastAPI(title="laya-decide")
router: Router = None                    # 启动时赋值
STARTED_AT = time.time()


@app.on_event("startup")
def load_models():
    global router
    t0 = time.time()
    # 两步写法：Router(preload=["english", "multilingual"]) 会被当成 preload=True，
    # 把三个 checkpoint 全部加载（在 4 GB 显存的卡上会 OOM 并退回 CPU）。
    router = Router(device=DEVICE)
    router.preload(["english", "multilingual"])
    print("已 preload %s，耗时 %.1f s" % (router.loaded, time.time() - t0), flush=True)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "loaded": router.loaded,
        "device": DEVICE or "auto",
        "uptime_s": round(time.time() - STARTED_AT, 1),
    }


@app.post("/decide")
def decide(req: DecideRequest):
    t0 = time.time()
    res = router.predict(req.state, req.questions or DEFAULT_QUESTIONS, model=req.model)
    res["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return res


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
