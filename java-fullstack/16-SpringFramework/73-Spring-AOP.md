---
title: Spring AOP
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring, aop, aspect, joinpoint, pointcut, advice, proxy, aspectj, around, before, after]
---

# Spring AOP

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [AOP 核心概念](#aop-核心概念)
- [AOP 底层原理——动态代理](#aop-底层原理动态代理)
- [AspectJ 注解方式](#aspectj-注解方式)
- [五种通知类型](#五种通知类型)
- [切点表达式（Pointcut Expression）](#切点表达式pointcut-expression)
- [通知执行顺序](#通知执行顺序)
- [JoinPoint 与 ProceedingJoinPoint](#joinpoint-与-proceedingjoinpoint)
- [Introductions 引入](#introductions-引入)
- [Aspect 实例化模型](#aspect-实例化模型)
- [AspectJ 编译时织入](#aspectj-编译时织入)
- [Schema-based AOP](#schema-based-aop)
- [AspectJProxyFactory 编程式代理](#aspectjproxyfactory-编程式代理)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

AOP（Aspect-Oriented Programming，面向切面编程）是 OOP 的补充。OOP 把系统纵向切分为类，AOP 把横切关注点（如日志、事务、安全）从业务逻辑中剥离出来。

```text
OOP 视角（纵向）              AOP 视角（横向）
 ┌──┬──┬──┬──┐                ┌──┬──┬──┬──┐
 │L │T │S │用户│               │L │T │S │用户│  ← 横切关注点
 │o │r │e │    │               │o │r │e │    │
 │g │a │c │服务│               │g │a │c │服务│
 │  │n │u │    │               │  │n │u │    │
 │  │s │r │订单│               │  │s │r │订单│
 │  │a │i │    │               │  │a │i │    │
 │  │c │t │库存│               │  │c │t │库存│
 │  │t │y │    │               │  │t │y │    │
 └──┴──┴──┴──┘                └──┴──┴──┴──┘
   分散在各处                   抽取为独立切面
```

Spring AOP 不是完整的 AOP 实现（AspectJ 才是），它是基于动态代理的轻量级 AOP 框架，专门针对 Spring Bean 的方法调用做拦截。

## AOP 核心概念

理解 AOP 必须先搞清楚以下术语（它们有严格的先后关系）：

```text
                           JoinPoint (连接点)
                                ↓
                           是 Pointcut (切入点) 匹配的吗？
                         ┌──────┴──────┐
                        是             否
                         ↓              ↓
                   Advice (通知)      不处理
                         ↓
                  执行增强逻辑
```

| 术语 | 英文 | 说明 | 类比 |
|------|------|------|------|
| 连接点 | Join Point | 程序执行过程中的点，Spring AOP 中就是**方法调用** | 班级中每个学生 |
| 切入点 | Pointcut | 匹配连接点的表达式，筛选出要增强的目标 | 选出"戴眼镜的学生" |
| 通知 | Advice | 在匹配的连接点执行的增强逻辑 | "让选中的学生站起来" |
| 切面 | Aspect | 切入点 + 通知的组合，横切关注点的模块化 | 完整的选拔规则 |
| 织入 | Weaving | 将切面应用到目标对象，创建代理对象的过程 | 实施过程 |
| 目标对象 | Target | 被代理的原始对象 | 学生本人 |
| 代理对象 | Proxy | 织入后生成的代理 | 被选中后站起来的学生（增强后） |
| 引入 | Introduction | 给目标类动态添加新方法/接口 | 给某个学生发一张"值日生"卡片 |

### Spring AOP 的连接点

Spring AOP 的连接点**只是方法执行**（Method Execution），不支持：
- 构造器调用
- 字段访问/修改
- 静态/ final 方法（无法代理）

需要这些能力时，使用完整的 AspectJ（编译时织入）。

## AOP 底层原理——动态代理

Spring AOP 使用两种动态代理技术：

| 条件 | 代理方式 | 说明 |
|------|---------|------|
| 目标类实现了接口 | JDK 动态代理 | 基于接口，生成实现了相同接口的代理对象 |
| 目标类未实现接口 | CGLIB | 基于继承，生成目标类的子类 |
| proxyTargetClass=true | 强制 CGLIB | Spring Boot 2.x 默认行为 |

### JDK 动态代理

```java
// 原理示意（简化版）
public class JdkProxy implements InvocationHandler {
    private final Object target;

    public JdkProxy(Object target) {
        this.target = target;
    }

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        System.out.println("Before: " + method.getName());
        Object result = method.invoke(target, args);  // 调用原始目标
        System.out.println("After: " + method.getName());
        return result;
    }

    // 创建代理
    public static <T> T createProxy(T target, Class<T> interfaceType) {
        return (T) Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            new Class[]{interfaceType},
            new JdkProxy(target)
        );
    }
}
```

**局限**：JDK 代理只能代理接口方法。`proxy.toString()` 不经过 invoke 方法，直接由 Proxy 类处理（这是为什么 `@Transactional` 调 this.method() 时不生效的原因之一）。

### CGLIB 代理

```java
// 原理示意（简化版）
Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(TargetClass.class);  // 继承目标类
enhancer.setCallback((MethodInterceptor) (obj, method, args, proxy) -> {
    System.out.println("Before: " + method.getName());
    Object result = proxy.invokeSuper(obj, args);  // 调用父类方法
    System.out.println("After: " + method.getName());
    return result;
});
TargetClass proxy = (TargetClass) enhancer.create();
```

**局限**：
- 不能代理 final 方法/类
- 不能代理 private 方法
- 如果目标类的构造器中调用了方法，代理不生效（此时代理尚未创建）

### Spring Boot 中的代理策略

```yaml
# Spring Boot 2.x 默认使用 CGLIB
spring:
  aop:
    proxy-target-class: true  # 默认 true
    auto: true                # 启用 @EnableAspectJAutoProxy
```

```java
// 等价于代码配置
@Configuration
@EnableAspectJAutoProxy(proxyTargetClass = true)  // 强制使用 CGLIB
public class AopConfig {}
```

### 代理的局限：自调用问题

```java
@Service
public class UserService {

    @Transactional  // 这个方法有事务
    public void methodA() {
        this.methodB();  // 自调用 —— 不经过代理！
    }

    @Transactional  // 这个方法的事务不会生效
    public void methodB() {
        // 直接调用 this.methodB() 时，this 是原始对象而不是代理
    }
}
```

原因：`methodA()` 被调用时经过了代理，但在方法内部 `this.methodB()` 是直接调用目标对象的 `methodB()`，绕过了代理。

解法：

```java
// 解法 1：注入自己（通过 setter 或 @Lazy）
@Service
public class UserService {
    @Lazy
    @Autowired
    private UserService self;

    public void methodA() {
        self.methodB();  // 通过代理对象调用
    }
}

// 解法 2：拆分到不同的类
@Service
public class UserServiceA {
    @Autowired
    private UserServiceB userServiceB;

    @Transactional
    public void methodA() {
        userServiceB.methodB();  // 代理生效
    }
}

// 解法 3：通过 ApplicationContext 获取代理（侵入性强）
@Autowired
private ApplicationContext context;

public void methodA() {
    context.getBean(UserService.class).methodB();
}

// 解法 4：AopContext.currentProxy()（需要开启 exposeProxy）
@EnableAspectJAutoProxy(exposeProxy = true)
@Service
public class UserService {
    @Transactional
    public void methodA() {
        ((UserService) AopContext.currentProxy()).methodB();
    }
}
```

推荐解法 2（拆分类），其次是解法 1。

## AspectJ 注解方式

Spring AOP 使用 AspectJ 的注解体系来定义切面：

### 定义切面

```java
@Aspect      // 标记为切面类
@Component   // 同时需要注册为 Spring Bean
public class LoggingAspect {

    // 切入点 + 通知
    @Before("execution(* com.example.service.*.*(..))")
    public void beforeServiceMethod(JoinPoint joinPoint) {
        System.out.println("调用方法：" + joinPoint.getSignature().getName());
    }
}
```

`@Aspect` 只告诉 Spring"这是一个切面"，不会自动注册为 Bean——需要同时添加 `@Component` 或在配置类中 `@Bean` 注册。

### 定义切入点

```java
@Aspect
@Component
public class LoggingAspect {

    // 定义切入点（可复用）
    @Pointcut("execution(* com.example.service.*.*(..))")
    public void serviceLayer() {}  // 方法体为空，仅为命名载体

    // 引用切入点
    @Before("serviceLayer()")
    public void logBefore(JoinPoint joinPoint) {
        // ...
    }

    @AfterReturning(value = "serviceLayer()", returning = "result")
    public void logAfterReturning(JoinPoint joinPoint, Object result) {
        // ...
    }
}
```

### 组合切入点

```java
@Pointcut("execution(* com.example.service.*.*(..))")
public void serviceLayer() {}

@Pointcut("execution(* com.example.dao.*.*(..))")
public void daosLayer() {}

// AND：同时满足
@Pointcut("serviceLayer() && daosLayer()")
public void serviceAndDao() {}

// OR：满足其一
@Pointcut("serviceLayer() || daosLayer()")
public void serviceOrDao() {}

// NOT：不满足
@Pointcut("serviceLayer() && !execution(* *.get*(..))")
public void serviceButNotGetter() {}

// 组合注解匹配 + 包匹配
@Pointcut("@annotation(org.springframework.transaction.annotation.Transactional) && within(com.example..*)")
public void transactionalMethods() {}
```

## 五种通知类型

Spring AOP 的五种通知覆盖了方法执行的完整生命周期：

```text
  @Before
     ↓
  try {
     @Around (前半段)
        ↓
     目标方法执行
        ↓
     @Around (后半段)
        ↓
     @AfterReturning  ←（正常返回）
  } catch (Exception e) {
     @AfterThrowing    ←（抛异常）
  } finally {
     @After            ←（最终，一定会执行）
  }
```

### 1. @Before —— 前置通知

```java
@Before("execution(* com.example.service.*.*(..))")
public void before(JoinPoint joinPoint) {
    String methodName = joinPoint.getSignature().getName();
    Object[] args = joinPoint.getArgs();
    System.out.println("准备执行：" + methodName + "，参数：" + Arrays.toString(args));
}
```

方法执行前调用。**不能阻止目标方法的执行**（就算抛异常，目标方法也会执行）。

### 2. @AfterReturning —— 返回后通知

```java
@AfterReturning(
    pointcut = "execution(* com.example.service.*.*(..))",
    returning = "result"  // 绑定返回值
)
public void afterReturning(JoinPoint joinPoint, Object result) {
    System.out.println("方法返回：" + result);
}
```

目标方法**正常返回后**调用。可以获取返回值。

### 3. @AfterThrowing —— 异常后通知

```java
@AfterThrowing(
    pointcut = "execution(* com.example.service.*.*(..))",
    throwing = "ex"  // 绑定异常
)
public void afterThrowing(JoinPoint joinPoint, Exception ex) {
    System.out.println("方法抛异常：" + ex.getMessage());
    // 记录异常日志、发送告警
}
```

目标方法**抛出异常后**调用。可以获取异常对象。

`throwing` 属性的值必须与方法参数名一致。类型写 `Exception` 时只拦截 Exception 的子类。如果要拦截所有 Throwable，类型写 `Throwable`。

### 4. @After —— 最终通知

```java
@After("execution(* com.example.service.*.*(..))")
public void after(JoinPoint joinPoint) {
    System.out.println("方法结束（无论正常还是异常）");
}
```

方法执行结束后调用，类似 `finally`。**不能获取返回值和异常**。

### 5. @Around —— 环绕通知（最强大）

```java
@Around("execution(* com.example.service.*.*(..))")
public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
    String methodName = joinPoint.getSignature().getName();
    long start = System.currentTimeMillis();

    try {
        // 前置逻辑
        System.out.println(">> " + methodName + " 开始");

        // 调用目标方法
        Object result = joinPoint.proceed();

        // 返回后逻辑
        System.out.println("<< " + methodName + " 完成，耗时: "
            + (System.currentTimeMillis() - start) + "ms");

        return result;

    } catch (Exception e) {
        // 异常后逻辑
        System.out.println("!! " + methodName + " 异常: " + e.getMessage());
        throw e;  // 可以选择不抛出（吞没异常）
    } finally {
        // 最终逻辑
        System.out.println("-- " + methodName + " 结束");
    }
}
```

`@Around` 可以完全控制目标方法——包括是否调用、修改参数、修改返回值、吞没异常。

**关键规则**：`joinPoint.proceed()` 必须调用（否则目标方法不会执行），返回值必须返回（否则调用方拿不到结果）。

## 切点表达式（Pointcut Expression）

### execution 表达式

最常用的切点表达式，语法：

```text
execution(修饰符? 返回类型 包名.类名.方法名(参数列表) throws?)
```

```java
// 匹配所有 public 方法
execution(public * *(..))

// 匹配 service 包下所有类的所有方法
execution(* com.example.service.*.*(..))

// 匹配 service 包及子包下所有类的所有方法
execution(* com.example.service..*.*(..))

// 匹配以 save 开头的方法
execution(* save*(..))

// 匹配指定返回类型的方法
execution(String com.example.service.*.*(..))

// 匹配指定参数的方法：第一个参数 Long，第二个任意
execution(* com.example.service.*.*(Long, *))

// 匹配无参方法
execution(* com.example.service.*.*())

// 匹配 UserService 类的所有方法
execution(* com.example.service.UserService.*(..))
```

### 其他切点指示符

```java
// within：限定类/包 —— 比 execution 更粗粒度
@Pointcut("within(com.example.service.*)")
public void servicePackage() {}

@Pointcut("within(com.example.service.UserService)")
public void userServiceOnly() {}

// this：代理对象类型匹配
@Pointcut("this(com.example.service.UserService)")
public void proxyIsUserService() {}

// target：目标对象类型匹配
@Pointcut("target(com.example.dao.UserDao)")
public void targetIsUserDao() {}

// args：参数类型匹配
@Pointcut("args(Long, ..)")
public void firstArgIsLong() {}        // 第一个参数是 Long

@Pointcut("args(Long, String)")
public void argsLongAndString() {}     // 两个参数：Long 和 String

// @annotation：方法上有指定注解
@Pointcut("@annotation(org.springframework.transaction.annotation.Transactional)")
public void transactionalMethods() {}

// @within：类上有指定注解
@Pointcut("@within(org.springframework.stereotype.Service)")
public void serviceAnnotatedClasses() {}

// @args：参数类型上有指定注解
@Pointcut("@args(javax.validation.Valid)")
public void validatedArgs() {}

// bean：按 Spring Bean 名称匹配（Spring 特有，AspectJ 不支持）
@Pointcut("bean(userService)")
public void userServiceBean() {}

@Pointcut("bean(*Service)")
public void allServiceBeans() {}       // 名称以 Service 结尾的 Bean
```

### 表达式组合示例

```java
// 切的是 service 包下、有 @Transactional 注解、且不是测试类的方法
@Pointcut("execution(* com.example.service..*.*(..)) " +
          "&& @annotation(org.springframework.transaction.annotation.Transactional) " +
          "&& !within(com.example.service.*Test)")
public void transactionalServiceMethods() {}
```

## 通知执行顺序

同一个连接点有多个切面时，执行顺序由以下规则决定：

### 正常执行

```text
Aspect1 @Before
  → Aspect2 @Before
    → 目标方法
  → Aspect2 @AfterReturning / @After
→ Aspect1 @AfterReturning / @After
```

### 异常执行

```text
Aspect1 @Before
  → Aspect2 @Before
    → 目标方法（抛异常）
  → Aspect2 @AfterThrowing / @After
→ Aspect1 @AfterThrowing / @After
```

### 控制顺序：@Order

```java
@Aspect
@Component
@Order(1)  // 数字越小优先级越高 —— 先执行
public class SecurityAspect {
    @Before("...")
    public void checkAuth() {
        // 安全检查先执行
    }
}

@Aspect
@Component
@Order(2)  // 后执行
public class LoggingAspect {
    @Before("...")
    public void log() {
        // 日志后执行
    }
}
```

**@Order 规则**：
- 正常执行：Order 小的切面在外面（先进后出）
- @Before：Order 小的先执行
- @After / @AfterReturning / @AfterThrowing：Order 小的后执行（栈结构）
- @Around：Order 小的先进入，后退出

## JoinPoint 与 ProceedingJoinPoint

### JoinPoint（除 @Around 外的通知）

```java
@Before("execution(* com.example.service.*.*(..))")
public void before(JoinPoint joinPoint) {
    // 获取方法签名
    Signature signature = joinPoint.getSignature();
    String methodName = signature.getName();                    // 方法名
    String className = signature.getDeclaringTypeName();       // 类名
    int modifiers = signature.getModifiers();                   // 修饰符

    // 获取参数
    Object[] args = joinPoint.getArgs();                        // 实参数组
    if (args.length > 0) {
        System.out.println("参数: " + args[0]);
    }

    // 获取目标对象
    Object target = joinPoint.getTarget();                      // 原始目标
    Object proxy = joinPoint.getThis();                         // 代理对象

    // 获取方法上的注解
    MethodSignature ms = (MethodSignature) signature;
    Method method = ms.getMethod();
    Transactional tx = method.getAnnotation(Transactional.class);
}
```

### ProceedingJoinPoint（@Around 专用）

```java
@Around("execution(* com.example.service.*.*(..))")
public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
    // 继承 JoinPoint 的所有方法，额外提供：

    // 调用目标方法（必须！）
    Object result = joinPoint.proceed();

    // 调用目标方法并修改参数
    Object[] args = joinPoint.getArgs();
    args[0] = "modified";               // 修改参数
    Object result = joinPoint.proceed(args);  // 传入修改后的参数

    return result;
}
```

## Introductions 引入

Introductions（引入）是 AOP 的高级特性——**让目标类在运行时动态实现额外的接口**，而无需修改目标类的源代码。用 `@DeclareParents` 实现。

典型场景：给一组领域对象动态添加"可审计"能力，而不是让每个类都继承同一个基类。

```java
// 1. 定义要动态添加的接口
public interface Auditable {
    void setAuditInfo(String info);
    String getAuditInfo();
}

// 2. 定义默认实现
public class DefaultAuditable implements Auditable {
    private String auditInfo;

    @Override
    public void setAuditInfo(String info) { this.auditInfo = info; }

    @Override
    public String getAuditInfo() { return auditInfo; }
}

// 3. 切面中声明引入
@Aspect
@Component
public class AuditableIntroduction {

    // 让所有 User 对象（value）额外实现 Auditable 接口，
    // 默认实现是 DefaultAuditable（defaultImpl）
    @DeclareParents(value = "com.example.entity.User",
                    defaultImpl = DefaultAuditable.class)
    public static Auditable auditable;
}
```

使用效果：

```java
@Service
public class AuditService {
    @Autowired
    private User user;  // 注意：注入的是代理对象

    public void audit() {
        // User 原本没有实现 Auditable，但代理对象可以强转为 Auditable
        Auditable auditable = (Auditable) user;
        auditable.setAuditInfo("创建于 2026-08-12");
        System.out.println(auditable.getAuditInfo());
    }
}
```

工作机制：Spring 为 User 生成代理时，代理类额外实现了 Auditable 接口，方法调用委托给 DefaultAuditable 实例。

**注意**：

1. `@DeclareParents` 标注的字段必须是 `static`，类型是要引入的接口
2. `value` 指定目标类型（AspectJ 类型表达式，如 `com.example.entity.User+` 表示 User 及其子类）
3. 只能通过代理对象强转为引入的接口，原始对象不行

## Aspect 实例化模型

默认情况下，切面是**单例**（Singleton）——整个应用共享一个切面实例。AspectJ 提供了两种按目标对象实例化切面的模型，但 Spring AOP **不支持**它们：

| 模型 | 说明 | Spring AOP 支持 |
|------|------|----------------|
| singleton | 默认，单例切面 | 支持 |
| perthis | 每个切入点匹配的**目标对象**一个切面实例 | 不支持 |
| pertarget | 每个目标对象的**类**一个切面实例 | 不支持 |

```java
// AspectJ 中的 perthis 用法（Spring AOP 不支持）
@Aspect("perthis(execution(* com.example.service.*.*(..)))")
public class PerThisAspect {
    // 每个被拦截的目标对象都有自己的一份切面状态
    private int invocationCount = 0;  // 可以在切面中保存状态

    @Around("execution(* com.example.service.*.*(..))")
    public Object count(ProceedingJoinPoint jp) throws Throwable {
        invocationCount++;  // 每个目标对象独立计数
        return jp.proceed();
    }
}
```

perthis 的用途：需要在切面中保存**每个目标对象独立的状态**时（如每个 Service 的调用次数统计）。由于 Spring AOP 不支持，需要自己维护 `Map<目标对象, 状态>` 来实现类似效果。

```java
// Spring AOP 中的替代方案
@Aspect
@Component
public class CountingAspect {
    private final Map<String, AtomicInteger> counts = new ConcurrentHashMap<>();

    @Around("execution(* com.example.service.*.*(..))")
    public Object count(ProceedingJoinPoint jp) throws Throwable {
        String key = jp.getTarget().getClass().getName() + "." + jp.getSignature().getName();
        counts.computeIfAbsent(key, k -> new AtomicInteger()).incrementAndGet();
        return jp.proceed();
    }
}
```

## AspectJ 编译时织入

Spring AOP 是运行时织入（通过动态代理），AspectJ 提供编译时、编译后、加载时三种织入方式。

### 对比

| 维度 | Spring AOP | AspectJ |
|------|------------|---------|
| 织入时机 | 运行时（动态代理） | 编译时 / 加载时 |
| 性能 | 有代理开销 | 无运行时开销（编译后与普通方法调用无异） |
| 连接点 | 仅方法执行 | 方法执行、构造器、字段访问、异常处理等 |
| 依赖 | 需要 Spring 容器 | 独立于 Spring |
| 使用复杂度 | 简单（注解即用） | 需要 AspectJ 编译器/weaver |
| 代理局限 | 自调用不生效、final 方法不能代理 | 无此限制 |

Spring AOP 满足 90% 的需求。AspectJ 用于少数需要精细控制或高性能的场景。

## Schema-based AOP

Schema-based AOP 是用 XML 配置切面的传统方式（Spring 1.x/2.x 时代的主流，现在已被注解取代）。理解它有助于维护遗留项目。

```xml
<beans xmlns:aop="http://www.springframework.org/schema/aop">
    <aop:config>
        <!-- 定义切面 -->
        <aop:aspect id="loggingAspect" ref="loggingBean">

            <!-- 定义切入点 -->
            <aop:pointcut id="serviceMethods"
                expression="execution(* com.example.service.*.*(..))" />

            <!-- 前置通知 -->
            <aop:before method="logBefore"
                pointcut-ref="serviceMethods" />

            <!-- 环绕通知 -->
            <aop:around method="logAround"
                pointcut-ref="serviceMethods" />

            <!-- 返回后通知 -->
            <aop:after-returning method="logAfterReturning"
                pointcut-ref="serviceMethods" returning="result" />

            <!-- 异常后通知 -->
            <aop:after-throwing method="logAfterThrowing"
                pointcut-ref="serviceMethods" throwing="ex" />

            <!-- 最终通知 -->
            <aop:after method="logAfter"
                pointcut-ref="serviceMethods" />
        </aop:aspect>
    </aop:config>

    <!-- 切面逻辑 Bean -->
    <bean id="loggingBean" class="com.example.aspect.LoggingAspect" />
</beans>
```

对应的 Java 类（无需 @Aspect 注解）：

```java
public class LoggingAspect {
    public void logBefore(JoinPoint jp) { /* ... */ }
    public Object logAround(ProceedingJoinPoint jp) throws Throwable {
        try {
            return jp.proceed();
        } finally {
            // ...
        }
    }
    public void logAfterReturning(JoinPoint jp, Object result) { /* ... */ }
    public void logAfterThrowing(JoinPoint jp, Exception ex) { /* ... */ }
    public void logAfter(JoinPoint jp) { /* ... */ }
}
```

`<aop:advisor>` 还可以直接把事务通知（tx:advice）等内置 advisor 应用到切点，这是 Spring 声明式事务 XML 配置的底层机制。

## AspectJProxyFactory 编程式代理

除了容器自动代理，Spring 提供 `AspectJProxyFactory`，允许脱离容器手动创建带切面的代理对象。

```java
import org.springframework.aop.aspectj.annotation.AspectJProxyFactory;

// 1. 创建目标对象
UserService target = new UserServiceImpl();

// 2. 创建代理工厂
AspectJProxyFactory factory = new AspectJProxyFactory(target);

// 3. 添加切面
factory.addAspect(LoggingAspect.class);
factory.addAspect(new SecurityAspect());

// 4. 获取代理对象（默认 CGLIB，也可以指定 JDK 代理）
UserService proxy = factory.getProxy();

// 5. 通过代理调用，切面生效
proxy.createUser(new User("张三"));
```

适用场景：

- 单元测试：单独测试某个切面的逻辑，无需启动整个容器
- 非 Spring 环境：在普通 Java 应用中使用 Spring AOP 的能力
- 手动织入：需要精确控制哪些对象被代理、哪些切面生效

```java
// 配合接口使用 JDK 代理
AspectJProxyFactory factory = new AspectJProxyFactory(target);
factory.setProxyTargetClass(false);  // false = 使用 JDK 动态代理（需要接口）
factory.addAspect(LoggingAspect.class);
UserService proxy = factory.getProxy();
```

## 应用场景实战

### 场景 1：方法耗时统计

```java
@Aspect
@Component
@Slf4j
public class TimingAspect {

    @Around("@annotation(timing)")  // 切自定义注解
    public Object measureTime(ProceedingJoinPoint joinPoint, Timing timing) throws Throwable {
        long start = System.nanoTime();
        try {
            return joinPoint.proceed();
        } finally {
            long cost = System.nanoTime() - start;
            String method = joinPoint.getSignature().toShortString();
            if (cost > timing.warnThreshold()) {
                log.warn("{} 执行耗时 {}ms，超过阈值 {}ms",
                    method, cost / 1_000_000, timing.warnThreshold() / 1_000_000);
            } else {
                log.info("{} cost {}ms", method, cost / 1_000_000);
            }
        }
    }
}

// 自定义注解
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Timing {
    long warnThreshold() default 1000;  // 默认 1 秒告警
}

// 使用
@Service
public class OrderService {
    @Timing(warnThreshold = 500)
    public Order createOrder(OrderDTO dto) {
        // ...
    }
}
```

### 场景 2：统一异常处理和返回包装

```java
@Aspect
@Component
public class ControllerAspect {

    @Around("execution(* com.example.controller..*.*(..))")
    public Object handleController(ProceedingJoinPoint joinPoint) {
        try {
            Object result = joinPoint.proceed();
            return Result.success(result);

        } catch (BusinessException e) {
            return Result.error(e.getCode(), e.getMessage());

        } catch (Exception e) {
            log.error("系统异常", e);
            return Result.error(500, "系统繁忙，请稍后重试");
        }
    }
}

// 配合注解进行精细化控制
@Around("@annotation(com.example.annotation.NotWrap)")
public Object skipWrap(ProceedingJoinPoint joinPoint) throws Throwable {
    return joinPoint.proceed();  // 不包装，直接返回
}
```

### 场景 3：分布式锁切面

```java
@Aspect
@Component
public class DistributedLockAspect {

    @Autowired
    private RedissonClient redissonClient;

    @Around("@annotation(distributedLock)")
    public Object around(ProceedingJoinPoint joinPoint, DistributedLock distributedLock)
            throws Throwable {

        String key = buildKey(joinPoint, distributedLock);  // 根据方法名+参数生成 key
        RLock lock = redissonClient.getLock(key);

        boolean acquired = lock.tryLock(
            distributedLock.waitTime(),       // 等待时间
            distributedLock.leaseTime(),      // 持有时间
            TimeUnit.MILLISECONDS
        );

        if (!acquired) {
            throw new BusinessException("操作过于频繁，请稍后重试");
        }

        try {
            return joinPoint.proceed();
        } finally {
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }

    private String buildKey(ProceedingJoinPoint joinPoint, DistributedLock lock) {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        String methodName = signature.getMethod().getName();
        Object[] args = joinPoint.getArgs();
        return lock.prefix() + ":" + methodName + ":" + Arrays.toString(args);
    }
}
```

### 场景 4：操作日志记录

```java
@Aspect
@Component
public class OperationLogAspect {

    @Autowired
    private OperationLogService logService;

    @AfterReturning(
        pointcut = "@annotation(operationLog)",
        returning = "result"
    )
    public void recordLog(JoinPoint joinPoint, OperationLog operationLog, Object result) {
        // 获取当前用户（从 SecurityContext 或 ThreadLocal）
        String username = getCurrentUsername();

        // 构建日志
        OperationLogEntity log = new OperationLogEntity();
        log.setOperator(username);
        log.setModule(operationLog.module());
        log.setAction(operationLog.action());
        log.setDescription(operationLog.description());
        log.setMethod(joinPoint.getSignature().toShortString());
        log.setParams(JSON.toJSONString(joinPoint.getArgs()));
        log.setResult("success");
        log.setOperateTime(LocalDateTime.now());

        logService.save(log);
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **AOP 只做横切关注点**。日志、事务、安全、缓存、幂等——这些"散落各处但逻辑一致"的功能才是 AOP 的用武之地。不要为了 AOP 而 AOP。

2. **用自定义注解标记切入点**。`@annotation` 比 `execution` 更精确，避免意外拦截：

```java
// 精确：只有标记了 @AuditLog 的方法才会被拦截
@Around("@annotation(com.example.annotation.AuditLog)")

// 宽泛：service 包下所有方法都会被拦截（可能误伤）
@Around("execution(* com.example.service.*.*(..))")
```

3. **@Around 中必须调用 proceed() 并返回结果**。忘记调用 proceed 会导致目标方法不执行，忘记 return 会导致调用方拿到 null。

4. **切面中使用 ThreadLocal 传递上下文**。不要用成员变量存储请求级别的数据——切面是单例的。

5. **控制切面数量**。太多切面会让调试困难（执行流程被多层代理包装）。

### 踩坑记录

**坑 1：@Around 的返回值类型不匹配**

```java
@Around("execution(* com.example.service.*.*(..))")
public Object around(ProceedingJoinPoint jp) throws Throwable {
    return "fixed string";  // 目标方法返回 User，这里返回 String —— 运行时 ClassCastException
}
```

@Around 返回类型必须与目标方法兼容。如果不知道返回类型，用 `Object` 接收 `proceed()` 的返回值并返回。

**坑 2：@AfterThrowing 不能吞没异常**

```java
@AfterThrowing(pointcut = "...", throwing = "ex")
public void handle(JoinPoint jp, Exception ex) {
    log.error("出错", ex);
    // @AfterThrowing 不能阻止异常传播 —— 异常仍会抛出
}
```

如果要吞没异常，只能用 @Around：

```java
@Around("...")
public Object around(ProceedingJoinPoint jp) {
    try {
        return jp.proceed();
    } catch (Exception e) {
        log.error("出错", e);
        return null;  // 吞没异常
    }
}
```

**坑 3：多个切面的执行顺序不可预测**

同一优先级（未指定 @Order）的切面执行顺序是不确定的。如果需要明确顺序，始终指定 @Order。

**坑 4：@Pointcut 方法的权限必须是 public**

```java
@Aspect
public class MyAspect {
    @Pointcut("execution(* com.example.*.*(..))")
    private void myPointcut() {}  // private！外部切面引用时报错
}
```

如果可能被其他切面引用，@Pointcut 方法必须是 public。

**坑 5：BeanPostProcessor 的代理冲突**

Spring 内部一些基础设施也通过代理工作（如 `@Async`、`@Cacheable`、`@Transactional`）。如果自定义切面与这些内置代理冲突，可能导致某些功能失效。

排查方法：启动时设置 `spring.aop.proxy-target-class=true` 并打开 DEBUG 日志查看代理创建过程。

**坑 6：Aspect 类中不能注入没有代理的 Bean**

```java
@Aspect
@Component
public class MyAspect {
    @Autowired
    private MyService myService;  // 如果 MyService 也有 AOP 切面，这里可能注入原始对象
}
```

当切面引用的 Bean 本身也被代理时，注意注入的是代理还是原始对象。加上 `@Lazy` 可以延迟注入，确保代理已创建。
