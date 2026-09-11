---
title: SpringBoot + Vue 项目部署到 Kubernetes
created: 2026-09-12
updated: 2026-09-12
type: integration
tags: [kubernetes, spring-boot, vue, deployment, service, configmap, secret, statefulset, pvc, hpa, 探针, 滚动更新, docker, 容器化]
---

> 整理日期：2026-09-12

## 目录

1. [概述](#1-概述)
2. [从 docker-compose 到 K8S 的思路映射](#2-从-docker-compose-到-k8s-的思路映射)
3. [核心知识点](#3-核心知识点)
4. [部署实战](#4-部署实战)
5. [全链路验证](#5-全链路验证)
6. [应用场景实战](#6-应用场景实战)
7. [最佳实践与踩坑记录](#7-最佳实践与踩坑记录)
8. [参考链接](#8-参考链接)

---

## 1. 概述

前后端分离项目（SpringBoot 后端 + Vue 前端 + MySQL + Redis）从单机 docker-compose 迁到 Kubernetes，要解决的问题可以归成四类：

| 问题 | docker-compose 的答案 | Kubernetes 的答案 |
|---|---|---|
| 进程怎么跑、挂了怎么办 | `restart: unless-stopped` | Deployment/StatefulSet 控制器自动维持副本 |
| 服务之间怎么找对方 | compose 的服务名做 DNS | Service 名做 DNS（语义一致，配置可复用） |
| 配置与密码放哪 | compose 的 `environment:` 明文 | ConfigMap + Secret，按最小权限授权 |
| 数据怎么持久化 | 命名卷 + 宿主机目录挂载 | PVC + StorageClass 动态供给 |
| 怎么发版、怎么扩容 | 手工 `docker compose up -d --build` | 滚动更新 + 回滚 + HPA 自动扩缩 |

本文用一套真实项目（问卷调查系统：Spring Boot 3.5 + Vue 3 + MySQL 8.4 + Redis 7.4，原部署方式是 docker-compose）走完整迁移过程：写清单、部署、验证、排错，全部输出为实测。

**本篇覆盖范围**：概念映射、9 类核心对象详解、7 个清单文件的写法与理由、部署与验证实录、生产化能力（探针/HPA/滚动更新）、8 个实测坑。

**配套文档**：`[[kubernetes-minikube-install]]`（集群怎么搭）。

---

## 2. 从 docker-compose 到 K8S 的思路映射

先看原来的 compose 编排（节选）：

```yaml
name: questionnaire
services:
  mysql:
    image: mysql:8.4
    ports: ["3307:3306"]
    volumes:
      - mysql-data:/var/lib/mysql
      - ./backend/sql/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
      - ./backend/sql/data.sql:/docker-entrypoint-initdb.d/02-data.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -uroot -proot123456 --silent"]
  redis:
    image: redis:7.4-alpine
    volumes: [redis-data:/data]
  backend:
    build: ./backend
    environment:
      MYSQL_HOST: mysql
      REDIS_HOST: redis
      MYSQL_PASSWORD: root123456
    depends_on:
      mysql: {condition: service_healthy}
      redis: {condition: service_healthy}
  frontend:
    build: ./frontend
    ports: ["8088:80"]
volumes:
  mysql-data:
  redis-data:
```

迁到 K8S 的完整对照：

| docker-compose | Kubernetes | 迁移要点 |
|---|---|---|
| `services.mysql` + `volumes: mysql-data` | StatefulSet + Headless Service + `volumeClaimTemplates` | 有状态服务用 StatefulSet，PVC 由模板自动生成 |
| `services.redis` + `volumes: redis-data` | Deployment + 显式 PVC | 单实例无主从，Deployment 够用；`strategy: Recreate` 防止两实例抢卷 |
| `services.backend` | Deployment(2 副本) + Service `backend` | **Service 名与原服务名保持一致**，前端 nginx 配置零改动 |
| `services.frontend` | Deployment(2 副本) + Service `frontend`(NodePort) | 对外入口 |
| `ports: "3307:3306"` | 不需要 | 集群内通过 Service 直连 3306；调试用 `port-forward` |
| `environment: MYSQL_HOST=mysql` | ConfigMap 同键名 | 值同样是「服务名」，语义完全一致 |
| `MYSQL_PASSWORD: root123456` | Secret + `secretKeyRef` | 密码从配置里剥离 |
| `depends_on: condition: service_healthy` | initContainer 等待 + 探针 | K8S 没有 depends_on，用 initContainer 显式阻塞 |
| `restart: unless-stopped` | 控制器自动维持副本 | 更强：自愈 + 滚动 + 扩缩 |
| `build: ./backend` | `docker build` + `minikube image load` | 无私有仓库时靠导入节点 |
| `docker-entrypoint-initdb.d` 挂本地文件 | ConfigMap 挂载同名目录 | MySQL 官方镜像机制一致 |
| `docker compose up -d --build` | `kubectl apply -f k8s/` | 声明式、幂等、可反复执行 |

**一句话总结迁移方法论**：compose 的「服务名」和 K8S 的「Service 名」语义相同，**迁移时保持服务名不变，既有配置（nginx 反代地址、数据库连接串）就不用改**——这是迁移成本最低的路径。

---

## 3. 核心知识点

### 3.1 Pod 与三层控制器

```text
Deployment（管版本、管滚动更新）
   └── ReplicaSet（管副本数量，名字带 pod-template-hash）
          └── Pod × N（真正运行容器的单元）
```

- **Pod** 是最小调度单元，一个 Pod 里可以有一个或多个容器（多容器共享网络命名空间和存储卷，典型用法是 sidecar）。
- **ReplicaSet** 保证「随时有 N 个 Pod 存活」，Pod 挂了立刻补。它由 Deployment 创建，一般不用手工操作。
- **Deployment** 管理 ReplicaSet，负责版本迭代：改 Pod 模板就生成新 ReplicaSet，逐个替换旧的，这就是滚动更新。

观测三层结构：

```bash
kubectl get deploy,rs,pods -n questionnaire
```

```text
NAME                       READY   UP-TO-DATE   AVAILABLE
deployment.apps/backend    2/2     2            2

NAME                                  DESIRED   CURRENT   READY
replicaset.apps/backend-597cff6d78    0         0         0        # 旧版本，已缩容到 0
replicaset.apps/backend-ff6f7cfcb     2         2         2        # 当前版本

NAME                            READY   STATUS
pod/backend-ff6f7cfcb-c2vms     1/1     Running
pod/backend-ff6f7cfcb-hb64p     1/1     Running
```

旧 ReplicaSet 会保留（副本数为 0），这是为了支持 `kubectl rollout undo` 回滚。

**有状态应用用 StatefulSet**，它和 Deployment 的三个区别：

1. Pod 名字固定为 `<名称>-<序号>`（`mysql-0`），不是随机后缀
2. 每个 Pod 有独立的 PVC（由 `volumeClaimTemplates` 生成），重建后挂回同一个卷
3. 默认按序号顺序启停

### 3.2 Service 与集群内 DNS

Service 解决「Pod IP 会变」的问题，它提供稳定的虚拟 IP（ClusterIP）和 DNS 名。

四种类型：

| 类型 | 行为 | 适用 |
|---|---|---|
| ClusterIP（默认） | 分配一个仅集群内可达的虚拟 IP | 内部服务互访（后端、数据库） |
| NodePort | 在 ClusterIP 基础上，每个节点开放一个 30000-32767 的端口 | 单机/裸机环境对外暴露 |
| LoadBalancer | 向云厂商申请外部负载均衡器 | 云环境 |
| ExternalName | 只是一个 DNS CNAME，不做转发 | 把集群外服务映射成集群内名字 |

**Headless Service**（`clusterIP: None`）是特殊的第四种：不分配虚拟 IP，只提供 DNS 记录，客户端直接连 Pod IP。有状态服务（数据库）用它，因为客户端需要明确知道连的是哪一个实例。

实测验证 DNS 解析（在一个 Pod 里查另一个 Service）：

```bash
kubectl exec -n questionnaire deploy/frontend -- nslookup backend
kubectl exec -n questionnaire deploy/frontend -- nslookup mysql
```

```text
Name:      backend.questionnaire.svc.cluster.local
Address:   10.109.4.16                    # 普通 Service，解析到 ClusterIP

Name:      mysql-0.mysql.questionnaire.svc.cluster.local   # Headless，解析到具体 Pod
```

DNS 命名规则：

```text
<service>.<namespace>.svc.cluster.local     普通 Service
<pod>.<service>.<namespace>.svc.cluster.local  StatefulSet 的单个 Pod
```

同命名空间内可以只写 `<service>`；跨命名空间必须写 `<service>.<namespace>` 或完整 FQDN。

**转发路径**（理解 NodePort 的实际链路）：

```text
外部请求 → 节点 IP:NodePort
           ↓ kube-proxy 的 iptables 规则
        Service ClusterIP:port
           ↓ 按后端列表轮询
        Pod IP:targetPort
```

查看 Service 关联了哪些 Pod：

```bash
kubectl get endpoints backend -n questionnaire
kubectl get endpointslices -n questionnaire
```

### 3.3 配置与密钥：ConfigMap / Secret

**ConfigMap 存非敏感配置**，两种注入方式：

```yaml
          # 方式一：整体注入成环境变量（键名即变量名）
          envFrom:
            - configMapRef:
                name: questionnaire-config
          # 方式二：逐个注入
          env:
            - name: MYSQL_HOST
              valueFrom:
                configMapKeyRef: {name: questionnaire-config, key: MYSQL_HOST}
```

也可以挂成文件（适合配置文件，如 nginx.conf）：

```yaml
          volumeMounts:
            - name: conf
              mountPath: /etc/nginx/conf.d/default.conf
              subPath: nginx.conf
      volumes:
        - name: conf
          configMap:
            name: web-config
            items:
              - key: nginx.conf
                path: nginx.conf
```

**两者的热更新行为不一样，这点必须记牢**：

| 注入方式 | 改 ConfigMap/Secret 后 | 是否需要重启 Pod |
|---|---|---|
| env / envFrom | 容器环境变量在启动时固定 | 需要（`kubectl rollout restart`） |
| volume 挂载 | kubelet 会定期同步文件到容器（约 1 分钟） | 不需要重启，但应用要自己支持重读 |

**Secret 与 ConfigMap 的区别**：Secret 用于密码、token、证书。注意 Secret 默认只是 base64 编码（不是加密），任何能读该 Secret 的人都能解出明文。生产环境要配合 etcd 静态加密或外部密钥管理（Vault、KMS）。

`stringData` 允许写明文，apiserver 自动转 base64：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: questionnaire-secret
  namespace: questionnaire
type: Opaque
stringData:
  mysql-root-password: "root123456"
  redis-password: "redis123456"
```

引用：

```yaml
          env:
            - name: MYSQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: questionnaire-secret
                  key: mysql-root-password
```

实测验证注入结果（密码已脱敏）：

```bash
kubectl exec -n questionnaire deploy/backend -- sh -c \
  'env | grep -E "MYSQL|REDIS|SPRING_PROFILES" | sed "s/PASSWORD=.*/PASSWORD=***/"'
```

```text
SPRING_PROFILES_ACTIVE=prod
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=questionnaire_sql
MYSQL_USERNAME=root
MYSQL_PASSWORD=***
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=***
```

### 3.4 存储：PV / PVC / StorageClass

三个概念的关系：

```text
StorageClass（存储类：规定「用哪种存储、怎么供给」）
     │ 动态供给
     ▼
PV（PersistentVolume：实际的存储卷，集群资源）
     ▲ 绑定
PVC（PersistentVolumeClaim：用户的存储申请，「我要 2Gi 读写」）
     ▲ 挂载
Pod
```

**部署时只需要写 PVC，PV 由供给器自动创建**。本机 minikube 的默认存储类是：

```bash
kubectl get storageclass
```

```text
NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate
```

两种绑定模式：

| 模式 | 行为 |
|---|---|
| Immediate | PVC 一创建就立刻绑定 PV（会先看到一次 `FailedScheduling: unbound immediate PersistentVolumeClaims`，属正常） |
| WaitForFirstConsumer | 等有 Pod 要用时才绑定（拓扑感知场景更合适） |

**回收策略决定删 PVC 后数据怎么办**：`Delete` 会连底层数据一起删；`Retain` 保留。

StatefulSet 的 `volumeClaimTemplates`（每个 Pod 一个独立卷）：

```yaml
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: standard
        resources:
          requests:
            storage: 2Gi
```

实测结果（PVC 名字是 `<模板名>-<StatefulSet名>-<序号>`）：

```bash
kubectl get pvc -n questionnaire
```

```text
NAME                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
data-mysql-0                         Bound    pvc-e0ddfb90-9673-4049-949b-e06d6d4e70c3   2Gi        RWO            standard
redis-data                           Bound    pvc-40f106bf-660e-4a2f-aa10-2e1a824e1661   1Gi        RWO            standard
```

**访问模式**：

| 模式 | 缩写 | 含义 |
|---|---|---|
| ReadWriteOnce | RWO | 只能被一个节点挂载读写 |
| ReadOnlyMany | ROX | 多节点只读 |
| ReadWriteMany | RWX | 多节点读写（hostPath/NFS 之外多数云盘不支持） |

### 3.5 探针：为什么必须分三种

探针是 K8S 判断容器「健康不健康」的机制，配错了会出真事故。

| 探针 | 探测成功/失败时的动作 | 适用 |
|---|---|---|
| `startupProbe` | 成功前不执行 readiness/liveness；启动超时则重启容器 | 启动慢的服务（数据库、JVM） |
| `readinessProbe` | 失败时把 Pod 从 Service 后端列表摘掉（不接流量，但容器不重启） | 所有对外服务 |
| `livenessProbe` | 失败时重启容器 | 可能死锁/卡死的服务 |

**三者的执行顺序**：

```text
容器启动
   ↓
startupProbe 反复探测 ──成功──► 开始 readiness/liveness 探测
   │                              │
   └─超时（failureThreshold 次）      ├─ readiness 失败 → 摘出 Service（不重启）
      → 重启容器                     └─ liveness 失败  → 重启容器
```

**本次实测踩到的坑**（详见第 7 章坑 1）：MySQL 只配了 livenessProbe（180 秒后开始判死），而它的首次初始化（建 29 张表 + 导入 5 个用户 + 3 份问卷）实测耗时约 6 分钟——初始化到一半被探针杀掉，数据目录留下未干净关闭的状态，之后每次启动都报 InnoDB redo log 无法创建，形成永久 CrashLoop。

正确的配置（数据库类服务）：

```yaml
          startupProbe:
            exec:
              command: [bash, -c, 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent']
            initialDelaySeconds: 20
            periodSeconds: 10
            failureThreshold: 60          # 最多给 10 分钟完成首次初始化
          readinessProbe:
            exec:
              command: [bash, -c, 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent']
            periodSeconds: 10
            failureThreshold: 6
          livenessProbe:
            exec:
              command: [bash, -c, 'mysqladmin ping -h 127.0.0.1 -uroot -p"$MYSQL_ROOT_PASSWORD" --silent']
            periodSeconds: 30
            failureThreshold: 5
```

**探针用什么探测**，按精确度排序：

| 方式 | 说明 | 适用 |
|---|---|---|
| httpGet `/actuator/health` | 能反映依赖状态（数据库断了会变 DOWN） | 引入了 Spring Boot Actuator 的服务，最推荐 |
| tcpSocket | 只验证端口可连，不保证业务可用 | 没有健康端点时的兜底 |
| exec 命令 | 最灵活（如 `redis-cli ping`） | 数据库、缓存等有原生客户端命令的服务 |

**注意**：`readinessProbe` 的 `initialDelaySeconds` 在配置了 `startupProbe` 后就没有意义了（启动期由 startupProbe 兜着），别把两个都配得很保守，会拖慢故障恢复。

### 3.6 资源 requests/limits 与 JVM 的特殊问题

```yaml
          resources:
            requests:                  # 调度依据 + HPA 的分母
              cpu: 200m
              memory: 512Mi
            limits:                    # cgroup 硬顶
              cpu: "1"
              memory: 1Gi
```

- **requests** 是调度器判断「这个节点放得下吗」的依据，也是 HPA 计算 CPU 利用率的基准
- **limits** 是容器实际不能超过的上限：CPU 超了被限流（不会杀）；内存超了直接 OOM Kill

**JVM 在容器里的经典问题**：JVM 默认按「物理机内存」计算堆上限（读 `/proc/meminfo`），在容器里读到的是宿主机内存，于是堆可能被设得远超 limits，一跑就 OOM。两种解法：

```bash
# 解法一（推荐）：按容器限额的百分比设堆
JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=70.0"

# 解法二：显式指定堆大小（要自己算，容易和 limits 脱节）
JAVA_OPTS="-Xmx768m -Xms512m"
```

本项目的实际配置（放在 ConfigMap 里）：

```yaml
  JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=70.0 -Duser.timezone=Asia/Shanghai -Dfile.encoding=UTF-8"
```

注意 JVM 的内存占用不等于堆大小：堆 + Metaspace + 线程栈 + 直接内存 + JIT 代码缓存，通常比 `-Xmx` 大 30% 以上。所以 limits 要比「你以为的堆大小」留出余量——本项目 requests 512Mi / limits 1Gi，实测两个副本各占约 350Mi。

### 3.7 滚动更新与回滚

```yaml
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1            # 最多超出期望副本数 1 个
      maxUnavailable: 0      # 更新过程中可用副本数不得低于期望值
```

`maxUnavailable: 0` 是零中断发布的配置：**先起一个新 Pod，就绪后再停一个旧的**，全程可用副本数不减。

实测零中断（更新过程中每 6 秒请求一次，8 次全部 200）：

```text
滚动过程中持续访问：
  第 1 次: HTTP 200
  ...
  第 8 次: HTTP 200
```

发布与回滚命令：

```bash
# 发布新版本
kubectl set image deploy/backend -n questionnaire backend=questionnaire-backend:1.0.7
kubectl rollout status deploy/backend -n questionnaire

# 查看历史
kubectl rollout history deploy/backend -n questionnaire

# 回滚
kubectl rollout undo deploy/backend -n questionnaire                     # 上一版
kubectl rollout undo deploy/backend -n questionnaire --to-revision=2     # 指定版本

# 重启（不改镜像，只让 Pod 重建，用于重读 ConfigMap）
kubectl rollout restart deploy/backend -n questionnaire
```

**前提**：镜像必须用版本 tag（`1.0.7`）而不是 `latest`。用 `latest` 时新旧 Pod 引用同一个 tag，回滚拿到的是同一个镜像，等于没回滚。

### 3.8 HPA 自动扩缩容

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 4
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

计算逻辑：

```text
期望副本数 = ceil(当前副本数 × 当前指标值 / 目标指标值)
```

**三个前置条件，缺一个 HPA 就显示 `<unknown>`**：

1. 集群装了 metrics-server（提供 metrics.k8s.io API）
2. 目标容器设了 `resources.requests.cpu`（百分比是相对 requests 算的，没有基准就没法算）
3. 目标是有副本数概念的工作负载（Deployment/StatefulSet/ReplicaSet）

实测：

```bash
kubectl get hpa -n questionnaire
kubectl top pods -n questionnaire
```

```text
NAME      REFERENCE            TARGETS        MINPODS   MAXPODS   REPLICAS   AGE
backend   Deployment/backend   cpu: 12%/70%   2         4         2          3m36s

NAME                        CPU(cores)   MEMORY(bytes)
backend-597cff6d78-4ctfm    49m          353Mi
backend-597cff6d78-vqvd8    2m           349Mi
```

当前 12% 低于 70% 阈值，维持最小副本数 2。

**缩容为什么要冷却**：指标有抖动，如果按瞬时值缩容，会出现「缩了 → 负载升高 → 又扩」的震荡。所以 HPA 默认缩容有 5 分钟稳定窗口，`behavior.scaleDown.stabilizationWindowSeconds` 可以调。

**什么时候不该用 HPA**：有状态服务（数据库）、会话粘性强的服务、启动很慢的服务（扩出来的 Pod 还没就绪，流量高峰已经过去）。

### 3.9 镜像交付：没有私有仓库怎么办

Kubernetes 只认镜像仓库里的镜像，**它不认宿主机 docker 里的镜像**（minikube 的 docker 驱动下，节点内是独立的 containerd 存储）。所以本地自建镜像必须显式导入。

```bash
# 构建
docker build -t questionnaire-backend:latest ./backend
docker build -t questionnaire-frontend:latest ./frontend

# 导入 minikube 节点
minikube image load questionnaire-backend:latest  -p minikube
minikube image load questionnaire-frontend:latest -p minikube

# 验证
minikube ssh -p minikube -- 'sudo crictl images | grep questionnaire'
```

```text
docker.io/library/questionnaire-backend    latest   3bdef3f73a548   170MB
docker.io/library/questionnaire-frontend   latest   0b4cd639ee6ac   22.3MB
```

**必须配 `imagePullPolicy: IfNotPresent`**。因为这样导入的镜像没有仓库地址，写默认的 `Always`（tag 是 `latest` 时的默认值）会让 kubelet 去 Docker Hub 找 `library/questionnaire-backend`，必然 `ImagePullBackOff`。

四种镜像交付方式对比：

| 方式 | 适用 | 代价 |
|---|---|---|
| `minikube image load` | 本地开发、单机验证 | 每次改代码都要重新导入；多节点集群要逐节点导入 |
| 自建私有仓库（Harbor / registry:2） | 团队内部、多环境 | 要维护仓库服务与证书 |
| 公共仓库（Docker Hub / 阿里云 ACR） | 有外网、想省事 | 私有代码要考虑安全 |
| `minikube image build` | 直接借用节点内的构建能力 | 构建缓存不在宿主机，调试不方便 |

**生产建议**：私有仓库 + 版本 tag。`latest` 只适合本地玩。

---

## 4. 部署实战

完整清单在 `/opt/project-work/questionnaire_work/k8s/`，7 个文件：

| 文件 | 内容 |
|---|---|
| `00-namespace.yaml` | Namespace `questionnaire` |
| `01-secret.yaml` | MySQL / Redis 密码 |
| `02-configmap-app.yaml` | 应用环境变量（含 JVM 参数、时区） |
| `03-mysql.yaml` | Headless Service + StatefulSet + volumeClaimTemplates |
| `04-redis.yaml` | Service + Deployment + PVC |
| `05-backend.yaml` | Deployment(2) + Service `backend` + initContainer |
| `06-frontend.yaml` | Deployment(2) + NodePort Service（固定 30088） |
| `07-hpa.yaml` | HPA 2~4 副本 |

### 4.1 数据库初始化 SQL 怎么进集群

MySQL 官方镜像会执行 `/docker-entrypoint-initdb.d/` 下的 `*.sql`（按文件名字典序），且**只在数据目录为空时执行一次**。所以把 SQL 文件打成 ConfigMap 挂进去：

```bash
kubectl create configmap mysql-init -n questionnaire \
  --from-file=01-schema.sql=backend/sql/schema.sql \
  --from-file=02-data.sql=backend/sql/data.sql
```

两个文件合计 80KB（34918 + 45184 字节），远小于 ConfigMap 单文件 1MB 上限。清单里挂载：

```yaml
          volumeMounts:
            - name: init-sql
              mountPath: /docker-entrypoint-initdb.d
              readOnly: true
      volumes:
        - name: init-sql
          configMap:
            name: mysql-init
```

### 4.2 后端清单的关键设计

**（1）Service 必须叫 `backend`**

前端镜像里的 nginx 配置写死了 `proxy_pass http://backend:8081/`。K8S 里 Service 名就是集群内 DNS 名，所以 Service 叫 `backend` 时这份配置一行都不用改。

**（2）用 initContainer 替代 depends_on**

```yaml
      initContainers:
        - name: wait-for-deps
          image: questionnaire-backend:latest      # 复用同一个镜像，不引入额外依赖
          imagePullPolicy: IfNotPresent
          command:
            - sh
            - -c
            - |
              set -e
              echo "[init] 等待 MySQL (mysql:3306) 就绪 ..."
              until nc -z -w 2 mysql 3306; do sleep 2; done
              echo "[init] MySQL 已可连接"
              echo "[init] 等待 Redis (redis:6379) 就绪 ..."
              until nc -z -w 2 redis 6379; do sleep 2; done
              echo "[init] 依赖全部就绪，交由主容器启动"
```

实测日志：

```text
[init] 等待 MySQL (mysql:3306) 就绪 ...
[init] MySQL 已可连接
[init] 等待 Redis (redis:6379) 就绪 ...
[init] 依赖全部就绪，交由主容器启动
```

主容器随后启动成功：

```text
00:42:02 INFO Tomcat started on port 8081 (http) with context path '/'
00:42:02 INFO Started QuestionnaireAdminApplication in 23.346 seconds
```

**（3）无状态化才能多副本**

登录态存在 Redis（sa-token 的 `Authorization:login:*`），JVM 内存里没有会话，所以后端天然无状态，可以安全跑 2 副本。验证 Redis 里确实有登录态：

```bash
kubectl exec -n questionnaire deploy/redis -- \
  redis-cli -a redis123456 --no-auth-warning -n 1 keys '*'
```

```text
Authorization:login:...BbaQ
system:user:route::1
system:role:menu:list::1
system:role:permission:list::1
system:dict:item:menu_type
...（共 12 个 key）
```

**注意 `-n 1`**：后端配置 `spring.data.redis.database: 1`，而 `redis-cli` 默认连 DB 0，不加会看到「空 Redis」而误判。

### 4.3 部署命令与实测输出

```bash
export KUBECONFIG=/root/.kube/config
cd /opt/project-work/questionnaire_work

kubectl apply -f k8s/00-namespace.yaml

kubectl create configmap mysql-init -n questionnaire \
  --from-file=01-schema.sql=backend/sql/schema.sql \
  --from-file=02-data.sql=backend/sql/data.sql

kubectl apply -f k8s/01-secret.yaml -f k8s/02-configmap-app.yaml
kubectl apply -f k8s/03-mysql.yaml -f k8s/04-redis.yaml

# 等 MySQL 完成首次初始化（实测约 6 分钟）
kubectl wait --for=condition=Ready pod/mysql-0 -n questionnaire --timeout=450s

kubectl apply -f k8s/05-backend.yaml -f k8s/06-frontend.yaml -f k8s/07-hpa.yaml
kubectl rollout status deploy/backend  -n questionnaire --timeout=380s
kubectl rollout status deploy/frontend -n questionnaire --timeout=180s
```

```text
namespace/questionnaire created
configmap/mysql-init created
secret/questionnaire-secret created
configmap/questionnaire-config created
service/mysql created
statefulset.apps/mysql created
persistentvolumeclaim/redis-data created
service/redis created
deployment.apps/redis created
pod/mysql-0 condition met
service/backend created
deployment.apps/backend created
service/frontend created
deployment.apps/frontend created
horizontalpodautoscaler.autoscaling/backend created
deployment "backend" successfully rolled out
deployment "frontend" successfully rolled out
```

最终状态：

```bash
kubectl get all -n questionnaire -o wide
```

```text
NAME                            READY   STATUS    RESTARTS   AGE     IP
pod/backend-5677c8874b-t57n2    1/1     Running   0          92s     10.244.0.26
pod/backend-5677c8874b-vrzhq    1/1     Running   0          50s     10.244.0.25
pod/frontend-5d64d4d588-q4ktp   1/1     Running   0          7m59s   10.244.0.21
pod/frontend-5d64d4d588-sl426   1/1     Running   0          7m59s   10.244.0.22
pod/mysql-0                     1/1     Running   0          14m     10.244.0.18
pod/redis-6fc9fcd475-65znw      1/1     Running   0          24m     10.244.0.16

NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
service/backend    ClusterIP   10.109.4.16     <none>        8081/TCP
service/frontend   NodePort    10.102.148.46   <none>        80:30088/TCP
service/mysql      ClusterIP   None            <none>        3306/TCP
service/redis      ClusterIP   10.104.17.142   <none>        6379/TCP

NAME                       READY   UP-TO-DATE   AVAILABLE
deployment.apps/backend    2/2     2            2
deployment.apps/frontend   2/2     2            2
deployment.apps/redis      1/1     1            1

NAME                     READY   AGE
statefulset.apps/mysql   1/1     12m
```

MySQL 首次初始化的实测时序（关键：`01-schema.sql` 单独跑了 101 秒）：

```text
00:28:12 [Entrypoint] Entrypoint script for MySQL Server 8.4.11-1.el9 started.
00:28:13 [Entrypoint] Initializing database files
00:31:31 [Entrypoint] Database files initialized
00:32:09 [Entrypoint] Creating database questionnaire_sql
00:32:09 [Entrypoint] running /docker-entrypoint-initdb.d/01-schema.sql
00:33:50 [Entrypoint] running /docker-entrypoint-initdb.d/02-data.sql
00:34:10 [Entrypoint] MySQL init process done. Ready for start up.
00:34:49 [Server] ready for connections. Version: '8.4.11'  port: 3306
```

---

## 5. 全链路验证

请求链路：

```text
浏览器
  │
  ▼ 宿主机 nginx :8090
  ▼ NodePort 30088（节点 192.168.49.2）
  ▼ 前端 Pod（nginx:80）
  │    ├─ 静态资源 / → /usr/share/nginx/html
  │    └─ /api/ → proxy_pass http://backend:8081/   （集群内 Service 解析）
  ▼ Service backend → 后端 Pod（Spring Boot:8081）
  │
  ├─► Service mysql → StatefulSet Pod mysql-0 → PVC（持久化）
  └─► Service redis → Deployment Pod → PVC
```

### 5.1 第一层：前端静态资源

```bash
curl -s -o /dev/null -w "GET / -> HTTP %{http_code}\n" http://192.168.49.2:30088/
curl -s http://192.168.49.2:30088/ | head -c 200
```

```text
GET / -> HTTP 200
<!doctype html>
<html lang="zh-cmn-Hans">
  <head>
    <meta name="buildTime" content="2026-08-20 06:28:35">
    <title>问卷调查系统</title>
```

### 5.2 第二层：集群内 DNS 与依赖连通性

```bash
kubectl exec -n questionnaire deploy/frontend -- nslookup backend
kubectl exec -n questionnaire deploy/backend  -- sh -c \
  'nc -z -w 2 mysql 3306 && echo "mysql:3306 通"; nc -z -w 2 redis 6379 && echo "redis:6379 通"'
```

```text
Name:      backend.questionnaire.svc.cluster.local
Address:   10.109.4.16

mysql:3306 通
redis:6379 通
```

### 5.3 第三层：登录接口（含密码处理方式）

**这个项目的前端在提交前会对密码做一次 sha256**，服务端再拼 salt 做第二次哈希：

```java
// SysUserServiceImpl.userLogin
String inputPassword = sysUserBO.getPassword() + userForUserName.getSalt();
if (!DigestUtils.sha256Hex(inputPassword).equals(userForUserName.getPassword())) {
    throw new BizException("登录失败，请核实用户名以及密码");
}
```

库里存的是 `sha256(sha256(明文) + salt)`。所以脚本直连 API 时必须自己先算 sha256：

```bash
python3 -c "import hashlib;print(hashlib.sha256('kt123456'.encode()).hexdigest())"
# 80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776

curl -s -X POST http://192.168.49.2:30088/api/auth/user_name \
  -H 'Content-Type: application/json' \
  -d '{"userName":"admin","password":"80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"}'
```

```text
{"code":200,"message":"操作成功","data":{"token":"eyJ0eX...BbaQ"},"timestamp":1789144675166}
```

带 token 取用户信息：

```bash
TOKEN=<上一步的 token>
curl -s -H "Authorization: Bearer $TOKEN" http://192.168.49.2:30088/api/auth/user_info
```

```text
{"code":200,"message":"操作成功","data":{"id":1,"userName":"admin","nickName":"管理员",
 "realName":"系统管理员","email":"admin@questionnaire.com","status":"1",
 "lastLoginTime":1789144674000,...}}
```

取菜单路由（复杂查询 + 权限计算）：

```text
{"code":200,"message":"操作成功","data":{"home":"home","routes":[{"name":"questionnaire",
 "path":"/questionnaire","component":"layout.base","meta":{"title":"问卷管理",...
```

### 5.4 第四层：数据落库证据

登录日志（后端写 MySQL）：

```bash
kubectl exec -n questionnaire mysql-0 -- bash -c \
  'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" --default-character-set=utf8mb4 -e \
   "select id,user_name,status,left(message,20) as msg,create_time from questionnaire_sql.mon_logs_login order by id desc limit 5"'
```

```text
id                  user_name  status  msg        create_time
2098450975994884097 admin      1       登陆成功   2026-09-12 00:37:55
```

业务数据（初始化脚本导入）：

```text
1001  2026 年度员工满意度调研   1
1002  产品功能市场调研          1
1003  Python 课程课后反馈       2
```

### 5.5 第五层：对外入口

NodePort 只监听节点地址，局域网无法直达，所以宿主机 nginx 反代一层（配置见 `/etc/nginx/conf.d/questionnaire.conf`）：

```nginx
server {
    listen 8090;
    server_name _;
    client_max_body_size 50m;
    location / {
        proxy_pass http://192.168.49.2:30088;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

实测可达性：

```text
http://127.0.0.1:8090/            HTTP 200
http://192.168.1.167:8090/        HTTP 200
http://100.71.112.119:8090/       HTTP 200
http://192.168.49.2:30088/        HTTP 200
```

---

## 6. 应用场景实战

### 场景一：前后端分离项目从 compose 迁到 K8S

**背景**：项目原本用 docker-compose 部署在单机上，需要迁到公司的 Kubernetes 集群，但不想改动任何应用代码和 nginx 配置。

**做法与关键决策**：

1. **保持服务名不变**。compose 里叫 `backend`/`mysql`/`redis`，K8S 的 Service 也叫这些名字。因为 compose 的服务名和 K8S 的 Service 名都是「集群内 DNS 名」，语义一致，所以 `application-prod.yml` 里的 `${MYSQL_HOST:mysql}`、前端 nginx 里的 `proxy_pass http://backend:8081/` **一行都不用改**。

2. **配置分层**。把 compose 里混在一起的 `environment:` 拆成三份：
   - 非敏感且不随环境变的（时区、JVM 参数）→ ConfigMap
   - 密码 → Secret
   - 随环境变的（`MYSQL_HOST` 在本地是 `mysql`，在测试环境可能是 `mysql.test.svc.cluster.local`）→ 用 Kustomize overlay 或 Helm values 分环境，不要复制多份清单

3. **用探针替代 healthcheck**。compose 的 `healthcheck` 只用于 `depends_on` 判断，K8S 的探针除了启动顺序还管流量摘挂与故障重启，语义更强。

4. **用 initContainer 替代 `depends_on`**。K8S 没有依赖顺序的概念，靠 initContainer 显式阻塞。

5. **数据卷换成 PVC**。compose 的命名卷 → K8S 的 PVC；如果生产用 NFS/Ceph，只改 `storageClassName`，Pod 模板不动。

**收益**：清单化之后，本地 minikube 和生产的清单是同一份（仅镜像来源与存储类不同），本地验证过的探针参数、资源配额、启动顺序在生产不会重踩。本次实测正是靠本地验证提前发现了「MySQL 首次初始化 6 分钟被 livenessProbe 杀掉」这个会损坏数据目录的问题。

### 场景二：同一份清单在本地与生产分别适配（Kustomize 思路）

**背景**：本地 minikube 与生产集群的差异集中在四处：镜像来源（本地导入 vs 私有仓库）、副本数（本地省资源 vs 生产按容量）、存储类（standard-hostpath vs ceph-rbd）、对外方式（NodePort+nginx vs Ingress）。

**做法**：base 放公共部分，overlay 只覆盖差异。

```text
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── 01-secret.yaml
│   ├── 02-configmap.yaml
│   ├── 03-mysql.yaml
│   ├── 04-redis.yaml
│   ├── 05-backend.yaml
│   └── 06-frontend.yaml
└── overlays/
    ├── minikube/
    │   ├── kustomization.yaml
    │   └── patch-resources.yaml       # imagePullPolicy: IfNotPresent、副本数 2、storageClassName: standard
    └── prod/
        ├── kustomization.yaml
        ├── patch-resources.yaml       # 镜像指向私有仓库、副本数 4、storageClassName: ceph-rbd
        └── ingress.yaml               # 生产用 Ingress 而不是 NodePort
```

部署时：

```bash
# 本地
kubectl apply -k k8s/overlays/minikube

# 生产
kubectl apply -k k8s/overlays/prod
```

差异只写在 overlay 里，base 改动所有环境同步生效——避免「改了本地清单忘了改生产」这类问题。

**当前本项目的简化做法**：只有一套环境，所以直接 7 个平铺文件 + `kubectl apply -f k8s/`。等需要多环境时再改成 Kustomize 结构（改造时不需要动任何业务代码）。

---

## 7. 最佳实践与踩坑记录

### 最佳实践

1. **清单全部进版本库**，集群当可丢弃资源。整套东西重建只要 `kubectl apply -f k8s/`（加上 ConfigMap 创建与 MySQL 初始化等待，约 10 分钟）。
2. **镜像用版本 tag，不用 `latest`**。`latest` 让回滚失效，也让 `imagePullPolicy` 默认变成 `Always`（本地导入的镜像会因此拉取失败）。
3. **探针该配三种就配三种**，尤其是启动慢的服务必须有 `startupProbe`。探针参数要按「最坏情况启动时间」定，不要按平均值。
4. **requests 一定要写**。不写 requests 的容器在调度时被当作 0 资源，节点会超卖；HPA 也无法工作。
5. **JVM 用 `MaxRAMPercentage`**，不要硬编码 `-Xmx`，让堆随 limits 自动伸缩。
6. **多副本前先确认应用无状态**。有会话的必须先外置到 Redis/数据库，否则多副本下会出现「登录成功但下一个请求跳到另一副本又变未登录」。
7. **删命名空间前确认数据能丢**。PVC 的回收策略是 `Delete` 时，删 PVC 会连底层数据一起删；要保留先导出 SQL。
8. **密码用 Secret，但要知道 Secret 不是加密**。生产要开 etcd 静态加密或接外部密钥管理。
9. **`kubectl describe pod` 的 Events 是排错第一入口**，比看容器日志更早发现问题（调度失败、拉镜像失败、探针失败都记在这里）。
10. **Pod 名字里的哈希不是随机噪音**：`backend-ff6f7cfcb-c2vms` 中 `ff6f7cfcb` 是 ReplicaSet 的 pod-template-hash（Pod 模板变了哈希就变），`c2vms` 才是 Pod 自己的随机后缀。

### 踩坑记录

**坑 1：livenessProbe 太激进，把正在初始化的 MySQL 杀了，导致永久 CrashLoop**

结论：MySQL Pod 反复重启，报

```text
[ERROR] [MY-012960] [InnoDB] Cannot create redo log files because data files are
corrupt or the database was not shut down cleanly after creating the data files.
```

原因：只配了 `livenessProbe(initialDelaySeconds: 120, periodSeconds: 20, failureThreshold: 3)`，即容器启动约 180 秒后开始判死；而 MySQL 首次初始化实测耗时约 6 分钟（`schema.sql` 一个文件就 101 秒）。探针在初始化过程中杀掉容器 → 数据目录留下未干净关闭的状态 → 之后每次启动都失败。

解法：加 `startupProbe(initialDelaySeconds: 20, periodSeconds: 10, failureThreshold: 60)`，让 readiness/liveness 在启动成功前都不计时。**同时必须删掉脏数据的 PVC 重建**（`kubectl delete pvc data-mysql-0`），否则脏状态一直在，光改探针没用。

**坑 2：服务端要的是 sha256 后的密码，不是明文**

结论：用 `admin` / `kt123456` 直接调登录接口，返回「登录失败，请核实用户名以及密码」。

原因：前端提交前对密码做了一次 sha256，服务端再拼 salt 做第二次哈希（`sha256(传入的密码 + salt)`，库中存 `sha256(sha256(明文) + salt)`）。所以直接传明文时服务端算出来的是 `sha256(明文 + salt)`，与库里的值不匹配。

解法：脚本测试时先算 sha256（见 5.3）。排查这类「密码肯定没错但登录失败」时，先看前端有没有做客户端加密。

**坑 3：Redis 看起来是空的（其实是查错了 DB）**

结论：`redis-cli keys '*'` 返回空，好像登录态没写进 Redis。

原因：后端配置 `spring.data.redis.database: 1`，`redis-cli` 默认连 DB 0。

解法：`redis-cli -n 1 keys '*'`。Redis 默认有 16 个库，多业务共用一个实例时常按库隔离，排查前先确认应用配置的库号。

**坑 4：本地导入的镜像 ImagePullBackOff**

结论：`ImagePullBackOff`，事件里显示去 `docker.io/library/<名字>` 拉取失败。

原因：`minikube image load` 导入的镜像不在任何仓库里；tag 是 `latest` 时 `imagePullPolicy` 默认为 `Always`，kubelet 会去 Docker Hub 找，而本机 Docker Hub 不通。

解法：显式写 `imagePullPolicy: IfNotPresent`。

**坑 5：PVC 未绑定导致第一次调度失败（正常现象）**

结论：事件里先出现

```text
Warning  FailedScheduling  default-scheduler  0/1 nodes are available:
  pod has unbound immediate PersistentVolumeClaims. not found
```

紧接着是 `Normal Scheduled ... Successfully assigned questionnaire/mysql-0 to minikube`。

原因：`Immediate` 绑定模式下 PVC 绑定是异步的，调度器第一次尝试时 PVC 还没 Bound。换 `WaitForFirstConsumer` 模式的 StorageClass 不会有这个现象。

解法：不用处理，看最终是否 Scheduled 成功即可。

**坑 6：ConfigMap 装不下大 SQL**

结论：ConfigMap 单个对象上限 1MB（etcd 限制 + apiserver 校验），几 MB 的初始化 SQL 放不进去。

原因：ConfigMap 的数据存在 etcd 里，etcd 对单个 value 有大小限制。

解法三选一：把 SQL 打进初始化镜像（`FROM mysql:8.4` + `COPY sql/ /docker-entrypoint-initdb.d/`）、用 Job 执行初始化、交给 Flyway/Liquibase 由应用启动时执行。

**坑 7：ConfigMap 改了但应用没生效**

结论：`kubectl edit configmap` 之后应用行为没变。

原因：以 env/envFrom 形式注入的变量在容器启动时就固化了，不会热更新。

解法：`kubectl rollout restart deploy/<名字>`。要热更新就改成 volume 挂载 + 应用自己重读配置文件（Spring Boot 需配合 `@RefreshScope` / Spring Cloud Config / 或监听文件变化）。

**坑 8：NodePort 局域网访问不通**

结论：`192.168.1.167:30088` 不可达，只有 `192.168.49.2:30088`（节点网桥地址）能通。

原因：NodePort 绑定在节点 IP 上，而 minikube 节点是容器，节点 IP 是宿主机内的网桥地址，只有宿主机能路由到。

解法：宿主机 nginx 反代（推荐，与现有站点统一）、`kubectl port-forward --address 0.0.0.0`（临时）、`minikube tunnel`（给 LoadBalancer 用，会写宿主机路由）。生产集群的节点是真实主机，不存在这个问题——用 Ingress 或 LoadBalancer 即可。

**坑 9：`kubectl logs` 报「a container name must be specified for pod」**

结论：多容器 Pod（含 initContainer）不指定容器名看不了日志。

原因：Pod 里有多个容器（含 init 容器），kubectl 不知道你要哪个。

解法：`kubectl logs <pod> -c <容器名>`；看 init 容器日志是 `-c wait-for-deps`，看上次崩溃的日志是 `--previous`。

---

## 8. 参考链接

- Kubernetes 官方概念文档：https://kubernetes.io/docs/concepts/
- Deployment 与滚动更新：https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Service 与 DNS：https://kubernetes.io/docs/concepts/services-networking/service/
- 配置最佳实践（ConfigMap/Secret）：https://kubernetes.io/docs/concepts/configuration/
- 探针配置：https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- 资源管理与 JVM 容器感知：https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- HPA：https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- 配套文档：
  - `[[kubernetes-minikube-install]]`（minikube 单节点集群搭建）
  - `/opt/project-work/questionnaire_work/K8S-部署手册.md`（本项目部署实操手册）
