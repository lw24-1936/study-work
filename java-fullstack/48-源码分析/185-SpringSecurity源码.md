---
title: Spring Security 源码分析
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springsecurity源码, filterchain, authentication, securitycontext, authorization]
---

# Spring Security 源码分析

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [FilterChain 过滤器链](#filterchain-过滤器链)
- [Authentication 认证](#authentication-认证)
- [SecurityContext 安全上下文](#securitycontext-安全上下文)
- [Authorization 授权](#authorization-授权)
- [认证授权流程](#认证授权流程)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Security 基于过滤器链实现认证授权，理解其源码能深入理解安全机制。

```text
Spring Security 的核心：
1. FilterChain —— 过滤器链（安全处理入口）
2. Authentication —— 认证（你是谁）
3. SecurityContext —— 安全上下文（存储认证信息）
4. Authorization —— 授权（你能做什么）
```

## FilterChain 过滤器链

Spring Security 的核心是一组过滤器链。

### 过滤器链

```text
Spring Security 的过滤器链（核心过滤器）：
1. SecurityContextPersistenceFilter —— 管理 SecurityContext
2. UsernamePasswordAuthenticationFilter —— 处理登录
3. BasicAuthenticationFilter —— HTTP Basic 认证
4. ExceptionTranslationFilter —— 异常处理（未认证跳登录）
5. FilterSecurityInterceptor —— 授权检查
```

### 过滤器链的作用

```text
请求 → 过滤器链（逐个处理）→ 控制器

每个过滤器负责一个安全职责：
认证过滤器 → 提取凭证、验证
授权过滤器 → 检查权限
异常过滤器 → 处理认证/授权异常
```

### 自定义过滤器

```java
// 自定义 JWT 过滤器（加在 UsernamePasswordAuthenticationFilter 之前）
@Component
public class JwtFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(request, response, chain) {
        String token = extractToken(request);
        if (token != null && jwtUtil.isValid(token)) {
            // 设置认证信息到 SecurityContext
            setAuthentication(token);
        }
        chain.doFilter(request, response);
    }
}
```

## Authentication 认证

Authentication 是认证的核心接口，表示认证信息。

### Authentication 接口

```java
public interface Authentication {
    Collection<? extends GrantedAuthority> getAuthorities();  // 权限
    Object getCredentials();      // 凭证（密码）
    Object getDetails();          // 详情
    Object getPrincipal();        // 主体（用户）
    boolean isAuthenticated();    // 是否认证
}
```

### 认证流程

```text
1. 用户提交用户名密码
2. AuthenticationManager 验证
3. 验证通过 → 创建 Authentication（已认证）
4. 存入 SecurityContext
```

### AuthenticationManager 与 Provider

```text
AuthenticationManager —— 认证管理器（接口）
ProviderManager —— 默认实现（委托给多个 AuthenticationProvider）

AuthenticationProvider：
DaoAuthenticationProvider —— 从数据库加载用户验证（最常用）
```

```text
DaoAuthenticationProvider 的验证流程：
1. 从数据库加载用户（UserDetailsService）
2. 比对密码（PasswordEncoder.matches）
3. 验证通过 → 返回已认证的 Authentication
```

## SecurityContext 安全上下文

SecurityContext 存储当前认证信息。

### SecurityContext 与 SecurityContextHolder

```text
SecurityContext —— 存储 Authentication
SecurityContextHolder —— 持有 SecurityContext（ThreadLocal）
```

```java
// 获取当前登录用户
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
String username = auth.getName();

// 获取用户信息
UserDetails userDetails = (UserDetails) auth.getPrincipal();
```

### SecurityContextHolder 的存储策略

```text
1. MODE_THREADLOCAL —— ThreadLocal（默认，每线程独立）
2. MODE_INHERITABLETHREADLOCAL —— 子线程继承
3. MODE_GLOBAL —— 全局
```

```text
SecurityContextPersistenceFilter 的作用：
请求开始 → 加载 SecurityContext 到 ThreadLocal
请求结束 → 清理 ThreadLocal
```

## Authorization 授权

授权检查用户是否有权限访问资源。

### 授权方式

```text
1. 方法级授权 —— @PreAuthorize 注解
2. URL 级授权 —— 配置 URL 权限
3. 过滤器级 —— FilterSecurityInterceptor
```

```java
// 方法级授权
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(Long id) { ... }

@PreAuthorize("hasAuthority('user:delete')")
public void deleteUser(Long id) { ... }
```

### 授权流程

```text
FilterSecurityInterceptor 的授权：
1. 获取当前 Authentication
2. 获取资源所需的权限
3. 判断用户是否有权限（AccessDecisionManager）
4. 无权限 → 抛 AccessDeniedException
```

### 授权注解的原理

```text
@PreAuthorize 的原理（AOP）：
1. 方法调用前，AOP 拦截
2. 解析 SpEL 表达式（hasRole/hasAuthority）
3. 判断当前用户是否满足
4. 不满足 → 抛异常
```

## 认证授权流程

```text
Spring Security 完整流程：

1. 请求进入过滤器链
2. SecurityContextPersistenceFilter 加载 SecurityContext
3. 认证过滤器（登录）或 JWT 过滤器（token）验证身份
4. 验证通过 → Authentication 存入 SecurityContext
5. FilterSecurityInterceptor 授权检查
6. 有权限 → 访问资源；无权限 → 403
```

## 最佳实践与踩坑记录

### 最佳实践

1. **理解过滤器链**。安全是一组过滤器，不是单个组件。

2. **密码用 BCrypt**。DaoAuthenticationProvider + PasswordEncoder。

3. **JWT 用 OncePerRequestFilter**。每次请求校验 token。

4. **方法级授权用 @PreAuthorize**。细粒度控制。

5. **SecurityContext 是 ThreadLocal**。异步线程注意传递。

### 踩坑记录

**坑 1：放行配置错误**

```java
// 放行静态资源，但配置错误，导致无法访问
http.authorizeHttpRequests()
    .requestMatchers("/api/**").permitAll();   // 顺序问题
```

放行路径要准确，注意匹配顺序。

**坑 2：密码没编码**

```text
密码没 BCrypt 编码，DaoAuthenticationProvider 验证失败
```

密码用 BCrypt 存储和验证。

**坑 3：JWT 过滤器顺序错误**

```text
JWT 过滤器加在认证过滤器之后，token 认证不生效
```

JWT 过滤器加在 UsernamePasswordAuthenticationFilter 之前。

**坑 4：SecurityContext 异步丢失**

```text
@Async 异步方法里拿不到 SecurityContext（ThreadLocal 丢失）
```

配置 MODE_INHERITABLETHREADLOCAL，或显式传递。

**坑 5：@PreAuthorize 不生效**

```text
没开启 @EnableMethodSecurity，注解不生效
```

开启 @EnableMethodSecurity(prePostEnabled = true)。

**坑 6：CSRF 导致接口 403**

```text
前后端分离，CSRF 防护导致 POST 请求 403
```

无状态 JWT 场景关闭 CSRF（http.csrf().disable()）。
