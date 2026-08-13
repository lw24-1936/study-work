---
title: REST API
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [rest, restful, http, api-design, json, http-status, versioning, spring-mvc]
---

# REST API

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [REST 核心原则](#rest-核心原则)
- [HTTP 方法语义](#http-方法语义)
- [HTTP 状态码](#http-状态码)
- [JSON 数据格式](#json-数据格式)
- [API 设计规范](#api-设计规范)
- [API 版本管理](#api-版本管理)
- [Spring Boot 中的 REST 实现](#spring-boot-中的-rest-实现)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

REST（Representational State Transfer，表述性状态转移）是 Roy Fielding 在 2000 年博士论文中提出的一种**软件架构风格**，不是协议或标准。RESTful 是遵循 REST 约束的 Web API 设计方式。

REST 的核心思想：把**一切抽象为资源（Resource）**，通过统一的 HTTP 方法对资源进行操作。

```text
资源（Resource）    —— 一切事物，用 URI 标识（如 /users/123）
表述（Representation） —— 资源的表现形式（JSON、XML、HTML）
状态转移（State Transfer） —— 通过 HTTP 方法改变资源状态
```

```text
对比传统 RPC 风格：
传统：GET /getUser?id=123          POST /deleteUser?id=123
REST：GET /users/123               DELETE /users/123

传统关注"动作"（getUser、deleteUser）
REST 关注"资源"（users/123）+ 标准动作（GET、DELETE）
```

## REST 核心原则

### 1. 资源导向（Resource-Oriented）

每个资源用 URI 唯一标识，URI 用名词（复数），不用动词：

```text
正确：
GET    /users          用户列表
GET    /users/123      用户 123
POST   /users          创建用户
GET    /users/123/orders   用户 123 的订单

错误：
GET    /getUsers          动词
POST   /createUser        动词
GET    /getUserById?id=123  动作 + 参数
```

### 2. 无状态（Stateless）

每个请求都包含处理请求所需的全部信息，服务器不保存客户端状态：

```text
有状态（错误）：服务器记住"上一个请求的用户"
无状态（正确）：每个请求都带 token 标识身份
```

好处：可扩展性强（任意服务器都能处理请求）、易于缓存、故障隔离。

### 3. 统一接口（Uniform Interface）

通过标准的 HTTP 方法（GET/POST/PUT/DELETE）操作资源，语义统一。

### 4. 表述性状态（Representation）

资源可以有多种表述（JSON、XML），客户端通过 Accept 头声明需要的格式：

```http
GET /users/123
Accept: application/json       → 返回 JSON
Accept: application/xml        → 返回 XML
```

### 5. HATEOAS（可选进阶）

超媒体作为应用状态引擎，在响应中提供可导航的链接：

```json
{
  "id": 123,
  "name": "张三",
  "_links": {
    "self": {"href": "/users/123"},
    "orders": {"href": "/users/123/orders"},
    "manager": {"href": "/users/456"}
  }
}
```

Spring 通过 Spring HATEOAS 支持。实际项目中 HATEOAS 用得不多，理解概念即可。

## HTTP 方法语义

### GET —— 获取资源

```text
安全（Safe）：不改变服务器状态
幂等（Idempotent）：多次请求结果一致
```

```java
GET /users            // 列表
GET /users/123        // 单个
GET /users/123/orders // 子资源
```

### POST —— 创建资源

```text
非安全：会改变服务器状态
非幂等：多次调用会创建多个资源
```

```java
POST /users           // 创建用户
POST /orders          // 创建订单
```

### PUT —— 完整更新资源

```text
幂等：多次调用结果一致（更新为同一状态）
```

```java
PUT /users/123        // 完整替换用户 123 的所有字段
```

PUT 要求提供资源的**完整表示**，未提供的字段会被置空。

### PATCH —— 部分更新

```text
非幂等（通常）：只更新提供的字段
```

```java
PATCH /users/123      // 只更新用户 123 的部分字段（如只改邮箱）
```

### DELETE —— 删除资源

```text
幂等：删除后再删除，结果都是"不存在"
```

```java
DELETE /users/123     // 删除用户 123
```

### 方法语义总结

| 方法 | 语义 | 安全 | 幂等 | 典型路径 |
|------|------|------|------|---------|
| GET | 查询 | 是 | 是 | /users/{id} |
| POST | 创建 | 否 | 否 | /users |
| PUT | 完整更新 | 否 | 是 | /users/{id} |
| PATCH | 部分更新 | 否 | 否 | /users/{id} |
| DELETE | 删除 | 否 | 是 | /users/{id} |

**关键区分**：
- POST 创建 → 客户端不知道资源 ID，服务器生成
- PUT 更新 → 客户端知道资源 ID，URI 含 ID
- PUT vs PATCH → PUT 传完整对象，PATCH 传部分字段

## HTTP 状态码

状态码是 REST API 的"语义语言"，正确使用状态码是 API 专业度的体现。

### 2xx —— 成功

| 状态码 | 含义 | 典型场景 |
|--------|------|---------|
| 200 OK | 请求成功 | GET/PUT/PATCH 成功 |
| 201 Created | 资源已创建 | POST 创建成功 |
| 202 Accepted | 请求已接受，异步处理中 | 异步任务提交 |
| 204 No Content | 成功但无响应体 | DELETE 成功 |

### 3xx —— 重定向

| 状态码 | 含义 |
|--------|------|
| 301 Moved Permanently | 永久重定向 |
| 304 Not Modified | 资源未修改（配合缓存） |

### 4xx —— 客户端错误

| 状态码 | 含义 | 典型场景 |
|--------|------|---------|
| 400 Bad Request | 请求格式错误 | 参数校验失败、JSON 格式错误 |
| 401 Unauthorized | 未认证 | 未登录、token 缺失 |
| 403 Forbidden | 已认证但无权限 | 权限不足 |
| 404 Not Found | 资源不存在 | 查不到数据 |
| 405 Method Not Allowed | 方法不允许 | GET 请求了只支持 POST 的接口 |
| 409 Conflict | 资源冲突 | 并发更新冲突 |
| 415 Unsupported Media Type | Content-Type 不支持 | 传了 XML 但只支持 JSON |
| 422 Unprocessable Entity | 语义校验失败 | 数据格式正确但业务校验不通过 |
| 429 Too Many Requests | 请求过多 | 限流 |

### 5xx —— 服务器错误

| 状态码 | 含义 |
|--------|------|
| 500 Internal Server Error | 服务器内部错误 |
| 502 Bad Gateway | 网关错误 |
| 503 Service Unavailable | 服务不可用（过载/维护） |
| 504 Gateway Timeout | 网关超时 |

### 常见误用

```text
错误：所有成功都返回 200，失败都返回 500
正确：
  POST 创建成功 → 201
  DELETE 成功 → 204
  未登录 → 401
  无权限 → 403
  资源不存在 → 404
  参数错误 → 400
```

## JSON 数据格式

JSON（JavaScript Object Notation）是现代 REST API 的事实标准数据格式。

### 基本规范

```json
{
  "id": 123,
  "name": "张三",
  "email": "zhangsan@example.com",
  "age": 25,
  "vip": true,
  "tags": ["java", "spring"],
  "address": {
    "city": "北京",
    "district": "朝阳区"
  },
  "orders": [
    {"id": 1, "amount": 99.9},
    {"id": 2, "amount": 199.9}
  ]
}
```

### 命名规范

```text
推荐：camelCase（驼峰）—— userId、createdAt、isDeleted
避免：snake_case（下划线）—— user_id、created_at
避免：PascalCase（帕斯卡）—— UserId、CreatedAt
```

### 日期时间格式

```text
推荐：ISO 8601 格式
"createdAt": "2026-08-12T14:30:00+08:00"

避免：时间戳数字（可读性差）
避免：无时区的时间（易混淆）
```

### 响应包装

有两种风格：

**风格 1：直接返回数据（REST 纯正风格）**

```json
{"id": 123, "name": "张三"}
```

**风格 2：统一包装（国内常用）**

```json
{
  "code": 200,
  "message": "success",
  "data": {"id": 123, "name": "张三"}
}
```

两种风格各有优劣。统一包装便于前端统一处理，但牺牲了 REST 的纯粹性（HTTP 状态码已能表达语义）。实际项目中二选一，团队内保持一致。

## API 设计规范

### 1. URI 设计

```text
资源用名词复数：
/users           ✓
/user            ✗（建议复数）
/getUsers        ✗（不要动词）

层级关系：
/users/{id}/orders          ✓ 用户下的订单
/users/{id}/orders/{orderId} ✓ 用户的某个订单

过滤/分页用查询参数：
/users?page=2&size=20&sort=age,desc&name=张
```

### 2. 统一响应结构

```java
// 统一响应体
public class Result<T> {
    private int code;         // 业务状态码
    private String message;   // 提示信息
    private T data;           // 数据

    public static <T> Result<T> success(T data) {
        return new Result<>(200, "success", data);
    }

    public static <T> Result<T> error(int code, String message) {
        return new Result<>(code, message, null);
    }
}
```

### 3. 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [{"id": 1, "name": "张三"}, {"id": 2, "name": "李四"}],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5
  }
}
```

### 4. 错误响应

```json
{
  "code": 40001,
  "message": "用户名已存在",
  "details": {
    "field": "username",
    "rejectedValue": "zhangsan"
  }
}
```

### 5. 安全与幂等

- 敏感接口用 HTTPS
- 认证用 Authorization 头（Bearer token），不要用 Cookie
- POST 创建要防重复提交（幂等键）
- 输入校验在服务端，不信任客户端

## API 版本管理

API 会演进，版本管理让老客户端不受新版本影响。

### 方式 1：URL 路径版本（最常用）

```text
GET /api/v1/users
GET /api/v2/users
```

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserControllerV1 { ... }

@RestController
@RequestMapping("/api/v2/users")
public class UserControllerV2 { ... }
```

### 方式 2：请求头版本

```http
GET /api/users
Accept: application/vnd.myapp.v1+json
```

### 方式 3：查询参数版本

```text
GET /api/users?version=1
```

### 版本策略建议

| 维度 | URL 版本 | 头版本 | 参数版本 |
|------|---------|--------|---------|
| 可读性 | 直观 | 隐晦 | 一般 |
| 缓存 | 天然隔离 | 需考虑 Vary | 需考虑 |
| 实现 | 简单 | 需自定义解析 | 简单 |
| 适用 | 大多数场景 | 强 REST 洁癖 | 临时方案 |

推荐 URL 版本，直观且易于实现。

### 兼容性原则

```text
向后兼容（Backward Compatible）：
- 新增字段：兼容（老客户端忽略新字段）
- 删除字段：不兼容（老客户端可能依赖）
- 改字段类型：不兼容
- 新增接口：兼容

破坏性变更 → 发布新版本 v2
非破坏性变更 → 在原版本演进
```

## Spring Boot 中的 REST 实现

### 基本 CRUD 接口

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Autowired
    private UserService userService;

    // 查询列表（分页）
    @GetMapping
    public PageResult<User> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        return userService.findByPage(page, size);
    }

    // 查询单个
    @GetMapping("/{id}")
    public ResponseEntity<User> get(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElseThrow(() -> new NotFoundException("用户不存在"));
    }

    // 创建
    @PostMapping
    public ResponseEntity<User> create(@RequestBody @Valid User user) {
        User saved = userService.save(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    // 完整更新
    @PutMapping("/{id}")
    public User update(@PathVariable Long id, @RequestBody User user) {
        user.setId(id);
        return userService.update(user);
    }

    // 部分更新
    @PatchMapping("/{id}")
    public User partialUpdate(@PathVariable Long id, @RequestBody Map<String, Object> updates) {
        return userService.partialUpdate(id, updates);
    }

    // 删除
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

### Jackson 序列化控制

```java
public class User {
    private Long id;

    @JsonIgnore          // 序列化时忽略（密码等敏感字段）
    private String password;

    @JsonProperty("userName")  // 自定义字段名
    private String name;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")  // 日期格式
    private LocalDateTime createdAt;

    @JsonInclude(JsonInclude.Include.NON_NULL)  // 类级别：null 字段不输出
    private String nickname;
}
```

```yaml
# application.yml 全局配置
spring:
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: GMT+8
    default-property-inclusion: non_null
    serialization:
      write-dates-as-timestamps: false
```

### 内容协商

Spring 根据 Accept 头自动选择序列化格式：

```java
@RestController
public class ContentController {

    @GetMapping(value = "/user/{id}",
                produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
    public User getUser(@PathVariable Long id) {
        return userService.find(id);
    }
    // Accept: application/json → JSON
    // Accept: application/xml  → XML
}
```

## 应用场景实战

### 场景 1：RESTful 订单系统完整接口设计

```text
资源设计：
POST   /api/v1/orders                 创建订单
GET    /api/v1/orders                 订单列表（分页/过滤）
GET    /api/v1/orders/{id}            订单详情
PUT    /api/v1/orders/{id}            修改订单（完整）
PATCH  /api/v1/orders/{id}/status     修改订单状态（部分）
DELETE /api/v1/orders/{id}            取消订单

子资源：
GET    /api/v1/orders/{id}/items      订单明细
POST   /api/v1/orders/{id}/items      添加明细
POST   /api/v1/orders/{id}/pay        支付订单（动作型资源）
```

```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @PostMapping
    public ResponseEntity<Order> create(@RequestBody @Valid OrderCreateRequest request) {
        Order order = orderService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(order);
    }

    @GetMapping("/{id}")
    public Order detail(@PathVariable Long id) {
        return orderService.findById(id);
    }

    @PatchMapping("/{id}/status")
    public Order updateStatus(@PathVariable Long id,
                              @RequestBody StatusUpdateRequest request) {
        return orderService.updateStatus(id, request.getStatus());
    }

    @PostMapping("/{id}/pay")
    public PayResult pay(@PathVariable Long id) {
        return orderService.pay(id);
    }
}
```

### 场景 2：带版本和分页的列表接口

```java
@RestController
@RequestMapping("/api/v2/users")
public class UserControllerV2 {

    @GetMapping
    public PageResult<UserDTO> list(UserQuery query) {
        // query 包含 page、size、sort、keyword 等
        return userService.query(query);
    }
}

public class PageResult<T> {
    private List<T> list;
    private long total;
    private int page;
    private int size;

    // 计算总页数
    public int getPages() {
        return size == 0 ? 0 : (int) Math.ceil((double) total / size);
    }
}
```

### 场景 3：幂等性设计（防重复提交）

```java
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @PostMapping
    public Result create(@RequestHeader("Idempotency-Key") String idempotencyKey,
                         @RequestBody OrderCreateRequest request) {
        // 用幂等键去重，防止用户重复点击导致重复下单
        Order existing = orderService.findByIdempotencyKey(idempotencyKey);
        if (existing != null) {
            return Result.success(existing);  // 已处理过，直接返回
        }
        Order order = orderService.create(idempotencyKey, request);
        return Result.success(order);
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **状态码语义正确**。POST 成功返回 201，DELETE 返回 204，不要所有成功都 200。

2. **URI 全小写、连字符分隔**。`/user-profiles` 优于 `/userProfiles` 优于 `/user_profiles`。

3. **列表接口一定带分页**。防止数据量大了之后接口超时和内存溢出。

4. **字段命名 camelCase + 日期 ISO 8601**。前后端约定统一格式。

5. **大数字用字符串传输**。JavaScript 的 Number 最大安全整数是 2^53-1，超出的 Long 类型 ID 会精度丢失：

```java
public class User {
    @JsonSerialize(using = ToStringSerializer.class)  // Long → String
    private Long id;
}
```

### 踩坑记录

**坑 1：DELETE 请求带 body 不被支持**

```http
DELETE /api/users
Content-Type: application/json
{"ids": [1, 2, 3]}
```

HTTP 规范不禁止 DELETE 带 body，但很多框架/网关/代理会忽略或拒绝。批量删除用 POST 更稳妥：`POST /api/users/batch-delete`。

**坑 2：PUT 的语义误解**

```java
// 错误：用 PUT 做部分更新
@PutMapping("/{id}")
public User update(@PathVariable Long id, @RequestBody User user) {
    // 如果 user 只传了 email，其他字段被置空 → 数据丢失
}
```

PUT 是"完整替换"，未传字段会被置空。部分更新应该用 PATCH。

**坑 3：状态码与响应体不一致**

```java
@GetMapping("/{id}")
public ResponseEntity<User> get(@PathVariable Long id) {
    return ResponseEntity.notFound().build();  // 404 但 body 为空
    // 前端拿不到错误信息，只能靠状态码判断
}
```

错误响应也要有 body（统一错误结构），方便前端展示错误信息。

**坑 4：Jackson 反序列化 Unknown 字段**

```java
// 前端多传了字段，默认抛 UnrecognizedPropertyException
@PostMapping
public User create(@RequestBody User user) { ... }
```

```yaml
# 忽略未知字段（前向兼容）
spring:
  jackson:
    deserialization:
      fail-on-unknown-properties: false
```

**坑 5：GET 请求携带敏感信息**

```http
GET /api/users?token=abc123&password=xxx
```

GET 的 URL 会被记录在日志、浏览器历史、代理日志中。敏感信息放 header 或 POST body。

**坑 6：超大响应未做压缩**

```java
// 返回大量数据时未开启 GZIP
```

```yaml
server:
  compression:
    enabled: true
    min-response-size: 1024
```
