---
title: Spring Boot 集成 Redisson 详解
created: 2026-08-09
updated: 2026-08-09
type: integration
tags: [spring-boot, redis, distributed, cache, lock]
---

> 整理日期：2026-08-09

## 目录

1. [Redisson 概述](#1-redisson-概述)
2. [核心特性](#2-核心特性)
3. [环境搭建](#3-环境搭建)
4. [配置详解](#4-配置详解)
5. [分布式对象](#5-分布式对象)
6. [分布式锁](#6-分布式锁)
7. [分布式集合](#7-分布式集合)
8. [发布订阅](#8-发布订阅)
9. [应用场景实战](#9-应用场景实战)
10. [最佳实践与踩坑记录](#10-最佳实践与踩坑记录)

---

## 1. Redisson 概述

### 1.1 什么是 Redisson

Redisson 是一个在 Redis 基础上实现的 **Java 驻内存数据网格（In-Memory Data Grid）**。它不仅是一个 Redis 客户端，更是一套分布式中间件——提供分布式锁、分布式集合、限流器、布隆过滤器等开箱即用的能力。

简单来说：**Redisson = Redis 客户端 + 分布式中间件**。

### 1.2 与 Jedis / Lettuce 的区别

| 特性 | Jedis | Lettuce | Redisson |
|------|-------|---------|----------|
| 定位 | 底层客户端 | 底层客户端 | 高级分布式框架 |
| 连接方式 | 同步/连接池 | 异步/响应式 | 异步/响应式/同步 |
| 分布式锁 | 需手动实现 | 需手动实现 | 开箱即用 |
| 分布式集合 | 无 | 无 | Map/Set/List/Queue 等 |
| 线程安全 | 非线程安全 | 线程安全 | 线程安全 |
| Spring 集成 | 需手动配置 | Spring Data Redis | spring-boot-starter |

### 1.3 为什么选择 Redisson

- 降低分布式开发门槛：分布式锁、布隆过滤器、限流器等无需自己实现
- 丰富的分布式数据结构：Map、Set、Queue、Topic 等，像用本地集合一样使用
- 完善的监控和诊断：提供连接池监控、集群拓扑可视化
- 响应式编程支持：完全支持 Reactive Streams

---

## 2. 核心特性

- 分布式锁（可重入、公平锁、联锁、红锁、读写锁）
- 分布式对象（AtomicLong、CountDownLatch、Semaphore）
- 分布式集合（Map、Set、List、Queue、Deque、SortedSet）
- 分布式发布订阅
- 分布式执行服务（ExecutorService、ScheduledExecutorService）
- 布隆过滤器（Bloom Filter）
- 限流器（RateLimiter）
- Redis 集群 / 哨兵 / 主从模式支持
- 本地缓存 + Redis 缓存（Near Cache）

---

## 3. 环境搭建

### 3.1 依赖引入

**Maven：**

```xml
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.34.0</version>
</dependency>
```

**Gradle：**

```groovy
implementation 'org.redisson:redisson-spring-boot-starter:3.34.0'
```

注意：`redisson-spring-boot-starter` 已包含 `spring-boot-starter-data-redis` 的依赖，无需重复引入。

### 3.2 application.yml 配置（推荐方式）

Redisson 3.x 的 `redisson-spring-boot-starter` 支持直接在 `application.yml` 中配置，无需额外写 `RedissonClient` Bean。这是最简单且推荐的方式。

**单机模式：**

```yaml
spring:
  redis:
    host: 127.0.0.1          # Redis 地址
    port: 6379               # Redis 端口
    password: your_password  # 密码（无密码则删除此行）
    database: 0              # 数据库索引，默认 0
    timeout: 3000ms          # 命令超时

    # 连接池配置（Lettuce 连接池）
    lettuce:
      pool:
        max-active: 16       # 最大活跃连接数
        max-idle: 8          # 最大空闲连接数
        min-idle: 4          # 最小空闲连接数
        max-wait: 2000ms     # 获取连接最大等待时间
```

**哨兵模式：**

```yaml
spring:
  redis:
    timeout: 3000ms
    sentinel:
      master: mymaster
      nodes:
        - 127.0.0.1:26379
        - 127.0.0.1:26380
        - 127.0.0.1:26381
      password: your_password
    lettuce:
      pool:
        max-active: 32
        max-idle: 16
        min-idle: 8
```

**集群模式：**

```yaml
spring:
  redis:
    timeout: 3000ms
    cluster:
      nodes:
        - 127.0.0.1:7000
        - 127.0.0.1:7001
        - 127.0.0.1:7002
        - 127.0.0.1:7003
        - 127.0.0.1:7004
        - 127.0.0.1:7005
      max-redirects: 3       # 最大重定向次数
    password: your_password
    lettuce:
      pool:
        max-active: 32
        max-idle: 16
        min-idle: 8
```

使用 `application.yml` 方式时，Spring Boot 自动配置会创建 `RedissonClient`，直接在业务代码中注入即可：

```java
@Autowired
private RedissonClient redissonClient;
```

**原理**：`RedissonAutoConfiguration` 会读取 `spring.redis.*` 配置，自动判断单机/哨兵/集群模式，创建对应的 `RedissonClient` Bean。

### 3.3 手动配置 RedissonClient Bean

当需要更精细的控制（如自定义序列化、指定看门狗超时时间等），可以手动创建 `RedissonClient` Bean。注意这种方式会覆盖 Spring Boot 自动配置，需要显式指定所有参数。

```java
import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RedissonConfig {

    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();

        // 单机模式
        config.useSingleServer()
                .setAddress("redis://127.0.0.1:6379")
                .setPassword("your_password")
                .setDatabase(0)
                .setConnectionPoolSize(16)
                .setConnectionMinimumIdleSize(4)
                .setIdleConnectionTimeout(10000)
                .setConnectTimeout(3000)
                .setTimeout(3000)
                .setRetryAttempts(3)
                .setRetryInterval(1500);

        return Redisson.create(config);
    }
}
```

**哨兵模式：**

```java
config.useSentinelServers()
    .setMasterName("mymaster")
    .addSentinelAddress("redis://127.0.0.1:26379", "redis://127.0.0.1:26380")
    .setPassword("your_password");
```

**集群模式：**

```java
config.useClusterServers()
    .addNodeAddress(
        "redis://127.0.0.1:7000",
        "redis://127.0.0.1:7001",
        "redis://127.0.0.1:7002"
    )
    .setPassword("your_password");
```

### 3.4 两种配置方式对比

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| application.yml | 零代码、自动识别模式、与 Spring 配置统一管理 | 无法精细控制连接参数 | 大多数标准场景 |
| 手动 Bean | 完全控制所有参数，可自定义序列化、看门狗 | 需维护 Java Config 类，切换环境改代码 | 特殊序列化需求、多 RedissonClient |

---

## 4. 配置详解

### 4.1 核心连接参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `connectionPoolSize` | 连接池大小 | 64 |
| `connectionMinimumIdleSize` | 最小空闲连接数 | 24 |
| `idleConnectionTimeout` | 空闲连接超时(ms) | 10000 |
| `connectTimeout` | 连接超时(ms) | 10000 |
| `timeout` | 命令超时(ms) | 3000 |
| `retryAttempts` | 失败重试次数 | 3 |
| `retryInterval` | 重试间隔(ms) | 1500 |
| `pingConnectionInterval` | 心跳检测间隔(ms) | 0(不启用) |
| `keepAlive` | 是否开启 TCP KeepAlive | false |

### 4.2 生产环境推荐配置（application.yml）

```yaml
spring:
  redis:
    host: ${REDIS_HOST:127.0.0.1}       # 环境变量优先
    port: ${REDIS_PORT:6379}
    password: ${REDIS_PASSWORD:}
    database: ${REDIS_DB:0}
    timeout: 5000ms                      # 适当放宽
    lettuce:
      pool:
        max-active: 32                   # 按 QPS 调整
        max-idle: 12
        min-idle: 8
        max-wait: 3000ms
        time-between-eviction-runs: 30s  # 空闲连接检测间隔
```

### 4.3 看门狗超时配置

看门狗的默认锁超时是 30 秒，检查间隔是 10 秒。如果需要调整（比如业务执行时间可能很长），在手动配置时修改：

```java
Config config = new Config();
config.setLockWatchdogTimeout(60000);  // 改为 60 秒
```

---

## 5. 分布式对象

### 5.1 通用 Object Bucket

```java
import org.redisson.api.RBucket;
import org.redisson.api.RedissonClient;
import java.util.concurrent.TimeUnit;

@Service
public class ObjectBucketService {

    @Autowired
    private RedissonClient redissonClient;

    // 存储任意对象，1 小时过期
    public void saveUser(String userId, User user) {
        RBucket<User> bucket = redissonClient.getBucket("user:" + userId);
        bucket.set(user, 1, TimeUnit.HOURS);
    }

    // 读取对象
    public User getUser(String userId) {
        RBucket<User> bucket = redissonClient.getBucket("user:" + userId);
        return bucket.get();
    }

    // 仅当不存在时设置（SETNX 语义）
    public boolean setIfAbsent(String key, Object value) {
        RBucket<Object> bucket = redissonClient.getBucket(key);
        return bucket.setIfAbsent(value);
    }
}
```

### 5.2 原子操作

```java
import org.redisson.api.RAtomicLong;

@Service
public class CounterService {

    @Autowired
    private RedissonClient redissonClient;

    // 分布式原子计数器 — 全局唯一自增 ID
    public long generateOrderId() {
        RAtomicLong counter = redissonClient.getAtomicLong("order:id:sequence");
        return counter.incrementAndGet();
    }

    // 带初始值
    public long decrementStock() {
        RAtomicLong counter = redissonClient.getAtomicLong("stock:product-101");
        counter.set(100);                  // 初始化库存
        return counter.decrementAndGet();  // 扣减库存
    }
}
```

### 5.3 信号量与门闩

```java
import org.redisson.api.RSemaphore;
import org.redisson.api.RCountDownLatch;

@Service
public class FlowControlService {

    @Autowired
    private RedissonClient redissonClient;

    // 信号量：并发限流，最多 5 个并发
    public boolean tryAcquireSlot() {
        RSemaphore semaphore = redissonClient.getSemaphore("task:semaphore");
        semaphore.trySetPermits(5);
        return semaphore.tryAcquire();
    }

    public void releaseSlot() {
        RSemaphore semaphore = redissonClient.getSemaphore("task:semaphore");
        semaphore.release();
    }

    // CountDownLatch：多服务启动协调
    public void waitForAllServices() throws InterruptedException {
        RCountDownLatch latch = redissonClient.getCountDownLatch("service:init:latch");
        latch.trySetCount(3);
        latch.await();
    }

    public void signalReady() {
        RCountDownLatch latch = redissonClient.getCountDownLatch("service:init:latch");
        latch.countDown();
    }
}
```

---

## 6. 分布式锁

### 6.1 可重入锁（最常用）

```java
import org.redisson.api.RLock;
import java.util.concurrent.TimeUnit;

@Service
public class DistributedLockService {

    @Autowired
    private RedissonClient redissonClient;

    /**
     * 可重入锁 — 防止同一业务并发执行。
     * 适用场景：订单支付、余额扣减等幂等操作。
     */
    public void processOrder(String orderId) {
        RLock lock = redissonClient.getLock("lock:order:" + orderId);

        try {
            // 尝试加锁：最多等待 10 秒，锁 30 秒后自动释放
            if (lock.tryLock(10, 30, TimeUnit.SECONDS)) {
                // ---- 业务逻辑 ----
                System.out.println("处理订单: " + orderId);
            } else {
                throw new RuntimeException("获取锁失败，订单正在处理中");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("获取锁被中断", e);
        } finally {
            // 必须在 finally 中释放，且检查是否当前线程持有
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
```

### 6.2 锁的种类

```java
// 1. 可重入锁 — 同一线程可多次获取
RLock lock = redissonClient.getLock("anyLock");

// 2. 公平锁 — 按请求顺序排队获取
RLock fairLock = redissonClient.getFairLock("anyFairLock");

// 3. 联锁（MultiLock）— 同时锁多个 Key，原子性获取
RLock lock1 = redissonClient.getLock("lock1");
RLock lock2 = redissonClient.getLock("lock2");
RLock multiLock = redissonClient.getMultiLock(lock1, lock2);
multiLock.lock();

// 4. 红锁（RedLock）— 多个独立 Redis 节点，解决主从切换丢锁问题
RLock lockA = redissonClientA.getLock("sharedResource");
RLock lockB = redissonClientB.getLock("sharedResource");
RLock lockC = redissonClientC.getLock("sharedResource");
RLock redLock = redissonClient.getRedLock(lockA, lockB, lockC);
redLock.lock();

// 5. 读写锁 — 读并发、写独占
RReadWriteLock rwLock = redissonClient.getReadWriteLock("readWriteLock");
RLock readLock = rwLock.readLock();    // 多线程可同时持有
RLock writeLock = rwLock.writeLock();  // 独占
```

### 6.3 看门狗机制（Watchdog）

Redisson 分布式锁的核心机制：如果未指定 `leaseTime`（即 `lock()` 不带参数），Redisson 会启动一个看门狗线程，**每 10 秒自动续期 30 秒**，直到客户端主动解锁。这解决了"业务执行时间不确定，锁可能提前过期"的问题。

```java
// 看门狗模式：锁默认 30 秒，自动续期，不怕业务超时
lock.lock();

// 手动租约：指定 30 秒后自动释放，不续期
lock.lock(30, TimeUnit.SECONDS);
```

**工作原理：**

```
看门狗定时器每 lockWatchdogTimeout/3 (默认 10 秒) 检查一次
  -> 如果锁仍被持有 -> 续期到 lockWatchdogTimeout (默认 30 秒)
  -> 客户端主动 unlock -> 取消看门狗
```

---

## 7. 分布式集合

### 7.1 Map（高频使用）

```java
import org.redisson.api.RMap;
import org.redisson.api.RMapCache;

@Service
public class DistributedMapService {

    @Autowired
    private RedissonClient redissonClient;

    // 普通 Map：无过期
    public void cacheSettings() {
        RMap<String, String> map = redissonClient.getMap("app:settings");
        map.put("maxUploadSize", "10MB");
        map.put("theme", "dark");
        map.fastPut("version", "1.0.0"); // 速度快，不返回旧值

        String theme = map.get("theme");
    }

    // 带 TTL 的 MapCache：每个 key 独立过期
    public void cacheSession() {
        RMapCache<String, UserSession> sessionCache =
                redissonClient.getMapCache("user:sessions");

        UserSession session = new UserSession("user123", "192.168.1.1");
        sessionCache.put("session:token-abc", session, 30, TimeUnit.MINUTES);

        // 过期策略：惰性删除（get 时检查）+ 定期删除（后台线程清除）
    }
}
```

### 7.2 List / Set / Queue

```java
// 分布式 List
RList<String> list = redissonClient.getList("message:queue");
list.add("msg-1");
list.add("msg-2");
List<String> batch = list.range(0, 10); // 分页读取

// 分布式 Set
RSet<String> onlineUsers = redissonClient.getSet("user:online");
onlineUsers.add("user-001");
onlineUsers.add("user-002");
boolean isOnline = onlineUsers.contains("user-001");

// 阻塞队列（生产者-消费者模式）
RBlockingQueue<String> queue = redissonClient.getBlockingQueue("task:queue");
queue.offer("process-image-123");                   // 生产者

String task = queue.poll(5, TimeUnit.SECONDS);      // 消费者，阻塞等待 5 秒
```

---

## 8. 发布订阅

```java
import org.redisson.api.RTopic;

@Service
public class PubSubService {

    @Autowired
    private RedissonClient redissonClient;

    // 发布消息
    public void notifyCacheEvict(String cacheKey) {
        RTopic topic = redissonClient.getTopic("cache:evict");
        topic.publish(cacheKey);
    }

    // 订阅消息
    @PostConstruct
    public void subscribe() {
        RTopic topic = redissonClient.getTopic("cache:evict");
        topic.addListener(String.class, (channel, msg) -> {
            System.out.println("收到缓存失效通知: " + msg);
            localCache.invalidate(msg);
        });
    }
}
```

---

## 9. 应用场景实战

### 场景 1：秒杀库存扣减

```java
@Service
public class FlashSaleService {

    @Autowired
    private RedissonClient redissonClient;

    /**
     * 秒杀下单：原子扣减 + 分布式锁。
     */
    public Result placeOrder(Long productId, Long userId) {
        String lockKey = "seckill:lock:" + productId;
        RLock lock = redissonClient.getLock(lockKey);

        try {
            if (!lock.tryLock(1, 5, TimeUnit.SECONDS)) {
                return Result.fail("抢购人数太多，请重试");
            }

            // 原子扣减库存
            RAtomicLong stock = redissonClient.getAtomicLong("seckill:stock:" + productId);
            long remaining = stock.decrementAndGet();

            if (remaining < 0) {
                stock.incrementAndGet(); // 回滚
                return Result.fail("已售罄");
            }

            // 创建订单...
            return Result.success("抢购成功");

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return Result.fail("系统异常");
        } finally {
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
```

### 场景 2：分布式全局唯一 ID 生成

```java
@Service
public class SnowflakeIdService {

    @Autowired
    private RedissonClient redissonClient;

    // Redisson 内置雪花算法 ID 生成器
    public long nextId() {
        return redissonClient.getIdGenerator("order:id:generator").nextId();
    }

    public List<Long> batchIds(int count) {
        RIdGenerator generator = redissonClient.getIdGenerator("order:id:generator");
        List<Long> ids = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            ids.add(generator.nextId());
        }
        return ids;
    }
}
```

### 场景 3：布隆过滤器 — 防止缓存穿透

```java
import org.redisson.api.RBloomFilter;

@Service
public class BloomFilterService {

    private RBloomFilter<String> bloomFilter;

    @PostConstruct
    public void init() {
        bloomFilter = redissonClient.getBloomFilter("product:bloom");
        // 预计插入 100 万条，误判率 0.03
        bloomFilter.tryInit(1_000_000L, 0.03);

        // 预热：将数据库已有 ID 加载到布隆过滤器
        List<Product> products = productMapper.selectAll();
        for (Product p : products) {
            bloomFilter.add(p.getId().toString());
        }
    }

    public Product getProduct(Long productId) {
        String key = productId.toString();

        // 1. 布隆过滤器判断：不存在则直接返回
        if (!bloomFilter.contains(key)) {
            return null; // 绝对不存在，拦截无效请求
        }

        // 2. 查缓存
        Product cached = cacheService.get(key);
        if (cached != null) return cached;

        // 3. 查数据库
        Product product = productMapper.selectById(productId);
        if (product != null) {
            cacheService.put(key, product);
        }
        return product;
    }
}
```

### 场景 4：分布式限流器

```java
import org.redisson.api.RRateLimiter;
import org.redisson.api.RateIntervalUnit;
import org.redisson.api.RateType;

@Service
public class RateLimiterService {

    @Autowired
    private RedissonClient redissonClient;

    /**
     * 接口限流：每秒最多 100 个请求。
     */
    public boolean isAllowed(String userId) {
        RRateLimiter limiter = redissonClient.getRateLimiter("api:rateLimit:" + userId);

        // 初始化：全局限流，每 1 秒产生 100 个令牌
        limiter.trySetRate(RateType.OVERALL, 100, 1, RateIntervalUnit.SECONDS);

        return limiter.tryAcquire();
    }

    /**
     * AOP 限流注解实现。
     */
    @Around("@annotation(rateLimit)")
    public Object rateLimit(ProceedingJoinPoint pjp, RateLimit rateLimit) throws Throwable {
        RRateLimiter limiter = redissonClient.getRateLimiter(rateLimit.key());
        limiter.trySetRate(RateType.OVERALL,
                rateLimit.permits(),
                rateLimit.period(),
                rateLimit.unit());

        if (!limiter.tryAcquire()) {
            throw new RuntimeException("请求过于频繁，请稍后重试");
        }
        return pjp.proceed();
    }
}
```

### 场景 5：延迟队列 — 订单超时取消

```java
import org.redisson.api.RDelayedQueue;
import org.redisson.api.RBlockingQueue;

@Service
public class OrderTimeoutService {

    @Autowired
    private RedissonClient redissonClient;

    /**
     * 订单创建时加入延迟队列，30 分钟后触发取消检查。
     */
    public void scheduleOrderCancel(Long orderId) {
        RBlockingQueue<Long> blockingQueue =
                redissonClient.getBlockingQueue("order:cancel:queue");

        RDelayedQueue<Long> delayedQueue =
                redissonClient.getDelayedQueue(blockingQueue);

        // 延迟 30 分钟投递
        delayedQueue.offer(orderId, 30, TimeUnit.MINUTES);
    }

    /**
     * 监听延迟队列，处理超时订单。
     */
    @PostConstruct
    public void startOrderCancelListener() {
        new Thread(() -> {
            RBlockingQueue<Long> queue =
                    redissonClient.getBlockingQueue("order:cancel:queue");

            while (true) {
                try {
                    Long orderId = queue.take(); // 阻塞等待
                    handleCancel(orderId);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "order-cancel-listener").start();
    }

    private void handleCancel(Long orderId) {
        Order order = orderMapper.selectById(orderId);
        if (order != null && OrderStatus.UNPAID.equals(order.getStatus())) {
            orderMapper.updateStatus(orderId, OrderStatus.CANCELLED);
            // 回滚库存...
        }
    }
}
```

### 场景 6：读写锁 — 配置热更新

```java
@Service
public class ConfigService {

    @Autowired
    private RedissonClient redissonClient;

    private Map<String, String> localCache = new ConcurrentHashMap<>();

    /**
     * 读取配置：多线程并发读，不阻塞。
     */
    public String getConfig(String key) {
        RReadWriteLock rwLock = redissonClient.getReadWriteLock("config:rwlock");
        RLock readLock = rwLock.readLock();

        readLock.lock();
        try {
            return localCache.getOrDefault(key, loadFromRedis(key));
        } finally {
            readLock.unlock();
        }
    }

    /**
     * 更新配置：写锁独占，阻塞所有读写。
     */
    public void updateConfig(String key, String value) {
        RReadWriteLock rwLock = redissonClient.getReadWriteLock("config:rwlock");
        RLock writeLock = rwLock.writeLock();

        writeLock.lock();
        try {
            redissonClient.getBucket("config:" + key).set(value);
            localCache.put(key, value);
            redissonClient.getTopic("config:change").publish(key);
        } finally {
            writeLock.unlock();
        }
    }
}
```

---

## 10. 最佳实践与踩坑记录

### 10.1 锁的正确释放

```java
// 错误写法：直接 unlock，可能释放别人的锁
lock.unlock();

// 正确写法：检查持有者后再释放
if (lock.isHeldByCurrentThread()) {
    lock.unlock();
}

// 推荐：tryLock + finally 模式
if (lock.tryLock(5, 30, TimeUnit.SECONDS)) {
    try {
        // 业务逻辑
    } finally {
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }
}
```

### 10.2 Watchdog 与 leaseTime 的选择

```java
// 风险：业务执行超过 30 秒，锁自动释放，其他线程介入
lock.lock(30, TimeUnit.SECONDS);

// 推荐：不指定 leaseTime，启用看门狗自动续期
lock.lock();

// 适合：明确知道业务很快完成（如缓存更新）
lock.lock(5, TimeUnit.SECONDS);
```

### 10.3 避免死锁

```java
// 危险：嵌套锁容易死锁
lock1.lock();
lock2.lock(); // 如果另一个线程持有 lock2 等待 lock1 -> 死锁

// 应该用联锁，原子性同时获取
RLock multiLock = redissonClient.getMultiLock(lock1, lock2);
multiLock.lock();
```

### 10.4 连接池调优建议

```yaml
# 生产环境推荐配置
spring:
  redis:
    lettuce:
      pool:
        max-active: 32           # 根据 QPS 调整
        max-idle: 12
        min-idle: 8              # 保持热连接
        max-wait: 3000ms
    timeout: 5000ms
```

手动配置方式的关键参数：

```
connectionPoolSize: 32           # 根据 QPS 调整
connectionMinimumIdleSize: 8     # 保持热连接
retryAttempts: 3                 # 3 次重试足够
retryInterval: 1000              # 1 秒间隔
pingConnectionInterval: 30000    # 30 秒心跳防断连
```

### 10.5 常见问题速查

| 问题 | 原因 | 解决 |
|------|------|------|
| `unlock` 报错 `IllegalMonitorStateException` | 锁已过期或释放了不属于自己的锁 | 加 `isHeldByCurrentThread()` 判断后再 unlock |
| Watchdog 不生效 | 指定了 `leaseTime` 参数 | `lock()` 不带参数 |
| 集群模式下锁丢失 | 主节点宕机，从节点未同步 | 使用红锁（RedLock） |
| OOM | 大量 RMap 未清理 | 使用 `RMapCache` 设置 TTL |
| 序列化异常 | 对象未实现 `Serializable` | 换用 JSON 序列化（见下一节） |
| 应用启动报 Redisson 连接失败 | 未排除 Lettuce 依赖冲突 | 检查依赖树，排除多余的 Lettuce |

### 10.6 替换序列化方式

Redisson 默认使用 JDK 序列化，生产环境建议替换为 JSON：

```java
@Configuration
public class RedissonCodecConfig {

    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer()
                .setAddress("redis://127.0.0.1:6379");

        // 使用 JSON 序列化，便于调试和跨语言
        config.setCodec(new org.redisson.codec.JsonJacksonCodec());

        return Redisson.create(config);
    }
}
```

### 10.7 版本兼容注意事项

- Redisson 3.27.0+ 支持 Spring Boot 3.x（JDK 17+）
- Redisson 3.16.x 支持 Spring Boot 2.x（JDK 8+）
- 如果同时引入了 `spring-boot-starter-data-redis` 和 `redisson-spring-boot-starter`，检查依赖树确保没有 Lettuce 版本冲突

---

## 总结

Redisson 是目前 Java 生态中最强大的 Redis 高级客户端，它将 Redis 从"缓存工具"提升为"分布式中间件平台"。核心记住三点：

1. **锁**：`tryLock(waitTime, leaseTime, unit)` + `isHeldByCurrentThread()` + `finally unlock()`
2. **看门狗**：不指定 `leaseTime` 时自动续期，防止业务超时锁释放
3. **序列化**：生产环境建议使用 `JsonJacksonCodec`，便于排查和跨语言

---

## 参考链接

- [Redisson 官方文档](https://github.com/redisson/redisson/wiki)
- [Redisson Spring Boot Starter](https://github.com/redisson/redisson/tree/master/redisson-spring-boot-starter)
- [Redisson 配置参数参考](https://github.com/redisson/redisson/wiki/2.-Configuration)
