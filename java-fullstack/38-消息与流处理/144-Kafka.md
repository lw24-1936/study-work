---
title: Kafka
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [kafka, producer, consumer, topic, partition, offset, consumer-group, replication, isr]
---

# Kafka

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [核心架构](#核心架构)
- [Producer 与 Consumer](#producer-与-consumer)
- [Consumer Group 与 Offset](#consumer-group-与-offset)
- [Replication 与 ISR](#replication-与-isr)
- [高性能原理](#高性能原理)
- [应用场景实战](#应用场景实战)

## 概述

Kafka 是分布式流处理平台，以高吞吐、持久化、可扩展著称，是消息与流处理的核心组件。

```text
Kafka 在流处理中的角色：
1. 消息队列 —— 系统间异步通信
2. 流处理平台 —— Kafka Streams 实时处理
3. 数据管道 —— 数据采集、传输
4. 事件溯源 —— 记录所有事件
```

```text
核心特点：
1. 高吞吐 —— 百万级消息/秒
2. 持久化 —— 消息落盘，可回溯
3. 水平扩展 —— 分区 + 副本
```

## 核心架构

### 核心概念

```text
Broker —— Kafka 节点
Topic —— 主题（消息分类）
Partition —— 分区（Topic 的物理分片）
Offset —— 偏移量（消息在分区内的位置）
Replica —— 副本（分区的备份）
ISR —— 同步副本集合
```

```text
Topic "orders"
├── Partition 0（Leader + Followers）
├── Partition 1
└── Partition 2
```

### 分区与顺序

```text
1. 同一 Partition 内消息有序
2. 跨 Partition 无序
3. 同 key 消息进同一分区（保证顺序）
```

## Producer 与 Consumer

### Producer

```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("acks", "all");                        // 所有副本确认
props.put("key.serializer", StringSerializer.class);
props.put("value.serializer", StringSerializer.class);

KafkaProducer<String, String> producer = new KafkaProducer<>(props);

// 发送消息
producer.send(new ProducerRecord<>("topic", "key", "value"), (metadata, e) -> {
    if (e != null) {
        e.printStackTrace();    // 发送失败
    }
});
```

### Producer 关键配置

```text
acks —— 确认机制（0/1/all）
retries —— 重试次数
batch.size —— 批量大小
linger.ms —— 批量等待时间
```

### Consumer

```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("group.id", "order-group");            // 消费组
props.put("enable.auto.commit", "false");        // 手动提交
props.put("key.deserializer", StringDeserializer.class);
props.put("value.deserializer", StringDeserializer.class);

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("topic"));

while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, String> record : records) {
        System.out.println(record.value());
    }
    consumer.commitSync();   // 手动提交 offset
}
```

## Consumer Group 与 Offset

### Consumer Group

```text
1. 同组内，一个分区只能被一个消费者消费
2. 不同组各自消费全量（广播）
3. 组内消费者数 > 分区数，多余的空闲
```

```text
组内负载均衡 + 组间广播：
group A：consumer1 消费 partition 0、1
         consumer2 消费 partition 2
group B：consumer3 消费 partition 0、1、2（独立消费全量）
```

### Offset 管理

```text
Offset 记录消费进度：
1. 自动提交 —— 定时提交，可能丢消息
2. 手动提交 —— 处理成功提交，至少一次
```

```text
Offset 的用途：
1. 断点续消费
2. 重复消费（重置 offset）
3. 消息回溯
```

## Replication 与 ISR

### 副本机制

```text
每个分区有多个副本：
Leader —— 处理读写
Follower —— 从 Leader 同步数据
```

```text
Partition 0：Leader(Broker1) + Follower(Broker2) + Follower(Broker3)
```

### ISR 同步副本

```text
ISR（In-Sync Replicas）= 与 Leader 保持同步的副本集合

1. Follower 同步落后，被踢出 ISR
2. Leader 故障，从 ISR 选举新 Leader
3. acks=all 时，所有 ISR 确认才算成功
```

### 副本的意义

```text
1. 高可用 —— Leader 故障，ISR 选举新 Leader
2. 数据安全 —— 副本跨节点存储
3. 容灾 —— 副本跨机架/机房
```

## 高性能原理

Kafka 高性能的四大原因。

### 1. 顺序写磁盘

```text
Kafka 消息追加写（append-only），顺序写磁盘
顺序写比随机写快几百倍（省去磁头寻道）
```

### 2. 零拷贝

```text
传统传输：磁盘 → 内核缓冲区 → 用户缓冲区 → 内核 → 网络（多次拷贝）
零拷贝：磁盘 → 内核缓冲区 → 网络（sendfile，省去用户态拷贝）
```

### 3. 页缓存

```text
消息先写页缓存（Page Cache），由操作系统决定何时刷盘
读消息优先读页缓存，命中则不走磁盘
```

### 4. 批量处理

```text
生产者批量发送（batch），消费者批量拉取（poll）
减少网络往返，提升吞吐
```

## 应用场景实战

### 场景 1：消息队列（异步解耦）

```text
订单系统 → Kafka → 库存系统/通知系统/统计系统
```

### 场景 2：日志采集

```text
应用日志 → Kafka → 实时分析（Flink）/ 存储（HDFS）
```

### 场景 3：流处理（配合 Kafka Streams）

```text
数据流 → Kafka → Kafka Streams 实时处理 → 结果
```

## 最佳实践与踩坑记录

### 最佳实践

1. **acks=all + 幂等**。生产环境最安全配置。

2. **分区数提前规划**。分区数只能增不能减。

3. **手动提交 offset**。重要业务处理成功再提交。

4. **关键消息用 key**。同 key 进同分区保证顺序。

5. **监控 lag**。消费 lag 过大说明消费跟不上。

### 踩坑记录

**坑 1：consumer 数超过 partition 数**

```text
组内 5 个 consumer，topic 只有 3 个 partition，2 个空闲
```

consumer 数 ≤ partition 数。

**坑 2：自动提交丢消息**

```text
自动提交 offset，处理到一半挂了，offset 已提交，消息丢失
```

重要业务手动提交 offset。

**坑 3：acks=0 丢消息**

```text
acks=0 不等确认，Leader 挂了消息丢失
```

生产环境用 acks=all。

**坑 4：分区倾斜**

```text
某些 key 数据量大，对应分区堆积，其他分区空闲
```

key 设计均匀，或热点 key 打散。

**坑 5：忽略消费 lag**

```text
消费 lag 持续增长，消息延迟越来越大，最终堆积
```

监控 lag，及时扩容或优化消费逻辑。

**坑 6：重试破坏顺序**

```text
消费失败重试，同分区后续消息先被消费，顺序破坏
```

重试用重试 topic，或接受分区内局部有序。
