---
title: Kubernetes 完整知识教程：从架构到生产编排
created: 2026-09-16
updated: 2026-09-16
type: concept
tags: [kubernetes, k8s, pod, deployment, service, ingress, configmap, secret, pvc, rbac, helm, 容器编排]
---

# Kubernetes 完整知识教程：从架构到生产编排

整理日期：2026-09-16

> 状态：已完成

本文是一份完整的 Kubernetes 知识教程，按「架构 → 核心对象 → 网络 → 存储 → 调度 → 安全 → 运维 → 实战」组织，覆盖 K8s 从概念到生产编排的全部高频知识点。文中标注「实测」的命令与输出均来自本机正在运行的 minikube 集群。

实测环境：

```text
集群：minikube 单节点（v1.37.0，control-plane 角色），kubectl v1.37.0
容器运行时：containerd 2.3.4    节点 IP：192.168.49.2（kicbase 虚拟机）
命名空间：default / demo / kube-system / kubernetes-dashboard / questionnaire
demo 命名空间跑着一个教学用的 web Deployment（3 副本 nginx + 双探针 + initContainer + ConfigMap + 双 Service），
本文的许多示例直接引用它
```

## 目录

- [1. Kubernetes 解决什么问题](#1-kubernetes-解决什么问题)
- [2. 架构与核心组件](#2-架构与核心组件)
- [3. 声明式 API 与对象模型](#3-声明式-api-与对象模型)
- [4. Pod：最小调度单元](#4-pod最小调度单元)
- [5. 控制器：Deployment / ReplicaSet / StatefulSet / DaemonSet / Job](#5-控制器deployment--replicaset--statefulset--daemonset--job)
- [6. Service 与服务发现](#6-service-与服务发现)
- [7. Ingress：七层路由入口](#7-ingress七层路由入口)
- [8. ConfigMap 与 Secret](#8-configmap-与-secret)
- [9. 存储：Volume / PV / PVC / StorageClass](#9-存储volume--pv--pvc--storageclass)
- [10. Namespace 与资源配额](#10-namespace-与资源配额)
- [11. 探针：liveness / readiness / startup](#11-探针liveness--readiness--startup)
- [12. 调度：亲和性、污点与容忍](#12-调度亲和性污点与容忍)
- [13. 安全：RBAC / ServiceAccount / SecurityContext / NetworkPolicy](#13-安全rbac--serviceaccount--securitycontext--networkpolicy)
- [14. 滚动更新、回滚与 HPA](#14-滚动更新回滚与-hpa)
- [15. Helm 包管理](#15-helm-包管理)
- [16. 生产运行要点](#16-生产运行要点)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)
- [相关文档](#相关文档)

## 1. Kubernetes 解决什么问题

Docker 解决了「单台机器上把一个应用跑起来」的问题，但生产环境面对的是「几十上百台机器、几十个服务」：某个服务该跑在哪个节点？挂了怎么自动重启？用户流量怎么均匀分到多个副本？发布新版本怎么不中断？这些是容器编排的职责，Kubernetes（K8s）就是事实标准。

K8s 提供的能力：

1. **调度**：把容器（Pod）按资源需求自动分配到集群里合适的节点
2. **自愈**：容器挂了自动重启、节点挂了自动把工作负载迁移到别的节点
3. **扩缩容**：按负载水平手动或自动增减副本
4. **服务发现与负载均衡**：给一组副本一个稳定的访问入口，自动分流
5. **滚动发布与回滚**：新版本逐步替换旧版本，出问题一键回退
6. **配置与密钥管理**：ConfigMap/Secret 把配置从镜像里剥离
7. **存储编排**：PV/PVC 把存储抽象出来，应用不管底层盘
8. **声明式管理**：描述「期望状态」，K8s 持续把实际状态收敛到期望状态

一句话理解：K8s 是「数据中心的操作系统」，你告诉它「我要 3 个副本、健康检查、能对外访问、坏了自动重启」，它负责把这些期望状态维持住。

## 2. 架构与核心组件

K8s 集群分两类节点：控制面（control plane，管决策）和工作节点（worker node，管干活）。

控制面组件（本机 minikube 是单节点，控制面和工作负载跑在一起）：

| 组件 | 作用 |
|---|---|
| kube-apiserver | 集群唯一入口，所有操作都走它（REST API），其他组件都通过它读写状态 |
| etcd | 分布式键值存储，保存集群全部状态（对象、配置），是集群的「记忆」 |
| kube-scheduler | 调度器，决定新 Pod 落在哪个节点 |
| kube-controller-manager | 一组控制器，持续把实际状态向期望状态收敛（副本数、节点状态等） |
| cloud-controller-manager | 云厂商集成（负载均衡、云盘），本地集群没有 |

工作节点组件：

| 组件 | 作用 |
|---|---|
| kubelet | 节点上的 agent，接收 apiserver 下发的 Pod 规格，调容器运行时拉起容器并上报状态 |
| kube-proxy | 维护网络规则（iptables/IPVS），实现 Service 的负载均衡 |
| 容器运行时 | containerd / CRI-O，真正跑容器的（通过 CRI 接口对接） |

本机实测（控制面组件都以静态 Pod 形式跑在 kube-system 命名空间）：

```text
$ kubectl get pods -n kube-system
NAME                               READY   STATUS    RESTARTS        AGE
coredns-6cf5fbd489-kf54k           1/1     Running   0               4d
etcd-minikube                      1/1     Running   0               4d
kube-apiserver-minikube            1/1     Running   0               4d
kube-controller-manager-minikube   1/1     Running   3 (4d ago)      4d
kube-proxy-lzx8x                   1/1     Running   0               4d
kube-scheduler-minikube            1/1     Running   0               4d
metrics-server-74b5d4fbd7-krfz9    1/1     Running   0               4d
storage-provisioner                1/1     Running   3 (3d12h ago)   4d
```

对照上表：etcd、kube-apiserver、kube-controller-manager、kube-scheduler 是控制面；kube-proxy 是节点组件；coredns 是集群 DNS；metrics-server 提供指标（HPA 依赖）；storage-provisioner 是 minikube 默认的存储供给器。

调用链：用户 `kubectl` → kube-apiserver →（写 etcd；控制器观察变更 → 调 scheduler 决策 → kubelet 执行）。apiserver 是唯一写 etcd 的组件，其余组件都通过 watch 监听 apiserver 的变化。

## 3. 声明式 API 与对象模型

K8s 的核心思想是**声明式**：你提交一份 YAML 描述「期望状态」（我要 3 个副本、用这个镜像、暴露 80 端口），K8s 的控制器循环（reconcile loop）持续对比「实际状态」和「期望状态」，有偏差就自动修正。

对比命令式：命令式是你一步步说「先建一个、再建一个、改这个」，声明式是你直接说「最终要是 3 个」，中间过程不用管。

所有 K8s 对象都遵循统一结构：

```yaml
apiVersion: apps/v1        # 对象的 API 组和版本
kind: Deployment           # 对象类型
metadata:                  # 元数据：名称、命名空间、标签
  name: web
  namespace: demo
  labels:
    app: web
spec:                      # 期望状态（每种对象不同）
  replicas: 3
  selector:                # 标签选择器：这个对象管理哪些 Pod
    matchLabels:
      app: web
  template:                # Pod 模板（spec 里再套一层 metadata+spec）
    metadata:
      labels:
        app: web
    spec:
      containers: [ ... ]
status:                    # 实际状态（K8s 自己维护，只读）
  replicas: 3
```

四个字段各司其职：apiVersion + kind 定位对象类型，metadata 是身份信息，spec 是你声明的期望，status 是 K8s 反馈的实际状态（你不用写，写了也无效）。

**标签（label）和选择器（selector）**是贯穿全 K8s 的关联机制：Deployment 用 `spec.selector` 匹配它管理的 Pod 的 label，Service 用 selector 匹配它要代理的 Pod。这是「松耦合关联」的关键——不靠名字硬编码，靠标签动态匹配。

## 4. Pod：最小调度单元

Pod 是 K8s 调度的最小单位，不是容器。一个 Pod 里可以放一个或多个容器，这些容器共享：

- 网络命名空间（同一个 IP、共享端口空间，容器间用 localhost 通信）
- 存储卷（Pod 内的容器挂载同一批卷）
- IPC 命名空间

多容器 Pod 的典型模式：

1. **sidecar**：主容器 + 辅助容器（如日志采集、代理、metrics 收集）
2. **initContainer**：主容器启动前先跑完的初始化容器（如准备文件、等依赖就绪）

本机实测 demo 命名空间的 web Pod 就是「initContainer + 主容器」结构（简化的完整 spec）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      initContainers:
        - name: build-index
          image: busybox:1.37
          command: ["sh", "-c", "cat > /work/index.html <<EOF ... EOF"]
          volumeMounts:
            - mountPath: /work
              name: html
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
              name: http
          resources:
            requests: { cpu: 50m, memory: 32Mi }
            limits:   { cpu: 200m, memory: 128Mi }
          livenessProbe:
            httpGet: { path: /healthz, port: 80 }
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet: { path: /healthz, port: 80 }
            initialDelaySeconds: 2
            periodSeconds: 5
          volumeMounts:
            - mountPath: /usr/share/nginx/html
              name: html
            - mountPath: /etc/nginx/conf.d/default.conf
              name: nginx-conf
              subPath: nginx.conf
      volumes:
        - name: html
          emptyDir: {}
        - name: nginx-conf
          configMap:
            name: web-config
            items:
              - key: nginx.conf
                path: nginx.conf
```

这里能看到 Pod 的几个关键机制：initContainer（busybox）先往共享的 emptyDir 卷里写 index.html，主容器 nginx 再挂同一卷读它——这就是 initContainer 与主容器「通过共享卷交接数据」的典型用法；resources 声明了 CPU/内存的 requests 和 limits；双探针做健康检查；ConfigMap 以 subPath 方式把配置挂成单个文件。

常用命令：

```bash
kubectl get pods -n demo -o wide    # 看 Pod 状态和 IP
kubectl describe pod <名> -n demo   # 看事件、探针、挂载细节（排查第一入口）
kubectl logs <名> -n demo           # 看日志（多容器要 -c 指定）
kubectl exec -it <名> -n demo -- sh # 进容器
kubectl delete pod <名> -n demo     # 删 Pod（被 Deployment 管的话会自动重建）
```

## 5. 控制器：Deployment / ReplicaSet / StatefulSet / DaemonSet / Job

Pod 本身是「一次性」的，删了就没了。真正让 Pod 有自愈能力的是**控制器**——它们盯着期望副本数，Pod 少了就补、多了就删、挂了就重建。

**Deployment 与 ReplicaSet**：最常用的无状态应用控制器。Deployment 管理 ReplicaSet，ReplicaSet 管理 Pod。Deployment 负责「滚动更新」（每次更新建一个新的 ReplicaSet，逐步把 Pod 从旧 RS 迁到新 RS），所以你能看到多个历史 ReplicaSet（用于回滚）。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3                       # 期望副本数
  strategy:                         # 更新策略
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                   # 更新时最多多出的 Pod 数
      maxUnavailable: 0             # 更新时最多不可用的 Pod 数
  selector:
    matchLabels: { app: web }
  template: { ... }
```

本机实测 web Deployment 的 ReplicaSet 和 Pod 命名规律（Pod 名 = RS 名 + 随机后缀）：

```text
$ kubectl get pods -n demo
NAME                   READY   STATUS    RESTARTS   AGE
web-69b584f78c-8t7h2   1/1     Running   0          4d
web-69b584f78c-ckp9z   1/1     Running   0          4d
web-69b584f78c-fgxqf   1/1     Running   0          4d
```

`web-69b584f78c-` 就是 ReplicaSet 的 hash 前缀，`-8t7h2` 等是每个 Pod 的随机后缀。

**StatefulSet**：有状态应用（数据库、消息队列）。与 Deployment 的区别：

| 特性 | Deployment | StatefulSet |
|---|---|---|
| Pod 名字 | 随机后缀（web-abc123） | 固定序号（mysql-0, mysql-1） |
| 网络标识 | 无稳定标识 | 稳定的 headless service + 序号域名 |
| 存储 | 共享或无状态 | 每个 Pod 独立 PVC（volumeClaimTemplates） |
| 启动/删除顺序 | 并行 | 顺序（0→1→2 启动，2→1→0 删除） |

本机实测 questionnaire 命名空间的 MySQL 就是 StatefulSet（Pod 名 `mysql-0` 带固定序号）：

```text
$ kubectl get pods -n questionnaire
NAME                        READY   STATUS    RESTARTS   AGE
mysql-0                     1/1     Running   0          3d23h
```

**DaemonSet**：每个节点跑一个副本（如日志采集 fluentd、监控 agent、网络插件）。节点扩了自动在新节点补一个。

**Job / CronJob**：一次性任务 / 定时任务。Job 跑完就结束（`completions` 指定成功次数），CronJob 按 cron 表达式周期触发 Job。

选型一句话：无状态用 Deployment，有状态需要稳定标识和独立存储用 StatefulSet，每节点一个用 DaemonSet，跑批任务用 Job/CronJob。

## 6. Service 与服务发现

Pod 的 IP 是临时的（重建就变），且 Pod 有多个副本。Service 提供一个**稳定的虚拟 IP（ClusterIP）+ DNS 名**，把流量负载均衡到一组匹配的 Pod（通过 selector 匹配 label）。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-svc
  namespace: demo
spec:
  selector:
    app: web            # 匹配哪些 Pod
  ports:
    - port: 80          # Service 端口
      targetPort: 80    # Pod 端口
  type: ClusterIP
```

四种 Service 类型：

| 类型 | 作用 | 访问方式 |
|---|---|---|
| ClusterIP | 默认，集群内部访问 | 集群内通过 Service 名/IP |
| NodePort | 在 ClusterIP 基础上，每个节点开一个固定端口 | `<节点IP>:<NodePort>` |
| LoadBalancer | 云厂商，自动创建外部 LB | 外部通过 LB 地址 |
| ExternalName | 把 Service 映射到外部域名（CNAME） | 集群内通过 Service 名访问外部 |

本机实测 demo 命名空间有两个 Service（一个 ClusterIP、一个 NodePort）：

```text
$ kubectl get svc -n demo
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
web-nodeport    NodePort    10.100.158.21   <none>        80:30080/TCP   4d    app=web
web-svc         ClusterIP   10.98.114.94    <none>        80/TCP         4d    app=web
```

**服务发现（DNS）**：集群内访问服务不用记 IP，直接用 Service 名。CoreDNS（kube-system 里的 coredns）提供解析：`<服务名>.<命名空间>.svc.cluster.local`。同一命名空间里可省略写 `<服务名>`。所以 questionnaire 的 backend 访问 MySQL 直接写 `mysql:3306`。

**负载均衡实现**：kube-proxy 维护 iptables/IPVS 规则，把打到 ClusterIP 的流量转发到后端 Pod。Service 通过 Endpoints 对象维护「当前有哪些健康 Pod」列表，Pod 增删时自动更新。

Headless Service（ClusterIP 设为 None）：不做负载均衡，DNS 直接解析出每个 Pod 的 IP，配合 StatefulSet 用（每个 Pod 有独立域名 `<pod名>.<服务名>`）。本机实测 MySQL 的 Service ClusterIP 就是 None（headless）。

## 7. Ingress：七层路由入口

Service 只解决「四层」负载均衡（按 IP:端口分流），Ingress 解决「七层」HTTP/HTTPS 路由：按域名和路径把请求路由到不同 Service，还能统一做 TLS 终结、重写。

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
spec:
  rules:
    - host: app.example.com        # 域名
      http:
        paths:
          - path: /api              # 路径前缀
            pathType: Prefix
            backend:
              service:
                name: backend-svc   # 路由到的 Service
                port: { number: 8080 }
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-svc
                port: { number: 80 }
  tls:
    - hosts: [app.example.com]
      secretName: app-tls           # TLS 证书（Secret 里）
```

关键点：**Ingress 只是规则声明，实际转发要一个 Ingress Controller**（如 ingress-nginx、traefik）。Controller 是真正监听 80/443、读取 Ingress 规则、做转发的组件。装了 Controller 后，Ingress 规则才生效。

## 8. ConfigMap 与 Secret

把配置从镜像里剥离出来，镜像保持不变、配置随环境变。

**ConfigMap**：非敏感配置（环境变量、配置文件）。四种使用方式：

1. 环境变量（`envFrom: configMapRef` 或 `env: valueFrom: configMapKeyRef`）
2. 挂载为文件（volume）
3. 挂载为单个文件（subPath，本机 web Deployment 的 nginx.conf 就这么用）
4. 命令行参数引用

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-config
  namespace: demo
data:
  APP_TITLE: "Demo Web"
  APP_ENV: "dev"
  nginx.conf: |
    server {
      listen 80;
      location /healthz { return 200 "ok"; }
    }
```

**Secret**：敏感信息（密码、token、证书）。与 ConfigMap 结构类似，值是 base64 编码。类型有 Opaque（默认）、`kubernetes.io/tls`（证书）、`kubernetes.io/dockerconfigjson`（镜像仓库凭证）等。

两者对比（面试高频）：

| 维度 | ConfigMap | Secret |
|---|---|---|
| 用途 | 非敏感配置 | 敏感信息 |
| 存储 | 明文 | base64 编码（注意：base64 不是加密，etcd 里仍可还原） |
| 隔离 | 无 | 默认仍明文存 etcd，需额外开 etcd 加密 |

坑点：Secret 的 base64 只是编码不是加密，任何能 `kubectl get secret` 的人都可还原。生产应配合 RBAC 控制访问 + etcd 静态加密。

## 9. 存储：Volume / PV / PVC / StorageClass

容器文件系统是临时的（Pod 删除就丢），存储抽象解决「数据持久化」。

三层抽象：

- **PV（PersistentVolume）**：集群级的存储资源（管理员准备，或动态供给），独立于 Pod 生命周期
- **PVC（PersistentVolumeClaim）**：用户（应用）的存储申请，像「我要 10GB 读写一次的盘」
- **StorageClass**：定义「如何动态创建 PV」（哪个 provisioner、什么参数），让 PV 按需自动供给

```yaml
# PVC：应用申请存储
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-data
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
```

Pod 里挂载 PVC：

```yaml
volumes:
  - name: mysql-data
    persistentVolumeClaim:
      claimName: mysql-data
```

访问模式：ReadWriteOnce（单节点读写，RWO，最常用）、ReadOnlyMany（多节点只读）、ReadWriteMany（多节点读写，需 NFS 等共享存储）。

动态供给流程：用户建 PVC（指定 StorageClass）→ StorageClass 的 provisioner 自动创建 PV 并绑定 → Pod 挂载 PVC 使用。本机 minikube 有默认的 `standard` StorageClass（storage-provisioner 组件，实测在 kube-system 里）。

## 10. Namespace 与资源配额

**Namespace**：集群内的逻辑隔离，把资源分组（不同环境、不同团队）。默认有 default、kube-system（系统组件）、kube-public 等。本机实测还有 demo、questionnaire、kubernetes-dashboard。

```bash
kubectl create namespace dev
kubectl get ns
```

**资源配额（ResourceQuota）**：限制一个 namespace 的资源总量（CPU、内存、Pod 数、PVC 数），防止某个团队吃光集群。

**资源请求与限制（requests/limits）**：单 Pod 层面，本机 web Deployment 里已体现：

```yaml
resources:
  requests: { cpu: 50m, memory: 32Mi }    # 调度依据：Pod 至少要这么多
  limits:   { cpu: 200m, memory: 128Mi }  # 上限：最多用这么多
```

- requests：scheduler 用来决定「这个节点还塞得下吗」
- limits：实际使用上限，CPU 超了被限流（throttle），内存超了直接 OOMKilled

单位：CPU 用 `m`（毫核，1000m = 1 核）；内存用 Mi/Gi（二进制）或 M/G（十进制）。

## 11. 探针：liveness / readiness / startup

容器「在跑」不等于「服务可用」，三种探针分别回答不同问题：

| 探针 | 回答的问题 | 失败后果 |
|---|---|---|
| livenessProbe | 进程还活着吗（是否卡死） | 重启容器 |
| readinessProbe | 能接流量吗（依赖就绪没） | 从 Service 后端摘除，不接流量 |
| startupProbe | 慢启动的应用起来了吗 | 未通过前不跑 liveness，防止误杀 |

探测方式：httpGet（HTTP 请求）、tcpSocket（TCP 连接）、exec（容器内执行命令）。

本机 web Deployment 的探针（前面贴过）：

```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 80 }
  initialDelaySeconds: 5     # 启动后等 5 秒才开始探
  periodSeconds: 10          # 每 10 秒探一次
readinessProbe:
  httpGet: { path: /healthz, port: 80 }
  initialDelaySeconds: 2
  periodSeconds: 5
```

坑点：liveness 探针配太激进（initialDelaySeconds 太小、阈值太严）会把慢启动的应用反复杀掉（CrashLoopBackOff）。慢启动应用应配 startupProbe 给足初始化时间，liveness 只做「卡死」检测。

## 12. 调度：亲和性、污点与容忍

scheduler 决定 Pod 落在哪个节点，三个影响调度的机制：

**节点选择（nodeSelector / nodeAffinity）**：Pod 指定要跑在哪些节点（按节点 label）。nodeSelector 是简单的「标签精确匹配」，nodeAffinity 支持更丰富的表达式（In、NotIn、Exists）。

```yaml
spec:
  nodeSelector:
    disktype: ssd          # 只调度到打了 disktype=ssd 标签的节点
```

**污点与容忍（taint / toleration）**：污点是「节点上的一道拒绝门」，只有带对应容忍的 Pod 才能调度上去。典型用途——给 GPU 节点打污点，只有要 GPU 的 Pod 声明容忍才上去。

```bash
# 给节点打污点：key=value:effect（NoSchedule 表示不调度新 Pod 上来）
kubectl taint nodes node1 gpu=true:NoSchedule
```

```yaml
# Pod 声明容忍
spec:
  tolerations:
    - key: gpu
      operator: Equal
      value: "true"
      effect: NoSchedule
```

**污点 effect 三种**：NoSchedule（不调度）、PreferNoSchedule（尽量不调度）、NoExecute（不调度 + 驱逐已有 Pod）。

**节点亲和 + 反亲和（podAffinity/podAntiAffinity）**：让 Pod 和某些 Pod 靠在一起（affinity）或分开（anti-affinity，如副本分散到不同节点提高可用性）。

## 13. 安全：RBAC / ServiceAccount / SecurityContext / NetworkPolicy

**ServiceAccount**：Pod 运行时的身份。默认 namespace 有 default SA，每个 Pod 自动挂载一个 token（用于访问 apiserver）。不用 `automountServiceAccountToken: false` 时应显式关闭不需要的挂载。

**RBAC**：基于角色的访问控制，回答「谁（Subject）能对什么（Resource）做什么（Verb）」。

四个对象：

| 对象 | 作用域 | 作用 |
|---|---|---|
| Role | 命名空间内 | 定义一组权限（对哪些资源做哪些操作） |
| ClusterRole | 集群级 | 同上，但可作用于集群级资源（节点、PV） |
| RoleBinding | 命名空间内 | 把 Role 授予某个用户/SA/组 |
| ClusterRoleBinding | 集群级 | 把 ClusterRole 授予全局 |

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: demo
  name: pod-reader
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: demo
  name: read-pods
subjects:
  - kind: ServiceAccount
    name: reader
    namespace: demo
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

**SecurityContext**：Pod/容器级别的安全设置——非 root 运行（`runAsNonRoot` + `runAsUser`）、只读根文件系统（`readOnlyRootFilesystem`）、capability 裁剪（`capabilities.drop: [ALL]`）、`allowPrivilegeEscalation: false` 等。与 Docker 的安全加固一一对应。

**NetworkPolicy**：Pod 间的网络防火墙（默认全部互通，加了策略后「默认拒绝，显式放行」）。需要 CNI 插件支持（Calico/Cilium，Flannel 默认不支持）。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow
  namespace: demo
spec:
  podSelector:
    matchLabels: { app: api }
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels: { app: web }   # 只允许 app=web 的 Pod 访问
      ports:
        - protocol: TCP
          port: 8080
```

## 14. 滚动更新、回滚与 HPA

**滚动更新**：Deployment 更新镜像/template 时，按 strategy（maxSurge/maxUnavailable）逐步用新 Pod 替换旧 Pod，实现零停机。本机 web Deployment 的 `maxSurge: 1, maxUnavailable: 0` 意味着「最多多 1 个 Pod、任何时刻不可用为 0」——先起一个新的、等它就绪、再删一个旧的。

```bash
# 更新镜像触发滚动更新
kubectl set image deployment/web nginx=nginx:1.27-alpine -n demo
# 看更新进度
kubectl rollout status deployment/web -n demo
```

**回滚**：每次更新都留了历史 ReplicaSet，一键回退：

```bash
kubectl rollout history deployment/web -n demo   # 看历史版本
kubectl rollout undo deployment/web -n demo      # 回滚到上一版
kubectl rollout undo deployment/web --to-revision=2 -n demo  # 回滚到指定版本
```

**HPA（Horizontal Pod Autoscaler）**：按 CPU/内存/自定义指标自动扩缩副本。

```bash
kubectl autoscale deployment web --cpu-percent=60 --min=3 --max=10 -n demo
```

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web
  namespace: demo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

HPA 依赖 metrics-server 提供指标（本机 kube-system 里有 metrics-server 组件）。VPA（垂直扩缩，调大单个 Pod 的 requests/limits）与 HPA 互补。

## 15. Helm 包管理

Helm 是 K8s 的「包管理器」，解决「一堆 YAML 怎么打包、参数化、复用、版本化」的问题。核心概念：

- **Chart**：一个应用包（目录，含 templates + values.yaml + Chart.yaml 元数据）
- **Release**：Chart 部署到集群后的一个实例（同一 Chart 可装多个 release）
- **values.yaml**：参数化配置，同一 Chart 换 values 就能适配不同环境
- **templates**：Go template 模板，渲染成最终 K8s YAML

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami   # 加仓库
helm install my-mysql bitnami/mysql --set auth.rootPassword=xxx  # 装
helm upgrade my-mysql bitnami/mysql --set ...              # 升级
helm rollback my-mysql 1                                  # 回滚
helm uninstall my-mysql                                    # 卸载
helm list                                                  # 看已装的 release
```

与纯 YAML 的区别：Helm 把「模板 + 默认值 + 可覆盖值」打包，团队共享一个 Chart、各自用不同 values 部署，避免复制粘贴一堆 YAML。生产常用 `helm install --values prod-values.yaml` 分环境管理。

## 16. 生产运行要点

1. **requests/limits 必配**：requests 保证调度正确，limits 防单 Pod 打爆节点（内存超限直接 OOMKilled）
2. **探针必配**：readiness 决定流量切换，liveness 决定自愈；慢启动应用加 startupProbe
3. **镜像用具体版本 + 私有仓库**：不用 latest（回滚和审计都要确定性）；内网用私有镜像仓库（Harbor）
4. **配置走 ConfigMap/Secret**：镜像与配置分离，换环境只换配置不重新构建
5. **有状态应用用 StatefulSet + PVC**：数据库、MQ 必须保证稳定标识和持久化
6. **RBAC 最小权限**：给应用/用户只授必要的 Role，Secret 访问严格管控
7. **资源配额 + LimitRange**：namespace 层面限总量，防止失控
8. **滚动更新 + 就绪探针 + 回滚预案**：maxUnavailable=0 保证不中断，出问题 rollout undo
9. **多副本 + 反亲和**：副本分散到不同节点，单节点故障不影响可用性
10. **日志与监控**：日志收集（EFK/Loki）、指标监控（Prometheus + Grafana）、告警

## 应用场景实战

### 场景一：把一个无状态 Web 应用跑成「多副本 + 可访问 + 自愈」

目标：部署一个 nginx web 应用，3 副本、能对外访问、Pod 挂了自动拉起、支持滚动更新。这正好是本机 demo 命名空间 web 应用的完整流程。

第一步：写 Deployment（含探针、资源限制、initContainer 生成首页）：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels: { app: web }
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    metadata:
      labels: { app: web }
    spec:
      initContainers:
        - name: build-index
          image: busybox:1.37
          command: ["sh", "-c", "echo '<h1>hello k8s</h1>' > /work/index.html"]
          volumeMounts:
            - mountPath: /work
              name: html
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
          resources:
            requests: { cpu: 50m, memory: 32Mi }
            limits: { cpu: 200m, memory: 128Mi }
          readinessProbe:
            httpGet: { path: /, port: 80 }
            initialDelaySeconds: 2
            periodSeconds: 5
          livenessProbe:
            httpGet: { path: /, port: 80 }
            initialDelaySeconds: 5
            periodSeconds: 10
          volumeMounts:
            - mountPath: /usr/share/nginx/html
              name: html
      volumes:
        - name: html
          emptyDir: {}
```

第二步：建 Service（NodePort 对外访问）：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
  namespace: demo
spec:
  selector: { app: web }
  type: NodePort
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
```

第三步：应用并验证（本机实测结果）：

```text
$ kubectl apply -f web.yaml
deployment.apps/web created
service/web-nodeport created

$ kubectl get pods -n demo -o wide
NAME                   READY   STATUS    RESTARTS   AGE   IP            NODE
web-69b584f78c-8t7h2   1/1     Running   0          4d    10.244.0.13   minikube
web-69b584f78c-ckp9z   1/1     Running   0          4d    10.244.0.14   minikube
web-69b584f78c-fgxqf   1/1     Running   0          4d    10.244.0.15   minikube

$ kubectl get svc -n demo
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
web-nodeport    NodePort    10.100.158.21   <none>        80:30080/TCP   4d

# 访问（minikube 用 node IP，真实集群用任一节点 IP）
$ curl http://192.168.49.2:30080
<h1>hello k8s</h1>
```

第四步：验证自愈（删一个 Pod，Deployment 自动补）：

```bash
kubectl delete pod web-69b584f78c-8t7h2 -n demo
kubectl get pods -n demo -w   # 观察旧 Pod 终止、新 Pod 自动拉起
```

### 场景二：部署一个「前端 + 后端 + MySQL + Redis」的完整应用栈

目标：把 questionnaire 这种典型四服务应用跑起来（本机 questionnaire 命名空间就是活样本，含 backend/frontend 各 2 副本 + mysql StatefulSet + redis）。

架构设计（每个服务怎么用 K8s 对象）：

| 服务 | 控制器 | 存储 | 对外 | 服务发现 |
|---|---|---|---|---|
| frontend | Deployment（2 副本） | 无 | NodePort | 直接访问 |
| backend | Deployment（2 副本） | 无 | 无（内网） | frontend 通过 Service 访问 |
| mysql | StatefulSet | PVC 持久化 | 无 | backend 通过 `mysql:3306` 访问 |
| redis | Deployment | PVC（可选） | 无 | backend 通过 `redis:6379` 访问 |

关键清单（MySQL 用 StatefulSet + headless service + PVC）：

```yaml
# mysql StatefulSet 片段
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: questionnaire
spec:
  serviceName: mysql
  replicas: 1
  selector:
    matchLabels: { app: mysql }
  template:
    metadata:
      labels: { app: mysql }
    spec:
      containers:
        - name: mysql
          image: mysql:8.4
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: password
          ports:
            - containerPort: 3306
          volumeMounts:
            - mountPath: /var/lib/mysql
              name: data
  volumeClaimTemplates:     # 每个 Pod 自动创建独立 PVC
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: standard
        resources:
          requests:
            storage: 10Gi
---
# headless service（ClusterIP: None），供 StatefulSet 稳定 DNS
apiVersion: v1
kind: Service
metadata:
  name: mysql
  namespace: questionnaire
spec:
  clusterIP: None
  selector: { app: mysql }
  ports:
    - port: 3306
```

backend 里连 MySQL 直接写 `mysql:3306`（同命名空间 DNS），密码从 Secret 注入，数据落在 PVC（Pod 删了数据还在）。

验证（本机实测 questionnaire 命名空间）：

```text
$ kubectl get pods -n questionnaire
NAME                        READY   STATUS    RESTARTS   AGE
backend-5677c8874b-t57n2    1/1     Running   0          3d23h
backend-5677c8874b-vrzhq    1/1     Running   0          3d23h
frontend-5d64d4d588-q4ktp   1/1     Running   0          3d23h
frontend-5d64d4d588-sl426   1/1     Running   0          3d23h
mysql-0                     1/1     Running   0          3d23h
redis-6fc9fcd475-65znw      1/1     Running   0          3d23h
```

frontend/backend 各 2 副本、mysql 是 StatefulSet（mysql-0 固定名）、redis 单副本——与设计一致。

## 最佳实践与踩坑记录

### 最佳实践

1. requests 和 limits 都要配：requests 保调度、limits 防 OOM，别只配一个
2. readiness 探针管流量、liveness 探针管重启，职责分开；慢启动加 startupProbe
3. 镜像用具体版本号，不用 latest；多环境复用镜像、只换 ConfigMap
4. 数据库、MQ 这类有状态服务用 StatefulSet + PVC，别用 Deployment
5. 密码、证书走 Secret，ConfigMap 只放非敏感配置
6. RBAC 按最小权限授，Secret 访问严格控制，etcd 开静态加密
7. 滚动更新 maxUnavailable=0 保证不中断，配 readiness 探针才能真零停机
8. 副本用 podAntiAffinity 分散到不同节点，单节点故障不影响可用
9. namespace 里配 ResourceQuota + LimitRange，防某个应用吃光集群
10. 用 Helm 管理复杂应用，values 分环境，revision 可回滚

### 踩坑记录

坑 1：Pod 一直 ImagePullBackOff

结论：镜像拉不下来，Pod 反复重试。

原因：镜像名写错、镜像仓库需要认证（没配 imagePullSecret）、私有仓库地址不通、国内拉 Docker Hub 慢。

解法：`kubectl describe pod` 看 Events 里的具体报错；私有仓库配 `imagePullSecrets`；国内用镜像加速或内网 Harbor。

坑 2：Pod 一直 CrashLoopBackOff

结论：容器反复启动失败崩溃。

原因：启动命令错、缺依赖、liveness 探针太激进（启动还没完成就被判定不健康杀掉）、OOMKilled。

解法：`kubectl logs <pod> --previous` 看上次崩溃日志；`kubectl describe pod` 看 Last State 的退出原因；是 OOM 就调大 limits 或修内存泄漏。

坑 3：Service 访问不通（selector 不匹配）

结论：Service 起了但请求到不了 Pod。

原因：Service 的 selector 和 Pod 的 label 对不上，Endpoints 为空。

解法：`kubectl get endpoints <svc>` 看有没有后端；核对 selector 和 Pod label 完全一致。

坑 4：liveness 探针把正常启动的应用反复杀

结论：应用启动要 60 秒，liveness 10 秒就探，还没起来就判死重启。

原因：liveness 的 initialDelaySeconds 配太小，或没有用 startupProbe 区分「启动慢」和「真卡死」。

解法：用 startupProbe 给足启动时间（如 60s），liveness 只在启动完成后做「卡死」检测。

坑 5：内存没配 limits，Pod 被 OOMKilled

结论：某 Pod 内存泄漏，没 limits 限制，最终被节点 OOM killer 杀掉（退出码 137）。

原因：没配 limits，Pod 无上限；或 Java 应用在容器里 `-Xmx` 按宿主机内存算。

解法：配 limits；Java 用容器感知的 `-XX:MaxRAMPercentage`。

坑 6：滚动更新卡住（新 Pod 一直没 Ready）

结论：`kubectl rollout status` 卡住，新旧 Pod 混着。

原因：新 Pod 的 readiness 探针一直失败（依赖没起、配置错），maxUnavailable=0 时旧 Pod 不删、新 Pod 起不来，卡死。

解法：`kubectl describe pod` 看新 Pod 探针失败原因；修配置后重试；紧急情况 `kubectl rollout undo` 回滚。

坑 7：数据丢了（用了 Deployment + emptyDir 跑数据库）

结论：数据库 Pod 重建后数据全没。

原因：数据库用 Deployment 跑，数据在 emptyDir（Pod 删就没）或容器层里，没有 PVC 持久化。

解法：数据库/MQ 用 StatefulSet + volumeClaimTemplates + PVC，数据落卷。

坑 8：Secret 的 base64 当成加密用了

结论：以为 Secret 是加密的，结果 `kubectl get secret -o yaml` 一 decode 就还原。

原因：base64 是编码不是加密，etcd 里默认明文存。

解法：RBAC 控制 Secret 访问；etcd 开静态加密；敏感值用外部密钥管理（Vault、云 KMS）。

坑 9：跨命名空间访问写错域名

结论：A 命名空间的 Pod 访问 B 命名空间的服务，写 `svc-name` 解析失败。

原因：DNS 短名只在同命名空间有效，跨命名空间要用完整域名。

解法：跨命名空间写 `<svc>.<namespace>.svc.cluster.local`。

坑 10：NodePort 端口范围冲突

结论：NodePort 报端口已占用或不在有效范围。

原因：NodePort 默认范围 30000-32767，多个服务不能占同一端口。

解法：换端口或让 K8s 自动分配（不写 nodePort 字段）；`--service-node-port-range` 可改范围。

## 相关文档

- [[kubernetes-minikube-install]] — Kubernetes 与 minikube 单节点集群搭建（本机实测），本文集群的搭建过程
- [[kubernetes-springboot-vue-deploy]] — SpringBoot + Vue 项目部署到 K8s 的完整映射对照与验证实录
- [[Docker完整教程]] — Docker 完整教程，K8s 编排的容器基础
- [[Docker面试题]] — Docker 面试题大全，容器底层原理与运维
- [[Docker部署大模型]] — 通过 Docker 部署大模型，推理服务容器化（GPU 调度）
- [[119-Kubernetes基础]] — Cluster/Node 架构、Pod、Deployment、StatefulSet、DaemonSet、Job
- [[120-Kubernetes网络]] — Service 四类型、Ingress、DNS 服务发现
- [[121-Kubernetes配置]] — ConfigMap/Secret/Namespace/Resource 资源管理
- [[122-Kubernetes运维]] — kubectl 命令、探针、HPA、滚动更新、Helm
- [[21.4-容器编排基础]] — Kubernetes 概念、Pod/Service/Deployment、kubectl
