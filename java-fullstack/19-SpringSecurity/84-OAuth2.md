---
title: OAuth2
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [oauth2, authorization-code, client-credentials, oidc, resource-server, authorization-server, spring-security]
---

# OAuth2

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [OAuth2 核心概念](#oauth2-核心概念)
- [四种授权模式](#四种授权模式)
- [Refresh Token 模式](#refresh-token-模式)
- [OpenID Connect（OIDC）](#openid-connectoidc)
- [OAuth2 Client](#oauth2-client)
- [OAuth2 Resource Server](#oauth2-resource-server)
- [OAuth2 Authorization Server](#oauth2-authorization-server)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

OAuth2（Open Authorization 2.0）是一个**授权**框架（RFC 6749），让第三方应用在**不接触用户密码**的情况下，获得用户资源的有限访问权限。

```text
OAuth2 解决的典型场景：
"网站 A 想读取你在微信/Google 的头像和昵称，但不应该知道你的微信密码"

传统方式（错误）：用户在网站 A 输入微信账号密码 → 密码泄露风险
OAuth2 方式（正确）：用户跳转到微信授权页 → 同意授权 → 微信给网站 A 发一个令牌 → 网站 A 用令牌读取信息
```

### OAuth2 vs 认证

```text
OAuth2 是"授权"协议，不是"认证"协议。
它解决"我能访问什么资源"，不解决"你是谁"。

身份认证由 OIDC（OpenID Connect，构建在 OAuth2 之上）解决。
```

## OAuth2 核心概念

### 四个角色

| 角色 | 说明 | 例子 |
|------|------|------|
| Resource Owner（资源所有者） | 拥有资源的用户 | 微信用户 |
| Client（客户端） | 请求访问资源的应用 | 网站 A |
| Authorization Server（授权服务器） | 认证用户并签发令牌 | 微信开放平台 |
| Resource Server（资源服务器） | 存储并保护资源 | 微信的用户信息 API |

### 核心术语

```text
Access Token   —— 访问令牌，客户端用它访问资源
Refresh Token  —— 刷新令牌，用于获取新的 Access Token
Scope          —— 权限范围，如 read:profile、write:posts
Grant Type     —— 授权模式（怎么获取令牌）
Redirect URI   —— 回调地址，授权后跳转回客户端
Client ID / Secret —— 客户端的身份标识和密钥
```

### 令牌类型

```text
Opaque Token（不透明令牌）
- 随机字符串，本身无信息
- 需要服务器存储或查询才能解析
- 可随时撤销

JWT Token（结构化令牌）
- 自包含用户信息（前面 83 篇讲的 JWT）
- 资源服务器可自行验证，无需查询授权服务器
- 无法主动撤销（除非黑名单）
```

## 四种授权模式

OAuth2 定义了多种授权模式（Grant Type），不同场景用不同模式。

### 1. Authorization Code（授权码模式）—— 最安全，最常用

**适用**：有后端的 Web 应用、移动应用。涉及用户参与授权。

```text
流程：
1. 客户端重定向用户到授权服务器
   GET /authorize?client_id=xxx&redirect_uri=xxx&scope=read&state=xxx
2. 用户在授权服务器登录并同意授权
3. 授权服务器重定向回客户端，带上授权码（code）
   GET /callback?code=xxx&state=xxx
4. 客户端用授权码换令牌（后端完成）
   POST /token  code=xxx&client_id=xxx&client_secret=xxx
5. 授权服务器返回 access_token + refresh_token
```

```text
为什么安全：
1. 授权码通过浏览器传递（可能泄露），但只有一次有效
2. 换令牌需要 client_secret（只在后端，不经过浏览器）
3. 用户密码只输入在授权服务器，客户端全程不接触
```

### 2. Client Credentials（客户端凭证模式）—— 服务间认证

**适用**：机器对机器（M2M），没有用户参与。

```text
流程：
1. 客户端直接用 client_id + client_secret 请求令牌
   POST /token grant_type=client_credentials&client_id=xxx&client_secret=xxx
2. 授权服务器返回 access_token
```

```text
典型场景：
- 后端服务调用另一个后端服务
- 定时任务访问 API
- CI/CD 流水线调用接口
```

### 3. Resource Owner Password（密码模式）—— 已废弃

**适用**：客户端完全可信（第一方应用）。OAuth2.1 已废弃此模式。

```text
流程：
1. 客户端收集用户名密码
2. 直接 POST /token grant_type=password&username=xxx&password=xxx
3. 返回 access_token
```

```text
为什么不推荐：
- 客户端接触用户密码，违背 OAuth2 初衷
- OAuth2.1 已移除，建议改用 Authorization Code + PKCE
```

### 4. Implicit（隐式模式）—— 已废弃

**适用**：纯前端 SPA（无后端）。OAuth2.1 已废弃。

```text
流程：
1. 重定向到授权服务器
2. 授权后直接在 URL 片段返回 access_token（不经过 code 换 token）
```

```text
为什么不推荐：
- Token 直接暴露在 URL，易泄露
- OAuth2.1 已移除，SPA 改用 Authorization Code + PKCE
```

### 授权模式对比

| 模式 | 用户参与 | 安全性 | 适用场景 | 现状 |
|------|---------|--------|---------|------|
| Authorization Code | 是 | 最高 | Web/移动应用 | 推荐 |
| Authorization Code + PKCE | 是 | 最高 | SPA/移动应用 | 推荐 |
| Client Credentials | 否 | 高 | 服务间调用 | 推荐 |
| Resource Owner Password | 是 | 低 | 第一方应用 | 已废弃 |
| Implicit | 是 | 低 | 纯前端 | 已废弃 |

### PKCE（Proof Key for Code Exchange）

PKCE 是授权码模式的增强，防止授权码被截获：

```text
普通授权码模式的问题：
- 授权码在浏览器跳转中传递，可能被恶意应用截获
- 恶意应用用截获的 code 换 token（如果有 client_secret 则安全，但 SPA 没有）

PKCE 解决：
1. 客户端生成 code_verifier（随机串）+ code_challenge（其哈希）
2. 授权请求带上 code_challenge
3. 换 token 时带上 code_verifier
4. 授权服务器验证 code_verifier 的哈希 == code_challenge
5. 只有原始客户端知道 code_verifier，截获 code 也无法换 token
```

## Refresh Token 模式

Refresh Token 用于在 Access Token 过期后获取新令牌，避免用户重新授权。

### 刷新流程

```text
1. 客户端发现 access_token 过期
2. 用 refresh_token 请求新令牌
   POST /token grant_type=refresh_token&refresh_token=xxx&client_id=xxx&client_secret=xxx
3. 授权服务器返回新的 access_token（+ 可选新 refresh_token）
```

### Refresh Token 的安全

```text
1. Refresh Token 有效期长（7 天~30 天），必须安全存储
2. Refresh Token 只在客户端后端使用，不进浏览器
3. 刷新时旧 refresh_token 作废（旋转刷新），防重放
4. 检测到 refresh_token 被重复使用 → 撤销所有令牌，强制重新登录
```

## OpenID Connect（OIDC）

OIDC 是构建在 OAuth2 之上的**身份认证**层，补充了 OAuth2 缺失的"你是谁"。

### OIDC 在 OAuth2 基础上新增

```text
1. ID Token —— JWT 格式的身份令牌，包含用户身份信息
2. UserInfo 端点 —— 获取用户详细资料
3. 标准 scope：openid、profile、email
```

### ID Token 结构

```json
{
  "iss": "https://auth.example.com",   // 签发者
  "sub": "1234567890",                 // 用户唯一标识
  "aud": "my-client-id",               // 接收者（客户端）
  "exp": 1516239022,                   // 过期时间
  "iat": 1516239022,                   // 签发时间
  "name": "张三",
  "email": "zhangsan@example.com",
  "picture": "https://example.com/avatar.jpg"
}
```

### OAuth2 vs OIDC

| 维度 | OAuth2 | OIDC |
|------|--------|------|
| 目的 | 授权（能访问什么） | 认证（你是谁） |
| 令牌 | Access Token | Access Token + ID Token |
| 标准 | RFC 6749 | OIDC 规范（基于 OAuth2） |
| 用户信息 | 通过 API 获取 | UserInfo 端点 + ID Token |

```text
记忆：
OAuth2 是"门禁卡"——给你进入某些房间的权限
OIDC 是"身份证"——告诉你这个人是谁
实际项目通常两者一起用：OIDC 认证 + OAuth2 授权
```

## OAuth2 Client

OAuth2 Client 是"第三方登录"的客户端——让用户用微信/Google/GitHub 账号登录你的应用。

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-client</artifactId>
</dependency>
```

### 配置第三方登录

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
            scope: read:user,user:email
          google:
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope: openid,profile,email
```

### 安全配置

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/login").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login")                    // 自定义登录页
                .defaultSuccessUrl("/home")             // 登录成功跳转
            );
        return http.build();
    }
}
```

### 获取登录用户信息

```java
@RestController
public class UserController {

    @GetMapping("/me")
    public Map<String, Object> me(@AuthenticationPrincipal OAuth2User principal) {
        // principal 包含第三方返回的用户信息
        return principal.getAttributes();
    }
}
```

## OAuth2 Resource Server

Resource Server 是"资源服务器"——验证 Access Token 并保护 API。

### 引入依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-resource-server</artifactId>
</dependency>
```

### JWT 资源服务器配置

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com     # 授权服务器地址
          jwk-set-uri: https://auth.example.com/oauth2/jwks  # 公钥地址
```

```java
@Configuration
@EnableWebSecurity
public class ResourceServerConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(Customizer.withDefaults())  // JWT 验证
            );
        return http.build();
    }
}
```

### 从 JWT 提取权限

```java
@Bean
public JwtAuthenticationConverter jwtAuthenticationConverter() {
    JwtGrantedAuthoritiesConverter converter = new JwtGrantedAuthoritiesConverter();
    converter.setAuthorityPrefix("ROLE_");       // 前缀
    converter.setAuthoritiesClaimName("roles");  // 从哪个 claim 读取权限

    JwtAuthenticationConverter jwtConverter = new JwtAuthenticationConverter();
    jwtConverter.setJwtGrantedAuthoritiesConverter(converter);
    return jwtConverter;
}
```

### 访问受保护接口

```http
GET /api/users
Authorization: Bearer eyJhbGciOi...（JWT Token）
```

## OAuth2 Authorization Server

Authorization Server 是"授权服务器"——签发和验证令牌。

### 现状

```text
Spring Security OAuth2 项目已废弃（EOL），
Authorization Server 需要单独实现或用第三方：
1. Spring Authorization Server（官方新项目）
2. Keycloak（开源，功能全）
3. Auth0 / Okta（商业服务）
```

### Spring Authorization Server

```xml
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-oauth2-authorization-server</artifactId>
</dependency>
```

```java
@Configuration
public class AuthorizationServerConfig {

    @Bean
    public RegisteredClientRepository registeredClientRepository() {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
            .clientId("my-client")
            .clientSecret("{noop}my-secret")
            .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
            .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
            .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
            .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
            .redirectUri("http://localhost:8080/login/oauth2/code/my-client")
            .scope("read")
            .scope("write")
            .build();

        return new InMemoryRegisteredClientRepository(client);
    }
}
```

### 推荐实践

```text
大多数项目不需要自己实现 Authorization Server：
- 用 Keycloak 或 Auth0 托管
- 自己的应用做 OAuth2 Client 或 Resource Server 即可
- 只有 SaaS 平台、统一认证中心才需要自己搭 Authorization Server
```

## 应用场景实战

### 场景 1：接入 GitHub 第三方登录

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
            redirect-uri: "{baseUrl}/login/oauth2/code/{registrationId}"
            scope: read:user
```

```java
@Controller
public class LoginController {
    @GetMapping("/")
    public String home(@AuthenticationPrincipal OAuth2User user, Model model) {
        if (user != null) {
            model.addAttribute("name", user.getAttribute("name"));
            model.addAttribute("avatar", user.getAttribute("avatar_url"));
        }
        return "home";
    }
}
```

### 场景 2：微服务间调用（Client Credentials）

```java
// 服务 A 调用服务 B 的受保护接口
@Service
public class ServiceAClient {

    @Autowired
    private WebClient webClient;

    public String callServiceB() {
        // 用 Client Credentials 获取 token
        String token = oauth2Client.getToken("service-b");

        return webClient.get()
            .uri("http://service-b/api/data")
            .header("Authorization", "Bearer " + token)
            .retrieve()
            .bodyToMono(String.class)
            .block();
    }
}
```

### 场景 3：Resource Server 保护 REST API

```java
@Configuration
@EnableWebSecurity
public class ResourceServerConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthenticationConverter()))
            );
        return http.build();
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **优先用 Authorization Code + PKCE**。这是 OAuth2.1 推荐的唯一用户参与模式，SPA 和移动应用也必须用它。

2. **Client Secret 绝不放前端**。secret 只存在后端，前端用 PKCE。

3. **Scope 最小化**。只申请需要的权限，不要 `scope=all`。

4. **Refresh Token 旋转 + 检测重放**。每次刷新换新 token，检测到旧 token 被重用立即撤销。

5. **OAuth2 授权用托管方案**。Authorization Server 用 Keycloak/Auth0，不要自己从零实现。

### 踩坑记录

**坑 1：Redirect URI 不匹配**

```text
授权服务器报 redirect_uri mismatch：
配置的 redirect URI 和请求中的必须完全一致（含路径、协议、端口）
```

回调地址要在授权服务器精确注册，任何字符差异都会导致失败。

**坑 2：state 参数未校验导致 CSRF**

```java
// 授权请求带 state，回调时未校验 state
// 攻击者可能伪造授权回调，导致 CSRF
```

授权请求生成随机 state，回调时校验 state 一致，防止 CSRF。

**坑 3：用 JWT 时忘配公钥**

```yaml
# Resource Server 用 JWT，但没配 jwk-set-uri 或 issuer-uri
# 无法获取签名公钥，token 验证失败
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com  # 必须配
```

JWT 资源服务器需要公钥验证签名，必须配置 issuer-uri 或 jwk-set-uri。

**坑 4：Access Token 和 ID Token 混淆**

```text
Access Token：访问资源用，不要解析它获取用户信息
ID Token：认证用，包含用户身份，不该用来访问 API

错误：把 ID Token 当 Access Token 传 API
```

两者用途不同，不要混用。

**坑 5：密码模式已废弃还在用**

```text
Resource Owner Password Grant 在 OAuth2.1 已废弃，
但很多老教程还在用。新项目应避免。
```

改用 Authorization Code + PKCE。

**坑 6：Client Secret 硬编码**

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-secret: abc123  # 硬编码泄露风险
```

用环境变量 `${GITHUB_CLIENT_SECRET}` 或配置中心，不要硬编码。
