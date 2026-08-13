---
title: Elasticsearch 查询
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [elasticsearch, match, term, bool, range, prefix, wildcard, query-string, aggregation]
---

# Elasticsearch 查询

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Match 全文匹配](#match-全文匹配)
- [Term 精确匹配](#term-精确匹配)
- [Bool 组合查询](#bool-组合查询)
- [Range 范围查询](#range-范围查询)
- [Prefix 前缀查询](#prefix-前缀查询)
- [Wildcard 通配符查询](#wildcard-通配符查询)
- [Query String 查询](#query-string-查询)
- [Aggregation 聚合](#aggregation-聚合)
- [查询选型总结](#查询选型总结)
- [应用场景实战](#应用场景实战)

## 概述

ES 使用 Query DSL（基于 JSON 的查询语言）进行查询，核心分为查询（Query）和聚合（Aggregation）两大类。

```text
查询类型：
1. 全文查询（Full-text）—— Match、Match Phrase、Query String（分词后匹配）
2. 词项查询（Term-level）—— Term、Range、Prefix、Wildcard（精确匹配，不分词）
3. 组合查询（Compound）—— Bool（多条件组合）
```

```bash
# 基本查询结构
GET /products/_search
{
  "query": { ... },       # 查询条件
  "from": 0,              # 分页起始
  "size": 10,             # 每页条数
  "sort": [ ... ],        # 排序
  "aggs": { ... }         # 聚合
}
```

## Match 全文匹配

Match 是全文查询，会先分词再匹配，是 ES 最常用的查询。

### 基本用法

```json
// 搜索名称包含"苹果手机"的文档（分词后匹配）
GET /products/_search
{
  "query": {
    "match": {
      "name": "苹果手机"
    }
  }
}
```

### match 的匹配逻辑

```text
match 查询对搜索词分词，分词结果之间是 OR 关系：
"苹果手机" → [苹果, 手机] → 匹配包含"苹果"或"手机"的文档
```

### match 的变体

```json
// 1. match_phrase：短语匹配（分词后按顺序连续匹配）
{
  "query": {
    "match_phrase": {
      "name": "苹果手机"     // 必须是"苹果手机"连续出现
    }
  }
}

// 2. match + operator：AND 关系（所有词都匹配）
{
  "query": {
    "match": {
      "name": {
        "query": "苹果手机",
        "operator": "and"      // 包含"苹果"且"手机"
      }
    }
  }
}

// 3. multi_match：多字段匹配
{
  "query": {
    "multi_match": {
      "query": "苹果手机",
      "fields": ["name", "description"]   // 多个字段搜索
    }
  }
}
```

## Term 精确匹配

Term 是词项查询，不分词，精确匹配，用于 keyword 字段。

### 基本用法

```json
// 精确匹配 category 为"手机"（不分词）
GET /products/_search
{
  "query": {
    "term": {
      "category": "手机"
    }
  }
}
```

### Term vs Match（核心区别）

| 维度 | Term | Match |
|------|------|-------|
| 是否分词 | 不分词 | 分词 |
| 适用字段 | keyword | text |
| 匹配方式 | 精确匹配 | 模糊匹配 |
| 典型场景 | 状态、ID、枚举 | 搜索、描述 |

```text
关键理解：
term 查询"手机"，只匹配 keyword 值完全等于"手机"的文档
match 查询"手机"，分词后匹配 text 中包含"手机"的文档
```

### Terms 多值匹配

```json
// 匹配 category 为"手机"或"电脑"
{
  "query": {
    "terms": {
      "category": ["手机", "电脑"]
    }
  }
}
```

## Bool 组合查询

Bool 是组合查询，用 must/should/must_not/filter 组合多个条件。

### Bool 的四个子句

```text
must       —— 必须满足（AND，参与评分）
should     —— 应该满足（OR，满足越多分越高）
must_not   —— 必须不满足（NOT，不参与评分）
filter     —— 必须满足（不参与评分，性能好，可缓存）
```

### 基本用法

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "手机" } }        // 必须包含"手机"
      ],
      "filter": [
        { "term": { "status": "on_sale" } },   // 必须是上架状态
        { "range": { "price": { "gte": 1000, "lte": 8000 } } }  // 价格 1000-8000
      ],
      "must_not": [
        { "term": { "brand": "山寨" } }         // 排除山寨
      ],
      "should": [
        { "term": { "category": "旗舰" } },     // 旗舰加分
        { "term": { "category": "热销" } }      // 热销加分
      ]
    }
  }
}
```

### filter vs must（核心区别）

```text
filter：不评分，结果可缓存，性能好
must：评分（影响 _score），结果不缓存

使用原则：
精确匹配、范围过滤用 filter（不关心相关性）
全文搜索用 must（关心相关性）
```

## Range 范围查询

Range 用于数值、日期范围查询。

### 基本用法

```json
{
  "query": {
    "range": {
      "price": {
        "gte": 1000,     // 大于等于
        "lte": 8000      // 小于等于
      }
    }
  }
}
```

### 范围操作符

```text
gt  —— 大于
gte —— 大于等于
lt  —— 小于
lte —— 小于等于
```

```json
// 日期范围
{
  "query": {
    "range": {
      "created_at": {
        "gte": "2026-01-01",
        "lte": "2026-12-31"
      }
    }
  }
}
```

## Prefix 前缀查询

Prefix 用于前缀匹配，适合 keyword 字段。

### 基本用法

```json
// 匹配 brand 以"华"开头的文档
{
  "query": {
    "prefix": {
      "brand": "华"
    }
  }
}
```

### 应用场景

```text
1. 搜索提示（autocomplete）—— 输入前缀提示
2. 前缀匹配 —— 手机号、邮编、编码
```

```text
注意：prefix 查询不分析文本（不分词），
对 text 字段用 prefix 可能查不到（已分词）
```

## Wildcard 通配符查询

Wildcard 用通配符匹配，类似 SQL 的 LIKE。

### 基本用法

```json
// 匹配 name 以"小米"开头的文档
{
  "query": {
    "wildcard": {
      "name.keyword": "小米*"
    }
  }
}
```

### 通配符

```text
* —— 匹配任意字符序列（0 个或多个）
? —— 匹配任意单个字符
```

```json
// ? 匹配单个字符
{ "wildcard": { "name.keyword": "iPhone ?" } }
```

### 注意事项

```text
1. 通配符查询性能差 —— 全表扫描（不利用倒排索引）
2. 避免以通配符开头 —— "小米*" 可以，"*手机" 极慢
3. 大量数据用 ngram 或 prefix 替代
```

## Query String 查询

Query String 用类似 Lucene 的查询语法，功能强大但复杂。

### 基本用法

```json
{
  "query": {
    "query_string": {
      "query": "(苹果 OR 华为) AND 手机 NOT 山寨",
      "fields": ["name", "description"]
    }
  }
}
```

### 查询语法

```text
AND / OR / NOT —— 逻辑运算
+ / -          —— 必须包含 / 排除
field:value    —— 指定字段
* 通配符        —— name:小米*
"" 短语         —— "苹果手机"（精确短语）
() 分组         —— 逻辑分组
```

```json
// 复杂查询字符串
{
  "query": {
    "query_string": {
      "query": "name:(苹果 OR 华为) AND price:[1000 TO 8000]"
    }
  }
}
```

### Query String 的优缺点

```text
优点：语法灵活，功能强大
缺点：语法复杂、易出错、性能差

适合：高级搜索、复杂表达式
不适合：常规搜索（用 match/bool 更清晰）
```

## Aggregation 聚合

Aggregation 用于统计分析，类似 SQL 的 GROUP BY。

### 聚合类型

```text
1. 指标聚合（Metric）—— 统计值（avg/sum/max/min/count）
2. 桶聚合（Bucket）—— 分组（terms/range/date_histogram）
3. 管道聚合（Pipeline）—— 对聚合结果再聚合
```

### 指标聚合

```json
{
  "size": 0,               // 不返回文档，只返回聚合结果
  "aggs": {
    "avg_price": { "avg": { "field": "price" } },      // 平均价格
    "max_price": { "max": { "field": "price" } },      // 最高价格
    "total_count": { "value_count": { "field": "price" } }  // 数量
  }
}
```

### 桶聚合（分组）

```json
// 按分类分组统计
{
  "size": 0,
  "aggs": {
    "group_by_category": {
      "terms": {
        "field": "category",
        "size": 10            // 前 10 个分类
      },
      "aggs": {
        "avg_price": { "avg": { "field": "price" } }   // 每组平均价格
      }
    }
  }
}
```

### 日期直方图聚合

```json
// 按天统计
{
  "size": 0,
  "aggs": {
    "sales_by_day": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "day"    // 按天分组
      }
    }
  }
}
```

### 嵌套聚合

```json
// 分类 → 品牌 → 平均价格（多层聚合）
{
  "size": 0,
  "aggs": {
    "by_category": {
      "terms": { "field": "category" },
      "aggs": {
        "by_brand": {
          "terms": { "field": "brand" },
          "aggs": {
            "avg_price": { "avg": { "field": "price" } }
          }
        }
      }
    }
  }
}
```

## 查询选型总结

| 查询 | 类型 | 是否分词 | 适用场景 |
|------|------|---------|---------|
| match | 全文 | 分词 | 全文搜索 |
| match_phrase | 全文 | 分词 | 短语搜索 |
| term | 词项 | 不分词 | 精确匹配 |
| terms | 词项 | 不分词 | 多值匹配 |
| range | 词项 | 不分词 | 范围（数值/日期） |
| prefix | 词项 | 不分词 | 前缀匹配 |
| wildcard | 词项 | 不分词 | 通配符（LIKE） |
| bool | 组合 | - | 多条件组合 |
| query_string | 组合 | 分词 | 复杂表达式 |

```text
选型速记：
- 搜索关键词 → match
- 精确匹配（状态/ID）→ term（filter）
- 多条件组合 → bool
- 数值/日期范围 → range（filter）
- 分组统计 → aggregation
```

## 应用场景实战

### 场景 1：商品搜索（综合条件）

```json
// 搜索：名称含"手机"，价格 1000-8000，上架状态，排除山寨，按价格排序
GET /products/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "手机" } }
      ],
      "filter": [
        { "term": { "status": "on_sale" } },
        { "range": { "price": { "gte": 1000, "lte": 8000 } } }
      ],
      "must_not": [
        { "term": { "brand": "山寨" } }
      ]
    }
  },
  "sort": [
    { "price": "asc" },
    { "_score": "desc" }
  ],
  "from": 0,
  "size": 20
}
```

### 场景 2：分类统计（聚合）

```json
// 统计各分类的商品数量和平均价格
GET /products/_search
{
  "size": 0,
  "aggs": {
    "by_category": {
      "terms": { "field": "category", "size": 10 },
      "aggs": {
        "count": { "value_count": { "field": "price" } },
        "avg_price": { "avg": { "field": "price" } }
      }
    }
  }
}
```

### 场景 3：搜索提示（Prefix）

```json
// 输入"苹"，提示以"苹"开头的商品
GET /products/_search
{
  "query": {
    "prefix": {
      "name.keyword": "苹"
    }
  },
  "size": 10
}
```

### 场景 4：日期范围统计

```json
// 统计最近 30 天每天的订单量
GET /orders/_search
{
  "size": 0,
  "query": {
    "range": {
      "created_at": { "gte": "now-30d/d" }
    }
  },
  "aggs": {
    "orders_by_day": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "day"
      }
    }
  }
}
```
