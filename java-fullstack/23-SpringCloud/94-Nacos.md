---
title: Nacos
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [nacos, 服务注册, 服务发现, 配置中心, 动态配置, 命名空间, 分组, 集群]
---

# Nacos

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Nacos 安装与启动](#nacos-安装与启动)
- [服务注册与发现](#服务注册与发现)
- [配置中心](#配置中心)
- [动态配置刷新](#动态配置刷新)
- [命名空间 Namespace](#命名空间-namespace)
- [分组 Group](#分组-group)
- [Nacos 集群](#nacos-集群)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Nacos（Dynamic Naming and Configuration Service）是阿里巴巴开源的服务注册发现和配置中心，一个组件同时提供两大能力。

```text
Nacos = 服务注册发现（Naming） + 配置中心（Configuration）

核心功能：
1. 服务注册 —— 服务启动时注册到 Nacos
2. 服务发现 —— 调用方从 Nacos 获取服务地址
3. 配置管理 —— 配置集中管理
4. 动态配置 —— 配置变更实时推送
```

```text
Nacos vs Eureka：
Nacos 支持 AP 和 CP 两种模式（可切换），Eureka 只支持 AP
Nacos 同时提供配置中心，Eureka 没有
Nacos 支持健康检查（主动探测 + 心跳），Eureka 只有心跳
```

## Nacos 安装与启动

### 单机启动

```bash
# 下载并启动（Windows/Linux）
# 单机模式
startup.sh -m standalone

# 默认地址
# 控制台：http://localhost:8848/nacos
# 默认账号密码：nacos/nacos
```

### Docker 启动

```bash
docker run -d \
  --name nacos \
  -p 8848:8848 \
  -e MODE=standalone \
  nacos/nacos-server:latest
```

## 服务注册与发现

### 引入依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
```

### 服务注册（提供者）

```yaml
spring:
  application:
    name: order-service    # 服务名（注册到 Nacos 的名称）
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848   # Nacos 地址
        username: nacos
        password: nacos
```

```java
@SpringBootApplication
@EnableDiscoveryClient   // 启用服务注册发现
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}
```

启动后，服务自动注册到 Nacos，控制台可看到 order-service。

### 服务发现（消费者）

```java
@RestController
public class OrderController {

    @Autowired
    private DiscoveryClient discoveryClient;

    @GetMapping("/services")
    public List<String> listServices() {
        // 获取所有服务名
        return discoveryClient.getServices();
    }

    @GetMapping("/instances")
    public List<ServiceInstance> getInstances() {
        // 获取指定服务的所有实例
        return discoveryClient.getInstances("user-service");
    }
}
```

### 服务调用

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
        String url = "http://" + instance.getHost() + ":" + instance.getPort() + "/users/" + userId;
        return restTemplate.getForObject(url, User.class);
    }
}
```

### 服务元数据

```yaml
spring:
  cloud:
    nacos:
      discovery:
        metadata:         # 自定义元数据
          version: v1
          region: beijing
          weight: 100
```

## 配置中心

Nacos 作为配置中心，集中管理各服务的配置。

### 引入依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
</dependency>
```

### 配置文件

```yaml
# bootstrap.yml（Spring Boot 2.4 前的配置加载顺序）
spring:
  application:
    name: order-service
  cloud:
    nacos:
      config:
        server-addr: localhost:8848
        file-extension: yml          # 配置文件格式
        group: DEFAULT_GROUP         # 分组
        namespace: public            # 命名空间
```

### Nacos 配置规则

```text
Nacos 中的 Data ID 命名规则：
{spring.application.name}-{profile}.{file-extension}

例如：
order-service.yml                —— 默认配置
order-service-dev.yml            —— dev 环境配置
order-service-prod.yml           —— prod 环境配置
```

### 读取配置

```java
// 通过 @Value 读取（支持动态刷新需 @RefreshScope）
@RestController
@RefreshScope          // 配置变更时动态刷新
public class ConfigController {

    @Value("${app.name}")
    private String appName;

    @Value("${app.timeout:30}")
    private int timeout;

    @GetMapping("/config")
    public Map<String, Object> getConfig() {
        return Map.of("appName", appName, "timeout", timeout);
    }
}
```

## 动态配置刷新

Nacos 的配置变更可以实时推送到应用，实现不改代码、不重启的动态配置。

### @RefreshScope 注解

```java
@RestController
@RefreshScope   // 标注后，配置变更时重新注入
public class DynamicConfigController {

    @Value("${app.feature.enabled:false}")
    private boolean featureEnabled;

    @GetMapping("/feature")
    public boolean isFeatureEnabled() {
        return featureEnabled;
    }
}
```

### 配置刷新机制

```text
1. 修改 Nacos 配置
2. Nacos 推送变更通知到订阅的应用
3. 应用刷新 @RefreshScope 标注的 Bean
4. 新配置生效，无需重启
```

### 监听配置变更

```java
@Component
public class ConfigListener {

    @NacosValue(value = "${app.timeout:30}", autoRefreshed = true)
    private int timeout;

    // 或编程式监听
    @Autowired
    private NacosConfigManager nacosConfigManager;

    public void addListener() throws NacosException {
        nacosConfigManager.getConfigService().addListener(
            "order-service.yml", "DEFAULT_GROUP",
            new Listener() {
                @Override
                public Executor getExecutor() { return null; }

                @Override
                public void receiveConfigInfo(String configInfo) {
                    // 配置变更回调
                    System.out.println("配置更新：" + configInfo);
                }
            });
    }
}
```

## 命名空间 Namespace

命名空间用于隔离不同环境（或不同租户）的配置和注册。

### 命名空间的用途

```text
默认命名空间 public：
- dev 环境 → dev 命名空间
- test 环境 → test 命名空间
- prod 环境 → prod 命名空间

隔离级别：
1. 配置隔离：不同命名空间的配置互不可见
2. 服务隔离：不同命名空间的服务互不发现
```

### 配置命名空间

```yaml
spring:
  cloud:
    nacos:
      discovery:
        namespace: dev-namespace-id     # 服务注册的命名空间
      config:
        namespace: dev-namespace-id     # 配置的命名空间
```

### 命名空间 vs Profile

```text
命名空间（Namespace）：
- 隔离粒度大（环境、租户）
- 物理隔离，跨命名空间完全不可见

Profile：
- 隔离粒度小（同环境的不同配置）
- 逻辑隔离，同一命名空间内
```

## 分组 Group

分组用于在同一命名空间内进一步细分配置和服务。

### 分组的用途

```text
默认分组 DEFAULT_GROUP：
- 稳定版服务 → stable 分组
- 灰度版服务 → gray 分组
- 同命名空间内，不同分组隔离
```

### 配置分组

```yaml
spring:
  cloud:
    nacos:
      discovery:
        group: gray-group       # 服务分组
      config:
        group: gray-group       # 配置分组
```

### Namespace + Group 的层级

```text
Namespace（环境隔离）
  └── Group（分组隔离）
        └── Data ID（具体配置）
        └── 服务实例
```

## Nacos 集群

生产环境 Nacos 必须集群部署，保证高可用。

### 集群架构

```text
        ┌─────────────┐
        │   Nginx     │  （负载均衡）
        └──────┬──────┘
       ┌───────┼───────┐
   ┌───┴───┐ ┌─┴────┐ ┌┴────┐
   │Nacos1 │ │Nacos2│ │Nacos3│  （Nacos 集群）
   └───┬───┘ └──┬───┘ └─┬────┘
       └────────┴────────┘
                │
        ┌───────┴───────┐
        │  MySQL 集群    │  （存储注册/配置数据）
        └───────────────┘
```

### 集群配置

```properties
# cluster.conf（每个 Nacos 节点配置集群成员）
192.168.1.1:8848
192.168.1.2:8848
192.168.1.3:8848
```

```properties
# application.properties（使用 MySQL 存储）
spring.datasource.platform=mysql
db.num=1
db.url.0=jdbc:mysql://mysql-host:3306/nacos_config
db.user=root
db.password=secret
```

### 客户端连接集群

```yaml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: 192.168.1.1:8848,192.168.1.2:8848,192.168.1.3:8848
```

### 集群模式选择

```text
AP 模式（默认）：高可用优先，可能短暂不一致
CP 模式：一致性优先，服务注册用 CP

切换：curl -X PUT 'http://nacos:8848/nacos/v1/ns/operator/switches?entry=serverMode&value=CP'
```

## 应用场景实战

### 场景 1：多环境配置隔离

```text
命名空间规划：
dev-namespace   —— 开发环境
test-namespace  —— 测试环境
prod-namespace  —— 生产环境
```

```yaml
# dev 环境配置
spring:
  cloud:
    nacos:
      config:
        namespace: dev-namespace-id
        group: DEFAULT_GROUP
```

```text
Nacos 配置：
dev-namespace/order-service.yml
  server.port: 8081
  spring.datasource.url: jdbc:mysql://dev-db:3306/order

prod-namespace/order-service.yml
  server.port: 8080
  spring.datasource.url: jdbc:mysql://prod-db:3306/order
```

### 场景 2：动态配置开关

```java
@RestController
@RefreshScope
public class FeatureController {

    @Value("${feature.new-ui:false}")
    private boolean newUiEnabled;

    @Value("${feature.max-upload-size:10}")
    private int maxUploadSize;

    @GetMapping("/feature/new-ui")
    public boolean isNewUiEnabled() {
        return newUiEnabled;
    }
}
```

```yaml
# Nacos 配置，运行时修改无需重启
feature:
  new-ui: true
  max-upload-size: 50
```

### 场景 3：灰度发布（分组）

```text
分组规划：
DEFAULT_GROUP  —— 稳定版本
gray-group     —— 灰度版本
```

```yaml
# 灰度服务实例
spring:
  cloud:
    nacos:
      discovery:
        group: gray-group
```

```java
// 消费者按分组发现灰度服务
@Configuration
public class GrayConfig {

    @Bean
    @LoadBalanced
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **命名空间按环境隔离**。dev/test/prod 用独立命名空间，防止配置串环境。

2. **生产环境 Nacos 集群 + MySQL**。避免单点故障和数据丢失。

3. **动态配置用 @RefreshScope**。需要实时刷新的配置加 @RefreshScope，否则改动不生效。

4. **配置优先级明确**。Nacos 配置 > 本地配置，敏感信息用环境变量覆盖。

5. **服务下线要优雅**。优雅停机时主动注销服务，避免流量打到已下线实例。

### 踩坑记录

**坑 1：bootstrap.yml 不生效**

```text
Spring Boot 2.4 之前用 bootstrap.yml 加载 Nacos 配置，
2.4 之后默认不加载 bootstrap.yml，需要引入 spring-cloud-starter-bootstrap 依赖
```

Spring Boot 2.4+ 需要额外引入 `spring-cloud-starter-bootstrap`，或用 `spring.config.import`。

**坑 2：配置不刷新**

```java
@RestController
public class ConfigController {
    @Value("${app.timeout}")
    private int timeout;   // 没有 @RefreshScope，Nacos 配置改了不生效
}
```

需要动态刷新的 Bean 加 @RefreshScope。

**坑 3：服务名与配置 Data ID 不匹配**

```text
服务名：order-service
Nacos 配置 Data ID：order_service.yml（下划线）
两者不匹配，读不到配置
```

Data ID 的 {spring.application.name} 部分必须与服务名完全一致。

**坑 4：命名空间 ID 写错**

```yaml
spring:
  cloud:
    nacos:
      config:
        namespace: dev   # 写成了命名空间名称，实际要写 namespace ID
```

命名空间要填 ID（一串随机字符），不是名称。

**坑 5：客户端缓存导致服务发现延迟**

```text
服务下线后，消费者可能还在缓存里读到已下线实例，
直到缓存刷新（默认几秒到几十秒）
```

Nacos 客户端有本地缓存，服务下线到消费者感知有延迟，属正常现象。

**坑 6：端口冲突**

```text
Nacos 默认端口 8848，如果和本地其他服务冲突
或 Nacos 2.x 需要额外开放 gRPC 端口（9848、9849）
```

Nacos 2.x 除了 8848，还需要 9848（gRPC 客户端）、9849（gRPC 服务端）端口，Docker 部署时注意映射。
