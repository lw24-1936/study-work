---
title: Kafka
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [kafka, broker, topic, partition, offset, consumer-group, ack, isr, replication, kafka-streams]
---

# Kafka

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [核心概念：Broker/Topic/Partition/Offset](#核心概念brokertopicpartitionoffset)
- [Producer 生产者](#producer-生产者)
- [Consumer 与 Consumer Group](#consumer-与-consumer-group)
- [消息确认 ACK](#消息确认-ack)
- [ISR 与 Replication](#isr-与-replication)
- [Kafka Streams](#kafka-streams)
- [Kafka vs RabbitMQ](#kafka-vs-rabbitmq)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Kafka 是分布式流处理平台，最初由 LinkedIn 开发，以高吞吐、持久化、可扩展著称。

```text
Kafka 特点：
1. 高吞吐 —— 百万级消息/秒
2. 持久化 —— 消息落盘，可回溯消费
3. 水平扩展 —— 分区 + 副本，轻松扩容
4. 流处理 —— Kafka Streams 实时处理

适用场景：
日志收集、消息系统、流处理、大数据管道、事件溯源
```

## 核心概念：Broker/Topic/Partition/Offset

### 架构概览

```text
Producer → Broker 集群（Topic 分区）→ Consumer Group
              ↓
           Zookeeper/KRaft（元数据管理）
```

### Broker（代理节点）

```text
Broker 是 Kafka 的服务节点，一个 Kafka 集群由多个 Broker 组成。
每个 Broker 存储一部分分区数据。
```

### Topic（主题）

```text
Topic 是消息的逻辑分类，类似数据库的表。
一个 Topic 可以有多个分区（Partition）。
```

### Partition（分区）

```text
Partition 是 Topic 的物理分片，是 Kafka 并行和扩展的基础：
1. 一个 Topic 分多个 Partition，分布在多个 Broker
2. 每个 Partition 是一个有序的、不可变的消息序列
3. 消息写入 Partition 后追加在末尾
4. 同一 Partition 内消息有序，跨 Partition 无序
```

```text
Topic "orders"
├── Partition 0  → [msg1, msg2, msg3, ...]
├── Partition 1  → [msg4, msg5, ...]
└── Partition 2  → [msg6, msg7, ...]
```

### Offset（偏移量）

```text
Offset 是消息在 Partition 内的唯一位置标识（从 0 递增）。
消费者通过 Offset 记录消费进度，实现：
1. 断点续消费
2. 重复消费（重置 Offset）
3. 消息回溯
```

## Producer 生产者

### 基本使用

```java
@Autowired
private KafkaTemplate<String, String> kafkaTemplate;

// 发送消息
kafkaTemplate.send("order-topic", "order-created", "订单创建消息");

// 发送对象（JSON）
kafkaTemplate.send("order-topic", order);

// 指定分区
kafkaTemplate.send("order-topic", 0, "key", order);

// 带回调
kafkaTemplate.send("order-topic", order).addCallback(
    result -> log.info("发送成功：{}", result.getRecordMetadata().offset()),
    ex -> log.error("发送失败", ex)
);
```

### 生产者的可靠性配置

```yaml
spring:
  kafka:
    producer:
      acks: all                 # 所有副本确认
      retries: 3                # 重试次数
      batch-size: 16384         # 批量大小
      buffer-memory: 33554432   # 缓冲区大小
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
      properties:
        linger.ms: 5            # 批量等待时间
```

### 消息分区策略

```text
1. 指定了 partition → 直接发到该分区
2. 指定了 key → 按 key 哈希取模（同 key 进同分区，保证有序）
3. 都没指定 → 轮询或随机
```

```java
// 同 key 消息进同一分区，保证顺序
kafkaTemplate.send("topic", "user-123", message);  // key=user-123
// 所有 user-123 的消息都在同一分区，顺序消费
```

## Consumer 与 Consumer Group

### 消费模型

```text
Consumer Group（消费者组）是 Kafka 消费的核心：
1. 同一个 Group 内，一个 Partition 只能被一个 Consumer 消费
2. 不同 Group 各自独立消费（广播）
3. Group 内 Consumer 数量 ≤ Partition 数量（多了空闲）
```

### 基本消费

```java
@Component
public class OrderConsumer {

    @KafkaListener(topics = "order-topic", groupId = "order-group")
    public void handle(Order order) {
        orderService.process(order);
    }

    // 批量消费
    @KafkaListener(topics = "order-topic", groupId = "order-group")
    public void handleBatch(List<Order> orders) {
        orders.forEach(orderService::process);
    }
}
```

### 消费者配置

```yaml
spring:
  kafka:
    consumer:
      group-id: order-group         # 消费者组
      auto-offset-reset: earliest   # 无 offset 时从最早开始（latest=最新）
      enable-auto-commit: false     # 关闭自动提交，手动控制
      max-poll-records: 500         # 单次拉取最大条数
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
```

### 手动提交 Offset

```yaml
spring:
  kafka:
    consumer:
      enable-auto-commit: false          # 关闭自动提交
    listener:
      ack-mode: manual                   # 手动确认
```

```java
@Component
public class ManualCommitConsumer {

    @KafkaListener(topics = "order-topic", groupId = "order-group")
    public void handle(Order order, Acknowledgment ack) {
        try {
            orderService.process(order);
            ack.acknowledge();   // 处理成功后手动提交 offset
        } catch (Exception e) {
            // 不提交 offset，下次重新消费
            throw e;
        }
    }
}
```

### Offset 提交策略

```text
自动提交：框架定时提交，可能丢消息（处理到一半提交）
手动提交：处理成功后提交，保证至少一次（at-least-once）

ack-mode 取值：
record     —— 每条处理完提交
batch      —— 每批处理完提交（默认）
time       —— 定时提交
count      —— 达到数量提交
manual     —— 手动提交
```

## 消息确认 ACK

Kafka 的 ACK 是生产者的确认机制（不同于消费者 offset）。

### 生产者 acks 配置

```text
acks=0   —— 不等确认，最快，可能丢消息
acks=1   —— Leader 确认即可，可能丢（Leader 挂了副本没同步）
acks=all —— 所有 ISR 副本确认，最安全（默认推荐）
```

```yaml
spring:
  kafka:
    producer:
      acks: all   # 所有副本确认，最安全
```

### 幂等生产者

```yaml
spring:
  kafka:
    producer:
      properties:
        enable.idempotence: true   # 幂等，防止重试导致重复
```

## ISR 与 Replication

### Replication（副本）

```text
每个 Partition 有多个副本（Replica）：
1. Leader 副本 —— 处理读写请求
2. Follower 副本 —— 从 Leader 同步数据

副本分布在不同的 Broker，保证高可用
```

```text
Partition 0：Leader(Broker1) + Follower(Broker2) + Follower(Broker3)
Partition 1：Leader(Broker2) + Follower(Broker1) + Follower(Broker3)
```

### ISR（In-Sync Replicas）

```text
ISR 是与 Leader 保持同步的副本集合。

正常情况：ISR = 所有副本
异常情况：某个 Follower 同步落后，被踢出 ISR
Leader 挂了：从 ISR 中选举新 Leader（保证数据不丢）

replica.lag.time.max.ms：副本落后多久会被踢出 ISR
```

### 副本机制的意义

```text
1. 高可用 —— Leader 挂了，ISR 中选举新 Leader
2. 数据安全 —— acks=all 时，所有 ISR 确认才算成功
3. 容灾 —— 副本跨 Broker、跨机架部署
```

## Kafka Streams

Kafka Streams 是 Kafka 的流处理库，用于实时处理 Kafka 中的数据流。

### 引入依赖

```xml
<dependency>
    <groupId>org.apache.kafka</groupId>
    <artifactId>kafka-streams</artifactId>
</dependency>
```

### 基础流处理

```java
@Configuration
public class StreamsConfig {

    @Bean
    public KStream<String, String> process(StreamsBuilder builder) {
        // 从 input-topic 读取
        KStream<String, String> stream = builder.stream("input-topic");

        // 处理：过滤、转换
        KStream<String, String> filtered = stream
            .filter((key, value) -> value.contains("error"))   // 过滤
            .mapValues(value -> value.toUpperCase());          // 转换

        // 写入 output-topic
        filtered.to("output-topic");
        return filtered;
    }
}
```

### 常见流操作

```java
// 聚合（按 key 分组统计）
KTable<String, Long> counts = stream
    .groupByKey()
    .count();

// 窗口聚合（每分钟统计）
KTable<Windowed<String>, Long> windowCounts = stream
    .groupByKey()
    .windowedBy(TimeWindows.of(Duration.ofMinutes(1)))
    .count();

// 连接两个流
KStream<String, String> joined = stream1.join(stream2, ...);
```

### Kafka Streams 应用场景

```text
1. 实时统计（点击量、订单量）
2. 数据清洗（过滤、转换）
3. 实时告警（异常检测）
4. 数据管道（ETL）
```

## Kafka vs RabbitMQ

| 维度 | Kafka | RabbitMQ |
|------|-------|----------|
| 吞吐量 | 百万级 | 万级 |
| 延迟 | 毫秒级 | 微秒级 |
| 消息模型 | 日志（append-only） | 队列（消费后删除） |
| 消息回溯 | 支持（offset） | 不支持 |
| 消费模型 | 拉取（pull） | 推送（push） |
| 顺序保证 | 分区内有序 | 队列内有序 |
| 路由 | 无（只有 topic） | 灵活（4 种交换机） |
| 适用场景 | 高吞吐、日志、流处理 | 业务消息、低延迟 |

## 应用场景实战

### 场景 1：订单消息处理

```java
// 生产者
@Service
public class OrderProducer {
    @Autowired
    private KafkaTemplate<String, Object> kafkaTemplate;

    public void sendOrderCreated(Order order) {
        // key = 用户ID，保证同一用户的订单顺序消费
        kafkaTemplate.send("order-topic", String.valueOf(order.getUserId()), order);
    }
}

// 消费者
@Component
public class OrderConsumer {

    @KafkaListener(topics = "order-topic", groupId = "order-service")
    public void handle(Order order, Acknowledgment ack) {
        try {
            orderService.process(order);
            ack.acknowledge();
        } catch (Exception e) {
            // 处理失败，不提交 offset，会重新消费
            log.error("订单处理失败", e);
            throw e;
        }
    }
}
```

### 场景 2：日志采集与实时统计（Kafka Streams）

```java
@Configuration
public class ClickStreamConfig {

    @Bean
    public KStream<String, String> clickProcess(StreamsBuilder builder) {
        // 从点击日志流读取
        KStream<String, String> clicks = builder.stream("click-topic");

        // 按页面分组统计点击量
        KTable<String, Long> pageViews = clicks
            .map((key, value) -> KeyValue.pair(extractPage(value), value))
            .groupByKey()
            .count();

        // 输出统计结果
        pageViews.toStream().to("page-views-topic");
        return clicks;
    }
}
```

### 场景 3：多消费者组（广播 + 点对点）

```java
// 广播：不同 group 各自消费全量消息
@KafkaListener(topics = "order-topic", groupId = "notification-service")
public void notifyConsumer(Order order) {
    notificationService.notify(order);   // 通知服务也收到订单
}

@KafkaListener(topics = "order-topic", groupId = "inventory-service")
public void inventoryConsumer(Order order) {
    inventoryService.deduct(order);      // 库存服务也收到订单
}

// 点对点：同 group 内负载均衡
@KafkaListener(topics = "order-topic", groupId = "order-service", concurrency = "3")
public void orderConsumer(Order order) {
    orderService.process(order);         // 3 个消费者分摊订单
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **acks=all + 幂等**。生产环境最安全的配置。

2. **消费者组设计**。一个服务一个 group，实现服务间广播；同服务多实例同 group，实现负载均衡。

3. **手动提交 offset**。处理成功再提交，保证 at-least-once。

4. **分区数提前规划**。分区数只能增不能减，且 consumer 并发受分区数限制。

5. **关键业务消息用 key**。同 key 进同分区，保证顺序消费。

### 踩坑记录

**坑 1：consumer 数量超过 partition 数**

```text
group 内 5 个 consumer，但 topic 只有 3 个 partition
→ 2 个 consumer 空闲，白占资源
```

consumer 数量 ≤ partition 数量，多余的空闲。

**坑 2：auto-offset-reset 理解错误**

```yaml
spring:
  kafka:
    consumer:
      auto-offset-reset: earliest   # 无 offset 时从最早开始
      # latest = 从最新开始（会错过历史消息）
```

earliest 会消费历史消息（可能重复消费），latest 会错过历史。新 group 首次消费要明确。

**坑 3：自动提交 offset 丢消息**

```yaml
spring:
  kafka:
    consumer:
      enable-auto-commit: true   # 自动提交，处理到一半挂了，offset 已提交，消息丢失
```

重要业务手动提交 offset（处理成功后 ack）。

**坑 4：重试导致的顺序问题**

```java
// 重试时，同分区的后续消息先被消费，破坏顺序
// 需要重试队列或将失败消息发到重试 topic
```

Kafka 消费重试会破坏分区内顺序，需要重试 topic 或死信 topic 处理。

**坑 5：JSON 反序列化类型问题**

```yaml
spring:
  kafka:
    consumer:
      properties:
        spring.json.trusted.packages: "com.example.*"  # 指定可信包
        spring.json.value.default.type: com.example.Order  # 指定类型
```

JSON 反序列化需要指定类型或可信包，否则反序列化失败或安全告警。

**坑 6：Kafka 消息延迟问题**

```text
linger.ms 配置过大（如 500ms），消息在缓冲区等待凑批，导致延迟
```

低延迟场景调小 linger.ms（如 5ms），或容忍批量延迟。

**坑 7：分区倾斜（数据热点）**

```text
某些 key 的数据量特别大，导致对应分区数据堆积，其他分区空闲
```

key 设计要均匀分布，或对热点 key 加随机后缀打散。
