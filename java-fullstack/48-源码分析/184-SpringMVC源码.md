---
title: Spring MVC 源码分析
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [springmvc源码, dispatcherservlet, handlermapping, handleradapter, handlermethod, argumentresolver, returnvaluehandler]
---

# Spring MVC 源码分析

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [DispatcherServlet 前端控制器](#dispatcherservlet-前端控制器)
- [HandlerMapping 处理器映射](#handlermapping-处理器映射)
- [HandlerAdapter 处理器适配器](#handleradapter-处理器适配器)
- [ArgumentResolver 参数解析](#argumentresolver-参数解析)
- [ReturnValueHandler 返回值处理](#returnvaluehandler-返回值处理)
- [请求处理流程](#请求处理流程)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring MVC 是经典的 Web 框架，理解其源码能深入理解请求处理的完整链路。

```text
Spring MVC 的核心组件：
DispatcherServlet —— 前端控制器（总入口）
HandlerMapping —— 处理器映射（找到处理器）
HandlerAdapter —— 处理器适配器（调用处理器）
ArgumentResolver —— 参数解析
ReturnValueHandler —— 返回值处理
```

## DispatcherServlet 前端控制器

DispatcherServlet 是 Spring MVC 的总入口，协调所有组件。

### 处理流程

```text
DispatcherServlet 的 doDispatch 流程：
1. 根据请求找到 Handler（HandlerMapping）
2. 找到 HandlerAdapter
3. 执行拦截器前置（preHandle）
4. 调用 Handler（参数解析 + 业务逻辑 + 返回值处理）
5. 执行拦截器后置（postHandle）
6. 视图渲染（或返回 JSON）
7. 执行拦截器完成后（afterCompletion）
```

### 核心代码

```java
// DispatcherServlet.doDispatch（简化）
protected void doDispatch(HttpServletRequest request, HttpServletResponse response) {
    // 1. 找到 Handler
    HandlerExecutionChain chain = getHandler(request);
    HandlerAdapter adapter = getHandlerAdapter(chain.getHandler());

    // 2. 拦截器前置
    if (!chain.applyPreHandle(request, response)) return;

    // 3. 调用 Handler
    ModelAndView mv = adapter.handle(request, response, chain.getHandler());

    // 4. 拦截器后置
    chain.applyPostHandle(request, response, mv);

    // 5. 渲染
    processDispatchResult(request, response, chain, mv);
}
```

## HandlerMapping 处理器映射

HandlerMapping 根据请求找到对应的处理器。

### 常见的 HandlerMapping

```text
1. RequestMappingHandlerMapping —— @RequestMapping 注解（最常用）
2. SimpleUrlHandlerMapping —— URL 映射
3. BeanNameUrlHandlerMapping —— Bean 名作为 URL
```

### 工作原理

```text
RequestMappingHandlerMapping 的工作：
1. 启动时扫描所有 @Controller
2. 解析 @RequestMapping 注解
3. 建立 URL → HandlerMethod 的映射
4. 请求时根据 URL 找到 HandlerMethod
```

## HandlerAdapter 处理器适配器

HandlerAdapter 调用处理器，是适配器模式的应用。

### 常见的 HandlerAdapter

```text
1. RequestMappingHandlerAdapter —— 处理 @RequestMapping 方法
2. HttpRequestHandlerAdapter —— 处理 HttpRequestHandler
3. SimpleControllerHandlerAdapter —— 处理 Controller 接口
```

### 工作原理

```text
HandlerAdapter 的 handle 方法：
1. 解析参数（ArgumentResolver）
2. 调用 Handler 方法
3. 处理返回值（ReturnValueHandler）
```

```java
// RequestMappingHandlerAdapter.handleInternal（简化）
protected ModelAndView handleInternal(...) {
    // 1. 解析参数
    Object[] args = resolveArguments(handlerMethod);

    // 2. 调用方法
    Object returnValue = handlerMethod.invoke(bean, args);

    // 3. 处理返回值
    handleReturnValue(returnValue);
}
```

## ArgumentResolver 参数解析

ArgumentResolver 负责把 HTTP 请求解析成方法参数。

### 常见参数解析器

```text
1. @RequestParam —— 查询参数
2. @PathVariable —— 路径参数
3. @RequestBody —— JSON 请求体
4. @ModelAttribute —— 表单对象
5. @RequestHeader —— 请求头
```

```java
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id,           // 路径参数
                    @RequestParam String name,        // 查询参数
                    @RequestHeader String token) {    // 请求头
    // ...
}
```

### 工作原理

```text
每个参数类型对应一个 ArgumentResolver：
1. 遍历方法参数
2. 找到支持的 ArgumentResolver
3. 解析参数
```

## ReturnValueHandler 返回值处理

ReturnValueHandler 负责处理方法的返回值。

### 常见返回值处理器

```text
1. @ResponseBody —— 返回 JSON
2. ModelAndView —— 视图
3. String —— 视图名
4. ResponseEntity —— 完整响应
```

```java
// @ResponseBody 返回 JSON
@GetMapping("/users/{id}")
@ResponseBody
public User getUser(@PathVariable Long id) {
    return userService.get(id);   // 转 JSON
}
```

### 工作原理

```text
1. 方法返回后，找到支持的 ReturnValueHandler
2. @ResponseBody → 用 HttpMessageConverter 转 JSON
3. 写回响应
```

## 请求处理流程

```text
Spring MVC 完整请求流程：

请求 → DispatcherServlet
     → HandlerMapping（找到 Handler）
     → HandlerAdapter
     → 拦截器 preHandle
     → ArgumentResolver（解析参数）
     → 调用 Handler 方法（业务逻辑）
     → ReturnValueHandler（处理返回值）
     → 拦截器 postHandle
     → 响应
```

## 最佳实践与踩坑记录

### 最佳实践

1. **理解 DispatcherServlet**。所有请求的总入口。

2. **自定义参数解析器**。特殊参数用自定义 ArgumentResolver。

3. **拦截器做通用逻辑**。鉴权、日志用拦截器。

4. **@ResponseBody 返回 JSON**。前后端分离的标准。

5. **理解 HandlerAdapter**。适配器模式的应用。

### 踩坑记录

**坑 1：拦截器不生效**

```text
拦截器注册了但没拦截（路径配置错误）
```

检查拦截器路径配置（addPathPatterns）。

**坑 2：参数解析失败**

```text
@RequestBody 解析失败（JSON 格式错误），400 错误
```

前端 JSON 格式正确，字段类型匹配。

**坑 3：@ResponseBody 和视图冲突**

```text
@Controller + 返回 String，以为是 JSON 实则是视图名
```

用 @RestController（= @Controller + @ResponseBody）。

**坑 4：自定义参数解析器没注册**

```text
自定义 ArgumentResolver 没注册到 WebMvcConfigurer
```

实现 WebMvcConfigurer 的 addArgumentResolvers。

**坑 5：静态资源 404**

```text
DispatcherServlet 拦截所有请求，静态资源也被拦截
```

配置静态资源映射（spring.mvc.static-path-pattern）。

**坑 6：路径参数匹配错误**

```text
@GetMapping("/users/{id}") 和 @GetMapping("/users/me") 冲突
```

具体路径放前面，通配路径放后面。
