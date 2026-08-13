---
title: Spark
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [spark, rdd, dataframe, dataset, spark-sql, spark-streaming]
---

# Spark

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [RDD 弹性分布式数据集](#rdd-弹性分布式数据集)
- [DataFrame 与 Dataset](#dataframe-与-dataset)
- [Spark SQL](#spark-sql)
- [Spark Streaming](#spark-streaming)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spark 是内存计算框架，替代 MapReduce 成为大数据批处理的事实标准，也支持流处理、SQL、机器学习。

```text
Spark 的核心优势（vs MapReduce）：
1. 内存计算 —— 中间结果在内存，比 MapReduce 快 10-100 倍
2. 统一引擎 —— 批处理、流处理、SQL、ML 一个引擎
3. 易用 —— 丰富 API（Java/Scala/Python/SQL）
4. DAG 执行 —— 优化执行计划
```

```text
Spark 四大组件：
1. Spark Core —— RDD（基础）
2. Spark SQL —— DataFrame/Dataset（结构化）
3. Spark Streaming —— 流处理（微批）
4. MLlib —— 机器学习
```

## RDD 弹性分布式数据集

RDD（Resilient Distributed Dataset）是 Spark 的核心抽象，不可变、可分区、可容错的分布式集合。

### RDD 的特点

```text
1. 弹性（Resilient）—— 数据丢失可重建（血缘 lineage）
2. 分布式（Distributed）—— 数据分布在集群节点
3. 数据集（Dataset）—— 元素集合
```

### RDD 操作

```java
// 创建 RDD
JavaSparkContext sc = new JavaSparkContext(conf);
JavaRDD<String> lines = sc.textFile("hdfs:///data/log.txt");

// 转换（Transformation，惰性）
JavaRDD<String> errors = lines.filter(line -> line.contains("ERROR"));
JavaRDD<String> words = lines.flatMap(line -> Arrays.asList(line.split(" ")).iterator());

// 行动（Action，触发计算）
long count = errors.count();              // 统计
List<String> top10 = words.take(10);      // 取前 10
```

### Transformation vs Action

```text
Transformation（转换）—— 惰性，不立即计算（filter/map/flatMap）
Action（行动）—— 触发计算（count/collect/take/save）

RDD 是惰性的：定义转换不执行，遇到 Action 才执行
```

### RDD 的局限

```text
1. 无 schema —— 数据无结构，操作低级
2. 性能优化难 —— 需手动优化
3. 序列化开销 —— Java 对象序列化

已被 DataFrame/Dataset 替代（更高效）
```

## DataFrame 与 Dataset

DataFrame 和 Dataset 是 Spark SQL 的结构化 API，比 RDD 更高效。

### DataFrame

```java
// DataFrame = 带 schema 的分布式数据集（类似表）
Dataset<Row> df = spark.read().json("data.json");
df.select("name", "age").filter("age > 18").show();
```

### Dataset

```java
// Dataset = 类型安全的 DataFrame
Dataset<User> users = spark.read().json("data.json").as(Encoders.bean(User.class));
Dataset<String> names = users.map(User::getName, Encoders.STRING());
```

### RDD vs DataFrame vs Dataset

| 维度 | RDD | DataFrame | Dataset |
|------|-----|-----------|---------|
| Schema | 无 | 有 | 有 |
| 类型安全 | 是 | 否（编译期） | 是 |
| 性能 | 低 | 高（优化） | 高 |
| 优化 | 手动 | Catalyst 优化 | Catalyst 优化 |
| 适用 | 底层 | 结构化数据 | 类型安全 |

```text
选择建议：
- 结构化数据 → DataFrame（最常用）
- 需要类型安全 → Dataset
- 底层操作 → RDD（少用）
```

## Spark SQL

Spark SQL 用 SQL 查询结构化数据，是 Spark 最常用的组件。

### 基本用法

```java
// 注册临时视图
df.createOrReplaceTempView("users");

// SQL 查询
Dataset<Row> result = spark.sql(
    "SELECT age, COUNT(*) AS cnt FROM users GROUP BY age");
```

### Spark SQL 示例

```sql
-- 聚合统计
SELECT category, SUM(amount) AS total
FROM orders
WHERE dt >= '2026-01-01'
GROUP BY category;

-- 连接查询
SELECT o.order_id, u.name
FROM orders o
JOIN users u ON o.user_id = u.user_id;
```

### Spark SQL vs Hive

```text
Spark SQL —— 基于内存，快
Hive —— 基于 MapReduce，慢

Spark SQL 可以读取 Hive 表（共享 MetaStore）
```

## Spark Streaming

Spark Streaming 用微批（micro-batch）处理流数据，把流数据切成小批次处理。

### 微批处理原理

```text
Spark Streaming = 微批处理（不是真正的流处理）

数据流 → 切成小批次（如每 1 秒一批）→ 每批用 RDD 处理
```

### 基本用法

```java
JavaStreamingContext ssc = new JavaStreamingContext(conf, Durations.seconds(1));

// 从 Kafka 读取流
JavaInputDStream<ConsumerRecord<String, String>> stream =
    KafkaUtils.createDirectStream(ssc, ..., topics);

// 处理
stream.map(record -> record.value())
    .flatMap(line -> Arrays.asList(line.split(" ")).iterator())
    .mapToPair(word -> new Tuple2<>(word, 1))
    .reduceByKey(Integer::sum)
    .print();

ssc.start();
ssc.awaitTermination();
```

### Spark Streaming vs Flink

```text
Spark Streaming —— 微批（不是真正的流，有延迟）
Flink —— 真正的流处理（逐条处理，低延迟）

实时性要求高 → Flink
统一批流 → Spark Structured Streaming
```

## 应用场景实战

### 场景 1：日志分析（Spark SQL）

```java
// 读取日志，统计分析
Dataset<Row> logs = spark.read().json("hdfs:///logs/2026-01-01/*.json");

logs.createOrReplaceTempView("logs");

// 统计错误分布
Dataset<Row> errorStats = spark.sql(
    "SELECT error_type, COUNT(*) AS cnt " +
    "FROM logs WHERE level = 'ERROR' " +
    "GROUP BY error_type ORDER BY cnt DESC");
```

### 场景 2：实时统计（Spark Streaming）

```java
// 实时统计订单量（微批）
JavaInputDStream<ConsumerRecord<String, String>> orders =
    KafkaUtils.createDirectStream(ssc, ..., topics);

orders.map(record -> 1)
    .reduce((a, b) -> a + b)   // 累计订单量
    .print();
```

## 最佳实践与踩坑记录

### 最佳实践

1. **优先用 DataFrame/Dataset**。比 RDD 快、易用。

2. **避免 collect 大数据**。collect 把数据拉到 Driver，会 OOM。

3. **用持久化（cache）**。多次使用的数据缓存。

4. **合理分区**。分区数匹配数据量和集群核数。

5. **避免 shuffle**。shuffle 是性能瓶颈，减少不必要的 shuffle。

### 踩坑记录

**坑 1：collect 大数据 OOM**

```java
List<Row> all = df.collect();   // 百万行 collect 到 Driver，OOM
```

大数据用 take/save，不要 collect 到 Driver。

**坑 2：shuffle 过多导致慢**

```text
频繁 groupBy、join 导致大量 shuffle，性能差
```

减少 shuffle，或广播小表（broadcast join）。

**坑 3：分区数不合理**

```text
分区数太少（并行度不够）或太多（调度开销大）
```

分区数 ≈ 核数的 2-3 倍。

**坑 4：惰性求值误解**

```java
df.filter(...);   // 以为执行了，实际没执行（惰性）
// 没调用 Action，什么都没发生
```

RDD/DataFrame 是惰性的，要调用 Action（count/show/save）才执行。

**坑 5：序列化问题**

```text
闭包里引用的对象没序列化，任务分发报错
```

闭包里的对象要可序列化，或广播变量。

**坑 6：Spark Streaming 不是真流**

```text
用 Spark Streaming 做低延迟场景（毫秒级），达不到要求
```

低延迟用 Flink（真流处理）。
