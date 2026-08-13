---
title: Spring Boot Starter
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-boot, starter, auto-configuration, autoconfiguration-imports, conditional, 自定义starter]
---

# Spring Boot Starter

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Starter 原理](#starter-原理)
- [自动配置的实现机制](#自动配置的实现机制)
- [条件注解详解](#条件注解详解)
- [自定义 Starter 完整步骤](#自定义-starter-完整步骤)
- [配置属性类与元数据](#配置属性类与元数据)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Starter 是 Spring Boot 的核心扩展机制。它把某个功能的**依赖管理**和**自动配置**打包在一起，让使用者只需引入一个依赖就能获得完整功能。

```text
Starter 解决的两个问题：
1. 依赖管理 —— 聚合功能需要的所有 jar，版本统一
2. 自动配置 —— 根据 classpath 自动创建所需的 Bean

例子：
引入 spring-boot-starter-data-redis 后，无需任何配置，
Spring Boot 自动：
- 创建 RedisConnectionFactory
- 创建 RedisTemplate
- 创建 StringRedisTemplate
- 绑定 spring.redis.* 配置
```

## Starter 原理

### Starter 的两模块结构

一个完整的 Starter 通常由两个模块组成：

```text
myproject-spring-boot-starter（Starter 模块）
├── pom.xml                          ← 只有依赖声明，无 Java 代码
└── （无源码）

myproject-spring-boot-autoconfigure（自动配置模块）
├── pom.xml                          ← 依赖 + 编译自动配置类
├── src/main/java/
│   └── com/myproject/
│       ├── MyServiceAutoConfiguration.java   ← 自动配置类
│       └── MyProperties.java                 ← 配置属性类
└── src/main/resources/
    └── META-INF/spring/
        └── org.springframework.boot.autoconfigure.AutoConfiguration.imports  ← 注册文件
```

```text
Starter 模块（聚合依赖）
    ↓ 依赖
自动配置模块（实现逻辑）
    ↓ 自动装配
使用者项目
```

### 为什么分两个模块

- **Starter 模块**：让使用者只关心"引入什么功能"，不关心内部依赖
- **自动配置模块**：与 Starter 解耦，可以独立测试、独立更新

这种分离让使用者可以只引入自动配置模块（绕过 Starter），或替换 Starter 中的某个依赖版本。

### 官方 Starter 的命名规范

```text
官方 Starter：
spring-boot-starter-{功能}          （前缀 spring-boot-starter-）

第三方 Starter（自定义）：
{项目}-spring-boot-starter          （后缀 -spring-boot-starter）

自动配置模块：
{项目}-spring-boot-autoconfigure    （后缀 -spring-boot-autoconfigure）
```

命名是约定，不是强制。但遵循约定能让人一眼识别模块用途。

## 自动配置的实现机制

### AutoConfiguration.imports 文件

这是自动配置的注册入口。Spring Boot 3.x 之前的 `spring.factories` 已废弃，改用：

```text
位置：META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
内容：每行一个自动配置类的全限定名
```

```text
# org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.myproject.autoconfigure.MyServiceAutoConfiguration
com.myproject.autoconfigure.MyCacheAutoConfiguration
```

### 自动配置的加载流程

```text
1. @EnableAutoConfiguration 触发 AutoConfigurationImportSelector
2. 选择器通过 SpringFactoriesLoader 读取所有 AutoConfiguration.imports 文件
3. 汇总所有自动配置类（Spring Boot 内置 + 第三方）
4. 对每个自动配置类进行条件评估（@Conditional 注解）
5. 满足条件的自动配置类生效，其 @Bean 方法创建 Bean
```

```java
// AutoConfigurationImportSelector 的核心逻辑（简化）
protected List<String> getCandidateConfigurations(AnnotationMetadata metadata, ...) {
    // 读取所有 META-INF/spring/...AutoConfiguration.imports 文件
    return ImportCandidates.load(AutoConfiguration.class, beanClassLoader)
        .getCandidates();
    // 返回所有自动配置类的全限定名列表
}
```

### 自动配置类的写法

```java
@AutoConfiguration                    // 标记为自动配置类（Spring Boot 3.x 引入，替代 @Configuration）
@ConditionalOnClass(MyService.class)  // classpath 有 MyService 才生效
@EnableConfigurationProperties(MyProperties.class)  // 启用配置属性类
public class MyServiceAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean          // 用户没自定义才创建
    public MyService myService(MyProperties properties) {
        return new MyService(properties);
    }
}
```

### 自动配置类的执行顺序

```java
@AutoConfiguration(after = OtherAutoConfiguration.class)  // 在某个之后
@AutoConfiguration(before = AnotherAutoConfiguration.class)  // 在某个之前
@AutoConfigureAfter(DataSourceAutoConfiguration.class)    // 老注解，等价
@AutoConfigureBefore(...)
@AutoConfigureOrder(Ordered.HIGHEST_PRECEDENCE)           // 指定顺序
public class MyAutoConfiguration { }
```

## 条件注解详解

条件注解是自动配置的"开关"，决定配置类是否生效。

### 核心条件注解

| 注解 | 条件 |
|------|------|
| @ConditionalOnClass | classpath 存在指定类 |
| @ConditionalOnMissingClass | classpath 不存在指定类 |
| @ConditionalOnBean | 容器中存在指定 Bean |
| @ConditionalOnMissingBean | 容器中不存在指定 Bean |
| @ConditionalOnProperty | 配置属性满足条件 |
| @ConditionalOnResource | classpath 存在指定资源 |
| @ConditionalOnWebApplication | 是 Web 应用 |
| @ConditionalOnNotWebApplication | 不是 Web 应用 |
| @ConditionalOnExpression | SpEL 表达式为 true |
| @ConditionalOnJava | Java 版本满足条件 |

### @ConditionalOnClass

```java
@Configuration
@ConditionalOnClass(RedisOperations.class)  // 有 Redis 依赖才生效
public class RedisAutoConfiguration {
    // ...
}

// value 和 name 二选一（name 用于类不在编译路径的情况）
@ConditionalOnClass(name = "com.mysql.cj.jdbc.Driver")
```

### @ConditionalOnMissingBean

```java
@Bean
@ConditionalOnMissingBean(RedisTemplate.class)  // 用户没定义 RedisTemplate 才创建
public RedisTemplate<String, Object> redisTemplate() {
    return new RedisTemplate<>();
}

// 按名称判断
@ConditionalOnMissingBean(name = "customRedisTemplate")

// 按类型 + 名称
@ConditionalOnMissingBean(type = "org.springframework.data.redis.core.RedisTemplate")
```

### @ConditionalOnProperty

```java
@Bean
@ConditionalOnProperty(name = "my.feature.enabled", havingValue = "true")
public FeatureService featureService() { ... }

// 属性存在即生效（不要求值）
@ConditionalOnProperty(name = "my.feature.enabled")

// 属性不存在也生效（matchIfMissing）
@ConditionalOnProperty(name = "my.feature.enabled", havingValue = "true", matchIfMissing = true)

// 前缀 + 多个属性
@ConditionalOnProperty(prefix = "my.feature", name = {"enabled", "beta"}, havingValue = "true")
```

### 自定义条件

```java
// 实现 Condition 接口
public class OnLinuxCondition implements Condition {
    @Override
    public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        Environment env = context.getEnvironment();
        String os = env.getProperty("os.name");
        return os != null && os.toLowerCase().contains("linux");
    }
}

// 使用
@Configuration
@Conditional(OnLinuxCondition.class)
public class LinuxOnlyConfig { }
```

### 组合条件

```java
// 多个条件 AND 关系（全部满足才生效）
@Configuration
@ConditionalOnClass(DataSource.class)
@ConditionalOnProperty(name = "spring.datasource.url")
public class DataSourceAutoConfiguration { }

// 条件嵌套（类和方法级别组合）
@Configuration
@ConditionalOnClass(MyService.class)
public class MyAutoConfiguration {
    @Bean
    @ConditionalOnMissingBean          // 类级别 + 方法级别条件都要满足
    public MyService myService() { ... }
}
```

## 自定义 Starter 完整步骤

以自定义一个"短信服务"Starter 为例，展示完整流程。

### 第 1 步：创建自动配置模块

```text
sms-spring-boot-autoconfigure/
├── pom.xml
└── src/main/java/com/example/sms/
    ├── SmsProperties.java
    ├── SmsService.java
    ├── AliyunSmsService.java
    ├── MockSmsService.java
    └── SmsAutoConfiguration.java
└── src/main/resources/META-INF/spring/
    └── org.springframework.boot.autoconfigure.AutoConfiguration.imports
```

### 第 2 步：定义配置属性类

```java
@ConfigurationProperties(prefix = "sms")
public class SmsProperties {

    private boolean enabled = true;
    private String provider = "aliyun";   // aliyun / mock
    private String accessKeyId;
    private String accessKeySecret;
    private String signName;
    private int timeout = 5000;

    // getter/setter
}
```

### 第 3 步：定义服务接口和实现

```java
public interface SmsService {
    void send(String phone, String content);
}

public class AliyunSmsService implements SmsService {
    private final SmsProperties properties;

    public AliyunSmsService(SmsProperties properties) {
        this.properties = properties;
    }

    @Override
    public void send(String phone, String content) {
        // 调用阿里云短信 API
        System.out.println("阿里云发送：" + phone + " -> " + content);
    }
}

public class MockSmsService implements SmsService {
    @Override
    public void send(String phone, String content) {
        // 测试环境不打真短信，只打印日志
        System.out.println("[Mock] 发送短信：" + phone + " -> " + content);
    }
}
```

### 第 4 步：编写自动配置类

```java
@AutoConfiguration
@ConditionalOnClass(SmsService.class)
@EnableConfigurationProperties(SmsProperties.class)
public class SmsAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(prefix = "sms", name = "enabled", havingValue = "true", matchIfMissing = true)
    public SmsService smsService(SmsProperties properties) {
        if ("mock".equals(properties.getProvider())) {
            return new MockSmsService();
        }
        return new AliyunSmsService(properties);
    }
}
```

### 第 5 步：注册自动配置类

```text
# META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.sms.SmsAutoConfiguration
```

### 第 6 步：创建 Starter 模块

```xml
<!-- sms-spring-boot-starter/pom.xml -->
<artifactId>sms-spring-boot-starter</artifactId>

<dependencies>
    <!-- 依赖自动配置模块 -->
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>sms-spring-boot-autoconfigure</artifactId>
        <version>1.0.0</version>
    </dependency>
    <!-- 依赖阿里云 SDK（可选，仅 aliyun provider 需要） -->
    <dependency>
        <groupId>com.aliyun</groupId>
        <artifactId>aliyun-java-sdk-core</artifactId>
    </dependency>
</dependencies>
```

### 第 7 步：使用者引入

```xml
<!-- 使用者的 pom.xml -->
<dependency>
    <groupId>com.example</groupId>
    <artifactId>sms-spring-boot-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
# 使用者的配置
sms:
  enabled: true
  provider: aliyun
  access-key-id: ${SMS_ACCESS_KEY}
  access-key-secret: ${SMS_ACCESS_SECRET}
  sign-name: 我的应用
```

```java
// 使用者直接注入使用
@Service
public class UserService {
    @Autowired
    private SmsService smsService;  // 自动配置好的

    public void notifyUser(String phone) {
        smsService.send(phone, "您的订单已发货");
    }
}
```

## 配置属性类与元数据

### 配置元数据（Configuration Metadata）

为了让 IDE 在编写 application.yml 时能提示配置项，需要生成配置元数据：

```xml
<!-- 自动配置模块 pom.xml 中添加注解处理器 -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-configuration-processor</artifactId>
    <optional>true</optional>
</dependency>
```

编译时自动生成 `META-INF/spring-configuration-metadata.json`：

```json
{
  "groups": [
    {
      "name": "sms",
      "type": "com.example.sms.SmsProperties",
      "sourceType": "com.example.sms.SmsProperties"
    }
  ],
  "properties": [
    {
      "name": "sms.enabled",
      "type": "java.lang.Boolean",
      "description": "是否启用短信服务",
      "sourceType": "com.example.sms.SmsProperties",
      "defaultValue": true
    },
    {
      "name": "sms.provider",
      "type": "java.lang.String",
      "description": "短信服务商：aliyun / mock"
    }
  ]
}
```

有了元数据，IDE 会自动提示 `sms.*` 的配置项和说明。

### @ConfigurationProperties 的 description

```java
@ConfigurationProperties(prefix = "sms")
public class SmsProperties {

    /** 短信服务商：aliyun / mock */
    private String provider = "aliyun";

    /** 是否启用短信服务 */
    private boolean enabled = true;
    // Javadoc 注释会生成到元数据的 description 中
}
```

## 应用场景实战

### 场景 1：自定义日志 Starter

```java
// LogProperties
@ConfigurationProperties(prefix = "mylog")
public class LogProperties {
    private boolean enabled = true;
    private String level = "INFO";
    private String format = "[{time}] {level} {message}";
    // getter/setter
}

// LogAutoConfiguration
@AutoConfiguration
@ConditionalOnProperty(prefix = "mylog", name = "enabled", havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(LogProperties.class)
public class LogAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public LogService logService(LogProperties properties) {
        return new LogService(properties);
    }
}

// 使用者
mylog:
  level: DEBUG
  format: "{time} - {level} - {message}"
```

### 场景 2：带 @ConditionalOnMissingBean 的扩展点

```java
@AutoConfiguration
@EnableConfigurationProperties(MyProperties.class)
public class MyAutoConfiguration {

    // 默认实现
    @Bean
    @ConditionalOnMissingBean
    public MyService myService(MyProperties properties) {
        return new DefaultMyService(properties);
    }

    // 钩子：用户可以通过自定义 Bean 覆盖默认实现
    // 使用者只需自己定义一个 MyService Bean，自动配置就退让
}
```

### 场景 3：条件化加载多个实现

```java
@AutoConfiguration
@EnableConfigurationProperties(CacheProperties.class)
public class CacheAutoConfiguration {

    @Bean
    @ConditionalOnProperty(prefix = "cache", name = "type", havingValue = "redis")
    @ConditionalOnClass(RedisOperations.class)
    public CacheService redisCache() {
        return new RedisCacheService();
    }

    @Bean
    @ConditionalOnProperty(prefix = "cache", name = "type", havingValue = "local", matchIfMissing = true)
    public CacheService localCache() {
        return new LocalCacheService();
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **自动配置类要用 @AutoConfiguration 而非 @Configuration**。Spring Boot 3.x 引入 @AutoConfiguration，语义更清晰，且自动配置类不会被组件扫描重复加载。

2. **每个 @Bean 都加 @ConditionalOnMissingBean**。让使用者能通过自定义 Bean 覆盖默认实现，这是 Starter 的"定制化入口"。

3. **配置属性类提供默认值**。让使用者在零配置时也能正常工作，符合"约定优于配置"。

4. **Starter 只做依赖聚合，逻辑放 autoconfigure**。保持模块职责单一，autoconfigure 可独立测试。

5. **生成配置元数据**。添加 `spring-boot-configuration-processor`，让 IDE 能提示配置项，提升使用体验。

### 踩坑记录

**坑 1：自动配置类没被注册**

```text
自动配置类写好了，但没在 AutoConfiguration.imports 文件中注册，
使用者引入后不生效。
```

检查：`META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 中是否有类名，且文件路径完全正确。

**坑 2：@ConditionalOnClass 用 name 和 value 的区别**

```java
@ConditionalOnClass(RedisOperations.class)   // 编译期就要有这个类
@ConditionalOnClass(name = "com.example.SomeClass")  // 运行期按名称判断
```

如果判断的类在 autoconfigure 模块的编译依赖里，用 `value`；如果类只是"可能存在"（optional 依赖），用 `name` 避免编译期强依赖。

**坑 3：@ConditionalOnBean 顺序问题**

```java
@Bean
@ConditionalOnBean(DataSource.class)  // DataSource 可能还没创建！
public MyService myService() { ... }
```

`@ConditionalOnBean` 依赖 Bean 创建顺序。如果 DataSource 是后创建的，条件判断为 false。用 `@AutoConfigureAfter(DataSourceAutoConfiguration.class)` 控制顺序。

**坑 4：Starter 命名错误**

```text
官方前缀 spring-boot-starter- 是保留的，
自定义 Starter 用 spring-boot-starter-mystarter 会与官方命名空间冲突
```

自定义 Starter 用 `{项目}-spring-boot-starter` 后缀形式。

**坑 5：spring.factories 不生效**

```text
Spring Boot 2.x 用 spring.factories 注册自动配置，
Spring Boot 3.x 改用 AutoConfiguration.imports，
混用或路径写错都会导致不生效。
```

Spring Boot 3.x 中 `spring.factories` 的 `EnableAutoConfiguration` 已废弃，必须用 `AutoConfiguration.imports`。

**坑 6：自动配置类被 @ComponentScan 扫描到导致双重注册**

```java
// 如果 autoconfigure 模块的类在 @ComponentScan 范围内，且用了 @Configuration 而非 @AutoConfiguration，
// 可能导致 Bean 被注册两次
```

自动配置类应放在独立包，用 @AutoConfiguration 标记，避免被使用者的组件扫描捕获。
