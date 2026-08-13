---
title: Spring Cloud 面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springcloud面试, nacos, gateway, feign, loadbalancer, circuitbreaker, sentinel, 分布式事务, seata, 链路追踪, cap, 服务雪崩]
---

# Spring Cloud 面试

整理日期：2026-08-13

## 目录

- [微服务基础与 CAP](#微服务基础与-cap)
- [Nacos](#nacos)
- [Gateway](#gateway)
- [Feign](#feign)
- [LoadBalancer](#loadbalancer)
- [CircuitBreaker](#circuitbreaker)
- [Sentinel 限流](#sentinel-限流)
- [分布式事务](#分布式事务)
- [链路追踪](#链路追踪)
- [服务雪崩与容错](#服务雪崩与容错)
- [面试重点总结](#面试重点总结)

## 微服务基础与 CAP

**问题 1：为什么用微服务？**

```text
优点：
1. 独立部署、独立扩展（按模块扩缩容）
2. 技术异构（不同服务用不同技术栈）
3. 故障隔离（单服务故障不拖垮全局）
4. 团队自治

缺点：
1. 分布式复杂性（网络、数据一致性、链路追踪）
2. 运维成本高（服务多、监控难）
3. 数据一致性难保证（分布式事务）
```

**问题 2：CAP 理论？**

```text
CAP：一致性（Consistency）、可用性（Availability）、分区容错性（Partition tolerance）
三者不能同时满足，最多满足两个。

实际：网络分区不可避免，必须选 P，在 C 和 A 之间取舍：
1. CP —— 保证一致性，牺牲可用性（Nacos 临时实例用 AP，持久实例用 CP；Zookeeper CP）
2. AP —— 保证可用性，牺牲一致性（Eureka、Nacos 默认临时实例）
```

**问题 3：微服务的核心组件？**

```text
1. 注册中心 —— Nacos/Eureka（服务发现）
2. 配置中心 —— Nacos/Apollo（配置管理）
3. 网关 —— Gateway（统一入口）
4. 服务调用 —— OpenFeign（声明式 HTTP）
5. 负载均衡 —— LoadBalancer（客户端均衡）
6. 熔断降级 —— Sentinel/Resilience4j
7. 分布式事务 —— Seata
8. 链路追踪 —— SkyWalking/Zipkin
```

## Nacos

**问题 1：Nacos 的作用？**

```text
Nacos（Na + Co + S：命名 + 配置 + 服务）：
1. 服务注册与发现 —— 服务实例注册、心跳、发现
2. 配置中心 —— 配置集中管理、动态刷新
```

**问题 2：服务注册和发现的流程？**

```text
1. 服务启动 → 注册到 Nacos（临时实例发送心跳续约，默认 5 秒）
2. 调用方 → 从 Nacos 拉取服务实例列表（并订阅变更）
3. 调用方 → 负载均衡选择实例调用
4. 服务下线 → 心跳超时（15 秒未续约）→ Nacos 移除实例并通知订阅者
```

**问题 3：Nacos 的配置中心？**

```text
1. 配置集中管理（dataId + group 定位配置）
2. 动态刷新（改配置不重启，@RefreshScope 或 @Value 刷新）
3. 命名空间（namespace）环境隔离、分组（group）业务隔离
4. 配置监听，客户端长轮询拉取变更
```

**问题 4：Nacos、Eureka、Consul、Zookeeper 对比？**

| 组件 | CAP | 一致性协议 | 特点 |
|------|-----|-----------|------|
| Nacos | AP + CP 可切换 | Raft（CP）/ Distro（AP） | 注册 + 配置一体，阿里开源 |
| Eureka | AP | 无（自我保护） | 简单，2.x 已停更 |
| Consul | CP | Raft | 注册 + 配置 + 健康检查 |
| Zookeeper | CP | ZAB | 强一致，旧 Dubbo 常用 |

## Gateway

**问题 1：Gateway 的作用？**

```text
网关是微服务的统一入口：
1. 路由 —— 请求转发到对应服务
2. 鉴权 —— 统一认证（登录态校验）
3. 限流 —— 保护后端
4. 日志 —— 统一日志、traceId 透传
5. 灰度发布、协议转换
```

**问题 2：Gateway 的三大核心？**

```text
1. Route（路由）—— 路由规则（目标服务 + 匹配条件）
2. Predicate（断言）—— 匹配条件（Path、Method、Header）
3. Filter（过滤器）—— 处理逻辑（鉴权、限流、加请求头）
```

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: user-route
          uri: lb://user-service
          predicates:
            - Path=/api/user/**
          filters:
            - StripPrefix=1
```

**问题 3：Gateway 和 Zuul 的区别？**

```text
Gateway —— 响应式（WebFlux，基于 Netty），性能好，Spring 官方
Zuul 1.x —— 阻塞（Servlet），已停止维护
Zuul 2.x —— 响应式，但 Spring Cloud 未正式集成
```

**问题 4：Gateway 如何实现限流？**

```text
用 Redis 的 RequestRateLimiter 过滤器（令牌桶算法）：
1. 配置 redis-rate-limiter.replenishRate（每秒令牌数）
2. burstCapacity（桶容量）
3. KeyResolver 指定限流维度（IP/用户/接口）
```

## Feign

**问题 1：Feign 是什么？**

```text
OpenFeign 是声明式 HTTP 客户端：
1. 定义接口 + 注解（@FeignClient + @GetMapping）
2. 动态代理自动生成实现
3. 简化服务间调用（写接口像写本地方法）
```

```java
@FeignClient(name = "user-service", fallback = UserClientFallback.class)
public interface UserClient {
    @GetMapping("/api/users/{id}")
    User getUser(@PathVariable Long id);
}
```

**问题 2：Feign 的原理？**

```text
1. @FeignClient 接口
2. JDK 动态代理生成实现
3. 调用时通过 LoadBalancer 从注册中心选择实例
4. 用配置的 HTTP 客户端（默认 HttpURLConnection，可换 OkHttp/Apache HttpClient）发送请求
```

**问题 3：Feign 的优化？**

```text
1. 超时配置（connectTimeout、readTimeout）
2. 连接池（换 HttpClient/OkHttp，复用连接）
3. 日志级别（FULL 排查问题）
4. 重试机制（Retryer，注意幂等）
5. 熔断降级（fallback/fallbackFactory）
```

## LoadBalancer

**问题 1：LoadBalancer 的负载均衡策略？**

```text
1. RoundRobin —— 轮询（默认）
2. Random —— 随机
3. Weighted —— 加权
4. 自定义 —— 实现 ReactorServiceInstanceLoadBalancer
```

**问题 2：客户端负载均衡 vs 服务端负载均衡？**

```text
服务端负载均衡 —— Nginx/LVS，请求先到负载均衡器再转发后端
客户端负载均衡 —— LoadBalancer，客户端自己从服务列表选择实例调用

区别：客户端均衡省去中间一跳，但服务列表要客户端感知（依赖注册中心）。
```

## CircuitBreaker

**问题 1：熔断器的作用？**

```text
熔断器防止服务故障级联（雪崩）：
1. 服务故障 → 快速失败（不等待超时）
2. 防止线程/连接堆积拖垮调用方
3. 服务恢复 → 半开状态探测后放行
```

**问题 2：熔断器的三种状态？**

```text
1. Closed（关闭）—— 正常，请求放行；失败率达到阈值 → 打开
2. Open（打开）—— 熔断，快速失败；冷却时间后 → 半开
3. Half-Open（半开）—— 放部分请求探测；成功恢复关闭，失败继续打开
```

**问题 3：熔断、降级、限流的区别？**

```text
熔断 —— 故障服务快速失败（防止级联）
降级 —— 返回兜底结果（保证核心链路可用）
限流 —— 控制请求量（防止过载）
```

## Sentinel 限流

**问题 1：Sentinel 是什么？**

```text
Sentinel 是阿里开源的流量治理组件（限流、熔断、降级、系统保护）：
1. 流量控制 —— QPS/线程数限流
2. 熔断降级 —— 慢调用比例/异常比例熔断
3. 热点参数限流 —— 针对参数维度限流
4. 系统自适应保护
5. 实时监控 + 控制台动态调整规则
```

**问题 2：Sentinel 和 Hystrix 的区别？**

```text
Sentinel —— 更细粒度限流（QPS/线程数/热点）、控制台动态改规则、限流降级分开
Hystrix —— 主要熔断隔离（线程池/信号量）、已停更

Sentinel 限流和熔断解耦，规则可动态调整，无需重启。
```

## 分布式事务

**问题 1：分布式事务的解决方案？**

```text
1. 2PC/3PC —— 两阶段提交（强一致，性能差，XA）
2. TCC —— Try-Confirm-Cancel（预留资源-确认-取消，需业务实现）
3. SAGA —— 长事务拆成多个本地事务 + 补偿
4. 本地消息表 —— 本地事务 + 消息表 + 定时补偿
5. 事务消息 —— RocketMQ 半消息（发送-本地执行-确认）
6. 最大努力通知 —— 多次重试 + 对账
```

**问题 2：Seata 的三种模式？**

```text
1. AT 模式 —— 自动（全局锁 + undo log 回滚，对业务无侵入，默认）
2. TCC 模式 —— Try-Confirm-Cancel，业务需实现三方法
3. SAGA 模式 —— 长事务补偿，适合无全局锁场景

Seata 组件：TC（事务协调者）+ TM（事务管理器）+ RM（资源管理器）
```

**问题 3：CAP 下的分布式事务取舍？**

```text
强一致 → 2PC/TCC（性能差，银行转账）
最终一致 → 消息 + 补偿（订单 + 库存，主流）
实际业务大多用最终一致 + 补偿，而非强一致。
```

## 链路追踪

**问题：链路追踪的原理和方案？**

```text
原理：
1. 请求入口生成全局 traceId
2. 每经过一个服务生成 spanId（记录调用关系 + 耗时）
3. traceId 透传（HTTP header / RPC 上下文）
4. 汇总到存储（ES），UI 展示调用链

方案：
1. SkyWalking —— 字节码探针，无侵入，Java 主流
2. Zipkin + Sleuth —— Spring 生态（Sleuth 已并入 Micrometer Tracing）
3. Jaeger —— CNCF 项目
```

## 服务雪崩与容错

**问题：什么是服务雪崩？如何解决？**

```text
雪崩：一个服务故障 → 调用它的服务线程阻塞（等超时）→ 线程耗尽 → 连锁故障扩散。

解决：
1. 熔断 —— 故障快速失败，不等待超时
2. 降级 —— 返回兜底结果
3. 限流 —— 控制并发，保护自身
4. 超时控制 —— 合理设置超时时间，不无限等待
5. 隔离 —— 线程池隔离（不同依赖独立线程池）
6. 缓存 —— 缓存热点数据，减少下游压力
```

## 面试重点总结

```text
高频考点：
1. CAP 理论 + Nacos/Eureka 的取舍（必考）
2. Nacos 注册中心 + 配置中心（心跳、动态刷新）
3. Gateway 三大核心（Route/Predicate/Filter）
4. Feign 声明式调用 + 原理
5. 熔断器三态 + 熔断/降级/限流区别（必考）
6. Sentinel 限流 vs Hystrix
7. 分布式事务方案 + Seata（必考）
8. 链路追踪原理（traceId/spanId）
9. 服务雪崩及解决
```
