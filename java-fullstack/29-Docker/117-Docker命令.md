---
title: Docker 命令
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [docker, docker-pull, docker-run, docker-ps, docker-exec, docker-logs, docker-inspect, docker-stop, docker-rm, docker-rmi]
---

# Docker 命令

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [镜像命令](#镜像命令)
- [容器生命周期命令](#容器生命周期命令)
- [容器操作命令](#容器操作命令)
- [日志与排查命令](#日志与排查命令)
- [资源与清理命令](#资源与清理命令)
- [应用场景实战](#应用场景实战)

## 概述

Docker 命令按功能分为镜像管理、容器生命周期、容器操作、日志排查、资源清理五类。

```text
命令分类：
1. 镜像命令 —— pull、images、build、tag、rmi
2. 容器生命周期 —— run、start、stop、restart、rm
3. 容器操作 —— ps、exec、cp
4. 日志排查 —— logs、inspect、top、stats
5. 资源清理 —— prune、system df
```

## 镜像命令

### docker pull —— 拉取镜像

```bash
docker pull nginx                 # 拉取 latest
docker pull nginx:1.25            # 拉取指定版本
docker pull mysql:8.0             # 拉取 MySQL 8.0
```

### docker images —— 查看镜像

```bash
docker images                     # 查看所有镜像
docker images -a                  # 含中间层镜像
docker images nginx               # 过滤
docker images -q                  # 只显示镜像 ID
```

### docker build —— 构建镜像

```bash
docker build -t myapp:1.0 .       # 构建（当前目录 Dockerfile）
docker build -f Dockerfile.prod -t myapp:1.0 .  # 指定 Dockerfile
docker build --no-cache -t myapp:1.0 .          # 不使用缓存
```

### docker tag —— 打标签

```bash
docker tag myapp:1.0 myapp:latest             # 打 latest 标签
docker tag myapp:1.0 registry.example.com/myapp:1.0  # 私有仓库标签
```

### docker rmi —— 删除镜像

```bash
docker rmi nginx:latest          # 删除镜像
docker rmi -f nginx:latest       # 强制删除
docker rmi $(docker images -q)   # 删除所有镜像（危险！）
```

## 容器生命周期命令

### docker run —— 创建并启动容器

```bash
docker run nginx                          # 前台运行
docker run -d nginx                       # 后台运行
docker run -it ubuntu bash                # 交互式
docker run --name web -p 80:80 nginx      # 命名 + 端口映射
docker run --rm nginx                     # 停止后自动删除
```

### docker start / stop / restart

```bash
docker start web              # 启动已停止的容器
docker stop web               # 停止容器（优雅，SIGTERM）
docker stop -t 10 web         # 停止，等待 10 秒
docker restart web            # 重启容器
docker kill web               # 强制停止（SIGKILL）
```

### docker rm —— 删除容器

```bash
docker rm web                 # 删除已停止的容器
docker rm -f web              # 强制删除（运行中的）
docker rm $(docker ps -aq)    # 删除所有容器
```

## 容器操作命令

### docker ps —— 查看容器

```bash
docker ps                     # 运行中的容器
docker ps -a                  # 所有容器（含停止）
docker ps -q                  # 只显示容器 ID
docker ps -l                  # 最近创建的容器
docker ps --filter "name=web" # 过滤
```

### docker exec —— 进入容器执行命令

```bash
docker exec -it web bash              # 进入容器（交互式 shell）
docker exec web ls /                  # 执行命令
docker exec -it web mysql -uroot -p   # 进入 MySQL
```

### docker cp —— 容器和宿主机复制文件

```bash
docker cp file.txt web:/tmp/          # 宿主机 → 容器
docker cp web:/tmp/file.txt ./        # 容器 → 宿主机
docker cp web:/app/logs ./logs        # 复制目录
```

## 日志与排查命令

### docker logs —— 查看日志

```bash
docker logs web                # 查看日志
docker logs -f web             # 实时跟踪（类似 tail -f）
docker logs --tail 100 web     # 最后 100 行
docker logs --since 1h web     # 最近 1 小时
docker logs -f --tail 50 web   # 从最后 50 行开始跟踪
```

### docker inspect —— 查看详情

```bash
docker inspect web                     # 完整信息（JSON）
docker inspect web | grep IPAddress    # 查容器 IP
docker inspect -f '{{.State.Status}}' web   # 查状态（格式化）
docker inspect -f '{{.NetworkSettings.IPAddress}}' web  # 查 IP
```

### docker top —— 查看容器进程

```bash
docker top web               # 容器内进程
```

### docker stats —— 资源监控

```bash
docker stats                 # 实时资源占用（CPU/内存/网络）
docker stats web             # 指定容器
docker stats --no-stream     # 一次性输出
```

## 资源与清理命令

### docker system df —— 查看占用

```bash
docker system df             # 磁盘占用总览
docker system df -v          # 详细
```

### docker prune —— 清理

```bash
docker system prune          # 清理未使用的容器、网络、镜像
docker system prune -a       # 清理所有未使用的资源（含镜像）
docker container prune       # 清理停止的容器
docker image prune           # 清理无标签的镜像
docker volume prune          # 清理未使用的数据卷
```

```bash
# 彻底清理（危险，会删所有未使用资源）
docker system prune -a --volumes
```

## 应用场景实战

### 场景 1：部署并排查 Java 应用

```bash
# 1. 构建镜像
docker build -t myapp:1.0 .

# 2. 运行
docker run -d --name myapp -p 8080:8080 myapp:1.0

# 3. 查看状态
docker ps | grep myapp

# 4. 查看日志（排查问题）
docker logs -f --tail 100 myapp

# 5. 进入容器排查
docker exec -it myapp bash
# 容器内：ls /app、cat application.yml

# 6. 查看资源占用
docker stats myapp
```

### 场景 2：数据库初始化

```bash
# 运行 MySQL
docker run -d --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=123456 \
  -e MYSQL_DATABASE=mydb \
  mysql:8.0

# 等待启动完成
docker logs mysql   # 看到 "ready for connections" 即就绪

# 进入 MySQL 执行 SQL
docker exec -it mysql mysql -uroot -p123456
```

### 场景 3：磁盘清理

```bash
# 查看磁盘占用
docker system df

# 清理停止的容器、无标签镜像、未使用的网络
docker system prune

# 查看并清理大镜像
docker images
docker rmi <不用的镜像>
```
