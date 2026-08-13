---
title: OpenFeign
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [openfeign, feign, 服务调用, 编码器, 解码器, 拦截器, 超时, 重试]
---

# OpenFeign

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [声明式服务调用](#声明式服务调用)
- [编码器与解码器](#编码器与解码器)
- [拦截器](#拦截器)
- [超时配置](#超时配置)
- [重试机制](#重试机制)
- [日志配置](#日志配置)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

OpenFeign 是 Spring Cloud 的声明式 HTTP 客户端，让服务间调用像调用本地方法一样简单。

```text
传统 RestTemplate 调用：
RestTemplate template = new RestTemplate();
String url = "http://user-service/users/" + id;
User user = template.getForObject(url, User.class);
// 手动拼 URL、手动负载均衡、手动解析

OpenFeign 调用：
@FeignClient("user-service")
public interface UserClient {
    @GetMapping("/users/{id}")
    User getUser(@PathVariable Long id);
}
// 只需声明接口，调用像本地方法
```

```text
OpenFeign 核心优势：
1. 声明式 —— 接口 + 注解，无需手动拼 URL
2. 自动负载均衡 —— 配合 LoadBalancer，自动选择实例
3. 自动序列化 —— 对象自动转 JSON
4. 集成熔断 —— 配合 Sentinel/Resilience4j
```

## 声明式服务调用

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
```

### 启用 Feign

```java
@SpringBootApplication
@EnableFeignClients   // 启用 Feign 客户端扫描
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}
```

### 定义 Feign 客户端

```java
// 服务提供者（user-service）
@RestController
@RequestMapping("/users")
public class UserController {
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) { ... }

    @PostMapping
    public User createUser(@RequestBody User user) { ... }
}

// 服务消费者（order-service）—— Feign 客户端
@FeignClient(name = "user-service")   // 服务名（配合服务发现）
public interface UserClient {

    @GetMapping("/users/{id}")        // 对应提供者的接口
    User getUser(@PathVariable("id") Long id);

    @PostMapping("/users")
    User createUser(@RequestBody User user);

    @GetMapping("/users")
    List<User> listUsers(@RequestParam("page") int page, @RequestParam("size") int size);
}
```

### 使用 Feign 客户端

```java
@Service
public class OrderService {

    @Autowired
    private UserClient userClient;   // 注入 Feign 客户端

    public Order createOrder(Long userId) {
        // 调用像本地方法，实际走 HTTP 到 user-service
        User user = userClient.getUser(userId);
        // ...
    }
}
```

### @FeignClient 属性

```java
@FeignClient(
    name = "user-service",              // 服务名（必填）
    url = "http://localhost:8081",      // 直接指定 URL（绕过服务发现）
    path = "/api",                      // 统一路径前缀
    fallback = UserClientFallback.class,     // 降级类
    fallbackFactory = UserClientFallbackFactory.class,  // 降级工厂（可获取异常）
    configuration = FeignConfig.class   // 自定义配置类
)
public interface UserClient { ... }
```

## 编码器与解码器

Feign 的编码器（Encoder）和解码器（Decoder）负责对象的序列化和反序列化。

### 默认编码解码

```text
默认：
Encoder —— SpringEncoder（基于 Jackson，对象 → JSON）
Decoder —— SpringDecoder（基于 Jackson，JSON → 对象）
```

### 自定义配置

```java
@Configuration
public class FeignConfig {

    @Bean
    public Encoder feignEncoder() {
        // 自定义 Jackson 配置
        ObjectMapper mapper = new ObjectMapper();
        mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
        return new SpringEncoder(() -> new HttpMessageConverters(
            new MappingJackson2HttpMessageConverter(mapper)));
    }

    @Bean
    public Decoder feignDecoder() {
        return new SpringDecoder(() -> new HttpMessageConverters(
            new MappingJackson2HttpMessageConverter()));
    }
}
```

### 日期格式处理

```java
@Bean
public Encoder feignEncoder() {
    ObjectMapper mapper = new ObjectMapper();
    // 配置日期格式
    mapper.setDateFormat(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"));
    return new JacksonEncoder(mapper);
}
```

## 拦截器

Feign 拦截器在请求发送前处理请求，常用于传递认证信息、公共请求头。

### 定义拦截器

```java
@Configuration
public class FeignInterceptorConfig {

    @Bean
    public RequestInterceptor requestInterceptor() {
        return requestTemplate -> {
            // 传递认证信息到下游服务
            String token = getCurrentToken();
            requestTemplate.header("Authorization", "Bearer " + token);

            // 传递链路追踪 ID
            String traceId = MDC.get("traceId");
            requestTemplate.header("X-Trace-Id", traceId);

            // 传递用户信息
            String userId = getCurrentUserId();
            requestTemplate.header("X-User-Id", userId);
        };
    }

    private String getCurrentToken() {
        // 从 SecurityContext 或 ThreadLocal 获取
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth != null ? auth.getName() : "";
    }
}
```

### 拦截器的典型用途

```text
1. 传递认证信息（token）到下游
2. 传递链路追踪 ID（traceId）
3. 传递用户上下文（userId、租户 ID）
4. 添加公共请求头（来源标识、版本号）
```

## 超时配置

### 配置超时

```yaml
spring:
  cloud:
    openfeign:
      client:
        config:
          default:                    # 全局默认
            connectTimeout: 3000      # 连接超时（毫秒）
            readTimeout: 5000         # 读取超时（毫秒）
          user-service:               # 指定服务
            connectTimeout: 2000
            readTimeout: 10000
```

```java
// 或编程式配置
@Configuration
public class FeignTimeoutConfig {
    @Bean
    public Request.Options options() {
        return new Request.Options(3, TimeUnit.SECONDS,   // 连接超时
                                    5, TimeUnit.SECONDS); // 读取超时
    }
}
```

### 超时时间设置建议

```text
连接超时：2-3 秒（建立连接很快）
读取超时：按业务，普通接口 5 秒，慢接口 10-30 秒
注意：超时时间要小于网关/上游的超时，否则链路超时不一致
```

## 重试机制

### Feign 重试配置

```yaml
spring:
  cloud:
    openfeign:
      client:
        config:
          default:
            retryer: com.example.config.CustomRetryer  # 自定义重试器
```

```java
// 自定义重试器
@Bean
public Retryer feignRetryer() {
    // 重试 3 次，间隔 1 秒、2 秒、4 秒（倍增）
    return new Retryer.Default(1000, 1000, 3);
}

// 不重试
@Bean
public Retryer feignRetryer() {
    return Retryer.NEVER_RETRY;
}
```

### 重试的注意事项

```text
1. Feign 默认不重试（NEVER_RETRY）
2. 重试只对幂等操作（GET）安全，POST 可能重复执行
3. 重试要配合幂等设计（幂等键）
4. 重试可能放大下游压力
```

## 日志配置

### 配置日志级别

```yaml
logging:
  level:
    com.example.client.UserClient: DEBUG   # Feign 客户端接口的日志级别
```

```java
@Configuration
public class FeignLogConfig {
    @Bean
    public Logger.Level feignLoggerLevel() {
        return Logger.Level.FULL;   // NONE/BASIC/HEADERS/FULL
    }
}
```

| 日志级别 | 内容 |
|---------|------|
| NONE | 不记录（默认） |
| BASIC | 方法、URL、状态码、耗时 |
| HEADERS | BASIC + 请求/响应头 |
| FULL | HEADERS + 请求/响应体 |

## 应用场景实战

### 场景 1：订单服务调用用户服务

```java
// user-service 提供接口
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}

// order-service 定义 Feign 客户端
@FeignClient(name = "user-service", path = "/api/users")
public interface UserClient {
    @GetMapping("/{id}")
    User getUser(@PathVariable("id") Long id);
}

// 使用
@Service
public class OrderService {
    @Autowired
    private UserClient userClient;

    public OrderDetail getOrderDetail(Long orderId) {
        Order order = orderMapper.findById(orderId);
        User user = userClient.getUser(order.getUserId());  // 远程调用
        return new OrderDetail(order, user);
    }
}
```

### 场景 2：带降级的 Feign 调用

```java
// 降级类（fallback）
@Component
public class UserClientFallback implements UserClient {
    @Override
    public User getUser(Long id) {
        // 降级：返回默认用户
        User user = new User();
        user.setId(id);
        user.setUsername("未知用户");
        return user;
    }
}

@FeignClient(name = "user-service", fallback = UserClientFallback.class)
public interface UserClient {
    @GetMapping("/{id}")
    User getUser(@PathVariable("id") Long id);
}
```

```java
// 降级工厂（可获取异常原因）
@Component
public class UserClientFallbackFactory implements FallbackFactory<UserClient> {
    @Override
    public UserClient create(Throwable cause) {
        return id -> {
            log.error("调用 user-service 失败：{}", cause.getMessage());
            User user = new User();
            user.setId(id);
            user.setUsername("服务不可用");
            return user;
        };
    }
}

@FeignClient(name = "user-service", fallbackFactory = UserClientFallbackFactory.class)
public interface UserClient { ... }
```

### 场景 3：传递认证信息的 Feign 调用

```java
@Configuration
public class FeignAuthConfig {

    @Bean
    public RequestInterceptor authInterceptor() {
        return template -> {
            // 从当前请求上下文传递 token 到下游
            ServletRequestAttributes attributes =
                (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attributes != null) {
                String token = attributes.getRequest().getHeader("Authorization");
                if (token != null) {
                    template.header("Authorization", token);
                }
            }
        };
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Feign 接口和提供者接口保持契约一致**。路径、参数、类型必须对应，建议用契约测试保证。

2. **复杂服务调用要配降级**。下游故障时返回默认值或缓存，避免雪崩。

3. **认证信息通过拦截器统一传递**。不要每个方法手动传 token。

4. **超时时间合理设置**。连接超时短、读取超时按业务，且小于网关超时。

5. **日志级别按需开启**。FULL 级别日志量大，只在排查问题时开，生产用 BASIC。

### 踩坑记录

**坑 1：@FeignClient 的 path 和方法的路径拼接**

```java
@FeignClient(name = "user-service", path = "/api/users")
public interface UserClient {
    @GetMapping("/{id}")   // 最终路径 = /api/users/{id}
    User getUser(@PathVariable Long id);

    @GetMapping("list")    // 错误：缺少 /，路径可能拼接错误
    List<User> list();
}
```

path 和方法的路径拼接要注意 `/`，最终路径 = path + 方法路径。

**坑 2：@PathVariable 缺少 value**

```java
@GetMapping("/{id}")
User getUser(@PathVariable Long id);   // 参数名和路径变量一致，OK

@GetMapping("/{userId}")
User getUser(@PathVariable Long id);   // 错误！路径变量是 userId，参数是 id
// 编译可能不报错，但运行时路径变量绑定失败
```

当参数名和路径变量名不一致时，必须写 `@PathVariable("userId")`。

**坑 3：Feign 的 GET 请求用 @RequestBody**

```java
@GetMapping("/search")
List<User> search(@RequestBody SearchParam param);  // GET 带 body，很多框架不支持
```

GET 请求带 body 不被广泛支持（网关、代理可能丢弃）。查询参数用 @RequestParam 或 @SpringQueryMap。

**坑 4：复杂对象参数 GET 请求**

```java
@GetMapping("/search")
List<User> search(UserQuery query);   // 复杂对象默认作为 body 发送
// GET 请求应该用 @SpringQueryMap
@GetMapping("/search")
List<User> search(@SpringQueryMap UserQuery query);  // 展开为查询参数
```

GET 请求的复杂参数用 @SpringQueryMap 展开为查询参数。

**坑 5：Feign 与 Sentinel 集成缺依赖**

```text
Feign 的 fallback 生效需要引入 Sentinel 或 Resilience4j，
只有 @FeignClient 的 fallback 属性但没有熔断依赖，降级不生效
```

fallback 需要配合熔断组件（Sentinel/Resilience4j）+ `feign.sentinel.enabled=true`。

**坑 6：Feign 客户端接口被重复扫描**

```java
// Feign 客户端接口放在主包下，被 @ComponentScan 扫描，
// 又被 @EnableFeignClients 扫描，可能重复注册
```

Feign 客户端接口不要加 @Component 注解，只被 @EnableFeignClients 扫描。
