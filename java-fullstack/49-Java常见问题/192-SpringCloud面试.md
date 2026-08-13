---
title: Spring Cloud 面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springcloud面试, nacos, gateway, feign, loadbalancer, circuitbreaker]
---

# Spring Cloud 面试

整理日期：2026-08-13

## 目录

- [Nacos](#nacos)
- [Gateway](#gateway)
- [Feign](#feign)
- [LoadBalancer](#loadbalancer)
- [CircuitBreaker](#circuitbreaker)

## Nacos

**问题 1：Nacos 的作用？**

```text
Nacos 是注册中心 + 配置中心：
1. 服务注册与发现 —— 服务实例注册、发现
2. 配置中心 —— 配置集中管理、动态刷新
```

**问题 2：服务注册和发现的流程？**

```text
1. 服务启动 → 注册到 Nacos
2. 调用方 → 从 Nacos 获取服务实例列表
3. 调用方 → 负载均衡选择实例调用
4. 服务下线 → Nacos 移除实例（心跳检测）
```

**问题 3：Nacos 的配置中心？**

```text
1. 配置集中管理
2. 动态刷新（改配置不重启）
3. 命名空间/分组隔离（环境隔离）
```

## Gateway

**问题 1：Gateway 的作用？**

```text
网关是微服务的统一入口：
1. 路由 —— 请求转发
2. 鉴权 —— 统一认证
3. 限流 —— 保护后端
4. 日志 —— 统一日志
```

**问题 2：Gateway 的三大核心？**

```text
1. Route（路由）—— 路由规则（目标服务 + 匹配条件）
2. Predicate（断言）—— 匹配条件（Path、Method）
3. Filter（过滤器）—— 处理逻辑（鉴权、限流）
```

**问题 3：Gateway 和 Zuul 的区别？**

```text
Gateway —— 响应式（WebFlux），性能好，Spring 官方
Zuul —— 阻塞（Servlet），已停止维护
```

## Feign

**问题 1：Feign 是什么？**

```text
Feign 是声明式 HTTP 客户端：
1. 定义接口 + 注解
2. 自动生成实现（动态代理）
3. 简化服务间调用
```

```java
@FeignClient(name = "user-service")
public interface UserClient {
    @GetMapping("/api/users/{id}")
    User getUser(@PathVariable Long id);
}
```

**问题 2：Feign 的原理？**

```text
1. @FeignClient 接口
2. 动态代理生成实现
3. 调用时通过 LoadBalancer 选择实例
4. 发送 HTTP 请求
```

## LoadBalancer

**问题：LoadBalancer 的负载均衡策略？**

```text
1. RoundRobin —— 轮询（默认）
2. Random —— 随机
3. Weighted —— 加权
4. 自定义 —— 实现 ReactorServiceInstanceLoadBalancer
```

```text
负载均衡的类型：
服务端负载均衡 —— Nginx（请求先到 Nginx）
客户端负载均衡 —— LoadBalancer（客户端选择实例）
```

## CircuitBreaker

**问题 1：熔断器的作用？**

```text
熔断器防止服务故障级联：
1. 服务故障 → 快速失败（不等待超时）
2. 防止线程堆积
3. 服务恢复 → 半开状态探测
```

**问题 2：熔断器的三种状态？**

```text
1. Closed（关闭）—— 正常，请求放行
2. Open（打开）—— 熔断，快速失败
3. Half-Open（半开）—— 探测，部分请求试探
```

**问题 3：熔断、降级、限流的区别？**

```text
熔断 —— 故障服务快速失败
降级 —— 返回兜底结果
限流 —— 控制请求量
```

## 面试重点总结

```text
高频考点：
1. Nacos 注册中心 + 配置中心
2. Gateway 三大核心（Route/Predicate/Filter）
3. Feign 声明式调用
4. 熔断器三态
5. 熔断/降级/限流区别
```
