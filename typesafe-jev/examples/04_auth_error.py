#!/usr/bin/env python3
"""04 错误处理：把 SDK 的异常分类对齐到代码分支。

这里故意打真实地址 https://api.typesafe.ai，用一个无效 Key，
观察真实的 401 响应与异常类型（不消耗额度，也不会成功计费）。

运行：
    /opt/ai-lab/jev/.venv/bin/python 04_auth_error.py
"""

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    TypeSafeAPIError,
    TypeSafeAPIResponseValidationError,
    TypeSafeAuthenticationError,
    TypeSafeAPIConnectionError,
    TypeSafeClient,
    TypeSafePermissionDeniedError,
    TypeSafeRateLimitError,
    TypeSafeUnprocessableEntityError,
)

# 无效 Key：仅用于演示鉴权失败路径，真实 Key 请从 console.typesafe.ai/keys 获取
INVALID_KEY = "ts_invalid_key_for_demo"

with TypeSafeClient(api_key=INVALID_KEY, base_url="https://api.typesafe.ai", retry=RetryPolicy(max_retries=0)) as client:
    try:
        client.system_one(
            state="I was charged twice. Please help.",
            questions={"billing": Noul(instructions="Is this about billing?")},
        )
    except TypeSafeAuthenticationError as exc:
        print("命中 TypeSafeAuthenticationError（401，Key 无效或缺失）")
        print("  status     :", exc.status)
        print("  message    :", exc)
        print("  body       :", exc.body)
        print("  request_id :", exc.request_id)
    except TypeSafeAPIConnectionError as exc:
        print("网络层失败：", type(exc).__name__, exc)

    try:
        client.models.list()
    except TypeSafeAPIError as exc:
        print()
        print("models.list() 同样失败：", type(exc).__name__, "->", exc)

print()
print("异常分层（用于写代码分支）：")
for name in (
    "TypeSafeAPIError           401/403/404/422/429/5xx 等带 HTTP 响应的失败",
    "  TypeSafeAuthenticationError   401 鉴权失败（Key 错/过期）",
    "  TypeSafePermissionDeniedError 403 无权限（模型或功能未开通）",
    "  TypeSafeUnprocessableEntityError 422 请求体校验失败（问句缺 criteria 等）",
    "  TypeSafeRateLimitError        429 超限，带 retry_after_ms 属性",
    "  TypeSafeAPIResponseValidationError 200 但响应体结构不符",
    "TypeSafeAPIConnectionError  没有拿到 HTTP 响应的失败（DNS/连接/超时）",
    "  TypeSafeAPITimeoutError       请求超时，带 timeout 属性",
    "TypeSafeError               客户端参数错误（缺 Key、timeout 非法等）",
):
    print("  " + name)

# 关键点：422 这类「请求写错了」不该重试，429/5xx 才该重试。
policy = RetryPolicy(max_retries=2, http_statuses={408, 429, 500, 502, 503, 504}, respect_retry_after=True)
print()
print("默认重试策略字段：", policy)
