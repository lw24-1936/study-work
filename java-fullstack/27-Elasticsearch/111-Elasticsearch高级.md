---
title: Elasticsearch 高级
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [elasticsearch, 分片, 副本, 集群, 倒排索引, analyzer, 分词器, 中文分词, 性能优化]
---

# Elasticsearch 高级

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [倒排索引](#倒排索引)
- [Analyzer 分析器](#analyzer-分析器)
- [分词器](#分词器)
- [中文分词](#中文分词)
- [分片、副本与集群](#分片副本与集群)
- [性能优化](#性能优化)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

本篇深入 Elasticsearch 的核心原理（倒排索引、分析器、分词）和工程实践（集群、性能优化），是掌握 ES 的关键。

```text
核心原理：
1. 倒排索引 —— ES 快速搜索的根本原因
2. Analyzer —— 文本如何被拆分成词
3. 分词器 —— 中文分词（IK）
4. 集群 —— 分片、副本、节点

工程实践：
5. 性能优化 —— 查询、写入、内存
```

## 倒排索引

倒排索引（Inverted Index）是 ES 实现快速全文搜索的核心，理解它才能理解 ES。

### 正排索引 vs 倒排索引

```text
正排索引（文档 → 词）：
文档 1 → "苹果手机很好用"
文档 2 → "苹果很好吃"
文档 3 → "华为手机也不错"

倒排索引（词 → 文档）：
苹果  → [文档 1, 文档 2]
手机  → [文档 1, 文档 3]
好    → [文档 1, 文档 3]
吃    → [文档 2]
华为  → [文档 3]
```

### 倒排索引的构建过程

```text
1. 分词 —— 文档内容拆分成词（term）
   "苹果手机很好用" → [苹果, 手机, 很, 好用]

2. 规范化 —— 小写、去停用词
   [苹果, 手机, 好用]

3. 建立词典 —— 每个词对应一个文档列表（posting list）
   苹果 → [文档1, 文档2]
   手机 → [文档1, 文档3]
```

### 倒排索引的结构

```text
Term Dictionary（词典）→ Posting List（倒排列表）

苹果 → [1, 2]（文档 1、2 包含"苹果"）
手机 → [1, 3]
好用 → [1]
```

```text
为什么快：
搜索"苹果"，直接从词典找到"苹果"，返回其倒排列表 [1, 2]，
不需要遍历所有文档（O(1) 查找，而非 O(n) 扫描）
```

### 倒排索引的组成

```text
1. 词典（Term Dictionary）—— 所有词的集合（排序存储，二分/前缀树查找）
2. 倒排列表（Posting List）—— 每个词对应的文档 ID 列表
3. 位置信息（Position）—— 词在文档中的位置（短语查询用）
4. 词频（TF）—— 词在文档中出现的次数（相关性评分用）
```

## Analyzer 分析器

Analyzer 负责将文本拆分成词（term），是文本索引和搜索的前提。

### Analyzer 的组成

```text
Analyzer = Character Filter + Tokenizer + Token Filter

1. Character Filter（字符过滤器）—— 预处理字符（去除 HTML、转换字符）
2. Tokenizer（分词器）—— 将文本拆分成词
3. Token Filter（词过滤器）—— 处理词（小写、去停用词、词干）
```

```text
流程：
原始文本 → Character Filter → Tokenizer → Token Filter → 词（term）
"Apple Phones!" → 去除 ! → [Apple, Phones] → 小写 → [apple, phones]
```

### 内置 Analyzer

| Analyzer | 说明 | 示例 |
|----------|------|------|
| standard | 标准（默认） | "iPhone 15" → [iphone, 15] |
| simple | 简单（按非字母切分） | "iPhone-15" → [iphone] |
| whitespace | 按空格切分 | "iPhone 15" → [iPhone, 15] |
| keyword | 不分词（整体） | "iPhone 15" → [iPhone 15] |
| ik_max_word | 中文最细粒度 | "苹果手机" → [苹果, 手机, 苹果手机] |
| ik_smart | 中文粗粒度 | "苹果手机" → [苹果手机] |

### 测试 Analyzer

```bash
# 测试分词效果
POST /_analyze
{
  "analyzer": "standard",
  "text": "iPhone 15 Pro Max"
}

# 测试中文分词
POST /_analyze
{
  "analyzer": "ik_max_word",
  "text": "中华人民共和国"
}
```

## 分词器

分词器（Tokenizer）是 Analyzer 的核心，负责拆分文本。

### 分词器类型

```text
1. 标准分词器（standard）—— 按单词边界切分（英文）
2. 空格分词器（whitespace）—— 按空格切分
3. 字母分词器（letter）—— 按非字母切分
4. 关键词分词器（keyword）—— 不分词
5. 中文分词器 —— IK、jieba、HanLP
```

### 英文分词 vs 中文分词

```text
英文分词：天然有空格分隔，按空格/标点切分即可
"Hello world" → [hello, world]

中文分词：无空格分隔，需要专门的分词算法
"中华人民共和国" → [中华人民共和国] 或 [中华, 人民, 共和国]
```

```text
中文分词的难点：
1. 无分隔符 —— 词与词之间没有空格
2. 歧义 —— "研究生命起源"（研究/研究生）
3. 新词 —— 网络新词、专有名词
```

## 中文分词

中文分词是中文搜索的关键，最常用的是 IK 分词器。

### IK 分词器

```text
IK 分词器（ik-analyzer）是 ES 最流行的中文分词插件。

两种模式：
1. ik_max_word —— 最细粒度切分（索引用，召回率高）
2. ik_smart —— 最粗粒度切分（搜索用，精确）
```

### 安装 IK

```bash
# 安装 IK 分词器（版本和 ES 一致）
./bin/elasticsearch-plugin install https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.0.0/elasticsearch-analysis-ik-8.0.0.zip
```

### 两种模式对比

```bash
# ik_max_word（细粒度）
POST /_analyze
{ "analyzer": "ik_max_word", "text": "中华人民共和国国歌" }
# 结果：中华人民共和国 / 中华人民 / 中华 / 华人 / 人民共和国 / 人民 / 共和国 / 共和 / 国歌

# ik_smart（粗粒度）
POST /_analyze
{ "analyzer": "ik_smart", "text": "中华人民共和国国歌" }
# 结果：中华人民共和国 / 国歌
```

### 自定义词典

```text
IK 支持自定义词典，添加新词（品牌名、网络词）：

config/analysis-ik/main.dic —— 主词典
config/analysis-ik/custom.dic —— 自定义词典（添加新词）
```

```text
# custom.dic 添加自定义词
华为
鸿蒙
遥遥领先
```

### 自定义词典的应用

```text
场景：品牌名"遥遥领先"默认被拆成"遥遥"+"领先"，
搜索"遥遥领先"匹配不到，添加到自定义词典后整体作为一个词
```

## 分片、副本与集群

分片、副本、集群是 ES 分布式的基础（基础概念见 109，这里聚焦集群）。

### 集群架构

```text
ES 集群由多个节点（Node）组成：

1. Master 节点 —— 管理集群（创建/删除索引、分片分配）
2. Data 节点 —— 存储数据、处理读写
3. Coordinating 节点 —— 转发请求（默认所有节点都是）
4. Ingest 节点 —— 数据预处理
```

```text
集群示例（3 节点）：
Node 1（Master + Data）—— Primary Shard 0, Replica 1
Node 2（Data）—— Primary Shard 1, Replica 0
Node 3（Data）—— Primary Shard 2, Replica 2
```

### 集群的健康状态

```bash
GET /_cluster/health
```

```text
green  —— 所有主分片和副本都正常分配
yellow —— 主分片正常，部分副本未分配（副本缺失）
red    —— 部分主分片未分配（数据不完整）
```

### 分片分配

```text
1. 主分片和副本分片分配在不同节点（保证高可用）
2. 节点故障，副本分片提升为主分片
3. 新节点加入，分片自动重新平衡
```

### 集群配置

```yaml
# elasticsearch.yml
cluster.name: my-cluster           # 集群名（同一集群的节点一致）
node.name: node-1                  # 节点名
node.master: true                  # 是否可成为 Master
node.data: true                    # 是否存储数据
network.host: 0.0.0.0
discovery.seed_hosts: ["node-1", "node-2", "node-3"]  # 集群节点
```

## 性能优化

ES 性能优化从查询、写入、内存三个维度。

### 查询优化

```text
1. filter 替代 must —— filter 不评分、可缓存，性能更好
2. 避免深度分页 —— from+size 超过 10000 用 scroll 或 search_after
3. 减少返回字段 —— _source 过滤，只返回需要的字段
4. 使用 keyword 字段 —— 精确匹配、排序、聚合用 keyword
5. 避免 wildcard 前缀通配 —— "*手机" 全表扫描
```

```json
// 优化：filter 替代 must + 只返回需要的字段
{
  "_source": ["name", "price"],       // 只返回这两个字段
  "query": {
    "bool": {
      "filter": [
        { "term": { "status": "on_sale" } },
        { "range": { "price": { "gte": 1000 } } }
      ]
    }
  }
}
```

### 写入优化

```text
1. 批量写入 —— Bulk API（比单条快几十倍）
2. 增加刷新间隔 —— refresh_interval 调大（如 30s）
3. 副本数设为 0 —— 大批量导入时先关副本，导入后再开
4. 使用自动生成 ID —— 指定 ID 需要检查存在，性能略低
```

```json
// 批量导入时优化设置
PUT /products/_settings
{
  "refresh_interval": "30s",        // 刷新间隔调大
  "number_of_replicas": 0            // 先关副本
}
// 导入完成后恢复
PUT /products/_settings
{
  "refresh_interval": "1s",
  "number_of_replicas": 1
}
```

### 内存优化

```text
1. JVM 堆内存 —— 不超过物理内存的 50%，且不超过 32GB（指针压缩）
2. 其余内存给 Lucene —— 操作系统文件缓存
3. 禁用 swap —— 避免内存交换到磁盘（性能骤降）
```

```yaml
# jvm.options
-Xms16g
-Xmx16g    # 堆内存不超过 32GB
```

### 常见性能问题

| 问题 | 原因 | 优化 |
|------|------|------|
| 查询慢 | 深度分页 | scroll/search_after |
| 查询慢 | 全表扫描 | 避免 wildcard 前缀通配 |
| 写入慢 | 频繁刷新 | 调大 refresh_interval |
| 内存不足 | 堆内存过大 | 堆内存 ≤ 32GB |
| 集群红 | 分片丢失 | 检查节点、副本 |

## 最佳实践与踩坑记录

### 最佳实践

1. **索引用 ik_max_word，搜索用 ik_smart**。索引细粒度（召回率高），搜索粗粒度（精确）。

2. **精确匹配、排序、聚合用 keyword**。text 字段用于全文搜索，keyword 用于精确操作。

3. **filter 替代 must**。不关心相关性评分的条件用 filter（可缓存、性能好）。

4. **避免深度分页**。from+size 深分页性能差，用 scroll 或 search_after。

5. **堆内存合理配置**。堆内存 ≤ 50% 物理内存且 ≤ 32GB，其余给文件缓存。

### 踩坑记录

**坑 1：中文不分词导致搜索不到**

```text
没装 IK 分词器，用 standard 分词中文：
"苹果手机" 被切成单个汉字 [苹, 果, 手, 机]，
搜索"手机"匹配不到（因为"手机"不是独立的词）
```

中文搜索必须装 IK 分词器（或 jieba、HanLP）。

**坑 2：text 字段排序报错**

```json
// text 字段排序报错：Fielddata is disabled on text fields
{
  "sort": [{ "name": "asc" }]   // name 是 text 类型
}
```

text 字段不能排序，用 name.keyword 排序。

**坑 3：深度分页性能问题**

```json
{
  "from": 100000,    // 深度分页，性能极差
  "size": 10
}
```

from+size 深度分页会遍历所有前面的文档，用 scroll 或 search_after。

**坑 4：wildcard 前缀通配查询**

```json
{ "wildcard": { "name": "*手机" } }   // 以通配符开头，全表扫描
```

避免以通配符开头，用 ngram 或专门的搜索建议方案。

**坑 5：堆内存过大**

```text
堆内存设置 64GB，超过 32GB 指针压缩失效，
内存利用率下降，反而性能差
```

堆内存不超过 32GB（指针压缩上限）。

**坑 6：副本数为 0**

```text
生产环境副本数为 0，节点故障数据丢失，集群变红
```

生产环境副本数至少 1，关键索引 2。
