---
title: Flink
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [flink, datastream, table-api, sql, window, state, checkpoint, exactly-once]
---

# Flink

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [DataStream 流处理](#datastream-流处理)
- [Table API 与 SQL](#table-api-与-sql)
- [Window 窗口](#window-窗口)
- [State 状态与 Checkpoint](#state-状态与-checkpoint)
- [Exactly Once 精确一次](#exactly-once-精确一次)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Flink 是真正的流处理框架，以低延迟、高吞吐、精确一次（Exactly Once）著称。

```text
Flink 的核心优势：
1. 真正的流处理 —— 逐条处理（不是微批）
2. 低延迟 —— 毫秒级
3. Exactly Once —— 精确一次语义
4. 状态管理 —— 强大的 State 和 Checkpoint
5. 批流统一 —— 批处理是流处理的特殊情况
```

```text
Flink vs Spark Streaming：
Flink —— 真流处理（逐条），低延迟
Spark Streaming —— 微批（小批次），延迟较高

实时性要求高 → Flink
```

## DataStream 流处理

DataStream 是 Flink 的核心抽象，表示数据流。

### 基本用法

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

// 从 Kafka 读取
DataStream<String> stream = env.addSource(
    new FlinkKafkaConsumer<>("topic", new SimpleStringSchema(), props));

// 处理
DataStream<WordCount> result = stream
    .flatMap((String line, Collector<String> out) -> {
        for (String word : line.split(" ")) {
            out.collect(word);
        }
    })
    .returns(Types.STRING)
    .map(word -> new Tuple2<>(word, 1))
    .returns(Types.TUPLE(Types.STRING, Types.INT))
    .keyBy(t -> t.f0)              // 按 word 分组
    .sum(1);                       // 求和

result.print();
env.execute("word count");
```

### 核心算子

```text
map —— 一对一转换
flatMap —— 一对多转换
filter —— 过滤
keyBy —— 分组（类似 group by）
reduce —— 归约
window —— 窗口
```

## Table API 与 SQL

Flink 的 Table API 和 SQL 用类 SQL 语法处理流数据。

### SQL 查询

```java
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);

// 注册表
tableEnv.createTemporaryView("orders", stream);

// SQL 查询
Table result = tableEnv.sqlQuery(
    "SELECT user_id, SUM(amount) AS total " +
    "FROM orders " +
    "GROUP BY user_id");
```

### Table API

```java
Table result = tableEnv.from("orders")
    .groupBy($("user_id"))
    .select($("user_id"), $("amount").sum().as("total"));
```

## Window 窗口

窗口把无限流切成有限的数据段，进行聚合计算。

### 窗口类型

```text
1. Tumbling Window（滚动窗口）—— 固定大小，不重叠
2. Sliding Window（滑动窗口）—— 固定大小，有重叠
3. Session Window（会话窗口）—— 按活动间隔
```

### 滚动窗口

```java
// 每 5 分钟统计一次
stream.keyBy(t -> t.f0)
    .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
    .sum(1);
```

### 滑动窗口

```java
// 窗口 10 分钟，每 5 分钟滑动一次（有重叠）
stream.keyBy(t -> t.f0)
    .window(SlidingProcessingTimeWindows.of(Time.minutes(10), Time.minutes(5)))
    .sum(1);
```

### 窗口类型对比

| 窗口 | 大小 | 重叠 | 场景 |
|------|------|------|------|
| 滚动 | 固定 | 无 | 每分钟统计 |
| 滑动 | 固定 | 有 | 最近 10 分钟（每 5 分钟更新） |
| 会话 | 动态 | 无 | 用户会话 |

## State 状态与 Checkpoint

### State 状态

状态是流处理的中间结果（如累计计数）。

```text
State 类型：
1. ValueState —— 单个值
2. ListState —— 列表
3. MapState —— 键值对
4. ReducingState —— 归约
```

```java
// 使用状态
public class CountFunction extends RichFlatMapFunction<String, Long> {
    private ValueState<Long> countState;

    @Override
    public void open(Configuration config) {
        ValueStateDescriptor<Long> descriptor =
            new ValueStateDescriptor<>("count", Long.class);
        countState = getRuntimeContext().getState(descriptor);
    }

    @Override
    public void flatMap(String value, Collector<Long> out) throws Exception {
        Long count = countState.value();
        count = (count == null) ? 1 : count + 1;
        countState.update(count);
        out.collect(count);
    }
}
```

### Checkpoint 检查点

Checkpoint 是状态的快照，用于故障恢复。

```java
// 配置 Checkpoint
env.enableCheckpointing(60000);   // 每 60 秒做一次快照
env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
env.getCheckpointConfig().setMinPauseBetweenCheckpoints(30000);
```

```text
Checkpoint 的作用：
1. 故障恢复 —— 从最近的 checkpoint 恢复
2. 保证 Exactly Once —— 配合状态和事务
3. 状态快照 —— 定期保存状态
```

## Exactly Once 精确一次

Exactly Once 是 Flink 的关键特性，保证每条数据只被处理一次。

### 三种语义

```text
At Most Once（至多一次）—— 可能丢数据
At Least Once（至少一次）—— 可能重复
Exactly Once（精确一次）—— 不丢不重
```

### Flink 如何实现 Exactly Once

```text
1. Checkpoint —— 定期做状态快照
2. 故障恢复 —— 从 checkpoint 恢复，回放未处理的数据
3. 端到端 —— 配合支持事务的 sink（如 Kafka 事务）
```

```text
端到端 Exactly Once 需要：
1. Source 可重放 —— Kafka（offset 可重置）
2. Flink Checkpoint —— 状态快照
3. Sink 幂等/事务 —— Kafka 事务、幂等写入
```

## 应用场景实战

### 场景 1：实时统计 PV/UV

```java
// 实时统计每分钟的 PV
DataStream<Event> events = env.addSource(kafkaSource);

events.keyBy(e -> e.getPageId())
    .window(TumblingProcessingTimeWindows.of(Time.minutes(1)))
    .aggregate(new CountAggregate())
    .print();
```

### 场景 2：实时告警

```java
// 实时检测异常（如登录失败次数超阈值）
DataStream<LoginEvent> logins = env.addSource(kafkaSource);

logins.filter(e -> !e.isSuccess())        // 失败的登录
    .keyBy(e -> e.getUserId())
    .window(TumblingProcessingTimeWindows.of(Time.minutes(5)))
    .aggregate(new CountAggregate())
    .filter(count -> count > 10)          // 5 分钟失败超 10 次
    .print("告警");
```

### 场景 3：实时大屏（订单统计）

```java
// 实时统计订单金额（滚动窗口 + SQL）
tableEnv.createTemporaryView("orders", orderStream);

Table result = tableEnv.sqlQuery(
    "SELECT TUMBLE_START(proctime, INTERVAL '1' MINUTE) AS window_start, " +
    "SUM(amount) AS total_amount " +
    "FROM orders " +
    "GROUP BY TUMBLE(proctime, INTERVAL '1' MINUTE)");
```

## 最佳实践与踩坑记录

### 最佳实践

1. **生产环境开启 Checkpoint**。保证故障恢复和 Exactly Once。

2. **状态用 RocksDB**。大状态用 RocksDB 后端（支持内存外状态）。

3. **合理设置并行度**。并行度匹配 Kafka 分区数和数据量。

4. **监控背压**。背压说明消费跟不上，需要扩容或优化。

5. **窗口类型选对**。滚动/滑动/会话按场景选择。

### 踩坑记录

**坑 1：状态无限增长**

```text
KeyedState 的 key 无限增长（如按 userId 分组），状态膨胀
```

用 TTL 清理过期状态（StateTtlConfig）。

**坑 2：Checkpoint 频繁导致性能下降**

```text
Checkpoint 间隔太短（如 1 秒），快照开销大，性能下降
```

Checkpoint 间隔合理（如 60 秒），状态大用增量 checkpoint。

**坑 3：没配 Checkpoint 故障丢数据**

```text
没开 Checkpoint，任务故障后状态丢失，数据重复或丢失
```

生产环境必须开启 Checkpoint。

**坑 4：并行度设置错误**

```text
并行度 > Kafka 分区数，多余的并行度空转
```

并行度 ≈ Kafka 分区数。

**坑 5：窗口数据延迟丢失**

```text
事件时间窗口，迟到数据被丢弃
```

用 allowedLateness 允许迟到，或 sideOutput 收集迟到数据。

**坑 6：背压不处理**

```text
下游处理慢导致背压，消息堆积，延迟增加
```

监控背压，优化处理逻辑或扩容。
