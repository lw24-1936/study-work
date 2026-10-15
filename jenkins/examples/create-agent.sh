#!/usr/bin/env bash
# 增加一个「入站 agent」并把它跑起来：
#  1) 用 CLI 在控制器上创建节点（launch method = inbound，即 agent 主动连控制器）
#  2) 从节点页面拿到 agent 密钥
#  3) 用 jenkins/inbound-agent 容器把 agent 跑起来，让它注册为在线
# 用途：把构建负载从控制器挪走（控制器只做调度），并隔离各语言工具链。
set -euo pipefail

JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_TOKEN="${JENKINS_TOKEN:?请先导出 JENKINS_TOKEN}"
AGENT_NAME="${AGENT_NAME:-linux-agent-1}"
AGENT_LABEL="${AGENT_LABEL:-linux docker-agent}"
AGENT_WORKDIR="${AGENT_WORKDIR:-/home/jenkins/agent}"
CLI_JAR="${CLI_JAR:-/tmp/jenkins-cli.jar}"
INSIDE_URL="${INSIDE_URL:-http://jenkins-demo:8080}"   # agent 容器访问控制器的地址

AUTH=(-u "$JENKINS_USER:$JENKINS_TOKEN")
[ -f "$CLI_JAR" ] || curl -fsSL "$JENKINS_URL/jnlpJars/jenkins-cli.jar" -o "$CLI_JAR"
cli() { java -jar "$CLI_JAR" -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_TOKEN" "$@"; }

echo "== 1. 创建节点 =="
cat > /tmp/agent.xml <<XML
<?xml version='1.1' encoding='UTF-8'?>
<slave>
  <name>$AGENT_NAME</name>
  <description>Linux 入站 agent（容器方式运行）</description>
  <remoteFS>$AGENT_WORKDIR</remoteFS>
  <numExecutors>2</numExecutors>
  <mode>NORMAL</mode>
  <retentionStrategy class="hudson.slaves.RetentionStrategy\$Always"/>
  <launcher class="hudson.slaves.JNLPLauncher">
    <workDirSettings>
      <disabled>false</disabled>
      <internalDir>remoting</internalDir>
      <failIfWorkDirIsMissing>false</failIfWorkDirIsMissing>
    </workDirSettings>
    <tunnel>false</tunnel>
  </launcher>
  <label>$AGENT_LABEL</label>
  <nodeProperties/>
</slave>
XML
cli create-node "$AGENT_NAME" < /tmp/agent.xml
cli list-computers

echo "== 2. 取 agent 密钥（agent 页面上的 secret） =="
SECRET=$(curl -fsS "${AUTH[@]}" "$JENKINS_URL/computer/$AGENT_NAME/slave-agent.jnlp" \
  | python3 -c 'import sys,xml.etree.ElementTree as ET; print(ET.fromstring(sys.stdin.read()).find("application-desc/argument[2]").text)')
echo "secret 长度：${#SECRET}"

echo "== 3. 用容器跑 agent =="
docker run -d --name "$AGENT_NAME" --restart unless-stopped \
  --network "$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' jenkins-demo)" \
  -e JENKINS_URL="$INSIDE_URL" \
  -e JENKINS_AGENT_NAME="$AGENT_NAME" \
  -e JENKINS_SECRET="$SECRET" \
  -e JENKINS_AGENT_WORKDIR="$AGENT_WORKDIR" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/inbound-agent:latest-jdk21

echo "== 4. 等 agent 上线 =="
for i in $(seq 1 30); do
  sleep 3
  STATE=$(curl -fsS "${AUTH[@]}" "$JENKINS_URL/computer/$AGENT_NAME/api/json?tree=offline" 2>/dev/null || echo '{}')
  echo "  第 ${i} 次：$STATE"
  if echo "$STATE" | grep -q '"offline":false'; then echo "agent 已在线"; break; fi
done
docker logs --tail 15 "$AGENT_NAME"
