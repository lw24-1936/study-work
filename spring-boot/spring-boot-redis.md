---
title: Spring Boot 集成 Redis 详解
created: 2026-08-09
updated: 2026-08-09
type: integration
tags: [spring-boot, redis, cache]
---

> 整理日期：2026-08-09

## 目录

1. [概述](#1-概述)
2. [Redis 客户端选型](#2-redis-客户端选型)
3. [环境搭建](#3-环境搭建)
4. [配置详解](#4-配置详解)
5. [RedisTemplate 核心操作](#5-redistemplate-核心操作)
6. [Spring Cache 缓存抽象](#6-spring-cache-缓存抽象)
7. [发布订阅](#7-发布订阅)
8. [Pipeline 批量操作](#8-pipeline-批量操作)
9. [应用场景实战](#9-应用场景实战)
10. [最佳实践与踩坑记录](#10-最佳实践与踩坑记录)

---

## 1. 概述

Spring Boot 通过 **Spring Data Redis** 提供对 Redis 的统一抽象，底层可以切换不同的 Redis 客户端（Jedis / Lettuce）。核心操作类是 `RedisTemplate` 和 `StringRedisTemplate`，同时 Spring Cache 抽象层提供了声明式缓存注解（`@Cacheable`、`@CachePut`、`@CacheEvict`）。

**与 Redisson 的关系**：Spring Data Redis 负责基础的数据读写，Redisson 在此基础上提供分布式锁、分布式集合等高级能力。两者可以共存——用 `RedisTemplate` 做缓存读写，用 `RedissonClient` 做分布式锁。详见 [[spring-boot-redisson]]。

---

## 2. Redis 客户端选型

Spring Boot 默认使用 **Lettuce** 作为 Redis 客户端，也支持切换到 Jedis。

| 特性 | Jedis | Lettuce |
|------|-------|---------|
| 连接模型 | 同步 BIO，需连接池 | 异步 NIO（Netty），单连接多路复用 |
| 线程安全 | 非线程安全，池化管理 | 原生线程安全 |
| Spring Boot 默认 | 否 | 是（2.x 起） |
| 集群支持 | 支持 | 支持 |
| 响应式编程 | 不支持 | 支持（Reactive） |
| 性能 | 连接池开销 | 更高，连接复用 |
| 适用场景 | 简单同步场景 | 高并发、响应式场景 |

**结论**：没有特殊原因直接用 Lettuce（Spring Boot 默认），无需切换。

---

## 3. 环境搭建

### 3.1 依赖引入

**Maven：**

```xml
<!-- Spring Data Redis（默认 Lettuce） -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>

<!-- 连接池依赖（Lettuce 需要 commons-pool2） -->
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-pool2</artifactId>
</dependency>
```

**Gradle：**

```groovy
implementation 'org.springframework.boot:spring-boot-starter-data-redis'
implementation 'org.apache.commons:commons-pool2'
```

**切换为 Jedis（可选）：**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
    <!-- 排除 Lettuce -->
    <exclusions>
        <exclusion>
            <groupId>io.lettuce</groupId>
            <artifactId>lettuce-core</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
</dependency>
```

### 3.2 application.yml 配置

```yaml
spring:
  redis:
    host: ${REDIS_HOST:127.0.0.1}     # 环境变量优先
    port: ${REDIS_PORT:6379}
    password: ${REDIS_PASSWORD:}       # 无密码则留空
    database: 0                        # 数据库索引，默认 0
    timeout: 3000ms                    # 连接超时

    lettuce:
      pool:
        max-active: 16                 # 最大活跃连接
        max-idle: 8                    # 最大空闲连接
        min-idle: 4                    # 最小空闲连接
        max-wait: 2000ms               # 获取连接最大等待时间
```

**哨兵模式：**

```yaml
spring:
  redis:
    timeout: 3000ms
    sentinel:
      master: mymaster
      nodes: 127.0.0.1:26379,127.0.0.1:26380,127.0.0.1:26381
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
      max-redirects: 3
    password: your_password
    lettuce:
      pool:
        max-active: 32
        max-idle: 16
        min-idle: 8
```

### 3.3 验证连接

```java
@SpringBootTest
class RedisConnectionTest {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    @Test
    void testConnection() {
        stringRedisTemplate.opsForValue().set("test:ping", "pong");
        String result = stringRedisTemplate.opsForValue().get("test:ping");
        assertEquals("pong", result);
    }
}
```

---

## 4. 配置详解

### 4.1 RedisTemplate 序列化配置

`RedisTemplate` 默认使用 JDK 序列化，存入 Redis 的是二进制字节，不可读且占用空间大。需要替换为 JSON 序列化：

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

@Configuration
public class RedisConfig {

    @Bean
    public RedisTemplate<String, Object> redisTemplate(
            RedisConnectionFactory connectionFactory) {

        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);

        // Key 用 String 序列化
        template.setKeySerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());

        // Value 用 JSON 序列化
        GenericJackson2JsonRedisSerializer jsonSerializer =
                new GenericJackson2JsonRedisSerializer();
        template.setValueSerializer(jsonSerializer);
        template.setHashValueSerializer(jsonSerializer);

        template.afterPropertiesSet();
        return template;
    }
}
```

序列化后存入 Redis 的效果：

```
# JDK 序列化（不可读）
\xac\xed\x00\x05t\x00\x05user1

# JSON 序列化（可读）
{"id":1,"name":"张三","age":25}
```

### 4.2 连接池参数调优

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `max-active` | 最大活跃连接 | 按业务 QPS 设置，一般 16-64 |
| `max-idle` | 最大空闲连接 | max-active * 0.5 |
| `min-idle` | 最小空闲连接 | max-active * 0.25，保持热连接 |
| `max-wait` | 获取连接最大等待 | 2000-5000ms，太长影响响应 |
| `timeout` | 命令超时 | 3000-5000ms |
| `time-between-eviction-runs` | 空闲连接检测间隔 | 30s |

**连接数计算公式：**

```
连接数 ≈ QPS / 单连接QPS + buffer
单连接QPS ≈ 10000（Lettuce 单连接效能很高）
示例：QPS 1000 → 1 个连接就够，但建议 min-idle 设为 4 保底
```

### 4.3 多数据源配置

当需要连接多个 Redis 实例时：

```java
@Configuration
public class MultiRedisConfig {

    // ----- 主 Redis -----
    @Primary
    @Bean("primaryRedisTemplate")
    public RedisTemplate<String, Object> primaryRedisTemplate(
            @Qualifier("primaryConnectionFactory") RedisConnectionFactory factory) {
        return createTemplate(factory);
    }

    @Primary
    @Bean("primaryConnectionFactory")
    public RedisConnectionFactory primaryConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("redis-primary");
        config.setPort(6379);
        return new LettuceConnectionFactory(config);
    }

    // ----- 从 Redis -----
    @Bean("secondaryRedisTemplate")
    public RedisTemplate<String, Object> secondaryRedisTemplate(
            @Qualifier("secondaryConnectionFactory") RedisConnectionFactory factory) {
        return createTemplate(factory);
    }

    @Bean("secondaryConnectionFactory")
    public RedisConnectionFactory secondaryConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("redis-secondary");
        config.setPort(6380);
        return new LettuceConnectionFactory(config);
    }
}
```

使用时按名称注入：

```java
@Autowired
@Qualifier("primaryRedisTemplate")
private RedisTemplate<String, Object> primaryTemplate;

@Autowired
@Qualifier("secondaryRedisTemplate")
private RedisTemplate<String, Object> secondaryTemplate;
```

---

## 5. RedisTemplate 核心操作

### 5.1 String 类型

```java
@Service
public class StringOpsService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate; // 专门处理 String

    // 基础读写
    public void basicOps() {
        ValueOperations<String, String> ops = stringRedisTemplate.opsForValue();

        ops.set("key1", "value1");
        ops.set("key2", "value2", 30, TimeUnit.SECONDS); // 30 秒过期

        String val = ops.get("key1");

        // 仅当 key 不存在时设置（SETNX）
        Boolean success = ops.setIfAbsent("lock:order:123", "1", 10, TimeUnit.SECONDS);

        // 自增
        ops.increment("counter:visits", 1);
    }
}
```

### 5.2 Hash 类型

```java
@Service
public class HashOpsService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    // 存储用户信息
    public void saveUser(Long userId, String name, Integer age) {
        String key = "user:" + userId;
        redisTemplate.opsForHash().put(key, "name", name);
        redisTemplate.opsForHash().put(key, "age", age);
    }

    // 读取单个字段
    public String getUserName(Long userId) {
        return (String) redisTemplate.opsForHash()
                .get("user:" + userId, "name");
    }

    // 批量存储对象
    public void saveUserObject(Long userId, User user) {
        String key = "user:" + userId;
        Map<String, Object> map = new HashMap<>();
        map.put("name", user.getName());
        map.put("age", user.getAge());
        map.put("email", user.getEmail());
        redisTemplate.opsForHash().putAll(key, map);
    }

    // 递增 Hash 字段
    public void incrementLoginCount(Long userId) {
        redisTemplate.opsForHash()
                .increment("user:" + userId, "loginCount", 1);
    }
}
```

### 5.3 List 类型

```java
@Service
public class ListOpsService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    // 消息队列（简单实现）
    public void pushMessage(String msg) {
        // 左侧入队
        stringRedisTemplate.opsForList().leftPush("queue:messages", msg);
    }

    public String popMessage() {
        // 右侧出队（阻塞版本用 rightPop(K, timeout, unit)）
        return stringRedisTemplate.opsForList().rightPop("queue:messages");
    }

    // 最新 N 条记录（如最近消息）
    public List<String> getRecentMessages(int count) {
        return stringRedisTemplate.opsForList()
                .range("chat:room:1", 0, count - 1);
    }

    // 修剪列表长度（保留最新 N 条）
    public void trimMessages(int maxSize) {
        stringRedisTemplate.opsForList()
                .trim("chat:room:1", 0, maxSize - 1);
    }
}
```

### 5.4 Set 类型

```java
@Service
public class SetOpsService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    // 在线用户管理
    public void userOnline(String userId) {
        stringRedisTemplate.opsForSet().add("users:online", userId);
    }

    public void userOffline(String userId) {
        stringRedisTemplate.opsForSet().remove("users:online", userId);
    }

    public boolean isOnline(String userId) {
        return Boolean.TRUE.equals(
                stringRedisTemplate.opsForSet().isMember("users:online", userId));
    }

    public long onlineCount() {
        return stringRedisTemplate.opsForSet().size("users:online");
    }

    // 共同好友（交集）
    public Set<String> commonFriends(String userA, String userB) {
        return stringRedisTemplate.opsForSet()
                .intersect("friends:" + userA, "friends:" + userB);
    }

    // 推荐好友（差集：A 有 B 没有）
    public Set<String> recommendFriends(String userA, String userB) {
        return stringRedisTemplate.opsForSet()
                .difference("friends:" + userA, "friends:" + userB);
    }
}
```

### 5.5 ZSet 类型（有序集合）

```java
@Service
public class ZSetOpsService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    // 排行榜：添加分数
    public void addScore(String userId, double score) {
        stringRedisTemplate.opsForZSet().add("ranking:daily", userId, score);
    }

    // 排行榜：Top N
    public Set<ZSetOperations.TypedTuple<String>> getTopN(int n) {
        return stringRedisTemplate.opsForZSet()
                .reverseRangeWithScores("ranking:daily", 0, n - 1);
    }

    // 排行榜：查询用户排名（从高到低）
    public Long getUserRank(String userId) {
        return stringRedisTemplate.opsForZSet()
                .reverseRank("ranking:daily", userId);
    }

    // 排行榜：查询用户分数
    public Double getUserScore(String userId) {
        return stringRedisTemplate.opsForZSet()
                .score("ranking:daily", userId);
    }
}
```

### 5.6 通用操作（过期、删除、判断存在）

```java
@Service
public class CommonOpsService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    // 设置过期
    public void setExpire(String key, long timeout, TimeUnit unit) {
        stringRedisTemplate.expire(key, timeout, unit);
    }

    // 获取剩余 TTL
    public long getTTL(String key) {
        return stringRedisTemplate.getExpire(key, TimeUnit.SECONDS);
    }

    // 删除 key
    public boolean delete(String key) {
        return Boolean.TRUE.equals(stringRedisTemplate.delete(key));
    }

    // 判断 key 是否存在
    public boolean exists(String key) {
        return Boolean.TRUE.equals(stringRedisTemplate.hasKey(key));
    }

    // 模糊匹配 key（慎用，生产环境用 scan 代替）
    public Set<String> keys(String pattern) {
        return stringRedisTemplate.keys(pattern);
    }
}
```

---

## 6. Spring Cache 缓存抽象

Spring Cache 提供声明式缓存，通过注解控制缓存行为，无需手动写 `RedisTemplate` 代码。

### 6.1 启用缓存

```java
@SpringBootApplication
@EnableCaching  // 启用缓存
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 6.2 配置缓存管理器

```java
@Configuration
public class CacheConfig {

    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
                // JSON 序列化
                .serializeValuesWith(
                    RedisSerializationContext.SerializationPair
                        .fromSerializer(new GenericJackson2JsonRedisSerializer()))
                // 默认过期时间 30 分钟
                .entryTtl(Duration.ofMinutes(30))
                // 缓存空值，防止缓存穿透
                .disableCachingNullValues()
                // Key 前缀
                .prefixCacheNameWith("cache:");

        return RedisCacheManager.builder(factory)
                .cacheDefaults(config)
                // 针对不同缓存名设置不同过期时间
                .withCacheConfiguration("userCache",
                    RedisCacheConfiguration.defaultCacheConfig()
                        .entryTtl(Duration.ofHours(1)))
                .withCacheConfiguration("productCache",
                    RedisCacheConfiguration.defaultCacheConfig()
                        .entryTtl(Duration.ofMinutes(10)))
                .build();
    }
}
```

### 6.3 核心注解

```java
@Service
public class UserCacheService {

    // ========== @Cacheable：查缓存，没有则执行方法并缓存 ==========

    /**
     * 缓存 key = "userCache::1"
     * 第一次调用查数据库并缓存，后续直接从 Redis 取
     */
    @Cacheable(value = "userCache", key = "#userId")
    public User getUserById(Long userId) {
        return userMapper.selectById(userId);
    }

    /**
     * 条件缓存：只有 id > 10 才缓存
     */
    @Cacheable(value = "userCache", key = "#userId", condition = "#userId > 10")
    public User getUserIfImportant(Long userId) {
        return userMapper.selectById(userId);
    }

    /**
     * 排除条件：结果为空不缓存
     */
    @Cacheable(value = "userCache", key = "#userId", unless = "#result == null")
    public User getUserNotNull(Long userId) {
        return userMapper.selectById(userId);
    }

    // ========== @CachePut：更新缓存，始终执行方法 ==========

    /**
     * 更新用户后，同步更新缓存
     */
    @CachePut(value = "userCache", key = "#user.id")
    public User updateUser(User user) {
        userMapper.updateById(user);
        return user; // 返回值会更新到缓存
    }

    // ========== @CacheEvict：清除缓存 ==========

    /**
     * 删除用户时清除对应缓存
     */
    @CacheEvict(value = "userCache", key = "#userId")
    public void deleteUser(Long userId) {
        userMapper.deleteById(userId);
    }

    /**
     * 清除整个 userCache 下的所有缓存
     */
    @CacheEvict(value = "userCache", allEntries = true)
    public void clearAllUserCache() {
        // 一般在批量更新后调用
    }

    // ========== @Caching：组合多个缓存操作 ==========

    @Caching(
        cacheable = {
            @Cacheable(value = "userCache", key = "#id")
        },
        put = {
            @CachePut(value = "userCache", key = "#result.username")
        }
    )
    public User getUserByIdAndCacheByUsername(Long id) {
        return userMapper.selectById(id);
    }
}
```

### 6.4 SpEL 表达式参考

| 表达式 | 说明 |
|--------|------|
| `#参数名` | 引用方法参数 |
| `#result` | 引用方法返回值（unless 中可用） |
| `#root.method` | 当前方法 |
| `#root.target` | 目标对象 |
| `#root.caches` | 受影响的缓存集合 |
| `#root.args[0]` | 第一个参数 |

---

## 7. 发布订阅

```java
@Service
public class RedisPubSubService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    // ===== 发布消息 =====
    public void publish(String channel, String message) {
        stringRedisTemplate.convertAndSend(channel, message);
    }

    // ===== 订阅消息 =====
    @Bean
    public MessageListenerAdapter cacheEvictListener() {
        return new MessageListenerAdapter(new Object() {
            @SuppressWarnings("unused")
            public void handleMessage(String message, String channel) {
                System.out.printf("频道: %s, 消息: %s%n", channel, message);
                // 处理缓存失效逻辑...
            }
        });
    }

    @Bean
    public RedisMessageListenerContainer listenerContainer(
            RedisConnectionFactory factory,
            MessageListenerAdapter listener) {

        RedisMessageListenerContainer container =
                new RedisMessageListenerContainer();
        container.setConnectionFactory(factory);
        container.addMessageListener(
                listener,
                new PatternTopic("cache:evict:*"));
        return container;
    }
}
```

---

## 8. Pipeline 批量操作

Pipeline 将多个命令打包发送，减少网络往返次数，适合批量操作场景。

```java
@Service
public class PipelineService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 批量写入 10000 条数据。
     * Pipeline 模式下不要用 stringRedisTemplate.opsForXxx()，
     * 它会为每个操作获取连接，无法享受 Pipeline 优化。
     */
    public void batchInsert() {
        stringRedisTemplate.executePipelined((RedisCallback<Object>) connection -> {
            StringRedisConnection stringConn = (StringRedisConnection) connection;
            for (int i = 0; i < 10000; i++) {
                stringConn.set("batch:key:" + i, "value:" + i);
            }
            return null;
        });
    }

    /**
     * 批量查询。
     */
    public List<Object> batchGet(List<String> keys) {
        return stringRedisTemplate.executePipelined((RedisCallback<Object>) connection -> {
            StringRedisConnection stringConn = (StringRedisConnection) connection;
            for (String key : keys) {
                stringConn.get(key);
            }
            return null;
        });
    }

    /**
     * 批量设置过期。
     */
    public void batchExpire(List<String> keys, long timeout, TimeUnit unit) {
        long seconds = unit.toSeconds(timeout);
        stringRedisTemplate.executePipelined((RedisCallback<Object>) connection -> {
            for (String key : keys) {
                connection.expire(key.getBytes(), seconds);
            }
            return null;
        });
    }
}
```

**性能对比：**

| 方式 | 10000 次写入耗时 |
|------|-----------------|
| 逐条写入 | 3-5 秒 |
| Pipeline 批量 | 0.1-0.3 秒 |

---

## 9. 应用场景实战

### 场景 1：短信验证码

```java
@Service
public class SmsCodeService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    private static final String PREFIX = "sms:code:";
    private static final int CODE_LENGTH = 6;
    private static final int EXPIRE_MINUTES = 5;
    private static final int SEND_LIMIT_MINUTES = 1;

    /**
     * 发送验证码。
     */
    public String sendCode(String phone) {
        // 1. 检查发送频率（1 分钟内只能发一次）
        String limitKey = PREFIX + "limit:" + phone;
        if (Boolean.TRUE.equals(
                stringRedisTemplate.hasKey(limitKey))) {
            throw new RuntimeException("发送过于频繁，请稍后再试");
        }

        // 2. 生成并存储验证码
        String code = String.format("%0" + CODE_LENGTH + "d",
                new Random().nextInt((int) Math.pow(10, CODE_LENGTH)));
        String codeKey = PREFIX + phone;

        stringRedisTemplate.opsForValue()
                .set(codeKey, code, EXPIRE_MINUTES, TimeUnit.MINUTES);
        stringRedisTemplate.opsForValue()
                .set(limitKey, "1", SEND_LIMIT_MINUTES, TimeUnit.MINUTES);

        // 3. 调用短信渠道发送...
        return code;
    }

    /**
     * 校验验证码。
     */
    public boolean verifyCode(String phone, String inputCode) {
        String codeKey = PREFIX + phone;
        String storedCode = stringRedisTemplate.opsForValue().get(codeKey);

        if (storedCode == null) {
            throw new RuntimeException("验证码已过期");
        }

        if (!storedCode.equals(inputCode)) {
            return false;
        }

        // 校验通过，删除验证码（一次性使用）
        stringRedisTemplate.delete(codeKey);
        return true;
    }
}
```

### 场景 2：分布式 Session 共享

```java
// application.yml
// spring:
//   session:
//     store-type: redis
//     timeout: 1800  # 30 分钟

// 依赖：
// <dependency>
//     <groupId>org.springframework.session</groupId>
//     <artifactId>spring-session-data-redis</artifactId>
// </dependency>
```

仅需依赖 + 一行配置，Spring Session 自动将 Session 存入 Redis，多服务共享。

### 场景 3：实时排行榜

```java
@Service
public class RankingService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    private static final String RANK_KEY = "ranking:weekly";

    /**
     * 更新用户分数。
     */
    public void updateScore(Long userId, double score) {
        stringRedisTemplate.opsForZSet().add(RANK_KEY, userId.toString(), score);
    }

    /**
     * 获取 Top 100 排行榜。
     */
    public List<RankItem> getTop100() {
        Set<ZSetOperations.TypedTuple<String>> tuples =
                stringRedisTemplate.opsForZSet()
                        .reverseRangeWithScores(RANK_KEY, 0, 99);

        List<RankItem> result = new ArrayList<>();
        int rank = 1;
        for (ZSetOperations.TypedTuple<String> tuple : tuples) {
            result.add(new RankItem(
                    rank++,
                    Long.valueOf(tuple.getValue()),
                    tuple.getScore()));
        }
        return result;
    }

    /**
     * 查询用户排名。
     */
    public Long getUserRank(Long userId) {
        Long rank = stringRedisTemplate.opsForZSet()
                .reverseRank(RANK_KEY, userId.toString());
        return rank == null ? null : rank + 1; // 排名从 1 开始
    }
}
```

### 场景 4：接口幂等性校验

```java
@Service
public class IdempotencyService {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 使用 SETNX 实现接口幂等。
     * 同一个 requestId 只能成功执行一次。
     */
    public boolean tryExecute(String requestId, Runnable action) {
        String key = "idempotent:" + requestId;

        // SETNX + 过期时间，原子操作
        Boolean success = stringRedisTemplate.opsForValue()
                .setIfAbsent(key, "1", 10, TimeUnit.MINUTES);

        if (Boolean.TRUE.equals(success)) {
            action.run();
            return true;
        }
        return false; // 重复请求，忽略
    }

    // 使用示例
    public void createOrder(String requestId, OrderDTO dto) {
        boolean executed = tryExecute(requestId, () -> {
            // 创建订单逻辑...
            System.out.println("订单创建: " + dto);
        });

        if (!executed) {
            throw new RuntimeException("请勿重复提交");
        }
    }
}
```

### 场景 5：分布式 ID 生成器

```java
@Service
public class RedisIdGenerator {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 基于 Redis INCR 的分布式 ID 生成。
     * 适合 QPS 不高的场景（高并发建议用雪花算法）。
     */
    public long nextId(String businessType) {
        String key = "id:sequence:" + businessType;
        Long id = stringRedisTemplate.opsForValue().increment(key, 1);

        // 防止 key 无限增长（设置一个较长的过期时间作为兜底）
        if (id != null && id == 1) {
            stringRedisTemplate.expire(key, 365, TimeUnit.DAYS);
        }
        return id;
    }
}
```

---

## 10. 最佳实践与踩坑记录

### 10.1 Key 命名规范

```
# 推荐格式：业务:类型:标识
user:info:1001          # 用户信息
user:cache:1001         # 用户缓存
order:detail:20240809   # 订单详情
sms:code:13800138000    # 验证码
ranking:daily:20240809  # 日排行榜

# 不要这样
user1001
order20240809
key123
```

用 `:` 分隔层级，Redis 客户端可图形化展示为树形结构。

### 10.2 缓存穿透 / 击穿 / 雪崩

| 问题 | 描述 | 解决方案 |
|------|------|----------|
| 缓存穿透 | 查询不存在的数据，直接打到 DB | 缓存空值、布隆过滤器（见 [[spring-boot-redisson]]） |
| 缓存击穿 | 热点 key 过期，瞬时大量请求打 DB | 互斥锁、逻辑过期（不设 TTL，用后台线程续期） |
| 缓存雪崩 | 大量 key 同时过期 | TTL 加随机值、多级缓存、限流降级 |

**TTL 加随机值示例：**

```java
public void setWithRandomTTL(String key, Object value, int baseMinutes) {
    int randomExtra = ThreadLocalRandom.current().nextInt(1, 10);
    long ttl = (baseMinutes + randomExtra) * 60;
    redisTemplate.opsForValue().set(key, value, ttl, TimeUnit.SECONDS);
}
```

### 10.3 大 Key 处理

```java
// 大 Key 的风险：
// - 读取慢，阻塞 Redis 单线程
// - 删除时造成主线程卡顿（Redis 4.0+ 可用 UNLINK 异步删除）
// - 带宽消耗大

// 解决方式 1：拆分
// 不要：hashKey = "user:all" 存所有用户
// 应该：hashKey = "user:1001" 每个用户独立

// 解决方式 2：批量拆页
public void setLargeObject(String key, Object value) {
    String json = new Gson().toJson(value);

    // 超过 10KB 压缩
    if (json.length() > 10240) {
        // 使用 GZIP 压缩
        byte[] compressed = compress(json);
        redisTemplate.opsForValue()
                .set(key, compressed, 30, TimeUnit.MINUTES);
    } else {
        redisTemplate.opsForValue()
                .set(key, value, 30, TimeUnit.MINUTES);
    }
}
```

### 10.4 慎用 keys 命令

```java
// keys 会阻塞 Redis 主线程，生产环境禁止使用
stringRedisTemplate.keys("user:*"); // 危险

// 使用 scan 代替
public Set<String> scanKeys(String pattern) {
    return stringRedisTemplate.execute((RedisCallback<Set<String>>) connection -> {
        Set<String> keys = new HashSet<>();
        Cursor<byte[]> cursor = connection.scan(
                ScanOptions.scanOptions().match(pattern).count(100).build());

        while (cursor.hasNext()) {
            keys.add(new String(cursor.next()));
        }
        return keys;
    });
}
```

### 10.5 @Cacheable 失效的常见原因

| 原因 | 说明 | 解决 |
|------|------|------|
| 同类方法调用 | `this.method()` 不走代理，AOP 不生效 | 注入自身代理，或拆分到不同类 |
| 非 Spring Bean | 类未交给 Spring 管理 | 加 `@Component` / `@Service` |
| 返回值 void | void 方法无法缓存 | 改为返回对象 |
| Key 不唯一 | 不同参数生成相同 key | 检查 SpEL 表达式 |
| 异常未捕获 | 方法抛异常缓存不写入 | 检查业务逻辑 |

### 10.6 连接池耗尽

```java
// 常见原因：
// 1. 事务内包含 Redis 操作（连接在事务结束后才释放）
// 2. 慢查询阻塞连接（keys、hgetall 大 key）
// 3. 连接泄露（未正确关闭）

// 排查方式：
// lettuce 连接池监控
@EventListener
public void handleConnectionEvent(ConnectionEvents.ConnectionActivatedEvent event) {
    log.info("Redis 连接激活: {}", event.getSource());
}
```

### 10.7 Redis 与 DB 数据一致性

```java
// 推荐方案：先更新 DB，再删除缓存（Cache Aside）

@Transactional
public User updateUser(User user) {
    // 1. 更新数据库
    userMapper.updateById(user);

    // 2. 删除缓存（不是更新缓存）
    redisTemplate.delete("user:" + user.getId());

    // 为什么删除而不是更新：
    // - 删除简单，更新涉及序列化和并发写入顺序问题
    // - 下次读取时自动重建缓存

    return user;
}
```

### 10.8 常见问题速查

| 问题 | 原因 | 解决 |
|------|------|------|
| `RedisConnectionFailureException` | Redis 未启动或网络不通 | 检查 `redis-cli ping` |
| `RedisCommandTimeoutException` | 命令执行超时 | 增大 `timeout`，检查是否有大 key |
| 存入 Redis 乱码 | 未配置序列化 | 使用 JSON 序列化（见 4.1 节） |
| `@Cacheable` 不生效 | 同类方法调用 | 拆分到不同 Service |
| 连接池耗尽报错 | 连接数不够或连接泄露 | 增大 pool size，检查事务 |
| `GenericJackson2JsonRedisSerializer` 反序列化报错 | 类结构变更 | 使用 `@JsonIgnoreProperties` 或在对象加 `@Type` 信息 |

---

## 总结

Spring Boot 集成 Redis 的核心是三个层面：

1. **RedisTemplate**：命令式操作，灵活但需要手动编码
2. **Spring Cache**：声明式缓存，用注解自动管理缓存，适合读多写少场景
3. **序列化**：生产环境必须替换为 JSON 序列化，避免 JDK 序列化的可读性和兼容性问题

配合 [[spring-boot-redisson]]（分布式锁、布隆过滤器等高级特性），可以覆盖绝大多数 Redis 使用场景。

---

## 参考链接

- [Spring Data Redis 官方文档](https://docs.spring.io/spring-data/redis/docs/current/reference/html/)
- [Spring Cache 官方文档](https://docs.spring.io/spring-framework/reference/integration/cache.html)
- [Lettuce 官方文档](https://lettuce.io/core/release/reference/)
- [Redis 命令参考](https://redis.io/commands/)
