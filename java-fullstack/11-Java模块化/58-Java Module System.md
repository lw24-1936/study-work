---
title: Java Module System
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, module, jpms, module-info, jigsaw]
---

# Java Module System

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [为什么需要模块化](#为什么需要模块化)
- [module-info.java](#module-infojava)
- [核心指令详解](#核心指令详解)
- [模块路径 vs 类路径](#模块路径-vs-类路径)
- [ServiceLoader 与服务发现](#serviceloader-与服务发现)
- [JDK 内置模块概览](#jdk-内置模块概览)
- [迁移到模块化](#迁移到模块化)
- [反射与 opens](#反射与-opens)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Java 模块系统（JPMS，又称 Project Jigsaw）是 JDK 9 引入的语言级模块化机制——在包（package）之上增加了一层封装：**模块（module）**。它让 Java 终于能明确声明"我依赖什么"和"我暴露什么"。

```
JDK 8 及之前：                 JDK 9+：
┌─────────────────┐           ┌─────────────────────┐
│     rt.jar      │           │  java.base           │
│  (所有核心类)    │           │  java.sql            │
│  60+ MB         │           │  java.xml            │
│                 │           │  java.desktop        │
│                 │           │  ... (26 个模块)      │
│  不可拆分        │           │  每个模块独立封装      │
└─────────────────┘           └─────────────────────┘
```

模块化带来的三个核心收益：
- **强封装**：模块内的包默认不对外暴露（`public` 不再等于"谁都能用"）
- **显式依赖**：`requires` 声明依赖，启动时检查，缺依赖直接报错
- **可定制运行时**：`jlink` 只打包需要的模块，裁剪出最小 JRE

## 为什么需要模块化

JDK 8 之前的问题：

```java
// 1. public 默认全局可见——内部 API 无法隐藏
// sun.misc.Unsafe 明明标着 @Deprecated，但谁都能用
import sun.misc.Unsafe;  // JDK 8: 警告；JDK 9+：编译错误！

// 2. classpath 下的 jar 无可见性控制
// 所有 public 类都会暴露——无法声明"这个包只给内部用"

// 3. 传递依赖——A 依赖 B，B 依赖 C，A 也能直接访问 C
// 破坏了封装原则

// 4. 启动时无法发现缺少依赖——运行时 ClassNotFoundException
// 模块化：启动时检查模块图 → 缺少模块直接报错
```

## module-info.java

每个模块的根目录下有一个 `module-info.java` 文件——模块的"身份证"：

```java
// module-info.java
module com.example.mymodule {    // 模块名
    // 指令...
}
```

### 模块命名约定

```
模块名 = 反向域名（和包名类似，但用点分隔）
com.example.myapp
com.example.mylib

JDK 内置模块：
java.base
java.sql
java.desktop
jdk.unsupported
```

## 核心指令详解

### requires —— 声明依赖

```java
module com.example.app {
    requires java.sql;           // 依赖 java.sql 模块
    requires com.example.lib;    // 依赖自定义模块

    // 传递依赖 —— 依赖我的模块也自动依赖此模块
    requires transitive com.example.api;
    // 如果我 requires transitive java.sql
    // 那么依赖我的模块也会隐式依赖 java.sql
    // 类似于 Maven 的 compile scope

    // 静态依赖 —— 编译时需要，运行时可选
    requires static lombok;
    // 类似于 Maven 的 optional
}
```

### exports —— 暴露包

```java
module com.example.lib {
    // 暴露指定包给所有模块
    exports com.example.lib.api;

    // 暴露指定包给指定模块（定向导出）
    exports com.example.lib.internal to com.example.app;
    // 只有 com.example.app 能访问 internal 包
    // 其他模块用不了！

    // 不导出 = 完全私有（即使类声明为 public）
    // com.example.lib.internal 未导出 → 外部不可见
}
```

### opens —— 开放反射

```java
module com.example.app {
    // 开放包给反射访问（不导出编译期类型，但允许运行时反射）
    opens com.example.app.model;

    // 开放给指定模块
    opens com.example.app.model to com.example.framework;
    // 只有 framework 模块能反射访问 model 包
}
```

### uses / provides —— 服务加载

```java
// 服务接口模块
module com.example.api {
    exports com.example.api;
}

// 服务提供模块
module com.example.provider {
    requires com.example.api;
    provides com.example.api.Plugin           // 接口
        with com.example.provider.PluginImpl;  // 实现类
}

// 服务消费模块
module com.example.app {
    requires com.example.api;
    uses com.example.api.Plugin;  // 声明"我使用这个服务"
}
```

### 指令速查

| 指令 | 作用 | 类比 |
|------|------|------|
| `requires M` | 依赖模块 M | Maven `<dependency>` |
| `requires transitive M` | 传递依赖 M | Maven compile scope |
| `requires static M` | 编译时需要，运行时可选 | Maven optional |
| `exports P` | 暴露包 P 给所有模块 | `public` 包级 |
| `exports P to M` | 只暴露给模块 M | 定向导出 |
| `opens P` | 开放反射访问 | 允许 `setAccessible` |
| `opens P to M` | 开放反射给模块 M | 定向反射 |
| `uses S` | 声明消费服务 S | ServiceLoader 消费者 |
| `provides S with Impl` | 提供服务 S 的实现 | ServiceLoader 提供者 |

## 模块路径 vs 类路径

JDK 9+ 引入**模块路径**（module path），与传统的类路径并行：

```bash
# 类路径（JDK 8-，JDK 9+ 仍然支持）
java -cp lib/mylib.jar:app.jar com.example.Main

# 模块路径（JDK 9+）
java --module-path lib:app --module com.example.app/com.example.Main
# 或简写：
java -p lib:app -m com.example.app/com.example.Main

# 两者可以混用：
java --module-path modlib -cp legacy.jar com.example.Main
```

| 维度 | 类路径 (classpath) | 模块路径 (module path) |
|------|-------------------|----------------------|
| 解析方式 | 扁平，所有 jar 同层级 | 有向图，模块有依赖关系 |
| 可见性 | 所有 public 类全局可见 | exports 控制可见 |
| 冲突检测 | 无 | 模块名唯一、包名不能分裂在两个模块 |
| 缺依赖 | 运行时 ClassNotFoundException | 启动时解析失败 |
| 封装 | 无 | 强封装（反射需 opens） |

## ServiceLoader 与服务发现

模块化增强了 JDK 1.6 就存在的 `ServiceLoader`——它是 SPI（Service Provider Interface）机制的核心：

```java
// 1. 定义服务接口
// src/com.example.api/module-info.java
module com.example.api {
    exports com.example.api;
}

package com.example.api;
public interface MessageService {
    void send(String msg);
}

// 2. 提供实现
// src/com.example.provider/module-info.java
module com.example.provider {
    requires com.example.api;
    provides com.example.api.MessageService
        with com.example.provider.EmailService,
             com.example.provider.SmsService;
}

// META-INF/services/com.example.api.MessageService 文件中写入：
// com.example.provider.EmailService
// com.example.provider.SmsService

// 3. 加载使用
// src/com.example.app/module-info.java
module com.example.app {
    requires com.example.api;
    uses com.example.api.MessageService;
}

// 应用代码
ServiceLoader<MessageService> loader = ServiceLoader.load(MessageService.class);
for (MessageService service : loader) {
    service.send("Hello");
}
```

ServiceLoader 的典型应用：
- JDBC 驱动加载（`java.sql.Driver`）
- 日志框架绑定（`SLF4J` → `Logback`）
- Spring Boot 自动配置（`spring.factories` 机制）
- 插件系统

## JDK 内置模块概览

JDK 本身被拆分为约 26 个模块，可以通过 `java --list-modules` 查看：

```bash
java --list-modules

# 核心模块：
java.base           # 基础（java.lang, java.util, java.io 等）—— 隐式依赖，不需要显式 requires
java.sql            # JDBC
java.xml            # XML 解析
java.desktop        # AWT/Swing
java.logging        # java.util.logging
java.management     # JMX
java.naming         # JNDI
java.net.http       # JDK 11+ HttpClient
jdk.unsupported     # sun.misc.Unsafe 等内部 API（需要显式 requires）
```

## 迁移到模块化

已有项目不需要一步到位——JDK 9+ 完全兼容传统的 classpath 运行方式：

### 阶段一：在 classpath 上运行（无改动）

```bash
# JDK 8 的启动方式在 JDK 9+ 完全可用
java -cp app.jar com.example.Main
```

### 阶段二：自动模块

```bash
# 如果 jar 包没有 module-info.java，但放在 module path 上
# JDK 会从 MANIFEST.MF 的 Automatic-Module-Name 读取模块名
# 或者从文件名推断（慎用，不稳定）

# 在 MANIFEST.MF 中声明：
# Automatic-Module-Name: com.example.mylib
```

### 阶段三：添加 module-info.java

```bash
# 在 src/main/java 目录下创建 module-info.java
# 从简单的 exports 开始，逐步增加 requires/opens/provides
```

### 检查工具

```bash
# jdeps —— 分析依赖关系
jdeps --module-path lib app.jar        # 查看依赖哪些模块
jdeps --generate-module-info . app.jar # 生成 module-info.java 草稿
```

## 反射与 opens

模块化对反射做了限制——这直接影响 Spring、Hibernate 等大量使用反射的框架：

```java
// JDK 8：反射可以访问所有包（不管是不是内部的）
// JDK 9+：反射只能访问 exports 的包

// 框架需要访问内部 API 时：
// 方案一：opens（推荐）
module myapp {
    opens com.example.entity to org.hibernate.core;
    // 允许 Hibernate 反射访问 entity 包
}

// 方案二：命令行参数（临时方案）
java --add-opens java.base/java.lang=ALL-UNNAMED -jar app.jar
// 开放 java.lang 包给未命名模块（classpath 上的代码）

// Spring 等框架在 JDK 17+ 需要的常见 add-opens：
--add-opens java.base/java.lang=ALL-UNNAMED
--add-opens java.base/java.lang.reflect=ALL-UNNAMED
--add-opens java.base/java.util=ALL-UNNAMED
```

## 应用场景实战

### 场景一：多模块项目结构

```
myapp/
├── api/
│   └── src/
│       └── main/java/
│           ├── module-info.java          # module com.example.api
│           └── com/example/api/
│               └── UserService.java      # 接口定义
├── core/
│   └── src/
│       └── main/java/
│           ├── module-info.java          # module com.example.core
│           └── com/example/core/
│               └── UserServiceImpl.java  # 接口实现
└── web/
    └── src/
        └── main/java/
            ├── module-info.java          # module com.example.web
            └── com/example/web/
                └── UserController.java   # 使用 core 模块
```

```java
// api/module-info.java
module com.example.api {
    exports com.example.api;
}

// core/module-info.java
module com.example.core {
    requires com.example.api;
    provides com.example.api.UserService
        with com.example.core.UserServiceImpl;
}

// web/module-info.java
module com.example.web {
    requires com.example.api;
    uses com.example.api.UserService;
}
```

### 场景二：jlink 裁剪定制 JRE

```bash
# 只打包必需模块的最小运行时
jlink --module-path $JAVA_HOME/jmods:myapp/modules \
      --add-modules com.example.app \
      --output custom-runtime \
      --strip-debug \
      --compress=2

# custom-runtime/bin/java -m com.example.app/com.example.Main
# 生成的 JRE 只包含应用所需的模块，大小可能只有 30-50MB
# 适合 Docker 镜像等场景
```

### 场景三：插件系统（ServiceLoader 模式）

```java
// 主程序通过 ServiceLoader 发现并加载插件
// 新增插件只需添加 jar 到 module path，不需要改主程序代码

module app {
    uses com.example.Plugin;
}

// 插件 jar 1
module plugin1 {
    requires app;
    provides com.example.Plugin with com.example.plugin1.Impl1;
}

// 插件 jar 2
module plugin2 {
    requires app;
    provides com.example.Plugin with com.example.plugin2.Impl2;
}
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `module not found` | 模块不在 module path 上 | 检查 `--module-path` 路径 |
| `package X is not visible` | 包未 exports | 在 module-info.java 中 `exports` 该包 |
| `Unable to make field accessible` | 反射访问未 opens 的包 | 添加 `opens` 或 `--add-opens` |
| `package X exists in multiple modules` | 同一个包被两个模块同时包含 | 拆分包，每个包只能属于一个模块 |
| `Cyclic dependence` | 两个模块互相 requires | 打破循环（提取公共接口到第三个模块） |

### 迁移建议

```
1. JDK 9+ 不强制使用模块化——classpath 完全兼容
2. 库项目先加 Automatic-Module-Name（最低成本）
3. 新项目可以考虑模块化（编译期依赖检查有实际价值）
4. Spring Boot 应用暂时不需要模块化——框架已处理好
5. 内部基础设施/共享库优先模块化——封装收益最明显
6. 用 jdeps 分析依赖来决定哪些包该 exports
```

### 模块化是否适合你？

```
需要使用模块化的信号：
  ✓ 开发一个公共库/框架，需要隐藏内部实现
  ✓ 大型单体需要拆分为明确的子系统
  ✓ 需要在 Docker 镜像中裁剪 JRE 减小体积
  ✓ 插件系统——运行时加载/卸载

暂时不需要模块化的信号：
  ✓ 普通的 Spring Boot Web 应用
  ✓ 团队不熟悉模块化，引入成本高
  ✓ 大量依赖的 jar 还没有 module-info
```

## 总结

- Java 模块化 = `module-info.java` 声明模块的依赖(`requires`)、导出(`exports`)、反射开放(`opens`)、服务(`uses/provides`)
- `exports X to Y` 实现定向导出——只有指定模块能访问
- 模块路径有向图 vs 类路径扁平化——启动时即可发现缺失依赖
- `--add-opens` / `--add-exports` 是框架访问内部 API 的临时方案
- ServiceLoader 是 SPI 的核心——JDBC、SLF4J、Spring 自动配置都基于此
- jlink 从完整 JDK 裁剪出最小运行时，适合 Docker 镜像
- 模块化不是必选项——JDK 9+ 完全向后兼容，现有项目可以零改动运行
