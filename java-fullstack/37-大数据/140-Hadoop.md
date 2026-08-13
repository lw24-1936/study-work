---
title: Hadoop
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [hadoop, hdfs, mapreduce, yarn]
---

# Hadoop

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [HDFS 分布式文件系统](#hdfs-分布式文件系统)
- [MapReduce 计算模型](#mapreduce-计算模型)
- [YARN 资源调度](#yarn-资源调度)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Hadoop 是大数据生态的基石，提供分布式存储（HDFS）和分布式计算（MapReduce）。

```text
Hadoop 三大核心组件：
1. HDFS —— 分布式文件系统（存储海量数据）
2. MapReduce —— 分布式计算模型（并行处理数据）
3. YARN —— 资源调度（管理计算资源）
```

```text
Hadoop 的价值：
1. 海量存储 —— 横向扩展存储 PB 级数据
2. 并行计算 —— 多机并行处理
3. 容错 —— 数据多副本，节点故障不丢数据
4. 廉价硬件 —— 用普通服务器构建集群
```

## HDFS 分布式文件系统

HDFS（Hadoop Distributed File System）是分布式文件系统，存储海量数据。

### HDFS 架构

```text
NameNode（主节点）—— 管理元数据（文件目录、块位置）
DataNode（数据节点）—— 存储实际数据块
```

```text
        NameNode（元数据：文件 → 块 → DataNode）
        │
   ┌────┼────┐
   │    │    │
DataNode1 DataNode2 DataNode3（存储数据块）
```

### 数据块（Block）

```text
1. 文件被切分成块（默认 128MB）
2. 每个块有 3 个副本（默认）
3. 副本分布在不同节点（容错）
```

```text
文件（500MB）→ 块1(128MB) + 块2(128MB) + 块3(128MB) + 块4(116MB)
每个块 3 个副本，分布在不同 DataNode
```

### HDFS 的特点

```text
1. 大文件友好 —— 适合大文件（GB/TB），不适合大量小文件
2. 一次写入多次读 —— 适合批处理，不适合随机写
3. 容错 —— 副本机制，节点故障自动恢复
4. 高吞吐 —— 顺序读写，吞吐高
```

### HDFS 命令

```bash
hdfs dfs -ls /                 # 列出目录
hdfs dfs -mkdir /data          # 创建目录
hdfs dfs -put local.txt /data/ # 上传文件
hdfs dfs -get /data/local.txt ./  # 下载文件
hdfs dfs -cat /data/local.txt  # 查看文件
hdfs dfs -rm /data/local.txt   # 删除文件
```

## MapReduce 计算模型

MapReduce 是分布式计算模型，分 Map 和 Reduce 两阶段并行处理数据。

### MapReduce 原理

```text
Map（映射）—— 并行处理每个数据块，输出键值对
Reduce（归约）—— 汇总相同 key 的结果
```

```text
以词频统计（WordCount）为例：
输入：["hello world", "hello hadoop"]

Map 阶段（每个块并行）：
  "hello world" → [hello:1, world:1]
  "hello hadoop" → [hello:1, hadoop:1]

Shuffle（分组）：
  hello: [1, 1]
  world: [1]
  hadoop: [1]

Reduce 阶段（汇总）：
  hello: 2
  world: 1
  hadoop: 1
```

### WordCount 实现

```java
public class WordCount {

    // Map 阶段
    public static class TokenizerMapper
            extends Mapper<Object, Text, Text, IntWritable> {

        private final static IntWritable one = new IntWritable(1);
        private Text word = new Text();

        public void map(Object key, Text value, Context context)
                throws IOException, InterruptedException {
            StringTokenizer itr = new StringTokenizer(value.toString());
            while (itr.hasMoreTokens()) {
                word.set(itr.nextToken());
                context.write(word, one);   // 每个词输出 (word, 1)
            }
        }
    }

    // Reduce 阶段
    public static class IntSumReducer
            extends Reducer<Text, IntWritable, Text, IntWritable> {

        public void reduce(Text key, Iterable<IntWritable> values, Context context)
                throws IOException, InterruptedException {
            int sum = 0;
            for (IntWritable val : values) {
                sum += val.get();   // 汇总
            }
            context.write(key, new IntWritable(sum));
        }
    }
}
```

### MapReduce 的局限

```text
1. 慢 —— 磁盘 IO 多（中间结果落盘）
2. 编程复杂 —— Map/Reduce 两阶段，难表达复杂逻辑
3. 不适合迭代计算 —— 机器学习需要多次迭代，MapReduce 低效

已被 Spark/Flink 替代（内存计算，更快）
```

## YARN 资源调度

YARN（Yet Another Resource Negotiator）是资源管理和任务调度框架。

### YARN 架构

```text
ResourceManager（资源管理器）—— 分配资源
NodeManager（节点管理器）—— 管理单个节点资源
ApplicationMaster —— 管理单个应用
Container —— 资源容器（CPU + 内存）
```

```text
YARN 的作用：
1. 资源管理 —— 统一管理集群 CPU/内存
2. 任务调度 —— 分配资源给任务
3. 多框架支持 —— MapReduce、Spark、Flink 都跑在 YARN 上
```

### YARN 的调度

```text
调度策略：
1. FIFO —— 先进先出（简单，不公平）
2. Capacity —— 容量调度（按队列分配）
3. Fair —— 公平调度（按权重公平）
```

## 应用场景实战

### 场景 1：日志分析（HDFS + MapReduce）

```text
1. 日志采集 → HDFS 存储
2. MapReduce 分析（统计 PV、UV）
3. 结果写入 HDFS/数据库
```

### 场景 2：Hadoop 生态定位

```text
Hadoop 生态：
- HDFS —— 存储（数据湖底座）
- MapReduce —— 计算（已被 Spark 替代）
- YARN —— 调度（Spark/Flink 跑在 YARN 上）
- Hive —— 数据仓库（SQL 查询）
- Spark —— 内存计算（替代 MapReduce）
- Flink —— 实时流处理
```

## 最佳实践与踩坑记录

### 最佳实践

1. **HDFS 存大文件**。小文件多会压垮 NameNode（元数据膨胀）。

2. **MapReduce 已被 Spark 替代**。新项目用 Spark，不用 MapReduce。

3. **YARN 资源合理分配**。按队列分配，避免资源抢占。

4. **副本数权衡**。副本多容错好但占空间，一般 3 副本。

### 踩坑记录

**坑 1：大量小文件**

```text
HDFS 存大量小文件（几 KB），NameNode 元数据爆炸，性能下降
```

小文件合并（SequenceFile、Parquet），或先合并再存。

**坑 2：NameNode 单点故障**

```text
NameNode 是单点，挂了整个集群不可用（HA 前）
```

用 NameNode HA（双 NameNode + 共享存储）。

**坑 3：MapReduce 中间结果落盘慢**

```text
MapReduce 频繁磁盘 IO，迭代计算极慢
```

迭代计算用 Spark（内存计算）。

**坑 4：YARN 资源分配不合理**

```text
单个任务占满资源，其他任务饿死
```

用 Capacity/Fair 调度器，按队列配额。

**坑 5：数据本地性忽视**

```text
计算和数据不在同一节点，网络传输慢
```

调度时考虑数据本地性（计算移到数据所在节点）。

**坑 6：HDFS 不适合随机写**

```text
HDFS 是追加写，随机修改文件低效
```

HDFS 适合一次写多次读，随机写场景用 HBase。
