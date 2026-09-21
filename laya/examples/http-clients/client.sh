#!/usr/bin/env bash
# curl 版外部调用示例。用法：
#     export LAYA_API_KEY=...            # 服务端开了鉴权才需要
#     bash client.sh http://192.168.1.167:8077 "请把 3 月的账单退款"
set -euo pipefail

BASE="${1:-http://127.0.0.1:8077}"
TEXT="${2:-We were charged twice for March, please refund today or we cancel.}"

echo "--- GET /health ---"
curl -s --max-time 10 "$BASE/health"
echo

echo "--- POST /decide（无 key，若服务端开了鉴权会得到 401） ---"
curl -s --max-time 60 -o /tmp/laya_401.json -w 'HTTP %{http_code}  %{time_total}s\n' \
  -X POST "$BASE/decide" -H 'Content-Type: application/json' \
  -d "$(printf '{"state":{"message":%s}}' "$(printf '%s' "$TEXT" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')")"
cat /tmp/laya_401.json
echo

echo "--- POST /decide（带 key） ---"
curl -s --max-time 60 -w '\nHTTP %{http_code}  %{time_total}s\n' \
  -X POST "$BASE/decide" \
  -H 'Content-Type: application/json' \
  ${LAYA_API_KEY:+-H "X-API-Key: $LAYA_API_KEY"} \
  -d "$(printf '{"state":{"message":%s}}' "$(printf '%s' "$TEXT" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')")"
