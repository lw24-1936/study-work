---
title: Spring Boot 基础
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-boot, auto-configuration, starter, springbootapplication, actuator, environment, profile]
---

# Spring Boot 基础

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Spring Boot 核心特性](#spring-boot-核心特性)
- [@SpringBootApplication](#springbootapplication)
- [自动配置原理](#自动配置原理)
- [Starter 机制](#starter-机制)
- [SpringApplication 启动流程](#springapplication-启动流程)
- [Actuator 生产就绪特性](#actuator-生产就绪特性)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Boot 是 Spring 生态的"脚手架"，它让创建独立的、生产级的 Spring 应用变得简单。核心哲学是**约定优于配置（Convention over Configuration）**——默认配置开箱即用，需要时再覆盖。

Spring Boot 解决的核心痛点：

```text
传统 Spring 的痛点：
1. 依赖管理复杂 —— 每个依赖都要指定版本，版本冲突频繁
2. 配置繁琐 —— 大量 XML/Java 配置
3. 部署麻烦 —— 需要外部 Tomcat，打 war 包
4. 监控缺失 —— 没有开箱即用的健康检查、指标

Spring Boot 的解决：
1. Starter 依赖 —— 一站式依赖管理，版本统一
2. 自动配置 —— 根据类路径自动配置 Bean
3. 内嵌服务器 —— 打 jar 包直接 java -jar 运行
4. Actuator —— 生产级监控端点
```

```text
Spring Boot vs Spring Framework：
Spring Framework 是基础框架（IoC、AOP、事务）
Spring Boot 是 Spring 的自动装配工具，基于 Spring Framework
Spring Boot ≠ 新框架，而是"让 Spring 更好用"的增强层
```

## Spring Boot 核心特性

### 1. 快速创建

```java
// 一个类就能启动完整的 Web 应用
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 2. Starter 依赖

```xml
<!-- 传统方式：需要自己管理一堆依赖和版本 -->
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-webmvc</artifactId>
    <version>6.1.0</version>
</dependency>
<!-- 还要 jackson、tomcat、日志... -->

<!-- Starter 方式：一个依赖搞定所有 -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <!-- 版本由 spring-boot-starter-parent 统一管理 -->
</dependency>
```

### 3. 内嵌服务器

```text
spring-boot-starter-web 内嵌 Tomcat
spring-boot-starter-webflux 内嵌 Netty
java -jar app.jar 直接运行，无需外部容器
```

### 4. 自动配置

根据 classpath 中的依赖自动配置 Spring Bean，无需手写配置。

### 5. 生产就绪

Actuator 提供健康检查、指标、日志等监控端点。

## @SpringBootApplication

`@SpringBootApplication` 是 Spring Boot 的核心注解，它是三个注解的组合：

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@SpringBootConfiguration   // 1. 标记为配置类
@EnableAutoConfiguration   // 2. 启用自动配置
@ComponentScan(...)        // 3. 组件扫描
public @interface SpringBootApplication {
    // ...
}
```

### 三个注解逐一拆解

**1. @SpringBootConfiguration**

本质就是 `@Configuration`，标记主类为配置类：

```java
@Configuration
public @interface SpringBootConfiguration {}
```

**2. @EnableAutoConfiguration**

启用自动配置，是 Spring Boot 的核心魔法：

```java
@AutoConfigurationPackage
@Import(AutoConfigurationImportSelector.class)
public @interface EnableAutoConfiguration {}
```

- `@AutoConfigurationPackage`：记录主类所在包，作为自动扫描的基准包
- `@Import(AutoConfigurationImportSelector.class)`：导入自动配置类的选择器

**3. @ComponentScan**

扫描主类所在包及子包下的 `@Component` 等注解：

```java
// 默认扫描主类所在包
@SpringBootApplication  // 主类在 com.example 下，扫描 com.example 及其子包
public class Application {}

// 自定义扫描范围
@SpringBootApplication(scanBasePackages = "com.example")
public class Application {}

// 排除特定类
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})
public class Application {}
```

### 关键：主类的位置

```text
推荐包结构：
com.example
├── Application.java          ← 主类（@SpringBootApplication）
├── controller/
├── service/
├── dao/
└── config/
```

主类必须放在**所有业务包的父包**，这样 `@ComponentScan` 才能扫描到所有组件。如果主类在子包，其他包的组件不会被扫描到。

## 自动配置原理

自动配置是 Spring Boot 的核心机制。它根据 classpath 中的类、配置属性、已有的 Bean，自动配置 Spring 容器。

### 自动配置如何工作

```text
1. 启动时，@EnableAutoConfiguration 触发 AutoConfigurationImportSelector
2. 选择器读取 classpath 下所有 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports 文件
3. 汇总所有自动配置类（约 180+ 个）
4. 每个自动配置类上有 @Conditional 条件注解，符合条件的才生效
5. 条件评估通过后，配置类中的 @Bean 方法创建 Bean
```

### 自动配置类示例

以 DataSource 自动配置为例：

```java
@AutoConfiguration
@ConditionalOnClass({DataSource.class, EmbeddedDatabaseType.class})
@EnableConfigurationProperties(DataSourceProperties.class)
public class DataSourceAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public DataSource dataSource(DataSourceProperties properties) {
        // 根据配置创建 DataSource
        return properties.initializeDataSourceBuilder().build();
    }
}
```

关键注解：

| 注解 | 作用 |
|------|------|
| @ConditionalOnClass | classpath 存在指定类才生效 |
| @ConditionalOnMissingBean | 容器中没有该 Bean 才创建 |
| @ConditionalOnProperty | 配置属性满足条件才生效 |
| @ConditionalOnWebApplication | Web 应用才生效 |
| @EnableConfigurationProperties | 启用配置属性类 |

### 自动配置的优先级

```text
自动配置类顺序（越低越优先执行）：
1. 用户自定义的 @Configuration（最高优先级）
2. 用户自定义的自动配置
3. Spring Boot 内置自动配置
```

用户定义的 Bean 优先于自动配置，这就是"约定优于配置、配置覆盖约定"的体现——你定义了 Bean，自动配置就退让。

### 查看哪些自动配置生效了

```bash
# 启动时开启 debug，查看自动配置报告
java -jar app.jar --debug

# 或在 application.yml 中
debug: true

# 日志中会输出：
# Positive matches（生效的自动配置）
# Negative matches（未生效的自动配置及原因）
```

```text
Positive matches:
   DataSourceAutoConfiguration matched:
      - @ConditionalOnClass found required class 'javax.sql.DataSource'

Negative matches:
   RedisAutoConfiguration:
      Did not match:
         - @ConditionalOnClass did not find required class 'org.springframework.data.redis.core.RedisOperations'
```

### 排除自动配置

```java
@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)
public class Application {}
```

```yaml
spring:
  autoconfigure:
    exclude:
      - org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
```

## Starter 机制

Starter 是一组依赖的集合，把某个功能需要的所有依赖打包成一个坐标。

### Starter 命名规范

```text
官方 Starter：
spring-boot-starter-web
spring-boot-starter-data-redis
spring-boot-starter-security
spring-boot-starter-actuator

第三方 Starter（自定义）：
myproject-spring-boot-starter
自定义 Starter 不能以 spring-boot 开头（那是官方保留前缀）
```

### 常见 Starter

| Starter | 功能 |
|---------|------|
| spring-boot-starter-web | Web 开发（内嵌 Tomcat + Spring MVC） |
| spring-boot-starter-webflux | 响应式 Web（Netty） |
| spring-boot-starter-data-jpa | JPA |
| spring-boot-starter-data-redis | Redis |
| spring-boot-starter-security | 安全 |
| spring-boot-starter-test | 测试 |
| spring-boot-starter-actuator | 监控 |
| spring-boot-starter-validation | 参数校验 |
| spring-boot-starter-aop | AOP |
| spring-boot-starter-cache | 缓存 |

### Starter 的组成

```text
一个 Starter 通常包含两个模块：
1. spring-boot-starter-xxx（Starter 模块）
   - 只包含 pom.xml，聚合所有需要的依赖
   - 没有任何 Java 代码

2. xxx-spring-boot-autoconfigure（自动配置模块）
   - 包含自动配置类
   - META-INF/spring/...AutoConfiguration.imports 文件
   - 条件注解 + @Bean 方法
```

Starter 机制的详细原理和自定义 Starter 在 80-Starter 中展开。

## SpringApplication 启动流程

SpringApplication.run() 是 Spring Boot 应用的入口，它的启动过程：

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 启动流程

```text
1. new SpringApplication(primarySources)
   - 推断应用类型（SERVLET / REACTIVE / NONE）
   - 加载 ApplicationContextInitializer 和 ApplicationListener（SPI）

2. run(args) 方法
   2.1 创建 StopWatch 计时器
   2.2 创建引导上下文，加载 Banner
   2.3 创建并准备 Environment（读取配置）
   2.4 打印 Banner
   2.5 创建 ApplicationContext（根据应用类型）
   2.6 准备上下文（注册 Bean、执行 initializer）
   2.7 刷新上下文（refresh()，触发自动配置）
   2.8 启动内嵌服务器（Web 应用）
   2.9 执行 ApplicationRunner / CommandLineRunner
   2.10 启动完成，输出 Started 日志
```

### 启动日志解读

```text
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | |_| (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/
 :: Spring Boot ::        (v3.3.0)

2026-08-12 22:00:00.123  INFO 12345 --- [main] com.example.Application : Starting Application
2026-08-12 22:00:02.456  INFO 12345 --- [main] com.example.Application : Started Application in 2.333 seconds
```

`Started Application in 2.333 seconds` 是启动耗时，是性能优化的重要指标。

### ApplicationRunner 与 CommandLineRunner

应用启动完成后执行初始化逻辑：

```java
@Component
@Order(1)  // 控制执行顺序
public class DataInitializer implements ApplicationRunner {

    @Override
    public void run(ApplicationArguments args) {
        // 启动完成后执行，如预热缓存、初始化数据
        cacheService.warmUp();
    }
}

@Component
@Order(2)
public class AnotherInitializer implements CommandLineRunner {
    @Override
    public void run(String... args) {
        // CommandLineRunner 接收原始参数
    }
}
```

区别：ApplicationRunner 接收封装后的 `ApplicationArguments`（可获取选项参数），CommandLineRunner 接收原始 String[] 参数。

### 自定义 Banner

```text
在 classpath 下放 banner.txt 文件，Spring Boot 启动时会显示自定义 Banner。

可以配置：
spring:
  banner:
    location: classpath:banner.txt
```

## Actuator 生产就绪特性

Actuator 为 Spring Boot 应用提供生产级监控和管理能力。

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

### 暴露端点

```yaml
management:
  endpoints:
    web:
      exposure:
        include: "*"          # 暴露所有端点
        # include: health,info,metrics  # 只暴露指定端点
  endpoint:
    health:
      show-details: always    # 显示健康检查详情
```

### 核心端点

| 端点 | 说明 |
|------|------|
| /actuator/health | 健康检查（UP/DOWN） |
| /actuator/info | 应用信息 |
| /actuator/metrics | 指标列表 |
| /actuator/metrics/{name} | 具体指标（如 jvm.memory.used） |
| /actuator/beans | Spring 容器中的 Bean |
| /actuator/env | 环境属性 |
| /actuator/configprops | 配置属性 |
| /actuator/mappings | URL 映射 |
| /actuator/loggers | 日志级别（可动态修改） |
| /actuator/threaddump | 线程转储 |
| /actuator/heapdump | 堆转储 |
| /actuator/prometheus | Prometheus 格式指标 |

### 健康检查

```text
GET /actuator/health
```

```json
{
  "status": "UP",
  "components": {
    "db": {"status": "UP", "details": {"database": "MySQL", "result": 1}},
    "diskSpace": {"status": "UP", "details": {"total": 100GB, "free": 50GB}},
    "redis": {"status": "UP"}
  }
}
```

自定义健康检查：

```java
@Component
public class CustomHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        // 检查某个依赖是否正常
        if (checkDependency()) {
            return Health.up().withDetail("status", "正常").build();
        }
        return Health.down().withDetail("status", "异常").build();
    }
}
```

### 自定义 Info

```yaml
info:
  app:
    name: my-app
    version: 1.0.0
    description: 我的应用
```

```java
@Component
public class CustomInfoContributor implements InfoContributor {
    @Override
    public void contribute(Info.Builder builder) {
        builder.withDetail("buildTime", LocalDateTime.now());
    }
}
```

### 动态修改日志级别

```text
POST /actuator/loggers/com.example.service
Content-Type: application/json
{"configuredLevel": "DEBUG"}

不重启应用，动态调整某个包的日志级别
```

## 应用场景实战

### 场景 1：快速构建一个 Web 服务

```java
// 1. pom.xml 依赖
// <dependency>spring-boot-starter-web</dependency>

// 2. 主类
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// 3. Controller
@RestController
public class HelloController {
    @GetMapping("/hello")
    public String hello() {
        return "Hello Spring Boot";
    }
}

// 4. 运行
// java -jar app.jar
// 访问 http://localhost:8080/hello
```

### 场景 2：启动时初始化数据

```java
@Component
@Order(1)
public class CacheWarmer implements ApplicationRunner {

    @Autowired
    private CacheService cacheService;

    @Override
    public void run(ApplicationArguments args) {
        // 启动完成后预热热点数据到缓存
        List<HotItem> hotItems = itemService.findHotItems(100);
        hotItems.forEach(cacheService::put);
        System.out.println("缓存预热完成：" + hotItems.size() + " 条");
    }
}
```

### 场景 3：生产环境监控配置

```yaml
# application-prod.yml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,loggers
  endpoint:
    health:
      show-details: when-authorized  # 仅授权用户可见详情
  metrics:
    export:
      prometheus:
        enabled: true

info:
  app:
    name: my-app
    version: 1.0.0
```

## 最佳实践与踩坑记录

### 最佳实践

1. **主类放在顶层包**。保证 @ComponentScan 能扫描到所有组件。

2. **理解"配置覆盖约定"**。Spring Boot 自动配置了大多数 Bean，但当你自己定义了同类型的 Bean 时，自动配置会退让（@ConditionalOnMissingBean）。这正是定制化的入口。

3. **启动耗时是重要指标**。`Started Application in X seconds` 是冷启动优化的关键指标。启动慢通常是 Bean 过多、数据库连接慢、懒加载未配置导致。

4. **生产环境关闭 DEBUG 级别的自动配置报告**。只在排查问题时临时开启 `--debug`。

5. **Actuator 端点要加安全保护**。health 可以公开（给负载均衡探测），但 env、beans、heapdump 等包含敏感信息，必须通过 Spring Security 保护。

### 踩坑记录

**坑 1：主类位置导致组件扫描不到**

```text
com.example
├── Application.java          ← 主类在 com.example
└── web/
    └── UserController.java   ← 能扫描到 ✓

com.example
├── config/
│   └── Application.java      ← 主类在 config 子包
└── web/
    └── UserController.java   ← 扫描不到 ✗（web 不在 config 包下）
```

解法：主类移到顶层包，或用 `@SpringBootApplication(scanBasePackages = "com.example")`。

**坑 2：@ComponentScan 与 @SpringBootApplication 冲突**

```java
@SpringBootApplication
@ComponentScan("com.other")  // 覆盖了默认的组件扫描范围！
public class Application {}
```

`@SpringBootApplication` 自带 @ComponentScan，再显式写 @ComponentScan 会覆盖默认范围。要扩展扫描范围，用 `scanBasePackages` 属性而不是加 @ComponentScan。

**坑 3：排除自动配置后功能失效**

```java
@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)
public class Application {}
// 排除了 DataSource 自动配置，但代码里还在用 JdbcTemplate
// 启动时 NoSuchBeanDefinitionException
```

排除自动配置前要确认没有代码依赖它创建的 Bean。

**坑 4：内嵌 Tomcat 端口被占用**

```text
Web server failed to start. Port 8080 was already in use.
```

```yaml
server:
  port: 8081  # 改端口
```

**坑 5：Actuator 端点暴露过多**

```yaml
management:
  endpoints:
    web:
      exposure:
        include: "*"  # 危险！env/beans/heapdump 泄露敏感信息
```

生产环境只暴露 health、info、metrics，其余端点配合 Spring Security 授权访问。

**坑 6：Banner 文件放错位置**

```text
banner.txt 必须放在 classpath 根目录（src/main/resources/banner.txt），
不是 src/main/java 下
```
