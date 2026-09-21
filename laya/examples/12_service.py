"""12 - 把 Laya 包成 HTTP 服务：启动时 preload，请求时只跑检测 + 一次前向。

跑法：
    export HF_ENDPOINT=https://hf-mirror.com
    /opt/ai-lab/laya/.venv/bin/python 12_service.py            # 默认 127.0.0.1:8077
    # 另开一个终端：
    curl -s localhost:8077/health
    curl -s -X POST localhost:8077/decide -H 'Content-Type: application/json' -d @payload.json

对外提供服务（别的机器 / 手机 / 前端页面要调用）时：
    export LAYA_HOST=0.0.0.0                 # 默认 127.0.0.1，只有本机能连
    export LAYA_API_KEY=<自己设一串随机字符>   # 设了之后 /decide 必须带 X-API-Key 头
    /opt/ai-lab/laya/.venv/bin/python 12_service.py
    # 从另一台机器：
    curl -s http://<本机IP>:8077/health
    curl -s -X POST http://<本机IP>:8077/decide \
         -H 'Content-Type: application/json' -H "X-API-Key: $KEY" -d @payload.json

依赖：fastapi、uvicorn（pip install fastapi uvicorn）
"""
import os
import time
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from laya import Router

DEVICE = os.environ.get("LAYA_DEVICE") or None          # "cpu" / "cuda" / None(自动)
PORT = int(os.environ.get("LAYA_PORT", "8077"))
HOST = os.environ.get("LAYA_HOST", "127.0.0.1")          # 对外服务要设 0.0.0.0
API_KEY = os.environ.get("LAYA_API_KEY")                 # 不设 = 不校验（仅限本机自用）

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
        "auth": bool(API_KEY),
        "uptime_s": round(time.time() - STARTED_AT, 1),
    }


def require_key(x_api_key: Optional[str] = Header(default=None)):
    """设了 LAYA_API_KEY 才校验；用比较运算而非 == 也无所谓——这是内网服务，不做时序攻击防护。"""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="bad or missing X-API-Key")


@app.post("/decide")
def decide(req: DecideRequest, _: None = Depends(require_key)):
    t0 = time.time()
    res = router.predict(req.state, req.questions or DEFAULT_QUESTIONS, model=req.model)
    res["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return res


if __name__ == "__main__":
    print("监听 http://%s:%d（鉴权：%s）" % (HOST, PORT, "开" if API_KEY else "关"), flush=True)
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
