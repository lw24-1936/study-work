---
title: Docker Compose
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [docker-compose, compose, service, network, volume, environment, healthcheck, dependency]
---

# Docker Compose

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [核心概念](#核心概念)
- [compose.yml 详解](#composeyml-详解)
- [常用命令](#常用命令)
- [Service 服务](#service-服务)
- [Network 与 Volume](#network-与-volume)
- [Environment 环境变量](#environment-环境变量)
- [Healthcheck 与依赖](#healthcheck-与依赖)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Docker Compose 是多容器编排工具，用一个 YAML 文件定义和运行多个容器，解决"多个容器如何一起启动"的问题。

```text
为什么需要 Compose：
1. 一个应用需要多个容器（应用 + MySQL + Redis + Nginx）
2. 手动 docker run 每个容器很繁琐
3. Compose 用 YAML 定义所有服务，一条命令启动全部
```

```text
Compose 的价值：
1. 声明式定义 —— YAML 描述所有服务
2. 一键启动 —— docker compose up 启动全部
3. 服务编排 —— 依赖、网络、数据卷统一管理
4. 环境隔离 —— 不同环境用不同 compose 文件
```

## 核心概念

```text
Compose 的核心概念：
1. Service（服务）—— 一个容器（如 app、mysql、redis）
2. Network（网络）—— 服务间通信
3. Volume（数据卷）—— 数据持久化
4. Environment（环境变量）—— 配置注入
```

```text
Compose 文件：
compose.yml / docker-compose.yml（推荐新版 compose.yml）
```

## compose.yml 详解

```yaml
# compose.yml
services:                    # 服务定义
  app:                       # 服务名
    image: myapp:1.0         # 镜像
    build: .                 # 或从 Dockerfile 构建
    ports:
      - "8080:8080"          # 端口映射
    environment:             # 环境变量
      - SPRING_PROFILES_ACTIVE=prod
    volumes:                 # 数据卷
      - app-logs:/app/logs
    depends_on:              # 依赖
      - mysql
      - redis
    restart: always

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=123456
    volumes:
      - mysql-data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"

volumes:                     # 声明数据卷
  app-logs:
  mysql-data:
  redis-data:
```

## 常用命令

```bash
docker compose up -d              # 后台启动所有服务
docker compose up -d app          # 启动指定服务
docker compose down               # 停止并删除所有服务
docker compose down -v            # 停止并删除（含数据卷）
docker compose ps                 # 查看服务状态
docker compose logs -f            # 查看日志（实时）
docker compose logs -f app        # 指定服务日志
docker compose restart app        # 重启服务
docker compose stop app           # 停止服务
docker compose build              # 构建镜像
docker compose pull               # 拉取镜像
docker compose exec app bash      # 进入服务容器
docker compose config             # 校验配置文件
```

```text
新版命令（docker compose）vs 旧版（docker-compose）：
新版是 docker 子命令（推荐），旧版是独立命令（已废弃）
```

## Service 服务

### 服务的定义方式

```yaml
services:
  # 方式 1：用现成镜像
  mysql:
    image: mysql:8.0

  # 方式 2：从 Dockerfile 构建
  app:
    build:
      context: .                # Dockerfile 所在目录
      dockerfile: Dockerfile    # Dockerfile 文件名

  # 方式 3：镜像 + 构建（优先构建）
  app2:
    image: myapp:1.0
    build: .
```

### 服务常用配置

```yaml
services:
  app:
    image: myapp:1.0
    container_name: myapp       # 容器名（自定义）
    ports: ["8080:8080"]        # 端口
    environment:                # 环境变量
      - JAVA_OPTS=-Xmx512m
    restart: unless-stopped     # 重启策略
    networks: [backend]         # 网络
    volumes: ["logs:/app/logs"] # 数据卷
    command: ["java", "-jar", "app.jar"]  # 启动命令
    logging:                    # 日志配置
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## Network 与 Volume

### Network 网络

```yaml
services:
  app:
    networks: [backend]         # 加入 backend 网络
  mysql:
    networks: [backend]

networks:                       # 声明网络
  backend:                      # Compose 自动创建网络
    driver: bridge
```

```text
Compose 网络特点：
1. 默认创建独立网络（服务间用服务名通信）
2. app 容器内用 "mysql" 访问 MySQL（服务名解析）
3. 网络隔离：不同 compose 项目网络隔离
```

### Volume 数据卷

```yaml
services:
  mysql:
    volumes:
      - mysql-data:/var/lib/mysql    # 命名卷（推荐）
      - ./conf:/etc/mysql/conf.d     # 绑定挂载（本地目录）

volumes:
  mysql-data:                        # 声明命名卷
```

```text
命名卷 vs 绑定挂载：
命名卷（mysql-data）—— Docker 管理，生产推荐
绑定挂载（./conf）—— 本地目录，开发调试方便
```

## Environment 环境变量

### 环境变量注入方式

```yaml
services:
  app:
    environment:                     # 方式 1：直接定义
      - SPRING_PROFILES_ACTIVE=prod
      - DB_HOST=mysql
      DB_PASSWORD: "123456"          # 或 map 形式

    env_file:                        # 方式 2：从文件读取
      - .env
```

### .env 文件（Compose 变量替换）

```yaml
# .env 文件
MYSQL_PASSWORD=123456
APP_PORT=8080

# compose.yml 引用
services:
  app:
    ports:
      - "${APP_PORT}:8080"           # 引用 .env 变量
  mysql:
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_PASSWORD}
```

### 环境变量优先级

```text
1. shell 环境变量（最高）
2. .env 文件
3. compose.yml 里的 environment
4. Dockerfile 的 ENV（最低）
```

## Healthcheck 与依赖

### Healthcheck 健康检查

```yaml
services:
  mysql:
    image: mysql:8.0
    healthcheck:                          # 健康检查
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s                       # 间隔
      timeout: 5s                         # 超时
      retries: 5                          # 重试次数
      start_period: 30s                   # 启动宽限期
```

### depends_on 依赖

```yaml
services:
  app:
    depends_on:                # 基础依赖（只保证启动顺序）
      - mysql
      - redis

  app2:
    depends_on:                # 高级依赖（等待健康）
      mysql:
        condition: service_healthy   # 等 mysql 健康后才启动
      redis:
        condition: service_started
```

```text
depends_on 两种方式：
1. 简单：depends_on: [mysql]（只保证启动顺序，不等就绪）
2. 健康：condition: service_healthy（等健康检查通过）
```

## 应用场景实战

### 场景 1：Java 应用 + MySQL + Redis 完整编排

```yaml
services:
  app:
    build: .
    container_name: myapp
    ports:
      - "8080:8080"
    environment:
      - SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/mydb
      - SPRING_DATASOURCE_USERNAME=root
      - SPRING_DATASOURCE_PASSWORD=123456
      - SPRING_DATA_REDIS_HOST=redis
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
    restart: always
    networks: [backend]

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=123456
      - MYSQL_DATABASE=mydb
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [backend]

  redis:
    image: redis:7
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks: [backend]

volumes:
  mysql-data:
  redis-data:

networks:
  backend:
```

### 场景 2：微服务多服务编排

```yaml
services:
  nacos:
    image: nacos/nacos-server:v2.3.0
    ports: ["8848:8848", "9848:9848"]
    environment:
      - MODE=standalone

  gateway:
    build: ./gateway
    ports: ["8080:8080"]
    depends_on:
      - nacos

  user-service:
    build: ./user-service
    depends_on:
      - nacos
      - mysql

  order-service:
    build: ./order-service
    depends_on:
      - nacos
      - mysql
      - redis
```

## 最佳实践与踩坑记录

### 最佳实践

1. **数据库用健康检查 + 条件依赖**。app 等 mysql 健康后才启动，避免连接失败。

2. **数据卷用命名卷**。数据库数据持久化，容器重建数据不丢。

3. **敏感信息用 .env 文件**。密码等不硬编码在 compose.yml。

4. **容器内通信用服务名**。app 访问 mysql 用服务名，不要写 IP。

5. **日志限制大小**。logging 配置 max-size，防止日志撑爆磁盘。

### 踩坑记录

**坑 1：depends_on 不等服务就绪**

```yaml
depends_on:
  - mysql    # 只保证启动顺序，mysql 可能还没就绪
# app 启动时 mysql 还在初始化，连接失败
```

用 `condition: service_healthy` 等健康检查通过，或应用加重试。

**坑 2：容器内用 localhost 连数据库**

```yaml
environment:
  - SPRING_DATASOURCE_URL=jdbc:mysql://localhost:3306/mydb  # 错误！
# 容器内 localhost 是容器自己，不是 mysql 容器
```

容器间通信用服务名（mysql），不是 localhost。

**坑 3：数据卷不声明导致数据丢失**

```yaml
services:
  mysql:
    image: mysql:8.0     # 没挂数据卷
# docker compose down -v 后数据丢失
```

数据库必须挂命名卷持久化。

**坑 4：端口冲突**

```yaml
services:
  app1:
    ports: ["8080:8080"]
  app2:
    ports: ["8080:8080"]   # 端口冲突，启动失败
```

检查端口冲突，用不同宿主机端口。

**坑 5：.env 变量不生效**

```yaml
# .env 文件改了，但 compose 用的还是旧值
# 需要重新 up，或 config 查看实际值
```

`docker compose config` 查看变量替换后的实际配置。

**坑 6：compose 版本兼容问题**

```yaml
version: "3"    # 旧版写法，新版 compose 已不需要 version 字段
```

新版 compose（docker compose）不需要 version 字段，旧版字段会告警。
