---
title: Spring Boot 集成 RabbitMQ 详解
created: 2026-08-10
updated: 2026-08-10
type: integration
tags: [spring-boot, rabbitmq, message-queue, distributed]
---

> 整理日期：2026-08-10

## 目录

1. [概述](#1-概述)
2. [核心概念](#2-核心概念)
3. [环境搭建](#3-环境搭建)
4. [交换机类型](#4-交换机类型)
5. [消息发送](#5-消息发送)
6. [消息接收](#6-消息接收)
7. [消息序列化](#7-消息序列化)
8. [消息可靠性](#8-消息可靠性)
9. [死信队列](#9-死信队列)
10. [延迟消息](#10-延迟消息)
11. [消息幂等](#11-消息幂等)
12. [应用场景实战](#12-应用场景实战)
13. [最佳实践与踩坑记录](#13-最佳实践与踩坑记录)
14. [参考链接](#14-参考链接)

---

## 1. 概述

### 1.1 RabbitMQ 是什么

RabbitMQ 是一个基于 AMQP（Advanced Message Queuing Protocol）协议的消息中间件，Erlang 编写。核心能力：**生产者发消息，消费者收消息，两者解耦**。

和 Kafka、RocketMQ 的区别一句话：RabbitMQ 偏重灵活路由和可靠投递，不追求高吞吐顺序日志。

### 1.2 适用场景

| 场景 | 说明 |
|------|------|
| 异步解耦 | 下单后发消息通知物流，不阻塞主流程 |
| 削峰填谷 | 秒杀请求先进队列，后端慢慢消费 |
| 延迟任务 | 订单 30 分钟未支付自动取消 |
| 广播通知 | 配置变更后通知所有服务实例刷新 |
| 日志收集 | 各服务日志统一发送到日志中心 |

### 1.3 和 Kafka 的主要区别

| 维度 | RabbitMQ | Kafka |
|------|----------|-------|
| 协议 | AMQP 0-9-1 | 自定义 TCP 协议 |
| 吞吐 | 万级/秒 | 百万级/秒 |
| 消息回溯 | 消费完即删除（或手动删除） | 按时间/offset 回溯 |
| 路由灵活性 | 4 种 Exchange + Binding Key | 固定 Topic 分区 |
| 延迟消息 | 死信队列 / 插件 | 原生不支持（需外部实现） |
| 适用 | 业务异步、可靠投递、复杂路由 | 大数据流、日志、事件溯源 |

---

## 2. 核心概念

在写代码之前，先搞清楚 AMQP 的几个概念：

```
Producer -> Exchange -> [Binding] -> Queue -> Consumer
                |
           Routing Key
```

| 概念 | 说明 |
|------|------|
| Producer | 消息发送方，把消息发给 Exchange |
| Exchange | 交换机，根据 Routing Key 将消息路由到 Queue |
| Queue | 消息队列，存储消息直到被消费 |
| Consumer | 消息消费方，从 Queue 获取消息 |
| Binding | Exchange 和 Queue 的绑定关系，带 Binding Key |
| Routing Key | 消息发送时指定，Exchange 用它决定路由到哪个 Queue |
| Virtual Host | 虚拟主机，隔离不同应用的消息（权限、资源独立） |

**一个常见的理解误区**：消息不是直接发到 Queue 的，是 Producer -> Exchange -> Queue。Exchange 才是消息的入口。

---

## 3. 环境搭建

### 3.1 启动 RabbitMQ（Docker）

```bash
docker run -d \
  --name rabbitmq \
  -p 5672:5672 \       # AMQP 协议端口
  -p 15672:15672 \     # 管理后台端口
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=admin \
  rabbitmq:3.12-management
```

访问 `http://localhost:15672`，账号 admin/admin。

### 3.2 依赖引入

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-amqp</artifactId>
</dependency>
```

不要同时引入 `spring-rabbit`，`spring-boot-starter-amqp` 已包含 Spring AMQP 全家桶。

### 3.3 application.yml 配置

```yaml
spring:
  rabbitmq:
    host: localhost                     # 服务器地址
    port: 5672                          # AMQP 端口
    username: admin                     # 账号
    password: admin                     # 密码
    virtual-host: /                     # 虚拟主机（默认 /）
    # 连接池（可选）
    requested-heartbeat: 60s            # 心跳间隔
    connection-timeout: 30s             # 连接超时
    # 生产者确认（可靠性配置，后面章节详讲）
    publisher-confirm-type: correlated  # 发布确认模式: none / correlated / simple
    publisher-returns: true             # 开启 Return 回调（消息无法路由时回调）
    # 消费者配置
    listener:
      simple:
        acknowledge-mode: manual        # 手动确认（默认 auto）
        prefetch: 1                     # 每次抓取 1 条（公平调度，避免消费者忙闲不均）
        concurrency: 3                  # 并发消费者数量
        max-concurrency: 10             # 最大消费者数量
        retry:
          enabled: true                 # 开启重试
          max-attempts: 3               # 最大重试次数
          initial-interval: 3000ms      # 初始重试间隔
          multiplier: 2                 # 间隔倍数（逐次翻倍）
          max-interval: 10000ms         # 最大间隔
```

### 3.4 启动类（无需额外注解）

```java
@SpringBootApplication
public class RabbitMqApplication {
    public static void main(String[] args) {
        SpringApplication.run(RabbitMqApplication.class, args);
    }
}
```

Spring Boot 自动配置了 `ConnectionFactory`、`RabbitTemplate`、`RabbitListenerContainerFactory` 等 Bean，无需手动声明。

---

## 4. 交换机类型

RabbitMQ 有 4 种 Exchange，每种的路由规则不同。

### 4.1 Direct Exchange（直连）

**精确匹配 Routing Key**。最常用的类型。

```java
@Configuration
public class DirectExchangeConfig {

    public static final String QUEUE_EMAIL = "queue.email";
    public static final String QUEUE_SMS   = "queue.sms";
    public static final String EXCHANGE    = "exchange.direct.notify";
    public static final String ROUTING_EMAIL = "email";
    public static final String ROUTING_SMS   = "sms";

    @Bean
    public DirectExchange directExchange() {
        return new DirectExchange(EXCHANGE);
    }

    @Bean
    public Queue queueEmail() {
        // durable: 持久化（服务重启后队列还在）
        return QueueBuilder.durable(QUEUE_EMAIL).build();
    }

    @Bean
    public Queue queueSms() {
        return QueueBuilder.durable(QUEUE_SMS).build();
    }

    // 将队列绑定到交换机，指定 Routing Key
    @Bean
    public Binding bindingEmail(Queue queueEmail, DirectExchange directExchange) {
        return BindingBuilder.bind(queueEmail).to(directExchange).with(ROUTING_EMAIL);
    }

    @Bean
    public Binding bindingSms(Queue queueSms, DirectExchange directExchange) {
        return BindingBuilder.bind(queueSms).to(directExchange).with(ROUTING_SMS);
    }
}
```

路由规则：Routing Key 为 `email` 的消息只进 `queue.email`，Routing Key 为 `sms` 的只进 `queue.sms`。

### 4.2 Fanout Exchange（广播）

**忽略 Routing Key，消息广播到所有绑定的 Queue**。适合配置刷新、全局通知。

```java
@Configuration
public class FanoutExchangeConfig {

    public static final String QUEUE_A = "queue.fanout.a";
    public static final String QUEUE_B = "queue.fanout.b";
    public static final String EXCHANGE = "exchange.fanout.notify";

    @Bean
    public FanoutExchange fanoutExchange() {
        return new FanoutExchange(EXCHANGE);
    }

    @Bean
    public Queue queueFanoutA() {
        return QueueBuilder.durable(QUEUE_A).build();
    }

    @Bean
    public Queue queueFanoutB() {
        return QueueBuilder.durable(QUEUE_B).build();
    }

    @Bean
    public Binding bindingA(Queue queueFanoutA, FanoutExchange fanoutExchange) {
        return BindingBuilder.bind(queueFanoutA).to(fanoutExchange);
    }

    @Bean
    public Binding bindingB(Queue queueFanoutB, FanoutExchange fanoutExchange) {
        return BindingBuilder.bind(queueFanoutB).to(fanoutExchange);
    }
}
```

注意：Fanout 的 Binding 不需要 `.with()`，因为 Routing Key 被忽略。

### 4.3 Topic Exchange（通配符）

**Routing Key 支持通配符 `*`（匹配一个词）和 `#`（匹配零个或多个词）**。词之间用 `.` 分隔。

```java
@Configuration
public class TopicExchangeConfig {

    public static final String QUEUE_LOG_ALL    = "queue.log.all";
    public static final String QUEUE_LOG_ERROR  = "queue.log.error";
    public static final String EXCHANGE = "exchange.topic.log";

    @Bean
    public TopicExchange topicExchange() {
        return new TopicExchange(EXCHANGE);
    }

    @Bean
    public Queue queueLogAll() {
        return QueueBuilder.durable(QUEUE_LOG_ALL).build();
    }

    @Bean
    public Queue queueLogError() {
        return QueueBuilder.durable(QUEUE_LOG_ERROR).build();
    }

    // 接收所有日志
    @Bean
    public Binding bindingAll(Queue queueLogAll, TopicExchange topicExchange) {
        return BindingBuilder.bind(queueLogAll).to(topicExchange).with("log.#");
    }

    // 只接收错误日志
    @Bean
    public Binding bindingError(Queue queueLogError, TopicExchange topicExchange) {
        return BindingBuilder.bind(queueLogError).to(topicExchange).with("log.error.*");
    }
}
```

路由示例：

| Routing Key | 匹配 `log.#` | 匹配 `log.error.*` |
|-------------|:--:|:--:|
| `log.info.order` | yes | no |
| `log.error.payment` | yes | yes |
| `log.error` | yes | no（`*` 必须匹配一个词） |

### 4.4 Headers Exchange（头匹配）

根据消息的 Header 属性匹配，不用 Routing Key。用 `whereAny`（或）、`whereAll`（且）指定匹配策略。使用场景极少，大多数情况 Topic 就够了。

```java
@Bean
public HeadersExchange headersExchange() {
    return new HeadersExchange("exchange.headers");
}

@Bean
public Binding bindingHeaders(Queue queue, HeadersExchange exchange) {
    return BindingBuilder.bind(queue).to(exchange)
            .whereAll("format", "pdf")  // 所有 Header 都匹配才路由
            .match();
}
```

### 4.5 四种交换机对比

| 类型 | 路由依据 | 使用场景 |
|------|---------|----------|
| Direct | Routing Key 精确匹配 | 点对点消息，不同通知类型不同队列 |
| Fanout | 忽略 Key，全广播 | 配置刷新广播、服务间通知 |
| Topic | Routing Key 通配符匹配 | 日志分级、事件分类 |
| Headers | Header 属性匹配 | 特殊场景，极少用 |

---

## 5. 消息发送

### 5.1 RabbitTemplate 基础发送

```java
@SpringBootTest
class RabbitSendTest {

    @Autowired
    private RabbitTemplate rabbitTemplate;

    // 方式一：发到默认 Exchange（Routing Key = Queue 名称）
    @Test
    void sendToQueue() {
        rabbitTemplate.convertAndSend("queue.email", "发送到指定队列");
    }

    // 方式二：发到指定 Exchange + Routing Key
    @Test
    void sendToExchange() {
        rabbitTemplate.convertAndSend("exchange.direct.notify", "email", "邮件通知内容");
    }

    // 方式三：发送对象（自动序列化为 JSON，需配置 MessageConverter）
    @Test
    void sendObject() {
        NotifyMessage msg = new NotifyMessage();
        msg.setUserId(1001L);
        msg.setTitle("订单通知");
        msg.setContent("您的订单已发货");
        rabbitTemplate.convertAndSend("exchange.direct.notify", "email", msg);
    }
}
```

### 5.2 Message 对象发送

直接构建 Spring AMQP 的 Message 对象，控制更多细节：

```java
@Test
void sendMessage() {
    // 消息体
    byte[] body = "自定义消息体".getBytes(StandardCharsets.UTF_8);

    // 消息属性
    MessageProperties props = new MessageProperties();
    props.setDeliveryMode(MessageDeliveryMode.PERSISTENT);  // 持久化
    props.setExpiration("60000");                           // 过期时间 60 秒
    props.setHeader("source", "order-service");             // 自定义 Header
    props.setContentType(MessageProperties.CONTENT_TYPE_JSON);

    Message message = new Message(body, props);
    rabbitTemplate.send("exchange.direct.notify", "email", message);
}
```

### 5.3 消息后处理器

发送前统一修改消息属性（如添加 Trace ID）：

```java
rabbitTemplate.convertAndSend("exchange.direct.notify", "email", data, message -> {
    MessageProperties props = message.getMessageProperties();
    // 给每条消息打上 Trace ID，便于链路追踪
    props.setHeader("traceId", MDC.get("traceId"));
    props.setHeader("timestamp", System.currentTimeMillis());
    return message;
});
```

### 5.4 延迟发送

RabbitMQ 原生不支持延迟投递。需要安装 `rabbitmq_delayed_message_exchange` 插件或者用死信队列模拟。用插件的方式见第 10 节。

---

## 6. 消息接收

### 6.1 @RabbitListener 基础用法

```java
@Component
public class EmailConsumer {

    // 监听指定队列
    @RabbitListener(queues = "queue.email")
    public void handleEmail(String message) {
        System.out.println("收到邮件通知: " + message);
    }

    // 接收对象（需配置 JSON 反序列化）
    @RabbitListener(queues = "queue.email")
    public void handleEmailObject(NotifyMessage message) {
        System.out.println("收到: " + message.getTitle());
    }

    // 接收完整 Message 对象（包含 Headers 等元信息）
    @RabbitListener(queues = "queue.email")
    public void handleEmailFull(Message message, Channel channel) {
        System.out.println("消息头: " + message.getMessageProperties());
        System.out.println("消息体: " + new String(message.getBody()));
    }
}
```

### 6.2 @RabbitListener + @RabbitHandler

一个类监听同一个 Queue，但根据消息类型分发到不同方法：

```java
@Component
@RabbitListener(queues = "queue.order")
public class OrderConsumer {

    @RabbitHandler
    public void handleCreateEvent(OrderCreateEvent event) {
        System.out.println("处理创建事件: " + event.getOrderId());
    }

    @RabbitHandler
    public void handleCancelEvent(OrderCancelEvent event) {
        System.out.println("处理取消事件: " + event.getOrderId());
    }

    // 当消息类型无法匹配时，走默认处理方法
    @RabbitHandler(isDefault = true)
    public void handleDefault(Object message) {
        System.out.println("未知消息类型: " + message.getClass().getName());
    }
}
```

通过 Content-Type Header 区分类型。发送时指定：

```java
rabbitTemplate.convertAndSend("exchange.order", "order.create", event, msg -> {
    msg.getMessageProperties().setHeader("__TypeId__", "com.example.event.OrderCreateEvent");
    return msg;
});
```

### 6.3 手动确认（Manual Ack）

配置了 `acknowledge-mode: manual` 后，消费者必须显式 ack/nack：

```java
@Component
public class ManualAckConsumer {

    @RabbitListener(queues = "queue.important")
    public void handle(String message, Channel channel, @Header(AmqpHeaders.DELIVERY_TAG) long tag) {
        try {
            // 业务处理
            doBusinessLogic(message);

            // 手动确认（tag: 投递标签, multiple: 是否批量确认之前的）
            channel.basicAck(tag, false);

        } catch (Exception e) {
            try {
                // requeue=true: 重新入队；false: 丢弃或进死信
                channel.basicNack(tag, false, false);
            } catch (IOException ioException) {
                log.error("nack 失败", ioException);
            }
        }
    }
}
```

**Ack 三种操作对比：**

| 操作 | 方法 | 效果 |
|------|------|------|
| basicAck | `channel.basicAck(tag, false)` | 确认消费，从队列删除 |
| basicNack | `channel.basicNack(tag, false, true)` | 拒绝，重新入队 |
| basicNack | `channel.basicNack(tag, false, false)` | 拒绝，不进死信则丢弃 |
| basicReject | `channel.basicReject(tag, false)` | 拒绝单条（和 nack 类似，不支持批量） |

### 6.4 并发消费

```yaml
spring:
  rabbitmq:
    listener:
      simple:
        concurrency: 5           # 启动 5 个消费者线程
        max-concurrency: 10      # 最大 10 个
        prefetch: 1              # 每个消费者一次只抓 1 条（公平分发）
```

无限制地提高并发不等同于高性能——瓶颈在数据库 IO 的话，再多线程也白搭。

### 6.5 消费重试

```yaml
spring:
  rabbitmq:
    listener:
      simple:
        retry:
          enabled: true
          max-attempts: 3                     # 重试 3 次
          initial-interval: 3000ms            # 第 1 次重试等 3 秒
          multiplier: 2                       # 第 2 次等 6 秒，第 3 次等 12 秒
          max-interval: 10000ms               # 单次最大等 10 秒
```

重试 3 次后仍然失败的消息会被丢弃或进入死信队列（前提是你配了死信）。建议所有核心业务队列都配死信，否则异常消息直接丢了。

---

## 7. 消息序列化

### 7.1 为什么需要改序列化

Spring AMQP 默认使用 `SimpleMessageConverter` / JDK 序列化。问题：
- 二进制不可读，RabbitMQ 管理后台看是乱码
- Java 反序列化有安全风险
- 跨语言消费者无法解析

生产环境统一用 JSON。

### 7.2 配置 JSON 序列化

```java
@Configuration
public class RabbitMqConfig {

    @Bean
    public MessageConverter messageConverter() {
        // Spring AMQP 内置的 Jackson 转换器
        Jackson2JsonMessageConverter converter = new Jackson2JsonMessageConverter();
        // 发送消息时自动将 Java 类型写入 __TypeId__ header，消费时靠它找对应的类
        return converter;
    }

    // 如果要自定义 Jackson ObjectMapper
    @Bean
    public MessageConverter messageConverter(ObjectMapper objectMapper) {
        objectMapper.registerModule(new JavaTimeModule());   // 支持 LocalDateTime
        objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        objectMapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE); // 字段蛇形转换

        Jackson2JsonMessageConverter converter = new Jackson2JsonMessageConverter(objectMapper);
        // 信任所有包（允许反序列化任何类），生产环境建议限制包名
        converter.setClassMapper(new DefaultJackson2JavaTypeMapper());

        return converter;
    }
}
```

### 7.3 TypeId 配置

默认 `__TypeId__` 是全限定类名。如果你嫌太长或不想暴露类名，自定义映射：

```java
Jackson2JsonMessageConverter converter = new Jackson2JsonMessageConverter();
DefaultJackson2JavaTypeMapper typeMapper = new DefaultJackson2JavaTypeMapper();

Map<String, Class<?>> mappings = new HashMap<>();
mappings.put("notify", NotifyMessage.class);
mappings.put("orderEvent", OrderCreateEvent.class);
typeMapper.setIdClassMapping(mappings);

converter.setClassMapper(typeMapper);
```

发送时手动指定 TypeId：

```java
rabbitTemplate.convertAndSend(exchange, routingKey, message, msg -> {
    msg.getMessageProperties().setHeader("__TypeId__", "notify");
    return msg;
});
```

---

## 8. 消息可靠性

消息从发送到消费的全程，有三个环节可能丢失：

```
Producer --[确认]--> Broker --[持久化]--> Broker --[确认]--> Consumer
```

### 8.1 生产者确认（Publisher Confirm）

防止消息根本没到 Broker：

```yaml
spring:
  rabbitmq:
    publisher-confirm-type: correlated   # 开启发布确认
    publisher-returns: true              # 开启 Return 回调（消息无法路由时）
```

```java
@Component
public class RabbitConfirmCallback implements RabbitTemplate.ConfirmCallback {

    @Override
    public void confirm(CorrelationData correlationData, boolean ack, String cause) {
        String msgId = correlationData != null ? correlationData.getId() : "unknown";
        if (ack) {
            log.info("消息已到达 Broker, msgId={}", msgId);
        } else {
            log.error("消息发送失败, msgId={}, cause={}", msgId, cause);
            // 重试或落库补救
        }
    }
}

@Component
public class RabbitReturnCallback implements RabbitTemplate.ReturnsCallback {

    @Override
    public void returnedMessage(ReturnedMessage returned) {
        // 消息到了 Exchange 但没有任何 Queue 匹配
        log.error("消息被退回: exchange={}, routingKey={}, replyText={}",
                returned.getExchange(),
                returned.getRoutingKey(),
                returned.getReplyText());
    }
}

// 注册回调
@PostConstruct
public void init() {
    rabbitTemplate.setConfirmCallback(confirmCallback);
    rabbitTemplate.setReturnsCallback(returnCallback);
}
```

发送时携带 CorrelationData，方便回调时定位：

```java
CorrelationData data = new CorrelationData(UUID.randomUUID().toString());
rabbitTemplate.convertAndSend("exchange", "key", message, data);
```

### 8.2 消息持久化

防 Broker 重启丢消息，两个条件缺一不可：

```java
// 1. 队列声明为 durable
QueueBuilder.durable("queue.name").build();

// 2. 消息标记为 persistent
message.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
```

注意：RabbitMQ 不是每收到一条就 fsync 到磁盘，有短暂的间隔。对于绝对不丢的要求，生产者确认 + 消费者确认 + 集群镜像队列才是完整方案。

### 8.3 消费者确认（Consumer Ack）

```yaml
spring:
  rabbitmq:
    listener:
      simple:
        acknowledge-mode: manual
```

```java
@RabbitListener(queues = "queue.important")
public void handle(String message, Channel channel,
                   @Header(AmqpHeaders.DELIVERY_TAG) long tag) {
    try {
        processMessage(message);
        channel.basicAck(tag, false);  // 处理成功，确认删除
    } catch (BusinessException e) {
        // 业务异常（如库存不足），不重试，直接确认丢弃
        channel.basicAck(tag, false);
        log.warn("业务异常，消息丢弃: {}", e.getMessage());
    } catch (Exception e) {
        // 系统异常（如数据库挂了），拒收并重新入队
        channel.basicNack(tag, false, true);
    }
}
```

关键判断：**业务异常不要重试，系统异常才重试**。业务异常无论重试多少次还是失败，反复重试只会阻塞队列。

### 8.4 消息可靠性架构小结

```
消息落库 -> 发送 -> Broker Confirm -> 更新消息状态为"已发送"
                                          |
                                    消费者处理成功 -> Ack -> 更新消息状态为"已消费"
                                          |
                                    处理失败 -> Nack(requeue=false) -> 死信队列 -> 人工处理
```

---

## 9. 死信队列

### 9.1 什么是死信

一条消息变成死信（Dead Letter）有三种情况：
- 被消费者 **basicNack/reject** 且 requeue=false
- 消息 TTL 过期（设置了过期时间未消费）
- 队列已满，被丢弃

### 9.2 死信队列配置

```java
@Configuration
public class DeadLetterConfig {

    // 死信交换机
    public static final String DLX_EXCHANGE = "exchange.dlx";
    // 死信队列
    public static final String DLX_QUEUE = "queue.dlx";
    // 死信路由 Key
    public static final String DLX_ROUTING = "dlx.order";

    // 业务队列
    public static final String ORDER_QUEUE = "queue.order";

    // ============ 死信队列声明 ============

    @Bean
    public DirectExchange dlxExchange() {
        return new DirectExchange(DLX_EXCHANGE);
    }

    @Bean
    public Queue dlxQueue() {
        return QueueBuilder.durable(DLX_QUEUE).build();
    }

    @Bean
    public Binding dlxBinding(Queue dlxQueue, DirectExchange dlxExchange) {
        return BindingBuilder.bind(dlxQueue).to(dlxExchange).with(DLX_ROUTING);
    }

    // ============ 业务队列（指定死信） ============

    @Bean
    public Queue orderQueue() {
        return QueueBuilder.durable(ORDER_QUEUE)
                .deadLetterExchange(DLX_EXCHANGE)       // 死信交换机
                .deadLetterRoutingKey(DLX_ROUTING)       // 死信路由 Key
                .ttl(60000)                              // 消息 60 秒过期（可选）
                .maxLength(1000)                         // 队列最大长度（可选）
                .build();
    }
}
```

### 9.3 死信消费者

```java
@Component
public class DeadLetterConsumer {

    @RabbitListener(queues = DeadLetterConfig.DLX_QUEUE)
    public void handleDeadLetter(Message message, Channel channel,
                                 @Header(AmqpHeaders.DELIVERY_TAG) long tag) {
        try {
            log.warn("死信消息: {}", new String(message.getBody()));

            // 原始信息都在 headers 里
            Map<String, Object> headers = message.getMessageProperties().getHeaders();
            List<Map<String, ?>> xDeath = (List<Map<String, ?>>) headers.get("x-death");
            // x-death 包含：队列名、原因（rejected/expired）、路由时间等

            // 记录到数据库，通知运维处理
            saveToDeadLetterTable(message, xDeath);

            channel.basicAck(tag, false);
        } catch (Exception e) {
            log.error("死信处理失败", e);
        }
    }
}
```

---

## 10. 延迟消息

### 10.1 两种实现方式

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 死信队列 + TTL | 消息过期 -> 死信 -> 死信消费者处理 | 无需插件 | 精度取决于 TTL，顺序问题 |
| delayed-message 插件 | 交换机延迟投递 | 精确，灵活 | 需装插件 |

### 10.2 方式一：死信队列模拟延迟

给业务队列设置 TTL，消息过期后自动进入死信队列。死信消费者就是实际的处理者。

```java
@Bean
public Queue delayOrderQueue() {
    return QueueBuilder.durable("queue.order.delay.30m")
            .deadLetterExchange("exchange.order")   // 过期后进入真正的订单 Exchange
            .deadLetterRoutingKey("order.cancel")   // 路由 Key=order.cancel
            .ttl(30 * 60 * 1000)                    // 30 分钟过期
            .build();
}
```

流程：
```
发送 -> queue.order.delay.30m（等 30 分钟）
     -> 过期 -> exchange.order.RoutingKey=order.cancel
     -> queue.order -> 消费者处理（取消订单）
```

缺点：如果同一个业务队列需要不同延迟时间，就得创建多个队列（5分钟、10分钟、30分钟...），管理起来麻烦。

### 10.3 方式二：Delay Exchange 插件

首先安装插件（Docker 已安装则跳过）：

```bash
# 进入容器
docker exec -it rabbitmq bash
# 启用插件
rabbitmq-plugins enable rabbitmq_delayed_message_exchange
# 重启
docker restart rabbitmq
```

代码配置：

```java
@Configuration
public class DelayExchangeConfig {

    public static final String DELAY_EXCHANGE = "exchange.delay";

    @Bean
    public CustomExchange delayExchange() {
        Map<String, Object> args = new HashMap<>();
        args.put("x-delayed-type", "direct");  // 底层 Exchange 类型

        return new CustomExchange(
                DELAY_EXCHANGE,
                "x-delayed-message",            // 固定值
                true,                            // 持久化
                false,                           // 不自动删除
                args
        );
    }

    @Bean
    public Queue delayQueue() {
        return QueueBuilder.durable("queue.delay.process").build();
    }

    @Bean
    public Binding delayBinding(Queue delayQueue, CustomExchange delayExchange) {
        return BindingBuilder.bind(delayQueue).to(delayExchange).with("delay.process").noargs();
    }
}
```

发送时在消息头中指定延迟时间：

```java
rabbitTemplate.convertAndSend(
        DelayExchangeConfig.DELAY_EXCHANGE,
        "delay.process",
        orderId,
        message -> {
            // 延迟 30 分钟投递（单位：毫秒）
            message.getMessageProperties().setDelay(30 * 60 * 1000);
            return message;
        }
);
```

**延迟时间用消息头而非队列 TTL**，同一个队列可支持不同延迟时间，解决了死信方式的痛点。

### 10.4 延迟消息典型场景：订单超时取消

```java
// 下单后发送延迟取消消息
@Service
public class OrderTimeoutService {

    @Autowired
    private RabbitTemplate rabbitTemplate;

    public void scheduleOrderCancel(Long orderId, long delayMinutes) {
        rabbitTemplate.convertAndSend(
                DelayExchangeConfig.DELAY_EXCHANGE,
                "order.cancel",
                orderId,
                message -> {
                    message.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
                    message.getMessageProperties().setDelay((int) (delayMinutes * 60 * 1000));
                    return message;
                }
        );
        log.info("已安排订单{}在{}分钟后自动取消检查", orderId, delayMinutes);
    }
}

// 消费者处理
@Component
public class OrderCancelConsumer {

    @Autowired
    private OrderService orderService;

    @RabbitListener(queues = "queue.order.cancel")
    public void cancelOrder(Long orderId, Channel channel,
                            @Header(AmqpHeaders.DELIVERY_TAG) long tag) throws IOException {
        // 查订单状态，如果还是待支付，则取消
        Order order = orderService.getById(orderId);
        if (order != null && order.getStatus() == OrderStatus.PENDING) {
            orderService.cancel(orderId);
            log.info("订单{}超时未支付，已自动取消", orderId);
        }
        channel.basicAck(tag, false);
    }
}
```

---

## 11. 消息幂等

### 11.1 为什么需要幂等

消费者处理完消息但 Ack 之前进程挂了，消息会重新投递。如果扣库存的操作重复执行，库存就扣多了。

### 11.2 基于数据库的去重

```java
@Component
public class IdempotentConsumer {

    @Autowired
    private MessageRecordMapper messageRecordMapper;
    @Autowired
    private OrderService orderService;

    @RabbitListener(queues = "queue.order")
    public void handle(OrderCreateEvent event, Channel channel,
                       @Header(AmqpHeaders.DELIVERY_TAG) long tag,
                       @Header(name = "messageId", required = false) String messageId) throws IOException {

        if (messageId == null) {
            log.warn("消息缺少 messageId，跳过幂等检查");
            doCreateOrder(event);
            channel.basicAck(tag, false);
            return;
        }

        // 插入幂等记录（UNIQUE 约束保证不会重复插入）
        MessageRecord record = new MessageRecord();
        record.setMessageId(messageId);
        record.setStatus("CONSUMING");
        try {
            messageRecordMapper.insert(record);
        } catch (DuplicateKeyException e) {
            // 已处理过，直接确认
            log.info("消息已处理过, messageId={}", messageId);
            channel.basicAck(tag, false);
            return;
        }

        // 实际业务处理
        doCreateOrder(event);

        // 更新为已消费
        record.setStatus("CONSUMED");
        messageRecordMapper.updateById(record);

        channel.basicAck(tag, false);
    }

    private void doCreateOrder(OrderCreateEvent event) {
        // 实际下单逻辑
    }
}
```

幂等表 DDL：

```sql
CREATE TABLE t_message_record (
    id          BIGINT PRIMARY KEY,
    message_id  VARCHAR(64) NOT NULL COMMENT '消息 ID',
    status      VARCHAR(20) NOT NULL COMMENT 'CONSUMING / CONSUMED',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_message_id (message_id)  -- 唯一约束保证幂等
);
```

### 11.3 基于 Redis 的去重

如果你的系统已经重度依赖 Redis，用 SETNX 更轻量：

```java
String key = "msg:" + messageId;
Boolean success = redisTemplate.opsForValue()
        .setIfAbsent(key, "1", Duration.ofHours(24));
if (Boolean.FALSE.equals(success)) {
    // 已处理
    channel.basicAck(tag, false);
    return;
}
```

### 11.4 基于业务状态的去重

如果业务本身有状态机（比如订单从"待支付"到"已支付"只允许一次），利用状态转换的 CAS 语义：

```sql
UPDATE t_order SET status = 'PAID' WHERE id = ? AND status = 'PENDING'
```

`affectedRows == 0` 说明已经被别的消息处理过，跳过即可。不依赖 messageId，也不需要额外的去重表。

---

## 12. 应用场景实战

### 场景一：订单通知系统（邮件 + 短信同步发送）

用户下单后，同时发送邮件和短信通知。用 Direct Exchange 将消息分别路由到邮件队列和短信队列。

**消息实体：**

```java
@Data
public class OrderNotifyMessage implements Serializable {

    private Long orderId;
    private String orderNo;
    private Long userId;
    private String email;
    private String phone;
    private BigDecimal totalAmount;
    private LocalDateTime createTime;
}
```

**队列配置：**

```java
@Configuration
public class OrderNotifyConfig {

    public static final String EXCHANGE_NOTIFY = "exchange.order.notify";
    public static final String QUEUE_EMAIL = "queue.order.email";
    public static final String QUEUE_SMS = "queue.order.sms";
    public static final String ROUTING_EMAIL = "email";
    public static final String ROUTING_SMS = "sms";

    @Bean
    public DirectExchange notifyExchange() {
        return ExchangeBuilder.directExchange(EXCHANGE_NOTIFY)
                .durable(true)
                .build();
    }

    @Bean
    public Queue emailQueue() {
        return QueueBuilder.durable(QUEUE_EMAIL).build();
    }

    @Bean
    public Queue smsQueue() {
        return QueueBuilder.durable(QUEUE_SMS).build();
    }

    @Bean
    public Binding emailBinding() {
        return BindingBuilder.bind(emailQueue()).to(notifyExchange()).with(ROUTING_EMAIL);
    }

    @Bean
    public Binding smsBinding() {
        return BindingBuilder.bind(smsQueue()).to(notifyExchange()).with(ROUTING_SMS);
    }
}
```

**生产者（订单创建后发送）：**

```java
@Service
@RequiredArgsConstructor
public class OrderNotifyProducer {

    private final RabbitTemplate rabbitTemplate;

    public void sendNotify(OrderNotifyMessage message) {
        // 发送邮件通知
        rabbitTemplate.convertAndSend(
                OrderNotifyConfig.EXCHANGE_NOTIFY,
                OrderNotifyConfig.ROUTING_EMAIL,
                message,
                msg -> {
                    msg.getMessageProperties().setMessageId(UUID.randomUUID().toString());
                    msg.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
                    return msg;
                }
        );

        // 发送短信通知
        rabbitTemplate.convertAndSend(
                OrderNotifyConfig.EXCHANGE_NOTIFY,
                OrderNotifyConfig.ROUTING_SMS,
                message,
                msg -> {
                    msg.getMessageProperties().setMessageId(UUID.randomUUID().toString());
                    msg.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
                    return msg;
                }
        );

        log.info("已发送订单{}的通知消息", message.getOrderNo());
    }
}
```

**消费者——邮件：**

```java
@Component
@Slf4j
public class EmailNotifyConsumer {

    @RabbitListener(queues = OrderNotifyConfig.QUEUE_EMAIL)
    public void handle(OrderNotifyMessage message, Channel channel,
                       @Header(AmqpHeaders.DELIVERY_TAG) long tag) {
        try {
            // 模拟发送邮件
            sendEmail(message.getEmail(),
                    "订单确认 - " + message.getOrderNo(),
                    buildEmailContent(message));

            channel.basicAck(tag, false);
            log.info("订单邮件通知发送成功: {}", message.getOrderNo());

        } catch (Exception e) {
            log.error("邮件发送失败, orderNo={}", message.getOrderNo(), e);
            try {
                // 邮件服务暂时不可用，重新入队
                channel.basicNack(tag, false, true);
            } catch (IOException ex) {
                log.error("nack 失败", ex);
            }
        }
    }

    private void sendEmail(String to, String subject, String content) {
        // 调用邮件服务的实际代码
    }

    private String buildEmailContent(OrderNotifyMessage message) {
        return String.format("""
                订单号：%s
                下单时间：%s
                订单金额：%.2f
                """, message.getOrderNo(), message.getCreateTime(), message.getTotalAmount());
    }
}
```

**消费者——短信：**

```java
@Component
@Slf4j
public class SmsNotifyConsumer {

    @RabbitListener(queues = OrderNotifyConfig.QUEUE_SMS)
    public void handle(OrderNotifyMessage message, Channel channel,
                       @Header(AmqpHeaders.DELIVERY_TAG) long tag) {
        try {
            String smsContent = String.format("【XX商城】订单%s已确认，金额%.2f元",
                    message.getOrderNo(), message.getTotalAmount());
            sendSms(message.getPhone(), smsContent);

            channel.basicAck(tag, false);
            log.info("订单短信通知发送成功: {}", message.getOrderNo());

        } catch (Exception e) {
            log.error("短信发送失败", e);
            try {
                channel.basicNack(tag, false, true);
            } catch (IOException ex) {
                log.error("nack 失败", ex);
            }
        }
    }

    private void sendSms(String phone, String content) {
        // 调用短信网关
    }
}
```

**Controller 入口：**

```java
@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;
    private final OrderNotifyProducer notifyProducer;

    @PostMapping
    public R<Long> create(@RequestBody @Valid OrderCreateDTO dto) {
        // 1. 创建订单
        Long orderId = orderService.createOrder(dto);

        // 2. 异步发送通知
        OrderNotifyMessage notifyMsg = new OrderNotifyMessage();
        notifyMsg.setOrderId(orderId);
        notifyMsg.setOrderNo(orderService.getOrderNo(orderId));
        notifyMsg.setUserId(getCurrentUserId());
        notifyMsg.setEmail(dto.getEmail());
        notifyMsg.setPhone(dto.getPhone());
        notifyMsg.setTotalAmount(dto.getTotalAmount());
        notifyMsg.setCreateTime(LocalDateTime.now());
        notifyProducer.sendNotify(notifyMsg);

        return R.ok(orderId);
    }
}
```

### 场景二：文章审核系统——消息回退 + 死信重试

提交文章 -> 自动审核 -> 审核失败 -> 重试 3 次 -> 仍失败进死信 -> 人工处理。

**消息体：**

```java
@Data
public class ArticleAuditMessage implements Serializable {

    private Long articleId;
    private String title;
    private String content;
    private Long authorId;
    private LocalDateTime submitTime;
    private int retryCount;       // 当前重试次数
}
```

**队列配置（带死信）：**

```java
@Configuration
public class ArticleAuditConfig {

    public static final String EXCHANGE_AUDIT = "exchange.article.audit";
    public static final String QUEUE_AUDIT = "queue.article.audit";
    public static final String DLX_EXCHANGE = "exchange.article.audit.dlx";
    public static final String DLX_QUEUE = "queue.article.audit.dlx";
    public static final String ROUTING_AUDIT = "audit";
    public static final String ROUTING_DLX = "audit.dlx";

    @Bean
    public DirectExchange auditExchange() {
        return new DirectExchange(EXCHANGE_AUDIT);
    }

    @Bean
    public DirectExchange auditDlxExchange() {
        return new DirectExchange(DLX_EXCHANGE);
    }

    @Bean
    public Queue auditQueue() {
        return QueueBuilder.durable(QUEUE_AUDIT)
                .deadLetterExchange(DLX_EXCHANGE)
                .deadLetterRoutingKey(ROUTING_DLX)
                .build();
    }

    @Bean
    public Queue auditDlxQueue() {
        return QueueBuilder.durable(DLX_QUEUE).build();
    }

    @Bean
    public Binding auditBinding() {
        return BindingBuilder.bind(auditQueue()).to(auditExchange()).with(ROUTING_AUDIT);
    }

    @Bean
    public Binding auditDlxBinding() {
        return BindingBuilder.bind(auditDlxQueue()).to(auditDlxExchange()).with(ROUTING_DLX);
    }
}
```

**消费者（带重试逻辑）：**

```java
@Component
@Slf4j
public class ArticleAuditConsumer {

    private static final int MAX_RETRY = 3;

    @RabbitListener(queues = ArticleAuditConfig.QUEUE_AUDIT)
    public void handle(ArticleAuditMessage message, Channel channel,
                       @Header(AmqpHeaders.DELIVERY_TAG) long tag) {
        try {
            // 调用第三方审核 API（敏感词、AI 检测等）
            AuditResult result = auditService.audit(message.getContent());

            if (result.isPassed()) {
                // 审核通过，更新文章状态
                articleService.updateStatus(message.getArticleId(), ArticleStatus.APPROVED);
                channel.basicAck(tag, false);
                log.info("文章审核通过: {}", message.getArticleId());

            } else if (result.isSuspicious()) {
                // 疑似违规，且未达到最大重试次数
                if (message.getRetryCount() < MAX_RETRY) {
                    // 递增重试次数后重新发送
                    message.setRetryCount(message.getRetryCount() + 1);
                    rabbitTemplate.convertAndSend(
                            ArticleAuditConfig.EXCHANGE_AUDIT,
                            ArticleAuditConfig.ROUTING_AUDIT,
                            message,
                            msg -> msg.getMessageProperties()
                                    .setExpiration(String.valueOf(3 * 1000))
                    );
                    channel.basicAck(tag, false);  // 确认原消息
                    log.info("审核可疑，第{}次重试: {}", message.getRetryCount(), message.getArticleId());
                } else {
                    // 达到最大重试次数，拒绝且不重新入队 -> 进死信
                    channel.basicReject(tag, false);
                    log.warn("重试{}次仍未通过，转入死信: {}", MAX_RETRY, message.getArticleId());
                }

            } else {
                // 明确违规，直接打回
                articleService.updateStatus(message.getArticleId(), ArticleStatus.REJECTED);
                articleService.addRejectReason(message.getArticleId(), result.getReason());
                channel.basicAck(tag, false);
                log.info("文章违规，已打回: {}", message.getArticleId());
            }

        } catch (IOException e) {
            // 审核 API 调用异常（网络问题等）
            log.error("审核 API 调用失败，消息重新入队", e);
            try {
                channel.basicNack(tag, false, true);
            } catch (IOException ex) {
                log.error("nack 失败", ex);
            }
        }
    }
}
```

**死信消费者（人工处理）：**

```java
@Component
@Slf4j
public class ArticleAuditDlxConsumer {

    @RabbitListener(queues = ArticleAuditConfig.DLX_QUEUE)
    public void handle(ArticleAuditMessage message, Channel channel,
                       @Header(AmqpHeaders.DELIVERY_TAG) long tag) {
        try {
            // 1. 标记为待人工审核
            articleService.updateStatus(message.getArticleId(), ArticleStatus.MANUAL_REVIEW);

            // 2. 给审核员发通知（钉钉 / 企业微信 / 站内信）
            notifyAuditor(message);

            channel.basicAck(tag, false);
            log.info("文章{}转入人工审核队列", message.getArticleId());

        } catch (Exception e) {
            log.error("死信处理失败", e);
        }
    }
}
```

---

## 13. 最佳实践与踩坑记录

### 13.1 推荐做法

**1. Bean 声明统一放配置类**

不要把 `@Bean` 声明 queue/exchange/binding 散落各处，建一个或几个 Config 类集中管理，找配置时不用翻遍项目。

**2. 生产环境必须配死信队列**

核心业务队列一定要配死信。一条消息如果反复失败，没有死信就永远丢了，有死信还能捞回来。

**3. 消费者区分业务异常和系统异常**

业务异常直接 ack 丢弃（或记日志），系统异常才 nack 重试。把所有异常都 nack 回去，队列很快被毒消息堵死。

**4. JSON 序列化，关掉 JDK 序列化**

JDK 序列化的消息 RabbitMQ 控制台是乱码，排查问题极其痛苦。

**5. 消息体携带 messageId**

生产者在消息头或消息体中打入唯一 ID，消费者靠它做幂等。

**6. 消息落库**

对于绝对不能丢的消息（支付、积分等），发送前先把消息写入数据库，确认后再删。出问题可追溯。

**7. prefetch 设为 1 保证公平分发**

默认 prefetch=250，一个消费者会一口气抓 250 条消息在本地。如果消费者 A 处理快、B 处理慢，A 干完活 B 还在堆着。prefetch=1 后，A 处理完一条再去拿一条，负载自然分散。

### 13.2 踩坑记录

**坑 1：容器启动时 RabbitMQ 没连上，应用直接崩了**

Spring Boot 默认 RabbitMQ 连接失败就启动不了。如果 RabbitMQ 后启动或网络不稳定，加连接重试：

```yaml
spring:
  rabbitmq:
    connection-timeout: 30000
    template:
      retry:
        enabled: true
        initial-interval: 2000ms
```

**坑 2：@RabbitListener 所在的类不在 Spring 容器中**

加了 `@RabbitListener` 的类不能被 `new` 出来，必须通过 `@Component`/`@Service` 交给 Spring 管理，否则监听不生效。

**坑 3：发送方用 `convertAndSend`，接收方拿到的却是 `byte[]`**

没配 `MessageConverter`，Spring AMQP 默认用 `SimpleMessageConverter`，会把对象转为序列化字节流。接收方如果声明参数为对象，反序列化失败。配置 `Jackson2JsonMessageConverter` 即可：

```java
@Bean
public MessageConverter messageConverter() {
    return new Jackson2JsonMessageConverter();
}
```

**坑 4：消费者抛异常后消息无限重试**

不配置重试策略的话，Spring AMQP 默认无限重试且无间隔。队列一直报同一个错，其他消息被堵死。必须配 retry：

```yaml
spring:
  rabbitmq:
    listener:
      simple:
        retry:
          enabled: true
          max-attempts: 3
```

**坑 5：手动 ack 模式下忘记 ack/nack**

`acknowledge-mode: manual` 后，每条消息必须显式 ack 或 nack。忘了等于不确认，消息一直 unacked。RabbitMQ 管理后台看到 unacked 数量不断增加，最终 OOM。

补救：设消费者超时。但根本解决方法是配死信 + 代码 review 确保每条路径都 ack/nack。

**坑 6：消息已经在 @Transactional 里了，结果 rollback 后消息照样发出去了**

RabbitMQ 操作默认不参与 Spring 事务。如果数据库回滚但消息已发送，数据不一致。解决方案：用 `RabbitTransactionManager` 或者使用 `@TransactionalEventListener` + `TransactionPhase.AFTER_COMMIT`：

```java
// 不在事务方法里直接发送，注册一个事务提交后的回调
@TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
public void handleOrderCreated(OrderCreatedEvent event) {
    rabbitTemplate.convertAndSend(...);
}
```

**坑 7：延迟消息用 TTL 队列时顺序问题**

队列里有两条消息，TTL 分别为 5 秒和 60 秒。5 秒的消息在前，但 60 秒的没被消费完，5 秒的消息也出不去——RabbitMQ 消费是 FIFO 的，必须等前面的消息先消费或过期。

解决方案：不同延迟时间用不同队列，或者用延迟插件（x-delayed-message）。

**坑 8：消息头过大**

`x-death` 等 RabbitMQ 自动注入的 header 体积不小。频繁消费死信并重新入队会让 header 越来越大，最终超出帧限制（默认 128KB）。解决：重新入队前清理不必要的 header，或用新消息体重建。

---

## 14. 参考链接

- RabbitMQ 官方文档：https://www.rabbitmq.com/docs
- Spring AMQP 文档：https://docs.spring.io/spring-amqp/reference/
- Docker RabbitMQ 镜像：https://hub.docker.com/_/rabbitmq
- RabbitMQ Delayed Message Plugin：https://github.com/rabbitmq/rabbitmq-delayed-message-exchange
- [[spring-boot-redisson]] — 分布式锁在消费端的应用（避免同一条消息被多个实例同时消费）
- [[spring-boot-scheduled]] — 定时任务扫表兜底（消息丢失后的最后一道防线）
