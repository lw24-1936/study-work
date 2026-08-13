---
title: Servlet
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [servlet, servlet-container, filter, listener, httpservlet, session, cookie, servletcontext, java-web]
---

# Servlet

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Servlet Container](#servlet-container)
- [Servlet 生命周期](#servlet-生命周期)
- [Servlet 体系结构](#servlet-体系结构)
- [HttpServlet](#httpservlet)
- [HttpServletRequest](#httpservletrequest)
- [HttpServletResponse](#httpservletresponse)
- [ServletConfig 与 ServletContext](#servletconfig-与-servletcontext)
- [Filter 过滤器](#filter-过滤器)
- [Listener 监听器](#listener-监听器)
- [Session 会话管理](#session-会话管理)
- [Cookie](#cookie)
- [请求转发与重定向](#请求转发与重定向)
- [文件上传与下载](#文件上传与下载)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Servlet 是 Java Web 的核心——运行在 Servlet Container（如 Tomcat）中的 Java 类，处理 HTTP 请求并生成响应。它是 Spring MVC 的底层基石，DispatcherServlet 本质上就是一个 Servlet。

Servlet 的职责：接收请求 -> 处理业务逻辑 -> 返回响应。它通过标准的 `javax.servlet` / `jakarta.servlet` API 与容器交互，开发者只需关注 `service()` 方法即可。

```text
浏览器 --HTTP--> Servlet Container --请求对象--> Servlet.service() --> 响应对象 --> 浏览器
```

Servlet 规范演变：
- Servlet 4.0（Jakarta EE 8）：支持 HTTP/2 Server Push
- Servlet 5.0（Jakarta EE 9）：包名从 javax.servlet 变为 jakarta.servlet
- Servlet 6.0（Jakarta EE 10）：支持虚拟线程

## Servlet Container

Servlet Container（也叫 Web 容器或 Servlet 引擎）是 Servlet 的运行环境。常见的实现：

| 容器 | 类型 | 说明 |
|------|------|------|
| Apache Tomcat | Servlet 容器 | 最广泛使用的开源实现，也是 Spring Boot 默认内嵌容器 |
| Jetty | Servlet 容器 | 轻量级，适合嵌入式场景 |
| Undertow | Servlet 容器 | Red Hat 开发，WildFly 默认，Spring Boot 也支持 |
| GlassFish | 完整 Jakarta EE 服务器 | 含 EJB、JPA 等全套规范 |
| WildFly | 完整 Jakarta EE 服务器 | 前身是 JBoss AS |

容器的核心职责：

1. **网络通信**：绑定端口，接收 HTTP 请求，解析请求头/请求体
2. **Servlet 生命周期管理**：加载类 -> 实例化 -> 初始化 -> 调用 service() -> 销毁
3. **多线程处理**：每个请求分配一个线程，调用 Servlet 的 service()
4. **安全管理**：身份验证、授权、SSL/TLS
5. **JSP 编译**：将 .jsp 文件编译为 Servlet 类
6. **资源管理**：数据库连接池、JNDI 绑定

```text
请求到达 Tomcat 的处理流程：

1. Connector（NIO/APR）接收 TCP 连接，解析 HTTP 报文
2. Engine 根据 Host 头选择虚拟主机
3. Host 匹配 Context（即项目路径，如 /myapp）
4. Context 中 Filter Chain 执行
5. 匹配到的 Servlet 执行 service()
6. 响应沿原路返回
```

## Servlet 生命周期

一个 Servlet 实例在容器中经历完整的生命周期，由容器以单实例多线程方式管理。

```
加载 --> 实例化 --> 初始化 --> 服务 --> 销毁
 |                   |         |        |
 |               init()    service() destroy()
```

### 阶段详解

**阶段 1：加载和实例化**

容器启动时（或首次请求到达时），通过反射创建 Servlet 实例：

```java
Class<?> clazz = Class.forName("com.example.MyServlet");
Servlet servlet = (Servlet) clazz.getDeclaredConstructor().newInstance();
```

默认情况下，Servlet 在**首次请求**时才加载（懒加载）。通过 `@WebServlet(loadOnStartup = 1)` 或 web.xml 中的 `<load-on-startup>` 可以改为容器启动时加载，值越小优先级越高。

**阶段 2：初始化 —— init()**

```java
public void init(ServletConfig config) throws ServletException {
    // 容器传入 ServletConfig，包含初始化参数
    super.init(config);  // 保存 config 引用
    // 做一次性初始化工作：加载配置、建立连接池等
}
```

init() 在 Servlet 生命周期中**只调用一次**，完成后 Servlet 才能处理请求。如果 init() 抛出 ServletException，Servlet 不会被投入使用。

**阶段 3：服务 —— service()**

```java
public void service(ServletRequest req, ServletResponse res) {
    // 每次请求都会调用
    // HttpServlet 实现中会将请求转为 HttpServletRequest/HttpServletResponse
    // 然后根据 HTTP 方法分发到 doGet()/doPost()/doPut()/doDelete() 等
}
```

service() 会被**多线程并发调用**。Servlet 实例是单例，所以不要使用实例变量保存请求状态——会导致线程安全问题。

**阶段 4：销毁 —— destroy()**

```java
public void destroy() {
    // 容器关闭或应用卸载时调用
    // 释放资源：关闭数据库连接、停止后台线程等
}
```

destroy() 也**只调用一次**。调用后 Servlet 实例被 GC 回收。

### 完整示例

```java
@WebServlet(name = "lifecycleServlet", urlPatterns = "/lifecycle", loadOnStartup = 1)
public class LifecycleServlet extends HttpServlet {

    public LifecycleServlet() {
        System.out.println("1. 构造方法");
    }

    @Override
    public void init() throws ServletException {
        System.out.println("2. init()");
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        System.out.println("3. service() -> doGet()");
    }

    @Override
    public void destroy() {
        System.out.println("4. destroy()");
    }
}
```

## Servlet 体系结构

```
javax.servlet.Servlet (接口)
    |
    +-- javax.servlet.GenericServlet (抽象类，协议无关)
            |
            +-- javax.servlet.http.HttpServlet (抽象类，HTTP 专用)
                    |
                    +-- 自定义 Servlet（如 DispatcherServlet）
```

### Servlet 接口

```java
public interface Servlet {
    void init(ServletConfig config) throws ServletException;
    ServletConfig getServletConfig();
    void service(ServletRequest req, ServletResponse res) throws ServletException, IOException;
    String getServletInfo();
    void destroy();
}
```

### GenericServlet

实现了 Servlet 和 ServletConfig 接口，提供默认实现，与协议无关。很少直接使用。

```java
public abstract class GenericServlet implements Servlet, ServletConfig {
    // 提供便捷的 log() 方法
    // 提供无参 init() 供子类重写（避免子类忘记调用 super.init(config)）
}
```

### 注册 Servlet 的方式

**方式 1：注解（Servlet 3.0+）**

```java
@WebServlet(
    name = "userServlet",
    urlPatterns = {"/user", "/user/*"},
    loadOnStartup = 1,
    initParams = {
        @WebInitParam(name = "encoding", value = "UTF-8")
    }
)
public class UserServlet extends HttpServlet { }
```

**方式 2：web.xml（传统方式）**

```xml
<servlet>
    <servlet-name>userServlet</servlet-name>
    <servlet-class>com.example.UserServlet</servlet-class>
    <init-param>
        <param-name>encoding</param-name>
        <param-value>UTF-8</param-value>
    </init-param>
    <load-on-startup>1</load-on-startup>
</servlet>
<servlet-mapping>
    <servlet-name>userServlet</servlet-name>
    <url-pattern>/user/*</url-pattern>
</servlet-mapping>
```

**方式 3：编程式注册（Servlet 3.0+，ServletContainerInitializer）**

```java
@HandlesTypes(MyServlet.class)
public class MyInitializer implements ServletContainerInitializer {
    @Override
    public void onStartup(Set<Class<?>> c, ServletContext ctx) {
        ServletRegistration.Dynamic servlet = ctx.addServlet("myServlet", MyServlet.class);
        servlet.addMapping("/my");
        servlet.setLoadOnStartup(1);
    }
}
```

Spring Boot 的 `DispatcherServletRegistrationBean` 内部也是用这种方式注册。

## HttpServlet

HttpServlet 是专门处理 HTTP 协议的 Servlet 基类。它的核心设计是 `service()` 方法根据 HTTP 方法分发到对应的 doXxx() 方法。

```java
protected void service(HttpServletRequest req, HttpServletResponse resp) {
    String method = req.getMethod();
    if ("GET".equals(method)) {
        doGet(req, resp);
    } else if ("POST".equals(method)) {
        doPost(req, resp);
    } else if ("PUT".equals(method)) {
        doPut(req, resp);
    } else if ("DELETE".equals(method)) {
        doDelete(req, resp);
    } else if ("HEAD".equals(method)) {
        doHead(req, resp);
    } else if ("OPTIONS".equals(method)) {
        doOptions(req, resp);
    } else if ("TRACE".equals(method)) {
        doTrace(req, resp);
    } else {
        resp.sendError(HttpServletResponse.SC_NOT_IMPLEMENTED);
    }
}
```

开发时只需重写对应的方法即可：

```java
@WebServlet("/api/users/*")
public class UserServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        // 查询用户
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        // 新增用户
    }

    @Override
    protected void doPut(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        // 更新用户
    }

    @Override
    protected void doDelete(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        // 删除用户
    }
}
```

**注意**：如果同时重写 `service(ServletRequest, ServletResponse)`，会覆盖 HttpServlet 的默认分发逻辑，所有请求都走你的 service()。一般不要这样做。

## HttpServletRequest

HttpServletRequest 封装了客户端发来的 HTTP 请求信息。它是 ServletRequest 的子接口。

### 获取请求行信息

```java
String method = req.getMethod();         // GET / POST / PUT / DELETE
String uri = req.getRequestURI();        // /myapp/api/users/123
String url = req.getRequestURL().toString();  // http://localhost:8080/myapp/api/users/123
String contextPath = req.getContextPath();    // /myapp
String servletPath = req.getServletPath();    // /api/users
String pathInfo = req.getPathInfo();          // /123（Servlet 映射为 /api/users/* 时）
String queryString = req.getQueryString();    // name=zhangsan&age=20
String protocol = req.getProtocol();          // HTTP/1.1
String scheme = req.getScheme();              // http / https
```

### 获取请求头

```java
String host = req.getHeader("Host");
String userAgent = req.getHeader("User-Agent");
String contentType = req.getContentType();
int contentLength = req.getContentLength();
String accept = req.getHeader("Accept");

// 遍历所有请求头
Enumeration<String> headerNames = req.getHeaderNames();
while (headerNames.hasMoreElements()) {
    String name = headerNames.nextElement();
    String value = req.getHeader(name);
}
```

### 获取请求参数

```java
// GET 的 ?name=zhangsan&age=20 和 POST 的 application/x-www-form-urlencoded 都能取到
String name = req.getParameter("name");
String[] hobbies = req.getParameterValues("hobby");  // 多值参数

// 遍历所有参数
Map<String, String[]> paramMap = req.getParameterMap();
// 注意：参数值始终是 String[]，因为一个参数名可能对应多个值
```

GET 和 POST 的参数获取方式相同，区别在于 GET 参数在 URL 后（有长度限制），POST 参数在请求体中。

### 获取请求体（JSON/XML/二进制）

```java
// 读取 JSON 请求体
BufferedReader reader = req.getReader();
StringBuilder sb = new StringBuilder();
String line;
while ((line = reader.readLine()) != null) {
    sb.append(line);
}
String jsonBody = sb.toString();

// 或使用 ServletInputStream 读取二进制数据
ServletInputStream inputStream = req.getInputStream();
byte[] buffer = new byte[1024];
int len;
ByteArrayOutputStream baos = new ByteArrayOutputStream();
while ((len = inputStream.read(buffer)) != -1) {
    baos.write(buffer, 0, len);
}
byte[] bodyBytes = baos.toByteArray();
```

**关键问题**：`getParameter()` 和 `getInputStream()` / `getReader()` 不能同时使用。如果在 multipart/form-data 请求中先调用了 `getParameter()`，后面再调用 `getInputStream()` 会读到空数据。因为容器在解析参数时已经消费了流。Spring MVC 的 `@RequestBody` 和 `@RequestParam` 也是同理的互斥关系。

### 请求属性（Request Attributes）

区别于参数（客户端传过来的），属性是由服务端代码设置的，用于在请求转发过程中传递数据：

```java
req.setAttribute("user", userObject);
User user = (User) req.getAttribute("user");
req.removeAttribute("user");
Enumeration<String> attrNames = req.getAttributeNames();
```

属性的生命周期仅限于当前请求，请求结束后自动清除。这是 Servlet 转发（Server 端内部跳转）的数据传递机制。

### 获取客户端信息

```java
String clientIP = req.getRemoteAddr();    // 客户端 IP
String clientHost = req.getRemoteHost();  // 客户端主机名
int clientPort = req.getRemotePort();     // 客户端端口

String serverName = req.getServerName();  // 接收请求的服务器主机名
int serverPort = req.getServerPort();     // 接收请求的端口
```

**注意**：如果前面有 Nginx 反向代理，`getRemoteAddr()` 返回的是 Nginx 的 IP，不是真实客户端 IP。正确做法是取 `X-Forwarded-For` 或 `X-Real-IP` 请求头。

## HttpServletResponse

HttpServletResponse 封装了服务器返回给客户端的 HTTP 响应。

### 设置响应行

```java
resp.setStatus(HttpServletResponse.SC_OK);           // 200
resp.setStatus(HttpServletResponse.SC_CREATED);      // 201
resp.setStatus(HttpServletResponse.SC_NO_CONTENT);   // 204
resp.setStatus(HttpServletResponse.SC_MOVED_TEMPORARILY); // 302
resp.setStatus(HttpServletResponse.SC_NOT_FOUND);    // 404
resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR); // 500

// 更简洁的方式
resp.sendError(HttpServletResponse.SC_NOT_FOUND, "用户不存在");
```

### 设置响应头

```java
resp.setContentType("application/json;charset=UTF-8");
resp.setCharacterEncoding("UTF-8");
resp.setContentLength(data.length);

// 缓存控制
resp.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");
resp.setHeader("Pragma", "no-cache");
resp.setHeader("Expires", "0");

// 跨域 CORS
resp.setHeader("Access-Control-Allow-Origin", "*");
resp.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE");
resp.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

// 自定义头
resp.setHeader("X-Powered-By", "MyApp/1.0");

// 添加而不是覆盖（同名头可以有多个值）
resp.addHeader("Set-Cookie", "sessionId=abc123; Path=/; HttpOnly");
```

### 获取输出流

```java
// 文本输出
resp.setContentType("text/html;charset=UTF-8");
PrintWriter writer = resp.getWriter();
writer.write("<html><body><h1>Hello</h1></body></html>");
writer.flush();

// 二进制输出（文件下载）
resp.setContentType("application/octet-stream");
ServletOutputStream out = resp.getOutputStream();
out.write(fileBytes);
out.flush();
```

**注意**：`getWriter()` 和 `getOutputStream()` 互斥，只能调用一个。重复调用会抛 IllegalStateException。

### 响应 JSON 示例

```java
resp.setContentType("application/json;charset=UTF-8");
PrintWriter writer = resp.getWriter();

User user = new User(1, "张三", "zhangsan@example.com");
ObjectMapper mapper = new ObjectMapper();
String json = mapper.writeValueAsString(user);

writer.write(json);
writer.flush();
```

### 中文乱码问题

Servlet 中文乱码的根本原因：浏览器和服务器对字符编码的理解不一致。解决方案分两个层面：

```java
// 方案 1：响应端设置（告诉浏览器用 UTF-8 解析）
resp.setContentType("text/html;charset=UTF-8");

// 方案 2：请求端设置（告诉容器用 UTF-8 解析请求参数）
req.setCharacterEncoding("UTF-8");

// 方案 3：全局设置 —— Filter 中统一处理（推荐）
@WebFilter("/*")
public class EncodingFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain) {
        req.setCharacterEncoding("UTF-8");
        resp.setContentType("text/html;charset=UTF-8");
        chain.doFilter(req, resp);
    }
}
```

**注意**：`req.setCharacterEncoding("UTF-8")` 只对 POST 的请求体有效。GET 的参数在 URL 中，编码由容器决定。Tomcat 8+ 默认 URIEncoding 为 UTF-8，不需要额外处理；Tomcat 7 及以下需要在 server.xml 的 Connector 中配置 `URIEncoding="UTF-8"`。

## ServletConfig 与 ServletContext

### ServletConfig —— 每个 Servlet 独享

ServletConfig 代表单个 Servlet 的配置信息，由容器在 init() 时传入。

```java
// 获取初始化参数（来自 @WebServlet(initParams=...) 或 web.xml <init-param>）
String encoding = getServletConfig().getInitParameter("encoding");
Enumeration<String> paramNames = getServletConfig().getInitParameterNames();

// 获取 ServletContext（整个 Web 应用共享的上下文）
ServletContext context = getServletConfig().getServletContext();

// 获取 Servlet 名称
String servletName = getServletConfig().getServletName();
```

### ServletContext —— 整个 Web 应用共享

ServletContext 代表整个 Web 应用的上下文，一个应用只有一个 ServletContext 实例。它是应用内全局数据共享的通道。

```java
ServletContext context = getServletContext();

// 获取上下文初始化参数（来自 web.xml <context-param>）
String appName = context.getInitParameter("appName");

// 全局属性（跨 Servlet 共享数据）
context.setAttribute("onlineCount", 100);
Integer count = (Integer) context.getAttribute("onlineCount");
context.removeAttribute("onlineCount");

// 获取应用信息
String contextPath = context.getContextPath();    // /myapp
String serverInfo = context.getServerInfo();      // Apache Tomcat/10.1.0
int majorVersion = context.getMajorVersion();     // Servlet 主版本号

// 获取真实路径（将虚拟路径转为文件系统路径）
String realPath = context.getRealPath("/WEB-INF/web.xml");
// 返回：/opt/tomcat/webapps/myapp/WEB-INF/web.xml

// 获取资源流（读取类路径下的文件）
InputStream is = context.getResourceAsStream("/WEB-INF/application.properties");

// 获取 MIME 类型
String mimeType = context.getMimeType("image.png");  // image/png
```

**ServletContext 域对象的生命周期**：服务器启动时创建、服务器关闭时销毁。范围是整个 Web 应用，所有 Servlet 和 JSP 都能访问。

## Filter 过滤器

Filter 是在请求到达 Servlet 之前和响应返回客户端之前执行的一段逻辑。它是责任链模式的典型应用。

### Filter 接口

```java
public interface Filter {
    // 初始化（容器启动时调用，只一次）
    default void init(FilterConfig filterConfig) throws ServletException {}

    // 核心方法：对请求和响应进行预处理/后处理
    void doFilter(ServletRequest request, ServletResponse response,
                  FilterChain chain) throws IOException, ServletException;

    // 销毁（容器关闭时调用，只一次）
    default void destroy() {}
}
```

### Filter 执行流程

```text
请求 --> Filter1.doFilter() --> Filter2.doFilter() --> ... --> Servlet.service()
            |                       |
            |<-- chain.doFilter() --|
            |                       |
响应 <-- 后处理逻辑            <-- 响应
```

关键：`chain.doFilter(request, response)` 是分水岭——之前的代码是**请求预处理**，之后的代码是**响应后处理**。

### Filter 注册

```java
@WebFilter(
    filterName = "authFilter",
    urlPatterns = {"/api/*", "/admin/*"},
    initParams = {
        @WebInitParam(name = "excludeUrls", value = "/api/login,/api/register")
    }
)
public class AuthFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpReq = (HttpServletRequest) req;
        HttpServletResponse httpResp = (HttpServletResponse) resp;

        // 请求预处理：检查登录状态
        HttpSession session = httpReq.getSession(false);
        if (session == null || session.getAttribute("user") == null) {
            httpResp.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            httpResp.getWriter().write("{\"code\":401,\"msg\":\"未登录\"}");
            return;  // 不放行——不调用 chain.doFilter()
        }

        // 放行到下一个 Filter 或 Servlet
        chain.doFilter(req, resp);

        // 响应后处理（在这里可以对响应再加工）
    }
}
```

### Filter 生命周期

与 Servlet 类似，但通过 FilterConfig 获取配置：

```java
public class MyFilter implements Filter {
    private FilterConfig config;

    @Override
    public void init(FilterConfig filterConfig) {
        this.config = filterConfig;
        String excludeUrls = config.getInitParameter("excludeUrls");
    }

    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain) {
        chain.doFilter(req, resp);
    }

    @Override
    public void destroy() {
        // 释放资源
    }
}
```

### FilterChain —— 过滤器链

FilterChain 由容器维护，按照 Filter 注册顺序依次执行。执行顺序规则：

- 注解 `@WebFilter`：按类名字典序
- web.xml：按 `<filter-mapping>` 声明顺序
- Spring Boot：通过 `@Order` 或 `Ordered` 接口控制

Filter 链的一个关键特性：任何一个 Filter 不放行（不调用 `chain.doFilter()`），请求就被终止，后续 Filter 和 Servlet 都不会执行。

### 常见 Filter 场景

```java
// 1. 编码过滤器
@WebFilter("/*")
public class EncodingFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain)
            throws IOException, ServletException {
        req.setCharacterEncoding("UTF-8");
        resp.setContentType("application/json;charset=UTF-8");
        chain.doFilter(req, resp);
    }
}

// 2. 耗时统计过滤器
@WebFilter("/*")
public class TimingFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain)
            throws IOException, ServletException {
        long start = System.currentTimeMillis();
        chain.doFilter(req, resp);
        long cost = System.currentTimeMillis() - start;
        String uri = ((HttpServletRequest) req).getRequestURI();
        System.out.println(uri + " cost " + cost + "ms");
    }
}

// 3. XSS 防御过滤器
@WebFilter("/*")
public class XssFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain)
            throws IOException, ServletException {
        // 将请求包装为 XSS 安全版本
        chain.doFilter(new XssRequestWrapper((HttpServletRequest) req), resp);
    }
}
```

### Filter 与 Spring Interceptor 的区别

| 维度 | Filter | Interceptor |
|------|--------|-------------|
| 规范 | Servlet 标准 | Spring 框架 |
| 依赖 | 只依赖 Servlet API | 依赖 Spring 容器 |
| 作用范围 | 所有请求（可按 URL 过滤） | 仅 DispatcherServlet 处理的请求 |
| 执行顺序 | Filter 先于 Interceptor | Interceptor 在 Filter 之后 |
| 能力 | 可以修改请求/响应 | 可以访问 Handler（Controller 方法） |
| 适用场景 | 编码、安全、日志、跨域 | 权限校验、日志记录、性能监控 |

## Listener 监听器

Listener 用于监听 Web 应用中的事件，基于观察者模式。

### 监听器分类

**1. 监听域对象创建和销毁（ServletContext / HttpSession / ServletRequest）**

```java
// ServletContext 生命周期
@WebListener
public class AppLifecycleListener implements ServletContextListener {
    @Override
    public void contextInitialized(ServletContextEvent sce) {
        // 应用启动
        System.out.println("应用启动");
    }

    @Override
    public void contextDestroyed(ServletContextEvent sce) {
        // 应用关闭
        System.out.println("应用关闭");
    }
}

// HttpSession 生命周期
@WebListener
public class SessionLifecycleListener implements HttpSessionListener {
    @Override
    public void sessionCreated(HttpSessionEvent se) {
        // 有用户登录
        ServletContext ctx = se.getSession().getServletContext();
        Integer count = (Integer) ctx.getAttribute("onlineCount");
        ctx.setAttribute("onlineCount", (count == null ? 0 : count) + 1);
    }

    @Override
    public void sessionDestroyed(HttpSessionEvent se) {
        // 用户登出/session 超时
    }
}

// ServletRequest 生命周期
@WebListener
public class RequestLifecycleListener implements ServletRequestListener {
    @Override
    public void requestInitialized(ServletRequestEvent sre) {
        // 请求到达
    }

    @Override
    public void requestDestroyed(ServletRequestEvent sre) {
        // 请求结束
    }
}
```

**2. 监听域对象属性变化**

```java
@WebListener
public class ContextAttributeListener implements ServletContextAttributeListener {
    @Override
    public void attributeAdded(ServletContextAttributeEvent event) {
        System.out.println("ServletContext 添加属性：" + event.getName());
    }

    @Override
    public void attributeReplaced(ServletContextAttributeEvent event) {
        System.out.println("ServletContext 替换属性：" + event.getName());
    }

    @Override
    public void attributeRemoved(ServletContextAttributeEvent event) {
        System.out.println("ServletContext 移除属性：" + event.getName());
    }
}
```

类似的还有 `HttpSessionAttributeListener` 和 `ServletRequestAttributeListener`。

**3. 监听 HttpSession 中的对象绑定（活化/钝化）**

```java
// 让 User 对象在 session 序列化到磁盘时得到通知
public class User implements HttpSessionActivationListener {
    @Override
    public void sessionWillPassivate(HttpSessionEvent se) {
        // 对象即将被钝化（写入磁盘/Redis）
    }

    @Override
    public void sessionDidActivate(HttpSessionEvent se) {
        // 对象从钝化状态恢复
    }
}
```

### 监听器注册

```java
// 注解方式
@WebListener
public class MyListener implements ServletContextListener { }

// web.xml 方式
// <listener>
//     <listener-class>com.example.MyListener</listener-class>
// </listener>
```

### 应用场景

- **初始化上下文**：在 `contextInitialized()` 中加载全局配置、预热缓存
- **在线人数统计**：在 `sessionCreated()` / `sessionDestroyed()` 中增减计数
- **请求耗时监控**：在 `RequestListener` 中记录开始/结束时间

## Session 会话管理

HTTP 是无状态协议——服务器无法直接知道两个请求是否来自同一个用户。Session（会话）机制解决了这个问题。

### Session 原理

```text
1. 用户首次请求，服务器创建 Session，生成唯一 sessionId
2. 服务器通过响应头 Set-Cookie: JSESSIONID=<sessionId> 将 sessionId 传给浏览器
3. 浏览器后续请求自动携带 Cookie: JSESSIONID=<sessionId>
4. 服务器根据 JSESSIONID 找到对应的 Session 对象
```

### HttpSession API

```java
// 获取 Session（如果没有则创建）
HttpSession session = req.getSession();

// 获取 Session（如果没有返回 null）
HttpSession session = req.getSession(false);

// 存储数据
session.setAttribute("user", user);
session.setAttribute("cart", shoppingCart);

// 读取数据
User user = (User) session.getAttribute("user");

// 移除数据
session.removeAttribute("user");

// 手动销毁 Session（如退出登录）
session.invalidate();

// Session 信息
String sessionId = session.getId();           // 唯一 ID
long creationTime = session.getCreationTime(); // 创建时间戳
long lastAccess = session.getLastAccessedTime(); // 最后访问时间
boolean isNew = session.isNew();               // 是否新创建

// 设置超时时间（秒），到期后容器自动销毁
session.setMaxInactiveInterval(30 * 60);  // 30 分钟
int maxInactive = session.getMaxInactiveInterval();
```

### Session 超时配置

```xml
<!-- web.xml -->
<session-config>
    <session-timeout>30</session-timeout>  <!-- 分钟 -->
</session-config>
```

```java
// 代码方式
session.setMaxInactiveInterval(1800);  // 秒
```

**注意**：Session 超时后，容器会销毁该 Session 对象，触发 `HttpSessionListener.sessionDestroyed()`。但是 Session 中绑定的对象并不会被立即回收——除非没有其他引用了。

### Session 安全问题

1. **Session 固定攻击（Session Fixation）**：登录后应创建新 Session
```java
// 登录成功后，废弃旧 Session，创建新 Session
HttpSession oldSession = req.getSession(false);
if (oldSession != null) {
    oldSession.invalidate();
}
HttpSession newSession = req.getSession(true);
newSession.setAttribute("user", user);
```

2. **JSESSIONID 泄露**：通过 URL 重写传递 Session ID 时可能被中间人截获，应避免

3. **分布式 Session**：Tomcat 默认 Session 存储在内存中，集群环境下需要使用 Redis 等共享存储。Spring Session 是解决方案。

### 禁用 Cookie 时的 Session 追踪

如果客户端禁用了 Cookie，容器会使用 URL 重写来传递 sessionId：

```java
// 对 URL 追加 ;jsessionid=xxx
String encodedUrl = resp.encodeURL("/myapp/user/profile");
// 结果：/myapp/user/profile;jsessionid=ABC123
```

`encodeURL()` 会自动判断是否需要追加 jsessionid（如果请求中有 Cookie 则不加）。

## Cookie

Cookie 是存储在客户端（浏览器）的小段数据（通常 < 4KB），每次请求时浏览器会自动携带。

### Cookie API

```java
// 创建 Cookie
Cookie cookie = new Cookie("username", "zhangsan");
cookie.setMaxAge(60 * 60 * 24 * 7);  // 7 天（秒），负数=浏览器关闭即失效，0=立即删除
cookie.setPath("/");                   // 哪些路径会携带此 Cookie
cookie.setDomain("example.com");       // 域名限制
cookie.setHttpOnly(true);              // 禁止 JS 读取（防 XSS）
cookie.setSecure(true);               // 仅 HTTPS 传输
resp.addCookie(cookie);

// 读取 Cookie
Cookie[] cookies = req.getCookies();
if (cookies != null) {
    for (Cookie c : cookies) {
        if ("username".equals(c.getName())) {
            String username = c.getValue();
            break;
        }
    }
}

// 删除 Cookie（设置 MaxAge=0）
Cookie deleteCookie = new Cookie("username", "");
deleteCookie.setMaxAge(0);
deleteCookie.setPath("/");
resp.addCookie(deleteCookie);
```

### Cookie vs Session 对比

| 维度 | Cookie | Session |
|------|--------|---------|
| 存储位置 | 客户端浏览器 | 服务器端 |
| 安全性 | 低（可被篡改） | 高（服务端不可见） |
| 容量 | 约 4KB | 无限制（受内存限制） |
| 性能 | 每次请求自动携带 | 需要查询服务端存储 |
| 跨域 | 受域名限制 | 可跨域（通过共享存储） |
| 生命周期 | 可设 MaxAge | 默认 30 分钟超时 |
| 用途 | 记住我、偏好设置、追踪 | 登录状态、购物车、临时数据 |

### 常见 Cookie 属性

```text
Set-Cookie: JSESSIONID=ABC123; Path=/myapp; HttpOnly; Secure; SameSite=Lax
```

- `HttpOnly`：禁止 JS 通过 document.cookie 读取，防御 XSS
- `Secure`：仅 HTTPS 连接下传输
- `SameSite`：Strict（严格，跨站不发送）/ Lax（默认，导航请求发送）/ None（允许跨站，需配合 Secure）

## 请求转发与重定向

### 请求转发（Forward）

服务器内部将请求转发给另一个资源处理，客户端无感知——浏览器地址栏不变。

```java
// 方式 1：通过 RequestDispatcher
req.getRequestDispatcher("/target").forward(req, resp);

// 方式 2：通过 ServletContext（路径必须以 / 开头）
getServletContext().getRequestDispatcher("/target").forward(req, resp);
```

**关键特性**：
- 只有一次请求，地址栏不变
- 可以访问 WEB-INF 下的资源
- 可以共享 request 属性（通过 `setAttribute()`）
- 只能转发到同应用内的资源

### 重定向（Redirect）

服务器告诉浏览器去访问另一个 URL，浏览器会发起第二次请求——地址栏会变。

```java
// 方式 1：标准
resp.sendRedirect("/myapp/target");

// 方式 2：手动设置
resp.setStatus(HttpServletResponse.SC_MOVED_TEMPORARILY);
resp.setHeader("Location", "/myapp/target");
```

**关键特性**：
- 两次请求，地址栏会变
- 可以重定向到外部 URL
- request 属性会丢失（新请求）
- 不能访问 WEB-INF 下的资源

### 转发 vs 重定向

| 维度 | 转发（Forward） | 重定向（Redirect） |
|------|----------------|-------------------|
| 请求次数 | 1 次 | 2 次 |
| 地址栏 | 不变 | 变为目标 URL |
| 数据共享 | request 属性可传递 | 丢失（需要 session/URL 参数） |
| 跨域 | 不能 | 可以 |
| WEB-INF | 可以访问 | 不能访问 |
| 速度 | 快（服务器内部） | 慢（多一次网络往返） |
| 使用场景 | 登录后跳转到首页 | POST 后跳转（PRG 模式防重复提交） |

**PRG（Post-Redirect-Get）模式**：表单 POST 提交后，重定向到结果页面。用户刷新时不会重复提交表单。

```java
protected void doPost(HttpServletRequest req, HttpServletResponse resp) {
    // 处理表单
    saveUser(req);

    // 重定向，防重复提交
    resp.sendRedirect(req.getContextPath() + "/success.jsp");
}
```

## 文件上传与下载

### 文件上传

Servlet 3.0 引入了 `@MultipartConfig` 注解支持文件上传。

```java
@WebServlet("/upload")
@MultipartConfig(
    maxFileSize = 10 * 1024 * 1024,      // 单个文件最大 10MB
    maxRequestSize = 50 * 1024 * 1024,   // 整个请求最大 50MB
    fileSizeThreshold = 1024 * 1024      // 超过 1MB 写入磁盘临时文件
)
public class UploadServlet extends HttpServlet {

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        // 获取上传的文件
        Part filePart = req.getPart("file");  // 对应 <input type="file" name="file">
        String fileName = filePart.getSubmittedFileName();
        long fileSize = filePart.getSize();
        String contentType = filePart.getContentType();

        // 保存到指定目录
        String savePath = getServletContext().getRealPath("/uploads/");
        File dir = new File(savePath);
        if (!dir.exists()) dir.mkdirs();

        filePart.write(savePath + File.separator + fileName);

        // 获取普通表单字段
        String description = req.getParameter("description");

        resp.getWriter().write("上传成功：" + fileName);
    }
}
```

多文件上传使用 `req.getParts()`：

```java
for (Part part : req.getParts()) {
    String name = part.getName();
    String fileName = part.getSubmittedFileName();
    if (fileName != null) {
        part.write(savePath + File.separator + fileName);
    }
}
```

### 文件下载

```java
@WebServlet("/download")
public class DownloadServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        String fileName = req.getParameter("file");
        if (fileName == null || fileName.contains("..")) {  // 防路径穿越
            resp.sendError(HttpServletResponse.SC_BAD_REQUEST);
            return;
        }

        String filePath = getServletContext().getRealPath("/uploads/") + File.separator + fileName;
        File file = new File(filePath);
        if (!file.exists()) {
            resp.sendError(HttpServletResponse.SC_NOT_FOUND);
            return;
        }

        // 设置响应头
        resp.setContentType(getServletContext().getMimeType(fileName));
        resp.setContentLengthLong(file.length());
        resp.setHeader("Content-Disposition",
            "attachment; filename=\"" + URLEncoder.encode(fileName, "UTF-8") + "\"");

        // 写入输出流
        try (FileInputStream fis = new FileInputStream(file);
             OutputStream out = resp.getOutputStream()) {
            byte[] buffer = new byte[4096];
            int len;
            while ((len = fis.read(buffer)) != -1) {
                out.write(buffer, 0, len);
            }
        }
    }
}
```

**中文文件名处理**：不同浏览器对 Content-Disposition 的编码要求不同。大多数现代浏览器支持 `filename*=UTF-8''encodedName`：

```java
String encodedFileName = URLEncoder.encode(fileName, "UTF-8").replaceAll("\\+", "%20");
resp.setHeader("Content-Disposition",
    "attachment; filename=\"" + encodedFileName + "\"; filename*=UTF-8''" + encodedFileName);
```

## 应用场景实战

### 场景 1：简易登录认证系统

使用 Servlet + Filter + Session 实现基于表单的登录认证。

```java
// LoginServlet —— 处理登录
@WebServlet("/login")
public class LoginServlet extends HttpServlet {

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        String username = req.getParameter("username");
        String password = req.getParameter("password");

        resp.setContentType("application/json;charset=UTF-8");
        PrintWriter writer = resp.getWriter();

        // 模拟用户验证
        if ("admin".equals(username) && "123456".equals(password)) {
            // 防止 Session 固定攻击，登录后换新 Session
            HttpSession oldSession = req.getSession(false);
            if (oldSession != null) {
                oldSession.invalidate();
            }
            HttpSession session = req.getSession(true);
            session.setAttribute("username", username);
            session.setAttribute("loginTime", System.currentTimeMillis());
            session.setMaxInactiveInterval(30 * 60);

            writer.write("{\"code\":200,\"msg\":\"登录成功\"}");
        } else {
            writer.write("{\"code\":401,\"msg\":\"用户名或密码错误\"}");
        }
    }
}

// AuthFilter —— 拦截未登录请求
@WebFilter("/api/*")
public class AuthFilter implements Filter {

    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpReq = (HttpServletRequest) req;
        HttpServletResponse httpResp = (HttpServletResponse) resp;

        String path = httpReq.getRequestURI();
        // 放行登录请求
        if (path.contains("/login")) {
            chain.doFilter(req, resp);
            return;
        }

        // 检查 Session
        HttpSession session = httpReq.getSession(false);
        if (session == null || session.getAttribute("username") == null) {
            httpResp.setContentType("application/json;charset=UTF-8");
            httpResp.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            httpResp.getWriter().write("{\"code\":401,\"msg\":\"未登录\"}");
            return;
        }

        chain.doFilter(req, resp);
    }
}

// UserServlet —— 受保护资源的访问
@WebServlet("/api/users/*")
public class UserServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        resp.setContentType("application/json;charset=UTF-8");
        HttpSession session = req.getSession();
        String username = (String) session.getAttribute("username");

        resp.getWriter().write("{\"username\":\"" + username + "\",\"role\":\"admin\"}");
    }
}
```

### 场景 2：请求日志与性能监控

```java
@WebFilter("/*")
public class AccessLogFilter implements Filter {

    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpReq = (HttpServletRequest) req;
        String method = httpReq.getMethod();
        String uri = httpReq.getRequestURI();
        String query = httpReq.getQueryString();
        String remoteAddr = httpReq.getRemoteAddr();

        long start = System.currentTimeMillis();
        try {
            chain.doFilter(req, resp);
        } finally {
            long cost = System.currentTimeMillis() - start;
            int status = ((HttpServletResponse) resp).getStatus();
            String fullUrl = query == null ? uri : uri + "?" + query;
            System.out.printf("[%s] %s %s -> %d (%dms)%n",
                remoteAddr, method, fullUrl, status, cost);
        }
    }
}
```

输出示例：

```text
[127.0.0.1] GET /myapp/api/users?id=1 -> 200 (15ms)
[127.0.0.1] POST /myapp/login -> 200 (32ms)
[192.168.1.100] GET /myapp/api/users -> 401 (2ms)
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Servlet 不要持有可变实例变量**。Servlet 是单实例多线程模式，实例变量会被多个请求共享，会导致线程安全问题。请求级别的数据存在局部变量或 request/session 域中。

2. **编码统一用 Filter 处理**，不要在每个 Servlet 中重复设置。

3. **在 Filter 中关闭输出流时不要调用 close()**。Servlet 容器会管理流的关闭。在 Filter 中 close 会导致后续 Filter/Servlet 无法写入响应。

4. **登录后必须换 Session ID**，防御 Session 固定攻击。

5. **文件上传时校验文件类型和大小**，不能只靠 Content-Type（可伪造），应校验文件魔数（magic bytes）。

6. **Cookie 安全三板斧**：HttpOnly（防 XSS 盗取）+ Secure（防中间人）+ SameSite（防 CSRF）。

### 踩坑记录

**坑 1：`getParameter()` 和 `getInputStream()` 互斥**

调用 `getParameter()` 后，容器会解析请求体（application/x-www-form-urlencoded）。此时流的指针已到末尾，后续 `getInputStream()` 读不到数据。

解法：一个请求要么读参数，要么读流，不要同时使用。如果需要从流中读取 JSON 并解析，直接用 `getReader()` 获取全文。

**坑 2：`getWriter()` 和 `getOutputStream()` 互斥**

同一个响应只能选其中一个输出流，重复调用会抛 `IllegalStateException`。Spring MVC 的 `@ResponseBody` 方法中不要同时调用 `HttpServletResponse.getWriter()`。

**坑 3：Tomcat 8 之前的 GET 请求中文乱码**

Tomcat 7 及以下默认 URIEncoding 为 ISO-8859-1，GET 参数中的中文会乱码。需要在 `server.xml` 的 Connector 配置 `URIEncoding="UTF-8"`。Tomcat 8+ 默认已是 UTF-8。

**坑 4：`sendRedirect()` 之后继续执行代码**

`sendRedirect()` 不会终止当前方法，后面的代码仍会执行。调用后应立即 `return`：

```java
resp.sendRedirect("/login");
return;  // 必须加，否则后面的代码会继续跑
```

**坑 5：`request.getAttribute()` 只在一次转发内有效**

用 `req.setAttribute()` 设置的数据在重定向后会丢失。跨重定向传递数据需要用 Session。

**坑 6：Session 中存大量对象导致内存溢出**

Session 默认存储在服务端内存中。存几百 KB 的 DTO 没问题，但若存入文件内容、图片等大对象且并发用户多，内存会很快耗尽。大数据存磁盘/对象存储，Session 只存索引/路径。
