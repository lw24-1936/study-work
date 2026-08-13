---
title: Java 包与访问控制
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, package, access-control, import]
---

# Java 包与访问控制

整理日期：2026-08-12

## 目录

- [package](#package)
- [import](#import)
- [static import](#static-import)
- [包结构与命名规范](#包结构与命名规范)
- [访问修饰符总结](#访问修饰符总结)
- [模块访问（Java 9+）](#模块访问java-9)

## package

包是 Java 的组织单元——把相关的类划为一组，避免命名冲突。

```java
package com.example.service;   // 包声明，必须在文件第一行（注释除外）

public class UserService {
    // ...
}
```

没有包声明的类属于"默认包"（unnamed package）。默认包中的类无法被其他包导入——实际项目中不要用默认包。

编译后，`.class` 文件按包结构生成目录：

```
src/com/example/service/UserService.java
  → target/com/example/service/UserService.class
```

运行带包名的类：

```bash
java com.example.service.Main    # 从 classpath 根目录找
```

## import

引入其他包中的类，避免写全限定名：

```java
// 不 import 的写法
java.util.List<String> list = new java.util.ArrayList<>();

// import 后的写法
import java.util.List;
import java.util.ArrayList;

List<String> list = new ArrayList<>();
```

导入规则：

```java
import java.util.List;             // 单个类导入
import java.util.*;                // 通配符导入：引入 java.util 包下的所有类
import static java.lang.Math.PI;   // 静态导入
```

通配符导入 `.*` 只导入当前包的直接类，不导入子包的类。`import java.*` 不会导入 `java.util` 下的类。

IDE 的"自动优化导入"功能通常会把 `.*` 展开为具体的类名——Google Java Style Guide 明确禁用通配符导入。

### 自动导入的包

`java.lang` 包中的类（String、System、Math、Object 等）不需要显式 import，编译器自动处理。

### 命名冲突

不同包中有同名类时，至少一个必须用全限定名：

```java
import java.util.Date;

// 同时用 sql.Date 和 util.Date
public void method() {
    Date utilDate = new Date();              // java.util.Date
    java.sql.Date sqlDate = new java.sql.Date(123456789L);
}
```

## static import

导入静态方法和静态常量，直接使用而不用写类名：

```java
import static java.lang.Math.PI;
import static java.lang.Math.sqrt;
import static java.lang.Math.*;

double area = PI * radius * radius;
double root = sqrt(16);
```

static import 用得少——过度使用会降低可读性（`min(a, b)` 到底是 Math.min 还是自定义的方法？）。仅对常量（如 JUnit 的 `assertTrue`、Mockito 的 `verify`）和频繁使用的工具方法（`Collections.emptyList()`）使用。

## 包结构与命名规范

### 命名规范

- 全小写，点分隔
- 通常用倒置域名：`com.公司名.项目名.模块`
- 不要用 `java` 或 `javax` 开头——被 JDK 保留

```
com.example.ecommerce        // 公司电商项目
com.example.ecommerce.model   // 数据模型
com.example.ecommerce.service  // 业务逻辑
com.example.ecommerce.controller // 控制器
```

### 包结构分层 vs 按功能

**按层分包（传统 Spring 项目）：**

```
com.example.project
├── controller
├── service
│   └── impl
├── mapper（或 dao）
├── model（或 entity / domain）
├── config
└── util
```

**按功能分包（领域驱动）：**

```
com.example.project
├── user
│   ├── UserController
│   ├── UserService
│   └── UserRepository
├── order
│   ├── OrderController
│   ├── OrderService
│   └── OrderRepository
└── product
```

小项目按层分够用，大项目按功能分更好维护。没有绝对的标准，项目内部统一即可。

## 访问修饰符总结

四种访问级别，从窄到宽：

| 修饰符 | 同类 | 同包 | 子类 | 任意 |
|--------|------|------|------|------|
| `private` | 可见 | | | |
| 默认 | 可见 | 可见 | | |
| `protected` | 可见 | 可见 | 可见 | |
| `public` | 可见 | 可见 | 可见 | 可见 |

访问控制的原则——**最小权限**：类、方法、属性默认用最窄的访问级别能工作就行，需要放开时再放。具体来说：

```java
// 类：通常 public 或包级（默认）
public class UserService { ... }         // 对外暴露的 API
class UserValidator { ... }              // 包内使用的工具类

// 属性：永远 private
public class User {
    private String name;                 // 属性私有
    public String getName() { ... }      // 通过方法暴露
}

// 方法：根据实际需要
public void register() { ... }           // 对外 API
protected void validate() { ... }         // 子类可能需要
private void encryptPassword() { ... }   // 纯内部逻辑
```

## 模块访问（Java 9+）

Java 9 引入了模块系统（Project Jigsaw），在包之上加了一层访问控制。

模块用 `module-info.java` 定义：

```java
// module-info.java
module com.example.myapp {
    requires java.sql;                      // 依赖的模块
    exports com.example.myapp.api;          // 对外暴露的包
    exports com.example.myapp.dto to       // 只对指定模块暴露
        com.example.client;
}
```

模块访问和经典访问修饰符的关系：一个包即使类声明为 `public`，如果模块没有 `exports` 这个包，外部模块依然访问不到。

目前模块系统在 JDK 自身和库中使用较广，但大多数业务代码仍然不用 `module-info.java`（classpath 模式）。了解它能看懂 JDK 源码中的模块依赖，以及理解为什么某些 `sun.misc.Unsafe` 之类的内部类越来越难访问就行。
