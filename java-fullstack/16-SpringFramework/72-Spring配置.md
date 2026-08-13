---
title: Spring 配置
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring, configuration, xml, java-config, annotation, componentscan, conditional, profile, import]
---

# Spring 配置

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [XML 配置](#xml-配置)
- [注解配置](#注解配置)
- [Java Config](#java-config)
- [@Configuration 与 @Bean](#configuration-与-bean)
- [编程式注册 Bean](#编程式注册-bean)
- [组件扫描](#组件扫描)
- [@Component 与衍生注解](#component-与衍生注解)
- [条件化配置](#条件化配置)
- [Environment 抽象](#environment-抽象)
- [配置属性注入](#配置属性注入)
- [配置方式对比与选择](#配置方式对比与选择)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring 容器需要知道"管理哪些 Bean"和"Bean 之间如何依赖"。配置就是告诉容器这些信息的方式。Spring 提供了三种配置方式，按历史演进顺序是：XML → 注解 → Java Config。

Spring Boot 项目中，Java Config + 注解是标配，XML 几乎不再使用。但理解 XML 配置有助于阅读遗留项目和理解 Spring 底层机制（Spring 内部大量使用基于 XML 的扩展机制）。

## XML 配置

XML 是 Spring 最早的配置方式，也是理解 Spring 底层运作方式的好入口。

### 基本结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:context="http://www.springframework.org/schema/context"
       xsi:schemaLocation="
           http://www.springframework.org/schema/beans
           http://www.springframework.org/schema/beans/spring-beans.xsd
           http://www.springframework.org/schema/context
           http://www.springframework.org/schema/context/spring-context.xsd">

    <!-- Bean 定义在这里 -->

</beans>
```

### 定义 Bean

```xml
<!-- 最简 Bean，通过无参构造器创建 -->
<bean id="userDao" class="com.example.dao.UserDaoImpl" />

<!-- 通过工厂方法创建 -->
<bean id="dataSource" class="com.zaxxer.hikari.HikariDataSource"
      destroy-method="close">
    <property name="jdbcUrl" value="jdbc:mysql://localhost:3306/mydb" />
    <property name="username" value="root" />
    <property name="password" value="secret" />
</bean>

<!-- 构造器注入 -->
<bean id="userService" class="com.example.service.UserService">
    <constructor-arg index="0" ref="userDao" />
    <constructor-arg index="1" value="admin" />
</bean>

<!-- setter 注入 -->
<bean id="orderService" class="com.example.service.OrderService">
    <property name="userDao" ref="userDao" />
    <property name="timeout" value="30" />
</bean>

<!-- 注入集合 -->
<bean id="complexBean" class="com.example.ComplexBean">
    <property name="stringList">
        <list>
            <value>item1</value>
            <value>item2</value>
        </list>
    </property>
    <property name="stringMap">
        <map>
            <entry key="key1" value="value1" />
            <entry key="key2" value-ref="userDao" />
        </map>
    </property>
    <property name="stringSet">
        <set>
            <value>a</value>
            <value>b</value>
        </set>
    </property>
    <property name="properties">
        <props>
            <prop key="app.name">MyApp</prop>
            <prop key="app.version">1.0</prop>
        </props>
    </property>
</bean>
```

### Bean 作用域与生命周期

```xml
<bean id="userService" class="com.example.service.UserService"
      scope="singleton"          <!-- singleton / prototype / request / session -->
      lazy-init="true"           <!-- 懒加载，不默认等同于 false -->
      init-method="init"         <!-- 初始化方法 -->
      destroy-method="cleanup"   <!-- 销毁方法 -->
      depends-on="userDao" />    <!-- 依赖的 Bean（用于控制创建顺序） -->
```

### 加载 XML 配置

```java
ApplicationContext context = new ClassPathXmlApplicationContext("applicationContext.xml");
UserService service = context.getBean(UserService.class);
```

### XML 命名空间

Spring 为特定功能提供了专用命名空间，简化 XML 配置：

```xml
<beans xmlns:context="http://www.springframework.org/schema/context"
       xmlns:tx="http://www.springframework.org/schema/tx"
       xmlns:aop="http://www.springframework.org/schema/aop">

    <!-- context 命名空间：启用注解 -->
    <context:component-scan base-package="com.example" />
    <context:property-placeholder location="classpath:app.properties" />

    <!-- tx 命名空间：声明式事务 -->
    <tx:annotation-driven transaction-manager="transactionManager" />

    <!-- aop 命名空间：AOP 配置 -->
    <aop:config>
        <aop:pointcut id="serviceMethods" expression="execution(* com.example.service.*.*(..))" />
        <aop:advisor advice-ref="txAdvice" pointcut-ref="serviceMethods" />
    </aop:config>
</beans>
```

### XML 配置的缺点

- 过于冗长——每个 Bean 都要写一行 `<bean>`
- 编译时不检查——类名写错要到运行时才发现
- IDE 支持弱——重构类名/包名时 XML 不会自动更新
- 类型不安全——ref 的值是字符串，没有类型检查

## 注解配置

注解配置是 Spring 2.5 引入的中间方案——用注解标记 Bean 但仍需 XML 或配置类来启动注解扫描。

### 启用注解扫描

```xml
<!-- XML 方式启用 -->
<context:component-scan base-package="com.example" />
```

```java
// Java Config 方式启用
@Configuration
@ComponentScan("com.example")
public class AppConfig {}
```

### 常用注解一览

| 注解 | 作用 | 说明 |
|------|------|------|
| @Component | 标记为 Spring Bean | 通用组件 |
| @Service | 标记为业务层 Bean | 语义上属于 Service |
| @Repository | 标记为持久层 Bean | 额外提供异常翻译（持久层异常→DataAccessException） |
| @Controller | 标记为 Web 层 Bean | Spring MVC 的控制器 |
| @Configuration | 标记为配置类 | 类中可包含 @Bean 方法 |
| @Bean | 方法返回值注册为 Bean | 用在 @Configuration 类中 |
| @Autowired | 自动注入依赖 | 按类型注入 |
| @Qualifier | 指定注入的 Bean 名称 | 配合 @Autowired |
| @Value | 注入配置值 | 支持 SpEL |
| @Scope | 指定 Bean 作用域 | singleton/prototype/request/session |
| @Lazy | 懒加载 | 容器启动时不创建 |
| @Primary | 标记为首选 Bean | 多个同类型时优先注入 |
| @PostConstruct | 初始化回调 | JSR-250 |
| @PreDestroy | 销毁回调 | JSR-250 |
| @Profile | 环境激活条件 | dev/test/prod |
| @Conditional | 条件化注册 | 自定义条件 |

## Java Config

Java Config 是 Spring 3.0 引入的纯 Java 配置方式，Spring Boot 的默认配置方式。

### @Configuration

```java
@Configuration
public class AppConfig {

    @Bean
    public UserDao userDao() {
        return new UserDaoImpl();
    }

    @Bean
    public UserService userService() {
        // 方法调用方式注入 —— 返回的是同一个 userDao 实例（CGLIB 保证）
        return new UserService(userDao());
    }

    @Bean
    public UserService userService2(UserDao userDao) {
        // 参数注入方式 —— 更清晰
        return new UserService(userDao);
    }
}
```

`@Configuration` 标注的类会被 CGLIB 代理。这意味着 `userDao()` 方法被调用多次时，返回的是容器中的同一个实例（Singleton），而不是每次都 new。

### @Bean

`@Bean` 将一个方法的返回值注册到 Spring 容器中。它比简单的 `@Component` 更灵活——可以在方法内写任何代码来决定如何创建 Bean。

```java
@Configuration
public class DataSourceConfig {

    @Bean
    @Scope("singleton")
    @Lazy(false)
    public DataSource dataSource(
            @Value("${db.url}") String url,
            @Value("${db.username}") String username,
            @Value("${db.password}") String password) {

        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(url);
        config.setUsername(username);
        config.setPassword(password);
        config.setMaximumPoolSize(20);
        config.setMinimumIdle(5);
        config.setConnectionTimeout(30000);
        return new HikariDataSource(config);
    }

    // 定义两个同类型的 Bean，用名称区分
    @Bean("mysqlDataSource")
    @Primary
    public DataSource mysqlDataSource() {
        return createDataSource("mysql");
    }

    @Bean("postgresDataSource")
    public DataSource postgresDataSource() {
        return createDataSource("postgres");
    }

    // initMethod 和 destroyMethod
    @Bean(initMethod = "init", destroyMethod = "close")
    public SomeResource someResource() {
        return new SomeResource();
    }
}
```

### @ComponentScan

`@ComponentScan` 告诉 Spring 在哪些包及其子包下扫描 `@Component` 注解：

```java
@Configuration
@ComponentScan(
    basePackages = {"com.example.service", "com.example.dao"},
    excludeFilters = {
        @ComponentScan.Filter(type = FilterType.REGEX, pattern = ".*TestBean"),
        @ComponentScan.Filter(type = FilterType.ASSIGNABLE_TYPE, classes = OldDao.class)
    },
    includeFilters = {
        @ComponentScan.Filter(type = FilterType.ANNOTATION, classes = MyCustomAnnotation.class)
    }
)
public class AppConfig {}
```

**Spring Boot 自动扫描**：`@SpringBootApplication` 内部包含 `@ComponentScan`，默认扫描启动类所在包及其子包。

```java
// SpringBootApplication 的三合一
@SpringBootConfiguration   // = @Configuration
@EnableAutoConfiguration   // Spring Boot 自动配置
@ComponentScan             // 组件扫描（默认扫描当前包及子包）
public @interface SpringBootApplication {}
```

### @Import

`@Import` 用于导入其他配置类或直接导入类注册为 Bean：

```java
@Configuration
@Import({ServiceConfig.class, DaoConfig.class})
public class AppConfig {}

// 直接导入类（不常用，Spring Boot 内部大量使用）
@Configuration
@Import(UserService.class)  // UserService 本身也会注册为 Bean
public class AppConfig {}
```

### @ImportResource

引入遗留的 XML 配置：

```java
@Configuration
@ImportResource("classpath:legacy-beans.xml")
public class AppConfig {}
```

## @Configuration 与 @Bean

### @Configuration 的 CGLIB 代理

`@Configuration` 类在容器启动时会被 CGLIB 增强。没有 CGLIB 代理的 `@Configuration` 会导致 `@Bean` 方法返回的 Bean 不是单例：

```java
@Configuration
public class AppConfig {
    @Bean
    public A a() {
        return new A(b());  // 这里的 b() 调用会走 CGLIB 代理，确保返回容器中的单例
    }

    @Bean
    public B b() {
        return new B();
    }
}
```

对比普通类（没有 @Configuration）：

```java
@Component  // 不是 @Configuration，没有 CGLIB 代理
public class AppConfig {
    @Bean
    public A a() {
        return new A(b());  // 普通方法调用，每次都 new
    }

    @Bean
    public B b() {
        return new B();
    }
}
```

没有 `@Configuration` 时，`a()` 中的 `b()` 是普通 Java 方法调用，每次都创建新实例。这并不是一定错误的——如果 B 本身就是 Prototype，可能这正是预期的行为。但大多数情况下应该用 `@Configuration`。

### @Configuration 的 proxyBeanMethods

Spring 5.2+ 引入：

```java
@Configuration(proxyBeanMethods = true)  // 默认 true，启用 CGLIB 代理
public class AppConfig {}

@Configuration(proxyBeanMethods = false)  // 禁用代理，@Bean 方法不再走代理
public class LiteConfig {}
```

`proxyBeanMethods = false` 的优点：
- 启动更快（不需要 CGLIB 代理）
- 没有代理限制（可以用 final 方法）

适用场景：大多数 Spring Boot 自动配置类都使用 `proxyBeanMethods = false`，因为它们不依赖于 Bean 之间的方法调用。

### @Bean 注解 vs @Component 注解

| 维度 | @Bean | @Component |
|------|-------|------------|
| 作用目标 | 方法 | 类 |
| 适用场景 | 第三方类（无法加注解）、需要构造逻辑的对象 | 自己写的类 |
| 控制度 | 完全控制创建过程 | 委托给 Spring 反射创建 |
| 条件化 | 可以在方法内加 if/else 判断 | 需要额外的条件注解 |

```java
// @Bean 适合创建第三方类
@Bean
public RestTemplate restTemplate() {
    return new RestTemplateBuilder()
        .setConnectTimeout(Duration.ofSeconds(5))
        .setReadTimeout(Duration.ofSeconds(10))
        .build();
}

// @Component 适合自己的类
@Component
public class UserService {
    @Autowired
    private UserDao userDao;
}
```

## 编程式注册 Bean

除了声明式配置（注解扫描、@Bean），Spring 5 还支持通过 `GenericApplicationContext.registerBean()` 编程式注册 Bean。这在动态决定要注册哪些 Bean 的场景下非常有用。

### registerBean 基础用法

```java
public class Application {
    public static void main(String[] args) {
        GenericApplicationContext context = new GenericApplicationContext();

        // 方式 1：直接注册类（等价于 @Component）
        context.registerBean(UserService.class);

        // 方式 2：注册类 + 指定 Bean 名称 + 构造参数
        context.registerBean("userService", UserService.class,
            () -> new UserService(userDao()));

        // 方式 3：注册 Supplier（函数式 Bean 定义，最灵活）
        context.registerBean(DataSource.class,
            () -> {
                HikariConfig config = new HikariConfig();
                config.setJdbcUrl("jdbc:mysql://localhost:3306/mydb");
                return new HikariDataSource(config);
            },
            bd -> {  // 自定义 BeanDefinition
                bd.setScope(ConfigurableBeanFactory.SCOPE_SINGLETON);
                bd.setLazyInit(false);
                bd.setPrimary(true);
            });

        context.refresh();  // 必须调用，触发 Bean 实例化

        UserService service = context.getBean(UserService.class);
        context.close();
    }
}
```

### 动态注册的场景

```java
// 根据运行环境动态注册不同的实现
GenericApplicationContext context = new GenericApplicationContext();
context.registerBean(ApplicationConfig.class);

if (isProduction()) {
    context.registerBean(PaymentService.class, AlipayPaymentService::new);
} else {
    context.registerBean(PaymentService.class, MockPaymentService::new);
}

context.refresh();
```

### Supplier 与 @Bean 的区别

| 维度 | Supplier（registerBean） | @Bean 方法 |
|------|------------------------|-----------|
| 注册时机 | 运行时动态决定 | 容器启动时静态定义 |
| 依赖注入 | 手动传入 | 方法参数自动注入 |
| 代理增强 | 无 CGLIB 增强 | @Configuration 中会被 CGLIB 代理 |
| 适用场景 | 插件化、条件动态注册 | 常规配置 |

Spring Boot 内部大量使用 registerBean（如自动配置中的条件化 Bean 注册），理解它有助于阅读框架源码。

## 组件扫描

### 扫描机制

`ClassPathBeanDefinitionScanner` 的工作流程：

```text
1. 从 basePackages 指定的包开始扫描
2. 递归遍历所有 .class 文件
3. 检查类是否标注了 @Component 或其衍生注解
4. 符合条件则解析为一个 BeanDefinition
5. 注册到 BeanDefinitionRegistry
```

### 自定义扫描过滤器

```java
// 自定义注解
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Component  // 被 @Component 元注解标记，Spring 会识别
public @interface MyCustomComponent {
    String value() default "";
}

// 使用
@MyCustomComponent("specialService")
public class SpecialService {}
```

默认过滤器只会识别 `@Component`、`@Service`、`@Repository`、`@Controller`。可以通过 `@ComponentScan` 的 `includeFilters` 添加自定义注解。

### 扫描的性能考量

大项目的组件扫描可能影响启动时间。优化建议：

```java
// 精确指定包，不要用顶层包
@ComponentScan("com.example.service")   // 好
@ComponentScan("com.example")           // 差 —— 扫描范围太大

// 在测试中使用 @SpringBootTest(classes = {...}) 限制加载范围
@SpringBootTest(classes = {UserService.class, UserDao.class})
```

## @Component 与衍生注解

`@Component`、`@Service`、`@Repository`、`@Controller` 的关系：

```text
@Component        —— 通用原型
    |
    +-- @Service      —— 业务层
    +-- @Repository   —— 持久层（额外提供异常翻译）
    +-- @Controller   —— Web 层（Spring MVC）
```

从 Spring 容器的角度看，这四个注解功能完全一样——都是把类标记为 Bean。它们的区别在于：

1. **语义区分**：让代码创建者一眼看出类的层次定位
2. **AOP 切入点**：可以针对特定注解做切入 `@Pointcut("@within(org.springframework.stereotype.Service)")`
3. **@Repository 特有功能**：Spring 会为 @Repository 类自动添加 `PersistenceExceptionTranslationPostProcessor`，将持久层异常（如 HibernateException）翻译为 Spring 统一的 `DataAccessException`

```java
@Repository
public class UserDao {
    public User findById(Long id) {
        // Hibernate 可能抛 ConstraintViolationException
        // 会被自动翻译为 Spring 的 DataIntegrityViolationException
    }
}
```

## 条件化配置

### @Profile

根据激活的 profile 决定是否注册 Bean：

```java
@Configuration
public class DataSourceConfig {

    @Bean
    @Profile("dev")
    public DataSource devDataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .build();
    }

    @Bean
    @Profile("prod")
    public DataSource prodDataSource() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:mysql://prod-db:3306/mydb");
        return new HikariDataSource(config);
    }
}
```

激活 profile：

```yaml
# application.yml
spring:
  profiles:
    active: dev
```

```bash
java -jar app.jar --spring.profiles.active=prod
```

### @Conditional

Spring 4.0 引入的条件化注解，比 @Profile 更灵活：

```java
@Bean
@Conditional(OnLinuxCondition.class)
public SomeBean linuxBean() {
    return new SomeBean();
}

// 自定义条件
public class OnLinuxCondition implements Condition {
    @Override
    public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        String osName = context.getEnvironment().getProperty("os.name");
        return osName != null && osName.toLowerCase().contains("linux");
    }
}
```

Spring Boot 提供了大量内置条件注解：

| 注解 | 条件 |
|------|------|
| @ConditionalOnClass | 类路径存在指定类 |
| @ConditionalOnMissingClass | 类路径不存在指定类 |
| @ConditionalOnBean | 容器中存在指定 Bean |
| @ConditionalOnMissingBean | 容器中不存在指定 Bean |
| @ConditionalOnProperty | 配置属性为指定值 |
| @ConditionalOnResource | 类路径存在指定资源 |
| @ConditionalOnWebApplication | 是 Web 应用 |
| @ConditionalOnExpression | SpEL 表达式为 true |

```java
@Configuration
@ConditionalOnClass(DataSource.class)
public class DataSourceAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(name = "spring.datasource.url")
    public DataSource dataSource() {
        // ...
    }
}
```

## Environment 抽象

Environment 是 Spring 对运行环境的抽象，它统一管理 **profile** 和 **properties** 两个维度。它是 `@Profile` 和 `@Value` 的底层基础。

### Environment 接口

```java
public interface Environment extends PropertyResolver {
    // Profile 相关
    String[] getActiveProfiles();        // 激活的 profile
    String[] getDefaultProfiles();       // 默认 profile
    boolean acceptsProfiles(Profiles profiles);  // 判断是否接受某 profile
}
```

PropertyResolver（父接口）提供属性解析能力：

```java
public interface PropertyResolver {
    String getProperty(String key);                     // 获取属性，无则返回 null
    String getProperty(String key, String defaultValue); // 带默认值
    <T> T getProperty(String key, Class<T> targetType);  // 类型转换
    <T> T getRequiredProperty(String key, Class<T> targetType);  // 必需，无则抛异常
    String resolvePlaceholders(String text);            // 解析 ${...} 占位符
    String resolveRequiredPlaceholders(String text);
}
```

### Environment 使用

```java
@Component
public class ConfigService {

    @Autowired
    private Environment environment;

    public String getAppName() {
        // 直接读取属性
        return environment.getProperty("app.name", "default-app");

        // 读取并转换类型
        // Integer port = environment.getProperty("server.port", Integer.class);

        // 必需属性（不存在抛 IllegalStateException）
        // String key = environment.getRequiredProperty("app.secret-key");
    }

    public boolean isProd() {
        // 判断激活的 profile
        return environment.acceptsProfiles(Profiles.of("prod"));
    }

    public String resolve(String template) {
        // 解析占位符
        return environment.resolvePlaceholders("服务器：${server.address}:${server.port}");
    }
}
```

### 属性来源（PropertySource）

Environment 内部维护一个 `PropertySources` 列表，按优先级排序查找属性：

```text
PropertySources（有序列表，前面的优先）
├── systemProperties     —— JVM 系统属性（-Dxxx=yyy）
├── systemEnvironment    —— 操作系统环境变量
├── application.properties —— 配置文件
├── @PropertySource 声明的文件
└── ...（自定义 PropertySource）
```

```java
// 查看所有属性来源
ConfigurableApplicationContext context = ...;
MutablePropertySources sources = context.getEnvironment().getPropertySources();
for (PropertySource<?> ps : sources) {
    System.out.println(ps.getName() + " = " + ps.getSource());
}
```

### 自定义 PropertySource

```java
// 从数据库/远程配置中心加载配置
@Configuration
public class RemoteConfig {

    @Autowired
    private void initConfig(ConfigurableEnvironment environment) {
        // 自定义属性源
        Map<String, Object> remoteProps = loadFromConfigCenter();
        MapPropertySource remoteSource = new MapPropertySource("remoteConfig", remoteProps);

        // 添加到最高优先级（first）或最低优先级（last）
        environment.getPropertySources().addFirst(remoteSource);
    }
}
```

### @PropertySource 与 Environment 的关系

`@PropertySource` 本质上是把一个资源注册到 Environment 的 PropertySources 中：

```java
@Configuration
@PropertySource("classpath:app.properties")
@PropertySource("file:/opt/config/db.properties")
public class AppConfig {
    @Autowired
    private Environment env;

    @Bean
    public DataSource dataSource() {
        // env.getProperty 会按优先级从所有 PropertySource 中查找
        return createDataSource(env.getProperty("db.url"));
    }
}
```

### 属性优先级

Spring Boot 中属性来源的完整优先级（从高到低）：

1. 命令行参数（`--server.port=8080`）
2. Java 系统属性（`-Dserver.port=8080`）
3. 操作系统环境变量
4. `application-{profile}.yml`（profile 专用）
5. `application.yml`
6. `@PropertySource` 声明的文件
7. 默认值

理解 Environment 抽象，就能理解为什么同一个配置项在不同来源下会有不同的生效值。

## 配置属性注入

### @Value

```java
@Component
public class AppProperties {

    @Value("${app.name}")
    private String appName;

    @Value("${app.version:1.0.0}")  // 默认值
    private String version;

    @Value("${app.max-connections:100}")
    private int maxConnections;

    // SpEL 表达式
    @Value("#{systemProperties['user.home']}")
    private String userHome;

    @Value("#{${app.timeout} * 1000}")
    private long timeoutMillis;

    // 注入 List（需要特殊处理，Spring 不直接支持）
    @Value("${app.allowed-origins}")
    private String allowedOriginsStr;

    private List<String> allowedOrigins;

    @PostConstruct
    public void init() {
        allowedOrigins = Arrays.asList(allowedOriginsStr.split(","));
    }
}
```

### @PropertySource

```java
@Configuration
@PropertySource("classpath:app.properties")
@PropertySource("classpath:database.properties")
public class AppConfig {}
```

### @ConfigurationProperties（Spring Boot）

Spring Boot 提供的类型安全配置绑定：

```java
@Component
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private String name;
    private String version;
    private int maxConnections;
    private List<String> allowedOrigins;
    private Map<String, String> mail;
    private Security security = new Security();

    // getter/setter 必须存在
    public static class Security {
        private boolean enabled;
        private String secretKey;
        // getter/setter
    }
}
```

```yaml
# application.yml 自动映射
app:
  name: MyApp
  version: "2.0"
  max-connections: 50
  allowed-origins:
    - http://localhost:3000
    - http://example.com
  mail:
    host: smtp.example.com
    port: 587
  security:
    enabled: true
    secret-key: abc123
```

`@ConfigurationProperties` 比 `@Value` 更适合绑定复杂嵌套结构，还支持 JSR-303 校验：

```java
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {
    @NotBlank
    private String name;

    @Min(1)
    @Max(1000)
    private int maxConnections;
}
```

## 配置方式对比与选择

| 维度 | XML | 注解 | Java Config |
|------|-----|------|-------------|
| 可读性 | 冗长 | 简洁 | 清晰 |
| 类型安全 | 字符串，不安全 | 支持 | 支持 |
| 重构友好 | 差（字符串） | 好 | 好 |
| 动态性 | 不可编程 | 不可编程 | 可编程（条件判断） |
| 第三方类 | 容易 | 不能（需要源码） | 容易（@Bean） |
| Spring Boot | 不推荐 | 默认 | 默认 |

```text
推荐策略：
- 新项目：Java Config（配置类）+ 注解（自己的类）+ @Bean（第三方类）
- 旧项目维护：保留现有 XML，新功能用 Java Config
- 如果团队不熟悉 Spring：优先 XML（配置集中，一眼就知道有哪些 Bean），逐步引入注解
```

## 应用场景实战

### 场景 1：多环境数据源配置

```java
@Configuration
public class MultiEnvDataSourceConfig {

    @Bean
    @Profile("dev")
    public DataSource devDataSource() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:h2:mem:devdb");
        config.setUsername("sa");
        config.setPassword("");
        return new HikariDataSource(config);
    }

    @Bean
    @Profile("test")
    public DataSource testDataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("schema.sql")
            .addScript("test-data.sql")
            .build();
    }

    @Bean
    @Profile("prod")
    @ConfigurationProperties(prefix = "spring.datasource")
    public DataSource prodDataSource() {
        return DataSourceBuilder.create().build();
    }
}
```

### 场景 2：第三方库的 Bean 注册 + 动态配置

```java
@Configuration
public class RedisConfig {

    @Value("${redis.host}")
    private String host;

    @Value("${redis.port}")
    private int port;

    @Value("${redis.password:}")
    private String password;

    @Value("${redis.database:0}")
    private int database;

    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName(host);
        config.setPort(port);
        if (StringUtils.hasText(password)) {
            config.setPassword(password);
        }
        config.setDatabase(database);

        LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
            .commandTimeout(Duration.ofSeconds(2))
            .shutdownTimeout(Duration.ofMillis(100))
            .build();

        return new LettuceConnectionFactory(config, clientConfig);
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate(
            RedisConnectionFactory connectionFactory) {

        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);

        // 自定义序列化
        Jackson2JsonRedisSerializer<Object> serializer =
            new Jackson2JsonRedisSerializer<>(Object.class);
        ObjectMapper mapper = new ObjectMapper();
        mapper.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
        mapper.activateDefaultTyping(
            mapper.getPolymorphicTypeValidator(),
            ObjectMapper.DefaultTyping.NON_FINAL
        );
        serializer.setObjectMapper(mapper);

        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(serializer);
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(serializer);
        template.afterPropertiesSet();

        return template;
    }
}
```

### 场景 3：条件化加载——功能开关

```java
@Configuration
public class FeatureToggleConfig {

    @Bean
    @ConditionalOnProperty(name = "feature.sms.enabled", havingValue = "true")
    public SmsService smsService() {
        return new AliyunSmsService();
    }

    @Bean
    @ConditionalOnMissingBean(SmsService.class)
    public SmsService mockSmsService() {
        return new MockSmsService();  // 开发环境下不发真短信
    }

    @Bean
    @ConditionalOnExpression("'${feature.notification}'.equals('all') || '${feature.notification}'.equals('email')")
    public EmailNotificationService emailNotificationService() {
        return new EmailNotificationService();
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **配置与业务分离**。配置类放在独立的 `config` 包中，不要和业务代码混在一起。

2. **@ConfigurationProperties 优于 @Value**。类型安全、支持嵌套、支持校验。对于一组相关配置属性，定义专门的配置类。

3. **使用 @Bean 时明确命名**。默认方法名作为 Bean 名称，但方法重构后名称会变。用 `@Bean("dataSource")` 显式命名。

4. **避免在 @Configuration 中使用字段注入**。配置类中需要什么值用 `@Value` 或方法参数获取：

```java
// 好 —— 参数注入
@Bean
public DataSource dataSource(@Value("${db.url}") String url) {
    return ...;
}

// 也行 —— @Value 成员变量
@Value("${db.url}")
private String url;

// 别这样做 —— 配置类字段被 @Autowired
@Autowired  // 不推荐在配置类中注入业务 Bean
private UserService userService;
```

5. **profile 命名标准化**：dev / test / staging / prod。

### 踩坑记录

**坑 1：@Configuration 中方法调用导致多实例**

```java
@Configuration
public class AppConfig {
    @Bean
    public A a() { return new A(); }

    @Bean
    public B b() {
        A a = a();  // 如果类上有 @Configuration，返回的是容器中的单例
        return new B(a);
    }
}
```

只要类上有 `@Configuration`（不是 `@Component`），`a()` 的调用就会走 CGLIB 代理，确保单例。如果用了 `proxyBeanMethods = false`，则变成普通方法调用。

**坑 2：@ComponentScan 找不到 Bean**

检查：
- 启动类所在包是否覆盖了业务类的包
- 是否有类型错误（接口 vs 实现类）
- 实现类上是否有 @Service/@Component

```java
// 差 —— 扫描从 com.example 开始，但业务类在 com.example.service
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// 好 —— 启动类放在了顶层包 com.example 下
// 或者显式指定：
@SpringBootApplication(scanBasePackages = "com.example")
```

**坑 3：@Bean 方法在非 @Configuration 类中不会走代理**

```java
@Component  // 不是 @Configuration
public class MyConfig {
    @Bean
    public A a() { return new A(); }

    @Bean
    public B b() { return new B(a()); }  // a() 每次调用都是新实例
}
```

如果要跨方法调用 Bean 方法，必须用 `@Configuration` 而不是 `@Component`。

**坑 4：@ConditionalOnBean 顺序问题**

```java
@Configuration
public class AConfig {
    @Bean
    @ConditionalOnBean(B.class)  // B 可能还没加载！
    public A a() { return new A(); }
}

@Configuration
public class BConfig {
    @Bean
    public B b() { return new B(); }
}
```

`@ConditionalOnBean` 依赖 Bean 加载顺序。如果 A 的配置先于 B 加载，条件判断为 false。解法：用 `@AutoConfigureAfter` 控制配置类的顺序，或使用 `@ConditionalOnClass` 代替。

**坑 5：多个 @Configuration 类中的 Bean 同名冲突**

```java
@Configuration
public class ConfigA {
    @Bean
    public DataSource dataSource() { return ...; }
}

@Configuration
public class ConfigB {
    @Bean
    public DataSource dataSource() { return ...; }  // 同名覆盖 ConfigA 的
}
```

默认情况下后加载的覆盖先加载的（Spring Boot 的默认行为是 allow-bean-definition-overriding=true，但 Spring Boot 2.1+ 改为 false，直接报错）。显式使用 `@Primary` 或 `@Qualifier` 解决冲突。
