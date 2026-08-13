---
title: Hive
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [hive, hql, data-warehouse, partition, bucket]
---

# Hive

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [Hive 架构](#hive-架构)
- [HQL 查询语言](#hql-查询语言)
- [Partition 分区](#partition-分区)
- [Bucket 分桶](#bucket-分桶)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Hive 是构建在 Hadoop 之上的数据仓库工具，用 SQL（HQL）查询海量数据。

```text
Hive 是什么：
1. 数据仓库 —— 面向分析（OLAP），不是事务（OLTP）
2. SQL 接口 —— 用 HQL（类似 SQL）查询，转成 MapReduce/Spark
3. 元数据 —— 表结构存 MetaStore（MySQL）
4. 底层存储 —— HDFS
```

```text
Hive 的价值：
1. 降低门槛 —— 会 SQL 就能分析大数据
2. 海量数据 —— 处理 PB 级数据
3. 批处理 —— 适合离线分析（不实时）
```

## Hive 架构

```text
用户（HQL）→ Hive → 编译成 MapReduce/Spark → YARN 执行 → 结果
                       ↓
                    MetaStore（MySQL，表元数据）
                       ↓
                    HDFS（数据存储）
```

### Hive 与数据库的区别

| 维度 | Hive | MySQL |
|------|------|-------|
| 定位 | 数据仓库（分析） | 数据库（事务） |
| 数据量 | PB 级 | GB/TB 级 |
| 延迟 | 分钟级（批处理） | 毫秒级 |
| 事务 | 不支持 | 支持 |
| 更新 | 不更新（追加） | 频繁更新 |
| 存储 | HDFS | 本地磁盘 |

## HQL 查询语言

HQL（Hive SQL）是类 SQL 的查询语言。

### 建表

```sql
CREATE TABLE orders (
    order_id BIGINT,
    user_id BIGINT,
    amount DECIMAL(10, 2),
    create_time STRING
)
PARTITIONED BY (dt STRING)      -- 按日期分区
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',';       -- 字段分隔符
```

### 查询

```sql
-- 基本查询
SELECT * FROM orders WHERE dt = '2026-01-01';

-- 聚合统计
SELECT user_id, SUM(amount) AS total_amount
FROM orders
WHERE dt >= '2026-01-01'
GROUP BY user_id;

-- 排序
SELECT * FROM orders
ORDER BY amount DESC
LIMIT 100;

-- 连接
SELECT o.order_id, u.user_name
FROM orders o
JOIN users u ON o.user_id = u.user_id;
```

### 数据导入

```sql
-- 从本地文件导入
LOAD DATA LOCAL INPATH '/data/orders.csv' INTO TABLE orders PARTITION (dt='2026-01-01');

-- 从 HDFS 导入
LOAD DATA INPATH '/hdfs/data/orders.csv' INTO TABLE orders;
```

## Partition 分区

分区是把表按某个维度（如日期）划分，查询时只扫描相关分区，提升性能。

### 分区的作用

```text
无分区：查询全表（扫描所有数据）
有分区：只扫描相关分区（如查某天，只扫当天数据）
```

```text
orders 表按日期分区：
/data/orders/dt=2026-01-01/
/data/orders/dt=2026-01-02/
/data/orders/dt=2026-01-03/

查询 dt='2026-01-01' 只扫描对应目录，快几十倍
```

### 分区操作

```sql
-- 建分区表
CREATE TABLE orders (...) PARTITIONED BY (dt STRING);

-- 查询指定分区（只扫该分区）
SELECT * FROM orders WHERE dt = '2026-01-01';

-- 查看分区
SHOW PARTITIONS orders;

-- 添加分区
ALTER TABLE orders ADD PARTITION (dt='2026-01-04');
```

### 动态分区

```sql
-- 动态分区：根据数据自动分区
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;

INSERT OVERWRITE TABLE orders PARTITION (dt)
SELECT order_id, user_id, amount, dt FROM source_orders;
```

## Bucket 分桶

分桶是把数据按某个字段哈希分到固定数量的桶，用于抽样和 join 优化。

### 分桶的作用

```text
1. 抽样 —— 快速取样本数据
2. Join 优化 —— 同桶 join 更快
3. 数据均匀 —— 哈希分布
```

### 分桶操作

```sql
-- 建分桶表
CREATE TABLE orders (
    order_id BIGINT,
    user_id BIGINT
)
CLUSTERED BY (user_id) INTO 4 BUCKETS;   -- 按 user_id 分 4 桶
```

### 分区 vs 分桶

| 维度 | 分区（Partition） | 分桶（Bucket） |
|------|------------------|---------------|
| 划分方式 | 按字段值（日期） | 按哈希 |
| 粒度 | 目录级别 | 文件级别 |
| 数量 | 动态（日期多） | 固定（桶数） |
| 场景 | 按日期/地区过滤 | 抽样、join 优化 |

## 应用场景实战

### 场景 1：日活统计

```sql
-- 按日期分区的用户行为表，统计日活
CREATE TABLE user_behavior (
    user_id BIGINT,
    action STRING,
    action_time STRING
)
PARTITIONED BY (dt STRING);

-- 统计某天日活（只扫当天分区）
SELECT COUNT(DISTINCT user_id) AS dau
FROM user_behavior
WHERE dt = '2026-01-01';
```

### 场景 2：订单分析

```sql
-- 按日统计订单量和金额
SELECT dt, COUNT(*) AS order_count, SUM(amount) AS total_amount
FROM orders
WHERE dt >= '2026-01-01' AND dt < '2026-02-01'
GROUP BY dt
ORDER BY dt;
```

## 最佳实践与踩坑记录

### 最佳实践

1. **分区表按日期分区**。查询按日期过滤，性能提升明显。

2. **分区字段不重复**。分区字段不必再出现在表字段里。

3. **Hive 适合离线分析**。实时查询用其他方案（Doris、ClickHouse）。

4. **ORC/Parquet 列式存储**。分析场景用列式存储，压缩率高、查询快。

### 踩坑记录

**坑 1：不分区导致全表扫描**

```sql
SELECT * FROM orders WHERE dt = '2026-01-01';
-- 表没分区，全表扫描，慢
```

大表必须分区，查询带分区过滤。

**坑 2：分区字段和表字段重名**

```sql
CREATE TABLE orders (dt STRING) PARTITIONED BY (dt STRING);
-- 报错：分区字段不能和表字段重名
```

分区字段单独定义，不重复。

**坑 3：小文件过多**

```text
频繁导入小文件，HDFS 小文件多，NameNode 压力大
```

合并小文件，或定时合并。

**坑 4：把 Hive 当 MySQL 用**

```text
用 Hive 做实时查询、频繁更新，性能差
```

Hive 是离线分析工具，实时用 OLAP 引擎。

**坑 5：动态分区全开导致分区爆炸**

```text
动态分区不限制，生成海量小分区
```

限制动态分区数量（hive.exec.max.dynamic.partitions）。

**坑 6：数据类型不匹配**

```text
Hive 的 STRING 和 MySQL 的 VARCHAR 不同，隐式转换可能出错
```

注意 Hive 类型和源数据类型的匹配。
