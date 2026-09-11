---
title: Kubernetes 与 minikube 单节点集群搭建
created: 2026-09-12
updated: 2026-09-12
type: integration
tags: [kubernetes, minikube, containerd, cni, kubelet, kubeadm, 容器编排, 镜像源]
---

> 整理日期：2026-09-12

## 目录

1. [概述](#1-概述)
2. [Kubernetes 架构与核心概念](#2-kubernetes-架构与核心概念)
3. [集群部署形态选型](#3-集群部署形态选型)
4. [minikube 的工作原理](#4-minikube-的工作原理)
5. [环境准备](#5-环境准备)
6. [安装实战](#6-安装实战)
7. [集群验证](#7-集群验证)
8. [容器镜像源方案](#8-容器镜像源方案)
9. [应用场景实战](#9-应用场景实战)
10. [最佳实践与踩坑记录](#10-最佳实践与踩坑记录)
11. [参考链接](#11-参考链接)

---

## 1. 概述

Kubernetes（缩写 K8S，K + 8 个字母 + S）是容器编排系统。它要解决的问题是：**当你有几十上百个容器要跑在若干台机器上时，如何让它们的部署、扩缩、故障恢复、服务发现、配置管理全部自动化**。

手工 `docker run` 管理容器，规模一上去就会遇到这些事：某个容器挂了要人工重启、发新版本要挨个停机、扩容要手工改 nginx upstream、配置散落在各台机器上。Kubernetes 的做法是把「你想要的最终状态」写成声明式配置（YAML）提交给集群，然后由一组控制器持续对比实际状态与期望状态，自动把差异补齐。

本机需要一套能跑生产级项目（Spring Boot + Vue + MySQL + Redis）的 Kubernetes 环境，用于学习和验证部署方案。本文记录从零搭建 minikube 单节点集群的完整过程，包括架构原理、参数含义、实测输出，以及本机网络环境下特有的镜像源问题。

**本篇覆盖范围**：K8S 架构与概念、部署形态选型、minikube 原理、安装与验证、镜像源方案。

**配套文档**：《SpringBoot + Vue 项目部署到 Kubernetes》记录把实际项目迁上去的完整过程。

---

## 2. Kubernetes 架构与核心概念

### 2.1 整体架构：控制面 + 工作节点

一个 Kubernetes 集群分两部分：

```text
                    ┌─────────────────── 控制面（Control Plane）───────────────────┐
                    │                                                              │
   kubectl ────────►│  kube-apiserver  ◄──►  etcd（唯一数据源）                    │
   （客户端）        │        ▲                                                     │
                    │        │                                                     │
                    │  kube-scheduler        kube-controller-manager              │
                    │  （决定 Pod 放哪个节点）  （不断把实际状态收敛到期望状态）        │
                    └────────┬─────────────────────────────────────────────────────┘
                             │  watch / 下发
                    ┌────────▼──────── 工作节点（Node）──────────────────────────┐
                    │  kubelet（节点代理，管 Pod 生命周期）                       │
                    │  kube-proxy（Service 转发规则）                            │
                    │  containerd / CRI-O（容器运行时，真正跑容器）                │
                    │  Pod  Pod  Pod ...                                        │
                    └───────────────────────────────────────────────────────────┘
```

组件职责：

| 组件 | 职责 | 关键点 |
|---|---|---|
| kube-apiserver | 集群唯一入口，负责认证、授权、准入、读写 etcd | 所有组件都只跟它通信，没有旁路 |
| etcd | 保存全部集群状态（对象定义、密钥、事件） | 不存业务数据；单点故障等于集群失忆 |
| kube-scheduler | 为新 Pod 选择节点（资源、污点、亲和性打分） | 只做决策，不负责启动容器 |
| kube-controller-manager | 跑几十个控制器循环，把实际状态拉回期望状态 | 自愈、扩缩、垃圾回收都在这里 |
| kubelet | 节点代理，照 Pod 规格指挥容器运行时启停容器 | 唯一直接管容器的 K8S 组件 |
| kube-proxy | 维护 Service 的 iptables/IPVS 转发规则 | ClusterIP、NodePort 都靠它 |
| 容器运行时 | 真正创建容器（containerd、CRI-O） | 通过 CRI 接口被 kubelet 调用 |

### 2.2 声明式 API 与控制器模式

这是理解 Kubernetes 的核心。它不是「命令式」的：

```text
命令式（docker）：docker run -d --name web nginx     # 我告诉系统做什么
声明式（K8S）：   YAML 里写「我要 3 个 web 副本」      # 我告诉系统我要什么
```

提交 YAML 后发生的事：

```text
1. apiserver 校验并写入 etcd（此刻「期望状态」= 3 个副本，实际 = 0 个）
2. Deployment 控制器发现差异 → 创建 ReplicaSet → 创建 3 个 Pod 对象
3. scheduler 发现没有节点的 Pod → 选节点 → 写入 nodeName
4. 目标节点的 kubelet watch 到「有 Pod 该我跑」→ 拉镜像、起容器
5. 若某个容器挂了：kubelet 重启它；若整个 Pod 被删：ReplicaSet 再补一个
6. 若节点失联：Node 控制器打 NotReady 污点并驱逐其 Pod
```

整套机制的产出是**自愈**：任何一环坏掉都有人把它拉回来。这也是为什么 K8S 里「删 Pod」不算个事——它本来就会被自动重建。

### 2.3 核心资源对象

| 对象 | 作用 | 一句话理解 |
|---|---|---|
| Pod | 最小调度单元，一个或多个共享网络/存储的容器 | 容器的「逻辑主机」 |
| ReplicaSet | 保证指定数量的 Pod 副本存活 | 管副本数量的看门狗 |
| Deployment | 管理 ReplicaSet，支持滚动更新与回滚 | 无状态应用的标准载体 |
| StatefulSet | 有序、有稳定网络标识和独立存储的 Pod | 数据库/中间件的标准载体 |
| DaemonSet | 每个节点跑一个 Pod | 日志采集、节点监控 |
| Job / CronJob | 跑一次 / 定时跑 | 批处理、定时任务 |
| Service | 一组 Pod 的稳定访问入口（ClusterIP/NodePort/LoadBalancer） | 解决 Pod IP 会变的问题 |
| Ingress | 七层路由（按域名/路径分发） | 集群的「nginx」 |
| ConfigMap / Secret | 配置与密钥 | 配置与镜像解耦 |
| Volume / PVC / StorageClass | 存储抽象与动态供给 | 让 Pod 用上持久化存储 |
| Namespace | 逻辑隔离分区 | 集群内的「虚拟集群」 |
| HPA | 按指标自动调副本数 | 自动扩缩容 |

### 2.4 网络模型：三个网段要分清

K8S 网络是很容易绕晕的部分，关键是分清三个网段：

```text
节点网段        192.168.49.0/24   节点自己的 IP（minikube 节点是 192.168.49.2）
Pod 网段        10.244.0.0/24     每个 Pod 一个 IP，Pod 之间可直接互通（本机 minikube 的 PodCIDR）
Service 网段    10.96.0.0/12      ClusterIP 从这里分配，是「虚拟 IP」，不存在于任何网卡上
```

- **Pod IP 会变**：Pod 重建后 IP 就换一个，所以不能写死 IP。
- **Service IP 稳定**：Service 一旦创建，ClusterIP 就固定，它靠 kube-proxy 的转发规则指向后端的 Pod。
- **DNS 是粘合剂**：集群内 DNS（CoreDNS）把 Service 名字解析成 ClusterIP，`Service名.命名空间.svc.cluster.local` 是标准 FQDN，同命名空间可简写为 `Service名`。
- **CNI 负责 Pod 网络**：kubelet 启动 Pod 时需要 CNI 插件提供网络。CNI 没就绪时，节点会报 `cni plugin not initialized` 并且一直 `NotReady`——所有 Pod 都调度不上去（这是本机之前那套坏集群的病因，详见《Kubernetes-K8S-单节点集群部署文档》第 4 章）。

---

## 3. 集群部署形态选型

K8S 官方只提供 kubeadm 引导工具，但社区有几种更省事的形态。选型要看目标：

| 形态 | 形态本质 | 资源占用 | 适合场景 | 不适合 |
|---|---|---|---|---|
| kubeadm | 集群组件直接装成宿主机 systemd 服务（kubelet 宿主进程 + 静态 Pod） | 最低（无虚拟化层） | 生产、多节点、真实拓扑 | 单机学习（侵入宿主机、牵扯 swap/iptables/端口） |
| k3s | 单二进制，控制面组件塞进一个进程，装成 systemd 服务 | 低（约 512MB） | 边缘计算、轻量生产、单机 | 想学标准组件细节（很多组件被裁剪） |
| **minikube** | **整个集群跑在一个容器（或虚拟机）里** | 中（约 1GB） | 本地开发、学习、单机验证 | 生产（单节点、无高可用） |
| kind | 用 Docker 容器模拟多节点集群 | 中 | CI 里跑集成测试、快速起多节点 | 长期运行的环境（节点是容器，重启即失） |

### 3.1 本机为什么选 minikube

三个决定因素：

1. **宿主机上已经跑着一批在用的服务**（1Panel、Jumpserver、Jenkins、Nacos、RabbitMQ、Milvus、MinIO、PostgreSQL）。kubeadm 会在宿主机再起一套 etcd（占 2379/2380 端口）和 kube-proxy 的 iptables 规则，而宿主机已经有 Milvus 依赖的 etcd 容器，冲突排查成本高。
2. **宿主机 swap 正在被使用**（8GiB 里用了 3.3GiB）。kubeadm 路线要求关 swap 或专门配置 kubelet 的 swap 行为，关 swap 在内存已用 9.4GiB 时有 OOM 风险。
3. **minikube 与 kubectl 已经装过**，且本地已有 1.9GB 镜像缓存（含 kicbase 基础镜像和 v1.37.0 的核心组件镜像），重建可离线完成。

minikube 的代价也说清楚：单节点（无法验证高可用与多节点调度）、节点容量声明与实际 cgroup 限额不一致（见第 10 章坑 4）、两层 overlayfs 叠加带来的快照脆弱性（见坑 5）。

---

## 4. minikube 的工作原理

minikube 的定位是「本地单节点 K8S 集群」，它的实现方式很值得理解：

```text
宿主机
├── docker daemon
│   └── minikube 容器（kicbase 镜像，基于 Debian 12）
│       ├── systemd（容器内的 1 号进程）
│       ├── containerd（容器运行时）
│       │   └── 所有 K8S 组件与业务 Pod
│       ├── kubelet / kube-proxy（systemd 服务）
│       └── kube-apiserver / etcd / scheduler / controller-manager
│           （以静态 Pod 形式由 kubelet 直接拉起）
└── kubectl ──(通过 kubeconfig 指向 192.168.49.2:8443)──► apiserver
```

几个关键点：

**（1）集群组件跑在容器里，不是宿主机上**

所以 `minikube delete` 等于把整个集群连根拔起，宿主机不留任何痕迹——这是它相比 kubeadm 最大的好处。

**（2）控制面组件是「静态 Pod」**

etcd、apiserver、scheduler、controller-manager 的名字后面带节点名后缀（`etcd-minikube`），它们是静态 Pod：清单文件放在节点内的 `/etc/kubernetes/manifests/`，由 kubelet 直接监控并拉起，**不走 scheduler，也不能用 kubectl delete 删除**（删了立刻重建）。这是「先有鸡还是先有蛋」的解法：apiserver 自己也是被 kubelet 拉起来的。

**（3）kicbase 是节点基础镜像**

`kicbase/stable:v0.0.51` 这个镜像里预装了 systemd、containerd、kubelet 二进制和 CNI 插件。minikube 启动时创建这个容器、写入 K8S 组件镜像、启动 systemd，集群就起来了。

**（4）网络怎么通的**

```text
宿主机 ──► 192.168.49.1（网桥）──► 192.168.49.2（节点）
                                     ├── Pod 网段 10.244.0.0/24
                                     └── Service 网段 10.96.0.0/12
```

宿主机上因此会多出一个 `br-xxxx` 网桥和 `192.168.49.1` 地址。NodePort（30000-32767）绑定在节点 IP `192.168.49.2` 上，**只有宿主机能路由到**——所以从局域网访问需要宿主机 nginx 反代或 port-forward（见配套文档）。

**（5）kubeconfig 在哪里**

`~/.kube/config`（本机是 `/root/.kube/config`），里面记录了 apiserver 地址、CA 证书、客户端证书和当前上下文。minikube 会自动切换上下文，所以 `kubectl` 开箱即用。

---

## 5. 环境准备

### 5.1 硬件与系统（本机实测）

```bash
nproc; free -h; df -h /; systemd-detect-virt
```

```text
8
               total        used        free      shared  buff/cache   available
内存：          19Gi       9.4Gi       848Mi       319Mi        9.7Gi       9.9Gi
交换：         8.0Gi       3.3Gi       4.7Gi
文件系统        大小  已用  可用 已用% 挂载点
/dev/sda2       915G   83G  786G   10% /
none                       # 裸机（非虚拟机）
```

minikube 官方最低要求是 2 CPU / 2GB 内存 / 20GB 磁盘。本机 8 核 19GiB 充裕，但要给节点容器**显式限制**资源，避免它跟宿主机上一堆在用服务抢内存。

### 5.2 需要的前置组件

| 组件 | 本机版本 | 作用 |
|---|---|---|
| Docker | 29.5.2 | minikube 的驱动（用容器跑节点） |
| containerd | 2.3.4 | 宿主机侧的容器运行时（Docker 内部也在用） |
| kubectl | v1.37.0 | 集群命令行客户端 |
| minikube | v1.39.0 | 集群管理器 |

内核模块与参数（K8S 网络需要）：

```bash
lsmod | grep -E 'br_netfilter|overlay'
```

```text
br_netfilter           32768  0
bridge                421888  1 br_netfilter
overlay               221184  24
```

两个模块都已加载。`br_netfilter` 让桥接流量走 iptables（Service 转发依赖它），`overlay` 是 overlayfs 文件系统（容器镜像分层依赖它）。若缺失需要 `modprobe` 并写入 `/etc/modules-load.d/` 持久化。

必要的 sysctl：

```bash
sysctl net.bridge.bridge-nf-call-iptables net.ipv4.ip_forward
```

```text
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
```

### 5.3 端口规划

宿主机已占用的端口要避开（尤其是 NodePort 段）：

```bash
ss -tlnp | grep -E ':(6443|8080|10250|30000)\b'
```

本机现状：8086（nginx，Archify）、8087/8090（nginx 反代 K8S 应用）、8088（docker-proxy）、8888（python http.server）、3100（Link Admin）、8089（Jenkins）等。Kubernetes 自己要用的端口（6443、10250、10257、10259、2379）在宿主机上都不冲突，因为它们在容器内部。

**NodePort 规划要避开已占端口**，K8S 演示应用用了 30080，问卷系统用了 30088。

---

## 6. 安装实战

### 6.1 第一步：确认本地镜像缓存（决定能否离线安装）

minikube 需要下载节点基础镜像和 K8S 组件镜像。本机 Docker Hub 与 gcr.io 都不通（原因见第 8 章），所以缓存是否完整直接决定成败：

```bash
du -sh /root/.minikube/cache/*
ls -lh /root/.minikube/cache/kic/amd64/
ls -lh /root/.minikube/cache/preloaded-tarball/
```

```text
158M  /root/.minikube/cache/images
1.3G  /root/.minikube/cache/kic
60M   /root/.minikube/cache/linux
348M  /root/.minikube/cache/preloaded-tarball

/root/.minikube/cache/kic/amd64/stable_v0.0.51.tar                  # 节点基础镜像 tarball
/root/.minikube/cache/preloaded-tarball/preloaded-images-k8s-v18-v1.37.0-containerd-overlay2-amd64.tar.lz4
/root/.minikube/cache/images/amd64/registry.cn-hangzhou.aliyuncs.com/google_containers/*
```

缓存里三类东西各有用处：

- `kic/` —— 节点基础镜像（kicbase），没有它就必须从 gcr.io 拉，而 gcr.io 不通
- `preloaded-tarball/` —— 预载的 K8S 组件镜像包，启动时批量导入节点
- `images/` —— 单个组件镜像（apiserver、etcd、coredns 等），从阿里云镜像源下过的

### 6.2 第二步：启动集群

```bash
export KUBECONFIG=/root/.kube/config

minikube start -p minikube \
  --driver=docker --force \
  --container-runtime=containerd \
  --cni=bridge \
  --kubernetes-version=v1.37.0 \
  --image-mirror-country=cn \
  --memory=4096 \
  --cpus=4 \
  --disk-size=30g \
  --extra-config=kubelet.fail-swap-on=false
```

实测输出（首尾）：

```text
* Ubuntu 24.04 上的 minikube v1.39.0
  - KUBECONFIG=/root/.kube/config
! 当提供 --force 参数时，minikube 将跳过各种验证，这可能会导致意外行为
* 根据现有的配置文件使用 docker 驱动程序
* 使用具有 root 权限的 Docker 驱动程序
* 在集群中 "minikube" 启动节点 "minikube" primary control-plane
* 正在拉取基础镜像 v0.0.51 ...
* 正在 containerd 2.3.4 中准备 Kubernetes v1.37.0…
  - kubelet.fail-swap-on=false
* 配置 bridge CNI (Container Networking Interface) ...
* 正在验证 Kubernetes 组件...
  - 正在使用镜像 registry.cn-hangzhou.aliyuncs.com/google_containers/storage-provisioner:v5
* 启用插件： default-storageclass, storage-provisioner
* 完成！kubectl 现在已配置，默认使用"minikube"集群和"default"命名空间
```

### 6.3 参数逐个解释

| 参数 | 含义 | 为什么必须这么写 |
|---|---|---|
| `-p minikube` | profile 名字 | 一个 minikube 可以管多个集群，用 profile 区分 |
| `--driver=docker` | 用 Docker 创建节点容器 | 相比虚拟机驱动，启动快、不占宿主机端口 |
| `--force` | 跳过「不要用 root 运行」的校验 | **以 root 运行时不加会直接退出**：`X 因 DRV_AS_ROOT 错误而退出：docker 驱动不应使用 root 权限。` |
| `--container-runtime=containerd` | 节点内用 containerd | 与本地预载镜像 tarball 的格式（`-containerd-overlay2-`）匹配，才能离线导入；Docker 运行时已逐步被弃用 |
| `--cni=bridge` | 用 minikube 内置的 bridge CNI | 零额外镜像依赖；用 Calico 需要从仓库拉镜像且必须配对 Pod 网段（见配套集群文档第 4 章的故障复盘） |
| `--kubernetes-version=v1.37.0` | 固定 K8S 版本 | 与本地缓存（`cache/linux/amd64/v1.37.0`、预载 tarball）和 kubectl 客户端对齐 |
| `--image-mirror-country=cn` | 组件镜像走阿里云地址 | 只影响 minikube 自己拉组件镜像的地址，**不等于配好了 containerd 镜像源**（见第 8 章） |
| `--memory=4096` / `--cpus=4` | 节点容器的资源上限 | 宿主机可用约 9.9GiB，且上面跑着一批在用服务，给 4GiB/4 核是安全值 |
| `--disk-size=30g` | 节点磁盘上限 | 宿主机余量充足 |
| `--extra-config=kubelet.fail-swap-on=false` | 允许在开启 swap 的机器上跑 kubelet | 宿主机 swap 已用 3.3GiB，关 swap 有 OOM 风险；此参数让 kubelet 容忍 swap（kubelet 默认行为是检测到 swap 开启就拒绝启动） |

启动耗时实测：**从执行到节点 Ready 约 5-6 分钟**（镜像是从本地缓存导入的，瓶颈在镜像导入与组件引导）。别误判为卡死。

### 6.4 日常启停

```bash
# 启动（集群已存在时，profile 里记住了上次的参数，不需要再写一长串）
minikube start -p minikube --force

# 状态
minikube status -p minikube

# 停止（注意看第 10 章坑 5，本机不推荐随手 stop）
minikube stop -p minikube

# 删除（保留 ~/.minikube/cache，下次重建更快）
minikube delete -p minikube
```

`minikube start` 会把上次的参数记在 `/root/.minikube/profiles/minikube/config.json` 里，所以日常启动不用重复那串参数——但 `--force` 每次都要带。

---

## 7. 集群验证

### 7.1 基础状态

```bash
minikube status -p minikube
kubectl config get-contexts
kubectl version
```

```text
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured

CURRENT   NAME       CLUSTER    AUTHINFO   NAMESPACE
*         minikube   minikube   minikube   default

Client Version: v1.37.0
Server Version: v1.37.0
```

### 7.2 节点与组件

```bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
```

```text
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    OS-IMAGE                CONTAINER-RUNTIME
minikube   Ready    control-plane   68s   v1.37.0   192.168.49.2   Debian GNU/Linux 12     containerd://2.3.4

NAMESPACE     NAME                               READY   STATUS    RESTARTS      AGE
kube-system   coredns-6cf5fbd489-qw2hw           1/1     Running   0             77s
kube-system   etcd-minikube                      1/1     Running   0             2m26s
kube-system   kube-apiserver-minikube            1/1     Running   0             2m28s
kube-system   kube-controller-manager-minikube   1/1     Running   3 (108s ago) 2m28s
kube-system   kube-proxy-wst48                   1/1     Running   0             77s
kube-system   kube-scheduler-minikube            1/1     Running   0             2m27s
kube-system   storage-provisioner                1/1     Running   1 (21s ago)  88s
```

每行的含义：

- `etcd-minikube`、`kube-apiserver-minikube`、`kube-scheduler-minikube`、`kube-controller-manager-minikube`：控制面四件套，**静态 Pod**（名字带节点名后缀），由 kubelet 直接管理
- `coredns-*`：集群内 DNS，解析 Service 名字，服务 IP 是 `10.96.0.10`
- `kube-proxy-*`：DaemonSet，负责 Service 转发规则
- `storage-provisioner`：minikube 特有，动态供给 hostPath 类型的 PV，让 PVC 能自动 Bound

**正常现象**：`kube-controller-manager` 显示重启 3 次，`kube-scheduler` 日志里可能短暂出现 `Failed to watch ... is forbidden: User "system:kube-scheduler" cannot list ...`。这是引导期的正常抖动（领导选举与缓存同步），几十秒后自行消失，日志随后出现 `"Caches are synced"`。只要节点能到 Ready 且组件最终 Running 就无需处理。

### 7.3 集群拓扑参数

```bash
kubectl get node minikube -o jsonpath='{.spec.podCIDR}{"\n"}{.status.capacity}{"\n"}'
kubectl get pod -n kube-system kube-apiserver-minikube -o jsonpath='{.spec.containers[0].command}' | tr ',' '\n' | grep service-cluster-ip-range
```

```text
10.244.0.0/24                    # Pod 网段
{"cpu":"8","memory":"20170620Ki","ephemeral-storage":"982240026624","pods":"110"}
"--service-cluster-ip-range=10.96.0.0/12"      # Service 网段
```

### 7.4 功能冒烟测试

```bash
# 跑一个 Pod
kubectl run smoke --image=alpine:3.20 --restart=Never --command -- echo hello
kubectl get pod smoke

# 看指标（需要 metrics-server，见下）
kubectl top nodes
```

```text
NAME    READY   STATUS      RESTARTS   AGE
smoke   0/1     Completed   0          20s

NAME       CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
minikube   150m         1%       824Mi           4%
```

启用常用插件：

```bash
minikube addons enable dashboard -p minikube
minikube dashboard -p minikube --url          # 会前台阻塞，Ctrl+C 结束
```

---

## 8. 容器镜像源方案

这一节是本机环境特有的关键问题：**镜像拉不动，Pod 就永远起不来**。

### 8.1 三个仓库的可达性实测

```bash
for u in registry-1.docker.io registry.k8s.io gcr.io registry.cn-hangzhou.aliyuncs.com \
         docker.m.daocloud.io docker.1ms.run hub.rat.dev quay.io; do
  printf '%-40s ' "$u"
  curl -4 -s -o /dev/null -w 'HTTP %{http_code}\n' "https://$u/v2/" || echo FAIL
done
```

```text
registry-1.docker.io              FAIL（IPv4/IPv6 均超时）
registry.k8s.io                   HTTP 401（入口可达，但见下）
gcr.io                            FAIL
registry.cn-hangzhou.aliyuncs.com HTTP 401（可用）
docker.m.daocloud.io              HTTP 401（可用）
docker.1ms.run                    HTTP 401（可用）
hub.rat.dev                       HTTP 302（可用）
quay.io                           HTTP 401（可用）
```

两个值得记下来的细节：

**Docker Hub 是 DNS 污染 + 连接阻断双重夹击**

```bash
getent ahostsv4 registry-1.docker.io
curl -4 -sI -o /dev/null -w '%{http_code}\n' https://registry-1.docker.io/v2/     # FAIL
curl -6 -sI -o /dev/null -w '%{http_code}\n' https://registry-1.docker.io/v2/     # FAIL
curl -4 -sI -o /dev/null -w '%{http_code}\n' https://auth.docker.io/token        # FAIL（连鉴权端点都不通）
```

```text
registry-1.docker.io  A: 116.89.243.8      # 污染地址，不是真实 IP
```

本机有 IPv6 出口（`2408:...` 全局地址 + 默认路由），但 v4/v6 都不通，所以不存在「强制 IPv4 就能通」的可能，必须走镜像源。

**registry.k8s.io 是「入口通、后端封」**

```bash
getent ahostsv4 registry.k8s.io                                   # 34.96.108.209
curl -4 -sI -o /dev/null -w '%{http_code}\n' https://registry.k8s.io/v2/    # 401，看起来可用
curl -sI https://registry.k8s.io/v2/metrics-server/metrics-server/manifests/v0.9.0
```

```text
HTTP 307 -> https://europe-west3-docker.pkg.dev/v2/k8s-artifacts-prod/images/metrics-server/...

# 而所有 *.pkg.dev 都不通：
us-east1-docker.pkg.dev          FAIL
us-west1-docker.pkg.dev          FAIL
asia-east1-docker.pkg.dev        FAIL
europe-west1-docker.pkg.dev      FAIL
```

DNS 能解析（`europe-west3-docker.pkg.dev → 74.125.142.82`），但 TCP 443 超时——属于网络层阻断，改 `/etc/hosts` 无效。

### 8.2 配置 docker.io 镜像源（containerd certs.d 方式）

containerd 2.x 支持按「仓库主机名」在 `/etc/containerd/certs.d/<host>/hosts.toml` 配置镜像源。相比老式 `config.toml` 的 `registry.mirrors`，**这种方式改完即时生效，不需要重启 containerd**。

创建 `/etc/containerd/certs.d/docker.io/hosts.toml`（在 minikube 节点内）：

```toml
server = "https://registry-1.docker.io"

[host."https://docker.m.daocloud.io"]
  capabilities = ["pull", "resolve"]
  skip_verify = true

[host."https://docker.1ms.run"]
  capabilities = ["pull", "resolve"]
  skip_verify = true

[host."https://hub.rat.dev"]
  capabilities = ["pull", "resolve"]
  skip_verify = true
```

写入方式（**必须用 minikube cp，不要用管道喂 stdin**，原因见坑 6）：

```bash
# 宿主机上准备文件后传入
minikube ssh -p minikube -- 'sudo mkdir -p /etc/containerd/certs.d/docker.io'
minikube cp ./hosts.docker.io.toml minikube:/tmp/hosts.toml
minikube ssh -p minikube -- 'sudo install -m 0644 -o root -g root /tmp/hosts.toml \
  /etc/containerd/certs.d/docker.io/hosts.toml'

# 回读校验（以字节数为准，不要只看命令有没有报错）
minikube ssh -p minikube -- 'sudo wc -c /etc/containerd/certs.d/docker.io/hosts.toml'
# 316

# 实测拉取
minikube ssh -p minikube -- 'sudo crictl pull docker.io/library/alpine:3.20'
```

验证成功的证据是 kubelet 拉镜像时走的镜像源（Redis 23.8 秒拉完）：

```text
Normal  Pulling  91s  kubelet  spec.containers{redis}: Pulling image "redis:7.4-alpine"
Normal  Pulled   67s  kubelet  spec.containers{redis}: Successfully pulled image "redis:7.4-alpine" in 23.826s
```

### 8.3 registry.k8s.io 为什么配不了通用镜像源

结论：**本机没有可用的 registry.k8s.io 通用镜像源**。原因是 containerd 的镜像转发不能改写镜像路径结构，而各镜像站的路径约定不同：

| 尝试 | 结果 |
|---|---|
| 阿里云 `google_containers` 作为镜像 | 路径结构不兼容：registry.k8s.io 用 `<project>/<image>`（如 `coredns/coredns`），阿里云是扁平 `<image>`（如 `coredns`）；且 metrics-server 这类第三方镜像阿里云没有 |
| DaoCloud `k8s-gcr.m.daocloud.io` 作为镜像 | containerd 会带 `?ns=registry.k8s.io` 参数，被拒：`unexpected status from HEAD request ... : 403 Forbidden` |
| DaoCloud 通用代理 `m.daocloud.io/registry.k8s.io/...` | HTTP 403 |

实际影响与对策：

- **K8S 官方核心镜像**（apiserver、etcd、coredns、pause）：minikube 的 `--image-mirror-country=cn` 会用阿里云地址改写，或直接命中本地预载缓存，开箱即用
- **托管在 registry.k8s.io 上的第三方镜像**（如 metrics-server）：用「离线导入法」——从可达的镜像站拉下来，在节点内重打成官方引用的标签

```bash
# 1) 从可达镜像站拉取（实测成功，23.3MB）
minikube ssh -p minikube -- 'sudo crictl pull k8s-gcr.m.daocloud.io/metrics-server/metrics-server:v0.9.0'

# 2) 在节点内重打成官方引用
minikube ssh -p minikube -- 'sudo ctr -n k8s.io images tag \
  k8s-gcr.m.daocloud.io/metrics-server/metrics-server:v0.9.0 \
  registry.k8s.io/metrics-server/metrics-server:v0.9.0'
```

`k8s-gcr.m.daocloud.io` 对官方镜像路径的兼容性也验证过（digest 与本地已有同版本镜像一致，说明返回的是同一份内容）：

```text
$ minikube ssh -- 'sudo crictl pull k8s-gcr.m.daocloud.io/coredns/coredns:v1.14.6'
Image is up to date for sha256:520212b8b0fcd9309d7362d592f513b72880fa5a4e9e8b91442e7ee3b622c6a9
$ minikube ssh -- 'sudo crictl pull k8s-gcr.m.daocloud.io/kube-apiserver:v1.37.0'
Image is up to date for sha256:bec5f0e1e2eeb613b139d1f11f4d3d651ace46da25fd6c578e415fb9e911b9cf
```

### 8.4 镜像源配置的持久化边界

| 配置 | `minikube stop` 后 start | `minikube delete` 后重建 |
|---|---|---|
| 节点内 `/etc/containerd/certs.d/*` | 保留（实测确认） | 丢失，需重新执行配置脚本 |
| 节点内已导入的镜像 | 保留 | 丢失，需重新导入 |
| kubeconfig / 集群数据 | 保留 | 丢失 |

所以重建后的标准动作是跑一遍配置脚本把镜像源补回来。

---

## 9. 应用场景实战

### 场景一：本地开发环境的「准生产」验证

**背景**：项目最终要部署到生产 K8S 集群（或客户环境），但直接在生产上试错成本高。本地起一套 minikube，把清单（Deployment/Service/ConfigMap/Secret/PVC/HPA）先跑通，再原样迁到生产。

**做法**：

```bash
# 本地起集群
minikube start -p minikube --driver=docker --force \
  --container-runtime=containerd --cni=bridge \
  --kubernetes-version=v1.37.0 --memory=4096 --cpus=4

# 用与生产同样的清单部署（唯一差别是镜像来源：本地导入 vs 私有仓库）
kubectl apply -f k8s/

# 本地验证：探针是否合理、启动顺序有没有问题、资源 requests/limits 够不够、
# 滚动更新是否零中断、HPA 能不能读到指标
kubectl rollout status deploy/backend -n questionnaire
kubectl get hpa -n questionnaire
kubectl top pods -n questionnaire
```

**关键收益**：清单是同一份，本地验证过的东西（探针参数、依赖启动顺序、JVM 内存参数）在生产不会重踩。本次实测正是靠这一步发现了「MySQL 首次初始化 6 分钟，被 livenessProbe 杀掉」的问题——如果在生产上发现，就是一次数据目录损坏的故障。

**注意**：本地集群的存储（hostPath）、网络（bridge CNI）、副本数（单节点）与生产不同，这几处清单要按环境区分（用 Kustomize 的 overlay 或 Helm 的 values 分环境更规范）。

### 场景二：多组件联调与 K8S 能力学习

**背景**：要理解 Service 发现、ConfigMap 注入、StatefulSet 存储、探针、HPA 这些机制，光看文档记不住，需要一个可以随便折腾、删了不心疼的环境。

**做法**：用 minikube 把一整套「前端 + 后端 + 数据库 + 缓存」跑起来，然后逐项做实验：

```bash
# 实验 1：Service 名字解析（把 Pod 当调试终端用）
kubectl run dnstest -n questionnaire --image=busybox:1.37 --restart=Never --command -- \
  sh -c 'nslookup backend; nslookup mysql; nslookup redis'
kubectl logs dnstest -n questionnaire

# 实验 2：改 ConfigMap 看应用是否感知（env 注入不会热更新，必须重启）
kubectl edit configmap questionnaire-config -n questionnaire
kubectl rollout restart deploy/backend -n questionnaire

# 实验 3：删掉数据库 Pod，看 StatefulSet 是否重建并挂回同一个 PVC
kubectl delete pod mysql-0 -n questionnaire
kubectl get pod mysql-0 -n questionnaire -w          # 名字不变、PVC 不变

# 实验 4：模拟故障——把 probe 端口改错看 Pod 是否被摘出 Service
kubectl get endpoints backend -n questionnaire

# 实验 5：压测触发 HPA 扩容
kubectl run loadtest -n questionnaire --image=busybox:1.37 --restart=Never -- \
  sh -c 'while true; do wget -q -O /dev/null http://backend:8081/; done'
kubectl get hpa -n questionnaire -w
```

**关键收益**：K8S 的核心机制都能在几分钟内亲手验证一遍。删掉整个命名空间重来也只要几分钟（`kubectl delete namespace questionnaire` + 重新 apply）。

---

## 10. 最佳实践与踩坑记录

### 最佳实践

1. **以 root 运行 minikube 必须带 `--force`**，建议把启动命令写进脚本（`/opt/project-work/k8s/scripts/start-cluster.sh`），避免每次手敲一长串参数。
2. **节点资源要显式限制**（`--memory`/`--cpus`）。不限制的话 minikube 会试着吃满宿主机（本机实测旧集群的节点声明了 8 核 19.2GiB），跟宿主机上其他服务抢资源。
3. **不要用 `minikube delete --all --purge`**，`--purge` 会删掉 `~/.minikube` 缓存；在本机网络环境下，那些缓存（kicbase、预载镜像）几乎无法重新下载。
4. **镜像源配置写入脚本并幂等**：`minikube delete` 之后必须重跑，所以要有脚本而不是手敲。
5. **删集群前先归档现场**：节点 describe、Pod 列表、事件、关键组件日志，排障和复盘都用得上。命令：

```bash
mkdir -p /root/k8s-backup/evidence
kubectl get nodes -o wide > /root/k8s-backup/evidence/nodes.txt
kubectl get pods -A -o wide > /root/k8s-backup/evidence/pods.txt
kubectl describe node minikube > /root/k8s-backup/evidence/node-describe.txt
kubectl get events -A --sort-by=.lastTimestamp > /root/k8s-backup/evidence/events.txt
```

6. **业务负载全部声明式管理**：所有东西都写成 YAML 提交进版本库，集群当作「可以随时丢弃重建」的临时资源。本次问卷系统的全部清单在 `k8s/`，重建只需 `kubectl apply -f k8s/`。
7. **命名空间按项目隔离**：不同项目用不同 Namespace，便于资源配额（ResourceQuota）和权限（RBAC）划分，也避免同名 Service 冲突。

### 踩坑记录

**坑 1：以 root 运行 `minikube start` 直接退出**

结论：报 `X 因 DRV_AS_ROOT 错误而退出：docker 驱动不应使用 root 权限。`

原因：docker 驱动检测到当前是 root 用户，出于安全考虑拒绝执行（minikube 认为 root 跑集群会让容器内文件归 root 所有，容易出权限问题）。

解法：加 `--force`。但这只是跳过校验，实际用 root 跑时，后续 `minikube delete` 之类的操作 minikube 也会提示「要删除此 root 拥有的集群，请运行：sudo minikube delete」。

**坑 2：加了 `--image-mirror-country=cn` 以为镜像问题就解决了**

结论：`--image-mirror-country=cn` 只把 sandbox（pause）镜像改写成阿里云地址，**并没有给 containerd 配置 docker.io 镜像源**。跑业务镜像照样 `ErrImagePull`。

原因：该参数的作用范围是 minikube 自己拉「K8S 组件镜像」时使用的仓库地址，不是节点内容器运行时的镜像源配置。

解法：单独配置 containerd 的 `certs.d/docker.io/hosts.toml`（见 8.2）。另一个常见误解是 `minikube start --registry-mirror=`，它的帮助文本明确写着「传递给 Docker 守护进程的注册表镜像」，**只对 `--container-runtime=docker` 生效，对 containerd 无效**。

**坑 3：本地导入的镜像 Pod 起不来（ImagePullBackOff）**

结论：`minikube image load` 导入的镜像不在任何仓库里，如果 Pod 的 `imagePullPolicy` 是 `Always`，kubelet 会去 Docker Hub 拉，必然失败。

原因：镜像引用没有仓库地址（本地构建的 `myapp:latest`），kubelet 只能按默认规则拼成 `docker.io/library/myapp:latest` 去拉。

解法：本地导入的镜像写 `imagePullPolicy: IfNotPresent`（或 `Never`）。判断默认策略的规则是：tag 为 `latest` 或省略 tag 时默认 `Always`，其他 tag 默认 `IfNotPresent`——所以**用 `latest` 更容易踩坑**，建议同时显式声明策略。

**坑 4：节点声明的容量远大于容器真实上限**

结论：`kubectl get node minikube` 显示 8 核 / 19.2GiB，而节点容器的 cgroup 限制只有 4 核 / 4GiB。调度器的百分比是拿虚高的分母算的。

原因：kubelet 从节点内 `/proc/meminfo`、`/proc/cpuinfo` 读取机器信息，在容器里读到的是宿主机的数值（除非用 lxcfs 之类的方案做隔离）。

影响：调度器可能把总内存请求超过 4GiB 的 Pod 放进来，然后被 cgroup OOM Kill。判断真实余量要看 `docker stats minikube` 或 `docker inspect minikube --format '{{.HostConfig.Memory}}'`。

解法：控制**所有 Pod 的 memory requests 总和**不超过容器上限的 75% 左右；需要更精确时用 `--extra-config=kubelet.system-reserved=memory=500Mi --extra-config=kubelet.kube-reserved=memory=500Mi` 让调度器看到更真实的可用量。

**坑 5：`minikube stop` 之后 start，containerd 快照损坏，新容器全部起不来**

结论：节点仍 `Ready`、控制面正常，但所有新 Pod 卡在 `ContainerCreating` / `PodInitializing`，kubelet 日志反复报：

```text
failed to create containerd container: failed to rename:
  rename /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/new-1727559772
       /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/50: file exists
```

原因：containerd 的 overlayfs snapshotter 元数据与外层目录失去同步（快照目录的 `fs` 子目录已不存在但目录本身还在，新快照分配到该 ID 时 rename 冲突）。深层原因是两层 overlayfs 叠加：宿主机 Docker 的 overlayfs 之上，节点内的 containerd 再跑一层。

解法（已实测）：`minikube delete -p minikube` + 一键重建脚本（重新配置镜像源、导入镜像、apply 清单）。**预防**：不要随手 `minikube stop`，长期保留运行（约 1GB 内存开销）；确需停机时先优雅停组件再停容器：

```bash
minikube ssh -p minikube -- 'sudo systemctl stop kubelet && sudo systemctl stop containerd && sync'
docker stop -t 120 minikube
```

**坑 6：用管道把文件内容喂给 `minikube ssh` 会永久挂起**

结论：`cat <<EOF | minikube ssh -- 'sudo tee /path/file'` 这类写法不会返回，命令卡在那里；有时表面「成功」但目标文件是 0 字节。

原因：`minikube ssh` 分配了 PTY，远端命令读 stdin 时拿不到 EOF，一直等输入；而输出重定向又让人误以为写入成功。

解法：往节点内写文件一律用 `minikube cp` + `sudo install`，并用 `wc -c` 回读校验：

```bash
minikube cp ./hosts.toml minikube:/tmp/hosts.toml
minikube ssh -p minikube -- 'sudo install -m 0644 -o root -g root /tmp/hosts.toml /etc/containerd/certs.d/docker.io/hosts.toml'
minikube ssh -p minikube -- 'sudo wc -c /etc/containerd/certs.d/docker.io/hosts.toml'
```

**坑 7：`set -euo pipefail` 的脚本里把 `minikube ssh` 管道给 `head` 会误报失败**

结论：脚本以退出码 141 结束（128 + 13，SIGPIPE）。

原因：`head` 读够行数就退出并关闭管道，`ssh` 继续写剩余数据时收到 SIGPIPE；在 `pipefail` 下整个管道被判为失败。

解法：先完整取回再截断：

```bash
CRI_IMAGES="$(minikube ssh -p minikube -- 'sudo crictl images')"
printf '%s\n' "$CRI_IMAGES" | head -20
```

**坑 8：NodePort 从局域网访问不通（不是故障）**

结论：NodePort 绑定在节点 IP（minikube 网桥 `192.168.49.2`）上，`192.168.1.167:30088`、`100.71.112.119:30088` 全部不可达。

原因：`192.168.49.2` 是宿主机上的网桥地址，只有宿主机能路由过去。

解法（三种）：宿主机 nginx 反代（推荐，与现有站点风格一致）、`kubectl port-forward --address 0.0.0.0`（临时）、`minikube tunnel`（给 LoadBalancer Service 用，但会写宿主机路由，与多个 Docker 网桥容易冲突）。

---

## 11. 参考链接

- Kubernetes 官方文档：https://kubernetes.io/docs/
- minikube 官方文档：https://minikube.sigs.k8s.io/docs/
- containerd 镜像源配置（certs.d）：https://github.com/containerd/containerd/blob/main/docs/hosts.md
- CNI 规范：https://www.cni.dev/docs/spec/
- 配套文档：
  - `/opt/project-work/Kubernetes-K8S-单节点集群部署文档.md`（本机集群的完整部署与排错记录）
  - `[[kubernetes-springboot-vue-deploy]]`（SpringBoot + Vue 项目部署到 K8S）
