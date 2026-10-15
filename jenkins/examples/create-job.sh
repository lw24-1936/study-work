#!/usr/bin/env bash
# 用 REST API 建流水线任务、触发、轮询结果、取控制台输出。
# 全部用用户 API Token 认证（推荐），不要用登录密码。
set -euo pipefail

JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_TOKEN="${JENKINS_TOKEN:?请先导出 JENKINS_TOKEN}"
JOB_NAME="${JOB_NAME:-demo-pipeline}"
GIT_URL="${GIT_URL:-file:///demo/repo.git}"
BRANCH="${BRANCH:-main}"

AUTH=(-u "$JENKINS_USER:$JENKINS_TOKEN")

echo "== 1. 健康检查与版本 =="
curl -fsS "${AUTH[@]}" "$JENKINS_URL/api/json?tree=mode,nodeName,numExecutors,quietingDown" ; echo
curl -fsS "${AUTH[@]}" "$JENKINS_URL/login" -o /dev/null -w 'login HTTP %{http_code}\n'

echo "== 2. 创建（或覆盖）流水线任务 =="
# 任务配置就是 Jenkins 自己的 XML；这里用最小可用配置：Pipeline script from SCM
curl -fsS -X POST "${AUTH[@]}" \
     -H 'Content-Type: application/xml' \
     --data-binary @- \
     "$JENKINS_URL/createItem?name=$JOB_NAME" <<XML
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>由 create-job.sh 通过 REST API 创建</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.ChoiceParameterDefinition>
          <name>ENVIRONMENT</name>
          <choices class="java.util.Arrays\$ArrayList">
            <a class="java.lang.String" value="dev"/>
            <a class="java.lang.String" value="staging"/>
            <a class="java.lang.String" value="prod"/>
          </choices>
          <description>部署环境</description>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH</name>
          <defaultValue>$BRANCH</defaultValue>
          <description>要构建的分支</description>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>$GIT_URL</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/$BRANCH</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
XML
echo "任务已创建：$JOB_NAME"

echo "== 3. 触发带参数构建 =="
curl -fsS -X POST "${AUTH[@]}" \
     --data-urlencode "ENVIRONMENT=dev" \
     --data-urlencode "BRANCH=$BRANCH" \
     "$JENKINS_URL/job/$JOB_NAME/buildWithParameters" -o /dev/null -w 'trigger HTTP %{http_code}\n'

echo "== 4. 轮询构建结果 =="
for i in $(seq 1 60); do
  sleep 5
  RESULT=$(curl -fsS "${AUTH[@]}" "$JENKINS_URL/job/$JOB_NAME/lastBuild/api/json?tree=number,building,result" || echo '{}')
  echo "  第 ${i} 次轮询：$RESULT"
  if echo "$RESULT" | grep -q '"building":false'; then break; fi
done

echo "== 5. 取控制台输出（尾部 30 行） =="
curl -fsS "${AUTH[@]}" "$JENKINS_URL/job/$JOB_NAME/lastBuild/consoleText" | tail -n 30

echo "== 6. 取构建元数据与产物列表 =="
curl -fsS "${AUTH[@]}" "$JENKINS_URL/job/$JOB_NAME/lastBuild/api/json?tree=number,result,duration,url,artifacts[fileName,relativePath]"; echo
