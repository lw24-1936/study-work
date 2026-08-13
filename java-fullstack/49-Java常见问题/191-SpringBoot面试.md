---
title: Spring Boot 面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springboot面试, 自动配置, starter, actuator, 启动流程, 配置文件, configurationproperties, springboot3, fat jar, runner]
---

# Spring Boot 面试

整理日期：2026-08-13

## 目录

- [自动配置](#自动配置)
- [Starter](#starter)
- [配置文件](#配置文件)
- [Actuator](#actuator)
- [启动流程](#启动流程)
- [核心注解](#核心注解)
- [Spring Boot 3 变化](#spring-boot-3-变化)
- [其他高频问题](#其他高频问题)
- [面试重点总结](#面试重点总结)

## 自动配置

**问题 1：Spring Boot 自动配置的原理？**

```text
1. @SpringBootApplication 包含 @EnableAutoConfiguration
2. @EnableAutoConfiguration 导入 AutoConfigurationImportSelector
3. 加载 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
   （Spring Boot 2.7 之前是 spring.factories）
4. 每个自动配置类用条件注解判断
5. 满足条件 → 创建默认 Bean
```

**问题 2：条件注解有哪些？**

```text
@ConditionalOnClass —— 指定类存在才生效（classpath 有依赖）
@ConditionalOnMissingClass —— 类不存在才生效
@ConditionalOnBean —— 容器有指定 Bean 才生效
@ConditionalOnMissingBean —— 容器没有才生效（用户可覆盖）
@ConditionalOnProperty —— 配置项满足才生效（开关）
@ConditionalOnWebApplication —— Web 应用才生效
```

**问题 3：如何排除自动配置？**

```java
@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)
```

```yaml
# 或配置文件排除
spring:
  autoconfigure:
    exclude: org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
```

**问题 4：自动配置的优先级问题？**

```text
用户自己定义的 Bean 优先于自动配置的 Bean（@ConditionalOnMissingBean）。
自动配置类用 @AutoConfigureOrder / @AutoConfigureBefore / @AutoConfigureAfter 控制顺序。
```

## Starter

**问题 1：Starter 是什么？**

```text
Starter 是"依赖 + 自动配置"的打包：
1. 引入 starter → 引入一组相关依赖（版本统一管理）
2. 自动配置类生效 → 创建默认 Bean
3. 开箱即用
```

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

**问题 2：如何自定义 Starter？**

```text
1. 创建自动配置类（@Configuration + @Bean）
2. 写 META-INF/spring/...AutoConfiguration.imports 注册
3. 用 @ConditionalOnMissingBean 允许用户覆盖
4. 可加 @ConfigurationProperties 读取配置

命名规范：官方 spring-boot-starter-xxx，自定义 xxx-spring-boot-starter
```

## 配置文件

**问题 1：配置文件的加载顺序？**

```text
优先级从高到低：
1. 命令行参数（--server.port=8081）
2. 操作系统环境变量
3. application-{profile}.yml（jar 外 config 目录 > jar 外 > jar 内）
4. application.yml（同上）
5. @PropertySource
6. 默认值

jar 外的 config/ 目录优先级最高（部署时改配置不改包）。
```

**问题 2：多环境配置？**

```yaml
# application.yml 指定激活环境
spring:
  profiles:
    active: prod   # 激活 application-prod.yml
```

```text
1. application.yml 放公共配置，application-{env}.yml 放环境差异
2. 通过 spring.profiles.active 切换
3. 也支持 @Profile 注解条件创建 Bean
```

**问题 3：@Value 和 @ConfigurationProperties 的区别？**

| 维度 | @Value | @ConfigurationProperties |
|------|--------|--------------------------|
| 绑定 | 单个属性 | 一组属性（前缀绑定） |
| 松散绑定 | 不支持 | 支持（user-name → userName） |
| 类型安全 | 无 | 有（类型转换） |
| 校验 | 无 | @Validated + JSR-303 |
| 复杂类型 | 麻烦 | 支持 List/Map/嵌套对象 |

```java
// @ConfigurationProperties（推荐，类型安全）
@ConfigurationProperties(prefix = "app")
public class AppConfig {
    private String name;
    private List<String> hosts;
    // getter/setter
}
```

## Actuator

**问题 1：Actuator 是什么？**

```text
Actuator 是 Spring Boot 的监控端点，用于生产环境观测：
1. /actuator/health —— 健康检查（可自定义 HealthIndicator）
2. /actuator/metrics —— 指标（JVM 内存、GC、HTTP 请求）
3. /actuator/info —— 应用信息
4. /actuator/env —— 环境配置
5. /actuator/beans —— 容器 Bean
6. /actuator/threaddump —— 线程转储
```

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
```

**问题 2：如何自定义健康检查？**

```java
@Component
public class MyHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        boolean ok = checkSomething();
        if (ok) return Health.up().build();
        return Health.down().withDetail("error", "xxx").build();
    }
}
```

## 启动流程

**问题 1：Spring Boot 的启动流程？**

```text
SpringApplication.run() 核心流程：
1. 创建 SpringApplication（推断应用类型、加载初始化器）
2. 准备环境 Environment（加载配置）
3. 创建 ApplicationContext（Servlet → AnnotationConfigServletWebServerApplicationContext）
4. 刷新上下文（加载 Bean、执行自动配置、启动内嵌 Tomcat）
5. 执行 Runner（ApplicationRunner / CommandLineRunner）
```

**问题 2：Spring Boot 如何启动内嵌 Tomcat？**

```text
1. spring-boot-starter-web 引入 tomcat-embed-core
2. 自动配置 ServletWebServerFactoryAutoConfiguration
3. 创建 TomcatServletWebServerFactory → 启动内嵌 Tomcat
4. 无需外部容器，main 方法直接启动
```

## 核心注解

**问题 1：@SpringBootApplication 包含哪些注解？**

```java
@SpringBootApplication
= @SpringBootConfiguration    // 配置类（本质 @Configuration）
+ @EnableAutoConfiguration    // 自动配置
+ @ComponentScan              // 组件扫描
```

**问题 2：@Configuration 和 @Component 的区别？**

```text
@Configuration —— 配置类，@Bean 方法经 CGLIB 代理，多次调用返回同一实例（单例保证）
@Component —— 普通组件，@Bean 方法无代理，多次调用返回不同实例

@Configuration 内部 @Bean 方法调用 this.xxx() 会走代理拿容器单例，@Component 不会。
```

**问题 3：@RestController 和 @Controller 的区别？**

```text
@RestController = @Controller + @ResponseBody
@Controller —— 返回视图（页面）
@RestController —— 返回 JSON（方法返回值序列化为响应体）
```

## Spring Boot 3 变化

**问题：Spring Boot 3 有哪些变化？**

```text
1. 基于 Spring Framework 6，要求 JDK 17+（最低 Java 17）
2. 全面迁移到 Jakarta EE（javax.* → jakarta.*，Servlet API 命名空间变更）
3. 默认使用 Spring Native / GraalVM 支持增强
4. spring.factories 移除，改用 AutoConfiguration.imports
5. 引入 @HttpExchange 声明式 HTTP 接口
6. 支持虚拟线程（JDK 21）
7. 可观测性升级（Micrometer Tracing）
```

```text
迁移注意：老项目升级 Spring Boot 3 时，javax.servlet 要换成 jakarta.servlet，
javax.persistence 换 jakarta.persistence。
```

## 其他高频问题

**问题 1：CommandLineRunner 和 ApplicationRunner 的区别？**

```text
都在应用启动完成后执行一次（常用于初始化数据、预热缓存）：
CommandLineRunner —— run(String... args)，原始参数
ApplicationRunner —— run(ApplicationArguments args)，封装后的参数（支持选项解析）

多个 Runner 用 @Order 控制执行顺序。
```

**问题 2：什么是 fat jar？**

```text
fat jar（可执行 jar）：把应用代码 + 所有依赖 + 内嵌容器打成单个 jar，
BOOT-INF/lib 放依赖，java -jar 直接运行，无需外部依赖环境。
```

**问题 3：热部署如何实现？**

```text
1. devtools —— spring-boot-devtools，改动后自动重启（restart classloader）
2. JRebel —— 商业热部署（改代码即时生效，无需重启）
3. IDE 热替换 —— 方法体修改可热替换，结构变更需重启
```

**问题 4：如何优雅停机？**

```text
1. 开启：server.shutdown=graceful
2. 设置超时：spring.lifecycle.timeout-per-shutdown-phase=30s
3. 停机流程：停止接收新请求 → 处理完在途请求 → 关闭容器
4. 配合 K8s 的 preStop hook 实现滚动更新无中断
```

## 面试重点总结

```text
高频考点：
1. 自动配置原理（必考）
2. 条件注解
3. Starter 机制 + 自定义 Starter
4. @SpringBootApplication 组成
5. 配置文件加载顺序 + @Value vs @ConfigurationProperties
6. 启动流程
7. Actuator 监控
8. Spring Boot 3 变化（Jakarta EE、JDK 17）
9. fat jar
```
