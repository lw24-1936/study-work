---
title: Spring 基础
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring, ioc, di, bean, applicationcontext, beanfactory, lifecycle, scope, singleton, prototype]
---

# Spring 基础

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Spring Framework 体系](#spring-framework-体系)
- [IoC —— 控制反转](#ioc--控制反转)
- [DI —— 依赖注入](#di--依赖注入)
- [JSR-330 标准注解](#jsr-330-标准注解)
- [Bean 定义与注册](#bean-定义与注册)
- [Bean 定义继承](#bean-定义继承)
- [BeanFactory 与 ApplicationContext](#beanfactory-与-applicationcontext)
- [Bean 生命周期](#bean-生命周期)
- [Bean Scope](#bean-scope)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Framework 是 Java 领域最核心的基础框架，2003 年由 Rod Johnson 创建，初衷是解决 EJB 过度复杂的问题。它的核心思想是 **IoC（控制反转）**——把对象创建和管理的控制权从开发者手中交给框架。

Spring 不是一个单一产品，而是一个生态。Spring Framework 是地基，Spring Boot 是脚手架，Spring Cloud 是分布式工具箱。理解 Spring Framework 的核心（IoC、AOP、事务）是掌握整个 Spring 生态的前提。

## Spring Framework 体系

Spring Framework 采用分层架构，核心模块如下：

```text
┌─────────────────────────────────────────────────────┐
│                   Spring Framework                    │
├─────────────┬─────────────┬─────────────┬────────────┤
│  数据访问    │   Web       │   AOP       │  核心容器   │
│  JDBC       │  MVC        │  Aspects    │  Beans     │
│  ORM        │  WebSocket  │  Instrument │  Core      │
│  OXM        │  WebFlux    │  Messaging  │  Context   │
│  JMS        │  Servlet    │             │  SpEL      │
│  TX         │             │             │            │
├─────────────┴─────────────┴─────────────┴────────────┤
│                     Test                              │
└─────────────────────────────────────────────────────┘
```

**核心容器（Core Container）** 是最基础的模块，包含：
- **spring-core**：IoC 基础，依赖注入的实现
- **spring-beans**：Bean 的定义、创建、管理（BeanFactory）
- **spring-context**：ApplicationContext，在 BeanFactory 之上增加了国际化、事件、资源加载
- **spring-expression**：SpEL 表达式语言

本文聚焦核心容器中的 IoC、DI、Bean 管理三大基础概念。

## IoC —— 控制反转

### 概念

IoC（Inversion of Control）是一种设计思想，不是 Spring 发明的，但 Spring 是 Java 领域最知名的 IoC 实践。理解它需要对比传统方式：

**传统方式（控制在自己手中）**：

```java
public class UserService {
    private UserDao userDao;

    public UserService() {
        // 自己创建依赖对象 —— 控制权在自己手中
        this.userDao = new UserDaoImpl();
    }
}
```

**IoC 方式（控制权交给容器）**：

```java
public class UserService {
    private UserDao userDao;

    // 依赖由外部注入 —— 控制权在容器手中
    public UserService(UserDao userDao) {
        this.userDao = userDao;
    }
}
```

核心转变：**"谁创建对象"的控制权从调用方转移到 Spring 容器**。开发者不再 new 对象，而是告诉容器"我需要什么"，容器负责装配。

### IoC 容器

Spring IoC 容器是一个对象工厂，负责：

1. **读取配置元数据**（XML、注解、Java Config）
2. **创建 Bean 实例**（通过反射）
3. **装配依赖**（通过依赖注入）
4. **管理 Bean 生命周期**（初始化、销毁回调）
5. **提供 Bean 查询**（按名称或类型获取）

```java
// 最简示例
ApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
UserService userService = context.getBean(UserService.class);
userService.doSomething();
```

### IoC 的两种实现

| 方式 | 说明 | 容器 |
|------|------|------|
| BeanFactory | 最底层的 IoC 容器，懒加载，功能较基础 | DefaultListableBeanFactory |
| ApplicationContext | BeanFactory 的子接口，功能更丰富（国际化、事件、资源加载） | AnnotationConfigApplicationContext、ClassPathXmlApplicationContext |

实际开发中几乎只用 ApplicationContext，BeanFactory 仅在内存极度受限的嵌入式场景使用。

## DI —— 依赖注入

DI（Dependency Injection）是 IoC 的具体实现方式。Spring 支持三种注入方式。

### 1. 构造器注入（推荐）

```java
@Component
public class UserService {

    private final UserDao userDao;  // final，强制不可变

    public UserService(UserDao userDao) {  // 构造器注入
        this.userDao = userDao;
    }
}
```

Spring 4.3+ 中，如果只有一个构造器，可以省略 `@Autowired`。构造器注入的优点：
- 依赖不可变（final）
- 注入的依赖在使用前一定存在（编译时保证）
- 方便单元测试（直接 new 传入 mock）

### 2. Setter 注入

```java
@Component
public class UserService {

    private UserDao userDao;

    @Autowired
    public void setUserDao(UserDao userDao) {  // setter 注入
        this.userDao = userDao;
    }
}
```

适合**可选依赖**场景。但如果依赖是必需的，构造器注入更好。

### 3. 字段注入（不推荐）

```java
@Component
public class UserService {
    @Autowired
    private UserDao userDao;  // 字段注入 —— 不推荐
}
```

字段注入的问题：
- 依赖不可见（从外部看不知道这个类依赖什么）
- 不能声明为 final
- 强依赖 Spring 容器，单元测试麻烦（需要反射注入）
- 容易导致循环依赖隐藏不报错

```java
// 字段注入的单元测试需要反射
UserService service = new UserService();
ReflectionTestUtils.setField(service, "userDao", mockUserDao);

// 构造器注入的单元测试很简单
UserService service = new UserService(mockUserDao);
```

### @Autowired 注入规则

Spring 的 `@Autowired` 按以下优先级匹配：

1. **按类型（byType）匹配**：在容器中查找类型匹配的 Bean
2. 同类型有多个时，**按名称（byName）** 匹配字段名/参数名
3. 仍无法确定时，配合 `@Qualifier` 指定

```java
// 按类型 —— 容器中只有一个 UserDao 实现
@Autowired
private UserDao userDao;

// 按名称 —— 容器中有多个 UserDao 类型时，字段名 "mysqlUserDao" 决定注入哪个
@Autowired
private UserDao mysqlUserDao;

// @Qualifier 明确指定 —— 最清晰的方式
@Autowired
@Qualifier("mysqlUserDao")
private UserDao userDao;

// @Primary —— 在 Bean 定义处声明首选
@Repository
@Primary
public class MysqlUserDao implements UserDao {}
```

### @Resource vs @Autowired

| 维度 | @Autowired | @Resource |
|------|-----------|-----------|
| 来源 | Spring 注解 | JSR-250（JDK 标准） |
| 默认匹配 | byType | byName |
| 配合 | @Qualifier | name 属性 |
| 是否必须 | required=false | 没有类似配置 |

```java
@Autowired(required = false)   // 找不到也不报错
private UserDao userDao;

@Resource(name = "mysqlUserDao")  // 按名称指定
private UserDao userDao;
```

`@Resource` 在名称找不到时会退化为 byType。大多数项目直接使用 `@Autowired`，只有需要 JSR 标准时才用 `@Resource`。

### 注入集合类型

Spring 支持自动注入同类型的所有 Bean：

```java
@Component
public class ValidatorChain {
    // 注入所有 Validator 类型的 Bean，放入 List
    @Autowired
    private List<Validator> validators;

    // 注入所有 Validator 类型的 Bean，放入 Map（key=beanName）
    @Autowired
    private Map<String, Validator> validatorMap;

    public void validate(Object target) {
        validators.forEach(v -> v.validate(target));
    }
}

// 定义多个 Validator 实现
@Component
public class NotNullValidator implements Validator {}

@Component
public class EmailValidator implements Validator {}

@Component
public class PhoneValidator implements Validator {}
```

这个模式在处理责任链、策略模式时很常用。

### 泛型作为限定符

Spring 4.0+ 支持用泛型类型作为自动装配的限定符。当容器中存在多个同类型的 Bean 时，泛型信息可以帮助精确匹配：

```java
@Configuration
public class StoreConfig {

    @Bean
    public Store<String> stringStore() {
        return new StringStore();
    }

    @Bean
    public Store<Integer> integerStore() {
        return new IntegerStore();
    }
}

// 自动装配时，根据字段的泛型类型精确匹配
@Component
public class StoreService {
    @Autowired
    private Store<String> stringStore;    // 注入 stringStore
    @Autowired
    private Store<Integer> integerStore;  // 注入 integerStore

    // 注入所有 Store 类型，泛型也会被保留
    @Autowired
    private List<Store<String>> stringStores;
}
```

泛型限定符是对 `@Qualifier` 的补充，在"一个接口多个泛型实现"的场景下非常有用（如 `Handler<T>`、`Converter<S,T>`）。

## JSR-330 标准注解

除了 Spring 自有的 `@Autowired`、`@Component`，Spring 也支持 JSR-330（Dependency Injection for Java）标准注解。这套注解来自 `javax.inject` / `jakarta.inject` 包。

| Spring 注解 | JSR-330 注解 | 说明 |
|------------|-------------|------|
| @Autowired | @Inject | 注入依赖 |
| @Component | @Named | 声明 Bean |
| @Qualifier | @Named / @Qualifier | 限定名称 |
| @Scope("singleton") | @Singleton | 单例作用域 |

### @Inject 与 @Autowired 的差异

```java
import jakarta.inject.Inject;
import jakarta.inject.Named;

@Named("userService")  // 等价于 @Component("userService")
public class UserService {

    private UserDao userDao;

    @Inject  // 等价于 @Autowired
    public UserService(UserDao userDao) {
        this.userDao = userDao;
    }
}

// @Inject 没有 required 属性，要表达"可选依赖"用 Optional
@Inject
public void setOptionalDao(Optional<UserDao> optionalDao) {
    // @Autowired(required=false) 的 JSR-330 等价写法
}

// @Inject 不支持 required=false，但 Spring 的 @Autowired 支持
@Autowired(required = false)
private UserDao userDao;
```

关键差异：

1. `@Inject` 没有 `required` 属性——Spring 的 `@Autowired(required=false)` 在 JSR-330 中需要用 `Optional<T>` 或 `@Nullable` 表达
2. `@Inject` 无法与 Spring 特有的 `@Lazy`、`@Primary` 组合使用（这两个是 Spring 专有）
3. `@Named` 没有 `@Component` 的衍生注解（@Service/@Repository/@Controller），语义区分弱
4. `@Named` 不带名称时，Bean 名称为类名首字母小写（与 @Component 一致）

```java
// @Named 与 @Inject 组合
@Named
public class OrderService {
    @Inject
    @Named("mysqlUserDao")  // 按名称限定
    private UserDao userDao;
}
```

**使用建议**：如果项目要求"只用标准注解，不依赖 Spring 专有 API"（便于切换 DI 框架，如 Guice），用 JSR-330；否则用 Spring 注解，功能更丰富。绝大多数 Spring 项目直接使用 `@Autowired`。

### Null-safety 注解

Spring 5 引入了 JSR-305 的 `@NonNull`、`@Nullable` 注解（`org.springframework.lang` 包），用于标注方法参数和返回值的可空性：

```java
import org.springframework.lang.NonNull;
import org.springframework.lang.Nullable;

@Component
public class UserService {

    @NonNull  // 参数不允许为 null
    public User findById(@NonNull Long id) {
        return userDao.findById(id);
    }

    @Nullable  // 返回值可能为 null
    public User findByEmail(String email) {
        return userDao.findByEmail(email);
    }

    @Nullable  // 字段可能为 null（延迟注入）
    @Autowired(required = false)
    private MailSender mailSender;
}
```

作用：

1. **IDE 静态检查**：IntelliJ IDEA 会根据这些注解给出警告（如对 @NonNull 参数传 null）
2. **Kotlin 互操作**：Spring 会将这些注解映射为 Kotlin 的平台类型/null 安全类型
3. **文档化**：让调用方明确知道哪些参数/返回值可以为 null

注意：这些注解是**编译期提示**，Spring 在运行时不会强制检查（不会因为传 null 到 @NonNull 参数而抛异常）。运行时校验要用 `Objects.requireNonNull()` 或 Bean Validation。

## Bean 定义与注册

### 什么是 Bean

Spring 中的 Bean 就是**由 IoC 容器管理的对象**。不是所有对象都是 Bean——只有那些由容器创建、装配、管理的对象才叫 Bean。

```java
// 普通的 POJO —— 不是 Bean
User user = new User("张三");

// 由 Spring 容器管理的对象 —— 是 Bean
@Component
public class UserService {
    @Autowired
    private UserDao userDao;
}
```

Bean 的组成部分：
- **全限定类名**：com.example.UserService
- **Bean 名称**：默认类名首字母小写（userService），可自定义
- **作用域**：singleton / prototype / request / session
- **构造参数/属性值**：构造器注入或属性注入的值
- **行为配置**：初始化方法、销毁方法、懒加载等

### BeanDefinition

Spring 内部用 `BeanDefinition` 接口描述一个 Bean 的元数据：

```java
// BeanDefinition 本质上是 Bean 的"配方"——容器根据这个配方创建实例
public interface BeanDefinition {
    String getBeanClassName();         // 全限定类名
    String getScope();                  // singleton / prototype
    boolean isLazyInit();               // 是否懒加载
    String[] getDependsOn();            // 依赖的 Bean
    ConstructorArgumentValues getConstructorArgumentValues();
    MutablePropertyValues getPropertyValues();
    String getInitMethodName();         // 初始化方法
    String getDestroyMethodName();      // 销毁方法
    // ...
}
```

开发者通常不需要直接操作 BeanDefinition，但理解它有助于理解容器内部机制。

### 让类成为 Bean 的方式

Spring 提供了多种方式将类注册为 Bean。这些方式会在下一篇（Spring 配置）中详细展开，这里只做概述：

```java
// 方式 1：@Component 系列注解
@Component
public class UserService {}

@Repository
public class UserDao {}  // @Repository 语义更明确（持久层）

@Service
public class UserServiceImpl {}  // @Service 语义更明确（业务层）

// 方式 2：@Bean 方法
@Configuration
public class AppConfig {
    @Bean
    public DataSource dataSource() {
        return new HikariDataSource();
    }
}

// 方式 3：XML（传统方式，Spring Boot 项目中几乎不用）
// <bean id="userService" class="com.example.UserService"/>
```

`@Component`、`@Service`、`@Repository`、`@Controller` 本质相同——都是让 Spring 扫描并注册为 Bean。区分它们的好处是语义清晰 + AOP 切入点可精确匹配。

## Bean 定义继承

Bean 定义继承（Bean Definition Inheritance）允许一个 Bean 定义继承另一个 Bean 定义的配置，类似类继承。子 Bean 复用父 Bean 的属性，并可以覆盖。

这个概念在现代注解驱动的项目中很少用（XML 时代的产物），但理解它有助于阅读遗留配置，也是 Spring 面试的经典考点。

```xml
<!-- 抽象父 Bean：不实例化，只作为配置模板 -->
<bean id="baseDataSource" class="org.apache.commons.dbcp2.BasicDataSource"
      abstract="true">
    <property name="driverClassName" value="com.mysql.cj.jdbc.Driver" />
    <property name="username" value="root" />
    <property name="password" value="secret" />
    <property name="maxTotal" value="20" />
</bean>

<!-- 子 Bean：继承父配置，只覆盖差异部分 -->
<bean id="orderDataSource" parent="baseDataSource">
    <property name="url" value="jdbc:mysql://localhost:3306/order_db" />
</bean>

<bean id="userDataSource" parent="baseDataSource">
    <property name="url" value="jdbc:mysql://localhost:3306/user_db" />
</bean>
```

关键特性：

1. **abstract Bean 不会被实例化**，只能作为模板被继承
2. 子 Bean 可以**覆盖**父 Bean 的任意属性
3. 子 Bean 继承父 Bean 的：scope、构造参数、属性值、init/destroy 方法、依赖（depends-on）等
4. 子 Bean 的 class 如果省略，继承父 Bean 的 class；如果指定，则必须与父 Bean 兼容
5. 父 Bean 本身也可以是具体的（非 abstract），此时父 Bean 既能独立使用又能被继承

注解时代的替代方案：用 `@Configuration` 类中的 `@Bean` 方法参数传递，或者用 `@ConfigurationProperties` + 组合来复用配置。Bean 定义继承本质上是"配置复用"，现代 Spring 有更好的方式（如 `@Profile` + `@Conditional` + 配置属性类）。

## BeanFactory 与 ApplicationContext

### 继承关系

```text
BeanFactory (接口 —— IoC 容器的最底层抽象)
    |
    +-- ApplicationContext (接口 —— 扩展了更多企业级功能)
            |
            +-- ConfigurableApplicationContext
                    |
                    +-- AnnotationConfigApplicationContext (注解驱动)
                    +-- ClassPathXmlApplicationContext   (XML 驱动)
                    +-- GenericWebApplicationContext     (Web 环境)
```

### BeanFactory

```java
// BeanFactory 核心方法
BeanFactory factory = new DefaultListableBeanFactory();
// ... 加载 BeanDefinition ...

Object bean = factory.getBean("userService");          // 按名称
UserService service = factory.getBean(UserService.class);  // 按类型
boolean exists = factory.containsBean("userService");
Class<?> type = factory.getType("userService");
boolean singleton = factory.isSingleton("userService");
boolean prototype = factory.isPrototype("userService");
String[] aliases = factory.getAliases("userService");
```

BeanFactory 特性：
- **懒加载**：getBean() 时才创建实例
- 功能精简：不提供国际化、事件发布、AOP 自动代理等
- 很少直接使用（Spring Boot 中全部用 ApplicationContext）

### ApplicationContext

ApplicationContext 是 BeanFactory 的超集，额外提供：

**1. 国际化（MessageSource）**

```java
// 读取 messages_zh_CN.properties 中的 welcome 键
String msg = context.getMessage("welcome", new Object[]{"张三"}, Locale.CHINA);
```

**2. 事件发布（ApplicationEventPublisher）**

```java
// 发布事件
@Component
public class OrderService {
    @Autowired
    private ApplicationEventPublisher publisher;

    public void createOrder(Order order) {
        // 保存订单...
        publisher.publishEvent(new OrderCreatedEvent(this, order));
    }
}

// 监听事件
@Component
public class EmailListener {
    @EventListener
    public void handleOrderCreated(OrderCreatedEvent event) {
        Order order = event.getOrder();
        // 发送邮件通知
    }
}

// 自定义事件
public class OrderCreatedEvent extends ApplicationEvent {
    private final Order order;
    public OrderCreatedEvent(Object source, Order order) {
        super(source);
        this.order = order;
    }
    public Order getOrder() { return order; }
}
```

**3. 资源加载（ResourceLoader）**

```java
// 加载 classpath 下文件
Resource resource = context.getResource("classpath:application.properties");
// 加载文件系统文件
Resource resource = context.getResource("file:/opt/config/app.properties");
// 加载 URL
Resource resource = context.getResource("https://example.com/config.json");
```

### AnnotationConfigApplicationContext

Spring Boot 内部使用的就是它（或 GenericWebApplicationContext），通过扫描注解来注册 Bean：

```java
// 手动启动 Spring 容器
AnnotationConfigApplicationContext context =
    new AnnotationConfigApplicationContext(AppConfig.class);

UserService service = context.getBean(UserService.class);
service.doSomething();

context.close();  // 触发 Bean 的 destroy 回调
```

### 容器启动流程

```text
1. new AnnotationConfigApplicationContext(AppConfig.class)
2.   创建 AnnotatedBeanDefinitionReader（读取 @Configuration 类）
3.   创建 ClassPathBeanDefinitionScanner（扫描 @Component 类）
4.   register(annotatedClasses) —— 注册配置类
5.   refresh() —— 核心方法，完成以下步骤：
     5.1   prepareRefresh() —— 准备环境
     5.2   obtainFreshBeanFactory() —— 创建 BeanFactory
     5.3   prepareBeanFactory() —— 配置 BeanFactory
     5.4   postProcessBeanFactory() —— BeanFactory 后处理
     5.5   invokeBeanFactoryPostProcessors() —— 执行 BeanFactoryPostProcessor（如 @Configuration 解析）
     5.6   registerBeanPostProcessors() —— 注册 BeanPostProcessor
     5.7   initMessageSource() —— 初始化消息源
     5.8   initApplicationEventMulticaster() —— 初始化事件广播器
     5.9   onRefresh() —— 留给子类的钩子（Spring Boot 在这里启动 Web 服务器）
     5.10  registerListeners() —— 注册事件监听器
     5.11  finishBeanFactoryInitialization() —— 实例化所有非懒加载的单例 Bean
     5.12  finishRefresh() —— 完成刷新，发布 ContextRefreshedEvent
```

`refresh()` 是 Spring 容器最核心的方法，理解它对排查启动问题很有帮助。

## Bean 生命周期

Spring Bean 从创建到销毁经历了完整的生命周期。了解这个生命周期对于理解 Spring 的扩展点和排查问题至关重要。

### 完整生命周期

```text
1. 实例化 —— 通过构造器/工厂方法创建对象
      |
2. 属性填充 —— 依赖注入（@Autowired、setter）
      |
3. BeanNameAware.setBeanName() —— 让 Bean 知道自己的名字
      |
4. BeanFactoryAware.setBeanFactory() —— 让 Bean 知道所属的 BeanFactory
      |
5. ApplicationContextAware.setApplicationContext() —— 让 Bean 知道所属的 ApplicationContext
      |
6. BeanPostProcessor.postProcessBeforeInitialization() —— 初始化前处理
      |
7. @PostConstruct —— JSR-250 规范的初始化回调
      |
8. InitializingBean.afterPropertiesSet() —— Spring 接口的初始化回调
      |
9. @Bean(initMethod) —— 自定义初始化方法
      |
10. BeanPostProcessor.postProcessAfterInitialization() —— 初始化后处理（AOP 代理在这里生成）
      |
11. Bean 就绪 —— 可正常使用
      |
12. @PreDestroy —— JSR-250 规范的销毁回调
      |
13. DisposableBean.destroy() —— Spring 接口的销毁回调
      |
14. @Bean(destroyMethod) —— 自定义销毁方法
```

### 关键扩展点

**1. Aware 接口族**

让 Bean 获取容器基础设施：

```java
@Component
public class MyBean implements ApplicationContextAware, BeanNameAware {

    private ApplicationContext applicationContext;
    private String beanName;

    @Override
    public void setBeanName(String name) {
        this.beanName = name;
        System.out.println("我的名字是：" + name);
    }

    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        this.applicationContext = ctx;
        // 现在可以编程式获取其他 Bean
        OtherBean other = ctx.getBean(OtherBean.class);
    }
}

// 常用 Aware 接口：
// BeanNameAware           —— 获取 Bean 名称
// BeanFactoryAware        —— 获取 BeanFactory
// ApplicationContextAware —— 获取 ApplicationContext
// EnvironmentAware        —— 获取 Environment（环境变量/配置）
// ResourceLoaderAware     —— 获取 ResourceLoader
// MessageSourceAware      —— 获取 MessageSource
```

注意：使用 Aware 会让 Bean 与 Spring 耦合。大多数场景下直接注入需要的 Bean 更好，不需要 Aware。

**2. BeanPostProcessor（BPP）**

容器级别的扩展点，影响**所有** Bean 的初始化过程：

```java
@Component
public class LoggingBeanPostProcessor implements BeanPostProcessor {

    @Override
    public Object postProcessBeforeInitialization(Object bean, String beanName) {
        // 初始化前 —— 可以对 Bean 做任何处理
        return bean;  // 返回原始 Bean 或包装
    }

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        // 初始化后 —— AOP 代理就是在这里创建的
        if (needProxy(bean)) {
            return createProxy(bean);  // 返回代理对象
        }
        return bean;
    }
}
```

BeanPostProcessor 是 Spring AOP 的实现基础——`AbstractAutoProxyCreator` 就是一个 BeanPostProcessor，在 `postProcessAfterInitialization` 中判断是否需要创建代理。

**补充：BeanFactoryPostProcessor（BFP）**

BeanFactoryPostProcessor 是 BeanPostProcessor 的"前辈"——它在**所有 Bean 实例化之前**执行，操作的是 BeanDefinition 而不是 Bean 实例。

```java
@Component
public class CustomBeanFactoryPostProcessor implements BeanFactoryPostProcessor {

    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // 在 Bean 实例化之前，可以修改 BeanDefinition
        BeanDefinition bd = beanFactory.getBeanDefinition("userService");
        bd.setScope(ConfigurableBeanFactory.SCOPE_PROTOTYPE);
        bd.setLazyInit(true);
    }
}
```

两者对比：

| 维度 | BeanFactoryPostProcessor | BeanPostProcessor |
|------|-------------------------|-------------------|
| 执行时机 | Bean 实例化**之前** | Bean 初始化**前后** |
| 操作对象 | BeanDefinition（元数据） | Bean 实例 |
| 典型实现 | PropertySourcesPlaceholderConfigurer（解析 @Value 占位符）、ConfigurationClassPostProcessor（解析 @Configuration） | AbstractAutoProxyCreator（AOP 代理） |

`@Value("${...}")` 的占位符解析就是由 `PropertySourcesPlaceholderConfigurer`（一个 BFP）完成的——它在 Bean 实例化前扫描所有 BeanDefinition，把 `${...}` 替换为实际值。这也是为什么 `@Value` 注入在属性填充阶段能拿到值。

**3. @PostConstruct 和 @PreDestroy**

最简单、最推荐的生命周期回调方式：

```java
@Component
public class DatabaseConnectionPool {

    @PostConstruct
    public void init() {
        System.out.println("初始化连接池...");
        // 创建连接
    }

    @PreDestroy
    public void cleanup() {
        System.out.println("关闭连接池...");
        // 释放连接
    }
}
```

**三种初始化回调的优先级**：`@PostConstruct` > `InitializingBean.afterPropertiesSet()` > `@Bean(initMethod = "...")`

**注意**：`@PostConstruct` 要求依赖注入已完成的 Bean 实例。prototype 作用域的 Bean 销毁时不会调用 `@PreDestroy`——Spring 不管理 prototype Bean 的完整生命周期。

### 生命周期示例

```java
@Component
public class LifecycleDemo implements InitializingBean, DisposableBean,
        BeanNameAware, ApplicationContextAware {

    public LifecycleDemo() {
        System.out.println("1. 构造方法");
    }

    @Autowired
    public void setOtherBean(OtherBean other) {
        System.out.println("2. 依赖注入");
    }

    @Override
    public void setBeanName(String name) {
        System.out.println("3. BeanNameAware: " + name);
    }

    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        System.out.println("4. ApplicationContextAware");
    }

    @PostConstruct
    public void postConstruct() {
        System.out.println("5. @PostConstruct");
    }

    @Override
    public void afterPropertiesSet() {
        System.out.println("6. InitializingBean.afterPropertiesSet()");
    }

    @PreDestroy
    public void preDestroy() {
        System.out.println("7. @PreDestroy");
    }

    @Override
    public void destroy() {
        System.out.println("8. DisposableBean.destroy()");
    }
}
```

## Bean Scope

Bean Scope 决定了 Bean 实例的创建策略和生命周期。Spring 提供了多种作用域。

### 1. Singleton（默认）

```java
@Component
@Scope("singleton")  // 默认值，可省略
public class SingletonBean {}
```

- 每个 IoC 容器中**只有一个实例**
- 容器启动时创建（非懒加载），随容器销毁而销毁
- **线程不安全**——多线程共享同一个实例，不能使用成员变量存储请求状态
- 适合无状态的 Bean（Service、Dao、Controller）

```java
ApplicationContext ctx = ...;
SingletonBean b1 = ctx.getBean(SingletonBean.class);
SingletonBean b2 = ctx.getBean(SingletonBean.class);
System.out.println(b1 == b2);  // true —— 同一个实例
```

### 2. Prototype

```java
@Component
@Scope("prototype")
public class PrototypeBean {}
```

- **每次获取都创建新实例**
- 容器只负责创建，不负责销毁（不会调用 destroy 方法）
- 适合有状态的 Bean（如每次请求需要独立状态的工具类）

```java
PrototypeBean b1 = ctx.getBean(PrototypeBean.class);
PrototypeBean b2 = ctx.getBean(PrototypeBean.class);
System.out.println(b1 == b2);  // false —— 不同实例
```

### 3. Request（Web 环境）

```java
@Component
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestScopedBean {}
```

- 每个 HTTP 请求一个实例
- 请求结束时销毁
- 适合存储请求级别的数据（如当前用户信息）

### 4. Session（Web 环境）

```java
@Component
@Scope(value = "session", proxyMode = ScopedProxyMode.TARGET_CLASS)
public class SessionScopedBean {}
```

- 每个 HTTP Session 一个实例
- Session 结束时销毁
- 适合存储会话级别的数据（如购物车）

### 5. Application（Web 环境）

```java
@Component
@Scope("application")
public class ApplicationScopedBean {}
```

- 整个 Web 应用一个实例（与 Singleton 类似，但生命周期绑定 ServletContext）

### Singleton 注入 Prototype 的问题

```java
@Component
@Scope("singleton")
public class SingletonService {
    @Autowired
    private PrototypeBean prototypeBean;  // 只注入一次！

    public void doSomething() {
        // prototypeBean 始终是同一个实例 —— 因为 SingletonService 只创建一次
    }
}
```

**问题**：Singleton Bean 在创建时注入 Prototype Bean，此后 Singleton Bean 不销毁，Prototype Bean 也永远不会被重新创建——失去了 Prototype 的意义。

**解法 1：使用代理模式**

```java
@Component
@Scope(value = "prototype", proxyMode = ScopedProxyMode.TARGET_CLASS)
public class PrototypeBean {}
```

此时注入的是 CGLIB 代理对象，每次调用方法时代理会去容器获取新的 Prototype Bean。

**解法 2：注入 ObjectFactory / Provider**

```java
@Component
public class SingletonService {
    @Autowired
    private ObjectFactory<PrototypeBean> prototypeBeanFactory;

    public void doSomething() {
        PrototypeBean bean = prototypeBeanFactory.getObject();  // 每次获取新实例
    }
}
```

**解法 3：使用 @Lookup**

```java
@Component
public abstract class SingletonService {
    @Lookup
    protected abstract PrototypeBean getPrototypeBean();

    public void doSomething() {
        PrototypeBean bean = getPrototypeBean();  // 每次调用返回新实例
    }
}
```

`@Lookup` 相对优雅，但需要类声明为 abstract（或方法 abstract），加上依赖 Spring 的 CGLIB 代理。

推荐使用 ObjectFactory，侵入性最小。

## 应用场景实战

### 场景 1：使用 Aware 接口实现工具类获取 Spring Bean

在非 Spring 管理的类中获取 Bean：

```java
@Component
public class SpringContextHolder implements ApplicationContextAware {

    private static ApplicationContext context;

    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        context = ctx;
    }

    public static <T> T getBean(Class<T> clazz) {
        return context.getBean(clazz);
    }

    public static <T> T getBean(String name, Class<T> clazz) {
        return context.getBean(name, clazz);
    }

    public static <T> Map<String, T> getBeansOfType(Class<T> clazz) {
        return context.getBeansOfType(clazz);
    }
}

// 使用
public class NonSpringClass {
    public void doWork() {
        UserService userService = SpringContextHolder.getBean(UserService.class);
        userService.doSomething();
    }
}
```

### 场景 2：事件驱动解耦——订单完成后的异步通知

```java
// 事件定义
@Getter
public class OrderCompletedEvent extends ApplicationEvent {
    private final Long orderId;
    private final BigDecimal amount;

    public OrderCompletedEvent(Object source, Long orderId, BigDecimal amount) {
        super(source);
        this.orderId = orderId;
        this.amount = amount;
    }
}

// 发布事件
@Service
public class OrderService {

    @Autowired
    private ApplicationEventPublisher publisher;

    @Transactional
    public void completeOrder(Long orderId) {
        // 更新订单状态
        orderDao.markCompleted(orderId);

        // 发布事件 —— 解耦后续操作
        Order order = orderDao.findById(orderId);
        publisher.publishEvent(new OrderCompletedEvent(this,
            orderId, order.getAmount()));
    }
}

// 监听者 1：发送短信
@Component
public class SmsNotificationListener {

    @EventListener
    @Async  // 异步执行，不阻塞事务提交
    public void handleOrderCompleted(OrderCompletedEvent event) {
        System.out.println("发送短信通知：订单 " + event.getOrderId() + " 已完成");
    }
}

// 监听者 2：更新统计
@Component
public class StatisticsListener {

    @EventListener
    @Async
    public void handleOrderCompleted(OrderCompletedEvent event) {
        System.out.println("更新统计数据：金额 " + event.getAmount());
    }
}
```

Spring 事件机制的优势：发布者不需要知道有哪些监听者，新增监听者不影响发布者。但如果需要事务提交后才执行监听者，需要用 `@TransactionalEventListener` 而不是 `@EventListener`。

### 场景 3：BeanPostProcessor 实现耗时统计

```java
@Component
public class TimingBeanPostProcessor implements BeanPostProcessor {

    private final Map<String, Class<?>> targetInterfaces = Map.of(
        "UserService", UserService.class,
        "OrderService", OrderService.class
    );

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        Class<?> targetInterface = targetInterfaces.get(beanName);
        if (targetInterface == null) {
            return bean;
        }

        // 创建 JDK 动态代理，统计方法耗时
        return Proxy.newProxyInstance(
            bean.getClass().getClassLoader(),
            new Class[]{targetInterface},
            (proxy, method, args) -> {
                long start = System.currentTimeMillis();
                try {
                    return method.invoke(bean, args);
                } finally {
                    long cost = System.currentTimeMillis() - start;
                    System.out.println(beanName + "." + method.getName()
                        + "() cost " + cost + "ms");
                }
            }
        );
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **优先使用构造器注入**。依赖不可变、编译时安全、易于测试。

2. **Beans 要保持无状态**。Singleton Bean 中不要使用成员变量存储请求数据——这会导致线程安全问题。

3. **不要过度使用 Aware 接口**。让 Bean 与 Spring API 耦合会降低可测试性。大多数场景下直接注入需要的 Bean。

4. **事件发布放在事务方法末尾**。如果在事务提交前发布事件，监听者可能看到数据库中的未提交数据。使用 `@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)` 确保事务提交后再执行。

5. **Bean 命名使用语义化名称**。默认类名首字母小写在大多数情况下可行，但接口/实现类的命名容易产生歧义——用 `@Component("mysqlUserDao")` 明确命名。

### 踩坑记录

**坑 1：循环依赖**

```java
@Component
public class A {
    @Autowired
    private B b;  // A 依赖 B
}

@Component
public class B {
    @Autowired
    private A a;  // B 依赖 A
}
```

Spring 对构造器注入的循环依赖会直接报错 `BeanCurrentlyInCreationException`。字段注入的循环依赖（且都是 Singleton）可以解决——Spring 通过三级缓存（singletonFactories → earlySingletonObjects → singletonObjects）暴露早期引用。

解法：重新设计，打破循环。可以用 `@Lazy` 临时绕过，但本质问题没解决。

**坑 2：@Autowired 在 static 字段上不生效**

```java
@Component
public class Utils {
    @Autowired
    private static DataSource dataSource;  // 不生效！@Autowired 不支持 static
}
```

Spring 依赖注入是基于实例的，static 字段属于类级别。解法：用 setter 注入到静态字段，或使用 ApplicationContextAware。

**坑 3：prototype Bean 中 @PreDestroy 不触发**

```java
@Component
@Scope("prototype")
public class PrototypeBean {
    @PreDestroy
    public void cleanup() {
        System.out.println("永远不会打印");  // prototype Bean 的 destroy 不会被调用
    }
}
```

Spring 只管理 Singleton Bean 的完整生命周期。prototype Bean 创建后交给调用方，容器不再跟踪。需要显式调用销毁方法，或注册 `DestructionAwareBeanPostProcessor`。

**坑 4：过早初始化导致 @Value 注入失败**

```java
@Component
public class MyService {
    @Value("${app.api.key}")
    private String apiKey;

    private final List<String> whitelist = Arrays.asList(apiKey);  // apiKey 是 null！
}
```

成员变量的初始化在构造器调用时执行，早于 `@Value` 注入（注入在属性填充阶段）。如果要使用配置值初始化集合，放在 `@PostConstruct` 中。

**坑 5：ApplicationContext.getBean() 取 prototype 导致内存泄漏**

每次调用 `getBean()` 都会创建新的 prototype 实例，但容器不会销毁它。频繁调用会导致内存不可控增长。prototype 的使用者必须自己管理实例的生命周期。

**坑 6：@EventListener 的异常吞没**

```java
@EventListener
public void handle(MyEvent event) {
    throw new RuntimeException("处理失败");  // 异常会吞没，不传播给发布者
}
```

默认情况下 `@EventListener` 是同步执行的，异常会阻止后续监听器执行但不会抛给发布者。如果希望异常传播，使用 `@TransactionalEventListener` 或显式 try-catch 处理。
