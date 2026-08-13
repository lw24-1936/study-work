---
title: Redis 应用
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [redis, 缓存, session, 分布式锁, 限流, 排行榜, 延迟队列, 消息队列, 布隆过滤器]
---

# Redis 应用

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [缓存](#缓存)
- [Session 共享](#session-共享)
- [分布式锁](#分布式锁)
- [限流](#限流)
- [排行榜](#排行榜)
- [延迟队列](#延迟队列)
- [消息队列](#消息队列)
- [布隆过滤器](#布隆过滤器)
- [应用场景总结](#应用场景总结)

## 概述

Redis 的八大经典应用场景，覆盖了绝大多数后端开发需求。

```text
八大应用场景：
1. 缓存          —— 热点数据缓存
2. Session 共享  —— 分布式会话
3. 分布式锁      —— 并发控制
4. 限流          —— 流量控制
5. 排行榜        —— 排序（ZSet）
6. 延迟队列      —— 定时任务（ZSet 时间戳）
7. 消息队列      —— 异步解耦（List/Stream）
8. 布隆过滤器    —— 防穿透（Bitmap）
```

```text
与其他篇章的关系：
- 缓存 → 详见 105-分布式缓存（Cache Aside 等模式）
- 分布式锁 → 详见 100-分布式锁（Redis/Redisson/ZK/数据库）
- 限流 → 详见 103-高并发（四种限流算法）
本篇聚焦 Redis 视角的实战实现
```

## 缓存

缓存是 Redis 最核心的应用，将热点数据缓存在内存，减轻数据库压力。

### 基本缓存

```java
@Service
public class UserCacheService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    public User getUser(Long id) {
        String key = "user:" + id;
        // 1. 查缓存
        String json = redisTemplate.opsForValue().get(key);
        if (json != null) {
            return JSON.parseObject(json, User.class);
        }
        // 2. 查数据库
        User user = userMapper.findById(id);
        // 3. 写缓存
        if (user != null) {
            redisTemplate.opsForValue().set(key, JSON.toJSONString(user),
                30, TimeUnit.MINUTES);
        }
        return user;
    }
}
```

### 缓存三大问题（详见 105-分布式缓存）

```text
1. 缓存穿透 —— 查不存在的 key（布隆过滤器/缓存空值）
2. 缓存击穿 —— 热点 key 过期（互斥锁/永不过期）
3. 缓存雪崩 —— 大量 key 同时过期（随机过期时间）
```

## Session 共享

分布式环境下，Session 存储在 Redis，实现多实例会话共享。

### 为什么需要 Session 共享

```text
单机：Session 存服务器内存，用户请求到同一台机器
分布式：用户请求可能到不同实例，Session 不共享导致登录失效

解决：Session 存 Redis，所有实例共享
```

### Spring Session 实现

```xml
<dependency>
    <groupId>org.springframework.session</groupId>
    <artifactId>spring-session-data-redis</artifactId>
</dependency>
```

```yaml
spring:
  session:
    store-type: redis          # Session 存 Redis
    timeout: 1800              # Session 过期（30 分钟）
```

```java
// 配置后无需改代码，Session 自动存 Redis
@RestController
public class LoginController {

    @PostMapping("/login")
    public String login(@RequestParam String username, HttpSession session) {
        session.setAttribute("user", username);   // 自动存 Redis
        return "登录成功";
    }

    @GetMapping("/profile")
    public String profile(HttpSession session) {
        return (String) session.getAttribute("user");  // 从 Redis 读取
    }
}
```

### 手动实现 Session 共享

```java
// 不用 Spring Session，手动用 Redis 存会话
@Service
public class TokenService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    public String createSession(Long userId) {
        String token = UUID.randomUUID().toString();
        redisTemplate.opsForValue().set("session:" + token,
            String.valueOf(userId), 30, TimeUnit.MINUTES);
        return token;
    }

    public Long getUserId(String token) {
        String userId = redisTemplate.opsForValue().get("session:" + token);
        return userId != null ? Long.valueOf(userId) : null;
    }
}
```

## 分布式锁

分布式锁控制并发访问（详见 100-分布式锁）。

### Redisson 实现

```java
@Autowired
private RedissonClient redissonClient;

public void doBusiness(String key) {
    RLock lock = redissonClient.getLock("lock:" + key);
    try {
        if (lock.tryLock(3, 30, TimeUnit.SECONDS)) {
            processBusiness();
        }
    } finally {
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }
}
```

### 手写 Redis 锁

```java
// 加锁（SET NX PX）
public boolean tryLock(String key, String value, long expireSeconds) {
    return Boolean.TRUE.equals(redisTemplate.opsForValue()
        .setIfAbsent(key, value, expireSeconds, TimeUnit.SECONDS));
}

// 解锁（Lua 原子）
public boolean unlock(String key, String value) {
    String script = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                    "return redis.call('del', KEYS[1]) else return 0 end";
    Long result = redisTemplate.execute(
        new DefaultRedisScript<>(script, Long.class),
        Collections.singletonList(key), value);
    return Long.valueOf(1).equals(result);
}
```

## 限流

限流控制请求速率（详见 103-高并发）。

### 固定窗口限流

```java
// 用 INCR + EXPIRE 实现简单限流
public boolean tryAcquire(String key, int limit, long windowSeconds) {
    Long count = redisTemplate.opsForValue().increment(key);
    if (count == 1) {
        redisTemplate.expire(key, windowSeconds, TimeUnit.SECONDS);
    }
    return count <= limit;
}
```

### 滑动窗口限流（ZSet）

```java
// 用 ZSet 实现滑动窗口限流
public boolean tryAcquire(String key, int limit, long windowSeconds) {
    long now = System.currentTimeMillis();
    long windowStart = now - windowSeconds * 1000;

    // 删除窗口外的记录
    redisTemplate.opsForZSet().removeRangeByScore(key, 0, windowStart);

    // 统计窗口内请求数
    Long count = redisTemplate.opsForZSet().zCard(key);
    if (count >= limit) {
        return false;
    }

    // 记录当前请求
    redisTemplate.opsForZSet().add(key, UUID.randomUUID().toString(), now);
    redisTemplate.expire(key, windowSeconds, TimeUnit.SECONDS);
    return true;
}
```

### 令牌桶限流（Lua）

```java
// Lua 令牌桶限流（原子）
String script =
    "local rate = tonumber(ARGV[1]) " +          // 生成速率
    "local capacity = tonumber(ARGV[2]) " +      // 桶容量
    "local now = tonumber(ARGV[3]) " +           // 当前时间
    "local tokens = tonumber(redis.call('get', KEYS[1]) or capacity) " +
    "local last = tonumber(redis.call('get', KEYS[2]) or now) " +
    "local elapsed = (now - last) / 1000 " +
    "tokens = math.min(capacity, tokens + elapsed * rate) " +
    "redis.call('set', KEYS[2], now) " +
    "if tokens < 1 then return 0 end " +
    "redis.call('set', KEYS[1], tokens - 1) " +
    "return 1";

Long result = redisTemplate.execute(
    new DefaultRedisScript<>(script, Long.class),
    Arrays.asList("tokens", "lastTime"),
    "10", "100", String.valueOf(System.currentTimeMillis()));
```

## 排行榜

排行榜是 Redis ZSet 的经典应用，用分数排序。

### 实现排行榜

```java
@Service
public class RankService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    private static final String RANK_KEY = "rank:score";

    // 更新分数
    public void updateScore(Long userId, double score) {
        redisTemplate.opsForZSet().add(RANK_KEY, String.valueOf(userId), score);
    }

    // 增加分数
    public void addScore(Long userId, double delta) {
        redisTemplate.opsForZSet().incrementScore(RANK_KEY, String.valueOf(userId), delta);
    }

    // 获取用户排名（从大到小）
    public Long getRank(Long userId) {
        return redisTemplate.opsForZSet().reverseRank(RANK_KEY, String.valueOf(userId));
    }

    // 获取排行榜前 10
    public List<String> getTop10() {
        Set<String> top10 = redisTemplate.opsForZSet()
            .reverseRange(RANK_KEY, 0, 9);   // 从大到小前 10
        return new ArrayList<>(top10);
    }

    // 获取用户分数
    public Double getScore(Long userId) {
        return redisTemplate.opsForZSet().score(RANK_KEY, String.valueOf(userId));
    }
}
```

### 排行榜的高级用法

```text
1. 实时排行榜 —— ZINCRBY 实时更新分数
2. 分页榜单 —— ZREVRANGE 带 offset
3. 周榜/月榜 —— 按时间分段 key（rank:2026:week1）
4. 并列排名 —— 分数相同按元素字典序
```

```java
// 分页查询排行榜
public List<String> getRankPage(int page, int size) {
    int start = (page - 1) * size;
    int end = start + size - 1;
    Set<String> range = redisTemplate.opsForZSet().reverseRange(RANK_KEY, start, end);
    return new ArrayList<>(range);
}
```

## 延迟队列

延迟队列用 ZSet 实现，分数为执行时间戳，定时取出到期任务。

### 延迟队列原理

```text
1. 添加任务：ZADD delay_queue 执行时间戳 任务内容
2. 取到期任务：ZRANGEBYSCORE delay_queue 0 当前时间
3. 执行后移除：ZREM delay_queue 任务内容
```

### 实现延迟队列

```java
@Component
public class DelayQueue {

    @Autowired
    private StringRedisTemplate redisTemplate;

    private static final String DELAY_KEY = "delay:queue";

    // 添加延迟任务
    public void addTask(String task, long delaySeconds) {
        long executeTime = System.currentTimeMillis() + delaySeconds * 1000;
        redisTemplate.opsForZSet().add(DELAY_KEY, task, executeTime);
    }

    // 获取并执行到期任务
    @Scheduled(fixedDelay = 1000)   // 每秒扫描
    public void processTasks() {
        long now = System.currentTimeMillis();
        // 获取所有到期任务
        Set<String> tasks = redisTemplate.opsForZSet()
            .rangeByScore(DELAY_KEY, 0, now);

        for (String task : tasks) {
            // 原子移除（防止重复执行）
            Long removed = redisTemplate.opsForZSet().remove(DELAY_KEY, task);
            if (removed != null && removed > 0) {
                // 执行任务
                executeTask(task);
            }
        }
    }

    private void executeTask(String task) {
        // 业务处理
        System.out.println("执行延迟任务：" + task);
    }
}
```

### 延迟队列的应用

```text
1. 订单超时取消 —— 下单 30 分钟未支付自动取消
2. 延迟通知 —— 定时提醒
3. 延迟重试 —— 失败后延迟重试
```

```text
延迟队列 vs 消息队列延迟消息：
Redis 延迟队列：自己实现，简单
RabbitMQ 延迟队列：TTL + 死信
RocketMQ 延迟消息：原生支持（1s~2h 18 个等级）
```

## 消息队列

Redis 可用 List 或 Stream 实现简单消息队列。

### List 实现（简单队列）

```java
// 生产者
public void produce(String message) {
    redisTemplate.opsForList().rightPush("queue:task", message);
}

// 消费者（阻塞读取）
public String consume() {
    return redisTemplate.opsForList().leftPop("queue:task", 10, TimeUnit.SECONDS);
}
```

```text
List 队列的局限：
1. 消息消费后即删除，不能重复消费
2. 无消费确认，消费者崩溃消息丢失
3. 无消费组
```

### Stream 实现（可靠队列）

```java
// 生产者：发送消息
public void produce(String message) {
    Map<String, Object> fields = new HashMap<>();
    fields.put("content", message);
    redisTemplate.opsForStream().add("stream:task", fields);
}

// 消费者：消费组读取
public void consume() {
    // 创建消费组（首次）
    // XGROUP CREATE stream:task group1 0

    // 读取消息
    List<MapRecord<String, Object, Object>> records = redisTemplate.opsForStream()
        .read(Consumer.from("group1", "consumer1"),
              StreamReadOptions.empty().count(10),
              StreamOffset.create("stream:task", ReadOffset.lastConsumed()));

    for (MapRecord<String, Object, Object> record : records) {
        // 处理消息
        processMessage(record.getValue());

        // 确认消息
        redisTemplate.opsForStream().acknowledge("stream:task", "group1", record.getId());
    }
}
```

```text
Stream vs List：
Stream：消息持久化、消费组、确认、可重复读
List：简单，消费即删

可靠消息队列用 Stream，简单场景用 List
```

## 布隆过滤器

布隆过滤器用于判断元素"可能存在"或"一定不存在"，防止缓存穿透。

### 布隆过滤器原理

```text
1. 一个 bit 数组 + 多个哈希函数
2. 添加元素：多个哈希函数计算位置，对应 bit 置 1
3. 查询元素：计算位置，全为 1 则"可能存在"，任一为 0 则"一定不存在"

特点：
- 一定不存在 → 100% 准确
- 可能存在 → 可能误判（假阳性）
- 空间效率极高
```

### 使用 Guava 布隆过滤器

```xml
<dependency>
    <groupId>com.google.guava</groupId>
    <artifactId>guava</artifactId>
</dependency>
```

```java
@Service
public class BloomFilterService {

    private final BloomFilter<Long> bloomFilter;

    public BloomFilterService() {
        // 预期 100 万元素，误判率 1%
        bloomFilter = BloomFilter.create(
            Funnels.longFunnel(), 1_000_000, 0.01);
    }

    // 初始化（把已有 ID 加入过滤器）
    public void init(List<Long> ids) {
        ids.forEach(bloomFilter::put);
    }

    // 查询前判断
    public boolean mightExist(Long id) {
        return bloomFilter.mightContain(id);
    }
}
```

```java
// 防止缓存穿透的完整流程
public User getUser(Long id) {
    // 1. 布隆过滤器判断（一定不存在直接返回）
    if (!bloomFilterService.mightExist(id)) {
        return null;   // 一定不存在，不查缓存和数据库
    }

    // 2. 查缓存
    User cached = cache.get("user:" + id);
    if (cached != null) return cached;

    // 3. 查数据库
    return userMapper.findById(id);
}
```

### 使用 Redis 布隆过滤器（Redisson）

```java
@Autowired
private RedissonClient redissonClient;

public boolean mightExist(String key, Long id) {
    RBloomFilter<Long> bloomFilter = redissonClient.getBloomFilter(key);
    bloomFilter.tryInit(1_000_000L, 0.01);   // 初始化（首次）
    return bloomFilter.contains(id);
}

public void add(String key, Long id) {
    RBloomFilter<Long> bloomFilter = redissonClient.getBloomFilter(key);
    bloomFilter.add(id);
}
```

## 应用场景总结

| 场景 | 数据结构 | 核心命令 | 关键点 |
|------|---------|---------|--------|
| 缓存 | String/Hash | GET/SET | 三大问题（穿透/击穿/雪崩） |
| Session 共享 | String | SETEX | Spring Session |
| 分布式锁 | String | SETNX/Lua | 过期、续期、误删 |
| 限流 | String/ZSet | INCR/ZRANGEBYSCORE | 算法选型 |
| 排行榜 | ZSet | ZADD/ZREVRANGE | 分数排序 |
| 延迟队列 | ZSet | ZADD/ZRANGEBYSCORE | 时间戳为分数 |
| 消息队列 | List/Stream | LPUSH/BRPOP/XADD | Stream 更可靠 |
| 布隆过滤器 | Bitmap | SETBIT/GETBIT | 防穿透 |
