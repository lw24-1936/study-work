---
title: Redis 基础
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [redis, string, list, set, hash, zset, stream, bitmap, hyperloglog, geo]
---

# Redis 基础

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [String 字符串](#string-字符串)
- [Hash 哈希](#hash-哈希)
- [List 列表](#list-列表)
- [Set 集合](#set-集合)
- [ZSet 有序集合](#zset-有序集合)
- [Bitmap 位图](#bitmap-位图)
- [HyperLogLog](#hyperloglog)
- [Geo 地理位置](#geo-地理位置)
- [Stream 流](#stream-流)
- [数据类型选型总结](#数据类型选型总结)

## 概述

Redis（Remote Dictionary Server）是高性能的内存键值数据库，是使用最广泛的缓存和数据结构存储。

```text
Redis 的特点：
1. 高性能 —— 内存操作，单机 QPS 可达 10 万+
2. 丰富的数据结构 —— 10 种数据类型，远超简单 KV
3. 持久化 —— RDB/AOF 支持数据落盘
4. 高可用 —— 主从、哨兵、集群
5. 原子操作 —— 单线程命令，天然原子
```

```text
Redis 为什么快：
1. 纯内存操作 —— 无磁盘 IO
2. 单线程 —— 无锁竞争、无上下文切换
3. 高效数据结构 —— 多种底层实现按数据量自动切换
4. IO 多路复用 —— 一个线程处理多个连接
```

```text
10 种数据类型：
String、List、Set、Hash、ZSet（5 种基础）
Bitmap、HyperLogLog、Geo（3 种扩展）
Stream（消息流）
```

## String 字符串

String 是最基础的类型，一个 key 对应一个字符串值，最大 512MB。

### 常用命令

```bash
# 基本读写
SET key value          # 设置
GET key                # 获取
DEL key                # 删除
EXISTS key             # 判断存在

# 数字操作（value 是数字时）
INCR key               # 自增 1
DECR key               # 自减 1
INCRBY key 10          # 加 10

# 过期时间
SETEX key 60 value     # 设置并指定 60 秒过期
SET key value EX 60    # 同上
TTL key                # 查看剩余过期时间

# 批量操作
MSET k1 v1 k2 v2       # 批量设置
MGET k1 k2             # 批量获取

# 条件设置
SETNX key value        # 不存在才设置（分布式锁核心）
SET key value NX       # 同上

# 追加
APPEND key "suffix"    # 追加字符串
```

### 底层实现

```text
String 的底层有三种编码：
1. int —— 整数（8 字节，能存 long 范围）
2. embstr —— 短字符串（≤ 44 字节，一次分配）
3. raw —— 长字符串（> 44 字节，两次分配）
```

### 应用场景

```text
1. 缓存 —— 缓存对象（JSON 字符串）
2. 计数器 —— 浏览量、点赞数（INCR 原子自增）
3. 分布式锁 —— SETNX + 过期时间
4. Session —— 会话数据
```

## Hash 哈希

Hash 是一个 key 对应多个 field-value 对，适合存储对象。

### 常用命令

```bash
HSET user:1001 name "张三"     # 设置单个字段
HGET user:1001 name            # 获取单个字段
HMSET user:1001 name "张三" age 20  # 设置多个字段
HGETALL user:1001              # 获取所有字段
HDEL user:1001 age             # 删除字段
HEXISTS user:1001 name         # 判断字段存在
HINCRBY user:1001 age 1        # 字段自增
HLEN user:1001                 # 字段数量
HKEYS user:1001                # 所有字段名
HVALS user:1001                # 所有字段值
```

### 底层实现

```text
Hash 的底层有两种编码：
1. ziplist（压缩列表）—— 字段少、值短时（默认 512 个字段内）
2. hashtable（哈希表）—— 字段多或值长时
```

### 应用场景

```text
1. 存储对象 —— 用户信息（相比 String 存 JSON，Hash 可部分更新）
2. 购物车 —— 用户 ID + 商品 ID + 数量
3. 计数器分组 —— 多个相关计数器
```

```text
Hash vs String 存对象：
String：user:1001 → {"name":"张三","age":20}（整个 JSON）
Hash：user:1001 → name=张三, age=20（字段独立）

Hash 优势：可以只更新某个字段，不用整个重写
```

## List 列表

List 是一个有序的字符串列表，底层是双向链表，支持两端操作。

### 常用命令

```bash
# 两端操作
LPUSH key v1 v2        # 从左边插入
RPUSH key v1 v2        # 从右边插入
LPOP key               # 从左边弹出
RPOP key               # 从右边弹出

# 范围查询
LRANGE key 0 -1        # 获取所有元素
LRANGE key 0 9         # 获取前 10 个

# 长度
LLEN key               # 列表长度

# 阻塞弹出（消息队列核心）
BLPOP key 10           # 阻塞弹出（10 秒超时）
BRPOP key 10

# 修剪
LTRIM key 0 99         # 只保留前 100 个
```

### 底层实现

```text
List 的底层有两种编码：
1. ziplist（压缩列表）—— 元素少且短时
2. linkedlist/quicklist —— 元素多时（Redis 7 用 quicklist）
```

### 应用场景

```text
1. 消息队列 —— LPUSH + BRPOP 实现简单队列
2. 最新列表 —— LPUSH + LTRIM 实现最新 N 条（如最新评论）
3. 栈 —— LPUSH + LPOP
4. 时间线 —— 关注的人动态
```

## Set 集合

Set 是无序的字符串集合，元素唯一，支持集合运算。

### 常用命令

```bash
SADD key v1 v2          # 添加元素
SREM key v1             # 删除元素
SISMEMBER key v1        # 判断元素存在
SMEMBERS key            # 获取所有元素
SCARD key               # 元素数量

# 集合运算
SINTER k1 k2            # 交集（共同好友）
SUNION k1 k2            # 并集
SDIFF k1 k2             # 差集（k1 有 k2 没有）

# 随机元素
SRANDMEMBER key 3       # 随机取 3 个（不删除）
SPOP key                # 随机弹出 1 个（删除）
```

### 底层实现

```text
Set 的底层有两种编码：
1. intset（整数集合）—— 全是整数且数量少
2. hashtable（哈希表）—— 其他情况
```

### 应用场景

```text
1. 去重 —— 唯一元素（如已读用户）
2. 共同好友 —— SINTER 求交集
3. 标签系统 —— 每个标签一个 Set
4. 抽奖 —— SRANDMEMBER 随机抽取
5. 点赞用户 —— SADD 记录点赞用户（去重）
```

## ZSet 有序集合

ZSet 是带分数的有序集合，元素按分数排序，是 Redis 最强大的类型之一。

### 常用命令

```bash
ZADD key 90 "张三"      # 添加（分数 90）
ZREM key "张三"         # 删除
ZSCORE key "张三"       # 获取分数
ZRANK key "张三"        # 排名（从小到大，从 0 开始）
ZREVRANK key "张三"     # 排名（从大到小）

# 范围查询
ZRANGE key 0 9          # 分数从小到大前 10
ZREVRANGE key 0 9       # 分数从大到小前 10
ZRANGEBYSCORE key 60 90 # 分数 60-90 之间的元素

# 分数操作
ZINCRBY key 10 "张三"   # 分数加 10

# 数量
ZCARD key               # 元素数量
ZCOUNT key 60 90        # 分数范围内的数量
```

### 底层实现

```text
ZSet 的底层有两种编码：
1. ziplist（压缩列表）—— 元素少时
2. skiplist + hashtable —— 元素多时（跳表保证排序 + 哈希保证查找）
```

### 应用场景

```text
1. 排行榜 —— 分数排序（游戏积分、销量、热度）
2. 延迟队列 —— 分数为时间戳
3. 优先级队列 —— 分数为优先级
4. 滑动窗口限流 —— 分数为时间戳 + ZRANGEBYSCORE
```

## Bitmap 位图

Bitmap 是用 bit 位存储布尔值的数据结构，极致节省内存。

### 常用命令

```bash
SETBIT key offset 1     # 设置第 offset 位为 1
GETBIT key offset       # 获取第 offset 位
BITCOUNT key            # 统计 1 的数量
BITPOS key 1            # 第一个 1 的位置

# 位运算
BITOP AND result k1 k2  # 交集（AND 运算）
BITOP OR result k1 k2   # 并集
BITOP XOR result k1 k2  # 异或
```

### 内存优势

```text
存储 1 亿个用户某天的签到状态：
普通存储（Set）：约 1 亿个元素，几 GB 内存
Bitmap：1 亿 bit = 12.5 MB，节省几百倍
```

### 应用场景

```text
1. 用户签到 —— 用户 ID 为 offset，1 表示签到
2. 在线状态 —— 用户在线标记
3. 布隆过滤器（配合）
4. 活跃统计 —— 某功能的使用用户
```

```bash
# 签到示例：用户 1001 在 2026-01-15（第 15 天）签到
SETBIT sign:2026-01 1001 1
# 统计 1 月签到天数
BITCOUNT sign:2026-01
```

## HyperLogLog

HyperLogLog 是基数统计数据结构，用极少内存统计海量数据的去重数量（近似值）。

### 常用命令

```bash
PFADD key v1 v2 v3       # 添加元素
PFCOUNT key              # 统计去重数量（近似）
PFMERGE result k1 k2     # 合并多个 HyperLogLog
```

### 特点

```text
1. 极省内存 —— 固定 12KB，统计 2^64 个元素
2. 近似统计 —— 误差约 0.81%
3. 只统计数量 —— 不存储元素本身
```

### 应用场景

```text
1. UV 统计 —— 网站独立访客（去重计数）
2. 去重计数 —— 活动参与人数
```

```text
对比：
Set 统计 UV：精确，但内存随元素增长
HyperLogLog：近似（0.81% 误差），固定 12KB
适合"大数统计、不要求精确"的场景
```

## Geo 地理位置

Geo 是地理位置存储，基于 ZSet 实现，支持距离计算和范围查询。

### 常用命令

```bash
GEOADD cities 116.40 39.90 "北京"     # 添加经纬度
GEOPOS cities "北京"                   # 获取经纬度
GEODIST cities "北京" "上海" km        # 距离（千米）
GEORADIUS cities 116.40 39.90 100 km   # 半径 100km 内的位置
GEOSEARCH cities FROMMEMBER "北京" BYRADIUS 100 km  # 附近的位置
```

### 底层实现

```text
Geo 基于 ZSet 实现：
经纬度编码为 Geohash（作为 ZSet 的 score），
距离计算用 Haversine 公式。
```

### 应用场景

```text
1. 附近的人 —— 基于经纬度查询附近用户
2. 附近商家 —— 外卖、打车（LBS）
3. 距离计算 —— 配送距离
```

## Stream 流

Stream 是 Redis 5.0 引入的消息队列数据结构，提供完整的消息队列能力。

### 常用命令

```bash
# 添加消息
XADD stream * field1 value1 field2 value2  # * 自动生成 ID

# 读取消息
XREAD COUNT 10 STREAMS stream 0     # 从头读 10 条
XREAD BLOCK 0 STREAMS stream $      # 阻塞读新消息

# 消费组
XGROUP CREATE stream group1 0       # 创建消费组
XREADGROUP GROUP group1 consumer1 COUNT 10 STREAMS stream >
XACK stream group1 message-id       # 确认消息
```

### Stream 的特点

```text
1. 消息持久化 —— 消息存在 Redis，可重复读
2. 消费组 —— 类似 Kafka 的消费者组
3. 消息确认 —— XACK 确认机制
4. 阻塞读取 —— XREAD BLOCK
```

### Stream vs 专业消息队列

| 维度 | Redis Stream | Kafka/RocketMQ |
|------|-------------|----------------|
| 可靠性 | 依赖 Redis 持久化 | 高（落盘） |
| 吞吐 | 中 | 高 |
| 功能 | 基础 | 完整（事务、延迟） |
| 适用 | 轻量消息 | 核心消息 |

```text
Stream 适合轻量消息队列，核心业务消息仍用 Kafka/RocketMQ。
```

## 数据类型选型总结

| 类型 | 数据结构 | 应用场景 |
|------|---------|---------|
| String | 字符串 | 缓存、计数器、分布式锁 |
| Hash | 字段映射 | 存储对象、购物车 |
| List | 双向链表 | 队列、最新列表 |
| Set | 集合 | 去重、共同好友、抽奖 |
| ZSet | 有序集合 | 排行榜、延迟队列 |
| Bitmap | 位图 | 签到、在线状态 |
| HyperLogLog | 基数统计 | UV 统计 |
| Geo | 地理位置 | 附近的人 |
| Stream | 消息流 | 轻量消息队列 |

```text
选型速记：
- 存对象 → Hash（可部分更新）或 String（存 JSON）
- 排行榜/排序 → ZSet
- 去重/集合运算 → Set
- 队列 → List（简单）/ Stream（完整）
- 计数（精确）→ String INCR
- 计数（海量去重）→ HyperLogLog
- 布尔状态（海量）→ Bitmap
- 位置 → Geo
```
