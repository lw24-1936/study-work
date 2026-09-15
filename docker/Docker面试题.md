---
title: Docker 面试题大全
created: 2026-09-16
updated: 2026-09-16
type: concept
tags: [docker, container, 面试, dockerfile, docker-compose, network, volume, namespace, cgroups]
---

# Docker 面试题大全

整理日期：2026-09-16

> 状态：已完成

本文按「基础概念 → 镜像与分层 → 容器生命周期 → Dockerfile → 存储 → 网络 → docker compose → 底层原理 → 安全 → 故障排查 → 生产与运维」组织，覆盖 Docker 面试的全部高频技术点。每题先给结论，再展开原理与追问，最后附「面试重点总结」。

## 目录

- [一、基础概念](#一基础概念)
- [二、镜像与分层](#二镜像与分层)
- [三、容器生命周期](#三容器生命周期)
- [四、Dockerfile](#四dockerfile)
- [五、存储](#五存储)
- [六、网络](#六网络)
- [七、docker compose](#七docker-compose)
- [八、底层原理（namespace / cgroups / unionfs）](#八底层原理namespace--cgroups--unionfs)
- [九、安全](#九安全)
- [十、故障排查](#十故障排查)
- [十一、生产与运维](#十一生产与运维)
- [面试重点总结](#面试重点总结)

## 一、基础概念

**问题 1：什么是 Docker？它解决什么问题？**

Docker 是一个开源的容器化平台，把应用及其依赖（代码、运行时、系统库、配置）打包进一个可移植的「镜像」，在任何装了 Docker 的机器上以「容器」的形式一致地运行。

它解决的核心问题是「在我机器上能跑」：开发、测试、生产环境不一致（库版本、系统差异、依赖冲突）导致的行为漂移。镜像把运行环境与应用绑定在一起交付，一次构建到处运行。

**问题 2：容器和虚拟机（VM）的区别？**

结论：容器共享宿主内核，虚拟机有独立 Guest OS。容器更轻、启动更快、资源占用更小，但隔离性弱于虚拟机。

| 维度 | 容器 | 虚拟机 |
|---|---|---|
| 隔离层 | 进程级（namespace + cgroups） | 硬件级（Hypervisor） |
| 内核 | 共享宿主内核 | 各自独立内核 |
| 启动速度 | 秒级 | 分钟级 |
| 资源开销 | 进程级别，几乎无额外损耗 | 每个 VM 一套完整 OS，GB 级内存 |
| 镜像大小 | MB 级 | GB 级 |
| 隔离强度 | 弱（共享内核，逃逸风险高于 VM） | 强 |

追问：为什么容器隔离性弱？因为容器与宿主机共享同一个内核，一旦内核存在漏洞，容器内的攻击者可能利用内核漏洞逃逸到宿主机。虚拟机通过硬件虚拟化提供更强边界，但代价是性能。

**问题 3：Docker 的三大核心组件是什么？**

Docker Client（`docker` 命令，发指令）、Docker Daemon（`dockerd`，真正干活的后台进程，管理镜像/容器/网络/卷）、Registry（镜像仓库，如 Docker Hub、Harbor、私有 Registry）。

三者关系：Client 通过 REST API 与 Daemon 通信（本地走 Unix socket `/var/run/docker.sock`，远程走 TCP），Daemon 需要镜像时从 Registry 拉取。

**问题 4：镜像（Image）和容器（Container）是什么关系？**

镜像是一个只读的、分层的模板，包含运行应用所需的文件系统和配置；容器是镜像的运行实例，等于「镜像 + 一个可写容器层（container layer）+ 运行配置（网络、资源限制、卷挂载等）」。

类比：镜像是「类」，容器是「实例」；镜像像安装盘 ISO，容器像装好并运行起来的系统。一个镜像可以启动多个互相独立的容器。

**问题 5：Docker 的架构调用链是什么？**

`docker` CLI → `dockerd`（Daemon）→ `containerd` → `containerd-shim-runc-v2` → `runc`。

- dockerd：接收客户端请求，编排镜像构建/拉取、容器生命周期等高层逻辑
- containerd：管理容器运行时、镜像传输、快照；是独立的 CNCF 项目
- containerd-shim：每个容器一个 shim 进程，让容器在 containerd 重启后仍能存活，并转发 stdin/stdout
- runc：OCI 运行时，真正用 namespace/cgroups 创建和启动容器进程

追问：为什么需要 containerd 和 runc 分层？解耦与标准化。Docker 早期把运行时逻辑揉在 daemon 里，后来拆出 containerd 对接 CRI 标准，runc 遵循 OCI 标准，让不同编排系统（K8s 通过 CRI）和不同运行时（crun、kata、gVisor）可以自由组合。

**问题 6：什么是 OCI（Open Container Initiative）？**

OCI 是容器领域的开放标准，定义了两个规范：runtime-spec（容器如何运行，实现有 runc/crun/kata）和 image-spec（镜像格式如何打包，层、manifest、config）。Docker 的镜像和运行时都兼容 OCI 标准，所以 OCI 镜像可以被其他运行时（Podman、containerd、CRI-O）直接使用。

**问题 7：Docker 和 Podman、containerd 的区别？**

- Docker：完整的容器平台，自带 daemon、CLI、compose、buildx 全家桶
- Podman：无 daemon（rootless-first），命令与 docker 高度兼容，可直接管理 OCI 镜像/容器
- containerd：容器运行时 + 镜像管理，不做镜像构建、不做编排，主要给 K8s 做 CRI 后端

**问题 8：Docker 是单机工具，为什么生产还要 K8s？**

Docker 解决「单机跑一个应用」的问题；生产环境面对的是「多台机器跑几十上百个服务」，需要跨主机的调度、服务发现、负载均衡、自动扩缩容、滚动发布、故障自愈。这些是容器编排（Kubernetes）的职责。Docker 容器是 K8s 调度和运行的最小单元，两者是「运行时」和「编排」的关系，不冲突。

## 二、镜像与分层

**问题 9：Docker 镜像的分层结构是什么？为什么要分层？**

镜像由多个只读层叠加而成。每条会改动文件系统的 Dockerfile 指令（RUN、COPY、ADD）产生一层，底层是基础镜像层，顶层是最后一条指令。分层的好处：

1. 复用与省空间：多个镜像共享相同的基础层，只存一份
2. 加速构建与分发：未变化的层直接命中缓存，拉取只传缺失的层

读取时通过联合文件系统（UnionFS）把这些层叠加成一个统一视图；运行容器时再叠加一个可写容器层，写操作走 copy-on-write（COW）：修改已有文件时，先把原文件从只读层复制到可写层再改，原层不变。

**问题 10：UnionFS 和 overlayfs 是什么？**

UnionFS 是一类「把多个目录/文件系统联合挂载成一个」的技术，Docker 用的具体实现是 overlayfs（现在是 overlay2 存储驱动）。

overlay2 把镜像各层作为 lowerdir 只读层叠加，容器可写层作为 upperdir，挂载后呈现合并视图。写文件时用 copy-on-write：先 `copy_up` 把文件从 lower 复制到 upper 再修改，删除文件时在 upper 创建 whiteout 文件标记删除。

追问：为什么读已修改过的文件有一次性开销？第一次写触发 copy_up 有复制成本，之后都在 upper 层读写。这也是「容器层只放轻量写、大文件放卷」的原因。

**问题 11：COPY 和 ADD 的区别？什么时候用哪个？**

- COPY：把构建上下文里的文件/目录复制到镜像，行为简单可预期
- ADD：在 COPY 基础上多两个能力——源可以是 URL（自动下载）、本地 tar 包会自动解压

官方推荐：绝大多数场景用 COPY；只有确需「远程下载」或「tar 自动解压」时才用 ADD。因为 ADD 的隐式行为（自动解压、远程下载）容易产生非预期结果，破坏构建的可复现性。

**问题 12：CMD 和 ENTRYPOINT 的区别？如何配合使用？**

- ENTRYPOINT：定义容器启动时执行的主命令，`docker run` 后面的参数会作为它的参数追加，不易被覆盖（除非 `--entrypoint`）
- CMD：定义默认命令或默认参数，`docker run` 后面的参数会整体替换它

两者配合的经典模式（镜像当「可执行程序」用）：

```dockerfile
ENTRYPOINT ["python", "app.py"]
CMD ["--help"]
```

这样 `docker run img` 执行 `python app.py --help`，`docker run img --port 8080` 执行 `python app.py --port 8080`（CMD 被替换成 `--port 8080`）。

追问：shell 形式和 exec 形式有什么区别？

```dockerfile
CMD echo hello        # shell 形式：/bin/sh -c "echo hello"，PID 1 是 sh
CMD ["echo","hello"]  # exec 形式：直接 exec，进程本身是 PID 1
```

shell 形式多一层 `/bin/sh -c` 包装，导致信号无法直达业务进程（见问题 24），且 `$VAR` 会被 shell 展开。生产镜像推荐 exec（JSON）形式。

**问题 13：什么是多阶段构建？为什么能减小镜像体积？**

多阶段构建允许一个 Dockerfile 里写多个 `FROM`，每段是一个独立的构建阶段，最后只把需要的产物 `COPY --from=<阶段>` 进最终镜像。

```dockerfile
# 阶段 1：编译
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o myapp .

# 阶段 2：运行（只有二进制 + 最小运行时）
FROM alpine:3.20
COPY --from=builder /app/myapp /usr/local/bin/myapp
ENTRYPOINT ["myapp"]
```

好处：编译工具链、源码、中间产物全部留在 builder 阶段，最终镜像只含运行时需要的文件，体积可以从 GB 级（带完整 Go 工具链）降到几 MB。同时减少了攻击面（镜像里没有编译器、没有源码）。

**问题 14：镜像构建时如何利用层缓存？为什么 COPY 顺序影响构建速度？**

Docker 构建时逐条指令执行，只有「当前指令及其上下文」和缓存层一致才命中缓存；一旦某条指令未命中，后续所有指令缓存全部失效。

所以把「变化频率低」的放前面、「变化频率高」的放后面。依赖安装是典型例子：

```dockerfile
# 差：源码一改，package.json 和 node_modules 全重装
COPY . .
RUN npm ci

# 好：只有 package.json 变化才重装依赖；源码改动只重跑 COPY
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
```

先只拷依赖清单 → 装依赖（这层可缓存）→ 再拷源码。日常只改源码时，依赖层直接命中缓存，构建快一个量级。

**问题 15：如何查看镜像的分层历史？`docker history` 能看到什么？**

`docker history <镜像>` 列出镜像每一层的创建指令、大小、ID。`--no-trunc` 显示完整内容。

要注意：`docker history` 也会暴露构建时用 `ARG`/`ENV` 传入的敏感值（如密钥），所以构建期密钥不能走 ARG（见问题 48）。

**问题 16：如何减小镜像体积？列举方法。**

1. 多阶段构建（最有效）
2. 基础镜像选 alpine/slim/distroless（前提：依赖兼容 musl libc）
3. 写好 `.dockerignore`，把 `.git`、`node_modules`、日志、密钥挡在上下文外
4. 合并同类 RUN 指令减少层数（但别为了层数牺牲缓存可读性）
5. 清理包管理器缓存（`apt-get clean` / `rm -rf /var/lib/apt/lists/*` 与安装合并到同一 RUN）
6. 语言运行时用瘦身方案（Go 静态编译用 scratch、Java 用 jre 镜像、Node 用 alpine）

## 三、容器生命周期

**问题 17：容器有哪几种状态？生命周期是怎样的？**

`docker ps -a` 里 STATUS 一列对应状态：Created（已创建未启动）→ Running（运行中）→ Paused（暂停，进程冻结）→ Restarting（重启中）→ Exited（已退出）→ Dead（已移除失败残留）。

核心流程：`docker run` = `docker create`（建容器，分配文件系统和资源）+ `docker start`（启动 PID 1 进程）；`docker stop` 发 SIGTERM 给 PID 1、宽限期后 SIGKILL；`docker rm` 删除容器（运行中的要先 `-f`）。

**问题 18：docker run 的 restart 策略有哪几种？**

`--restart` 取值：

| 策略 | 行为 |
|---|---|
| no | 默认，退出不重启 |
| on-failure[:N] | 仅非 0 退出码时重启，可限定最大次数 |
| always | 任何情况退出都重启（包括手动 stop，daemon 重启时也拉起） |
| unless-stopped | 类似 always，但「被手动 stop 过」的容器在 daemon 重启后不自动拉起 |

追问：always 和 unless-stopped 的关键区别——前者即使你手动 `docker stop` 过，daemon 重启仍会拉起；后者记住「被停止」状态，daemon 重启后保持停止。生产服务一般用 unless-stopped。

**问题 19：docker run 常用参数的作用？**

- `-d`：后台运行（detached）
- `-p 8080:80`：宿主端口映射到容器端口
- `-v /host/path:/container/path`：挂载卷
- `-e KEY=value`：设置环境变量
- `--name`：命名容器
- `--rm`：退出后自动删除容器
- `-i -t`（`-it`）：交互式 + 分配 TTY
- `--restart`：重启策略
- `--network`：指定网络
- `--memory` / `--cpus`：资源限制
- `--read-only`：只读根文件系统
- `--init`：用 tini 作为 PID 1 转发信号

**问题 20：docker exec 和 docker attach 的区别？**

- `docker exec -it <容器> <命令>`：在运行中的容器里新起一个进程，最常用，退出不影响容器主进程
- `docker attach`：附着到容器主进程（PID 1）的标准输入/输出/错误，`Ctrl+C` 可能直接终止主进程

排查用 exec（比如 `docker exec -it myapp sh` 进去看环境），attach 用于需要直连主进程输出的场景。

**问题 21：容器退出码 0、1、125、126、127、137、143 分别代表什么？**

- 0：正常退出
- 1：应用自身错误退出
- 125：`docker run` 命令本身失败（如参数错误）
- 126：容器内命令无法执行（权限不足，如没加执行位）
- 127：容器内命令找不到（not found，常是镜像缺依赖或路径错）
- 137：SIGKILL（128 + 9），典型是 OOMKilled 或 `docker rm -f` / `docker stop` 超时被强杀
- 143：SIGTERM（128 + 15），`docker stop` 正常发 SIGTERM 后应用退出

规律：容器退出码 = 128 + 信号编号。所以 137 = 128 + 9（SIGKILL），143 = 128 + 15（SIGTERM）。

**问题 22：什么是 PID 1 问题？为什么容器里要重视 PID 1？**

容器内主进程就是 PID 1。Linux 内核给 PID 1 特殊待遇：

1. 信号处理：内核不把「没有安装处理函数的信号」投递给 PID 1（孤儿进程信号保护机制）。如果 PID 1 是 shell 或 `sleep` 这类不处理信号的进程，`docker stop` 发的 SIGTERM 会被忽略，只能等超时 SIGKILL（退出码 137）
2. 僵尸进程回收：PID 1 有责任 wait 回收孤儿僵尸进程，普通进程不处理会导致容器里积累僵尸进程

解法：启动命令用 exec 形式让业务进程直接做 PID 1；业务进程本身要注册 SIGTERM/SIGINT 优雅停机；必要时用 `--init`（docker 内置 tini）或 `tini`/`dumb-init` 作为 PID 1 转发信号并回收僵尸。

## 四、Dockerfile

**问题 23：Dockerfile 有哪些常用指令？各做什么？**

- `FROM`：指定基础镜像（每个阶段第一行）
- `RUN`：构建时执行命令（装依赖、编译）
- `COPY` / `ADD`：复制文件进镜像
- `WORKDIR`：设置工作目录（后续指令和容器启动的相对目录）
- `ENV`：设置环境变量（构建期 + 运行期都生效）
- `ARG`：构建参数（仅构建期，`docker build --build-arg` 传入）
- `CMD` / `ENTRYPOINT`：启动命令（见问题 12）
- `EXPOSE`：声明容器监听的端口（仅文档作用，不真正发布端口）
- `VOLUME`：声明匿名卷挂载点
- `USER`：切换后续指令和运行时的用户
- `HEALTHCHECK`：定义健康检查
- `LABEL`：元数据标签
- `ONBUILD`：作为基础镜像时，子镜像构建时触发的指令（已不推荐）

**问题 24：Dockerfile 指令的 shell 形式和 exec 形式有什么区别？**

- shell 形式：`RUN apt-get update`、`CMD echo hi` —— 通过 `/bin/sh -c` 执行，支持 shell 特性（管道、变量展开、`&&`），但多一层 shell
- exec 形式：`RUN ["apt-get", "update"]`、`CMD ["echo", "hi"]` —— 直接 exec，无 shell 处理

对 CMD/ENTRYPOINT，exec 形式让业务进程直接做 PID 1（信号能送达），是生产推荐写法。对 RUN，shell 形式用 `&&` 串命令更自然。

**问题 25：ARG 和 ENV 的区别？**

- `ARG`：仅构建期可用，通过 `--build-arg` 传入，不进入运行期环境变量，也不会进最终镜像的 env
- `ENV`：构建期和运行期都生效，会固化进镜像的 env（`docker run` 可用 `-e` 覆盖）

典型用法：`ARG` 传构建版本号、基础镜像 tag；`ENV` 设置运行时需要的路径、时区、配置项。

追问：为什么构建期密钥不能用 ARG？因为 `ARG` 的值会写进构建历史，`docker history` 能直接看到明文（见问题 48，用 BuildKit secret）。

**问题 26：HEALTHCHECK 怎么用？它解决什么问题？**

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8080/health || exit 1
```

容器「在运行」不等于「服务可用」。HEALTHCHECK 让 Docker 周期性地探测服务就绪状态，状态流转 healthy / unhealthy。健康状态可以被 `docker ps` 看到、被 compose 的 `depends_on: condition: service_healthy` 用来做启动依赖、被编排系统（K8s 的 readiness/liveness 是另一套，但思路一致）用来做流量切换。

**问题 27：为什么需要 .dockerignore？写什么内容？**

`docker build` 会把整个构建上下文（默认当前目录）发给 builder。`.dockerignore` 与 `.gitignore` 类似，排除不需要进上下文的文件。不写会导致：构建上下文巨大（拖慢构建）、`COPY . .` 把 `.git`、`node_modules`、密钥、日志全打进镜像。

常见内容：`.git`、`**/node_modules`、`**/target`、`*.log`、`.env`、`**/*.key`、`**/*.pem`、`dist`（若在容器内构建）等。

## 五、存储

**问题 28：Docker 有哪些存储方式？各自适用场景？**

| 类型 | 存储位置 | 生命周期 | 适用 |
|---|---|---|---|
| named volume（命名卷） | Docker 管理（`/var/lib/docker/volumes/`） | 独立于容器 | 持久化数据，首选 |
| bind mount（绑定挂载） | 宿主机任意路径 | 随宿主路径 | 开发时热更新代码、挂配置 |
| tmpfs | 内存 | 随容器 | 临时敏感数据，不落盘 |
| anonymous volume（匿名卷） | Docker 管理，随机名 | 容器删除时随删（`--rm`） | Dockerfile 里 VOLUME 声明的默认行为 |

推荐：生产数据用命名卷（Docker 管理、可备份、可跨容器复用）；开发调试用 bind mount。

**问题 29：named volume 和 bind mount 的区别？如何选择？**

- named volume：由 Docker 管理，路径在 `/var/lib/docker/volumes/<名>/_data`，跨平台、权限好处理（首次挂载会复制容器内已有数据）、可用 `docker volume` 命令备份
- bind mount：挂宿主机的具体路径，路径完全由用户控制，但权限/所有权、路径可移植性都是坑

选择：需要「宿主机直接读写文件内容」（如热加载代码、挂 nginx 配置）用 bind mount；只是「要持久化数据、不关心内部路径」用 named volume。

**问题 30：如何备份和恢复容器数据卷？**

```bash
# 备份：起一个临时容器，把卷内容和备份目录同时挂上，打包
docker run --rm -v mydata:/data -v "$(pwd)":/backup alpine \
  tar czf /backup/mydata-backup.tar.gz -C /data .

# 恢复：反向操作
docker run --rm -v mydata:/data -v "$(pwd)":/backup alpine \
  tar xzf /backup/mydata-backup.tar.gz -C /data
```

思路是「借一个一次性容器（`--rm`）+ 临时 bind mount」把卷内容导出/导入，不依赖宿主机的 Docker 内部目录。

**问题 31：容器删除后数据会丢吗？什么情况会丢？**

容器可写层（container layer）里的数据随容器删除而丢。挂载在 named volume / bind mount 里的数据不随容器删除而丢（卷独立于容器生命周期）。

所以「重要数据必须放卷」，代码里别往容器可写层写业务数据。`docker compose down` 默认保留卷（要 `-v` 才删卷），`docker rm -v` 会连同匿名卷一起删。

## 六、网络

**问题 32：Docker 有哪几种网络驱动？各自用途？**

- bridge：默认，单机容器之间通过虚拟网桥通信，需 `-p` 发布端口给外部
- host：容器直接共享宿主机网络栈（`--network host`），无 NAT、性能最好，但端口冲突、不安全
- none：无网络（`--network none`），完全隔离
- overlay：跨多台 Docker 主机的容器网络（配合 Swarm），生产多机场景
- macvlan：给容器分配宿主机同网段的独立 MAC/IP，像接在物理网络上

单机最常用 bridge；需要容器直连宿主机网络用 host；多机编排用 overlay（现在更多直接上 K8s）。

**问题 33：默认 bridge 网络和自定义 bridge 网络有什么区别？**

关键区别是 DNS：

- 默认 bridge（`docker0`）：容器之间只能通过 IP 互访，没有内置 DNS，容器名无法解析
- 自定义 bridge 网络：内置 DNS 服务器（`127.0.0.11`），容器之间可以直接用容器名互相解析访问

生产多容器应用必须用自定义网络（compose 会自动建一个），通过服务名互访，不写死 IP（容器重建 IP 会变）。

**问题 34：端口映射 -p 和 -P 的区别？**

- `-p 8080:80`：把宿主机 8080 映射到容器 80（也可 `-p 127.0.0.1:8080:80` 指定绑定地址、`-p 8080:80/udp` 指定协议）
- `-P`：把 Dockerfile 里 `EXPOSE` 声明的所有端口随机映射到宿主机高位端口

追问：`-p 8080:80` 里前后两个数字分别是谁？前者宿主机端口、后者容器端口。映射靠 iptables DNAT 规则实现。

**问题 35：容器之间如何通信？跨主机呢？**

同主机同自定义网络：直接容器名互访（DNS 解析）。同主机不同网络：默认不互通，需要 `docker network connect` 把容器加入目标网络。容器访问宿主机：用 `host.docker.internal`（部分环境）或宿主机网卡 IP。容器访问外网：通过 NAT 出宿主。

跨主机：单机 bridge 不管跨主机，需要 overlay 网络（Swarm）或交给 Kubernetes（CNI 插件，如 Flannel/Calico/Cilium）。

**问题 36：host 网络的优缺点？**

优点：无 NAT、无端口转发开销，性能好；容器直接绑定宿主机端口，访问简单。
缺点：端口冲突风险（多个容器不能绑同一端口）、容器直接用宿主网络栈、隔离性差。

适用于对网络性能敏感、或需要与宿主机网络紧密交互的场景（如某些监控 agent、网络代理）。

## 七、docker compose

**问题 37：docker compose 是什么？解决什么问题？**

Docker Compose 是一个用 YAML 文件（`compose.yml` / `docker-compose.yml`）定义和运行多容器应用的工具。一条 `docker compose up` 拉起一整套服务（web + api + db + cache），并自动管理它们之间的网络和卷。

解决「多容器应用如何声明式地一起定义、一起启动、一起管理」的问题，是单机多容器编排的事实标准。新版以插件形式提供（`docker compose`），不再是独立的 `docker-compose` 二进制。

**问题 38：compose.yml 里 services / networks / volumes 三个顶层字段分别定义什么？**

```yaml
services:        # 一组容器，每个服务对应一个容器（可扩展副本）
  web:
    build: ./web
    ports: ["8080:80"]
    networks: [frontend]
networks:        # 自定义网络定义（不声明则 compose 自动建默认网络）
  frontend:
volumes:         # 命名卷定义
  db-data:
```

service 是最小单元：一个 service 定义镜像来源（image 或 build）、端口、环境变量、卷、网络、依赖、健康检查、资源限制等。

**问题 39：depends_on 能保证依赖服务就绪吗？**

不能。`depends_on` 默认只保证「启动顺序」（先启依赖服务再启本服务），不等待依赖服务真正可用（如数据库完成初始化、端口可连）。

要真正等就绪，用 `depends_on` 的 `condition: service_healthy`（依赖服务需配 healthcheck），或应用侧自己做连接重试。

```yaml
web:
  depends_on:
    db:
      condition: service_healthy
```

**问题 40：compose 里环境变量从哪里来？优先级？**

1. `environment` 字段直接写死
2. `env_file` 指定的文件
3. shell 环境变量
4. 项目目录的 `.env` 文件（compose 自动读取，用于变量替换 `${VAR}`）

`.env` 里的值可在 compose.yml 里用 `${VAR}` 引用（用于注入端口、密码等可变项），避免密钥写死在 YAML 里。注意 `environment` 里写 `MYSQL_PASSWORD: ${MYSQL_PASSWORD}` 时，值来自 `.env` 或 shell。

**问题 41：docker compose 常用命令？**

- `docker compose up -d`：后台启动（`--build` 先构建）
- `docker compose down`：停止并删除容器/网络（`-v` 连卷一起删）
- `docker compose ps`：查看服务状态
- `docker compose logs -f <service>`：看日志
- `docker compose exec <service> <cmd>`：进容器执行命令
- `docker compose restart / stop / start`：重启/停/启
- `docker compose pull`：拉取最新镜像
- `docker compose config`：校验并展开配置（排查 compose 文件问题的利器）

## 八、底层原理（namespace / cgroups / unionfs）

**问题 42：Linux namespace 是什么？Docker 用了哪些？**

namespace 是 Linux 内核的进程隔离机制，让一组进程看到独立的系统资源视图，是容器隔离的基石。Docker 用到的 namespace：

| namespace | 隔离内容 |
|---|---|
| PID | 进程号空间（容器内 PID 1 独立） |
| NET | 网络栈（网卡、路由、端口） |
| MNT | 挂载点（容器看到自己的根文件系统） |
| UTS | 主机名、域名 |
| IPC | 进程间通信（信号量、消息队列） |
| USER | 用户/组 ID（容器内 root 可映射为宿主非特权用户，rootless 基础） |
| Cgroup | cgroup 视图（资源限制视图） |

追问：namespace 是「隔离」不是「虚拟化」——容器和宿主共享同一个内核，只是各自看到不同的资源视图。

**问题 43：cgroups 是什么？Docker 用它做什么？**

cgroups（control groups）是内核的资源限制/统计机制，把进程分组并对每组设置 CPU、内存、IO 等资源上限，是容器「限流」的基础。

Docker 用它实现 `--memory`（内存上限）、`--cpus`（CPU 配额）、`--pids-limit`（进程数）、IO 权重等资源限制。内存限制生效靠 cgroup 的 memory 子系统，超出上限时 OOM killer 杀掉组内进程（容器退出码 137）。

追问：为什么容器里 `free -h` 看到的是宿主机的内存？因为 cgroup 限制的是「可用上限」，而 `/proc/meminfo` 读的是宿主机全局值；要看容器真实可用内存，读 cgroup 文件（`/sys/fs/cgroup/memory.max`）。

**问题 44：容器的「写时复制」和「写时分配」是什么？**

- copy-on-write（写时复制）：多个容器共享同一镜像只读层，写文件时先复制到自己的可写层再改，节省空间
- copy-on-write 的存储层由 overlay2 等存储驱动实现

好处：多个容器共享基础层（只存一份），写操作互不影响（各自 copy 到可写层）。

**问题 45：Docker 的存储驱动有哪些？默认是什么？**

常见：overlay2（默认，主流推荐）、aufs（早期）、devicemapper（早期）、btrfs/zfs/vfs。overlay2 是现在的事实标准，性能和稳定性最好。`docker info` 里 `Storage Driver` 字段可查看（本机是 overlay2）。

## 九、安全

**问题 46：为什么生产容器要用非 root 用户运行？**

容器内默认是 root，虽然被 namespace 限制，但仍有风险：宿主目录挂载进容器后 root 可直接读写、`--privileged` 可完全逃逸、漏洞利用后拿到 root 权限攻击面更大。非 root 运行是纵深防御的第一道：即使容器被攻破，攻击者拿到的也是低权限用户。

```dockerfile
RUN useradd -m appuser
USER appuser
```

追问：容器内 root 和宿主机 root 是同一个 root 吗？在「未启用 user namespace」的情况下，容器内 root（uid 0）就是宿主机 root，只是被 namespace 和 capability 约束；启用 userns（rootless 或 `--userns`）后，容器内 root 映射为宿主机普通用户。

**问题 47：--read-only、--tmpfs、--cap-drop 分别做什么？**

- `--read-only`：根文件系统只读，防止容器内写文件（配合 tmpfs 给需要写的位置，如 `/tmp`）
- `--tmpfs /tmp`：把 `/tmp` 挂成内存盘（不落盘、临时）
- `--cap-drop ALL --cap-add NET_BIND_SERVICE`：裁剪 Linux capabilities，只保留必要的能力（默认容器拥有较多能力，按最小权限原则应裁剪）

三者是容器加固的常用组合：只读根 + 临时写 + 最小能力集。

**问题 48：构建镜像时如何安全传递密钥？**

错误做法：`ARG` / `ENV` 传密钥——会留在镜像构建历史里，`docker history` 可见。

正确做法：BuildKit secret 挂载：

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=github_token \
    GITHUB_TOKEN=$(cat /run/secrets/github_token) pip install ...
```

构建时 `docker build --secret id=github_token,src=./token.txt .`。secret 只在当前 RUN 挂载可用，不进镜像层。运行期密钥则用编排系统的 secret 或只读文件挂载，不用环境变量。

**问题 49：如何保证镜像安全？**

1. 基础镜像用官方镜像并锁版本（不用 `latest`）
2. 构建后用镜像扫描（`docker scout`、Trivy、Clair、Snyk）扫描漏洞
3. 多阶段构建减少攻击面（去掉编译器、源码）
4. 非 root 运行、只读根、capability 裁剪
5. 私有仓库 + TLS，签名校验（cosign / Notary）
6. 持续更新基础镜像打补丁

**问题 50：Docker daemon 暴露 TCP 端口有什么风险？**

`dockerd -H tcp://0.0.0.0:2375` 会把 Docker API 暴露到网络。裸的 HTTP 2375 端口无认证，等于把宿主机 root 权限送人（通过 API 可挂载根目录、起特权容器）。正确做法：默认只监听本地 Unix socket；必须远程访问时用 TLS（2376）+ 客户端证书认证，或用 SSH 隧道。

**问题 51：把用户加进 docker 组有什么安全含义？**

docker 组成员相当于拥有宿主机 root：能 `-v /:/host` 挂载根目录、`--privileged` 起特权容器、修改容器隔离边界。所以 docker 组不是「普通权限组」，生产机上应严格管控成员，多用户场景用 rootless Docker 或统一规范。

## 十、故障排查

**问题 52：容器 OOMKilled（退出码 137）怎么排查？**

现象：`docker inspect` 里 `OOMKilled: true`，容器反复重启，退出码 137。

排查：`docker inspect <容器> --format '{{.HostConfig.Memory}}'` 看内存上限；`docker stats` 看实时内存；看应用是否有内存泄漏、JVM 堆设置是否超容器内存（Java 在容器内 `-Xmx` 若不配会按宿主机内存算，容易 OOM）。

解法：调大 `--memory` 或减小应用内存占用；Java 用容器感知的 `-XX:MaxRAMPercentage`；给应用加内存监控。

**问题 53：容器内时间不对（时区问题）怎么解决？**

现象：容器里 `date` 显示 UTC，日志时间与本地差 8 小时。

原因：容器默认 UTC；alpine 等精简镜像没有 tzdata，`TZ` 环境变量不生效。

解法：镜像里装 tzdata 并设时区（`apk add --no-cache tzdata` + `ENV TZ=Asia/Shanghai`），或挂载宿主 `/etc/localtime`；Node/Java 自带时区数据，直接 `-e TZ=Asia/Shanghai` 即可。

**问题 54：端口被占用 / 端口映射冲突怎么排查？**

现象：`docker run -p` 报 `bind: address already in use`。

排查：`docker ps --format '{{.Names}}\t{{.Ports}}'` 看已有容器占用；`ss -tlnp` 看宿主机端口占用；注意容器名、卷名也是全局唯一的（多人一机易冲突）。

解法：换端口、停掉占用者、或统一端口段规划。

**问题 55：镜像拉取慢 / 拉不下来怎么办？**

原因：Docker Hub 官方源在国内访问慢或不稳定。

解法：配置镜像加速器（`/etc/docker/daemon.json` 里 `registry-mirrors`，rootless 用户改 `~/.config/docker/daemon.json`）；内网私有仓库（Harbor）；离线环境 `docker save`/`docker load`。

**问题 56：`docker stop` 要等很久才停（10 秒+）是什么原因？**

原因：业务进程（PID 1）没处理 SIGTERM，`docker stop` 发 SIGTERM 后等默认 10 秒超时，再 SIGKILL。所以总耗时 > 10 秒。

解法：启动命令用 exec 形式让业务进程做 PID 1；应用注册 SIGTERM 优雅停机；必要时 `docker stop -t <秒>` 调整宽限期或 `--init`。

## 十一、生产与运维

**问题 57：如何给容器限制 CPU 和内存？**

```bash
docker run --memory 512m --cpus 1.5 --pids-limit 256 ...
```

- `--memory`（`-m`）：内存上限，可加 `--memory-swap` 控制 swap 上限
- `--cpus`：CPU 核数配额（如 1.5 核）；也可 `--cpuset-cpus=0-3` 绑定具体核
- `--pids-limit`：进程数上限

compose 里对应 `deploy.resources.limits`（或旧版 `mem_limit`/`cpus`）。限制资源是生产容器的基础要求，防止单容器打爆宿主。

**问题 58：如何配置容器日志轮转？**

容器日志默认 json-file 驱动，无轮转会无限增长写满磁盘。在 daemon 或容器级配置：

```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "100m", "max-file": "3" }
}
```

或容器级 `docker run --log-driver json-file --log-opt max-size=100m --log-opt max-file=3`。生产一般两种都配。

**问题 59：如何实现零停机更新（滚动更新）？**

单机 docker 本身没有内置滚动更新（compose 的 `up -d` 是重建容器，有短暂中断）。要零停机：

1. 用反向代理（nginx/traefik）做负载，更新时先拉新容器、健康检查通过后切流量、再下旧容器（蓝绿/金丝雀思路）
2. 多副本 + 负载均衡，逐个替换
3. 集群场景直接用 Kubernetes 的滚动更新（Deployment 的 rolling update 策略 + readiness probe）

**问题 60：docker system prune 会删什么？使用要注意什么？**

`docker system prune` 清理未使用的容器、网络、悬空镜像（dangling images）；`-a` 连带所有未使用的镜像；`--volumes` 连带未使用的卷。

危险点：生产机上别敲 `docker system prune -a --volumes`——「未使用」不等于「不要了」，可能把回滚用的旧镜像、还有数据但暂时没容器引用的卷删掉。清理要精确：`docker image prune --filter "until=24h"`、按 label/名称过滤，只删明确不要的资源。

**问题 61：live-restore 是什么？有什么用？**

`live-restore: true`（daemon.json）让 Docker daemon 重启（如升级、配置变更）时，正在运行的容器不中断。没有它，`systemctl restart docker` 会停掉所有容器（除非 restart 策略为 always 会再拉起，但仍有中断）。

生产升级 Docker 版本时开 live-restore，能显著减少服务中断窗口。

## 面试重点总结

1. **容器 vs 虚拟机**：共享内核 vs 独立内核，进程级隔离 vs 硬件级隔离——记住「轻量 + 共享内核 + 隔离弱」三个关键词。
2. **镜像分层 + copy-on-write**：每条会改文件系统的指令一层，overlay2 叠加，写时复制——这是「镜像小、启动快、可复用」的根因。
3. **CMD vs ENTRYPOINT**：ENTRYPOINT 定主命令、CMD 定默认参数；exec 形式让业务进程做 PID 1。
4. **PID 1 问题**：内核不给 PID 1 投递无处理函数的信号，导致 stop 超时 SIGKILL（137）——生产必用 exec 形式 + 优雅停机。
5. **存储三兄弟**：named volume（持久化首选）/ bind mount（开发热更新）/ tmpfs（临时）；重要数据必须放卷。
6. **网络核心**：默认 bridge 无 DNS、自定义网络有 DNS（127.0.0.11）——多容器必用自定义网络 + 服务名互访。
7. **多阶段构建**：构建工具不进最终镜像，减体积 + 减攻击面——必答题。
8. **层缓存优化**：先拷依赖清单再装依赖再拷源码，让依赖层缓存复用。
9. **depends_on 不等就绪**：要 `condition: service_healthy` + healthcheck。
10. **底层三件套**：namespace（隔离）+ cgroups（限流）+ unionfs（分层存储）。
11. **安全三件套**：非 root + 只读根 + capability 裁剪；密钥走 BuildKit secret，不用 ARG。
12. **退出码**：137 = OOMKilled/SIGKILL，143 = SIGTERM 正常停——排查容器重启必看。

## 相关文档

- [[Docker完整教程]] — Docker 完整教程（讲解版），本文所有面试题背后的完整原理、命令与真实输出
- [[116-Docker基础]] — Image/Container/Registry 三大概念、镜像分层、容器生命周期、Dockerfile、Volume、Network
- [[117-Docker命令]] — 镜像与容器命令速查、日志排查、资源清理
- [[118-Docker-Compose]] — 多容器编排、compose.yml 详解
- [[119-Kubernetes基础]] — 从 Docker 走向集群编排：Pod、Deployment、StatefulSet、探针、自愈
- [[21.2-容器原理]] — namespace / cgroups、镜像分层、容器运行时原理（Linux 视角）
- [[Kubernetes完整教程]] — Kubernetes 完整知识教程，容器编排的下一站
