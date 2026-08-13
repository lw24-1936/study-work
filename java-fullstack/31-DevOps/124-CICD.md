---
title: CI/CD
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [ci-cd, jenkins, github-actions, gitlab-ci, pipeline, build, test, package, deploy]
---

# CI/CD

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [CI/CD 概念](#cicd-概念)
- [Pipeline 流水线](#pipeline-流水线)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Jenkins](#jenkins)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

CI/CD 是持续集成和持续交付/部署，自动化构建、测试、部署流程，提升交付效率和质量。

```text
CI（持续集成）—— 代码合并后自动构建、测试
CD（持续交付/部署）—— 自动部署到环境

价值：
1. 快速反馈 —— 提交后立即知道是否通过
2. 减少人工 —— 自动化构建部署
3. 质量保障 —— 自动测试
4. 快速发布 —— 一键/自动部署
```

## CI/CD 概念

### CI（Continuous Integration）

```text
持续集成：开发者频繁合并代码，每次合并自动构建 + 测试

流程：
提交代码 → 触发构建 → 运行测试 → 反馈结果
```

### CD（Continuous Delivery/Deployment）

```text
持续交付（Delivery）—— 自动构建测试，人工确认部署
持续部署（Deployment）—— 自动构建测试部署，全自动
```

```text
CI → CD（交付）→ CD（部署）

提交 → 构建 → 测试 → 打包 → 部署
        （自动）      （自动）  （自动/手动）
```

### CI/CD 流水线阶段

```text
Build（构建）→ Test（测试）→ Package（打包）→ Deploy（部署）

Build    —— 编译、打包（mvn package）
Test     —— 单元测试、集成测试
Package  —— 构建 Docker 镜像
Deploy   —— 部署到服务器/K8s
```

## Pipeline 流水线

Pipeline 是 CI/CD 的核心，定义构建部署的自动化流程。

### Pipeline 的阶段

```text
stages:
  - build       # 构建
  - test        # 测试
  - package     # 打包
  - deploy      # 部署
```

### Java 项目的典型 Pipeline

```text
1. build    —— mvn clean package（编译打包）
2. test     —— mvn test（单元测试）
3. package  —— docker build（构建镜像）
4. deploy   —— docker push + kubectl apply（部署）
```

## GitHub Actions

GitHub Actions 是 GitHub 的 CI/CD 服务，用 YAML 定义工作流。

### 工作流文件

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]          # main 分支 push 触发
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest      # 运行环境
    steps:
      - uses: actions/checkout@v4       # 检出代码

      - name: Setup JDK
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Build with Maven
        run: mvn clean package

      - name: Run tests
        run: mvn test

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: app
          path: target/*.jar
```

### 完整 CI/CD（构建 + 部署）

```yaml
name: CI/CD

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup JDK
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      # 构建
      - name: Build
        run: mvn clean package -DskipTests

      # 构建 Docker 镜像
      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      # 推送到镜像仓库
      - name: Push to registry
        run: |
          docker tag myapp:${{ github.sha }} registry.example.com/myapp:${{ github.sha }}
          docker push registry.example.com/myapp:${{ github.sha }}

      # 部署到 K8s
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deploy/myapp myapp=registry.example.com/myapp:${{ github.sha }}
```

### GitHub Actions 核心概念

```text
Workflow —— 工作流（.github/workflows/*.yml）
Job —— 任务（并行/串行执行）
Step —— 步骤（Job 内的操作）
Action —— 可复用的步骤（uses）
Runner —— 运行环境（ubuntu/windows/mac）
```

## GitLab CI

GitLab CI 是 GitLab 内置的 CI/CD，用 .gitlab-ci.yml 定义。

### .gitlab-ci.yml

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build-job:
  stage: build
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn clean package -DskipTests
  artifacts:
    paths:
      - target/*.jar

test-job:
  stage: test
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn test

deploy-job:
  stage: deploy
  only:
    - main                 # 只有 main 分支部署
  script:
    - docker build -t myapp:latest .
    - docker push registry.example.com/myapp:latest
```

### GitLab CI 核心概念

```text
Runner —— 执行任务的机器（GitLab Runner）
Pipeline —— 流水线（一次 CI/CD 执行）
Stage —— 阶段（串行）
Job —— 任务（同 stage 并行）
```

## Jenkins

Jenkins 是最经典的 CI/CD 工具，自建部署，插件丰富。

### Jenkins 特点

```text
1. 自建 —— 部署在自己的服务器
2. 插件丰富 —— 上千个插件
3. 灵活 —— Jenkinsfile 定义流水线
4. 经典 —— 历史悠久，生态成熟
```

### Jenkinsfile（Pipeline as Code）

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/example/myapp.git'
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }

        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }

        stage('Build Image') {
            steps {
                sh 'docker build -t myapp:latest .'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker push registry.example.com/myapp:latest'
                sh 'kubectl set image deploy/myapp myapp=registry.example.com/myapp:latest'
            }
        }
    }
}
```

### 三大工具对比

| 维度 | GitHub Actions | GitLab CI | Jenkins |
|------|---------------|-----------|---------|
| 部署 | 云端（GitHub） | 云端/自建 | 自建 |
| 配置 | YAML | YAML | Groovy |
| 生态 | GitHub 集成好 | GitLab 集成好 | 插件最丰富 |
| 成本 | 免费额度 | 免费额度 | 自建成本 |
| 适用 | GitHub 项目 | GitLab 项目 | 需要自建/灵活控制 |

## 应用场景实战

### 场景 1：Java 项目完整 CI/CD（GitHub Actions）

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
          cache: maven
      - name: Build & Test
        run: mvn clean verify
      - name: SonarQube Scan
        run: mvn sonar:sonar
      - name: Build Docker Image
        run: docker build -t myapp:${{ github.sha }} .
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: |
          docker push registry.example.com/myapp:${{ github.sha }}
          kubectl set image deploy/myapp myapp=myapp:${{ github.sha }}
```

### 场景 2：多环境部署

```yaml
# 不同分支部署到不同环境
deploy-dev:
  stage: deploy
  only:
    - develop          # develop 分支 → dev 环境
  script:
    - deploy_to_dev.sh

deploy-prod:
  stage: deploy
  only:
    - main             # main 分支 → prod 环境
  script:
    - deploy_to_prod.sh
```

## 最佳实践与踩坑记录

### 最佳实践

1. **流水线分阶段**。build → test → package → deploy，每阶段独立。

2. **缓存依赖**。Maven 缓存（.m2）、Docker 层缓存，加速构建。

3. **部署前自动测试**。测试失败不部署。

4. **环境隔离**。dev/test/prod 不同流水线或不同触发条件。

5. **构建产物可追溯**。用 commit SHA 作为镜像标签，可回溯。

### 踩坑记录

**坑 1：流水线不触发**

```yaml
on:
  push:
    branches: [ main ]    # 只监听 main
# 推到其他分支不触发
```

检查 on 的触发条件（分支、事件）。

**坑 2：缓存不生效导致构建慢**

```text
没配置 Maven 缓存，每次全量下载依赖，构建慢
```

配置依赖缓存（setup-java 的 cache: maven）。

**坑 3：测试不稳定导致流水线失败**

```text
测试依赖外部服务（数据库），CI 环境没有，测试失败
```

测试要自包含（Testcontainers、内存数据库），不依赖外部。

**坑 4：部署用 latest 标签**

```yaml
docker push myapp:latest   # latest 标签，无法追溯是哪个 commit
```

用 commit SHA 或版本号作为标签。

**坑 5：敏感信息硬编码**

```yaml
run: docker login -u admin -p password123   # 密码硬编码
```

用 Secrets（GitHub Secrets、GitLab Variables）管理敏感信息。

**坑 6：流水线太长**

```text
流水线执行 30 分钟，反馈慢，开发效率低
```

拆分流水线、并行任务、缓存加速、只跑相关测试。
