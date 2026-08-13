---
title: Spring 事务
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring, transaction, transactional, propagation, isolation, rollback, transactionmanager, aop]
---

# Spring 事务

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Spring 事务抽象](#spring-事务抽象)
- [PlatformTransactionManager](#platformtransactionmanager)
- [声明式事务 —— @Transactional](#声明式事务--transactional)
- [编程式事务](#编程式事务)
- [事务同步与事务事件](#事务同步与事务事件)
- [事务传播行为](#事务传播行为)
- [事务隔离级别](#事务隔离级别)
- [事务回滚规则](#事务回滚规则)
- [事务失效场景（8 种）](#事务失效场景8-种)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring 事务管理的核心价值是**统一的事务抽象**——无论底层使用 JDBC、Hibernate、JPA 还是 MyBatis，上层的使用方式完全一致。

```text
  Service 层
      |
  @Transactional（声明式事务 —— AOP 实现）
      |
  PlatformTransactionManager（统一事务接口）
      |
  ┌───┴───┬──────────┬──────────┐
  JDBC    Hibernate  JPA       JTA
  (DataSourceTransactionManager)
```

Spring 事务基于 AOP 实现。`@Transactional` 注解方法的调用会被代理拦截，在方法执行前后开启/提交/回滚事务。

## Spring 事务抽象

Spring 事务的核心接口：

```java
// 事务管理器 —— 创建/提交/回滚事务
public interface PlatformTransactionManager {
    TransactionStatus getTransaction(TransactionDefinition definition) throws TransactionException;
    void commit(TransactionStatus status) throws TransactionException;
    void rollback(TransactionStatus status) throws TransactionException;
}

// 事务定义 —— 传播行为、隔离级别、超时、只读
public interface TransactionDefinition {
    int getPropagationBehavior();    // 传播行为
    int getIsolationLevel();         // 隔离级别
    int getTimeout();               // 超时时间（秒）
    boolean isReadOnly();           // 是否只读
    String getName();               // 事务名称
}

// 事务状态 —— 事务是否已完成、是否新事务、是否有保存点
public interface TransactionStatus {
    boolean isNewTransaction();
    boolean hasSavepoint();
    void setRollbackOnly();         // 标记为回滚
    boolean isRollbackOnly();
    boolean isCompleted();
}
```

## PlatformTransactionManager

Spring 提供了多种事务管理器实现：

| 实现类 | 适用场景 |
|--------|---------|
| DataSourceTransactionManager | 单个 JDBC DataSource |
| JpaTransactionManager | JPA（Hibernate） |
| HibernateTransactionManager | 原生 Hibernate |
| JtaTransactionManager | 分布式事务（JTA） |
| JdbcTransactionManager | Spring 5.3+，DataSourceTransactionManager 的替代 |

Spring Boot 根据类路径自动配置：

```java
// Spring Boot 自动配置逻辑（简化）
@ConditionalOnClass(DataSource.class)
@ConditionalOnMissingBean(PlatformTransactionManager.class)
public DataSourceTransactionManager transactionManager(DataSource dataSource) {
    return new DataSourceTransactionManager(dataSource);
}
```

## 声明式事务 —— @Transactional

声明式事务是 Spring 最常用的使用方式——在方法上加 `@Transactional` 注解，框架通过 AOP 自动管理事务。

### 基本使用

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderDTO dto) {
        orderDao.insert(order);
        orderDao.insertItems(order.getItems());
        inventoryDao.decreaseStock(order.getItems());
    }
    // 方法正常结束时 commit，抛 RuntimeException 时 rollback
}
```

### 注解属性详解

```java
@Transactional(
    propagation = Propagation.REQUIRED,        // 传播行为
    isolation = Isolation.DEFAULT,             // 隔离级别（跟随数据库默认）
    timeout = 30,                              // 超时秒数（-1 = 不限制）
    readOnly = false,                          // 是否只读
    rollbackFor = Exception.class,             // 哪些异常回滚
    noRollbackFor = IllegalArgumentException.class,  // 哪些异常不回滚
    transactionManager = "transactionManager", // 指定事务管理器（多数据源时使用）
    value = "transactionManager"               // transactionManager 的别名
)
public void doSomething() { }
```

### @Transactional 可以放在哪里

```java
// 类级别 —— 对该类所有 public 方法生效
@Service
@Transactional(readOnly = true)  // 默认只读
public class UserQueryService {

    public User findById(Long id) {  // 继承类级别配置：readOnly=true
        return userDao.findById(id);
    }

    @Transactional(readOnly = false)  // 方法级别覆盖
    public void updateUser(User user) {
        userDao.update(user);
    }
}

// 接口级别 —— 不推荐（Spring 推荐用在具体类上）
public interface UserService {
    @Transactional
    void createUser(User user);
}
```

**Spring 官方建议**：`@Transactional` 用在**具体类或方法**上，不要用在接口上。原因：
- 基于接口的代理模式下，接口上的注解会被继承
- 但在 CGLIB 代理（Spring Boot 默认）中，接口上的注解不会被继承
- 不统一导致混淆

### tx:advice XML 声明式事务

`@Transactional` 出现之前，声明式事务通过 XML 的 `tx:advice` 配置（遗留项目会遇到）：

```xml
<beans xmlns:tx="http://www.springframework.org/schema/tx"
       xmlns:aop="http://www.springframework.org/schema/aop">

    <!-- 事务管理器 -->
    <bean id="transactionManager"
          class="org.springframework.jdbc.datasource.DataSourceTransactionManager">
        <property name="dataSource" ref="dataSource" />
    </bean>

    <!-- 事务通知：定义事务行为 -->
    <tx:advice id="txAdvice" transaction-manager="transactionManager">
        <tx:attributes>
            <!-- 查询方法：只读 -->
            <tx:method name="get*" read-only="true" />
            <tx:method name="find*" read-only="true" />
            <tx:method name="query*" read-only="true" />
            <!-- 写方法：默认 REQUIRED -->
            <tx:method name="save*" />
            <tx:method name="insert*" />
            <tx:method name="update*" propagation="REQUIRED" rollback-for="Exception" />
            <tx:method name="delete*" />
            <!-- 兜底 -->
            <tx:method name="*" />
        </tx:attributes>
    </tx:advice>

    <!-- 将事务通知绑定到切点 -->
    <aop:config>
        <aop:pointcut id="serviceMethods"
            expression="execution(* com.example.service.*.*(..))" />
        <aop:advisor advice-ref="txAdvice" pointcut-ref="serviceMethods" />
    </aop:config>
</beans>
```

关键点：

1. `<tx:method>` 的 `name` 支持通配符（`*`、`get*`），按声明顺序匹配
2. 属性与 `@Transactional` 完全对应：`propagation`、`isolation`、`read-only`、`rollback-for`、`timeout`
3. 底层机制与 `@Transactional` 相同——都是 AOP 代理 + 事务通知

启用注解方式只需一行：`<tx:annotation-driven transaction-manager="transactionManager" />`（等价于 `@EnableTransactionManagement`）。

## 编程式事务

声明式事务覆盖 95% 的场景，但编程式事务在需要更精细控制时很有用。

### TransactionTemplate

```java
@Service
public class OrderService {

    @Autowired
    private TransactionTemplate transactionTemplate;

    public void createOrder(OrderDTO dto) {
        transactionTemplate.execute(status -> {
            try {
                orderDao.insert(dto.toOrder());
                inventoryDao.decrease(dto.getItems());

                // 如果库存不足，手动标记回滚
                if (inventoryInsufficient(dto)) {
                    status.setRollbackOnly();
                    return null;
                }

                return null;

            } catch (Exception e) {
                status.setRollbackOnly();
                throw e;
            }
        });
    }
}
```

### PlatformTransactionManager 直接使用

```java
@Service
public class OrderService {

    @Autowired
    private PlatformTransactionManager transactionManager;

    public void createOrder(OrderDTO dto) {
        DefaultTransactionDefinition def = new DefaultTransactionDefinition();
        def.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);
        def.setIsolationLevel(TransactionDefinition.ISOLATION_READ_COMMITTED);
        def.setTimeout(30);

        TransactionStatus status = transactionManager.getTransaction(def);

        try {
            orderDao.insert(dto.toOrder());
            inventoryDao.decrease(dto.getItems());

            transactionManager.commit(status);

        } catch (Exception e) {
            transactionManager.rollback(status);
            throw e;
        }
    }
}
```

### 声明式 vs 编程式

| 维度 | 声明式（@Transactional） | 编程式 |
|------|-------------------------|--------|
| 代码量 | 一行注解 | 10+ 行 |
| 粒度 | 方法级别 | 代码块级别 |
| 灵活性 | 固定模式 | 完全控制 |
| 可读性 | 高 | 对开发者要求高 |
| 适用场景 | 标准 CRUD | 复杂事务逻辑、部分回滚 |

## 事务同步与事务事件

Spring 提供了两个与事务生命周期联动的机制：事务同步（Transaction Synchronization）和事务事件（Transaction-bound Events）。

### TransactionSynchronizationManager

`TransactionSynchronizationManager` 是事务的"幕后管家"，它把事务资源（数据库连接、事务状态）绑定到当前线程，并提供事务生命周期的回调注册。

```java
@Service
public class OrderService {

    @Autowired
    private TransactionTemplate transactionTemplate;

    public void createOrder(Order order) {
        transactionTemplate.execute(status -> {
            // 注册事务同步回调
            TransactionSynchronizationManager.registerSynchronization(
                new TransactionSynchronization() {

                    @Override
                    public void afterCommit() {
                        // 事务提交后执行 —— 常用于发消息、清缓存
                        mqProducer.send(new OrderCreatedMessage(order));
                        cacheManager.evict("order:" + order.getId());
                    }

                    @Override
                    public void afterCompletion(int status) {
                        // 事务结束（提交或回滚）后执行 —— 常用于清理资源
                        // STATUS_COMMITTED / STATUS_ROLLED_BACK / STATUS_UNKNOWN
                        cleanupResources();
                    }
                }
            );

            orderDao.insert(order);
            return null;
        });
    }
}
```

TransactionSynchronization 接口的回调方法：

| 回调 | 触发时机 |
|------|---------|
| beforeCommit | 事务提交前（可以在此读取事务性资源） |
| beforeCompletion | 事务结束前（提交/回滚） |
| afterCommit | 事务提交后（最常用：发消息、清缓存） |
| afterCompletion | 事务结束后（提交/回滚），做最终清理 |

**核心价值**：`afterCommit()` 保证只有事务真正提交了，后续操作才执行。这解决了"事务还没提交就发消息，消费者读到旧数据"的经典问题。

其他常用方法：

```java
// 判断当前线程是否在事务中
boolean inTx = TransactionSynchronizationManager.isActualTransactionActive();

// 判断当前事务是否只读
boolean readOnly = TransactionSynchronizationManager.isCurrentTransactionReadOnly();

// 绑定资源到当前线程（如 DataSource 连接）
TransactionSynchronizationManager.bindResource(dataSource, connection);

// 获取绑定资源
Connection conn = (Connection) TransactionSynchronizationManager.getResource(dataSource);
```

### @TransactionalEventListener

`@TransactionalEventListener` 是事务事件的注解版，相比 `@EventListener`，它让事件监听绑定到事务生命周期。这是 `afterCommit` 的声明式替代。

```java
// 发布事件（在事务方法内）
@Service
public class OrderService {

    @Autowired
    private ApplicationEventPublisher publisher;

    @Transactional
    public void createOrder(OrderDTO dto) {
        Order order = orderDao.insert(dto.toOrder());
        // 发布事件 —— 监听器会在事务提交后执行
        publisher.publishEvent(new OrderCreatedEvent(this, order));
    }
}

// 监听事件 —— 事务提交后才执行
@Component
public class OrderNotificationListener {

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleOrderCreated(OrderCreatedEvent event) {
        // 事务已提交，此时发消息/短信是安全的
        smsService.send("订单 " + event.getOrderId() + " 创建成功");
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_ROLLBACK)
    public void handleOrderRollback(OrderCreatedEvent event) {
        // 事务回滚了 —— 记录异常、补偿
        log.warn("订单创建回滚：{}", event.getOrderId());
    }
}
```

TransactionPhase 的取值：

| Phase | 说明 |
|-------|------|
| BEFORE_COMMIT | 事务提交前 |
| AFTER_COMMIT（默认） | 事务提交后 |
| AFTER_ROLLBACK | 事务回滚后 |
| AFTER_COMPLETION | 事务结束后（提交或回滚） |

与 `@EventListener` 的关键区别：

| 维度 | @EventListener | @TransactionalEventListener |
|------|---------------|---------------------------|
| 执行时机 | 立即同步执行 | 绑定事务生命周期 |
| 无事务时 | 正常执行 | 不执行（除非 fallbackExecution=true） |
| 典型场景 | 通用事件 | 事务成功后的副作用 |

```java
// fallbackExecution=true：没有事务时也执行
@TransactionalEventListener(
    phase = TransactionPhase.AFTER_COMMIT,
    fallbackExecution = true
)
public void handle(OrderCreatedEvent event) {
    // 即使发布方不在事务中，也执行监听
}
```

**实战建议**：凡是"事务提交后才该做的事"——发消息、清缓存、通知第三方——都应该用 `@TransactionalEventListener(AFTER_COMMIT)`，避免事务未提交就产生副作用。

## 事务传播行为

事务传播定义了**一个事务方法被另一个事务方法调用时**，事务应该如何传播。

Spring 定义了 7 种传播行为：

### REQUIRED（默认）

```java
@Transactional(propagation = Propagation.REQUIRED)
public void methodA() {
    // 如果当前有事务，加入；没有则新建
    methodB();  // methodB 也是 REQUIRED，加入 methodA 的事务
}
```

- 有事务：加入当前事务
- 无事务：创建新事务
- 使用频率最高，适合大多数场景

### REQUIRES_NEW

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void methodB() {
    // 不管当前有无事务，总是新开一个事务
    // 新事务与外部事务完全独立
}
```

- 挂起当前事务（如果存在），创建全新事务
- 新事务提交/回滚不影响外部事务

```java
@Transactional  // REQUIRED
public void placeOrder(Order order) {
    orderDao.insert(order);  // 主流程 —— 必须成功

    try {
        logService.recordLog(order);  // 记日志 —— 失败不影响主流程
    } catch (Exception e) {
        // 日志失败，主订单依然提交
    }
}

@Service
public class LogService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordLog(Order order) {
        logDao.insert(order);
    }
}
```

### SUPPORTS

- 有事务：加入
- 无事务：非事务执行（裸跑）

适合查询方法——有事务时参与，没事务时也不强求。

### NOT_SUPPORTED

- 有事务：挂起当前事务，非事务执行
- 无事务：非事务执行

### MANDATORY

- 有事务：加入
- 无事务：**抛异常**

强制调用方必须开启事务。

### NEVER

- 有事务：**抛异常**
- 无事务：非事务执行

不允许在事务中执行。

### NESTED

```java
@Transactional(propagation = Propagation.NESTED)
public void methodB() {
    // 嵌套事务 —— 使用 Savepoint
    // 回滚到 Savepoint，不影响外部事务
}
```

- 有事务：创建保存点（Savepoint），嵌套事务回滚只回滚到保存点
- 无事务：行为同 REQUIRED（创建新事务）

**NESTED vs REQUIRES_NEW**：

| 维度 | NESTED | REQUIRES_NEW |
|------|--------|-------------|
| 外部事务回滚 | 嵌套事务也被回滚 | 新事务不受影响 |
| 嵌套回滚 | 只回滚到 Savepoint | 完全独立回滚 |
| 实现 | Savepoint（JDBC） | 新数据库连接 |
| 适用场景 | 部分失败不影响整体 | 完全独立的子事务 |

```java
@Transactional  // 外部事务
public void checkout(Cart cart) {
    orderDao.createOrder(cart);  // 主订单

    try {
        // NESTED：积分扣减失败只回滚积分，不影响订单
        pointsService.deductPoints(cart);
    } catch (Exception e) {
        log.warn("积分扣减失败", e);
    }

    // 如果下面抛异常，订单和积分都回滚
    inventoryDao.decrease(cart.getItems());
}
```

### 传播行为总结表

| 传播行为 | 当前有事务 | 当前无事务 |
|---------|-----------|-----------|
| REQUIRED（默认） | 加入 | 新建 |
| REQUIRES_NEW | 挂起当前，新建 | 新建 |
| SUPPORTS | 加入 | 非事务执行 |
| NOT_SUPPORTED | 挂起当前，非事务执行 | 非事务执行 |
| MANDATORY | 加入 | 抛异常 |
| NEVER | 抛异常 | 非事务执行 |
| NESTED | Savepoint | 新建（同 REQUIRED） |

## 事务隔离级别

隔离级别解决并发事务的三大问题：

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 说明 |
|---------|------|-----------|------|------|
| READ_UNCOMMITTED | √ | √ | √ | 最低级别，不推荐 |
| READ_COMMITTED | × | √ | √ | 大多数数据库默认（Oracle、PG、SQL Server） |
| REPEATABLE_READ | × | × | √（部分） | MySQL InnoDB 默认 |
| SERIALIZABLE | × | × | × | 串行执行，性能最差 |

Spring 中的配置：

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public void transfer() { }

// Isolation.DEFAULT：跟随数据库默认（推荐，大多数场景够用）
@Transactional(isolation = Isolation.DEFAULT)
public void query() { }
```

数据库默认隔离级别通常就是最佳选择，一般不需要手动覆盖。

## 事务回滚规则

### 默认回滚规则

Spring 的默认回滚规则：**RuntimeException 及其子类回滚，受检异常（checked exception）不回滚**。

```java
@Transactional
public void createOrder() throws IOException {
    orderDao.insert(order);
    throw new RuntimeException();  // 回滚
}

@Transactional
public void createOrder() throws IOException {
    orderDao.insert(order);
    throw new IOException();       // 不回滚！数据提交了
}
```

### 自定义回滚规则

```java
// 指定哪些异常回滚
@Transactional(rollbackFor = Exception.class)       // 所有异常（包括 checked）都回滚
@Transactional(rollbackFor = {SQLException.class, IOException.class})

// 指定哪些异常不回滚
@Transactional(noRollbackFor = IllegalArgumentException.class)

// 组合
@Transactional(
    rollbackFor = Exception.class,
    noRollbackFor = {IllegalArgumentException.class, ValidationException.class}
)
```

### 最佳实践

```java
// 推荐：Service 层方法都设置为 rollbackFor = Exception.class
// 防止 checked exception 意外不回滚
@Transactional(rollbackFor = Exception.class)
public void businessMethod() {
    // 任何异常都回滚
}
```

`rollbackFor = Exception.class` 是最安全的做法，除非有特殊需求（如某些 checked exception 不应回滚事务）。

### @Transactional 的回滚标记

事务只有抛出未被捕获的异常时才会自动回滚。以下情况不会回滚：

```java
@Transactional
public void doSomething() {
    try {
        dangerousOperation();  // 抛异常
    } catch (Exception e) {
        log.error("出错了", e);
        // 异常被吞没 —— 事务正常提交！
    }
}
```

如果要在 catch 后仍回滚：

```java
@Transactional
public void doSomething() {
    try {
        dangerousOperation();
    } catch (Exception e) {
        log.error("出错了", e);
        TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
        // 或者直接 throw e;
    }
}
```

## 事务失效场景（8 种）

### 1. 非 public 方法

```java
@Service
public class UserService {
    @Transactional
    private void updateUser() {  // private —— 事务不生效
        // Spring AOP 通过代理实现，JDK/CGLIB 代理无法代理 private 方法
    }

    @Transactional
    protected void deleteUser() {  // protected —— 也不生效（CGLIB 可以，但 JDK 不行）
    }
}
```

**原因**：Spring AOP 基于代理，JDK 代理只能代理接口中的 public 方法，CGLIB 能代理 protected 但 `@Transactional` 默认要求 public（可通过 `@EnableTransactionManagement` 配置修改，但不推荐）。

### 2. 自调用（类内部调用）

```java
@Service
public class UserService {

    public void createUser() {
        this.updateUser();  // 事务不生效！
    }

    @Transactional
    public void updateUser() {
        // this.updateUser() 直接调用目标方法，绕过了代理
    }
}
```

**原因**：代理模式下，外部调用 `proxy.createUser()` 会走代理，但 `createUser()` 内部的 `this.updateUser()` 走的是原始对象，非代理对象。

**解法**：拆分类、注入自己（`@Lazy @Autowired private UserService self`）、或使用 `AopContext.currentProxy()`。

### 3. 异常被吞没

```java
@Transactional
public void doSomething() {
    try {
        jdbcTemplate.execute("INSERT INTO ...");  // 成功
        throw new RuntimeException("模拟失败");    // 异常被 catch
    } catch (Exception e) {
        // 吞没异常 —— 事务正常提交，第一条 INSERT 入库了
    }
}
```

**解法**：catch 后重新抛出异常，或标记 `setRollbackOnly()`。

### 4. 异常类型不匹配

```java
@Transactional
public void doSomething() throws SQLException {
    jdbcTemplate.execute("INSERT INTO ...");
    throw new SQLException("数据异常");  // Checked Exception —— 默认不回滚
}
```

**解法**：添加 `@Transactional(rollbackFor = Exception.class)`。

### 5. 数据库引擎不支持事务

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    ...
) ENGINE=MyISAM;  -- MyISAM 不支持事务！
```

MySQL 的 MyISAM 引擎不支持事务。必须使用 InnoDB。

### 6. 多线程环境

```java
@Transactional
public void createOrder() {
    new Thread(() -> {
        userDao.update(user);  // 不在当前事务中！
    }).start();
}
```

Spring 事务通过 ThreadLocal 绑定到当前线程。新开的线程获取不到当前事务。

### 7. Spring 事务管理器未配置

```java
// 没有配置事务管理器时 @Transactional 不生效
// Spring Boot 会自动配置，纯 Spring 需要手动配置：
@Bean
public PlatformTransactionManager transactionManager(DataSource dataSource) {
    return new DataSourceTransactionManager(dataSource);
}
```

### 8. @Transactional 所在的类没有被 Spring 管理

```java
// 自己 new 的对象
UserService service = new UserService();
service.createUser();  // 不是 Spring Bean，没有代理，事务不生效

// @Transactional 只有通过 Spring 容器获取的代理对象才生效
UserService service = context.getBean(UserService.class);
```

### 失效场景排查口诀

```text
非公自调吞异常，匹配引擎多线程，缺管漏注容器外。
```

## 应用场景实战

### 场景 1：转账——事务一致性

```java
@Service
public class TransferService {

    @Autowired
    private AccountDao accountDao;

    @Autowired
    private TransferLogDao transferLogDao;

    @Transactional(rollbackFor = Exception.class)
    public void transfer(String fromAccount, String toAccount, BigDecimal amount) {
        // 扣款
        Account from = accountDao.findByAccount(fromAccount);
        if (from.getBalance().compareTo(amount) < 0) {
            throw new BusinessException("余额不足");
        }
        accountDao.decreaseBalance(fromAccount, amount);

        // 加款
        accountDao.increaseBalance(toAccount, amount);

        // 记录日志
        TransferLog log = new TransferLog(fromAccount, toAccount, amount);
        transferLogDao.insert(log);
    }
    // 任何一步失败，全部回滚
}
```

### 场景 2：订单创建 + 库存扣减 + 积分（不同传播行为）

```java
@Service
public class OrderService {

    @Autowired
    private OrderDao orderDao;
    @Autowired
    private InventoryService inventoryService;
    @Autowired
    private PointsService pointsService;
    @Autowired
    private LogService logService;

    @Transactional(rollbackFor = Exception.class)  // 主事务
    public void createOrder(OrderDTO dto) {
        // 1. 创建订单（主事务）
        Order order = dto.toOrder();
        orderDao.insert(order);

        // 2. 扣减库存（REQUIRED —— 加入主事务，失败则订单也回滚）
        inventoryService.decrease(dto.getItems());

        // 3. 扣减积分（NESTED —— 失败只回滚积分，不影响订单）
        try {
            pointsService.deduct(dto.getUserId(), dto.getPoints());
        } catch (Exception e) {
            log.warn("积分扣减失败，订单继续", e);
        }

        // 4. 记录操作日志（REQUIRES_NEW —— 日志独立提交，即使主事务回滚日志也在）
        try {
            logService.record("CREATE_ORDER", order.getId());
        } catch (Exception e) {
            // 日志失败不阻塞业务流程
        }
    }
}
```

### 场景 3：编程式事务——部分回滚

```java
@Service
public class BatchImportService {

    @Autowired
    private TransactionTemplate transactionTemplate;

    public ImportResult importData(List<Record> records) {
        ImportResult result = new ImportResult();
        int successCount = 0;
        int failCount = 0;

        for (Record record : records) {
            try {
                // 每条记录独立事务 —— 一条失败不影响其他
                transactionTemplate.execute(status -> {
                    validate(record);
                    processRecord(record);
                    return null;
                });
                successCount++;

            } catch (Exception e) {
                failCount++;
                result.addError(record.getId(), e.getMessage());
            }
        }

        result.setSuccessCount(successCount);
        result.setFailCount(failCount);
        return result;
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **@Transactional 用在 Service 层，不要用在 Controller 或 DAO 层**。Service 层是业务逻辑的边界，事务范围应与此一致。

2. **指定 rollbackFor = Exception.class**，避免 checked exception 意外提交。

3. **只读事务加 readOnly = true**：

```java
@Transactional(readOnly = true)
public List<User> findUsers(UserQuery query) {
    return userDao.findByQuery(query);
}
```

MySQL 的只读事务可以利用只读视图，JDBC 驱动可以做一些优化（如不记录 undo log）。

4. **事务方法尽量短小**。长事务会长时间占用数据库连接和锁，导致性能问题。耗时操作（文件 I/O、网络调用、大量计算）放在事务外。

5. **避免在事务中执行 RPC 调用**。外部服务超时/失败会导致事务长时间挂起。如果必须 RPC，使用异步或放在事务完成后。

6. **事务嵌套保持简洁**。传播行为用 REQUIRED（默认）即可覆盖 90% 场景。过度使用 REQUIRES_NEW 和 NESTED 会让事务行为变得难以追踪。

### 踩坑记录

**坑 1：@Transactional 的默认超时**

```java
@Transactional(timeout = 30)  // 秒
```

默认值是 -1（无限等待）。对于可能长时间执行的方法，设置合理超时防止死锁。

**坑 2：readOnly = true 不能保证只读**

```java
@Transactional(readOnly = true)
public void updateUser(Long id) {
    userDao.update(id);  // MySQL InnoDB 的 readOnly 提示会被忽略，数据仍然被修改了
}
```

`readOnly = true` 只是一个"提示"，不同数据库/驱动的行为不同。MySQL 的 InnoDB 在只读事务中可以写入数据。**不要在 readOnly 事务中执行写操作，这是一种坏实践**。

**坑 3：@Transactional + @Async 的事务传播**

```java
@Transactional
public void sendNotifications() {
    notificationService.sendEmail();  // 同步
    notificationService.sendSms();    // @Async —— 异步执行，不在同一个事务中
}
```

`@Async` 方法运行在独立线程中，ThreadLocal 的事务上下文不会传递。异步操作的事务是独立的。

**坑 4：@Transactional 和 synchronized 一起用的问题**

```java
@Transactional
public synchronized void deduct() {  // 危险的组合
    // synchronized 在事务外释放，之后事务才提交
    // 其他线程可能看到未提交的数据（取决于隔离级别）
}
```

`synchronized` 和事务的组合会导致"锁在事务提交前释放"的问题。使用数据库锁（SELECT ... FOR UPDATE）或分布式锁来解决。

**坑 5：嵌套调用 REQUIRES_NEW 的死锁**

```java
// ServiceA
@Transactional  // 事务 T1
public void methodA(Long id) {
    User user = userDao.selectForUpdate(id);  // 获取行锁
    serviceB.methodB(id);  // 调用另一个事务方法
}

// ServiceB
@Transactional(propagation = Propagation.REQUIRES_NEW)  // 事务 T2
public void methodB(Long id) {
    userDao.updateById(id);  // 等待 T1 释放锁 → T1 又在等 T2 完成 → 死锁
}
```

REQUIRES_NEW 挂起外部事务 T1，创建新事务 T2。但 T1 持有的数据库锁不会释放，T2 如果访问同一行数据就会死锁。
