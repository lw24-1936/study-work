---
title: Event Sourcing
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [event-sourcing, event, event-store, event-stream, snapshot, projection]
---

# Event Sourcing

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [核心概念](#核心概念)
- [Event Store 事件存储](#event-store-事件存储)
- [Snapshot 快照](#snapshot-快照)
- [Projection 投影](#projection-投影)
- [Event Sourcing 与 CQRS](#event-sourcing-与-cqrs)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Event Sourcing（事件溯源）把所有状态变更记录为事件，状态由事件重放推导，而不是直接存储当前状态。

```text
传统存储：存当前状态（余额 = 100 元）
Event Sourcing：存事件序列（+50、-20、+70），重放得到当前状态
```

```text
Event Sourcing 的核心思想：
1. 不存状态，存事件
2. 状态 = 事件重放的结果
3. 事件不可变、可追溯
```

```text
Event Sourcing 的价值：
1. 完整历史 —— 任何时刻的状态都可重建
2. 审计 —— 谁在何时做了什么，一清二楚
3. 追溯 —— 可回溯到任意历史状态
4. 调试 —— 重放事件复现问题
```

## 核心概念

### Event（事件）

```text
事件 = 状态变更的事实（不可变、过去式命名）
```

```java
// 事件（不可变、过去式命名）
public class AccountCreatedEvent {
    private Long accountId;
    private BigDecimal initialBalance;
}

public class MoneyDepositedEvent {
    private Long accountId;
    private BigDecimal amount;
}

public class MoneyWithdrawnEvent {
    private Long accountId;
    private BigDecimal amount;
}
```

### 状态由事件推导

```text
事件序列：
1. AccountCreated(账户创建，100 元)
2. MoneyDeposited(存入 50 元)
3. MoneyWithdrawn(取出 20 元)

当前余额 = 100 + 50 - 20 = 130 元（重放事件得到）
```

## Event Store 事件存储

Event Store 是事件的存储，只追加（append-only），不可修改。

### Event Store 的特点

```text
1. 只追加 —— 事件只能追加，不能修改删除
2. 有序 —— 事件按发生顺序存储
3. 按聚合分组 —— 每个聚合有自己的事件流
```

### 事件存储实现

```java
public interface EventStore {
    // 追加事件
    void append(Long aggregateId, List<DomainEvent> events);

    // 加载事件流（用于重放）
    List<DomainEvent> load(Long aggregateId);
}
```

```java
// 数据库表存储事件
CREATE TABLE events (
    id BIGINT PRIMARY KEY,
    aggregate_id BIGINT,      -- 聚合 ID
    aggregate_type VARCHAR(64),
    event_type VARCHAR(64),   -- 事件类型
    event_data JSON,          -- 事件数据
    version INT,              -- 版本（乐观锁）
    created_at DATETIME
);
```

### 事件重放

```java
public Account loadAccount(Long accountId) {
    // 加载事件流
    List<DomainEvent> events = eventStore.load(accountId);

    // 重放事件，重建状态
    Account account = new Account();
    for (DomainEvent event : events) {
        account.apply(event);   // 应用事件
    }
    return account;
}
```

## Snapshot 快照

Snapshot 是状态的快照，避免每次都从头重放事件。

### 为什么需要快照

```text
问题：聚合事件多了（几千个），每次重放很慢
解决：定期保存快照，从最近的快照 + 后续事件重放
```

```text
快照 + 增量重放：
快照（第 1000 个事件时的状态）+ 重放第 1001-1050 个事件
而不是从第 1 个事件重放
```

### 快照实现

```java
public Account loadAccount(Long accountId) {
    // 1. 加载最近的快照
    AccountSnapshot snapshot = snapshotStore.loadLatest(accountId);

    // 2. 从快照版本开始重放后续事件
    List<DomainEvent> events = eventStore.loadAfter(accountId, snapshot.getVersion());

    Account account = snapshot.getAccount();
    for (DomainEvent event : events) {
        account.apply(event);
    }
    return account;
}
```

## Projection 投影

投影把事件流转换成读模型（当前状态），供查询使用。

### 投影是什么

```text
投影 = 消费事件，生成/更新读模型

事件流 → 投影 → 读模型（当前状态表）
```

```java
// 投影：消费事件，维护读模型
public class AccountProjection {

    @EventHandler
    public void on(MoneyDepositedEvent event) {
        // 更新账户余额表（读模型）
        accountReadModel.increaseBalance(event.getAccountId(), event.getAmount());
    }

    @EventHandler
    public void on(MoneyWithdrawnEvent event) {
        accountReadModel.decreaseBalance(event.getAccountId(), event.getAmount());
    }
}
```

### 投影的用途

```text
1. 读模型 —— 当前状态（查询用）
2. 报表 —— 聚合统计
3. 搜索索引 —— ES 索引
```

## Event Sourcing 与 CQRS

Event Sourcing 和 CQRS 是黄金搭档（详见 158-CQRS）。

### 为什么搭配

```text
Event Sourcing 提供事件流（写模型）
CQRS 通过投影生成读模型（读模型分离）
```

```text
完整架构：
命令（写）→ 生成事件 → Event Store
                            ↓
                        投影（Projection）
                            ↓
                        读模型 → 查询（读）
```

### 单独使用 vs 搭配使用

```text
单独用 Event Sourcing —— 有历史追溯，但查询复杂
单独用 CQRS —— 读写分离，但无历史
搭配使用 —— 事件流 + 投影，完美结合
```

## 应用场景实战

### 场景 1：银行账户（经典场景）

```java
// 账户操作都记录事件
public class AccountService {
    public void deposit(Long accountId, BigDecimal amount) {
        // 记录存款事件
        eventStore.append(accountId, new MoneyDepositedEvent(accountId, amount));
    }

    public BigDecimal getBalance(Long accountId) {
        // 重放事件得到余额
        return loadAccount(accountId).getBalance();
    }
}
```

### 场景 2：订单状态追溯

```text
订单事件流：
1. OrderCreated
2. OrderPaid
3. OrderShipped
4. OrderDelivered

任何时刻的订单状态都可重建，完整审计历史
```

## 最佳实践与踩坑记录

### 最佳实践

1. **事件不可变**。事件一旦存储，不可修改（追加新事件补偿）。

2. **事件用过去式命名**。OrderCreated、MoneyDeposited。

3. **配合快照**。事件多了用快照优化重放性能。

4. **配合 CQRS**。投影生成读模型，避免每次重放。

5. **事件版本化**。事件结构变化要版本化（兼容旧事件）。

### 踩坑记录

**坑 1：事件重放性能差**

```text
聚合几万个事件，每次重放极慢
```

用快照（Snapshot），从最近快照 + 增量事件重放。

**坑 2：修改事件**

```text
直接修改已存储的事件，破坏历史，状态错乱
```

事件不可变，用补偿事件（新事件修正）。

**坑 3：事件版本升级**

```text
事件结构变了，旧事件无法反序列化
```

事件版本化，兼容旧版本事件。

**坑 4：所有场景都用 Event Sourcing**

```text
简单场景也用 Event Sourcing，复杂度高收益低
```

适合：审计要求高、需要历史追溯的场景。

**坑 5：忽略投影一致性**

```text
投影是异步的，读模型可能滞后（最终一致）
```

明确一致性要求，关键场景同步投影。

**坑 6：事件存储无乐观锁**

```text
并发修改同一聚合，事件版本冲突没检测
```

事件存储用版本号（乐观锁）防并发冲突。
