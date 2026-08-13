---
title: LoadBalancer
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [loadbalancer, 负载均衡, round-robin, random, 自定义负载均衡, spring-cloud]
---

# LoadBalancer

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [服务端 vs 客户端负载均衡](#服务端-vs-客户端负载均衡)
- [Spring Cloud LoadBalancer](#spring-cloud-loadbalancer)
- [内置负载均衡策略](#内置负载均衡策略)
- [自定义负载均衡策略](#自定义负载均衡策略)
- [配合 OpenFeign 使用](#配合-openfeign-使用)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

负载均衡（Load Balancing）是将请求分发到多个服务实例的技术，是微服务高可用的基础。

```text
负载均衡解决的问题：
1. 流量分发 —— 请求均匀分布到多个实例
2. 高可用 —— 某个实例故障时自动剔除
3. 水平扩展 —— 增加实例分摊负载
```

```text
Spring Cloud LoadBalancer 是 Spring Cloud 官方的客户端负载均衡组件，
替代了进入维护模式的 Netflix Ribbon。
```

## 服务端 vs 客户端负载均衡

### 服务端负载均衡

```text
请求 → 负载均衡器（Nginx/F5）→ 服务实例
```

```text
特点：
1. 负载均衡器独立部署（Nginx、F5）
2. 客户端无感知，请求先到负载均衡器
3. 配置集中，运维方便
4. 单点风险（负载均衡器本身要 HA）
```

### 客户端负载均衡

```text
客户端 → 从注册中心获取实例列表 → 自己选择实例 → 直接调用
```

```text
特点：
1. 负载均衡逻辑在客户端（每个服务内部）
2. 配合服务注册发现（Nacos/Eureka）
3. 无单点，每个客户端独立均衡
4. Spring Cloud LoadBalancer 就是这种
```

### 对比

| 维度 | 服务端（Nginx） | 客户端（LoadBalancer） |
|------|----------------|----------------------|
| 部署 | 独立组件 | 集成在客户端 |
| 单点 | 有（需 HA） | 无 |
| 灵活度 | 配置集中 | 可编程定制 |
| 服务发现 | 手动配置 upstream | 自动（注册中心） |
| 典型场景 | 对外入口 | 服务间调用 |

```text
实际架构通常两者结合：
外部请求 → Nginx（服务端 LB）→ 网关 → LoadBalancer（客户端 LB）→ 服务实例
```

## Spring Cloud LoadBalancer

### 引入依赖

```xml
<!-- 单独使用 -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-loadbalancer</artifactId>
</dependency>
```

注意：`spring-cloud-starter-openfeign` 和 `spring-cloud-starter-gateway` 已包含 LoadBalancer，无需重复引入。

### 核心接口

```java
// 负载均衡客户端
public interface LoadBalancerClient {
    ServiceInstance choose(String serviceId);   // 选择一个实例
    <T> T execute(String serviceId, LoadBalancerRequest<T> request);
}

// 响应式负载均衡（核心）
public interface ReactiveLoadBalancer<T> {
    Mono<Response<T>> choose(Request request);
}
```

### 基本使用

```java
@Service
public class OrderService {

    @Autowired
    private LoadBalancerClient loadBalancerClient;

    @Autowired
    private RestTemplate restTemplate;

    public User getUser(Long userId) {
        // 负载均衡选择一个 user-service 实例
        ServiceInstance instance = loadBalancerClient.choose("user-service");
        String url = instance.getUri() + "/users/" + userId;
        return restTemplate.getForObject(url, User.class);
    }
}
```

### @LoadBalanced RestTemplate

```java
@Configuration
public class RestTemplateConfig {

    @Bean
    @LoadBalanced   // 启用负载均衡
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

@Service
public class OrderService {
    @Autowired
    private RestTemplate restTemplate;  // 带 @LoadBalanced

    public User getUser(Long userId) {
        // 直接用服务名，LoadBalancer 自动选择实例
        return restTemplate.getForObject(
            "http://user-service/users/" + userId, User.class);
    }
}
```

## 内置负载均衡策略

### 1. Round Robin（轮询，默认）

```text
轮询：依次选择每个实例，循环往复
实例列表 [A, B, C] → A, B, C, A, B, C, ...
```

```yaml
spring:
  cloud:
    loadbalancer:
      ribbon:
        enabled: false    # 关闭 Ribbon 兼容
      nacos:
        enabled: true
```

Spring Cloud LoadBalancer 默认就是轮询策略，无需额外配置。

### 2. Random（随机）

随机选择一个实例。

```java
@Configuration
public class LoadBalancerConfig {

    @Bean
    public ReactorLoadBalancer<ServiceInstance> randomLoadBalancer(
            Environment environment, LoadBalancerClientFactory factory) {
        String name = environment.getProperty(LoadBalancerClientFactory.PROPERTY_NAME);
        return new RandomLoadBalancer(
            factory.getLazyProvider(name, ServiceInstanceListSupplier.class), name);
    }
}
```

### 策略对比

| 策略 | 原理 | 适用场景 |
|------|------|---------|
| Round Robin | 依次轮询 | 通用（实例性能一致） |
| Random | 随机选择 | 通用（分布均匀） |
| 加权轮询 | 按权重分配 | 实例性能不一致 |
| 最少连接 | 选连接最少的 | 长连接场景 |
| 一致性哈希 | 按 key 哈希 | 会话保持、缓存命中 |

## 自定义负载均衡策略

### 自定义 ReactorLoadBalancer

```java
// 基于权重的负载均衡（不同实例权重不同）
@Configuration
public class WeightLoadBalancerConfig {

    @Bean
    public ReactorLoadBalancer<ServiceInstance> weightLoadBalancer(
            Environment environment, LoadBalancerClientFactory factory) {
        String name = environment.getProperty(LoadBalancerClientFactory.PROPERTY_NAME);
        return new WeightLoadBalancer(
            factory.getLazyProvider(name, ServiceInstanceListSupplier.class), name);
    }
}

// 权重负载均衡器
public class WeightLoadBalancer implements ReactorLoadBalancer<ServiceInstance> {

    private final ObjectProvider<ServiceInstanceListSupplier> supplierProvider;
    private final String serviceId;

    public WeightLoadBalancer(ObjectProvider<ServiceInstanceListSupplier> supplierProvider, String serviceId) {
        this.supplierProvider = supplierProvider;
        this.serviceId = serviceId;
    }

    @Override
    public Mono<Response<ServiceInstance>> choose(Request request) {
        return supplierProvider.getIfAvailable().get()
            .next()
            .map(instances -> {
                ServiceInstance instance = selectByWeight(instances);
                return new DefaultResponse(instance);
            });
    }

    private ServiceInstance selectByWeight(List<ServiceInstance> instances) {
        // 从元数据读权重，按权重随机选择
        List<ServiceInstance> weighted = new ArrayList<>();
        for (ServiceInstance instance : instances) {
            String weightStr = instance.getMetadata().getOrDefault("weight", "1");
            int weight = Integer.parseInt(weightStr);
            for (int i = 0; i < weight; i++) {
                weighted.add(instance);
            }
        }
        int index = new Random().nextInt(weighted.size());
        return weighted.get(index);
    }
}
```

### 配置服务实例权重（Nacos 元数据）

```yaml
spring:
  cloud:
    nacos:
      discovery:
        metadata:
          weight: 3    # 权重 3（相比默认 1，分配 3 倍流量）
```

## 配合 OpenFeign 使用

OpenFeign 默认集成 LoadBalancer，使用服务名即可自动负载均衡。

```java
@FeignClient(name = "user-service")   // 自动负载均衡到 user-service 实例
public interface UserClient {
    @GetMapping("/users/{id}")
    User getUser(@PathVariable("id") Long id);
}
```

```text
Feign + LoadBalancer 的工作流程：
1. Feign 请求 user-service
2. LoadBalancer 从注册中心获取 user-service 实例列表
3. 按策略（轮询）选择一个实例
4. 请求转发到选中实例
```

### 为指定服务配置策略

```java
@Configuration
public class UserServiceLoadBalancerConfig {

    @Bean
    public ReactorLoadBalancer<ServiceInstance> userServiceLoadBalancer(
            Environment environment, LoadBalancerClientFactory factory) {
        String name = environment.getProperty(LoadBalancerClientFactory.PROPERTY_NAME);
        // 为 user-service 配置随机策略
        return new RandomLoadBalancer(
            factory.getLazyProvider(name, ServiceInstanceListSupplier.class), name);
    }
}
```

```java
// 在 Feign 客户端上指定配置类
@FeignClient(name = "user-service", configuration = UserServiceLoadBalancerConfig.class)
public interface UserClient { ... }
```

## 应用场景实战

### 场景 1：服务间调用负载均衡

```java
// 订单服务调用用户服务（自动负载均衡）
@Service
public class OrderService {

    @Autowired
    private UserClient userClient;   // Feign 自动负载均衡

    public OrderDetail getDetail(Long orderId) {
        Order order = orderMapper.findById(orderId);
        // 自动负载均衡到 user-service 的某个实例
        User user = userClient.getUser(order.getUserId());
        return new OrderDetail(order, user);
    }
}
```

### 场景 2：带权重的负载均衡

```yaml
# user-service 实例 1（性能好，权重 3）
spring:
  application:
    name: user-service
  cloud:
    nacos:
      discovery:
        metadata:
          weight: 3

# user-service 实例 2（性能差，权重 1）
spring:
  application:
    name: user-service
  cloud:
    nacos:
      discovery:
        metadata:
          weight: 1
```

```java
// 自定义权重负载均衡器（见上文），按权重分配流量
// 实例 1 收到 75% 流量，实例 2 收到 25% 流量
```

### 场景 3：灰度发布（版本路由）

```java
// 自定义负载均衡：优先选择新版本实例
public class VersionLoadBalancer implements ReactorLoadBalancer<ServiceInstance> {

    @Override
    public Mono<Response<ServiceInstance>> choose(Request request) {
        // 从请求上下文获取目标版本
        String targetVersion = request.getContext().getOrDefault("version", "v1");

        return supplierProvider.getIfAvailable().get()
            .next()
            .map(instances -> {
                // 优先选择匹配版本的实例
                ServiceInstance instance = instances.stream()
                    .filter(i -> targetVersion.equals(i.getMetadata().get("version")))
                    .findFirst()
                    .orElse(instances.get(0));
                return new DefaultResponse(instance);
            });
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **服务间调用统一用 Feign（自动负载均衡）**。不用手动 LoadBalancerClient + RestTemplate。

2. **实例性能不一致时用加权策略**。通过元数据配置权重，让性能好的实例多扛流量。

3. **负载均衡配合健康检查**。注册中心剔除故障实例，LoadBalancer 才不会选到坏实例。

4. **理解"最终一致"的实例列表**。客户端缓存的实例列表有延迟，故障剔除需要时间。

### 踩坑记录

**坑 1：RestTemplate 没加 @LoadBalanced**

```java
@Bean
public RestTemplate restTemplate() {
    return new RestTemplate();   // 没有 @LoadBalanced
}
// restTemplate.getForObject("http://user-service/...") 报错：UnknownHostException
// "user-service" 不是真实域名，无法解析
```

用服务名调用必须加 @LoadBalanced，否则服务名无法解析为 IP。

**坑 2：Ribbon 和 LoadBalancer 冲突**

```text
同时引入 Ribbon 和 LoadBalancer 的依赖，可能导致冲突
Spring Cloud 2020.0 之后 Ribbon 已废弃，统一用 LoadBalancer
```

检查依赖，移除 Ribbon，只保留 spring-cloud-starter-loadbalancer。

**坑 3：实例下线后仍被选中**

```text
服务实例下线，但客户端缓存的实例列表未及时更新，
短时间内请求仍发到已下线实例（导致失败）
```

这是客户端负载均衡的固有延迟，配合重试机制缓解。

**坑 4：自定义 LoadBalancer 配置不生效**

```java
@Configuration
public class LoadBalancerConfig {
    @Bean
    public ReactorLoadBalancer<ServiceInstance> customLoadBalancer(...) { ... }
}
// 如果配置类被 @ComponentScan 扫描，可能影响所有服务的负载均衡
```

自定义负载均衡配置类要用 @Configuration(proxyBeanMethods=false) 且不被 @ComponentScan 全局扫描（配合 @LoadBalancerClient 指定服务）。

**坑 5：Feign 多实例调用不均衡**

```text
轮询策略在多实例下应该均匀，但如果某个实例响应慢，
可能积累更多请求（缺乏自适应能力）
```

对性能敏感场景，考虑加权或最少连接策略。

**坑 6：WebClient 没配置负载均衡**

```java
// WebFlux 项目用 WebClient，需要额外配置负载均衡
@Bean
@LoadBalanced
public WebClient.Builder loadBalancedWebClientBuilder() {
    return WebClient.builder();
}
```

WebFlux 项目用 WebClient 也要加 @LoadBalanced，并引入 reactor-loadbalancer。
