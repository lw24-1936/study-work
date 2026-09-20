---
title: Kafka 使用介绍：大数据场景下的定位、组件与核心用法
created: 2026-09-21
updated: 2026-09-21
type: concept
tags: [kafka, kafka-kraft, message-queue, streaming, big-data, data-pipeline, producer, consumer, kafka-connect, kafka-streams]
---

# Kafka 使用介绍：大数据场景下的定位、组件与核心用法

整理日期：2026-09-21

> 状态：已完成

本文是《Kafka完整教程》的提炼版，面向两类读者：刚开始接触 Kafka、需要先搞清「它是什么、由哪些组件构成、在大数据链路里怎么用」的人；以及已经用过 Kafka、想快速把组件与概念对上一遍的人。全文以介绍为主，不含代码与命令，所有涉及的版本口径、默认值、行为特征都以 Kafka 4.1.2（KRaft 模式）的实测为准，需要动手时照着同目录的完整教程做即可。

需要强调的一句话：Kafka 本身不是数据库、不是数据湖，也不是计算引擎。它是一个**以日志为中心的传输与缓冲层**，大数据体系里绝大多数实时链路都以它作为「数据总线」。

## 目录

- [1. Kafka 是什么](#1-kafka-是什么)
- [2. Kafka 在大数据体系中的位置](#2-kafka-在大数据体系中的位置)
- [3. 核心概念与组件地图](#3-核心概念与组件地图)
- [4. 服务端组件](#4-服务端组件)
- [5. 客户端组件](#5-客户端组件)
- [6. 生态组件](#6-生态组件)
- [7. 数据是怎么流动的](#7-数据是怎么流动的)
- [8. 大数据里的典型用法](#8-大数据里的典型用法)
- [9. 部署形态与运行方式](#9-部署形态与运行方式)
- [10. 可靠性、顺序与消费语义](#10-可靠性顺序与消费语义)
- [11. 监控与运维](#11-监控与运维)
- [12. 安全](#12-安全)
- [13. 与其它消息系统的对比选型](#13-与其它消息系统的对比选型)
- [14. 常见误区](#14-常见误区)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)
- [相关文档](#相关文档)

## 1. Kafka 是什么

### 1.1 一句话定义

Kafka 是一个分布式、分区、多副本的提交日志（commit log）。它同时扮演三个角色：

```text
消息队列      生产者写、消费者读，解耦上下游、削峰填谷
存储系统      消息按保留策略落盘（默认 7 天），可以被重复读取、可以被回放
流处理平台    与 Kafka Streams / Flink / Spark Structured Streaming 配合做实时计算
```

「提交日志」这个词是关键：Kafka 的核心数据结构就是把消息**顺序追加**到一个只增不减的日志文件里，每条消息在分区内有一个递增编号（offset）。读写都围绕这个结构展开，Kafka 的高吞吐、可重放、多消费组互不干扰，全部由「顺序追加 + 位移由消费者自己维护」这两点派生出来。

### 1.2 它与传统消息队列的三个差别

```text
1. 消息不因「被消费」而删除
   RabbitMQ 一类是「投递-确认-删除」，Kafka 是「写入-落盘-按保留策略删除」。
   消费者读到哪儿由消费者自己提交位移记录，broker 不关心谁读过了。

2. 拉模型而不是推模型
   消费者按自己的节奏 poll 一批消息，不会被 broker 压垮；积压时表现为 LAG，而不是 broker 阻塞。

3. 消费进度是「每个消费组各一份」
   同一份数据可以被多个消费组分别消费（一个组落数仓、一个组算指标），互不影响。
```

这三点带来的直接能力是：**回放**（用同一个消费组把位移重置到某个时间点重读历史）、**多路复用**（一份数据供多个下游）、**扩容简单**（加消费者即可，Kafka 自动重新分配分区）。

### 1.3 它解决的是什么问题

传统链路的痛点与 Kafka 的定位是一一对应的：

| 传统做法 | 问题 | Kafka 的做法 |
|---|---|---|
| 用数据库表当队列 | 行锁争用、轮询压力大、历史数据一删就无法重放 | 追加写日志，读写无锁争用，保留期内随时可重放 |
| 上游直接 HTTP 调下游 | 下游抖动直接拖垮上游，没有缓冲，流量尖峰即故障 | 上游写入成功即返回（毫秒级），尖峰被磁盘缓冲吸收 |
| 点对点集成 N 个下游 | 每加一个下游就要改上游代码 | 上游只写主题，下游各自订阅，新增下游不动上游 |
| 用 Redis List 当队列 | 内存成本高、无副本保证、宕机容易丢数据 | 多副本 + ISR 保证不丢，磁盘成本远低于内存 |

一句话概括它的定位：**上游只管投递，下游按自己的节奏消费**。

### 1.4 什么时候不该用它

- 请求-响应式的同步调用：直接用 RPC（HTTP/gRPC）更简单，Kafka 不适合当 RPC 替代品。
- 需要严格的全局有序：有序性只在分区内成立，要全局有序就只能退化到单分区，吞吐上不去。
- 消息量极小（一天几百条）：引入 Kafka 的部署与运维成本远超收益，数据库表 + 定时任务更实在。
- 需要复杂路由与定时投递：按 routing key 分发、延迟队列、优先级队列这些是 RabbitMQ 的强项。
- 浏览器/移动端直连：不要把 Kafka 暴露给客户端，必须经过后端服务或网关。

## 2. Kafka 在大数据体系中的位置

### 2.1 数据分层里的传输层

把大数据链路按「采集 → 传输 → 计算 → 存储与服务」分层，Kafka 稳定地占据传输层：

```text
采集层      Filebeat / Fluent Bit / Vector / Logstash / Flume
            Debezium / Canal / Flink CDC（数据库变更捕获）
                 │
                 ▼
传输层      ┌─────────────── Kafka ───────────────┐
            │ 主题按业务域划分，多消费组并行消费     │
            └─────────────────────────────────────┘
                 │                    │
                 ▼                    ▼
计算层      Flink / Spark Structured Streaming / Kafka Streams
                 │                    │
                 ▼                    ▼
存储与服务层 Hive / HDFS / Iceberg / Hudi、ClickHouse / Doris / StarRocks / ES
```

### 2.2 它在链路里承担的四个角色

| 角色 | 说明 | 典型表现 |
|---|---|---|
| 数据总线 | 所有上游事件的统一入口 | ODS 层的实时入口主题，命名带业务域前缀 |
| 缓冲与解耦 | 下游（数仓、检索、风控）故障时不影响上游 | 上游写入速率与下游处理速率解耦，用 LAG 度量差距 |
| 流批同源 | 同一份数据既供实时计算，也供离线回灌 | 实时链路走 Flink，T+1 链路用消费组从头重读 |
| 变更管道 | 承接 CDC 数据，做增量入湖 | MySQL binlog → Kafka → 数仓/湖表，主键做 key 保序 |

### 2.3 与周边大数据组件的边界

这是最容易混淆的一组边界，写清楚能省很多沟通成本：

- **Kafka 不是数据湖**：它按保留策略删数据（默认 7 天），没有分区裁剪、没有列式存储、不便宜。要长期保存原始数据，落 HDFS/对象存储（Iceberg、Hudi、Paimon 这类表格式）。
- **Kafka 不负责计算**：窗口聚合、join、CEP、状态管理是 Flink/Spark/Streams 的事，Kafka 只负责把数据搬到位。
- **Kafka 不是数据库**：不能按任意条件查询、不能更新单条消息、不能事务性关联多张表。它提供的是「按 key 还原最新状态」的能力（压实主题），仅此而已。
- **Kafka 不是 ETL 工具的替代品**：批量全量同步、跨库字段映射、复杂转换用 DataX/SeaTunnel/NiFi 更合适；Kafka Connect 擅长的是「持续的、配置化的」增量搬运。

### 2.4 在 Lambda 与 Kappa 架构里的位置

- Lambda 架构：实时链路（Kafka + Flink）与离线链路（Kafka → 落 HDFS → Hive/Spark）并行，两者互补。Kafka 同时是两条链路的入口，这是企业里最常见、也最实用的形态。
- Kappa 架构：只保留流式一条链路，历史数据通过「重放 Kafka 主题（保留期足够长）或读取下游湖表」得到。它对 Kafka 的保留时长与分层存储能力要求更高，落地成本也更高。
- 现实中多数团队走的是「Lambda 起步、逐步往 Kappa 收」的路线，Kafka 在两种形态里的位置都不变。

## 3. 核心概念与组件地图

### 3.1 概念速查

| 概念 | 含义 | 工程含义 |
|---|---|---|
| Broker | 一个 Kafka 服务进程（一个节点） | 3 节点是最小生产规模，可容忍 1 台宕机 |
| Topic | 逻辑上的消息类别 | 命名规范 `{域}.{实体}.{事件}`，环境前缀放最前 |
| Partition | 主题的物理分片，并行与有序的基本单位 | 分区数决定消费并发上限，且只能增不能减 |
| Replica | 分区的副本，分布在不同 broker | 副本因子 3 + min.insync.replicas 2 是常用组合 |
| Leader | 每个分区唯一对外提供读写的副本 | 生产与消费都只找 Leader |
| Follower | 只从 Leader 同步、不对外服务的副本 | 落后太多会被踢出 ISR |
| ISR | In-Sync Replicas，与 Leader 保持同步的副本集合 | ISR 收缩是核心告警信号 |
| ELR | Eligible Leader Replicas，ISR 之外「可安全当选」的副本 | Kafka 4.0 引入（KIP-966），4.1 起新集群默认启用 |
| Offset | 消息在分区内的递增编号 | 消费者提交的是「下一条要读的位移」 |
| LEO | Log End Offset，分区最新消息的下一个位置 | 判断副本落后程度的基准 |
| HW | High Watermark，已同步到所有 ISR 的位移分界 | 消费者只能读到 HW 之前的消息 |
| Consumer Group | 消费组，组内分区互斥、组间广播 | 同组消费者数超过分区数时多出来的会空闲 |
| Segment | 分区目录下的日志文件（默认 1GB 一个） | 过期删除的最小单位是 segment，不是单条消息 |
| Controller | KRaft 元数据仲裁选出的元数据管理节点 | 负责分区分配、Leader 选举、主题与 ACL 变更 |
| KRaft | Kafka 自带的 Raft 实现，替代 ZooKeeper | 4.0 起是唯一的元数据方案 |

### 3.2 组件地图

按「服务端 / 客户端 / 生态 / 运维」四类把 Kafka 世界里会遇到的组件列全，后面第 4~6 章逐个介绍：

```text
服务端组件
    Broker、Controller、KRaft Quorum（voter / observer）
    Topic / Partition / Replica / Segment 与索引文件
    内部主题：__cluster_metadata、__consumer_offsets、__transaction_state
    Group Coordinator、Transaction Coordinator、日志清理线程

客户端组件
    Producer（含序列化器、分区器、拦截器、累加器与 Sender 线程）
    Consumer（含位移提交、Rebalance 监听器）
    Consumer Group、AdminClient
    Spring Kafka（KafkaTemplate / @KafkaListener / 错误处理与死信）

生态组件
    Kafka Connect（Source / Sink Connector、SMT）
    Kafka Streams、ksqlDB
    Schema Registry、MirrorMaker 2、REST Proxy
    Debezium / Canal / Flink CDC、Flink / Spark Structured Streaming
    Filebeat / Fluent Bit / Vector（采集端）

运维与可观测组件
    发行包 bin/ 下的命令行工具族
    JMX 与 JmxTool、Prometheus JMX Exporter / kafka-exporter、Grafana
    Docker / Docker Compose、systemd、Kubernetes Operator、托管云服务
```

### 3.3 三个必须先建立的直觉

```text
1. 分区是并行与有序的边界
   分区内严格有序（按写入顺序），跨分区无序。要「同一实体的消息有序」就按实体 ID 做 key。

2. 服务器只保证「至少一次」，不保证「只处理一次」
   消息可能重复投递（重试、Rebalance、位移回退），消费端必须能处理重复与乱序。

3. 元数据也是日志
   KRaft 下主题、分区、副本、ACL 这些元数据本身存成一条日志（__cluster_metadata），
   通过 Raft 复制——理解了这点，controller 的很多行为就顺理成章了。
```

## 4. 服务端组件

### 4.1 Broker

Broker 就是一个 Kafka 服务进程，也是「一个节点」的代名词。它承担的全部工作是：接收生产者的写入、把消息顺序追加到分区日志、把数据复制给其它副本、响应消费者的拉取请求、把位移与事务状态记到内部主题。

一个 broker 上需要理解的几件事：

- **监听器与端口**：broker 会开多个监听器。客户端通道通常是 9092（`PLAINTEXT`，生产上换成 `SASL_SSL`），KRaft 的元数据复制走另一个端口（容器部署里常见 9093，协议是 `CONTROLLER`）。云上还常见 `INTERNAL` / `EXTERNAL` 双监听器，分别面向内网与外部客户端。
- **advertised.listeners 是通告地址**：客户端 bootstrap 连上后，broker 会告诉它「你应该用这个地址来找我」。这个值写错（比如容器内通告了 localhost、云上通告了内网 IP），症状是「第一次能连上、之后全部连不上」，是新手第一大坑。
- **性能来源**：顺序写磁盘、操作系统页缓存（page cache）、零拷贝（sendfile）、批量发送与压缩共同构成高吞吐。堆内存反而不需要大（生产经验 6~8GB 足够），因为数据主要走页缓存。
- **关键资源是文件句柄与磁盘**：segment 文件、索引文件与每个连接都占 fd，`ulimit -n` 一般不低于 100000；数据盘建议 SSD/NVMe，多块盘配多个 `log.dirs`（Kafka 会轮流写入），禁用 NFS。
- **节点身份存在数据目录里**：`meta.properties` 记录 `cluster.id` 与 `node.id`，所以「数据目录换了」等于「换了一个节点」，不能随便把别的节点的目录拷过来。

### 4.2 Controller

Controller 是集群里的「元数据管理者」，不负责存消息，负责：主题的创建与删除、分区的分配与副本布局、Leader 选举、动态配置与 ACL 变更、broker 上下线的处理。任何一个分区 Leader 挂了，都是 controller 从 ISR（必要时 ELR）里挑一个新 Leader。

KRaft 时代一个容易被误解的点：**controller 不是某个固定节点，而是一个角色**——多个 controller 节点用 Raft 选出 leader，只有那个 leader 在干活（4.1.2 里体现为 `kafka-metadata-quorum` 的 `LeaderId`）。生产上的建议是让 controller 与 broker 分角色部署，把元数据负载与数据负载隔开。

### 4.3 KRaft Quorum

KRaft（Kafka Raft）是 Kafka 自带的元数据一致性协议，4.0 起彻底取代 ZooKeeper。要理解的要点：

```text
角色          controller 节点分 voter（有投票权）与 observer（只跟随）。
              broker 在 KRaft 里是 observer 角色——它只订阅元数据变更，不参与仲裁。

多数派        controller 数量必须是奇数（3 或 5），Raft 需要多数派才能选出 leader。
              两个 controller 的「多数派」是 2，容错能力反而比 1 个还差，所以只推荐 1（开发）或 3/5（生产）。

元数据日志    集群元数据存在 __cluster_metadata 主题里，落到每个节点的数据目录，
              由 controller 之间用 Raft 复制。主题数多、分区数多的集群，这份日志也不小。

部署形态      combined（process.roles=broker,controller）：单机开发、中小规模，省机器
              分离（broker 与 controller 各自独立）：生产推荐

排障入口      kafka-metadata-quorum 命令能看 quorum 状态：当前 leader、high watermark、
              最大 follower 落后量、voter 与 observer 列表。
```

一个实测出来的经验（对搭建集群的人很重要）：官方镜像的「自动格式化 + 静态 `controller.quorum.voters`」在多 voter 场景下容易选不出 leader（表现为 epoch 持续递增、broker 最终以「unable to register with the controller quorum」退出）；动态 quorum（KIP-853）又需要用 `kafka-storage` 显式给出初始 controller 集合，不能靠镜像自动格式化。可行且简单的拓扑是 **1 个 controller-only 节点 + N 个 broker-only 节点**（开发/演示），生产则按官方分角色部署或使用托管服务。

### 4.4 ZooKeeper

ZooKeeper 是 Kafka 3.x 及之前的外部依赖，承担「存元数据 + 选 controller」两件事：主题配置、ACL、controller 选举、broker 成员关系都放在 ZK 的 ZNode 里，集群因此多了一套需要独立运维的系统（还要防止 ZK 与 Kafka 的会话超时互相放大问题）。

4.0 起 ZooKeeper 被整体删除，所有 `--zookeeper` 参数失效，命令行统一用 `--bootstrap-server`；升级路径必须是 **3.x（ZK 模式）→ 3.9（KRaft 迁移版本）→ 4.x**，不能直接跳。现在读到的老教程、老脚本里凡是有 `localhost:2181` 的，都属于 ZooKeeper 时代。

### 4.5 Topic 与 Partition

Topic 是逻辑上的消息类别（建议按 `{域}.{实体}.{事件}` 命名，如 `order.order.created`），Partition 是它的物理分片——每个分区在磁盘上就是一个目录，目录里是一串日志文件。

围绕分区需要记住三条规则：

```text
1. 并发上限 = 分区数
   同一消费组里，一个分区同时只能被一个消费者消费；消费者数超过分区数时多出来的会空转。

2. 有序性只在分区内成立
   需要「同一订单的事件严格有序」，就用 orderId 作为 key，让它固定落到同一个分区。

3. 分区数只能增加，不能减少
   而且增加分区会改变「同一 key 落到哪个分区」的映射（默认分区器对 key 取 murmur2 哈希再取模），
   历史数据与新增数据可能被拆到不同分区，需要严格有序的实体在扩容时要格外小心。
```

key 的两种行为：有 key 时按哈希固定落分区（相同 key 必落同一分区）；没 key 时从 Kafka 2.4 起默认用「粘性分区」（一批消息粘在同一分区，攒满后换下一个），所以不指定 key 时不要指望顺序，也不要指望绝对均匀。热点 key（某个大客户、某台高频主机）会把单个分区打满，识别方法是看各分区的位移差异与目录大小，处理办法是给 key 加后缀打散——代价是同一实体失去全局有序。

### 4.6 Replica、Leader、Follower 与 ISR

每个分区可以有多份副本（replication factor），它们分布在不同的 broker 上。同一时刻只有一份是 Leader，负责全部读写；其它副本是 Follower，只从 Leader 拉取数据同步。

```text
ISR（In-Sync Replicas）      与 Leader 保持同步的副本集合，是「不丢数据」的判断基础。
                              生产者 acks=all 的含义就是「写入所有 ISR 副本后才算成功」。

ELR（Eligible Leader Replicas）  4.0 引入：ISR 之外，但「数据完整到可以安全当选」的副本。
                              它的意义是避免「ISR 全挂时只能等」或「被迫做不安全的 unclean 选举」；
                              4.0 需显式开启（eligible.leader.replicas.version=1），4.1 起新集群默认启用。

Leader 选举顺序               ISR 非空 → 从 ISR 里选；ISR 为空 → 从 ELR 里选未隔离的；
                              再不行 → 选最后一次的 Leader（等价于旧版在全部副本离线时的行为）。
```

几个工程结论：

- 副本因子 3 + `min.insync.replicas=2`：可容忍 1 台 broker 宕机而不中断写入、不丢数据。三副本集群实测中，停一台时 Leader 自动切换、ISR 收缩到 2、写入继续；再停第二台，ISR 只剩 1，写入被拒绝（`NotEnoughReplicasException`）——这是**一致性优先于可用性**的体现，也是设计行为。
- ISR 会自动回补：坏掉的节点恢复后，落后的副本追平进度就重新进入 ISR，不需要人工干预。
- `unclean.leader.election.enable` 保持 `false`：允许非同步副本当 Leader，等于用小概率丢数据换可用性，除非业务明确接受。
- 自动刷盘（而不是每条 fsync）依赖副本机制保证安全，把 `log.flush.interval.messages` 调得很小只会拖垮性能。

### 4.7 Segment 与索引文件

分区目录里不是一个巨大的日志文件，而是一串 segment（默认每 1GB 滚一个），每个 segment 配三类文件：

```text
{offset}.log                    消息本体（含消息批次、CRC 校验、时间戳）
{offset}.index                  位移索引：offset -> 文件内物理位置
{offset}.timeindex              时间戳索引：时间 -> offset（按时间查位移、按时间重置位移的基础）
leader-epoch-checkpoint         Leader 变更历史（副本一致性、epoch 校验用）
partition.metadata              该分区归属的主题 ID（topicId）
```

由此产生一个常见误解：**空分区也会占几十 MB**。因为索引文件按 `log.index.size.max.bytes`（默认 10MB）预分配，且是稀疏文件；看真实占用要用 `du --apparent-size` 或分区级容量工具，别用 `df` 对着整机看，也别以为这是磁盘泄漏。

Kafka 查找一条消息用的是「三段式查找」：先用内存里的稀疏位移索引定位到 segment，再用 `.index` 定位到消息块，最后在块内顺序扫（块内消息不大，几十 KB 级别的顺序读在页缓存里很快）。这也是为什么「按位移读」比「按时间戳读」更快。

### 4.8 内部主题

Kafka 自己也要用主题来存数据，这些内部主题最容易在运维时被忽略：

| 内部主题 | 存什么 | 注意点 |
|---|---|---|
| `__cluster_metadata` | KRaft 的集群元数据日志 | 落在每个节点的数据目录，由 controller 之间复制 |
| `__consumer_offsets` | 各消费组对每个分区的已提交位移 | 默认 50 个分区（`offsets.topic.num.partitions`）；副本因子不够会在单节点上建不出来 |
| `__transaction_state` | 事务生产者的状态 | 只在用事务时才有内容，副本因子同样要按集群规模设置 |

这三个主题的副本因子都有**独立配置项**（`offsets.topic.replication.factor`、`transaction.state.log.replication.factor` 等），不受 `default.replication.factor` 影响。单节点实验最常见的一幕是：生产者能写、消费者一直超时、broker 日志里反复出现「Sent auto-creation request for Set(__consumer_offsets)」——原因就是官方镜像把 `offsets.topic.replication.factor` 默认设成 3，单 broker 上这个主题永远建不出来，而消费组的一切功能都依赖它。

### 4.9 Coordinator

- **Group Coordinator（消费组协调者）**：某个 broker 上的一个角色，负责某个消费组的成员管理、分区分配（配合组内 leader 客户端）、位移提交、Rebalance 协调。消费组按 `group.id` 哈希到 `__consumer_offsets` 的某个分区，该分区的 Leader 所在的 broker 就是这组的协调者。
- **Transaction Coordinator（事务协调者）**：负责事务的 begin/commit/abort 状态机，把事务状态写进 `__transaction_state`，并负责超时事务的清理与「僵尸生产者」的隔离（fencing）。
- 这两个协调者都是「某个 broker 兼任的角色」，不是独立进程，也不需要额外部署；但排查消费组问题时，知道「要找这组的协调者是哪个 broker」能省很多时间。

### 4.10 保留与压实

Kafka 的数据不是读完就删，而是按策略删：

```text
retention.ms / retention.bytes      按时间或总大小清理（默认 7 天）；两者都设时先满足谁就删谁
cleanup.policy=delete（默认）       删除过期 segment
cleanup.policy=compact             压实：同一个 key 只保留最新一条（用于「按主键还原状态」）
tombstone                          compact 主题里 value 为空的消息，表示「这个 key 被删除了」
```

几个必须知道的行为细节：

- 删除的最小单位是 segment，并且由后台线程周期性执行（`log.retention.check.interval.ms` 默认 5 分钟），所以「设置 10 秒保留」后可能等好几分钟消息才真正消失。判断保留是否生效，要看分区的「最早可读位移」（log-start-offset）是否推进，而不是凭感觉看消息还在不在。
- 压实主题适合「用户档案变更」「配置变更」「订单最终状态」这类「按主键取最新」的场景；纯事件流不要用压实，否则历史事件会被吞掉。
- 保留策略与磁盘水位是一对：磁盘满时刷盘失败 → ISR 收缩 → 严重时分区离线。所以分区级容量监控（而不是整机 df）是必备告警项。

## 5. 客户端组件

### 5.1 Producer

生产者是写消息的客户端。它的内部结构与参数都能对上号：

```text
send(record)
  -> 序列化器（Serializer）：把 key / value 转成字节
  -> 分区器（Partitioner）：决定写到哪个分区（有 key 用哈希，无 key 用粘性分区）
  -> 累加器（RecordAccumulator）：按分区攒批，batch.size 是单分区批次上限
  -> Sender 线程：按 linger.ms 与批量情况拉取待发批次，真正做网络发送
  -> broker 写入 Leader，按 acks 决定何时算成功
```

三个使用层面的结论：

- **`send()` 是异步的**：它只是把消息放进客户端内存缓冲并返回一个 Future，真正的网络发送在独立线程里做。所以关键业务要同步等待结果，非关键业务用回调，进程退出前必须 flush（否则缓冲里的消息会丢）。
- **`acks` 决定「何时算成功」**：`acks=all` 表示写入所有 ISR 副本才返回，是默认基线与推荐值；`acks=1` 只等 Leader 落盘（Leader 宕机丢数据），`acks=0` 不等待（只用于可丢的埋点）。
- **幂等与事务是两件事**：`enable.idempotence=true`（3.0 起默认开启）保证「同一生产者会话内重试不产生重复」，靠 PID + 序列号去重；事务（`transactional.id`）保证「跨分区、跨主题的写入原子」，还能把位移提交也纳入事务（流式 ETL 的读-改-写链路）。

生产端最重要的参数就是那么几个，口诀是「可靠性靠 acks + 幂等，吞吐靠 batch.size + linger.ms + 压缩」：

| 参数 | 作用 | 建议 |
|---|---|---|
| `acks` | 确认级别（0/1/all） | 保持 all，并让服务端配 min.insync.replicas=2 |
| `enable.idempotence` | 幂等生产 | 保持开启，避免重试导致重复 |
| `retries` / `delivery.timeout.ms` | 重试次数与总超时 | 重试给足，总超时明确设置（别无限等） |
| `batch.size` / `linger.ms` | 攒批大小与等待时间 | 64KB~1MB、5~50ms，是提升吞吐最省力的两个旋钮 |
| `compression.type` | 压缩算法 | lz4 通用折中，zstd 压缩率更高但更吃 CPU |
| `buffer.memory` / `max.block.ms` | 客户端缓冲与阻塞上限 | 高吞吐调大缓冲；线程池里的生产者把阻塞上限调小，让业务快速失败 |
| `max.in.flight.requests.per.connection` | 单连接未确认请求数 | 幂等开启时 5 是安全上限；关闭幂等又要求严格顺序时必须设为 1 |
| `key.serializer` / `value.serializer` | 序列化器 | 生产用 Avro/Protobuf + Schema Registry，不要裸 JSON 长期裸奔 |

### 5.2 Consumer

消费者是读消息的客户端，使用模型是「订阅主题 + 循环拉取 + 处理 + 提交位移」：

- **拉模型**：消费者主动 poll 一批（`max.poll.records` 控制批量），处理完再拉下一批。这天然形成背压——处理慢就消费慢，不会像推模型那样被压垮。
- **位移提交三种方式**：自动提交（默认 5 秒一次，简单但可能丢/重复，因为它提交的是「poll 到的位置」而不是「处理完成的位置」）、手动同步提交（处理成功后提交，最稳，生产推荐）、手动异步提交（吞吐更好，失败靠回调补）。**关闭自动提交 + 处理成功后提交 + 业务幂等**，是绝大多数生产链路的正确姿势。
- **Rebalance**：组内成员加入/退出、订阅主题的分区数变化、心跳超时（`session.timeout.ms`）、单位处理超时（`max.poll.interval.ms`）都会触发分区重新分配。Rebalance 期间整个组短暂停止消费；缓解手段是减少 `max.poll.records`、把耗时处理放到线程池、把 `max.poll.interval.ms` 调大、给实例设 `group.instance.id` 变成静态成员（避免重启引发的抖动）。
- **起点策略**：`auto.offset.reset` 决定「没有已提交位移时从哪儿读」，`earliest` 从最早可读位移开始，`latest` 只读新消息。它只在「没有位移」时生效，不是「每次都从头读」。
- **读不到数据的几种原因**要能一眼分辨：位移超出范围（保留期过了，报 `OffsetOutOfRangeException`）、消息还没到 HW（副本没同步完，read_committed 还要等事务提交）、失去分区归属（Rebalance 期间提交，报 `CommitFailedException`）、毒药消息卡住分区（处理一直失败，LAG 不动）。

### 5.3 Consumer Group 与 AdminClient

**Consumer Group** 是 Kafka 水平扩展消费能力的方式：同一组内一个分区只给一个消费者（分区互斥），不同组之间互不影响（广播语义）。所以扩容有两条路——加消费者（受分区数限制，得先加分区）、加消费组（不受限制，同一份数据被多个组分别处理）。判断消费能力是否够，看的是 LAG：稳定在低位是正常、持续增长是能力不足、抖动且偶尔归零通常意味着频繁 Rebalance。

**AdminClient** 是程序化管理集群的客户端 API：建/删主题、改分区与动态配置、查消费组与位移、管理 ACL 与配额。命令行工具（下一章的工具族）本质上就是 AdminClient 的命令行封装。生产上建议用 IaC（脚本或平台）统一建主题，并关掉 `auto.create.topics.enable`，避免客户端打错名字产生一堆垃圾主题。

### 5.4 客户端版本兼容与 Java 要求

- **客户端与 broker 双向兼容**：老客户端能连新 broker（4.0 的 broker 支持 2.1+ 的客户端），新客户端也能连老 broker。所以老项目不必为了用新 broker 去升级 Spring Boot。
- **Java 版本要求**：4.0 起客户端与 Kafka Streams 需要 Java 11（KIP-750），broker / Connect / 命令行工具需要 Java 17（KIP-1013）。也就是说「用 4.x 的 kafka-clients 客户端，但工程还编译在 Java 8」是行不通的；如果工程必须留在 Java 8，就用 3.x 的客户端去连 4.x 的 broker。
- **线协议演进**：4.0 移除了 2.1 之前的老版本协议，老客户端如果太老会直接连不上，排查时先用 `kafka-broker-api-versions` 看两端支持的协议区间。

### 5.5 Spring Kafka

Java 后端最常用的封装。它把客户端组件包装成 Spring 的 Bean 与注解：

| 组件 | 角色 | 关键点 |
|---|---|---|
| `KafkaTemplate` | 发送消息 | 封装 Producer，支持同步/异步、事务、指定分区与 header |
| `@KafkaListener` | 消费消息 | 封装 Consumer，`concurrency` 控制并发线程数（不要超过分区数） |
| `KafkaAdmin` + `NewTopic` Bean | 声明式建主题 | 应用启动时补建缺失主题，避免「主题不存在」导致启动失败 |
| `ErrorHandlingDeserializer` | 容错反序列化 | 坏消息不会把消费线程打死；要配 `JsonDeserializer` 的信任包 |
| `DefaultErrorHandler` + `DeadLetterPublishingRecoverer` | 重试与死信 | 重试耗尽后把消息投到 DLT 主题，分区继续前进不被毒药消息卡死 |
| `AckMode.MANUAL_IMMEDIATE` | 手动提交位移 | 业务处理成功后显式 acknowledge，避免「没处理就提交」 |

三个容易漏的认知：手动 ack 时如果 `AckMode` 没设成 MANUAL/MANUAL_IMMEDIATE，`acknowledge()` 是空操作；重试处理器要用 `addNotRetryableExceptions` 把「重试没有意义」的异常（如反序列化失败）直接送死信；**死信主题不是终点**——没有 DLT 消费者、没有告警、没有回放工具，消息只是从「卡住分区」变成「静静躺在另一个主题里」。

## 6. 生态组件

### 6.1 Kafka Connect

Connect 是「配置驱动的数据搬运框架」，用 connector 把外部系统与 Kafka 连起来，不用写代码：

```text
Source Connector：外部系统 -> Kafka
    MySQL / PostgreSQL / MongoDB（可用 Debezium 做 CDC）、S3、文件、日志
Sink Connector：Kafka -> 外部系统
    ES、ClickHouse、HDFS、S3、JDBC、Redis、对象存储
```

使用层面的要点：

- **两种运行模式**：单机（开发、调试）与分布式（生产：任务自动分配、offset 存进 Kafka 内部主题、节点可扩、重启可恢复、提供 REST API 管理）。
- **三个内部主题**：`connect-configs`（必须 compact、单分区）、`connect-offsets`、`connect-status`（都必须 compact）。这些主题的副本因子同样要按集群规模设置，否则 Connect 集群在单节点上起不来。
- **转换能力有限**：字段改名、脱敏、路由这类轻量转换用 SMT（Single Message Transform）解决；复杂 join、聚合、多步转换交给 Flink/Streams，不要硬塞进 Connect。
- **它的价值是省事**：手工消费程序要自己写 offset 管理、重试、批量、幂等、监控，每个数据源都要重复一遍；Connect 把这些变成配置。

### 6.2 Kafka Streams

Kafka Streams 是一个**库**（不是独立集群），嵌在 Java 应用里做流处理：读 Kafka、算完写回 Kafka。核心概念是 KStream（记录流，一行一个事件）与 KTable（变更流，一行一个 key 的最新状态），配合窗口（滚动/滑动/会话）、状态存储（本地 RocksDB + 变更日志主题）、join 与 exactly-once 支持。

什么时候用它：处理逻辑就在 Java 应用内部（尤其是「读 Kafka 写 Kafka」）、拓扑不太复杂、不想额外运维一个 Flink 集群。什么时候不用：需要独立可扩缩的计算集群、需要多语言（Python/SQL）、拓扑复杂或状态特别大——这些场景 Flink 更合适。

一个实践中的坑：状态存储会随 key 无限增长（窗口类操作尤其明显），必须配窗口保留与状态清理策略，否则磁盘会被吃满。

### 6.3 ksqlDB

ksqlDB 用 SQL 描述流处理（建 stream/table、做聚合与 join、输出物化视图），适合快速验证想法、做轻量实时指标。它的底层就是 Kafka Streams，因此能力边界与 Streams 类似：复杂 UDF、极致性能、精细状态控制不是它的强项。注意它是 Confluent 生态组件（Apache Kafka 发行包里没有）。

### 6.4 Schema Registry

Schema Registry 管理消息的模式（Avro / Protobuf / JSON Schema）并做兼容性校验，是「生产必备但入门常被忽略」的组件：

- **它解决的问题**：JSON 没有强制模式，生产者把字段 `amount` 改名成 `amt`，消费者不会报错，只会静默解析成 null——这类数据事故非常难查。
- **机制**：消息体只带 schema ID，schema 存在 Registry；生产者注册新版本时按兼容性策略（BACKWARD / FORWARD / FULL）校验，不兼容的变更在发布阶段就被拦住。
- **客户端的配合**：序列化器/反序列化器需要配置 Registry 地址；Connect 与 Streams 也都能接。
- 同样属于 Confluent 组件（Apache 侧有 Apicurio Registry 等替代品）。

### 6.5 MirrorMaker 2 与跨集群复制

MirrorMaker 2（MM2，Apache Kafka 自带）负责集群间的数据复制，用途有三类：灾备（主备集群）、数据汇聚（多机房数据汇到中心集群）、集群迁移（老集群搬新集群，配合消费组位移同步）。

使用要点：复制拓扑、topic 重命名规则、offset 同步（MM2 会把源集群的位移映射到目标集群，让消费者能接着读）、以及**复制是异步的**——灾备切换时必然有数据差（RPO 不为零），要按业务容忍度规划。云上还有 Cluster Linking / 托管复制服务这类等价能力。

### 6.6 REST Proxy

REST Proxy 让非 Java 客户端（Python、Go、前端、运维脚本）通过 HTTP 访问 Kafka（生产、消费、查主题与消费组）。它的价值是降低接入门槛；风险也很明确：**它一旦暴露在公网，等于把你整个集群的读写能力开放出去**。生产部署必须放在内网、加认证鉴权、限流，不允许浏览器直连。

### 6.7 CDC 与数据集成工具

- **Debezium**：最常用的 CDC 引擎，以 Kafka Connect connector 的形式运行，读 MySQL binlog / PostgreSQL WAL 等，输出结构化变更事件（含 op 类型、前后镜像），主键作为 key 保证同一行变更的顺序。
- **Canal / Maxwell**：国内 MySQL CDC 的常见选择，实现思路与 Debezium 类似，直接写 Kafka。
- **Flink CDC**：把 CDC 源做成 Flink Source，适合「CDC 直连计算」的链路（MySQL → Flink → 湖表），中间可以不经 Kafka；也能写成 Kafka。
- **批量同步工具**（DataX、SeaTunnel、Sqoop）：负责全量/批量搬运，与 Kafka 的增量管道配合使用。

CDC 消费端要处理的四件事在任何工具下都一样：事件类型判别（新增/更新/删除/快照）、同一行变更落同一分区、用主键 upsert 做幂等、快照阶段与增量阶段的实时性差异。

### 6.8 计算引擎侧的消费者

Flink、Spark Structured Streaming、Trino（配合 Kafka connector 做查询/联邦）在 Kafka 面前都是「普通的消费者或生产者」。它们的 Kafka connector 关注的是：起点策略（从提交位移/最早/最新/指定时间戳开始）、水位线（watermark）与事件时间、checkpoint 与位移提交如何联动、以及消费并行度与分区数的对应关系。这是大数据链路里 Kafka 的「下游大头」，也决定了主题的分区数规划。

### 6.9 采集端与分层存储

- **采集端**：Filebeat、Fluent Bit、Vector、Flume、Logstash 负责把日志与指标写进 Kafka。选 key 的原则是「同一来源有序」，通常用主机名或服务名；要注意某些采集器的默认批量与压缩配置对 broker 的压力。
- **分层存储（Tiered Storage）**：KIP-405 引入的能力，把旧的 segment 从本地盘下沉到对象存储（S3/HDFS 等），本地只留热数据。它在 3.6 作为早期访问特性出现、3.9 起标记为生产可用，具体可用范围与限制（例如压实主题不支持）以所用版本文档为准。它的意义是「同一份数据既便宜又久留」，是 Kappa 架构与长保留场景的关键拼图。

## 7. 数据是怎么流动的

### 7.1 写入路径

```text
生产者 send
   1) 序列化成字节
   2) 分区器决定分区
   3) 进客户端累加器攒批（batch.size 满或 linger.ms 到就发）
   4) Sender 线程发往该分区 Leader 所在 broker
   5) Leader 写入自己的页缓存（此时还没落盘）
   6) Follower 拉取并写入各自的页缓存，复制完成后推进高水位 HW
   7) acks=all 时，等所有 ISR 副本都写入，才返回成功给生产者
```

### 7.2 读取路径

消费者只能读到**高水位之前**的消息（HW 是「所有 ISR 都同步到的位置」），这样保证「读到即不会因 Leader 切换而消失」。使用事务并设成 `read_committed` 时，还要额外等事务提交，未提交的消息对它是不可见的。

消费者的读取是「按位移顺序拉」：从提交的位移开始，一批一批往后读，处理完提交新位移。理解这一点后就能解释很多现象——LAG 是「最新位移 − 已提交位移」，位移重置可以「重放历史」，命令行消费者退出时会为它拿到的分区提交位移（所以用它演示积压很容易一启动就把 LAG 抹平）。

### 7.3 位移、Rebalance 与积压的三角关系

```text
积压（LAG）增长  ->  消费能力不足：加分区 + 加消费者，或优化单条处理耗时
积压抖动、组状态反复变化  ->  Rebalance 频繁：查心跳超时与单批处理耗时
位移提交失败  ->  处理期间失去分区归属：提交要放在处理循环内，并在撤销回调里补一次
```

一句实践口径：**Kafka 只保证「至少一次」，做到「不丢」要靠先处理成功再提交位移；做到「不重」要靠业务幂等**。两者合起来才是生产上所谓的「事实上的精确一次」。

### 7.4 保留与压实如何改变「能读到什么」

- 保留期内：从最早可读位移（log-start-offset）到 LEO 都能读；`earliest` 不是「从 0 开始」，而是「从还没被删的第一条开始」。
- 保留期外：segment 被物理删除，此时拿一个过期位移去读会报 `OffsetOutOfRangeException`，必须按业务决定重置到最早或最新。
- 压实主题：同一个 key 只留最新一条，位移会有空洞（被压实掉的位置读不到），遍历时的场景要按「按 key 取状态」而不是「逐条事件」来设计。

## 8. 大数据里的典型用法

### 8.1 六类用法速览

| 用法 | 链路形状 | key 选择 | 消费语义 | 主要风险 |
|---|---|---|---|---|
| 业务解耦 | 订单服务 → Kafka → 库存/积分/风控/数仓 | 业务主键（orderId） | 至少一次 + 业务幂等 | 下游幂等没做好，重复扣减 |
| 日志与埋点采集 | 采集器 → Kafka → ES/ClickHouse/HDFS | 主机名或服务名 | 至少一次 | 分区倾斜、流量突发打满磁盘 |
| 数据管道与 CDC 入湖 | 业务库 → CDC → Kafka → 湖表/数仓 | 表主键 | 精确一次（可用事务） | 快照与增量混淆、删除事件未处理 |
| 实时计算 | 事件流 → Kafka → Flink → 指标/告警 | 业务维度键 | 至少一次或精确一次 | 水位线/事件时间配置错误 |
| 削峰填谷 | 高峰写入 → Kafka 缓冲 → 低速消费 | 无需有序时可打散 | 至少一次 | 积压持续增长直到磁盘打满 |
| 事件溯源与状态还原 | 事件流 → compact 主题 → 状态服务 | 实体 ID | 至少一次 + 幂等 | 压实配置用错，历史事件被吞 |

### 8.2 日志与埋点采集链路

```text
应用日志
  -> Filebeat / Fluent Bit（按服务名或主机名做 key）
  -> Kafka（6~24 分区、副本 3、保留 3~7 天）
  -> 消费组 A：批量写 ES / ClickHouse（检索与看板）
  -> 消费组 B：落 HDFS / 对象存储（离线归档与回溯）
  -> 消费组 C：异常日志实时告警
```

要点：日志允许重放但不必留太久；分区数按「日峰值 QPS ÷ 单分区吞吐」估；消费端批量写（攒 500~2000 条或 1~2 秒一批）比逐条写效率高一个量级；LAG 与消费速率是扩容的唯一依据。

### 8.3 CDC 数据管道

```text
MySQL binlog
  -> Debezium / Canal / Flink CDC（按主键做 key，按表分主题）
  -> Kafka（保留期要覆盖「下游故障修复所需时间」，建议 ≥ 3 天）
  -> Flink / 消费程序：upsert 到 Iceberg/Hudi/ClickHouse/ES
  -> 附带：schema 变更（加字段）与 DDL 事件的处理策略要提前定
```

要点：CDC 事件必须按主键保序（工具默认已做）；删除事件的 value 结构与新增不同，要单独处理；用主键 upsert 实现幂等；快照阶段（initial）会灌一大批历史数据，别在那段时间用实时性要求高的消费者。

### 8.4 实时计算链路

```text
业务事件 -> Kafka（事件时间字段必须带上）
  -> Flink（水位线 + 窗口聚合 / 双流 join / CEP 规则）
  -> 结果写回 Kafka / 写 Redis/ClickHouse / 触发告警
```

要点：**消息本身必须带事件时间**（业务发生时间），否则只能退化成处理时间语义；分区内有序才能保证同一 key 的事件按序到达算子；Flink 的 checkpoint 与位移提交的联动方式决定了故障恢复时是「精确一次」还是「重复计算」。

### 8.5 削峰填谷链路

流量尖峰（秒杀、批量导入、报表导出）的典型处理：上游把请求写成事件写进 Kafka 就返回，下游按自己的能力消费。这条链路的健康指标不是吞吐，而是「积压能否在规定时间内追平」：

```text
积压量（LAG 之和） ÷ 消费速率 = 追平所需时间
这个时间必须小于业务的容忍窗口（如「导出结果 10 分钟内必须生成」）
```

### 8.6 事件溯源与状态还原

用 compact 主题承接「按主键变更」的事件，消费者从头读一遍即可重建全量状态（如用户档案、商品信息、配置中心）。它的好处是「状态是可重建的、可审计的」，代价是状态规模受 key 数量限制（压实只保留每 key 最新一条），以及必须处理好 tombstone（删除标记）语义。

## 9. 部署形态与运行方式

### 9.1 四种部署形态

| 形态 | 适用 | 优点 | 代价 |
|---|---|---|---|
| 官方容器镜像 | 本地开发、演示、CI | 一条 compose 起单节点，环境变量改配置 | 生产要靠平台编排，配置散在环境变量里 |
| 二进制包 + systemd | 中小规模生产、可控的裸机环境 | 配置可控、性能稳定、便于调优 | 需要自己做安装、JVM 参数、监控接入 |
| Kubernetes + Operator | 已有 K8S 体系的团队 | 声明式管理、滚动升级、弹性 | 存储（本地盘/云盘）、网络通告地址都要仔细设计 |
| 托管云服务 | 不想自己做运维 | 免运维、自带监控与扩容 | 成本更高、能力受服务商限制、跨云迁移要考虑兼容 |

裸机部署的几个真实门槛（实测踩过）：broker / Connect / 命令行工具需要 JDK 17+；`kafka-server-start.sh` 需要预先建好并授权 `$KAFKA_HOME/logs`（否则 GC 日志写不进去、JVM 起不来）；`systemctl stop` 会让 JVM 以 143 退出，systemd 会记为失败，需要在 unit 里显式声明 `SuccessExitStatus=143`；JMX 端口记得开（否则没有监控数据）。

### 9.2 集群拓扑建议

```text
开发/演示    1 个 combined 节点（broker + controller）即可
            注意：单节点必须把内部主题副本因子显式设为 1

最小生产     3 个 broker + 3 个 controller（分角色），或 3 个 combined
            能容忍 1 台宕机；副本因子 3、min.insync.replicas 2

中等规模     5~10 个 broker，controller 独立 3 台
            关注机架感知（broker.rack），让副本跨机架/跨可用区

大规模       按业务域拆集群（数十 broker 的单一集群风险与升级窗口都不可控）
```

controller 数量必须是奇数（1/3/5），理由是 Raft 需要多数派；两台 controller 的容错能力反而不如一台。

### 9.3 监听器与端口

```text
PLAINTEXT / SASL_PLAINTEXT     客户端通道（开发明文，生产用 SASL 认证）
SSL / SASL_SSL                 加密与认证通道
CONTROLLER                     KRaft 元数据复制与选举（与客户端端口分开）
INTERNAL / EXTERNAL            云上内外网分离，避免跨区流量与费用失控
```

`advertised.listeners` 是「broker 告诉客户端该用哪个地址来找我」的值，必须按访问来源正确设置：容器内客户端、宿主机客户端、云上外部客户端看到的应该是不同的地址。写错的症状统一为「第一次连上，后面全部超时或解析失败」。

### 9.4 关键配置的分类

```text
身份与目录      node.id、process.roles、log.dirs、meta.properties（自动生成）
元数据与选举    controller.quorum.voters / bootstrap.servers、controller.quorum 相关
副本与可靠性    default.replication.factor、min.insync.replicas、unclean.leader.election.enable
内部主题        offsets.topic.replication.factor、transaction.state.log.replication.factor 等
日志与保留      log.retention.ms/bytes、log.segment.bytes、log.retention.check.interval.ms
线程与网络      num.network.threads、num.io.threads、socket.send/request 缓冲
客户端准入      auto.create.topics.enable、group.initial.rebalance.delay.ms、消息大小上限
```

其中「静态参数」与「动态参数」要分清：像 `log.dirs`、`num.network.threads`、`log.retention.check.interval.ms` 只能改配置文件后重启，用动态配置命令去改会被拒绝；查询配置时能看到它属于静态还是动态来源，这一点在排障时很省时间。

## 10. 可靠性、顺序与消费语义

### 10.1 「不丢」的三处关键配置

生产环境 95% 的消息丢失来自三个地方：

```text
acks=1 或 acks=0               Leader 宕机时，还没同步到 Follower 的消息丢失
min.insync.replicas 没设置      ISR 萎缩到只剩 Leader 时写入依然「成功」，Leader 再挂就丢
enable.auto.commit=true        消费者「还没处理就先提交位移」，表现为丢消息
```

正确组合是「服务端用副本保证不丢，客户端用 acks 决定何时算成功」：

| 侧 | 配置 | 推荐值 |
|---|---|---|
| 服务端 | replication.factor | 3 |
| 服务端 | min.insync.replicas | 2 |
| 服务端 | unclean.leader.election.enable | false |
| 服务端 | 内部主题副本因子 | 与集群规模一致（3 节点就设 3） |
| 生产端 | acks / 幂等 / 重试 / 总超时 | all / 开启 / 给足 / 明确设置 |
| 消费端 | 自动提交 / 单批上限 / 处理超时 | 关闭 / 按耗时设置 / 覆盖最长单批处理时间 |
| 事务场景 | isolation.level | read_committed |

### 10.2 三副本集群的宕机行为（实测结论）

- 停 1 台 broker：分区 Leader 自动切换（controller 从 ISR 里选），ISR 收缩到 2，`min.insync.replicas=2` 仍满足，写入照常成功——**这是「可用性」**。
- 再停第 2 台：ISR 只剩 1，`acks=all` 的写入被拒绝并抛 `NotEnoughReplicasException`，业务侧报错或降级——**这是「一致性优先」**。如果这里把 `min.insync.replicas` 设成 1，写入会「成功」，但 Leader 再挂就真丢数据。
- 恢复节点：副本自动追平并重新进入 ISR，无需人工干预；追平期间消费不受影响（消费者只读 HW 之前的数据）。

### 10.3 幂等与事务的边界

```text
幂等生产者          保证「同一生产者会话内重试不产生重复」（PID + 序列号去重）
                    不保证「进程重启后不重复」——PID 变了，跨会话的重复仍可能发生

事务                保证「跨分区、跨主题写入的原子性」，并可把位移提交纳入事务
                    不保证「业务只执行一次」——写数据库、调第三方 API 仍要自己幂等

fencing             同一个 transactional.id 被两个实例使用，broker 会抬高 epoch 让旧实例失效，
                    这是防止「僵尸生产者」的设计行为，不是 bug

精确一次的真实含义  Kafka 内部（读-处理-写都在 Kafka 里）可以做到端到端精确一次；
                    跨出 Kafka 之后，靠的是业务键去重、唯一索引、状态机校验
```

### 10.4 顺序性的四个前提

```text
1. 同一业务实体用同一个 key（保证落同一分区）
2. 生产者端不重排序（幂等开启时 max.in.flight ≤ 5 安全；关闭幂等又要求严格顺序则设为 1）
3. 消费者端按 key 串行处理（同一分区虽只有一个消费者，但它内部可能是多线程）
4. 应用层不要引入打乱顺序的重投机制（失败后「先跳过、稍后重放」必然晚于后续消息）
```

破坏顺序的常见操作：增加分区数（同一 key 的映射会变）、用不带 key 的消息却期望有序、消费失败后无序重放。

## 11. 监控与运维

### 11.1 命令行工具族

发行包 `bin/` 下有几十个脚本，日常真正用到的十来个，按用途分四类：

```text
看集群      kafka-broker-api-versions（协议版本与节点状态）、kafka-cluster（集群 ID）、
            kafka-metadata-quorum（KRaft 仲裁状态）、kafka-log-dirs（分区级磁盘占用）

管主题      kafka-topics（建/改/查/删主题、看副本分布与 ISR）、
            kafka-configs（动态配置的增删改查，含主题级覆盖与 quotas）

收发与消费组  kafka-console-producer / kafka-console-consumer（联调利器）、
            kafka-consumer-groups（消费组状态、LAG、位移重置与导出）、
            kafka-get-offsets（各分区位移）、kafka-dump-log（看消息批次内部结构）

运维动作    kafka-reassign-partitions（限速迁移副本、扩容均衡）、
            kafka-leader-election（首选 Leader 选举，把 Leader 分布拉回均衡）、
            kafka-storage（KRaft 格式化与集群 ID）、kafka-acls（授权）、
            kafka-producer-perf-test / kafka-consumer-perf-test（压测，只做相对比较）
```

工具使用上有两个版本相关的坑：4.x 把工具类统一挪到 `org.apache.kafka.tools` 包（老的 `kafka.tools.GetOffsetShell` 会报「找不到主类」），参数也从 `--broker-list` 改成 `--bootstrap-server`；命令行消费者不加超时参数时会永久挂住，脚本里必须加超时。

### 11.2 监控指标体系

broker 侧（通过 JMX 采集）：

| 指标 | 健康值 | 含义 |
|---|---|---|
| UnderReplicatedPartitions | 0 | 欠副本分区数，最核心的告警项 |
| OfflinePartitionsCount | 0 | 不可用分区数，非 0 即故障 |
| ActiveControllerCount | 集群恰好 1 | 0 表示无 controller，大于 1 是脑裂 |
| IsrShrinksPerSec / IsrExpandsPerSec | 长期为 0 | 频繁收缩说明有节点在掉队 |
| MessagesInPerSec | 与业务量匹配 | 突然归零说明上游断流 |
| BytesInPerSec / BytesOutPerSec | 与容量规划对照 | 判断是否需要扩容 |
| RequestHandlerAvgIdlePercent | 大于 0.3 | 低于 0.3 说明请求线程被打满 |
| 分区级磁盘占用 | 小于 70% | 用分区级数据采集，不要只看整机 df |

消费侧：消费组 LAG（最贴近业务的健康指标）、组状态（Stable / PreparingRebalance / Empty）、每个分区提交位移的增长速度与生产速率之差。

采集与展示组件：broker 暴露 JMX → JMX Exporter 或 kafka-exporter 转成 Prometheus 指标 → Grafana 出图与告警（也可用 JMX 客户端临时采样、或用命令行工具做一次性的健康检查）。指标的意义在于**用「ISR 是否完整、LAG 是否收敛、磁盘是否够用」三个问题覆盖绝大多数故障**。

### 11.3 日常运维动作

```text
扩容消费者        先加分区（只能增），再扩消费者实例；或者加消费组（不受分区数限制）
均衡副本与流量     用分区重分配工具做限速迁移（必须限速，否则打满网络与磁盘 IO），
                  迁移期间新旧副本并存、磁盘水位会短暂上升，要预留空间
Leader 分布回正     触发首选 Leader 选举，把「演练后全挤在一台」的 Leader 摊平
重置消费位移       按时间点或按偏移重置（用于重放与修数据），操作前先导出备份
滚动升级          逐节点重启，关注 ISR 回补与 LAG；升级前确认客户端版本满足新 broker 的要求
故障演练          至少做两次：停 1 台（应无感）、停 2 台（应报错但不丢数据）
```

### 11.4 容量与规格参考

```text
CPU      16~32 核：Kafka 的 CPU 主要消耗在压缩、网络线程与副本同步
内存     64GB 起：绝大部分留给操作系统页缓存（堆内存 6~8GB 足够）
磁盘     SSD/NVMe；多块盘配多个 log.dirs；经验值是「数据盘容量 : 内存 超过 8:1 性能开始恶化」
文件句柄 ulimit -n 不低于 100000（segment 文件与连接都占 fd）
网络     万兆起；副本因子 3 意味着约 2~3 倍的写放大流量
机架     broker.rack 配好，副本自动跨机架/可用区分布
```

磁盘写满是导致「部分分区不可用」的最常见原因：Kafka 依赖顺序写与页缓存，磁盘满时刷盘失败 → ISR 收缩 → 严重时分区离线。防线是「分区级水位告警 + 保留策略 + 单分区容量上限」三件套。

## 12. 安全

Kafka 的安全能力围绕四件事，入门阶段知道「有这些开关、上线前必须打开」就够：

```text
传输加密    SSL/TLS：客户端与 broker、broker 之间都可加密
身份认证    SASL：SASL/PLAIN（简单，需配 TLS）、SASL/SCRAM（用户名密码，生产常用）、
            SASL/GSSAPI（Kerberos，企业内网）、SASL/OAUTHBEARER（令牌/OIDC）
权限控制    ACL：按「主体 + 操作（读/写/建/删/描述）+ 资源（主题/消费组/集群）」授权，
            通过 kafka-acls 管理；也可以接外部 Authorizer
配额与审计  client quota 限制单客户端的流量（防止一个客户端打满集群）；
            审计日志记录授权失败，用于排查与合规
```

两条实践红线：**不要把 broker 暴露到公网**（要开放就用 REST Proxy/网关做鉴权与限流）；**浏览器与移动端不要直连 Kafka**（客户端凭据一旦泄露等于集群完全敞开）。

## 13. 与其它消息系统的对比选型

### 13.1 横向对比

| 维度 | Kafka | RabbitMQ | RocketMQ | Pulsar |
|---|---|---|---|---|
| 模型 | 分区日志（拉模型） | AMQP 队列/交换机（推模型） | 队列 + CommitLog | 分区日志 + 分层存储 |
| 单机吞吐 | 极高（十万~百万级每秒） | 中（万级每秒） | 高 | 高 |
| 消息顺序 | 分区内有序 | 队列内有序 | 队列内有序 | 分区内有序 |
| 消息保留 | 按时间/大小，可重放 | 消费即删（可配） | 按时间，可重放 | 按时间，可重放 |
| 延迟 | 毫秒 | 微秒~毫秒（更低延迟） | 毫秒 | 毫秒 |
| 复杂路由 | 无（靠主题设计） | 强（exchange / routing key / 延迟队列 / 死信） | 中等 | 中等 |
| 事务 | 支持（跨分区原子写） | 支持（性能较差） | 支持（事务消息） | 支持 |
| 运维复杂度 | 中（4.x 已简化掉 ZK） | 低 | 中 | 高 |
| 典型场景 | 日志、埋点、数仓管道、流计算 | 业务解耦、任务分发、RPC 替代 | 电商交易、金融 | 多租户、分层存储 |

选型口诀：

```text
要吞吐、要重放、要接大数据生态    -> Kafka
要复杂路由、要低延迟、量不大      -> RabbitMQ
要事务消息、要延迟消息、国内生态  -> RocketMQ
要多租户、要对象存储分层          -> Pulsar
```

### 13.2 什么时候用 Kafka Connect 而不是自己写消费者

结论是「搬运用 Connect，处理用程序」：数据在系统之间搬（数据库→数仓、Kafka→ES）、转换逻辑很轻（改字段名、脱敏、过滤），用 Connect 配置化解决，省掉 offset 管理、重试、监控这些重复劳动；一旦涉及多表 join、窗口聚合、外部 API 调用、复杂状态，就写 Flink/Streams/普通消费者，别硬塞进 Connect。

## 14. 常见误区

1. **把 Kafka 当数据库用**：Kafka 不能按任意条件查询、不能更新单条消息、默认 7 天就删数据。需要长期保存与查询，落数据湖或数仓。
2. **以为「被消费了就删掉」**：Kafka 按保留策略删数据，读与删是两件事；这也是它能重放的原因。
3. **用单分区追求全局有序**：单分区牺牲全部并行度，吞吐上不去。正确做法是「按业务实体做 key，只要求实体内有序列」。
4. **以为加消费者就能扩容消费**：并发上限是分区数，先加分区再扩实例。
5. **以为分区数可以随便调**：只能增不能减，且增加会破坏同一 key 的历史映射；分区数要在设计阶段定好。
6. **以为开了自动提交就安全**：自动提交的是「poll 到的位置」，不是「处理完成的位置」，容易丢消息。
7. **以为副本因子设了 3 就不丢数据**：还要配 `min.insync.replicas=2` 与客户端 `acks=all`，否则 ISR 掉到 1 时写入照样「成功」。
8. **忽略内部主题的副本因子**：`__consumer_offsets`、`__transaction_state` 建不出来时，表现为「能生产、消费组一直超时」这种完全不直观的症状。
9. **用裸 JSON 长期裸奔**：字段改名会静默解析成 null，排查成本极高；Avro/Protobuf + Schema Registry 才是有约束的做法。
10. **以为命令行消费者可以演示积压**：它退出时会为拿到的分区提交位移，一启动就把 LAG 抹平了。
11. **忽略 `advertised.listeners`**：症状是「第一次能连、之后全部超时」，容器与云环境最容易踩。
12. **生产环境直接用压测数字做容量规划**：共享环境、随机字节消息的压测只能用于「改参数前后的相对比较」。
13. **以为迁移副本不影响业务**：不限速的迁移会打满网络与磁盘 IO，进而引发 ISR 收缩与 LAG 暴涨。
14. **以为 4.x 还能连 ZooKeeper**：4.0 起没有 ZK，所有 `--zookeeper` 参数失效，升级路径必须经过 3.9。

## 应用场景实战

### 场景一：业务库到数仓的 CDC 数据管道

业务需求：订单库的增量变更要进数仓与检索系统，实时性要求分钟级，不允许在业务库上跑大批量查询。

链路与步骤：

```text
1. 规划主题：cdc.shop.orders、cdc.shop.order_items（按表分主题），key = 主键
   分区数按「变更速率 ÷ 单分区吞吐」估，起步 6；副本 3、min.insync.replicas 2
2. 规划保留：至少 3 天（要覆盖「下游故障发现 + 修复 + 重启消费」的时间窗）
3. 部署采集：Debezium（Connect 分布式模式）或 Flink CDC 读 MySQL binlog，
   initial 快照 + 增量；schema 变更（加字段）先在测试环境验证兼容性
4. 下游消费：Flink 作业或消费程序按主键 upsert 到 Iceberg/ClickHouse，
   同一行的变更因为 key 相同必然串行落在一个分区，天然保序
5. 幂等保障：目标表按主键 upsert（重复事件覆盖同一条记录，不产生副作用）
6. 异常处理：反序列化失败的坏消息进死信主题 + 告警；删除事件（op=d）单独处理
7. 监控：LAG、CDC 连接器状态、目标表写入延迟；延迟超阈值告警
```

设计要点：CDC 的主题必须有足够长的保留期，否则一次下游故障就可能把增量窗口错过；快照阶段的数据量大，别用实时看板直接读；DDL 事件要有人负责，否则加字段后下游静默丢字段。

### 场景二：日志采集与削峰填谷

业务需求：应用日志集中采集，允许消费者重启或故障，但不能丢日志；高峰写入要能缓冲，消费者按自己的能力消费。

链路与步骤：

```text
1. 采集端用 Filebeat/Fluent Bit 写 Kafka，key 用主机名（同一来源有序），
   主题按「日志类型」划分（应用日志、访问日志、审计日志分开）
2. 主题配置：6~24 分区、副本 3、保留 3~7 天（日志可重放，但不必长期保存）
3. 消费端多消费组并行：一组批量写 ES（检索）、一组落 HDFS/对象存储（归档）、
   一组做异常告警
4. 高峰期：上游 1 秒内写完数万条并返回，完全不关心消费者是否在线
5. 消费者离线期间用「LAG 之和」度量积压，这个数字就是「需要多少实例才能追平」的依据
6. 消费者恢复后按分区并行追平，追平速度上限 = 分区数 × 单消费者吞吐
7. 告警：LAG 超阈值或长时间不下降即告警，同时盯分区级磁盘水位
```

设计要点：分区倾斜（某服务日志量特别大）会让个别分区先追不上，key 的选择要评估分布；日志链路允许「至少一次」，消费端要能接受重复写入（按日志唯一 ID 去重或用带版本的目标表覆盖）。

### 场景三：实时指标与风控链路

业务需求：下单、支付等事件要实时产出分钟级指标，并对异常行为做实时拦截。

链路与步骤：

```text
1. 事件主题：order.order.created、pay.payment.succeeded，key = 用户 ID 或订单 ID
   消息必须带业务事件时间（用于事件时间语义与乱序处理）
2. 计算层：Flink 消费，按事件时间做 1 分钟滚动窗口聚合，输出到指标主题或直接写结果存储
3. 风控：另一条 Flink 作业（或 Streams 应用）做 CEP 规则匹配与阈值判断，
   命中后写告警主题（再由下游推送）
4. 语义选择：只统计指标可用「至少一次」；涉及金额与扣减的链路用事务（读-改-写原子）
5. 保障：checkpoint 与位移提交联动；上游主题分区数决定计算并行度上限
6. 监控：作业反压、checkpoint 时长、消费 LAG、窗口延迟（事件时间与当前时间之差）
```

设计要点：实时指标的准确性依赖「事件时间 + 水位线」配置，配置不当会出现「数据重复计算」或「结果长时间不出」；风控链路对延迟敏感，消费端的处理逻辑要控制在毫秒级，重活异步化。

## 最佳实践与踩坑记录

### 最佳实践

1. 主题命名用 `{域}.{实体}.{事件}`，环境前缀放最前（`prod.`、`test.`），一个主题只表达一种事件。
2. 分区数按「目标吞吐 ÷ 单分区吞吐」估算并预留 2~3 倍余量（常见起步 6/12/24），因为只能增不能减。
3. 同一业务实体的所有事件用同一个 key，保证分区内有序；热点 key 用加后缀的方式打散，代价是失去实体级有序。
4. 生产环境三 broker 起步，`replication.factor=3` + `min.insync.replicas=2`，并且把内部主题（位移、事务状态、Connect 元数据）的副本因子同步设成 3。
5. 生产者保持 `acks=all` + 幂等开启，不为了「快一点」关掉；吞吐靠 `batch.size`、`linger.ms`、压缩来调。
6. 关键业务用同步发送确认落盘，非关键用异步回调；进程退出前一定 flush。
7. 消费者关闭自动提交，处理成功后手动提交，并保证业务处理是幂等的（唯一索引、去重表、状态机校验）。
8. 消费端必须能处理重复消息和乱序消息——这是分布式系统的默认前提，不是异常情况。
9. 死信闭环三件套：DLT 主题 + DLT 消费者 + 告警与回放工具，缺一个都不算闭环。
10. 序列化用 Avro/Protobuf + Schema Registry，把「不兼容的字段变更」拦在发布阶段。
11. 关掉自动建主题（`auto.create.topics.enable=false`），主题由运维或 IaC 统一创建，避免客户端打错名字产生垃圾主题。
12. 监控四件套：ISR 与欠副本分区数、消费组 LAG、分区级磁盘水位、请求队列与延迟。
13. 上线前做两次演练：停 1 台 broker（应无感）、停 2 台（应写入报错但不丢数据）。
14. 分区扩容与副本迁移用限速工具做，不要直接挪数据目录；迁移前预留磁盘空间。
15. 保留时长按「下游故障恢复窗口」定，而不是拍脑袋；日志类 3~7 天，CDC 类至少 3 天，事件溯源类用压实或分层存储。
16. 容量规划按「磁盘容量 : 内存 不超过 8:1」、`ulimit -n` 不低于 100000、数据盘不放日志文件来配。
17. 4.x 升级前先检查客户端版本与 Java 版本（客户端 ≥ Java 11、broker/工具 ≥ Java 17），并确认脚本里没有 `--zookeeper`。

### 踩坑记录

坑 1：单节点集群里消费组完全不可用，生产者却能正常写入。

```text
结论：能生产、消费一直超时、broker 日志反复出现 auto-creation request for __consumer_offsets。
原因：内部主题的副本因子有独立配置项，官方镜像默认 offsets.topic.replication.factor=3，
      单 broker 上 __consumer_offsets 永远建不出来，而消费组的一切都依赖它。
解法：单节点显式把 offsets.topic.replication.factor 与 transaction.state.log 相关项设为 1；
      生产集群则显式设为 3。
```

坑 2：设置了很短的保留时间，消息却几分钟后才消失。

```text
结论：「消息还在」不等于「保留策略没生效」。
原因：删除的最小单位是 segment，且由后台线程周期性扫描（默认 5 分钟一次）；
      而这个扫描间隔是静态配置，动态修改会被拒绝。
解法：用分区的「最早可读位移」判断保留是否生效；实验时把 segment 大小与检查间隔一起调小。
```

坑 3：三个 KRaft 节点起不来，日志刷满选举信息。

```text
结论：combined 节点 + 静态 quorum 配置在多 voter 场景下选不出 leader，broker 最终以
      「unable to register with the controller quorum」退出。
原因：镜像的自动格式化生成的引导信息与多 voter 静态配置不匹配；动态 quorum 又要求
      显式给出初始 controller 集合。
解法：开发/演示用「1 个 controller-only + N 个 broker-only」；生产按官方分角色部署，
      并用 kafka-storage 显式格式化给出初始 controller 集合。
```

坑 4：老脚本搬到 4.x 上直接报「找不到主类」。

```text
结论：4.x 把工具类统一挪到 org.apache.kafka.tools 包，参数也从 --broker-list 改成 --bootstrap-server。
原因：4.0 做了一轮包的整理与旧协议清理。
解法：升级时把所有脚本里的类名与参数过一遍；新写的脚本统一用 --bootstrap-server。
```

坑 5：客户端第一次能连上，之后全部超时。

```text
结论：bootstrap 成功、随后拿到错误的元数据地址就再也连不上。
原因：broker 会把 advertised.listeners 的地址返回给客户端，容器内地址、内网地址
      在宿主机或外部客户端看来是不可达的。
解法：按访问来源配置多个监听器与不同的通告地址；容器内客户端与宿主机客户端分别验证。
```

坑 6：一条坏消息让整个分区卡死，LAG 再也不动。

```text
结论：消费端反序列化失败后无限重试同一条消息，分区无法前进。
原因：默认反序列化器抛异常、默认错误处理器无限重试。
解法：用 ErrorHandlingDeserializer 包一层 + 显式错误处理器 + 死信主题；
      把「重试没有意义」的异常（反序列化失败等）直接送死信。
```

坑 7：以为「加了分区」就解决了消费慢，结果同 key 的数据顺序乱了。

```text
结论：增加分区会改变同一 key 的分区归属，历史数据与新增数据被拆到不同分区。
原因：默认分区器对 key 取哈希再对分区数取模，分区数变了映射就变了。
解法：需要严格有序的实体在设计阶段就定好分区数；必要时停写做一次性数据迁移后再扩容。
```

坑 8：事务生产者写入成功，read_committed 的消费者却读不到。

```text
结论：事务消息要等 commit 之后才对 read_committed 消费者可见。
原因：消费端只读「已提交」数据，未提交（或已回滚）的事务数据对它不可见。
解法：消费端显式设 isolation.level=read_committed，并监控未提交事务数量与事务超时。
```

坑 9：同一个 transactional.id 被两个实例使用，旧实例的写入全部失败。

```text
结论：这是 fencing 设计行为，不是故障。
原因：broker 会把同名 transactional.id 的 epoch 抬高，让旧实例失效，避免僵尸生产者重复写。
解法：transactional.id 与实例绑定（如带 Pod 序号），滚动更新时先确认旧实例已停止。
```

坑 10：不限速地迁移副本，业务侧 LAG 突然暴涨。

```text
结论：迁移会复制大量数据，占满网络与磁盘 IO，进而引发 ISR 收缩与消费滞后。
原因：副本迁移是「先复制再切换」，期间新旧副本并存，磁盘水位还会短暂上升。
解法：迁移必须限速，观察 ISR 与 LAG，迁移完成后确认限速已被清除。
```

坑 11：不看磁盘水位，直到整个 broker 挂掉。

```text
结论：磁盘写满是「部分分区不可用」的最常见原因。
原因：磁盘满时刷盘失败，ISR 收缩，严重时分区离线。
解法：用分区级容量做告警（别只看整机 df），保留策略与单分区容量上限双保险，
      数据盘不要放日志文件、也不要与其它写密集型服务共用。
```

坑 12：把压测数字直接当成容量规划依据。

```text
结论：共享环境里压出来的吞吐不能线性外推到生产。
原因：测试机上有其它负载、消息是随机字节（压缩率与真实业务数据差异大）。
解法：容量规划要在目标硬件、目标网络、真实消息体上做；共享环境的压测只用于改参数前后的相对比较。
```

## 相关文档

- [[Kafka完整教程]] — 完整教程：命令、配置、集群部署与全部实测输出（本文的源头）
- [[09.1-Kafka 架构与存储]] — 大数据视角的 Kafka 架构与存储原理
- [[09.2-Kafka Producer]] — 生产者原理：批次、压缩、幂等与事务的内部机制
- [[09.3-Kafka Consumer]] — 消费者原理：消费组协调、位移管理与 Rebalance 协议
- [[09.4-Kafka 生态与数据集成]] — Connect、Streams、CDC 与数据集成链路
- [[15.2-数据集成工具与同步语义]] — 批量与流式 ETL、全量与增量同步的一致性语义
- [[31.5-Kafka 优化]] — 大数据性能优化专题里的 Kafka 调优参数
- [[35.2-Kafka 源码]] — 源码阅读：日志存储、副本复制与控制器实现
- [[33.3-实时数仓架构]] — Kafka、Flink、Iceberg、StarRocks 组成的实时数仓
- [[144-Kafka]] — Java 全栈视角的 Kafka 入门与 Spring 集成
- [[145-Kafka-Streams]] — Kafka Streams 流处理：拓扑、窗口与状态存储
- [[92-Kafka]] — Spring Messaging 体系下的 Kafka 集成写法
- [[Docker完整教程]] — 容器化部署基础（镜像、网络、数据卷、compose）
- [[Kubernetes完整教程]] — 把 Kafka 部署到 K8S 的编排知识
