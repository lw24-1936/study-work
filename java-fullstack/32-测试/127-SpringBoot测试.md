---
title: Spring Boot 测试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springboottest, mockmvc, webtestclient, test-slice, datajpatest]
---

# Spring Boot 测试

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [@SpringBootTest 集成测试](#springboottest-集成测试)
- [MockMvc Web 层测试](#mockmvc-web-层测试)
- [WebTestClient 响应式测试](#webtestclient-响应式测试)
- [Test Slice 切片测试](#test-slice-切片测试)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Boot 测试基于 Spring Test 框架，提供丰富的测试支持，从完整应用测试到切片测试。

```text
测试类型（从重到轻）：
1. @SpringBootTest —— 完整上下文测试（最重）
2. MockMvc —— Web 层测试
3. Test Slice —— 切片测试（@DataJpaTest 等，最轻）
```

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

## @SpringBootTest 集成测试

@SpringBootTest 启动完整 Spring 上下文，是最完整的测试。

### 基本用法

```java
@SpringBootTest
class UserServiceTest {

    @Autowired
    private UserService userService;   // 真实注入

    @Test
    void testGetUser() {
        User user = userService.getUser(1L);
        assertThat(user).isNotNull();
    }
}
```

### 配置选项

```java
@SpringBootTest(
    webEnvironment = WebEnvironment.MOCK        // 默认，模拟 Web 环境
    // webEnvironment = WebEnvironment.RANDOM_PORT  // 真实端口（随机）
    // webEnvironment = WebEnvironment.DEFINED_PORT // 指定端口
)
class UserServiceTest { ... }
```

### 使用随机端口 + TestRestTemplate

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class UserControllerTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void testGetUser() {
        ResponseEntity<User> response = restTemplate
            .getForEntity("/api/users/1", User.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    }
}
```

### 测试配置隔离

```java
// 用测试配置覆盖生产配置
@SpringBootTest
@TestPropertySource(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb",
    "spring.redis.host=localhost"
})
class UserServiceTest { ... }
```

## MockMvc Web 层测试

MockMvc 测试 Web 层（Controller），不需要真实服务器。

### 基本用法

```java
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void testGetUser() throws Exception {
        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("张三"))
            .andExpect(jsonPath("$.id").value(1));
    }

    @Test
    void testCreateUser() throws Exception {
        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"张三\",\"age\":20}"))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("张三"));
    }
}
```

### 常用断言

```java
mockMvc.perform(get("/api/users/1"))
    .andExpect(status().isOk())              // 状态码
    .andExpect(jsonPath("$.name").value("张三"))  // JSON 字段
    .andExpect(jsonPath("$.list", hasSize(3)))    // 集合大小
    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
    .andExpect(header().string("X-Custom", "value"));
```

### Mock 依赖（纯 Web 层测试）

```java
@WebMvcTest(UserController.class)   // 只加载 Web 层，不加载完整上下文
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean                       // mock Service 依赖
    private UserService userService;

    @Test
    void testGetUser() throws Exception {
        when(userService.getUser(1L)).thenReturn(new User(1L, "张三"));

        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("张三"));
    }
}
```

## WebTestClient 响应式测试

WebTestClient 是响应式 Web 测试客户端，支持 WebFlux 和传统 MVC。

### 依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
    <scope>test</scope>
</dependency>
```

### 基本用法

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class UserControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @Test
    void testGetUser() {
        webTestClient.get().uri("/api/users/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody(User.class)
            .value(user -> assertThat(user.getName()).isEqualTo("张三"));
    }
}
```

### WebTestClient vs MockMvc

| 维度 | MockMvc | WebTestClient |
|------|---------|---------------|
| 适用 | MVC（Servlet） | WebFlux + MVC |
| 风格 | 命令式 | 响应式 |
| 服务器 | 不需要 | 可选真实服务器 |

## Test Slice 切片测试

切片测试只加载 Spring 的部分组件，更快、更聚焦。

### @DataJpaTest（数据层测试）

```java
@DataJpaTest   // 只加载 JPA 相关组件（Repository、EntityManager）
class UserRepositoryTest {

    @Autowired
    private UserRepository userRepository;

    @Test
    void testFindByName() {
        User user = new User(null, "张三");
        userRepository.save(user);

        Optional<User> found = userRepository.findByName("张三");
        assertThat(found).isPresent();
    }
}
```

```text
@DataJpaTest 特点：
1. 只加载 JPA 组件（快速）
2. 默认使用内嵌数据库（H2）
3. 自动事务回滚（测试数据不污染）
```

### 其他切片测试

| 注解 | 加载内容 | 用途 |
|------|---------|------|
| @DataJpaTest | JPA 组件 | Repository 测试 |
| @WebMvcTest | Web 层 | Controller 测试 |
| @DataMongoTest | MongoDB | Mongo Repository |
| @DataRedisTest | Redis | Redis 操作 |
| @JsonTest | JSON 序列化 | Jackson 测试 |
| @RestClientTest | RestTemplate | HTTP 客户端 |

### 切片测试 vs 完整测试

```text
@SpringBootTest —— 完整上下文（慢，全面）
@WebMvcTest —— Web 层（快，聚焦 Controller）
@DataJpaTest —— 数据层（快，聚焦 Repository）

原则：能用切片测试的不用完整测试（更快）
```

## 应用场景实战

### 场景 1：Controller + Service + Repository 分层测试

```java
// Repository 层（@DataJpaTest）
@DataJpaTest
class UserRepositoryTest {
    @Autowired
    private UserRepository repository;

    @Test
    void testSaveAndFind() {
        repository.save(new User(null, "张三"));
        assertThat(repository.findByName("张三")).isPresent();
    }
}

// Service 层（@SpringBootTest + Mock）
@SpringBootTest
class UserServiceTest {
    @MockBean
    private UserRepository repository;

    @Autowired
    private UserService service;

    @Test
    void testGetUser() {
        when(repository.findById(1L)).thenReturn(Optional.of(new User(1L, "张三")));
        assertThat(service.getUser(1L).getName()).isEqualTo("张三");
    }
}

// Controller 层（@WebMvcTest）
@WebMvcTest(UserController.class)
class UserControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService service;

    @Test
    void testGetUser() throws Exception {
        when(service.getUser(1L)).thenReturn(new User(1L, "张三"));
        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("张三"));
    }
}
```

### 场景 2：参数校验测试

```java
@WebMvcTest(UserController.class)
class UserValidationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void shouldReturn400WhenNameEmpty() throws Exception {
        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"name\":\"\",\"age\":20}"))  // name 为空
            .andExpect(status().isBadRequest());
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **分层测试**。Repository 用 @DataJpaTest，Controller 用 @WebMvcTest，Service 用 @SpringBootTest + MockBean。

2. **测试配置隔离**。测试用内嵌数据库（H2），不依赖外部环境。

3. **@MockBean 只 mock 必要依赖**。过度 mock 会导致测试失真。

4. **测试数据不污染**。@DataJpaTest 自动回滚事务，或 @Transactional 包裹。

5. **用 jsonPath 断言响应**。清晰验证 JSON 结构。

### 踩坑记录

**坑 1：@SpringBootTest 找不到配置类**

```java
@SpringBootTest   // 测试类和主类不在同一包，找不到 @SpringBootApplication
class UserServiceTest { ... }
```

用 `@SpringBootTest(classes = Application.class)` 指定主类。

**坑 2：@MockBean 影响其他测试**

```java
@MockBean
private UserService service;   // 在 @SpringBootTest 里 mock，影响整个上下文
// 其他测试类也用这个上下文，可能受影响
```

@MockBean 会替换整个上下文的 bean，注意影响范围。

**坑 3：测试依赖真实数据库**

```java
@SpringBootTest   // 没配测试数据源，连真实数据库
class UserServiceTest {
    // 测试污染生产/开发数据库
}
```

测试用内嵌数据库（H2）或独立的测试数据库。

**坑 4：@DataJpaTest 默认 H2 但项目用 MySQL**

```text
@DataJpaTest 默认 H2，但 SQL 用了 MySQL 语法，测试失败
```

配置测试数据源，或加 @AutoConfigureTestDatabase(replace = NONE) 用真实测试库。

**坑 5：MockMvc 测试没加载 Security**

```java
@WebMvcTest   // 项目有 Spring Security，请求 401
```

加 @AutoConfigureMockMvc(addFilters = false) 或 mock 安全上下文。

**坑 6：测试之间状态污染**

```java
@Test
void test1() { service.updateUser(); }   // 修改了数据

@Test
void test2() { assertThat(...); }        // 依赖 test1 的修改
```

测试要隔离，用 @Transactional 回滚或 @BeforeEach 重置。
