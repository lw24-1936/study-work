---
title: Kubernetes 运维
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [kubernetes, kubectl, helm, probe, hpa, rolling-update, rollback]
---

# Kubernetes 运维

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [kubectl 常用命令](#kubectl-常用命令)
- [Probe 探针](#probe-探针)
- [HPA 自动伸缩](#hpa-自动伸缩)
- [Rolling Update 与 Rollback](#rolling-update-与-rollback)
- [Helm 包管理](#helm-包管理)
- [应用场景实战](#应用场景实战)

## 概述

Kubernetes 运维涵盖日常操作（kubectl）、健康检查（Probe）、弹性伸缩（HPA）、发布回滚、包管理（Helm）。

```text
运维核心内容：
1. kubectl —— 日常操作命令
2. Probe —— 探针（存活/就绪）
3. HPA —— 自动伸缩
4. 滚动更新/回滚 —— 发布管理
5. Helm —— 应用包管理
```

## kubectl 常用命令

kubectl 是 K8s 的命令行工具，所有操作都通过它。

### 查看资源

```bash
kubectl get pods                    # 查看 Pod
kubectl get pods -o wide            # 详细信息（IP、节点）
kubectl get pods -w                 # 实时监控（watch）
kubectl get all                     # 查看所有资源
kubectl get nodes                   # 查看节点
kubectl get svc                     # 查看 Service
kubectl get deploy                  # 查看 Deployment
kubectl describe pod myapp          # Pod 详情（排查问题）
kubectl get events --sort-by=.metadata.creationTimestamp  # 事件
```

### 查看日志

```bash
kubectl logs myapp                        # 查看 Pod 日志
kubectl logs -f myapp                     # 实时跟踪
kubectl logs myapp --tail 100             # 最后 100 行
kubectl logs myapp -c sidecar             # 指定容器（多容器）
kubectl logs deploy/myapp                 # 查看 Deployment 日志
```

### 进入容器

```bash
kubectl exec -it myapp -- bash            # 进入 Pod
kubectl exec myapp -- ls /                # 执行命令
kubectl cp myapp:/app/logs ./logs         # 复制文件
```

### 资源操作

```bash
kubectl apply -f app.yaml         # 创建/更新（声明式）
kubectl delete -f app.yaml        # 删除
kubectl scale deploy myapp --replicas=5   # 扩缩容
kubectl delete pod myapp          # 删除 Pod
```

## Probe 探针

探针（Probe）是容器的健康检查，K8s 据此决定重启或摘除流量。

### 三种探针

| 探针 | 作用 | 失败后果 |
|------|------|---------|
| livenessProbe | 存活检查（是否活着） | 重启容器 |
| readinessProbe | 就绪检查（能否服务） | 摘除流量 |
| startupProbe | 启动检查（是否启动完成） | 保护慢启动 |

```text
liveness vs readiness：
liveness —— 容器挂了 → 重启（自愈）
readiness —— 容器没准备好 → 不分配流量（等就绪）
```

### 探针的三种方式

```yaml
livenessProbe:
  httpGet:                    # 方式 1：HTTP 请求
    path: /actuator/health
    port: 8080
  # 方式 2：TCP 连接
  # tcpSocket:
  #   port: 8080
  # 方式 3：执行命令
  # exec:
  #   command: ["cat", "/tmp/healthy"]
  initialDelaySeconds: 30     # 启动后延迟探测
  periodSeconds: 10           # 探测间隔
  timeoutSeconds: 5           # 超时
  failureThreshold: 3         # 失败次数（3 次失败判定）
```

### Java 应用探针配置

```yaml
# Spring Boot Actuator 提供健康检查端点
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 10
```

## HPA 自动伸缩

HPA（Horizontal Pod Autoscaler）根据负载自动调整 Pod 副本数。

### HPA 原理

```text
HPA 监控 Pod 的 CPU/内存等指标，
负载高时自动扩容，负载低时自动缩容。
```

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 2              # 最小副本数
  maxReplicas: 10             # 最大副本数
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70   # 平均 CPU 70% 触发扩容
```

### HPA 的前提

```text
1. 需要 metrics-server（采集指标）
2. Pod 设置了 resources.requests（计算利用率）
3. 应用支持水平扩展（无状态）
```

```bash
kubectl get hpa                   # 查看 HPA
kubectl autoscale deploy myapp --min=2 --max=10 --cpu-percent=70  # 快速创建
```

## Rolling Update 与 Rollback

滚动更新是零停机发布，回滚是恢复到上一版本。

### 滚动更新原理

```text
滚动更新（Rolling Update）：
1. 创建新的 Pod（新版本）
2. 新 Pod 就绪后，删除旧的 Pod
3. 逐步替换，直到全部更新

优势：零停机、可控制更新节奏
```

### 更新策略

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 最多多创建 1 个 Pod
      maxUnavailable: 0    # 最多 0 个不可用（严格）
```

### 更新与回滚

```bash
kubectl set image deploy/myapp myapp=myapp:2.0   # 更新镜像
kubectl rollout status deploy/myapp              # 查看更新状态
kubectl rollout history deploy/myapp             # 更新历史
kubectl rollout undo deploy/myapp                # 回滚到上一版本
kubectl rollout undo deploy/myapp --to-revision=2  # 回滚到指定版本
```

### 回滚的场景

```text
1. 新版本有 bug，回滚到稳定版本
2. 更新失败（新 Pod 起不来），自动或手动回滚
3. 灰度发现问题，快速回退
```

## Helm 包管理

Helm 是 K8s 的包管理器（类似 apt/yum），简化应用的部署和管理。

### Helm 核心概念

```text
Chart —— 应用包（一组 K8s 资源模板）
Release —— Chart 的部署实例
Repository —— Chart 仓库
```

```text
Helm 的价值：
1. 模板化 —— 一个 Chart 适配不同环境（values 传参）
2. 复用 —— 复用官方或社区 Chart（MySQL、Nginx）
3. 版本管理 —— 应用版本、回滚
```

### 常用命令

```bash
helm install myapp ./myapp-chart       # 安装
helm install myapp ./chart --set image.tag=2.0  # 安装（传参）
helm upgrade myapp ./myapp-chart       # 升级
helm rollback myapp 1                  # 回滚到版本 1
helm uninstall myapp                   # 卸载
helm list                              # 查看已安装
helm repo add bitnami https://charts.bitnami.com/bitnami  # 添加仓库
helm install mysql bitnami/mysql       # 安装官方 Chart
```

### Chart 结构

```text
mychart/
├── Chart.yaml          # Chart 元数据
├── values.yaml         # 默认配置
├── templates/          # 模板文件
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
└── charts/             # 依赖 Chart
```

### 模板示例

```yaml
# templates/deployment.yaml（用 values 变量）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.name }}
spec:
  replicas: {{ .Values.replicas }}
  template:
    spec:
      containers:
      - name: {{ .Values.name }}
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
```

```yaml
# values.yaml
name: myapp
replicas: 3
image:
  repository: myapp
  tag: "1.0"
```

## 应用场景实战

### 场景 1：排查应用问题

```bash
# 1. 查看 Pod 状态
kubectl get pods -o wide

# 2. 查看 Pod 详情（事件）
kubectl describe pod myapp-xxx

# 3. 查看日志
kubectl logs -f myapp-xxx --tail 100

# 4. 进入容器排查
kubectl exec -it myapp-xxx -- bash

# 5. 查看资源使用
kubectl top pods
kubectl top nodes
```

### 场景 2：发布新版本 + 回滚

```bash
# 1. 发布新版本
kubectl set image deploy/myapp myapp=myapp:2.0

# 2. 监控更新
kubectl rollout status deploy/myapp

# 3. 发现问题，回滚
kubectl rollout undo deploy/myapp
```

### 场景 3：配置 HPA 自动伸缩

```bash
# 创建 HPA（CPU 70% 触发，2-10 个副本）
kubectl autoscale deploy myapp --min=2 --max=10 --cpu-percent=70

# 查看 HPA 状态
kubectl get hpa
```

## 最佳实践与踩坑记录

### 最佳实践

1. **配置 liveness + readiness 探针**。liveness 自愈，readiness 摘流量。

2. **滚动更新设置 maxUnavailable**。控制更新节奏，保证可用性。

3. **发布用 rollout，回滚用 rollout undo**。保留版本历史，快速回退。

4. **复杂应用用 Helm 管理**。模板化、版本化、可复用。

5. **监控用 kubectl top**。及时了解资源使用，配合 HPA。

### 踩坑记录

**坑 1：探针配置错误导致反复重启**

```yaml
livenessProbe:
  httpGet:
    path: /health    # 路径不对，一直失败
    port: 8080
  initialDelaySeconds: 5   # 启动延迟太短，应用还没起来
```

探针路径要正确，initialDelaySeconds 要足够（慢启动应用加大）。

**坑 2：滚动更新卡住**

```text
滚动更新卡住（新 Pod 起不来）：
新 Pod 镜像错误、探针失败，更新一直不完成
```

kubectl rollout status 查看，kubectl rollout undo 回滚。

**坑 3：HPA 不生效**

```text
HPA 创建了但没反应：
1. 没装 metrics-server
2. Pod 没设 resources.requests
```

HPA 需要 metrics-server + requests 配置。

**坑 4：误删 Pod 导致服务中断**

```text
直接删 Pod（kubectl delete pod），Deployment 会重建
但如果删除 Deployment，服务就真的没了
```

删除前确认资源类型，删除 Deployment 才是删除应用。

**坑 5：kubectl logs 看不到日志**

```text
Pod 重启后，旧容器日志丢失
多容器 Pod 要指定 -c 容器名
```

重启的 Pod 用 `kubectl logs --previous` 看上次日志。

**坑 6：Helm 升级覆盖手动修改**

```text
手动改了 K8s 资源，Helm 升级又覆盖回去了
```

用 Helm 管理的资源要通过 Helm 修改（values），不要手动改。
