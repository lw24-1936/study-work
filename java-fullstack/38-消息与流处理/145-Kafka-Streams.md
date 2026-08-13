---
title: Kafka Streams
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [kafka-streams, stream, ktable, processor, state-store, window]
---

# Kafka Streams

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [Stream 与 KTable](#stream-与-ktable)
- [Processor 处理器](#processor-处理器)
- [State Store 状态存储](#state-store-状态存储)
- [Window 窗口](#window-窗口)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Kafka Streams 是 Kafka 的流处理库，用 Java 实时处理 Kafka 中的数据流。

```text
Kafka Streams 的特点：
1. 轻量 —— 只是一个库，嵌入应用（不依赖集群）
2. 流处理 —— 实时处理 Kafka 数据
3. 状态化 —— State Store 保存状态
4. 精确一次 —— 支持 Exactly Once
```

```text
Kafka Streams vs Flink：
Kafka Streams —— 轻量库，嵌入应用，适合简单流处理
Flink —— 独立集群，功能更强，适合复杂场景
```

## Stream 与 KTable

### KStream

```text
KStream —— 记录流，每条记录独立（类似插入日志）
```

```java
KStream<String, String> stream = builder.stream("input-topic");

stream.filter((key, value) -> value.contains("ERROR"))
    .mapValues(String::toUpperCase)
    .to("output-topic");
```

### KTable

```text
KTable —— 变更流，记录最新状态（类似表，key 唯一）
```

```java
KTable<String, Long> table = builder.table("user-status-topic");
// 每个 key 只保留最新值
```

### KStream vs KTable

| 维度 | KStream | KTable |
|------|---------|--------|
| 语义 | 记录流（追加） | 变更流（更新） |
| 重复 key | 保留每条 | 只保留最新 |
| 类比 | 日志 | 数据库表 |
| 场景 | 事件流 | 状态快照 |

```text
KStream 例子：订单事件（每条订单都是独立记录）
KTable 例子：用户信息（每个用户只保留最新）
```

## Processor 处理器

Processor API 是 Kafka Streams 的底层 API，比 DSL 更灵活。

### Processor API

```java
Topology topology = new Topology();

topology.addSource("source", "input-topic")
    .addProcessor("process", MyProcessor::new, "source")
    .addSink("sink", "output-topic", "process");
```

```java
public class MyProcessor implements Processor<String, String> {
    private ProcessorContext context;

    @Override
    public void init(ProcessorContext context) {
        this.context = context;
    }

    @Override
    public void process(String key, String value) {
        // 处理每条记录
        if (value.contains("ERROR")) {
            context.forward(key, value);   // 转发到下游
        }
    }

    @Override
    public void close() { }
}
```

### DSL vs Processor API

```text
DSL —— 高级，声明式（filter/map/groupBy），够用 90% 场景
Processor API —— 低级，灵活，复杂场景
```

## State Store 状态存储

State Store 保存流处理的状态（如累计计数）。

### 状态存储

```java
// 创建状态存储
KeyValueBytesStoreSupplier storeSupplier =
    Stores.persistentKeyValueStore("count-store");

StreamsBuilder builder = new StreamsBuilder();
KStream<String, String> stream = builder.stream("input-topic");

stream.groupByKey()
    .count(Materialized.as("count-store"));   // 结果存状态存储
```

### 状态存储的用途

```text
1. 聚合 —— 累计计数、求和
2. 连接 —— stream-table join
3. 去重 —— 记录已处理的数据
```

### 状态存储的持久化

```text
状态存储在本地磁盘（RocksDB），
配合 changelog topic 实现容错
```

## Window 窗口

窗口把流切成时间段，进行聚合。

### 窗口类型

```java
// 滚动窗口（固定，不重叠）
TimeWindows.of(Duration.ofMinutes(5));

// 滑动窗口（固定，重叠）
TimeWindows.of(Duration.ofMinutes(10)).advanceBy(Duration.ofMinutes(5));

// 会话窗口（动态，按活动间隔）
SessionWindows.with(Duration.ofMinutes(5));
```

### 窗口聚合

```java
KTable<Windowed<String>, Long> windowedCounts = stream
    .groupByKey()
    .windowedBy(TimeWindows.of(Duration.ofMinutes(1)))   // 每分钟
    .count();

windowedCounts.toStream().to("windowed-output");
```

## 应用场景实战

### 场景 1：实时点击量统计

```java
StreamsBuilder builder = new StreamsBuilder();

KStream<String, String> clicks = builder.stream("click-topic");

// 按页面分组，统计点击量
KTable<String, Long> pageViews = clicks
    .map((key, value) -> KeyValue.pair(extractPage(value), value))
    .groupByKey()
    .count();

pageViews.toStream().to("page-views-topic");
```

### 场景 2：实时单词计数（含窗口）

```java
KStream<String, String> text = builder.stream("text-topic");

KTable<Windowed<String>, Long> wordCounts = text
    .flatMapValues(value -> Arrays.asList(value.split(" ")))
    .groupBy((key, word) -> word)
    .windowedBy(TimeWindows.of(Duration.ofMinutes(1)))
    .count();

wordCounts.toStream().to("word-count-topic");
```

### 场景 3：数据过滤与转换

```java
// 过滤错误日志，转换为告警
KStream<String, String> logs = builder.stream("logs-topic");

logs.filter((key, value) -> value.contains("ERROR"))
    .mapValues(value -> "ALERT: " + value)
    .to("alert-topic");
```

## 最佳实践与踩坑记录

### 最佳实践

1. **状态用持久化存储**。Materialized.as 指定状态存储，配合 changelog 容错。

2. **窗口类型选对**。滚动/滑动/会话按场景选择。

3. **Exactly Once 配置**。processing.guarantee=exactly_once。

4. **监控 lag 和状态**。监控消费延迟和状态大小。

5. **状态要 TTL**。避免状态无限增长。

### 踩坑记录

**坑 1：KStream 和 KTable 混用错误**

```java
// KStream 是记录流，KTable 是变更流，语义不同
// join 时要注意类型匹配
```

理解 KStream（追加）和 KTable（更新）的语义区别。

**坑 2：状态无限增长**

```text
groupByKey 后 count，key 无限增长，状态膨胀
```

用窗口限制状态范围，或定期清理。

**坑 3：没配置状态存储目录**

```text
State Store 默认存 /tmp，重启丢失
```

配置 state.dir 到持久目录。

**坑 4：忽略 Exactly Once 配置**

```text
默认 At Least Once，可能重复处理
```

需要精确一次时配置 processing.guarantee=exactly_once。

**坑 5：窗口数据乱序**

```text
事件时间乱序，窗口结果不准
```

用事件时间 + 水位线（watermark）处理乱序。

**坑 6：拓扑太复杂**

```text
一个拓扑做太多事，难维护难调试
```

拆分拓扑，每个拓扑专注一件事。
