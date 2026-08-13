---
title: Kubernetes 网络
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [kubernetes, service, clusterip, nodeport, loadbalancer, ingress, dns]
---

# Kubernetes 网络

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [Service 服务抽象](#service-服务抽象)
- [ClusterIP 集群内部访问](#clusterip-集群内部访问)
- [NodePort 节点端口](#nodeport-节点端口)
- [LoadBalancer 负载均衡器](#loadbalancer-负载均衡器)
- [Ingress 七层路由](#ingress-七层路由)
- [DNS 服务发现](#dns-服务发现)
- [应用场景实战](#应用场景实战)

## 概述

Kubernetes 网络解决"Pod 之间如何通信、外部如何访问服务"的问题。

```text
K8s 网络的核心问题：
1. Pod 间通信 —— Pod 有自己的 IP，跨节点通信
2. 服务发现 —— Pod IP 不稳定，如何稳定访问
3. 外部访问 —— 外部如何访问集群内的服务
```

```text
核心概念：
Service —— 服务的稳定入口（Pod 的负载均衡）
Ingress —— 七层路由（HTTP/HTTPS 路由）
DNS —— 服务名解析
```

## Service 服务抽象

Service 是 Pod 的稳定访问入口，解决 Pod IP 不稳定的问题。

### 为什么需要 Service

```text
Pod 是短暂的，重建后 IP 会变：
- Deployment 的 Pod IP：10.0.0.1 → 重建后 10.0.0.5
- 其他服务无法用固定 IP 访问

Service 提供稳定入口：
- Service 有稳定的 IP（ClusterIP）和 DNS 名
- Service 负载均衡到后端 Pod
```

```text
Service → 稳定入口（ClusterIP + DNS 名）
    │ 负载均衡
    ├── Pod 1（10.0.0.1）
    ├── Pod 2（10.0.0.2）
    └── Pod 3（10.0.0.3）
```

### Service 的四种类型

| 类型 | 访问范围 | 说明 |
|------|---------|------|
| ClusterIP | 集群内部 | 默认，集群内访问 |
| NodePort | 节点 IP:端口 | 通过节点端口访问 |
| LoadBalancer | 外部 LB | 云厂商负载均衡器 |
| ExternalName | 外部域名 | 映射到外部服务 |

## ClusterIP 集群内部访问

ClusterIP 是默认类型，为服务分配集群内部 IP，只能在集群内访问。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  type: ClusterIP          # 默认
  selector:
    app: order-service     # 选择后端 Pod
  ports:
  - port: 8080             # Service 端口
    targetPort: 8080       # Pod 端口
```

```bash
kubectl get svc            # 查看 Service
# order-service  ClusterIP  10.96.0.10  8080/TCP
```

```text
集群内访问方式：
1. ClusterIP：http://10.96.0.10:8080
2. 服务名：http://order-service:8080（DNS 解析）
3. 完整域名：http://order-service.default.svc.cluster.local
```

## NodePort 节点端口

NodePort 在每个节点开放一个端口，通过节点 IP + 端口访问。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  type: NodePort           # NodePort 类型
  selector:
    app: order-service
  ports:
  - port: 8080             # Service 端口
    targetPort: 8080       # Pod 端口
    nodePort: 30080        # 节点端口（30000-32767）
```

```text
访问方式：
任意节点的 IP:30080 → Service → 后端 Pod

NodePort 的局限：
1. 端口范围受限（30000-32767）
2. 每个服务占用一个节点端口
3. 需要额外的负载均衡（Nginx/LB）做入口
```

## LoadBalancer 负载均衡器

LoadBalancer 使用云厂商的负载均衡器，为服务提供外部访问。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  type: LoadBalancer       # 云厂商 LB
  selector:
    app: order-service
  ports:
  - port: 80
    targetPort: 8080
```

```text
LoadBalancer 的工作：
1. 创建云厂商 LB（如 AWS ELB、阿里云 SLB）
2. LB 分配外部 IP
3. 外部流量 → LB → NodePort → Service → Pod

局限：
1. 依赖云厂商
2. 每个 Service 一个 LB（成本高）
```

## Ingress 七层路由

Ingress 是七层（HTTP/HTTPS）路由，用一个入口路由到多个服务。

### 为什么需要 Ingress

```text
NodePort/LoadBalancer 的问题：
每个服务都需要端口或 LB，管理复杂、成本高

Ingress 的解决：
一个 Ingress 入口，按路径/域名路由到多个服务
```

```text
Ingress 路由规则：
http://example.com/api/order → order-service
http://example.com/api/user  → user-service
```

### Ingress 定义

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gateway-ingress
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /order
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 8080
      - path: /user
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8080
```

### Ingress Controller

```text
Ingress 需要 Ingress Controller 实现：
1. Nginx Ingress Controller（最常用）
2. Traefik
3. Istio Gateway

流程：Ingress 规则 → Ingress Controller（Nginx）→ 转发到 Service
```

## DNS 服务发现

K8s 内置 DNS 服务（CoreDNS），服务名自动解析。

### DNS 解析规则

```text
Pod 内访问服务的 DNS 名：
<service-name>.<namespace>.svc.cluster.local

同 namespace：<service-name>（简写）
跨 namespace：<service-name>.<namespace>
完整：<service-name>.<namespace>.svc.cluster.local
```

```text
示例：
order-service 在 default namespace
Pod 内访问：http://order-service:8080（同 namespace）
完整：http://order-service.default.svc.cluster.local:8080
```

### Headless Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  clusterIP: None          # Headless（无 ClusterIP）
  selector:
    app: mysql
  ports:
  - port: 3306
```

```text
Headless Service（clusterIP: None）：
不分配 ClusterIP，直接解析到 Pod IP
用于 StatefulSet（每个 Pod 有稳定的 DNS 名）
如：mysql-0.mysql.default.svc.cluster.local
```

## 应用场景实战

### 场景 1：微服务集群内部通信

```yaml
# 每个服务一个 Service（ClusterIP），服务间用服务名通信
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  type: ClusterIP
  selector:
    app: user-service
  ports:
  - port: 8080
    targetPort: 8080
```

```yaml
# order-service 内访问 user-service
# 用服务名：http://user-service:8080
# Spring Cloud 也可用 K8s 服务发现（spring-cloud-kubernetes）
```

### 场景 2：外部访问（Ingress）

```yaml
# 一个 Ingress 路由多个服务
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api/order
        pathType: Prefix
        backend:
          service:
            name: order-service
            port: { number: 8080 }
      - path: /api/user
        pathType: Prefix
        backend:
          service:
            name: user-service
            port: { number: 8080 }
```

### 场景 3：访问数据库（Headless + StatefulSet）

```yaml
# MySQL StatefulSet + Headless Service
# 应用访问 mysql-0.mysql.default.svc.cluster.local:3306
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  clusterIP: None
  selector:
    app: mysql
  ports:
  - port: 3306
```

## 最佳实践与踩坑记录

### 最佳实践

1. **集群内通信用 ClusterIP + 服务名**。不要用 Pod IP（不稳定）。

2. **外部访问用 Ingress**。一个入口路由多个服务，避免每个服务一个 LB。

3. **Service 的 port 和 targetPort 区分**。port 是 Service 端口，targetPort 是 Pod 端口。

4. **selector 要匹配 Pod 的 labels**。selector 不匹配，Service 找不到后端 Pod。

5. **有状态应用用 Headless Service**。稳定 DNS 名（mysql-0、mysql-1）。

### 踩坑记录

**坑 1：Service 的 selector 不匹配**

```yaml
spec:
  selector:
    app: myapp         # Service 找 app=myapp 的 Pod
# 但 Pod 的 labels 是 name=myapp，selector 不匹配
# Service 没有后端，访问失败
```

selector 必须精确匹配 Pod 的 labels。

**坑 2：NodePort 端口冲突**

```yaml
nodePort: 30080    # 两个 Service 用同一个 nodePort，冲突
```

NodePort 范围 30000-32767，避免冲突（不指定会自动分配）。

**坑 3：访问 Service 用 Pod IP**

```text
用 Pod IP 访问服务，Pod 重建后 IP 变了，访问失败
```

用 Service 名或 ClusterIP 访问，不要用 Pod IP。

**坑 4：Ingress 没有 Ingress Controller**

```text
创建了 Ingress 规则，但没有部署 Ingress Controller（Nginx）
Ingress 不生效
```

Ingress 需要 Ingress Controller 配合，先部署 Nginx Ingress Controller。

**坑 5：跨 namespace 访问用短名**

```text
在 namespace-a 访问 namespace-b 的 user-service
用短名 user-service 解析失败（不在同一 namespace）
```

跨 namespace 用完整名：user-service.namespace-b。

**坑 6：Headless Service 的 ClusterIP 是 None**

```text
Headless Service（clusterIP: None）没有 ClusterIP
用 ClusterIP 访问会失败
```

Headless Service 用 DNS 名访问（mysql-0.mysql...），不是 ClusterIP。
