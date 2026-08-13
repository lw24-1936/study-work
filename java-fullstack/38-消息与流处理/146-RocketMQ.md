---
title: RocketMQ
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [rocketmq, producer, consumer, topic, tag, 顺序消息, 延迟消息, 事务消息]
---

# RocketMQ

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [核心概念](#核心概念)
- [Producer 与 Consumer](#producer-与-consumer)
- [顺序消息](#顺序消息)
- [延迟消息](#延迟消息)
- [事务消息](#事务消息)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

RocketMQ 是阿里的分布式消息中间件，功能丰富，支持顺序消息、延迟消息、事务消息，是国内电商场景的主流选择。

```text
RocketMQ 的特点：
1. 功能丰富 —— 顺序、延迟、事务消息原生支持
2. 高可靠 —— 同步刷盘、主从复制
3. 高吞吐 —— 十万级 TPS
4. 国产 —— 阿里开源，国内生态好
```

```text
RocketMQ vs Kafka：
RocketMQ —— 功能丰富（顺序/延迟/事务），电商场景
Kafka —— 高吞吐，日志、流处理场景
```

## 核心概念

```text
Producer —— 生产者
Consumer —— 消费者
Broker —— 消息存储节点
NameServer —— 路由中心（类似注册中心）
Topic —— 主题
Tag —— 标签（Topic 下的子分类）
Queue —— 队列（Topic 的分片）
```

```text
RocketMQ 架构：
Producer → NameServer（路由）→ Broker（存储）→ Consumer
```

### Tag 标签

```text
Tag 是 Topic 下的子分类，用于消息过滤：
Topic: order
  Tag: order_create
  Tag: order_pay
  Tag: order_cancel
```

## Producer 与 Consumer

### Producer

```java
DefaultMQProducer producer = new DefaultMQProducer("producer-group");
producer.setNamesrvAddr("localhost:9876");
producer.start();

Message msg = new Message("order", "order_create", "订单创建".getBytes());
SendResult result = producer.send(msg);

producer.shutdown();
```

### Consumer

```java
DefaultMQPushConsumer consumer = new DefaultMQPushConsumer("consumer-group");
consumer.setNamesrvAddr("localhost:9876");
consumer.subscribe("order", "order_create || order_pay");   // 订阅 + tag 过滤

consumer.registerMessageListener((MessageListenerConcurrently) (msgs, context) -> {
    for (MessageExt msg : msgs) {
        System.out.println(new String(msg.getBody()));
    }
    return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
});

consumer.start();
```

### Spring Boot 集成

```xml
<dependency>
    <groupId>org.apache.rocketmq</groupId>
    <artifactId>rocketmq-spring-boot-starter</artifactId>
    <version>2.2.3</version>
</dependency>
```

```java
// 生产者
@Autowired
private RocketMQTemplate rocketMQTemplate;

rocketMQTemplate.convertAndSend("order:order_create", order);   // topic:tag

// 消费者
@RocketMQMessageListener(topic = "order", consumerGroup = "order-group",
    selectorExpression = "order_create")
@Component
public class OrderConsumer implements RocketMQListener<Order> {
    @Override
    public void onMessage(Order order) {
        // 处理消息
    }
}
```

## 顺序消息

顺序消息保证同一类消息的消费顺序。

### 顺序消息的原理

```text
1. 发送时指定消息选择器，同 key 消息进同一队列
2. 队列内消息有序
3. 消费端按队列顺序消费
```

### 发送顺序消息

```java
// 同 orderId 的消息进同一队列（保证顺序）
SendResult result = producer.send(msg, (queues, message, arg) -> {
    Long orderId = (Long) arg;
    int index = (int) (orderId % queues.size());   // 按 orderId 选队列
    return queues.get(index);
}, orderId);
```

### 消费顺序消息

```java
consumer.registerMessageListener((MessageListenerOrderly) (msgs, context) -> {
    for (MessageExt msg : msgs) {
        process(msg);   // 顺序处理
    }
    return ConsumeOrderlyStatus.SUCCESS;
});
```

### 顺序消息的适用场景

```text
1. 订单状态流转 —— 创建 → 支付 → 发货（顺序不能乱）
2. 数据库 binlog 同步 —— 保证操作顺序
```

## 延迟消息

延迟消息在指定时间后才投递。

### 延迟消息的使用

```java
Message msg = new Message("order", "order_close", "关闭订单".getBytes());
msg.setDelayTimeLevel(16);   // 延迟级别（16 = 30 分钟）
producer.send(msg);
```

### 延迟级别

```text
RocketMQ 延迟级别（固定）：
1=1s, 2=5s, 3=10s, 4=30s, 5=1m, 6=2m, 7=3m, 8=4m, 9=5m,
10=6m, 11=7m, 12=8m, 13=9m, 14=10m, 15=20m, 16=30m, 17=1h, 18=2h
```

```text
注意：延迟级别是固定的（18 个级别），
不能指定任意延迟时间（如 7 分钟）
```

### 延迟消息的适用场景

```text
1. 订单超时关闭 —— 下单 30 分钟未支付自动关闭
2. 延迟通知 —— 定时提醒
```

## 事务消息

事务消息保证消息和本地事务的一致性（详见 102-分布式事务）。

### 事务消息流程

```text
1. 发送 half 消息（消费者不可见）
2. 执行本地事务
3. 本地事务成功 → 提交消息（消费者可见）
   本地事务失败 → 回滚消息
4. 超时未确认 → MQ 回查本地事务状态
```

### 事务消息实现

```java
// 发送事务消息
TransactionMQProducer producer = new TransactionMQProducer("tx-producer-group");
producer.setTransactionListener(new TransactionListener() {

    @Override
    public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        // 执行本地事务
        try {
            orderService.createOrder((Order) arg);
            return LocalTransactionState.COMMIT_MESSAGE;   // 提交
        } catch (Exception e) {
            return LocalTransactionState.ROLLBACK_MESSAGE;  // 回滚
        }
    }

    @Override
    public LocalTransactionState checkLocalTransaction(MessageExt msg) {
        // 回查本地事务状态
        Order order = orderService.findById(Long.parseLong(msg.getKeys()));
        return order != null
            ? LocalTransactionState.COMMIT_MESSAGE
            : LocalTransactionState.ROLLBACK_MESSAGE;
    }
});

producer.sendMessageInTransaction(msg, order);
```

### 事务消息的适用场景

```text
1. 订单 + 扣库存 —— 保证两者一致
2. 支付 + 通知 —— 支付成功才发通知
```

## 应用场景实战

### 场景 1：订单超时关闭（延迟消息）

```java
// 下单后发送延迟消息，30 分钟后关闭未支付订单
public void createOrder(Order order) {
    orderMapper.insert(order);

    // 发送延迟消息（30 分钟后检查）
    Message msg = new Message("order", "order_close", order.getId().toString().getBytes());
    msg.setDelayTimeLevel(16);   // 30 分钟
    producer.send(msg);
}

// 消费者：关闭未支付订单
@RocketMQMessageListener(topic = "order", consumerGroup = "order-close",
    selectorExpression = "order_close")
@Component
public class OrderCloseConsumer implements RocketMQListener<String> {
    @Override
    public void onMessage(String orderId) {
        orderService.closeIfUnpaid(Long.parseLong(orderId));
    }
}
```

### 场景 2：订单 + 扣库存（事务消息）

```java
// 下单 + 扣库存保证一致
public void createOrderWithStock(Order order) {
    producer.sendMessageInTransaction(createOrderMessage(order), order);
    // 事务监听器里：本地事务 = 创建订单 + 扣库存
    // 成功 → 提交消息，失败 → 回滚
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **顺序消息用顺序监听器**。MessageListenerOrderly 保证顺序。

2. **延迟消息注意级别限制**。只有 18 个固定级别，不能任意延迟。

3. **事务消息回查要准确**。回查逻辑错误导致消息错投。

4. **消费要幂等**。RocketMQ 可能重复投递。

5. **监控消费 lag**。堆积及时处理。

### 踩坑记录

**坑 1：延迟时间不是任意的**

```java
msg.setDelayTimeLevel(16);   // 只有 18 个固定级别
// 想延迟 7 分钟，但没有这个级别
```

延迟级别固定，任意延迟用定时任务或自定义方案。

**坑 2：顺序消息用并发监听器**

```java
// 顺序消息用 MessageListenerConcurrently（并发），顺序被打乱
```

顺序消息必须用 MessageListenerOrderly。

**坑 3：事务消息回查逻辑错误**

```java
// 本地事务已提交，但回查返回 ROLLBACK，消息没发出，数据不一致
```

回查逻辑要准确判断本地事务状态。

**坑 4：NameServer 地址错误**

```java
producer.setNamesrvAddr("localhost:9876");   // 地址错误，连不上
```

NameServer 默认端口 9876，确认地址正确。

**坑 5：消费组和订阅关系不一致**

```text
同一个消费组内，订阅的 topic/tag 不一致，可能消费错乱
```

同一消费组内订阅关系要一致。

**坑 6：消息堆积不处理**

```text
消费慢导致堆积，消息延迟，影响业务
```

监控堆积，扩容消费者或优化处理逻辑。
