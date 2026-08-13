---
title: Elasticsearch 基础
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [elasticsearch, index, document, field, mapping, shard, replica]
---

# Elasticsearch 基础

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [与 MySQL 概念对照](#与-mysql-概念对照)
- [Index 索引](#index-索引)
- [Document 文档](#document-文档)
- [Field 字段](#field-字段)
- [Mapping 映射](#mapping-映射)
- [Shard 分片与 Replica 副本](#shard-分片与-replica-副本)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Elasticsearch（简称 ES）是基于 Lucene 的分布式搜索和分析引擎，用于全文搜索、日志分析、实时统计。

```text
Elasticsearch 的核心能力：
1. 全文搜索 —— 海量文本的快速检索（倒排索引）
2. 实时分析 —— 聚合统计（Aggregation）
3. 分布式 —— 分片 + 副本，水平扩展
4. 高可用 —— 集群、副本、自动故障转移
```

```text
典型应用：
1. 站内搜索 —— 商品搜索、文章搜索
2. 日志分析 —— ELK（Elasticsearch + Logstash + Kibana）
3. 实时监控 —— 指标分析、告警
4. 全文检索 —— 文档、新闻、知识库
```

## 与 MySQL 概念对照

ES 的概念和 MySQL 可以一一对应，便于理解：

| MySQL | Elasticsearch | 说明 |
|-------|--------------|------|
| Database | Index | 索引（数据库） |
| Table | Type（已废弃） | ES 7+ 移除 type |
| Row | Document | 文档（一行记录） |
| Column | Field | 字段（一列） |
| Schema | Mapping | 映射（表结构） |
| SQL | Query DSL | 查询语法 |
| SELECT | GET /index/_search | 查询 |
| INSERT | POST /index/_doc | 写入 |
| 主从 | Shard + Replica | 分片 + 副本 |

```text
核心区别：
MySQL：面向结构化数据，精确查询（=、LIKE）
ES：面向全文检索，分词匹配（倒排索引）
```

## Index 索引

Index 是文档的集合，类似数据库的表，是 ES 最大的逻辑单元。

### 索引的特点

```text
1. 索引名必须小写，不能以下划线开头
2. 一个索引包含多个 Document
3. 索引由多个 Shard（分片）组成
4. 索引的字段结构由 Mapping 定义
```

### 索引操作

```bash
# 创建索引
PUT /products
{
  "settings": {
    "number_of_shards": 3,      # 主分片数
    "number_of_replicas": 1     # 副本数
  }
}

# 删除索引
DELETE /products

# 查看索引
GET /products

# 查看所有索引
GET /_cat/indices?v
```

## Document 文档

Document 是 ES 的最小数据单元，一个 JSON 对象，类似数据库的一行记录。

### 文档操作

```bash
# 添加文档（指定 ID）
PUT /products/_doc/1
{
  "name": "iPhone 15",
  "price": 6999,
  "category": "手机",
  "description": "苹果最新旗舰手机"
}

# 添加文档（自动生成 ID）
POST /products/_doc
{
  "name": "华为 Mate 60",
  "price": 5999
}

# 查询文档
GET /products/_doc/1

# 更新文档（部分更新）
POST /products/_update/1
{
  "doc": {
    "price": 6499
  }
}

# 删除文档
DELETE /products/_doc/1
```

### 文档的元数据

```text
_index —— 文档所属索引
_id    —— 文档唯一 ID
_version —— 版本号（乐观锁，每次更新 +1）
_score —— 相关性得分（搜索时）
_source —— 原始 JSON 文档
```

## Field 字段

Field 是文档中的字段，类似数据库的列，有不同的数据类型。

### 核心数据类型

| 类型 | 说明 | 示例 |
|------|------|------|
| text | 文本（分词，全文搜索） | 描述、标题 |
| keyword | 关键词（不分词，精确匹配） | 状态、标签、ID |
| long/integer | 整数 | 数量 |
| float/double | 浮点数 | 价格 |
| date | 日期 | 时间 |
| boolean | 布尔 | 是否 |
| object | 对象（嵌套） | JSON 对象 |
| nested | 嵌套数组 | 对象数组 |
| geo_point | 地理位置 | 经纬度 |

### text vs keyword（核心区别）

```text
text：会分词，用于全文搜索
- 存储时：分词、小写化、去停用词
- "iPhone 15 Pro" → [iphone, 15, pro]
- 适合：搜索、模糊匹配

keyword：不分词，完整字符串存储
- 精确匹配、排序、聚合
- "iPhone 15 Pro" → "iPhone 15 Pro"（整体）
- 适合：状态、枚举、ID、精确匹配
```

```text
常见做法：一个字段同时建 text 和 keyword 两种类型
name: { type: "text", fields: { keyword: { type: "keyword" } } }
name 用于搜索，name.keyword 用于精确匹配和排序
```

## Mapping 映射

Mapping 定义索引的字段结构，类似数据库的表结构（Schema）。

### Mapping 的类型

```text
1. 动态映射（Dynamic Mapping）—— ES 自动推断字段类型
2. 显式映射（Explicit Mapping）—— 手动指定字段类型
```

### 动态映射

```bash
# 不指定 mapping，直接写文档，ES 自动推断类型
POST /products/_doc/1
{
  "name": "iPhone 15",      # 推断为 text + keyword
  "price": 6999,            # 推断为 long
  "in_stock": true,         # 推断为 boolean
  "created_at": "2026-01-01" # 推断为 date
}
```

### 显式映射

```bash
PUT /products
{
  "mappings": {
    "properties": {
      "name": {
        "type": "text",                    # 全文搜索
        "analyzer": "ik_max_word",         # 中文分词
        "fields": {
          "keyword": { "type": "keyword" }  # 精确匹配用
        }
      },
      "price": { "type": "double" },
      "category": { "type": "keyword" },    # 精确匹配
      "status": { "type": "keyword" },
      "created_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss"
      },
      "tags": { "type": "keyword" }         # 数组
    }
  }
}
```

### 常用 Mapping 参数

```text
type     —— 字段类型（text/keyword/long 等）
analyzer —— 分词器（ik_max_word 等）
fields   —— 子字段（一个字段多种类型）
index    —— 是否建索引（false 则不可搜索，可节省空间）
format   —— 日期格式
doc_values —— 是否启用排序聚合（默认 true）
```

### Mapping 的限制

```text
1. 字段类型创建后不能修改（只能新增字段）
2. 修改已有字段类型需要 reindex（重建索引）
3. 动态映射可能推断错类型（如字符串被推断为 date）
```

## Shard 分片与 Replica 副本

分片和副本是 ES 分布式和水平扩展的基础。

### 分片 Shard

```text
主分片（Primary Shard）：
1. 索引的数据分成多个分片存储
2. 分片分布在不同节点，实现水平扩展
3. 每个分片是独立的 Lucene 索引
```

```text
Index "products"
├── Primary Shard 0（节点 1）
├── Primary Shard 1（节点 2）
└── Primary Shard 2（节点 3）
```

### 副本 Replica

```text
副本分片（Replica Shard）：
1. 主分片的副本，提供冗余
2. 副本分布在不同节点，保证高可用
3. 副本可处理读请求，提升读性能
```

```text
分片 + 副本：
Primary Shard 0（节点1）→ Replica 0（节点2）
Primary Shard 1（节点2）→ Replica 1（节点3）
Primary Shard 2（节点3）→ Replica 1（节点1）
```

### 分片和副本的作用

```text
分片（Shard）：
1. 水平扩展 —— 数据分散到多节点
2. 提升写入性能 —— 多分片并行写

副本（Replica）：
1. 高可用 —— 主分片故障，副本提升为主
2. 提升读性能 —— 副本分担读请求
```

### 分片数设计

```text
主分片数（number_of_shards）：
1. 创建索引时设置，创建后不能修改
2. 过多：小索引分片浪费资源
3. 过少：无法充分利用集群

经验值：
- 单分片 10-50GB
- 分片数 ≈ 数据总量 / 单分片大小
```

```text
副本数（number_of_replicas）：
1. 可以动态修改（PUT /index/_settings）
2. 至少 1（高可用），生产环境一般 1-2
3. 副本越多，读性能越好，但存储翻倍
```

## 应用场景实战

### 场景 1：商品搜索索引设计

```bash
# 创建商品索引
PUT /products
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "ik_max_word",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "description": {
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "price": { "type": "double" },
      "category": { "type": "keyword" },
      "brand": { "type": "keyword" },
      "status": { "type": "keyword" },
      "created_at": { "type": "date" }
    }
  }
}
```

### 场景 2：批量写入文档

```bash
# Bulk API 批量写入
POST /products/_bulk
{ "index": { "_id": "1" } }
{ "name": "iPhone 15", "price": 6999, "category": "手机" }
{ "index": { "_id": "2" } }
{ "name": "华为 Mate 60", "price": 5999, "category": "手机" }
{ "index": { "_id": "3" } }
{ "name": "小米 14", "price": 3999, "category": "手机" }
```

## 最佳实践与踩坑记录

### 最佳实践

1. **字段类型规划好**。text 用于搜索，keyword 用于精确匹配/排序/聚合，避免后期 reindex。

2. **字符串字段建 text + keyword 双类型**。既支持全文搜索，又支持精确匹配。

3. **分片数合理**。单分片 10-50GB，分片数匹配数据量，避免小索引过多分片。

4. **副本至少 1**。生产环境副本数 1-2，保证高可用。

5. **批量写入用 Bulk API**。比单条写入快几十倍。

### 踩坑记录

**坑 1：动态映射推断错类型**

```text
写入 "2026-01-01" 这样的字符串，被动态映射为 date 类型，
后续写入非日期字符串会报错
```

对日期、ID 等易误判的字段，用显式映射明确指定类型。

**坑 2：字段类型不能修改**

```text
字段创建为 keyword 后，想改成 text，直接修改报错
需要 reindex（重建索引）迁移数据
```

字段类型规划要谨慎，改了要 reindex。

**坑 3：text 字段用 term 查询查不到**

```json
// 错误：text 字段（已分词）用 term 查询整词
{ "term": { "name": "iPhone 15 Pro" } }
// name 是 text 类型，存储时已分词为 [iphone, 15, pro]，整词查不到
```

text 字段用 match 查询，keyword 字段（name.keyword）用 term 查询。

**坑 4：分片数过多**

```text
小索引设置了 10 个分片，每个分片很小，
分片管理开销大，性能反而下降
```

分片数匹配数据量（单分片 10-50GB），不要盲目多分片。

**坑 5：副本数设置过高**

```text
副本数设置 5，存储膨胀 6 倍（1 主 + 5 副本），
且副本同步开销大
```

副本数 1-2 即可，副本过多浪费存储。

**坑 6：忽略 Mapping 的 index 参数**

```text
不需要搜索的字段（如图片二进制）也建了索引，
浪费存储和内存
```

不需要搜索的字段设置 "index": false，节省资源。
