---
title: Spring Boot 面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springboot面试, 自动配置, starter, actuator, 启动流程]
---

# Spring Boot 面试

整理日期：2026-08-13

## 目录

- [自动配置](#自动配置)
- [Starter](#starter)
- [Actuator](#actuator)
- [启动流程](#启动流程)
- [核心注解](#核心注解)

## 自动配置

**问题 1：Spring Boot 自动配置的原理？**

```text
1. @SpringBootApplication 包含 @EnableAutoConfiguration
2. @EnableAutoConfiguration 导入 AutoConfigurationImportSelector
3. 加载 META-INF/spring/...AutoConfiguration.imports
4. 每个自动配置类用条件注解判断
5. 满足条件 → 创建默认 Bean
```

**问题 2：条件注解有哪些？**

```text
@ConditionalOnClass —— 类存在才生效
@ConditionalOnMissingBean —— Bean 不存在才生效
@ConditionalOnProperty —— 配置满足才生效
@ConditionalOnBean —— Bean 存在才生效
```

**问题 3：如何排除自动配置？**

```java
@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)
```

## Starter

**问题 1：Starter 是什么？**

```text
Starter 是一组依赖的打包 + 自动配置：
1. 引入 starter → 引入相关依赖
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
1. 创建自动配置类
2. 写 META-INF/spring/...AutoConfiguration.imports
3. 用 @ConditionalOnMissingBean 允许覆盖
```

## Actuator

**问题：Actuator 是什么？**

```text
Actuator 是 Spring Boot 的监控端点：
1. /actuator/health —— 健康检查
2. /actuator/metrics —— 指标
3. /actuator/info —— 应用信息
4. /actuator/env —— 环境配置
```

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
```

## 启动流程

**问题：Spring Boot 的启动流程？**

```text
SpringApplication.run() 的流程：
1. 创建 SpringApplication
2. 准备环境（Environment）
3. 创建 ApplicationContext
4. 刷新上下文（加载 Bean、自动配置）
5. 执行 CommandLineRunner
```

## 核心注解

**问题：@SpringBootApplication 包含哪些注解？**

```java
@SpringBootApplication
= @SpringBootConfiguration    // 配置类
+ @EnableAutoConfiguration    // 自动配置
+ @ComponentScan              // 组件扫描
```

**问题：@Configuration 和 @Component 的区别？**

```text
@Configuration —— 配置类，@Bean 方法有代理（单例保证）
@Component —— 普通组件

@Configuration 的 @Bean 方法：多次调用返回同一实例（CGLIB 代理）
```

## 面试重点总结

```text
高频考点：
1. 自动配置原理（必考）
2. 条件注解
3. Starter 机制
4. @SpringBootApplication 组成
5. Actuator 监控
```
