---
title: JWT
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [jwt, access-token, refresh-token, token, 无状态认证, 黑名单, spring-security]
---

# JWT

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [JWT 结构详解](#jwt-结构详解)
- [JWT 依赖与工具类](#jwt-依赖与工具类)
- [Access Token 与 Refresh Token](#access-token-与-refresh-token)
- [Token 过期处理](#token-过期处理)
- [Token 黑名单](#token-黑名单)
- [Token 刷新流程](#token-刷新流程)
- [JWT 集成 Spring Security](#jwt-集成-spring-security)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JWT（JSON Web Token）是一种开放标准（RFC 7519），用于在各方之间安全地传输信息。它是最流行的无状态认证方案。

```text
JWT 解决 Session 认证的痛点：
1. Session 认证依赖服务器存储（内存/Redis），分布式环境需要共享存储
2. JWT 无状态 —— 服务器不存任何会话信息，Token 自包含用户信息
3. JWT 适合前后端分离、微服务、跨域场景

JWT 的代价：
1. Token 无法主动失效（除非用黑名单）
2. Token 较大（每次请求都携带）
3. 信息泄露风险（Payload 只是 base64 编码，不是加密）
```

## JWT 结构详解

JWT 由三部分组成，用 `.` 分隔：

```text
header.payload.signature

示例：
eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjEsInVzZXJuYW1lIjoiYWRtaW4ifQ.签名部分
```

### Header（头部）

```json
{
  "alg": "HS256",   // 签名算法：HS256/HMAC、RS256/RSA、ES256/ECDSA
  "typ": "JWT"      // 类型
}
```

### Payload（负载）

```json
{
  "sub": "1234567890",      // 主题（subject），通常放用户 ID
  "name": "admin",          // 自定义字段
  "userId": 1,
  "role": "ADMIN",
  "iat": 1516239022,        // 签发时间（Issued At）
  "exp": 1516242622         // 过期时间（Expiration）
}
```

标准声明（Registered Claims）：

| 声明 | 含义 |
|------|------|
| sub | 主题（subject），用户标识 |
| iss | 签发者（issuer） |
| aud | 接收者（audience） |
| exp | 过期时间（expiration） |
| nbf | 生效时间（not before） |
| iat | 签发时间（issued at） |
| jti | JWT 唯一标识（ID） |

### Signature（签名）

```text
签名算法：HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

签名作用：**防篡改**。任何人改了 Payload，签名就对不上，服务器能发现。

### 关键理解

```text
JWT 的 Payload 只是 base64Url 编码，任何人可以解码看到内容，
所以绝不能在 Payload 放敏感信息（密码、密钥）。

JWT 的安全靠签名保证"内容没被篡改"，不靠"内容不可见"。
要保密需额外加密（JWE），但实际项目很少用。
```

## JWT 依赖与工具类

### 引入依赖

```xml
<!-- jjwt 库（最流行的 Java JWT 实现） -->
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-api</artifactId>
    <version>0.12.5</version>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-impl</artifactId>
    <version>0.12.5</version>
    <scope>runtime</scope>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-jackson</artifactId>
    <version>0.12.5</version>
    <scope>runtime</scope>
</dependency>
```

### JWT 工具类

```java
@Component
public class JwtUtil {

    @Value("${jwt.secret}")
    private String secret;  // 密钥（至少 32 字节）

    @Value("${jwt.expiration}")
    private long expiration;  // 过期时间（毫秒）

    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    // 生成 Token
    public String generateToken(Long userId, String username, List<String> roles) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + expiration);

        return Jwts.builder()
            .subject(String.valueOf(userId))     // sub = userId
            .claim("username", username)         // 自定义字段
            .claim("roles", roles)
            .issuedAt(now)                       // iat
            .expiration(expiry)                  // exp
            .signWith(getSigningKey())           // 签名
            .compact();
    }

    // 解析 Token（校验签名 + 过期）
    public Claims parseToken(String token) {
        return Jwts.parser()
            .verifyWith(getSigningKey())
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }

    // 从 Token 获取 userId
    public Long getUserId(String token) {
        return Long.parseLong(parseToken(token).getSubject());
    }

    // 从 Token 获取用户名
    public String getUsername(String token) {
        return parseToken(token).get("username", String.class);
    }

    // 判断 Token 是否过期
    public boolean isExpired(String token) {
        return parseToken(token).getExpiration().before(new Date());
    }
}
```

### JWT 配置

```yaml
jwt:
  secret: mySecretKeyThatIsAtLeast32BytesLong1234567890
  expiration: 3600000      # Access Token 1 小时
  refresh-expiration: 604800000  # Refresh Token 7 天
```

## Access Token 与 Refresh Token

单一 JWT 的困境：Token 有效期长了不安全（泄露后长时间有效），短了用户体验差（频繁重新登录）。双 Token 机制解决这个矛盾。

### 双 Token 机制

```text
Access Token（访问令牌）
- 有效期短（15 分钟 ~ 2 小时）
- 用于访问受保护资源
- 泄露影响有限

Refresh Token（刷新令牌）
- 有效期长（7 天 ~ 30 天）
- 只用于换取新的 Access Token
- 泄露风险大，需安全存储
```

### 双 Token 工作流程

```text
1. 登录成功 → 返回 accessToken + refreshToken
2. 客户端访问 API → 携带 accessToken
3. accessToken 过期 → 客户端用 refreshToken 请求刷新接口
4. 服务器校验 refreshToken → 返回新的 accessToken（+ 可选新 refreshToken）
5. refreshToken 也过期 → 要求重新登录
```

### 登录接口返回双 Token

```java
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @PostMapping("/login")
    public Result<TokenResponse> login(@RequestBody LoginRequest request) {
        // 认证逻辑（验证用户名密码）
        User user = authService.authenticate(request);

        // 生成双 Token
        String accessToken = jwtUtil.generateToken(user.getId(), user.getUsername(), user.getRoles());
        String refreshToken = jwtUtil.generateRefreshToken(user.getId());

        return Result.success(new TokenResponse(accessToken, refreshToken));
    }
}

public class TokenResponse {
    private String accessToken;
    private String refreshToken;
    private String tokenType = "Bearer";
    private long expiresIn;
}
```

## Token 过期处理

### 过期异常处理

```java
// 解析 Token 时的异常处理
public Claims parseTokenWithGrace(String token) {
    try {
        return jwtUtil.parseToken(token);
    } catch (ExpiredJwtException e) {
        // Token 过期
        throw new BusinessException(40101, "Token 已过期");
    } catch (JwtException e) {
        // Token 无效（签名错误、格式错误）
        throw new BusinessException(40102, "Token 无效");
    }
}
```

jjwt 的异常类型：

| 异常 | 含义 |
|------|------|
| ExpiredJwtException | Token 过期 |
| SignatureException | 签名错误 |
| MalformedJwtException | 格式错误 |
| UnsupportedJwtException | 不支持的 Token |

### 过期检测时机

```text
1. 前端：解码 accessToken 的 exp，提前刷新（如提前 1 分钟）
2. 后端：解析时校验 exp，过期抛 401
3. 前端收到 401：用 refreshToken 刷新，重试原请求
```

## Token 黑名单

JWT 无状态的代价是无法主动失效。黑名单是解决方案。

### 什么时候需要黑名单

```text
1. 用户登出 —— 希望 Token 立即失效
2. 用户改密码 —— 旧的 Token 应失效
3. 账号被盗 —— 强制下线
4. Refresh Token 刷新后 —— 旧 refreshToken 作废
```

### 黑名单实现（Redis）

```java
@Service
public class TokenBlacklistService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    // 加入黑名单（存到 Token 过期时间）
    public void blacklist(String token, long ttlSeconds) {
        // key = 黑名单前缀 + jti（Token 唯一标识）
        String key = "token:blacklist:" + jwtUtil.getJti(token);
        redisTemplate.opsForValue().set(key, "1", ttlSeconds, TimeUnit.SECONDS);
    }

    // 检查是否在黑名单
    public boolean isBlacklisted(String token) {
        String key = "token:blacklist:" + jwtUtil.getJti(token);
        return Boolean.TRUE.equals(redisTemplate.hasKey(key));
    }
}
```

### 登出时加入黑名单

```java
@PostMapping("/logout")
public Result logout(@RequestHeader("Authorization") String authHeader) {
    String token = extractToken(authHeader);
    long remainingTtl = jwtUtil.getRemainingTtl(token);
    tokenBlacklistService.blacklist(token, remainingTtl);
    return Result.success("登出成功");
}
```

### 在 JWT Filter 中检查黑名单

```java
if (tokenBlacklistService.isBlacklisted(token)) {
    response.setStatus(401);
    response.getWriter().write("{\"code\":401,\"msg\":\"Token 已失效\"}");
    return;
}
```

### 黑名单的权衡

```text
黑名单让 JWT 变得"有状态"（需要查 Redis），部分牺牲了 JWT 的无状态优势。
但这是"既要安全又要可撤销"的务实选择。

替代方案：
1. 短有效期 Access Token（15 分钟），靠过期自然失效，不用黑名单
2. 只对 refreshToken 做黑名单（数量少），accessToken 靠短有效期
```

## Token 刷新流程

### 刷新接口

```java
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @PostMapping("/refresh")
    public Result<TokenResponse> refresh(@RequestBody RefreshRequest request) {
        String refreshToken = request.getRefreshToken();

        // 1. 校验 refreshToken
        if (!jwtUtil.isRefreshToken(refreshToken)) {
            throw new BusinessException(401, "无效的刷新令牌");
        }
        if (jwtUtil.isExpired(refreshToken)) {
            throw new BusinessException(401, "刷新令牌已过期，请重新登录");
        }
        // 2. 检查黑名单（旧的 refreshToken 已作废）
        if (tokenBlacklistService.isBlacklisted(refreshToken)) {
            throw new BusinessException(401, "刷新令牌已失效，请重新登录");
        }

        // 3. 旧的 refreshToken 作废，生成新的
        Long userId = jwtUtil.getUserId(refreshToken);
        User user = userService.findById(userId);
        tokenBlacklistService.blacklist(refreshToken, jwtUtil.getRemainingTtl(refreshToken));

        String newAccessToken = jwtUtil.generateToken(user.getId(), user.getUsername(), user.getRoles());
        String newRefreshToken = jwtUtil.generateRefreshToken(user.getId());

        return Result.success(new TokenResponse(newAccessToken, newRefreshToken));
    }
}
```

### 前端刷新流程

```javascript
// axios 拦截器：401 时自动刷新
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response.status === 401 && !error.config._retry) {
      error.config._retry = true;
      try {
        const { accessToken } = await refreshToken();  // 调用刷新接口
        error.config.headers.Authorization = `Bearer ${accessToken}`;
        return axios(error.config);  // 重试原请求
      } catch (e) {
        // 刷新失败，跳转登录页
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

## JWT 集成 Spring Security

### JWT 认证过滤器

```java
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        // 1. 从请求头提取 Token
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);

            try {
                // 2. 解析 Token
                String username = jwtUtil.getUsername(token);

                // 3. 如果当前没有认证信息，加载用户并认证
                if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                    UserDetails userDetails = userDetailsService.loadUserByUsername(username);

                    if (jwtUtil.isValid(token, userDetails)) {
                        UsernamePasswordAuthenticationToken authentication =
                            new UsernamePasswordAuthenticationToken(
                                userDetails, null, userDetails.getAuthorities());
                        authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                        SecurityContextHolder.getContext().setAuthentication(authentication);
                    }
                }
            } catch (Exception e) {
                // Token 无效，不设置认证信息，后续 Filter 会返回 401
            }
        }

        chain.doFilter(request, response);
    }
}
```

### 安全配置集成 JWT

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())  // JWT 无状态，关闭 CSRF
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)  // 无状态，不创建 Session
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/login", "/api/auth/register", "/api/auth/refresh").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint((request, response, e) -> {
                    response.setContentType("application/json;charset=UTF-8");
                    response.setStatus(401);
                    response.getWriter().write("{\"code\":401,\"msg\":\"未登录或Token失效\"}");
                })
            );
        return http.build();
    }
}
```

## 应用场景实战

### 场景 1：完整的 JWT 认证系统

```text
接口设计：
POST /api/auth/register   注册
POST /api/auth/login      登录（返回双 Token）
POST /api/auth/refresh    刷新 Token
POST /api/auth/logout     登出（Token 进黑名单）
GET  /api/users/me        获取当前用户（需要认证）
```

```java
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @PostMapping("/register")
    public Result<Void> register(@RequestBody RegisterRequest request) {
        authService.register(request);
        return Result.success(null);
    }

    @PostMapping("/login")
    public Result<TokenResponse> login(@RequestBody LoginRequest request) {
        return Result.success(authService.login(request));
    }

    @PostMapping("/refresh")
    public Result<TokenResponse> refresh(@RequestBody RefreshRequest request) {
        return Result.success(authService.refresh(request.getRefreshToken()));
    }

    @PostMapping("/logout")
    public Result<Void> logout(@RequestHeader("Authorization") String authHeader) {
        authService.logout(authHeader);
        return Result.success(null);
    }
}
```

### 场景 2：携带角色信息的 JWT

```java
// 生成带角色的 Token
public String generateToken(User user) {
    return Jwts.builder()
        .subject(String.valueOf(user.getId()))
        .claim("username", user.getUsername())
        .claim("roles", user.getRoles())  // ["ADMIN", "USER"]
        .claim("permissions", user.getPermissions())  // ["user:read", "user:write"]
        .signWith(getSigningKey())
        .compact();
}

// 方法级权限校验
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(Long id) { ... }
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Access Token 短、Refresh Token 长**。Access 15-30 分钟，Refresh 7 天，平衡安全与体验。

2. **密钥强度要够**。HS256 的密钥至少 32 字节（256 位），且不能硬编码在代码里（用环境变量/配置中心）。

3. **Payload 不放敏感信息**。只放用户 ID、用户名、角色等非敏感字段，密码、密钥绝不进 Payload。

4. **Refresh Token 用后即废**。每次刷新旧 refreshToken 作废，发新的，防止重放攻击。

5. **登出和改密码必须做黑名单**。否则 Token 在有效期内依然可用。

### 踩坑记录

**坑 1：密钥太短导致签名失败**

```java
String secret = "mySecret";  // 太短！
Keys.hmacShaKeyFor(secret.getBytes());  // WeakKeyException
```

HS256 要求密钥至少 256 位（32 字节）。密钥要足够长且随机。

**坑 2：Payload 泄露敏感信息**

```json
{
  "userId": 1,
  "password": "abc123",  // 危险！任何人都能 base64 解码看到
  "idCard": "110101199001011234"
}
```

Payload 只是 base64 编码，不是加密。敏感信息绝对不能放。

**坑 3：Token 过期后未清理 SecurityContext**

```java
// 解析 Token 抛 ExpiredJwtException，但没清理已设置的 SecurityContext
catch (Exception e) {
    // 应该：SecurityContextHolder.clearContext();
}
```

认证失败时要清理上下文，防止残留错误的认证信息。

**坑 4：JWT Filter 拦截了放行路径**

```java
// JwtAuthenticationFilter 对所有请求都解析 Token，
// 包括 /api/auth/login 这种放行路径
// 如果 login 请求带了无效 Token，可能被误拦截
```

Filter 中要先判断请求路径是否放行，或确保解析失败时不设置认证信息、继续走 Filter 链。

**坑 5：刷新接口的 Token 类型混淆**

```java
// 用 accessToken 去刷新接口，或刷新逻辑没区分 access/refresh token
// 应该在 Token 中加 type 字段区分
String tokenType = jwtUtil.getType(token);  // "access" 或 "refresh"
```

在 Payload 中加 `type` 字段区分 Token 类型，刷新接口只接受 refresh token。

**坑 6：Session 没关闭导致状态混乱**

```java
// 用了 JWT 但没配置 STATELESS
// Spring Security 默认会创建 Session，导致 JWT 和 Session 并存，语义混乱
http.sessionManagement(session -> session
    .sessionCreationPolicy(SessionCreationPolicy.STATELESS));
```

JWT 无状态认证必须配置 STATELESS，否则 Spring Security 仍会创建 Session。
