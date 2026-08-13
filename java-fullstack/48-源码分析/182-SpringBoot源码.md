---
title: Spring Boot 源码分析
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springboot源码, springapplication, 启动流程, 自动配置, starter, 条件装配, configuration-properties]
---

# Spring Boot 源码分析

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [SpringApplication 启动流程](#springapplication-启动流程)
- [自动配置原理](#自动配置原理)
- [Starter 机制](#starter-机制)
- [条件装配](#条件装配)
- [ConfigurationProperties](#configurationproperties)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Boot 的核心是"约定优于配置"和"自动配置"，理解启动流程和自动配置原理是掌握 Spring Boot 的关键。

```text
Spring Boot 的核心：
1. 自动配置 —— 根据依赖自动配置（引入 starter 即生效）
2. 启动流程 —— SpringApplication 驱动
3. 约定优于配置 —— 默认配置，可覆盖
```

## SpringApplication 启动流程

### 启动入口

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 启动流程（run 方法）

```text
1. 创建 SpringApplication（推断应用类型）
2. 加载 ApplicationContextInitializer
3. 加载 ApplicationListener
4. 推断主类（main 方法所在类）
5. 准备环境（Environment）
6. 创建 ApplicationContext
7. 刷新上下文（核心：Bean 的创建）
8. 执行 CommandLineRunner
```

```text
核心流程：
创建应用 → 准备环境 → 创建上下文 → 刷新上下文（自动配置在此）
```

### @SpringBootApplication 拆解

```java
@SpringBootApplication   // 组合注解
= @SpringBootConfiguration    // 配置类
+ @EnableAutoConfiguration    // 开启自动配置
+ @ComponentScan              // 组件扫描
```

## 自动配置原理

自动配置是 Spring Boot 的核心机制，根据依赖自动装配 Bean。

### 自动配置入口

```text
@EnableAutoConfiguration → @Import(AutoConfigurationImportSelector)

AutoConfigurationImportSelector 加载
META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
中的自动配置类
```

### 自动配置流程

```text
1. 启动时加载所有自动配置类
2. 每个自动配置类用条件注解判断是否生效
3. 满足条件的自动配置类创建 Bean
```

### 自动配置类示例

```java
// DataSourceAutoConfiguration（数据源自动配置）
@AutoConfiguration
@ConditionalOnClass({DataSource.class, EmbeddedDatabaseType.class})
@ConditionalOnMissingBean(DataSource.class)   // 用户没自定义才生效
public class DataSourceAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public DataSource dataSource() {
        // 创建默认数据源
    }
}
```

### 自动配置的关键注解

```text
@ConditionalOnClass —— 类存在才生效
@ConditionalOnMissingBean —— Bean 不存在才生效
@ConditionalOnProperty —— 配置项满足才生效
@ConditionalOnBean —— Bean 存在才生效
```

## Starter 机制

Starter 是一组依赖的打包，引入即自动配置（详见 80-Starter）。

### Starter 的结构

```text
Starter = 依赖打包 + 自动配置类

my-spring-boot-starter
├── 依赖（引入相关库）
└── 自动配置类（AutoConfiguration）
    └── META-INF/spring/...AutoConfiguration.imports
```

### Starter 的工作原理

```text
1. 引入 starter → 引入依赖 + 自动配置类
2. 自动配置类被加载
3. 条件注解判断 → 创建默认 Bean
4. 用户可覆盖默认配置
```

### 常见 Starter

```text
spring-boot-starter-web —— Web 开发（内嵌 Tomcat）
spring-boot-starter-data-jpa —— JPA
spring-boot-starter-data-redis —— Redis
spring-boot-starter-security —— 安全
```

## 条件装配

条件装配是自动配置的基础，用条件注解控制 Bean 的创建。

### 条件注解

```java
// @ConditionalOnClass：类存在才创建
@Bean
@ConditionalOnClass(RedisConnectionFactory.class)
public RedisTemplate<String, Object> redisTemplate() { ... }

// @ConditionalOnProperty：配置项满足才创建
@Bean
@ConditionalOnProperty(name = "cache.enabled", havingValue = "true")
public CacheManager cacheManager() { ... }

// @ConditionalOnMissingBean：Bean 不存在才创建
@Bean
@ConditionalOnMissingBean
public DataSource dataSource() { ... }
```

### 自定义条件

```java
// 自定义条件
public class OnLinuxCondition implements Condition {
    @Override
    public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        return System.getProperty("os.name").contains("Linux");
    }
}

@Bean
@Conditional(OnLinuxCondition.class)
public Bean linuxBean() { ... }
```

## ConfigurationProperties

@ConfigurationProperties 绑定配置到对象（详见 79-配置体系）。

### 配置绑定

```yaml
app:
  name: my-app
  timeout: 5000
  datasource:
    url: jdbc:mysql://...
```

```java
@ConfigurationProperties(prefix = "app")
@Component
public class AppProperties {
    private String name;
    private int timeout;
    private DataSource datasource;   // 嵌套

    // getter/setter
}
```

### 绑定原理

```text
1. @ConfigurationProperties 声明前缀
2. 启动时读取配置
3. 松散绑定（app.name → app.name / app-name）
4. 绑定到对象字段
```

### @ConfigurationProperties vs @Value

```text
@ConfigurationProperties —— 批量绑定（对象），支持校验、松散绑定
@Value —— 单个值，简单
```

## 最佳实践与踩坑记录

### 最佳实践

1. **理解自动配置**。引入 starter 即自动配置，可覆盖。

2. **自动配置可排除**。@SpringBootApplication(exclude = ...)。

3. **自定义 Starter 用条件注解**。@ConditionalOnMissingBean 允许覆盖。

4. **配置用 @ConfigurationProperties**。批量绑定 + 校验。

5. **看自动配置报告**。启动时 --debug 查看自动配置生效情况。

### 踩坑记录

**坑 1：自动配置冲突**

```text
引入多个 starter，自动配置冲突（如多个数据源）
```

用 @ConditionalOnMissingBean 或 exclude 排除。

**坑 2：自定义 Bean 覆盖不了默认**

```text
自定义 Bean 没生效，因为自动配置的 Bean 已存在
```

自动配置类用 @ConditionalOnMissingBean，用户自定义优先。

**坑 3：@Value 不刷新**

```text
@Value 注入的值，配置改了不刷新（需 @RefreshScope）
```

动态配置用 @ConfigurationProperties + 配置中心。

**坑 4：配置属性不生效**

```text
@ConfigurationProperties 没加 @Component 或 @EnableConfigurationProperties
```

加 @Component 或 @EnableConfigurationProperties 注册。

**坑 5：忽略自动配置报告**

```text
自动配置不生效，不知道原因
```

启动时 --debug 查看自动配置报告。

**坑 6：条件注解判断错误**

```text
@ConditionalOnClass 的类名写错，条件永远不满足
```

确认条件注解引用的类正确存在。
