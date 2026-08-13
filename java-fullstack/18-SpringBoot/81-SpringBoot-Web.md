---
title: Spring Boot Web
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-boot, web, spring-mvc, webflux, rest, json, upload, download, cors, websocket, sse]
---

# Spring Boot Web

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [内嵌 Web 服务器](#内嵌-web-服务器)
- [Spring MVC 与 WebFlux](#spring-mvc-与-webflux)
- [JSON 配置](#json-配置)
- [文件上传与下载](#文件上传与下载)
- [CORS 跨域](#cors-跨域)
- [WebSocket](#websocket)
- [SSE 服务器推送](#sse-服务器推送)
- [静态资源](#静态资源)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Boot Web 是 Spring Boot 对 Web 开发的集成——内嵌服务器 + Spring MVC 自动配置，让 Web 应用无需部署到外部容器即可运行。

```text
spring-boot-starter-web 包含：
1. 内嵌 Tomcat（默认，可换成 Jetty/Undertow）
2. Spring MVC 自动配置
3. Jackson（JSON 序列化）
4. 参数校验（Hibernate Validator）
```

## 内嵌 Web 服务器

### 默认服务器与切换

```xml
<!-- 默认内嵌 Tomcat -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<!-- 切换到 Jetty：先排除 Tomcat，再加 Jetty -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jetty</artifactId>
</dependency>
```

### 服务器配置

```yaml
server:
  port: 8080                       # 端口
  address: 0.0.0.0                 # 绑定地址
  servlet:
    context-path: /api             # 上下文路径
  compression:
    enabled: true                  # 开启 GZIP 压缩
    min-response-size: 1024
  tomcat:
    max-threads: 200               # 最大线程数
    accept-count: 100              # 等待队列长度
    max-connections: 10000         # 最大连接数
    connection-timeout: 20000      # 连接超时
```

### 优雅停机

```yaml
server:
  shutdown: graceful                # 优雅停机
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s  # 停机等待时间
```

优雅停机让正在处理的请求完成后再关闭，避免请求中断。

## Spring MVC 与 WebFlux

Spring Boot 支持两种 Web 编程模型：命令式的 Spring MVC 和响应式的 WebFlux。

### 对比

| 维度 | Spring MVC | WebFlux |
|------|-----------|---------|
| 编程模型 | 命令式（阻塞） | 响应式（非阻塞） |
| 底层服务器 | Tomcat/Jetty/Undertow | Netty（默认） |
| 线程模型 | 每请求一线程（线程池） | 事件循环（少量线程） |
| 返回类型 | 对象 / ResponseEntity | Mono / Flux |
| 数据库 | JDBC（阻塞） | R2DBC（非阻塞） |
| 适用场景 | 传统 CRUD、事务密集 | 高并发、I/O 密集、流式 |
| 依赖 | spring-boot-starter-web | spring-boot-starter-webflux |

### WebFlux 基础

```java
@RestController
public class ReactiveController {

    @Autowired
    private ReactiveUserRepository repository;

    // 返回单个元素（异步）
    @GetMapping("/users/{id}")
    public Mono<User> getUser(@PathVariable Long id) {
        return repository.findById(id);
    }

    // 返回多个元素（流式）
    @GetMapping("/users")
    public Flux<User> listUsers() {
        return repository.findAll();
    }

    // 响应式处理请求体
    @PostMapping("/users")
    public Mono<User> createUser(@RequestBody Mono<User> userMono) {
        return userMono.flatMap(repository::save);
    }
}
```

### 响应式类型

```java
Mono<T>   // 0 或 1 个元素的异步序列（类似 Optional）
Flux<T>   // 0 到 N 个元素的异步流（类似 List/Stream）

Mono.just(1)                    // 单元素
Mono.empty()                    // 空
Flux.fromIterable(list)         // 集合转 Flux
Flux.range(1, 10)               // 1 到 10 的流
flux.map(x -> x * 2)            // 转换
flux.filter(x -> x > 5)         // 过滤
flux.flatMap(...)               // 扁平映射（异步）
mono.zip(mono2)                 // 合并
```

### 何时选 WebFlux

```text
选 WebFlux：
- 高并发、大量 I/O（如网关、代理、实时数据推送）
- 需要流式处理（SSE、WebSocket）
- 整个技术栈都是响应式的（WebFlux + R2DBC + Reactor）

选 Spring MVC：
- 传统业务 CRUD
- 依赖 JDBC / JPA（阻塞的数据库访问）
- 团队熟悉命令式编程
```

大多数业务系统用 Spring MVC 就够了，WebFlux 适合特定场景。

## JSON 配置

### Jackson 全局配置

```yaml
spring:
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss    # 日期格式
    time-zone: GMT+8                     # 时区
    default-property-inclusion: non_null # null 字段不序列化
    serialization:
      write-dates-as-timestamps: false   # 日期不转时间戳
    deserialization:
      fail-on-unknown-properties: false  # 忽略未知字段
    generator:
      write-bigdecimal-as-plain: true    # BigDecimal 不转科学计数法
```

### 自定义 ObjectMapper

```java
@Configuration
public class JacksonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> {
            builder.simpleDateFormat("yyyy-MM-dd HH:mm:ss");
            builder.serializers(new LocalDateTimeSerializer(
                DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
            builder.deserializers(new LocalDateTimeDeserializer(
                DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
            builder.serializationInclusion(JsonInclude.Include.NON_NULL);
            builder.failOnUnknownProperties(false);
        };
    }
}
```

### 常见 JSON 注解

```java
public class User {
    @JsonIgnore                    // 忽略字段（密码）
    private String password;

    @JsonProperty("user_name")     // 自定义字段名
    private String userName;

    @JsonFormat(pattern = "yyyy-MM-dd")  // 字段级日期格式
    private LocalDate birthday;

    @JsonInclude(JsonInclude.Include.NON_NULL)  // 字段级 null 不输出
    private String nickname;
}
```

## 文件上传与下载

### 文件上传

```java
@RestController
@RequestMapping("/api/files")
public class FileController {

    // 单文件上传
    @PostMapping("/upload")
    public Result upload(@RequestParam("file") MultipartFile file) throws IOException {
        String originalName = file.getOriginalFilename();
        long size = file.getSize();
        String contentType = file.getContentType();

        // 保存到指定目录
        Path targetPath = Paths.get("/opt/uploads/" + originalName);
        file.transferTo(targetPath);

        return Result.success("/uploads/" + originalName);
    }

    // 多文件上传
    @PostMapping("/upload/batch")
    public Result uploadBatch(@RequestParam("files") MultipartFile[] files) {
        for (MultipartFile file : files) {
            // 处理每个文件
        }
        return Result.success();
    }
}
```

### 上传大小限制

```yaml
spring:
  servlet:
    multipart:
      max-file-size: 10MB        # 单文件最大
      max-request-size: 50MB     # 请求总大小
      enabled: true
      file-size-threshold: 2KB    # 超过则写入磁盘
      location: /tmp/upload-tmp   # 临时目录
```

### 文件下载

```java
@RestController
@RequestMapping("/api/files")
public class FileController {

    @GetMapping("/download/{filename}")
    public ResponseEntity<Resource> download(@PathVariable String filename) throws IOException {
        // 防路径穿越
        if (filename.contains("..") || filename.contains("/")) {
            return ResponseEntity.badRequest().build();
        }

        Path filePath = Paths.get("/opt/uploads/" + filename);
        Resource resource = new FileSystemResource(filePath);

        // 中文文件名编码
        String encodedName = URLEncoder.encode(filename, "UTF-8")
            .replaceAll("\\+", "%20");

        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .header("Content-Disposition",
                "attachment; filename=\"" + encodedName + "\"; filename*=UTF-8''" + encodedName)
            .body(resource);
    }
}
```

### 大文件下载（流式）

```java
@GetMapping("/download/large/{filename}")
public ResponseEntity<StreamingResponseBody> downloadLarge(@PathVariable String filename) {
    StreamingResponseBody stream = outputStream -> {
        try (InputStream input = Files.newInputStream(Paths.get("/opt/uploads/" + filename))) {
            byte[] buffer = new byte[8192];
            int len;
            while ((len = input.read(buffer)) != -1) {
                outputStream.write(buffer, 0, len);
            }
        }
    };
    return ResponseEntity.ok()
        .header("Content-Disposition", "attachment; filename=\"" + filename + "\"")
        .body(stream);
}
```

## CORS 跨域

CORS（Cross-Origin Resource Sharing）允许浏览器跨域访问 API。

### 全局配置

```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")           // 允许跨域的路径
            .allowedOrigins("http://localhost:3000", "http://example.com")  // 允许的来源
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")       // 允许的方法
            .allowedHeaders("*")                 // 允许的请求头
            .allowCredentials(true)              // 允许携带 Cookie
            .maxAge(3600);                       // 预检请求缓存时间
    }
}
```

### 注解方式

```java
@RestController
@RequestMapping("/api/users")
@CrossOrigin(origins = "http://localhost:3000", maxAge = 3600)
public class UserController { }

// 方法级别
@GetMapping
@CrossOrigin(origins = "http://localhost:3000")
public List<User> list() { ... }
```

### CORS 原理

```text
简单请求（GET/POST + 简单头）：
浏览器直接发请求，响应带 Access-Control-Allow-Origin 头

预检请求（PUT/DELETE/自定义头）：
浏览器先发 OPTIONS 请求（Preflight），服务器确认后才发真实请求
```

**注意**：`allowedOrigins("*")` 与 `allowCredentials(true)` 不能同时使用——携带凭证时不能允许所有来源。

## WebSocket

WebSocket 提供全双工、长连接的实时通信。

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-websocket</artifactId>
</dependency>
```

### 配置 WebSocket 端点

```java
@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(new MyWebSocketHandler(), "/ws")
            .setAllowedOrigins("*");
    }
}
```

### 处理类

```java
public class MyWebSocketHandler extends TextWebSocketHandler {

    private static final Set<WebSocketSession> sessions = ConcurrentHashMap.newKeySet();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);  // 连接建立，加入会话池
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        String payload = message.getPayload();
        // 广播给所有客户端
        for (WebSocketSession s : sessions) {
            s.sendMessage(new TextMessage("收到：" + payload));
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);  // 连接关闭，移出会话池
    }
}
```

### 前端连接

```javascript
const ws = new WebSocket("ws://localhost:8080/ws");
ws.onopen = () => ws.send("Hello");
ws.onmessage = (event) => console.log(event.data);
```

### 应用场景

```text
- 实时聊天
- 实时通知推送
- 协作编辑
- 实时行情（股票、加密货币）
```

## SSE 服务器推送

SSE（Server-Sent Events）是单向的服务器推送技术，比 WebSocket 简单。

### 与 WebSocket 对比

| 维度 | WebSocket | SSE |
|------|-----------|-----|
| 通信方向 | 双向 | 单向（服务器→客户端） |
| 协议 | 独立协议（ws://） | 基于 HTTP |
| 复杂度 | 高 | 低 |
| 自动重连 | 需手动 | 浏览器自动 |
| 适用场景 | 聊天、协作 | 通知、进度推送 |

### Spring MVC 实现 SSE

```java
@RestController
@RequestMapping("/api/events")
public class SseController {

    // 返回 SseEmitter，单向推送
    @GetMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter(30_000L);  // 30 秒超时

        // 异步推送数据
        executorService.execute(() -> {
            try {
                for (int i = 0; i < 10; i++) {
                    emitter.send(SseEmitter.event()
                        .name("message")
                        .data("第 " + i + " 条消息"));
                    Thread.sleep(1000);
                }
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }
}
```

### WebFlux 实现 SSE（更简洁）

```java
@RestController
public class ReactiveSseController {

    @GetMapping(value = "/api/events/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> stream() {
        // 每秒推送一条，共 10 条
        return Flux.interval(Duration.ofSeconds(1))
            .map(i -> ServerSentEvent.<String>builder()
                .event("message")
                .data("第 " + i + " 条消息")
                .build())
            .take(10);
    }
}
```

### 前端接收

```javascript
const eventSource = new EventSource("/api/events/stream");
eventSource.onmessage = (event) => console.log(event.data);
```

## 静态资源

### 默认静态资源目录

```text
classpath:/static/
classpath:/public/
classpath:/resources/
classpath:/META-INF/resources/
```

```text
访问 http://localhost:8080/logo.png
会查找 classpath:/static/logo.png
```

### 自定义静态资源

```yaml
spring:
  web:
    resources:
      static-locations: classpath:/static/, file:/opt/static/
      cache:
        period: 3600     # 缓存时间（秒）
```

### 静态资源映射

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 将 /files/** 映射到文件系统 /opt/uploads/
        registry.addResourceHandler("/files/**")
            .addResourceLocations("file:/opt/uploads/");
    }
}
```

## 应用场景实战

### 场景 1：带 CORS 和 JSON 配置的 REST 服务

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000")
            .allowedMethods("*")
            .allowedHeaders("*")
            .allowCredentials(true);
    }
}
```

```yaml
spring:
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: GMT+8
    default-property-inclusion: non_null
```

### 场景 2：实时通知推送（SSE）

```java
@Service
public class NotificationService {

    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();

    // 用户订阅
    public SseEmitter subscribe(String userId) {
        SseEmitter emitter = new SseEmitter(0L);  // 不超时
        emitters.put(userId, emitter);

        emitter.onCompletion(() -> emitters.remove(userId));
        emitter.onTimeout(() -> emitters.remove(userId));
        return emitter;
    }

    // 推送通知
    public void push(String userId, String message) {
        SseEmitter emitter = emitters.get(userId);
        if (emitter != null) {
            try {
                emitter.send(SseEmitter.event().data(message));
            } catch (IOException e) {
                emitters.remove(userId);
            }
        }
    }
}
```

### 场景 3：WebSocket 聊天室

```java
public class ChatWebSocketHandler extends TextWebSocketHandler {

    private static final Set<WebSocketSession> sessions = ConcurrentHashMap.newKeySet();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);
        broadcast("用户 " + session.getId() + " 加入聊天室");
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        broadcast(message.getPayload());  // 广播消息
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);
        broadcast("用户 " + session.getId() + " 离开聊天室");
    }

    private void broadcast(String message) {
        for (WebSocketSession s : sessions) {
            try {
                s.sendMessage(new TextMessage(message));
            } catch (IOException e) {
                // 发送失败，忽略
            }
        }
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **REST 接口统一 JSON 配置**。日期格式、时区、null 处理在 application.yml 全局配置，避免每个字段加注解。

2. **文件上传限制大小**。防止恶意上传超大文件耗尽磁盘和内存。

3. **下载路径做防穿越校验**。`filename` 参数必须过滤 `..` 和 `/`，防止任意文件读取。

4. **CORS 精确配置来源**。不要 `allowedOrigins("*")` 同时 `allowCredentials(true)`，生产环境明确列出允许的来源。

5. **SSE 连接要管理生命周期**。用 Map 管理 emitter，onCompletion/onTimeout 时移除，防止内存泄漏。

### 踩坑记录

**坑 1：WebFlux 和 Spring MVC 同时引入冲突**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>
<!-- 同时引入，Spring Boot 默认以 Spring MVC 为准，但会警告 -->
```

两者不能同时作为主 Web 框架。要么只用 MVC，要么只用 WebFlux。

**坑 2：文件上传超过大小限制报 413**

```text
MaxUploadSizeExceededException: Maximum upload size exceeded
```

默认限制单文件 1MB、总请求 10MB。上传大文件需要调大 `spring.servlet.multipart.max-file-size`。

**坑 3：@CrossOrigin 在 @RestController 上不生效**

```java
// @CrossOrigin 用在类上对类内所有方法生效
// 但如果方法上也有 @CrossOrigin 且配置冲突，方法级覆盖类级
// 另外 @CrossOrigin 不能处理 Filter 层的跨域（如 Spring Security 的 CORS）
```

需要跨域的场景统一在 CorsConfig 全局配置，避免分散。

**坑 4：SSE 被代理缓冲**

```text
Nginx 等反向代理默认会缓冲响应，SSE 的流式推送会失效。
需要在 Nginx 配置：
proxy_buffering off;
X-Accel-Buffering: no;
```

**坑 5：WebSocket 握手被拦截**

```text
WebSocket 握手是 HTTP 请求，如果 Spring Security 或拦截器拦截了 /ws 路径，
握手会失败。需要在 Security 配置中放行 WebSocket 端点。
```

**坑 6：content-type 不匹配导致 415**

```http
POST /api/user
Content-Type: text/plain      ← 错误
{"name": "张三"}

Content-Type: application/json  ← 正确
```

`@RequestBody` 要求 `application/json`，前端要正确设置 Content-Type。
