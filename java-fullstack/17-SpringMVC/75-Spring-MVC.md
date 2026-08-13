---
title: Spring MVC
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-mvc, dispatcherservlet, controller, requestmapping, handleradapter, handlermapping, interceptor, converter, formatter]
---

# Spring MVC

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [DispatcherServlet](#dispatcherservlet)
- [请求处理流程](#请求处理流程)
- [Controller 与 @RequestMapping](#controller-与-requestmapping)
- [参数绑定](#参数绑定)
- [返回值处理](#返回值处理)
- [HandlerMapping 与 HandlerAdapter](#handlermapping-与-handleradapter)
- [Converter 与 Formatter](#converter-与-formatter)
- [Interceptor 拦截器](#interceptor-拦截器)
- [Filter 与 Interceptor 的关系](#filter-与-interceptor-的关系)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring MVC 是 Spring Framework 的 Web 模块，基于 Servlet 之上构建的 MVC 框架。它的核心是前端控制器（Front Controller）模式——所有请求先经过 DispatcherServlet，再由它分发给具体的 Controller。

```text
MVC 分工：
Model（模型）    —— 业务数据 + 业务逻辑（Service/DAO 层）
View（视图）     —— 页面渲染（JSP、Thymeleaf、JSON 序列化）
Controller（控制器） —— 接收请求、调用 Service、返回 Model 和 View
```

Spring MVC 是 Spring 全家桶 Web 开发的基石，Spring Boot 的 `spring-boot-starter-web` 就是基于它自动配置的。

## DispatcherServlet

DispatcherServlet 是 Spring MVC 的前端控制器，**它本身就是一个 Servlet**（继承自 HttpServlet）。所有请求都先到达它，再由它协调分发。

### 核心职责

1. 接收所有 HTTP 请求
2. 根据请求信息（URL、方法、参数）找到对应的 Handler（Controller 方法）
3. 调用 Handler 处理请求
4. 将 Handler 的返回结果渲染为响应

### 在 web.xml 中注册（传统方式）

```xml
<web-app>
    <servlet>
        <servlet-name>dispatcher</servlet-name>
        <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
        <init-param>
            <param-name>contextConfigLocation</param-name>
            <param-value>/WEB-INF/dispatcher-servlet.xml</param-value>
        </init-param>
        <load-on-startup>1</load-on-startup>
    </servlet>

    <servlet-mapping>
        <servlet-name>dispatcher</servlet-name>
        <url-pattern>/</url-pattern>
    </servlet-mapping>
</web-app>
```

### 编程式注册（Servlet 3.0+）

```java
public class MyWebApplicationInitializer implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext servletContext) {
        // 创建 Spring 容器
        AnnotationConfigWebApplicationContext context =
            new AnnotationConfigWebApplicationContext();
        context.register(WebConfig.class);

        // 注册 DispatcherServlet
        DispatcherServlet servlet = new DispatcherServlet(context);
        ServletRegistration.Dynamic registration =
            servletContext.addServlet("dispatcher", servlet);
        registration.setLoadOnStartup(1);
        registration.addMapping("/");
    }
}
```

Spring Boot 中由 `DispatcherServletAutoConfiguration` 自动完成注册，无需手动配置。

### url-pattern 为 / 的含义

```xml
<url-pattern>/</url-pattern>       <!-- 拦截所有请求（除了 .jsp），推荐 -->
<url-pattern>/*</url-pattern>      <!-- 拦截所有请求（含 .jsp），不推荐 -->
<url-pattern>/api/*</url-pattern>  <!-- 只拦截 /api/ 下的请求 -->
```

`/` 是 Spring MVC 的标准配置——它匹配所有请求，但静态资源（如 .css、.js）需要额外配置放行。

## 请求处理流程

一次 HTTP 请求在 Spring MVC 中的完整流转：

```text
1. 浏览器发送请求
      ↓
2. DispatcherServlet.service() 接收请求
      ↓
3. HandlerMapping 根据 URL 找到 Handler（Controller 方法）+ Interceptor 链
      ↓
4. HandlerAdapter 适配并调用 Handler（Controller 方法）
      ↓
5. 参数解析（HandlerMethodArgumentResolver）—— 将请求参数绑定到方法参数
      ↓
6. Controller 方法执行，返回结果（ModelAndView / 对象 / ResponseEntity）
      ↓
7. 返回值处理（HandlerMethodReturnValueHandler）—— 视图渲染 / JSON 序列化
      ↓
8. 响应写回浏览器
```

每一步都有对应的扩展点（HandlerMapping、HandlerAdapter、ArgumentResolver、ReturnValueHandler），这是 Spring MVC 灵活性的来源。

## Controller 与 @RequestMapping

### @Controller 与 @RestController

```java
@Controller  // 标记为控制器，配合视图渲染
public class UserController {

    @RequestMapping("/user")
    public String userPage(Model model) {  // 返回视图名
        model.addAttribute("user", userService.find(1L));
        return "user/detail";  // 转发到 user/detail 视图
    }
}

@RestController  // = @Controller + @ResponseBody
public class UserApiController {

    @RequestMapping("/api/user")
    public User user() {  // 返回对象，自动序列化为 JSON
        return userService.find(1L);
    }
}
```

```java
// @RestController 的定义
@Controller
@ResponseBody
public @interface RestController {}
```

### @RequestMapping 注解

`@RequestMapping` 是核心的请求映射注解，可以标注在类和方法上：

```java
@RestController
@RequestMapping("/api/users")  // 类级别：统一前缀
public class UserController {

    // 方法级别：细化路径，最终路径 = /api/users/list
    @RequestMapping("/list")
    public List<User> list() { ... }
}
```

常用属性：

```java
@RequestMapping(
    value = "/user",              // 路径（可多个：{"/user", "/member"}）
    method = RequestMethod.GET,   // HTTP 方法（可多个）
    params = "type=admin",        // 请求参数限制
    headers = "X-Requested-With=XMLHttpRequest",  // 请求头限制
    consumes = "application/json", // Content-Type 限制
    produces = "application/json"  // Accept 限制
)
```

### 方法级别快捷注解

```java
@GetMapping("/user/{id}")      // = @RequestMapping(method=GET)
@PostMapping("/user")          // = @RequestMapping(method=POST)
@PutMapping("/user/{id}")      // = @RequestMapping(method=PUT)
@DeleteMapping("/user/{id}")   // = @RequestMapping(method=DELETE)
@PatchMapping("/user/{id}")    // = @RequestMapping(method=PATCH)
```

### URL 通配符

```java
@GetMapping("/files/*")       // 匹配 /files/abc，不匹配 /files/a/b
@GetMapping("/files/**")      // 匹配 /files/a/b/c 任意层级
@GetMapping("/files/{id}")    // 路径变量
@GetMapping("/files/{id:\\d+}")  // 路径变量 + 正则约束
```

## 参数绑定

Spring MVC 提供丰富的注解将请求参数绑定到方法参数。

### @RequestParam —— 查询参数/表单参数

```java
@GetMapping("/search")
public Result search(
    @RequestParam("keyword") String keyword,      // 必填参数
    @RequestParam(value = "page", defaultValue = "1") int page,  // 默认值
    @RequestParam(value = "size", required = false) Integer size, // 可选
    @RequestParam List<String> tags               // 多值参数 ?tags=a&tags=b
) { ... }
```

不写 `@RequestParam` 时，简单类型参数（String、int、Integer 等）也会自动从请求参数绑定：

```java
@GetMapping("/search")
public Result search(String keyword, int page) { ... }  // 等价于 @RequestParam
```

### @PathVariable —— 路径变量

```java
@GetMapping("/users/{id}")
public User getUser(@PathVariable("id") Long id) { ... }

// 变量名一致时可省略 value
@GetMapping("/users/{id}/orders/{orderId}")
public Order getOrder(@PathVariable Long id, @PathVariable Long orderId) { ... }

// 多路径变量
@GetMapping("/{category}/{subCategory}")
public Result list(@PathVariable String category, @PathVariable String subCategory) { ... }
```

### @RequestBody —— 请求体（JSON）

```java
@PostMapping("/users")
public User createUser(@RequestBody User user) {
    // 将 JSON 请求体反序列化为 User 对象（通过 HttpMessageConverter）
    return userService.save(user);
}

// 配合 @Valid 校验
@PostMapping("/users")
public User createUser(@RequestBody @Valid User user, BindingResult bindingResult) {
    if (bindingResult.hasErrors()) {
        // 处理校验错误
    }
    return userService.save(user);
}
```

### @RequestHeader / @CookieValue

```java
@GetMapping("/info")
public Result info(
    @RequestHeader("User-Agent") String userAgent,
    @RequestHeader(value = "X-Token", required = false) String token,
    @CookieValue(value = "JSESSIONID", required = false) String sessionId
) { ... }
```

### @ModelAttribute —— 对象绑定

自动将请求参数绑定到对象的属性（表单提交场景）：

```java
@PostMapping("/users")
public String createUser(@ModelAttribute User user) {
    // 自动将 ?name=张三&age=25 绑定到 user 的 name、age 属性
    userService.save(user);
    return "redirect:/users";
}
```

### 参数绑定总结表

| 注解 | 绑定来源 | 典型场景 |
|------|---------|---------|
| @RequestParam | 查询参数 / 表单 | ?keyword=xx |
| @PathVariable | URL 路径 | /users/{id} |
| @RequestBody | 请求体（JSON/XML） | POST JSON |
| @RequestHeader | 请求头 | Authorization、User-Agent |
| @CookieValue | Cookie | JSESSIONID |
| @ModelAttribute | 表单参数 → 对象 | 表单提交 |
| @RequestPart | multipart 部分 | 文件 + JSON 混合 |

## 返回值处理

### 返回视图名（@Controller）

```java
@Controller
public class PageController {

    @GetMapping("/users")
    public String listUsers(Model model) {
        model.addAttribute("users", userService.findAll());
        return "user/list";  // 视图名，由 ViewResolver 解析为具体视图
    }

    // 返回 ModelAndView（同时指定视图和数据）
    @GetMapping("/user/{id}")
    public ModelAndView userDetail(@PathVariable Long id) {
        ModelAndView mav = new ModelAndView("user/detail");
        mav.addObject("user", userService.find(id));
        return mav;
    }

    // 重定向
    @PostMapping("/user")
    public String createUser(@ModelAttribute User user) {
        userService.save(user);
        return "redirect:/users";  // 重定向
    }

    // 转发
    @GetMapping("/forward")
    public String forward() {
        return "forward:/internal/page";  // 服务器内部转发
    }
}
```

### 返回对象（@RestController / @ResponseBody）

```java
@RestController
public class UserApiController {

    @GetMapping("/user/{id}")
    public User getUser(@PathVariable Long id) {  // 自动序列化为 JSON
        return userService.find(id);
    }

    @GetMapping("/user/{id}")
    @ResponseBody  // 在 @Controller 中单独标注
    public User getUser2(@PathVariable Long id) {
        return userService.find(id);
    }
}
```

### ResponseEntity —— 完全控制响应

```java
@RestController
public class UserApiController {

    @GetMapping("/user/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        User user = userService.find(id);
        if (user == null) {
            return ResponseEntity.notFound().build();  // 404
        }
        return ResponseEntity.ok(user);  // 200 + body
    }

    @PostMapping("/user")
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User saved = userService.save(user);
        // 201 + 自定义头
        return ResponseEntity.status(HttpStatus.CREATED)
            .header("X-Resource-Id", String.valueOf(saved.getId()))
            .body(saved);
    }

    @GetMapping("/download")
    public ResponseEntity<byte[]> download() {
        byte[] data = fileService.read();
        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .header("Content-Disposition", "attachment; filename=\"report.pdf\"")
            .body(data);
    }
}
```

### 返回类型对比

| 返回类型 | 说明 | 注解要求 |
|---------|------|---------|
| String | 视图名 / 重定向 | @Controller |
| ModelAndView | 视图 + 数据 | @Controller |
| 对象（User/List） | JSON 序列化 | @RestController 或 @ResponseBody |
| ResponseEntity | 完全控制状态码/头/体 | @RestController 或 @ResponseBody |
| void | 无响应体（配合 HttpServletResponse） | - |

## HandlerMapping 与 HandlerAdapter

HandlerMapping 和 HandlerAdapter 是 Spring MVC 的核心扩展点，理解它们有助于理解请求分发机制。

### HandlerMapping —— 请求到 Handler 的映射

HandlerMapping 负责根据请求找到处理它的 Handler：

```java
public interface HandlerMapping {
    HandlerExecutionChain getHandler(HttpServletRequest request) throws Exception;
}
```

返回的 `HandlerExecutionChain` 包含 Handler 和 Interceptor 链。

常见的 HandlerMapping 实现：

| 实现类 | 用途 |
|--------|------|
| RequestMappingHandlerMapping | 处理 @RequestMapping 注解（现代主流） |
| SimpleUrlHandlerMapping | URL 到 Handler 的简单映射 |
| BeanNameUrlHandlerMapping | 按 Bean 名称映射（/user 对应名为 /user 的 Bean） |
| RouterFunctionMapping | 函数式路由（WebFlux 风格） |

### HandlerAdapter —— 调用 Handler

HandlerAdapter 负责真正调用 Handler 并处理返回值：

```java
public interface HandlerAdapter {
    boolean supports(Object handler);       // 是否支持该 Handler
    ModelAndView handle(HttpServletRequest req, HttpServletResponse resp, Object handler) throws Exception;
    long getLastModified(HttpServletRequest req, Object handler);
}
```

| 实现类 | 用途 |
|--------|------|
| RequestMappingHandlerAdapter | 处理 @RequestMapping 方法（现代主流） |
| HttpRequestHandlerAdapter | 处理 HttpRequestHandler |
| SimpleControllerHandlerAdapter | 处理 Controller 接口实现（旧式） |

### 为什么需要 Adapter 模式

Handler 的类型多种多样（@RequestMapping 方法、HttpRequestHandler、Controller 接口实现），DispatcherServlet 通过 HandlerAdapter 的 `supports()` 判断能否处理，解耦了 DispatcherServlet 和具体 Handler 类型。

```java
// DispatcherServlet 的核心逻辑（简化）
protected void doDispatch(HttpServletRequest request, HttpServletResponse response) {
    // 1. 找到 Handler + Interceptor 链
    HandlerExecutionChain chain = handlerMapping.getHandler(request);

    // 2. 找到能处理该 Handler 的 Adapter
    HandlerAdapter adapter = getHandlerAdapter(chain.getHandler());

    // 3. 调用 Adapter 处理请求
    ModelAndView mav = adapter.handle(request, response, chain.getHandler());

    // 4. 渲染视图
    processDispatchResult(request, response, chain, mav);
}
```

### 自定义 HandlerMapping 场景

```java
// 场景：根据数据库中的路由配置动态映射 URL
@Component
public class DynamicUrlHandlerMapping implements HandlerMapping {

    @Override
    public HandlerExecutionChain getHandler(HttpServletRequest request) throws Exception {
        String path = request.getRequestURI();
        // 从数据库查询 URL 对应的处理器
        Handler handler = routeTable.findHandler(path);
        return new HandlerExecutionChain(handler);
    }
}
```

## Converter 与 Formatter

Spring 提供了类型转换体系，用于把请求中的字符串参数转换为目标类型。

### Converter —— 类型转换

```java
public interface Converter<S, T> {
    T convert(S source);
}
```

```java
// 自定义 Converter：String → 自定义类型
@Component
public class StringToUserConverter implements Converter<String, User> {
    @Override
    public User convert(String source) {
        // "1:张三" → User(id=1, name=张三)
        String[] parts = source.split(":");
        return new User(Long.parseLong(parts[0]), parts[1]);
    }
}
```

注册 Converter：

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(new StringToUserConverter());
    }
}
```

### Formatter —— 格式化（字符串 ↔ 对象，支持本地化）

Formatter 是 Converter 的特化，专用于字符串和对象之间的转换，支持 Locale：

```java
public interface Formatter<T> extends Printer<T>, Parser<T> {
    // Printer<T>.print(T object, Locale locale)  → 对象转字符串
    // Parser<T>.parse(String text, Locale locale) → 字符串转对象
}
```

```java
// 自定义日期格式化器
public class DateFormatter implements Formatter<Date> {
    private final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Override
    public String print(Date object, Locale locale) {
        return formatter.format(object.toInstant().atZone(ZoneId.systemDefault()).toLocalDate());
    }

    @Override
    public Date parse(String text, Locale locale) throws ParseException {
        return Date.from(LocalDate.parse(text, formatter)
            .atStartOfDay(ZoneId.systemDefault()).toInstant());
    }
}
```

### 内置的 Converter 和 Formatter

Spring 内置了大量 Converter（String → int/Long/Date/枚举等），以及 `@DateTimeFormat`、`@NumberFormat` 注解：

```java
@RestController
public class OrderController {

    // 自动将 "2026-08-12" 转换为 LocalDate
    @GetMapping("/orders")
    public Result list(@RequestParam @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate date) { ... }

    // 自动将 "1,234.56" 转换为数字
    @GetMapping("/amount")
    public Result amount(@RequestParam @NumberFormat(pattern = "#,##0.00") BigDecimal amount) { ... }
}
```

### Converter vs Formatter

| 维度 | Converter | Formatter |
|------|-----------|-----------|
| 转换方向 | 任意类型间 | 字符串 ↔ 对象 |
| 本地化 | 不支持 | 支持 Locale |
| 典型场景 | 任意类型互转 | 字符串格式化（日期、数字） |
| 接口 | Converter<S,T> | Formatter<T> |

## Interceptor 拦截器

HandlerInterceptor 是 Spring MVC 的拦截器，在 Controller 方法执行前后插入逻辑。

### HandlerInterceptor 接口

```java
public interface HandlerInterceptor {

    // Controller 方法执行前
    default boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        return true;  // true=放行，false=拦截（不调用 Controller）
    }

    // Controller 方法执行后、视图渲染前
    default void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler, ModelAndView modelAndView) throws Exception {
    }

    // 整个请求处理完成后（视图渲染后）
    default void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
    }
}
```

### 注册拦截器

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new AuthInterceptor())
            .addPathPatterns("/api/**")        // 拦截路径
            .excludePathPatterns("/api/login", "/api/register");  // 排除路径
    }
}
```

### 完整拦截器示例

```java
@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        // 检查登录态
        HttpSession session = request.getSession(false);
        if (session == null || session.getAttribute("user") == null) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/json;charset=UTF-8");
            try {
                response.getWriter().write("{\"code\":401,\"msg\":\"未登录\"}");
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
            return false;  // 拦截
        }
        return true;  // 放行
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        // 清理 ThreadLocal、记录耗时等
    }
}
```

### 执行顺序

```text
Filter.doFilter() 前置
  → Interceptor.preHandle()
    → Controller 方法
  → Interceptor.postHandle()
  → 视图渲染
  → Interceptor.afterCompletion()
Filter.doFilter() 后置
```

多个拦截器按注册顺序执行：preHandle 按注册顺序，postHandle/afterCompletion 按逆序。

## Filter 与 Interceptor 的关系

| 维度 | Filter | Interceptor |
|------|--------|-------------|
| 规范 | Servlet 标准 | Spring MVC 框架 |
| 依赖 | 只依赖 Servlet API | 依赖 Spring 容器 |
| 作用范围 | 所有请求（含静态资源） | 仅 DispatcherServlet 处理的请求 |
| 执行时机 | 进入 DispatcherServlet 之前 | Controller 方法前后 |
| 能力 | 可以修改请求/响应 | 可以访问 Handler（Controller 方法）、ModelAndView |
| 配置 | @WebFilter / FilterRegistrationBean | addInterceptors |
| 典型场景 | 编码、安全、跨域、日志 | 权限校验、登录检查、耗时统计 |

```text
请求 → Filter → DispatcherServlet → Interceptor → Controller
```

选择原则：**与业务相关的拦截用 Interceptor**（能拿到 Controller 方法信息），**与基础设施相关的用 Filter**（编码、安全等，先于 Spring MVC 生效）。

## 应用场景实战

### 场景 1：完整的 REST 用户管理接口

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public List<User> list(
            @RequestParam(value = "page", defaultValue = "1") int page,
            @RequestParam(value = "size", defaultValue = "10") int size) {
        return userService.findByPage(page, size);
    }

    @GetMapping("/{id}")
    public ResponseEntity<User> get(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<User> create(@RequestBody @Valid User user) {
        User saved = userService.save(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    @PutMapping("/{id}")
    public ResponseEntity<User> update(@PathVariable Long id, @RequestBody User user) {
        user.setId(id);
        return ResponseEntity.ok(userService.update(user));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

### 场景 2：文件上传与下载

```java
@RestController
@RequestMapping("/api/files")
public class FileController {

    // 文件上传
    @PostMapping("/upload")
    public Result upload(@RequestParam("file") MultipartFile file) {
        String originalName = file.getOriginalFilename();
        long size = file.getSize();
        String contentType = file.getContentType();

        // 保存文件
        String savedPath = storageService.store(file);
        return Result.success(savedPath);
    }

    // 多文件上传
    @PostMapping("/upload/batch")
    public Result uploadBatch(@RequestParam("files") MultipartFile[] files) {
        for (MultipartFile file : files) {
            storageService.store(file);
        }
        return Result.success();
    }

    // 文件下载
    @GetMapping("/download/{filename}")
    public ResponseEntity<Resource> download(@PathVariable String filename) {
        Resource file = storageService.load(filename);
        return ResponseEntity.ok()
            .header("Content-Disposition",
                "attachment; filename=\"" + filename + "\"")
            .body(file);
    }
}
```

### 场景 3：耗时统计拦截器

```java
@Component
public class PerformanceInterceptor implements HandlerInterceptor {

    private static final ThreadLocal<Long> START_TIME = new ThreadLocal<>();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        START_TIME.set(System.currentTimeMillis());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        try {
            long cost = System.currentTimeMillis() - START_TIME.get();
            String uri = request.getRequestURI();
            String method = request.getMethod();

            if (cost > 1000) {
                log.warn("慢请求：{} {} cost {}ms", method, uri, cost);
            } else {
                log.info("{} {} cost {}ms", method, uri, cost);
            }
        } finally {
            START_TIME.remove();  // 必须清理，防止内存泄漏
        }
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Controller 保持薄**。Controller 只做参数接收、校验、调用 Service、返回结果，业务逻辑全部在 Service 层。

2. **REST API 用 @RestController，页面跳转用 @Controller**。清晰区分前后端分离接口和视图渲染。

3. **路径变量和查询参数分工明确**。资源标识用路径变量（/users/{id}），过滤/分页/排序用查询参数（?page=1&sort=name）。

4. **返回类型优先用 ResponseEntity**。需要精确控制状态码（201、204、404）时，ResponseEntity 比裸对象更规范。

5. **拦截器里清理 ThreadLocal**。在 afterCompletion 的 finally 块中 remove，防止线程池复用导致的数据污染和内存泄漏。

### 踩坑记录

**坑 1：@RequestParam 参数名与变量名不一致**

```java
@GetMapping("/search")
public Result search(@RequestParam("q") String keyword) { ... }
// 请求 ?keyword=xx 绑定不上，必须 ?q=xx
```

当参数名和变量名不一致时，必须显式写 `@RequestParam("q")`。省略时 Spring 按变量名绑定。

**坑 2：@PathVariable 与路径冲突**

```java
@GetMapping("/users/{id}")       // 匹配 /users/123
@GetMapping("/users/me")          // 匹配 /users/me —— 但会被 /users/{id} 抢先匹配
```

Spring 优先匹配精确路径，但不同版本行为可能不同。为避免歧义，用正则约束路径变量：`@GetMapping("/users/{id:\\d+}")`。

**坑 3：POST 请求体为空**

```java
@PostMapping("/user")
public Result create(@RequestBody User user) { ... }
// 前端没传 body 或 Content-Type 不对，报 400 Bad Request（HttpMessageNotReadableException）
```

`@RequestBody` 要求 Content-Type 为 application/json，且 body 非空。空 body 会抛异常，需全局异常处理器兜底。

**坑 4：返回字符串被当成视图名**

```java
@Controller
public class ApiController {
    @GetMapping("/status")
    public String status() {
        return "ok";  // 被当成视图名 "ok"，不是响应体 "ok"！
    }
}
```

在 `@Controller` 中返回 String 会被解析为视图名。要返回字符串作为响应体，用 `@ResponseBody` 或 `@RestController`。

**坑 5：@RequestBody 和 @RequestParam 混用**

```java
@PostMapping("/user")
public Result create(@RequestBody User user, @RequestParam String source) { ... }
// @RequestBody 消费整个请求体，@RequestParam 从查询参数取值，两者可以共存
// 但表单参数（application/x-www-form-urlencoded）不能和 @RequestBody 同时用
```

`@RequestBody` 读取的是请求体（JSON），`@RequestParam` 读取的是查询参数或表单参数。两者来源不同，可以共存，但要注意 Content-Type。

**坑 6：拦截器注册顺序与排除路径**

```java
registry.addInterceptor(new AuthInterceptor())
    .addPathPatterns("/api/**")
    .excludePathPatterns("/api/login");
// excludePathPatterns 的路径必须是 addPathPatterns 的子集，否则不生效
```

排除路径要精确，且是拦截路径的子集。

**坑 7：HandlerInterceptor 中 response 已提交**

```java
@Override
public void postHandle(...) {
    // 如果 Controller 已经写入了 response（如直接 getWriter().write），
    // 这里再操作 response 会抛 IllegalStateException
}
```

Controller 通过 `HttpServletResponse` 直接写响应后，response 已提交，postHandle 中不能再修改。JSON 序列化场景下用 `@RestController` 而非直接写 response 可以避免。
