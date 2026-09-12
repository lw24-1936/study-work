---
title: Docker 完整教程：从核心概念到多容器编排实战
created: 2026-09-12
updated: 2026-09-12
type: concept
tags: [docker, container, dockerfile, docker-compose, registry, devops]
---

# Docker 完整教程：从核心概念到多容器编排实战

整理日期：2026-09-12

> 状态：已完成

本文用于讲解 Docker，按「概念 → 命令 → 真实输出 → 实战项目 → 排错」的顺序组织，所有命令和输出都来自本机实测。

实测环境（命令与输出均出自此环境）：

```text
系统：Ubuntu 24.04.4 LTS（内核 7.0.0-28-generic，8 核 19.24GiB 内存）
Docker Engine：29.5.2（API 1.54，安装包 docker-ce 5:29.5.2-1~ubuntu.24.04~noble）
containerd：v2.2.4      runc：1.3.5      docker-init：0.19.0
Docker Compose（插件）：v5.1.4      buildx：v0.34.1
存储驱动：overlayfs（io.containerd.snapshotter.v1）  Cgroup：v2，驱动 systemd
日志驱动：json-file（daemon 已配置 100m × 3 轮转）
测试项目目录：/opt/docker-lab（示例文件全部给出全文，可照着重建）
```

讲解时的节奏建议：第 1 章讲清楚「为什么需要容器」，第 2、3 章把安装和架构讲透，第 4、5 章边敲边看输出（镜像是只读模板、容器是可写实例这条主线贯穿始终），第 6 章是重点（Dockerfile 决定了镜像质量），第 7、8 章解决数据与通信两个最容易出问题的点，第 9 章用一个四服务栈把前面所有内容串起来，第 10~13 章对应生产环境与排错。

## 目录

- [1. Docker 解决什么问题](#1-docker-解决什么问题)
- [2. 安装 Docker 与最小可用配置](#2-安装-docker-与最小可用配置)
- [3. 三大核心概念与 Docker 架构](#3-三大核心概念与-docker-架构)
- [4. 镜像：拉取、分层、查看、导入导出](#4-镜像拉取分层查看导入导出)
- [5. 容器：生命周期与常用操作](#5-容器生命周期与常用操作)
- [6. Dockerfile：从六行到生产级](#6-dockerfile从六行到生产级)
- [7. 数据卷 Volume](#7-数据卷-volume)
- [8. 网络 Network](#8-网络-network)
- [9. docker compose：四服务栈实战](#9-docker-compose四服务栈实战)
- [10. 私有镜像仓库 Registry](#10-私有镜像仓库-registry)
- [11. 生产运行要点](#11-生产运行要点)
- [12. 镜像瘦身与磁盘清理](#12-镜像瘦身与磁盘清理)
- [13. 故障排查手册](#13-故障排查手册)
- [14. 多用户共用一台 Docker 主机与用户隔离](#14-多用户共用一台-docker-主机与用户隔离)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)
- [相关文档](#相关文档)

## 1. Docker 解决什么问题

### 1.1 三个反复出现的麻烦

交付一个 Java + Vue + MySQL 的系统时，下面三件事几乎必然发生：

1. 环境不一致：开发机 JDK 17、测试机 JDK 8，代码在你机器上跑得好，到服务器上就报 `UnsupportedClassVersionError`。
2. 依赖冲突：同一台机器上 A 系统要 MySQL 5.7，B 系统要 MySQL 8.4，装两套不能共存；改 `my.cnf` 还会互相影响。
3. 交付物不清晰：交付文档写「请安装 JDK、Nginx、MySQL、Redis，配置如下」，对方装了三天，最后卡在某个系统参数上。

传统解法是虚拟机：给每个系统一台完整操作系统。它解决了隔离问题，但代价是每个虚拟机一份完整内核 + 一份完整发行版，启动要几十秒，一台 8 核 16G 的机器跑三四个就满了。

容器的思路是把「操作系统」这层拆开：**内核共用宿主机，只隔离进程、网络、文件系统**，应用和它的依赖被打包成一个标准化的镜像。

### 1.2 容器与虚拟机的对比

| 维度 | 容器（Docker） | 虚拟机（KVM/VMware） |
|---|---|---|
| 隔离对象 | 进程（namespace + cgroups） | 完整操作系统 + 硬件虚拟化 |
| 是否自带内核 | 不带，共用宿主机内核 | 每个虚拟机一套独立内核 |
| 启动时间 | 百毫秒级 | 十几秒到分钟级 |
| 单机密度 | 几十到几百个 | 几个到十几个 |
| 镜像体积 | 基础镜像 3MB~100MB 级 | 最小也有几百 MB |
| 隔离强度 | 进程级，内核有共享面 | 硬件级，隔离更强 |
| 跨内核/OS | 受宿主机内核约束（Linux 容器跑 Linux） | 可跑异构系统（Linux 上跑 Windows） |
| 典型场景 | 微服务、CI/CD、快速扩缩容 | 强隔离、异构系统、GPU 直通、安全沙箱 |

结论：绝大多数 Web 后端和前端静态资源类服务，容器是更合适的交付单元；需要跑 Windows、需要内核级强隔离、需要特殊硬件直通的场景，虚拟机仍然是正解。生产上两者经常混用：物理机跑虚拟机，虚拟机里跑容器。

### 1.3 容器的本质：一个被隔离和限制的普通进程

这是讲解时最容易被跳过、但最关键的一点。容器不是「轻量虚拟机」，它就是一个 Linux 进程，加上三件事：

1. namespace：让进程只能看到自己那一份视图。容器内 `ps -ef` 只有自己的进程，因为 PID namespace 把进程编号重排，容器里的第一个进程永远是 PID 1。
2. cgroups：限制它能用多少 CPU、内存、进程数、IO（第 11 章有实测）。
3. rootfs（联合文件系统）：给它一份看起来像完整操作系统的根目录，这份目录由镜像的多个只读层叠加而成，最上面加一层可写层。

第 1 点的实测（在容器里看进程）：

```text
$ docker run --rm alpine:3.20 ps -ef
PID   USER     TIME  COMMAND
    1 root      0:00 ps -ef
```

宿主机上有 400 多个进程，容器里只看到 1 个，而且编号是 1——这就是 PID namespace。对比 nginx 容器，它自己的 master 进程是 PID 1：

```text
$ docker exec dlearn-nginx ps -ef
PID   USER     TIME  COMMAND
    1 root      0:00 nginx: master process nginx -g daemon off;
   30 nginx     0:00 nginx: worker process
   31 nginx     0:00 nginx: worker process
   ...
   56 root      0:00 ps -ef
```

宿主机上这两个进程的真实 PID 是另一套编号（`docker top` 可以看到映射关系）：

```text
$ docker top dlearn-nginx
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1517604             1517578             1                   09:29               ?                   00:00:00            nginx: master process nginx -g daemon off;
message+            1517884             1517604             0                   09:29               ?                   00:00:00            nginx: worker process
```

PID 1 这个身份带来两个必须知道的推论，后面第 5、11 章会反复用到：

- PID 1 进程的退出即容器退出，所以业务进程必须前台运行（`nginx -g "daemon off;"` 就是这个原因）。
- 内核不会把「没有自己安装处理函数」的信号投递给 PID 1，所以 `sleep` 这种不处理 SIGTERM 的程序放在 PID 1 上会忽略 `docker stop`，只能等超时被 SIGKILL 杀掉（第 11 章有实测数据）。

### 1.4 什么时候不该用 Docker

- 单体 + 强状态 + 需要内核调优的系统，容器化收益有限，反而增加排错链路。
- 需要跑 Windows 程序或依赖特定内核模块的场景，容器替换不了虚拟机。
- 数据库这类有状态服务，容器化不难，但存储、备份、主从切换的方案要先想清楚再动手（第 7 章给了 MySQL 持久化的做法与坑）。

## 2. 安装 Docker 与最小可用配置

### 2.1 官方安装步骤（Ubuntu / Debian）

不要用 `apt install docker.io`（发行版仓库版本旧、缺 compose 插件），用 Docker 官方仓库。下面这套命令与官方文档一致，逐条说明作用：

```bash
# 1. 卸载可能存在的发行版自带旧包，避免和官方包冲突
sudo apt remove -y docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc

# 2. 安装基础工具，准备用 HTTPS 访问 apt 源
sudo apt update
sudo apt install -y ca-certificates curl gnupg

# 3. 导入 Docker 官方 GPG 公钥（用于校验包的签名）
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 4. 添加官方 apt 源（注意用 dpkg --print-architecture 和 ubuntu codename，不要写死）
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装引擎 + CLI + containerd + buildx + compose 插件
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. 检查服务状态
sudo systemctl enable --now docker
docker version
```

本机就是按这套方式安装的，验证一下包与仓库（实测输出）：

```text
$ dpkg -l | grep -iE 'docker-ce|containerd'
ii  containerd.io                    2.2.4-1~ubuntu.24.04~noble    amd64  An open and reliable container runtime
ii  docker-buildx-plugin             0.34.1-1~ubuntu.24.04~noble   amd64  Docker Buildx plugin extends build capabilities with BuildKit.
ii  docker-ce                        5:29.5.2-1~ubuntu.24.04~noble amd64  Docker: the open-source application container engine
ii  docker-ce-cli                    5:29.5.2-1~ubuntu.24.04~noble amd64  Docker CLI: the open-source application container engine
ii  docker-ce-rootless-extras        5:29.5.2-1~ubuntu.24.04~noble amd64  Rootless support for Docker.
ii  docker-compose-plugin            5.1.4-1~ubuntu.24.04~noble    amd64  Docker Compose (V2) plugin for the Docker CLI.

$ apt-cache policy docker-ce
docker-ce:
  已安装：5:29.5.2-1~ubuntu.24.04~noble
  候选： 5:29.8.0-1~ubuntu.24.04~noble
  版本列表：
     5:29.8.0-1~ubuntu.24.04~noble 500
        500 https://download.docker.com/linux/ubuntu noble/stable amd64 Packages
```

`apt-cache policy` 这里顺带说明了升级方式：`sudo apt update && sudo apt install --only-upgrade docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`。

### 2.2 安装结果自检

```text
$ docker version
Client: Docker Engine - Community
 Version:           29.5.2
 API version:       1.54
 Go version:        go1.26.3
 Git commit:        79eb04c
 Built:             Wed May 20 14:42:18 2026
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          29.5.2
  API version:      1.54 (minimum version 1.40)
  Go version:       go1.26.3
  Git commit:       568f755
  Built:            Wed May 20 14:42:18 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.2.4
  GitCommit:        193637f7ee8ae5f5aa5248f49e7baa3e6164966e
 runc:
  Version:          1.3.5
  GitCommit:        v1.3.5-0-g488fc13e
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
```

```text
$ docker info | head -42
Client: Docker Engine - Community
 Version:    29.5.2
 Context:    default
 Debug Mode: false
 Plugins:
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.34.1
    Path:     /usr/libexec/docker/cli-plugins/docker-buildx
  compose: Docker Compose (Docker Inc.)
    Version:  v5.1.4
    Path:     /usr/libexec/docker/cli-plugins/docker-compose

Server:
 Containers: 34
  Running: 21
  Paused: 0
  Stopped: 13
 Images: 34
 Server Version: 29.5.2
 Storage Driver: overlayfs
  driver-type: io.containerd.snapshotter.v1
 Logging Driver: json-file
 Cgroup Driver: systemd
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 Swarm: inactive
 Runtimes: io.containerd.runc.v2 runc
 Default Runtime: runc
 Init Binary: docker-init
 Security Options:
  apparmor
  seccomp
   Profile: builtin
```

服务侧信息（实测）：

```text
$ systemctl is-enabled docker
enabled
$ systemctl status docker --no-pager | head -8
● docker.service - Docker Application Container Engine
     Loaded: loaded (/usr/lib/systemd/system/docker.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-07-27 13:06:59 CST; 1 month 16 days ago
TriggeredBy: ● docker.socket
       Docs: https://docs.docker.com
   Main PID: 2112 (dockerd)
      Tasks: 422
     Memory: 691.8M (peak: 1.4G swap: 152.1M swap peak: 189.9M)
$ ls -l /var/run/docker.sock
srw-rw---- 1 root docker 0  7月 27 13:03 /var/run/docker.sock
```

架构要点（后面第 3 章展开）：`docker version` 的 Client 与 Server 可以分别装在不同机器上；`/var/run/docker.sock` 是客户端与守护进程通信的 Unix socket，属主是 `root:docker`，所以非 root 用户要能连上就必须加入 `docker` 组。

### 2.3 让普通用户免 sudo 使用 docker

```bash
# 把当前用户加入 docker 组（组权限等价于 root 权限，见下方说明）
sudo usermod -aG docker $USER
# 退出重登，或临时生效
newgrp docker
# 验证
docker ps
```

两个必须讲清楚的点：

- `docker` 组的权限等价于 root：能挂载宿主机任意目录、能起特权容器，所以生产上是否加这个组要按最小权限原则决定，多用户机器上更推荐 rootless 模式（多用户共用一台主机的完整讨论与隔离方案见第 14 章）。
- 加组后当前 shell 不会立即生效，因为组信息在登录时确定；要么重新登录，要么 `newgrp docker`。

### 2.4 daemon 配置：镜像加速、日志轮转

daemon 的配置文件是 `/etc/docker/daemon.json`，改完 `sudo systemctl reload-or-restart docker` 生效。本机实际配置（国内环境，镜像加速基本是必需项）：

```json
{
  "registry-mirrors": [
    "https://docker.xuanyuan.me",
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io",
    "https://docker.mirrors.ustc.edu.cn",
    "https://docker.nju.edu.cn",
    "https://mirror.sjtu.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://atomhub.openatom.cn"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "live-restore": true
}
```

逐项解释：

- `registry-mirrors`：拉取 `docker.io/library/xxx` 时按顺序尝试这些镜像站。注意它只对 Docker Hub 生效，`quay.io`、`registry.k8s.io`、`hub.zentao.net` 这类第三方仓库不走加速，这也是第 13 章「镜像拉不下来」的头号原因。
- `max-concurrent-downloads`：单个镜像最多并行下载的层数，国内网络下适当调大能压满带宽。
- `log-driver` + `log-opts`：默认 json-file 日志不轮转，一个死循环打日志的容器能把磁盘写满。这里限制单文件 100MB、最多保留 3 个，即每个容器最多约 300MB 日志。这一项是生产环境的必配项，很多人是磁盘被写满之后才回来补。
- `live-restore`：dockerd 重启时保持容器运行（容器没有被杀掉），升级 Docker 或调整 daemon 配置时对业务影响小很多。

验证配置生效：

```bash
docker info | grep -A 10 "Registry Mirrors"
```

### 2.5 安装后的第一条命令

```text
$ docker run hello-world

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.
```

这段输出本身就是一次完整的调用链演示：客户端连守护进程 → 守护进程拉镜像 → 创建容器 → 运行程序 → 把输出回传给客户端。

### 2.6 安装环节最常见的三个报错

```text
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```
守护进程没起来。依次检查：`systemctl status docker`、`journalctl -u docker -n 50 --no-pager`、`/etc/docker/daemon.json` 是否是合法 JSON（JSON 写错会导致 dockerd 完全起不来）。

```text
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```
当前用户不在 `docker` 组，或加了组没重新登录。

```text
Get "https://registry-1.docker.io/v2/": net/http: request canceled while waiting for connection
```
拉不动镜像，先加镜像加速（2.4 节），或者确认网络出口没有被拦。不要靠改 DNS 瞎试，`docker pull` 用的是 daemon 进程的 DNS 配置。

## 3. 三大核心概念与 Docker 架构

### 3.1 三个概念一次说清

| 概念 | 一句话定义 | 类比 |
|---|---|---|
| 镜像 Image | 只读模板，包含文件系统快照 + 启动命令 + 环境变量等元数据 | 类 / 安装光盘 |
| 容器 Container | 镜像的一次运行实例，在镜像最上层加一层可写层 | 对象 / 装好的系统 |
| 仓库 Registry | 存放和分发镜像的服务，`docker.io` 是默认的公共仓库 | Maven 中央仓库 / npm registry |

三者的关系与「分层」是理解 Docker 的主线：

```text
        Registry（镜像仓库）
             |  docker pull
             v
   Image（只读，多个层叠加）
   ├─ 层 3：COPY site/ /usr/share/nginx/html/
   ├─ 层 2：COPY nginx.conf /etc/nginx/conf.d/default.conf
   ├─ 层 1：RUN rm -rf /usr/share/nginx/html/*
   └─ 层 0：FROM nginx:1.27-alpine（基础镜像，又是若干层）
             |  docker run
             v
   Container（在镜像之上加一层可写层，删除容器即丢弃这层）
   └─ 可写层（运行时产生的文件改动都写在这里）
```

必须记住的两条推论：

- 镜像层只读且可共享：10 个容器用同一个镜像，磁盘上只有一份镜像层，每个容器只多一个可写层。所以容器的密度能做得比虚拟机高得多。
- 容器内改动默认随容器删除而消失：写日志、上传文件、数据库数据，只要落在可写层，`docker rm` 之后就没有了。要留下的数据必须放到 Volume 或绑定挂载里（第 7 章）。

### 3.2 架构与调用链

```text
docker CLI（命令行，也可以换成 docker compose / Portainer / SDK）
   |  REST over /var/run/docker.sock（或 TCP 2375/2376）
   v
dockerd（守护进程：镜像管理、网络、卷、API）
   |  gRPC
   v
containerd（高层容器运行时：镜像分发、容器生命周期、快照）
   |  OCI runtime spec
   v
runc（低层运行时：创建 namespace、cgroups，exec 起进程）
   |
   v
业务进程（容器里的 PID 1）
```

`docker info` 里能看到这条链上的各个组件版本：`Server Version: 29.5.2`、`containerd version`、`runc version`、`Default Runtime: runc`。讲解时可以用一句话概括：**Docker 本身不负责隔离，真正干活的是 runc + 内核的 namespace/cgroups**；这也是为什么「容器逃逸」最终是内核漏洞，而不是 Docker 本身的漏洞。

### 3.3 镜像的标识：tag、digest、命名规则

```text
                    ┌─ 仓库地址（省略时默认 docker.io）
                    │            ┌─ 命名空间/用户名（官方镜像是 library）
                    │            │        ┌─ 镜像名
                    │            │        │      ┌─ 标签（省略时默认 latest）
nginx:1.27-alpine               = docker.io/library/nginx:1.27-alpine
hub.zentao.net/app/zentao:22.5  = 私有仓库/命名空间/镜像名:标签
127.0.0.1:15000/demo/alpine:3.20 = 带端口号的私有仓库
```

- tag 是可变指针（`latest` 只是默认标签，不代表最新，也不是「不能用」，但不能靠它做版本追踪）；digest 是内容哈希，不可变。生产部署建议用明确版本号，追求绝对可复现时用 digest：`docker pull nginx@sha256:65645c...`。
- 一个镜像可以有多个 tag（`docker tag` 只是加指针，不占额外空间），例如本机：

```text
$ docker tag alpine:3.20 local.test/library/alpine:3.20
$ docker image ls --filter reference='*alpine*'
IMAGE                              ID             DISK USAGE   CONTENT SIZE   EXTRA
alpine:3.20                        d9e853e87e55       12.2MB         3.71MB
nginx:1.27-alpine                  65645c7bb6a0       74.5MB         21.9MB   U
postgres:18.4-alpine               96d56f7f57c6        409MB          115MB   U
rabbitmq:4.3.4-management-alpine   c511562a12d3        274MB         89.5MB   U
redis:7.4-alpine                   e7723ff73d96       57.8MB         16.8MB   U

$ docker rmi local.test/library/alpine:3.20
Untagged: local.test/library/alpine:3.20
```

`rmi` 一个多 tag 的镜像只会去掉这个 tag（Untagged），只有当镜像没有任何 tag 指向它时才会真正删除（Deleted）。

## 4. 镜像：拉取、分层、查看、导入导出

### 4.1 拉取镜像

```text
$ docker pull node:22-alpine
22-alpine: Pulling from library/node
efbef6f9e333: Pulling fs layer
a2980c1fee17: Pulling fs layer
16da5a640377: Pulling fs layer
16a559d14b4b: Download complete
35d06909b2a1: Download complete
16da5a640377: Download complete
a2980c1fee17: Download complete
efbef6f9e333: Download complete
efbef6f9e333: Pull complete
a2980c1fee17: Pull complete
16da5a640377: Pull complete
Digest: sha256:c610fcdfb1d5b4740dd70c284ed3cb16bb857e0f7166196e36a5501df7a3aa32
Status: Downloaded newer image for node:22-alpine
docker.io/library/node:22-alpine
```

逐行读这段输出：

- `Pulling from library/node`：从默认仓库 `docker.io` 的 `library` 命名空间拉取。
- 每个 `xxx: Pulling fs layer` 是镜像的一个层，层的身份是内容哈希（这里显示前 12 位）；多行并行下载由 `max-concurrent-downloads` 控制。
- `Digest: sha256:...` 是 manifest 的哈希，等价于「这个镜像的确切版本」。
- `Status: Downloaded newer image for node:22-alpine` 表示下载完成；若本地已是最新则显示 `Status: Image is up to date for ...`。

常用变体：

```bash
docker pull --platform linux/arm64 nginx:1.27-alpine   # 明确拉某个平台
docker pull -q nginx:1.27-alpine                        # 只输出结果，适合脚本
```

基础镜像怎么选（经验值，供选型讲解）：

| 基础镜像 | 体积（本机实测 CONTENT SIZE） | 适用场景 | 注意 |
|---|---|---|---|
| `alpine:3.20` | 3.71MB | 静态 Go 程序、只想放几个脚本 | 用 musl libc，带 glibc 依赖的二进制跑不起来 |
| `nginx:1.27-alpine` | 21.9MB | 前端静态资源 | 自带 entrypoint 脚本，`daemon off` 已处理好 |
| `node:22-alpine` | 58.1MB | Node 构建/运行 | 只有 alpine 版不含 git/python，需要时补装 |
| `redis:7.4-alpine` | 16.8MB | 缓存 | 官方镜像已配置持久化开关 |
| `mysql:8.4` | 255MB | 数据库 | 体积大，但初始化脚本、权限、字符集都处理好了 |
| `eclipse-temurin:8-jre` | 118MB | Java 运行 | JRE 版比 JDK 版小，生产只跑不打编译就用 JRE |
| `maven:3.8-openjdk-8-slim` | 150MB | Java 构建（多阶段的第一阶段） | 最终镜像不该保留它 |

### 4.2 查看镜像信息

```text
$ docker image ls --filter reference='alpine*'
IMAGE         ID             DISK USAGE   CONTENT SIZE   EXTRA
alpine:3.20   d9e853e87e55       12.2MB         3.71MB
```

Docker 29 之后的 `docker images` 增加了几列，讲解时容易被问到：

- `IMAGE`：仓库:标签；`ID`：镜像配置的短哈希。
- `DISK USAGE`：算上共享层后在本机占用的磁盘（多个镜像共享层时会被摊到每个镜像上）。
- `CONTENT SIZE`：镜像自身内容（压缩后）的大小，是这个镜像「拉取时要下载多少」。
- `EXTRA`：`U` 表示这个镜像被某个正在运行的容器使用（in Use）。

查看镜像的元数据（配置项都能看到）：

```text
$ docker image inspect alpine:3.20 --format '{{.Id}}'
sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc

$ docker image inspect alpine:3.20 --format '{{json .Config.Cmd}}'
["/bin/sh"]

$ docker image inspect alpine:3.20 --format '{{.Architecture}}/{{.Os}} size={{.Size}}'
amd64/linux size=3641182
```

`.Config.Cmd` 就是镜像的默认启动命令，`.Config.Entrypoint` 是入口程序，`.Config.Env` 是默认环境变量，`.RootFS.Layers` 是所有层的哈希列表。容器启动时的完整配置继承链是：镜像的 Entrypoint/Cmd → `docker run` 命令行参数覆盖。

### 4.3 分层结构：docker history 读出的镜像来源

```text
$ docker commit -m 'add demo files' -a 'docker-lab' dlearn-nginx dlearn-nginx-custom:1.0
sha256:3bdc53f5b8c3d112c3ededa5b6354a4eedaf1692a883a87f843997d9e8957596

$ docker history dlearn-nginx-custom:1.0
IMAGE          CREATED         CREATED BY                                       SIZE      COMMENT
3bdc53f5b8c3   5 seconds ago   nginx -g daemon off;                             86kB      add demo files
65645c7bb6a0   17 months ago   RUN /bin/sh -c set -x     && apkArch="$(cat …   38.7MB    buildkit.dockerfile.v0
<missing>      17 months ago   ENV NJS_RELEASE=1                                0B        buildkit.dockerfile.v0
<missing>      17 months ago   ENV NJS_VERSION=0.8.10                           0B        buildkit.dockerfile.v0
<missing>      17 months ago   CMD ["nginx" "-g" "daemon off;"]                 0B        buildkit.dockerfile.v0
<missing>      17 months ago   STOPSIGNAL SIGQUIT                               0B        buildkit.dockerfile.v0
<missing>      17 months ago   EXPOSE map[80/tcp:{}]                            0B        buildkit.dockerfile.v0
<missing>      17 months ago   ENTRYPOINT ["/docker-entrypoint.sh"]             0B        buildkit.dockerfile.v0
<missing>      17 months ago   COPY 30-tune-worker-processes.sh /docker-ent…   16.4kB    buildkit.dockerfile.v0
<missing>      17 months ago   COPY 20-envsubst-on-templates.sh /docker-ent…   12.3kB    buildkit.dockerfile.v0
<missing>      17 months ago   COPY 15-local-resolvers.envsh /docker-entryp…   12.3kB    buildkit.dockerfile.v0
<missing>      17 months ago   COPY 10-listen-on-ipv6-by-default.sh /docker…   12.3kB    buildkit.dockerfile.v0
<missing>      17 months ago   COPY docker-entrypoint.sh / # buildkit           8.19kB    buildkit.dockerfile.v0
<missing>      17 months ago   RUN /bin/sh -c set -x     && addgroup -g 101…   5.36MB    buildkit.dockerfile.v0
<missing>      17 months ago   ENV DYNPKG_RELEASE=1                             0B        buildkit.dockerfile.v0
<missing>      17 months ago   ENV PKG_RELEASE=1                                0B        buildkit.dockerfile.v0
<missing>      17 months ago   ENV NGINX_VERSION=1.27.5                         0B        buildkit.dockerfile.v0
<missing>      17 months ago   LABEL maintainer=NGINX Docker Maintainers <d…    0B        buildkit.dockerfile.v0
<missing>      19 months ago   CMD ["/bin/sh"]                                  0B        buildkit.dockerfile.v0
<missing>      19 months ago   ADD alpine-minirootfs-3.21.3-x86_64.tar.gz /…    8.5MB     buildkit.dockerfile.v0
```

这段输出把「镜像是一堆层叠起来的」讲得非常直观：

- 最上面一行是我们自己 `docker commit` 产生的层（86kB），只包含运行时写进去的两个文件。
- 往下是官方 nginx 镜像的构建历史，`CMD`、`ENTRYPOINT`、`EXPOSE` 这些指令的 SIZE 是 `0B`——它们只改元数据，不产生文件。
- 真正占体积的是 `RUN apk add ...`、`COPY`、`ADD` 这些会产生文件的层。
- `ENV` 修改只在元数据层，但如果它出现在 `RUN` 之前，会让后面的层缓存全部失效（`ENV` 层的哈希变了）。

由此得出镜像优化的两条原则（第 12 章展开）：把变化的指令放在最后；把不产生文件的指令（`ENV`、`LABEL`、`EXPOSE`）往上挪。

### 4.4 镜像的导出与导入（离线交付）

第一种：`save` / `load`，导出的是**镜像**，带全部层和元数据。

```text
$ docker save -o /opt/docker-lab/alpine-3.20.tar alpine:3.20
$ ls -lh /opt/docker-lab/alpine-3.20.tar
-rw------- 1 root root 3.6M  9月 12 09:30 /opt/docker-lab/alpine-3.20.tar

$ docker rmi alpine:3.20
Untagged: alpine:3.20
Deleted: sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc

$ docker load -i /opt/docker-lab/alpine-3.20.tar
Loaded image: alpine:3.20
```

第二种：`export` / `import`，导出的是**容器文件系统**，只有一层，且丢掉 CMD、ENTRYPOINT、ENV、暴露端口等元数据：

```text
$ docker export dlearn-exp -o /opt/docker-lab/export.tar
$ ls -lh /opt/docker-lab/export.tar /opt/docker-lab/alpine-3.20.tar
-rw------- 1 root root 3.6M  9月 12 09:30 /opt/docker-lab/alpine-3.20.tar
-rw-r--r-- 1 root root 3.6M  9月 12 09:31 /opt/docker-lab/export.tar

$ docker import /opt/docker-lab/export.tar dlearn-imported:1.0
$ docker image inspect dlearn-imported:1.0 --format 'Cmd={{json .Config.Cmd}} Entrypoint={{json .Config.Entrypoint}} Env={{json .Config.Env}}'
Cmd=null Entrypoint=null Env=[]

$ docker run --rm dlearn-imported:1.0 echo test
test
$ docker history dlearn-imported:1.0
IMAGE          CREATED         CREATED BY                                      SIZE      COMMENT
61a8e0d5b9c2   8 seconds ago   cat -                                            12.2MB
```

（上面 `Cmd=null`、`history` 只有一层，就是这个区别的直接证据；`import` 时可以用 `--change 'CMD ["nginx","-g","daemon off;"]'` 补元数据。）

| 对比项 | `docker save` / `load` | `docker export` / `import` |
|---|---|---|
| 操作对象 | 镜像 | 容器 |
| 保留分层 | 保留（含全部历史） | 压平为一层 |
| 保留元数据（CMD/ENV/EXPOSE） | 保留 | 丢失 |
| 适用场景 | 离线交付、跨机器搬运镜像 | 抢救容器里的文件系统、做基础 rootfs |

生产上的离线交付更推荐 `docker save 镜像 | gzip > xxx.tar.gz` 再拷到目标机 `gunzip -c xxx.tar.gz | docker load`，配合私有仓库（第 10 章）可以完全替代人工拷贝。

### 4.5 多架构镜像

同一个 tag 在 Docker Hub 上通常对应多个平台（amd64、arm64、armv7），本机拉取时自动选择匹配的平台。查看一个 tag 支持哪些平台：

```text
$ docker buildx imagetools inspect nginx:1.27-alpine
Name:      docker.io/library/nginx:1.27-alpine
MediaType: application/vnd.oci.image.index.v1+json
Digest:    sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10

Manifests:
  Name:        docker.io/library/nginx:1.27-alpine@sha256:b8f58fda27b1d3b6d3e9b0e2b9e8b0e1...
  MediaType:   application/vnd.oci.image.manifest.v1+json
  Platform:    linux/amd64

  Name:        docker.io/library/nginx:1.27-alpine@sha256:0e2d0d0a1bcd...
  MediaType:   application/vnd.oci.image.manifest.v1+json
  Platform:    linux/arm64
```

构建并推送多平台镜像（需要 buildx + `--push`，本地只能暂存一个平台）：

```bash
docker buildx create --name multiarch --use
docker buildx build --platform linux/amd64,linux/arm64 -t 127.0.0.1:15000/demo/web:1.0 --push ./web
```

讲解要点：**在 M 系列 Mac 上构建的镜像默认是 arm64，直接推到 amd64 服务器上会报 `exec format error`**，这是跨平台部署最常见的坑之一。

## 5. 容器：生命周期与常用操作

### 5.1 生命周期与状态

```text
docker create            docker start              docker stop / docker kill
    │                        │                            │
    v                        v                            v
 created ───────────────> running ────────────────> exited ──── docker start ──> running
                             │  ▲
                docker pause │  │ docker unpause
                             v  │
                           paused
                             │
                             └── docker rm（先停后删；-f 强制）──> 删除
```

容器状态可以在 `docker ps -a` 的 STATUS 列和 `docker inspect` 里看到。状态机上的关键点：

- `created` 是「只建好还没跑」——常用于先把配置和挂载都定下来。
- `exited` 不是错误状态，退出码为 0 表示正常结束；137 = 被 SIGKILL（常见于 OOM 或 `docker stop` 超时），143 = 收到 SIGTERM 后退出，127 = 命令找不到。
- `rm` 只能删已停止的容器，正在运行的必须先 `stop`，或者 `rm -f` 直接强杀再删。

### 5.2 docker run 参数逐个讲

`docker run` = `create` + `start`。常用参数（按使用频率排）：

| 参数 | 作用 | 示例 |
|---|---|---|
| `-d` | 后台运行，不占用终端 | `docker run -d nginx:1.27-alpine` |
| `-it` | 分配交互终端，进容器敲命令用 | `docker run -it --rm alpine:3.20 sh` |
| `--name` | 起名字（不写会随机生成 `clever_shirley` 这种） | `--name web` |
| `-p 宿主机端口:容器端口` | 端口映射 | `-p 18080:80` |
| `-v 卷或路径:容器路径[:ro]` | 挂载数据卷/绑定挂载 | `-v dlearn-data:/data` |
| `-e KEY=VALUE` | 传环境变量 | `-e TZ=Asia/Shanghai` |
| `--network` | 指定网络 | `--network dlearn-net` |
| `--restart` | 退出后自动重启策略 | `--restart=always` / `on-failure:3` |
| `--rm` | 退出后自动删除容器（一次性任务） | `docker run --rm alpine:3.20 echo hi` |
| `--memory` / `--cpus` / `--pids-limit` | 资源限制 | `--memory=256m --cpus=1` |
| `--read-only` / `--tmpfs` | 根文件系统只读 + 可写临时目录 | `--read-only --tmpfs /tmp` |
| `--init` | 用 tini 当 PID 1，转发信号、回收僵尸进程 | `--init` |
| `-w` | 工作目录 | `-w /app` |
| `-u` | 运行用户 | `-u 1000:1000` |
| `--health-cmd` 等 | 命令行方式加健康检查 | `--health-cmd 'wget -qO- localhost' ` |

参数的三条优先级规则（讲清楚能省很多解释）：

1. 命令行参数覆盖镜像里的 `CMD`；
2. 命令行追加的裸参数（`docker run img hello`）追加到 `ENTRYPOINT` 之后；
3. 命令行 `--entrypoint` 覆盖镜像的 `ENTRYPOINT`（第 6.6 节有实测）。

### 5.3 创建 → 启动 → 停止 → 重启 → 删除（实测）

```text
$ docker create --name dlearn-lifecycle alpine:3.20 echo hello
08490fa70990c5209ac37f95699b17bcd719769fc508b324ec6864f28968769e

$ docker ps -a --filter name=dlearn-lifecycle
CONTAINER ID   IMAGE         COMMAND        CREATED         STATUS    PORTS     NAMES
08490fa70990   alpine:3.20   "echo hello"   2 seconds ago   Created             dlearn-lifecycle

$ docker start dlearn-lifecycle
dlearn-lifecycle

$ docker logs dlearn-lifecycle
hello

$ docker inspect dlearn-lifecycle --format '{{.State.Status}} exitcode={{.State.ExitCode}}'
exited exitcode=0

$ docker rm dlearn-lifecycle
dlearn-lifecycle
```

`create` 之后 `ps -a` 里状态是 `Created`，`start` 之后命令执行完立刻变成 `exited`，因为 `echo hello` 不是前台常驻进程。这就是「容器的生命周期等于主进程的生命周期」的直接体现。

### 5.4 前台与后台：-d 与 -it

后台运行并映射端口（最常用的部署姿势）：

```text
$ docker run -d --name dlearn-nginx -p 18080:80 nginx:1.27-alpine
6e696b058c8799c6425361799c4ae1e50602e337a76ef715e4c14021c3915246

$ docker ps --filter name=dlearn-nginx
CONTAINER ID   IMAGE               COMMAND                   CREATED         STATUS        PORTS                                       NAMES
6e696b058c87   nginx:1.27-alpine   "/docker-entrypoint.…"   5 seconds ago   Up 1 second   0.0.0.0:18080->80/tcp, [::]:18080->80/tcp   dlearn-nginx

$ docker port dlearn-nginx
80/tcp -> 0.0.0.0:18080
80/tcp -> [::]:18080

$ curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:18080/
HTTP 200
```

三个细节值得在讲解时点出来：

- `docker run -d` 立刻返回容器 ID，但**服务不一定已经就绪**。实测中紧接着 curl 会拿到 `HTTP 000`（连接被重置），因为 nginx 还在启动。脚本里必须做就绪判断，生产上则交给 healthcheck 与探针。
- `PORTS` 列出现两条 `0.0.0.0:18080->80/tcp` 和 `[::]:18080->80/tcp`，分别是 IPv4 与 IPv6 的监听。
- `-p` 的写法还有 `-p 8080:80/tcp`（指定协议）、`-p 127.0.0.1:8080:80`（只监听本机回环，不对外暴露，适合数据库类服务）。

交互式进入容器（调试用；建议加 `--rm`，退出即清理）：

```bash
docker run -it --rm alpine:3.20 sh
# 容器里 exit 或 Ctrl+D 退出，容器自动删除
docker run -it --rm --entrypoint sh nginx:1.27-alpine   # 镜像自带 entrypoint 时覆盖它
```

注意：脚本里不要写 `-t`。实测报错：

```text
$ docker exec -it dlearn-nginx sh -c 'cat /etc/nginx/conf.d/default.conf | head -5'
cannot attach stdin to a TTY-enabled container because stdin is not a terminal
```

### 5.5 exec 与 attach 的区别

```text
$ docker exec dlearn-nginx nginx -v
nginx version: nginx/1.27.5

$ docker exec dlearn-nginx head -5 /etc/nginx/conf.d/default.conf
server {
    listen       80;
    listen  [::]:80;
    server_name  localhost;
```

- `docker exec`：在运行中的容器里**再起一个进程**，不影响 PID 1，退出也不影响容器。查配置、连数据库、看文件都该用它。
- `docker attach`：把当前终端接到 PID 1 的标准输入输出上。它不做新进程，因此 `Ctrl+C` 可能直接把主进程干掉导致容器退出。除了看前台日志流，一般不用它。

`exec` 里改的文件会写进容器可写层，`docker rm` 之后就没了——这是同一个概念的第三次出现，讲解时值得强调。

### 5.6 文件互拷

```text
$ docker cp dlearn-nginx:/etc/nginx/nginx.conf /opt/docker-lab/nginx.conf.copy
$ head -3 /opt/docker-lab/nginx.conf.copy

user  nginx;
worker_processes  auto;

$ echo 'hello from bind file' > /opt/docker-lab/host-file.txt
$ docker cp /opt/docker-lab/host-file.txt dlearn-nginx:/usr/share/nginx/html/host-file.txt
$ curl -s http://127.0.0.1:18080/host-file.txt
hello from bind file
```

`docker cp` 支持容器与宿主机双向拷贝，即使容器已停止也能拷（`docker cp` 直接操作文件系统）。频繁改动的内容应该改成挂载（第 7 章），而不是每次 `cp`。

### 5.7 查看容器状态

```text
$ docker top dlearn-nginx
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1517604             1517578             1                   09:29               ?                   00:00:00            nginx: master process nginx -g daemon off;
message+            1517884             1517604             0                   09:29               ?                   00:00:00            nginx: worker process
...

$ docker stats --no-stream dlearn-nginx
CONTAINER ID   NAME           CPU %     MEM USAGE / LIMIT     MEM %     NET I/O          BLOCK I/O     PIDS
6e696b058c87   dlearn-nginx   0.00%     7.137MiB / 19.24GiB   0.04%     4.5kB / 4.93kB   0B / 8.19kB   9
```

- `docker top` 看的是容器内进程在**宿主机上的真实 PID**，用来和 `top`/`ss` 的输出对齐。
- `docker stats` 是实时资源面板，`--no-stream` 只取一次（适合写进监控脚本）；不加参数就是持续刷新。
- `docker inspect` 是排查问题的万能入口，常用字段：

```bash
docker inspect 容器名 --format '{{.State.Status}} exit={{.State.ExitCode}} pid={{.State.Pid}}'
docker inspect 容器名 --format '{{.State.OOMKilled}}'                       # 是否被内存限制杀掉
docker inspect 容器名 --format '{{json .NetworkSettings.Ports}}'            # 端口映射
docker inspect 容器名 --format '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'   # 挂载
docker inspect 容器名 --format '{{range .Config.Env}}{{println .}}{{end}}'  # 环境变量
docker inspect 容器名 --format '{{json .State.Health}}'                     # 健康检查结果
```

### 5.8 重启策略

四种取值（`docker run --restart=`）：

| 取值 | 行为 |
|---|---|
| `no`（默认） | 不自动重启 |
| `on-failure[:N]` | 退出码非 0 时重启，最多 N 次；不写 N 表示无限 |
| `always` | 无论退出码都重启，且 dockerd 重启后也会拉起 |
| `unless-stopped` | 同 `always`，但手动 `docker stop` 过的不再自动拉起（生产最常用） |

实测 `on-failure:3` 的行为（退出码为 2，重启 3 次后停在 exited）：

```text
$ docker run -d --name dlearn-restart3 --restart=on-failure:3 alpine:3.20 sh -c 'echo "尝试启动"; sleep 3; exit 2'
$ docker inspect dlearn-restart3 --format 'RestartCount={{.RestartCount}} Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
RestartCount=3 Status=exited ExitCode=2
```

讲解要点：重启策略解决不了「进程启动即失败」的问题，反而会掩盖它。加上 `--restart` 的同时必须配健康检查或至少看 `RestartCount`，否则会出现「一直在重启、没人发现」的情况。

### 5.9 commit：把容器改动固化成镜像

```text
$ docker commit -m 'add demo files' -a 'docker-lab' dlearn-nginx dlearn-nginx-custom:1.0
sha256:3bdc53f5b8c3d112c3ededa5b6354a4eedaf1692a883a87f843997d9e8957596

$ docker run --rm dlearn-nginx-custom:1.0 cat /usr/share/nginx/html/exec-demo.txt
hello from docker exec
```

`commit` 把容器可写层固化成一个新镜像，是理解「可写层」的好工具，但**不要用它做生产镜像**：产物不可复现（无法从 Dockerfile 重建）、层里可能混进临时文件和密钥、历史的启动命令等等都会一起带走。正确做法是把改动写回 Dockerfile 重新 `build`。

## 6. Dockerfile：从六行到生产级

Dockerfile 是构建镜像的唯一「配方」，镜像质量几乎完全由它决定。这一章从一个能用的 Dockerfile 出发，把每条指令、缓存规则、启动命令的区别、多阶段构建全部实测一遍。

### 6.1 第一个 Dockerfile：静态站点镜像

项目结构（本文所有示例都在 `/opt/docker-lab` 下）：

```text
01-static-site/
├── Dockerfile
├── nginx.conf
└── site/
    ├── index.html
    └── assets/
        ├── app.js
        └── style.css
```

`01-static-site/Dockerfile` 全文：

```dockerfile
# 教学示例一：单阶段构建，把静态站点打进 nginx 镜像
FROM nginx:1.27-alpine

LABEL maintainer="docker-lab" \
      description="static site demo"

ENV TZ=Asia/Shanghai

# 清理官方默认欢迎页，避免和站点内容混淆
RUN rm -rf /usr/share/nginx/html/*

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

`nginx.conf`（放到 `/etc/nginx/conf.d/default.conf`，覆盖官方默认站点）：

```nginx
server {
    listen       80;
    server_name  _;

    root  /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;

    # 健康检查端点，供 HEALTHCHECK 和负载均衡探针使用
    location = /healthz {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "ok\n";
    }

    # SPA 路由回退：刷新 /about 这类前端路由不会 404
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 带指纹的静态资源长缓存
    location ~* \.(?:css|js|png|jpg|jpeg|svg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }
}
```

构建：

```text
$ docker build -t dlearn-static:1.0 ./01-static-site
#0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 576B 0.0s done
#1 DONE 1.1s

#2 [internal] load metadata for docker.io/library/nginx:1.27-alpine
#2 DONE 0.8s

#3 [internal] load .dockerignore
#3 transferring context: 2B done
#3 DONE 2.0s

#4 [internal] load build context
#4 DONE 0.0s

#5 [1/4] FROM docker.io/library/nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10
#5 resolve docker.io/library/nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10 1.6s done
#5 CACHED

#6 [2/4] RUN rm -rf /usr/share/nginx/html/*
#4 [internal] load build context
#4 transferring context: 1.95kB done
#4 DONE 2.4s

#6 [2/4] RUN rm -rf /usr/share/nginx/html/*
#6 DONE 4.9s

#7 [3/4] COPY nginx.conf /etc/nginx/conf.d/default.conf
#7 DONE 2.1s

#8 [4/4] COPY site/ /usr/share/nginx/html/
#8 DONE 2.3s

#9 exporting to image
#9 exporting layers 10.9s done
#9 naming to docker.io/library/dlearn-static:1.0 0.1s done
#9 DONE 23.5s
```

构建日志的读法（BuildKit 的输出比旧的构建器难读，讲解时值得逐段解释）：

- `[internal]` 打头的是构建器自身的动作：读 Dockerfile、拉基础镜像的元数据、读 `.dockerignore`、加载构建上下文。
- `#6 [2/4]` 表示「第 6 个步骤，Dockerfile 里第 2 个需要执行的指令（共 4 个）」。
- `CACHED` 表示这一层命中了本地缓存，没有重新执行。
- `exporting to image` 是把结果层的快照打包成镜像，这一步在 SSD 上也要几秒到十几秒。

运行并验证：

```text
$ docker run -d --name dlearn-static -p 18081:80 dlearn-static:1.0
8144955d6679b2adb2d81b1c78f79877a0ca8d6902d1943e4808208db39a770d

$ docker ps --filter name=dlearn-static
CONTAINER ID   IMAGE               COMMAND                   CREATED          STATUS                            PORTS                                       NAMES
8144955d6679   dlearn-static:1.0   "/docker-entrypoint.…"   14 seconds ago   Up 4 seconds (health: starting)   0.0.0.0:18081->80/tcp, [::]:18081->80/tcp   dlearn-static

$ curl -s -o /dev/null -w 'GET /            -> %{http_code}\n' http://127.0.0.1:18081/
GET /            -> 200
$ curl -s http://127.0.0.1:18081/healthz
ok
$ curl -s -o /dev/null -w "GET /about     -> %{http_code}\n" http://127.0.0.1:18081/about
GET /about     -> 200
$ curl -sI http://127.0.0.1:18081/assets/style.css | grep -iE "^(HTTP|etag|cache-control|expires)"
HTTP/1.1 200 OK
ETag: "6aa4ac39-154"
Expires: Sat, 19 Sep 2026 01:36:26 GMT
Cache-Control: max-age=604800
Cache-Control: public, max-age=604800, immutable
```

注意 `STATUS` 列里的 `(health: starting)`——镜像里定义了 `HEALTHCHECK`，容器启动后会按周期执行检查命令，状态会从 `starting` 变成 `healthy`。

### 6.2 指令全景

| 指令 | 作用 | 讲解要点 |
|---|---|---|
| `FROM` | 指定基础镜像 | 必须是第一条（`ARG` 除外）；`FROM ... AS name` 用于多阶段 |
| `RUN` | 构建时执行命令，产生新层 | 多条命令用 `&&` 连成一条，末尾清理缓存，减少层数与体积 |
| `COPY` | 从构建上下文复制文件进镜像 | 首选，只做复制；`--from=阶段名` 可跨阶段复制 |
| `ADD` | 增强版 COPY | 还能解压 tar、支持 URL；不推荐，行为不直观 |
| `WORKDIR` | 设置工作目录 | 后续指令的基准目录，目录不存在会自动创建 |
| `ENV` | 设置环境变量（运行时也生效） | 写法 `ENV A=1 B=2`；被它影响的层缓存会失效 |
| `ARG` | 构建参数（只在构建期有效） | `docker build --build-arg` 传入；不要用它传密钥（会留在镜像历史里） |
| `LABEL` | 元数据 | 便于 `docker inspect` 与清理时按 label 过滤 |
| `EXPOSE` | 声明监听的端口 | 只是文档与 `-P` 的提示，不等于发布端口 |
| `VOLUME` | 声明数据卷挂载点 | 声明后该目录的写入不进镜像层；滥用会导致「删容器即丢数据」的误解 |
| `USER` | 指定运行用户 | 生产镜像一律不要用 root（第 11 章） |
| `HEALTHCHECK` | 健康检查命令 | 只对单机 Docker 有意义，K8S 里用探针替代 |
| `CMD` | 默认启动命令 | 可被 `docker run` 的参数整体覆盖 |
| `ENTRYPOINT` | 固定入口命令 | 参数追加在其后，适合做「命令 + 参数」型镜像 |
| `STOPSIGNAL` | `docker stop` 发的信号 | 默认 SIGTERM；nginx 官方镜像设成了 SIGQUIT |
| `SHELL` | 改变 RUN/CMD 的默认 shell | 需要 pipefail 或换 shell 时用 |
| `ONBUILD` | 被当作基础镜像时触发 | 很少用，会造成隐式行为，不推荐 |

### 6.3 层缓存：什么让缓存失效

只改一个静态文件，重新构建：

```text
$ docker build -t dlearn-static:1.1 ./01-static-site
#5 [1/4] FROM docker.io/library/nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10
#5 DONE 1.0s

#6 [2/4] RUN rm -rf /usr/share/nginx/html/*
#6 CACHED

#7 [3/4] COPY nginx.conf /etc/nginx/conf.d/default.conf
#7 CACHED

#8 [4/4] COPY site/ /usr/share/nginx/html/
#8 DONE 2.6s
#9 DONE 10.4s
```

规则很简单，但用途很大：**每条指令的缓存键 = 父层缓存键 + 指令本身 + 指令涉及的文件内容哈希**。所以：

- 只改 `site/` 里的文件，`RUN rm`、`COPY nginx.conf` 都命中缓存，只有 `COPY site/` 及之后的层重建。
- 反过来，如果 `COPY . .` 写在 `RUN npm ci` 之前，任何一次代码改动都会让依赖层失效、重新装一遍依赖，构建时间从 10 秒变成 5 分钟。这是 Dockerfile 里最常见、最影响效率的错误，第 6.6 节用多阶段构建演示正确顺序。

顺带两个命令：

```bash
docker build --no-cache -t app:1.0 .        # 完全不用缓存（排查「本地能构建、CI 上不能」时用）
docker build --progress=plain -t app:1.0 .  # 输出完整日志，不用折叠格式（CI 日志里更好读）
```

### 6.4 .dockerignore：别把整个目录塞进构建上下文

构建时客户端会把上下文（`docker build` 最后那个目录）传给构建器。上下文越大越慢，而且 `COPY . .` 会把不该进镜像的文件（`.git`、`node_modules`、日志、密钥）一起带进去。

实测对照（项目里放一个 20MB 的垃圾文件，然后用 `COPY . /src/` 构建）：

```text
$ dd if=/dev/zero of=04-context/junk.bin bs=1M count=20
$ ls -lh 04-context/
总计 21M
-rw-r--r-- 1 root root 247  9月 12 09:42 Dockerfile
-rw-r--r-- 1 root root 20M  9月 12 09:43 junk.bin

$ docker build --progress=plain -t dlearn-ctx-no-ignore:1 ./04-context 2>&1 | grep -F 'transferring context'
#3 transferring context: 2B done
#4 transferring context: 20.98MB 0.2s done

$ docker run --rm dlearn-ctx-no-ignore:1
--- /src 内容 ---
total 20M
-rw-r--r--    1 root     root         247 Sep 12 01:42 Dockerfile
-rw-r--r--    1 root     root       20.0M Sep 12 01:43 junk.bin
--- 目录大小 ---
20.0M	/src

$ docker image ls --filter reference=dlearn-ctx-no-ignore
IMAGE                    ID             DISK USAGE   CONTENT SIZE   EXTRA
dlearn-ctx-no-ignore:1   d27ac37497e6       33.1MB         3.66MB

# 加上 .dockerignore 之后再构建同一个项目
$ cp .dockerignore.template 04-context/.dockerignore
$ docker build --progress=plain -t dlearn-ctx-with-ignore:1 ./04-context 2>&1 | grep -F 'transferring context'
#3 transferring context: 183B done
#4 transferring context: 213B done

$ docker run --rm dlearn-ctx-with-ignore:1
--- /src 内容 ---
total 4K
-rw-r--r--    1 root     root         247 Sep 12 01:42 Dockerfile
--- 目录大小 ---
12.0K	/src

$ docker image ls --filter reference=dlearn-ctx-with-ignore
IMAGE                      ID             DISK USAGE   CONTENT SIZE   EXTRA
dlearn-ctx-with-ignore:1   5874cefd26f1       12.1MB         3.63MB
```

结论一目了然：上下文 20.98MB → 213B，镜像 33.1MB → 12.1MB，容器里也看不到那个垃圾文件了。

`.dockerignore` 的写法（本示例用的文件）：

```text
# 构建上下文排除清单：不进 build context，也不进镜像层
**/node_modules
**/.git
**/.idea
**/.vscode
**/dist
junk.bin
*.log
```

讲解要点：`.dockerignore` 的位置是**构建上下文的根目录**（和 `docker build` 的路径参数同级），不是 Dockerfile 所在目录；用 `-f` 指定别处 Dockerfile 时很容易搞错。

### 6.5 CMD 与 ENTRYPOINT：启动命令的两种写法

先看三种写法的镜像（都是 `FROM alpine:3.20`）：

```dockerfile
# Dockerfile.cmd
CMD ["echo", "default-cmd"]

# Dockerfile.entrypoint
ENTRYPOINT ["echo", "fixed-entrypoint"]

# Dockerfile.shell-form（错误示范）
CMD echo shell-form-cmd
```

实测行为：

```text
$ docker run --rm dlearn-cmd:1.0
default-cmd

$ docker run --rm dlearn-cmd:1.0 hello docker
docker: Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: exec: "hello": executable file not found in $PATH

$ docker run --rm dlearn-cmd:1.0 echo hello docker
hello docker

$ docker run --rm dlearn-entrypoint:1.0
fixed-entrypoint

$ docker run --rm dlearn-entrypoint:1.0 hello docker
fixed-entrypoint hello docker

$ docker run --rm --entrypoint sh dlearn-entrypoint:1.0 -c 'echo 覆盖 ENTRYPOINT'
覆盖 ENTRYPOINT
```

把这四组输出对照着讲：

- `CMD` 是**默认值**，命令行给了参数就整体替换掉。`docker run dlearn-cmd hello docker` 相当于要执行 `hello docker` 这个命令，系统里没有 `hello` 这个可执行文件，于是报 `executable file not found`（退出码 127）。想追加参数必须显式写全：`docker run dlearn-cmd echo hello docker`。
- `ENTRYPOINT` 是**固定入口**，命令行参数会追加在它后面：`fixed-entrypoint hello docker`。
- `--entrypoint` 可以临时覆盖镜像的入口，调试时非常有用。

再看两种语法形式的区别（exec 形式是 JSON 数组，shell 形式是裸字符串）：

```text
$ docker inspect dlearn-entrypoint:1.0 --format 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}}'
Entrypoint=["echo","fixed-entrypoint"] Cmd=null

$ docker inspect dlearn-epcmd:1.0 --format 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}}'
Entrypoint=["echo","usage: greeting <name>"] Cmd=["world"]

$ docker inspect dlearn-shell:1.0 --format 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}}'
Entrypoint=null Cmd=["/bin/sh","-c","echo shell-form-cmd"]
```

关键差别（这段实测最能说明问题）：

- exec 形式：`CMD ["nginx","-g","daemon off;"]`，直接 exec 该程序，进程就是 PID 1，能收到信号。
- shell 形式：`CMD echo shell-form-cmd` 会被包成 `["/bin/sh","-c","echo shell-form-cmd"]`，PID 1 变成 `/bin/sh`，业务进程是它的子进程。
- 两个后果：一是信号发给 `sh` 而不是业务进程，`sh` 不转发的话 `docker stop` 只能等超时强杀；二是追加参数的行为不同，实测 `docker run --rm dlearn-shell:1.0 foo` 同样报 `exec: "foo": executable file not found`，因为参数把整个 `CMD` 替换掉了。

构建时工具也会提示这一点：

```text
$ docker build -f 02-cmd-entrypoint/Dockerfile.shell-form -t dlearn-shell:1.0 02-cmd-entrypoint
 1 warning found (use docker --debug to expand):
 - JSONArgsRecommended: JSON arguments recommended for CMD to prevent unintended behavior related to OS signals (line 3)
```

**结论：`CMD` 和 `ENTRYPOINT` 一律用 exec 形式（JSON 数组）。**

### 6.6 PID 1 与信号：为什么容器停不下来

上一节说了 `sh` 挡信号的问题，这一节把它实测出来。两个镜像只差一个写法：

```dockerfile
# Dockerfile.exec-sleep
CMD ["sleep", "300"]

# Dockerfile.shell-sleep
CMD sleep 300
```

实测停止耗时与退出码：

```text
$ docker run -d --name dlearn-exec-sleep dlearn-exec-sleep:1.0
$ docker top dlearn-exec-sleep
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1571196             1571172             0                   09:41               ?                   00:00:00            sleep 300

$ time docker stop dlearn-exec-sleep
dlearn-exec-sleep
real	0m12.797s
$ docker inspect dlearn-exec-sleep --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
Status=exited ExitCode=137

$ docker top dlearn-shell-sleep
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1571576             1571552             0                   09:41               ?                   00:00:00            sleep 300

$ time docker stop dlearn-shell-sleep
real	0m14.241s
$ docker inspect dlearn-shell-sleep --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
Status=exited ExitCode=137
```

两种写法都花了 12~14 秒（超过 `docker stop` 默认的 10 秒超时），退出码都是 137（SIGKILL 强杀）。原因是 **PID 1 有特殊待遇：内核不投递「没有安装处理函数」的信号给 PID 1**，`sleep` 没装 SIGTERM 处理函数，等于忽略。

对比一个自己处理信号的程序（nginx 官方镜像设了 `STOPSIGNAL SIGQUIT` 并有 master 进程管理）：

```text
$ time docker stop dlearn-signal-nginx
dlearn-signal-nginx
real	0m2.146s
$ docker inspect dlearn-signal-nginx --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
Status=exited ExitCode=0
```

2.1 秒优雅退出，退出码 0。三种解法（生产上按需选）：

1. 用 `--init`：Docker 会在容器里加一个小 init（tini）当 PID 1，转发信号并回收僵尸进程。实测：

```text
$ docker run -d --init --name dlearn-pid1-init dlearn-exec-sleep:1.0
$ docker top dlearn-pid1-init
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                1591474             1591452             0                   09:45               ?                   00:00:00            /sbin/docker-init -- sleep 300
root                1591707             1591474             0                   09:45               ?                   00:00:00            sleep 300

$ time docker stop dlearn-pid1-init
real	0m5.365s
$ docker inspect dlearn-pid1-init --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
Status=exited ExitCode=143
```

退出码从 137 变成 143（143 = 128 + 15，说明业务进程确实收到了 SIGTERM 正常终止，而不是被 SIGKILL 强杀）。

2. 业务代码自己注册 SIGTERM 处理函数，实现优雅停机（Spring Boot 的 `server.shutdown=graceful`、Node 的 `process.on('SIGTERM')` 都属于这一类）。
3. 需要更长时间收尾时，`docker stop -t 30` 把超时时间调大。

顺带明确一个易错点：`docker stop` 只给 PID 1 发信号。如果业务是 shell 脚本启动的（`sh -c "java -jar app.jar"`），信号就到不了 Java 进程，必须用 `exec java -jar app.jar` 让 Java 进程顶上 PID 1。

### 6.7 多阶段构建：把构建工具留在第一阶段

场景：Vue/React 前端需要 Node 和 node_modules 才能构建，但运行只需要静态文件。单阶段镜像会把 Node、npm 缓存、node_modules 全部留在最终镜像里，几百 MB；多阶段构建只把构建产物复制进一个干净的 nginx 镜像。

项目结构与关键文件（`/opt/docker-lab/03-multistage`）：

```text
03-multistage/
├── Dockerfile            # 多阶段
├── Dockerfile.single     # 单阶段对照
├── server.js             # 单阶段用它托管静态文件
├── nginx.conf
├── package.json
├── package-lock.json
├── .dockerignore
└── src/
    ├── app.js
    ├── format.js
    ├── index.html
    └── util.js
```

`package.json`：

```json
{
  "name": "docker-lab-site",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "mkdir -p dist/assets && esbuild src/app.js --bundle --minify --target=es2020 --outfile=dist/assets/bundle.js && cp src/index.html dist/index.html"
  },
  "devDependencies": {
    "esbuild": "^0.25.0"
  }
}
```

`src/app.js`（打包入口，引用另外两个模块）：

```javascript
import { greet } from './util.js';
import { formatTime } from './format.js';

const root = document.getElementById('app');
root.innerHTML = `
  <h2>${greet('Docker 多阶段构建')}</h2>
  <p>页面渲染时间：${formatTime(new Date())}</p>
  <p>这段文本由 esbuild 打包压缩后产出，源码在 src/ 目录。</p>
`;
```

`Dockerfile`（多阶段）全文：

```dockerfile
# 多阶段构建：builder 阶段装依赖、打包；runtime 阶段只带产物，不带 node_modules
FROM node:22-alpine AS builder

WORKDIR /app
ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com

# 先拷依赖清单再装依赖：源码改动不会让依赖层缓存失效
COPY package.json package-lock.json ./
RUN npm ci

COPY src ./src
RUN npm run build && ls -lh dist/assets/

# ---------- 运行阶段 ----------
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="docker-lab"
ENV TZ=Asia/Shanghai

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

`Dockerfile.single`（单阶段对照，构建和运行都用 node）：

```dockerfile
# 单阶段对照镜像：node 负责构建 + 运行，node_modules 一起进最终镜像
FROM node:22-alpine

WORKDIR /app
ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com

COPY package.json package-lock.json ./
RUN npm ci

COPY src ./src
COPY server.js ./
RUN npm run build

EXPOSE 3000
CMD ["node", "server.js"]
```

先在本机生成锁文件（真实项目里这一步在开发机或 CI 里做，容器里用 `npm ci` 保证可复现）：

```text
$ npm install --registry=https://registry.npmmirror.com

added 2 packages in 2m

$ ls -l package-lock.json
-rw-r--r-- 1 root root 14664  9月 12 09:50 package-lock.json
$ du -sh node_modules
11M	node_modules
```

构建多阶段镜像（日志已裁剪掉与讲解无关的中间行）：

```text
$ docker build -t dlearn-site-multi:1.0 ./03-multistage
#7 [builder 1/6] FROM docker.io/library/node:22-alpine@sha256:c610fcdfb1d5b4740dd70c284ed3cb16bb857e0f7166196e36a5501df7a3aa32
#7 DONE 30.2s

#6 [runtime 1/3] FROM docker.io/library/nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10
#6 CACHED

#9 [builder 2/6] WORKDIR /app
#9 DONE 13.0s

#10 [builder 3/6] COPY package.json package-lock.json ./
#10 DONE 20.8s

#11 [builder 4/6] RUN npm ci
#11 DONE 36.9s

#12 [builder 5/6] COPY src ./src
#12 DONE 14.5s

#13 [builder 6/6] RUN npm run build && ls -lh dist/assets/
#13 DONE 27.0s

#8 [runtime 2/3] COPY nginx.conf /etc/nginx/conf.d/default.conf
#8 DONE 15.0s

#14 [runtime 3/3] COPY --from=builder /app/dist /usr/share/nginx/html
#14 DONE 15.5s

#15 exporting to image
#15 DONE 76.7s
```

两个讲解点：

- 日志里 `[builder ...]` 与 `[runtime ...]` 交替出现，因为 BuildKit 会并行构建没有依赖关系的阶段（两个 `FROM` 同时拉取、同时执行）。
- 第三个阶段只有一条 `COPY --from=builder`，产物就是 `dist/` 里的两个文件，Node 与 node_modules 完全不进最终镜像。

验证多阶段镜像：

```text
$ docker run -d --name dlearn-multi -p 18083:80 dlearn-site-multi:1.0
$ curl -s -o /dev/null -w 'GET / -> %{http_code}\n' http://127.0.0.1:18083/
GET / -> 200
$ curl -s http://127.0.0.1:18083/ | grep -E "bundle.js|多阶段"
  <title>Docker 多阶段构建示例</title>
  <script src="/assets/bundle.js"></script>
$ curl -s http://127.0.0.1:18083/assets/bundle.js | head -c 200; echo
(()=>{function t(e){return`Hello, ${e}!`}function r(e){return new Intl.DateTimeFormat("zh-CN",{dateStyle:"medium",timeStyle:"medium"}).format(e)}var m=document.getElementById("app");m.innerHTML=`
  <h
$ curl -s http://127.0.0.1:18083/healthz
ok

$ docker exec dlearn-multi ls -lh /usr/share/nginx/html /usr/share/nginx/html/assets
/usr/share/nginx/html:
total 12K
-rw-r--r--    1 root     root         497 Apr 16  2025 50x.html
drwxr-xr-x    2 root     root        4.0K Sep 12 09:52 assets
-rw-r--r--    1 root     root         608 Sep 12 09:52 index.html

/usr/share/nginx/html/assets:
total 4K
-rw-r--r--    1 root     root         466 Sep 12 09:52 bundle.js

$ docker exec dlearn-multi sh -c "command -v node || echo 运行阶段没有 node"
运行阶段没有 node
```

`运行阶段没有 node` 这一行就是多阶段构建的意义所在：最终镜像里根本没有构建工具。

体积对比（同一个项目，两种构建方式）：

```text
$ docker image ls --filter reference='dlearn-site-*'
IMAGE                    ID             DISK USAGE   CONTENT SIZE   EXTRA
dlearn-site-multi:1.0    5b2aeb476d02       73.6MB           21MB   U
dlearn-site-single:1.0   21b88e485c6b        259MB         67.2MB   U
```

73.6MB（多阶段，nginx 底座）对 259MB（单阶段，node 底座 + node_modules），差别 3.5 倍。从 `docker history` 也能看出来单阶段镜像里那层 17.8MB 的依赖：

```text
$ docker history dlearn-site-single:1.0
IMAGE          CREATED         CREATED BY                                       SIZE      COMMENT
21b88e485c6b   2 minutes ago   CMD ["node" "server.js"]                         0B        buildkit.dockerfile.v0
<missing>      2 minutes ago   EXPOSE [3000/tcp]                                0B        buildkit.dockerfile.v0
<missing>      2 minutes ago   RUN /bin/sh -c npm run build # buildkit          57.3kB    buildkit.dockerfile.v0
<missing>      2 minutes ago   COPY server.js ./ # buildkit                     12.3kB    buildkit.dockerfile.v0
<missing>      6 minutes ago   COPY src ./src # buildkit                        28.7kB    buildkit.dockerfile.v0
<missing>      7 minutes ago   RUN /bin/sh -c npm ci # buildkit                 17.8MB    buildkit.dockerfile.v0
<missing>      7 minutes ago   COPY package.json package-lock.json ./ # bui…   28.7kB    buildkit.dockerfile.v0
<missing>      7 minutes ago   ENV NPM_CONFIG_REGISTRY=https://registry.npm…   0B        buildkit.dockerfile.v0
<missing>      8 minutes ago   WORKDIR /app                                     8.19kB    buildkit.dockerfile.v0
```

值得注意的是两个镜像的层数都是 10，所以**层数不是衡量镜像质量的标准，内容才是**——单阶段镜像的层里塞满了运行阶段用不到的东西。

用 `--target` 可以只构建到指定阶段（调试构建阶段、或给 CI 做缓存预热）：

```text
$ docker build --target builder -t dlearn-builder-only:1.0 ./03-multistage
$ docker run --rm --entrypoint sh dlearn-builder-only:1.0 -c "ls -lh /app/dist/assets && node -v"
total 4K
-rw-r--r--    1 root     root         466 Sep 12 09:52 bundle.js
v22.23.2
```

Java 项目同理，而且收益更明显（`maven:3.8-openjdk-8-slim` 150MB 的构建镜像不进最终产物）：

```dockerfile
# 构建阶段：用 maven 打 jar
FROM maven:3.8-openjdk-8-slim AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn -q dependency:go-offline          # 依赖层单独缓存
COPY src ./src
RUN mvn -q clean package -DskipTests

# 运行阶段：只要 JRE
FROM eclipse-temurin:8-jre
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar
ENV TZ=Asia/Shanghai
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

## 7. 数据卷 Volume

容器可写层随容器删除而消失，所以数据库文件、上传目录、日志这类必须留存的数据一定要放在卷里。Docker 提供三种挂载方式，选择依据很清楚。

### 7.1 三种挂载方式怎么选

| 方式 | 语法 | 数据位置 | 适用场景 |
|---|---|---|---|
| 命名卷（volume） | `-v mydata:/data` | Docker 管理目录 `/var/lib/docker/volumes/mydata/_data` | 数据库数据、需要备份迁移的业务数据（首选） |
| 绑定挂载（bind mount） | `-v /host/path:/data` | 宿主机指定路径 | 配置文件、开发时挂源码、宿主机已有的数据目录 |
| 临时文件系统（tmpfs） | `--tmpfs /tmp` | 内存 | 临时文件、敏感数据不落盘 |

命名卷由 Docker 管理，跨平台、可 `docker volume` 系列命令统一操作、支持卷驱动（NFS、云盘）；绑定挂载完全依赖宿主机目录结构，可移植性差，但在开发环境里最方便。

### 7.2 命名卷：容器删了数据还在

```text
$ docker volume create dlearn-data
dlearn-data

$ docker volume ls --filter name=dlearn-data
DRIVER    VOLUME NAME
local     dlearn-data

$ docker run --rm -v dlearn-data:/data alpine:3.20 sh -c 'echo "first write" > /data/note.txt; ls -l /data'
total 4
-rw-r--r--    1 root     root            12 Sep 12 01:48 note.txt

# 换一个新容器，数据还在
$ docker run --rm -v dlearn-data:/data alpine:3.20 cat /data/note.txt
first write

$ docker volume inspect dlearn-data
[
    {
        "CreatedAt": "2026-09-12T09:47:45+08:00",
        "Driver": "local",
        "Labels": null,
        "Mountpoint": "/var/lib/docker/volumes/dlearn-data/_data",
        "Name": "dlearn-data",
        "Options": null,
        "Scope": "local"
    }
]
```

两个讲解点：

- `Mountpoint` 就是数据在宿主机上的真实位置。可以直接 `ls /var/lib/docker/volumes/dlearn-data/_data` 看（需要 root），但**不要手工改里面的文件**——数据库类应用的权限和属主由容器内进程决定（很多镜像用 uid 999 的 mysql 用户），宿主机上手工拷贝容易把属主改坏。
- 卷的生命周期独立于容器：容器 `rm` 不影响卷；只有 `docker volume rm`（或 `docker compose down -v`）才会删。这也是「删了容器数据不见了」的常见误解来源——那是没用卷。

### 7.3 绑定挂载：宿主机目录直接映射

```text
$ echo 'host side file' > /opt/docker-lab/host-dir/from-host.txt
$ docker run --rm -v /opt/docker-lab/host-dir:/data alpine:3.20 sh -c 'ls -l /data; cat /data/from-host.txt'
total 4
-rw-r--r--    1 root     root            15 Sep 12 01:48 from-host.txt
host side file

$ docker run --rm -v /opt/docker-lab/host-dir:/data alpine:3.20 sh -c 'echo "container side file" > /data/from-container.txt'
$ ls -l host-dir/
总计 8
-rw-r--r-- 1 root root 20  9月 12 09:49 from-container.txt
-rw-r--r-- 1 root root 15  9月 12 09:48 from-host.txt
$ cat host-dir/from-container.txt
container side file
```

容器与宿主机看到的是同一份文件，改哪边都立刻生效。两个坑要提前讲：

- 路径必须是绝对路径，`-v ./data:/data` 这种相对路径会被当成「命名卷」而不是目录（结果是一个叫 `./data` 的奇怪卷名或者直接报错）。
- 宿主机目录不存在时，Docker 会**以 root 身份自动创建**这个目录，容易在项目目录里留下一堆 root 属主的空目录（之后普通用户还删不掉）。

### 7.4 只读挂载与匿名卷

只读挂载（`:ro`），适合把配置、证书、静态资源挂给容器，防误写：

```text
$ docker run --rm -v /opt/docker-lab/host-dir:/data:ro alpine:3.20 sh -c 'echo x > /data/readonly.txt'
sh: can't create /data/readonly.txt: Read-only file system

$ docker run --rm -v /opt/docker-lab/host-dir:/data:ro alpine:3.20 sh -c 'cat /data/from-host.txt && echo "只读读是正常的"'
host side file
只读读是正常的
```

匿名卷：`-v` 只写容器内路径不给名字时，Docker 自动生成一个 64 位哈希名的卷：

```text
$ docker run -d --name dlearn-anon -v /var/lib/demo alpine:3.20 sleep 300
$ docker inspect dlearn-anon --format '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{"\n"}}{{end}}'
volume 0d78cf923582963b18a756b79a52e07b3462017a282abf1bd72c99ed2ad8c9ce -> /var/lib/demo

$ docker rm -f dlearn-anon
$ docker volume ls --filter dangling=true
DRIVER    VOLUME NAME
local     0d78cf923582963b18a756b79a52e07b3462017a282abf1bd72c99ed2ad8c9ce
local     039c0b99b8bca75781bc80212161cc03ce61d7b92c6cc51aee142b4aed569b83
local     8014ecc940f5e8d605a8e99d78c883b8898fbe6487ef2baf635d995ea400209e
local     dlearn-data
```

匿名卷是「删了容器还留着一堆哈希卷」的主要来源。`docker volume ls --filter dangling=true` 可以列出所有没被容器引用的卷（注意：**不一定是垃圾**，可能是有意保留的数据，删之前先 `inspect` 看 Mountpoint 时间戳）。另外 `Dockerfile` 里的 `VOLUME` 指令会给每个容器生成匿名卷，这就是很多官方镜像（mysql、postgres）容器删了以后磁盘还占着的原因。

### 7.5 `-v` 与 `--mount`：两种写法与查看挂载

```text
$ docker run -d --name dlearn-mount-syntax --mount type=volume,src=dlearn-data,dst=/data,readonly alpine:3.20 sleep 300
$ docker inspect dlearn-mount-syntax --format '{{json .Mounts}}'
[{"Type":"volume","Name":"dlearn-data","Source":"/var/lib/docker/volumes/dlearn-data/_data","Destination":"/data","Driver":"local","Mode":"z","RW":false,"Propagation":""}]
```

`--mount` 的写法啰嗦但**不会静默创建不存在的目录**：路径写错会直接报错，而不是悄悄建一个空目录把容器里的数据盖掉。生产脚本里推荐 `--mount`。参数名对应关系：

| `-v` 写法 | `--mount` 写法 |
|---|---|
| `-v myvol:/data` | `--mount type=volume,src=myvol,dst=/data` |
| `-v /host/dir:/data` | `--mount type=bind,src=/host/dir,dst=/data` |
| `-v /host/dir:/data:ro` | `--mount type=bind,src=/host/dir,dst=/data,readonly` |
| `-v myvol:/data:ro` | `--mount type=volume,src=myvol,dst=/data,readonly` |
| `-v /host/dir:/data:z` | `--mount type=bind,src=/host/dir,dst=/data,bind-propagation=shared` |

查看一个容器挂了什么：

```bash
docker inspect 容器名 --format '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}} RW={{.RW}}{{"\n"}}{{end}}'
docker volume ls -f dangling=true          # 没被引用的卷
docker volume inspect 卷名 --format '{{.Mountpoint}} {{.CreatedAt}}'
```

### 7.6 MySQL 数据持久化：删容器不丢，删卷才丢

以 MySQL 为例走一遍完整流程（本机实测）。用命名卷启动：

```text
$ docker run -d --name dlearn-mysql -p 13306:3306 \
    -e MYSQL_ROOT_PASSWORD=root123456 \
    -e MYSQL_DATABASE=demo \
    -v dlearn-mysql-data:/var/lib/mysql \
    mysql:8.4 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

$ docker volume inspect dlearn-mysql-data --format 'Mountpoint={{.Mountpoint}} CreatedAt={{.CreatedAt}}'
Mountpoint=/var/lib/docker/volumes/dlearn-mysql-data/_data CreatedAt=2026-09-12T10:14:14+08:00
```

`-v 卷名:/var/lib/mysql` 这一条就是全部关键——MySQL 的所有数据文件都写在 `/var/lib/mysql`，挂到卷上之后数据就脱离了容器生命周期。

**删掉容器，卷还在**：

```text
$ docker stop dlearn-mysql
dlearn-mysql
$ docker rm dlearn-mysql
dlearn-mysql
$ docker volume ls --filter name=dlearn-mysql-data
DRIVER    VOLUME NAME
local     dlearn-mysql-data
```

**挂同一个卷起新容器，数据还在**（这套流程在四服务栈里也验证过，见第 9.6 节第五层：`docker compose down` 之后 `up` 起来三条数据都在）。

反过来说，**没挂卷就等于把数据放在可写层**：删除容器时数据跟着消失，只剩下一个没人知道的匿名卷（第 7.4 节）。很多「重建容器后数据库空了」的事故就是这么来的。

**备份与恢复的标准姿势**（不用装 mysqldump 客户端，直接用 tar 打包卷）：

```text
# 1. 先停业务容器，保证数据文件一致
$ docker stop dlearn-mysql2

# 2. 用一次性容器挂载该卷（只读），打包到宿主机目录
$ docker run --rm -v dlearn-mysql-data:/data:ro -v /opt/docker-lab:/backup \
    alpine:3.20 tar czf /backup/mysql-volume-backup.tar.gz -C /data .
$ ls -lh mysql-volume-backup.tar.gz

# 3. 恢复到新卷
$ docker volume create dlearn-mysql-restore
$ docker run --rm -v dlearn-mysql-restore:/data -v /opt/docker-lab:/backup \
    alpine:3.20 sh -c 'tar xzf /backup/mysql-volume-backup.tar.gz -C /data && ls /data | head -5'

# 4. 重新启动业务容器
$ docker start dlearn-mysql2
```

要点：**备份前先停写**（否则可能备份到写一半的文件）；卷挂载加 `:ro` 避免误写；恢复出来的卷可以直接挂给新容器。生产上更推荐 `mysqldump` 逻辑备份（可跨版本恢复、体积小），tar 卷备份适合整库搬迁和灾备。

## 8. 网络 Network

容器的网络问题占实际排错量的一大半，核心要讲清楚三件事：默认 bridge 为什么不能按名字互访、自定义网络的 DNS 怎么工作、端口发布是怎么实现的。

### 8.1 五种网络模式

| 模式 | 说明 | 典型场景 |
|---|---|---|
| `bridge`（默认） | 每个容器一块虚拟网卡，接在 `docker0` 网桥上，通过 NAT 出网 | 绝大多数单机场景 |
| 自定义 bridge | 自己创建的网桥，**自带 DNS，容器间可按名字互访** | 多容器应用（首选） |
| `host` | 容器直接共用宿主机网络栈，没有独立 IP，不用 `-p` | 对性能敏感、需要复用宿主机端口 |
| `none` | 只有 lo，完全无网络 | 只做计算、离线批处理 |
| `overlay` | 跨主机网络（Swarm/K8S 用） | 集群 |

先看本机的网络清单：

```text
$ docker network ls
NETWORK ID     NAME                           DRIVER    SCOPE
49cfcba0160f   1panel-network                 bridge    local
ec34547a3bd0   bridge                         bridge    local
19fe813eb5f3   host                           host      local
3b8a83784ecf   kb-network                     bridge    local
daa3f86d5601   minikube                       bridge    local
c61daaf2859b   nacos_default                  bridge    local
ef68d6b56974   none                           null      local
426e2d2c7b6e   orjuice-platform_orjuice-net   bridge    local
fa8eab3cbfd1   questionnaire_default          bridge    local
```

`bridge`、`host`、`none` 是 Docker 自带的三个，其余是各个 compose 项目（`xxx_default` 是 `docker compose up` 自动创建的）和手工创建的。默认 bridge 的网段：

```text
$ docker network inspect bridge --format '{{json .IPAM.Config}}'
[{"Subnet":"172.17.0.0/16","Gateway":"172.17.0.1"}]

$ docker network inspect bridge --format '{{json .Options}}'
{"com.docker.network.bridge.default_bridge":"true","com.docker.network.bridge.enable_icc":"true","com.docker.network.bridge.enable_ip_masquerade":"true","com.docker.network.bridge.host_binding_ipv4":"0.0.0.0","com.docker.network.bridge.name":"docker0","com.docker.network.driver.mtu":"1500"}
```

记住 `docker0` 这个网桥名和 `172.17.0.1` 这个网关——容器里看到的网关就是宿主机的 `docker0` 地址。

### 8.2 默认 bridge：容器之间不能按名字互访

```text
$ docker run -d --name dlearn-a alpine:3.20 sleep 300
$ docker run -d --name dlearn-b alpine:3.20 sleep 300

$ docker exec dlearn-a ping -c 1 -W 2 dlearn-b
ping: bad address 'dlearn-b'

$ docker inspect dlearn-b --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
172.17.0.6

$ docker exec dlearn-a ping -c 1 -W 2 172.17.0.6
PING 172.17.0.6 (172.17.0.6): 56 data bytes
64 bytes from 172.17.0.6: seq=0 ttl=64 time=0.102 ms

--- 172.17.0.6 ping statistics ---
1 packets transmitted, 1 packets received, 0% packet loss
```

结论：默认 bridge 上**只能用 IP 互访**，用容器名会解析失败。原因是默认 bridge 不提供内置 DNS。这条决定了「为什么 docker-compose 里可以直接写 `mysql:3306`」——compose 会给项目创建自定义网络。

### 8.3 自定义 bridge：内置 DNS 按容器名解析

```text
$ docker network create dlearn-net
fcaeb8915a53a7722e65597590f92172d0dfefe57cd5dee7e8c8640d51762ef7

$ docker run -d --name dlearn-c --network dlearn-net alpine:3.20 sleep 300
$ docker run -d --name dlearn-d --network dlearn-net alpine:3.20 sleep 300

$ docker exec dlearn-c cat /etc/resolv.conf
# Generated by Docker Engine.
# This file can be edited; Docker Engine will not make further changes once it
# has been modified.

nameserver 127.0.0.11
search tailc6bb9f.ts.net
options edns0 trust-ad ndots:0

# Based on host file: '/etc/resolv.conf' (internal resolver)
# ExtServers: [host(127.0.0.53)]

$ docker exec dlearn-c ping -c 1 -W 2 dlearn-d
PING dlearn-d (172.23.0.3): 56 data bytes
64 bytes from 172.23.0.3: seq=0 ttl=64 time=0.121 ms

$ docker exec dlearn-d ping -c 1 -W 2 dlearn-c
PING dlearn-c (172.23.0.2): 56 data bytes
64 bytes from 172.23.0.2: seq=0 ttl=64 time=0.063 ms

$ docker network inspect dlearn-net --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
dlearn-d 172.23.0.3/16
dlearn-c 172.23.0.2/16
```

讲解重点：`nameserver 127.0.0.11` 是 Docker 内置 DNS 服务器（跑在容器的网络命名空间里），它把同一自定义网络内其他容器的**名字和网络别名**解析成 IP。宿主机上的 `/etc/resolv.conf` 被当作上游，所以容器既能解析容器名，也能解析外网域名。

一个容易踩的坑（本机实测，注意域名后缀）：容器里带了 `search tailc6bb9f.ts.net`，用 `nslookup` 查短名会把搜索域拼上去：

```text
$ docker exec dlearn-c nslookup dlearn-d
Server:		127.0.0.11
Address:	127.0.0.11:53

** server can't find dlearn-d.tailc6bb9f.ts.net: NXDOMAIN
```

`ping dlearn-d` 能通、`nslookup` 却报 NXDOMAIN，是因为 `nslookup` 只查了带搜索域的完整名字。要验证名字解析，用 `getent hosts dlearn-d` 或直接 `ping`，别只看 `nslookup` 的输出。

### 8.4 网络隔离与多网络接入

不在同一个网络的容器互相不可见：

```text
$ docker network create dlearn-net2
$ docker run -d --name dlearn-e --network dlearn-net2 alpine:3.20 sleep 300

$ docker exec dlearn-c ping -c 1 -W 2 dlearn-e
ping: bad address 'dlearn-e'

# 把 dlearn-c 同时接入第二个网络
$ docker network connect dlearn-net2 dlearn-c
$ docker exec dlearn-c ping -c 1 -W 2 dlearn-e
PING dlearn-e (172.24.0.2): 56 data bytes
64 bytes from 172.24.0.2: seq=0 ttl=64 time=0.105 ms
```

```text
$ docker inspect dlearn-c --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}'
dlearn-net=172.23.0.2 dlearn-net2=172.24.0.3

$ docker network disconnect dlearn-net2 dlearn-c
```

这个能力在生产上很有用：把「前端网络」和「数据库网络」分开，只让 nginx 同时接两个网络，数据库就与前端容器完全隔离（第 9 章的 compose 栈就是这么做的）。

### 8.5 网络别名与「按项目隔离」

自定义网络里，容器的**名字**和**网络别名**都能被解析。`--network-alias` 可以给同一个容器加额外名字，这也是 compose 的底层机制——compose 会把**服务名**注册成网络别名，所以后端代码里直接写 `db:3306`、`redis:6379` 就能连通：

```bash
docker run -d --name dlearn-api1 --network dlearn-net --network-alias api alpine:3.20 sleep 300
# 同网络里的其他容器：ping api / ping dlearn-api1 都能解析到同一个 IP
```

compose 项目会自动创建以项目名开头的网络，网络里的成员一目了然（本机四服务栈的实测）：

```text
$ docker network inspect dlearn-stack_backend --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
dlearn-stack-cache 172.23.0.2/16
dlearn-stack-db 172.23.0.3/16
```

**「按项目隔离」的关键就是网络**：`dlearn-stack_backend` 只有 api/db/cache 三个成员，别的 compose 项目（或别人的手工容器）默认进不来；而 `dlearn-stack_frontend` 只有 web。这样即使前端容器被攻破，也访问不到数据库（因为它不在 backend 网络里）。反过来，**要让两个 compose 项目互相通信，必须显式接入同一个外部网络**：

```bash
docker network create shared-net

# 项目 A 的 compose 文件里
networks:
  shared-net:
    external: true
```



### 8.5 端口发布：-p / -P / 端口冲突

```text
$ docker run -d --name dlearn-p1 -p 18085:80 nginx:1.27-alpine
$ docker inspect dlearn-p1 --format '{{json .NetworkSettings.Ports}}'
{"80/tcp":[{"HostIp":"0.0.0.0","HostPort":"18085"},{"HostIp":"::","HostPort":"18085"}]}
```

`-p` 的几种写法：

```bash
-p 8080:80                 # 宿主机所有网卡的 8080 -> 容器 80
-p 127.0.0.1:8080:80       # 只监听回环，外部访问不到（数据库推荐）
-p 8080:80/tcp             # 显式指定协议
-p 8080:80/udp
-P                         # 随机分配宿主机端口（由 EXPOSE 决定容器端口）
```

端口冲突的真实报错：

```text
$ docker run --rm -p 18085:80 nginx:1.27-alpine
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint epic_hoover (edd928733eaa4f7785a570d03ca85262d82b79408b213a56476574dd36c64f21): Bind for 0.0.0.0:18085 failed: port is already allocated
```

`-P` 随机端口：

```text
$ docker run -d --name dlearn-p2 -P nginx:1.27-alpine
$ docker port dlearn-p2
80/tcp -> 0.0.0.0:32768
80/tcp -> [::]:32768
```

**就绪竞态的真实表现**（本机实测，值得在讲解时现场演示一遍）：容器刚起来的一瞬间去访问，拿到的是 `000`：

```text
$ docker run -d --name dlearn-p1 -p 18085:80 nginx:1.27-alpine
$ curl -s -o /dev/null -w 'GET :18085 -> %{http_code}\n' http://127.0.0.1:18085/
GET :18085 -> 000
[exit=56]
```

`exit 56` 是 curl 的「接收数据失败/连接被重置」，含义是 **docker-proxy 已经把端口监听起来并接受了连接，但容器里的 nginx 还没开始 listen**，于是连接被重置。稍等片刻或轮询一次就正常：

```text
$ docker run -d --name dlearn-nginx -p 18080:80 nginx:1.27-alpine
# 等待容器内 80 端口可访问（脚本里的就绪判断）
$ wait_http http://127.0.0.1:18080/
ready after 1s
$ curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:18080/
HTTP 200
```

所以：**只要在脚本或流水线里「起完容器马上访问」，就必须自己写就绪轮询**；生产环境则交给健康检查与 compose 的 `depends_on: condition: service_healthy`（第 9 章）。



### 8.6 host 网络与 none 网络

`host` 模式：容器直接共用宿主机网络栈，能访问宿主机上所有监听在 `127.0.0.1` 的服务（下面用宿主机上跑着的 RabbitMQ 管理端口 15672 做对照）：

```text
$ docker run --rm --network host alpine:3.20 sh -c 'wget -qO- -T3 http://127.0.0.1:15672/ | head -3'
<!DOCTYPE html>
<html>
  <head>

# 不加 --network host 时，容器里的 127.0.0.1 是它自己，自然连不上
$ docker run --rm alpine:3.20 sh -c 'wget -qO- -T3 http://127.0.0.1:15672/ | head -3'
wget: can't connect to remote host (127.0.0.1): Connection refused
```

`host` 模式下不需要也不允许端口映射（`-p` 会给出警告并被忽略），容器里的端口就是宿主机的端口，多个容器抢同一个端口会直接冲突。宿主机上 12 个 `inet` 地址在 `host` 容器里全部可见。

`none` 模式：

```text
$ docker run --rm --network none alpine:3.20 sh -c 'ip addr show | grep -E "^[0-9]+:|inet "; wget -qO- -T3 http://1.1.1.1 || echo "无外网"'
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
    inet 127.0.0.1/8 scope host lo
wget: can't connect to remote host (1.1.1.1): Network unreachable
无外网
```

### 8.7 容器内 DNS 与外网访问

```text
$ docker run --rm alpine:3.20 sh -c 'nslookup registry.npmmirror.com | head -6'
Server:		192.168.1.1
Address:	192.168.1.1:53

Non-authoritative answer:
registry.npmmirror.com	canonical name = registry.npmmirror.com.w.cdngslb.com
Name:	registry.npmmirror.com.w.cdngslb.com
```

默认 bridge / host 网络下（非自定义网络）容器直接使用宿主机的 DNS 配置。三种调整方式：

```text
$ docker run --rm --dns 8.8.8.8 alpine:3.20 cat /etc/resolv.conf
nameserver 8.8.8.8
search tailc6bb9f.ts.net

$ docker run --rm --add-host demo.internal:10.10.10.10 alpine:3.20 cat /etc/hosts
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
10.10.10.10	demo.internal
172.17.0.9	9dcea2fb6cd2
```

- `--dns`：给这个容器指定 DNS（daemon 级默认值配在 daemon.json 的 `dns` 字段）。
- `--add-host`：往 `/etc/hosts` 里塞一条静态解析，适合访问内部固定 IP 的服务。
- `--hostname`：改容器主机名（也是 `/etc/hosts` 里的那条记录）。

### 8.8 网络排查命令清单

```bash
docker network ls                                   # 有哪些网络
docker network inspect 网络名                        # 网段、网关、接了哪些容器
docker inspect 容器名 --format '{{json .NetworkSettings.Networks}}'   # 容器的 IP、网关、别名
docker port 容器名                                   # 端口映射
docker exec 容器名 cat /etc/resolv.conf              # 容器用的 DNS
docker exec 容器名 getent hosts 服务名                # 名字解析是否正常
docker exec 容器名 wget -qO- -T3 http://服务名:端口/  # 容器间连通性
ss -lntp | grep 端口                                 # 宿主机上端口是否被占用（docker-proxy）
```

三个高频结论：

1. 容器访问宿主机上的服务，不能用 `127.0.0.1`（那是容器自己），要用 `host.docker.internal`（Docker 20.10+ 在 Linux 上需要 `--add-host`）或宿主机在 `docker0` 上的地址（通常 `172.17.0.1`）。
2. compose 项目之间互相隔离：A 项目的容器访问不到 B 项目的容器名，除非把它们接入同一个外部网络（`docker network create` + 各项目里声明 `external: true`）。
3. 换了网络或重建容器后 IP 会变，所以任何配置里都不要写容器 IP，一律写服务名。

## 9. docker compose：四服务栈实战

单容器用 `docker run`，多容器手工 `docker run` 就会变成一长串命令，还得自己处理网络、启动顺序、环境变量。`docker compose` 用一个 YAML 文件描述整套服务，一条命令起停。

这一章用一个真实四服务栈把前面所有内容串起来：**nginx（web）→ Node 接口（api）→ MySQL（db）+ Redis（cache）**，四个容器、两个网络、两个命名卷、四个健康检查。

### 9.1 项目结构

```text
05-compose-stack/
├── docker-compose.yml
├── .env
├── web/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── html/
│       ├── index.html
│       └── app.js
├── api/
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── server.js
│   └── .dockerignore
└── db/
    └── init/
        └── 01-schema.sql
```

### 9.2 docker-compose.yml 全文与逐段解释

```yaml
name: dlearn-stack

services:
  web:
    build:
      context: ./web
    image: dlearn-stack-web:1.0
    container_name: dlearn-stack-web
    ports:
      - "${WEB_PORT}:80"
    depends_on:
      api:
        condition: service_healthy
    networks:
      - frontend
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1/healthz"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s

  api:
    build:
      context: ./api
    image: dlearn-stack-api:1.0
    container_name: dlearn-stack-api
    environment:
      MYSQL_HOST: db
      MYSQL_PORT: "3306"
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      REDIS_URL: redis://cache:6379
      TZ: Asia/Shanghai
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    networks:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:3000/api/health"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s

  db:
    image: mysql:8.4
    container_name: dlearn-stack-db
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      TZ: Asia/Shanghai
    volumes:
      - db-data:/var/lib/mysql
      - ./db/init:/docker-entrypoint-initdb.d:ro
    networks:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -uroot -p$$MYSQL_ROOT_PASSWORD --silent"]
      interval: 10s
      timeout: 10s
      retries: 30
      start_period: 180s

  cache:
    image: redis:7.4-alpine
    container_name: dlearn-stack-cache
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - cache-data:/data
    networks:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

networks:
  frontend:
  backend:

volumes:
  db-data:
  cache-data:
```

逐个讲清每条设置的理由：

| 配置 | 为什么这么写 |
|---|---|
| `name: dlearn-stack` | 项目名，决定容器名前缀、网络名（`dlearn-stack_backend`）、卷名（`dlearn-stack_db-data`）。多人在一台机器上跑 compose 时**必须**各自不同，否则会互相覆盖（第 14.6 节） |
| `build.context` + `image` | 既构建又打标签：首次 `up --build` 会构建，之后可以直接用这个镜像名在其他机器上跑 |
| `container_name` | 固定容器名便于 `docker exec dlearn-stack-db ...`；不写则生成 `项目名-服务名-序号` |
| `ports: "${WEB_PORT}:80"` | 只有 web 发布端口；db/cache 在内网，宿主机访问不到 |
| `depends_on + condition: service_healthy` | 真正解决「启动顺序」问题：等 db 的 healthcheck 变 healthy 才启动 api（第 9.5 节有反面案例） |
| `networks: frontend / backend` | web 同时接两个网络（对外、对内）；api/db/cache 只在 backend。前端容器即使被攻破也碰不到数据库 |
| `restart: unless-stopped` | 进程挂了自动拉起、宿主机重启后自动拉起，但 `docker compose stop` 之后不会自己回来 |
| `environment` 用 `${}` | 从 `.env` 取值，敏感信息不进版本库（配合 `.gitignore`） |
| `volumes: db-data` | 命名卷，容器重建数据不丢（第 9.6 节实测） |
| `./db/init:/docker-entrypoint-initdb.d:ro` | 只读挂载初始化 SQL，MySQL 官方镜像会在**数据目录为空时**执行它 |

`.env`（compose 自动读取当前目录的 .env）：

```ini
# docker compose 会自动读取同目录下的 .env，用这里的值替换 docker-compose.yml 里的 ${变量}
WEB_PORT=18090
MYSQL_ROOT_PASSWORD=root123456
MYSQL_DATABASE=demo
MYSQL_USER=demo
MYSQL_PASSWORD=demo123456
```

验证变量替换是否生效（`config` 子命令会把最终生效的配置打印出来，**这是排查 compose 问题的第一招**）：

```text
$ docker compose config --services
web
api
db
cache

$ docker compose config --volumes
db-data
cache-data

$ docker compose config
name: dlearn-stack
services:
  api:
    build:
      context: /opt/docker-lab/05-compose-stack/api
      dockerfile: Dockerfile
    container_name: dlearn-stack-api
    depends_on:
      cache:
        condition: service_healthy
        required: true
      db:
        condition: service_healthy
        required: true
    environment:
      MYSQL_DATABASE: demo
      MYSQL_HOST: db
      MYSQL_PASSWORD: demo123456
      MYSQL_PORT: "3306"
      MYSQL_USER: demo
      REDIS_URL: redis://cache:6379
      TZ: Asia/Shanghai
    healthcheck:
      test:
        - CMD
        - wget
        - -qO-
        - http://127.0.0.1:3000/api/health
      timeout: 3s
      interval: 10s
      retries: 5
      start_period: 10s
    image: dlearn-stack-api:1.0
    networks:
      backend: null
    restart: unless-stopped
```

注意 `MYSQL_PASSWORD: demo123456`——`.env` 里的值已经替换进来了。另外 `$$MYSQL_ROOT_PASSWORD` 在 `config` 输出里仍然是 `$$` 形式，这是 compose 的转义：`$$` 表示「这个 `$` 不要被 compose 解析」，最终传给容器的是 `$MYSQL_ROOT_PASSWORD`，由容器内的 shell 展开成环境变量的值。**把密码直接写死在 healthcheck 里（`-proot123456`）会导致改密码时漏改一处，用 `$$` 引用变量是标准做法。**

### 9.3 web 服务（nginx + 前端页面）

`web/nginx.conf` 的关键部分（完整的见项目文件）：

```nginx
server {
    listen       80;
    server_name  _;

    root  /usr/share/nginx/html;
    index index.html;

    # 用变量形式转发：nginx 在每次请求时才重新解析 api 这个名字，
    # 避免容器重建后 IP 变化导致 502（写成 upstream 只在启动时解析一次）
    resolver 127.0.0.11 valid=10s ipv6=off;
    set $api_upstream http://api:3000;

    gzip on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/javascript application/json;

    location = /healthz {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "ok\n";
    }

    location /api/ {
        proxy_pass $api_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 3s;
        proxy_read_timeout    30s;
    }

    location = /index.html {
        add_header Cache-Control "no-cache";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

这段配置里有两个值得单独讲的点：

1. `resolver 127.0.0.11` + `set $api_upstream` + `proxy_pass $api_upstream`：**用变量形式让 nginx 在每次请求时重新解析服务名**。如果写成 `upstream api_upstream { server api:3000; }`，nginx 只在启动时解析一次，`docker compose up -d --force-recreate api` 之后 api 容器 IP 变了，nginx 仍然往旧 IP 发请求 → 502。这是 compose 环境里的经典坑。
2. `location /api/` 用变量形式的 `proxy_pass` 时会**原样转发 URI**（保留 `/api/` 前缀），所以后端路由要按 `/api/xxx` 定义（第 9.4 节的 server.js 就是这么写的）。

`web/Dockerfile`：

```dockerfile
FROM nginx:1.27-alpine

LABEL maintainer="docker-lab"
ENV TZ=Asia/Shanghai

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY html/ /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

`web/html/index.html` 里有一个表单和消息列表，`web/html/app.js` 用 fetch 调 `/api/health` 与 `/api/messages`（源码见项目文件，核心逻辑）：

```javascript
async function loadHealth() {
  const res = await fetch('/api/health');
  const data = await res.json();
  statusEl.innerHTML =
    `api 容器 <code>${data.host}</code> 正常；MySQL：<code>${data.db}</code>；` +
    `Redis：<code>${data.redis}</code>；本接口已被访问 <code>${data.hits}</code> 次`;
}
```

### 9.4 api 服务（Node + mysql2 + ioredis）

`api/package.json`：

```json
{
  "name": "dlearn-stack-api",
  "version": "1.0.0",
  "private": true,
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "ioredis": "^5.4.1",
    "mysql2": "^3.11.3"
  }
}
```

`api/server.js`（完整可运行，三个接口：健康检查、查列表、写一条）：

```javascript
'use strict';

const http = require('http');
const os = require('os');
const mysql = require('mysql2/promise');
const Redis = require('ioredis');

const PORT = Number(process.env.PORT || 3000);
const MYSQL_HOST = process.env.MYSQL_HOST || 'db';
const MYSQL_PORT = Number(process.env.MYSQL_PORT || 3306);
const MYSQL_USER = process.env.MYSQL_USER || 'demo';
const MYSQL_PASSWORD = process.env.MYSQL_PASSWORD || 'demo123456';
const MYSQL_DATABASE = process.env.MYSQL_DATABASE || 'demo';
const REDIS_URL = process.env.REDIS_URL || 'redis://cache:6379';

const HOSTNAME = os.hostname();

const pool = mysql.createPool({
  host: MYSQL_HOST,
  port: MYSQL_PORT,
  user: MYSQL_USER,
  password: MYSQL_PASSWORD,
  database: MYSQL_DATABASE,
  waitForConnections: true,
  connectionLimit: 5,
});

const redis = new Redis(REDIS_URL, { maxRetriesPerRequest: 3 });

function send(res, code, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
  });
  res.end(body);
}

async function readJson(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString('utf8');
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (err) {
    return null;
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const path = url.pathname;

  try {
    if (path === '/api/health' && req.method === 'GET') {
      const [rows] = await pool.query('SELECT 1 AS ok');
      const pong = await redis.ping();
      const hits = await redis.incr('api:hits');
      return send(res, 200, {
        status: 'ok',
        host: HOSTNAME,
        db: rows[0].ok === 1 ? 'ok' : 'error',
        redis: String(pong).toLowerCase(),
        hits,
      });
    }

    if (path === '/api/messages' && req.method === 'GET') {
      const [rows] = await pool.query(
        "SELECT id, content, DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at " +
          'FROM t_msg ORDER BY id DESC LIMIT 50'
      );
      return send(res, 200, { count: rows.length, items: rows });
    }

    if (path === '/api/messages' && req.method === 'POST') {
      const body = await readJson(req);
      if (!body || typeof body.content !== 'string' || !body.content.trim()) {
        return send(res, 400, { error: 'content is required' });
      }
      const [result] = await pool.execute('INSERT INTO t_msg (content) VALUES (?)', [
        body.content.trim(),
      ]);
      await redis.del('api:messages');
      return send(res, 201, { id: result.insertId });
    }

    if (path === '/') {
      return send(res, 200, {
        service: 'dlearn-stack-api',
        host: HOSTNAME,
        routes: ['/api/health', '/api/messages'],
      });
    }

    return send(res, 404, { error: 'not found', path });
  } catch (err) {
    return send(res, 500, { error: err.message });
  }
});

server.listen(PORT, () => {
  console.log(`api listening on ${PORT}, hostname=${HOSTNAME}`);
});

for (const signal of ['SIGTERM', 'SIGINT']) {
  process.on(signal, async () => {
    console.log(`received ${signal}, shutting down`);
    server.close();
    await pool.end().catch(() => {});
    redis.disconnect();
    process.exit(0);
  });
}
```

`api/Dockerfile`（非 root + 依赖层缓存 + 生产依赖）：

```dockerfile
FROM node:22-alpine

WORKDIR /app

ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com \
    NODE_ENV=production

# 依赖清单单独一层：只改业务代码时不会重装依赖
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY server.js ./
RUN chown -R node:node /app

# 以非 root 用户运行
USER node

EXPOSE 3000

CMD ["node", "server.js"]
```

### 9.5 db 服务（MySQL + 初始化脚本）

`db/init/01-schema.sql`（只在数据目录为空时执行一次）：

```sql
-- MySQL 容器第一次初始化时（数据目录为空）自动执行本目录下的 sql/脚本
CREATE TABLE IF NOT EXISTS t_msg (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  content    VARCHAR(128) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

INSERT INTO t_msg (content) VALUES ('初始化脚本写入的第一条数据');
```

**反面案例（本机实测）**：最初把 db 的健康检查写成 `start_period: 30s`、`retries: 12`，而在这台机器上 MySQL 8.4 初始化要几分钟（机器上还跑着 milvus、jenkins、nacos 等一堆服务），结果 db 一直 `unhealthy`，导致依赖它的服务全都不启动：

```text
$ docker compose ps
NAME                 IMAGE              COMMAND                   SERVICE   CREATED         STATUS                     PORTS
dlearn-stack-cache   redis:7.4-alpine   "docker-entrypoint.s…"   cache     5 minutes ago   Up 4 minutes (healthy)     6379/tcp
dlearn-stack-db      mysql:8.4          "docker-entrypoint.s…"   db        5 minutes ago   Up 3 minutes (unhealthy)   3306/tcp, 33060/tcp

$ docker compose restart db          # 重启 db，等它的健康检查
$ docker compose up -d
dependency failed to start: container dlearn-stack-db is unhealthy
```

`web`、`api` 两个容器根本没被创建（`docker compose ps` 里看不到），因为 `depends_on` 的条件没满足。**这就是「依赖未就绪」类故障的完整链路**，解法是把 `start_period` 调到覆盖最慢的初始化时间（我们改成了 180s + 30 次重试），或者在初始化慢的服务上不放 `service_healthy` 条件而改用应用侧重试。

### 9.6 端到端验证与数据持久化（实测）

把 `start_period` 提到 180s 之后重新拉起整套服务（本机负载高，MySQL 首次初始化用了约 9 分钟，健康检查通过后 api、web 依次启动）：

```text
$ docker compose -f docker-compose.run.yml up -d
 Container dlearn-stack2-cache Healthy
 Container dlearn-stack2-db Healthy
 Container dlearn-stack2-api Starting
 Container dlearn-stack2-api Started
 Container dlearn-stack2-api Waiting
 Container dlearn-stack2-api Healthy
 Container dlearn-stack2-web Starting
 Container dlearn-stack2-web Started

$ docker compose ps
NAME                  IMAGE                  COMMAND                   SERVICE   CREATED         STATUS                   PORTS
dlearn-stack2-api     dlearn-stack-api:1.0   "docker-entrypoint.s…"   api       2 minutes ago   Up 2 minutes (healthy)
dlearn-stack2-cache   redis:7.4-alpine       "docker-entrypoint.s…"   cache     10 minutes ago  Up 10 minutes (healthy)  6379/tcp
dlearn-stack2-db      mysql:8.4              "docker-entrypoint.s…"   db        10 minutes ago  Up 10 minutes (healthy)  3306/tcp, 33060/tcp
dlearn-stack2-web     dlearn-stack-web:1.0   "/docker-entrypoint.…"   web       1 minute ago    Up 1 minute (healthy)    0.0.0.0:18091->80/tcp
```

四个容器全部 healthy，只有 web 发布了宿主端口。

**第一层：nginx 提供页面、健康检查端点正常**

```text
$ curl -s http://127.0.0.1:18091/ | head -4
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
$ curl -s http://127.0.0.1:18091/healthz
ok
```

**第二层：nginx 反代到 api，api 同时连上 MySQL 与 Redis**

```text
$ curl -s http://127.0.0.1:18091/api/health
{"status":"ok","host":"d00598365053","db":"ok","redis":"pong","hits":4}
```

这一行 JSON 就把三件事全验证了：`host` 是 api 容器的 hostname（说明请求确实到了容器里）、`db":"ok"`（MySQL 查询成功）、`redis":"pong"`（Redis 连通），`hits` 是 Redis 计数器（说明写操作也正常）。

**第三层：写库与读库**

```text
$ curl -s -X POST -H 'Content-Type: application/json' -d '{"content":"从 curl 写入的第二条数据"}' http://127.0.0.1:18091/api/messages
{"id":2}
$ curl -s -X POST -H 'Content-Type: application/json' -d '{"content":"第三条数据"}' http://127.0.0.1:18091/api/messages
{"id":3}
$ curl -s http://127.0.0.1:18091/api/messages
{"count":3,"items":[{"id":3,"content":"第三条数据","created_at":"2026-09-12 10:50:09"},{"id":2,"content":"从 curl 写入的第二条数据","created_at":"2026-09-12 10:50:09"},{"id":1,"content":"åˆå§‹åŒ–è„šæœ¬å†™å…¥çš„ç¬¬ä¸€æ¡æ•°æ®","created_at":"2026-09-12 10:43:00"}]}

$ curl -s -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:18091/api/messages
{"error":"content is required"}
$ curl -s -o /dev/null -w '不存在的接口 -> %{http_code}\n' http://127.0.0.1:18091/api/nope
不存在的接口 -> 404
```

注意 `id:1` 那条是初始化 SQL 写进去的，内容是乱码（`åˆå§‹...`），而通过接口写入的 2、3 两条中文正常——这是字符集问题，原因与解法见「坑 17」。

**第四层：容器之间按服务名互访，数据库不对外暴露**

```text
$ docker compose exec -T web wget -qO- http://api:3000/api/health
{"status":"ok","host":"d00598365053","db":"ok","redis":"pong","hits":5}

$ docker compose exec -T api node -e "const net=require('net');const s=net.connect(3306,'db',()=>{console.log('api 容器能连 db:3306');s.end()});s.on('error',e=>console.log('连不上:',e.message))"
api 容器能连 db:3306

$ docker inspect dlearn-stack2-db --format '{{json .NetworkSettings.Ports}}'
{"3306/tcp":null,"33060/tcp":null}
```

`docker inspect` 的 `Ports` 显示 `{"3306/tcp":null}`——**声明了端口但没有映射到宿主机**，所以宿主机（以及外网）根本连不到这个数据库，只有 backend 网络里的容器能连。前面 curl 的 `/api/*` 全部走 nginx 转发，宿主机上只开放了 18091 一个端口。

网络成员（两个网络各自装着谁）：

```text
$ docker network inspect dlearn-stack2_backend --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
dlearn-stack2-cache 172.23.0.2/16
dlearn-stack2-db 172.23.0.3/16
dlearn-stack2-api 172.23.0.4/16

$ docker network inspect dlearn-stack2_frontend --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
dlearn-stack2-web 172.25.0.2/16
```

**第五层：数据真的落在命名卷上（重建容器不丢数据）**

```text
$ docker compose down          # 删掉所有容器和网络，卷保留
 Container dlearn-stack2-web Stopping / Stopped / Removing / Removed
 Container dlearn-stack2-api Stopping / Stopped / Removing / Removed
 Container dlearn-stack2-cache Stopping / Stopped / Removing / Removed
 Container dlearn-stack2-db Stopping / Stopped / Removing / Removed

$ docker volume ls --filter name=dlearn-stack2
DRIVER    VOLUME NAME
local     dlearn-stack2_cache-data
local     dlearn-stack2_db-data

$ docker compose up -d         # 重新拉起（MySQL 因为数据目录已存在，秒级就绪）
$ curl -s http://127.0.0.1:18091/api/messages
{"count":3,"items":[{"id":3,"content":"第三条数据","created_at":"2026-09-12 10:50:09"},{"id":2,"content":"从 curl 写入的第二条数据","created_at":"2026-09-12 10:50:09"},{"id":1,"content":"åˆå§‹åŒ–è„šæœ¬å†™å…¥çš„ç¬¬ä¸€æ¡æ•°æ®","created_at":"2026-09-12 10:43:00"}]}
```

容器全部重建过，三条数据一条不少——这就是命名卷的价值，也是「`docker compose down` 不会丢数据、`down -v` 才会」的直接证明。

最后停服务时用 `docker compose stop`（保留容器和卷）：

```text
$ docker compose stop
 Container dlearn-stack2-web Stopped
 Container dlearn-stack2-api Stopped
 Container dlearn-stack2-db Stopped
 Container dlearn-stack2-cache Stopped

$ docker compose ps --all
NAME                  IMAGE                  COMMAND                   SERVICE   STATUS
dlearn-stack2-api     dlearn-stack-api:1.0   "docker-entrypoint.s…"   api       Exited (0)
dlearn-stack2-cache   redis:7.4-alpine       "docker-entrypoint.s…"   cache     Exited (0)
dlearn-stack2-db      mysql:8.4              "docker-entrypoint.s…"   db        Exited (0)
dlearn-stack2-web     dlearn-stack-web:1.0   "/docker-entrypoint.…"   web       Exited (0)
```

四个容器都是 `Exited (0)`——优雅退出，没有 137。原因：nginx、MySQL、Redis、Node（我们的 server.js 注册了 SIGTERM 处理）都对 SIGTERM 做了处理（对照第 6.6 节的实测）。



### 9.7 compose 常用命令

```bash
# 起停
docker compose up -d                 # 后台起全部服务
docker compose up -d --build         # 先构建再起
docker compose up -d api             # 只起某个服务（含它依赖的服务）
docker compose stop                  # 停止（保留容器、网络、卷）
docker compose start                 # 启动已停止的容器
docker compose restart api           # 重启单个服务
docker compose down                  # 停止并删除容器+网络（保留卷）
docker compose down -v               # 连卷一起删（数据会丢，谨慎）
docker compose down --rmi local      # 连本地构建的镜像一起删

# 观察
docker compose ps                    # 状态（含健康检查结果）
docker compose ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}'
docker compose logs -f --tail=50 api
docker compose top                   # 每个服务的进程
docker compose images                # 用到的镜像
docker compose config                # 渲染后的最终配置（排查变量替换）
docker compose ls                    # 这台机器上有哪些 compose 项目

# 操作
docker compose exec api sh           # 进容器（注意不是 docker exec）
docker compose exec -T db mysql -uroot -p密码
docker compose run --rm api node -e "console.log('一次性任务')"   # 一次性容器
docker compose scale api=3            # 扩容（要求不写 container_name、不映射固定宿主端口）
docker compose pull                  # 拉取所有镜像
```

三个高频注意点：

- `docker compose exec` 默认带 TTY，**脚本里要加 `-T`**（否则报 `the input device is not a TTY`）。
- `docker compose` 命令必须在有 compose 文件的目录（或 `-f` 指定文件）执行；文件查找顺序是 `compose.yaml` → `compose.yml` → `docker-compose.yaml` → `docker-compose.yml`。
- 服务名用于 `exec`/`logs`/`restart`，**容器名用于 `docker exec`**，两者不是一回事。设了 `container_name` 之后容器名固定，服务名仍然用于 compose 命令。

## 10. 私有镜像仓库 Registry

镜像要在多台机器之间流转，靠 `docker save` 拷 tar 包只能救急。标准做法是搭一个私有仓库，`docker push` / `docker pull` 走内网。

### 10.1 起一个最小的私有仓库

官方 `registry:2` 镜像就是完整的 Registry 实现（5000 端口）：

```text
$ docker pull registry:2
2: Pulling from library/registry
b537bf6d1146: Download complete
32a76c78501f: Download complete
...
Digest: sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373
Status: Downloaded newer image for registry:2

$ docker run -d --name dlearn-registry -p 15000:5000 \
  -v dlearn-registry-data:/var/lib/registry \
  -e REGISTRY_STORAGE_DELETE_ENABLED=true \
  registry:2
fe1b58cf57ed87b9c6128891f016190a323ed7faa0aa839baf5402497ae6242f

$ curl -s -o /dev/null -w 'GET /v2/ -> %{http_code}\n' http://127.0.0.1:15000/v2/
GET /v2/ -> 200
```

三个参数的意义：`-v dlearn-registry-data:/var/lib/registry` 把镜像数据放到命名卷（否则删容器就丢）；`REGISTRY_STORAGE_DELETE_ENABLED=true` 允许删除操作；`-p 15000:5000` 用 15000 是为了避开宿主机上可能已占用的 5000。

### 10.2 打标签与推送

镜像名里的第一段（`127.0.0.1:15000`）就是「推到哪个仓库」：

```text
$ docker tag alpine:3.20 127.0.0.1:15000/demo/alpine:3.20
$ docker image inspect 127.0.0.1:15000/demo/alpine:3.20 --format 'RepoTags={{json .RepoTags}}'
RepoTags=["127.0.0.1:15000/demo/alpine:3.20","alpine:3.20"]

$ docker push 127.0.0.1:15000/demo/alpine:3.20
The push refers to repository [127.0.0.1:15000/demo/alpine]
25f1d6b1951a: Pushed
3.20: digest: sha256:c64c687cbea9300178b30c95835354e34c4e4febc4badfe27102879de0483b5e size: 1023

 Info -> Not all multiplatform-content is present and only the available single-platform image was pushed
         sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc -> sha256:c64c687cbea9300178b30c95835354e34c4e4febc4badfe27102879de0483b5e
```

`tag` 只是加了一个指针，两个名字指向同一个镜像 ID，不额外占空间。push 时按层上传，输出里每条 `xxx: Pushed` 就是一个层（已存在的层会显示 `Layer already exists`，这是换台机器推同一个镜像时最常见的日志）。

用 Registry 的 HTTP API 核对内容（排查 push 是否真的成功、有哪些 tag）：

```text
$ curl -s http://127.0.0.1:15000/v2/_catalog
{"repositories":["demo/alpine"]}

$ curl -s http://127.0.0.1:15000/v2/demo/alpine/tags/list
{"name":"demo/alpine","tags":["3.20"]}
```

### 10.3 删掉本地镜像，再从私有仓库拉回来

```text
$ docker rmi 127.0.0.1:15000/demo/alpine:3.20
Untagged: 127.0.0.1:15000/demo/alpine:3.20

$ docker pull 127.0.0.1:15000/demo/alpine:3.20
3.20: Pulling from demo/alpine
Digest: sha256:c64c687cbea9300178b30c95835354e34c4e4febc4badfe27102879de0483b5e
Status: Downloaded newer image for 127.0.0.1:15000/demo/alpine:3.20
127.0.0.1:15000/demo/alpine:3.20

$ docker image ls --filter reference='127.0.0.1:15000/demo/alpine'
IMAGE                              ID             DISK USAGE   CONTENT SIZE   EXTRA
127.0.0.1:15000/demo/alpine:3.20   c64c687cbea9       12.1MB         3.63MB

$ docker run --rm 127.0.0.1:15000/demo/alpine:3.20 cat /etc/os-release
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.20.10
PRETTY_NAME="Alpine Linux v3.20"
```

### 10.4 仓库数据落在卷上

```text
$ docker volume inspect dlearn-registry-data
$ docker exec dlearn-registry find /var/lib/registry -maxdepth 4 -type d | head -12
/var/lib/registry
/var/lib/registry/docker
/var/lib/registry/docker/registry
/var/lib/registry/docker/registry/v2
/var/lib/registry/docker/registry/v2/blobs
/var/lib/registry/docker/registry/v2/blobs/sha256
...
```

换机器只迁移这个卷（或它的 tar 备份），所有镜像就跟着走了。

### 10.5 HTTP 仓库要配 insecure-registries

上面能直接 push 是因为**客户端把 `127.0.0.1` 和 `localhost` 当成本地地址，默认允许走 HTTP**。换成内网 IP 或域名（例如 `192.168.1.20:5000`）就会报错：

```text
$ docker push 192.168.1.20:5000/demo/app:1.0
The push refers to repository [192.168.1.20:5000/demo/app]
Get "http://192.168.1.20:5000/v2/": dial tcp 192.168.1.20:5000: connect: connection refused
```

两种解法：

1. 用 HTTPS（生产推荐：给仓库配域名和证书，或前面挂一个 nginx 做 TLS 终止）。
2. 每个**客户端**的 `/etc/docker/daemon.json` 里声明这个仓库是 HTTP：

```json
{
  "insecure-registries": ["192.168.1.20:5000"]
}
```

改完必须重启 docker（`systemctl restart docker`）。注意 `insecure-registries` 是客户端配置，改服务端没用；而且这一项在多用户场景下要逐个 daemon 配置（rootless 用户改自己的 `~/.config/docker/daemon.json`）。

### 10.6 生产上还需要什么

`registry:2` 只有存储和分发，没有页面、权限、清理策略。企业内网一般用 Harbor（Apache 2.0，自带 Web UI、项目级 RBAC、镜像扫描、垃圾回收），部署方式也是 compose 或 Helm：

| 需求 | registry:2 | Harbor |
|---|---|---|
| 推送/拉取 | 支持 | 支持 |
| Web 界面检索 | 无 | 有 |
| 用户/项目权限 | 无（只有 basic auth 的简易方案） | RBAC，项目隔离 |
| 漏洞扫描 | 无 | 集成 Trivy |
| 镜像清理（GC） | 需手工调 API | 界面操作 |
| 复制到异地仓库 | 无 | 支持 |

教学顺序建议：先用 `registry:2` 把 tag/push/pull 的原理讲透，再说 Harbor 是「加了权限和界面的 registry」，避免一上来就陷进 Harbor 的部署细节。

## 11. 生产运行要点

前面把「怎么跑起来」讲完了，这一章讲「怎么跑得住」：资源限制、只读、时区、日志、健康检查、非 root、密钥、标签策略。

### 11.1 资源限制：不让一个容器拖垮整机

`docker run` 的资源参数（compose 里是同名的 `deploy.resources` / `mem_limit` 等）：

```bash
--memory=512m --memory-swap=512m   # 内存上限（swap 与 memory 相等表示禁用 swap）
--cpus=1.5                         # 最多用 1.5 个核
--cpu-shares=512                   # 相对权重（只在争抢时生效，默认 1024）
--pids-limit=200                   # 进程数上限
--blkio-weight=500                 # 磁盘 IO 权重
--ulimit nofile=65535:65535        # 文件句柄上限
```

**内存超限会被杀，而且日志里看不出原因**（实测）：

```text
$ docker run -d --name dlearn-oom --memory=100m --memory-swap=100m node:22-alpine \
    node -e "const a=[]; setInterval(() => a.push(Buffer.alloc(8*1024*1024,'x')), 50);"
2fc03d1d0770ed8229cf356fa31bbc07ccc9d8ca93310570674be4ae4d05419d

$ docker ps -a --filter name=dlearn-oom
CONTAINER ID   IMAGE            COMMAND                   CREATED          STATUS           PORTS     NAMES
2fc03d1d0770   node:22-alpine   "docker-entrypoint.s…"   55 seconds ago   Exited (137) 22 seconds ago             dlearn-oom

$ docker inspect dlearn-oom --format 'OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}} Memory={{.HostConfig.Memory}}'
OOMKilled=true ExitCode=137 Memory=104857600

$ docker logs dlearn-oom
（空）
```

`Exited (137)` + `docker logs` 是空的 + `OOMKilled=true`，这是内存超限的标准三件套。Java 服务尤其要注意：JVM 默认按**宿主机**内存算堆大小，容器限制 512M 而 JVM 按 16G 算堆，起来就被 OOM Killed。解法是让 JVM 感知容器（JDK 10+ 默认开启 `UseContainerSupport`）：

```bash
java -XX:MaxRAMPercentage=75.0 -jar app.jar     # 按容器内存的 75% 设堆
```

**CPU 限制是限速，不是隔离**（实测同一段计算量）：

```text
$ 默认（不限制 CPU）
耗时 1348ms
$ --cpus=0.5（最多用半个核）
耗时 2560ms
$ --cpus=4
耗时 1406ms
```

`--cpus=0.5` 时耗时约翻倍，符合预期；`--cpus=4` 和默认差不多，因为这段代码是单线程的（起不了并行）。讲解时用这个例子说明：**CPU 限制对单线程程序的影响是线性的，对多线程程序要看能否并行**。

**进程数限制可以挡住 fork 炸弹**（实测）：

```text
$ docker run --rm --pids-limit 20 alpine:3.20 sh -c 'for i in $(seq 1 40); do sleep 100 & done; wait'
（被限制在第 20 个进程，后续 fork 失败）
```

### 11.2 只读根文件系统

```text
$ docker run --rm --read-only alpine:3.20 sh -c 'touch /newfile'
touch: /newfile: Read-only file system

$ docker run --rm --read-only --tmpfs /tmp alpine:3.20 sh -c 'echo ok > /tmp/newfile; ls -l /tmp/newfile; echo "tmpfs 可写"'
-rw-r--r--    1 root     root             3 Sep 12 02:24 /tmp/newfile
tmpfs 可写

# 默认情况下根文件系统是可写的
$ docker run --rm alpine:3.20 sh -c 'touch /newfile && ls -l /newfile && echo "默认根文件系统可写"'
-rw-r--r--    1 root     root             0 Sep 12 02:25 /newfile
默认根文件系统可写
```

`--read-only` 的意义是防篡改：即使应用被拿下了，攻击者也没法往镜像里写 webshell、放持久化脚本。要写的地方用 `--tmpfs` 或挂卷单独放开。注意很多镜像需要写 `/tmp`、`/run`、日志目录，配的时候要一个一个试（起不来先看日志里的 `Read-only file system`）。

### 11.3 时区：容器默认是 UTC

```text
$ docker run --rm alpine:3.20 date
Sat Sep 12 02:26:47 UTC 2026

$ date            # 宿主机是 CST
2026年 09月 12日 星期六 10:28:30 CST

$ docker run --rm -e TZ=Asia/Shanghai alpine:3.20 date
Sat Sep 12 02:27:27 UTC 2026      # 注意：还是 UTC

$ docker run --rm -v /etc/localtime:/etc/localtime:ro -e TZ=Asia/Shanghai alpine:3.20 date
Sat Sep 12 02:28:18 UTC 2026      # 也是 UTC
```

**alpine 镜像里没有 tzdata，光设 `TZ` 环境变量不生效**（时区库文件不存在，回退到 UTC）。Node/Java 这类自带时区数据的基础镜像里 `-e TZ=Asia/Shanghai` 是有效的（实测 Node）：

```text
$ docker run --rm node:22-alpine node -e "console.log('node 看到的时区:', new Date().toString())"
node 看到的时区: Sat Sep 12 2026 02:28:47 GMT+0000 (Coordinated Universal Time)

$ docker run --rm -e TZ=Asia/Shanghai node:22-alpine node -e "console.log('node 看到的时区:', new Date().toString())"
node 看到的时区: Sat Sep 12 2026 10:28:47 GMT+0800 (中国标准时间)
```

三种让容器用上正确时区的做法（按推荐顺序）：

```dockerfile
# 1. 镜像里装 tzdata 并设默认时区（推荐，一次搞定）
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
```

```bash
# 2. 运行时挂载宿主机的时区文件 + 环境变量（不需要改镜像）
docker run -e TZ=Asia/Shanghai -v /etc/localtime:/etc/localtime:ro 镜像名
```

```bash
# 3. 对 Java 单独指定（JVM 不认 TZ 的某些写法时用）
docker run -e JAVA_TOOL_OPTIONS="-Duser.timezone=Asia/Shanghai" 镜像名
```

时区错了会导致什么：日志时间戳差 8 小时（排查问题时对不上）、定时任务在错误的时刻触发、订单/账单日期错一天。属于「不疼不痒但迟早出事」的配置项，镜像里统一设好最省心。

### 11.4 日志：落盘位置、查看技巧、轮转

```text
$ docker logs --tail 3 dlearn-logger
log line 4
log line 5
log line 6

$ docker logs --tail 3 --timestamps dlearn-logger
2026-09-12T02:30:16.774652248Z log line 4
2026-09-12T02:30:17.775190937Z log line 5
2026-09-12T02:30:18.775850792Z log line 6

$ docker logs --since 3s dlearn-logger
log line 3
log line 4
log line 5
log line 6

$ docker inspect dlearn-logger --format 'LogPath={{.LogPath}} LogDriver={{.HostConfig.LogConfig.Type}} LogOpts={{json .HostConfig.LogConfig.Config}}'
LogPath=/var/lib/docker/containers/39c17a41.../39c17a41...-json.log LogDriver=json-file LogOpts={"max-file":"3","max-size":"100m"}
```

日志文件的真实内容就是 JSON 行（每行带时间戳与流名称）：

```text
$ head -c 300 /var/lib/docker/containers/39c17a41.../39c17a41...-json.log
{"log":"log line 1\n","stream":"stdout","time":"2026-09-12T02:30:13.772663763Z"}
{"log":"log line 2\n","stream":"stdout","time":"2026-09-12T02:30:14.773339962Z"}
{"log":"log line 3\n","stream":"stdout","time":"2026-09-12T02:30:15.774026056Z"}
```

实用技巧：

```bash
docker logs -f --since 10m 容器名              # 跟日志，从 10 分钟前开始
docker logs --tail 200 容器名 | grep ERROR
docker compose logs -f --tail=50 api           # compose 里按服务看
docker logs 容器名 2>&1 | head -1              # 只看第一行（启动报错通常在这里）
```

**生产必须配日志轮转**，否则一个死循环打日志的容器能写满磁盘（本机 daemon.json 已配 `max-size: 100m`、`max-file: 3`，即每容器最多 300MB）。也可以按容器单独指定：

```bash
docker run --log-opt max-size=50m --log-opt max-file=5 镜像名
```

日志量大的场景换成 `journald`、`fluentd`、`gelf`、`awslogs` 等驱动（`docker info` 的 `Log:` 一行能看到本机支持哪些），但注意：**换了驱动之后 `docker logs` 可能就看不到内容了**（内容被送到别处了）。

### 11.5 健康检查

镜像里定义（第 6.1 节示例）或运行时指定：

```bash
docker run --health-cmd 'wget -qO- http://127.0.0.1/healthz || exit 1' \
           --health-interval 10s --health-timeout 3s --health-retries 3 --health-start-period 5s 镜像名
```

三个参数的取舍：`interval` 别太短（检查本身也是开销）；`timeout` 要小于 `interval`；`start-period` 是留给应用启动的宽限期（本机实测 MySQL 初始化要几分钟，这个值给小了会一直 `unhealthy`，进而拖垮依赖它的服务——第 9 章有真实案例）。

查看状态与历史：

```bash
docker ps                                  # STATUS 列显示 (healthy) / (unhealthy) / (health: starting)
docker inspect 容器名 --format '{{.State.Health.Status}}'
docker inspect 容器名 --format '{{json .State.Health}}'
docker inspect 容器名 --format '{{range .State.Health.Log}}{{.ExitCode}} {{.Output}}{{end}}'   # 每次检查的输出
```

`unhealthy` **不会自动重启容器**，也不会自动摘流量（单机 Docker 没有负载均衡层）。它的价值是：compose 的 `depends_on: condition: service_healthy` 能用它做启动门禁、监控系统能告警。要让「不健康就重启」，得自己写守护逻辑或者上编排系统（K8S 的 liveness 探针就是干这个的）。

### 11.6 非 root 运行

```text
$ docker run --rm dlearn-nonroot:1.0
当前用户: node uid: 1000
可以写 /app（工作目录已 chown 给 node）
写 / 失败: EACCES

$ docker run --rm alpine:3.20 sh -c 'id'
uid=0(root) gid=0(root) groups=0(root),...
```

默认是 root，生产镜像要显式切：

```dockerfile
FROM node:22-alpine
WORKDIR /app
RUN chown -R node:node /app      # 工作目录要给运行用户
USER node                        # 官方 node 镜像自带 uid=1000 的 node 用户
COPY --chown=node:node server.js ./
CMD ["node", "server.js"]
```

要点：`USER` 之后的 `COPY` 默认还是 root 属主，要用 `--chown`；只读的静态资源不需要改属主；Java 镜像常用 `USER 1000`（数字 uid，避免宿主和镜像里用户名不一致的坑）。好处是即使容器被突破，攻击者也只有普通用户权限（配合第 11.2 节的只读根、第 11.1 节的资源限制，构成基础加固）。

### 11.7 构建期密钥：ARG 会留在镜像历史里

```text
$ docker build --build-arg APP_VERSION=2.3.1 --build-arg BUILD_TOKEN=super-secret-token -t dlearn-args:1.0 ./06-args
 1 warning found (use docker --debug to expand):
 - SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data (ARG "BUILD_TOKEN") (line 6)

$ docker history --no-trunc dlearn-args:1.0
<missing>  3 minutes ago  RUN |2 APP_VERSION=2.3.1 BUILD_TOKEN=super-secret-token /bin/sh -c echo "构建时看到 APP_VERSION=${APP_VERSION}，令牌长度=${#BUILD_TOKEN}" # buildkit   4.1kB
<missing>  3 minutes ago  ARG BUILD_TOKEN=super-secret-token                                                                                                         0B
```

**用 `ARG` 传密钥等于把密钥写进镜像**：`docker history` 一查就出来（构建时工具已经给了 `SecretsUsedInArgOrEnv` 警告，直接忽略是不行的）。正确做法是 BuildKit 的 secret：

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-alpine
WORKDIR /app
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc -t app:1.0 .
```

secret 只在构建时挂载、不进任何层、`docker history` 里看不到。运行时的密钥则用环境变量（配合编排系统的 secret 管理）或只读文件挂载，**不要固化进镜像**。

另外 BuildKit 的缓存挂载能把依赖缓存放在构建缓存里跨构建复用（`RUN --mount=type=cache,target=/root/.npm npm ci`），本机实测首次构建 2m17s：

```text
#8 [stage-0 4/4] RUN --mount=type=cache,target=/root/.npm npm ci
#8 16.13 added 21 packages in 1s
#8 DONE 24.0s
```

（这段缓存挂载的对比实验里，第二次构建因为我在 package.json 里追加了一行非 JSON 注释而报 `npm error code EJSONPARSE` 失败——顺带说明 `package.json` 必须是严格 JSON，不能写注释。）

### 11.8 优雅停机

要点在第 6.6 节已经实测过：`docker stop` 只给 PID 1 发信号（默认 SIGTERM，可用 `STOPSIGNAL` 改）；PID 1 不处理信号就会等 10 秒超时被 SIGKILL（退出码 137）。生产上做到三件事：

1. 启动命令用 exec 形式，业务进程就是 PID 1；
2. 应用注册信号处理（Spring Boot：`server.shutdown=graceful` + `spring.lifecycle.timeout-per-shutdown-phase=30s`；Node：`process.on('SIGTERM', ...)`）；
3. 需要更长时间收尾时 `docker stop -t 60`，或者给容器加 `--init`。

### 11.9 镜像标签与版本策略

```bash
# 不推荐
docker tag app:latest registry.local/team/app:latest

# 推荐：语义化版本 + 提交号/构建号 + 环境
registry.local/team/app:1.4.2-20260912-1
registry.local/team/app:1.4.2
```

- 生产部署用明确版本号（谁都能追溯是哪次构建），不要用 `latest`。
- 需要绝对可复现时用 digest：`registry.local/team/app@sha256:...`。
- 保留策略：只保留最近 N 个版本 + 每个正式版本，旧的可删（仓库侧做 GC）。
- 多阶段构建的中间镜像不要在 CI 里推送到仓库（只推最终镜像的 tag）。

### 11.10 两个可直接用的生产级 Dockerfile 模板

Java（Spring Boot，多阶段 + JRE + 非 root + 时区 + 优雅停机）：

```dockerfile
# ---------- 构建阶段 ----------
FROM maven:3.8-openjdk-8-slim AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src ./src
RUN mvn -q -B clean package -DskipTests

# ---------- 运行阶段 ----------
FROM eclipse-temurin:8-jre
LABEL maintainer="ops@example.com"

ENV TZ=Asia/Shanghai \
    JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75.0 -Duser.timezone=Asia/Shanghai"

WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar

RUN groupadd -g 1000 app && useradd -u 1000 -g app -m app && chown -R app:app /app
USER 1000

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -fs http://127.0.0.1:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

Node（前后端一体或纯 API）：

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM node:22-alpine
LABEL maintainer="ops@example.com"
ENV NODE_ENV=production \
    TZ=Asia/Shanghai

WORKDIR /app
RUN apk add --no-cache tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/dist ./dist
COPY --from=builder --chown=node:node /app/package.json ./

USER node
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/api/health || exit 1

CMD ["node", "dist/server.js"]
```

## 12. 镜像瘦身与磁盘清理

### 12.1 镜像瘦身的六个手段

按收益从大到小排（每一条都在第 4~6 章有实测依据）：

| 手段 | 效果 | 示例 |
|---|---|---|
| 换更小的基础镜像 | 常用 100MB~1GB → 20MB~200MB | `node:22` → `node:22-alpine`；`maven` 只在构建阶段用 |
| 多阶段构建 | 去掉构建工具和依赖目录 | 前端 259MB → 73.6MB（第 6.7 节实测） |
| 合并 RUN 并清理缓存 | 少几层、少几百 MB | `RUN apt-get update && apt-get install -y x && rm -rf /var/lib/apt/lists/*` |
| 用 .dockerignore 排除 | 上下文和镜像一起瘦 | 20.98MB → 213B（第 6.4 节实测） |
| `COPY` 精确到文件/目录 | 别 `COPY . .` | `COPY dist/ /usr/share/nginx/html/` |
| 依赖只装生产所需 | 少几十 MB | `npm ci --omit=dev`、`pip install --no-cache-dir -r requirements.txt` |

同一类指令的写法差异（`RUN` 的层数效应）：

```dockerfile
# 不推荐：三层，且 apt 缓存全部留在镜像里
RUN apt-get update
RUN apt-get install -y curl vim
RUN rm -rf /var/lib/apt/lists/*

# 推荐：一层，安装与清理在同一条命令里
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl vim \
 && rm -rf /var/lib/apt/lists/*
```

Java 项目常见的三档瘦身（示意的体积量级，供讲解时对比）：

```text
openjdk:8-jdk           约 640MB   JDK + 完整 Debian
eclipse-temurin:8-jre   约 118MB   只要 JRE（本机实测 CONTENT SIZE）
eclipse-temurin:8-jre-alpine  约 60MB   musl 版 JRE，注意 glibc 依赖问题
```

### 12.2 磁盘都去哪了：docker system df

```text
$ docker system df
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          33        24        34.69GB   3.521GB (10%)
Containers      25        13        1.668GB   745.1MB (44%)
Local Volumes   7         5         3.787GB   88.56kB (0%)
Build Cache     284       0         11.23GB   8.356GB
```

四类占用对应的清理命令：

| 类型 | 查看 | 清理 |
|---|---|---|
| 镜像 | `docker image ls` | `docker image prune -a`（删掉所有没被容器使用的镜像） |
| 容器 | `docker ps -a` | `docker container prune`（删掉所有已停止的容器） |
| 卷 | `docker volume ls` | `docker volume prune`（删掉没被引用的卷） |
| 构建缓存 | `docker system df` | `docker builder prune` |
| 网络 | `docker network ls` | `docker network prune` |

### 12.3 真实清理一次构建缓存

构建缓存是磁盘占用增长最快的一项（本机 284 个缓存条目、11.23GB）。只清 48 小时前的缓存，实测回收 5.667GB：

```text
$ docker builder prune -f --filter until=48h
zfcifahmwoymmopa967y63jsm               true    212.2MB   3 weeks ago
Total:  5.667GB
```

按 label 精确清理某组镜像（推荐做法，不会碰到同机其他人的资源）：

```bash
# 只清带指定 label 的镜像
docker image prune -a -f --filter label=maintainer=docker-lab
# 只清名字带前缀的容器
docker ps -aq --filter name=dlearn- | xargs -r docker rm -f
# 只清本项目的卷
docker volume ls -q --filter name=dlearn- | xargs -r docker volume rm
```



### 12.3 清理的三条铁律

这三条是踩过坑之后总结的，讲解时一定要说：

1. **`docker system prune -a --volumes` 是核弹，不要在客户机器上随手敲**。它删掉所有未被运行中容器使用的镜像、停止的容器、没用到的网络和卷。数据库卷只要当时没有正在运行的容器引用，就会被删——数据不可恢复。要清理就按类型分步来，每步先 `ls` 确认。
2. **清理前先看 RECLAIMABLE 那一列**，而不是看 TOTAL。TOTAL 大不代表能清，只有未被使用的部分可回收（镜像共享层也会让 RECLAIMABLE 显得很小）。
3. **停掉的服务不要用 `down -v` 收尾**。`docker compose down`（不带 `-v`）保留卷，`down -v` 会连卷一起删；排查「重启后数据没了」时，先看 compose 命令里有没有 `-v`。

### 12.4 一个可直接用的安全清理脚本

```bash
#!/usr/bin/env bash
# 安全清理：只清本项目/本标签的产物，其他资源一律不动
set -euo pipefail

LABEL="maintainer=my-team"

echo "== 清理前 =="
docker system df

echo "== 1. 删除本项目带 label 的镜像（含没被使用的） =="
docker image prune -a -f --filter "label=${LABEL}"

echo "== 2. 删除已退出的本项目容器 =="
docker ps -a --filter "label=${LABEL}" --filter "status=exited" -q | xargs -r docker rm

echo "== 3. 删除没人引用的本项目卷 =="
docker volume ls -q --filter "label=${LABEL}" | xargs -r docker volume rm

echo "== 4. 清理 48 小时前的构建缓存 =="
docker builder prune -f --filter until=48h

echo "== 清理后 =="
docker system df
```

要点：`--filter label=` 是最安全的做法——Dockerfile 里写 `LABEL maintainer="my-team"`，清理时按 label 精确命中自己的资源，不会误删同机上别人的东西（这也是第 14 章多用户场景下必须遵守的约定）。

## 13. 故障排查手册

下面每一条都是本机实测踩出来的，按「现象 → 真实报错 → 原因 → 解法」整理。

### 13.1 五步法：先看状态，再看日志，最后才动手

```bash
docker ps -a                                  # 1. 容器在不在、什么状态、退出码
docker inspect 容器名 --format '{{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}}'
docker logs --tail 100 --timestamps 容器名     # 2. 业务自己吐的日志
docker inspect 容器名 | head -60               # 3. 配置对不对（挂载、环境变量、网络、命令）
docker exec -it 容器名 sh                      # 4. 进得去就进去看（进不去说明进程已死）
docker events --since 10m --until 0s           # 5. 看 daemon 层面发生了什么
```

退出码速查（决定了往哪个方向查）：

| 退出码 | 含义 | 常见原因 |
|---|---|---|
| 0 | 正常结束 | 一次性任务跑完；长驻进程被优雅停止 |
| 1 | 应用自身报错 | 配置缺失、连不上数据库、端口被占 |
| 125 | docker 命令本身失败 | `docker run` 参数错误、端口已分配 |
| 126 / 127 | 命令不可执行 / 找不到 | `CMD` 写错、镜像里没有这个可执行文件 |
| 137 | 被 SIGKILL | 内存超限（OOMKilled=true）、`docker stop` 超时 |
| 143 | 被 SIGTERM | 正常收到停止信号（配合优雅停机） |
| 139 | 段错误 | 二进制与镜像架构不匹配（arm64 镜像跑在 amd64 上） |

### 13.2 容器起不来 / 起来就退

**现象一：`exec: "hello": executable file not found in $PATH`（退出码 127）**

```text
$ docker run --rm dlearn-cmd:1.0 hello docker
docker: Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: exec: "hello": executable file not found in $PATH
```

原因：镜像的 `CMD` 是 `["echo","default-cmd"]`，命令行给了参数就**整体替换**了 `CMD`，于是 docker 去找 `hello` 这个可执行文件。解法：写全命令（`docker run dlearn-cmd:1.0 echo hello docker`），或者改用 `ENTRYPOINT` + 参数追加的写法（第 6.5 节）。

**现象二：容器跑了但立刻退出，日志是空的**

多数是主进程前台化没做对。`docker ps -a` 看到 `Exited (0)` 说明命令执行完就结束了，比如 `cmd: nginx`（没有 `daemon off;`）。解法：让主进程保持前台（`CMD ["nginx","-g","daemon off;"]`），或在 Dockerfile 里查看基础镜像文档推荐的启动方式。

**现象三：反复重启，`RestartCount` 一直涨**

```text
$ docker inspect dlearn-restart3 --format 'RestartCount={{.RestartCount}} Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
RestartCount=3 Status=exited ExitCode=2
```

重启策略把「启动即失败」掩盖成了「随机不可用」。解法：先 `--restart=no` 跑一次看清真实报错，修好再加回策略；生产上必须配健康检查。

**现象四：`Permission denied` / `Read-only file system`**

```text
$ docker run --rm --read-only alpine:3.20 sh -c 'touch /newfile'
touch: /newfile: Read-only file system
```

镜像用了 `--read-only` 或 `USER` 非 root，写目录需要提前 `chown` 或加可写的挂载/`--tmpfs`。

### 13.3 端口相关

**现象一：端口已被占用（启动就失败，退出码 125）**

```text
Bind for 0.0.0.0:18101 failed: port is already allocated
```

排查：`ss -lntp | grep 18101` 看是谁占的（可能是 docker-proxy，也可能是宿主机的其他服务）；`docker ps --format '{{.Names}} {{.Ports}}' | grep 18101` 看是不是被别的容器占了。解法：改宿主机端口（`-p 18102:80`），或停掉旧容器。**注意：`docker ps` 里看不到停止容器的端口占用，实际上停止的容器不占端口。**

**现象二：容器里（或宿主机上）`curl` 返回 000 / `Connection reset by peer`**

```text
$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18085/
000
$ echo $?
56
```

这是**服务还没就绪**的典型症状（exit 56 = 连接被重置）：`docker run -d` 返回时容器的 web 服务往往还在启动。解法：脚本里做就绪轮询，或者用健康检查：

```bash
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18085/) || true
  [ "$code" = "200" ] && { echo "ready in ${i}s"; break; }
  sleep 1
done
```

**现象三：宿主机能访问，别的机器访问不了**

三种可能：`-p 127.0.0.1:8080:80` 只监听了回环；宿主机防火墙没放行该端口；容器里服务只监听 `127.0.0.1` 而不是 `0.0.0.0`（用 `docker exec 容器 ss -lnt` 确认）。

### 13.4 网络与 DNS

**现象一：`ping: bad address 'dlearn-b'`**

```text
$ docker exec dlearn-a ping -c 1 -W 2 dlearn-b
ping: bad address 'dlearn-b'
```

原因：两个容器在**默认 bridge** 上，没有内置 DNS。解法：创建自定义网络并把双方接进去（第 8.3 节），或者临时用 IP。

**现象二：`nslookup` 报 NXDOMAIN，但 ping 能通**

```text
$ docker exec dlearn-c nslookup dlearn-d
** server can't find dlearn-d.tailc6bb9f.ts.net: NXDOMAIN
```

原因：容器里的 `search` 域名把短名补全成了完整域名，`nslookup` 查不到。这不是故障——用 `getent hosts dlearn-d` 验证解析更可靠。

**现象三：容器访问不了宿主机上的服务**

容器里的 `127.0.0.1` 是容器自己：

```text
$ docker run --rm alpine:3.20 sh -c 'wget -qO- -T3 http://127.0.0.1:15672/ | head -3'
wget: can't connect to remote host (127.0.0.1): Connection refused
```

解法：用 `--network host`（实测可直接通）、或 `--add-host=host.docker.internal:host-gateway` 后用 `host.docker.internal:15672`、或用 `docker0` 网关地址（通常 `172.17.0.1`）。

### 13.5 数据与卷

**现象一：数据没了 / 数据库报「表不存在」**

先确认卷是否挂上：

```bash
docker inspect 容器名 --format '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}{{"\n"}}{{end}}'
```

没挂载就是走了容器可写层；挂了卷但数据没了，检查是不是执行过 `docker compose down -v` 或 `docker volume rm`。

**现象二：MySQL 报数据文件损坏（本机实测，真实报错）**

```text
2026-09-12T02:04:31.333906Z 1 [ERROR] [MY-012960] [InnoDB] Cannot create redo log files because data files are corrupt or the database was not shut down cleanly after creating the data files.
2026-09-12T02:04:31.333960Z 1 [ERROR] [MY-012930] [InnoDB] Plugin initialization aborted with error Generic error.
2026-09-12T02:04:31.458538Z 0 [ERROR] [MY-010020] [Server] Data Dictionary initialization failed.
2026-09-12T02:04:31.458549Z 0 [ERROR] [MY-010119] [Server] Aborting
```

原因：MySQL 8.4 **首次初始化数据目录很慢**（本机高负载下用了 2~5 分钟，日志里能看到 `Initializing database files`），在初始化没完成时用 `docker rm -f` 强杀容器，InnoDB 的数据文件与 redo log 处于不一致状态，卷就坏了。之后挂同一个卷起新容器，直接报上面的错并退出。

解法：

```bash
# 1. 确认初始化状态：日志里出现 "ready for connections" 才算完成
docker logs --tail 20 dlearn-mysql
# 2. 初始化期间不要动它；要停就 docker stop（留足时间）
docker stop -t 120 dlearn-mysql
# 3. 已经坏了：数据不要了就直接删卷重新初始化
docker rm -f dlearn-mysql && docker volume rm dlearn-mysql-data
# 4. 数据要保留：用 mysqldump 在旧容器能起来时导出，或从备份恢复
```

同理，MySQL 容器没就绪时 `docker exec ... mysql` 会报：

```text
ERROR 2003 (HY000): Can't connect to MySQL server on '127.0.0.1:3306' (111)
```

**现象三：卷删不掉**

```text
$ docker volume rm dlearn-mysql-restore
Error response from daemon: remove dlearn-mysql-restore: volume is in use - [bd3386bda9cb97c94d5ea821c8ac2cb6736c6bb7b4c4b6bb03184c896d05ac51]
```

原因：还有容器（含**已停止**的容器）引用它。解法：先 `docker ps -a --filter volume=dlearn-mysql-data` 找到引用者并删除容器，再删卷。

### 13.6 镜像与仓库

**现象一：`No such image` / `tag does not exist`**

```text
$ docker tag dlearn-stack-api:1.0 127.0.0.1:15000/demo/stack-api:1.0
Error response from daemon: No such image: dlearn-stack-api:1.0
```

说明本地没有这个 tag（可能构建失败、或构建出来的镜像名不同）。先 `docker image ls | grep 关键词` 确认。

**现象二：拉取镜像超时（国内环境最常见）**

```text
docker: Error response from daemon: failed to resolve reference "docker.io/library/hello-world:latest": failed to do request: Head "https://registry-1.docker.io/v2/library/hello-world/manifests/latest": dial tcp [2a03:2880:f12d:83:face:b00c:0:25de]:443: i/o timeout
```

三种解法：配镜像加速（第 2.4 节）；离线导入（`docker load -i xxx.tar`）；换 `hub-mirror` 类代理。**注意 rootless 用户不吃 `/etc/docker/daemon.json`，要单独配 `~/.config/docker/daemon.json`**（第 14 章实测）。

**现象三：push 到私有仓库失败**

```text
failed to do request: Head "https://192.168.1.167:15000/v2/demo/alpine/blobs/sha256:...": dial tcp 192.168.1.167:15000: connect: connection refused
```

客户端默认对非 localhost 仓库走 HTTPS。解法见第 10.5 节（`insecure-registries` 或给仓库配 TLS）。

### 13.7 权限问题

```text
$ docker ps
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

原因：当前用户不在 `docker` 组。解法：`sudo usermod -aG docker $USER` 后重新登录（第 2.3 节）。

```text
$ ls -l /run/user/1001/docker.sock
ls: 无法访问 '/run/user/1001/docker.sock': 权限不够
```

这是**预期的好事**——rootless 模式下每个用户的 socket 只对自己可读（第 14 章）。

### 13.8 编排（compose）相关

**现象一：`depends_on` 写了，但应用启动时还是连不上数据库**

`depends_on` 默认只保证**启动顺序**，不保证**服务就绪**。解法：用 `condition: service_healthy` + 目标服务定义 `healthcheck`（第 9 章完整示例）。

**现象二：`docker inspect --format` 报模板错误**

```text
template parsing error: template: :1:50: executing "" at <.GraphDriver.Name>: map has no entry for key "GraphDriver"
```

`docker inspect` 的 JSON 字段随版本变化（例如 29.x 用 containerd 快照后没有 `GraphDriver` 了）。解法：先 `docker inspect 容器名 | head -80` 看清真实字段名，再写 `--format`；或者用 `docker inspect 容器名 --format '{{json .}}' | python3 -m json.tool` 慢慢翻。

**现象三：`docker compose` 报找不到 compose 文件 / 项目名不对**

```bash
docker compose ls                 # 当前有哪些 compose 项目在跑
docker compose -f /path/compose.yml ps   # 指定文件
docker compose -p myproj ps       # 指定项目名
```

## 14. 多用户共用一台 Docker 主机与用户隔离

这一章回答一个很实际的问题：**同一台机器上多个开发者要同时用 Docker，行不行？怎么隔离？**

### 14.1 结论先说

- **能同时操作**：Docker 守护进程是多客户端设计，多个用户并发 `docker run`、`docker build` 完全没问题，本机实测两个用户各并发起 3 个容器全部成功。
- **但默认没有用户隔离**：一台机器只有一个 dockerd、一份镜像/容器/卷/网络，而权限入口只有 `/var/run/docker.sock`。能连上这个 socket 的人，就等于拿到了这台机器上「容器与镜像的全部管理权」，且彼此之间没有任何边界。
- **要做到隔离，主流做法是每人一套 rootless dockerd**（单机多用户场景），或多机集群里的 namespace + RBAC（团队/生产场景）。

### 14.2 权限入口：只有那个 socket

```text
$ ls -l /var/run/docker.sock
srw-rw---- 1 root docker 0  7月 27 13:03 /var/run/docker.sock

$ getent group docker
docker:x:984:
```

`srw-rw---- root:docker` 的含义很明确：只有 root 和 `docker` 组成员能读写这个 socket（组里默认是空的）。所以：

- 未授权的普通用户连不上（本机实测）：

```text
$ su - dockerdev1 -c 'docker ps'
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

- 加进 `docker` 组就能用：

```text
$ usermod -aG docker dockerdev1
$ usermod -aG docker dockerdev2
$ getent group docker
docker:x:984:dockerdev1,dockerdev2

$ su - dockerdev1 -c 'id'
uid=1001(dockerdev1) gid=1001(dockerdev1) 组=1001(dockerdev1),100(users),984(docker)
```

要讲清楚的一点：**`docker` 组权限 ≈ root 权限**。组成员可以挂载宿主机任意目录（`-v /:/host`）、可以起特权容器（`--privileged`）、可以直接读写宿主机的 `/etc`。所以「给不给 docker 组」本质上是信任问题，不是技术便利问题。

### 14.3 实测：共享一个 daemon 时的真实行为

两个用户各起一个容器（一个 18101、一个 18102）：

```text
$ su - dockerdev1 -c 'docker run -d --name dev1-web -p 18101:80 nginx:1.27-alpine'
cb9a4a9ce52c8657fa0708c4c44075f543fdf3468c2e80ae942aab886bd2dc39
$ su - dockerdev2 -c 'docker run -d --name dev2-web -p 18102:80 nginx:1.27-alpine'
5703c95ee6f8ed8d9bf79e6f2e50ce5f6fffd126c2866596dc340dbf882269df

$ su - dockerdev2 -c 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"'
NAMES                          IMAGE                  PORTS
dev2-web                       nginx:1.27-alpine      0.0.0.0:18102->80/tcp, [::]:18102->80/tcp
dev1-web                       nginx:1.27-alpine      0.0.0.0:18101->80/tcp, [::]:18101->80/tcp
1Panel-zentao-iP2L             hub.zentao.net/app/zentao:22.5   0.0.0.0:3000->3000/tcp, ...
minikube                       kicbase/stable:v0.0.51 127.0.0.1:32793->22/tcp, ...
...
```

**dev2 能看到 dev1 的容器、宿主机上所有其他人的容器，包括运行状态和端口。**接下来四类冲突都是必然发生的：

**（1）容器名全局唯一**

```text
$ su - dockerdev2 -c 'docker run --name dev1-web alpine:3.20 echo hi'
docker: Error response from daemon: Conflict. The container name "/dev1-web" is already in use by container "cb9a4a9ce52c8657fa0708c4c44075f543fdf3468c2e80ae942aab886bd2dc39". You have to remove (or rename) that container to be able to reuse that name.
```

**（2）宿主机端口全局唯一**

```text
$ su - dockerdev2 -c 'docker run --rm -p 18101:80 nginx:1.27-alpine'
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint epic_hoover (edd928733eaa4f7785a570d03ca85262d82b79408b213a56476574dd36c64f21): Bind for 0.0.0.0:18101 failed: port is already allocated
```

**（3）镜像共享，谁都能覆盖、也能直接跑别人打的镜像**

```text
$ su - dockerdev1 -c 'docker tag alpine:3.20 dev1/img:1.0'
$ su - dockerdev2 -c 'docker run --rm dev1/img:1.0 echo "dev2 正在运行 dev1 打的镜像"'
dev2 正在运行 dev1 打的镜像
```

同一个 tag 被覆盖时，对方下次 `docker run` 用的就是你的版本——这是「环境突然变了」类事故的常见根源。

**（4）谁都能删掉、停掉、进入别人的容器**

```text
$ su - dockerdev2 -c 'docker rm -f dev1-web'
dev1-web
$ su - dockerdev1 -c 'docker ps --format "table {{.Names}}\t{{.Status}}"'
NAMES                          STATUS
dev2-web                       Up 52 seconds
...
# dev1-web 已经不在了
```

`docker exec` 也一样随便进，这意味着**同一台机器上任何 docker 组成员都能看到别人的环境变量、挂载的文件、跑在容器里的密钥**。

并发本身不是问题（两个用户同时创建 6 个容器，全部成功）：

```text
$ docker ps --filter name=dev1-c --format 'table {{.Names}}\t{{.Status}}'
NAMES     STATUS
dev1-c3   Up 12 seconds
dev1-c1   Up 16 seconds
dev1-c2   Up 8 seconds

$ docker ps --filter name=dev2-c --format 'table {{.Names}}\t{{.Status}}'
NAMES     STATUS
dev2-c3   Up 10 seconds
dev2-c1   Up 10 seconds
dev2-c2   Up 11 seconds
```

所以准确的说法是：**并发没问题，隔离没有**。

共享一台 daemon 的风险清单（讲解时可以逐条问听众「这条出了事谁能查出来」）：

| 风险 | 说明 |
|---|---|
| 资源互相影响 | 一个用户起的大内存容器能把整机内存吃满，别人的容器被 OOM 杀掉 |
| 误删 | `docker system prune -a --volumes`、`down -v`、按名字 `rm` 都可能清掉别人的东西 |
| 数据卷互相可见 | 卷名全局唯一，知道名字就能挂进自己的容器读 |
| 密钥泄露 | 容器里的环境变量、挂载的 `.env`、镜像层里的凭证对所有人可见 |
| 提权 | `-v /:/host` 或 `--privileged` 直接等价于宿主机 root |
| 端口抢占 | 谁都可能把别人要用的端口占掉，且报错信息不指向具体人 |

### 14.4 五种隔离方案对比

| 方案 | 隔离强度 | 成本 | 适用场景 |
|---|---|---|---|
| 共用一个 daemon + 团队约定 | 无（靠人守规矩） | 0 | 4 人以内小团队、互相信任、非生产机器 |
| **每用户一套 rootless Docker** | 强（各自 daemon、各自 socket、各自存储） | 低（装一次） | 单机多用户开发机、CI 跑不同用户的构建（推荐） |
| 每用户/每组一套独立 dockerd（TCP/unix） | 强 | 中（要管多个 daemon 与端口） | 需要 root 特性（低于 1024 端口、iptables 直管） |
| 集群 namespace + RBAC（K8S） | 强且可审计 | 高 | 多机生产、多团队、需要配额与审计 |
| 虚拟机 / Podman | 最强（VM）/ 强（Podman 天然 rootless） | 中~高 | 强安全要求、需要跑异构内核 |

### 14.5 rootless Docker 实操（本机实测）

思路：每个用户在**自己的用户空间**里跑一个 dockerd，socket 放在自己的 `$XDG_RUNTIME_DIR`，镜像和容器数据放在自己的家目录。别人既看不到也进不去。

**前置条件**：

```text
$ command -v dockerd-rootless.sh newuidmap newgidmap
/usr/bin/dockerd-rootless.sh
/usr/bin/newuidmap
/usr/bin/newgidmap

$ grep -E "dockerdev1" /etc/subuid /etc/subgid
/etc/subuid:dockerdev1:165536:65536
/etc/subgid:dockerdev1:165536:65536
```

- `docker-ce-rootless-extras` 提供 `dockerd-rootless.sh`（本机随 docker-ce 一起装上了）。
- `uidmap` 包提供 `newuidmap`/`newgidmap`（没装的话 `apt-get install -y uidmap`）。
- `/etc/subuid` 和 `/etc/subgid` 里必须给该用户分配一个子 UID/GID 段（Ubuntu 的 `adduser` 会自动加，`useradd` 不会，需要 `usermod --add-subuids 100000-165535 --add-subgids 100000-165535 用户名`）。
- `$XDG_RUNTIME_DIR`（通常是 `/run/user/<uid>`）必须存在且属主是自己；无登录会话的用户需要 `loginctl enable-linger 用户名`。

**坑：Ubuntu 23.10+ 默认禁止非特权 user namespace**

不加配置直接跑会失败。真正的报错在 `unshare` 层面（本机实测）：

```text
$ sysctl kernel.apparmor_restrict_unprivileged_userns
kernel.apparmor_restrict_unprivileged_userns = 1

$ su - dockerdev1 -c 'unshare -Ur echo 非特权 user namespace 创建成功'
unshare: 写失败：/proc/self/uid_map: 不允许的操作

$ su - dockerdev1 -c 'unshare -Urm echo 带 mount 的 user namespace 创建成功'
unshare: 写失败：/proc/self/uid_map: 不允许的操作
```

放开之后同样的命令立刻成功：

```text
$ sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
kernel.apparmor_restrict_unprivileged_userns = 0

$ su - dockerdev1 -c 'unshare -Ur echo 非特权 user namespace 创建成功'
非特权 user namespace 创建成功
```

所以要用 rootless Docker，需要：`sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`，并写入 `/etc/sysctl.d/` 持久化。这一项是安全权衡（关掉后任何用户都能自建 user namespace，历史上提权漏洞的利用面会变大），在内网开发机上通常可以接受，公网服务器上要评估。替代方案是给 `dockerd-rootless.sh`/`rootlesskit` 单独打 AppArmor profile。

**启动与验证**：

```bash
# 用户自己启动（不需要 sudo）
export XDG_RUNTIME_DIR=/run/user/1001

# 手动前台跑（调试用）
dockerd-rootless.sh

# 后台常驻（生产化用 systemctl --user）
dockerd-rootless-setuptool.sh install
systemctl --user enable --now docker
loginctl enable-linger $USER        # 没登录也能常驻
```

启动成功的日志与验证（实测）：

```text
$ ls -l /run/user/1001/docker.sock
srw-rw---T 1 dockerdev1 166519 0  9月 12 10:08 /run/user/1001/docker.sock

$ su - dockerdev1 -c "export DOCKER_HOST=unix:///run/user/1001/docker.sock; docker info --format 'ServerVersion={{.ServerVersion}} SecurityOptions={{.SecurityOptions}} Root={{.DockerRootDir}}'"
ServerVersion=29.5.2 SecurityOptions=[name=seccomp,profile=builtin name=rootless name=cgroupns] Root=/home/dockerdev1/.local/share/docker
```

三个关键点：`SecurityOptions` 里有 `name=rootless`（确认是 rootless 模式）；`DockerRootDir` 在该用户家目录下（数据不混在一起）；socket 权限是 `srw-rw---T`，属主是用户自己。

**坑：rootless daemon 不读 `/etc/docker/daemon.json`**

第一次在 rootless 里拉镜像直接超时（因为镜像加速配置在系统级 daemon.json 里）：

```text
$ su - dockerdev1 -c "export DOCKER_HOST=unix:///run/user/1001/docker.sock; docker run --rm hello-world"
Unable to find image 'hello-world:latest' locally
docker: Error response from daemon: failed to resolve reference "docker.io/library/hello-world:latest": failed to do request: Head "https://registry-1.docker.io/v2/library/hello-world/manifests/latest": dial tcp [2a03:2880:f12d:83:face:b00c:0:25de]:443: i/o timeout
```

解法：给这个用户在 `~/.config/docker/daemon.json` 里单独配一份（内容可以和系统级一样）：

```bash
install -d -m 700 ~/.config/docker
cp /etc/docker/daemon.json ~/.config/docker/daemon.json
systemctl --user restart docker      # 或者 kill 掉手动起的 dockerd 重新启动
```

配好之后一切正常（实测）：

```text
$ docker pull nginx:1.27-alpine
Digest: sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10
Status: Downloaded newer image for nginx:1.27-alpine

$ docker run -d --name dev1-rootless-web -p 18111:80 nginx:1.27-alpine
$ docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
NAMES               STATUS         PORTS
dev1-rootless-web   Up 7 seconds   0.0.0.0:18111->80/tcp, [::]:18111->80/tcp

# root 用户从宿主机访问 18111 依然可以（rootless 会做端口转发，>1024 的端口没问题）
$ curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18111/
200
```

**隔离验证（这是最关键的一组实测）**：

```text
# 1. 另一个用户连 socket 都看不到
$ su - dockerdev2 -c 'ls -l /run/user/1001/docker.sock'
ls: 无法访问 '/run/user/1001/docker.sock': 权限不够
$ su - dockerdev2 -c 'DOCKER_HOST=unix:///run/user/1001/docker.sock docker ps'
permission denied while trying to connect to the docker API at unix:///run/user/1001/docker.sock

# 2. root 的系统级 daemon 里看不到它（两套 daemon 完全独立）
$ docker ps -a --filter name=dev1-rootless-web
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

# 3. 容器里的 root 在宿主机上就是普通用户
$ ps -o pid,user,uid,cmd -p <容器主进程PID>
    PID USER       UID CMD
1714663 dockerd+  1001 nginx: master process nginx -g daemon off;
$ docker exec dev1-rootless-web id
uid=0(root) gid=0(root) groups=0(root),...

# 4. rootlesskit 以该用户身份运行
$ pgrep -a rootlesskit
1684528 rootlesskit --state-dir=/run/user/1001/dockerd-rootless --net=gvisor-tap-vsock --mtu=65520 ... /usr/bin/dockerd-rootless.sh
```

把第 3 条讲透：容器里 `id` 是 `uid=0(root)`，但在宿主机上这个进程属于 `uid=1001`（dockerdev1）。这就是 rootless 的安全价值——**容器里即使拿到 root，也伤不到宿主机**（不能改宿主机文件、不能绑低端口、不能动别人的容器）。相比第 14.2 节的「docker 组 ≈ root」，隔了一个数量级。

**rootless 的限制**（讲解时要说明白，避免听众踩坑）：

- 不能绑定低于 1024 的端口（要用 80/443 就在前面挂 nginx 或做端口转发）。
- 不能用 `--privileged`、不能随便改 iptables、不能挂某些内核文件系统。
- 性能略低（走 slirp4netns/gvisor 网络栈，批量网络 IO 有损耗）。
- 数据在各自家目录，磁盘配额要自己管（`~/.local/share/docker` 容易长到几十 GB）。
- 每个用户一套说明「镜像要各拉一遍」——想省磁盘就用私有仓库（第 10 章）或共享的镜像缓存方案。

### 14.6 如果必须共用一台 daemon：把约定写进规范

现实里很多团队就是共用一台测试机，这时候靠规范把风险降到最低：

1. **命名统一前缀**：容器/镜像/卷/网络都用 `项目名-` 或 `用户名-` 开头，避免撞名（撞名的报错根本看不出是谁的）。
2. **清理只用 label/前缀过滤**，禁止 `docker system prune -a --volumes`：

```bash
docker image prune -f --filter label=owner=team-a
docker ps -aq --filter name=team-a- | xargs -r docker rm -f
```

3. **compose 项目名隔离**：`docker-compose.yml` 里写 `name: team-a-stack`，网络和卷会自动带上前缀，不会和别人的 `*_default` 网络混。
4. **端口规划**：给每个项目分配固定端口段（例如 A 组 18000-18099、B 组 18100-18199），写进团队文档。
5. **不发布不必要的端口**：容器之间靠自定义网络按服务名通信，宿主机只暴露入口（nginx 一个端口）。
6. **密钥不要放环境变量**：`docker inspect` 能看到环境变量；用文件挂载 + 只读（`-v secret.txt:/run/secrets/x:ro`）或 K8S Secret。
7. **镜像 tag 带责任人/构建号**：别都用 `latest`，避免互相覆盖（`team-a/api:20260912-1`）。
8. **约定「不停别人的容器」**：要腾资源先看 `docker stats`，再找容器属主（`docker inspect --format '{{.Config.Labels.owner}}'`，前提是大家都打了 label）。

### 14.7 该选哪个：决策清单

```text
需要多人同时用吗
├─ 不需要（单人开发机）→ 直接用 docker 组 + root 模式最省事
└─ 需要
   ├─ 互相信任、非生产、4 人以内 → 共用 daemon + 命名/端口规范（14.6）
   ├─ 需要真正隔离、还是单机 → rootless Docker（14.5），每人一套
   ├─ 需要 root 特性（低端口、特权、自定义网络驱动）→ 每人一套独立 dockerd
   └─ 多机、多团队、要配额和审计 → Kubernetes + namespace + RBAC（本机 k8s 单节点部署见《kubernetes-minikube-install》）
```

一句话总结：**Docker 本身没有多租户设计，多用户靠「每人一套 rootless daemon」（单机）或「K8S namespace + RBAC」（集群）来实现隔离；在共用 daemon 的场景下，隔离只能靠规范和纪律。**

## 应用场景实战

下面三个场景都是完整可执行的流程，覆盖「新项目容器化上线」「CI 构建与交付」「离线环境交付」。

### 场景一：把一个传统项目容器化并一键交付

假设手头是一个「Vue 前端 + Node API + MySQL + Redis」的项目，要求交给运维时只给一条命令。

第一步：写两个 Dockerfile（前端多阶段、后端非 root），内容见第 6.7 与第 11.10 节模板。

第二步：写 `docker-compose.yml`（结构见第 9.2 节），要点：

```yaml
name: myproject
services:
  web:
    build: ./web
    ports: ["${WEB_PORT}:80"]
    depends_on:
      api: { condition: service_healthy }
    networks: [frontend, backend]
    restart: unless-stopped
  api:
    build: ./api
    environment:
      MYSQL_HOST: db
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    depends_on:
      db: { condition: service_healthy }
    networks: [backend]
    restart: unless-stopped
  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: myproject
    volumes:
      - db-data:/var/lib/mysql
      - ./db/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -uroot -p$$MYSQL_ROOT_PASSWORD --silent"]
      interval: 10s
      timeout: 10s
      retries: 30
      start_period: 180s
    networks: [backend]
  cache:
    image: redis:7.4-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes: [cache-data:/data]
    networks: [backend]
networks: { frontend: {}, backend: {} }
volumes: { db-data: {}, cache-data: {} }
```

第三步：`.env` 与 `.gitignore`（密钥不进版本库）：

```ini
# .env（提交 .env.example，真实的 .env 不提交）
WEB_PORT=18090
MYSQL_ROOT_PASSWORD=改成强密码
MYSQL_DATABASE=myproject
MYSQL_USER=app
MYSQL_PASSWORD=改成强密码
```

```gitignore
.env
db-data/
*.log
node_modules/
dist/
```

第四步：交付命令与上线检查清单：

```bash
# 交付方：构建并验证
docker compose up -d --build
docker compose ps                                  # 必须全部 healthy
curl -fs http://127.0.0.1:18090/api/health && echo OK
docker compose exec -T db mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SELECT COUNT(*) FROM myproject.t_msg;"

# 接收方：一条命令拉起
git clone <仓库> && cd <仓库>
cp .env.example .env && vim .env                   # 只改密码和端口
docker compose up -d --build
```

上线检查清单（逐条确认，缺一条都可能在上线当天出问题）：

| 检查项 | 命令/方式 |
|---|---|
| 所有服务 healthy | `docker compose ps` 里没有 `unhealthy` / `starting` |
| 数据落在卷上 | `docker volume ls` 有 `项目名_db-data`；`docker compose down` 再 `up` 数据还在 |
| 只有入口服务发布端口 | `docker ps --format '{{.Names}}\t{{.Ports}}'`，db/cache 不该出现 `0.0.0.0:` |
| 时区正确 | `docker compose exec -T api date` |
| 日志有轮转 | `docker inspect <容器> --format '{{json .HostConfig.LogConfig}}'` |
| 非 root 运行 | `docker compose exec -T api id` 显示非 0 uid |
| 内存有上限 | `docker inspect <容器> --format '{{.HostConfig.Memory}}'` |
| 重启策略 | `docker inspect <容器> --format '{{.HostConfig.RestartPolicy.Name}}'` |

### 场景二：CI 构建镜像 → 私有仓库 → 服务器滚动更新

完整脚本（可放进 Jenkins/GitLab CI 的构建阶段）：

```bash
#!/usr/bin/env bash
# build-and-push.sh ：CI 里构建、打标签、推送
set -euo pipefail

REGISTRY="registry.internal:5000"
PROJECT="team-a"
APP="api"
VERSION="$(git describe --tags --always)"          # 例如 1.4.2-3-gabc1234
BUILD_NO="${BUILD_NUMBER:-local}"
TAG="${VERSION}-${BUILD_NO}"

echo "== 登录私有仓库 =="
echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY" -u "$REGISTRY_USER" --password-stdin

echo "== 构建（多阶段，带缓存） =="
docker build \
  --cache-from "${REGISTRY}/${PROJECT}/${APP}:latest" \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t "${REGISTRY}/${PROJECT}/${APP}:${TAG}" \
  -f api/Dockerfile .

echo "== 推送 =="
docker push "${REGISTRY}/${PROJECT}/${APP}:${TAG}"
docker tag "${REGISTRY}/${PROJECT}/${APP}:${TAG}" "${REGISTRY}/${PROJECT}/${APP}:latest"
docker push "${REGISTRY}/${PROJECT}/${APP}:latest"

echo "== 记录部署用的确切版本 =="
echo "${REGISTRY}/${PROJECT}/${APP}:${TAG}" > image-tag.txt
```

服务器侧（拉取新版本 + 回滚都靠 tag）：

```bash
#!/usr/bin/env bash
# deploy.sh ：服务器上执行（用固定版本号，不用 latest）
set -euo pipefail

NEW_TAG="$1"                       # 例如 1.4.2-128
COMPOSE="docker compose -f /opt/app/docker-compose.yml --env-file /opt/app/.env"

echo "== 拉取新镜像 =="
sed -i "s|^APP_IMAGE=.*|APP_IMAGE=${NEW_TAG}|" /opt/app/.env
$COMPOSE pull api
$COMPOSE up -d api

echo "== 等健康检查 =="
for i in $(seq 1 60); do
  status=$(docker inspect "$($COMPOSE ps -q api)" --format '{{.State.Health.Status}}' 2>/dev/null || echo unknown)
  [ "$status" = "healthy" ] && { echo "部署成功（${i}s）"; break; }
  [ "$i" = "60" ] && { echo "健康检查超时，回滚"; /opt/app/rollback.sh; exit 1; }
  sleep 1
done
```

```bash
#!/usr/bin/env bash
# rollback.sh ：回滚到上一个版本
set -euo pipefail
PREV="$1"                            # 上一个 tag
sed -i "s|^APP_IMAGE=.*|APP_IMAGE=${PREV}|" /opt/app/.env
docker compose -f /opt/app/docker-compose.yml --env-file /opt/app/.env up -d api
```

关键点：**部署用具体版本号（`1.4.2-128`），`latest` 只作本地便利标签**；`--cache-from` 让 CI 复用上一次构建的层（构建时间能省一半以上）；健康检查超时就自动回滚。

### 场景三：完全离线的内网交付

没有外网、不能访问任何仓库时的标准做法：

```bash
# 1. 有网机器：拉取并打包所有需要的基础镜像
docker pull nginx:1.27-alpine
docker pull mysql:8.4
docker pull redis:7.4-alpine
docker pull node:22-alpine
docker save nginx:1.27-alpine mysql:8.4 redis:7.4-alpine node:22-alpine | gzip > images-20260912.tar.gz
ls -lh images-20260912.tar.gz          # 本机量级：约 500MB~1GB

# 2. 拷贝到内网机器（U 盘/scp/堡垒机）
scp images-20260912.tar.gz user@内网机器:/opt/

# 3. 内网机器：导入
gunzip -c /opt/images-20260912.tar.gz | docker load
docker image ls | grep -E 'nginx|mysql|redis|node'

# 4. 内网机器上构建自己的业务镜像（依赖已在本地的镜像，不需要外网）
docker compose build
docker compose up -d

# 5. 内网自建仓库（长期方案）：docker-registry 起好之后
docker tag myapp:1.0 192.168.1.20:5000/myapp:1.0
docker push 192.168.1.20:5000/myapp:1.0
```

注意点：`docker save` 一次可以打包多个镜像；`gzip` 后体积能小一半左右；导入到内网机器上镜像的**名字和 tag 都会保留**，所以内网机器上的 `docker-compose.yml` 不用改。离线环境里的 `insecure-registries`、镜像加速器（用不上）、日志轮转这些配置要在交付前一并写好（第 2.4 节）。

## 最佳实践与踩坑记录

### 最佳实践

1. **镜像用多阶段构建**，构建工具不进最终镜像（实测 259MB → 73.6MB）。
2. **基础镜像选 alpine/slim**，但要先确认依赖能跑（musl 与 glibc 的差异；Java 用 `-alpine` 前先测一遍）。
3. **Dockerfile 里先拷依赖清单、再拷源码**，让依赖层缓存复用（`COPY package.json` → `RUN npm ci` → `COPY src`）。
4. **写 `.dockerignore`**，把 `.git`、`node_modules`、日志、密钥挡在构建上下文外面。
5. **`CMD`/`ENTRYPOINT` 一律用 exec（JSON）形式**，并让业务进程做 PID 1。
6. **所有需要留存的数据都放卷**（命名卷优先），代码里不要往容器内写业务数据。
7. **多容器用自定义网络 + 服务名互访**，不要写死容器 IP，不要用默认 bridge 跑多容器应用。
8. **生产镜像一律 `USER` 非 root**，配合 `--read-only`、`--tmpfs`、资源限制做基础加固。
9. **镜像里设好时区**（`ENV TZ` + tzdata 或挂 `/etc/localtime`），别等日志对不上才补。
10. **每个服务都要健康检查**，`depends_on` 用 `condition: service_healthy`；`start_period` 要覆盖最慢的初始化时间（MySQL 实测几分钟）。
11. **daemon 配日志轮转**（`max-size`/`max-file`），否则容器日志能写满磁盘。
12. **清理只用 `--filter` 精确命中自己的资源**（label / name 前缀），永远不要在生产机上敲 `docker system prune -a --volumes`。
13. **镜像部署用具体版本号或 digest**，`latest` 只作本地便利标签。
14. **多用户共用一台机器时用 rootless Docker**，或者把命名/端口/label 规范写进团队文档。
15. **交付前跑一遍「上线检查清单」**（场景一那 8 条），比上线后救火便宜得多。

### 踩坑记录

坑 1：MySQL 初始化期间被强杀，数据卷直接损坏

结论：容器处于 `Initializing database files` 阶段时 `docker rm -f`，卷里的数据文件与 redo log 不一致，之后挂同一个卷起新容器会直接报错退出。

原因：MySQL 8.4 首次初始化要写大量文件（本机高负载下 2~5 分钟），中途 SIGKILL 会留下半成品数据目录。

解法：看日志确认出现 `ready for connections` 再操作；要停就 `docker stop -t 120`；已损坏且数据不要了，删卷重新初始化。

```text
[ERROR] [MY-012960] [InnoDB] Cannot create redo log files because data files are corrupt or the database was not shut down cleanly after creating the data files.
```

坑 2：`depends_on` 写了却还是启动失败

结论：`depends_on` 默认只保证启动顺序，不保证依赖服务可用；改用 `condition: service_healthy` 后，还要保证 `start_period` 足够长，否则依赖服务永远 `unhealthy`，上游服务根本不启动。

原因：健康检查有宽限期（`start_period`）+ 连续失败次数（`retries`）两个门槛，初始化慢的服务会被判为不健康。

解法：`start_period` 按最慢初始化时间的 1.5~2 倍设置（本机 MySQL 设成 180s），并在应用侧也做连接重试。

坑 3：`docker run -d` 之后立刻访问拿到 `HTTP 000`

结论：容器"启动了"不等于"服务就绪"。实测 `Up 1 second` 时 curl 报 `HTTP 000`、退出码 56（连接被重置）。

原因：`-d` 只保证进程被拉起，应用监听端口还需要时间。

解法：脚本里做就绪轮询，或者用健康检查 + `depends_on` 条件。

坑 4：设了 `TZ=Asia/Shanghai`，`date` 还是 UTC

结论：alpine 基础镜像没有 tzdata，时区环境变量不生效。

原因：`TZ` 指向的时区库文件不存在，libc 回退到 UTC。

解法：镜像里 `apk add --no-cache tzdata` 并复制 `/usr/share/zoneinfo/Asia/Shanghai` 到 `/etc/localtime`；或挂载宿主机的 `/etc/localtime`（Node/Java 自带时区数据，`-e TZ` 直接有效）。

坑 5：`docker stop` 要等 10 秒以上，退出码 137

结论：业务进程没处理 SIGTERM，只能等超时被 SIGKILL。

原因：`docker stop` 只给 PID 1 发信号，而内核不投递"没有处理函数"的信号给 PID 1；实测 `sleep 300` 无论 exec 还是 shell 形式都拖满 12~14 秒。

解法：启动命令用 exec 形式让业务进程做 PID 1、应用注册优雅停机、必要时 `--init` 或 `docker stop -t 60`。

坑 6：容器名、端口、卷名全局唯一，多人一机时互相踩

结论：同一台 Docker 主机上所有资源共用一个命名空间，第二个用户用同名容器或同一宿主端口会直接被拒。

原因：Docker 是单机单 daemon 设计，没有多租户隔离。

解法：见第 14 章——单机多用户用 rootless，或统一命名前缀 + 端口段规划。

坑 7：以为"给 docker 组"只是方便，实际等于给 root

结论：`docker` 组成员可以用 `-v /:/host` 挂载宿主机根目录、起 `--privileged` 容器，等价于宿主机 root。

原因：容器的隔离边界是内核提供的，而 Docker 守护进程以 root 运行，能任意配置这个边界。

解法：生产机上严格控制 docker 组成员；多用户场景用 rootless；不要把 docker 组当成"普通权限组"发放。

坑 8：rootless 用户拉不动镜像

结论：rootless daemon **不读** `/etc/docker/daemon.json`，镜像加速器配置必须放在该用户自己的 `~/.config/docker/daemon.json`。

原因：rootless 模式下 daemon 以用户身份运行，读取的是用户级配置目录。

解法：`cp /etc/docker/daemon.json ~/.config/docker/daemon.json` 后重启用户的 daemon。

```text
docker: Error response from daemon: failed to resolve reference "docker.io/library/hello-world:latest": ... dial tcp [2a03:2880:f12d:83:face:b00c:0:25de]:443: i/o timeout
```

坑 9：Ubuntu 24.04 上 rootless Docker 起不来

结论：`kernel.apparmor_restrict_unprivileged_userns=1` 阻止了非特权 user namespace 创建。

原因：Ubuntu 23.10+ 默认收紧了这个开关，而 rootlesskit 需要它。

解法：`sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`（写入 `/etc/sysctl.d/` 持久化）或给 rootlesskit 单独打 AppArmor profile；先用 `unshare -Ur echo ok` 验证。

```text
unshare: 写失败：/proc/self/uid_map: 不允许的操作
```

坑 10：`COPY . .` 把 20MB 垃圾文件和 `.git` 一起打进镜像

结论：构建上下文会被整体传给构建器（BuildKit 只传被 COPY 引用的文件，但一旦 `COPY . .` 就全都进），实测镜像从 12.1MB 涨到 33.1MB、上下文 213B → 20.98MB。

原因：没有 `.dockerignore`。

解法：写好 `.dockerignore`（`**/node_modules`、`**/.git`、日志、密钥），并且 `COPY` 精确到目录。

坑 11：用 `--build-arg` 传密钥，密钥留在镜像历史里

结论：`docker history --no-trunc` 能直接看到 `ARG BUILD_TOKEN=super-secret-token`。

原因：`ARG` 的值会写进构建元数据，构建器也会给出 `SecretsUsedInArgOrEnv` 警告。

解法：用 BuildKit secret（`RUN --mount=type=secret` + `--secret`），运行期密钥用编排系统的 secret 或只读文件挂载。

坑 12：卷删不掉

结论：还有容器（包括已停止的）引用该卷时 `docker volume rm` 报 `volume is in use`。

原因：卷与容器的引用关系独立于容器运行状态。

解法：`docker ps -a --filter volume=卷名` 找到引用者，删掉容器再删卷；`docker compose down`（不带 `-v`）会保留卷，是正常的。

坑 13：两个容器在默认 bridge 上，按名字互 ping 失败

结论：`ping: bad address 'xxx'`，只能用 IP 互访。

原因：默认 bridge 不提供内置 DNS（自定义网络才有 `127.0.0.11`）。

解法：`docker network create` 建自定义网络，双方都接入；或者用 compose（自动建网络）。

坑 14：nginx 反代容器重启后 502

结论：`upstream` 里的服务名只在 nginx 启动时解析一次，后端容器重建（IP 变化）后继续打旧 IP。

原因：nginx 对 `upstream` 块做的是启动时解析。

解法：用 `resolver 127.0.0.11 valid=10s` + 变量形式的 `proxy_pass $upstream`（第 9.3 节），或让 nginx 与后端在同一 compose 项目里用服务名并通过 restart 一起重建。

坑 15：push 到内网私有仓库报 TLS/连接错误

结论：`docker push 192.168.1.167:15000/...` 报 `dial tcp ...: connect: connection refused`（客户端默认走 HTTPS，仓库只有 HTTP）。

原因：只有 `localhost`/`127.0.0.1` 被默认当作不安全的 HTTP 仓库，其他地址一律按 HTTPS 处理。

解法：给仓库配 TLS，或在客户端 `daemon.json` 里加 `insecure-registries`（rootless 用户改自己的那份）。

坑 16：`npm ci` 报缺 lock 文件 / `package.json` 里写注释报 EJSONPARSE

结论：`npm ci` 必须要有 `package-lock.json`（没有就报错退出，这是它的设计目标：锁死依赖）；`package.json` 不能有注释。

原因：`npm ci` 走的是锁文件的确定性安装；JSON 不支持注释。

解法：本地 `npm install` 生成并提交 lock 文件；`package.json` 里别写注释（本机实测犯了后一个错误，构建直接失败）。

坑 17：MySQL 初始化脚本里的中文变成乱码

结论：初始化 SQL 里写的中文，通过接口读出来是 `åˆå§‹åŒ–è„šæœ¬...` 这种乱码；而在容器里用 `mysql` 客户端查同一行，中文显示成 `?`。

原因：两个环节的字符集都不对——初始化脚本执行时客户端连接没有用 utf8mb4（把 UTF-8 字节按 latin1 解释后存进去，正确读出时就成了双重编码的乱码）；`mysql` 命令行客户端默认字符集也可能是 latin1（所以显示 `?`）。

解法：初始化 SQL 文件第一行加 `SET NAMES utf8mb4;`；命令行查询时加 `--default-character-set=utf8mb4`。

```bash
docker compose exec -T db mysql --default-character-set=utf8mb4 -uroot -p密码 -e "SELECT * FROM demo.t_msg;"
```

## 相关文档

- [[116-Docker基础]] — Image/Container/Registry 三大概念、镜像分层、容器生命周期、Registry 与加速器、Dockerfile 指令、Volume、Network 基础
- [[117-Docker命令]] — 镜像与容器命令速查、日志排查、资源清理、部署排查实战
- [[118-Docker-Compose]] — 多容器编排、compose.yml 详解、环境变量与依赖条件
- [[21.2-容器原理]] — namespace / cgroups、镜像分层、容器运行时原理（Linux 视角）
- [[21.3-Docker]] — Linux 运维视角的 Docker：镜像/容器/网络/存储/Dockerfile/Compose
- [[21.5-容器运行时生态]] — containerd、CRI-O、runc、Podman 等运行时对比
- [[32.1-Docker 与容器]] — 大数据平台上的容器化：组件容器化与资源编排
- [[81.1-Docker]] — 前端工程化的 Docker 基础：Image/Container/Layer/Dockerfile/Volume/Network
- [[81.2-前端 Docker]] — 前端专用：Node 构建、多阶段构建、Nginx 托管、静态资源与运行时配置
- [[119-Kubernetes基础]] — 从单机 Docker 走向集群：Pod、Deployment、StatefulSet、探针、自愈
- [[kubernetes-minikube-install]] — 单节点 K8S 集群搭建（本机实测），容器镜像源方案与集群验证
- [[kubernetes-springboot-vue-deploy]] — SpringBoot + Vue 项目从 docker-compose 迁移到 K8S 的完整对照与验证实录
