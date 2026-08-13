---
title: Spring Data Elasticsearch
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-data-elasticsearch, index, document, mapping, query, aggregation, search, elasticsearch]
---

# Spring Data Elasticsearch

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [依赖与配置](#依赖与配置)
- [@Document 与 @Field 映射](#document-与-field-映射)
- [索引操作](#索引操作)
- [ElasticsearchRepository](#elasticsearchrepository)
- [ElasticsearchOperations 查询](#elasticsearchoperations-查询)
- [全文搜索](#全文搜索)
- [Aggregation 聚合](#aggregation-聚合)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Data Elasticsearch 是 Spring 对 Elasticsearch 的集成。Elasticsearch 是分布式搜索引擎，基于 Lucene，提供全文搜索和分析能力。

```text
Elasticsearch 核心概念（与关系数据库对照）：
ES Index（索引）        ≈ MySQL Table（表）
ES Document（文档）     ≈ MySQL Row（行）
ES Field（字段）        ≈ MySQL Column（列）
ES Mapping（映射）      ≈ MySQL Schema（表结构）
ES Shard（分片）        ≈ MySQL 分表
ES Replica（副本）      ≈ MySQL 主从备份
```

```text
核心组件：
ElasticsearchRepository   —— Repository 抽象
ElasticsearchOperations   —— 底层操作模板（原 ElasticsearchTemplate）
IndexOperations           —— 索引管理（创建、删除、映射）
```

## 依赖与配置

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```

### 版本对应关系

```text
Spring Boot 3.x  → Spring Data Elasticsearch 5.x → Elasticsearch 8.x
Spring Boot 2.7  → Spring Data Elasticsearch 4.4 → Elasticsearch 7.17
```

版本必须匹配，否则客户端连接失败。

### 连接配置

```yaml
spring:
  elasticsearch:
    uris: http://localhost:9200
    username: elastic
    password: ${ES_PASSWORD}
    connection-timeout: 3s
    socket-timeout: 60s
```

```java
// 编程式配置（多集群等场景）
@Configuration
public class EsConfig {

    @Bean
    public ClientConfiguration clientConfiguration() {
        return ClientConfiguration.builder()
            .connectedTo("localhost:9200")
            .withBasicAuth("elastic", "secret")
            .build();
    }

    @Bean
    public ElasticsearchClient elasticsearchClient() {
        return ElasticsearchClients.create(clientConfiguration());
    }
}
```

## @Document 与 @Field 映射

### @Document 注解

```java
@Document(indexName = "products")   // 索引名
public class Product {

    @Id                              // 文档 _id
    private String id;

    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String name;             // 分词字段，用于全文搜索

    @Field(type = FieldType.Keyword)
    private String category;         // 不分词，精确匹配

    @Field(type = FieldType.Double)
    private BigDecimal price;

    @Field(type = FieldType.Integer)
    private Integer stock;

    @Field(type = FieldType.Date, format = DateFormat.date_hour_minute_second)
    private LocalDateTime createdAt;

    @Field(type = FieldType.Boolean)
    private Boolean onSale;
}
```

### FieldType 类型

| FieldType | 说明 | 用途 |
|-----------|------|------|
| Text | 分词文本 | 全文搜索（商品名、文章内容） |
| Keyword | 不分词 | 精确匹配（分类、状态、标签） |
| Long/Integer/Double | 数值 | 价格、数量 |
| Date | 日期 | 时间字段 |
| Boolean | 布尔 | 开关字段 |
| Object | 嵌套对象 | 嵌套结构 |
| Nested | 嵌套数组 | 数组内独立索引 |

### Text vs Keyword

```text
Text 字段：
- 会分词（如 "小米手机" → 小米/手机）
- 用于全文搜索（match 查询）
- 不适合排序和精确匹配

Keyword 字段：
- 不分词，整体作为值
- 用于精确匹配（term 查询）
- 适合排序、聚合、过滤

经典用法：一个字段双类型
name → text（搜索用）+ name.keyword（排序/聚合用）
```

### 映射配置

```java
@Field(type = FieldType.Text,
       analyzer = "ik_max_word",        // 索引时分词器
       searchAnalyzer = "ik_smart")     // 搜索时分词器
private String description;

@Field(type = FieldType.Keyword, index = false)  // 不建索引（不参与搜索）
private String rawContent;
```

## 索引操作

### 创建/删除索引

```java
@Autowired
private ElasticsearchOperations operations;

// 创建索引（根据 @Document 的映射自动创建）
IndexOperations indexOps = operations.indexOps(Product.class);
indexOps.create();                    // 创建索引
indexOps.createWithMapping();         // 创建索引 + 映射

// 判断索引是否存在
boolean exists = indexOps.exists();

// 删除索引
indexOps.delete();
```

### 自动创建索引

```yaml
spring:
  data:
    elasticsearch:
      repositories:
        enabled: true
```

```java
@Document(indexName = "products", createIndex = true)  // 启动时自动创建
public class Product { ... }
```

### 批量导入

```java
@Autowired
private ElasticsearchOperations operations;

public void bulkImport(List<Product> products) {
    operations.save(products);  // 批量保存
}
```

## ElasticsearchRepository

### 定义 Repository

```java
public interface ProductRepository extends ElasticsearchRepository<Product, String> {

    // 方法名派生查询
    List<Product> findByName(String name);
    List<Product> findByCategory(String category);
    List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);

    // @Query 注解（ES 查询 DSL）
    @Query("{\"match\": {\"name\": \"?0\"}}")
    List<Product> searchByName(String keyword);

    // 分页
    Page<Product> findByCategory(String category, Pageable pageable);
}
```

### 基础 CRUD

```java
@Service
public class ProductService {

    @Autowired
    private ProductRepository productRepository;

    public Product save(Product product) {
        return productRepository.save(product);
    }

    public Product findById(String id) {
        return productRepository.findById(id).orElse(null);
    }

    public void delete(String id) {
        productRepository.deleteById(id);
    }

    public Page<Product> search(String keyword, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return productRepository.searchByName(keyword, pageable);
    }
}
```

## ElasticsearchOperations 查询

ElasticsearchOperations 提供灵活的查询能力（基于 Query DSL）。

### 基础查询

```java
@Autowired
private ElasticsearchOperations operations;

// 按 ID 查询
Product product = operations.get("id1", Product.class);

// 查询所有
SearchHits<Product> hits = operations.search(Query.findAll(), Product.class);

// 条件查询
Criteria criteria = new Criteria("category").is("手机");
Query query = new CriteriaQuery(criteria);
SearchHits<Product> result = operations.search(query, Product.class);
```

### Criteria 条件构建

```java
// 精确匹配
Criteria.where("category").is("手机")

// 范围
Criteria.where("price").between(1000, 5000)
Criteria.where("price").greaterThan(1000)
Criteria.where("price").lessThan(5000)

// 多个条件 AND
Criteria criteria = new Criteria("category").is("手机")
    .and(new Criteria("price").between(1000, 5000));

// OR
Criteria criteria = new Criteria("category").is("手机")
    .or(new Criteria("category").is("电脑"));
```

### NativeQuery（原生 DSL）

```java
// 用原生 ES 查询 DSL
Query query = new NativeQueryBuilder()
    .withQuery(q -> q
        .bool(b -> b
            .must(m -> m.match(ma -> ma.field("name").query("小米手机")))
            .filter(f -> f.range(r -> r.field("price").gte(JsonData.of(1000)).lte(JsonData.of(5000))))
        )
    )
    .build();

SearchHits<Product> hits = operations.search(query, Product.class);
```

### 分页排序

```java
Query query = new CriteriaQuery(criteria);
query.setPageable(PageRequest.of(0, 20, Sort.by(Sort.Direction.DESC, "price")));

SearchHits<Product> hits = operations.search(query, Product.class);
```

### 处理查询结果

```java
SearchHits<Product> hits = operations.search(query, Product.class);

// 总数
long total = hits.getTotalHits();

// 遍历结果
for (SearchHit<Product> hit : hits) {
    Product product = hit.getContent();   // 文档内容
    float score = hit.getScore();         // 相关度评分
    String id = hit.getId();              // 文档 ID
}
```

## 全文搜索

全文搜索是 Elasticsearch 的核心能力，基于分词和倒排索引。

### match 查询（分词匹配）

```java
// match 查询：对查询词分词后匹配
@Query("{\"match\": {\"name\": \"?0\"}}")
List<Product> searchByName(String keyword);

// 多字段匹配
@Query("{\"multi_match\": {\"query\": \"?0\", \"fields\": [\"name\", \"description\"]}}")
List<Product> search(String keyword);
```

### 搜索类型对比

| 查询类型 | 说明 | 适用场景 |
|---------|------|---------|
| match | 分词匹配，相关度排序 | 全文搜索 |
| multi_match | 多字段匹配 | 综合搜索 |
| term | 精确匹配（不分词） | 精确过滤 |
| range | 范围查询 | 价格、时间范围 |
| bool | 组合查询 | 复杂条件 |
| fuzzy | 模糊查询 | 纠错搜索 |
| wildcard | 通配符 | 前缀匹配 |

### bool 查询

```java
// bool 查询：must/should/filter
@Query("{\"bool\": {" +
       "\"must\": [{\"match\": {\"name\": \"?0\"}}]," +        // 必须匹配（算分）
       "\"filter\": [{\"range\": {\"price\": {\"gte\": 1000}}}]" +  // 过滤（不算分）
       "}}")
List<Product> searchWithFilter(String keyword);
```

```text
bool 查询的子句：
must     —— 必须匹配，参与评分（AND）
should   —— 应该匹配，参与评分（OR）
filter   —— 必须匹配，不参与评分（高效过滤）
must_not —— 必须不匹配（NOT）
```

## Aggregation 聚合

Elasticsearch 聚合用于统计分析，类似 SQL 的 GROUP BY。

### 常见聚合

```java
// 按分类统计数量（term 聚合）
@Autowired
private ElasticsearchOperations operations;

NativeQuery query = NativeQuery.builder()
    .withAggregation("category_count", Aggregation.of(a -> a
        .terms(t -> t.field("category").size(10))))
    .build();

SearchHits<Product> hits = operations.search(query, Product.class);
```

### 用 Repository 的聚合

```java
// 定义聚合结果接收
public interface CategoryCount {
    String getKey();      // 分组键
    long getDocCount();   // 文档数量
}

// Repository 查询
public interface ProductRepository extends ElasticsearchRepository<Product, String> {

    @Query("{\"match_all\": {}}")
    SearchPage<Product> aggregate(Pageable pageable);
}
```

### 统计聚合

```java
// 平均值、最大值、最小值
Aggregation.of(a -> a
    .avg(av -> av.field("price")));   // 平均价格

Aggregation.of(a -> a
    .max(m -> m.field("price")));     // 最高价格

Aggregation.of(a -> a
    .min(m -> m.field("price")));     // 最低价格
```

## 应用场景实战

### 场景 1：商品全文搜索

```java
@Document(indexName = "products")
public class Product {
    @Id
    private String id;

    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String name;

    @Field(type = FieldType.Keyword)
    private String category;

    @Field(type = FieldType.Double)
    private BigDecimal price;

    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String description;
}

@Service
public class ProductSearchService {

    @Autowired
    private ElasticsearchOperations operations;

    public List<Product> search(String keyword, String category,
                                BigDecimal minPrice, BigDecimal maxPrice) {
        // 组合查询：关键词 + 分类过滤 + 价格范围
        Query query = new NativeQueryBuilder()
            .withQuery(q -> q.bool(b -> {
                b.must(m -> m.multiMatch(mm -> mm
                    .fields("name", "description")
                    .query(keyword)));
                if (category != null) {
                    b.filter(f -> f.term(t -> t.field("category").value(category)));
                }
                if (minPrice != null && maxPrice != null) {
                    b.filter(f -> f.range(r -> r.field("price")
                        .gte(JsonData.of(minPrice)).lte(JsonData.of(maxPrice))));
                }
                return b;
            }))
            .build();

        SearchHits<Product> hits = operations.search(query, Product.class);
        return hits.getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
}
```

### 场景 2：搜索 + 聚合（分类统计）

```java
@Service
public class SearchFacetService {

    @Autowired
    private ElasticsearchOperations operations;

    public SearchResult searchWithFacets(String keyword) {
        NativeQuery query = NativeQuery.builder()
            .withQuery(q -> q.match(m -> m.field("name").query(keyword)))
            .withAggregation("categories", Aggregation.of(a -> a
                .terms(t -> t.field("category").size(20))))
            .withAggregation("price_stats", Aggregation.of(a -> a
                .stats(s -> s.field("price"))))
            .build();

        SearchHits<Product> hits = operations.search(query, Product.class);

        // 提取聚合结果
        Map<String, Aggregation> aggregations =
            (Map<String, Aggregation>) hits.getAggregations().aggregations();

        return new SearchResult(hits, aggregations);
    }
}
```

### 场景 3：日志搜索分析

```java
@Document(indexName = "app-logs")
public class AppLog {
    @Id
    private String id;

    @Field(type = FieldType.Text)
    private String message;

    @Field(type = FieldType.Keyword)
    private String level;       // ERROR/WARN/INFO

    @Field(type = FieldType.Keyword)
    private String serviceName;

    @Field(type = FieldType.Date)
    private LocalDateTime timestamp;
}

// 搜索最近的 ERROR 日志
Criteria criteria = new Criteria("level").is("ERROR")
    .and(new Criteria("timestamp").greaterThan(LocalDateTime.now().minusHours(1)));
Query query = new CriteriaQuery(criteria);
SearchHits<AppLog> errors = operations.search(query, AppLog.class);
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Text 和 Keyword 双类型**。搜索字段用 Text（分词），同一字段的 .keyword 用于排序和精确匹配。

2. **filter 优于 must**。不参与评分的过滤用 filter，性能更好（可缓存）。

3. **批量导入用 Bulk**。大量数据导入用 `operations.save(collection)` 批量操作，或 BulkRequest 手动批量。

4. **合理设置分片数**。索引创建时规划分片数（后期不能修改），单分片建议 10-50GB。

5. **中文搜索配 IK 分词器**。中文场景安装 ik 分词器，否则默认分词器对中文不友好。

### 踩坑记录

**坑 1：版本不匹配**

```text
Spring Data Elasticsearch 与 Elasticsearch 版本严格对应：
Spring Data ES 4.x → ES 7.x
Spring Data ES 5.x → ES 8.x
版本不匹配会导致连接失败或 API 不兼容
```

**坑 2：Text 字段用 term 查询查不到**

```java
// name 是 Text 类型（已分词），用 term 精确查询查不到
@Query("{\"term\": {\"name\": \"小米手机\"}}")
// term 查询不分词，"小米手机" 在倒排索引中是 "小米" 和 "手机"，查不到完整词

// 正确：Text 字段用 match 查询
@Query("{\"match\": {\"name\": \"小米手机\"}}")
```

Text 字段用 match（分词匹配），Keyword 字段用 term（精确匹配）。

**坑 3：@Field 类型标注错误**

```java
@Field(type = FieldType.Text)
private String status;  // 状态应该用 Keyword，不是 Text
// Text 会分词，"ACTIVE" 被拆成 "act", "ive"，精确匹配失败
```

精确匹配的字段（状态、分类、ID）用 Keyword，不要用 Text。

**坑 4：聚合结果字段名错误**

```java
// 聚合的 field 必须是 Keyword 类型，Text 字段不能直接聚合
.terms(t -> t.field("category"))   // category 必须是 Keyword
```

Text 字段不能聚合（分词后每个词都是一个桶），聚合字段用 Keyword。

**坑 5：分页深翻页性能问题**

```java
// from + size 深翻页（from=10000）性能差，ES 默认限制 10000
PageRequest.of(1000, 20)  // 深度分页性能下降
```

深度分页用 search_after 或 scroll API，避免 from + size 深翻页。

**坑 6：中文分词不生效**

```text
中文内容搜索不准确，因为没装 ik 分词器。
默认 standard 分词器对中文按单字分词。
```

中文搜索必须安装 ik 分词器，并在 @Field 中配置 `analyzer = "ik_max_word"`。
