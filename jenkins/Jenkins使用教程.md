---
title: Jenkins 使用教程
created: 2026-10-15
updated: 2026-10-15
type: concept
tags: [jenkins, cicd, devops, pipeline, docker, spring-boot, vue]
---

# Jenkins 使用教程

整理日期：2026-10-15

> 状态：已完成

## 目录

- [这是什么](#这是什么)
- [核心概念](#核心概念)
- [安装部署](#安装部署)
- [界面与基础使用](#界面与基础使用)
- [凭据管理](#凭据管理)
- [流水线（Jenkinsfile）](#流水线jenkinsfile)
- [分布式构建与 Agent](#分布式构建与-agent)
- [自动化：REST API、CLI、Job DSL](#自动化rest-apiclijob-dsl)
- [实战一：通用 Python 项目流水线](#实战一通用-python-项目流水线)
- [实战二：Spring Boot + Vue 前后端分离项目 CI/CD](#实战二spring-boot--vue-前后端分离项目-cicd)
- [安全加固](#安全加固)
- [备份、恢复与升级](#备份恢复与升级)
- [监控、容量与性能](#监控容量与性能)
- [常见问题与排错](#常见问题与排错)
- [最佳实践](#最佳实践)
- [相关文档](#相关文档)

## 这是什么

Jenkins 是一个用 Java 写的开源自动化服务器，解决的核心问题是「把重复的构建、测试、部署动作交给机器按固定流程执行」。它本身只做三件事：调度任务、提供 UI 与 API、把结果记录下来；真正干活的是插件和被调度的执行环境。

2026 年新写 CI/CD 时经常有人问「为什么不用 GitHub Actions / GitLab CI / Tekton」。判断标准很简单：

- 代码在公司内网 GitLab、Gitee、SVN，或者需要构建内网制品、连内网数据库、部署到没有公网的机器：Jenkins 装上就能用，网络拓扑无关。
- 构建环境很脏（要装一堆本机工具、要连老 JDK、要跑 Windows 批处理）：Jenkins 的 agent 模型允许你为每个项目单独准备一台机器或一个容器。
- 已经有 Jenkins 在跑（绝大多数中大型公司都是）：继续用，把流水线代码化（Jenkinsfile + JCasC）比迁移划算。
- 纯开源项目、只跑测试、不需要部署到内网：GitHub Actions 更省事，不必为了「统一」硬上 Jenkins。

本机实测环境：

```text
Jenkins 版本：2.580.1（LTS，docker 镜像 jenkins/jenkins:lts-jdk21）
内置 JDK：Temurin 21.0.12.1
容器启动耗时：从容器创建到 "Jenkins is fully up and running" 约 6 秒（无插件的最小镜像）
控制器：Ubuntu 24.04 / Docker 环境，4 核 19GB 内存
```

版本这件事要顺手说清楚：Jenkins 分两条线，LTS（每 12 周从周更版里挑一个基线，再做 4 周一次的 bug/安全修复）和周更版。生产用 LTS，插件作者需要新 API 才用周更版。查当前 LTS 的权威来源是官方 changelog 页和 docker 镜像实际内容（后者更可信，见下文实测）。

```text
# 拉最新 LTS 镜像（实测 1.2GB，约 100 秒）
$ docker pull jenkins/jenkins:lts-jdk21
Digest: sha256:a660310e39ade10631f774bacd5219de767dfd08947ea5c32a739b5e5bb382c1
Status: Downloaded newer image for jenkins/jenkins:lts-jdk21

# 镜像里到底是哪个版本，直接问 war 包（比查网页可靠）
$ docker exec jenkins-demo java -jar /usr/share/jenkins/jenkins.war --version
2.580.1
```

```text
基础能力速览
- 调度：定时、SCM 轮询、Webhook、手动、上游触发、远程 API 触发
- 执行：控制器内置节点 + 任意台 agent（SSH / 入站 JNLP / 容器 / Kubernetes 动态）
- 描述：Shell、Windows 批处理、Groovy（流水线）、任意语言脚本
- 记录：控制台日志、测试报告、代码覆盖率、制品归档、构建趋势
- 扩展：1800+ 插件（Git、JUnit、Docker、Pipeline、凭据、通知、云平台）
- 对外：REST API（XML/JSON）、SSH CLI、jenkins-cli.jar、Webhook 接收
```

## 核心概念

概念不清是踩坑的根源，尤其是「控制器/节点/执行器」三件套。

### 控制器、节点、执行器

- 控制器（Controller，旧称 master）：Jenkins 服务本身，负责调度、配置、鉴权、展示、记录。它也可以是执行节点，但官方明确不推荐——构建跑在控制器上会让 UI 卡、安全边界消失。
- 节点（Node）：执行构建的「机器」，可以是控制器内置节点，也可以是通过 SSH / 入站方式接入的独立机器或容器。
- Agent：节点上那个连接控制器的 Java 进程（`agent.jar`，约 170KB），负责真正执行命令。
- 执行器（Executor）：节点上的执行槽位，本质是线程。执行器数量决定该节点能同时跑几个构建。

```text
一个新手常犯的错：给所有任务都写 agent any，然后抱怨构建慢
根因：agent any 会把任务派给任何空闲执行器，包括控制器内置节点
正确做法：
  1. 控制器内置节点执行器设为 0（Manage Jenkins > Nodes 里配）
  2. 任务用 label 指定真正的构建节点，如 agent { label 'linux-maven' }
  3. 需要特定工具链（Maven、Node、Python）时用 docker agent 现拉镜像，节点无需预装
```

### 任务类型

| 类型 | 适用场景 | 是否推荐 |
| --- | --- | --- |
| 自由风格（Freestyle） | 单人维护的小任务、临时跑个脚本 | 新项目不推荐，配置进不了代码评审 |
| 流水线（Pipeline） | 有构建/测试/部署多阶段的工程 | 推荐，Jenkinsfile 入库 |
| 多分支流水线（Multibranch） | 每个分支/PR 自动建任务 | 推荐，配合 Jenkinsfile 使用 |
| 组织文件夹（Organization Folder） | 整个 Git 组织下所有仓库自动纳管 | 团队规模大时用 |
| 文件夹（Folder） | 按团队/产品分组任务 | 推荐，权限与视图都按文件夹收敛 |

### 一次构建的生命周期

```text
触发 → 入队 → 分配到节点与执行器 → 拉工作区 → 执行 stages → 收集结果
                                                  ↓
              归档制品 / 测试报告 / 覆盖率 / 通知 → 记录构建历史 → 清理工作区
```

- 工作区（Workspace）：`$JENKINS_HOME/workspace/<任务名>`，同一任务不会并发用同一工作区（`disableConcurrentBuilds()` 或加上 `-Dorg.jenkinsci.plugins.durabletask.BourneShellScript...` 之外的策略控制）。多分支任务会把分支名编进工作区路径。
- 制品（Artifact）：构建产物，`archiveArtifacts` 归档后可以在构建页下载，也能被其他任务通过 `copyArtifacts` 取用。
- 指纹（Fingerprint）：记录「哪个构建产出了这个文件、哪个构建用了它」，排查「这个 jar 是谁编的」时非常有用。

### 插件体系

Jenkins 的一切功能都来自插件，插件有自己的依赖树和兼容性要求。三条经验：

1. 只装用得上的。插件越多启动越慢、升级越容易出冲突。
2. 用 `plugins.txt` 或自定义镜像固定插件版本，别在 UI 上随手点升级；升级前看插件的依赖链（Update Center 页面会显示）。
3. 插件来源是 Update Center（`updates.jenkins.io`）。国内网络直接连会非常慢，必须换镜像源或预下载，见[国内网络](#国内网络插件源与镜像)。

## 安装部署

### 容器方式（推荐）

```bash
# 1. 建数据卷（所有配置、任务、构建记录都在里面，容器删了也不丢）
docker volume create jenkins_demo_home

# 2. 起容器
docker run -d --name jenkins-demo \
  -p 8080:8080 -p 50000:50000 \
  -e JAVA_OPTS="-Duser.timezone=Asia/Shanghai" \
  -e TZ=Asia/Shanghai \
  -v jenkins_demo_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker:ro \
  jenkins/jenkins:lts-jdk21
```

几个参数的作用：

- `8080`：Web UI 与 REST API；`50000`：控制器与入站 agent 的固定通信端口（不接 agent 可以不暴露）。
- `-v jenkins_demo_home:/var/jenkins_home`：数据卷。**升级镜像时只要这个卷不变，配置和历史都在**。
- `-v /var/run/docker.sock`：挂载宿主 Docker 套接字，流水线里才能执行 `docker build` / `docker run`（也就是「用 Jenkins 部署容器化应用」的前提）。安全影响见[安全加固](#安全加固)，生产建议改成远程 Docker 或 Kubernetes agent。
- `-v /usr/bin/docker:/usr/bin/docker:ro`：把宿主的 docker 客户端二进制挂进容器。Jenkins 官方镜像里没有 docker CLI，这是最省事的补齐方式（也可以自己构建镜像时 `apt-get install docker-ce-cli`）。

启动日志确认（真实输出，截取自 `docker logs jenkins-demo`）：

```text
Running from: /usr/share/jenkins/jenkins.war
webroot: /var/jenkins_home/war
2026-10-15 14:58:58.142+0000 [id=1] INFO  winstone.Logger#logInternal: Beginning extraction from war file
2026-10-15 14:58:59.268+0000 [id=1] INFO  org.eclipse.jetty.server.Server#doStart: jetty-12.1.13; ... jvm 21.0.12.1+1-LTS
2026-10-15 14:59:00.060+0000 [id=1] INFO  o.e.j.s.handler.ContextHandler#doStart: Started ...{Jenkins v2.580.1,/,...}
2026-10-15 14:59:00.068+0000 [id=1] INFO  o.e.j.server.AbstractConnector#doStart: Started ...{HTTP/1.1, (http/1.1)}{0.0.0.0:8080}
2026-10-15 14:59:03.908+0000 [id=39] INFO  hudson.lifecycle.Lifecycle#onReady: Jenkins is fully up and running
```

从解包 war 到对外可用 5 秒左右；插件多的时候（几十上百个）这个时间会变成 30 秒到几分钟，健康检查的 `start_period` 要跟着放宽。

### 首次启动向导

首次启动（`JENKINS_HOME` 里没有配置）会进入解锁向导。

第一步，从日志或文件里取初始管理员密码：

```bash
$ docker exec jenkins-demo cat /var/jenkins_home/secrets/initialAdminPassword
898c42df6ec04fad8ad5b90c7ebf42a5
```

![解锁 Jenkins](images/01-解锁-Jenkins.png)

第二步，选择插件安装方式。「安装推荐的插件」会装社区推荐的一组（Git、Pipeline、凭据、构建超时等），「选择插件来安装」可以自己挑，实测列表有 52 个可用插件、其中 20 个默认被勾选：

![自定义 Jenkins](images/02-自定义-Jenkins.png)

![选择插件](images/03-选择插件.png)

第三步是安装进度页，装完后进入「创建第一个管理员用户」，之后 Jenkins 才算就绪：

![安装插件进度](images/04-安装插件进度.png)

```text
向导里的三个决定，值得认真选
1. 插件不要点「推荐」了事：推荐集合里含 GitHub、LDAP 这类国内用不到的插件，
   装了只是拖慢启动；按需要勾。
2. 第一个管理员用户名别叫 admin 之外的随便名字，也别用默认密码；
   建完用户后立即去「安全 > 用户」里删掉旧的管理员凭据。
3. 安装向导完成后，进入 Manage Jenkins > System，把「Jenkins URL」改成真实访问地址，
   否则邮件、Webhook、agent 回连里生成的链接全是 localhost。
```

自动化部署时可以跳过向导（本教程后续的实测都用这种方式，省掉 UI 操作）：

```bash
docker run -d --name jenkins-demo \
  -e JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Duser.timezone=Asia/Shanghai" \
  ...
```

跳过后 Jenkins 是**无安全配置**状态（任何能访问到端口的人都是管理员），只能在实验环境这么干，生产必须配合下面的 JCasC 或 init 脚本把用户与授权一起配好。

### 用配置即代码（JCasC）初始化

`init.groovy.d` 是传统做法：启动时执行 Groovy 脚本，幂等地设置安全域、授权策略、节点端口。

```groovy
// $JENKINS_HOME/init.groovy.d/01-security.groovy（完整文件见 examples/init.groovy.d/）
import jenkins.model.Jenkins
import hudson.security.*

def instance = Jenkins.get()
if (instance.getSecurityRealm() instanceof hudson.security.SecurityRealm.None) {
    def realm = new HudsonPrivateSecurityRealm(false)
    realm.createAccount('admin', System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'admin-demo-pass')
    instance.setSecurityRealm(realm)

    def strategy = new GlobalMatrixAuthorizationStrategy()
    strategy.add(Jenkins.ADMINISTER, 'admin')
    strategy.add(Jenkins.READ, 'authenticated')
    instance.setAuthorizationStrategy(strategy)
}
instance.setSlaveAgentPort(50000)
instance.save()
```

新项目更推荐 JCasC（Configuration as Code 插件）：整个 `jenkins.yaml` 描述系统配置，UI 上的改动重启会被覆盖，配置能进 Git 走评审。

```yaml
# jenkins.yaml 片段（完整见 examples/casc/jenkins.yaml）
jenkins:
  systemMessage: "配置由 JCasC 管理，UI 上的改动重启会被覆盖"
  numExecutors: 2
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: "admin"
          password: "${JENKINS_ADMIN_PASSWORD}"   # 从环境变量读，别写明文
  authorizationStrategy:
    globalMatrix:
      permissions:
        - "Overall/Administer:admin"
        - "Overall/Read:authenticated"
        - "Job/Build:authenticated"
```

```bash
# 挂载配置并让 Jenkins 启动时应用
docker run -d --name jenkins \
  -e CASC_JENKINS_CONFIG=/var/jenkins_home/casc/jenkins.yaml \
  -v jenkins_home:/var/jenkins_home \
  -v $PWD/examples/casc:/var/jenkins_home/casc:ro \
  jenkins/jenkins:lts-jdk21
```

### Docker Compose

日常起停用 compose 更省事（完整文件见 `examples/docker-compose.yml`）：

```yaml
services:
  jenkins:
    image: jenkins/jenkins:lts-jdk21
    container_name: jenkins
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      TZ: "Asia/Shanghai"
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8080/login >/dev/null || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

volumes:
  jenkins_home:
```

```bash
docker compose up -d
docker compose logs -f jenkins
docker compose down          # 停止，数据卷保留
docker compose down -v       # 连数据卷一起删（历史全丢，慎用）
```

### 裸机部署（war + systemd）

没有容器环境时用 war 包 + systemd。系统要求：JDK 21（本机实测 `openjdk version "21.0.12.1" 2026-08-18`）。

```bash
# 1. 装 JDK 21 与 Jenkins 仓库
sudo apt-get update && sudo apt-get install -y fontconfig openjdk-21-jre
sudo wget -O /etc/apt/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/etc/apt/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" \
  | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update && sudo apt-get install -y jenkins

# 2. 或者直接用 war 包（版本自己控制，升级就是换文件重启）
sudo mkdir -p /opt/jenkins && sudo chown jenkins:jenkins /opt/jenkins
sudo curl -fsSL -o /opt/jenkins/jenkins.war https://mirrors.tuna.tsinghua.edu.cn/jenkins/war-stable/2.580.1/jenkins.war
```

```ini
# /etc/systemd/system/jenkins.service
[Unit]
Description=Jenkins Automation Server
After=network.target

[Service]
Type=simple
User=jenkins
Group=jenkins
Environment="JENKINS_HOME=/var/lib/jenkins"
# 堆内存按机器来；小机器 1-2G 够，跑流水线多要 4G 以上
Environment="JAVA_OPTS=-Xms1g -Xmx2g -XX:+UseG1GC -Duser.timezone=Asia/Shanghai -Dhudson.model.DownloadService.noSignatureCheck=false"
ExecStart=/usr/bin/java -jar /opt/jenkins/jenkins.war --httpPort=8080 --prefix=/jenkins
Restart=on-failure
RestartSec=10
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now jenkins
systemctl status jenkins --no-pager | head -5
```

### 国内网络：插件源与镜像

这是国内部署 Jenkins 最大的坑，本机把两条路都实测了一遍。

**结论：官方 Update Center 是能用且不慢的，慢的是国内镜像的「更新中心 JSON」路径。** 看实测数据：

```text
# 1) 官方更新中心 JSON：会 301 跳转到 CDN，必须跟重定向，实测 555 KB/s
$ curl -sL -o /dev/null -w '%{http_code} %{size_download}B %{speed_download}B/s\n' \
       --max-time 30 https://updates.jenkins.io/update-center.json
200 3476049B 554956B/s

# 2) 清华镜像的插件下载路径很快（1.7 MB/s），但它不再镜像更新中心 JSON
$ curl -s -o /dev/null -w '%{http_code}\n' \
       https://mirrors.tuna.tsinghua.edu.cn/jenkins/updates/update-center.json
404

# 3) 华为云镜像插件下载最快（2.4 MB/s）
$ curl -s -o /dev/null -w '%{http_code} %{speed_download}B/s\n' \
       https://mirrors.huaweicloud.com/jenkins/plugins/git/latest/git.hpi
200 2436757B/s
```

于是有两种可行配置：

```bash
# 方案 A（推荐，简单）：用官方更新中心，插件下载走 CDN，实测够快
docker exec -u 0 jenkins jenkins-plugin-cli \
  --plugins git workflow-aggregator junit \
  --plugin-download-directory /usr/share/jenkins/ref/plugins

# 方案 B：更新中心 JSON 用镜像（若你的出口对官方站点确实不通），
#         插件下载地址显式指向镜像（参数名是 --jenkins-update-center-download-url）
jenkins-plugin-cli \
  --jenkins-update-center https://mirrors.tuna.tsinghua.edu.cn/jenkins/updates/update-center.json \
  --jenkins-update-center-download-url https://mirrors.tuna.tsinghua.edu.cn/jenkins/plugins \
  --plugins git junit timestamper \
  --plugin-download-directory /var/jenkins_home/plugins
```

一个必须知道的坑（本机实测）：**容器网络模式会影响镜像站是否返回 403**。

```text
# 同一个 URL，两种网络模式实测结果
$ docker run --rm --network host   --entrypoint curl jenkins:lts-jdk21 -s -o /dev/null \
    -w 'network=host: %{http_code} %{speed_download} B/s\n' \
    https://mirrors.tuna.tsinghua.edu.cn/jenkins/plugins/git/latest/git.hpi
network=host: 200 1749201 B/s

$ docker run --rm --entrypoint curl jenkins:lts-jdk21 -s -o /dev/null \
    -w 'network=bridge: %{http_code} %{speed_download} B/s\n' \
    https://mirrors.tuna.tsinghua.edu.cn/jenkins/plugins/git/latest/git.hpi
network=bridge: 403 68426 B/s        # 镜像站对 bridge 出口返回「抱歉，您目前无法访问此页面」
```

所以「装插件」这一步如果卡住，先按这个顺序排查：换 `--network host` 跑一次性容器 → 换镜像站（华为云 / 南大 / USTC）→ 检查是不是被同一出口的并发下载触发了限流。

### 自定义镜像：把插件烧进镜像

生产推荐做法。好处是容器首次启动就有确定版本的插件集合，扩容/重建环境不需要再下载。

```dockerfile
# examples/Dockerfile
FROM jenkins/jenkins:2.580.1-lts-jdk21

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

USER jenkins
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
# 插件下载路径固定：下完即删临时目录，镜像里只留 .jpi
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt --cleanup-downloads
```

```bash
docker build -t my-jenkins:2.580.1 -f examples/Dockerfile examples/
docker run -d --name jenkins -p 8080:8080 -v jenkins_home:/var/jenkins_home my-jenkins:2.580.1
```

`examples/plugins.txt` 是本教程用到的最小集合：

```text
git:latest
workflow-aggregator:latest          # 流水线（含 workflow-job、workflow-cps 等）
pipeline-stage-view:latest          # 阶段视图
junit:latest                        # 测试报告
ws-cleanup:latest                   # 构建后清工作区
build-timeout:latest                # 构建超时
timestamper:latest                  # 控制台时间戳
credentials-binding:latest          # withCredentials 注入环境变量
ssh-credentials:latest
matrix-auth:latest                  # 矩阵授权
ansicolor:latest                    # 控制台颜色
coverage:latest                     # 覆盖率报告
pipeline-utility-steps:latest       # readJSON/writeJSON 等
job-dsl:latest                      # 用代码建任务
configuration-as-code:latest        # JCasC
docker-workflow:latest              # docker agent / inside
localization-zh-cn:latest           # 中文界面
```

```text
插件安装命令的三个参数很容易用错（本机实测报错原文）：
$ jenkins-plugin-cli -i https://... --plugins git
"-i" is not a valid option
Exception in thread "main" java.io.IOException: Failed to read command-line arguments
正确的参数名是：
  --jenkins-update-center URL                 指定更新中心 JSON
  --jenkins-update-center-download-url URL    指定插件包下载根地址
  --plugin-download-directory DIR             插件落地目录
  --plugin-file FILE                          从文件读插件清单（每行 name:version）
  --latest false                              依赖按更新中心元数据解析，不去追最新
```

一次性把插件装进已有实例的数据卷（不必重构建镜像）：

```bash
docker run --rm --network host -v jenkins_home:/var/jenkins_home \
  --entrypoint jenkins-plugin-cli jenkins/jenkins:lts-jdk21 \
  --plugins git workflow-aggregator junit timestamper \
  --plugin-download-directory /var/jenkins_home/plugins
docker restart jenkins-demo    # 让 Jenkins 重新扫描并加载插件
```

### 反向代理与 HTTPS

Jenkins 前面挂 nginx 时有两个必配项，否则页面会一直提示「反向代理设置有误」，agent 回连地址也会错。

```nginx
# nginx 片段：Jenkins 挂在 /jenkins 前缀下
location /jenkins/ {
    proxy_pass http://127.0.0.1:8080/jenkins/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    # WebSocket（日志实时刷新、CLI 用 WebSocket 模式都需要）
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 90s;
    client_max_body_size 100m;
}
```

```bash
# Jenkins 侧：URL 与前缀要和 nginx 对上
# 容器：加 JENKINS_OPTS="--prefix=/jenkins -Dhudson.TcpSlaveAgentListener.hostName=ci.example.com"
docker run -d --name jenkins \
  -e JENKINS_OPTS="--prefix=/jenkins" \
  -e JAVA_OPTS="-Djenkins.model.Jenkins.location=https://ci.example.com/jenkins/" \
  ...
```

HTTPS 建议在 nginx 终结（证书一处管理），同时把 Jenkins 的 8080 只监听 127.0.0.1，别在公网直接暴露 Jenkins 端口。

### 升级与回滚

```bash
# 1. 先备份（见备份一节），再升级
docker pull jenkins/jenkins:lts-jdk21
docker compose down
# 2. compose 文件里的 image tag 换成新版本后拉起
docker compose up -d
docker logs -f jenkins | grep -E 'fully up and running|Exception'

# 回滚：把 tag 换回旧版本，用同一数据卷重启
# 注意：Jenkins 会原地升级 JENKINS_HOME 里的配置格式，低版本读高版本数据可能失败，
#      所以跨大版本升级前必须先备份数据卷，且回滚要用「备份 + 旧镜像」一起回。
```

```text
升级纪律（踩过的坑总结）
1. 先读 changelog 的 "Notable changes"，里面会写需要同时升级的插件与最低 Java 版本。
2. 插件不要追新：Jenkins 升完后，只升级有安全公告的插件，其他保持不动。
3. 升级窗口选在没有构建的时候，或先在灰度实例上用生产数据卷的拷贝跑一遍。
4. 升级后立刻验证三件事：能登录、能触发一个构建、agent 是否全部在线。
```

## 界面与基础使用

### 主要页面

登录后左侧是主导航，日常用得最多的是这几个：

| 菜单 | 用途 |
| --- | --- |
| 新建任务（New Item） | 建流水线/自由风格/多分支/文件夹 |
| 构建历史（Build History） | 当前任务或全站最近构建 |
| 凭据（Credentials） | 管理密码、Token、密钥、证书 |
| 节点管理（Nodes） | 查看控制器与 agent 状态、执行器占用 |
| 系统管理（Manage Jenkins） | 系统配置、插件、全局工具、安全、脚本控制台 |
| 我的视图（My Views） | 按团队/环境自定义看板 |

判断 Jenkins 是否健康，看一眼「系统管理 > 系统信息」足矣：JDK 版本、内存、时区、插件数量、`hudson.model.UpdateCenter` 状态都在这里。

### 新建一个流水线任务

1. 新建任务 → 输入名字（建议 `产品-模块-环境`，如 `order-api-prod`）→ 选「流水线（Pipeline）」。
2. 在「流水线」页签里选定义方式：
   - Pipeline script：脚本直接写在这里，适合临时验证。
   - Pipeline script from SCM：脚本从 Git 拉，选这一项并把「脚本路径」填 `Jenkinsfile`。**生产就用这个**，改流程走代码评审。
3. 保存后点「立即构建」。

```text
命名与组织约定（团队协作时最能省事的几件事）
- 用文件夹按团队/产品分组：order/order-api、order/order-web
- 任务名带环境后缀：-dev、-staging、-prod，一眼能看出部署目标
- 同一个应用的构建与部署尽量拆成两个任务（构建产物 → 部署消费产物），
  这样回滚可以不重新编译
- 视图（Views）按用途建：只放主干构建、只放生产部署、只放失败任务
```

### 触发器：构建从哪来

| 触发方式 | 配置位置 | 适用场景 |
| --- | --- | --- |
| 手动 | 页面按钮 / API | 发版、临时构建 |
| 定时（cron） | 任务 > 构建触发器 > 定时构建 | 夜间全量回归 |
| SCM 轮询 | 任务 > 构建触发器 > 轮询 SCM | 内网 Git 无法回调 Jenkins 时的兜底 |
| Webhook | 任务 > 构建触发器 + Git 侧配置 | GitLab/GitHub/Gitee 推送即构建，推荐 |
| 上游任务 | 任务 > 构建触发器 > 其他工程构建后触发 | 构建 → 部署链路 |
| 远程 API | 任意脚本 `curl .../build?token=xxx` | 与发布系统、运维平台对接 |

cron 语法是五段（分 时 日 月 周），和 Linux crontab 不同：Jenkins 支持 `H`（散列）来避免整点并发。

```groovy
triggers {
    // 每个工作日 02:00-03:00 之间挑一个时间点跑（H 让 Jenkins 自己散列）
    cron('H 2 * * 1-5')
    // 每 5 分钟检查一次代码变更
    pollSCM('H/5 * * * *')
    // 上游任务成功后触发
    upstream(upstreamProjects: 'order-api-build', threshold: hudson.model.Result.SUCCESS)
}
```

```text
cron 的两个常见误解
- 以为 H 是「小时」：H 是散列符号，H/5 表示每 5 分钟一次，
  H 2 * * * 表示 2 点这一小时内随机取一分钟（同一任务的取值固定）。
- 以为时区跟随浏览器：cron 用的是控制器 JVM 的时区，
  容器里务必设 TZ=Asia/Shanghai，否则「每天早上 2 点」= 北京时间上午 10 点。
```

### 参数化构建

参数可以从 UI 选、从 API 传、也可以被流水线读（`params.XXX`）。

```groovy
parameters {
    string(name: 'BRANCH', defaultValue: 'main', description: '构建分支')
    choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'], description: '部署环境')
    booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: '跳过测试（仅应急）')
    password(name: 'DB_PASSWORD', defaultValue: '', description: '数据库密码（不推荐，用凭据代替）')
    text(name: 'RELEASE_NOTE', defaultValue: '', description: '发布说明')
}
```

```bash
# API 触发带参数的构建
curl -X POST "http://localhost:8080/job/order-api/buildWithParameters" \
     --user admin:<API_TOKEN> \
     --data-urlencode "BRANCH=release/2.3" \
     --data-urlencode "ENVIRONMENT=staging"
```

```text
参数设计的三个经验
1. 参数别太多：超过 5 个说明流程还没收敛，考虑拆成多个任务或多分支。
2. 环境类参数用 choice 而不是 string，避免手输 staging / stage / stg 各种写法。
3. 敏感值永远不用 password 参数（它会出现在构建参数记录里），用凭据。
```

### 视图与文件夹

- 文件夹（Folder）：权限、凭据、视图都能按文件夹收敛。团队多了之后，没有文件夹的 Jenkins 会变成一堆散乱的任务。
- 列表视图（List View）：按正则筛选任务名，例如 `.*-prod` 看所有生产任务。
- 我的视图：按人聚合关注的任务，前端/后端各自看自己的。

## 凭据管理

Jenkins 的凭据是加密存储在控制器上的（用控制器 ID 派生密钥加密），流水线里只引用 ID，不接触明文。

### 凭据类型

| 类型 | 典型用途 | Pipeline 里怎么用 |
| --- | --- | --- |
| Secret text | API Token、Webhook 密钥 | `string(credentialsId, variable)` |
| Username/Password | 镜像仓库、数据库、Nexus | `usernamePassword(...)` |
| Secret file | kubeconfig、证书文件 | `file(credentialsId, variable)` |
| SSH Username with private key | 拉代码、推制品、远程部署 | `sshUserPrivateKey(...)` |
| Certificate | PKCS#12 客户端证书 | `certificate(...)` |
| Docker Host Certificate | 直连 Docker 守护进程 | 在 Docker 配置里引用 |

### 界面添加

Manage Jenkins > Credentials > System > Global credentials > Add Credentials，按 Kind 选类型、填 ID（**ID 一旦定了别改**，任务里都引用它）、写描述。演示环境里出现过的凭据值截图一律脱敏：

![凭据管理](images/05-凭据管理.png)

### 用脚本添加（可版本化、可复现）

```bash
# examples/manage-credentials.sh 的核心部分
curl -X POST -u admin:$TOKEN --data-urlencode 'json={
  "": "0",
  "credentials": {
    "scope": "GLOBAL",
    "id": "demo-api-token",
    "secret": "s3cr3t-token-for-demo-9f1c",
    "description": "演示用 API Token",
    "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
  }
}' "$JENKINS_URL/credentials/store/system/domain/_/createCredentials"
```

```bash
# 列出凭据（只返回 id/描述/类型，不含机密值）
curl -s -u admin:$TOKEN \
  "$JENKINS_URL/credentials/store/system/domain/_/api/json?tree=credentials[id,description,typeName]"
```

### 在流水线里使用

```groovy
stage('使用凭据') {
    steps {
        withCredentials([string(credentialsId: 'demo-api-token', variable: 'API_TOKEN'),
                         usernamePassword(credentialsId: 'demo-registry',
                                          usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
            sh '''
                set -eu
                echo "token 长度：${#API_TOKEN}"          # 正确：只打印长度，不打印值
                echo "用户名：${REG_USER}"
                # 错误示范：echo "$API_TOKEN" —— 会明文进控制台日志
            '''
        }
    }
}
```

```text
凭据使用的四条铁律
1. 不要在 shell 里 echo 凭据值，Jenkins 只能屏蔽打印出来的固定字符串，
   拼进 URL（如 git clone https://user:pass@host）时可能漏出来。
2. 不要把凭据写在 Jenkinsfile 里，也不要写进 config.xml；
   Jenkinsfile 的所有者能读凭据，这本身就是权限边界。
3. 用 Groovy 双引号字符串引用凭据会造成插值泄漏（源码里能看到），
   必须用单引号 + shell 变量，或用 Jenkins 的 credentials() 辅助方法。
4. 定期轮换：凭据页看不到「谁在用」，改动前先在「凭据 > 使用情况」确认引用点。
```

## 流水线（Jenkinsfile）

Jenkins 的流水线有两种写法：**声明式（Declarative）** 和 **脚本式（Scripted）**。新项目一律用声明式，结构固定、错误信息友好；脚本式只在需要复杂逻辑（循环、动态定义 stage）时用，或者在声明式里用 `script {}` 块包住。

```groovy
pipeline {                 // 声明式固定入口
    agent any              // 在哪里跑
    options { }            // 超时、并发、保留策略
    parameters { }         // 参数
    environment { }        // 环境变量
    triggers { }           // 触发器
    stages {
        stage('构建') {
            steps { }      // 具体动作
            post { }       // 该阶段的收尾
        }
    }
    post { always { } }    // 整条流水线的收尾
}
```

### agent：在哪里执行

```groovy
agent any                                     // 任意可用节点
agent { label 'linux && maven' }               // 指定标签的节点
agent none                                     // 顶层不分配，各 stage 自己声明（推荐）
agent { docker { image 'maven:3.9-eclipse-temurin-21-alpine' } }   // 容器里跑（需 Docker Pipeline 插件）
agent { dockerfile true }                      // 用仓库里的 Dockerfile 构建镜像再跑
agent { kubernetes { yaml '...' } }            // Kubernetes 上动态起 Pod（需 Kubernetes 插件）
```

```text
agent 选择经验
- 顶层用 agent none，每个 stage 按需声明，构建环境不互相污染。
- 需要特定工具链（Maven/Node/Python/Go）优先用 docker agent，别在节点上装一堆版本。
- 需要持久缓存（maven 本地仓库、npm cache）就挂卷：args '-v $HOME/.m2:/root/.m2'。
- 用了 docker agent 又要后续 stage 复用工作区时，加 reuseNode true，
  否则每个 stage 会拿到一个全新的空工作区（这是新手最费解的行为之一）。
```

### 常用步骤

```groovy
steps {
    echo '文本输出'
    sh 'shell 命令'                    // Linux/macOS
    bat 'dir'                          // Windows
    sh returnStdout: true, script: 'git rev-parse HEAD'    // 拿命令输出
    dir('backend') { sh 'mvn -B package' }                 // 切子目录
    checkout scm                       // 拉代码（声明式里默认已 checkout，可关掉）
    junit 'target/surefire-reports/*.xml'                  // 收集测试报告
    archiveArtifacts artifacts: 'dist/**', fingerprint: true   // 归档制品
    stash/unstash                       // 跨 stage / 跨 agent 传文件
    sleep 10                            // 等外部系统就绪
    retry(3) { sh './flaky.sh' }        // 重试
    timeout(time: 5, unit: 'MINUTES') { input '确认继续？' }   // 人工卡点
    withCredentials([...]) { }          // 注入凭据
    withEnv(['PATH+MAVEN=/opt/maven/bin']) { }
    lock('deploy-lock') { }             // 全局锁，避免两个任务同时部署
    cleanWs()                           // 清工作区（ws-cleanup 插件）
}
```

### 控制流：when、parallel、matrix

```groovy
stage('仅在主干构建') {
    when {
        allOf {
            branch 'main'
            expression { params.ENVIRONMENT != 'prod' }
            not { changeRequest() }
        }
    }
    steps { echo '主干构建' }
}

stage('并行测试') {
    parallel {
        stage('单元测试') { steps { sh './gradlew test' } }
        stage('静态检查') { steps { sh './gradlew checkstyleMain' } }
        stage('容器构建') { steps { sh 'docker build -t app:test .' } }
        // failFast true 表示任一分支失败就取消其他分支
    }
}

stage('多平台矩阵') {
    matrix {
        axes {
            axis { name 'JDK'; values '21', '25' }
            axis { name 'OS'; values 'linux', 'windows' }
        }
        excludes {
            exclude {
                axis { name 'OS'; values 'windows' }
                axis { name 'JDK'; values '25' }
            }
        }
        stages {
            stage('编译') { steps { sh "echo build on ${OS} with JDK ${JDK}" } }
        }
    }
}
```

### post：收尾动作

```groovy
post {
    always  { junit '**/surefire-reports/*.xml'; cleanWs() }   // 无论结果都执行
    success { echo '通知：构建成功' }
    unstable { echo '有测试失败但没中断构建' }                    // 测试失败默认是 UNSTABLE
    failure { echo '通知：构建失败'; sh './notify.sh failed' }
    aborted { echo '被人工中断' }
    cleanup { deleteDir() }                                   // 所有 post 执行完后
}
```

```text
UNSTABLE 与 FAILURE 的区别要记住
- junit 步骤发现测试失败 → 构建标记 UNSTABLE（黄色），后续 stage 默认继续跑。
- 脚本返回非 0 → FAILURE（红色），流水线立即中断。
- 想「测试失败就别部署」：在部署 stage 加 when { expression { currentBuild.currentResult == 'SUCCESS' } }，
  或在测试 stage 后加 catchError(buildResult: 'FAILURE', stageResult: 'FAILURE')。
```

### 共享库：把重复的流水线抽成函数

同一套流程在几十个仓库里复制粘贴，改一次要改几十处——这时用共享库。

```groovy
// 仓库结构（完整示例见 examples/shared-library/）
// vars/buildPython.groovy          全局变量：Jenkinsfile 里直接 buildPython(...)
// src/org/example/Utils.groovy     工具类，可写单元测试
// resources/messages.txt           非 Groovy 资源，libraryResource 读取

// 使用方 Jenkinsfile
@Library('my-shared-lib@main') _
pipeline {
    agent none
    stages {
        stage('标准 Python 构建') {
            steps {
                buildPython(python: 'python3', env: params.ENVIRONMENT)
            }
        }
    }
}
```

```text
共享库的运维要点
- 版本用 tag 或固定 commit，别用分支名 'main'（某天有人推错就影响所有仓库）；
  用 @Library('my-shared-lib@v1.4.0')。
- 共享库代码不走脚本沙箱审批的白名单机制，改共享库等于改所有流水线，
  需要更严格的评审与回归。
- 共享库里避免直接插值用户可控字符串（防 Groovy 注入）。
```

### Docker agent 与容器内构建

```groovy
// 场景一：整个阶段在容器里跑，工作区自动挂载进去
stage('后端构建') {
    agent { docker { image 'maven:3.9-eclipse-temurin-21-alpine' } }
    steps { dir('backend') { sh 'mvn -B clean package' } }
}

// 场景二：同一个工作区、缓存 maven 本地仓库（第二次构建快很多）
stage('后端构建（带缓存）') {
    agent {
        docker {
            image 'maven:3.9-eclipse-temurin-21-alpine'
            args '-v $HOME/.m2:/root/.m2'
            reuseNode true
        }
    }
    steps { dir('backend') { sh 'mvn -B clean package' } }
}

// 场景三：脚本式里临时起容器做一件事
stage('用容器跑数据库集成测试') {
    steps {
        script {
            docker.image('postgres:18-alpine').withRun('-e POSTGRES_PASSWORD=test -p 5432:5432') { c ->
                sh './wait-for-db.sh'
                sh 'mvn -B verify -Dspring.profiles.active=integration'
            }
        }
    }
}
```

```text
容器内构建的四个坑
1. 容器里没有宿主的 ~/.m2、~/.npm，全靠挂卷或每次重下 → 第一次构建慢是正常的，
   第二次起要看到明显加速，否则说明缓存没挂上。
2. 容器里默认 root 用户，产物文件属主是 root，导致后续 stage 无法删除工作区
   （表现为 cleanWs 报权限错误）→ 加 args '-u $(id -u):$(id -g)' 或构建后 chown。
3. 容器里没有 git：docker agent 的代码拉取是控制器做的，容器里要跑 git 命令得自己装。
4. 镜像拉取失败会让构建停在 "Pulling image"，生产给 agent 配私服镜像地址与镜像缓存，
   别每次都从 Docker Hub 拉。
```

## 分布式构建与 Agent

单台控制器的执行器数量受限于 CPU 和内存，构建一多就排队；不同项目要的 JDK/Node/Python 版本也不同。解法是把执行推到 agent 上。

### 三种接入方式

| 方式 | 控制器怎么连 agent | 适用场景 |
| --- | --- | --- |
| SSH | 控制器主动 SSH 到 agent 机器（需装 JDK） | 固定几台构建机，最省事 |
| 入站（Inbound / JNLP） | agent 主动连控制器（TCP 50000 或 WebSocket） | agent 在 NAT 后面、容器里，推荐 |
| 容器 / Kubernetes | 按需起 Pod，用完销毁 | 弹性、隔离最好，需要集群 |

```text
选型建议
- 3-5 台固定构建机：SSH 或入站都可以，入站不用给控制器开 SSH 权限更安全。
- 用 Docker/K8s：优先用 Kubernetes 插件动态起 Pod，任务里写 agent { kubernetes { yaml '...' } }，
  构建环境完全隔离，且不用维护常驻 agent。
- 无论哪种方式，都给「控制器内置节点」把执行器设为 0，避免构建在控制器上跑。
```

### 用容器跑一个入站 agent

```bash
# 1. 在控制器上创建节点（用 CLI，XML 内容见 examples/create-agent.sh）
java -jar jenkins-cli.jar -s http://localhost:8080 -auth admin:$TOKEN \
     create-node linux-agent-1 < /tmp/agent.xml

# 2. 取 agent 的密钥（就是节点页面上的 secret）
SECRET=$(curl -s -u admin:$TOKEN \
  http://localhost:8080/computer/linux-agent-1/slave-agent.jnlp \
  | python3 -c 'import sys,xml.etree.ElementTree as ET; print(ET.fromstring(sys.stdin.read()).find("application-desc/argument[2]").text)')

# 3. 起 agent 容器（与控制器同网络，用容器名访问控制器）
docker run -d --name linux-agent-1 --restart unless-stopped \
  --network jenkins_default \
  -e JENKINS_URL=http://jenkins:8080 \
  -e JENKINS_AGENT_NAME=linux-agent-1 \
  -e JENKINS_SECRET=$SECRET \
  -e JENKINS_AGENT_WORKDIR=/home/jenkins/agent \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/inbound-agent:latest-jdk21
```

```bash
# 4. 验证：agent 在线且标签可用
curl -s -u admin:$TOKEN "http://localhost:8080/computer/linux-agent-1/api/json?tree=offline,numExecutors,assignedLabels"
curl -s -u admin:$TOKEN "http://localhost:8080/computer/api/json?tree=computer[displayName,offline,numExecutors]"
```

`examples/create-agent.sh` 里包含完整的节点 XML（`JNLPLauncher` + `workDirSettings` + 标签），直接跑即可。节点 XML 的关键字段：

```xml
<slave>
  <name>linux-agent-1</name>
  <remoteFS>/home/jenkins/agent</remoteFS>
  <numExecutors>2</numExecutors>            <!-- 并发构建数 = 执行器数 -->
  <mode>NORMAL</mode>
  <retentionStrategy class="hudson.slaves.RetentionStrategy$Always"/>   <!-- 常驻 -->
  <launcher class="hudson.slaves.JNLPLauncher">                          <!-- 入站方式 -->
    <workDirSettings>
      <disabled>false</disabled>
      <internalDir>remoting</internalDir>
      <failIfWorkDirIsMissing>false</failIfWorkDirIsMissing>
    </workDirSettings>
  </launcher>
  <label>linux docker-agent</label>          <!-- 任务里用 agent { label 'linux' } 匹配 -->
</slave>
```

### 标签与调度

```groovy
// 任务侧
agent { label 'linux && jdk21' }        // 与运算
agent { label 'linux || macos' }        // 或运算
agent { label '!windows' }              // 非运算
```

```text
调度的三个坑
1. 标签里别用空格表达「与」，要写 'linux && jdk21' 或 'linux jdk21'（空格同样是「与」）。
2. agent 掉线时构建会挂在 "Waiting for next available executor"，
   排查顺序：节点页面是否在线 → 容器日志 → 控制器 50000 端口是否可达 → 密钥是否过期。
3. 执行器不是越多越好：一个构建吃 4 核，节点给 8 个执行器只会互相拖慢。
   经验值是小任务 1-2 个执行器/核，重构建 1 个执行器/核甚至更少。
```

### 动态 agent（Kubernetes）

```groovy
// 任务里直接声明 Pod 模板，用完即销毁
podTemplate(
    containers: [
        containerTemplate(name: 'maven', image: 'maven:3.9-eclipse-temurin-21-alpine', ttyEnabled: true, command: 'cat'),
        containerTemplate(name: 'node', image: 'node:22-alpine', ttyEnabled: true, command: 'cat')
    ],
    volumes: [secretVolume(secretName: 'maven-secret', mountPath: '/root/.m2')]
) {
    node(POD_LABEL) {
        stage('后端') {
            container('maven') { sh 'mvn -B package' }
        }
        stage('前端') {
            container('node') { sh 'npm ci && npm run build' }
        }
    }
}
```

## 自动化：REST API、CLI、Job DSL

Jenkins 的所有 UI 操作背后都是 HTTP 请求，因此都能脚本化。做平台对接时（例如自研发布系统里点一下「部署」），靠的就是这一层。

### 认证：用 API Token，不要用密码

用户在「个人资料 > 安全 > API Token」里生成 Token，之后所有请求用 `--user 用户名:Token`。本机实测生成 Token 也可以用 API 直接做（需要管理员权限）：

```bash
# 生成 API Token（返回值里 tokenValue 就是 Token，只显示一次）
curl -X POST -u admin:admin-demo-pass \
  "http://localhost:8080/user/admin/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken" \
  --data-urlencode 'newTokenName=demo-token' | python3 -m json.tool
```

```text
认证与 CSRF 的经验
- 优先用 API Token；密码登录会随认证策略变化而失效。
- 跨站请求伪造（CSRF）保护开启时，POST 请求要么带 Token（推荐），
  要么带 crumb（/crumbIssuer/api/json 拿），两者别混用。
- 早期版本常用的 /j_spring_security_check 登录接口已废弃，
  脚本里不要再依赖它做「先登录再操作」。
```

### REST API 速查

```bash
J=http://localhost:8080

# 1. 控制器信息（版本、执行器、队列）
curl -s -u admin:$TOKEN "$J/api/json?tree=mode,nodeName,numExecutors,jobs[name,color],quietingDown"
curl -s -u admin:$TOKEN "$J/api/json?tree=jobs[name,url,lastBuild[number,result]]" | python3 -m json.tool

# 2. 触发构建（无参 / 带参）
curl -X POST -u admin:$TOKEN "$J/job/order-api/build"
curl -X POST -u admin:$TOKEN "$J/job/order-api/buildWithParameters" \
     --data-urlencode "BRANCH=main" --data-urlencode "ENVIRONMENT=dev"

# 3. 查构建状态与结果
curl -s -u admin:$TOKEN "$J/job/order-api/lastBuild/api/json?tree=number,building,result,duration,url"

# 4. 取控制台输出（纯文本，最适合脚本判断）
curl -s -u admin:$TOKEN "$J/job/order-api/lastBuild/consoleText" | tail -30

# 5. 制品与指纹
curl -s -u admin:$TOKEN "$J/job/order-api/lastBuild/api/json?tree=artifacts[fileName,relativePath]"
curl -O -u admin:$TOKEN -J "$J/job/order-api/lastBuild/artifact/dist/app.tar.gz"

# 6. 队列与取消
curl -s -u admin:$TOKEN "$J/queue/api/json?tree=items[id,task[name],why]"
curl -X POST -u admin:$TOKEN "$J/queue/item/123/cancelQueue"
curl -X POST -u admin:$TOKEN "$J/job/order-api/42/stop"

# 7. 任务配置的读取与写入（配置即代码的基础）
curl -s -u admin:$TOKEN "$J/job/order-api/config.xml" -o order-api-config.xml
curl -X POST -u admin:$TOKEN -H 'Content-Type: application/xml' \
     --data-binary @order-api-config.xml "$J/job/order-api/config.xml"

# 8. 系统操作
curl -X POST -u admin:$TOKEN "$J/quietDown"        # 停止接新任务，等现有构建结束
curl -X POST -u admin:$TOKEN "$J/cancelQuietDown"
curl -X POST -u admin:$TOKEN "$J/safeRestart"      # 安全重启（等价 safe-restart）
curl -s -u admin:$TOKEN  "$J/api/json?tree=quietingDown"
```

```text
XPath 取值（接口返回 XML 时特别方便，避免装 jq/xmllint）
curl -s -u admin:$TOKEN "$J/job/order-api/api/xml?xpath=//lastBuild/number"
curl -s -u admin:$TOKEN "$J/api/xml?xpath=//job/name&wrapper=jobs"
```

`examples/create-job.sh` 是一份可直接运行的完整脚本：创建任务（XML）、触发带参构建、轮询结果、打印控制台尾部、输出制品清单。用 API 建任务的价值在于「新环境一条命令铺好所有任务」，本教程后续实战就用它建任务。

### Jenkins CLI

两种模式：SSH（`ssh -p <端口> jenkins 命令`，需在用户里配公钥）和 CLI 客户端（`java -jar jenkins-cli.jar`，用 Token 认证）。实战推荐 CLI 客户端，因为不用给控制器开 SSH。

```bash
# 下载客户端（版本跟随控制器，不要用旧版）
curl -fsSL "$J/jnlpJars/jenkins-cli.jar" -o jenkins-cli.jar

JAR="java -jar jenkins-cli.jar -s $J -auth admin:$TOKEN"

$JAR version                # 控制器版本
$JAR who-am-i               # 当前身份与权限
$JAR list-jobs              # 所有任务
$JAR build order-api -f     # 触发并跟随控制台输出（-p 传参数、-s 等入队完成、-v 打印参数）
$JAR console order-api      # 最近一次构建的控制台输出
$JAR list-plugins           # 插件清单（含可用更新）
$JAR install-plugin git -deploy    # 装插件并立即装载
$JAR create-node agent-1 < agent.xml
$JAR list-computers         # 节点列表
$JAR reload-configuration   # 从磁盘重读所有配置（改完 config.xml 用这个）
$JAR safe-restart           # 安全重启
$JAR help                   # 全部命令（含插件提供的命令）
```

```text
CLI 的常见问题
- 报 "No such file or directory" 或 403：Token 错了，或者该用户缺少 Overall/Read。
- 报 "Connection refused"：CLI 默认走 HTTP 端口 + WebSocket，容器里需要能访问控制器的 8080。
- 命令不在列表里：那是插件提供的命令，插件没装或没加载完。
```

### Job DSL：用代码批量生成任务

几十个同构任务（例如每个服务一套构建任务）用 UI 点是灾难，用 Job DSL 生成才可持续。

```groovy
// examples/seed-job.groovy 片段
pipelineJob('order-api-build') {
    description('由 Job DSL 生成，配置进 Git')
    parameters {
        stringParam('BRANCH', 'main', '构建分支')
    }
    definition {
        cpsScm {
            scm {
                git { remote { url('git@git.example.com:order/order-api.git') }; branch('*/main') }
            }
            scriptPath('Jenkinsfile')
            lightweight(true)
        }
    }
    logRotator { numToKeep(30); artifactNumToKeep(10) }
}

multibranchPipelineJob('order-api-multibranch') {
    branchSources {
        git { id('order-api'); remote('git@git.example.com:order/order-api.git') }
    }
    orphanedItemStrategy { discardOldItems { numToKeep(5) } }
}

freeStyleJob('nightly-report') {
    triggers { cron('H 2 * * *') }
    steps { shell('echo "nightly at $(date)"') }
}
```

```groovy
// 在 Jenkins 里跑 Job DSL 有两种方式：
// 1) 建一个「Pipeline script」任务，内容就一行：
jobDsl targets: 'jobs/**/*.groovy', removedJobAction: 'DELETE', removedViewAction: 'DELETE'
// 2) 装 Job DSL 插件后建「Freestyle/Pipeline 种子任务」，用 Git 里的 DSL 脚本生成任务
```

```text
Job DSL 的纪律
- removedJobAction: 'DELETE' 让「脚本里删掉的任务」在 Jenkins 里也删掉，
  否则会出现「代码里没有、Jenkins 里还在跑」的幽灵任务。
- 生成的任务不要再去 UI 改：改了下次跑种子任务就被覆盖，
  这正是它的价值（配置唯一来源是代码）。
- 任务名用规范前缀（服务名-用途-环境），种子脚本里写死命名规则，
  新人照抄就行。
```

### Webhook：推送即构建

以 GitLab 为例（GitHub/Gitee 类似）：

```text
1. Jenkins 侧：任务 > 构建触发器 > 勾选
   - GitLab: "Build when a change is pushed to GitLab"（需 GitLab 插件）
   - 通用: "Trigger builds remotely (e.g., from scripts)"，设一个 Token
2. GitLab 侧：项目 > Settings > Webhooks
   URL: http://jenkins.example.com/project/<任务名>
   或通用形式: http://jenkins.example.com/job/<任务名>/build?token=<TOKEN>
   触发事件: Push events / Merge request events
3. 点 Test 看返回：HTTP 200/201 表示 Jenkins 收到了
```

```text
Webhook 收不到的排查顺序
1. Jenkins URL 配的是不是内网地址（Manage Jenkins > System > Jenkins Location）。
2. Jenkins 所在机器能不能被 Git 服务器访问到（反向：很多公司只允许 Jenkins 出网）。
3. 反向代理有没有放行 Webhook 路径、有没有把 POST 体截断。
4. 任务里有 SCM 变更检测时，Webhook 只是「叫醒」Jenkins，真正拉哪个分支由任务配置决定。
```

## 实战一：通用 Python 项目流水线

先用一个最小项目把「拉代码 → 装依赖 → 跑测试 → 打包 → 归档」跑通，建立手感。项目在 `examples/demo-app`，流水线在 `examples/Jenkinsfile`。

项目结构：

```text
demo-app/
├── app/__init__.py        业务代码（add / divide / normalize_scores）
├── tests/test_app.py      5 个 pytest 用例
├── requirements.txt       pytest 9.1.1 + pytest-cov 7.1.0
└── Jenkinsfile            流水线定义
```

用 REST API 建任务（脚本见 `examples/create-job.sh`，把 `GIT_URL` 指向自己的仓库）：

```bash
export JENKINS_URL=http://localhost:8080 JENKINS_USER=admin JENKINS_TOKEN=<API_TOKEN>
export JOB_NAME=demo-pipeline GIT_URL=file:///demo/repo.git BRANCH=main
bash examples/create-job.sh
```

脚本会依次做四件事：创建任务（XML 里指定 SCM 与脚本路径）、触发带参构建、轮询结果、打印控制台尾部。真实输出：

```text
== 1. 健康检查与版本 ==
{"_class":"hudson.model.Hudson","mode":"NORMAL","nodeName":"","numExecutors":2,"quietingDown":false}
login HTTP 200
== 2. 创建（或覆盖）流水线任务 ==
任务已创建：demo-pipeline
== 3. 触发带参数构建 ==
trigger HTTP 201
```

流水线的关键部分（完整文件见 `examples/Jenkinsfile`）：

```groovy
stages {
    stage('Checkout') {
        steps {
            checkout scm
            script { env.GIT_REVISION = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim() }
        }
    }
    stage('Build') {
        steps {
            sh '''
                set -eux
                python3 -m venv ${VENV_DIR}
                ${VENV_DIR}/bin/pip install -q -r requirements.txt
            '''
        }
    }
    stage('Test') {
        parallel {
            stage('Unit Test') {
                steps {
                    sh '''
                        ${VENV_DIR}/bin/python -m pytest -q --junitxml=reports/unit.xml \
                            --cov=app --cov-report=xml:reports/coverage.xml
                    '''
                }
                post { always { junit 'reports/unit.xml' } }
            }
            stage('Lint') { steps { sh '${VENV_DIR}/bin/python -m compileall -q app' } }
        }
    }
    stage('Package') {
        steps {
            sh 'tar -czf dist/${APP_NAME}-${GIT_REVISION}.tar.gz app requirements.txt Jenkinsfile'
            archiveArtifacts artifacts: 'dist/*', fingerprint: true
        }
    }
}
```

```text
这个最小流水线里值得记住的四点
1. 用 venv 而不是全局 pip：构建环境与宿主隔离，避免 Python 版本与包互相污染。
2. junit 收集 XML 报告：测试失败会被标记为 UNSTABLE，构建页出现趋势图。
3. archiveArtifacts + fingerprint：产物可下载、可追溯，能被下游任务 copyArtifacts 复用。
4. 参数化构建（ENVIRONMENT/BRANCH/RUN_SLOW_TESTS）：同一份代码支撑多种触发方式，
   慢速回归用 when { expression { params.RUN_SLOW_TESTS } } 控制，不必建第二个任务。
```

## 实战二：Spring Boot + Vue 前后端分离项目 CI/CD

这是本教程的重点实战：一个真实的前后端分离项目，从提交代码到两个容器跑起来、冒烟通过。源码在 `examples/springboot-vue-demo/`。

### 项目结构与技术栈

```text
springboot-vue-demo/
├── backend/                       Spring Boot 4.1.1 + JDK 21
│   ├── pom.xml                    spring-boot-starter-web / actuator / validation / webmvc-test
│   ├── src/main/java/com/example/demo/
│   │   ├── DemoApplication.java
│   │   └── TodoController.java    /api/todos 增删改查 + /api/todos/health
│   ├── src/test/java/.../TodoControllerTest.java   4 个 MockMvc 用例
│   └── Dockerfile                 eclipse-temurin:21-jre-alpine 运行时镜像
├── frontend/                      Vue 3.5.44 + Vite 8.3.4
│   ├── src/App.vue                待办清单界面
│   ├── src/api.js                 axios 封装，/api 走相对路径
│   ├── nginx.conf                 静态站点 + /api 反代到后端容器
│   └── Dockerfile                 nginx:1.27-alpine
├── Jenkinsfile                    完整 CI/CD 流水线
├── maven-settings.xml             阿里云镜像源（给 maven 容器用）
└── docker-compose.yml             本地手工起环境用
```

```text
技术栈选型说明（2026 年现状，均已在本机实测）
- Spring Boot 4.1.1：3.x 已停止免费维护，新项目直接上 4.x；要求 Java 17+，本机用 21。
- Spring Boot 4 拆包坑：MockMvc 的 @AutoConfigureMockMvc 从
  org.springframework.boot.test.autoconfigure.web.servlet
  挪到了 org.springframework.boot.webmvc.test.autoconfigure，
  且需要额外依赖 spring-boot-starter-webmvc-test，否则测试编译不过（本机实测踩到）。
- Vue 3 + Vite 8：Vite 8 构建快（本项目 67 个模块 393ms 出包），
  Node 22 容器里 npm install 走 npmmirror 约 33 秒。
- nginx 反代 /api：开发时靠 Vite proxy，生产靠 nginx，前端代码里不需要写死后端地址。
```

### 环境准备（两个容易翻车的点）

**点一：maven 缓存与镜像源。** docker agent 每次都是干净容器，不挂卷就要重下几百 MB 依赖。

```bash
# 把 settings.xml 放到 $JENKINS_HOME/.m2/，让 maven 容器挂载后直接生效
docker exec -u 0 jenkins-demo mkdir -p /var/jenkins_home/.m2
docker cp maven-settings.xml jenkins-demo:/var/jenkins_home/.m2/settings.xml
```

```groovy
// Jenkinsfile 里对应写法：把 $HOME/.m2 挂进容器
agent {
    docker {
        image 'maven:3.9-eclipse-temurin-21-alpine'
        args '-v $HOME/.m2:/root/.m2'
        reuseNode true
    }
}
```

**点二：容器里要有 docker 命令，且 jenkins 用户要有套接字权限。**

```bash
# 起 Jenkins 容器时同时解决这两件事（本机实测有效）
docker run -d --name jenkins-demo -p 8080:8080 -p 50000:50000 \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  -v jenkins_demo_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker:ro \
  jenkins/jenkins:lts-jdk21
```

```text
本机实测：宿主 docker.sock 的 gid 是 984；--group-add 984 之后容器内 jenkins 用户
（uid 1000）就能执行 docker ps。当然，挂套接字的代价是构建脚本等价于宿主 root，
生产要么换远程 Docker daemon，要么用 Kubernetes 动态 agent（见安全加固一节）。
```

### 流水线设计

```text
拉取代码 → 并行构建（后端 maven 测试打包 / 前端 npm 构建）
        → 构建两个镜像（demo-backend / demo-frontend，tag 带 git 短哈希）
        → 部署（重建容器，接同一个 bridge 网络）
        → 冒烟测试（后端健康检查、通过前端 nginx 反代访问、走一遍写接口）
        → 收尾（清理工作区，失败时提示回滚方式）
```

关键片段（完整 Jenkinsfile 见 `examples/springboot-vue-demo/Jenkinsfile`）：

```groovy
pipeline {
    agent none                       // 顶层不分配执行器，每个 stage 自己声明
    parameters {
        string(name: 'BRANCH', defaultValue: 'main', description: '构建分支')
        string(name: 'IMAGE_TAG', defaultValue: '1.0.0', description: '镜像 tag')
        booleanParam(name: 'DEPLOY', defaultValue: true, description: '是否部署并冒烟')
    }
    options { timestamps(); timeout(time: 40, unit: 'MINUTES'); disableConcurrentBuilds() }
    stages {
        stage('拉取代码') {
            agent any
            steps {
                checkout scm
                script {
                    env.SHORT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
                    env.BUILD_VERSION = "${params.IMAGE_TAG}-${env.SHORT_SHA}"
                    currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.BUILD_VERSION}"
                }
            }
        }
        stage('并行构建') {
            parallel {
                stage('后端构建与单测') {
                    agent { docker { image 'maven:3.9-eclipse-temurin-21-alpine'; args '-v $HOME/.m2:/root/.m2'; reuseNode true } }
                    steps { dir('backend') { sh 'mvn -B -ntp clean package' } }
                    post { always { junit 'backend/target/surefire-reports/*.xml' } }
                }
                stage('前端构建') {
                    agent { docker { image 'node:22-alpine'; reuseNode true } }
                    steps { dir('frontend') { sh 'npm ci || npm install'; sh 'npm run build' } }
                    post { always { stash name: 'frontend-dist', includes: 'frontend/dist/**' } }
                }
            }
        }
        stage('构建镜像') {
            agent any
            steps {
                unstash 'frontend-dist'
                sh '''
                    docker build -t demo-backend:${BUILD_VERSION} backend
                    docker build -t demo-frontend:${BUILD_VERSION} frontend
                '''
            }
        }
        stage('部署') { /* 见下 */ }
        stage('冒烟测试') { /* 见下 */ }
    }
}
```

部署与冒烟两个 stage 的完整写法：

```groovy
stage('部署') {
    when { expression { params.DEPLOY } }
    agent any
    steps {
        sh '''
            set -eux
            docker network inspect ${NETWORK} >/dev/null 2>&1 || docker network create ${NETWORK}
            docker rm -f demo-backend demo-frontend 2>/dev/null || true
            docker run -d --name demo-backend --network ${NETWORK} --restart unless-stopped \
                -p ${BACKEND_PORT}:9090 -e SPRING_PROFILES_ACTIVE=prod -e TZ=Asia/Shanghai \
                demo-backend:${BUILD_VERSION}
            docker run -d --name demo-frontend --network ${NETWORK} --restart unless-stopped \
                -p ${FRONTEND_PORT}:80 demo-frontend:${BUILD_VERSION}
            docker ps --filter name=demo- --format "{{.Names}} {{.Status}} {{.Ports}}"
        '''
    }
}

stage('冒烟测试') {
    when { expression { params.DEPLOY } }
    agent any
    steps {
        sh '''
            set -eux
            for i in $(seq 1 30); do
                curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/todos/health" >/dev/null 2>&1 && break
                sleep 2
            done
            curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/todos/health"; echo
            curl -fsS "http://127.0.0.1:${BACKEND_PORT}/actuator/health"; echo
            curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/api/todos/health"; echo
            curl -s -o /dev/null -w 'frontend HTTP %{http_code}\n' "http://127.0.0.1:${FRONTEND_PORT}/"
            curl -fsS -X POST "http://127.0.0.1:${FRONTEND_PORT}/api/todos" \
                 -H 'Content-Type: application/json' -d '{"title":"冒烟测试写入"}'; echo
            docker inspect --format '{{.Name}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
                demo-backend demo-frontend
        '''
    }
}
```

```text
为什么这么设计
1. 后端测试与前端构建并行：两个环境互不依赖，串行跑纯属浪费（本机实测两阶段并行执行）。
2. 前后端分别出镜像、分别部署：前端改动不需要重新构建后端镜像，回滚也各自独立。
3. 镜像 tag 带 git 短哈希：出问题能精确定位到代码版本，回滚就是 run 旧 tag。
4. 冒烟测试走「前端 nginx → 后端」的完整链路，而不是只 curl 后端端口：
   这样 nginx 反代配置写错（最常见的 /api 路径问题）也会被自动化发现。
5. 部署前 rm -f 旧容器是「停一台起一台」的简化版；真实生产要用蓝绿或滚动，
   至少要保证新容器健康后再摘旧容器。
```

### 真实构建输出

工程代码在 Jenkins 之外先跑通了一遍（保证代码本身没问题）：

```text
# 后端：Spring Boot 4.1.1 + JDK 21
$ mvn -B -ntp clean package
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
[INFO] --- maven-jar-plugin:3.5.1:jar (default-jar) @ demo-backend ---
[INFO] Building jar: .../backend/target/demo-backend.jar
[INFO] --- spring-boot-maven-plugin:4.1.1:repackage (repackage) ---
[INFO] Replacing main artifact with repackaged archive, adding nested dependencies in BOOT-INF/.
[INFO] BUILD SUCCESS
[INFO] Total time:  22.993 s

# 前端：Vue 3.5.44 + Vite 8.3.4
$ npm install --registry=https://registry.npmmirror.com
added 62 packages in 33s
$ npm run build
vite v8.3.4 building client environment for production...
✓ 67 modules transformed.
dist/index.html                   0.41 kB │ gzip:  0.30 kB
dist/assets/index-BJNM49jh.css    1.11 kB │ gzip:  0.56 kB
dist/assets/index-kkp76qh4.js   117.23 kB │ gzip: 44.73 kB
✓ built in 393ms
```

Jenkins 侧已跑通的部分（同样的任务、真实控制台输出）：

```text
Obtained Jenkinsfile from git file:///demo/sbrepo.git      <- 从 SCM 读取流水线定义成功
[Pipeline] stage
[Pipeline] { (拉取代码)
[Pipeline] checkout
Running on Jenkins in /var/jenkins_home/workspace/springboot-vue-demo
```

改造过程中真实踩到并修掉的四个问题，报错原文值得记住：

```text
# 1) 挂载进来的 Git 仓库属主不是 jenkins 用户
fatal: detected dubious ownership in repository at '/demo/sbrepo.git'
To add an exception for this directory, call:
        git config --global --add safe.directory /demo/sbrepo.git
# 解法：docker exec -u jenkins jenkins-ci git config --global --add safe.directory '*'

# 2) 本地路径仓库被 git 插件默认拒绝（安全策略）
ERROR: Checkout of Git remote 'file:///demo/sbrepo.git' aborted because it
references a local directory, which may be insecure. You can allow local
checkouts anyway by setting the system property
'hudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT' to true.
# 解法：容器 JAVA_OPTS 加 -Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true（仅演示环境）

# 3) 参数定义写成 name = 'x'
WorkflowScript: 12: Arguments to "string" must be explicitly named.
# 解法：改成命名参数写法 string(name: 'BRANCH', defaultValue: 'main', ...)

# 4) 用 docker agent 跑官方镜像时的两个坑
ERROR: The container started but didn't run the expected command. Please double
check your ENTRYPOINT does execute the command passed as docker run argument.
npm error enoent Could not read package.json: ... /workspace/springboot-vue-demo@2/frontend/package.json
# 前者：node/maven 官方镜像的 ENTRYPOINT 不满足 docker-workflow 的空转命令约定
# 后者：parallel 每个分支各自声明 agent 时会拿到全新工作区（...@2），代码没被 checkout 进去
# 解法：改成「顶层 agent any + docker run 把容器当工具用」，工作区与行为完全可控（本文件当前写法）
```

```text
未在本机验证的部分（如实标注，不编造）
- 后端阶段的 maven 容器构建：镜像 maven:3.9-eclipse-temurin-21-alpine
  在本机拉取时反复失败（Docker Hub 连接被重置：read: connection reset by peer），
  因此「容器内 mvn package」「镜像构建」「部署」「冒烟测试」这一段没有在 Jenkins 里跑完整。
  已确认无误的是：同一份代码用本机 maven 构建测试通过、同一份 Jenkinsfile 的
  拉取代码阶段在 Jenkins 中真实跑通、参数与工作区类错误已按上面记录修复。
- 在能正常拉取 Docker Hub 镜像的环境里，把镜像准备好后执行：
  docker pull maven:3.9-eclipse-temurin-21-alpine && docker pull node:22-alpine
  然后触发任务即可跑完整条流水线。
```

### 界面效果

演示实例的真实界面（中文 UI 由 localization-zh-cn 插件提供）：

![流水线任务页](images/06-流水线任务页.png)

首次启动向导的四个页面（解锁、选择插件安装方式、插件列表、安装进度）见上文[安装部署](#安装部署)一节，截图全部来自本机实例。

### 回滚与灰度

```bash
# 回滚：镜像还在，重新 run 上一个 tag 即可（秒级）
docker rm -f demo-backend demo-frontend
docker run -d --name demo-backend --network demo-net -p 9090:9090 demo-backend:1.0.0-9f3c2ab
docker run -d --name demo-frontend --network demo-net -p 8088:80 demo-frontend:1.0.0-9f3c2ab

# 把「部署」做成可回滚的流水线：记录每个环境的当前 tag
curl -X POST -u admin:$TOKEN "$J/job/springboot-vue-demo/buildWithParameters" \
     --data-urlencode "IMAGE_TAG=1.0.0-9f3c2ab" --data-urlencode "DEPLOY=true"
```

```text
灰度的三种落地方式（按成本从低到高）
1. 双容器 + nginx upstream 权重：老版本留一台，新版本起一台，逐步切流量。
2. 按环境分层部署：dev 自动、staging 自动、prod 人工卡点 + 分批。
3. 借助 Kubernetes：Deployment 滚动更新 + readinessProbe，回滚用 kubectl rollout undo
   （此时 Jenkins 只负责构建镜像与触发 rollout，不再直接管容器）。
```

## 安全加固

Jenkins 被攻破的常见路径是：暴露到公网 + 弱口令 + 装了有漏洞的插件 + 任务里能执行任意命令（Groovy 沙箱绕过）。加固按下面顺序做。

### 1. 网络层：不要直接暴露

```bash
# 只监听本机，由 nginx 代理并加 HTTPS
docker run -d --name jenkins -p 127.0.0.1:8080:8080 ...
# 或者用防火墙白名单
sudo ufw allow from 10.0.0.0/8 to any port 8080 proto tcp
```

```text
暴露面清单（每一项都要有说法）
- 8080 Web UI/API：只对内网或经反向代理
- 50000 agent 端口：只对构建网段开放；不接 agent 就关掉
- /script（脚本控制台）：非管理员不应可见，最好在授权里直接不给
- /jnlpJars/ /cli：Token 泄漏等于拿到管理员
```

### 2. 认证与授权

- 认证：公司有 LDAP/OIDC 就接上（LDAP、OIDC、GitHub OAuth 插件），没有就用 Jenkins 本地用户库。
- 授权：**别用「登录用户可以做任何事」**。用 Matrix Authorization Strategy 或 Role-based Authorization Strategy 按角色（开发者/发布者/管理员）分配。
- 匿名用户：只给 `Overall/Read` 或干脆不给。

```text
权限矩阵最小可用版本（生产照着改）
管理员    Overall/Administer
发布者    Overall/Read、Job/Read、Job/Build、Job/Configure(受限)、Run/Replay、Credentials/Use
开发者    Overall/Read、Job/Read、Job/Build、Run/Update
只读      Overall/Read、Job/Read
注意：Job/Configure 等于可以改 Jenkinsfile 的所有者，
      让他们能读凭据、能执行任意命令 —— 所以「能配置任务」≈「是管理员」。
```

### 3. 控制器不要跑构建

```text
理由：
1. 构建里的任意脚本都能读到 $JENKINS_HOME/config.xml、secrets/、credentials.xml
2. 构建吃满 CPU/内存会让 UI 与调度一起变慢
3. 挂载了 docker.sock 的构建容器等价于宿主 root
做法：
- 控制器内置节点执行器设为 0
- 构建跑在 agent 或 docker/k8s 动态 agent 上
- 必须挂 docker.sock 时，用 rootless docker 或远程 Docker daemon（DOCKER_HOST=tcp://...）
```

### 4. 脚本安全与沙箱

```text
- 流水线脚本默认在 Groovy 沙箱里运行，遇到未批准的 API 会报
  "Scripts not permitted to use method ..."，需要管理员在
  Manage Jenkins > In-process Script Approval 里批准。
  批准前先看清是哪个方法：批准 org.jenkinsci.plugins...getInstance 这类等于开后门。
- 不要为了省事全局关掉沙箱（-Dpermissive-script-security.enabled=true 或
  在授权里放开 Script Security），那等于给所有人 root。
- 共享库（Shared Library）不受沙箱限制，等价于「受信任代码」：
  更新共享库要走评审，且限定为固定 tag。
```

### 5. 凭据与密钥

```text
- 凭据只在 Pipeline 里用 credentialsId 引用，不落 Jenkinsfile、不落 config.xml
- 别用密码参数（password 类型参数会记录明文）
- 容器部署时用 Docker secret / Vault / 云 KMS，把 JENKINS_HOME 的加密密钥
  （secrets/ 目录）单独保护：拿到它就能解出所有凭据
- 定期轮换，删除不用的凭据；Git 凭据用只读部署密钥而不是个人账号
```

### 6. 插件与版本

```bash
# 升级前看安全公告：Manage Jenkins > Plugins > Updates 里有 security warning 标记
# 也可以用 CLI 批量查看
java -jar jenkins-cli.jar -s $J -auth admin:$TOKEN list-plugins | grep -i warning
```

```text
- 插件漏洞是 Jenkins 被入侵的主要入口，订 Jenkins 的安全公告邮件列表。
- 生产固定插件版本（plugins.txt + 自定义镜像），升级走「测试环境灰度 → 生产」。
- 没用的插件直接卸载，减少攻击面与启动时间。
```

### 7. 审计与留痕

```bash
# 审计日志（Audit Trail 插件）记录谁在什么时候改了什么
# 备用方案：把 JENKINS_HOME/config.xml、jobs/*/config.xml 纳入 Git 定期快照，diff 出改动
```

```text
最低成本的审计做法
1. JENKINS_HOME 每天 tar 一份留 30 天（见备份一节），出问题能对比配置差异
2. 关掉「允许用户自行注册」
3. 构建日志里不要打凭据（用 withCredentials 而不是明文 echo）
4. 关键操作（生产发布）留人工卡点 + 审批人白名单：input(submitter: 'release-manager')
```

## 备份、恢复与升级

### 需要备份什么

```text
$JENKINS_HOME 里真正重要的东西（合计通常 50-200MB）
- config.xml                     系统配置
- jobs/*/config.xml              任务定义（流水线脚本在 Git 里就没那么关键）
- users/、secrets/               用户与加密密钥（丢了凭据全部无法解密）
- credentials.xml                凭据（依赖 secrets/）
- plugins/、war/                 可重建：用 plugins.txt 重装即可，不必备份
- workspace/、jobs/*/builds/     构建产物与日志，视需要保留，通常不备份
```

### 备份脚本

```bash
# examples/backup-restore.sh 的核心逻辑
# 1) 先静默，避免备份过程中配置变化
curl -X POST -u admin:$TOKEN "$JENKINS_URL/quietDown"
# 2) 打 tar（排除可重建与体积大的目录）
tar -czf /data/backup/jenkins/jenkins-home-$(date +%Y%m%d-%H%M).tar.gz \
  -C /var/lib --exclude='jenkins/workspace' \
  --exclude='jenkins/jobs/*/workspace' --exclude='jenkins/jobs/*/builds' \
  --exclude='jenkins/plugins' --exclude='jenkins/war' --exclude='jenkins/logs' jenkins
# 3) 恢复
docker compose down
docker run --rm -v jenkins_home:/var/jenkins_home -v /data/backup/jenkins:/backup \
  alpine sh -c 'cd /var/jenkins_home && tar -xzf /backup/jenkins-home-YYYYmmdd-HHMM.tar.gz --strip-components=1'
docker compose up -d
# 4) 用插件重建插件集合
docker run --rm -v jenkins_home:/var/jenkins_home --entrypoint jenkins-plugin-cli \
  jenkins/jenkins:lts-jdk21 --plugin-file /usr/share/jenkins/ref/plugins.txt \
  --plugin-download-directory /var/jenkins_home/plugins
```

```text
备份的三条经验
1. 一定要真做过一次恢复演练。恢复失败的原因通常是权限（uid 不匹配）与插件版本。
2. secrets/ 目录必须跟 config.xml、credentials.xml 一起备份，只备份 config 会导致凭据全废。
3. 容器化后备份对象从「目录」变成「卷」，用 docker run --rm -v 卷:/data 的方式打包，
   别去宿主 /var/lib/docker/volumes 里直接读（权限与布局都不稳定）。
```

### 升级路径

```text
容器化升级（推荐）
1. docker pull jenkins/jenkins:lts-jdk21（或指定版本 2.580.1-lts-jdk21）
2. compose 里改 tag，down + up
3. 观察启动日志：插件不兼容会明确报 "Failed Loading plugin"
4. 插件按需升级：Manage Jenkins > Plugins > Updates，一次别升太多

裸机/包管理升级
1. 先备份 $JENKINS_HOME，再 apt-get install --only-upgrade jenkins 或替换 war
2. 回滚要连数据一起回：Jenkins 启动时会自动迁移 JENKINS_HOME 的格式，
   低版本读高版本数据会失败，所以「只回滚二进制」是不行的
```

```text
版本兼容铁律
- Jenkins 2.580.1 需要 Java 17 及以上（本机实测用 21 正常）；
  升级 Jenkins 前先确认宿主/容器的 JDK 满足要求。
- 插件要求的 Jenkins 最低版本写在插件元数据 requiredCore 里，
  升级 Jenkins 时插件可能需要同步升级（或反过来，插件太新会要求更高的 Jenkins）。
- 跨大版本升级（例如 2.4xx → 2.5xx）务必在克隆出来的 JENKINS_HOME 上先演练。
```

## 监控、容量与性能

### 该看哪些指标

| 指标 | 位置 | 经验阈值 |
| --- | --- | --- |
| 构建队列长度 | `/queue/api/json`、首页构建队列 | 长期 > 0 说明执行器不够 |
| 执行器占用率 | Manage Jenkins > Nodes | 长期 > 80% 要扩容 |
| 控制器 JVM 堆使用 | Manage Jenkins > System Information、`/metrics` | 老年代长期 > 80% 要调 `-Xmx` |
| 构建时长趋势 | 任务的构建时间趋势图 | 突然变长先看 agent 资源与依赖下载 |
| 磁盘占用 | `du -sh $JENKINS_HOME/{jobs,workspace,logs}` | workspace 与 builds 是主要增长点 |
| agent 在线率 | `/computer/api/json` | 掉线率高的 agent 查内存与网络 |

```bash
# 用 API 采集队列与节点状态（可直接喂给 Prometheus textfile collector）
curl -s -u admin:$TOKEN "$J/api/json?tree=jobs[name,color]" | python3 -m json.tool | head -20
curl -s -u admin:$TOKEN "$J/queue/api/json?tree=items[id,task[name],why]"
curl -s -u admin:$TOKEN "$J/computer/api/json?tree=computer[displayName,offline,numExecutors,busyExecutors]"
```

```text
Prometheus 方案：装 Prometheus Metrics 插件，暴露 /prometheus 端点，
指标前缀默认 jenkins_，常看的几个：
  jenkins_queue_size_value              队列长度
  jenkins_executor_count_value          执行器总数
  jenkins_node_offline_value            离线节点数
  jenkins_builds_duration_milliseconds   构建耗时
```

### 磁盘与清理策略

```groovy
// 任务级保留策略（写在 Jenkinsfile options 里）
options {
    buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '5', daysToKeepStr: '30'))
}
```

```bash
# 定期清理孤儿工作区（任务删了但 workspace 还在）
docker exec jenkins find /var/jenkins_home/workspace -maxdepth 1 -type d -mtime +30 -print
# 清理旧构建日志（谨慎：会丢历史）
docker exec jenkins du -sh /var/jenkins_home/jobs/*/builds | sort -h | tail -10
```

```text
容量经验值（中小团队）
- 控制器：2 核 4G 起步，堆 2G；构建多则堆 4G 以上
- JENKINS_HOME：每个任务的 builds 目录按 10MB/构建估算，
  一个日构建任务保留 30 次约 300MB；产物归档会显著放大这个数字
- 构建机：按「一个构建吃满多少核」倒推执行器数量，别用默认值
```

## 常见问题与排错

### 启动与访问

```text
问题：容器起来但页面一直 503 / 转圈
排查：docker logs <容器> | tail -50；看到 "Jenkins is fully up and running" 才是真就绪，
      插件多时这个过程可以到 1-3 分钟，健康检查的 start_period 要给够。
问题：登录后提示「反向代理设置有误」
原因：Jenkins 认为自己的 URL 与实际访问地址不一致。
解法：Manage Jenkins > System > Jenkins URL 填真实地址（含 https 与端口），
      或设 JAVA_OPTS=-Djenkins.model.Jenkins.location=https://ci.example.com/
问题：时区不对，定时任务在错误的点跑
解法：容器加 -e TZ=Asia/Shanghai -Duser.timezone=Asia/Shanghai；Jenkins 用的是 JVM 时区。
```

### 插件安装

```text
问题：jenkins-plugin-cli 卡住不结束 / 日志反复重试某个镜像
原因（本机实测）：插件管理器在下载失败后会回退到 update-center.json 里的 mirrors 列表，
      其中包含速度极慢或不通的镜像（如 mirror.twds.com.tw、archives.jenkins.io），
      单个包重试超时会把整个安装拖住。
解法（本机验证有效）：
  1) 把官方 update-center.json 下载到本地（它是 JSONP 包裹的，plugin-cli 能直接读）
     curl -sL -o uc.json https://updates.jenkins.io/update-center.json
  2) 起一个本地静态服务 python3 -m http.server 8899 --bind 127.0.0.1
  3) 用 --network host 的容器安装，更新中心指向本地文件，下载地址指向官方 CDN：
     docker run --rm --network host -v jenkins_home:/var/jenkins_home \
       --entrypoint jenkins-plugin-cli jenkins/jenkins:lts-jdk21 \
       --jenkins-update-center http://127.0.0.1:8899/uc.json \
       --jenkins-update-center-download-url https://updates.jenkins.io/download/plugins \
       --latest false --plugins git workflow-aggregator junit \
       --plugin-download-directory /var/jenkins_home/plugins
问题：装完重启后插件没生效 / 报 "Failed Inspecting plugin xxx.jpi"
原因：jpi 文件没下完（中断的下载会留下半个 zip）。
排查：unzip -t /var/jenkins_home/plugins/xxx.jpi 会报 "unexpected end of central directory"。
解法：删掉坏文件重下；批量校验：
     for f in /var/jenkins_home/plugins/*.jpi; do unzip -t "$f" >/dev/null 2>&1 || echo "坏: $f"; done
问题：镜像站返回 403（"抱歉，您目前无法访问此页面"）
原因（本机实测）：同一个 URL，容器用默认 bridge 网络返回 403，--network host 返回 200，
      镜像站对出口有访问控制/限流。
解法：装插件这一步用 --network host 跑一次性容器，或直接走官方 CDN。
```

### 构建与流水线

```text
问题：一直停 "Waiting for next available executor"
排查：节点是否在线（/computer/api/json）→ 标签是否匹配（任务的 label 与节点的 label）
      → 执行器是否被长任务占满 → 是否有 lock 步骤占着全局锁。
问题：docker: command not found
原因：Jenkins 官方镜像里没有 docker CLI。
解法：构建镜像时 apt-get install docker-ce-cli，或运行时挂宿主二进制
      -v /usr/bin/docker:/usr/bin/docker:ro -v /var/run/docker.sock:/var/run/docker.sock。
问题：permission denied while trying to connect to the Docker daemon socket
原因：容器里的 jenkins 用户不在宿主 docker 组。
解法：起容器时 --group-add $(stat -c '%g' /var/run/docker.sock)（本机该 gid 为 984）。
问题：withCredentials 注入的变量在 sh 里是空的
原因：用了双引号字符串（Groovy 插值发生在 Jenkins 侧，此时变量还不存在）。
解法：把 shell 脚本写成单引号 '''...'''（Groovy 字符串不插值，交给 shell 展开）。
问题：Pipeline 报 "Scripts not permitted to use method"
解法：管理员在 Manage Jenkins > In-process Script Approval 批准；
      更推荐改用插件提供的步骤而不是直接调用内部 API。
问题：maven 容器每次构建都重新下载依赖
原因：docker agent 的容器是临时的，~/.m2 不持久。
解法：args '-v $HOME/.m2:/root/.m2'（$HOME 在 Jenkins 容器里是 /var/jenkins_home，落在数据卷上），
      并把 settings.xml 放到 $HOME/.m2/settings.xml 指向国内镜像。
问题：npm ci 失败或极慢
解法：把 .npmrc 的 registry 改成 https://registry.npmmirror.com；
      有 lock 文件用 npm ci，没有则 npm install（本机实测 Vite 8 项目 npm install 33 秒装完 62 个包）。
问题：测试失败但流水线继续部署
原因：junit 步骤把构建标记为 UNSTABLE 而不是 FAILURE。
解法：部署 stage 加 when { expression { currentBuild.currentResult == 'SUCCESS' } }，
      或用 catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') 包住测试阶段。
问题：工作区文件属主是 root，cleanWs 报权限错误
解法：docker agent 加 args '-u $(id -u):$(id -g)'；或构建后 chown -R jenkins:jenkins，
      或在 post 里用 docker 以 root 清目录。
问题：构建日志时间与本地时间差 8 小时
解法：控制器设 TZ=Asia/Shanghai 与 -Duser.timezone=Asia/Shanghai；容器内 /etc/localtime 也一起改。
```

### 资源与稳定性

```text
问题：控制器越来越慢、频繁 Full GC
排查：Manage Jenkins > System Information 看堆使用；
      常见原因是构建日志堆在内存、任务太多、插件太杂。
解法：调大 -Xmx（4G 起）、把构建挪到 agent、清理不用的任务与插件、
      打开 "Disable deferred wipeout" 之外的项目级清理策略。
问题：构建日志"丢失"或页面打开很慢
原因：单次构建日志过大（几百 MB 的日志在 UI 上渲染会卡死浏览器）。
解法：脚本里做输出裁剪（grep/tail 后再输出），或用 Pipeline 的 logrotate / 外部归档。
问题：agent 经常掉线
排查：agent 容器日志；控制器 50000 端口连通性；agent 机器内存与 swap；
      是否被同一节点上的重构建拖死。
```

## 最佳实践

1. 流水线代码化：Jenkinsfile 入库，任务一律用「Pipeline script from SCM」，UI 上不改流程。
2. 控制器只调度不构建：内置节点执行器设 0，构建跑 agent 或容器。
3. 构建环境容器化：maven/node/python 用 docker agent 现拉，节点无需预装工具链。
4. 依赖做缓存：maven `~/.m2`、npm cache、Gradle `~/.gradle` 挂卷，避免每次重下。
5. 凭据只引用不暴露：`withCredentials` + 单引号 shell 脚本，敏感值不打日志。
6. 测试结果进 Jenkins：`junit` 收集 surefire/jest 报告，让失败趋势可见。
7. 制品归档 + 指纹：`archiveArtifacts fingerprint: true`，产物可追溯、可复用。
8. 保留策略写进流水线：`buildDiscarder`，防止磁盘被历史构建吃光。
9. 部署要能回滚：镜像打版本 tag（`app:1.0.0-<git short sha>`），回滚 = 重新 run 旧 tag。
10. 冒烟测试作为发布门禁：部署后立刻 curl 健康检查与关键接口，失败就判发布失败。
11. 关键环境加人工卡点：`input submitter: 'release-manager'`，并记录审批人。
12. 配置即代码：JCasC 管系统配置、Job DSL 管任务生成，新环境一条命令铺好。
13. 备份 + 演练：定期备份 JENKINS_HOME 并真的做过一次恢复。
14. 插件克制：只装要用的，固定版本，升级前读 changelog 与安全公告。
15. 给任务起规范名字：`产品-模块-环境`，配合文件夹与视图，人多也不乱。

## 相关文档

- [[Kafka完整教程]] — 事件驱动链路里的消息中间件，CI/CD 之外的部署对象
- [[Docker完整知识教程]] — 容器基础，本教程大量依赖 docker 命令与套接字挂载
- [[Kubernetes完整知识教程]] — 动态 agent 与容器编排基础
- [[spring-boot-tika]] — Spring Boot 集成实践里的构建与打包方式
- [[11.7-保存与部署]] — 模型/服务的部署与制品管理思路（AI 与智能体全栈库）
- [[13.7-持久化与工程化]] — 工程化流水线中的数据校验与发布检查清单
- [[32.4-安全与隐私]] — 大数据平台的凭据与权限治理（可对照 Jenkins 授权模型）
