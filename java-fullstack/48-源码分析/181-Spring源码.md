---
title: Spring 源码分析
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [spring源码, ioc, beanfactory, applicationcontext, beandefinition, beanpostprocessor, aop, transaction]
---

# Spring 源码分析

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [IoC 容器](#ioc-容器)
- [BeanFactory 与 ApplicationContext](#beanfactory-与-applicationcontext)
- [BeanDefinition 与 Bean 生命周期](#beandefinition-与-bean-生命周期)
- [BeanPostProcessor](#beanpostprocessor)
- [AOP 实现原理](#aop-实现原理)
- [事务实现原理](#事务实现原理)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring 源码分析聚焦 IoC 和 AOP 两大核心，理解它们才能理解 Spring 的整个体系。

```text
Spring 两大核心：
1. IoC（控制反转）—— 对象创建和依赖注入交给容器
2. AOP（面向切面）—— 横切逻辑（事务、日志）统一处理
```

## IoC 容器

IoC 容器管理 Bean 的创建、配置、依赖注入。

### IoC 的核心思想

```text
传统：对象自己 new 依赖（控制权在对象）
IoC：容器创建对象并注入依赖（控制权在容器）
```

```java
// 传统：自己 new
public class UserService {
    private UserRepository repository = new UserRepositoryImpl();
}

// IoC：容器注入
@Service
public class UserService {
    @Autowired
    private UserRepository repository;   // 容器注入
}
```

## BeanFactory 与 ApplicationContext

### BeanFactory（基础容器）

```text
BeanFactory 是 IoC 容器的基础接口：
1. getBean() —— 获取 Bean
2. 懒加载 —— 用到才创建
```

### ApplicationContext（高级容器）

```text
ApplicationContext 是 BeanFactory 的子接口，扩展了：
1. 国际化（MessageSource）
2. 事件（ApplicationEvent）
3. 资源加载（ResourceLoader）
4. 自动注册 BeanPostProcessor
```

```text
BeanFactory vs ApplicationContext：
BeanFactory —— 基础容器，懒加载
ApplicationContext —— 高级容器，启动时预初始化单例
```

### 容器启动流程

```text
ApplicationContext 启动：
1. 读取配置（XML/注解/Java Config）
2. 解析成 BeanDefinition
3. 注册 BeanPostProcessor
4. 实例化单例 Bean
5. 完成依赖注入
```

## BeanDefinition 与 Bean 生命周期

### BeanDefinition

BeanDefinition 是 Bean 的定义（元数据）。

```text
BeanDefinition 包含：
1. 类名（beanClassName）
2. 作用域（scope：singleton/prototype）
3. 依赖（dependsOn）
4. 初始化/销毁方法
```

```text
BeanDefinition 的来源：
1. XML 配置
2. @Component/@Service 注解扫描
3. @Bean 方法
4. @Configuration
```

### Bean 生命周期

```text
Bean 的完整生命周期：
1. 实例化（new 对象）
2. 属性填充（依赖注入 @Autowired）
3. BeanNameAware/BeanFactoryAware（感知接口）
4. BeanPostProcessor 前置处理
5. @PostConstruct（初始化）
6. InitializingBean.afterPropertiesSet
7. BeanPostProcessor 后置处理
8. 使用中
9. @PreDestroy（销毁）
```

```java
@Component
public class UserService implements InitializingBean {

    @PostConstruct
    public void init() {
        // 初始化逻辑
    }

    @Override
    public void afterPropertiesSet() {
        // InitializingBean 接口的初始化
    }

    @PreDestroy
    public void destroy() {
        // 销毁逻辑
    }
}
```

## BeanPostProcessor

BeanPostProcessor 是 Bean 的后置处理器，在初始化前后拦截 Bean。

### BeanPostProcessor 的作用

```text
BeanPostProcessor 是 Spring 的扩展点：
1. 初始化前处理（postProcessBeforeInitialization）
2. 初始化后处理（postProcessAfterInitialization）
```

```java
public interface BeanPostProcessor {
    // 初始化前
    default Object postProcessBeforeInitialization(Object bean, String beanName) {
        return bean;
    }

    // 初始化后（AOP 在这里生成代理）
    default Object postProcessAfterInitialization(Object bean, String beanName) {
        return bean;
    }
}
```

### 常见 BeanPostProcessor

```text
1. AutowiredAnnotationBeanPostProcessor —— 处理 @Autowired
2. CommonAnnotationBeanPostProcessor —— 处理 @PostConstruct
3. AnnotationAwareAspectJAutoProxyCreator —— AOP 代理
```

```text
AOP 的关键：
AnnotationAwareAspectJAutoProxyCreator（一个 BeanPostProcessor）
在 Bean 初始化后，生成代理对象（动态代理）
```

## AOP 实现原理

AOP 通过动态代理实现（详见 73-Spring-AOP）。

### AOP 的实现

```text
1. Spring AOP 基于动态代理：
   - JDK 动态代理（有接口）
   - CGLIB（无接口，继承）

2. 代理生成时机：Bean 初始化后（BeanPostProcessor）
```

### AOP 执行流程

```text
1. 定义切面（@Aspect + 通知）
2. 容器启动时，AOP 的 BeanPostProcessor 识别需要代理的 Bean
3. 生成代理对象（JDK 动态代理 / CGLIB）
4. 方法调用时，代理拦截，执行通知链
```

```java
@Aspect
@Component
public class LogAspect {

    @Around("execution(* com.example..*(..))")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        // 前置
        Object result = pjp.proceed();
        // 后置
        return result;
    }
}
```

### JDK 动态代理 vs CGLIB

```text
JDK 动态代理 —— 基于接口（Proxy + InvocationHandler）
CGLIB —— 基于继承（生成子类）

Spring 默认：有接口用 JDK，无接口用 CGLIB
Spring Boot 2+ 默认 CGLIB
```

## 事务实现原理

事务通过 AOP 实现（详见 74-Spring事务）。

### 事务的 AOP 实现

```text
1. @Transactional 注解
2. 事务的 AOP 切面拦截方法
3. 方法开始：开启事务
4. 方法正常：提交事务
5. 方法异常：回滚事务
```

```text
事务执行流程：
事务拦截器 → 开启事务（获取连接）→ 执行方法 → 提交/回滚 → 释放连接
```

### 事务失效的原因

```text
1. 方法不是 public（CGLIB 代理）
2. 同类方法调用（this.xxx() 不走代理）
3. 异常被捕获（catch 后不抛出）
4. 抛的是受检异常（默认只回滚 RuntimeException）
```

```java
// 事务失效：同类方法调用（this 调用不走代理）
@Service
public class UserService {
    @Transactional
    public void create() { ... }

    public void batchCreate() {
        this.create();   // 同类调用，事务失效
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **理解 Bean 生命周期**。@PostConstruct 初始化，BeanPostProcessor 扩展。

2. **理解 AOP 代理**。事务、缓存都靠代理。

3. **理解事务失效场景**。避免同类调用、私有方法。

4. **用 ApplicationContext**。比 BeanFactory 功能全。

5. **善用 BeanPostProcessor**。自定义扩展点。

### 踩坑记录

**坑 1：事务失效（同类调用）**

```java
this.create();   // 同类调用，不走代理，事务失效
```

通过代理调用（注入自身，或拆到另一个 Bean）。

**坑 2：事务失效（异常被捕获）**

```java
@Transactional
public void create() {
    try {
        doSomething();   // 抛异常
    } catch (Exception e) {
        // 捕获后不抛出，事务不感知异常，不回滚
    }
}
```

异常要抛出，或手动回滚。

**坑 3：@PostConstruct 里调用未初始化的依赖**

```text
@PostConstruct 时依赖可能未完全注入
```

用 afterPropertiesSet 或构造器注入。

**坑 4：原型 Bean 注入单例**

```text
prototype Bean 注入 singleton，只会创建一次（失效）
```

用 ObjectFactory 或 @Lookup 获取原型 Bean。

**坑 5：循环依赖**

```text
A 依赖 B，B 依赖 A，循环依赖
```

Spring 用三级缓存解决（构造器循环依赖无法解决）。

**坑 6：不理解代理导致 @Transactional 不生效**

```text
new UserService() 直接创建（不是容器代理），事务注解失效
```

用容器获取 Bean（@Autowired），不要 new。
