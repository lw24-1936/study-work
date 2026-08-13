---
title: Spring 面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [spring面试, ioc, di, aop, bean生命周期, 循环依赖, 事务, 自动配置, bean作用域, beanfactory, factorybean, spring事件, 设计模式]
---

# Spring 面试

整理日期：2026-08-13

## 目录

- [IoC 与 DI](#ioc-与-di)
- [AOP](#aop)
- [Bean 生命周期](#bean-生命周期)
- [Bean 作用域](#bean-作用域)
- [BeanFactory 与 ApplicationContext](#beanfactory-与-applicationcontext)
- [循环依赖](#循环依赖)
- [事务](#事务)
- [自动配置](#自动配置)
- [@Autowired 与 @Resource](#autowired-与-resource)
- [FactoryBean 与 BeanFactory](#factorybean-与-beanfactory)
- [Spring 事件机制](#spring-事件机制)
- [Spring 用到的设计模式](#spring-用到的设计模式)
- [面试重点总结](#面试重点总结)

## IoC 与 DI

**问题 1：什么是 IoC？**

```text
IoC（控制反转）：对象创建和依赖管理的控制权从代码转移到容器。

传统：对象自己 new 依赖（控制权在对象）
IoC：容器创建对象并注入依赖（控制权在容器）
```

```java
// 传统：自己 new
UserService service = new UserService(new UserRepository());

// IoC：容器注入
@Service
public class UserService {
    @Autowired
    private UserRepository repository;
}
```

**问题 2：什么是 DI？依赖注入的方式？**

```text
DI（依赖注入）是 IoC 的实现方式，三种：
1. 构造器注入（推荐，不可变 + 依赖明确 + 便于测试）
2. Setter 注入（可选依赖）
3. 字段注入（@Autowired 字段，不推荐，隐藏依赖、难测试）
```

```java
// 构造器注入（推荐）
@Service
public class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

**问题 3：IoC 容器是如何工作的？**

```text
1. 读取配置（注解/XML）得到 Bean 定义（BeanDefinition）
2. 反射创建 Bean 实例
3. 解析依赖，注入依赖
4. 生命周期管理（初始化、销毁）
5. 容器持有 Bean 供使用
```

## AOP

**问题 1：什么是 AOP？**

```text
AOP（面向切面编程）：把横切逻辑（日志、事务、权限、缓存）从业务代码中分离。

横切关注点：散布在多个方法中的重复逻辑，与核心业务无关。
```

**问题 2：AOP 的实现原理？**

```text
AOP 基于动态代理：
1. JDK 动态代理 —— 目标类实现接口时用（Proxy + InvocationHandler）
2. CGLIB —— 目标类无接口时用（生成子类，ASM 字节码）

Spring 在 Bean 初始化后（BeanPostProcessor 后置处理）生成代理对象。
Spring Boot 2.x 默认 CGLIB，proxy-target-class=true。
```

```text
JDK 动态代理 vs CGLIB：
JDK 动态代理 —— 只能代理接口，性能略好，基于反射
CGLIB —— 可代理类，通过生成子类，final 类/方法无法代理
```

**问题 3：AOP 的五个通知类型？**

```text
1. 前置通知 @Before —— 方法执行前
2. 后置通知 @AfterReturning —— 方法正常返回后
3. 异常通知 @AfterThrowing —— 方法抛异常后
4. 最终通知 @After —— 方法执行后（无论成败，finally 语义）
5. 环绕通知 @Around —— 前后都可控制（最强大，可决定是否执行）
```

```text
执行顺序：@Around 前 → @Before → 方法 → @Around 后 → @After → @AfterReturning
异常时：@AfterThrowing 替代 @AfterReturning
```

**问题 4：AOP 的相关概念？**

```text
1. 切面（Aspect）—— 横切逻辑的类（@Aspect）
2. 通知（Advice）—— 切面里的方法
3. 切点（Pointcut）—— 匹配哪些方法（切点表达式）
4. 连接点（JoinPoint）—— 可切入的点（Spring 只支持方法）
5. 织入（Weaving）—— 把通知应用到目标对象
```

## Bean 生命周期

**问题 1：Spring Bean 的生命周期？**

```text
1. 实例化（构造器/工厂方法 new 对象）
2. 属性填充（依赖注入）
3. Aware 接口回调（BeanNameAware/BeanFactoryAware/ApplicationContextAware）
4. BeanPostProcessor.postProcessBeforeInitialization
5. @PostConstruct 初始化
6. InitializingBean.afterPropertiesSet
7. BeanPostProcessor.postProcessAfterInitialization（AOP 代理在这里生成）
8. Bean 就绪使用
9. 容器关闭 → @PreDestroy → DisposableBean.destroy
```

**问题 2：@PostConstruct 和 afterPropertiesSet 的区别？**

```text
@PostConstruct —— 注解方式，JSR-250 标准，Spring 支持
afterPropertiesSet —— InitializingBean 接口方式

执行顺序：@PostConstruct → afterPropertiesSet（都用于初始化）
推荐用 @PostConstruct（不耦合 Spring 接口）。
```

**问题 3：BeanPostProcessor 的作用？**

```text
BeanPostProcessor 是 Bean 后置处理器，所有 Bean 初始化前后都会经过它：
1. postProcessBeforeInitialization —— 初始化前（可改 Bean 定义）
2. postProcessAfterInitialization —— 初始化后（AOP 代理、@Autowired 解析等）

AOP 就是 AbstractAutoProxyCreator 这个 BeanPostProcessor 实现的。
```

## Bean 作用域

**问题：Bean 的作用域有哪些？**

```text
1. singleton —— 单例，默认（一个容器一个实例）
2. prototype —— 原型，每次获取新建实例（Spring 不管理销毁）
3. request —— 每个 HTTP 请求一个实例（Web）
4. session —— 每个会话一个实例（Web）
5. application —— 每个 ServletContext 一个实例（Web）
6. websocket —— 每个 WebSocket 一个实例
```

```text
单例 Bean 的线程安全问题：
单例 Bean 本身无状态（不存可变字段）则线程安全；
存了可变字段则要考虑线程安全（如用 ThreadLocal 隔离）。
```

## BeanFactory 与 ApplicationContext

**问题：BeanFactory 和 ApplicationContext 的区别？**

| 维度 | BeanFactory | ApplicationContext |
|------|-------------|-------------------|
| 关系 | 底层接口 | 继承 BeanFactory |
| 加载时机 | 懒加载（getBean 才创建） | 启动时预加载单例（可配置懒） |
| 功能 | 基础 IoC | 额外：AOP、事件、国际化、资源加载、环境 |

```text
ApplicationContext 扩展功能：
1. 事件发布（ApplicationEvent）
2. 国际化（MessageSource）
3. 资源加载（ResourceLoader）
4. 环境抽象（Environment/Profile）
5. 注解支持（@Autowired）
```

## 循环依赖

**问题 1：什么是循环依赖？**

```text
循环依赖：A 依赖 B，B 依赖 A（直接或间接）。

Spring 只能解决单例 Bean 的 Setter 注入循环依赖。
构造器注入、prototype 作用域的循环依赖无法解决。
```

**问题 2：Spring 如何解决循环依赖？**

```text
三级缓存解决（只解决单例 Setter 注入）：

一级缓存（singletonObjects）—— 完整 Bean
二级缓存（earlySingletonObjects）—— 早期 Bean（已实例化未填充）
三级缓存（singletonFactories）—— ObjectFactory（可生成早期代理）

流程：
1. A 创建 → 实例化 → 提前暴露三级缓存（存 A 的 ObjectFactory）
2. A 填充属性 → 发现依赖 B → 创建 B
3. B 填充属性 → 发现依赖 A → 从三级缓存拿到 A 的早期引用
4. B 创建完成 → A 也创建完成
```

**问题 3：为什么是三级缓存，二级够吗？**

```text
三级缓存的 ObjectFactory 是为了延迟处理 AOP：
如果 A 需要 AOP 代理，早期暴露的应是代理对象而非原对象。
三级缓存存工厂，在需要时才调用工厂生成（普通对象或代理对象），
二级缓存存生成的结果。若只用二级缓存，无法在早期阶段灵活决定是否代理。
```

```text
为什么构造器注入解决不了循环依赖：
构造器注入时对象还没实例化完成，无法提前暴露到缓存。
可用 @Lazy 让依赖延迟注入，打破构造器循环。
```

## 事务

**问题 1：Spring 事务的原理？**

```text
事务通过 AOP 实现：
1. @Transactional 注解 → 切点
2. 事务切面（TransactionInterceptor）拦截方法
3. 通过 PlatformTransactionManager 管理：开启事务 → 执行业务 → 提交/回滚
4. 底层依赖数据库连接（Connection）的事务控制
```

**问题 2：事务的传播行为？**

```text
1. REQUIRED —— 有事务加入，无则新建（默认）
2. REQUIRES_NEW —— 总是新建独立事务，挂起当前事务
3. NESTED —— 嵌套事务（保存点 Savepoint，可部分回滚）
4. SUPPORTS —— 有则加入，无则非事务
5. NOT_SUPPORTED —— 以非事务执行，挂起当前事务
6. MANDATORY —— 必须有事务，无则抛异常
7. NEVER —— 必须非事务，有则抛异常
```

**问题 3：事务的隔离级别？**

```text
1. DEFAULT —— 使用数据库默认
2. READ_UNCOMMITTED —— 读未提交（脏读）
3. READ_COMMITTED —— 读已提交（不可重复读）
4. REPEATABLE_READ —— 可重复读（MySQL 默认）
5. SERIALIZABLE —— 串行化
```

**问题 4：事务失效的场景？**

```text
1. 方法不是 public（代理无法拦截非 public）
2. 同类方法自调用（this.xxx() 不走代理，事务失效）
3. 异常被 catch 吞掉（事务感知不到异常）
4. 抛受检异常（默认只回滚 RuntimeException 和 Error，需 rollbackFor 指定）
5. 类没有被 Spring 管理（不是 Bean）
6. 数据库引擎不支持事务（MyISAM）
7. 传播行为配置不当（NOT_SUPPORTED/NEVER）
```

```java
// 正确指定回滚异常
@Transactional(rollbackFor = Exception.class)
public void save() { }
```

## 自动配置

**问题：Spring Boot 自动配置的原理？**

```text
1. @SpringBootApplication → @EnableAutoConfiguration
2. @EnableAutoConfiguration → 导入 AutoConfigurationImportSelector
3. 加载 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
4. 每个自动配置类用条件注解判断
5. 满足条件 → 创建默认 Bean
6. @ConditionalOnMissingBean 允许用户自定义覆盖
```

## @Autowired 与 @Resource

**问题：@Autowired 和 @Resource 的区别？**

| 维度 | @Autowired | @Resource |
|------|-----------|-----------|
| 来源 | Spring | JSR-250（JDK） |
| 注入方式 | 默认按类型（byType） | 默认按名称（byName） |
| 多个同类型 | 配合 @Qualifier 指定 | 用 name 属性指定 |
| required | 可设 required=false | 默认必须存在 |

```text
@Autowired 按类型注入，多个同类型 Bean 时需 @Qualifier 指定名称。
@Resource 默认按字段名/name 查找，找不到再按类型。
```

## FactoryBean 与 BeanFactory

**问题：FactoryBean 和 BeanFactory 的区别？**

```text
BeanFactory —— IoC 容器，管理 Bean 的工厂（容器本身）
FactoryBean —— 特殊的 Bean，用于定制 Bean 创建过程

FactoryBean：getBean("&name") 返回 FactoryBean 本身，getBean("name") 返回 getObject() 产物。
典型应用：MyBatis 的 SqlSessionFactoryBean、@FeignClient 的代理生成。
```

```java
public class MyFactoryBean implements FactoryBean<User> {
    @Override
    public User getObject() { return new User(); }   // 返回的 Bean
    @Override
    public Class<?> getObjectType() { return User.class; }
    @Override
    public boolean isSingleton() { return true; }
}
```

## Spring 事件机制

**问题：Spring 的事件机制？**

```text
Spring 事件基于观察者模式：
1. 定义事件 —— 继承 ApplicationEvent
2. 发布事件 —— ApplicationEventPublisher.publishEvent()
3. 监听事件 —— @EventListener 或实现 ApplicationListener
4. @Async + @EventListener 实现异步事件
```

```java
// 定义事件
public class UserRegisterEvent extends ApplicationEvent {
    public UserRegisterEvent(User source) { super(source); }
}

// 监听
@EventListener
public void handleUserRegister(UserRegisterEvent event) { sendEmail(); }

// 发布
eventPublisher.publishEvent(new UserRegisterEvent(user));
```

```text
应用场景：注册后发邮件、订单支付后通知、解耦业务模块。
注意：默认同步执行，异步需 @Async。
```

## Spring 用到的设计模式

**问题：Spring 用了哪些设计模式？**

```text
1. 工厂模式 —— BeanFactory/FactoryBean
2. 单例模式 —— 单例 Bean（容器内单例）
3. 代理模式 —— AOP 动态代理
4. 模板方法模式 —— JdbcTemplate、RestTemplate、AbstractApplicationContext
5. 观察者模式 —— 事件监听
6. 适配器模式 —— HandlerAdapter、AdvisorAdapter
7. 装饰器模式 —— BeanWrapper、HttpServletRequestWrapper
8. 策略模式 —— 资源访问 Resource 的不同实现
9. 建造者模式 —— BeanDefinitionBuilder
```

## 面试重点总结

```text
高频考点：
1. IoC/DI 概念 + 三种注入方式（必考）
2. AOP 原理（动态代理）+ 通知类型（必考）
3. Bean 生命周期（必考）
4. Bean 作用域 + 单例线程安全
5. BeanFactory vs ApplicationContext
6. 循环依赖 + 三级缓存（必考）
7. 事务传播行为 + 失效场景（必考）
8. 自动配置原理
9. @Autowired vs @Resource
10. FactoryBean vs BeanFactory
11. Spring 事件机制
12. Spring 用到的设计模式
```
