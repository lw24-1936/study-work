---
title: Spring Data Redis
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-data-redis, redistemplate, stringredistemplate, serialization, pub-sub, stream, lock, redis]
---

# Spring Data Redis

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [依赖与连接配置](#依赖与连接配置)
- [RedisTemplate 与 StringRedisTemplate](#redistemplate-与-stringredistemplate)
- [序列化机制](#序列化机制)
- [五种数据类型操作](#五种数据类型操作)
- [Redis Pub/Sub 发布订阅](#redis-pubsub-发布订阅)
- [Redis Stream 消息流](#redis-stream-消息流)
- [Redis 分布式锁](#redis-分布式锁)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Data Redis 是 Spring 对 Redis 的集成，提供了统一的操作抽象，屏蔽了底层客户端（Lettuce/Jedis）的差异。

```text
Spring Data Redis 核心组件：
RedisConnectionFactory  —— 连接工厂（管理 Redis 连接）
RedisTemplate           —— 高层操作模板（支持对象序列化）
StringRedisTemplate     —— 字符串专用模板（key/value 都是 String）
RedisConnection         —— 底层连接（直接执行 Redis 命令）
```

```text
架构层次：
应用 → RedisTemplate → RedisConnectionFactory → Lettuce/Jedis → Redis 服务器
```

## 依赖与连接配置

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

默认使用 Lettuce 客户端（Spring Boot 2.x+ 默认）。

### 连接配置

```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      password: ${REDIS_PASSWORD}
      database: 0
      timeout: 3000ms
      lettuce:
        pool:
          max-active: 8          # 最大连接数
          max-idle: 8            # 最大空闲连接
          min-idle: 0
          max-wait: -1ms         # 获取连接最大等待时间
```

### 连接工厂

```java
@Bean
public RedisConnectionFactory redisConnectionFactory() {
    RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
    config.setHostName("localhost");
    config.setPort(6379);
    config.setPassword("secret");
    config.setDatabase(0);

    LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
        .commandTimeout(Duration.ofSeconds(2))
        .build();

    return new LettuceConnectionFactory(config, clientConfig);
}
```

## RedisTemplate 与 StringRedisTemplate

### RedisTemplate

```java
@Autowired
private RedisTemplate<String, Object> redisTemplate;

// 字符串操作
redisTemplate.opsForValue().set("key", "value");
Object value = redisTemplate.opsForValue().get("key");

// Hash 操作
redisTemplate.opsForHash().put("user:1", "name", "张三");
Object name = redisTemplate.opsForHash().get("user:1", "name");

// List 操作
redisTemplate.opsForList().leftPush("list", "a");
redisTemplate.opsForList().rightPop("list");

// Set 操作
redisTemplate.opsForSet().add("set", "a", "b");

// ZSet 操作
redisTemplate.opsForZSet().add("zset", "member", 1.0);

// 通用操作
redisTemplate.expire("key", 60, TimeUnit.SECONDS);  // 设置过期
redisTemplate.delete("key");
redisTemplate.hasKey("key");
redisTemplate.getExpire("key");  // 剩余过期时间
```

### StringRedisTemplate

```java
@Autowired
private StringRedisTemplate stringRedisTemplate;

// key 和 value 都是 String，无需序列化配置
stringRedisTemplate.opsForValue().set("counter", "100");
String value = stringRedisTemplate.opsForValue().get("counter");

// 递增（计数器场景）
Long count = stringRedisTemplate.opsForValue().increment("counter");  // 101
```

### 两者区别

| 维度 | RedisTemplate | StringRedisTemplate |
|------|--------------|---------------------|
| 泛型 | RedisTemplate<K, V>（可自定义类型） | RedisTemplate<String, String> |
| 序列化 | 默认 JDK 序列化（需自定义） | String 序列化（开箱即用） |
| 适用场景 | 存储对象、复杂类型 | 存储字符串、计数器 |
| 配置 | 需配置序列化器 | 无需配置 |

**经验**：能用 StringRedisTemplate 就用它（简单、无序列化坑）。要存对象时，自定义 RedisTemplate 的序列化器为 JSON。

## 序列化机制

序列化是 Redis 使用中最容易踩坑的地方。RedisTemplate 默认使用 JDK 序列化，会导致存储内容不可读。

### 默认序列化的问题

```java
@Autowired
private RedisTemplate<String, Object> redisTemplate;

redisTemplate.opsForValue().set("user:1", new User("张三"));
// 默认 JDK 序列化，存储的是二进制，redis-cli 里看到的是乱码
// \xac\xed\x00\x05sr\x00...
```

### 自定义 JSON 序列化

```java
@Configuration
public class RedisConfig {

    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory factory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);

        // JSON 序列化器
        Jackson2JsonRedisSerializer<Object> serializer =
            new Jackson2JsonRedisSerializer<>(Object.class);
        ObjectMapper mapper = new ObjectMapper();
        mapper.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
        mapper.activateDefaultTyping(
            mapper.getPolymorphicTypeValidator(),
            ObjectMapper.DefaultTyping.NON_FINAL
        );
        serializer.setObjectMapper(mapper);

        // Key 用 String，Value 用 JSON
        StringRedisSerializer stringSerializer = new StringRedisSerializer();
        template.setKeySerializer(stringSerializer);
        template.setHashKeySerializer(stringSerializer);
        template.setValueSerializer(serializer);
        template.setHashValueSerializer(serializer);

        template.afterPropertiesSet();
        return template;
    }
}
```

### 常见序列化器

| 序列化器 | 存储格式 | 说明 |
|---------|---------|------|
| JdkSerializationRedisSerializer | 二进制 | 默认，对象需实现 Serializable |
| StringRedisSerializer | 字符串 | key/value 都是可读字符串 |
| Jackson2JsonRedisSerializer | JSON | 可读性好，类型安全 |
| GenericJackson2JsonRedisSerializer | JSON | 带类型信息，反序列化更可靠 |
| GenericToStringSerializer | 字符串 | 调用 toString |

```text
推荐组合：
Key   → StringRedisSerializer（可读，方便排查）
Value → GenericJackson2JsonRedisSerializer（JSON 可读 + 类型信息）
```

### 序列化器的坑

```text
坑 1：用 RedisTemplate 存，用 redis-cli 取，看到乱码
原因：JDK 序列化是二进制格式

坑 2：改了序列化器，旧数据读不出来
原因：旧数据是 JDK 序列化，新序列化器是 JSON，格式不兼容

坑 3：反序列化 ClassCastException
原因：Jackson2JsonRedisSerializer 丢失类型信息，反序列化成 LinkedHashMap
```

## 五种数据类型操作

Redis 五种数据类型在 Spring Data Redis 中的操作。

### 1. String（字符串）

```java
ValueOperations<String, Object> ops = redisTemplate.opsForValue();

ops.set("name", "张三");
ops.set("key", "value", 60, TimeUnit.SECONDS);  // 带过期时间
ops.setIfAbsent("lock", "1");                    // setnx（分布式锁基础）
ops.get("name");
ops.increment("counter");                        // 自增
ops.decrement("counter");                        // 自减
```

### 2. Hash（哈希）

```java
HashOperations<String, Object, Object> ops = redisTemplate.opsForHash();

ops.put("user:1", "name", "张三");
ops.put("user:1", "age", "25");
ops.get("user:1", "name");
Map<Object, Object> entries = ops.entries("user:1");  // 整个 hash
ops.hasKey("user:1", "name");
ops.delete("user:1", "age");
```

### 3. List（列表）

```java
ListOperations<String, Object> ops = redisTemplate.opsForList();

ops.leftPush("queue", "task1");      // 左进（队列头）
ops.rightPush("queue", "task2");     // 右进（队列尾）
ops.leftPop("queue");                // 左出
ops.rightPop("queue");               // 右出
ops.range("queue", 0, -1);           // 获取所有
ops.size("queue");                   // 长度
```

### 4. Set（集合）

```java
SetOperations<String, Object> ops = redisTemplate.opsForSet();

ops.add("tags", "java", "spring", "redis");
ops.members("tags");                 // 所有成员
ops.isMember("tags", "java");        // 是否成员
ops.size("tags");                    // 大小
ops.difference("set1", "set2");      // 差集
ops.intersect("set1", "set2");       // 交集
ops.union("set1", "set2");           // 并集
```

### 5. ZSet（有序集合）

```java
ZSetOperations<String, Object> ops = redisTemplate.opsForZSet();

ops.add("leaderboard", "player1", 100);   // 加入，分数 100
ops.add("leaderboard", "player2", 200);
ops.incrementScore("leaderboard", "player1", 10);  // 加分
ops.score("leaderboard", "player1");      // 查分数
ops.rank("leaderboard", "player1");       // 排名（从 0 开始）
ops.reverseRange("leaderboard", 0, 9);    // 排行榜前 10
ops.rangeByScore("leaderboard", 100, 200); // 按分数范围
```

## Redis Pub/Sub 发布订阅

Redis 的发布订阅机制，用于消息广播。

### 消息监听器

```java
@Component
public class RedisMessageListener implements MessageListener {

    @Override
    public void onMessage(Message message, byte[] pattern) {
        String channel = new String(message.getChannel());
        String body = new String(message.getBody());
        System.out.println("收到消息，频道：" + channel + "，内容：" + body);
    }
}
```

### 配置监听

```java
@Configuration
public class PubSubConfig {

    @Bean
    public RedisMessageListenerContainer container(
            RedisConnectionFactory factory, RedisMessageListener listener) {
        RedisMessageListenerContainer container = new RedisMessageListenerContainer();
        container.setConnectionFactory(factory);
        container.addMessageListener(listener, new ChannelTopic("order:created"));
        return container;
    }
}
```

### 发布消息

```java
@Autowired
private StringRedisTemplate stringRedisTemplate;

public void publish(String channel, String message) {
    stringRedisTemplate.convertAndSend(channel, message);
}

// 使用
publish("order:created", "订单 123 已创建");
```

### 应用场景

```text
1. 事件广播：订单创建后通知多个系统
2. 缓存失效通知：数据变更后广播清理缓存
3. 实时通知：用户上线通知
```

**注意**：Pub/Sub 是"即发即失"的，没有消息持久化。订阅者离线时错过消息。需要可靠消息用 Stream 或消息队列（Kafka/RabbitMQ）。

## Redis Stream 消息流

Redis Stream（5.0+）是 Pub/Sub 的升级版，支持消息持久化和消费组。

### 发送消息

```java
@Autowired
private StringRedisTemplate stringRedisTemplate;

public void sendMessage(String streamKey, Map<String, String> message) {
    MapRecord<String, String, String> record = StreamRecords.newRecord()
        .in(streamKey)
        .ofMap(message);
    stringRedisTemplate.opsForStream().add(record);
}
```

### 消费消息

```java
// 读取最新消息
List<MapRecord<String, Object, Object>> messages =
    stringRedisTemplate.opsForStream().read(
        StreamOffset.fromStart("mystream"));

// 消费组
stringRedisTemplate.opsForStream().createGroup("mystream", "group1");
List<MapRecord<String, Object, Object>> records =
    stringRedisTemplate.opsForStream().read(
        Consumer.from("group1", "consumer1"),
        StreamOffset.create("mystream", ReadOffset.lastConsumed()));

// 确认消息
stringRedisTemplate.opsForStream().acknowledge("mystream", "group1", recordId);
```

### Stream vs Pub/Sub

| 维度 | Pub/Sub | Stream |
|------|---------|--------|
| 消息持久化 | 否（即发即失） | 是 |
| 消费组 | 无 | 支持（多个消费者分组消费） |
| 消息确认 | 无 | 支持 ack |
| 历史消息 | 不能回溯 | 可以（offset 回溯） |
| 适用场景 | 实时广播 | 可靠消息、异步任务 |

## Redis 分布式锁

Redis 是分布式锁的经典实现（SET NX PX）。

### 手动实现

```java
@Component
public class RedisLock {

    @Autowired
    private StringRedisTemplate redisTemplate;

    // 加锁
    public boolean tryLock(String key, String value, long expireSeconds) {
        Boolean success = redisTemplate.opsForValue()
            .setIfAbsent(key, value, expireSeconds, TimeUnit.SECONDS);
        return Boolean.TRUE.equals(success);
    }

    // 解锁（用 Lua 脚本保证原子性）
    public void unlock(String key, String value) {
        String script = "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                        "return redis.call('del', KEYS[1]) " +
                        "else return 0 end";
        redisTemplate.execute(
            new DefaultRedisScript<>(script, Long.class),
            Collections.singletonList(key),
            value);
    }
}
```

```java
// 使用
String lockKey = "lock:order:" + orderId;
String lockValue = UUID.randomUUID().toString();

try {
    if (redisLock.tryLock(lockKey, lockValue, 30)) {
        // 执行业务逻辑
        processOrder(orderId);
    } else {
        throw new BusinessException("操作频繁，请稍后重试");
    }
} finally {
    redisLock.unlock(lockKey, lockValue);  // 必须释放
}
```

### 分布式锁的关键点

```text
1. SET NX PX —— 原子加锁 + 设置过期时间（防止死锁）
2. value 用唯一标识（UUID）—— 防止误删别人的锁
3. 解锁用 Lua 脚本 —— 保证"判断 + 删除"原子性
4. 锁要加过期时间 —— 防止持锁线程崩溃导致死锁
5. 更复杂的场景（可重入、自动续期）用 Redisson
```

### 用 Redisson 简化

```java
@Autowired
private RedissonClient redissonClient;

public void doSomething(String key) {
    RLock lock = redissonClient.getLock(key);
    try {
        if (lock.tryLock(3, 30, TimeUnit.SECONDS)) {  // 等 3 秒，持锁 30 秒
            // 业务逻辑
        }
    } finally {
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }
}
```

Redisson 提供看门狗（自动续期）、可重入锁、读写锁等高级能力，生产环境推荐用它而不是手写。

## 应用场景实战

### 场景 1：缓存 + 过期时间

```java
@Service
public class UserCacheService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    private static final String PREFIX = "user:";

    public User getUser(Long id) {
        String key = PREFIX + id;
        String json = redisTemplate.opsForValue().get(key);

        if (json != null) {
            return JSON.parseObject(json, User.class);  // 缓存命中
        }

        // 缓存未命中，查数据库
        User user = userMapper.findById(id);
        if (user != null) {
            redisTemplate.opsForValue().set(key, JSON.toJSONString(user), 30, TimeUnit.MINUTES);
        }
        return user;
    }

    public void updateUser(User user) {
        userMapper.update(user);
        // 更新后删除缓存（Cache Aside 模式）
        redisTemplate.delete(PREFIX + user.getId());
    }
}
```

### 场景 2：排行榜（ZSet）

```java
@Service
public class LeaderboardService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    private static final String KEY = "game:leaderboard";

    // 记录分数
    public void recordScore(String playerId, double score) {
        redisTemplate.opsForZSet().add(KEY, playerId, score);
    }

    // 获取前 10 名
    public List<String> top10() {
        Set<String> top = redisTemplate.opsForZSet().reverseRange(KEY, 0, 9);
        return new ArrayList<>(top);
    }

    // 获取玩家排名
    public Long getRank(String playerId) {
        Long rank = redisTemplate.opsForZSet().reverseRank(KEY, playerId);
        return rank == null ? null : rank + 1;  // 从 1 开始
    }
}
```

### 场景 3：计数器（防刷）

```java
@Service
public class RateLimitService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    // 简单计数器限流：每分钟最多 60 次
    public boolean isAllowed(String userId) {
        String key = "rate:" + userId + ":" + LocalDate.now();
        Long count = redisTemplate.opsForValue().increment(key);

        if (count == 1) {
            redisTemplate.expire(key, 60, TimeUnit.SECONDS);  // 首次设置过期
        }
        return count <= 60;
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Key 命名规范**。用冒号分层：`业务:模块:ID`，如 `user:profile:123`、`order:detail:456`。

2. **Value 序列化用 JSON**。避免默认 JDK 序列化，可读性差且占用空间大。

3. **所有 Key 都要设置过期时间**。防止内存被无过期 Key 占满。除非是明确需要永久保留的数据。

4. **分布式锁用 Redisson**。手写锁容易踩坑（误删、死锁、不可重入），Redisson 封装好了。

5. **大 Key 要拆分**。单个 Key 过大（如存几十 MB 的 JSON）影响性能，拆成多个小 Key 或 Hash 结构。

### 踩坑记录

**坑 1：RedisTemplate 存对象读出来是乱码**

```java
// 默认 JDK 序列化，redis-cli 看到 \xac\xed 乱码
redisTemplate.opsForValue().set("user", new User("张三"));
```

解法：自定义序列化器为 JSON，或直接用 StringRedisTemplate。

**坑 2：setIfAbsent 返回 null 导致 NPE**

```java
Boolean success = redisTemplate.opsForValue().setIfAbsent("key", "value");
if (success) { ... }  // success 可能为 null，拆箱 NPE
```

Lettuce 客户端某些情况下返回 null。用 `Boolean.TRUE.equals(success)` 判断。

**坑 3：缓存和数据库不一致**

```java
// 先删缓存再更新数据库，中间有请求读到旧数据写回缓存
// 或先更新数据库再删缓存，删除失败导致不一致
```

用 Cache Aside 模式（先更新 DB，再删缓存）+ 删除失败重试，或用延迟双删。

**坑 4：Redis 连接超时**

```text
命令在 Redis 阻塞（如 KEYS *、大 Key 操作）导致连接超时
```

生产禁用 `KEYS *`，用 `SCAN` 替代。大 Key 拆分或异步处理。

**坑 5：分布式锁过期时间太短**

```java
// 锁 10 秒过期，但业务执行了 30 秒
// 锁提前释放，其他线程拿到锁，并发执行
```

锁过期时间要大于业务执行时间，或用 Redisson 看门狗自动续期。

**坑 6：Pub/Sub 消息丢失**

```java
// 订阅者离线时发布的消息会丢失（Pub/Sub 无持久化）
```

需要可靠消息用 Redis Stream 或消息队列（Kafka/RabbitMQ）。
