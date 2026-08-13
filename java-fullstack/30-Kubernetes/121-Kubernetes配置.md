---
title: Kubernetes 配置
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [kubernetes, configmap, secret, namespace, resource, limit, request]
---

# Kubernetes 配置

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [ConfigMap 配置管理](#configmap-配置管理)
- [Secret 敏感信息](#secret-敏感信息)
- [Namespace 命名空间](#namespace-命名空间)
- [Resource 资源管理](#resource-资源管理)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Kubernetes 配置管理解决"应用配置如何注入、敏感信息如何保护、资源如何隔离"的问题。

```text
配置管理的内容：
1. ConfigMap —— 非敏感配置（环境变量、配置文件）
2. Secret —— 敏感信息（密码、token、证书）
3. Namespace —— 环境隔离（dev/test/prod）
4. Resource —— 资源限制（requests/limits）
```

## ConfigMap 配置管理

ConfigMap 存储非敏感配置，以环境变量或文件方式注入 Pod。

### 创建 ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  SPRING_PROFILES_ACTIVE: "prod"
  DB_URL: "jdbc:mysql://mysql:3306/mydb"
  application.yml: |      # 或整个配置文件
    server:
      port: 8080
    spring:
      datasource:
        url: jdbc:mysql://mysql:3306/mydb
```

```bash
# 从文件创建
kubectl create configmap app-config --from-file=application.yml
kubectl get configmap
```

### 使用 ConfigMap

```yaml
# 方式 1：作为环境变量
spec:
  containers:
  - name: myapp
    image: myapp:1.0
    envFrom:
    - configMapRef:
        name: app-config        # 注入所有 key 为环境变量

# 方式 2：作为文件挂载
spec:
  containers:
  - name: myapp
    image: myapp:1.0
    volumeMounts:
    - name: config
      mountPath: /app/config    # 配置文件挂载到这里
  volumes:
  - name: config
    configMap:
      name: app-config
```

### ConfigMap 的适用场景

```text
1. 环境变量 —— 数据库地址、服务地址
2. 配置文件 —— application.yml、nginx.conf
3. 非敏感参数 —— 端口、日志级别
```

## Secret 敏感信息

Secret 存储敏感信息（密码、token、证书），以 base64 编码存储。

### 创建 Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
data:
  username: cm9vdA==          # base64 编码（root）
  password: MTIzNDU2          # base64 编码（123456）
```

```bash
# 从命令行创建
kubectl create secret generic mysql-secret \
  --from-literal=password=123456

# 从文件创建
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=admin \
  --docker-password=secret
```

### 使用 Secret

```yaml
spec:
  containers:
  - name: myapp
    image: myapp:1.0
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: mysql-secret
          key: password
```

### Secret 类型

| 类型 | 用途 |
|------|------|
| Opaque | 通用（默认） |
| kubernetes.io/dockerconfigjson | 镜像仓库认证 |
| kubernetes.io/tls | TLS 证书 |
| kubernetes.io/basic-auth | 基础认证 |

### ConfigMap vs Secret

| 维度 | ConfigMap | Secret |
|------|-----------|--------|
| 内容 | 非敏感配置 | 敏感信息 |
| 编码 | 明文 | base64（注意：不是加密！） |
| 场景 | 环境变量、配置文件 | 密码、token、证书 |

```text
重要：Secret 的 base64 只是编码，不是加密！
需要加密用 KMS、Sealed Secrets 等方案。
```

## Namespace 命名空间

Namespace 用于资源隔离，将集群划分为多个虚拟集群。

### Namespace 的用途

```text
1. 环境隔离 —— dev、test、prod 隔离
2. 团队隔离 —— 不同团队各自命名空间
3. 资源配额 —— 按命名空间限制资源
```

### 常用命令

```bash
kubectl get namespaces                    # 查看命名空间
kubectl create namespace dev              # 创建命名空间
kubectl get pods -n dev                   # 查看指定命名空间的 Pod
kubectl apply -f app.yaml -n dev          # 部署到指定命名空间
kubectl config set-context --current --namespace=dev  # 切换默认命名空间
```

### 内置命名空间

```text
default —— 默认（未指定时的命名空间）
kube-system —— 系统组件
kube-public —— 公共资源
```

### 资源配额（ResourceQuota）

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "10"       # CPU 总量限制
    requests.memory: 20Gi    # 内存总量限制
    pods: "50"               # Pod 数量限制
```

## Resource 资源管理

Resource 定义容器的资源请求和限制，是资源管理的基础。

### requests 与 limits

```yaml
spec:
  containers:
  - name: myapp
    image: myapp:1.0
    resources:
      requests:              # 请求（调度依据）
        memory: "512Mi"
        cpu: "500m"
      limits:                # 限制（上限）
        memory: "1Gi"
        cpu: "1"
```

```text
requests（请求）：
1. 调度依据 —— 节点要有足够的资源
2. 保证的最低资源

limits（限制）：
1. 资源上限 —— 容器不能超过
2. 超出 CPU 被限流，内存超出被 OOM Kill
```

### CPU 和内存单位

```text
CPU：
1 = 1 个 CPU 核心
500m = 0.5 核（m 是毫核）
0.25 = 250m

内存：
512Mi = 512 MB
1Gi = 1 GB
```

### requests vs limits 的最佳实践

```text
1. requests 设合理值（保证调度）
2. limits 设上限（防止资源失控）
3. 生产环境 requests = limits（保证稳定性）
4. 资源紧张时 limits 可大于 requests（允许突发）
```

### 资源不足的表现

```text
1. requests 不足 → Pod 无法调度（Pending）
2. 内存超 limits → OOMKilled（容器被杀）
3. CPU 超 limits → 被限流（变慢，不杀）
```

## 应用场景实战

### 场景 1：完整的应用配置（ConfigMap + Secret）

```yaml
# ConfigMap：应用配置
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  SPRING_PROFILES_ACTIVE: "prod"
  DB_URL: "jdbc:mysql://mysql:3306/mydb"

---
# Secret：数据库密码
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  password: "123456"

---
# Deployment：使用 ConfigMap 和 Secret
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:1.0
        envFrom:
        - configMapRef:
            name: app-config        # 注入 ConfigMap
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password         # 注入 Secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
```

### 场景 2：多环境隔离（Namespace）

```bash
# 创建环境命名空间
kubectl create namespace dev
kubectl create namespace prod

# 部署到不同环境
kubectl apply -f app.yaml -n dev
kubectl apply -f app.yaml -n prod

# 查看各环境资源
kubectl get pods -n dev
kubectl get pods -n prod
```

## 最佳实践与踩坑记录

### 最佳实践

1. **配置用 ConfigMap，敏感信息用 Secret**。不要混用，敏感信息不放进 ConfigMap。

2. **requests 和 limits 都要设置**。requests 保证调度，limits 防止失控。

3. **环境用 Namespace 隔离**。dev/test/prod 独立命名空间。

4. **Secret 用 stringData（明文写，自动编码）**。避免手动 base64 出错。

5. **配置文件挂载用 subPath**。避免挂载整个目录覆盖原有文件。

### 踩坑记录

**坑 1：Secret 的 base64 误以为是加密**

```text
Secret 的 base64 只是编码，base64 解码就能看到明文
```

Secret 不是加密，敏感信息用 KMS 或 Sealed Secrets。

**坑 2：requests 设置过高导致 Pod 无法调度**

```yaml
resources:
  requests:
    memory: "8Gi"    # 节点只有 4Gi，无法调度，Pending
```

requests 要匹配节点实际资源。

**坑 3：内存超 limits 被 OOMKilled**

```text
应用内存泄漏，超过 limits，容器被 OOM Kill 重启
```

limits 设合理值，监控内存使用，修复泄漏。

**坑 4：ConfigMap 更新后 Pod 不生效**

```text
修改了 ConfigMap，但 Pod 还是用旧配置
```

ConfigMap 作为环境变量注入，需要重启 Pod 才生效（挂载方式的会热更新）。

**坑 5：挂载 ConfigMap 覆盖目录**

```yaml
volumeMounts:
- name: config
  mountPath: /app    # 挂载整个 /app，覆盖原文件
```

挂载配置用 subPath 挂载具体文件，避免覆盖整个目录。

**坑 6：忘记指定 namespace**

```bash
kubectl get pods    # 只看 default namespace
# 应用部署在 prod namespace，看不到
```

明确指定 -n namespace，或切换默认命名空间。
