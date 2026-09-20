---
title: Kafka 完整教程：架构原理、集群部署、客户端开发与生产运维
created: 2026-09-20
updated: 2026-09-20
type: concept
tags: [kafka, kafka-kraft, message-queue, streaming, producer, consumer, spring-kafka, big-data, devops]
---

# Kafka 完整教程：架构原理、集群部署、客户端开发与生产运维

整理日期：2026-09-20

> 状态：已完成

本文用于系统讲解 Apache Kafka，按「概念 → 部署 → 命令行 → 存储 → 客户端 → 可靠性 → 集群运维 → Spring Boot 集成 → 实战 → 踩坑」的顺序组织。文中所有命令、配置、输出都是本机实际执行得到的（容器与裸机两种部署各跑了一遍），可以直接照着复现。

实测环境：

```text
系统：Ubuntu 24.04（内核 7.0.0-28-generic，8 核 19GiB 内存）
Docker Engine：29.5.2    Docker Compose：v5.1.4
Kafka：4.1.2（KRaft 模式，无 ZooKeeper）
镜像：apache/kafka:4.1.2
JDK：OpenJDK 21.0.12（编译目标 Java 8，kafka-clients 3.9.0）
Maven：3.8.7
Spring Boot：2.7.18 + spring-kafka 2.8.11（kafka-clients 3.1.2）
实验目录：/opt/kafka-lab（示例工程与脚本见 /opt/study-work/kafka/examples/）
端口规划：容器单节点 9092/9093，裸机 9092/9093/9101(JMX)，三节点集群仅集群内互通
```

关于版本：Kafka 4.x 是当前主线，**4.0 起彻底移除了 ZooKeeper，只支持 KRaft 模式**；同时 KIP-750 / KIP-1013 把 Java 要求提高为「客户端与 Kafka Streams 需 Java 11，broker / Connect / 命令行工具需 Java 17」。所以老教程里 `--zookeeper localhost:2181` 那一套在 4.x 已经完全不可用，本文全部基于 KRaft 讲述，并在第 14 章列出 3.x 与 4.x 的差异点。

## 目录

- [1. Kafka 是什么](#1-kafka-是什么)
- [2. 核心概念与架构](#2-核心概念与架构)
- [3. 部署：容器与裸机两种方式](#3-部署容器与裸机两种方式)
- [4. 命令行工具全解](#4-命令行工具全解)
- [5. 存储格式与保留策略](#5-存储格式与保留策略)
- [6. 生产者](#6-生产者)
- [7. 消费者与消费组](#7-消费者与消费组)
- [8. 可靠性：不丢、不重、有序](#8-可靠性不丢不重有序)
- [9. 集群运维](#9-集群运维)
- [10. Spring Boot 集成](#10-spring-boot-集成)
- [11. 生态与选型对比](#11-生态与选型对比)
- [12. 应用场景实战](#12-应用场景实战)
- [13. 最佳实践与踩坑记录](#13-最佳实践与踩坑记录)
- [14. 3.x 与 4.x 的差异](#14-3x-与-4x-的差异)
- [相关文档](#相关文档)

## 1. Kafka 是什么

### 1.1 一句话定义

Kafka 是一个**分布式、分区、多副本的提交日志（commit log）**，同时扮演三个角色：

```text
消息队列      生产者写、消费者读，解耦上下游，削峰填谷
存储系统      消息按配置的保留策略落盘（默认 7 天），可重复消费
流处理平台    配合 Kafka Streams / Flink / Spark 做实时计算
```

它和传统 MQ（RabbitMQ、ActiveMQ）最大的不同在于**消息读完后不立即删除**：Kafka 靠「位移（offset）由消费者自己维护」来记录读到哪儿，broker 只按时间或大小删数据。这带来两个直接好处——消息可以重放、多个消费组可以各读各的互不影响。

### 1.2 为什么不用数据库或 HTTP 直连

```text
用数据库当队列        -> 行锁争用、轮询压力大、删除历史数据后无法重放
用 HTTP 直连下游      -> 下游抖动直接拖垮上游；没有缓冲，流量尖峰即故障
用 Redis List 当队列  -> 内存成本高、无副本保证、消费者宕机容易丢数据
```

Kafka 的定位是「**上游只管投递，下游自己按节奏消费**」：上游写入成功即返回（毫秒级），下游挂了也不影响上游；流量尖峰被磁盘缓冲吸收；消费者扩容只需加进程，Kafka 自动重新分配分区。

### 1.3 典型使用场景

| 场景 | 说明 | 关键点 |
|---|---|---|
| 业务解耦 | 下单后通知库存、积分、风控、推送 | 下游新增无需改上游代码 |
| 削峰填谷 | 秒杀、报表导出、批量导入 | 上游写入不受下游处理速度影响 |
| 数据管道 | 业务库 → Kafka → 数仓/ES/ClickHouse | 用 Connect 或 CDC 工具对接 |
| 日志采集 | 应用日志 → Kafka → 消费落盘/检索 | 高吞吐、可多路复用 |
| 流式计算 | 实时指标、风控规则、告警 | 与 Flink/Streams 配合 |
| 事件溯源 | 以事件流作为系统的唯一真相来源 | 需要设置 cleanup.policy=compact |

### 1.4 一个最小的端到端认知

```text
生产者 --写--> Topic(3 分区, 每分区 3 副本) --读--> 消费者组(2 个消费者)
                    │
                    └── 每个分区在 3 个 broker 上各存一份；Leader 对外服务，Follower 同步
```

后面所有章节都是在这张图上展开：分区决定并发度与顺序边界，副本决定可靠性，位移决定消费进度，消费组决定水平扩展方式。

## 2. 核心概念与架构

### 2.1 概念速查

| 概念 | 含义 | 工程含义 |
|---|---|---|
| Broker | 一个 Kafka 服务进程（节点） | 3 节点是最小生产规模（能容忍 1 台宕机） |
| Topic | 逻辑上的消息类别 | 命名规范：`{业务}.{实体}.{事件}`，如 `order.order.created` |
| Partition | 主题的物理分片，是并行与有序的基本单位 | 分区数决定消费者并发上限，且只能增不能减 |
| Replica | 分区的副本，分布在不同 broker | 副本因子 3 + min.insync.replicas 2 是常用组合 |
| Leader / Follower | 每个分区一个 Leader 对外读写，Follower 只同步 | Leader 挂了由 controller 从 ISR 中重新选举 |
| ISR | In-Sync Replicas，与 Leader 保持同步的副本集合 | ISR 缩小意味着有副本落后，是核心告警指标 |
| Offset | 分区内每条消息的递增编号 | 消费位移由消费者提交，broker 不记录「谁读到哪」 |
| Consumer Group | 一组消费者，组内分区互斥、组间广播 | 扩容消费者时新成员会分到一部分分区 |
| Segment | 分区目录下的日志文件（默认 1GB 一个） | 过期删除的最小单位是 segment，不是单条消息 |
| Controller | KRaft 下由元数据仲裁选出的元数据管理节点 | 负责分区分配、Leader 选举；4.x 由 KRaft Quorum 承担 |
| __cluster_metadata | KRaft 的元数据日志（存在 broker 数据目录） | 元数据也走日志复制，替代了 ZooKeeper 的 ZNode |

### 2.2 KRaft：4.x 的元数据管理

ZooKeeper 时代，Kafka 把「集群元数据 + 选举」交给外部 ZK；KRaft（Kafka Raft）把这部分内置进来：

```text
ZooKeeper 模式（3.x 及以前）    KRaft 模式（4.x 唯一选择）
Kafka broker  ----------+
Kafka broker  ----> ZooKeeper（存元数据、选 controller）
Kafka broker  ----------+

Kafka node(process.roles=controller)  <--- Raft 复制 --->  其它 controller
Kafka node(process.roles=broker)      <--- 只订阅元数据变更
```

两种角色的部署形态：

```text
combined 模式：process.roles=broker,controller   —— 单机开发、中小规模
分离模式：    process.roles=broker / controller  —— 生产推荐，元数据负载与数据负载隔离
```

controller 数量必须是奇数（3 或 5），Raft 需要多数派才能选出 leader。

### 2.3 分区：并行度与顺序的边界

```text
同一个分区内：消息严格有序（按写入顺序，位移递增）
不同分区之间：无序，不保证任何先后关系
```

由此推出三条设计规则：

1. **并发度上限 = 分区数**：一个分区同时只能被同一消费组内的一个消费者消费，消费者数超过分区数时多出来的会空闲。
2. **有序性只在分区内成立**：需要「同一订单的事件严格有序」就按 `orderId` 做 key，让它固定落到同一分区。
3. **分区数要提前规划**：Kafka 只能增加分区、不能减少；增加分区后同一 key 的哈希映射会变（旧数据在新旧分区之间不再保证顺序）。

key 到分区的映射（默认分区器）：

```text
有 key：partition = murmur2(key) % 分区数      -> 相同 key 必落同一分区
无 key：粘性分区（Kafka 2.4+ 默认）            -> 一批消息粘在同一分区，攒满后换下一个
```

### 2.4 副本与 ISR：可靠性的地基

```text
分区 0 的分布（3 分区 3 副本集群）：
  broker 1: [副本，可能有 Leader]
  broker 2: [副本]
  broker 3: [副本]
```

- 生产者 `acks=all` 表示「消息写入所有 ISR 副本后才算成功」。
- `min.insync.replicas=2` 表示「ISR 少于 2 个副本时，`acks=all` 的写入直接失败」。
- 两者组合才真正不丢：只设 `acks=all` 而不设 `min.insync.replicas`，当 ISR 萎缩到只剩 Leader 一个时，写入依然「成功」，此时 Leader 宕机就丢数据。

```text
可靠写入三件套（服务端 + 客户端各一半）：
  服务端：replication.factor=3、min.insync.replicas=2
  客户端：acks=all、enable.idempotence=true、retries 足够大
```

### 2.5 数据目录长什么样

```
/var/lib/kafka/data/
├── meta.properties                        # 节点身份：cluster.id / node.id
├── __cluster_metadata-0/                  # KRaft 元数据日志（相当于 ZK 的替代）
├── cleaneroffset-checkpoint               # 清理线程进度
├── log-start-offset-checkpoint            # 各分区最早可读位移
├── recovery-point-offset-checkpoint        # 刷盘进度
├── replication-offset-checkpoint           # 副本同步进度
├── orders-0/                              # 分区目录：{topic}-{partition}
│   ├── 00000000000000000000.log           # 消息日志（含消息批次、CRC、时间戳）
│   ├── 00000000000000000000.index         # 位移索引（offset -> 文件物理位置）
│   ├── 00000000000000000000.timeindex     # 时间戳索引（时间 -> 位移，用于按时间查）
│   ├── leader-epoch-checkpoint            # Leader 变更历史（保证副本一致性）
│   └── partition.metadata                 # 该分区的 topicId
```

`index` / `timeindex` 默认按 `log.index.size.max.bytes`（10MB）预分配，所以空分区看着也占 20MB 左右——这是正常现象，不是泄漏。

## 3. 部署：容器与裸机两种方式

两种方式都实测过，选择建议：

```text
容器（docker compose）  -> 开发环境、CI、快速验证；镜像内置 KRaft 自动格式化，改配置全靠环境变量
裸机（二进制包 + systemd）-> 生产服务器；配置是显式文件，便于审计、调优、接监控
K8S                     -> 用 Strimzi / Confluent Operator 管理，不再手工部署（本文不展开）
```

### 3.1 容器部署：单节点 KRaft（实测）

配置文件见 `examples/compose/docker-compose-single.yml`，下面是关键片段与逐条解释：

```yaml
services:
  kafka:
    image: apache/kafka:4.1.2
    container_name: kafka-single
    hostname: kafka-single
    ports:
      - "9092:9092"      # broker 端口，宿主机客户端用
      - "9093:9093"      # controller 端口，调试用
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller                     # combined 模式
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka-single:9093        # {nodeId}@{host}:{port}
      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      KAFKA_NUM_PARTITIONS: 3
      KAFKA_DEFAULT_REPLICATION_FACTOR: 1
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_LOG_SEGMENT_BYTES: 1073741824
      KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS: 5000
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      # 内部主题副本数：单节点必须显式设为 1，否则消费组不可用（见 3.3 的坑）
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
    volumes:
      - kafka-single-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 20s
```

启动与健康检查（真实输出）：

```text
$ docker compose -f docker-compose-single.yml up -d
$ docker compose ps
NAME           IMAGE                COMMAND                   SERVICE   CREATED          STATUS                    PORTS
kafka-single   apache/kafka:4.1.2   "/__cacert_entrypoin…"   kafka     20 seconds ago   Up 12 seconds (healthy)   0.0.0.0:9092-9093->9092-9093/tcp, [::]:9092-9093->9092-9093/tcp

$ docker inspect --format '{{.State.Health.Status}} {{.State.StartedAt}}' kafka-single
healthy 2026-09-20T14:59:07.117495122Z
```

启动日志里的关键一行（说明 KRaft 已就绪）：

```text
$ docker logs kafka-single | grep -E 'Kafka Server started|KafkaRaftServer nodeId'
[2026-09-20 14:59:16,771] INFO [KafkaRaftServer nodeId=1] Kafka Server started (kafka.server.KafkaRaftServer)
```

镜像的自动格式化行为（这是官方镜像的便利之处，也是排查时的线索）：

```text
$ docker logs kafka-single | head -20
===> User
uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
===> Setting default values of environment variables if not already set.
CLUSTER_ID not set. Setting it to default value: "5L6g3nShT-eMCtK--X86sw"
===> Configuring ...
Running in KRaft mode...
===> Launching ...
===> Using provided cluster id 5L6g3nShT-eMCtK--X86sw ...
```

注意最后两行：**镜像在没有设置 `CLUSTER_ID` 时会使用一个写死的默认值**。单节点无所谓，但三节点集群里如果某些节点用了默认值、某些节点用了自己生成的值，就会因 cluster ID 不一致而无法组集群——生产上应当显式传入。

### 3.2 数据目录与节点身份

```text
$ docker exec kafka-single ls -la /var/lib/kafka/data
total 20
drwxrwxr-x 3 appuser root    4096 Sep 20 14:59 .
drwxrwxr-x 3 appuser root    4096 Feb 25  2026 ..
-rw-r--r-- 1 appuser appuser    0 Sep 20 14:59 .lock
drwxr-xr-x 2 appuser appuser 4096 Sep 20 14:59 __cluster_metadata-0
-rw-r--r-- 1 appuser appuser  355 Sep 20 14:59 bootstrap.checkpoint
-rw-r--r-- 1 appuser appuser    0 Sep 20 14:59 cleaner-offset-checkpoint
-rw-r--r-- 1 appuser appuser    0 Sep 20 14:59 log-start-offset-checkpoint
-rw-r--r-- 1 appuser appuser  122 Sep 20 14:59 meta.properties
-rw-r--r-- 1 appuser appuser    0 Sep 20 14:59 recovery-point-offset-checkpoint
-rw-r--r-- 1 appuser appuser    0 Sep 20 14:59 replication-offset-checkpoint

$ docker exec kafka-single cat /var/lib/kafka/data/meta.properties
#
#Sun Sep 20 14:59:11 GMT 2026
cluster.id=5L6g3nShT-eMCtK--X86sw
directory.id=G0fmKhCkY341jgZkfX4_ow
node.id=1
version=1
```

四个 checkpoint 文件的含义：

| 文件 | 作用 | 异常时的信号 |
|---|---|---|
| `cleaner-offset-checkpoint` | 日志压实线程处理到哪个位移 | 压实不生效时看它是否推进 |
| `log-start-offset-checkpoint` | 每个分区最早可读位移 | 与 `log-end-offset` 一起判断消息是否被删除 |
| `recovery-point-offset-checkpoint` | 刷盘进度 | 非正常退出时会留下 `.tmp` 残留 |
| `replication-offset-checkpoint` | 副本同步进度 | ISR 抖动时观察它 |

### 3.3 单节点最容易踩的坑：内部主题副本因子

单节点集群如果只设了 `KAFKA_DEFAULT_REPLICATION_FACTOR=1`，消费组相关功能依然不可用。原因是官方镜像把 `offsets.topic.replication.factor` 默认设成了 3，`__consumer_offsets` 在单 broker 上创建失败，而 broker 的日志只有一行行的 INFO：

```text
$ docker logs kafka-single | grep auto-creation | tail -3
[2026-09-20 15:08:39,143] INFO Sent auto-creation request for Set(__consumer_offsets) to the active controller. (kafka.server.DefaultAutoTopicCreationManager)
[2026-09-20 15:08:39,673] INFO Sent auto-creation request for Set(__consumer_offsets) to the active controller. (kafka.server.DefaultAutoTopicCreationManager)
[2026-09-20 15:08:40,019] INFO Sent auto-creation request for Set(__consumer_offsets) to the active controller. (kafka.server.DefaultAutoTopicCreationManager)
```

表现是「生产能写、消费组一直超时」，很容易误判成网络问题：

```text
$ kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders --from-beginning --max-messages 3 --timeout-ms 15000
ERROR Error processing message, terminating consumer process:  (org.apache.kafka.tools.consumer.ConsoleConsumer)
org.apache.kafka.common.errors.TimeoutException
Processed a total of 0 messages
```

对照验证：不指定消费组、直接指定分区消费是正常的，说明网络和消息本身都没问题。

```text
$ kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders --offset earliest --partition 0 --max-messages 2
v2
v3
Processed a total of 2 messages
```

修好之后的生效配置（`STATIC_BROKER_CONFIG` 表示来自 server.properties / 环境变量）：

```text
$ kafka-configs.sh --describe --entity-type brokers --entity-name 1 --all | grep -E 'offsets.topic.replication.factor|transaction.state.log.replication.factor'
  offsets.topic.replication.factor=1 sensitive=false synonyms={STATIC_BROKER_CONFIG:offsets.topic.replication.factor=1, DEFAULT_CONFIG:offsets.topic.replication.factor=3}
  transaction.state.log.replication.factor=1 sensitive=false synonyms={STATIC_BROKER_CONFIG:transaction.state.log.replication.factor=1, DEFAULT_CONFIG:transaction.state.log.replication.factor=3}
```

同一个 `synonyms` 字段还能反查出配置来源（静态配置 / 默认值 / 动态配置），排查「为什么这个参数不是我以为的值」时非常有用。

### 3.4 裸机部署：二进制包 + systemd（实测）

容器镜像把 server.properties 藏起来了，要真正理解 Kafka 的配置，还是得看裸机部署。完整脚本见 `examples/scripts/04-native-systemd.sh`，下面是关键步骤与真实输出。

第一步，安装与目录准备：

```text
$ useradd --system --home /opt/kafka --shell /usr/sbin/nologin kafka
$ tar -xzf kafka_2.13-4.1.2.tgz -C /opt && ln -sfn /opt/kafka_2.13-4.1.2 /opt/kafka
$ ls -l /opt | grep kafka
lrwxrwxrwx  1 root  root    21  9月 20 23:48 kafka -> /opt/kafka_2.13-4.1.2
drwxr-xr-x  8 root  root  4096  9月 20 23:48 kafka_2.13-4.1.2
drwxr-xr-x 55 kafka kafka 4096  9月 20 23:51 kafka-data

$ ls /opt/kafka/bin | wc -l
44
```

44 个命令行脚本都在 `bin/` 下（4.x 里已经没有 ZooKeeper 相关脚本了）。

第二步，踩第一个坑：GC 日志目录的权限。这是本机第一次以 systemd 启动时的真实报错：

```text
$ mkdir: 无法创建目录 "/opt/kafka/bin/../logs": 权限不够
$ Error opening log file '/opt/kafka/bin/../logs/kafkaServer-gc.log': No such file or directory
$ Invalid -Xlog option '-Xlog:gc*:file=/opt/kafka/bin/../logs/kafkaServer-gc.log:time,tags:filecount=10,filesize=100M', see error log for details.
$ Error: Could not create the Java Virtual Machine.
$ Error: A fatal exception has occurred. Program will exit.
```

原因：`kafka-server-start.sh` 默认把 GC 日志写到 `$KAFKA_HOME/logs`（也就是 `/opt/kafka/logs`），而解压出来的目录属主是 root，`kafka` 用户既不能创建这个目录、也不能写。解法：

```bash
mkdir -p /opt/kafka/logs
chown -R kafka:kafka /opt/kafka/logs /opt/kafka-data
```

（也可以用 `LOG_DIR` 环境变量把日志指到 `/var/log/kafka`，再配合 systemd 的 `LogsDirectory=`。）

第三步，KRaft 配置文件（生产上按这个骨架改）：

```properties
############################# KRaft 身份 #############################
node.id=1
process.roles=broker,controller
controller.quorum.voters=1@localhost:9093

############################# 监听器 #############################
listeners=PLAINTEXT://:9092,CONTROLLER://:9093
advertised.listeners=PLAINTEXT://localhost:9092
listener.security.protocol.map=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
inter.broker.listener.name=PLAINTEXT
controller.listener.names=CONTROLLER

############################# 存储 #############################
log.dirs=/opt/kafka-data
num.partitions=3
default.replication.factor=1
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1

############################# 保留 #############################
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
log.cleaner.enable=true

############################# 消费组 #############################
group.initial.rebalance.delay.ms=0
offsets.retention.minutes=10080
```

第四步，生成集群 ID 并格式化存储目录（KRaft 独有的两步，ZooKeeper 时代没有）：

```text
$ kafka-storage.sh random-uuid
iU_Ctn7zT-O2UvrjWdHlvA

$ kafka-storage.sh format -t $CLUSTER_ID -c config/kraft-single.properties
Formatting metadata directory /opt/kafka-data with metadata.version 4.1-IV1.

$ cat /opt/kafka-data/meta.properties
#
#Sun Sep 20 23:24:18 CST 2026
cluster.id=iU_Ctn7zT-O2UvrjWdHlvA
directory.id=myEgn1EKB3taOCIvd5ueSg
node.id=1
version=1
```

第五步，systemd unit（`/etc/systemd/system/kafka.service`）：

```ini
[Unit]
Description=Apache Kafka 4.1.2 (KRaft mode, combined broker+controller)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=kafka
Group=kafka
# 堆内存不用大：Kafka 的性能主要来自操作系统页缓存，堆通常 6~8GB 足够
Environment="KAFKA_HEAP_OPTS=-Xmx1G -Xms1G"
# JMX：Prometheus JMX Exporter / JmxTool 从这里采集指标
Environment="JMX_PORT=9101"
Environment="KAFKA_OPTS=-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=9101 -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Djava.rmi.server.hostname=127.0.0.1"
# 文件句柄：segment 文件与连接都占 fd，默认 1024 远远不够
LimitNOFILE=100000
# 注意：Kafka 默认把 GC 日志写到 $KAFKA_HOME/logs，该目录要预先建好并授权给 kafka 用户
KillSignal=SIGTERM
TimeoutStopSec=60
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft-single.properties
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

第六步，启动并验证（真实输出）：

```text
$ systemctl daemon-reload && systemctl enable --now kafka
$ systemctl status kafka --no-pager
● kafka.service - Apache Kafka 4.1.2 (KRaft mode, combined broker+controller)
     Loaded: loaded (/etc/systemd/system/kafka.service; enabled; preset: enabled)
     Active: active (running) since Sun 2026-09-20 23:48:17 CST; 25s ago
   Main PID: 2303359 (java)
      Tasks: 112 (limit: 21075)
     Memory: 403.4M (peak: 414.5M)
        CPU: 6.430s
     CGroup: /system.slice/kafka.service

$ journalctl -u kafka -n 15 --no-pager
... [BrokerLifecycleManager id=1] The broker has been unfenced. Transitioning from RECOVERY to RUNNING.
... Awaiting socket connections on 0.0.0.0:9092.
... [BrokerServer id=1] Transition from STARTING to STARTED
... Kafka version: 4.1.2
... [KafkaRaftServer nodeId=1] Kafka Server started

$ ss -lntp | grep -E '9092|9093|9101'
LISTEN 0 50  *:9093  *:*  users:(("java",pid=2303359,fd=135))
LISTEN 0 50  *:9092  *:*  users:(("java",pid=2303359,fd=167))
LISTEN 0 50  *:9101  *:*  users:(("java",pid=2303359,fd=116))
```

日志里两个 KRaft 专属信号值得记住：`The broker has been unfenced`（节点完成注册、开始对外服务）与 `Kafka Server started`（完整就绪）。

第七步，用发行包自带的 CLI 验证业务可用（不依赖容器）：

```text
$ /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
__consumer_offsets
native-demo

$ printf 'native-1\nnative-2\nnative-3\n' | kafka-console-producer.sh --bootstrap-server localhost:9092 --topic native-demo
$ kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic native-demo --from-beginning --max-messages 3 --timeout-ms 15000
native-1
native-2
native-3
Processed a total of 3 messages
```

第八步，JMX 指标采集（监控章节用的就是这套方式）：

```text
# 4.x 里类名带 org.apache.kafka.tools 前缀，老的 kafka.tools.JmxTool 会报 ClassNotFoundException
$ kafka-run-class.sh org.apache.kafka.tools.JmxTool \
    --object-name 'kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec' \
    --jmx-url service:jmx:rmi:///jndi/rmi://127.0.0.1:9101/jmxrmi --one-time true
Trying to connect to JMX url: service:jmx:rmi:///jndi/rmi://127.0.0.1:9101/jmxrmi
"time","...MessagesInPerSec:Count","...:FifteenMinuteRate","...:MeanRate","...:OneMinuteRate","...:RateUnit"
1789919465376,6,messages,0.006520387263988433,0.01871620354479334,0.10597531929506099,0.0722345473842117,SECONDS

# 其它关键指标（一次性采样）
$ JmxTool --object-name 'kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions' ... --one-time true
1789919474301,0                                     # 欠副本分区数 = 0，健康

$ JmxTool --object-name 'kafka.server:type=ReplicaManager,name=PartitionCount' ... --one-time true
1789919475362,52                                    # 分区总数（含 50 个 __consumer_offsets）

$ JmxTool --object-name 'kafka.controller:type=KafkaController,name=ActiveControllerCount' ... --one-time true
1789919476447,1                                     # 恰好 1 个活跃 controller（KRaft 下也保留了这个指标）

$ JmxTool --object-name 'kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent' ... --one-time true
1789919477461,...,1.955992814186882,NANOSECONDS      # IO 线程空闲率，低于 0.3 说明处理不过来

$ JmxTool --object-name 'kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec' ... --one-time true
1789919478361,704,bytes,...,7.797867539486169,SECONDS
```

第九步，优雅停止与数据持久化验证：

```text
$ systemctl stop kafka
$ journalctl -u kafka -n 4 --no-pager
... kafka.service: Main process exited, code=exited, status=143/n/a     # 143 = 128+15，即收到 SIGTERM
... kafka.service: Consumed 10.209s CPU time, 414.5M memory peak

$ systemctl start kafka && systemctl is-active kafka
active

# 重启后主题与消息都还在（数据落在 /opt/kafka-data，属主是 kafka）
$ kafka-topics.sh --bootstrap-server localhost:9092 --list
__consumer_offsets
native-demo
```

注意 `Restart=on-failure` 与 `status=143` 的组合：正常 `systemctl stop` 也会让 JVM 以 143 退出，systemd 会把它记为一次「失败」，因此 `systemctl is-active` 在停止后短暂显示 `failed`。如果希望「手工停止不算失败」，加 `SuccessExitStatus=143` 即可。

数据目录的真实样子（节选）：

```text
$ ls /opt/kafka-data | head -12
__cluster_metadata-0
__consumer_offsets-0
__consumer_offsets-1
__consumer_offsets-10
...
__consumer_offsets-9
.lock
bootstrap.checkpoint
cleaner-offset-checkpoint
log-start-offset-checkpoint
meta.properties
native-demo-0
native-demo-1
recovery-point-offset-checkpoint
replication-offset-checkpoint
```

`__consumer_offsets-0..49` 一共 50 个分区（`offsets.topic.num.partitions` 默认 50），这是单机实验里"分区数最多"的地方，容易误以为数据量很大。

### 3.5 部署选择清单

```text
开发/测试
  docker compose 单节点，auto.create.topics.enable=true，内部主题副本数显式设 1
生产
  3 个 broker（最少）+ 3 个 controller（可分离部署）
  replication.factor=3、min.insync.replicas=2、acks=all、幂等开启
  auto.create.topics.enable=false（主题由运维或 IaC 统一创建）
  log.dirs 单独挂盘（推荐 XFS/EXT4，禁用 NFS），ulimit -n 不低于 100000
  JMX 或 Prometheus 采集开启，重点看 UnderReplicatedPartitions、ISR、RequestQueue
```

### 3.6 四种 broker 端口与监听器速查

| 监听器 | 用途 | 常见误区 |
|---|---|---|
| `PLAINTEXT` | 客户端与 broker 之间的明文通道 | `advertised.listeners` 写了容器内地址导致宿主机客户端连不上 |
| `CONTROLLER` | KRaft 内部选举与元数据复制 | 与 broker 端口混用、或忘了在 `listener.security.protocol.map` 里声明 |
| `SSL` / `SASL_SSL` | 加密与认证 | 证书换了只重启部分节点，导致握手失败 |
| `INTERNAL` / `EXTERNAL` | 云上常见的内外网分离 | 内网用了公网地址，跨区流量与费用暴涨 |

`advertised.listeners` 是新手第一大坑：它是 broker 告诉客户端「你应该用这个地址来找我」的地址。写错了，客户端第一次连接成功、随后拿到错误的元数据就再也连不上：

```text
容器内跑客户端，broker 通告 localhost:9092  -> 能连
宿主机跑客户端，broker 通告 kafka-1:9092   -> DNS 解析失败，报 UnknownHostException
云上跨网访问，broker 通告内网 IP           -> 客户端连内网地址不通，超时
```

## 4. 命令行工具全解

Kafka 发行包的 `bin/` 下有 40 个脚本，日常真正用到的就是十来个。本章按「看一眼集群 → 建主题 → 收发消息 → 管消费组 → 查位移 → 改配置 → 看文件」的顺序讲，所有输出都是本机实测。

约定：容器部署用 `docker exec kafka-single /opt/kafka/bin/xxx.sh`；裸机部署直接用 `/opt/kafka/bin/xxx.sh`；两者命令完全一致。

### 4.1 集群速查

```text
$ kafka-broker-api-versions.sh --bootstrap-server localhost:9092 | head -5
localhost:9092 (id: 1 rack: null isFenced: false) -> (
        Produce(0): 0 to 13 [usable: 13],
        Fetch(1): 4 to 18 [usable: 18],
        ListOffsets(2): 1 to 10 [usable: 10],
        Metadata(3): 0 to 13 [usable: 13],
...

$ kafka-cluster.sh cluster-id --bootstrap-server localhost:9092
Cluster ID: 5L6g3nShT-eMCtK--X86sw
```

`kafka-broker-api-versions.sh` 输出的是每个 broker 支持的协议版本区间，排查「客户端太新/太旧」时第一眼就看它：

```text
usable: 13                    客户端能用到的最高版本
isFenced: false               节点是否被隔离（KRaft 里被 fencing 的节点不接客）
id: 1 / rack: null            节点 ID 与机架；机架用于跨机架副本分配
```

### 4.2 主题管理

```text
$ kafka-topics.sh --bootstrap-server localhost:9092 --list
auto-created-topic
demo-java
demo-orders
...

$ kafka-topics.sh --bootstrap-server localhost:9092 --create --topic orders --partitions 3 --replication-factor 1
Created topic orders.

$ kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic orders
Topic: orders   TopicId: VPyFaStOQ1qN17P2wD6q8A    PartitionCount: 3   ReplicationFactor: 1   Configs: min.insync.replicas=1,segment.bytes=1073741824,max.message.bytes=1048588
        Topic: orders   Partition: 0   Leader: 1   Replicas: 1   Isr: 1   Elr:   LastKnownElr:
        Topic: orders   Partition: 1   Leader: 1   Replicas: 1   Isr: 1   Elr:   LastKnownElr:
        Topic: orders   Partition: 2   Leader: 1   Replicas: 1   Isr: 1   Elr:   LastKnownElr:
```

describe 输出要会读：

```text
TopicId              主题的唯一 ID（改过名的主题靠它识别，运维脚本用它做幂等）
PartitionCount       分区数
ReplicationFactor    副本因子
Configs              显式设置的 + 未被默认值覆盖的关键配置
Partition / Leader   分区号与该分区当前 Leader 的 broker ID
Replicas             副本所在 broker 列表（第一个是"首选 Leader"）
Isr                  当前与 Leader 保持同步的副本；Isr 少于 Replicas 就是欠副本
Elr / LastKnownElr   Kafka 4.x 新增的「ELR（Eligible Leader Replicas）」字段，用于不支持 ISR 时的可用副本集
```

三个真实的报错（比看文档记得牢）：

```text
# 1. 副本数超过 broker 数量
$ kafka-topics.sh --bootstrap-server localhost:9092 --create --topic too-many-replicas --partitions 1 --replication-factor 3
Error while executing topic command : Unable to replicate the partition 3 time(s): The target replication factor of 3 cannot be reached because only 1 broker(s) are registered.
 (org.apache.kafka.tools.TopicCommand)

# 2. 重复创建
$ kafka-topics.sh --bootstrap-server localhost:9092 --create --topic orders --partitions 3 --replication-factor 1
Error while executing topic command : Topic 'orders' already exists.
 (org.apache.kafka.tools.TopicCommand)

# 3. 删除后再 describe（删除是异步的）
Error while executing topic command : Topic 'ttl-demo' does not exist as expected
```

常用的增删改：

```bash
# 增加分区（只能增加，不能减少；已有数据不会重新分配）
kafka-topics.sh --bootstrap-server localhost:9092 --alter --topic orders --partitions 6

# 删除主题（要确认 delete.topic.enable=true，4.x 默认就是 true）
kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic orders

# 只列出欠副本的分区（集群健康检查最常用的一条）
kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-replicated-partitions

# 只列出不可用分区
kafka-topics.sh --bootstrap-server localhost:9092 --describe --unavailable-partitions

# 看主题级配置（未显式设置的显示为默认值）
kafka-configs.sh --bootstrap-server localhost:9092 --describe --entity-type topics --entity-name orders --all
```

### 4.3 收发消息（联调利器）

```text
$ printf 'order-1:v1\norder-2:v2\n...' | kafka-console-producer.sh --bootstrap-server localhost:9092 \
    --topic demo-orders --property parse.key=true --property key.separator=:
写入完成

$ kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic demo-orders --from-beginning \
    --max-messages 8 --timeout-ms 20000 --property print.partition=true --property print.key=true --property key.separator=' -> '
Partition:0 -> order-2 -> v2
Partition:0 -> order-3 -> v3
Partition:0 -> order-2 -> v5
Partition:0 -> order-3 -> v6
Partition:0 -> order-2 -> v8
Partition:1 -> order-1 -> v1
Partition:1 -> order-1 -> v4
Partition:1 -> order-1 -> v7
Processed a total of 8 messages

$ kafka-console-consumer.sh ... | grep order-2      # 同一 key 的三个分区号完全相同
Partition:0 -> order-2 -> v2
Partition:0 -> order-2 -> v5
Partition:0 -> order-2 -> v8
```

三条实战经验：

```text
1. 一定要加 --timeout-ms。不加时消费者会一直等新消息，脚本/CI 会永久挂住（本机踩过：一条 400 秒的挂起）。
2. --max-messages 直接退出；只想看某分区用 --partition N --offset earliest。
3. 生产/消费用 --property 打印 key、分区、offset、时间戳，排查分区倾斜问题时能一眼看出。
```

常用参数速查：

| 参数 | 作用 |
|---|---|
| `--from-beginning` | 从最早可读位移开始（等价 `--offset earliest`） |
| `--offset latest` | 只读从现在开始产生的消息 |
| `--partition N --offset M` | 指定分区与位移，不需要消费组 |
| `--group G` | 用消费组消费，位移会提交到 `__consumer_offsets` |
| `--isolation-level read_committed` | 只读已提交的事务消息 |
| `--property print.timestamp=true` | 打印消息时间戳 |
| `--property print.headers=true` | 打印消息头（排查死信、链路追踪时必用） |
| `--max-messages N` / `--timeout-ms T` | 退出条件，脚本里必须二选一 |

### 4.4 消费组与位移

```text
$ kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group order-cg

GROUP           TOPIC           PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG   CONSUMER-ID  HOST       CLIENT-ID
order-cg        demo-orders     2          0               0               0     -            -          -
order-cg        demo-orders     1          3               3               0     -            -          -
order-cg        demo-orders     0          5               5               0     -            -          -

$ kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
order-cg
console-consumer-97875
console-consumer-61142
console-consumer-80400
```

四列必须会读：

```text
CURRENT-OFFSET   消费组已提交的位移（下一条要读的位置）
LOG-END-OFFSET   分区最新位移
LAG              LOG-END-OFFSET - CURRENT-OFFSET，积压量；LAG 持续增长说明消费能力不足
CONSUMER-ID      为空（"-"）表示当前没有活跃消费者，位移是历史提交值
```

组内两个消费者时的分区分配（每行是一个「消费者 × 分区」的归属）：

```text
$ kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group rebalance-cg

GROUP          TOPIC         PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  CONSUMER-ID                                          HOST       CLIENT-ID
rebalance-cg   demo-orders   1          3               3               0    console-consumer-4b16bbad-bdb5-42ef-ade9-62a8f689df67 /127.0.0.1 console-consumer
rebalance-cg   demo-orders   0          5               5               0    console-consumer-4b16bbad-bdb5-42ef-ade9-62a8f689df67 /127.0.0.1 console-consumer
rebalance-cg   demo-orders   2          0               0               0    console-consumer-7d05ff4b-3abb-4775-b535-59e7c6fd7563 /127.0.0.1 console-consumer
```

两个消费者分担 3 个分区（一个拿 2 个、一个拿 1 个），这就是「消费者数不能超过分区数」的实际表现：再启动第三个消费者，它会一直拿不到分区而空转。

位移重置（改 bug 后重放、跳过坏消息的常用手段）：

```text
$ kafka-consumer-groups.sh --bootstrap-server localhost:9092 --reset-offsets --group order-cg \
    --topic demo-orders --to-earliest --execute

GROUP                          TOPIC                          PARTITION  NEW-OFFSET
order-cg                       demo-orders                    0          0
order-cg                       demo-orders                    1          0
order-cg                       demo-orders                    2          0

$ kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group order-cg
order-cg        demo-orders     2          0               0               0     -   -   -
order-cg        demo-orders     1          0               3               3     -   -   -
order-cg        demo-orders     0          0               5               5     -   -   -
```

重置的四种目标与注意事项：

```bash
--to-earliest          回到该分区最早可读位移
--to-latest            直接跳到最新（等于放弃积压）
--to-offset 100        跳到指定位移
--to-datetime 2026-09-20T00:00:00.000   按时间重放
--shift-by -100        相对回退 100 条（负数回退，正数前进）
--dry-run              先看结果不执行（重要操作务必先跑一遍）

执行前提：该消费组必须没有活跃消费者，否则报 "Assignments can only be reset if the group is inactive"
```

### 4.5 配置管理

```text
$ kafka-configs.sh --bootstrap-server localhost:9092 --describe --entity-type brokers --entity-name 1 --all | grep -E 'offsets.topic.replication.factor|log.retention.check.interval.ms'
  log.retention.check.interval.ms=5000 sensitive=false synonyms={STATIC_BROKER_CONFIG:log.retention.check.interval.ms=5000, DEFAULT_CONFIG:log.retention.check.interval.ms=300000}
  offsets.topic.replication.factor=1 sensitive=false synonyms={STATIC_BROKER_CONFIG:offsets.topic.replication.factor=1, DEFAULT_CONFIG:offsets.topic.replication.factor=3}
```

`synonyms` 是排查配置来源的关键：它告诉你是「静态配置（server.properties / 环境变量）」、「动态配置（kafka-configs 改的）」还是「默认值」。动态配置优先级最高，且不用重启：

```bash
# 主题级动态配置（立即生效）
kafka-configs.sh --bootstrap-server localhost:9092 --alter --entity-type topics --entity-name orders \
  --add-config retention.ms=86400000,max.message.bytes=10485760

# 查看某个主题的动态覆盖项
kafka-configs.sh --bootstrap-server localhost:9092 --describe --entity-type topics --entity-name orders

# 删除动态配置（回落到默认值）
kafka-configs.sh --bootstrap-server localhost:9092 --alter --entity-type topics --entity-name orders \
  --delete-config retention.ms
```

不是所有参数都能动态改。本机实测的反例（这是个必须记住的边界）：

```text
$ kafka-configs.sh --bootstrap-server localhost:9092 --alter --entity-type brokers --entity-name 1 \
    --add-config log.retention.check.interval.ms=5000
java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.InvalidRequestException: Cannot update these configs dynamically: Set(log.retention.check.interval.ms)
Caused by: org.apache.kafka.common.errors.InvalidRequestException: Cannot update these configs dynamically: Set(log.retention.check.interval.ms)
```

判断方法：broker 配置里凡是标了 `DYNAMIC_BROKER_CONFIG` 支持的才能改；`log.retention.check.interval.ms`、`log.dirs`、`num.network.threads` 这类属于**静态配置**，只能改配置文件后重启。

### 4.6 数据文件与位移查询

```text
$ docker exec kafka-single ls -la /var/lib/kafka/data/demo-orders-0
total 20
drwxr-xr-x  2 appuser appuser     4096 Sep 20 15:12 .
-rw-r--r--  1 appuser appuser 10485760 Sep 20 15:12 00000000000000000000.index
-rw-r--r--  1 appuser appuser      141 Sep 20 15:12 00000000000000000000.log
-rw-r--r--  1 appuser appuser 10485756 Sep 20 15:12 00000000000000000000.timeindex
-rw-r--r--  1 appuser appuser        8 Sep 20 15:12 leader-epoch-checkpoint
-rw-r--r--  1 appuser appuser       43 Sep 20 15:12 partition.metadata

$ kafka-dump-log.sh --files /var/lib/kafka/data/demo-orders-0/00000000000000000000.log --print-data-log
Dumping /var/lib/kafka/data/demo-orders-0/00000000000000000000.log
Log starting offset: 0
baseOffset: 0 lastOffset: 4 count: 5 baseSequence: 0 lastSequence: 4 producerId: 1000 producerEpoch: 0 partitionLeaderEpoch: 0 isTransactional: false isControl: false deleteHorizonMs: OptionalLong.empty position: 0 CreateTime: 1789917130802 size: 141 magic: 2 compresscodec: none crc: 2095750176 isvalid: true
| offset: 0 CreateTime: 1789917130801 keySize: 7 valueSize: 2 sequence: 0 headerKeys: [] key: order-2 payload: v2
| offset: 1 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 1 headerKeys: [] key: order-3 payload: v3
| offset: 2 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 2 headerKeys: [] key: order-2 payload: v5
| offset: 3 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 3 headerKeys: [] key: order-3 payload: v6
| offset: 4 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 4 headerKeys: [] key: order-2 payload: v8
```

这段输出信息量很大：

```text
一个 .log 文件里是一条条「消息批次（RecordBatch）」，不是一个批次一条消息
baseOffset: 0 lastOffset: 4 count: 5      该批次覆盖的位移区间与条数（一次原子写入）
producerId: 1000 producerEpoch: 0         生产者 ID 与纪元：幂等生产者的身份
baseSequence..lastSequence                批内序号，broker 靠它去重（幂等的实现基础）
partitionLeaderEpoch                      写入时的 Leader 纪元，用于副本一致性校验
magic: 2                                  Kafka 0.11 之后的格式；magic 0/1 已不再支持
crc / isvalid                             批次校验和，磁盘位翻转时能识别出来
compresscodec: none                       压缩算法（这里是没压缩）
```

索引文件为什么是 10MB？因为 `log.index.size.max.bytes` 默认 10MB 且**预分配**，实际是稀疏文件。分区目录看着几十 MB，真实占用要看 `du --apparent-size` 与 `kafka-log-dirs.sh`。

位移查询工具在 4.x 换了包名与参数（3.x 老脚本会直接报 ClassNotFound）：

```text
# 4.x 正确写法
$ kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic perf-test --time -2
perf-test:0:0
perf-test:1:0
perf-test:2:0

$ kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic ttl-check --time -1
ttl-check:0:3

# 3.x 的老写法在 4.x 报错
$ kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic ttl-check --time -1
Error: Could not find or load main class kafka.tools.GetOffsetShell
Error occurred: broker-list is not a recognized option
```

`--time` 三个取值：`-1` 最新位移、`-2` 最早可读位移、时间戳（毫秒）按时间查位移。

### 4.7 磁盘占用与清理

```text
$ kafka-log-dirs.sh --bootstrap-server localhost:9092 --topic-list perf-test --describe | tail -2
{"brokers":[{"broker":1,"logDirs":[{"partitions":[{"partition":"perf-test-0","size":34541004,"offsetLag":0,"isFuture":false},{"partition":"perf-test-1","size":34627199,"offsetLag":0,"isFuture":false},{"partition":"perf-test-2","size":34639580,"offsetLag":0,"isFuture":false}],"error":null,"logDir":"/var/lib/kafka/data"}]}],"version":1}
```

哪个分区占盘多、哪个目录快满了，看它最直接。磁盘水位告警应该基于这个指标，而不是整个数据盘的使用率：

```bash
# 单分区删除到指定位移（清理坏数据/降低保留范围；慎用）
kafka-delete-records.sh --bootstrap-server localhost:9092 --offset-json-file delete.json

# delete.json 内容
{"partitions":[{"topic":"perf-test","partition":0,"offset":50000}],"version":1}
```

### 4.8 性能测试

```text
$ kafka-producer-perf-test.sh --topic perf-test --num-records 100000 --record-size 1024 --throughput -1 \
    --producer-props bootstrap.servers=localhost:9092 acks=1 batch.size=16384 linger.ms=5 compression.type=lz4
100000 records sent, 24142.9 records/sec (23.58 MB/sec), 1022.82 ms avg latency, 2296.00 ms max latency, 742 ms 50th, 2243 ms 95th, 2287 ms 99th, 2294 ms 99.9th.

$ kafka-consumer-perf-test.sh --bootstrap-server localhost:9092 --topic perf-test --messages 100000 --group perf-cg --timeout 60000
start.time, end.time, data.consumed.in.MB, MB.sec, data.consumed.in.nMsg, nMsg.sec, rebalance.time.ms, fetch.time.ms, fetch.MB.sec, fetch.nMsg.sec
2026-09-20 15:14:10:647, 2026-09-20 15:14:11:754, 97.6563, 88.2170, 100000, 90334.2367, 372, 735, 132.8656, 136054.4218

$ kafka-log-dirs.sh --topic-list perf-test --describe   # 10 万条 × 1KB = 原始 100MB，落盘
"partition":"perf-test-0","size":34541004 / perf-test-1: 34627199 / perf-test-2: 34639580   # 合计约 103MB
```

怎么读这几个数：

```text
records/sec 24142        生产者吞吐（单节点、单进程、1KB 消息）
MB/sec 23.58             上面换算成带宽
1022ms avg latency       平均端到端延迟；这里偏高是因为瓶颈在磁盘/CPU 争用（同机还跑着别的服务）
50th/95th/99th           分位延迟，比平均值更能反映用户体验
consumer: 90334 rec/s    消费者吞吐；fetch.MB.sec 是纯拉取速率
```

两点提醒：

1. 这台机器是共享环境（同机跑着数据库、CI、其他容器），数字只用于**对比相对变化**（改参数前后），不要拿它当集群选型依据。
2. 测试数据是随机字节，lz4 压不动，所以落盘 103MB ≈ 原始 100MB。真实业务日志（文本重复度高）压缩率通常 3~5 倍，磁盘规划要按实际数据类型估算。

参数调优的对照实验方法：

```bash
# 只改一个变量，其它保持默认，看吞吐与 99 线延迟变化
# 变量 1：批量与延迟（吞吐 vs 实时性的经典权衡）
--producer-props batch.size=16384 linger.ms=5      # 攒批 16KB 或最多等 5ms
--producer-props batch.size=16384 linger.ms=0      # 不等待，吞吐会掉
--producer-props batch.size=1048576 linger.ms=50   # 大攒批，吞吐高但延迟高

# 变量 2：确认级别
--producer-props acks=1        # 只写 leader，最快但有丢消息风险
--producer-props acks=all      # 等全部 ISR，慢一些但可配 min.insync.replicas 保证不丢

# 变量 3：压缩
--producer-props compression.type=none|lz4|snappy|zstd
```

## 5. 存储格式与保留策略

### 5.1 分区 = 目录，消息 = 追加写的日志文件

```text
/var/lib/kafka/data/demo-orders-0/          分区目录，命名规则 {topic}-{partition}
├── 00000000000000000000.log                消息日志，文件名是「该文件第一条消息的位移」
├── 00000000000000000000.index              位移索引：offset -> 物理位置
├── 00000000000000000000.timeindex          时间戳索引：时间 -> 位移
├── leader-epoch-checkpoint                 Leader 纪元变更历史
└── partition.metadata                      分区元数据（topicId）
```

滚动规则：当前 segment 超过 `log.segment.bytes`（默认 1GB）或超过 `log.roll.ms/hours`（默认 7 天）就切一个新文件，文件名是该新文件第一条消息的位移（所以会看到 `00000000000000000000.log`、`00000000000000064426.log` 这种）。

为什么按 segment 滚动，而不是一条一个文件或全部一个文件：

```text
一条一个文件  -> 元数据爆炸、顺序读变随机读
一个分区一个文件 -> 无法删除旧数据（删除必须整文件）
segment 折中  -> 顺序写（性能）+ 整段删除（保留策略可实现）+ 稀疏索引加速定位
```

### 5.2 三段式查找：Kafka 怎么在 TB 级日志里秒定位一条消息

```text
消费者要读 offset = 36,400,000 的消息
  1. 二分查找 segment 文件名 -> 定位到 0000000000000036000000.log
  2. 查该文件的 .index（稀疏索引，每 log.index.interval.bytes=4096 字节记一条）
     -> 找到一条比目标小的最大 offset 对应的物理位置
  3. 从该物理位置开始顺序扫描（最多几千字节）-> 命中目标消息
```

稀疏索引是「空间/时间折中」的经典设计：索引只有 10MB 上限（`log.index.size.max.bytes`），不可能记录每条消息；用「二分 + 少量顺序扫描」把查找压到毫秒级。

### 5.3 消息格式：一个批次里装多条消息（dump-log 实测）

```text
$ kafka-dump-log.sh --files /var/lib/kafka/data/demo-orders-0/00000000000000000000.log --print-data-log
baseOffset: 0 lastOffset: 4 count: 5 baseSequence: 0 lastSequence: 4 producerId: 1000 producerEpoch: 0
partitionLeaderEpoch: 0 isTransactional: false isControl: false deleteHorizonMs: OptionalLong.empty
position: 0 CreateTime: 1789917130802 size: 141 magic: 2 compresscodec: none crc: 2095750176 isvalid: true
| offset: 0 CreateTime: 1789917130801 keySize: 7 valueSize: 2 sequence: 0 headerKeys: [] key: order-2 payload: v2
| offset: 1 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 1 headerKeys: [] key: order-3 payload: v3
| offset: 2 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 2 headerKeys: [] key: order-2 payload: v5
| offset: 3 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 3 headerKeys: [] key: order-3 payload: v6
| offset: 4 CreateTime: 1789917130802 keySize: 7 valueSize: 2 sequence: 4 headerKeys: [] key: order-2 payload: v8
```

从这段真实输出能读出的设计要点：

| 字段 | 作用 |
|---|---|
| `baseOffset` / `lastOffset` / `count` | 批次覆盖的位移区间与条数；一个批次一次原子写入，压缩也以批次为单位 |
| `producerId` / `producerEpoch` | 幂等生产者的身份；同一 PID+Epoch 的重试会被 broker 按序号去重 |
| `baseSequence` / `lastSequence` | 批内消息序号，配合 PID 实现「不重复」 |
| `partitionLeaderEpoch` | 写入时的 Leader 纪元，副本间用它判断谁的数据更新（避免脑裂后数据回滚错乱） |
| `magic: 2` | 消息格式版本；Kafka 4.0 起只支持 2（0/1 已删除） |
| `crc` / `isvalid` | 批次校验和，磁盘位翻转能被检测出来 |
| `compresscodec` | 压缩单位是批次，不是单条消息 |

所以「Kafka 压缩能省带宽和磁盘」的前提是**攒批**：`batch.size` 太小、`linger.ms=0` 时每个批次只有一条消息，压缩几乎没有收益。

### 5.4 保留策略：按时间/大小清理

三种清理策略（`cleanup.policy`）：

```text
delete（默认）  按 retention.ms / retention.bytes 删除整个 segment
compact         按 key 压实：保留每个 key 的最新值（适合变更日志、状态恢复）
compact,delete  两者都做：压实 + 按时间删除旧数据
```

按时间删除的实测（这是最容易误解的一处）：创建 `retention.ms=15000` 的主题，写入 3 条，然后观察两个位移：

```text
# 写入后：最新位移 3，最早可读位移 0
$ kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic ttl-check --time -1
ttl-check:0:3
$ kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic ttl-check --time -2
ttl-check:0:0

# 等待 32 秒后：最新位移仍是 3，但最早可读位移前进到 3 —— 说明 0/1/2 已被物理删除
$ kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic ttl-check --time -1
ttl-check:0:3
$ kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic ttl-check --time -2
ttl-check:0:3

# 消费者的实际体验：从最早开始也读不到任何消息
$ kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic ttl-check --from-beginning --timeout-ms 8000
org.apache.kafka.common.errors.TimeoutException
Processed a total of 0 messages

# 分区目录里只剩 .deleted 残留（删除是先重命名、再落盘 unlink）
$ docker exec kafka-single ls -la /var/lib/kafka/data/ttl-check-0
total 36
-rw-r--r--   1 appuser appuser        0 Sep 20 15:19 00000000000000000000.index.deleted
-rw-r--r--   1 appuser appuser       91 Sep 20 15:18 00000000000000000000.log.deleted
-rw-r--r--   1 appuser appuser       12 Sep 20 15:19 00000000000000000000.timeindex.deleted
-rw-r--r--   1 appuser appuser        0 Sep 20 15:19 00000000000000000003.log
-rw-r--r--   1 appuser appuser       56 Sep 20 15:19 00000000000000000003.snapshot
-rw-r--r--   1 appuser appuser 10485756 Sep 20 15:19 00000000000000000003.timeindex

# 对照：没有设置短保留的主题，最早位移仍为 0
$ kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic perf-test --time -2
perf-test:0:0
perf-test:1:0
perf-test:2:0
```

三个必须记住的点：

```text
1. 删除的最小单位是 segment。retention.ms=15s 但 segment 里有「最近」的消息时，
   整段都不会删——所以「设置了 1 小时保留，结果磁盘还是满的」通常不是 bug，
   而是 segment.bytes 太大 + 消息量太小导致的（1GB 一段可能几天才写满）。
   要缩短这个时间窗，把 segment.bytes / segment.ms 一起调小。

2. 位移不会被删除。消息删了，log-end-offset 依然是 3，消费者的提交位移依然有效；
   当消费者要读的位置小于 log-start-offset 时，Kafka 自动跳到最早可用位置
   （或按 auto.offset.reset 处理）。

3. 清理线程默认每 5 分钟跑一次（log.retention.check.interval.ms=300000），
   而且是静态配置，动态改会被拒绝（见 4.5 的实测报错）。
   所以「刚写完就期待过期删除」通常看不到效果。
```

### 5.5 日志压实（compact）与 tombstone

```bash
# 建一个压实主题
kafka-topics.sh --bootstrap-server localhost:9092 --create --topic user-state \
  --partitions 3 --replication-factor 3 \
  --config cleanup.policy=compact \
  --config min.cleanable.dirty.ratio=0.01 \    # 压实触发阈值：脏数据占比
  --config delete.retention.ms=600000          # tombstone 保留时长
```

```text
行为要点：
  同一个 key 的多条消息：保留最后一条，更早的会被清理
  value 为 null 的消息 = tombstone（墓碑），表示「删除该 key」
  tombstone 不会立刻消失，保留 delete.retention.ms（默认 24 小时）后清掉，
    这段时间是留给还没有消费到墓碑的消费者的
  compact 只保证「每个 key 的最终值还在」，位移是跳跃的（不是连续的 0,1,2,3）
  典型用途：Kafka Streams 的状态存储、CDC 场景下「按主键还原当前状态」
```

一个常见误解：compact 不是「去重」的通用手段，它只对 key 语义成立（同一个 key 的最新值有意义）。用 UUID 之类永不重复的 key 做 compact，等于什么也没压实。

### 5.6 磁盘选型与容量规划

```text
文件系统：XFS 或 EXT4；不要用 NFS（Kafka 依赖 fsync 与顺序写，网络文件系统会掉性能）
RAID：RAID10 或 JBOD（多目录多盘，靠副本保证可靠性，不靠 RAID 冗余）
盘容量估算：
    单分区日增数据 = 峰值写入带宽 × 86400 × (1 - 压缩率)
    总容量 = 单分区日增 × 分区数 × 保留天数 × 副本因子 × 1.3（30% 余量）
示例：100 MB/s 峰值、压缩率 70%、保留 3 天、3 副本
    100 × 86400 × 0.3 ≈ 2.5 GB/分区/天
    3 天 × 3 副本 × 1.3 ≈ 每分区约 30 GB；100 个分区就是 3 TB
内存：页缓存越多越好。生产经验值是「数据盘容量 : 内存 ≥ 8:1 时性能开始恶化」
```

### 5.7 磁盘满了会怎样（真实症状）

```text
写入被拒        生产者报 NOT_ENOUGH_REPLICAS / KAFKA_STORAGE_ERROR
ISR 收缩         从节点刷不动盘，跟不上 Leader，ISR 缩小
分区离线        磁盘被写满且无法删除时，分区可能变为不可用（unavailable）
恢复手段        优先删除；然后清理旧的 segment（调小 retention.*）
                其次扩容磁盘或把分区迁移到新盘（kafka-reassign-partitions）
                最后才考虑 force 操作
```

生产上必须有的两条防线：

```bash
# 1. 分区级磁盘水位告警（用 kafka-log-dirs.sh 的 size 做阈值，而不是看整机 df）
# 2. 单分区容量上限（避免一个大分区吃满整个盘）：
#    topic 级配置 max.message.bytes + 业务上限制 key 分布，避免数据全部落在少数分区
```

## 6. 生产者

### 6.1 发送流程

```text
send(record)
  -> 序列化 key/value（Serializer）
  -> 分区器决定分区（有 key 用 murmur2(key) % 分区数；无 key 用粘性分区）
  -> 写入累加器（RecordAccumulator）：按分区攒成批次
  -> Sender 线程按 broker 拉取待发批次
  -> 网络发送 -> broker 写入 -> 按 acks 决定何时返回成功
```

关键点：`send()` 只是把消息放进客户端内存缓冲，**立即返回一个 Future**。真正的网络发送在独立线程里。所以：

```text
producer.send(...).get()     同步等待结果（可靠但慢，适合关键消息）
producer.send(..., callback) 异步回调（高吞吐场景）
producer.flush()             阻塞直到缓冲清空（进程退出前必须调用，否则缓冲里的消息会丢）
```

### 6.2 完整示例（原生客户端）

完整代码见 `examples/java/kafka-client-demo/src/main/java/com/example/kafka/ProducerDemo.java`，核心配置：

```java
Properties props = new Properties();
props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);

// 序列化器：生产环境用 Avro/Protobuf + Schema Registry，JSON 只适合入门
props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

// ---- 可靠性 ----
props.put(ProducerConfig.ACKS_CONFIG, "all");                        // 所有 ISR 落盘才算成功
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");         // 幂等：重试不重复
props.put(ProducerConfig.RETRIES_CONFIG, Integer.toString(Integer.MAX_VALUE));
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, "5"); // 幂等模式下上限就是 5

// ---- 性能 ----
props.put(ProducerConfig.BATCH_SIZE_CONFIG, Integer.toString(16 * 1024)); // 攒批 16KB
props.put(ProducerConfig.LINGER_MS_CONFIG, "10");                         // 最多等 10ms
props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "lz4");                 // 压缩算法
props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, Long.toString(32L * 1024 * 1024));

KafkaProducer<String, String> producer = new KafkaProducer<String, String>(props);
```

### 6.3 实测：同步发送、key 分区、异步回调、指定分区、异常

```text
$ java -cp target/kafka-client-demo-1.0.0-jar-with-dependencies.jar com.example.kafka.ProducerDemo localhost:9092 demo-java
== 1. 同步发送（等 broker 确认，能拿到分区与位移）==
  topic=demo-java partition=1 offset=0 key=order-1
  topic=demo-java partition=0 offset=0 key=order-2
  topic=demo-java partition=0 offset=1 key=order-3
== 2. 相同 key 必落同一分区（分区器对 key 做 murmur2 哈希）==
  key=user-42 -> partition=1 offset=1
  key=user-42 -> partition=1 offset=2
  key=user-42 -> partition=1 offset=3
  key=user-42 -> partition=1 offset=4
  key=user-42 -> partition=1 offset=5
  key=user-42 -> partition=1 offset=6
== 3. 异步发送 + 回调（高吞吐场景）==
  async-2 -> partition=2 offset=0
  async-1 -> partition=1 offset=7
  async-3 -> partition=1 offset=8
== 4. 显式指定分区（业务自己做分区策略时）==
  partition=2 offset=1
== 5. 用非法主题名发送：观察异常类型 ==
  异常: InvalidTopicException - Invalid topics: [bad topic name]
```

四个结论：

```text
1. 同步发送能拿到 partition + offset，是「确认投递」的唯一方式
2. 相同 key 的三条消息位移连续（1..6 -> 7..8），顺序有保证；key 一旦写入就不能再改分区的归属
3. 异步发送的回调顺序不保证（async-2 先于 async-1 返回），但同一分区内 offset 顺序仍然正确
4. 主题名非法时抛 InvalidTopicException；主题不存在且 auto.create.topics.enable=false 时
   抛 UnknownTopicOrPartitionException——这两类属于「代码写错了」，重试没有意义
```

### 6.4 生产端参数速查

| 参数 | 作用 | 默认 | 生产建议 |
|---|---|---|---|
| `acks` | 确认级别：0/1/all | all（3.0+） | 保持 all；不允许丢数据时必须配 min.insync.replicas=2 |
| `enable.idempotence` | 幂等生产者 | true（3.0+） | 保持 true，防止重试导致重复 |
| `retries` | 重试次数 | MAX_VALUE（幂等时） | 保持；配合 `delivery.timeout.ms` 控制总时长 |
| `max.in.flight.requests.per.connection` | 单连接未确认请求数 | 5 | 幂等开启时 5 是安全上限；关闭幂等且要求严格顺序时必须设为 1 |
| `batch.size` | 单分区批次字节上限 | 16384 | 吞吐优先可到 64KB~1MB，注意内存占用 = batch.size × 分区数 |
| `linger.ms` | 攒批等待时间 | 0（3.x 前）/5（4.x 默认 5ms） | 5~50ms 明显提升吞吐，代价是延迟 |
| `compression.type` | 压缩：none/gzip/snappy/lz4/zstd | none | lz4 通用折中；zstd 压缩率更高但 CPU 更贵 |
| `buffer.memory` | 客户端缓冲总大小 | 32MB | 高吞吐场景调大，否则 `send()` 会阻塞在 max.block.ms |
| `max.block.ms` | 缓冲区满/send 阻塞上限 | 60000 | 线程池里的生产者建议调小（如 5000），让业务快速失败 |
| `delivery.timeout.ms` | 从发送到最终成功的总超时 | 120000 | 应 ≥ linger.ms + request.timeout.ms |
| `key.serializer` / `value.serializer` | 序列化器 | 无 | 必填；生产用 Avro/Protobuf，避免上下游强耦合 |

### 6.5 分区的三种选择

```text
按 key 哈希（默认）
    优点：同 key 有序，天然支持「按业务主键分区」
    风险：热点 key（如某个大客户）会把单个分区打满

自定义 Partitioner
    按业务量分流（如 vip 客户单独分区）、或加入随机化避免热点
    注意：分区逻辑一旦上线，改动会破坏「同 key 同分区」的历史数据顺序

显式指定分区
    record = new ProducerRecord<>(topic, partition, key, value)
    适合「业务自己维护分区映射表」的场景，但把分配责任揽到了应用层
```

热点 key 的识别与处理：

```bash
# 识别：看各分区消息量与磁盘占用差异
kafka-log-dirs.sh --bootstrap-server localhost:9092 --topic-list orders --describe
kafka-get-offsets.sh --bootstrap-server localhost:9092 --topic orders   # 各分区位移差异

# 处理：热点 key 加后缀打散（代价是同一实体失去全局有序）
# 例如 "user-42" -> "user-42-{0..9}"，下游按前缀聚合
```

### 6.6 事务生产者：跨主题的原子写

场景：从源主题读一条消息，处理后写入目标主题，同时提交源主题位移——三步必须原子。

```java
producerProps.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "txn-demo-1");   // 事务 ID，必须全局唯一
producerProps.put(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, "60000");     // 事务超时，防止悬挂
producerProps.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");       // 事务隐含要求幂等

producer.initTransactions();
try {
    producer.beginTransaction();
    for (ConsumerRecord<String, String> record : records) {
        producer.send(new ProducerRecord<String, String>(targetTopic, record.key(), "已处理: " + record.value()));
    }
    producer.sendOffsetsToTransaction(currentOffsets(consumer), consumer.groupMetadata());  // 位移也进事务
    producer.commitTransaction();
} catch (Exception e) {
    producer.abortTransaction();   // 目标和位移一起撤销
    throw e;
}
```

消费端必须设 `isolation.level=read_committed`，否则会读到未提交（甚至最终回滚）的消息。

本机实测（真实输出）：

```text
$ java -cp target/kafka-client-demo-1.0.0-jar-with-dependencies.jar com.example.kafka.TransactionDemo localhost:9092 txn-source txn-target
已写入 3 条源消息到 txn-source
事务提交成功，本批处理 3 条
共处理 3 条，写入目标主题 txn-target

# 校验：read_committed 能读到 3 条
$ kafka-console-consumer.sh --topic txn-target --from-beginning --max-messages 3 --property isolation.level=read_committed
tx-1    已处理: 源消息 1
tx-2    已处理: 源消息 2
tx-3    已处理: 源消息 3

# 校验：消费位移是被事务一起提交的
$ kafka-consumer-groups.sh --describe --group txn-demo-group
GROUP           TOPIC       PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
txn-demo-group  txn-source  0          3               3               0
txn-demo-group  txn-source  1          2               2               0
txn-demo-group  txn-source  2          0               0               0
```

事务的三个必须知道的边界：

```text
1. transactional.id 必须全局唯一且稳定。同一 ID 被第二个实例使用时，第一个实例会被
   fencing（broker 抬高 epoch，旧实例的写入被拒），这是防止「僵尸生产者」的关键机制。
2. 事务有超时（transaction.timeout.ms，默认 60s），超时后 broker 主动 Abort，
   避免一个挂掉的生产者把 `__transaction_state` 锁住。
3. 事务只保证「写入原子」，不保证「只写一次」：跨系统的幂等仍然要靠业务键去重。
```

## 7. 消费者与消费组

### 7.1 消费组模型：分工与再平衡

```text
同一消费组内：一个分区同一时刻只能被一个消费者消费（分区互斥）
不同消费组之间：互不影响，各读各的位移（广播语义）

组内变化（消费者加入/退出/订阅变化/分区数变化）-> 触发 Rebalance
```

Rebalance 的三种触发条件与代价：

```text
触发：组内成员增减、订阅主题的分区数变化、心跳超时（session.timeout.ms）
代价：Rebalance 期间整个组短暂停止消费；时间等于「协调者等待所有成员重新加入」的时间
缓解：group.initial.rebalance.delay.ms 让首次 Rebalance 等一等（同组多个消费者一起启动时减少一次抖动）
      合理设置 max.poll.interval.ms（处理慢的消费者别被误判为死亡）
      用「静态成员（group.instance.id）」避免重启导致的 Rebalance
```

### 7.2 完整示例（手动提交 + Rebalance 监听）

```java
props.put(ConsumerConfig.GROUP_ID_CONFIG, "demo-consumer-group");
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");        // 手动提交，处理成功后再提交
props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");      // 新组第一次从最早开始
props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, "10000");        // 心跳超时
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "5");              // 单批上限，控制处理量

consumer.subscribe(Collections.singletonList(topic), new ConsumerRebalanceListener() {
    @Override
    public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
        consumer.commitSync();     // 失去分区前提交位移，减少重复消费
    }
    @Override
    public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
        System.out.println("  [rebalance] 分配到分区: " + partitions);
    }
});
```

本机实测（真实输出）：

```text
$ java -cp target/kafka-client-demo-1.0.0-jar-with-dependencies.jar com.example.kafka.ConsumerDemo localhost:9092 demo-java 15
  [rebalance] 分配到分区: [demo-java-0, demo-java-1, demo-java-2]
  partition=0 offset=0 key=order-2 value={"orderId":"order-2","amount":200}
  partition=0 offset=1 key=order-3 value={"orderId":"order-3","amount":300}
  partition=1 offset=0 key=order-1 value={"orderId":"order-1","amount":100}
  partition=1 offset=1 key=user-42 value=第 1 次操作
  partition=1 offset=2 key=user-42 value=第 2 次操作
  ...
  partition=2 offset=0 key=async-2 value=async payload 2
  partition=2 offset=1 key=pinned-key value=指定写入分区 2
本次消费条数: 13
各分区消费条数: {0=2, 1=9, 2=2}
  已提交位移 demo-java-0 -> 2
  已提交位移 demo-java-1 -> 9
  已提交位移 demo-java-2 -> 2
  [rebalance] 即将失去分区: [demo-java-0, demo-java-1, demo-java-2]，先同步提交位移
```

读法：

```text
1. 一个消费者拿到了全部 3 个分区（组内只有它）
2. 分区内的 offset 严格递增（0,1 与 0..8），跨分区的顺序无意义
3. 已提交位移 = 「下一条要读的位移」：消费到 offset 1 时提交的是 2
4. 关闭消费者（close）也会触发一次 Rebalance，代码里在 revoked 回调里提交位移是最佳实践
```

### 7.3 位移提交的三种方式

```java
// 1) 自动提交（默认，5 秒一次）：简单但会丢/重复
enable.auto.commit=true, auto.commit.interval.ms=5000
// 风险：poll 拿到 100 条，处理到第 50 条时进程被杀，重平衡后从「上次自动提交点」重来 -> 重复消费
//       更糟的情况：自动提交点在 poll 返回时就前移了，处理失败也等于「已消费」-> 丢数据

// 2) 手动同步提交：处理完再提交，最稳
consumer.commitSync();                       // 提交 poll 返回的所有分区
consumer.commitSync(Collections.singletonMap(tp, new OffsetAndMetadata(offset + 1)));  // 精确到条

// 3) 手动异步提交：吞吐更好，失败要靠回调补
consumer.commitAsync((offsets, exception) -> {
    if (exception != null) { /* 记录并重试，或退化为同步提交 */ }
});
```

生产上的推荐组合：

```text
手动提交 + 幂等消费
    消费端按业务主键去重（数据库唯一索引 / Redis setnx）
    这样即使重复消费也不会产生副作用（至少一次语义 + 幂等 = 事实上的精确一次）
```

### 7.4 消费并发与分区数

```text
规则：消费者数 > 分区数时，多出来的消费者拿不到分区（空转）
所以：并发度上限 = 分区数
```

扩容的两种方向：

```text
加消费者（受分区数限制）      -> 先在运维侧把分区数调大，再扩消费者实例
加消费组（不受分区数限制）    -> 同一份数据被多个组处理（一个组落库、一个组做实时指标）
```

消费滞后（LAG）的判断与处置：

```bash
# 查看积压
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group order-demo-group

# 持续观察（每秒刷新）
watch -n 1 "kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group order-demo-group"

# 判断依据
LAG 稳定在小数值        -> 正常
LAG 持续增长            -> 消费能力不足：加分区+加实例，或优化单条处理耗时
LAG 抖动且偶尔归零      -> Rebalance 频繁：检查 session.timeout.ms / max.poll.interval.ms / 是否有消费者频繁重启
```

### 7.5 消费者常见异常与含义

| 异常 / 现象 | 原因 | 处理 |
|---|---|---|
| `OffsetOutOfRangeException` | 要读的位移已被删除（保留期过了）或超出范围 | 按业务决定重置到 earliest/latest |
| `CommitFailedException` | 提交时已失去分区归属（Rebalance 期间提交） | 提交放在处理循环内，revoked 回调里补一次 commitSync |
| 消费组一直超时、无 LAG 数据 | `__consumer_offsets` 建不出来（单节点副本因子问题） | 见 3.3 的实测与修复 |
| 消费卡在某个 offset 不前进 | 该条消息处理一直失败（毒药消息） | 死信主题 + 跳过策略，见第 10 章 |
| `max.poll.interval.ms` 超时被踢出组 | 单次处理太慢（如批量写库 5 分钟） | 减少 `max.poll.records`、处理放线程池、调大该参数 |

## 8. 可靠性：不丢、不重、有序

这一章把「消息为什么不丢」拆成服务端与客户端两半，并用三副本集群的真实宕机演练验证。

### 8.1 一条消息的完整旅程

```text
producer.send()
   │  ① 客户端缓冲（buffer.memory，满了会阻塞或抛错）
   ▼
broker Leader（跳过分区 0 的某台机器）
   │  ② 写入 Leader 的页缓存（操作系统缓存，此时还没落盘）
   │  ③ Follower 拉取并写入自己的页缓存（副本同步）
   ▼
   │  ④ 达到 acks 要求后返回成功给生产者
   ▼
   │  ⑤ 后台刷盘 + 副本推进 high watermark（HW）
   ▼
consumer.poll() 只能读到 HW 之前的消息（read_committed 还要等事务提交）
```

丢消息可能发生在 11 个位置，但生产环境 95% 的丢失来自三个配置：

```text
acks=1 或 0                    -> Leader 宕机时未同步到 Follower 的消息丢失
min.insync.replicas 未设置      -> ISR 萎缩到 1 时仍写入成功，此时 Leader 挂掉必丢
enable.auto.commit=true        -> 消费者「没处理就先提交位移」，表现为丢消息
```

### 8.2 服务端配置矩阵

| 配置 | 推荐值 | 作用 | 不这么配的后果 |
|---|---|---|---|
| `replication.factor` | 3 | 每个分区 3 份副本 | 只能容忍 0 台宕机（=1）或数据易丢 |
| `min.insync.replicas` | 2 | ISR 少于 2 时拒绝 `acks=all` 写入 | ISR 掉到 1 时仍写入，Leader 挂掉即丢 |
| `unclean.leader.election.enable` | false | 禁止非 ISR 副本当 Leader | 允许「落后的副本」当 Leader，丢一批消息换可用性 |
| `default.replication.factor` | 3 | 新主题默认副本数 | 忘了指定副本数时建出单副本主题 |
| `offsets.topic.replication.factor` | 3 | 位移主题副本数 | 位移丢失 → 大面积重复消费 |
| `transaction.state.log.replication.factor` | 3 | 事务状态主题副本数 | 事务无法恢复 |
| `log.flush.interval.messages` | 不设置 | 靠副本而不是靠 fsync 保证安全 | 设得太小会拖垮性能（正确做法是 3 副本 + acks=all） |

一句话记忆：**服务端用副本保证「不丢」，客户端用 acks 决定「何时算成功」，两者必须配对使用。**

### 8.3 三副本集群宕机演练（本机实测）

环境：1 controller + 3 broker 的 KRaft 集群，主题 `demo-replicated` 为 3 分区 3 副本、`min.insync.replicas=2`。

初始状态（三个分区 Leader 分散在三台 broker 上，ISR 完整）：

```text
$ kafka-topics.sh --describe --topic demo-replicated
Topic: demo-replicated   PartitionCount: 3   ReplicationFactor: 3   Configs: min.insync.replicas=2
        Partition: 0   Leader: 3   Replicas: 3,1,2   Isr: 3,1,2
        Partition: 1   Leader: 1   Replicas: 1,2,3   Isr: 1,2,3
        Partition: 2   Leader: 2   Replicas: 2,3,1   Isr: 2,3,1

# 每个 broker 的数据目录里都有三个分区的副本
$ for c in kafka-1 kafka-2 kafka-3; do docker exec $c ls /var/lib/kafka/data | grep demo-replicated; done
kafka-1  : demo-replicated-0 demo-replicated-1 demo-replicated-2
kafka-2  : demo-replicated-0 demo-replicated-1 demo-replicated-2
kafka-3  : demo-replicated-0 demo-replicated-1 demo-replicated-2
```

演练一：停掉分区 0 的 Leader（broker 3）

```text
$ docker stop kafka-3

$ kafka-topics.sh --describe --topic demo-replicated
        Partition: 0   Leader: 1   Replicas: 3,1,2   Isr: 1,2      <- Leader 从 3 切到 1，ISR 少一个
        Partition: 1   Leader: 1   Replicas: 1,2,3   Isr: 1,2
        Partition: 2   Leader: 2   Replicas: 2,3,1   Isr: 2,1

# 只剩 2 个副本，min.insync.replicas=2 仍然满足，写入照常成功
$ printf 'k4:m7\nk5:m8\n' | kafka-console-producer.sh --topic demo-replicated --property parse.key=true --property key.separator=: --producer-property acks=all
demo-replicated:0:3
demo-replicated:1:3
demo-replicated:2:2
```

这一步是「可用性」的证明：**3 副本 + min.insync=2 可以容忍 1 台 broker 宕机且不丢数据、不中断写入。**

演练二：再停一台 broker（broker 2），ISR 只剩 1

```text
$ docker stop kafka-2

$ kafka-topics.sh --describe --topic demo-replicated
        Partition: 0   Leader: 1   Replicas: 3,1,2   Isr: 1   Elr: 2   LastKnownElr:
        Partition: 1   Leader: 1   Replicas: 1,2,3   Isr: 1   Elr: 2   LastKnownElr:
        Partition: 2   Leader: 1   Replicas: 2,3,1   Isr: 1   Elr: 2   LastKnownElr:

# 继续写入（acks=all）——被拒绝
$ printf 'k6:m9\n' | kafka-console-producer.sh ... --producer-property acks=all
WARN  Got error produce response with correlation id 6 on topic-partition demo-replicated-1, retrying (1 attempts left). Error: NOT_ENOUGH_REPLICAS
WARN  Got error produce response with correlation id 7 on topic-partition demo-replicated-1, retrying (0 attempts left). Error: NOT_ENOUGH_REPLICAS
ERROR Error when sending message to topic demo-replicated with key: 2 bytes, value: 2 bytes with error:
org.apache.kafka.common.errors.NotEnoughReplicasException: Messages are rejected since there are fewer in-sync replicas than required.
```

这一步是「一致性」的证明：**宁可拒绝写入（业务侧报错、重试/降级），也不接受「只有一份副本」的写入。** 如果这里把 `min.insync.replicas` 设成 1，写入会「成功」，但此时 Leader 再宕机就真的丢数据了。

顺带一个 4.x 的新字段：ISR 只剩 1 时，`Elr: 2` 出现了——ELR（Eligible Leader Replicas）是 4.x 引入的「备选 Leader 候选集」，用于在 ISR 为空时判断哪些副本可以被提升，理解它有助于读懂 KRaft 时代的首选出错信息。

演练三：恢复两个 broker

```text
$ docker start kafka-3 kafka-2
$ kafka-topics.sh --describe --topic demo-replicated
        Partition: 0   Leader: 1   Replicas: 3,1,2   Isr: 1,2,3
        Partition: 1   Leader: 1   Replicas: 1,2,3   Isr: 1,2,3
        Partition: 2   Leader: 1   Replicas: 2,3,1   Isr: 1,3,2

# 写入恢复
$ printf 'k7:m10\n' | kafka-console-producer.sh ... --producer-property acks=all
demo-replicated:0:3
demo-replicated:1:4
demo-replicated:2:2
```

结论：**ISR 会自动回补**，无需人工干预；回补期间消费不受影响（消费者只读 HW 之前的数据，落后者不参与）。

### 8.4 客户端配置矩阵

生产者（不丢）：

```java
props.put(ProducerConfig.ACKS_CONFIG, "all");                       // 等所有 ISR
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");        // 重试不重复
props.put(ProducerConfig.RETRIES_CONFIG, Integer.toString(Integer.MAX_VALUE));
props.put(ProducerConfig.DELIVERY_TIMEOUT_MS_CONFIG, "120000");     // 总超时，避免无限等待
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, "5"); // 幂等下的安全上限
```

消费者（不重/不丢）：

```java
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");       // 处理完再提交
props.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed"); // 只读已提交事务
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "100");           // 控制单批处理量
props.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, "300000");    // 处理慢的场景适当调大
```

### 8.5 幂等与事务的边界

```text
enable.idempotence=true
    保证：同一生产者会话内，重试不会产生重复消息（PID + 序列号去重）
    不保证：进程重启后 PID 变化，跨会话的重复仍可能发生

事务（transactional.id）
    保证：跨分区、跨主题的写入原子；配合 sendOffsetsToTransaction 让位移也进事务
    不保证：业务层面的「只执行一次」；下游仍要按业务键幂等

精确一次（exactly-once）在真实系统里的完整表述：
    Kafka 内部：事务 + read_committed 可以做到端到端精确一次
    Kafka 之外：写数据库/调第三方 API 必须自己保证幂等（唯一索引、幂等键、状态机校验）
```

### 8.6 顺序性保证清单

```text
保证范围：单个分区内有序（按写入顺序），跨分区无序
保证条件：
  1. 同一业务实体用同一个 key（保证落同一分区）
  2. 生产者不重排序：幂等开启时 max.in.flight ≤ 5 是安全的；关闭幂等又要求严格顺序时设为 1
  3. 消费者单线程处理该分区（同一分区在组内只被一个消费者拥有，但该消费者内部可能多线程处理，
     需要按 key 哈希到固定线程）
  4. 不用 retries 之外的重投机制打乱顺序（如应用层重试队列要保证顺序）
破坏顺序的常见操作：
  - 消费失败后「先跳过、稍后重放」——重放的消息必然晚于后续消息
  - 增加分区数（同一 key 的映射会变）
  - 使用不带 key 的消息却期望有序
```

### 8.7 可靠性自检清单

```text
[ ] 主题副本因子 ≥ 3，min.insync.replicas = 2
[ ] 内部主题（__consumer_offsets、__transaction_state）副本因子与 min.insync 同步设置
[ ] unclean.leader.election.enable = false
[ ] 生产者 acks=all + 幂等开启，delivery.timeout.ms 明确设置
[ ] 消费者手动提交 + 业务幂等（唯一键/去重表）
[ ] 事务场景消费端 isolation.level=read_committed
[ ] 演练过：停 1 台（无感）、停 2 台（写入报错但不丢）
[ ] 有死信链路与回放工具
[ ] LAG、ISR、磁盘水位三项监控与告警到位
```

## 9. 集群运维

### 9.1 副本分布与「首选 Leader」

```text
$ kafka-topics.sh --describe --topic demo-replicated
        Partition: 0   Leader: 3   Replicas: 3,1,2   Isr: 3,1,2
        Partition: 1   Leader: 1   Replicas: 1,2,3   Isr: 1,2,3
        Partition: 2   Leader: 2   Replicas: 2,3,1   Isr: 2,3,1
```

`Replicas` 的第一个元素是「首选 Leader（preferred leader）」。Kafka 的默认分配策略会把每个分区的 Leader 与副本均匀摊在三台机器上（分区 0 的 Leader 在 3、分区 1 在 1、分区 2 在 2），这样读写压力与磁盘占用都均衡。

如果发生过 Leader 切换（演练之后），Leader 分布会变成「都挤在一台上」：

```text
演练一之后：Partition 0/1 的 Leader 都变成了 1，Partition 2 是 2 —— 已经出现聚集
```

把 Leader 拉回首选位置（也能顺带均衡负载）：

```bash
# 对指定主题触发首选 Leader 选举（broker 侧需要 auto.leader.rebalance.enable 或手工触发）
kafka-leader-election.sh --bootstrap-server localhost:9092 --election-type preferred --all-topic-partitions
# 或指定主题与分区
kafka-leader-election.sh --bootstrap-server localhost:9092 --election-type preferred --topic demo-replicated --partition 0
```

### 9.2 controller 状态（KRaft）

```text
$ kafka-metadata-quorum.sh --bootstrap-controller kafka-ctrl:9093 describe --status
ClusterId:              Ct9rXm2pT0KuV6wLbYhN4Q
LeaderId:               100
LeaderEpoch:            1
HighWatermark:          378
MaxFollowerLag:         0
MaxFollowerLagTimeMs:   0
CurrentVoters:          [{"id": 100, "endpoints": ["CONTROLLER://kafka-ctrl:9093"]}]
CurrentObservers:       [{"id": 2, "directoryId": "UnUzm6ZNiwL4GfHeer9JUg"}, {"id": 1, "directoryId": "W9AEPrssIiQt1wGYE8fU8g"}]

$ kafka-metadata-quorum.sh --bootstrap-controller kafka-ctrl:9093 describe --replication
（列出元数据日志的复制情况：哪个节点是 Leader、每个节点的 LastFetchTimestamp / LastCaughtUpTimestamp）
```

读法（这是 4.x 特有的排障入口）：

```text
LeaderId              当前 controller（元数据仲裁的 Leader）
HighWatermark         元数据日志已提交到哪个位移；停滞说明 controller 出问题
MaxFollowerLag        voter 之间的最大落后量，正常为 0
CurrentVoters         有投票权的 controller 节点（真正决定仲裁结果）
CurrentObservers      只跟随元数据、不投票的节点；broker 就是 observer 角色
```

一个重要认知：**KRaft 里 broker 是 observer 而不是 voter**。三台 broker 宕掉两台不会影响 controller 仲裁（只要 controller 自己是多数派），这与「broker 数量决定集群能不能选举」的直觉不同。

### 9.3 分区重分配（扩容/迁移/负载均衡）

真实执行输出：

```text
$ cat /tmp/reassign.json
{"version":1,"partitions":[
  {"topic":"demo-replicated","partition":0,"replicas":[3,2,1]},
  {"topic":"demo-replicated","partition":1,"replicas":[1,3,2]},
  {"topic":"demo-replicated","partition":2,"replicas":[2,1,3]}
]}

$ kafka-reassign-partitions.sh --bootstrap-server kafka-1:9092 --reassignment-json-file /tmp/reassign.json --execute
Current partition replica assignment

{"version":1,"partitions":[{"topic":"demo-replicated","partition":0,"replicas":[3,1,2],"log_dirs":["any","any","any"]}, ...]}

Save this to use as the --reassignment-json-file option during rollback     <- 官方提示：保存原分配以便回滚
Successfully started partition reassignments for demo-replicated-0,demo-replicated-1,demo-replicated-2

$ kafka-reassign-partitions.sh --bootstrap-server kafka-1:9092 --reassignment-json-file /tmp/reassign.json --verify
Status of partition reassignment:
Reassignment of partition demo-replicated-0 is completed.
Reassignment of partition demo-replicated-1 is completed.
Reassignment of partition demo-replicated-2 is completed.

Clearing broker-level throttles on brokers 1,2,3
Clearing topic-level throttles on topic demo-replicated

$ kafka-topics.sh --describe --topic demo-replicated
        Partition: 0   Leader: 1   Replicas: 3,2,1   Isr: 1,2,3     <- 副本顺序已按新分配变化
        Partition: 1   Leader: 1   Replicas: 1,3,2   Isr: 1,2,3
        Partition: 2   Leader: 1   Replicas: 2,1,3   Isr: 1,3,2
```

生产上用它的三个场景与注意点：

```text
场景 1：扩容新 broker 后把部分副本迁过去（均衡磁盘与流量）
场景 2：某台机器要下线/换盘，把它的副本迁走
场景 3：修复「所有分区都挤在一台机器上」的分配不均

必须做的事：
  1. 迁移会复制大量数据（GB~TB 级），一定加限速，否则会打满网络与磁盘 IO
     kafka-reassign-partitions.sh ... --execute --throttle 52428800   # 50MB/s
     迁移完成后用 --verify 确认，并确认 throttle 已被清除（输出里有两行 Clearing ... throttles）
  2. 先用 --generate 生成候选分配方案，人工 review 再执行
  3. 保留原始分配 JSON，回滚时用得上（执行输出里官方也会提示保存）
  4. 迁移期间磁盘水位会短暂上升（新旧副本并存），要预留空间
```

### 9.4 监控指标清单

broker 侧（JMX / Prometheus）：

| 指标 | 健康值 | 说明 |
|---|---|---|
| `UnderReplicatedPartitions` | 0 | 欠副本分区数，最核心的告警项 |
| `OfflinePartitionsCount` | 0 | 不可用分区数，非 0 就是故障 |
| `ActiveControllerCount` | 整个集群恰好 1 | 出现 0（无 controller）或 >1（脑裂）都要告警 |
| `IsrShrinksPerSec` / `IsrExpandsPerSec` | 长期为 0 | 频繁收缩说明有节点在掉队 |
| `MessagesInPerSec` | 与业务量匹配 | 突然归零说明上游断流或客户端故障 |
| `BytesInPerSec` / `BytesOutPerSec` | 与容量规划对照 | 判断是否需要扩容 |
| `RequestHandlerAvgIdlePercent` | > 0.3 | 低于 0.3 说明 IO 线程被打满 |
| `LogFlushRateAndTimeMs` | —— | 刷盘耗时，异常升高说明磁盘有问题 |
| `DiskUsage`（每分区目录大小） | < 70% | 用 kafka-log-dirs.sh 采集，别只看整机 df |

消费侧：

| 指标 | 说明 |
|---|---|
| 消费组 LAG（`kafka-consumer-groups.sh` 或 `kafka-consumer-groups.sh --state`） | 最贴近业务的健康指标 |
| 消费组状态（Stable / PreparingRebalance / Empty） | 频繁 Rebalance 要查心跳与处理耗时 |
| 每个分区的 commit 位移增长速度 | 与生产速率对比，判断消费能力余量 |

本机用 JMX 读指标的实测方式（裸机部署时开启 JMX 端口后）：

```bash
kafka-run-class.sh kafka.tools.JmxTool \
  --object-name 'kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions' \
  --jmx-url service:jmx:rmi:///jndi/rmi://127.0.0.1:9101/jmxrmi --one-time true
```

### 9.5 常见运维动作速查

```bash
# 查看所有消费组
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# 查看消费组状态（是否有成员、是否在 Rebalance）
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group X --state

# 删除一个消费组（会清掉它的位移，慎用）
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --delete --group X

# 导出/备份某个消费组的位移
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group X > offsets.txt
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --reset-offsets --group X --from-file offsets.txt --execute

# 列出所有主题的配置覆盖项
kafka-configs.sh --bootstrap-server localhost:9092 --describe --entity-type topics --all

# 增加主题分区（只能增，不能减）
kafka-topics.sh --bootstrap-server localhost:9092 --alter --topic demo-replicated --partitions 6

# 单条消息大小上限（主题级，生产常见需求：大 payload）
kafka-configs.sh --bootstrap-server localhost:9092 --alter --entity-type topics --entity-name demo-replicated \
  --add-config max.message.bytes=5242880
```

### 9.6 集群规模与机器规格参考

```text
最小生产集群：3 broker + 3 controller（或 3 combined）
    能容忍 1 台宕机；单机故障不影响可用性

中等规模（日增 TB 级）：5~10 broker，controller 独立部署 3 台
    关注：机架感知（broker.rack）让副本跨机架、跨可用区

大规模（数十 broker）：按业务域拆分集群，不要一个集群装下所有业务
    理由：故障爆炸半径、升级窗口、单点热点都会随规模放大

机器规格：
    CPU：16~32 核（Kafka 吃 CPU 主要在压缩与网络线程）
    内存：64GB 起（大量留给页缓存，堆内存反而不用大：6~8GB）
    磁盘：SSD/NVMe，多块盘做多个 log.dirs（Kafka 会轮流写入）
    网络：万兆起，Kafka 是网络密集型，副本同步会放大跨机流量（RF=3 意味着约 2~3 倍写放大）
    机架：broker.rack 配置好，副本会自动跨机架分布
```

## 10. Spring Boot 集成

### 10.1 依赖与版本

`examples/java/springboot-kafka-demo/pom.xml`（教学口径：Spring Boot 2.7 + javax.* + Java 8 语法，不使用 Lambda/Stream）：

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.18</version>
</parent>

<properties>
    <java.version>8</java.version>
</properties>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter</artifactId>
    </dependency>
    <!-- spring-kafka：Spring 对 kafka-clients 的封装，版本由 Spring Boot 管理 -->
    <dependency>
        <groupId>org.springframework.kafka</groupId>
        <artifactId>spring-kafka</artifactId>
    </dependency>
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>
</dependencies>
```

本机解析出的实际版本（`mvn dependency:list` 真实输出）：

```text
org.springframework.boot:spring-boot-starter:jar:2.7.18
org.springframework.kafka:spring-kafka:jar:2.8.11
org.apache.kafka:kafka-clients:jar:3.1.2
```

版本兼容关系（记住这一条就够）：**Kafka 客户端与服务端是双向兼容的**——3.1.2 的客户端可以连 4.1.2 的 broker（4.0 起 broker 支持 2.1+ 的客户端），所以老项目不必为了用新 broker 而升级 Spring Boot。反过来，用 4.x 的 kafka-clients 需要 Java 11+（KIP-750）。

### 10.2 配置与 Bean 定义

`application.yml`：

```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    consumer:
      group-id: order-demo-group
      auto-offset-reset: earliest

app:
  topics:
    order-events: order-events
```

`KafkaConfig` 里集中定义三类 Bean（完整代码见示例工程）：

```java
// ---- 主题：声明式建主题，应用启动时 KafkaAdmin 会补建缺失的主题 ----
@Bean
public NewTopic orderEventsTopicBean() {
    return TopicBuilder.name(orderEventsTopic).partitions(3).replicas(1)
            .config("retention.ms", "86400000").build();
}

@Bean
public NewTopic orderEventsDltTopicBean() {
    return TopicBuilder.name(orderEventsTopic + ".DLT").partitions(3).replicas(1)
            .config("retention.ms", "604800000").build();     // 死信主题留久一点，给人工回放
}

// ---- 生产者 ----
@Bean
public ProducerFactory<String, Object> producerFactory() {
    Map<String, Object> props = new HashMap<String, Object>();
    props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
    props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
    props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class.getName());
    props.put(ProducerConfig.ACKS_CONFIG, "all");
    props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
    props.put(ProducerConfig.RETRIES_CONFIG, Integer.toString(Integer.MAX_VALUE));
    props.put(ProducerConfig.LINGER_MS_CONFIG, "10");
    props.put(ProducerConfig.BATCH_SIZE_CONFIG, Integer.toString(16 * 1024));
    return new DefaultKafkaProducerFactory<String, Object>(props);
}

// ---- 消费者：三个关键开关 ----
@Bean
public ConsumerFactory<String, OrderEvent> consumerFactory() {
    Map<String, Object> props = new HashMap<String, Object>();
    props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
    props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
    // 1) 用 ErrorHandlingDeserializer 包一层：坏消息不会把消费线程打死
    props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, ErrorHandlingDeserializer.class.getName());
    props.put(ErrorHandlingDeserializer.VALUE_DESERIALIZER_CLASS, JsonDeserializer.class.getName());
    props.put(JsonDeserializer.VALUE_DEFAULT_TYPE, OrderEvent.class.getName());
    props.put(JsonDeserializer.TRUSTED_PACKAGES, "com.example.kafkademo");
    // 2) 关闭自动提交
    props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
    props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
    return new DefaultKafkaConsumerFactory<String, OrderEvent>(props);
}

@Bean
public ConcurrentKafkaListenerContainerFactory<String, OrderEvent> kafkaListenerContainerFactory(
        ConsumerFactory<String, OrderEvent> consumerFactory, KafkaTemplate<String, Object> kafkaTemplate) {
    ConcurrentKafkaListenerContainerFactory<String, OrderEvent> factory =
            new ConcurrentKafkaListenerContainerFactory<String, OrderEvent>();
    factory.setConsumerFactory(consumerFactory);
    factory.setConcurrency(2);     // 不要超过分区数
    // 3) 手动提交：监听方法里 acknowledge() 才提交位移
    factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);

    // 重试 2 次（间隔 1 秒）后进死信主题
    FixedBackOff backOff = new FixedBackOff(1000L, 2L);
    DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(kafkaTemplate);
    DefaultErrorHandler errorHandler = new DefaultErrorHandler(recoverer, backOff);
    errorHandler.addNotRetryableExceptions(DeserializationException.class);   // 反序列化失败重试无意义
    factory.setCommonErrorHandler(errorHandler);
    return factory;
}
```

### 10.3 消费者写法

```java
@KafkaListener(
        topics = "${app.topics.order-events}",
        groupId = "${spring.kafka.consumer.group-id}",
        containerFactory = "kafkaListenerContainerFactory")
public void onOrderEvent(ConsumerRecord<String, OrderEvent> record,
                         Acknowledgment acknowledgment,
                         @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition) {
    log.info("收到事件 topic={} partition={} offset={} key={} value={}",
            record.topic(), partition, record.offset(), record.key(), record.value());

    if (record.value().isPoison()) {
        throw new IllegalStateException("模拟业务处理失败，orderId=" + record.value().getOrderId());
    }

    // 业务处理成功后提交位移
    acknowledgment.acknowledge();
}
```

### 10.4 实测：正常消费 + 重试 + 死信（真实日志）

```text
$ mvn package && java -jar target/springboot-kafka-demo-1.0.0.jar
... Started KafkaDemoApplication in 1.88 seconds (JVM running for 2.192)
... order-demo-group: partitions revoked: [order-events-2, order-events-1, order-events-0]
... 收到事件 topic=order-events partition=1 offset=2 key=order-1 value=OrderEvent{orderId='order-1', ..., poison=false}
... 业务处理成功 orderId=order-1 amount=100
... 收到事件 topic=order-events partition=2 offset=4 key=order-5 value=OrderEvent{orderId='order-5', ..., poison=true}
... Error handler threw an exception                    # 第 1 次失败
... 收到事件 topic=order-events partition=2 offset=4 key=order-5 value=OrderEvent{... poison=true}
... Error handler threw an exception                    # 重试第 2 次失败
... 收到事件 topic=order-events partition=2 offset=4 key=order-5 value=OrderEvent{... poison=true}
... 业务处理成功 orderId=order-8 amount=800            # 重试耗尽后错误处理器把消息投到 DLT，分区继续前进
... [死信消费者] 死信消息 key=order-5 value=OrderEvent{orderId='order-5', ...}
      headers=RecordHeaders(headers = [
        RecordHeader(key = kafka_dlt-exception-fqcn, value = [111, 114, 103, ...]),
        RecordHeader(key = kafka_dlt-exception-cause-fqcn, value = [106, 97, ...]),
        RecordHeader(key = kafka_dlt-exception-message, value = [76, 105, ...]),
        RecordHeader(key = kafka_dlt-original-topic, value = [111, 114, 100, ...]),
        RecordHeader(key = kafka_dlt-original-partition, value = [0, 0, 0, 2]),
        RecordHeader(key = kafka_dlt-original-offset, value = [0, 0, 0, 0, 0, 0, 0, 4]),
        RecordHeader(key = kafka_dlt-original-consumer-group, value = [111, 114, ...])
      ])
等待结果: true（true 表示 8 条都有归宿）
正常处理 7 条: [order-4, order-1, order-7, order-2, order-3, order-6, order-8]
进入死信 1 条: [order-5]
演示程序退出（app.auto-exit=true）
```

这段日志把「生产可用的消费链路」完整跑了一遍，逐点解读：

```text
重试可见：同一条 offset=4 的消息被投递 3 次（1 次 + 2 次重试），间隔 1 秒
死信可见：重试耗尽后消息被搬到 order-events.DLT，原分区不再阻塞（offset=5 的消息继续处理）
头信息：kafka_dlt-* 系列头里带着原始 topic/partition/offset/消费组与异常栈，
        这是死信回放的唯一线索（值以字节数组打印，需要 decode 后看）
退出时 Rebalance：partitions revoked 出现在关闭阶段，属于正常现象
```

### 10.5 死信主题不是终点

```text
DeadLetterPublishingRecoverer 只负责「把失败消息搬到 DLT」，
如果没有人消费 DLT，消息就在那里躺着——「进了死信」不等于「处理完了」。
完整的死信闭环需要三件东西：
  1. DLT 消费程序（本示例中的 DeadLetterConsumer）
  2. 告警（DLT 有消息就通知值班，这是「业务失败」而不是「系统故障」）
  3. 回放工具（修完 bug 后把 DLT 消息按原 topic/partition/key 重新投递）
```

### 10.6 常见坑与配置对照

| 现象 | 原因 | 处理 |
|---|---|---|
| 消费端 JSON 解析失败，反复重试卡住分区 | 没包 `ErrorHandlingDeserializer` | 包一层并配 `JsonDeserializer.TRUSTED_PACKAGES` |
| `The class ... is not in the trusted packages` | 反序列化白名单限制 | 显式配 `TRUSTED_PACKAGES`（不要图省事写 `*`） |
| 应用启动即报 `Topic ... not present in metadata` | 主题没建、也没配 KafkaAdmin | 加 `NewTopic` Bean（本示例做法）或运维预建 |
| 手动 ack 了但位移没提交 | `AckMode` 不是 MANUAL/MANUAL_IMMEDIATE | 明确设置 `ContainerProperties.AckMode.MANUAL_IMMEDIATE` |
| 期望「处理失败自动重投」却没发生 | 没配 `DefaultErrorHandler` | 显式配 `DefaultErrorHandler` + `FixedBackOff` |
| 批量消费改不生效 | `batchListener` 未开启，方法参数不是 `List<ConsumerRecord>` | `factory.setBatchListener(true)` + 方法签名同步改 |
| 并发线程数调大后吞吐没涨 | 并发数超过分区数 | 先把分区数调大，再调 concurrency |

## 11. 生态与选型对比

### 11.1 Kafka 生态全景

```text
                       ┌──────────────── Kafka Connect（数据进出，无需写代码）────────────────┐
   数据库 / 文件 / ES  → │  Source Connector：MySQL、PostgreSQL、MongoDB、S3、FileStream       │
                       │  Sink Connector：  ES、ClickHouse、HDFS、S3、JDBC、Redis            │
                       └────────────────────────────────────────────────────────────────────┘
                                        ↓ 写入 / 读取
   Producer（业务应用、CDC 工具）  →  Kafka 集群  →  Consumer（业务应用、Flink/Spark/Streams）
                                        ↑
   Schema Registry（Avro/Protobuf 模式管理）  Kafka Streams（流处理库）  ksqlDB（SQL 流处理）
```

### 11.2 四个组件的定位

| 组件 | 是什么 | 什么时候用 | 不适用 |
|---|---|---|---|
| Kafka Connect | 配置驱动的数据搬运框架 | 数据库↔数仓/ES 的标准同步 | 复杂转换逻辑（那属于流处理） |
| Kafka Streams | 嵌入应用的流处理库 | 应用内做窗口聚合、join、状态存储 | 需要独立集群/多语言（用 Flink 更合适） |
| ksqlDB | 用 SQL 写流处理 | 快速验证、轻量实时指标 | 复杂 UDF、严格性能要求 |
| Schema Registry | 消息模式的注册与兼容性校验 | Avro/Protobuf 场景（生产必备） | 纯 JSON 且团队能自律的场景 |

Schema Registry 为什么重要：JSON 没有强制模式，生产者改个字段名，消费者就静默解析成 null。Avro/Protobuf + Registry 会把「不兼容的变更」拦在发布阶段（兼容性策略：BACKWARD/FORWARD/FULL）。

### 11.3 Kafka Connect 相对手工消费的优势

```text
手工消费程序
  - 要自己写 offset 管理、重试、批量、幂等、监控
  - 每个数据源都要重复一遍

Kafka Connect
  - connector 配置化：{"connector.class":"io.debezium.connector.mysql.MySqlConnector", ...}
  - 分布式模式自带：任务分配、offset 存储（存在 Kafka 内部主题）、重启恢复、REST API 管理
  - 需要转换时用 SMT（Single Message Transform）或外部流处理
```

一个 Connect 分布式模式的启动骨架（配置示例，本机未部署 Connect 集群）：

```properties
# connect-distributed.properties
bootstrap.servers=kafka-1:9092,kafka-2:9092,kafka-3:9092
group.id=connect-cluster
key.converter=org.apache.kafka.connect.storage.StringConverter
value.converter=io.confluent.connect.avro.AvroConverter
value.converter.schema.registry.url=http://schema-registry:8081
config.storage.topic=connect-configs          # 必须 compact、单分区
offset.storage.topic=connect-offsets          # 必须 compact、多分区
status.storage.topic=connect-status            # 必须 compact、多分区
```

### 11.4 与其它消息中间件的对比

| 维度 | Kafka | RabbitMQ | RocketMQ | Pulsar |
|---|---|---|---|---|
| 模型 | 分区日志（拉模型） | AMQP 队列/交换机（推模型） | 队列 + CommitLog | 分区日志 + 分层存储 |
| 单机吞吐 | 极高（十万~百万级/s） | 中（万级/s） | 高 | 高 |
| 消息顺序 | 分区内有序 | 队内有序 | 队列内有序 | 分区内有序 |
| 消息保留 | 按时间/大小，可重放 | 消费即删（可配） | 按时间，可重放 | 按时间，可重放 |
| 延迟 | 毫秒 | 微秒~毫秒（低延迟更好） | 毫秒 | 毫秒 |
| 复杂路由 | 无（靠 topic 设计） | 强（exchange/routing key/死信/延迟） | 中等 | 中等 |
| 事务 | 支持（跨分区原子写） | 支持（AMQP 事务，性能差） | 支持 | 支持 |
| 运维复杂度 | 中（4.x KRaft 已简化） | 低 | 中 | 高 |
| 典型场景 | 日志、埋点、数仓管道、流计算 | 业务解耦、任务分发、RPC 替代 | 电商交易、金融 | 多租户、分层存储 |

选型口诀：

```text
要吞吐、要重放、要接大数据生态   -> Kafka
要复杂路由、要低延迟、量不大     -> RabbitMQ
要事务消息、要延迟消息、国内生态 -> RocketMQ
要多租户、要对象存储分层         -> Pulsar
```

### 11.5 什么时候不该用 Kafka

```text
请求-响应式同步调用       -> 直接 RPC（HTTP/gRPC）更简单
需要严格全局顺序         -> 单分区性能有上限，考虑数据库或专门的顺序化方案
消息量极小（每天几百条） -> 引入 Kafka 的运维成本超过收益，用数据库表 + 定时任务更实在
需要复杂定时/延迟投递    -> RabbitMQ 的延迟插件或业务侧时间轮更合适
客户端在浏览器/移动端    -> 不要直连 Kafka，必须经后端
```

## 12. 应用场景实战

三个场景都是真实跑过的：场景一与场景三是 Java 程序实测，场景二是命令行实测。

### 场景一：订单事件流（业务解耦 + 幂等消费 + 死信兜底）

业务需求：下单成功后要通知库存、积分、风控、数据平台四个下游；任何一个下游故障都不能影响下单主流程；下游处理失败要有兜底与追溯。

链路设计：

```text
下单服务 ──写 order.order.created──> Kafka(3 分区, key=orderId)
                                          ├── 库存消费组（扣减库存）
                                          ├── 积分消费组（加积分）
                                          ├── 风控消费组（实时规则）
                                          └── 数据平台消费组（写入数仓/ES）
                                     任一消费者失败 ──> order.order.created.DLT（人工/自动回放）
```

生产端（关键代码）：

```java
public void publishOrderCreated(Order order) {
    // 用 orderId 作 key：同一订单的所有事件落同一分区，保证分区内有序
    ProducerRecord<String, Object> record = new ProducerRecord<String, Object>(
            "order.order.created", order.getOrderId(), OrderCreatedEvent.from(order));
    // 加业务头：便于链路追踪与排障
    record.headers().add("traceId", order.getTraceId().getBytes(StandardCharsets.UTF_8));
    // 同步发送：订单创建是核心流程，必须确认落盘成功
    try {
        kafkaTemplate.send(record).get(3, TimeUnit.SECONDS);
    } catch (Exception e) {
        // 发送失败的兜底：写本地 outbox 表，由补偿任务重发（不要静默吞掉）
        outboxRepository.save(Outbox.of(record));
        throw new IllegalStateException("订单事件投递失败，已进入补偿队列", e);
    }
}
```

消费端（幂等 + 手动提交 + 死信）：

```java
@KafkaListener(topics = "order.order.created", groupId = "inventory-group",
               containerFactory = "kafkaListenerContainerFactory")
public void onOrderCreated(ConsumerRecord<String, OrderCreatedEvent> record, Acknowledgment ack) {
    OrderCreatedEvent event = record.value();

    // 1) 幂等：订单可能被重复投递（至少一次语义），用唯一索引或去重表兜住
    if (inventoryDedupRepository.exists(event.getOrderId())) {
        log.info("重复消息，跳过 orderId={}", event.getOrderId());
        ack.acknowledge();
        return;
    }

    // 2) 业务处理：扣库存 + 记录去重标记，放在同一个本地事务里
    inventoryService.deductWithinTransaction(event);

    // 3) 处理成功才提交位移
    ack.acknowledge();
}
```

实测结果（第 10 章的 Spring Boot 示例，8 条事件）：

```text
正常处理 7 条: [order-4, order-1, order-7, order-2, order-3, order-6, order-8]
进入死信 1 条: [order-5]        # 该条消息被标记为 poison，重试 2 次后进 DLT
```

设计要点回顾：

```text
1. 下游故障不影响下单：Kafka 写入成功即返回，下游自己按节奏消费
2. 新增下游（比如新增「优惠券」消费组）不需要改下单服务：换个 group 订阅同一主题即可
3. 分区内有序 + key=orderId：同一订单的事件不会乱序
4. 幂等靠业务去重表，不依赖 Kafka 的「不重复投递」（Kafka 只保证至少一次）
5. 死信 + 告警 + 回放，构成失败消息的闭环
```

### 场景二：日志采集与削峰（消费者故障时不丢数据）

业务需求：应用日志集中采集，允许消费者重启/故障，但不能丢日志；高峰写入要能缓冲，消费者按自己能力消费。

实测（脚本 `examples/scripts/06-scenario-backlog.sh`，6 分区、key=服务名）：

```text
# 6.2 高峰写入 10000 条
$ seq 1 10000 | awk '{...服务名作为 key...}' | kafka-console-producer.sh --property parse.key=true
写入完成

# 6.3 数据按 key 散列到 4 个分区（4 个服务名只映射到 4 个分区，另两个为空）
$ kafka-get-offsets.sh --topic app-log
app-log:0:0
app-log:1:5000
app-log:2:2500
app-log:3:0
app-log:4:0
app-log:5:2149

# 6.4 6 个并行消费者消费完初始数据，LAG 归零
log-consumer    app-log   1    5000    5000    0
log-consumer    app-log   2    2500    2500    0
log-consumer    app-log   5    2149    2149    0

# 6.5 消费者离线期间再写入 10000 条 —— 积压出现
$ kafka-consumer-groups.sh --describe --group log-consumer
log-consumer    app-log   1    5000    10000   5000
log-consumer    app-log   2    2500    5000    2500
log-consumer    app-log   5    2149    4649    2500
  LAG 合计: 10000        <- CONSUMER-ID 为空，说明没有任何消费者在线

# 6.6 消费者恢复，积压被追平（每 4 秒采样一次）
  第 1 次采样 LAG 合计: 2000
  第 2 次采样 LAG 合计: 1500
  第 3 次采样 LAG 合计: 0
  第 4 次采样 LAG 合计: 0
  第 5 次采样 LAG 合计: 0
```

这段输出把「削峰填谷」讲清楚了：

```text
1. 生产者 1 秒内写完 1 万条并返回，完全不关心消费者是否在线
2. 消费者离线的这段时间，积压量（LAG 之和）= 10000，是「需要多少人手/实例来追」的唯一依据
3. 消费者恢复后按分区并行追平，追平速度上限 = 分区数 × 单消费者吞吐
4. 实测的一个坑：kafka-console-consumer 退出时会为「所有被分配的分区」提交位移（哪怕没处理完），
   所以用命令行演示积压必须「先消费完一批，再离线写入」，否则一启动就把 LAG 抹平了
```

生产落地方案（与手工消费的对应关系）：

```text
采集端：Fluent Bit / Filebeat / Vector  →  Kafka（key 用 hostname 或服务名，保证同一来源有序）
Kafka：  6~24 分区、副本 3、保留 3~7 天（日志允许重放，但不必留太久）
消费端：按分区并行消费 → 批量写 ES / ClickHouse / S3；失败重试 + 死信；
        用 LAG 与消费速率做扩容依据
告警：  LAG 超过阈值（如 10 万条）或长时间不下降 → 告警
```

### 场景三：CDC 与「读-改-写」的原子链路

CDC（Change Data Capture）的典型链路：

```text
MySQL binlog ──Debezium Connector──> Kafka(按表分主题, key=主键) ──> 消费端写数仓/ES/缓存
```

Debezium 侧的关键配置（配置示例，本机未部署 Debezium，仅列出经过核对的参数形态）：

```json
{
  "name": "mysql-orders-cdc",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "mysql",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "***",
    "database.server.id": "184054",
    "topic.prefix": "cdc",
    "table.include.list": "shop.orders,shop.order_items",
    "snapshot.mode": "initial",
    "key.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081",
    "decimal.handling.mode": "string",
    "time.precision.mode": "connect"
  }
}
```

CDC 消费端要处理的四件事：

```text
1. 事件类型判别：op=c 新增 / u 更新 / d 删除 / r 快照；删除事件的 value 结构不同，要单独处理
2. 顺序保证：同一行变更必须落同一分区（Debezium 已按主键做 key），下游按 key 串行处理
3. 幂等：用主键 upsert（REPLACE INTO / ON DUPLICATE KEY UPDATE / ES 的 _id 覆盖）
4. 快照与增量：initial 快照阶段别用实时性要求高的消费者；快照完成后延迟才稳定
```

「读源-写目标-提交位移」的原子链路（本机实测，见第 6.6 节）：Kafka 用事务把「写目标主题 + 提交源主题位移」绑在一起，消费端用 `read_committed` 保证只读已提交数据。实测输出：

```text
$ java -cp ... com.example.kafka.TransactionDemo localhost:9092 txn-source txn-target
已写入 3 条源消息到 txn-source
事务提交成功，本批处理 3 条
共处理 3 条，写入目标主题 txn-target

$ kafka-consumer-groups.sh --describe --group txn-demo-group
txn-demo-group  txn-source   0   3   3   0
txn-demo-group  txn-source   1   2   2   0
txn-demo-group  txn-source   2   0   0   0
```

什么时候必须用事务、什么时候不用：

```text
必须用：流式 ETL（源 → 目标）不允许「写成功但位移没提交」导致重复，或「位移提交了但写失败」导致丢数据
不用：  普通业务事件分发（下游各自消费、各自幂等），用「至少一次 + 幂等」更简单也更便宜
```

### 场景对比小结

| 场景 | 分区 key | 消费语义 | 是否需要事务 | 主要风险 |
|---|---|---|---|---|
| 订单事件流 | orderId | 至少一次 + 业务幂等 | 否 | 下游幂等没做好 → 重复扣减 |
| 日志采集 | 服务名/主机名 | 至少一次 | 否 | 分区倾斜（某服务日志量特别大） |
| CDC / 流式 ETL | 主键 | 精确一次（事务） | 是 | 快照与增量混淆、删除事件未处理 |

## 13. 最佳实践与踩坑记录

### 13.1 最佳实践

主题与分区

1. 主题命名用 `{域}.{实体}.{事件}`，如 `order.order.created`、`pay.payment.succeeded`；环境前缀放最前（`prod.`、`test.`）。
2. 分区数按「目标吞吐 ÷ 单分区吞吐」估算，并预留 2~3 倍余量（只能增不能减）；常见起步值 6/12/24。
3. 同一业务实体的所有事件用同一个 key（如 `orderId`），保证分区内有序。
4. 长期保留 + 压实（`cleanup.policy=compact`）只用于「按主键还原状态」的场景，不要用在纯事件流上。

生产端

5. `acks=all` + `enable.idempotence=true` 是默认基线，不要为了「快一点」关掉。
6. `linger.ms` 5~50ms、`batch.size` 64KB~1MB，是把吞吐做上去最省力的两个参数。
7. 关键业务同步 `send().get()`，非关键异步 + 回调；进程退出前一定 `flush()`。
8. 序列化用 Avro/Protobuf + Schema Registry，不要裸 JSON 直连生产（字段改名会静默丢失数据）。

消费端

9. 关闭自动提交，处理成功后手动提交；配合业务键幂等，得到「至少一次 + 幂等」。
10. `max.poll.records` 按单条处理耗时设置（保证一批能在 `max.poll.interval.ms` 内处理完）。
11. 死信闭环三件套：DLT 主题 + DLT 消费者 + 告警与回放工具。
12. 消费端必须能处理「重复消息」和「乱序消息」，这是分布式系统的默认前提。

运维

13. 三个 broker 起步，`replication.factor=3`、`min.insync.replicas=2`；内部主题（`__consumer_offsets`、`__transaction_state`）也要设成 3/2，否则它们会成为可靠性短板。
14. 监控四件套：`UnderReplicatedPartitions`（=0）、消费组 LAG、磁盘水位（分区级）、请求队列与延迟。
15. 上线前做两次演练：停一个 broker（应无感）、停两个 broker（应写入失败但不丢数据）。
16. 分区扩容/迁移用 `kafka-reassign-partitions.sh` 做「限速迁移」，不要直接挪数据目录。
17. `auto.create.topics.enable=false`，主题由 IaC 或运维统一创建，避免客户端打错名字产生垃圾主题。

### 13.2 踩坑记录

坑 1：单节点集群配了 `default.replication.factor=1`，消费组还是不可用。

```text
结论：官方镜像把 offsets.topic.replication.factor 默认设成 3，__consumer_offsets 建不出来，
      表现是「生产能写、消费一直超时」，broker 日志只有反复的
      Sent auto-creation request for Set(__consumer_offsets) to the active controller。
原因：内部主题的副本因子有独立配置项，不受 default.replication.factor 影响。
解法：单节点显式设置 KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1、
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1、KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1。
验证：不指定消费组、直接按分区消费一切正常；指定消费组就超时——这个对比能快速定位。
```

坑 2：以为 `retention.ms=10s` 会让消息 10 秒后消失，结果等了 5 分钟还在。

```text
结论：清理线程默认每 5 分钟才扫一次（log.retention.check.interval.ms=300000），
      而且它是静态配置，kafka-configs 动态改会被拒绝：
      InvalidRequestException: Cannot update these configs dynamically。
原因：删除的最小单位是 segment，还要等清理线程轮询。
解法：改配置文件（或容器环境变量）后重启 broker；实验时把 segment.bytes 和检查间隔一起调小。
      「消息还在」不等于「保留策略没生效」，要用 log-start-offset 判断。
```

坑 3：三个 KRaft 节点起不来，日志刷满选举信息。

```text
结论：combined 节点 + 静态 controller.quorum.voters 在 4.1.2 上多 voter 场景下选不出 leader，
      epoch 一直涨，broker 最终报
      Shutting down because we were unable to register with the controller quorum 并以 exit 1 退出。
原因：镜像的自动格式化生成的元数据引导信息与多 voter 静态配置不匹配。
解法：改用 1 个 controller-only 节点（voters 只含自己）+ 3 个 broker-only 节点的拓扑；
      或按官方文档分角色部署并用 kafka-storage.sh format --initial-controllers 显式给出初始集合。
补充：controller-only 节点不能设 KAFKA_ADVERTISED_LISTENERS，镜像会直接拒绝：
      KAFKA_ADVERTISED_LISTENERS is not supported on a KRaft controller.
```

坑 4：把 4.x 的 `kafka.tools.GetOffsetShell` 老命令直接搬过来。

```text
结论：4.x 里类名与参数都变了。
原因：工具类统一挪到 org.apache.kafka.tools 下，参数从 --broker-list 改成 --bootstrap-server。
解法：kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server ... --time -1
报错原文：Error: Could not find or load main class kafka.tools.GetOffsetShell
          Error occurred: broker-list is not a recognized option
```

坑 5：命令行消费者不加 `--timeout-ms`，脚本永久挂住。

```text
结论：没有新消息时 kafka-console-consumer.sh 会一直等下去。
原因：默认没有超时，只有 --max-messages 满足才会退出。
解法：脚本里一律加 --timeout-ms（本机踩过一次 400 秒挂起，整个批处理被卡住）。
```

坑 6：用命令行消费者演示「积压」，一启动 LAG 就归零了。

```text
结论：console consumer 退出时会为「所有被分配的分区」提交位移，即使它没处理完这些消息。
原因：它在关闭时调用 commitSync()，提交的是当前 poll 到的位置（而不是已处理位置）。
解法：演示积压要让消费组先消费完一批，再离线写入新数据；真实业务的消费端不会有这个问题
      （它们用 Acknowledgment 逐条确认）。
```

坑 7：`kafka-configs.sh --alter` 改 broker 参数报 InvalidRequestException。

```text
结论：不是所有 broker 参数都支持动态修改。
原因：静态参数（log.dirs、num.network.threads、log.retention.check.interval.ms 等）不支持动态更新。
解法：改 server.properties / 环境变量后重启；用 --describe --all 看 synonyms 里是
      STATIC_BROKER_CONFIG 还是 DYNAMIC_BROKER_CONFIG，一眼能判断。
```

坑 8：`advertised.listeners` 写错，客户端第一次能连、后面全部超时。

```text
结论：broker 会把 advertised.listeners 的地址返回给客户端，让客户端用它来连接。
原因：客户端 bootstrap 成功后，从元数据里拿到「真实地址」，写错了就连不上。
解法：容器内客户端用容器网络地址，宿主机客户端用宿主机地址，云上用可路由的公网/内网地址；
      必要时配置多监听器（INTERNAL/EXTERNAL）分别通告。
```

坑 9：消费端 JSON 反序列化失败，整个分区卡死。

```text
结论：一条坏消息会让消费线程反复抛异常，LAG 永远不动。
原因：默认的反序列化器失败直接抛出，默认错误处理器无限重试。
解法：用 ErrorHandlingDeserializer 包一层 + DefaultErrorHandler + 死信主题；
      DLT 的 kafka_dlt-* 头里带着原始 topic/partition/offset，是回放的关键。
```

坑 10：`enable.auto.commit=true` 配异步处理，出现了「消息没处理但位移已提交」。

```text
结论：自动提交提交的是「poll 到的位置」，不是「处理完成的位置」，会丢消息。
原因：poll 返回后位移就可能被提交，业务此时还没处理。
解法：关掉自动提交，处理成功后手动 ack；Spring 里用 AckMode.MANUAL_IMMEDIATE。
```

坑 11：以为「加了分区就万事大吉」，结果同 key 的顺序乱了。

```text
结论：增加分区会改变「同一 key 落在哪个分区」的映射。
原因：分区数变了，murmur2(key) % 分区数 的结果也变了；同一 key 的历史数据在新旧分区里被拆开。
解法：需要严格有序的实体，扩容时要么停写做一次性的数据迁移，要么接受「不同批次数据有序」。
      分区数要在设计阶段定好。
```

坑 12：事务生产者写入成功，消费者却读不到。

```text
结论：消费端没设 isolation.level=read_committed 时读的是未提交数据；反之，
      如果事务一直没提交，read_committed 的消费者永远看不到。
原因：事务消息要等 commit 后才对 read_committed 消费者可见。
解法：消费端显式设 isolation.level=read_committed，并监控「未提交事务数量」与事务超时。
```

坑 13：同一个 `transactional.id` 被两个实例使用，旧实例的写入全部失败。

```text
结论：这是设计行为（fencing），不是 bug。
原因：broker 会把同名 transactional.id 的 epoch 抬高，让旧实例失效，避免僵尸生产者重复写入。
解法：transactional.id 与实例绑定（如带上 pod 序号），滚动更新时先确认旧实例已停止。
```

坑 14：`kafka-producer-perf-test.sh` 的吞吐数字被当成选型依据。

```text
结论：本机实测 24142 rec/s、23.58 MB/s，但不能直接用于生产容量规划。
原因：测试机是共享环境（同机有数据库、CI、其他容器），且消息是随机字节（压缩率失真）。
解法：压测要在目标硬件、目标网络、目标消息体（真实业务数据）上做；
      共享环境里的压测只能用于「改参数前后的相对比较」。
```

坑 15：不看磁盘水位，直到整个 broker 挂掉。

```text
结论：磁盘写满是导致「部分分区不可用」的最常见原因。
原因：Kafka 依赖顺序写 + 页缓存，磁盘满时刷盘失败，ISR 收缩，严重时分区离线。
解法：用 kafka-log-dirs.sh 的分区级 size 做告警；保留策略 + 分区容量上限双保险；
      不要在数据盘上放日志文件、不要在同一个盘上跑其它写密集型服务。
```

## 14. 3.x 与 4.x 的差异

这一章专门列迁移时最容易踩的点，全部是本次实测或官方发布说明确认过的。

### 14.1 移除 ZooKeeper

```text
3.x：ZooKeeper 模式 + KRaft 模式（实验/预览）并存
4.0：只支持 KRaft，ZooKeeper 代码整体删除
```

影响：

```text
--zookeeper localhost:2181 这类参数全部失效，脚本必须改用 --bootstrap-server
kafka-topics.sh / kafka-configs.sh 等命令不再有 zookeeper 分支
升级路径必须：3.x（ZK 模式）-> 3.9（KRaft 迁移）-> 4.x
```

### 14.2 Java 版本要求

```text
客户端与 Kafka Streams：Java 11+（KIP-750，3.x 时代还支持 Java 8）
broker / Connect / 命令行工具：Java 17+（KIP-1013）
```

实际影响举例：本机用的 kafka-clients 3.9.0 仍可用 Java 8 编译，配 4.1.2 的 broker 正常；但如果把客户端换成 4.1.2，`maven.compiler.source=8` 会直接编译失败。

### 14.3 命令行工具的包名与参数变化

```text
# 3.x 写法
kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic t --time -1

# 4.x 写法（类名移到 org.apache.kafka.tools，参数改成 --bootstrap-server）
kafka-run-class.sh org.apache.kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic t --time -1

# JmxTool 同样挪了包名（本机实测报错：找不到或无法加载主类 kafka.tools.JmxTool）
kafka-run-class.sh kafka.tools.JmxTool --object-name ...            # 3.x 写法（4.x 报错）
kafka-run-class.sh org.apache.kafka.tools.JmxTool --object-name ...  # 4.x 写法
```

本机实测的报错（老脚本直接搬过来会看到这两行）：

```text
Error: Could not find or load main class kafka.tools.GetOffsetShell
Error occurred: broker-list is not a recognized option
```

### 14.4 KRaft 的 quorum 配置（本机踩到的硬骨头）

```text
官方镜像的自动格式化 + 静态 controller.quorum.voters 在多节点场景下不稳定：
  三个 combined 节点同时启动 -> controller quorum 选举风暴（epoch 持续递增、无 leader）
  broker 60 秒后报 Shutting down because we were unable to register with the controller quorum -> exit 1

改用 KIP-853 的动态 quorum（只给 controller.quorum.bootstrap.servers）又被拒绝：
  Because controller.quorum.voters is not set on this controller, you must specify one of the following:
  --standalone, --initial-controllers, or --no-initial-controllers
  （说明：动态 quorum 需要先用 kafka-storage.sh format --initial-controllers 显式给出初始 controller 集合，
   不能靠镜像的自动格式化）

controller-only 节点还有一个专属限制（本机实测报错）：
  KAFKA_ADVERTISED_LISTENERS is not supported on a KRaft controller.

可行做法（本教程采用的拓扑）：
  1 个 controller-only 节点（voters 只含自己，quorum=1，永远能选出 leader）
  + 3 个 broker-only 节点（voters 指向那个 controller）
  这样既能真实演示 3 副本 / ISR / Leader 切换，又绕开了多 voter 选举问题。
生产上要么用官方推荐的分角色部署（3 controller + N broker），要么用托管服务/Operator，
  并在上线前把「停一个节点、停两个节点」的演练做一遍。
```

### 14.5 其它值得注意的变化

```text
消息格式：只支持 v2（magic=2）；老版本的 v0/v1 消息需要在上线 4.x 前完成转换
旧协议 API：4.0 移除了一批 2.1 之前的老版本协议（用 kafka-broker-api-versions.sh 确认客户端版本）
ELR 字段：kafka-topics.sh --describe 里新增 Elr / LastKnownElr（Eligible Leader Replicas）
新消费组协议：KIP-848 的 consumer group protocol 在 4.x 逐步成为可选路径，
    组类型与经典协议有差异（排查消费组问题时注意 group.coordinator.rebalance.protocols 配置）
```

### 14.6 迁移检查清单

```text
[ ] 客户端版本 ≥ 2.1（推荐 ≥ 3.x），且 Java 版本满足要求
[ ] 所有脚本里的 --zookeeper / --broker-list 已改掉
[ ] 主题的消息格式已转到 v2（老集群需先做 inter.broker.protocol 升级）
[ ] 内部主题（__consumer_offsets、__transaction_state）副本数与 min.insync 已按新集群规模设置
[ ] 监控项已适配（ISR、UnderReplicatedPartitions、Controller 选举状态在 KRaft 下的指标名有变化）
[ ] 演练过：单 broker 宕机、controller 宕机、磁盘写满、客户端版本混跑
```

## 相关文档

- [[09.1-Kafka 架构与存储]] — 大数据视角的 Kafka 架构与存储原理（本文的部署与客户端部分更偏工程实操）
- [[09.2-Kafka Producer]] — 生产者原理：批次、压缩、幂等、事务的内部机制
- [[09.3-Kafka Consumer]] — 消费者原理：消费组协调、位移管理、Rebalance 协议
- [[09.4-Kafka 生态与数据集成]] — Connect、Streams、CDC 与数据集成链路
- [[31.5-Kafka 优化]] — 大数据性能优化专题里的 Kafka 调优参数
- [[35.2-Kafka 源码]] — 源码阅读：日志存储、副本复制、控制器实现
- [[144-Kafka]] — Java 全栈视角的 Kafka 入门与 Spring 集成
- [[145-Kafka-Streams]] — Kafka Streams 流处理：拓扑、窗口、状态存储
- [[92-Kafka]] — Spring Messaging 体系下的 Kafka 集成（KafkaTemplate/@KafkaListener 另一套写法）
- [[Docker完整教程]] — 容器化部署基础（镜像、网络、数据卷、compose）
- [[Kubernetes完整教程]] — 把 Kafka 部署到 K8S 的编排知识（本文未展开 Operator 方案）
