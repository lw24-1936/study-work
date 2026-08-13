---
title: Redis 高级
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [redis, rdb, aof, 持久化, 主从, sentinel, cluster, pipeline, lua, pub-sub, stream]
---

# Redis 高级

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [RDB 持久化](#rdb-持久化)
- [AOF 持久化](#aof-持久化)
- [混合持久化](#混合持久化)
- [事务](#事务)
- [Pipeline 管道](#pipeline-管道)
- [Lua 脚本](#lua-脚本)
- [Pub/Sub 发布订阅](#pubsub-发布订阅)
- [主从 / Sentinel / Cluster](#主从--sentinel--cluster)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Redis 高级特性包括持久化、事务、Pipeline、Lua、发布订阅以及高可用架构。理解这些是生产环境用好 Redis 的基础。

```text
本篇聚焦：
1. 持久化 —— RDB、AOF、混合持久化（数据不丢）
2. 事务与 Pipeline —— 批量操作优化
3. Lua 脚本 —— 原子性复杂操作
4. Pub/Sub —— 发布订阅
5. 高可用架构 —— 主从、哨兵、集群（详见 105-分布式缓存）
```

## RDB 持久化

RDB（Redis Database）是快照持久化，将某一时刻的内存数据写入磁盘文件。

### RDB 原理

```text
RDB = 内存数据快照

触发时机：
1. 手动触发：SAVE（阻塞）、BGSAVE（后台，fork 子进程）
2. 自动触发：满足 save 配置（如 900 秒内 1 次修改）
```

```text
BGSAVE 流程（不阻塞）：
1. Redis 主进程 fork 子进程
2. 子进程将内存数据写入临时 RDB 文件
3. 写完后原子替换旧 RDB 文件
4. fork 使用写时复制（COW），内存翻倍风险
```

### RDB 配置

```properties
# redis.conf
save 900 1       # 900 秒内至少 1 次修改则触发
save 300 10      # 300 秒内至少 10 次修改
save 60 10000    # 60 秒内至少 10000 次修改

dbfilename dump.rdb
dir /var/lib/redis
```

### RDB 优缺点

```text
优点：
1. 文件紧凑 —— 二进制文件，适合备份和灾难恢复
2. 恢复快 —— 直接加载快照，速度快
3. 性能影响小 —— fork 子进程，主进程不阻塞

缺点：
1. 可能丢数据 —— 两次快照之间的数据丢失（如 5 分钟）
2. fork 开销 —— 大内存 fork 可能阻塞（毫秒级）
3. 内存翻倍 —— 写时复制期间内存可能翻倍
```

## AOF 持久化

AOF（Append Only File）是日志持久化，记录每次写命令，重启时重放命令恢复数据。

### AOF 原理

```text
AOF = 记录写命令日志

流程：
1. 每次写操作追加到 AOF 缓冲区
2. 缓冲区按策略刷盘（appendfsync）
3. 重启时重放 AOF 命令恢复数据
```

### AOF 刷盘策略

```properties
# redis.conf
appendfsync always    # 每次写都刷盘（最安全，性能差）
appendfsync everysec  # 每秒刷盘（折中，默认，最多丢 1 秒数据）
appendfsync no        # 交给操作系统（性能最好，可能丢数据）
```

### AOF 重写

```text
问题：AOF 文件持续增长（记录所有写命令）

解决：AOF 重写（BGREWRITEAOF）
将多条命令合并为一条（如 100 次 INCR 合并为 1 次 SET）
```

```text
重写前：
INCR counter × 100 次 → AOF 记录 100 条命令

重写后：
SET counter 100 → AOF 只有 1 条命令
```

### AOF 优缺点

```text
优点：
1. 数据安全 —— 最多丢 1 秒数据（everysec）
2. 可读 —— AOF 是文本命令，可人工查看
3. 自动重写 —— 防止文件无限增长

缺点：
1. 文件大 —— 比 RDB 大（记录命令）
2. 恢复慢 —— 重放命令比加载快照慢
3. 性能略差 —— 每次写都要记录
```

## 混合持久化

混合持久化（Redis 4.0+）结合 RDB 和 AOF 的优点。

### 混合原理

```text
AOF 重写时，先写 RDB 快照，再追加增量命令：

AOF 文件结构：
[RDB 快照][增量 AOF 命令]

重写时：将当前内存生成 RDB 快照写入 AOF 文件开头
重写后：新增写命令以 AOF 格式追加
```

### 混合配置

```properties
# redis.conf
aof-use-rdb-preamble yes   # 开启混合持久化（默认开启）
```

### 三种持久化对比

| 维度 | RDB | AOF | 混合 |
|------|-----|-----|------|
| 数据安全 | 差（可能丢几分钟） | 好（丢 1 秒） | 好 |
| 文件大小 | 小 | 大 | 中 |
| 恢复速度 | 快 | 慢 | 快 |
| 性能影响 | 小 | 中 | 中 |

```text
选型建议：
1. 生产环境默认开启混合持久化（aof-use-rdb-preamble yes + appendfsync everysec）
2. 纯缓存（可丢数据）→ 关闭持久化
3. 备份 → 定期 RDB 快照
```

## 事务

Redis 事务提供命令的批量执行，保证原子性和顺序性。

### 事务命令

```bash
MULTI           # 开启事务
SET k1 v1
INCR counter
EXEC            # 执行事务（所有命令一起执行）
DISCARD         # 取消事务
WATCH key       # 乐观锁（监视 key，key 变化则事务失败）
```

### 事务的特点

```text
1. 原子性 —— 事务内命令要么都执行，要么都不执行（不保证回滚）
2. 顺序性 —— 按入队顺序执行
3. 无隔离性 —— 事务执行期间其他命令不能插入（单线程）
4. 错误处理 —— 语法错误（入队时发现）全部不执行；运行时错误（如类型错）继续执行其他命令
```

```java
// Redis 事务（Spring Data Redis）
List<Object> results = redisTemplate.execute(new SessionCallback<List<Object>>() {
    @Override
    public List<Object> execute(RedisOperations operations) {
        operations.multi();                       // 开启事务
        operations.opsForValue().set("k1", "v1");
        operations.opsForValue().increment("counter");
        return operations.exec();                 // 执行
    }
});
```

### 事务 vs Lua

```text
事务：保证原子性，但不能用中间结果（命令间不能传递结果）
Lua：保证原子性 + 可以用中间结果（脚本内可编程）

复杂原子操作用 Lua，简单批处理用事务
```

## Pipeline 管道

Pipeline 批量发送命令，减少网络往返（RTT），提升吞吐。

### Pipeline 原理

```text
普通模式：发命令 → 等响应 → 发命令 → 等响应（N 次 RTT）
Pipeline：一次发送 N 条命令 → 一次接收 N 个响应（1 次 RTT）
```

```text
普通：CMD1 → RESP1 → CMD2 → RESP2 → ...（慢）
管道：CMD1 CMD2 CMD3 → RESP1 RESP2 RESP3（快）
```

### Pipeline 实现

```java
// Spring Data Redis Pipeline
List<Object> results = redisTemplate.executePipelined(
    new SessionCallback<Object>() {
        @Override
        public Object execute(RedisOperations operations) {
            for (int i = 0; i < 1000; i++) {
                operations.opsForValue().set("key:" + i, i);
            }
            return null;   // 返回 null，结果在 results 中
        }
    });
```

```java
// Jedis Pipeline
Pipeline pipeline = jedis.pipelined();
for (int i = 0; i < 1000; i++) {
    pipeline.set("key:" + i, String.valueOf(i));
}
pipeline.sync();   // 一次性发送并接收
```

### Pipeline 的注意事项

```text
1. Pipeline 不保证原子性 —— 命令可能与其他客户端命令交错
2. Pipeline 减少 RTT —— 适合批量独立操作
3. 与事务区别 —— 事务保证原子，Pipeline 只是批量
4. 批量大小 —— 太大占内存，一般 1000 条左右
```

## Lua 脚本

Lua 脚本在 Redis 服务端原子执行，可用于复杂原子操作。

### 为什么用 Lua

```text
1. 原子性 —— 整个脚本原子执行，中间不被其他命令打断
2. 减少网络开销 —— 复杂逻辑一次脚本搞定
3. 复用 —— 脚本可缓存（EVALSHA）
```

### Lua 脚本示例

```lua
-- 限流脚本（原子判断 + 扣减）
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
    return 0   -- 超过限制
end
return 1       -- 放行
```

```lua
-- 分布式锁释放（原子判断 + 删除）
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
```

### Java 执行 Lua

```java
// 限流 Lua 脚本
String script =
    "local current = redis.call('INCR', KEYS[1]) " +
    "if current == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end " +
    "if current > tonumber(ARGV[2]) then return 0 end " +
    "return 1";

Long result = redisTemplate.execute(
    new DefaultRedisScript<>(script, Long.class),
    Collections.singletonList("limit:api"),   // KEYS
    "60", "100");                              // ARGV（60 秒、100 次）

if (result == 1) {
    // 放行
} else {
    // 限流
}
```

### Lua 的注意事项

```text
1. 脚本要快 —— 原子执行会阻塞其他命令
2. 不要在脚本里做耗时操作（循环、大遍历）
3. 脚本用 KEYS/ARGV 传参 —— 不要拼接字符串
4. 集群模式下，脚本涉及的 key 要在同一槽
```

## Pub/Sub 发布订阅

Pub/Sub 是 Redis 的发布订阅功能，实现消息广播。

### 常用命令

```bash
SUBSCRIBE channel1 channel2   # 订阅频道
PUBLISH channel1 "message"    # 发布消息
PSUBSCRIBE pattern            # 模式订阅（通配符）
UNSUBSCRIBE channel1          # 取消订阅
```

```java
// Spring Data Redis 发布订阅
// 发布
redisTemplate.convertAndSend("channel:order", "订单已创建");

// 订阅
@Bean
RedisMessageListenerContainer container(RedisConnectionFactory factory) {
    RedisMessageListenerContainer container = new RedisMessageListenerContainer();
    container.setConnectionFactory(factory);
    container.addMessageListener(
        (message, pattern) -> System.out.println(new String(message.getBody())),
        new ChannelTopic("channel:order"));
    return container;
}
```

### Pub/Sub 的局限

```text
1. 消息不持久化 —— 订阅者离线期间的消息丢失
2. 无确认机制 —— 发了就忘，不保证消费
3. 无消息回溯 —— 只能收到订阅后的消息
```

```text
Pub/Sub vs Stream：
Pub/Sub：广播、无持久化、无确认（简单通知）
Stream：消息队列、持久化、消费组、确认（可靠消息）

可靠消息用 Stream，简单广播通知用 Pub/Sub
```

## 主从 / Sentinel / Cluster

Redis 的高可用架构（详见 105-分布式缓存，这里简要回顾）。

### 主从复制

```text
一主多从：主写从读
解决：读扩展、数据备份
局限：主节点单点、无自动故障转移
```

### Sentinel 哨兵

```text
主从 + 哨兵：自动故障转移
解决：主节点故障自动切换
局限：单主写、无法水平扩展
```

### Cluster 集群

```text
多主多从 + 数据分片（16384 槽）
解决：水平扩展、容量、高可用
局限：跨槽操作限制、复杂度高
```

```text
选型：
小规模（< 10GB）→ 主从或 Sentinel
大规模（> 10GB，需扩展）→ Cluster
```

## 最佳实践与踩坑记录

### 最佳实践

1. **生产环境用混合持久化**。`aof-use-rdb-preamble yes` + `appendfsync everysec`，兼顾安全和性能。

2. **批量操作用 Pipeline**。减少 RTT，吞吐提升明显（1000 条一批）。

3. **复杂原子操作用 Lua**。比事务更灵活，且能保证原子性。

4. **大 key 要拆分**。单个 key 过大（如几 MB），影响性能，拆成 Hash 或多个 key。

5. **定期备份 RDB**。RDB 适合备份和灾难恢复，定期备份到异地。

### 踩坑记录

**坑 1：RDB 的 fork 导致内存翻倍**

```text
BGSAVE fork 子进程时，写时复制导致内存翻倍
内存 10GB，fork 时可能占用 20GB，OOM 风险
```

预留足够内存（至少 1.5 倍），或监控 fork 耗时。

**坑 2：AOF 文件过大**

```text
AOF 文件持续增长，没有开启自动重写，
文件几十 GB，恢复极慢
```

开启 AOF 自动重写（auto-aof-rewrite-percentage）。

**坑 3：Lua 脚本阻塞 Redis**

```lua
-- 错误：在 Lua 里循环遍历大量 key（阻塞）
local keys = redis.call('KEYS', 'user:*')
for i, key in ipairs(keys) do
    redis.call('DEL', key)
end
-- KEYS 命令本身就慢，加上循环，阻塞 Redis
```

Lua 脚本要快，不要用 KEYS（生产禁用），用 SCAN。

**坑 4：事务和 Pipeline 混淆**

```java
// Pipeline 不保证原子性，多条命令可能和其他客户端命令交错
// 需要原子性时用事务或 Lua，不能只靠 Pipeline
```

Pipeline 只是批量减少 RTT，不保证原子性。

**坑 5：Pub/Sub 消息丢失**

```text
订阅者离线期间发布的消息直接丢失（无持久化）
用于通知（丢了可接受），不能用于关键业务消息
```

关键消息用 Stream 或专业消息队列（Kafka/RocketMQ）。

**坑 6：混合持久化配置错误**

```properties
# 只开了 AOF 但 appendonly 没开启
appendonly no          # AOF 关闭
aof-use-rdb-preamble yes   # 这个配置无效（AOF 没开）
```

使用混合持久化前要 `appendonly yes` 开启 AOF。
