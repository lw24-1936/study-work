---
title: Kubernetes 基础
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [kubernetes, cluster, node, pod, deployment, replicaset, statefulset, daemonset, job, cronjob]
---

# Kubernetes 基础

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [核心概念：Cluster 与 Node](#核心概念cluster-与-node)
- [Pod 最小调度单元](#pod-最小调度单元)
- [Deployment 与 ReplicaSet](#deployment-与-replicaset)
- [StatefulSet 有状态应用](#statefulset-有状态应用)
- [DaemonSet 守护进程](#daemonset-守护进程)
- [Job 与 CronJob](#job-与-cronjob)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Kubernetes（K8s）是容器编排平台，自动化部署、扩展和管理容器应用，是云原生的基石。

```text
为什么需要 Kubernetes：
1. 自动化调度 —— 容器自动分配到合适的节点
2. 自愈 —— 容器挂了自动重启，节点挂了自动迁移
3. 弹性伸缩 —— 按负载自动扩缩容
4. 服务发现 —— 自动负载均衡和 DNS
5. 滚动更新 —— 零停机发布
```

```text
Docker vs Kubernetes：
Docker —— 单个容器的运行（单机）
Kubernetes —— 容器集群的编排（多机）
K8s 是 Docker 之上的编排层，管理成百上千个容器
```

## 核心概念：Cluster 与 Node

### Cluster 集群

```text
Cluster（集群）= 一组 Node（节点）组成的容器运行环境。

K8s 集群结构：
┌─────────────────────────────────┐
│          Control Plane（控制平面）│
│  API Server / Scheduler / etcd   │
├─────────────────────────────────┤
│  Node 1    Node 2    Node 3      │  ← 工作节点
│  (Pod...)  (Pod...)  (Pod...)    │
└─────────────────────────────────┘
```

### Node 节点

```text
Node（节点）是集群中的工作机器（物理机或虚拟机）：
1. Control Plane（Master）—— 管理节点（调度、状态、API）
2. Worker Node —— 工作节点（运行 Pod）
```

```bash
kubectl get nodes          # 查看所有节点
kubectl describe node node1  # 节点详情
```

## Pod 最小调度单元

Pod 是 K8s 最小的调度单元，包含一个或多个容器。

### Pod 是什么

```text
Pod = 一个或多个紧密耦合的容器组：
1. 共享网络命名空间（同一 IP、端口空间）
2. 共享存储卷
3. 一起调度、一起启停
```

```text
Pod 与容器的关系：
1. Pod 是调度单位，容器是运行单位
2. 一个 Pod 通常一个主容器（单容器 Pod 最常见）
3. 多容器 Pod 用于 sidecar（日志收集、代理）
```

### Pod 定义（YAML）

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
  labels:
    app: myapp
spec:
  containers:
  - name: myapp
    image: myapp:1.0
    ports:
    - containerPort: 8080
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

### Pod 的生命周期

```text
Pending → Running → Succeeded/Failed

Pending   —— 已创建，等待调度或镜像拉取
Running   —— 运行中
Succeeded —— 正常退出（一次性任务）
Failed    —— 异常退出
```

```bash
kubectl get pods              # 查看 Pod
kubectl describe pod myapp    # Pod 详情
kubectl logs myapp            # Pod 日志
kubectl exec -it myapp -- bash  # 进入 Pod
kubectl delete pod myapp      # 删除 Pod
```

## Deployment 与 ReplicaSet

Deployment 是无状态应用的标准部署方式，管理 Pod 副本和滚动更新。

### 层级关系

```text
Deployment → ReplicaSet → Pod

Deployment   —— 声明期望状态（副本数、镜像版本）
ReplicaSet   —— 维护 Pod 副本数（自动创建）
Pod          —— 实际运行实例
```

### Deployment 定义

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3                    # 3 个副本
  selector:
    matchLabels:
      app: myapp
  template:                      # Pod 模板
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:1.0
        ports:
        - containerPort: 8080
```

### Deployment 的核心能力

```text
1. 副本管理 —— replicas 指定副本数，自动维护
2. 滚动更新 —— 更新镜像版本，逐步替换旧 Pod
3. 回滚 —— 更新失败可回滚到上一版本
4. 自愈 —— Pod 挂了自动重建
```

```bash
kubectl create deployment myapp --image=myapp:1.0   # 创建
kubectl scale deployment myapp --replicas=5         # 扩容
kubectl set image deployment/myapp myapp=myapp:2.0  # 更新镜像
kubectl rollout status deployment/myapp             # 查看更新状态
kubectl rollout undo deployment/myapp               # 回滚
```

## StatefulSet 有状态应用

StatefulSet 用于有状态应用（数据库等），提供稳定的网络标识和存储。

### 与 Deployment 的区别

| 维度 | Deployment | StatefulSet |
|------|-----------|-------------|
| 适用 | 无状态应用 | 有状态应用 |
| Pod 名称 | 随机（myapp-xxxx） | 有序（mysql-0、mysql-1） |
| 网络标识 | 无稳定标识 | 稳定（Headless Service） |
| 存储 | 共享/无 | 独立 PVC |
| 启停顺序 | 无序 | 有序（0,1,2...） |

### StatefulSet 定义

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql           # 稳定的服务名
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:        # 每个 Pod 独立存储
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### StatefulSet 适用场景

```text
1. 数据库（MySQL、MongoDB）
2. 消息队列（Kafka、RabbitMQ）
3. 需要稳定标识和独立存储的应用
```

## DaemonSet 守护进程

DaemonSet 保证每个节点运行一个 Pod，用于节点级服务。

### DaemonSet 的特点

```text
1. 每个节点运行一个 Pod（自动在新节点上创建）
2. 节点删除时自动清理
3. 适合节点级服务
```

### 典型应用

```text
1. 日志收集 —— Fluentd、Filebeat（收集每个节点的日志）
2. 监控代理 —— Prometheus Node Exporter
3. 网络插件 —— Calico、Flannel
```

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: filebeat
spec:
  selector:
    matchLabels:
      app: filebeat
  template:
    metadata:
      labels:
        app: filebeat
    spec:
      containers:
      - name: filebeat
        image: filebeat:8.0
```

## Job 与 CronJob

Job 和 CronJob 用于一次性任务和定时任务。

### Job（一次性任务）

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  completions: 1          # 成功完成次数
  template:
    spec:
      restartPolicy: Never   # 失败不重启（或 OnFailure）
      containers:
      - name: migration
        image: migration:1.0
```

### CronJob（定时任务）

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: data-backup
spec:
  schedule: "0 2 * * *"   # 每天凌晨 2 点（cron 表达式）
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: backup
            image: backup:1.0
```

```text
Job vs CronJob：
Job —— 执行一次（数据迁移、初始化）
CronJob —— 定时执行（备份、清理、报表）
```

## 应用场景实战

### 场景 1：部署无状态 Java 应用（Deployment）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:
      - name: order-service
        image: order-service:1.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
        livenessProbe:            # 存活探针
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 30
        readinessProbe:           # 就绪探针
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 10
```

### 场景 2：部署有状态 MySQL（StatefulSet）

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
```

## 最佳实践与踩坑记录

### 最佳实践

1. **无状态应用用 Deployment，有状态用 StatefulSet**。区分清楚应用类型。

2. **配置资源 requests 和 limits**。requests 用于调度，limits 防止资源失控。

3. **配置存活和就绪探针**。liveness 重启故障 Pod，readiness 摘除流量。

4. **镜像用具体版本标签**。不要用 latest（K8s 默认拉取策略会缓存）。

5. **声明式管理**。用 YAML 文件 + kubectl apply，不要手动 kubectl run。

### 踩坑记录

**坑 1：Pod 一直 Pending**

```text
Pod 卡在 Pending，通常是：
1. 资源不足（requests 超过节点可用）
2. 没有匹配的节点（节点选择器、污点）
```

kubectl describe pod 查看事件，定位原因。

**坑 2：ImagePullBackOff**

```text
镜像拉取失败（ImagePullBackOff）：
1. 镜像不存在或 tag 错误
2. 私有仓库需要 imagePullSecrets
```

检查镜像名和 tag，私有仓库配置 imagePullSecrets。

**坑 3：CrashLoopBackOff**

```text
容器反复崩溃重启（CrashLoopBackOff）：
1. 应用启动失败（配置错误、依赖不可用）
2. 探针配置错误
```

kubectl logs 查看崩溃原因。

**坑 4：删除 Deployment 后 Pod 又出现**

```text
kubectl delete pod 后，Deployment 自动重建 Pod
要删除应用，删除 Deployment 而不是 Pod
```

Pod 由 Deployment 管理，删除 Deployment 才能彻底删除。

**坑 5：StatefulSet 的 Pod 删除后数据丢失**

```text
StatefulSet 的 Pod 删除后，PVC 默认保留
但如果删除了 PVC，数据就丢了
```

StatefulSet 的存储要谨慎删除，用 Retain 策略。

**坑 6：配置变更不生效**

```text
修改了环境变量，但 Pod 没重启，配置不生效
```

kubectl rollout restart deployment 触发滚动重启。
