---
title: Spring Security 基础
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-security, authentication, authorization, securitycontext, filterchain, passwordencoder, userdetails, userdetailsservice]
---

# Spring Security 基础

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Authentication 与 Authorization](#authentication-与-authorization)
- [SecurityContext 安全上下文](#securitycontext-安全上下文)
- [Filter Chain 过滤器链](#filter-chain-过滤器链)
- [UserDetails 与 UserDetailsService](#userdetails-与-userdetailsservice)
- [PasswordEncoder 密码编码器](#passwordencoder-密码编码器)
- [DaoAuthenticationProvider 认证流程](#daoauthenticationprovider-认证流程)
- [授权配置](#授权配置)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Security 是 Spring 生态的安全框架，提供认证（Authentication）和授权（Authorization）两大核心能力，以及防护常见 Web 攻击（CSRF、会话固定、点击劫持等）。

```text
Spring Security 核心能力：
1. 认证（Authentication）—— 你是谁？验证身份
2. 授权（Authorization）—— 你能干什么？权限控制
3. 攻击防护 —— CSRF、Session Fixation、XSS、点击劫持
4. 与 Spring 无缝集成 —— Filter 链 + 注解 + AOP
```

```text
核心概念关系：
用户输入凭据 → AuthenticationManager 认证 → 生成 Authentication
→ 存入 SecurityContextHolder → Filter 链拦截请求 → 授权检查
```

## Authentication 与 Authorization

### 两个概念的区别

| 维度 | Authentication（认证） | Authorization（授权） |
|------|----------------------|---------------------|
| 问题 | 你是谁？ | 你能干什么？ |
| 时机 | 先认证 | 后授权 |
| 手段 | 密码、Token、指纹 | 角色、权限、ACL |
| 失败 | 401 Unauthorized | 403 Forbidden |

```text
流程：
1. 用户登录（Authentication）→ 身份确认
2. 访问资源（Authorization）→ 权限校验
3. 认证是授权的前提
```

### Authentication 接口

Authentication 是认证信息的核心载体：

```java
public interface Authentication extends Principal, Serializable {

    Collection<? extends GrantedAuthority> getAuthorities();  // 权限列表
    Object getCredentials();       // 凭据（密码/token，认证后通常清除）
    Object getDetails();           // 额外信息（IP、会话等）
    Object getPrincipal();         // 主体（认证前是用户名，认证后是 UserDetails）
    boolean isAuthenticated();     // 是否已认证
    void setAuthenticated(boolean isAuthenticated);
}
```

### 认证方式

```text
Spring Security 支持的认证方式：
1. 表单登录（Form Login）—— 用户名密码表单
2. HTTP Basic —— Authorization: Basic base64(user:pass)
3. HTTP Digest —— 摘要认证
4. JWT Token —— 无状态 token 认证
5. OAuth2 —— 第三方授权登录
6. LDAP / CAS / SAML —— 企业级 SSO
```

## SecurityContext 安全上下文

SecurityContext 保存当前请求的认证信息，通过 ThreadLocal 与当前线程绑定。

### SecurityContextHolder

```java
// 获取当前认证信息
Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

// 获取当前用户名
String username = authentication.getName();

// 获取当前用户详情
UserDetails userDetails = (UserDetails) authentication.getPrincipal();

// 判断是否已认证
boolean isAuthenticated = authentication.isAuthenticated();

// 获取权限
Collection<? extends GrantedAuthority> authorities = authentication.getAuthorities();
```

### SecurityContext 的存储策略

```java
// 三种存储模式
SecurityContextHolder.MODE_THREADLOCAL        // 默认：ThreadLocal（每个线程独立）
SecurityContextHolder.MODE_INHERITABLETHREADLOCAL  // 子线程继承父线程
SecurityContextHolder.MODE_GLOBAL             // 全局共享（不推荐）
```

```java
// 配置存储策略
SecurityContextHolder.setStrategyName(SecurityContextHolder.MODE_THREADLOCAL);
```

**关键**：ThreadLocal 模式意味着认证信息只在当前线程有效。异步线程（@Async、新 Thread）中获取不到认证信息，需要手动传递。

### 在业务代码中获取当前用户

```java
// 方式 1：SecurityContextHolder 直接获取
public String getCurrentUsername() {
    Authentication auth = SecurityContextHolder.getContext().getAuthentication();
    return auth != null ? auth.getName() : null;
}

// 方式 2：@AuthenticationPrincipal 注解注入（推荐）
@GetMapping("/profile")
public UserDTO profile(@AuthenticationPrincipal UserDetails userDetails) {
    return userService.findByUsername(userDetails.getUsername());
}

// 方式 3：Authentication 参数注入
@GetMapping("/profile")
public UserDTO profile(Authentication authentication) {
    String username = authentication.getName();
    return userService.findByUsername(username);
}
```

### 手动设置认证信息（登录成功后）

```java
UsernamePasswordAuthenticationToken token =
    new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
SecurityContextHolder.getContext().setAuthentication(token);
```

## Filter Chain 过滤器链

Spring Security 基于 Servlet Filter 实现，核心是 Filter Chain 和 DelegatingFilterProxy。

### SecurityFilterChain

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/login", "/register", "/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/**").authenticated()
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .defaultSuccessUrl("/home")
            )
            .logout(logout -> logout
                .logoutUrl("/logout")
                .logoutSuccessUrl("/login")
            )
            .csrf(Customizer.withDefaults());
        return http.build();
    }
}
```

### DelegatingFilterProxy

Spring Security 的入口是一个名为 `springSecurityFilterChain` 的 Filter，通过 DelegatingFilterProxy 委托：

```text
请求 → DelegatingFilterProxy → FilterChainProxy → SecurityFilterChain → 各个 Security Filter
```

### 核心 Security Filter 执行顺序

```text
1.  SecurityContextPersistenceFilter   —— 加载/保存 SecurityContext
2.  CsrfFilter                         —— CSRF 防护
3.  LogoutFilter                       —— 处理登出
4.  UsernamePasswordAuthenticationFilter —— 表单登录认证
5.  BasicAuthenticationFilter          —— HTTP Basic 认证
6.  ExceptionTranslationFilter         —— 异常翻译（401/403）
7.  AuthorizationFilter                —— 授权检查
```

### Filter Chain 的核心概念

```text
SecurityFilterChain：一组 Security Filter 的集合，可以有多个（不同的链匹配不同 URL）
FilterChainProxy：管理所有 SecurityFilterChain，按 URL 匹配分发
```

## UserDetails 与 UserDetailsService

### UserDetails 接口

UserDetails 是 Spring Security 的用户信息抽象：

```java
public interface UserDetails extends Serializable {
    Collection<? extends GrantedAuthority> getAuthorities();  // 权限
    String getPassword();              // 密码
    String getUsername();              // 用户名
    boolean isAccountNonExpired();     // 账号未过期
    boolean isAccountNonLocked();      // 账号未锁定
    boolean isCredentialsNonExpired(); // 凭据未过期
    boolean isEnabled();               // 账号可用
}
```

### 自定义 UserDetails 实现

```java
public class LoginUser implements UserDetails {

    private final User user;
    private final List<String> permissions;

    public LoginUser(User user, List<String> permissions) {
        this.user = user;
        this.permissions = permissions;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return permissions.stream()
            .map(SimpleGrantedAuthority::new)
            .collect(Collectors.toList());
    }

    @Override
    public String getPassword() { return user.getPassword(); }

    @Override
    public String getUsername() { return user.getUsername(); }

    @Override
    public boolean isAccountNonExpired() { return true; }

    @Override
    public boolean isAccountNonLocked() { return !user.isLocked(); }

    @Override
    public boolean isCredentialsNonExpired() { return true; }

    @Override
    public boolean isEnabled() { return user.isEnabled(); }
}
```

### UserDetailsService 接口

UserDetailsService 负责从数据源加载用户：

```java
public interface UserDetailsService {
    UserDetails loadUserByUsername(String username) throws UsernameNotFoundException;
}
```

```java
@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    @Autowired
    private UserMapper userMapper;

    @Override
    public UserDetails loadUserByUsername(String username) {
        // 1. 查询用户
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new UsernameNotFoundException("用户不存在：" + username);
        }

        // 2. 查询用户权限
        List<String> permissions = userMapper.findPermissions(user.getId());

        // 3. 构造 UserDetails
        return new LoginUser(user, permissions);
    }
}
```

### 内存用户（开发/测试）

```java
@Bean
public UserDetailsService userDetailsService() {
    UserDetails admin = User.withUsername("admin")
        .password(passwordEncoder().encode("123456"))
        .roles("ADMIN")
        .build();

    UserDetails user = User.withUsername("user")
        .password(passwordEncoder().encode("123456"))
        .roles("USER")
        .build();

    return new InMemoryUserDetailsManager(admin, user);
}
```

## PasswordEncoder 密码编码器

PasswordEncoder 负责密码的加密和校验。**绝不存储明文密码**。

### PasswordEncoder 接口

```java
public interface PasswordEncoder {
    String encode(CharSequence rawPassword);                    // 加密
    boolean matches(CharSequence rawPassword, String encodedPassword);  // 校验
    default boolean upgradeEncoding(String encodedPassword) { return false; }
}
```

### BCryptPasswordEncoder（推荐）

```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}
```

```java
// 使用
String encoded = passwordEncoder.encode("123456");  // $2a$10$...
boolean matches = passwordEncoder.matches("123456", encoded);  // true
```

BCrypt 特点：
- 自带盐值（每次加密结果不同）
- 计算强度可调（cost factor，默认 10）
- 抗暴力破解

### 其他编码器

| 编码器 | 说明 | 安全性 |
|--------|------|--------|
| BCryptPasswordEncoder | 主流，推荐 | 高 |
| SCryptPasswordEncoder | 内存敏感型 | 高 |
| Argon2PasswordEncoder | 最新，密码哈希竞赛冠军 | 最高 |
| Pbkdf2PasswordEncoder | PBKDF2 算法 | 高 |
| NoOpPasswordEncoder | 明文，仅测试 | 无 |
| DelegatingPasswordEncoder | 委托，支持多种格式 | 取决于委托 |

### DelegatingPasswordEncoder

支持多种密码格式，格式为 `{算法}密码`：

```java
@Bean
public PasswordEncoder passwordEncoder() {
    String idForEncode = "bcrypt";
    Map<String, PasswordEncoder> encoders = new HashMap<>();
    encoders.put(idForEncode, new BCryptPasswordEncoder());
    encoders.put("noop", NoOpPasswordEncoder.getInstance());
    encoders.put("pbkdf2", new Pbkdf2PasswordEncoder());
    return new DelegatingPasswordEncoder(idForEncode, encoders);
}
```

```text
存储格式：{bcrypt}$2a$10$...（bcrypt 加密）
        {noop}123456（明文，仅测试）
        {pbkdf2}...（pbkdf2 加密）
```

好处：可以平滑迁移密码算法，旧密码用旧算法校验，新密码用新算法。

## DaoAuthenticationProvider 认证流程

DaoAuthenticationProvider 是用户名密码认证的核心，它组合 UserDetailsService 和 PasswordEncoder。

### 认证流程

```text
1. 用户提交用户名密码
2. UsernamePasswordAuthenticationFilter 捕获凭据
3. 调用 AuthenticationManager（ProviderManager）
4. ProviderManager 委托给 DaoAuthenticationProvider
5. DaoAuthenticationProvider 调用 UserDetailsService.loadUserByUsername()
6. 拿到 UserDetails 后，用 PasswordEncoder.matches() 校验密码
7. 校验通过，创建已认证的 Authentication
8. 存入 SecurityContextHolder
```

### 手动配置 AuthenticationManager

```java
@Bean
public AuthenticationManager authenticationManager(
        UserDetailsService userDetailsService,
        PasswordEncoder passwordEncoder) {

    DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
    provider.setUserDetailsService(userDetailsService);
    provider.setPasswordEncoder(passwordEncoder);
    return new ProviderManager(provider);
}
```

### 手动认证（登录接口）

```java
@RestController
public class AuthController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @PostMapping("/login")
    public Result login(@RequestBody LoginRequest request) {
        // 1. 构造认证 token
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            request.getUsername(), request.getPassword());

        // 2. 执行认证
        Authentication result = authenticationManager.authenticate(authentication);

        // 3. 存入安全上下文
        SecurityContextHolder.getContext().setAuthentication(result);

        // 4. 返回结果
        return Result.success("登录成功");
    }
}
```

## 授权配置

### URL 级别授权

```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/", "/login", "/css/**", "/js/**").permitAll()  // 公开
        .requestMatchers("/admin/**").hasRole("ADMIN")                   // 角色
        .requestMatchers("/user/**").hasAnyRole("USER", "ADMIN")         // 多角色
        .requestMatchers("/api/**").hasAuthority("api:read")             // 权限
        .anyRequest().authenticated()                                    // 其余需认证
    );
    return http.build();
}
```

授权表达式：

```text
permitAll()            —— 所有用户可访问
denyAll()              —— 所有用户不可访问
authenticated()        —— 已认证
anonymous()            —— 匿名
hasRole("ADMIN")       —— 有 ADMIN 角色（ROLE_ADMIN 权限）
hasAnyRole("A", "B")   —— 有 A 或 B 角色
hasAuthority("xxx")    —— 有 xxx 权限
hasAnyAuthority(...)   —— 有任一权限
```

### 方法级别授权

```java
@Configuration
@EnableMethodSecurity  // 启用方法级安全（Spring Security 6.x）
public class MethodSecurityConfig { }
```

```java
@Service
public class UserService {

    @PreAuthorize("hasRole('ADMIN')")
    public List<User> findAll() { ... }

    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public User findById(Long id) { ... }

    @PreAuthorize("#id == authentication.principal.id")
    public User getOwnProfile(Long id) { ... }

    @PreAuthorize("hasAuthority('user:delete')")
    @DeleteMapping("/{id}")
    public void delete(Long id) { ... }

    @PostAuthorize("returnObject.owner == authentication.name")
    public Order getOrder(Long id) { ... }
}
```

## 应用场景实战

### 场景 1：完整的表单登录配置

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 授权规则
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/login", "/register", "/static/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            // 表单登录
            .formLogin(form -> form
                .loginPage("/login")               // 自定义登录页
                .loginProcessingUrl("/doLogin")    // 表单提交地址
                .defaultSuccessUrl("/index")       // 登录成功跳转
                .failureUrl("/login?error")        // 登录失败跳转
                .permitAll()
            )
            // 登出
            .logout(logout -> logout
                .logoutUrl("/logout")
                .logoutSuccessUrl("/login?logout")
                .invalidateHttpSession(true)       // 失效会话
                .deleteCookies("JSESSIONID")       // 删除 Cookie
            )
            // 记住我
            .rememberMe(remember -> remember
                .key("uniqueAndSecret")
                .tokenValiditySeconds(86400)       // 7 天
            )
            // 会话管理
            .sessionManagement(session -> session
                .maximumSessions(1)                // 同一账号最多 1 个会话
                .maxSessionsPreventsLogin(true)    // 达到上限阻止新登录
            )
            // 异常处理
            .exceptionHandling(ex -> ex
                .accessDeniedPage("/403")          // 无权限跳转
            );
        return http.build();
    }
}
```

### 场景 2：前后端分离的认证（返回 JSON）

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())  // 前后端分离（无 Cookie），关闭 CSRF
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .anyRequest().authenticated()
            )
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint((request, response, e) -> {
                    // 未认证返回 JSON
                    response.setContentType("application/json;charset=UTF-8");
                    response.setStatus(401);
                    response.getWriter().write("{\"code\":401,\"msg\":\"未登录\"}");
                })
                .accessDeniedHandler((request, response, e) -> {
                    // 无权限返回 JSON
                    response.setContentType("application/json;charset=UTF-8");
                    response.setStatus(403);
                    response.getWriter().write("{\"code\":403,\"msg\":\"无权限\"}");
                })
            );
        return http.build();
    }
}
```

### 场景 3：数据库用户 + 自定义权限

```java
@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    @Autowired
    private UserMapper userMapper;

    @Override
    public UserDetails loadUserByUsername(String username) {
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new UsernameNotFoundException("用户不存在");
        }

        // 加载权限（如 ROLE_ADMIN、user:read 等）
        List<String> authorities = userMapper.findAuthorities(user.getId());

        return org.springframework.security.core.userdetails.User
            .withUsername(user.getUsername())
            .password(user.getPassword())  // 数据库存的 BCrypt 密文
            .authorities(authorities.toArray(new String[0]))
            .disabled(!user.isEnabled())
            .build();
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **密码用 BCrypt，绝不明文存储**。`PasswordEncoder` 统一用 BCryptPasswordEncoder，数据库存密文。

2. **用 @AuthenticationPrincipal 获取当前用户**，比 SecurityContextHolder 更简洁、更类型安全。

3. **CSRF 防护不要盲目关闭**。前后端分离且不用 Cookie 时可以关，但用 Cookie/Session 认证时必须开启。

4. **方法级权限用 @PreAuthorize**。比 URL 级别更细粒度，权限紧贴业务方法。

5. **认证失败信息要模糊**。返回"用户名或密码错误"，不要区分"用户不存在"和"密码错误"，防止用户名枚举攻击。

### 踩坑记录

**坑 1：密码编码器不匹配**

```text
DaoAuthenticationProvider 找不到 PasswordEncoder，
或数据库中存的明文但配置了 BCrypt，导致认证失败：
BadCredentialsException
```

确保：注册 PasswordEncoder Bean + 数据库存 BCrypt 密文 + 注册用户时用同一个 encoder 加密。

**坑 2：@EnableWebSecurity 的配置类被 @ComponentScan 重复加载**

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig { }
// 如果 SecurityConfig 被 @ComponentScan 扫描到，可能加载两次
```

SecurityConfig 通常放在主包下由组件扫描加载一次，不要额外手动注册。

**坑 3：Spring Security 6.x 的 API 变化**

```java
// Spring Security 5.x（旧写法，已废弃）
http.authorizeRequests().antMatchers("/admin/**").hasRole("ADMIN");

// Spring Security 6.x（新写法）
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/admin/**").hasRole("ADMIN"));
```

`antMatchers` 已废弃，改用 `requestMatchers`。`@EnableGlobalMethodSecurity` 改用 `@EnableMethodSecurity`。

**坑 4：SecurityContext 在异步线程丢失**

```java
@Async
public void sendNotification() {
    // 这里 SecurityContextHolder.getContext() 是空的！
    // ThreadLocal 不跨线程
}
```

解法：使用 `DelegatingSecurityContextAsyncTaskExecutor`，或手动传递 SecurityContext。

**坑 5：放行路径不生效**

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/api/auth/login").permitAll()
    .anyRequest().authenticated()
);
// 如果登录接口在 Filter 层被其他逻辑拦截（如自定义 JWT Filter），permitAll 可能不生效
```

自定义 Filter 要正确处理放行逻辑，否则 permitAll 的路径也会被拦截。

**坑 6：getPrincipal() 类型转换错误**

```java
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
// 匿名用户的 principal 是 String "anonymousUser"，不是 UserDetails
UserDetails userDetails = (UserDetails) auth.getPrincipal();  // ClassCastException！
```

匿名用户（未登录）的 principal 是字符串。转换前先判断 `auth.getPrincipal() instanceof UserDetails`。
