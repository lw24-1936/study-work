---
title: Spring Boot 集成 AOP 详解
created: 2026-08-10
updated: 2026-08-10
type: integration
tags: [spring-boot, aop, aspectj, design-pattern]
---

> 整理日期：2026-08-10

## 目录

1. [概述](#1-概述)
2. [环境搭建](#2-环境搭建)
3. [AOP 核心概念](#3-aop-核心概念)
4. [五种通知类型](#4-五种通知类型)
5. [切点表达式](#5-切点表达式)
6. [切面执行顺序](#6-切面执行顺序)
7. [应用场景实战](#7-应用场景实战)
8. [最佳实践与踩坑记录](#8-最佳实践与踩坑记录)
9. [参考链接](#9-参考链接)

---

## 1. 概述

### 1.1 AOP 是什么

AOP（Aspect-Oriented Programming，面向切面编程）是 OOP 的补充，核心思路：**把散布在各处的横切关注点（日志、权限、事务等）集中到一个地方管理，不侵入业务代码**。

不用 AOP 时，每个方法里都要写一段相同的逻辑（比如打印日志、校验权限）。改一次就得全项目改一遍。AOP 把这些"横切逻辑"抽到切面里，通过切点表达式定义哪些方法需要、在什么时机织入。

### 1.2 Spring AOP 的代理机制

Spring AOP 基于动态代理。如果目标类实现了接口，用 JDK 动态代理；如果没有接口，用 CGLIB 代理（生成子类）。

关键限制：**调用同一个类内部的方法不会触发代理**。`this.methodB()` 走的是原始对象引用，绕过了代理。

### 1.3 和 AspectJ 的区别

| 维度 | Spring AOP | AspectJ |
|------|-----------|---------|
| 织入时机 | 运行时（动态代理） | 编译期 / 类加载期 / 运行时 |
| 依赖 | Spring 容器 | 需要 AspectJ 编译器 |
| 范围 | 只对 Spring Bean 的方法 | 任意方法（包括构造器、静态方法） |
| 性能 | 运行时代理有少量开销 | 编译期织入，运行无代理开销 |
| 使用场景 | 绝大多数业务场景 | 需要织入非 Spring 管理的对象 |

项目中 99% 的需求用 Spring AOP 就够了。如果需要对 static 方法、构造器或非 Spring Bean 织入，上 AspectJ。

---

## 2. 环境搭建

### 2.1 依赖

```xml
<!-- Spring Boot AOP Starter（包含 spring-aop + aspectjweaver） -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-aop</artifactId>
</dependency>
```

### 2.2 开启 AOP

Spring Boot 自动配置默认开启了 `@EnableAspectJAutoProxy`，不需要手动加。确认一下即可：

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
    // 已经相当于加了 @EnableAspectJAutoProxy
}
```

---

## 3. AOP 核心概念

**一张图讲清楚各概念的关系：**

```
@Aspect（切面类）
 ├── @Pointcut（切点：哪里切入）
 ├── @Before（前置通知：方法执行前）
 ├── @After（后置通知：方法执行后，无论是否异常）
 ├── @AfterReturning（返回通知：方法正常返回后）
 ├── @AfterThrowing（异常通知：方法抛异常后）
 └── @Around（环绕通知：包裹方法执行全过程）
         │
         ├── joinPoint.proceed()  // 执行目标方法
         ├── 修改入参
         ├── 修改返回值
         └── 异常捕获
```

最少要掌握四个概念：

| 概念 | 说明 |
|------|------|
| Aspect | 切面类，用 `@Aspect` 标记，把横切逻辑集中到这个类里 |
| JoinPoint | 连接点，程序执行中的某个点（方法调用、异常抛出等）。Spring AOP 只支持方法级别的 JoinPoint |
| Pointcut | 切点表达式，定义哪些 JoinPoint 被拦截 |
| Advice | 通知，在切点处执行的具体逻辑（Before/After/Around 等） |

---

## 4. 五种通知类型

### 4.1 @Before — 前置通知

目标方法执行**前**触发，可以拿到入参，**不能阻止方法执行**（要看返回值控制用 Around）。

```java
@Aspect
@Component
public class BeforeAspect {

    @Before("execution(* com.example.service.UserService.*(..))")
    public void before(JoinPoint joinPoint) {
        String methodName = joinPoint.getSignature().getName();
        Object[] args = joinPoint.getArgs();
        System.out.println("调用 " + methodName + "，参数：" + Arrays.toString(args));
    }
}
```

### 4.2 @After — 后置通知

目标方法执行**后**触发，**无论是否抛出异常都会执行**。不能拿到返回值。

```java
@After("execution(* com.example.service.*.*(..))")
public void after(JoinPoint joinPoint) {
    System.out.println(joinPoint.getSignature().getName() + " 执行完毕");
}
```

After 适合做资源释放（关连接、清理 ThreadLocal），比 finally 好在不需要在每个方法里写。

### 4.3 @AfterReturning — 返回通知

目标方法**正常返回**后触发，可以拿到返回值。

```java
@AfterReturning(
    pointcut = "execution(* com.example.service.*.*(..))",
    returning = "result"   // 返回值绑定到参数名
)
public void afterReturning(JoinPoint joinPoint, Object result) {
    System.out.println("返回结果：" + result);
    // 可以修改引用对象的属性，但不能修改返回值本身
    // 要修改返回值用 @Around
}
```

### 4.4 @AfterThrowing — 异常通知

目标方法**抛出异常**后触发，可以拿到异常对象。

```java
@AfterThrowing(
    pointcut = "execution(* com.example.service.*.*(..))",
    throwing = "ex"         // 异常对象绑定到参数名
)
public void afterThrowing(JoinPoint joinPoint, Exception ex) {
    System.err.println("方法 " + joinPoint.getSignature().getName()
            + " 抛出异常：" + ex.getMessage());
}
```

### 4.5 @Around — 环绕通知（最强大）

包裹整个方法调用，可以控制是否执行目标方法、修改入参、修改返回值、处理异常。但**必须手动调用 `joinPoint.proceed()`** 才会执行目标方法。

```java
@Around("execution(* com.example.service.*.*(..))")
public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
    String methodName = joinPoint.getSignature().getName();
    Object[] args = joinPoint.getArgs();

    System.out.println(">> 开始: " + methodName);

    long start = System.currentTimeMillis();
    Object result = null;
    try {
        // 执行目标方法（不调这行目标方法就不会执行）
        result = joinPoint.proceed();

        long elapsed = System.currentTimeMillis() - start;
        System.out.println("<< 成功: " + methodName + " 耗时 " + elapsed + "ms");
        return result;

    } catch (Exception e) {
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("<< 异常: " + methodName + " 耗时 " + elapsed + "ms, " + e.getMessage());
        throw e;  // 不吞异常，继续往外抛
    }
}
```

### 4.6 五种通知的执行顺序

```
正常流程：
  @Around(前半段) -> @Before -> 目标方法 -> @AfterReturning -> @After -> @Around(后半段)

异常流程：
  @Around(前半段) -> @Before -> 目标方法抛异常 -> @AfterThrowing -> @After
  （@Around 的后半段不会执行，除非你在 Around 里 catch 了异常）
```

---

## 5. 切点表达式

切点表达式决定了"拦截哪些方法"。设计模式参考 AspectJ 的 pointcut 语法。

### 5.1 execution（最常用）

```
execution(modifiers? return-type declaring-type? name-pattern(param-pattern) throws-pattern?)
```

常用写法：

```java
// 拦截 UserService 的所有 public 方法
@Pointcut("execution(public * com.example.service.UserService.*(..))")
public void userServicePointcut() {}

// 拦截 service 包下所有类的所有方法（不包含子包）
@Pointcut("execution(* com.example.service.*.*(..))")

// 拦截 service 包及其所有子包
@Pointcut("execution(* com.example.service..*.*(..))")

// 拦截所有以 find 开头的方法
@Pointcut("execution(* com.example..*Service.find*(..))")

// 拦截第一个参数为 Long 类型的方法
@Pointcut("execution(* com.example..*.*(Long, ..))")

// 拦截返回值为 User 类型的方法
@Pointcut("execution(com.example.entity.User com.example..*.*(..))")

// 拦截所有 Controller
@Pointcut("execution(* com.example.controller..*.*(..))")
```

### 5.2 @annotation（按注解拦截）

拦截所有标注了指定注解的方法。自定义注解 + AOP 的组合是最常用的模式。

```java
// 拦截所有 @Log 注解的方法
@Pointcut("@annotation(com.example.annotation.Log)")
public void logAnnotationPointcut() {}

// 拦截类上标注了 @Log 的类的所有方法
@Pointcut("@within(com.example.annotation.Log)")
public void withinAnnotationPointcut() {}
```

### 5.3 within（按类/包拦截）

```java
// UserService 的所有方法
@Pointcut("within(com.example.service.UserService)")

// service 包下所有类的所有方法
@Pointcut("within(com.example.service..*)")
```

`within` 和 `execution` 的区别：`within` 只看类，不看返回值、参数、异常。

### 5.4 args（按参数类型拦截）

```java
// 第一个参数是 Long 的方法
@Pointcut("args(Long, ..)")

// 参数只有一个 User 对象的方法，且方法上有 @Valid 注解
@Pointcut("args(com.example.entity.User) && @annotation(jakarta.validation.Valid)")
```

### 5.5 bean（按 Bean 名称拦截）

```java
// 拦截 Bean 名为 userService 的方法
@Pointcut("bean(userService)")

// 拦截所有以 Service 结尾的 Bean
@Pointcut("bean(*Service)")
```

`bean` 是 Spring AOP 独有的，比 `within` 更直观——直接按 Spring Bean 名称匹配。

### 5.6 组合切点

用 `&&`（且）、`||`（或）、`!`（非）组合：

```java
@Pointcut("execution(* com.example.service..*.*(..))")
public void serviceLayer() {}

@Pointcut("execution(* com.example.controller..*.*(..))")
public void controllerLayer() {}

// service 或 controller
@Pointcut("serviceLayer() || controllerLayer()")
public void webLayer() {}

// service 但不是 UserService
@Pointcut("serviceLayer() && !within(com.example.service.UserService)")
public void serviceWithoutUser() {}
```

---

## 6. 切面执行顺序

多个切面拦截同一个方法时，通过 `@Order` 控制执行顺序。

```java
@Aspect
@Component
@Order(1)  // 数字越小，先进入（洋葱从外往里）
public class LogAspect {
    @Around("execution(* com.example.service.*.*(..))")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("Log: 进入");
        Object result = pjp.proceed();
        System.out.println("Log: 退出");
        return result;
    }
}

@Aspect
@Component
@Order(2)  // 数字越大，后进入（洋葱从里往外）
public class PerformanceAspect {
    @Around("execution(* com.example.service.*.*(..))")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("Perf: 进入");
        Object result = pjp.proceed();
        System.out.println("Perf: 退出");
        return result;
    }
}
```

执行顺序（洋葱模型）：

```
Log 进入 -> Perf 进入 -> 目标方法 -> Perf 退出 -> Log 退出
```

---

## 7. 应用场景实战

### 场景 1：操作日志（最基础）

记录谁在什么时间调了什么方法，参数是什么，返回值是什么。

**自定义注解：**

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface OperationLog {

    /** 操作模块（如 "用户管理"、"订单管理"） */
    String module() default "";

    /** 操作类型（如 "新增"、"删除"、"查询"） */
    String operation() default "";

    /** 操作描述（支持 SpEL 表达式，如 "删除用户#{#userId}"） */
    String desc() default "";
}
```

**切面实现：**

```java
@Aspect
@Component
@Slf4j
public class OperationLogAspect {

    @Autowired(required = false)
    private HttpServletRequest request;

    @Around("@annotation(operationLog)")
    public Object around(ProceedingJoinPoint joinPoint, OperationLog operationLog) throws Throwable {
        long start = System.currentTimeMillis();
        String methodName = joinPoint.getSignature().getName();
        Object[] args = joinPoint.getArgs();

        // 获取当前用户（从 SecurityContext 或请求头获取）
        String username = getCurrentUsername();

        try {
            Object result = joinPoint.proceed();
            long elapsed = System.currentTimeMillis() - start;

            // 记录成功日志
            log.info(
                "[操作日志] 用户={}, 模块={}, 操作={}, 方法={}, 耗时={}ms, 参数={}, 结果=成功",
                username,
                operationLog.module(),
                operationLog.operation(),
                methodName,
                elapsed,
                safeToString(args)
            );

            // 异步落库（省略具体实现）
            // operationLogService.asyncSave(...);

            return result;

        } catch (Exception e) {
            long elapsed = System.currentTimeMillis() - start;

            log.error(
                "[操作日志] 用户={}, 模块={}, 操作={}, 方法={}, 耗时={}ms, 参数={}, 异常={}",
                username,
                operationLog.module(),
                operationLog.operation(),
                methodName,
                elapsed,
                safeToString(args),
                e.getMessage()
            );

            throw e;  // 不吞异常
        }
    }

    private String getCurrentUsername() {
        // 从 SecurityContext 或 JWT 中取
        return Optional.ofNullable(request)
                .map(r -> r.getHeader("X-Username"))
                .orElse("anonymous");
    }

    private String safeToString(Object[] args) {
        try {
            return Arrays.toString(args);
        } catch (Exception e) {
            return "[序列化失败]";
        }
    }
}
```

**使用：**

```java
@RestController
public class UserController {

    @OperationLog(module = "用户管理", operation = "删除", desc = "删除用户#{#userId}")
    @DeleteMapping("/users/{userId}")
    public R<Void> deleteUser(@PathVariable Long userId) {
        userService.deleteById(userId);
        return R.ok();
    }

    @OperationLog(module = "用户管理", operation = "新增")
    @PostMapping("/users")
    public R<Long> createUser(@RequestBody @Valid UserCreateDTO dto) {
        Long id = userService.create(dto);
        return R.ok(id);
    }
}
```

---

### 场景 2：接口耗时统计

所有 Controller 方法自动打印耗时，方便性能排查。

```java
@Aspect
@Component
@Slf4j
public class PerformanceAspect {

    @Around("execution(* com.example.controller..*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();

        try {
            return joinPoint.proceed();
        } finally {
            long elapsed = System.currentTimeMillis() - start;
            String method = joinPoint.getSignature().toShortString();

            if (elapsed > 3000) {
                // 慢查询告警
                log.warn("[慢接口] {} 耗时 {}ms（超过阈值 3000ms）", method, elapsed);
            } else {
                log.info("[接口耗时] {} {}ms", method, elapsed);
            }
        }
    }
}
```

加上分层阈值：

```java
@Around("execution(* com.example.controller..*.*(..))")
public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
    long start = System.currentTimeMillis();
    Object result = joinPoint.proceed();
    long elapsed = System.currentTimeMillis() - start;

    String methodPath = joinPoint.getSignature().getDeclaringType().getSimpleName()
            + "." + joinPoint.getSignature().getName();

    if (elapsed < 500) {
        // 正常，不打印
    } else if (elapsed < 2000) {
        log.info("[接口耗时] {} -> {}ms", methodPath, elapsed);
    } else if (elapsed < 5000) {
        log.warn("[慢接口] {} -> {}ms", methodPath, elapsed);
    } else {
        log.error("[超慢接口] {} -> {}ms，建议优化", methodPath, elapsed);
        // 可以触发告警
    }

    return result;
}
```

---

### 场景 3：权限校验

替代在每个方法里写 `if (!hasPermission(...)) throw new ...`。

**注解：**

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RequirePermission {

    /** 权限标识（如 "user:delete", "order:create"） */
    String value();

    /** 多个权限的逻辑：AND / OR */
    Logical logical() default Logical.AND;

    enum Logical { AND, OR }
}
```

**切面：**

```java
@Aspect
@Component
@Order(1)   // 先于业务切面执行
public class PermissionAspect {

    @Autowired(required = false)
    private HttpServletRequest request;

    @Around("@annotation(requirePermission)")
    public Object around(ProceedingJoinPoint joinPoint, RequirePermission requirePermission) throws Throwable {
        // 从请求中获取当前用户拥有的权限列表
        Set<String> userPermissions = getCurrentUserPermissions();

        String[] required = requirePermission.value().split(",");

        boolean allowed;
        if (requirePermission.logical() == RequirePermission.Logical.AND) {
            // 所有权限都要有
            allowed = Arrays.stream(required).allMatch(userPermissions::contains);
        } else {
            // 只要有一个
            allowed = Arrays.stream(required).anyMatch(userPermissions::contains);
        }

        if (!allowed) {
            throw new BusinessException("权限不足，需要：" + String.join(", ", required));
        }

        return joinPoint.proceed();
    }

    private Set<String> getCurrentUserPermissions() {
        // 从 JWT 或 Redis 中获取
        String token = request.getHeader("Authorization");
        // 解析 token 获取权限列表...
        return Set.of("user:query", "user:update"); // 示例
    }
}
```

**使用：**

```java
@RequirePermission("user:delete")
@DeleteMapping("/users/{id}")
public R<Void> deleteUser(@PathVariable Long id) { ... }

@RequirePermission("user:update,user:audit")  // 两个权限都要
@PutMapping("/users/{id}/status")
public R<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) { ... }
```

---

### 场景 4：参数校验（类型校验，自定义规则）

Spring MVC 自带的 `@Valid` 解决了基础校验。当需要自定义校验规则（比如"用户状态不能是未激活时调用付费接口"），用 AOP 补充。

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface CheckParam {

    /** SpEL 表达式，返回 true 才通过 */
    String value();
}
```

```java
@Aspect
@Component
public class ParamCheckAspect {

    // 需要引入 SpEL 解析
    @Autowired
    private ExpressionParser parser;

    @Around("@annotation(checkParam)")
    public Object around(ProceedingJoinPoint joinPoint, CheckParam checkParam) throws Throwable {
        // SpEL 上下文注入方法参数
        StandardEvaluationContext context = new StandardEvaluationContext();
        String[] paramNames = getParamNames(joinPoint);
        Object[] args = joinPoint.getArgs();
        for (int i = 0; i < paramNames.length; i++) {
            context.setVariable(paramNames[i], args[i]);
        }

        Boolean result = parser.parseExpression(checkParam.value()).getValue(context, Boolean.class);
        if (Boolean.FALSE.equals(result)) {
            throw new BusinessException("参数校验失败: " + checkParam.value());
        }

        return joinPoint.proceed();
    }

    // 获取方法参数名（需要编译时 -parameters，或借助 LocalVariableTableParameterNameDiscoverer）
    private String[] getParamNames(ProceedingJoinPoint joinPoint) {
        // Spring 自带的获取方式
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        return signature.getParameterNames();
    }
}
```

```java
@CheckParam("#amount > 0 and #amount <= #balance")
// 金额必须大于 0 且不能超过余额
public void transfer(Long userId, BigDecimal amount, BigDecimal balance) {
    // ...
}
```

---

### 场景 5：缓存（声明式缓存增强）

Spring Cache（`@Cacheable`、`@CacheEvict`）本身就是基于 AOP 实现的。这里展示如何自定义缓存逻辑。

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RedisCache {

    /** 缓存 key 前缀 */
    String key();

    /** 过期时间（秒） */
    long expire() default 300;

    /** 是否缓存 null 值 */
    boolean cacheNull() default false;
}
```

```java
@Aspect
@Component
public class RedisCacheAspect {

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Autowired
    private ExpressionParser parser;

    @Around("@annotation(redisCache)")
    public Object around(ProceedingJoinPoint joinPoint, RedisCache redisCache) throws Throwable {
        // 构建缓存 key（支持 SpEL）
        String cacheKey = buildKey(redisCache.key(), joinPoint);

        // 先查缓存
        String cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            // 缓存命中
            return deserialize(cached, joinPoint);
        }

        // 缓存未命中，执行目标方法
        Object result = joinPoint.proceed();

        // 回写缓存
        if (result != null || redisCache.cacheNull()) {
            String serialized = serialize(result);
            redisTemplate.opsForValue().set(cacheKey, serialized,
                    redisCache.expire(), TimeUnit.SECONDS);
        }

        return result;
    }

    private String buildKey(String keyExp, ProceedingJoinPoint joinPoint) {
        // 如果 key 是常量直接返回，否则 SpEL 解析
        if (!keyExp.contains("#")) {
            return keyExp;
        }
        StandardEvaluationContext context = new StandardEvaluationContext();
        String[] names = ((MethodSignature) joinPoint.getSignature()).getParameterNames();
        Object[] args = joinPoint.getArgs();
        for (int i = 0; i < names.length; i++) {
            context.setVariable(names[i], args[i]);
        }
        return parser.parseExpression(keyExp).getValue(context, String.class);
    }

    private String serialize(Object obj) {
        try {
            return new ObjectMapper().writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("序列化失败", e);
        }
    }

    private Object deserialize(String json, ProceedingJoinPoint joinPoint) throws Throwable {
        Class<?> returnType = ((MethodSignature) joinPoint.getSignature()).getReturnType();
        if (returnType == void.class || returnType == Void.class) {
            return null;
        }
        return new ObjectMapper().readValue(json, returnType);
    }
}
```

```java
@RedisCache(key = "'user:' + #id", expire = 600)
public User getUserById(Long id) {
    return userMapper.selectById(id);
}
```

---

### 场景 6：分布式锁

防止同一个方法被多个实例同时执行（如定时任务）。参见 [[spring-boot-redisson]]。

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface DistributeLock {

    /** 锁的 key（支持 SpEL） */
    String key();

    /** 等待获取锁的时间（秒） */
    long waitTime() default 3;

    /** 锁的自动释放时间（秒） */
    long leaseTime() default 10;
}
```

```java
@Aspect
@Component
public class DistributeLockAspect {

    @Autowired
    private RedissonClient redissonClient;

    @Around("@annotation(distributeLock)")
    public Object around(ProceedingJoinPoint joinPoint, DistributeLock distributeLock) throws Throwable {
        String lockKey = buildKey(distributeLock.key(), joinPoint);
        RLock lock = redissonClient.getLock(lockKey);

        boolean acquired = false;
        try {
            acquired = lock.tryLock(distributeLock.waitTime(), distributeLock.leaseTime(), TimeUnit.SECONDS);
            if (!acquired) {
                throw new BusinessException("系统繁忙，请稍后重试");
            }
            return joinPoint.proceed();
        } finally {
            if (acquired && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }

    private String buildKey(String keyExp, ProceedingJoinPoint joinPoint) {
        // SpEL 解析，同上
        if (!keyExp.contains("#")) return keyExp;
        // ... 省略具体实现
        return keyExp;
    }
}
```

```java
@DistributeLock(key = "'order:cancel:' + #orderId")
public void cancelOrder(Long orderId) {
    // 取消订单（同一订单不会并发取消）
}
```

---

### 场景 7：接口限流

防止单个 IP/用户调用频率过高。最简单的实现基于 Guava RateLimiter 或 Redis。

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RateLimit {

    /** 每秒允许的请求数 */
    double permitsPerSecond() default 5.0;

    /** 限流维度：IP / USER */
    LimitType type() default LimitType.IP;

    enum LimitType { IP, USER }
}
```

**Redis 滑动窗口实现：**

```java
@Aspect
@Component
public class RateLimitAspect {

    @Autowired
    private StringRedisTemplate redisTemplate;
    @Autowired(required = false)
    private HttpServletRequest request;

    private static final String RATE_LIMIT_KEY = "rate_limit:%s:%s";

    @Around("@annotation(rateLimit)")
    public Object around(ProceedingJoinPoint joinPoint, RateLimit rateLimit) throws Throwable {
        String methodName = joinPoint.getSignature().toShortString();
        String key = buildRateLimitKey(rateLimit.type(), methodName);

        // 滑动窗口算法：用 Redis ZSet，score 为时间戳
        long now = System.currentTimeMillis();
        long windowStart = now - 1000;  // 过去 1 秒

        // 删除窗口外的记录
        redisTemplate.opsForZSet().removeRangeByScore(key, 0, windowStart);

        // 统计当前窗口内的请求数
        Long count = redisTemplate.opsForZSet().count(key, windowStart, now);

        if (count != null && count >= rateLimit.permitsPerSecond()) {
            throw new BusinessException("请求过于频繁，请稍后再试");
        }

        // 记录本次请求
        redisTemplate.opsForZSet().add(key, String.valueOf(now), now);
        redisTemplate.expire(key, 2, TimeUnit.SECONDS);

        return joinPoint.proceed();
    }

    private String buildRateLimitKey(RateLimit.LimitType type, String method) {
        String identifier;
        if (type == RateLimit.LimitType.IP && request != null) {
            identifier = getClientIp(request);
        } else {
            identifier = request != null ? request.getHeader("X-Username") : "anonymous";
        }
        return String.format(RATE_LIMIT_KEY, identifier, method);
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) ip = request.getHeader("X-Real-IP");
        if (ip == null || ip.isEmpty()) ip = request.getRemoteAddr();
        return ip != null ? ip.split(",")[0].trim() : "unknown";
    }
}
```

```java
@RateLimit(permitsPerSecond = 1.0)  // 每秒最多 1 次
@PostMapping("/sms/send-verify-code")
public R<Void> sendVerifyCode(@RequestParam String phone) {
    // ...
}
```

---

### 场景 8：接口幂等（防重复提交）

基于唯一 token，同一请求在 N 秒内只能执行一次。

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Idempotent {

    /** 幂等 key（支持 SpEL） */
    String key();

    /** 幂等有效期（秒） */
    long expire() default 5;
}
```

```java
@Aspect
@Component
public class IdempotentAspect {

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Around("@annotation(idempotent)")
    public Object around(ProceedingJoinPoint joinPoint, Idempotent idempotent) throws Throwable {
        // 构建幂等 key
        String key = buildKey(idempotent.key(), joinPoint);

        // 尝试设置（SETNX）
        Boolean success = redisTemplate.opsForValue()
                .setIfAbsent(key, "1", idempotent.expire(), TimeUnit.SECONDS);

        if (Boolean.FALSE.equals(success)) {
            throw new BusinessException("请勿重复提交");
        }

        return joinPoint.proceed();
    }

    private String buildKey(String keyExp, ProceedingJoinPoint joinPoint) {
        // 如果 key 包含 # 且需要 SpEL，参考前文实现
        return "idempotent:" + keyExp;
    }
}
```

**配合前端 Token 模式：**

```java
// 前端先获取 token
@GetMapping("/idempotent-token")
public R<String> getToken() {
    String token = UUID.randomUUID().toString();
    redisTemplate.opsForValue().set("token:" + token, "1", 5, TimeUnit.MINUTES);
    return R.ok(token);
}

// 提交时在请求头带上 token
@Idempotent(key = "#header['X-Idempotent-Token']")
@PostMapping("/orders")
public R<Long> createOrder(@RequestBody OrderCreateDTO dto,
                            @RequestHeader("X-Idempotent-Token") String token) {
    // 方法执行完后，AOP 不清除 key（靠 expire 自动清理）
    return R.ok(orderService.create(dto));
}
```

---

### 场景 9：异常重试

特定异常（如网络超时、数据库死锁）自动重试。

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Retryable {

    /** 最大重试次数 */
    int maxAttempts() default 3;

    /** 重试间隔（毫秒） */
    long backoff() default 1000;

    /** 需要重试的异常类型 */
    Class<? extends Throwable>[] retryFor() default {Exception.class};
}
```

```java
@Aspect
@Component
@Slf4j
public class RetryAspect {

    @Around("@annotation(retryable)")
    public Object around(ProceedingJoinPoint joinPoint, Retryable retryable) throws Throwable {
        int attempts = 0;
        Throwable lastException;

        do {
            attempts++;
            try {
                return joinPoint.proceed();
            } catch (Throwable e) {
                lastException = e;

                // 检查是否需要重试
                boolean shouldRetry = false;
                for (Class<? extends Throwable> clazz : retryable.retryFor()) {
                    if (clazz.isAssignableFrom(e.getClass())) {
                        shouldRetry = true;
                        break;
                    }
                }

                if (!shouldRetry || attempts >= retryable.maxAttempts()) {
                    throw e;
                }

                log.warn("方法 {} 第{}次执行失败: {}，{}ms 后重试",
                        joinPoint.getSignature().getName(),
                        attempts,
                        e.getMessage(),
                        retryable.backoff() * attempts);

                Thread.sleep(retryable.backoff() * attempts);
            }
        } while (attempts < retryable.maxAttempts());

        throw new RuntimeException("unreachable");
    }
}
```

```java
// 调用外部 API 超时时最多重试 3 次
@Retryable(maxAttempts = 3, backoff = 2000,
           retryFor = {SocketTimeoutException.class, ConnectException.class})
public OrderStatus queryOrderStatus(String orderNo) {
    return thirdPartyApi.query(orderNo);
}
```

---

### 场景 10：数据脱敏

返回给前端的敏感数据（手机号、身份证、邮箱）自动脱敏。

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Desensitize {

    /** 脱敏字段：phone/idCard/email/bankCard */
    String[] fields() default {};
}
```

```java
@Aspect
@Component
public class DesensitizeAspect {

    @Around("@annotation(desensitize)")
    public Object around(ProceedingJoinPoint joinPoint, Desensitize desensitize) throws Throwable {
        Object result = joinPoint.proceed();
        return desensitizeFields(result, Set.of(desensitize.fields()));
    }

    private Object desensitizeFields(Object obj, Set<String> fields) {
        if (obj == null) return null;
        if (fields.isEmpty()) return obj;

        try {
            // 反射遍历字段
            for (Field field : obj.getClass().getDeclaredFields()) {
                if (fields.contains(field.getName())) {
                    field.setAccessible(true);
                    Object value = field.get(obj);
                    if (value instanceof String s) {
                        field.set(obj, mask(s, field.getName()));
                    }
                }
            }
        } catch (IllegalAccessException e) {
            // ignore
        }
        return obj;
    }

    private String mask(String value, String fieldName) {
        if (value == null || value.isEmpty()) return value;

        return switch (fieldName) {
            case "phone" -> value.replaceAll("(\\d{3})\\d{4}(\\d{4})", "$1****$2");
            case "idCard" -> value.replaceAll("(\\d{4})\\d{10}(\\d{4})", "$1****$2");
            case "email" -> value.replaceAll("(\\w{2})\\w+(@\\w+)", "$1****$2");
            case "bankCard" -> value.replaceAll("(\\d{4})\\d+(\\d{4})", "$1****$2");
            default -> value;
        };
    }
}
```

```java
@Desensitize(fields = {"phone", "email", "idCard"})
@GetMapping("/users/{id}")
public R<UserVO> getUser(@PathVariable Long id) {
    UserVO user = userService.getById(id);
    return R.ok(user);
    // 手机 138****1234、邮箱 zh****@qq.com、身份证 3201****5678
}
```

---

### 场景 11：请求参数加解密

前端的请求体加密传过来，Controller 接收前先解密；返回给前端的数据加密后再返回。

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Crypto {

    /** 是否解密入参 */
    boolean decrypt() default true;

    /** 是否加密返回值 */
    boolean encrypt() default true;
}
```

```java
@Aspect
@Component
public class CryptoAspect {

    @Around("@annotation(crypto)")
    public Object around(ProceedingJoinPoint joinPoint, Crypto crypto) throws Throwable {
        Object[] args = joinPoint.getArgs();

        // 解密入参
        if (crypto.decrypt()) {
            for (int i = 0; i < args.length; i++) {
                if (args[i] instanceof String encrypted) {
                    args[i] = AESUtils.decrypt(encrypted);
                }
            }
        }

        // 执行目标方法
        Object result = joinPoint.proceed(args);

        // 加密出参
        if (crypto.encrypt() && result instanceof String plain) {
            result = AESUtils.encrypt(plain);
        }

        return result;
    }
}
```

---

### 场景 12：防 SQL 注入 / XSS 过滤

对所有 String 入参做 XSS 过滤，放在 Controller 层统一处理。

```java
@Aspect
@Component
@Order(2)
public class XssFilterAspect {

    @Around("execution(* com.example.controller..*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        Object[] args = joinPoint.getArgs();

        for (int i = 0; i < args.length; i++) {
            if (args[i] instanceof String s) {
                args[i] = cleanXss(s);
            }
        }

        return joinPoint.proceed(args);
    }

    private String cleanXss(String value) {
        return value
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll("\"", "&quot;")
                .replaceAll("'", "&#x27;")
                .replaceAll("&", "&amp;");
    }
}
```

---

### 场景 13：ThreadLocal 上下文自动清理

请求结束后的 ThreadLocal 清理，避免内存泄漏。

```java
@Aspect
@Component
@Order(Integer.MAX_VALUE)  // 最后执行
public class ThreadLocalCleanAspect {

    @Around("execution(* com.example.controller..*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        try {
            return joinPoint.proceed();
        } finally {
            // 请求结束时清理 ThreadLocal
            UserContextHolder.clear();
            TraceContextHolder.clear();
        }
    }
}
```

---

### 场景 14：统一异常处理（替代 @RestControllerAdvice 的补充）

虽然 Spring 提供了 `@RestControllerAdvice`，但如果有特殊逻辑需要在异常时记录上下文（如当前方法的参数），用 AOP 更灵活。

```java
@Aspect
@Component
public class ExceptionRecordAspect {

    @AfterThrowing(
        pointcut = "execution(* com.example.service..*.*(..))",
        throwing = "ex"
    )
    public void recordException(JoinPoint joinPoint, RuntimeException ex) {
        String method = joinPoint.getSignature().toShortString();
        Object[] args = joinPoint.getArgs();

        // 不是所有异常都记录——只记录意料之外的
        if (!(ex instanceof BusinessException)) {
            log.error("[未预期异常] 方法={}, 参数={}", method, safeToString(args), ex);
        }
    }

    private String safeToString(Object[] args) {
        try {
            return Arrays.toString(args);
        } catch (Exception e) {
            return "[...]";
        }
    }
}
```

---

### 场景 15：数据库读写分离

根据方法前缀（get/query/find 走读库，save/insert/update/delete 走写库），自动切换数据源。

```java
@Aspect
@Component
@Order(-1)  // 先于事务切面
public class DataSourceAspect {

    @Around("execution(* com.example.service..*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName().toLowerCase();

        if (methodName.startsWith("get") || methodName.startsWith("query")
                || methodName.startsWith("find") || methodName.startsWith("list")
                || methodName.startsWith("count")) {
            // 读库
            DynamicDataSourceContext.setDataSourceKey("read");
        } else {
            // 写库
            DynamicDataSourceContext.setDataSourceKey("write");
        }

        try {
            return joinPoint.proceed();
        } finally {
            DynamicDataSourceContext.clear();
        }
    }
}
```

---

### 场景 16：全局请求 traceId

在请求入口注入 traceId，所有后续日志自动带上，方便链路追踪。

```java
@Aspect
@Component
@Order(0)
public class TraceIdAspect {

    @Around("execution(* com.example.controller..*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        String traceId;

        // 优先从请求头取（网关透传的），没有就自己生成
        ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attributes != null) {
            HttpServletRequest request = attributes.getRequest();
            traceId = request.getHeader("X-Trace-Id");
        } else {
            traceId = null;
        }

        if (traceId == null || traceId.isEmpty()) {
            traceId = UUID.randomUUID().toString().replace("-", "");
        }

        // 注入到 MDC（日志框架自动识别）
        MDC.put("traceId", traceId);

        try {
            return joinPoint.proceed();
        } finally {
            MDC.remove("traceId");
        }
    }
}
```

配合 `logback-spring.xml`：

```xml
<appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
        <pattern>%d{HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger - %msg%n</pattern>
    </encoder>
</appender>
```

---

## 8. 最佳实践与踩坑记录

### 8.1 推荐做法

**1. 自定义注解 + AOP，不要写死切点**

```java
// 不推荐：按方法名匹配，重构就断
@Around("execution(* com.example.service.*.delete*(..))")

// 推荐：注解驱动
@Around("@annotation(com.example.annotation.OperationLog)")
```

**2. Around 中一定 try-finally 或正确传播异常**

```java
@Around("...")
public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
    // 需要清理的资源用 try-finally
    long start = System.currentTimeMillis();
    try {
        return joinPoint.proceed();
    } catch (Exception e) {
        log.error("...", e);
        throw e;  // 必须抛，否则上层感知不到
    } finally {
        log.info("cost: {}ms", System.currentTimeMillis() - start);
    }
}
```

**3. 多个切面时用 @Order 控制顺序**

典型顺序：TraceId -> 权限 -> 参数校验 -> 幂等 -> 限流 -> 缓存 -> 业务 -> 日志。

**4. 切面的依赖注入用 `required = false`**

切面也可能在没有对应依赖的环境中运行（如单元测试），加 `required = false` 防止启动报错。

```java
@Autowired(required = false)
private HttpServletRequest request;
```

**5. 能用 @After/AfterReturning 就不用 Around**

Around 虽然最灵活，但需要手动调 `proceed()`，忘了就成空操作。Before/After 语义更明确，不易出错。

### 8.2 踩坑记录

**坑 1：同类内部调用不走代理**

```java
@Service
public class UserService {

    public void methodA() {
        // 直接调 methodB，不走 AOP
        this.methodB();
    }

    @OperationLog(module = "用户")
    public void methodB() {
        // @OperationLog 不生效！
    }
}
```

解决方案一：注入自己

```java
@Service
public class UserService {
    @Autowired
    private UserService self;

    public void methodA() {
        self.methodB();  // 走代理
    }
}
```

解决方案二：拆到另一个类

```java
@Service
public class UserLogService {
    @OperationLog(module = "用户")
    public void methodB() { ... }
}
```

**坑 2：AOP 不拦截 final 方法和 private 方法**

CGLIB 通过生成子类实现代理，final 方法不能被子类重写，private 方法不可见。Spring AOP 对这两种方法无效。

```java
// @Cacheable 不会生效
@Cacheable("users")
public final User getUser(Long id) { ... }

// @Transactional 不会生效
@Transactional
private void doBusiness() { ... }
```

**坑 3：@Around 吞了异常**

```java
// 错误的写法
@Around("...")
public Object around(ProceedingJoinPoint pjp) {
    try {
        return pjp.proceed();
    } catch (Throwable e) {
        log.error("出错", e);
        return null;  // 异常被吞了，上层以为是正常返回 null
    }
}
```

正确的做法是如果不是业务上真的需要吞异常，就原样抛出：

```java
} catch (Throwable e) {
    log.error("出错", e);
    throw e;  // 继续传播
}
```

**坑 4：切点表达式匹配范围过大导致性能问题**

```java
// 不推荐：拦截所有方法，每次调用都走一遍切面
@Around("execution(* *(..))")

// 推荐：限定到具体包
@Around("execution(* com.example.controller..*.*(..))")
```

**坑 5：用了 @Around 但没调 proceed()**

```java
@Around("...")
public Object around(ProceedingJoinPoint pjp) {
    log.info("进入");
    // 忘了调 pjp.proceed() —— 目标方法永远不会执行
    return null;
}
```

**坑 6：@Transactional 是 AOP，和自定义切面的顺序冲突**

`@Transactional` 本身就是 Spring 基于 AOP 实现的。如果你的切面按方法前缀切换数据源（读写分离），得确保数据源切面在事务切面**前面**执行：

```java
@Aspect
@Component
@Order(-1)  // 比事务切面（默认 Order）更靠前
public class DataSourceAspect { ... }
```

**坑 7：Aspect 类必须加 @Component**

只加 `@Aspect` 不加 `@Component`（或不在配置类中声明为 Bean），Spring 不会把它纳入容器管理，切面永远不生效。

---

## 9. 参考链接

- Spring AOP 官方文档：https://docs.spring.io/spring-framework/reference/core/aop.html
- AspectJ 切点表达式语法：https://www.eclipse.org/aspectj/doc/released/progguide/semantics-pointcuts.html
- Spring Boot AOP 示例：https://github.com/spring-projects/spring-boot/tree/main/spring-boot-project/spring-boot-starters/spring-boot-starter-aop
- [[spring-boot-redisson]] — 分布式锁 + AOP 实现
- [[spring-boot-redis]] — 缓存注解的底层依赖
- [[spring-boot-mybatis-plus]] — 读写分离数据源切换
