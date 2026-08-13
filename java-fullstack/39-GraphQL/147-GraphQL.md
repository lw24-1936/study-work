---
title: GraphQL
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [graphql, schema, query, mutation, subscription, resolver, datafetcher]
---

# GraphQL

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [Schema 与类型系统](#schema-与类型系统)
- [Interface、Union 与 Directive](#interfaceunion-与-directive)
- [Query 查询](#query-查询)
- [Mutation 变更](#mutation-变更)
- [Subscription 订阅](#subscription-订阅)
- [Resolver 解析器](#resolver-解析器)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

GraphQL 是 API 查询语言，客户端按需查询数据，解决 REST 的过度获取和多次请求问题。

```text
GraphQL 解决的问题：
1. 过度获取（Over-fetching）—— REST 返回整个对象，只要部分字段也返回全部
2. 不足获取（Under-fetching）—— REST 要多次请求才能凑齐数据
3. 版本管理 —— REST 要 /v1、/v2，GraphQL 加字段即可
```

```text
GraphQL 的核心：
1. 按需查询 —— 客户端声明要什么字段
2. 单一端点 —— 所有请求发到一个 /graphql 端点
3. 强类型 —— Schema 定义类型
```

```text
REST vs GraphQL：
REST：/api/users/1 → 返回整个 User 对象
GraphQL：query { user(id:1) { name age } } → 只返回 name 和 age
```

## Schema 与类型系统

Schema 定义 API 的类型结构，是 GraphQL 的核心。

### 类型定义（SDL）

```graphql
# Schema 定义（Schema Definition Language）
type User {
    id: ID!
    name: String!
    age: Int
    email: String
    posts: [Post!]      # 关联的帖子
}

type Post {
    id: ID!
    title: String!
    author: User!
}

# 查询入口
type Query {
    user(id: ID!): User
    users: [User!]!
    post(id: ID!): Post
}

# 变更入口
type Mutation {
    createUser(name: String!, age: Int): User
    deleteUser(id: ID!): Boolean
}
```

### 标量类型（Scalar）

```text
内置标量：
Int —— 整数
Float —— 浮点数
String —— 字符串
Boolean —— 布尔
ID —— 唯一标识

自定义标量：
scalar Date   # 自定义日期类型
```

### 类型修饰符

```text
! —— 非空（必填/必有值）
[] —— 列表（数组）

User!      —— 非空 User
[User]     —— User 列表（可为空）
[User!]!   —— 非空的 User 列表（列表和元素都非空）
```

## Interface、Union 与 Directive

### Interface 接口

Interface 定义一组公共字段，多个类型实现它，实现多态查询。

```graphql
# 定义接口
interface Node {
    id: ID!
}

# 实现接口
type User implements Node {
    id: ID!
    name: String!
}

type Post implements Node {
    id: ID!
    title: String!
}
```

```graphql
# 通过接口查询（多态）
query {
    node(id: 1) {
        id
        ... on User { name }
        ... on Post { title }
    }
}
```

### Union 联合类型

Union 是多个类型的并集（无公共字段），配合内联片段使用。

```graphql
# 联合类型：搜索结果可能是用户或帖子
union SearchResult = User | Post

type Query {
    search(keyword: String!): [SearchResult!]!
}
```

```graphql
query {
    search(keyword: "spring") {
        ... on User { name }
        ... on Post { title }
    }
}
```

### Interface vs Union

| 维度 | Interface | Union |
|------|-----------|-------|
| 公共字段 | 有（必须实现） | 无 |
| 类型关系 | 实现（implements） | 联合（|） |
| 查询 | 直接查公共字段 + 片段 | 只能用内联片段 |
| 场景 | 有共同行为的类型 | 完全无关的类型 |

### Directive 指令

Directive 是 GraphQL 的元指令，控制查询/字段的行为。

```graphql
# 内置指令
query getUser($withPosts: Boolean!) {
    user(id: 1) {
        name
        posts @include(if: $withPosts) {   # 条件包含
            title
        }
        email @skip(if: true)              # 条件跳过
    }
}
```

```text
内置指令：
1. @include(if: Boolean) —— 条件包含字段
2. @skip(if: Boolean) —— 条件跳过字段
3. @deprecated —— 标记废弃

自定义指令：@auth、@cache（需要服务端实现）
```

## Query 查询

Query 是读取数据的入口。

### 基本查询

```graphql
# 查询单个用户（只取 name 和 age）
query {
    user(id: 1) {
        name
        age
    }
}
```

```json
// 响应
{
  "data": {
    "user": { "name": "张三", "age": 20 }
  }
}
```

### 带参数查询

```graphql
query {
    user(id: 1) {
        name
        age
        email
    }
}
```

### 嵌套查询（关联数据）

```graphql
# 一次请求获取用户和其帖子
query {
    user(id: 1) {
        name
        posts {
            title
        }
    }
}
```

### 别名和片段

```graphql
query {
    user1: user(id: 1) { name }   # 别名
    user2: user(id: 2) { name }

    # 片段（复用字段）
    user3: user(id: 3) {
        ...userFields
    }
}

fragment userFields on User {
    name
    age
    email
}
```

## Mutation 变更

Mutation 是写数据的入口（增删改）。

### 基本 Mutation

```graphql
mutation {
    createUser(name: "张三", age: 20) {
        id
        name
    }
}
```

### 带变量的 Mutation

```graphql
mutation CreateUser($name: String!, $age: Int) {
    createUser(name: $name, age: $age) {
        id
        name
    }
}
```

```json
// 变量
{ "name": "张三", "age": 20 }
```

## Subscription 订阅

Subscription 是实时数据推送（类似 WebSocket）。

### 订阅定义

```graphql
type Subscription {
    userCreated: User!
}
```

### 订阅的用途

```text
1. 实时通知 —— 新消息、新订单
2. 实时数据 —— 股票价格、实时统计
3. 聊天 —— 实时消息
```

```text
注意：Subscription 需要 WebSocket 支持，
Java 实现复杂，不是所有场景都适合。
```

## Resolver 解析器

Resolver（DataFetcher）负责解析每个字段的数据。

### Java 实现（Spring GraphQL）

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-graphql</artifactId>
</dependency>
```

```java
@Controller
public class UserController {

    // Query 解析器
    @QueryMapping
    public User user(@Argument Long id) {
        return userService.getById(id);
    }

    @QueryMapping
    public List<User> users() {
        return userService.listAll();
    }

    // Mutation 解析器
    @MutationMapping
    public User createUser(@Argument String name, @Argument Integer age) {
        return userService.create(name, age);
    }

    // 字段解析器（关联数据）
    @SchemaMapping(typeName = "User", field = "posts")
    public List<Post> posts(User user) {
        return postService.getByUserId(user.getId());
    }
}
```

### Resolver 的执行

```text
每个字段都有对应的 Resolver：
user(id:1) → user() 方法
user.name → User.getName()
user.posts → posts(User) 方法（关联查询）
```

## 应用场景实战

### 场景 1：按需查询（解决过度获取）

```graphql
# 列表页只需要 name 和 age
query {
    users {
        name
        age
    }
}

# 详情页需要全部字段 + 帖子
query {
    user(id: 1) {
        name
        age
        email
        posts { title }
    }
}
```

### 场景 2：一次请求获取关联数据

```graphql
# REST 需要 3 次请求，GraphQL 一次搞定
query {
    user(id: 1) {
        name
        posts { title }
        orders { amount }
    }
}
```

### 场景 3：Spring Boot GraphQL 完整实现

```java
@Controller
public class OrderController {

    @QueryMapping
    public Order order(@Argument Long id) {
        return orderService.getById(id);
    }

    @MutationMapping
    public Order createOrder(@Argument OrderInput input) {
        return orderService.create(input);
    }

    @SchemaMapping(typeName = "Order", field = "user")
    public User user(Order order) {
        return userService.getById(order.getUserId());
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **按需查询字段**。客户端只请求需要的字段，减少传输。

2. **关联数据用嵌套查询**。避免多次请求。

3. **分页用 cursor**。GraphQL 分页用 cursor（不靠 offset）。

4. **N+1 问题用 DataLoader**。批量加载关联数据。

5. **错误用 errors 字段**。GraphQL 错误在 errors 数组，不在 data 里。

### 踩坑记录

**坑 1：N+1 查询问题**

```java
@SchemaMapping(typeName = "User", field = "posts")
public List<Post> posts(User user) {
    return postService.getByUserId(user.getId());   // 每个 user 查一次，N+1
}
```

用 DataLoader 批量加载（一次查所有关联数据）。

**坑 2：过度嵌套导致深度查询**

```graphql
query {
    user(id: 1) { posts { comments { user { posts { ... } } } } }
}
// 无限嵌套，恶意查询拖垮服务
```

限制查询深度（maxDepth），防止深度嵌套攻击。

**坑 3：Subscription 实现复杂**

```text
Subscription 需要 WebSocket，Java 实现复杂
```

不是所有场景都需要 Subscription，先评估需求。

**坑 4：缓存困难**

```text
GraphQL 单一端点，HTTP 缓存（按 URL）失效
```

用客户端缓存（Apollo/Relay）或数据层缓存。

**坑 5：错误处理混乱**

```text
GraphQL 部分成功（data + errors），客户端要处理 errors 数组
```

客户端要同时处理 data 和 errors，不能只判断 HTTP 状态码。

**坑 6：把 GraphQL 当万能药**

```text
简单 API 也用 GraphQL，增加复杂度
```

简单场景用 REST，复杂关联、按需查询用 GraphQL。
