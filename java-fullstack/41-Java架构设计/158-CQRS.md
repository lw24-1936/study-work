---
title: CQRS
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [cqrs, command, query, command-handler, query-handler, event]
---

# CQRS

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [核心概念](#核心概念)
- [Command 与 Query](#command-与-query)
- [读写分离](#读写分离)
- [CQRS 与 Event Sourcing](#cqrs-与-event-sourcing)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

CQRS（Command Query Responsibility Segregation，命令查询职责分离）把读操作和写操作分离，用不同的模型处理。

```text
传统模型的问题：
同一个模型既用于读又用于写：
- 读需要优化（联表查询、聚合）
- 写需要保证一致性
两者需求冲突，一个模型难以兼顾
```

```text
CQRS 的核心：
Command（命令）—— 写操作（修改数据）
Query（查询）—— 读操作（查询数据）

两者分离，用不同的模型、不同的存储
```

## 核心概念

### Command 与 Query

```text
Command（命令）—— 改变状态（创建、更新、删除）
Query（查询）—— 读取状态（不改变）
```

```java
// Command（命令）
public class CreateOrderCommand {
    private Long userId;
    private List<OrderItemDTO> items;
}

// Query（查询）
public class GetOrderQuery {
    private Long orderId;
}
```

### Command Handler 与 Query Handler

```text
Command Handler —— 处理命令（执行写操作）
Query Handler —— 处理查询（执行读操作）
```

```java
// Command Handler
public class CreateOrderHandler {
    public void handle(CreateOrderCommand command) {
        // 执行写操作（创建订单）
    }
}

// Query Handler
public class GetOrderHandler {
    public Order handle(GetOrderQuery query) {
        // 执行读操作（查询订单）
    }
}
```

## Command 与 Query

### Command 的特点

```text
1. 改变状态 —— 有副作用
2. 不返回数据 —— 命令不返回查询结果
3. 幂等设计 —— 命令可能需要幂等
```

### Query 的特点

```text
1. 不改变状态 —— 无副作用
2. 返回数据 —— 返回查询结果
3. 可优化 —— 读模型可以针对性优化
```

### CQRS 的读写分离

```text
写模型（Write Model）：
- 面向业务（领域模型）
- 保证一致性
- 存数据库

读模型（Read Model）：
- 面向查询（DTO/视图）
- 优化查询（冗余、聚合、缓存）
- 可以是独立存储（读库、ES、缓存）
```

## 读写分离

### 数据库读写分离

```text
主库（写）→ 同步 → 从库（读）

写操作 → 主库
读操作 → 从库
```

```java
// 读写分离（Spring 动态数据源）
@Service
public class OrderService {

    @Write   // 走主库
    public void createOrder(Order order) { ... }

    @Read    // 走从库
    public Order getOrder(Long id) { ... }
}
```

### 读模型优化

```text
读模型的优化手段：
1. 预聚合 —— 提前计算好聚合数据
2. 冗余 —— 冗余字段减少 join
3. 缓存 —— 热点数据缓存
4. 搜索引擎 —— ES 全文搜索
```

## CQRS 与 Event Sourcing

CQRS 常和 Event Sourcing 搭配（详见 159-Event Sourcing）。

### 为什么搭配

```text
CQRS 分离读写，Event Sourcing 存储事件：
1. 事件流作为写模型（Event Store）
2. 投影（Projection）生成读模型
3. 天然支持 CQRS 的读写分离
```

```text
CQRS + Event Sourcing：
写：命令 → 事件 → Event Store
读：事件 → 投影 → 读模型 → 查询
```

## 应用场景实战

### 场景 1：订单系统 CQRS

```java
// 写模型（命令）
@Service
public class OrderCommandService {
    public void createOrder(CreateOrderCommand cmd) {
        // 创建订单（写主库）
    }
}

// 读模型（查询）
@Service
public class OrderQueryService {
    public OrderDetailDTO getOrderDetail(Long orderId) {
        // 查询订单详情（读从库/缓存，聚合用户、明细）
    }
}
```

### 场景 2：复杂报表系统

```text
场景：订单量巨大，查询复杂（多维度统计）

写模型：订单数据（主库，简单写入）
读模型：预聚合的统计表（从库/ES，优化查询）
```

## 最佳实践与踩坑记录

### 最佳实践

1. **先判断是否需要 CQRS**。读写都简单用传统模型，复杂才用 CQRS。

2. **读模型独立优化**。读模型可以用缓存、ES、预聚合。

3. **命令要幂等**。命令可能重试，要幂等。

4. **读写一致性**。读模型可能延迟（最终一致），要考虑一致性。

5. **从简到繁**。先代码层面分离（Command/Query），再存储分离。

### 踩坑记录

**坑 1：简单系统过度设计**

```text
简单 CRUD 也上 CQRS，复杂度远超收益
```

读写不冲突、不复杂，用传统模型即可。

**坑 2：忽略读写一致性**

```text
写后立即读，读模型还没同步（最终一致），读到旧数据
```

明确一致性要求，写后读走主库，或接受最终一致。

**坑 3：命令返回查询结果**

```java
public Order createOrder(CreateOrderCommand cmd) {
    // 命令返回了 Order（查询结果），违反 CQRS
    return order;
}
```

命令不返回查询结果，查询用 Query Handler。

**坑 4：读模型过度冗余**

```text
读模型冗余字段太多，同步复杂，数据不一致
```

读模型冗余要克制，权衡查询性能和一致性。

**坑 5：CQRS 和 Event Sourcing 强绑定**

```text
以为 CQRS 必须配 Event Sourcing，增加复杂度
```

CQRS 可以独立使用，Event Sourcing 可选。
