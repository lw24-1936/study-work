---
title: Spring 资源抽象（Resources）
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring, resource, resourceloader, resourcepatternresolver, classpathresource, filesystemresource, urlresource]
---

# Spring 资源抽象（Resources）

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Resource 接口](#resource-接口)
- [内置 Resource 实现](#内置-resource-实现)
- [ResourceLoader 接口](#resourceloader-接口)
- [ResourcePatternResolver 接口](#resourcepatternresolver-接口)
- [ResourceLoaderAware 接口](#resourceloaderaware-接口)
- [资源作为依赖注入](#资源作为依赖注入)
- [应用上下文中的资源路径](#应用上下文中的资源路径)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring 的 Resource 抽象解决了 Java 标准 `java.net.URL` 类的不足。`URL` 无法直接访问 classpath 下的资源、无法判断资源是否存在，而为每种前缀（http:、file: 等）注册新的 URL handler 又很复杂。

Spring 用 `org.springframework.core.io.Resource` 接口统一抽象了底层资源的访问，屏蔽了不同来源（classpath、文件系统、URL、ServletContext）的差异。Resource 在 Spring 内部被广泛使用——`ApplicationContext` 构造、`@PropertySource`、`@ImportResource` 等都用它加载资源。

## Resource 接口

Resource 继承自 `InputStreamSource`，是 Spring 资源访问的统一入口：

```java
// 基础接口：提供输入流
public interface InputStreamSource {
    InputStream getInputStream() throws IOException;
}

// Resource 接口：在输入流之上增加资源元信息能力
public interface Resource extends InputStreamSource {

    boolean exists();                    // 资源是否物理存在
    boolean isReadable();                // 是否可读
    boolean isOpen();                    // 是否持有已打开的流（InputStreamResource 返回 true）
    boolean isFile();                    // 是否为文件系统资源

    URL getURL() throws IOException;     // 转 URL
    URI getURI() throws IOException;     // 转 URI
    File getFile() throws IOException;   // 转 File（仅文件系统资源支持）

    ReadableByteChannel readableChannel() throws IOException;  // NIO 通道
    long contentLength() throws IOException;                   // 内容长度
    long lastModified() throws IOException;                    // 最后修改时间

    Resource createRelative(String relativePath) throws IOException;  // 创建相对资源
    String getFilename();                // 文件名
    String getDescription();             // 描述（错误输出用，通常是完整路径或 URL）
}
```

关键方法说明：

- `getInputStream()`：每次调用返回**新的** InputStream，调用方负责关闭
- `isOpen()`：所有常规实现返回 false（可重复读取）；只有 `InputStreamResource` 返回 true（只能读一次）
- `getDescription()`：用于错误信息，如 `class path resource [config/app.properties]`

部分实现还实现了 `WritableResource` 接口，支持写入：

```java
public interface WritableResource extends Resource {
    OutputStream getOutputStream() throws IOException;
}
```

## 内置 Resource 实现

Spring 为不同资源来源提供了多种实现：

| 实现类 | 资源来源 | 前缀 |
|--------|---------|------|
| ClassPathResource | classpath 下资源 | classpath: |
| FileSystemResource | 文件系统 | file: |
| UrlResource | URL（http/https/ftp/file） | http: / https: / ftp: |
| ServletContextResource | Web 应用根目录 | 无前缀（Web 上下文默认） |
| InputStreamResource | 已打开的 InputStream | 无 |
| ByteArrayResource | 内存字节数组 | 无 |

### ClassPathResource

访问 classpath 下的资源，默认用当前线程的 ClassLoader 加载：

```java
// 默认从 classpath 根查找
Resource resource = new ClassPathResource("config/app.properties");
InputStream is = resource.getInputStream();

// 指定 ClassLoader
Resource resource = new ClassPathResource("config/app.properties", MyClass.class.getClassLoader());

// 指定相对于某个类的路径
Resource resource = new ClassPathResource("app.properties", MyClass.class);
```

### FileSystemResource

访问文件系统资源：

```java
// 绝对路径
Resource resource = new FileSystemResource("/opt/config/app.properties");

// 相对路径（相对于当前工作目录）
Resource resource = new FileSystemResource("data/input.txt");

File file = resource.getFile();  // 直接得到 File 对象
```

### UrlResource

访问任意 URL 资源：

```java
Resource httpResource = new UrlResource("https://example.com/config.json");
Resource ftpResource = new UrlResource("ftp://server/file.txt");
Resource fileResource = new UrlResource("file:///opt/config/app.properties");

URL url = httpResource.getURL();
```

### ServletContextResource

访问 Web 应用根目录下的资源（相对于 ServletContext）：

```java
// 在 Servlet/Controller 中
ServletContext context = request.getServletContext();
Resource resource = new ServletContextResource(context, "/WEB-INF/views/index.jsp");
```

### InputStreamResource

包装已打开的 InputStream，**只能读取一次**：

```java
InputStream is = socket.getInputStream();
InputStreamResource resource = new InputStreamResource(is);
// isOpen() 返回 true，不能重复读取
```

### ByteArrayResource

包装内存字节数组，适合测试或从内存构造资源：

```java
byte[] data = "hello spring".getBytes(StandardCharsets.UTF_8);
ByteArrayResource resource = new ByteArrayResource(data);
byte[] bytes = resource.getByteArray();
```

## ResourceLoader 接口

ResourceLoader 是加载资源的统一入口，根据路径前缀返回对应的 Resource 实现：

```java
public interface ResourceLoader {
    String CLASSPATH_URL_PREFIX = "classpath:";  // 前缀常量

    Resource getResource(String location);

    ClassLoader getClassLoader();
}
```

`getResource()` 根据前缀决定返回类型：

```java
ResourceLoader loader = ...;  // 通常是 ApplicationContext

// 不同前缀返回不同的 Resource 实现
Resource classpathRes = loader.getResource("classpath:config/app.properties");  // ClassPathResource
Resource fileRes = loader.getResource("file:/opt/config/app.properties");       // FileSystemResource
Resource urlRes = loader.getResource("https://example.com/config.json");        // UrlResource
Resource webRes = loader.getResource("/WEB-INF/views/index.jsp");               // ServletContextResource（Web 上下文）
```

**核心**：ApplicationContext 都实现了 ResourceLoader 接口，所以可以直接注入使用：

```java
@Component
public class ConfigLoader {
    @Autowired
    private ResourceLoader resourceLoader;

    public String loadConfig() throws IOException {
        Resource resource = resourceLoader.getResource("classpath:config/app.properties");
        try (InputStream is = resource.getInputStream()) {
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
}
```

前缀规则总结：

| 路径前缀 | 返回类型 | 说明 |
|---------|---------|------|
| classpath: | ClassPathResource | classpath 下资源 |
| file: | FileSystemResource | 文件系统 |
| http: / https: / ftp: | UrlResource | URL 资源 |
| 无前缀 | 取决于上下文 | ClassPathXmlApplicationContext 默认 ClassPathResource，Web 上下文默认 ServletContextResource |

## ResourcePatternResolver 接口

ResourcePatternResolver 是 ResourceLoader 的扩展，支持**通配符匹配**多个资源：

```java
public interface ResourcePatternResolver extends ResourceLoader {
    String CLASSPATH_ALL_URL_PREFIX = "classpath*:";

    Resource[] getResources(String locationPattern) throws IOException;
}
```

核心区别：`getResource()` 返回单个资源，`getResources()` 返回匹配的**资源数组**。

```java
ResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();

// 匹配 classpath 下所有 .properties 文件
Resource[] resources = resolver.getResources("classpath*:config/*.properties");

// 匹配 classpath 下任意层级的 XML 文件
Resource[] xmls = resolver.getResources("classpath*:**/*.xml");

// 匹配所有 jar 包中的同名文件（classpath*: 会遍历所有 jar）
Resource[] logbacks = resolver.getResources("classpath*:logback.xml");
```

**classpath: vs classpath\*:**：

| 前缀 | 行为 |
|------|------|
| classpath: | 只在**第一个**匹配的 classpath 位置查找 |
| classpath\*: | 遍历**所有** classpath 位置（含所有 jar 包） |

经典场景：`classpath*:mapper/*.xml` 加载 MyBatis 的 Mapper XML——因为 Mapper XML 可能分散在多个 jar 包中。

```java
// ApplicationContext 也实现了 ResourcePatternResolver
ApplicationContext ctx = ...;
Resource[] mappers = ctx.getResources("classpath*:mapper/*.xml");
```

Ant 风格通配符：

```text
?       匹配单个字符
*       匹配当前目录下任意字符（不跨目录）
**      匹配任意层级目录
```

```java
resolver.getResources("classpath*:com/**/service/*.class");  // 匹配 service 包下所有 class
```

## ResourceLoaderAware 接口

实现 ResourceLoaderAware 的 Bean 会由容器注入 ResourceLoader（通常是 ApplicationContext 本身）：

```java
@Component
public class TemplateService implements ResourceLoaderAware {

    private ResourceLoader resourceLoader;

    @Override
    public void setResourceLoader(ResourceLoader resourceLoader) {
        this.resourceLoader = resourceLoader;
    }

    public void loadTemplate(String path) throws IOException {
        Resource template = resourceLoader.getResource("classpath:templates/" + path);
        // ...
    }
}
```

**注意**：这是早期的 Aware 用法。现代 Spring 直接用 `@Autowired` 注入 ResourceLoader 更简洁（如上一节所示）。ResourceLoaderAware 只在需要"先拿到 ResourceLoader 再做额外初始化"时才用。

## 资源作为依赖注入

Resource 可以直接作为 Bean 的依赖注入，通过 `@Value` 或构造器注入：

```java
@Component
public class ReportGenerator {

    // @Value 注入 Resource，路径带前缀
    @Value("classpath:reports/template.docx")
    private Resource template;

    @Value("file:/opt/data/output.txt")
    private Resource outputFile;

    @Value("https://example.com/logo.png")
    private Resource logo;

    public void generate() throws IOException {
        // 直接读取注入的资源
        try (InputStream is = template.getInputStream()) {
            // 处理模板
        }
    }
}
```

```java
// 构造器注入 Resource
@Component
public class KeyStoreLoader {
    private final Resource keyStore;

    public KeyStoreLoader(@Value("classpath:keystore.jks") Resource keyStore) {
        this.keyStore = keyStore;
    }
}
```

配置文件中也可以引用资源：

```properties
app.template-location=classpath:reports/template.docx
```

```java
@Value("${app.template-location}")
private Resource template;  // Spring 自动解析为 Resource
```

## 应用上下文中的资源路径

不同类型的 ApplicationContext 对无前缀路径的默认解析不同：

```java
// ClassPathXmlApplicationContext：无前缀默认 classpath
ApplicationContext ctx = new ClassPathXmlApplicationContext("applicationContext.xml");

// FileSystemXmlApplicationContext：无前缀默认文件系统（相对于工作目录）
ApplicationContext ctx = new FileSystemXmlApplicationContext("conf/applicationContext.xml");

// Web 环境：无前缀默认相对于 ServletContext 根目录
// AnnotationConfigWebApplicationContext
```

在 Spring Boot 中，`SpringApplication` 的资源加载统一使用 classpath 优先的策略：

```java
// 通配符配置示例：加载多个配置文件
spring.config.import=classpath:additional.properties
```

## 应用场景实战

### 场景 1：批量加载 classpath 下的 SQL 脚本

```java
@Component
public class SqlScriptRunner {

    @Autowired
    private ResourcePatternResolver resolver;

    @Autowired
    private DataSource dataSource;

    public void runScripts(String locationPattern) throws IOException {
        // 匹配 classpath 下（含所有 jar）的 SQL 文件
        Resource[] scripts = resolver.getResources("classpath*:" + locationPattern);

        for (Resource script : scripts) {
            // 按文件名排序，保证执行顺序
        }
        Arrays.sort(scripts, Comparator.comparing(Resource::getFilename));

        for (Resource script : scripts) {
            try (InputStream is = script.getInputStream()) {
                String sql = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                // 执行 SQL
                JdbcTemplate jdbc = new JdbcTemplate(dataSource);
                jdbc.execute(sql);
                System.out.println("执行脚本：" + script.getFilename());
            }
        }
    }
}

// 使用：加载所有 jar 包中的 schema.sql
scriptRunner.runScripts("db/**/*.sql");
```

### 场景 2：配置文件热加载与刷新

```java
@Component
public class DynamicConfigLoader {

    @Autowired
    private ResourceLoader resourceLoader;

    private volatile Properties currentProperties = new Properties();
    private volatile long lastModified = -1;

    public String getConfig(String key) {
        checkAndReload();
        return currentProperties.getProperty(key);
    }

    private void checkAndReload() {
        Resource resource = resourceLoader.getResource("classpath:dynamic-config.properties");
        try {
            long fileLastModified = resource.lastModified();
            if (fileLastModified > lastModified) {
                synchronized (this) {
                    if (fileLastModified > lastModified) {
                        Properties props = new Properties();
                        try (InputStream is = resource.getInputStream()) {
                            props.load(is);
                        }
                        currentProperties = props;
                        lastModified = fileLastModified;
                    }
                }
            }
        } catch (IOException e) {
            throw new RuntimeException("加载配置失败", e);
        }
    }
}
```

### 场景 3：资源存在性检查与容错

```java
@Component
public class TemplateResolver {

    @Autowired
    private ResourceLoader resourceLoader;

    public Resource resolveTemplate(String templateName) {
        // 按优先级依次查找，找到第一个存在的
        String[] candidates = {
            "file:/opt/app/templates/" + templateName,      // 外部配置优先
            "classpath:templates/" + templateName,           // classpath 兜底
            "classpath:default-template.html"                // 默认模板
        };

        for (String location : candidates) {
            Resource resource = resourceLoader.getResource(location);
            if (resource.exists()) {
                return resource;
            }
        }
        throw new IllegalStateException("找不到模板：" + templateName);
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **统一用 Resource 抽象，不要直接 new File / new URL**。Resource 屏蔽了来源差异，代码更容易测试（测试时可用 ByteArrayResource 替换真实文件）。

2. **加载 classpath 资源用 classpath: 前缀显式声明**。不依赖上下文的默认解析策略，代码意图更清晰。

3. **多 jar 包场景用 classpath\*:**。尤其 MyBatis Mapper、Hibernate hbm.xml、logback.xml 等可能分散在多个模块的场景。

4. **用 try-with-resources 关闭流**。`getInputStream()` 返回的流必须由调用方关闭。

### 踩坑记录

**坑 1：classpath: 只找到第一个匹配**

```java
// 如果多个 jar 包中都有 application.properties
Resource resource = resolver.getResource("classpath:application.properties");
// 只返回 classpath 顺序中第一个匹配的，可能不是你要的那个
```

解法：明确指定位置，或用 `classpath*:` + 遍历 + 按需选择。

**坑 2：InputStreamResource 不能重复读取**

```java
InputStream is = socket.getInputStream();
InputStreamResource resource = new InputStreamResource(is);
resource.getInputStream();  // 第一次 OK
resource.getInputStream();  // 第二次读到空或抛异常（流已消费）
```

`isOpen()` 返回 true，说明这个资源只能读一次。需要重复读取时，先把内容读入 ByteArrayResource。

**坑 3：FileSystemResource 相对路径的歧义**

```java
// 相对路径是相对于 JVM 工作目录，不是相对于 classpath
Resource resource = new FileSystemResource("config/app.properties");
```

JVM 工作目录（`user.dir`）在不同启动方式下不同（IDE、命令行、容器）。绝对路径或用 `file:` 前缀更可控。

**坑 4：getFile() 在 jar 包内资源上抛异常**

```java
Resource resource = resourceLoader.getResource("classpath:config/app.properties");
// 应用打成 jar 包后，资源在 jar 内，没有独立的 File 对象
File file = resource.getFile();  // 抛 FileNotFoundException
```

解法：不要调用 `getFile()`，直接用 `getInputStream()` 读内容。或者用 `ResourceUtils` 先把 jar 内资源提取到临时文件。

**坑 5：Web 环境与 classpath 环境的默认路径不同**

```java
// 在 Web 应用（ServletContext）中
resourceLoader.getResource("/config/app.properties");
// 解析为相对于 ServletContext 根目录，而不是 classpath
```

解法：显式使用 `classpath:` 前缀，消除上下文差异。
