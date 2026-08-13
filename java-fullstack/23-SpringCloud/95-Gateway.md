---
title: Spring Cloud Gateway
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-cloud-gateway, route, predicate, filter, globalfilter, 限流, 鉴权, 灰度发布]
---

# Spring Cloud Gateway

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [核心概念：Route/Predicate/Filter](#核心概念routepredicatefilter)
- [路由配置](#路由配置)
- [Predicate 断言](#predicate-断言)
- [Filter 过滤器](#filter-过滤器)
- [GlobalFilter 全局过滤器](#globalfilter-全局过滤器)
- [限流](#限流)
- [统一鉴权](#统一鉴权)
- [灰度发布](#灰度发布)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Cloud Gateway 是 Spring 官方的 API 网关，基于 WebFlux（响应式）构建，是微服务架构的统一入口。

```text
网关的作用：
1. 统一入口 —— 所有请求经过网关，隐藏内部服务
2. 路由转发 —— 根据请求转发到对应服务
3. 统一鉴权 —— 登录校验、权限控制
4. 限流熔断 —— 保护后端服务
5. 日志监控 —— 统一请求日志、链路追踪
6. 跨域处理 —— 统一 CORS 配置
```

```text
Gateway vs Zuul：
Gateway 基于 WebFlux（响应式，非阻塞），Zuul 基于 Servlet（阻塞）
Gateway 性能更好，是 Spring Cloud 官方推荐
```

## 核心概念：Route/Predicate/Filter

```text
Route（路由）：网关的基本构建块，由 ID、目标 URI、Predicate、Filter 组成
Predicate（断言）：匹配请求的条件（路径、方法、请求头等）
Filter（过滤器）：对请求/响应做处理（添加头、限流、鉴权等）
```

```text
请求处理流程：
请求 → 匹配 Predicate → 命中 Route → 执行 Filter 链 → 转发到目标服务
```

```java
// 编程式定义路由
@Bean
public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
    return builder.routes()
        .route("user-service", r -> r
            .path("/api/user/**")          // Predicate：路径匹配
            .uri("lb://user-service"))     // 目标：负载均衡到 user-service
        .build();
}
```

## 路由配置

### YAML 配置路由

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service          # 路由 ID（唯一）
          uri: lb://user-service    # 目标 URI（lb=负载均衡，服务名）
          predicates:
            - Path=/api/user/**     # 匹配 /api/user/ 开头的请求
          filters:
            - StripPrefix=1         # 去掉第一段路径（/api）

        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/order/**
          filters:
            - StripPrefix=1
```

### 路由到不同目标

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 负载均衡到服务（推荐）
        - id: user-service
          uri: lb://user-service

        # 直接转发到固定地址
        - id: external-api
          uri: http://external.example.com

        # 转发到 WebSocket
        - id: websocket
          uri: lb:ws://websocket-service
```

### 动态路由（配合 Nacos）

```yaml
spring:
  cloud:
    gateway:
      discovery:
        locator:
          enabled: true              # 启用服务发现路由
          lower-case-service-id: true
```

启用后，`/服务名/**` 自动路由到对应服务，无需手动配置每个路由。

## Predicate 断言

Predicate 是路由的匹配条件，满足条件才路由到目标。

### 常用 Predicate

```yaml
predicates:
  # 路径匹配
  - Path=/api/user/**,/api/member/**
  
  # 时间匹配（在指定时间后）
  - After=2026-01-01T00:00:00+08:00
  - Before=2026-12-31T23:59:59+08:00
  - Between=2026-01-01T00:00:00+08:00,2026-12-31T23:59:59+08:00

  # 请求方法匹配
  - Method=GET,POST

  # 请求头匹配
  - Header=X-Request-Id, \d+

  # 请求参数匹配
  - Query=version, v1

  # Cookie 匹配
  - Cookie=sessionId, .+

  # 主机匹配
  - Host=**.example.com

  # 权重匹配（灰度发布）
  - Weight=group1, 80
```

### 组合断言

```yaml
predicates:
  - Path=/api/order/**
  - Method=POST        # 同时满足：路径 + 方法
```

多个 Predicate 是 AND 关系，全部满足才匹配。

## Filter 过滤器

Filter 对请求和响应做处理，分为局部过滤器（Route 级）和全局过滤器（GlobalFilter）。

### 常用局部 Filter

```yaml
filters:
  # 路径重写
  - StripPrefix=1            # 去掉第一段路径 /api/user/xxx → /user/xxx
  - PrefixPath=/api          # 加前缀 /xxx → /api/xxx
  - RewritePath=/old/(?<segment>.*), /new/$\{segment}  # 正则重写

  # 请求头处理
  - AddRequestHeader=X-Request-From, gateway      # 添加请求头
  - RemoveRequestHeader=X-Request-From            # 删除请求头
  - AddResponseHeader=X-Gateway, spring-cloud     # 添加响应头

  # 参数处理
  - AddRequestParameter=source, gateway           # 添加请求参数

  # 限流
  - name: RequestRateLimiter
    args:
      redis-rate-limiter.replenishRate: 10
      redis-rate-limiter.burstCapacity: 20
```

### 自定义 Filter

```java
@Component
public class LoggingGatewayFilterFactory
        extends AbstractGatewayFilterFactory<LoggingGatewayFilterFactory.Config> {

    public LoggingGatewayFilterFactory() {
        super(Config.class);
    }

    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            // 前置处理
            long start = System.currentTimeMillis();
            ServerHttpRequest request = exchange.getRequest();
            log.info("请求：{} {}", request.getMethod(), request.getURI());

            return chain.filter(exchange).then(Mono.fromRunnable(() -> {
                // 后置处理
                long cost = System.currentTimeMillis() - start;
                log.info("响应耗时：{}ms", cost);
            }));
        };
    }

    public static class Config {
        // 配置属性
    }
}
```

## GlobalFilter 全局过滤器

GlobalFilter 对所有路由生效，常用于统一鉴权、日志、链路追踪。

### 自定义 GlobalFilter

```java
@Component
@Order(-1)   // 执行顺序，值越小越先执行
public class AuthGlobalFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        // 放行登录等公开路径
        String path = request.getPath().value();
        if (path.contains("/auth/login") || path.contains("/public")) {
            return chain.filter(exchange);
        }

        // 校验 token
        String token = request.getHeaders().getFirst("Authorization");
        if (token == null || !token.startsWith("Bearer ")) {
            // 未认证，返回 401
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.UNAUTHORIZED);
            return response.setComplete();
        }

        // 校验通过，放行
        return chain.filter(exchange);
    }

    @Override
    public int getOrder() {
        return -1;
    }
}
```

### 内置 GlobalFilter

```text
1. NettyRoutingFilter         —— 转发请求到目标服务
2. LoadBalancerClientFilter   —— 负载均衡（lb://）
3. ReactiveLoadBalancerClientFilter —— 响应式负载均衡
4. WebsocketRoutingFilter     —— WebSocket 转发
5. ForwardRoutingFilter       —— 本地转发
```

## 限流

网关是限流的最佳位置，保护后端服务。

### 令牌桶限流（RequestRateLimiter）

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10      # 每秒补充令牌数
                redis-rate-limiter.burstCapacity: 20      # 桶容量（突发上限）
                key-resolver: "#{@userKeyResolver}"       # 限流 key 解析器
```

```java
@Configuration
public class RateLimiterConfig {

    // 按用户 IP 限流
    @Bean
    public KeyResolver userKeyResolver() {
        return exchange -> Mono.just(
            exchange.getRequest().getRemoteAddress().getAddress().getHostAddress());
    }

    // 按用户 ID 限流
    @Bean
    public KeyResolver userIdKeyResolver() {
        return exchange -> Mono.just(
            exchange.getRequest().getHeaders().getFirst("X-User-Id"));
    }
}
```

### 限流需要 Redis

```text
RequestRateLimiter 基于 Redis 实现，需要引入：
spring-boot-starter-data-redis-reactive
```

## 统一鉴权

网关统一鉴权，下游服务不再重复校验。

### 鉴权流程

```text
1. 登录请求 → 网关放行 → 认证服务 → 返回 token
2. 业务请求 → 网关校验 token → 放行 → 下游服务
3. token 无效 → 网关返回 401
```

### 鉴权 GlobalFilter

```java
@Component
public class JwtAuthFilter implements GlobalFilter, Ordered {

    @Autowired
    private JwtUtil jwtUtil;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getPath().value();

        // 白名单路径放行
        if (isWhitelist(path)) {
            return chain.filter(exchange);
        }

        // 提取并校验 token
        String token = extractToken(exchange.getRequest());
        if (token == null || !jwtUtil.isValid(token)) {
            return unauthorized(exchange);
        }

        // 解析用户信息，传递到下游
        Long userId = jwtUtil.getUserId(token);
        ServerHttpRequest mutatedRequest = exchange.getRequest().mutate()
            .header("X-User-Id", String.valueOf(userId))
            .build();

        return chain.filter(exchange.mutate().request(mutatedRequest).build());
    }

    private Mono<Void> unauthorized(ServerWebExchange exchange) {
        exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
        exchange.getResponse().getHeaders().setContentType(MediaType.APPLICATION_JSON);
        byte[] bytes = "{\"code\":401,\"msg\":\"未登录\"}".getBytes();
        return exchange.getResponse().writeWith(
            Mono.just(exchange.getResponse().bufferFactory().wrap(bytes)));
    }
}
```

## 灰度发布

灰度发布：新版本先给部分用户试用，稳定后全量。

### 基于权重的灰度

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 稳定版本（80% 流量）
        - id: user-service-v1
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
            - Weight=group1, 80
        # 灰度版本（20% 流量）
        - id: user-service-v2
          uri: lb://user-service-v2
          predicates:
            - Path=/api/user/**
            - Weight=group1, 20
```

### 基于请求头的灰度

```yaml
spring:
  cloud:
    gateway:
      routes:
        # 灰度版本（带 version=v2 请求头）
        - id: user-service-v2
          uri: lb://user-service-v2
          predicates:
            - Path=/api/user/**
            - Header=version, v2
        # 稳定版本（默认）
        - id: user-service-v1
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
```

### 基于用户/参数的灰度

```yaml
# 指定用户走灰度
- id: user-service-gray
  uri: lb://user-service-v2
  predicates:
    - Path=/api/user/**
    - Query=userId, 1001,1002    # userId 为 1001/1002 的用户走灰度
```

## 应用场景实战

### 场景 1：统一网关配置

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - StripPrefix=1
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 50
                redis-rate-limiter.burstCapacity: 100
                key-resolver: "#{@ipKeyResolver}"

        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/order/**
          filters:
            - StripPrefix=1

      # 全局跨域
      globalcors:
        cors-configurations:
          '[/**]':
            allowedOrigins: "http://localhost:3000"
            allowedMethods: "*"
            allowedHeaders: "*"
            allowCredentials: true
```

### 场景 2：完整鉴权 + 限流网关

```java
@Component
@Order(0)
public class AuthFilter implements GlobalFilter {

    private static final List<String> WHITELIST = List.of(
        "/api/auth/login", "/api/auth/register", "/actuator/health"
    );

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getPath().value();

        if (WHITELIST.stream().anyMatch(path::startsWith)) {
            return chain.filter(exchange);
        }

        String token = exchange.getRequest().getHeaders().getFirst("Authorization");
        if (token == null) {
            return writeError(exchange, 401, "未登录");
        }

        // 校验 token 并注入用户信息
        return chain.filter(exchange);
    }
}
```

### 场景 3：灰度发布（权重 + 请求头）

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-gray
          uri: lb://user-service-gray
          predicates:
            - Path=/api/user/**
            - Header=gray, true           # 带 gray:true 请求头走灰度

        - id: user-stable
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
            - Weight=stable, 90           # 其余 90% 稳定版
```

## 最佳实践与踩坑记录

### 最佳实践

1. **网关只做横切关注点**。鉴权、限流、日志、跨域放在网关，业务逻辑放服务。

2. **路由用服务名（lb://）而非固定地址**。配合服务发现，实例动态变化无需改配置。

3. **限流 key 合理设计**。按 IP 限流防刷，按用户限流防单个用户滥用，按接口限流保护热点。

4. **鉴权后把用户信息传递到下游**。通过请求头（X-User-Id）传递，下游服务不再重复解析 token。

5. **白名单路径明确**。登录、健康检查、公开接口要放行，否则全被拦截。

### 踩坑记录

**坑 1：StripPrefix 后路径不对**

```yaml
filters:
  - StripPrefix=1    # /api/user/list → /user/list
  # 如果下游服务也带 /api 前缀，会出现路径不匹配
```

StripPrefix 去掉的段数要和下游服务的实际路径匹配。

**坑 2：GlobalFilter 顺序混乱**

```java
@Component
@Order(-1)   // 顺序要和内置 Filter 协调
public class AuthFilter implements GlobalFilter { ... }
```

自定义 GlobalFilter 的 @Order 要和内置 Filter 协调，鉴权 Filter 要在路由 Filter 之前。

**坑 3：响应式 API 的错误使用**

```java
// 错误：在 Gateway 里用阻塞 API
public Mono<Void> filter(...) {
    Thread.sleep(1000);   // 阻塞！Gateway 是响应式的，不能阻塞
    return chain.filter(exchange);
}
```

Gateway 基于 WebFlux，不能用阻塞 API（Thread.sleep、JDBC 等），要响应式。

**坑 4：限流没有配 Redis**

```text
RequestRateLimiter 依赖 Redis，没配 Redis 或没引入 reactive Redis，
限流不生效或报错
```

限流需要 `spring-boot-starter-data-redis-reactive` 依赖。

**坑 5：跨域配置不生效**

```yaml
spring:
  cloud:
    gateway:
      globalcors:
        cors-configurations:
          '[/**]':    # 必须是 [/ **]，不是 /**
            allowedOrigins: "*"
```

跨域路径配置要写 `[/**]`，且允许携带 Cookie 时不能用 `*`。

**坑 6：网关转发的请求体丢失**

```java
// 在 GlobalFilter 中读取了请求体（body），但没重新包装，
// 导致下游服务读不到 body
String body = exchange.getAttribute("cachedRequestBody");
```

读取请求体后要缓存并重新包装，否则下游读不到 body。用 `ReadBodyPredicateFactory` 或缓存装饰器。
