#!/usr/bin/env python3
"""本地模拟 TypeSafe API 服务（stub）。

用途：在没有真实 TYPESAFE_API_KEY 的情况下，完整跑通 SDK 的
请求序列化 -> HTTP 传输 -> 响应解析 -> 类型化答案 这条链路，
并演示错误分类与重试策略。

重要：本服务返回的 JSON 结构对齐 https://docs.typesafe.ai/api 的官方 schema，
但概率数值由本文件的启发式规则生成（关键词词干匹配 + 固定分布），
不是 Jev 模型的真实输出。真实数值必须用 API Key 打
https://api.typesafe.ai/v1/systemone 才会产生。

启动：
    /opt/ai-lab/jev/.venv/bin/python stub_server.py 8787

环境变量：
    STUB_FLAKY=1   前 2 次请求返回 503（带 retry-after-ms 头），用于演示 SDK 重试
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

FLAKY = os.environ.get("STUB_FLAKY") == "1"
_request_count = 0

# 用来演示「置信度路由」的测试标记：state 里出现该词时返回接近均摊的分布，
# 这样 confidence 会明显下降。
AMBIGUOUS_MARKER = "AMBIGUOUS"

# 分布的三个档位，用于让 confidence 落在有区分度的区间
CLEAR_TOP = 0.93
UNCLEAR_TOP = 0.60
FLAT = 0.0

# 题目里必然出现的虚词，不能当作「判断依据」的关键词（否则任何 state 都会命中）
STOPWORDS = frozenset(
    """
    does did this that these those the and for not any all can may might must need needs
    message reply text document content contain contains include includes with from about
    which what when where have has had been will would should could there here their them
    they your yours than then also into over only just some such same very more less
    present within given below above right now please help check
    """.split()
)


def _confidence(probabilities: dict[str, float]) -> float:
    """按分布形状计算 confidence：1 - 归一化熵，与官方文档描述的口径一致。

    https://docs.typesafe.ai/confidence 说明 confidence 由 probabilities 的形状
    推导：集中在一个选项时接近 1，均摊在多个选项时明显下降。
    本 stub 用归一化熵实现同样语义，仅用于演示。
    """
    values = [p for p in probabilities.values() if p > 0]
    if len(values) <= 1:
        return 1.0
    entropy = -sum(p * math.log2(p) for p in values)
    return round(1.0 - entropy / math.log2(len(probabilities)), 4)


def _estimate_tokens(payload: dict[str, Any]) -> int:
    """粗略估算 input token 数（按 4 字符 1 token），不是真实计费口径。"""
    text = json.dumps(payload.get("state", ""), ensure_ascii=False)
    text += json.dumps(payload.get("questions", {}), ensure_ascii=False)
    return max(1, len(text) // 4)


def _words(value: Any, min_len: int = 4) -> set[str]:
    """把任意 JSON 值拍平成小写单词集合。

    min_len=4 用于「关键词」抽取（避免 the/and 这类虚词）；
    min_len=3 用于 state 文本（fit、api、box 这类 3 字母实词必须保留）。
    """
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return {token.lower() for token in re.split(r"[^0-9A-Za-z]+", text) if len(token) >= min_len}


def _state_words(state: Any) -> set[str]:
    return _words(state, min_len=3)


def _norm(word: str) -> str:
    """去掉常见英文后缀，让 fits/fit、charges/charged、shipping/shipped 能对上。"""
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _stem(word: str) -> str:
    return _norm(word)[:5]


def _hits(state_words: set[str], keywords: set[str]) -> int:
    """词干命中数：归一化后取前 5 个字符比较，能覆盖 charges/charged、shipping/shipped 这类变形。"""
    state_stems = {_stem(word) for word in state_words}
    return len({keyword for keyword in keywords if _stem(keyword) in state_stems})


def _option_keywords(name: str, description: Any) -> set[str]:
    keywords = _words(name.replace("_", " "))
    keywords |= _words(description)
    return keywords


def _pick(state: Any, options: dict[str, Any]) -> tuple[str, bool]:
    """按关键词命中数选一个选项；全部未命中时退回第一个选项。"""
    state_words = _state_words(state)
    best_name = next(iter(options))
    best_hits = -1
    for name, description in options.items():
        hits = _hits(state_words, _option_keywords(name, description))
        if hits > best_hits:
            best_name, best_hits = name, hits
    return best_name, best_hits > 0


def _distribution(names: list[str], winner: str, top: float) -> dict[str, float]:
    if top == FLAT:
        share = round(1.0 / len(names), 4)
        return {name: share for name in names}
    if len(names) == 1:
        return {names[0]: 1.0}
    rest = round((1.0 - top) / (len(names) - 1), 4)
    return {name: (top if name == winner else rest) for name in names}


def _choose(state: Any, question: dict[str, Any], flat: bool) -> dict[str, Any]:
    criteria = question.get("criteria", {}) or {"unknown": None}
    winner, matched = _pick(state, criteria)
    top = FLAT if flat else (CLEAR_TOP if matched else UNCLEAR_TOP)
    probabilities = _distribution(list(criteria), winner, top)
    return {
        "type": "choice",
        "choice": winner,
        "confidence": _confidence(probabilities),
        "probabilities": probabilities,
    }


def _state_values(state: Any) -> str:
    """取 state 的「值」文本（dict 只取 value，不取 key），用于判断题匹配。"""
    if isinstance(state, dict):
        parts = [value if isinstance(value, str) else json.dumps(value, ensure_ascii=False) for value in state.values()]
        return " ".join(parts)
    return json.dumps(state, ensure_ascii=False)


def _noul(state: Any, question: dict[str, Any], flat: bool) -> dict[str, Any]:
    if flat:
        return {"type": "noul", "noul": 0.5}
    # 只取长度 >= 4 的实词，并剔除在题目里必然出现的虚词，避免假命中
    keywords = {word for word in _words(question.get("instructions", "")) if word not in STOPWORDS}
    criteria = question.get("criteria") or {}
    keywords |= _words(criteria.get("true", ""))
    hit = _hits(_state_words(_state_values(state)), keywords)
    return {"type": "noul", "noul": 0.93 if hit else 0.08}


def _score(state: Any, question: dict[str, Any], flat: bool) -> dict[str, Any]:
    levels = question.get("criteria", []) or ["unknown"]
    count = len(levels)
    if flat:
        probabilities = _distribution([str(i) for i in range(count)], "0", FLAT)
    else:
        # 命中哪一级描述就压在哪一级；一级都不命中时压在最轻的一级（保守兜底）
        state_words = _state_words(state)
        scores = [_hits(state_words, _words(level)) for level in levels]
        target = scores.index(max(scores)) if max(scores) > 0 else 0
        probabilities = {str(i): (0.0 if i != target else 1.0) for i in range(count)}
        if count >= 2:
            neighbour = target + 1 if target + 1 < count else target - 1
            probabilities[str(target)] = 0.7
            probabilities[str(neighbour)] = 0.3
    score = round(sum(int(key) * value for key, value in probabilities.items()), 4)
    legend = {str(index): level for index, level in enumerate(levels)}
    return {
        "type": "score",
        "score": score,
        "confidence": _confidence(probabilities),
        "legend": legend,
        "probabilities": probabilities,
    }


def build_response(payload: dict[str, Any]) -> dict[str, Any]:
    state = payload.get("state", "")
    flat = AMBIGUOUS_MARKER in json.dumps(state, ensure_ascii=False)
    answers: dict[str, Any] = {}
    for name, question in payload.get("questions", {}).items():
        kind = question.get("type")
        if kind == "choice":
            answers[name] = _choose(state, question, flat)
        elif kind == "noul":
            answers[name] = _noul(state, question, flat)
        elif kind == "score":
            answers[name] = _score(state, question, flat)
    return {
        "model": "jev-1.13.0",
        "answers": answers,
        "usage": {
            "input_tokens": _estimate_tokens(payload),
            "output_tokens": 12 * max(1, len(answers)),
        },
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, status: int, body: dict[str, Any], extra_headers: dict[str, str] | None = None) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("x-typesafe-request-id", "req_stub_0001")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802 - http.server 要求的固定方法名
        if self.path.startswith("/v1/models"):
            self._send_json(
                200,
                {
                    "models": [
                        {
                            "name": "jev-1.13.0",
                            "description": "General-purpose system one model.",
                            "release_date": "2026-09-15",
                        },
                        {
                            "name": "jev-latest",
                            "description": "Alias for the most recent stable release.",
                            "release_date": "2026-09-15",
                        },
                    ]
                },
            )
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - http.server 要求的固定方法名
        global _request_count
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if not self.path.startswith("/v1/systemone"):
            self._send_json(404, {"error": "not found"})
            return
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or len(auth) <= len("Bearer "):
            self._send_json(401, {"error": "Cannot authenticate with the server. Please check your API key and try again."})
            return
        _request_count += 1
        if FLAKY and _request_count <= 2:
            print("[stub] 第 %d 次请求 -> 503（模拟上游抖动）" % _request_count, file=sys.stderr)
            self._send_json(503, {"error": "upstream temporarily unavailable"}, {"retry-after-ms": "200"})
            return
        try:
            payload = json.loads(raw.decode("utf-8"))
        except ValueError:
            self._send_json(400, {"error": "invalid json"})
            return
        print("[stub] 收到请求：", json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        self._send_json(200, build_response(payload))

    def log_message(self, format: str, *args: Any) -> None:
        print("[stub] " + format % args, file=sys.stderr)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("[stub] 监听 http://127.0.0.1:%d（FLAKY=%s）" % (port, FLAKY), file=sys.stderr)
    server.serve_forever()


if __name__ == "__main__":
    main()
