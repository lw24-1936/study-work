---
title: Docker 基础
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [docker, image, container, registry, dockerfile, volume, network]
---

# Docker 基础

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [Image 镜像](#image-镜像)
- [Container 容器](#container-容器)
- [Registry 仓库](#registry-仓库)
- [Dockerfile](#dockerfile)
- [Volume 数据卷](#volume-数据卷)
- [Network 网络](#network-网络)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Docker 是容器化平台，将应用及其依赖打包成镜像，在任何环境一致运行，解决"在我机器上能跑"的问题。

```text
Docker 的核心价值：
1. 环境一致 —— 镜像包含应用 + 依赖，开发/测试/生产一致
2. 快速部署 —— 秒级启动，比虚拟机快
3. 资源隔离 —— 容器隔离进程、文件系统、网络
4. 轻量 —— 共享宿主机内核，比虚拟机省资源
```

```text
Docker vs 虚拟机：
虚拟机：完整操作系统（几 GB，分钟级启动）
容器：共享宿主机内核（几十 MB，秒级启动）
```

### Docker 三大核心概念

```text
Image（镜像）—— 应用的只读模板（类似类）
Container（容器）—— 镜像的运行实例（类似对象）
Registry（仓库）—— 镜像的存储分发（类似 Maven 仓库）
```

```text
Image → run → Container
Registry → pull → Image → run → Container
```

## Image 镜像

镜像（Image）是容器的模板，包含应用和运行环境，分层存储。

### 镜像的分层结构

```text
镜像由多个只读层叠加：
┌──────────────┐
│ 应用层（app.jar）│  ← 你的应用
├──────────────┤
│ JDK 层        │  ← 运行环境
├──────────────┤
│ 基础镜像层     │  ← 操作系统
└──────────────┘
```

```text
分层的好处：
1. 复用 —— 多个镜像共享相同的基础层
2. 缓存 —— 构建时未变化的层用缓存
3. 高效 —— 只传输变化的层
```

### 镜像相关命令

```bash
docker pull nginx:latest        # 拉取镜像
docker images                   # 查看本地镜像
docker rmi nginx:latest         # 删除镜像
docker build -t app:1.0 .       # 构建镜像
docker tag app:1.0 app:latest   # 打标签
docker save -o app.tar app:1.0  # 导出镜像
docker load -i app.tar          # 导入镜像
```

### 镜像命名

```text
镜像名格式：仓库/镜像名:标签

nginx:latest          # 官方镜像
myapp:1.0             # 自定义镜像
registry.example.com/myapp:1.0  # 私有仓库镜像

标签（tag）：
latest —— 最新（默认，但不建议生产用）
1.0.0 —— 具体版本（生产建议明确版本）
```

## Container 容器

容器（Container）是镜像的运行实例，是应用的实际运行环境。

### 容器生命周期

```bash
docker run -d -p 8080:80 nginx     # 创建并启动容器（后台）
docker ps                          # 查看运行中的容器
docker ps -a                       # 查看所有容器（含停止的）
docker start <容器>                # 启动已停止的容器
docker stop <容器>                 # 停止容器
docker restart <容器>              # 重启容器
docker rm <容器>                   # 删除容器
docker rm -f <容器>                # 强制删除（运行中的）
```

### docker run 常用参数

```bash
docker run -d \                    # 后台运行
  --name myapp \                   # 容器名
  -p 8080:8080 \                   # 端口映射（宿主机:容器）
  -v /opt/data:/data \             # 数据卷挂载
  -e MYSQL_ROOT_PASSWORD=123 \     # 环境变量
  --restart=always \               # 自动重启
  --memory=512m \                  # 内存限制
  myapp:1.0                        # 镜像
```

### 进入容器

```bash
docker exec -it <容器> bash        # 进入容器（交互式）
docker exec <容器> ls /            # 在容器内执行命令
docker logs <容器>                 # 查看日志
docker logs -f <容器>              # 实时查看日志
```

### 容器 vs 镜像

```text
镜像：只读模板，静态
容器：运行实例，动态（镜像 + 可写层）

一个镜像可以启动多个容器（互不影响）
容器停止/删除不影响镜像
```

## Registry 仓库

Registry 是镜像的存储和分发中心。

### 仓库类型

```text
1. Docker Hub —— 官方公共仓库（docker.io）
2. 私有仓库 —— 公司内部（Harbor、Nexus）
3. 云仓库 —— 阿里云、腾讯云容器镜像服务
```

### 常用仓库

```bash
# Docker Hub
docker pull nginx                    # 从 Docker Hub 拉取

# 阿里云镜像加速器（国内加速）
# 配置 /etc/docker/daemon.json
{
  "registry-mirrors": ["https://xxx.mirror.aliyuncs.com"]
}

# 推送到私有仓库
docker tag myapp:1.0 registry.example.com/myapp:1.0
docker push registry.example.com/myapp:1.0
```

### 镜像加速器（国内必备）

```bash
# 配置阿里云镜像加速器
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://xxxx.mirror.aliyuncs.com"]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

## Dockerfile

Dockerfile 是构建镜像的脚本，定义镜像的构建步骤。

### 常用指令

```dockerfile
FROM openjdk:17-jdk-slim         # 基础镜像
WORKDIR /app                     # 工作目录
COPY app.jar app.jar             # 复制文件
ADD config.tar.gz /app/          # 复制并解压
RUN mvn package                  # 构建时执行命令
ENV JAVA_OPTS="-Xmx512m"         # 环境变量
EXPOSE 8080                      # 声明端口
CMD ["java", "-jar", "app.jar"]  # 启动命令
ENTRYPOINT ["java", "-jar"]      # 入口命令
```

### Java 应用 Dockerfile

```dockerfile
# 构建阶段（多阶段构建）
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

# 运行阶段
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /build/target/app.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 多阶段构建

```text
多阶段构建的好处：
1. 镜像更小 —— 最终镜像不含 Maven、源码
2. 构建缓存 —— 依赖层单独缓存
3. 安全 —— 构建工具不进最终镜像
```

### CMD vs ENTRYPOINT

```text
CMD —— 默认命令（可被 docker run 后的参数覆盖）
ENTRYPOINT —— 入口命令（docker run 后的参数作为其参数）

组合使用：
ENTRYPOINT ["java", "-jar"]
CMD ["app.jar"]
# docker run myapp → java -jar app.jar
# docker run myapp other.jar → java -jar other.jar
```

## Volume 数据卷

数据卷（Volume）持久化容器数据，容器删除后数据不丢。

### 为什么需要数据卷

```text
容器是可写的，但容器删除后数据丢失（容器层随容器删除）
数据卷把数据存在宿主机，独立于容器生命周期
```

### 数据卷的三种方式

```bash
# 1. 命名卷（推荐，Docker 管理）
docker volume create mydata
docker run -v mydata:/data mysql

# 2. 绑定挂载（宿主机目录）
docker run -v /opt/data:/data mysql

# 3. 匿名卷（不指定名字）
docker run -v /data mysql
```

```bash
# 数据卷管理
docker volume ls            # 查看数据卷
docker volume rm mydata     # 删除数据卷
```

### 数据卷的应用（MySQL 持久化）

```bash
docker run -d \
  --name mysql \
  -p 3306:3306 \
  -v mysql-data:/var/lib/mysql \     # 数据持久化
  -e MYSQL_ROOT_PASSWORD=123456 \
  mysql:8.0
```

## Network 网络

Docker 网络实现容器间通信和端口映射。

### 网络类型

| 网络 | 说明 | 适用场景 |
|------|------|---------|
| bridge | 默认桥接网络（容器互通） | 单机容器通信 |
| host | 共享宿主机网络 | 高性能、端口不隔离 |
| none | 无网络 | 隔离容器 |
| overlay | 跨主机网络 | Swarm/K8s |

### 自定义网络（推荐）

```bash
# 创建自定义网络
docker network create my-network

# 容器加入同一网络，可用容器名通信
docker run -d --name mysql --network my-network mysql:8.0
docker run -d --name app --network my-network myapp:1.0

# app 容器内可以用 "mysql" 访问 MySQL（容器名解析）
```

```text
自定义网络的优点：
1. 容器名解析 —— 用容器名通信（不用 IP）
2. 隔离 —— 不同网络的容器隔离
3. DNS 服务 —— 内置 DNS
```

### 端口映射

```bash
-p 8080:8080      # 宿主机 8080 → 容器 8080
-p 127.0.0.1:8080:8080   # 只绑定本机
-p 8080-8090:8080-8090   # 端口范围映射
```

## 应用场景实战

### 场景 1：部署 MySQL

```bash
docker run -d \
  --name mysql \
  --restart=always \
  -p 3306:3306 \
  -v mysql-data:/var/lib/mysql \
  -v /opt/mysql/conf:/etc/mysql/conf.d \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e TZ=Asia/Shanghai \
  mysql:8.0
```

### 场景 2：部署 Redis

```bash
docker run -d \
  --name redis \
  --restart=always \
  -p 6379:6379 \
  -v redis-data:/data \
  -e TZ=Asia/Shanghai \
  redis:7 \
  redis-server --appendonly yes --requirepass 123456
```

### 场景 3：部署 Java 应用

```bash
# 构建镜像
docker build -t myapp:1.0 .

# 运行容器
docker run -d \
  --name myapp \
  --restart=always \
  -p 8080:8080 \
  -v /opt/app/logs:/app/logs \
  -e SPRING_PROFILES_ACTIVE=prod \
  myapp:1.0
```

## 最佳实践与踩坑记录

### 最佳实践

1. **用多阶段构建**。镜像更小、更安全，构建缓存更高效。

2. **数据用数据卷持久化**。数据库、日志等数据用 -v 挂载，容器删除不丢。

3. **生产环境用具体版本标签**。不要用 latest，避免版本漂移。

4. **容器间通信用自定义网络**。用容器名通信，不依赖 IP。

5. **时区设置**。`-e TZ=Asia/Shanghai` 或 Dockerfile `ENV TZ=Asia/Shanghai`。

### 踩坑记录

**坑 1：容器删除后数据丢失**

```bash
docker run -d mysql:8.0   # 没挂数据卷
docker rm mysql           # 删除容器，数据全丢
```

数据库、有状态应用必须挂数据卷。

**坑 2：时区问题**

```text
容器默认 UTC 时区，日志时间差 8 小时
```

设置 `-e TZ=Asia/Shanghai` 或 Dockerfile `ENV TZ`。

**坑 3：端口占用**

```bash
docker run -p 8080:8080 myapp   # 宿主机 8080 被占用，启动失败
```

检查端口占用（ss -tlnp），换端口映射。

**坑 4：镜像体积过大**

```text
用完整 JDK 镜像 + 源码构建，镜像 1GB+
```

用多阶段构建 + JRE 基础镜像 + slim 版本。

**坑 5：容器内 localhost 不通宿主机**

```text
容器内 localhost 是容器自己，不是宿主机
容器访问宿主机服务要用 host.docker.internal 或宿主 IP
```

容器内访问宿主机用 `host.docker.internal`（或 --network host）。

**坑 6：latest 标签版本漂移**

```text
用了 latest 标签，重新 pull 时版本变了，行为不一致
```

生产环境用具体版本标签（如 mysql:8.0.36）。
