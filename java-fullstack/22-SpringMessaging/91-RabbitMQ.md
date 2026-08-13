---
title: RabbitMQ
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [rabbitmq, exchange, queue, binding, direct, topic, fanout, ack, dead-letter, ttl, retry]
---

# RabbitMQ

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [核心概念：Exchange/Queue/Binding](#核心概念exchangequeuebinding)
- [四种交换机](#四种交换机)
- [消息确认 ACK/NACK](#消息确认-acknack)
- [死信队列 Dead Letter](#死信队列-dead-letter)
- [消息 TTL](#消息-ttl)
- [消息重试 Retry](#消息重试-retry)
- [可靠性投递](#可靠性投递)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

RabbitMQ 是基于 AMQP（Advanced Message Queuing Protocol）协议的开源消息中间件，以可靠、灵活、低延迟著称。

```text
RabbitMQ 特点：
1. AMQP 协议 —— 标准、成熟
2. 灵活路由 —— 四种交换机，灵活的消息路由
3. 可靠性高 —— 消息确认、持久化、死信队列
4. 低延迟 —— 微秒级，适合业务消息

适用场景：
业务解耦、异步处理、流量削峰、RPC 调用
```

## 核心概念：Exchange/Queue/Binding

RabbitMQ 的消息模型基于三个核心概念。

### 消息流转

```text
生产者 → Exchange（交换机）→ Binding（绑定）→ Queue（队列）→ 消费者
```

```text
关键理解：
1. 生产者不发消息到队列，而是发到 Exchange
2. Exchange 根据 Routing Key 和绑定规则，把消息路由到 Queue
3. 消费者从 Queue 消费消息
```

### 三个核心组件

| 组件 | 说明 |
|------|------|
| Exchange（交换机） | 接收消息，按规则路由到队列 |
| Queue（队列） | 存储消息，消费者从队列取 |
| Binding（绑定） | Exchange 和 Queue 之间的路由规则 |

### Routing Key

```text
Routing Key 是消息路由的关键：
1. 生产者发送消息时指定 Routing Key
2. Binding 定义了 Exchange 到 Queue 的路由规则（绑定键）
3. Exchange 根据 Routing Key 匹配绑定键，决定投递到哪个队列
```

## 四种交换机

### 1. Direct Exchange（直连交换机）

按 Routing Key 精确匹配。

```text
Binding: queue1 ←→ routingKey="error"
        queue2 ←→ routingKey="info"

消息 routingKey="error" → queue1
消息 routingKey="info"  → queue2
消息 routingKey="warn"  → 丢弃（无匹配）
```

```java
@Configuration
public class DirectConfig {
    @Bean
    public DirectExchange directExchange() {
        return new DirectExchange("log.direct");
    }

    @Bean
    public Queue errorQueue() {
        return new Queue("error.queue");
    }

    @Bean
    public Binding errorBinding() {
        return BindingBuilder.bind(errorQueue())
            .to(directExchange())
            .with("error");   // routing key
    }
}
```

### 2. Topic Exchange（主题交换机）

按 Routing Key 模式匹配（支持通配符 `*` 和 `#`）。

```text
通配符：
*  —— 匹配一个词
#  —— 匹配零个或多个词

Binding: queue1 ←→ "order.*"     （匹配 order.create、order.pay）
        queue2 ←→ "order.#"     （匹配 order 开头的所有）
        queue3 ←→ "*.error"     （匹配 user.error、order.error）
```

```java
@Bean
public TopicExchange topicExchange() {
    return new TopicExchange("order.topic");
}

@Bean
public Binding orderCreateBinding() {
    return BindingBuilder.bind(orderCreateQueue())
        .to(topicExchange())
        .with("order.create");   // 匹配 order.create
}

@Bean
public Binding orderAllBinding() {
    return BindingBuilder.bind(orderAllQueue())
        .to(topicExchange())
        .with("order.#");        // 匹配所有 order.*
}
```

### 3. Fanout Exchange（广播交换机）

忽略 Routing Key，广播到所有绑定的队列。

```text
Binding: queue1 ←→ fanout
        queue2 ←→ fanout
        queue3 ←→ fanout

消息 → 同时投递到 queue1、queue2、queue3
```

```java
@Bean
public FanoutExchange fanoutExchange() {
    return new FanoutExchange("broadcast.fanout");
}
```

典型场景：一条消息多个系统都要处理（如订单创建后，短信、库存、统计都要收到）。

### 4. Headers Exchange（头交换机）

按消息头匹配（不使用 Routing Key），已很少使用。

```java
@Bean
public HeadersExchange headersExchange() {
    return new HeadersExchange("header.exchange");
}
```

### 四种交换机对比

| 交换机 | 路由规则 | 适用场景 |
|--------|---------|---------|
| Direct | Routing Key 精确匹配 | 精确路由 |
| Topic | Routing Key 模式匹配（* #） | 灵活路由 |
| Fanout | 广播到所有队列 | 一对多广播 |
| Headers | 消息头匹配 | 特殊场景（少用） |

## 消息确认 ACK/NACK

消息确认保证消息被可靠消费。

### 确认模式

```yaml
spring:
  rabbitmq:
    listener:
      simple:
        acknowledge-mode: auto   # auto（默认）/ manual / none
```

| 模式 | 说明 |
|------|------|
| none | 不确认，消息自动 ACK |
| auto | 框架自动确认（正常返回 ACK，异常 NACK） |
| manual | 手动确认（最可控） |

### 手动 ACK

```java
@Component
public class ManualAckConsumer {

    @RabbitListener(queues = "order.queue", ackMode = "MANUAL")
    public void handle(Order order, Channel channel,
                       @Header(AmqpHeaders.DELIVERY_TAG) long deliveryTag) throws IOException {
        try {
            orderService.process(order);
            // 处理成功，确认
            channel.basicAck(deliveryTag, false);
        } catch (Exception e) {
            // 处理失败，拒绝（重新入队）
            channel.basicNack(deliveryTag, false, true);
            // 或拒绝（不重新入队，进入死信）
            // channel.basicNack(deliveryTag, false, false);
        }
    }
}
```

### ACK 的三个方法

```java
channel.basicAck(deliveryTag, multiple);    // 确认
channel.basicNack(deliveryTag, multiple, requeue);  // 拒绝（可重入队）
channel.basicReject(deliveryTag, requeue);  // 拒绝单个（不批量）
```

## 死信队列 Dead Letter

死信队列（DLX）用于处理无法正常消费的消息。

### 什么消息会进入死信

```text
1. 消息被拒绝（basicNack/basicReject 且 requeue=false）
2. 消息过期（TTL 到期）
3. 队列达到最大长度
```

### 配置死信队列

```java
@Configuration
public class DeadLetterConfig {

    // 业务队列（绑定死信交换机）
    @Bean
    public Queue orderQueue() {
        return QueueBuilder.durable("order.queue")
            .deadLetterExchange("dead.letter.exchange")   // 死信交换机
            .deadLetterRoutingKey("order.dead")           // 死信路由键
            .build();
    }

    // 死信交换机
    @Bean
    public DirectExchange deadLetterExchange() {
        return new DirectExchange("dead.letter.exchange");
    }

    // 死信队列
    @Bean
    public Queue deadLetterQueue() {
        return new Queue("dead.letter.queue");
    }

    @Bean
    public Binding deadLetterBinding() {
        return BindingBuilder.bind(deadLetterQueue())
            .to(deadLetterExchange())
            .with("order.dead");
    }
}
```

### 死信队列的用途

```text
1. 收集失败消息，人工介入处理
2. 延迟队列（消息 TTL + 死信队列实现）
3. 告警（消费异常堆积时告警）
```

### 延迟队列（TTL + 死信实现）

```text
延迟队列原理：
消息发送到延迟队列（设置 TTL，无消费者）
→ 消息过期 → 进入死信队列
→ 消费者监听死信队列 → 实现延迟消费
```

## 消息 TTL

TTL（Time To Live）是消息的存活时间。

### 队列级别 TTL

```java
// 队列中所有消息统一 TTL
@Bean
public Queue ttlQueue() {
    return QueueBuilder.durable("ttl.queue")
        .ttl(10_000)  // 10 秒过期
        .build();
}
```

### 消息级别 TTL

```java
// 单条消息设置 TTL
rabbitTemplate.convertAndSend("exchange", "routingKey", message, msg -> {
    msg.getMessageProperties().setExpiration("10000");  // 10 秒
    return msg;
});
```

## 消息重试 Retry

消费失败时的重试机制。

### 配置重试

```yaml
spring:
  rabbitmq:
    listener:
      simple:
        retry:
          enabled: true
          max-attempts: 3           # 最大重试次数
          initial-interval: 1000ms  # 初始间隔
          multiplier: 2             # 间隔倍增
          max-interval: 10000ms     # 最大间隔
```

### 重试 + 死信组合

```text
最佳实践：
1. 消费失败 → 自动重试（如 3 次）
2. 重试仍失败 → 拒绝并进入死信队列
3. 死信队列人工处理或告警
```

```java
@Component
public class RetryConsumer {

    @RabbitListener(queues = "order.queue")
    public void handle(Order order, Channel channel,
                       @Header(AmqpHeaders.DELIVERY_TAG) long deliveryTag) throws IOException {
        try {
            orderService.process(order);
            channel.basicAck(deliveryTag, false);
        } catch (Exception e) {
            // 失败，重试耗尽后进入死信
            channel.basicNack(deliveryTag, false, false);  // 不重入队，进死信
        }
    }
}
```

## 可靠性投递

保证消息可靠投递的完整方案。

### 生产者可靠性

```yaml
spring:
  rabbitmq:
    publisher-confirm-type: correlated  # 开启发送确认
    publisher-returns: true             # 开启路由失败返回
```

```java
@Configuration
public class RabbitConfig {

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory factory) {
        RabbitTemplate template = new RabbitTemplate(factory);

        // 发送确认回调
        template.setConfirmCallback((correlationData, ack, cause) -> {
            if (ack) {
                log.info("消息发送成功：{}", correlationData.getId());
            } else {
                log.error("消息发送失败：{}", cause);
                // 失败补偿
            }
        });

        // 路由失败回调
        template.setReturnsCallback(returned -> {
            log.error("消息路由失败：{}", returned.getMessage());
        });

        return template;
    }
}
```

### 可靠性三要素

```text
1. 发送确认（Confirm）—— 消息到达 Exchange
2. 路由确认（Return）—— 消息路由到 Queue
3. 持久化 —— Exchange、Queue、消息都持久化
```

### 完整可靠性方案

```text
业务端：本地消息表 + 定时重发
生产者：Confirm + Return 回调
消息：持久化 + TTL
消费者：手动 ACK + 重试 + 死信队列
```

## 应用场景实战

### 场景 1：订单延迟关闭（TTL + 死信）

```java
@Configuration
public class DelayConfig {

    // 延迟队列（TTL 30 分钟，无消费者）
    @Bean
    public Queue orderDelayQueue() {
        return QueueBuilder.durable("order.delay.queue")
            .ttl(30 * 60 * 1000)                       // 30 分钟
            .deadLetterExchange("order.exchange")       // 过期后进入死信交换机
            .deadLetterRoutingKey("order.close")        // 路由键
            .build();
    }

    // 延迟交换机
    @Bean
    public DirectExchange orderDelayExchange() {
        return new DirectExchange("order.delay.exchange");
    }

    @Bean
    public Binding orderDelayBinding() {
        return BindingBuilder.bind(orderDelayQueue())
            .to(orderDelayExchange())
            .with("order.delay");
    }
}
```

```java
// 下单时发送延迟消息
@Service
public class OrderService {
    public void createOrder(Order order) {
        orderMapper.insert(order);
        // 30 分钟后检查订单是否支付，未支付则关闭
        rabbitTemplate.convertAndSend("order.delay.exchange", "order.delay", order.getId());
    }
}

// 监听关闭订单
@Component
public class OrderCloseConsumer {
    @RabbitListener(queues = "order.close.queue")
    public void closeOrder(Long orderId) {
        // 检查订单状态，未支付则关闭
        orderService.closeIfUnpaid(orderId);
    }
}
```

### 场景 2：订单创建广播（Fanout）

```java
@Configuration
public class FanoutConfig {
    @Bean
    public FanoutExchange orderFanout() {
        return new FanoutExchange("order.fanout");
    }

    @Bean
    public Queue smsQueue() { return new Queue("sms.queue"); }
    @Bean
    public Queue inventoryQueue() { return new Queue("inventory.queue"); }
    @Bean
    public Queue statisticsQueue() { return new Queue("statistics.queue"); }

    @Bean
    public Binding smsBinding() {
        return BindingBuilder.bind(smsQueue()).to(orderFanout());
    }
    @Bean
    public Binding inventoryBinding() {
        return BindingBuilder.bind(inventoryQueue()).to(orderFanout());
    }
    @Bean
    public Binding statisticsBinding() {
        return BindingBuilder.bind(statisticsQueue()).to(orderFanout());
    }
}
```

### 场景 3：消息失败重试 + 死信处理

```yaml
spring:
  rabbitmq:
    listener:
      simple:
        retry:
          enabled: true
          max-attempts: 3
          initial-interval: 1000ms
          multiplier: 2
```

```java
// 死信队列消费（告警 + 人工处理）
@Component
public class DeadLetterConsumer {

    @RabbitListener(queues = "dead.letter.queue")
    public void handle(Message message) {
        // 记录失败消息，发送告警
        String body = new String(message.getBody());
        log.error("消息最终处理失败：{}", body);
        alertService.send("消息处理失败：" + body);
        // 持久化到数据库，人工处理
        failedMessageRepository.save(new FailedMessage(body));
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **消息、队列、交换机都持久化**。`durable(true)`，防止 RabbitMQ 重启丢消息。

2. **消费失败要重试 + 死信**。不能简单丢弃，也不能无限重试。

3. **生产者开启 Confirm**。保证消息真的到达了 Exchange。

4. **消费者要幂等**。RabbitMQ 可能重复投递。

5. **路由键用点号分层**。`order.created`、`order.paid`，配合 Topic 交换机灵活路由。

### 踩坑记录

**坑 1：队列和交换机参数不一致**

```java
// 已有队列 order.queue 是 durable 的，代码改成非 durable
// 启动报错：PRECONDITION_FAILED - inequivalent arg 'durable'
```

已存在的队列/交换机，修改参数会导致冲突。要么删掉重建，要么保持一致。

**坑 2：auto ack 模式下异常吞掉消息**

```java
@RabbitListener(queues = "order.queue")
public void handle(Order order) {
    try {
        orderService.process(order);
    } catch (Exception e) {
        log.error("失败", e);  // auto ack 模式下，异常被吞，消息已 ACK，实际没处理成功
    }
}
```

auto ack 模式下不要 try-catch 吞异常，让异常抛出触发 NACK 和重试。

**坑 3：basicNack 的 requeue 参数误解**

```java
channel.basicNack(deliveryTag, false, true);   // requeue=true：立即重新入队
// 如果消费一直失败，消息会无限循环重试（requeue 没有次数限制）
channel.basicNack(deliveryTag, false, false);  // requeue=false：进入死信（配合死信队列）
```

requeue=true 会无限重试（没有重试次数限制），要配合重试次数或死信队列。

**坑 4：延迟队列的 TTL 队列级 vs 消息级**

```java
// 队列级 TTL：队列中所有消息统一过期时间，只能有一个固定延迟
// 消息级 TTL：不同消息可以不同延迟，但队列已就绪的消息可能被"插队"
```

需要多种延迟时用消息级 TTL 或 RabbitMQ 的延迟插件（rabbitmq_delayed_message_exchange）。

**坑 5：连接配置错误**

```yaml
spring:
  rabbitmq:
    host: localhost
    port: 5672      # AMQP 端口
    # 不是 15672（管理界面端口）
```

5672 是 AMQP 协议端口，15672 是管理界面端口，不要混淆。

**坑 6：生产者发消息没持久化**

```java
// 消息默认是持久化的，但如果手动设置 deliveryMode=1（非持久化）
// RabbitMQ 重启后消息丢失
message.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
```

确保 deliveryMode=PERSISTENT（默认即是），且 Exchange 和 Queue 都 durable。
