---
title: Spring 面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [spring面试, ioc, di, aop, bean生命周期, 循环依赖, 事务, 自动配置]
---

# Spring 面试

整理日期：2026-08-13

## 目录

- [IoC 与 DI](#ioc-与-di)
- [AOP](#aop)
- [Bean 生命周期](#bean-生命周期)
- [循环依赖](#循环依赖)
- [事务](#事务)
- [自动配置](#自动配置)

## IoC 与 DI

**问题 1：什么是 IoC？**

```text
IoC（控制反转）：对象创建和依赖注入的控制权从代码交给容器

传统：对象自己 new 依赖（控制权在对象）
IoC：容器创建对象并注入依赖（控制权在容器）
```

```java
// 传统：自己 new
UserService service = new UserService(new UserRepository());

// IoC：容器注入
@Autowired
private UserRepository repository;   // 容器注入
```

**问题 2：什么是 DI？依赖注入的方式？**

```text
DI（依赖注入）是 IoC 的实现方式：
1. 构造器注入（推荐）
2. Setter 注入
3. 字段注入（@Autowired，不推荐）
```

```java
// 构造器注入（推荐，不可变 + 便于测试）
@Service
public class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {   // 构造器注入
        this.repository = repository;
    }
}
```

## AOP

**问题 1：什么是 AOP？**

```text
AOP（面向切面编程）：把横切逻辑（日志、事务、权限）从业务中分离

横切关注点：散布在各处的重复逻辑
```

**问题 2：AOP 的实现原理？**

```text
AOP 基于动态代理：
1. JDK 动态代理 —— 有接口（Proxy + InvocationHandler）
2. CGLIB —— 无接口（生成子类）

Spring 在 Bean 初始化后生成代理对象
```

**问题 3：AOP 的相关概念？**

```text
1. 切面（Aspect）—— 横切逻辑的类
2. 通知（Advice）—— 切面的方法（before/after/around）
3. 切点（Pointcut）—— 在哪里切
4. 连接点（JoinPoint）—— 可切入的点
```

## Bean 生命周期

**问题：Spring Bean 的生命周期？**

```text
1. 实例化（new 对象）
2. 属性填充（依赖注入）
3. Aware 接口（BeanNameAware/BeanFactoryAware）
4. BeanPostProcessor 前置处理
5. @PostConstruct 初始化
6. InitializingBean.afterPropertiesSet
7. BeanPostProcessor 后置处理（AOP 代理）
8. 使用中
9. @PreDestroy 销毁
```

## 循环依赖

**问题 1：什么是循环依赖？**

```text
循环依赖：A 依赖 B，B 依赖 A
```

**问题 2：Spring 如何解决循环依赖？**

```text
Spring 用三级缓存解决（只解决单例的 Setter 注入）：

一级缓存（singletonObjects）—— 完整 Bean
二级缓存（earlySingletonObjects）—— 早期 Bean
三级缓存（singletonFactories）—— Bean 工厂（提前暴露）

流程：
1. A 创建，提前暴露到三级缓存
2. A 注入 B，B 创建，B 注入 A
3. B 从缓存拿到 A 的早期引用
4. B 创建完成，A 也创建完成
```

```text
注意：
1. 构造器注入的循环依赖无法解决（还没创建完）
2. prototype 的循环依赖无法解决
```

## 事务

**问题 1：Spring 事务的原理？**

```text
事务通过 AOP 实现：
1. @Transactional 注解
2. 事务切面拦截方法
3. 开启事务 → 执行 → 提交/回滚
```

**问题 2：事务的传播行为？**

```text
常见传播行为：
1. REQUIRED —— 有事务加入，无则新建（默认）
2. REQUIRES_NEW —— 新建事务（独立）
3. NESTED —— 嵌套事务
4. SUPPORTS —— 有则加入，无则非事务
```

**问题 3：事务失效的场景？**

```text
1. 方法不是 public
2. 同类方法调用（this.xxx() 不走代理）
3. 异常被捕获（catch 后不抛出）
4. 抛受检异常（默认只回滚 RuntimeException）
```

## 自动配置

**问题：Spring Boot 自动配置的原理？**

```text
1. @EnableAutoConfiguration
2. 加载 META-INF/spring/...AutoConfiguration.imports
3. 每个自动配置类用条件注解判断
4. 满足条件 → 创建 Bean
5. @ConditionalOnMissingBean 允许用户覆盖
```

## 面试重点总结

```text
高频考点：
1. IoC/DI 概念（必考）
2. AOP 原理（动态代理，必考）
3. Bean 生命周期（必考）
4. 循环依赖 + 三级缓存（必考）
5. 事务失效场景（必考）
6. 自动配置原理
```
