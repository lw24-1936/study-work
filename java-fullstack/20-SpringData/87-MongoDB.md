---
title: Spring Data MongoDB
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-data-mongodb, mongotemplate, mongorepository, document, query, aggregation, mongodb]
---

# Spring Data MongoDB

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [依赖与配置](#依赖与配置)
- [@Document 实体映射](#document-实体映射)
- [MongoRepository](#mongorepository)
- [MongoTemplate](#mongotemplate)
- [Query 与 Criteria](#query-与-criteria)
- [Aggregation 聚合框架](#aggregation-聚合框架)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Data MongoDB 是 Spring 对 MongoDB 的集成。MongoDB 是文档型 NoSQL 数据库，存储 JSON 风格的 BSON 文档。

```text
MongoDB 特点：
1. 文档型 —— 数据以 JSON 文档存储，天然适合对象
2. 灵活 Schema —— 不需要预定义表结构
3. 水平扩展 —— 分片支持海量数据
4. 聚合管道 —— 强大的数据分析能力

核心组件：
MongoTemplate    —— 底层操作模板（CRUD、查询、聚合）
MongoRepository  —— Repository 抽象（类似 JPA）
```

```text
MongoDB vs 关系数据库：
MySQL 表          MongoDB 集合（Collection）
MySQL 行          MongoDB 文档（Document）
MySQL 列          MongoDB 字段（Field）
MySQL join        MongoDB 嵌入文档 / DBRef
```

## 依赖与配置

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
```

### 连接配置

```yaml
spring:
  data:
    mongodb:
      uri: mongodb://localhost:27017/mydb
      # 或者分项配置
      # host: localhost
      # port: 27017
      # database: mydb
      # username: root
      # password: ${MONGO_PASSWORD}
      # authentication-database: admin
```

### URI 格式

```text
mongodb://[用户名:密码@]主机[:端口]/数据库[?选项]

单机：mongodb://localhost:27017/mydb
副本集：mongodb://host1:27017,host2:27017,host3:27017/mydb?replicaSet=rs0
```

## @Document 实体映射

### @Document 注解

```java
@Document(collection = "users")   // 指定集合名（默认类名首字母小写）
public class User {

    @Id                              // 主键（映射到 _id）
    private String id;

    @Field("username")               // 指定字段名（默认属性名）
    private String username;

    @Indexed(unique = true)          // 唯一索引
    private String email;

    @Field("created_at")
    private LocalDateTime createdAt;

    // 嵌套文档
    private Address address;

    // 数组
    private List<String> tags;
}
```

### 常用注解

| 注解 | 作用 |
|------|------|
| @Document | 标记文档，指定集合名 |
| @Id | 主键（映射 _id） |
| @Field | 指定字段名 |
| @Indexed | 创建索引（unique、direction 等） |
| @CompoundIndex | 复合索引 |
| @Transient | 忽略该字段（不持久化） |
| @DBRef | 引用其他集合的文档 |
| @Version | 乐观锁版本号 |

### 嵌套文档与数组

```java
@Document(collection = "orders")
public class Order {
    @Id
    private String id;
    private String orderNo;

    // 嵌套文档（直接嵌入，无需 join）
    private Customer customer;
    private Address shippingAddress;

    // 数组
    private List<OrderItem> items;
}

public class OrderItem {
    private String productId;
    private int quantity;
    private BigDecimal price;
}
```

```json
// 存储结构
{
  "_id": "...",
  "orderNo": "ORD001",
  "customer": {"name": "张三", "email": "..."},
  "items": [
    {"productId": "p1", "quantity": 2, "price": 99.9}
  ]
}
```

嵌套文档是 MongoDB 的核心优势——关联数据直接嵌入，无需 join。

## MongoRepository

MongoRepository 提供与 JPA 类似的 Repository 抽象。

### 定义 Repository

```java
public interface UserRepository extends MongoRepository<User, String> {

    // 方法名派生查询
    List<User> findByUsername(String username);
    List<User> findByAgeGreaterThan(int age);
    List<User> findByUsernameContaining(String keyword);

    // @Query 注解（MongoDB 查询语法）
    @Query("{'age': {$gt: ?0}}")
    List<User> findAdults(int age);

    @Query(value = "{'status': ?0}", fields = "{'username': 1, 'email': 1}")
    List<User> findByStatus(String status);  // 只返回指定字段（投影）
}
```

### MongoRepository 接口方法

```java
public interface MongoRepository<T, ID> extends PagingAndSortingRepository<T, ID> {
    <S extends T> S insert(S entity);              // 插入（不更新）
    <S extends T> List<S> insert(Iterable<S> entities);
    <S extends T> S save(S entity);                // 保存（存在则更新）
    List<T> findAll();
    List<T> findAll(Sort sort);
    Page<T> findAll(Pageable pageable);
    // 继承自 CrudRepository：findById、existsById、deleteById 等
}
```

### 使用

```java
@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    public User save(User user) {
        return userRepository.save(user);
    }

    public User findById(String id) {
        return userRepository.findById(id).orElse(null);
    }

    public List<User> findByAgeGreaterThan(int age) {
        return userRepository.findByAgeGreaterThan(age);
    }
}
```

## MongoTemplate

MongoTemplate 是更底层的操作模板，提供灵活的操作能力。

### 基础 CRUD

```java
@Autowired
private MongoTemplate mongoTemplate;

// 插入
User user = new User();
user.setUsername("张三");
mongoTemplate.insert(user);          // insert：只插入
mongoTemplate.save(user);            // save：存在则更新

// 查询
User found = mongoTemplate.findById("id", User.class);
List<User> all = mongoTemplate.findAll(User.class);

// 删除
mongoTemplate.remove(user);
mongoTemplate.remove(query, User.class);
```

### 更新

```java
import org.springframework.data.mongodb.core.query.Update;

// 更新单个字段
Query query = Query.query(Criteria.where("username").is("张三"));
Update update = Update.update("age", 26);
mongoTemplate.updateFirst(query, update, User.class);

// 更新多个
mongoTemplate.updateMulti(query, update, User.class);

// upsert（不存在则插入）
mongoTemplate.upsert(query, update, User.class);

// 原子递增
Update increment = new Update().inc("loginCount", 1);
mongoTemplate.updateFirst(query, increment, User.class);
```

### findAndModify（原子操作）

```java
// 原子地查询并修改
Query query = Query.query(Criteria.where("orderNo").is("ORD001"));
Update update = Update.update("status", "PAID");
User updated = mongoTemplate.findAndModify(query, update, User.class);
```

## Query 与 Criteria

Criteria 是构建查询条件的 DSL，Query 封装 Criteria + 分页排序。

### Criteria 条件构建

```java
// 等值
Criteria.where("username").is("张三")

// 比较
Criteria.where("age").gt(18)          // 大于
Criteria.where("age").gte(18)         // 大于等于
Criteria.where("age").lt(60)          // 小于
Criteria.where("age").lte(60)         // 小于等于
Criteria.where("age").ne(18)          // 不等于

// 范围
Criteria.where("age").in(18, 19, 20)  // 在范围内
Criteria.where("age").nin(18, 19)     // 不在范围

// 正则
Criteria.where("username").regex("^张")

// 存在性
Criteria.where("email").exists(true)
```

### 组合条件

```java
// AND
Query query = new Query();
query.addCriteria(Criteria.where("age").gt(18).and("status").is("ACTIVE"));

// OR
Criteria criteria = new Criteria().orOperator(
    Criteria.where("username").is("张三"),
    Criteria.where("email").is("zhangsan@example.com")
);

// 完整示例
Query query = new Query();
query.addCriteria(
    Criteria.where("age").gte(18)
        .andOperator(
            Criteria.where("status").is("ACTIVE"),
            Criteria.where("vip").is(true)
        )
);
```

### 分页排序

```java
Query query = new Query(Criteria.where("age").gt(18));
query.with(Sort.by(Sort.Direction.DESC, "createdAt"));  // 排序
query.skip(20).limit(10);                                // 分页

List<User> users = mongoTemplate.find(query, User.class);
```

### 投影（只查部分字段）

```java
Query query = new Query();
query.fields().include("username").include("email");  // 只返回这些字段
query.fields().exclude("password");                   // 排除字段

List<User> users = mongoTemplate.find(query, User.class);
```

## Aggregation 聚合框架

MongoDB 的聚合管道（Aggregation Pipeline）是强大的数据分析工具，类似 SQL 的 GROUP BY + 聚合函数。

### 聚合管道概念

```text
聚合管道：数据依次经过多个阶段（Stage）处理
document → $match → $group → $sort → 结果

常用阶段：
$match   —— 过滤（类似 WHERE）
$group   —— 分组（类似 GROUP BY）
$sort    —— 排序
$project —— 投影（选择字段）
$limit   —— 限制条数
$skip    —— 跳过
$unwind  —— 展开数组
$lookup  —— 关联查询（类似 JOIN）
```

### 聚合示例

```java
// 按状态统计用户数量（类似 GROUP BY status COUNT(*)）
Aggregation agg = Aggregation.newAggregation(
    Aggregation.group("status").count().as("count")
);
AggregationResults<Map> results = mongoTemplate.aggregate(agg, "users", Map.class);
```

```java
// 完整示例：按年龄段统计
Aggregation agg = Aggregation.newAggregation(
    // 1. 过滤
    Aggregation.match(Criteria.where("createdAt").gte(startTime)),

    // 2. 分组统计
    Aggregation.group("ageGroup")
        .count().as("count")
        .avg("score").as("avgScore"),

    // 3. 排序
    Aggregation.sort(Sort.Direction.DESC, "count")
);

AggregationResults<AgeGroupResult> results =
    mongoTemplate.aggregate(agg, "users", AgeGroupResult.class);
List<AgeGroupResult> list = results.getMappedResults();
```

### 常用聚合操作

```java
// 统计文档总数
long count = mongoTemplate.count(new Query(), User.class);

// 去重统计
List<String> distinctUsernames = mongoTemplate.findDistinct(
    new Query(), "username", User.class, String.class);

// $unwind 展开数组（每个数组元素生成一条文档）
Aggregation agg = Aggregation.newAggregation(
    Aggregation.unwind("tags"),
    Aggregation.group("tags").count().as("count")
);
```

### 聚合 vs 查询

| 维度 | Query/Criteria | Aggregation |
|------|---------------|-------------|
| 用途 | 文档查询 | 数据分析、统计 |
| 分组 | 不支持 | 支持 $group |
| 统计 | 只支持 count | 支持 sum/avg/max/min |
| 复杂度 | 简单 | 复杂管道 |

统计、报表、分析场景用 Aggregation，普通 CRUD 用 Query。

## 应用场景实战

### 场景 1：商品搜索（条件组合 + 分页）

```java
@Service
public class ProductService {

    @Autowired
    private MongoTemplate mongoTemplate;

    public Page<Product> search(String keyword, BigDecimal minPrice,
                                BigDecimal maxPrice, String category,
                                int page, int size) {
        Criteria criteria = new Criteria();

        // 动态组合条件
        if (StringUtils.hasText(keyword)) {
            criteria.and("name").regex(keyword, "i");  // 忽略大小写
        }
        if (minPrice != null && maxPrice != null) {
            criteria.and("price").gte(minPrice).lte(maxPrice);
        }
        if (StringUtils.hasText(category)) {
            criteria.and("category").is(category);
        }

        Query query = new Query(criteria);
        query.with(Sort.by(Sort.Direction.DESC, "sales"));  // 按销量排序
        query.skip((long) page * size).limit(size);

        List<Product> products = mongoTemplate.find(query, Product.class);
        long total = mongoTemplate.count(query, Product.class);

        return new Page<>(products, total, page, size);
    }
}
```

### 场景 2：销售统计报表（聚合）

```java
@Service
public class SalesReportService {

    @Autowired
    private MongoTemplate mongoTemplate;

    // 按天统计销售额
    public List<DailySales> dailySales(LocalDate start, LocalDate end) {
        Aggregation agg = Aggregation.newAggregation(
            Aggregation.match(Criteria.where("orderDate").gte(start).lte(end)),
            Aggregation.group("orderDate")
                .sum("amount").as("totalAmount")
                .count().as("orderCount"),
            Aggregation.sort(Sort.Direction.ASC, "_id")
        );

        return mongoTemplate.aggregate(agg, "orders", DailySales.class)
            .getMappedResults();
    }

    // 按分类统计
    public List<CategorySales> categorySales() {
        Aggregation agg = Aggregation.newAggregation(
            Aggregation.unwind("items"),  // 展开订单明细
            Aggregation.group("items.category")
                .sum("items.quantity").as("totalQuantity")
                .sum("items.amount").as("totalAmount")
        );

        return mongoTemplate.aggregate(agg, "orders", CategorySales.class)
            .getMappedResults();
    }
}
```

### 场景 3：嵌套文档操作

```java
@Document(collection = "users")
public class User {
    @Id
    private String id;
    private String username;
    private List<Address> addresses;  // 嵌套数组
}

// 给用户添加地址（嵌套数组操作）
Query query = Query.query(Criteria.where("id").is(userId));
Update update = new Update().push("addresses", new Address("北京市", "朝阳区"));
mongoTemplate.updateFirst(query, update, User.class);
```

## 最佳实践与踩坑记录

### 最佳实践

1. **合理选择嵌套还是引用**。高频一起读的数据嵌入（embed），低频访问的数据引用（reference）。

2. **大数组不要无限增长**。文档最大 16MB，嵌套数组无限增长会触顶。用引用或单独集合。

3. **为查询字段建索引**。`@Indexed` 标注高频查询字段，否则全表扫描。

4. **用聚合做统计**。不要查出所有数据在内存统计，用 $group 在数据库端聚合。

5. **批量操作用 bulkOps**。大量写入用 `bulkOps` 批量操作，减少网络往返。

### 踩坑记录

**坑 1：@Id 字段类型问题**

```java
@Document
public class User {
    @Id
    private String id;  // String 类型，Spring 自动生成 ObjectId 字符串
    // 如果用 ObjectId 类型，需要手动处理
}
```

String 类型的 @Id，Spring Data 自动生成 ObjectId 并转为字符串。用 ObjectId 类型则需要 import 和手动处理。

**坑 2：save 和 insert 的区别**

```java
mongoTemplate.insert(user);  // 已存在的 _id 会抛 DuplicateKeyException
mongoTemplate.save(user);    // 已存在的 _id 会更新（upsert 语义）
```

insert 是纯插入，save 是"有则更新无则插入"。

**坑 3：嵌套文档更新覆盖问题**

```java
Update update = Update.update("address", newAddress);
// 这会整体覆盖 address 字段，如果只想改 address.city 会丢失其他字段

// 正确：用点路径
Update update = Update.update("address.city", "上海市");
```

嵌套字段用点路径（`address.city`）精确更新，避免整体覆盖。

**坑 4：正则查询不区分大小写**

```java
// MongoDB 正则默认区分大小写
Criteria.where("username").regex("zhang");  // 只匹配小写 zhang

// 忽略大小写用 "i" 选项
Criteria.where("username").regex("zhang", "i");
```

**坑 5：聚合结果类型转换**

```java
// 聚合返回的 _id 字段是 ObjectId 或其他类型，直接映射可能失败
Aggregation.group("age").count().as("count");
// 结果 Map 的 key 类型要注意（数字可能是 Integer/Long/Double）
```

聚合结果用合适的 DTO 接收，注意类型匹配。

**坑 6：大文档导致性能问题**

```java
// 单个文档存储大量数组数据（如用户的所有订单明细）
// 文档超过几 MB 后读写性能下降，且接近 16MB 上限
```

大数组拆分为独立集合，用引用关联。
