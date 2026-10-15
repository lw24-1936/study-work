#!/usr/bin/env bash
# 用 Jenkins CLI 做日常运维：列出任务、触发构建、看控制台、装插件、重启。
# 依赖：java（本机 21）、curl。CLI jar 从控制器下载，随版本变化不要固定旧版。
set -euo pipefail

JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_TOKEN="${JENKINS_TOKEN:?请先导出 JENKINS_TOKEN（用户 API Token，不是登录密码）}"
CLI_JAR="${CLI_JAR:-/tmp/jenkins-cli.jar}"

# 下载 CLI 客户端（与控制器同版本）
if [ ! -f "$CLI_JAR" ]; then
  curl -fsSL "$JENKINS_URL/jnlpJars/jenkins-cli.jar" -o "$CLI_JAR"
fi

cli() {
  java -jar "$CLI_JAR" -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_TOKEN" "$@"
}

echo "== 控制器版本与环境 =="
cli version
cli who-am-i

echo "== 任务清单 =="
cli list-jobs

echo "== 触发构建并跟踪日志（-f 跟随控制台输出） =="
cli build demo-pipeline -p BRANCH=main -f

echo "== 查看最近一次构建结果 =="
cli console demo-pipeline | tail -n 20

echo "== 节点与队列 =="
cli list-computers
cli list-nodes || true

echo "== 插件管理 =="
cli list-plugins | head -n 20
# cli install-plugin git -deploy     # 安装并立即装载
# cli safe-restart                    # 安全重启（等构建结束）

echo "== 系统信息与配置重载 =="
cli reload-configuration
