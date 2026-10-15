#!/usr/bin/env bash
# 用 REST API 管理凭据（新增 / 列表 / 删除），凭据值只出现在命令行参数里，不入库不落盘。
set -euo pipefail

JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_TOKEN="${JENKINS_TOKEN:?请先导出 JENKINS_TOKEN}"
AUTH=(-u "$JENKINS_USER:$JENKINS_TOKEN")
STORE="$JENKINS_URL/credentials/store/system/domain/_"

echo "== 新增 secret text 凭据 =="
curl -fsS -X POST "${AUTH[@]}" --data-urlencode 'json={
  "": "0",
  "credentials": {
    "scope": "GLOBAL",
    "id": "demo-api-token",
    "secret": "s3cr3t-token-for-demo-9f1c",
    "description": "演示用 API Token（截图里的值已脱敏）",
    "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
  }
}' "$STORE/createCredentials" -o /dev/null -w 'create secret text HTTP %{http_code}\n'

echo "== 新增用户名密码凭据 =="
curl -fsS -X POST "${AUTH[@]}" --data-urlencode 'json={
  "": "0",
  "credentials": {
    "scope": "GLOBAL",
    "id": "demo-registry",
    "username": "deployer",
    "password": "r3gistry-pass-demo",
    "description": "演示用镜像仓库账号",
    "$class": "com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl"
  }
}' "$STORE/createCredentials" -o /dev/null -w 'create username/password HTTP %{http_code}\n'

echo "== 列出凭据（只看 id 与描述，不含机密） =="
curl -fsS "${AUTH[@]}" "$STORE/api/json?tree=credentials[id,description,typeName]" | python3 -m json.tool

echo "== 删除凭据 =="
# curl -fsS -X POST "${AUTH[@]}" "$STORE/credential/demo-api-token/delete" -w 'delete HTTP %{http_code}\n'
