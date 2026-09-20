#!/usr/bin/env bash
# 08 直接调用 HTTP API（不经 SDK）
#
# 用法：
#   bash 08_curl.sh                 # 打真实 API，用无效 Key 演示 401
#   bash 08_curl.sh stub            # 打本地 stub，演示 200 与完整响应体
#
# 注意：脚本不把 Key 拼进命令行明文（会进 shell 历史和 ps），从环境变量读取。

set -u

BASE_URL="https://api.typesafe.ai"
if [ "${1:-}" = "stub" ]; then
  BASE_URL="http://127.0.0.1:8787"
fi

KEY="${TYPESAFE_API_KEY:-ts_invalid_key_for_demo}"

echo "POST ${BASE_URL}/v1/systemone"
curl -sS -i -X POST "${BASE_URL}/v1/systemone" \
  -H "Authorization: Bearer ${KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "jev-latest",
    "state": "My running shoes arrived in the wrong size. Can I swap them for a size 10?",
    "questions": {
      "department": {
        "type": "choice",
        "instructions": "Which team should handle this?",
        "criteria": {
          "returns": "Exchanges, wrong or damaged items",
          "shipping": "Delivery status, delays, lost packages",
          "billing": "Charges, invoices, payment problems"
        }
      },
      "is_human_escalation": {
        "type": "noul",
        "instructions": "Does this message require a human to take over?"
      }
    }
  }'

echo
echo "GET ${BASE_URL}/v1/models"
curl -sS -i -X GET "${BASE_URL}/v1/models" -H "Authorization: Bearer ${KEY}"
