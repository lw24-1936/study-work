---
title: JVM 基础
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, jvm, architecture, bytecode, class-file]
---

# JVM 基础

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [JDK / JRE / JVM 关系](#jdk--jre--jvm-关系)
- [JVM 整体架构](#jvm-整体架构)
- [Java 程序执行流程](#java-程序执行流程)
- [Class 文件结构概览](#class-文件结构概览)
- [字节码简介](#字节码简介)
- [HotSpot JVM 发展](#hotspot-jvm-发展)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JVM（Java Virtual Machine）是 Java 生态的基石——它让"一次编写，到处运行"成为可能。理解 JVM 的架构和工作原理，是诊断内存溢出、分析 GC 日志、调优性能的前提。

## JDK / JRE / JVM 关系

```
JDK (Java Development Kit)
 │  开发工具包：编译器、调试器、文档工具...
 │
 ├── JRE (Java Runtime Environment)
 │    │  运行环境：核心类库、运行时支持
 │    │
 │    └── JVM (Java Virtual Machine)
 │         虚拟机：字节码解释执行、内存管理、垃圾回收
 │
 └── 开发工具：javac、jar、javadoc、jdb...
```

| 组件 | 全称 | 包含 | 使用者 |
|------|------|------|--------|
| JDK | Java Development Kit | JRE + 编译器(javac) + 工具(jar/javadoc/jdb) | 开发者 |
| JRE | Java Runtime Environment | JVM + 核心类库(rt.jar/jmod) | 运行者 |
| JVM | Java Virtual Machine | 类加载器 + 运行时数据区 + 执行引擎 | 底层 |

JDK 11+ 不再单独发布 JRE——JDK 自带运行时（`jlink` 可裁剪定制 JRE）。

## JVM 整体架构

```
                    ┌──────────────────────────────┐
                    │        Class 文件              │
                    │  (HelloWorld.class)           │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │        类加载器子系统           │
                    │  Bootstrap / Platform / App   │
                    │  加载 → 验证 → 准备 → 解析 → 初始化 │
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐    ┌───────────────────────┐    ┌───────────────┐
│   方法区       │    │        堆 (Heap)       │    │    直接内存     │
│  (Metaspace)  │    │  ┌─────┬─────┬─────┐  │    │  (Direct Mem) │
│  类元数据      │    │  │Young│ Old │ ... │  │    │  NIO Buffer   │
│  常量池       │    │  └─────┴─────┴─────┘  │    │               │
│  静态变量      │    │   对象实例、数组        │    │               │
└───────────────┘    └───────────────────────┘    └───────────────┘
        │                                                    │
        │    ┌──────────────┐    ┌──────────────┐            │
        └────┤  Java 虚拟机栈 │    │  本地方法栈    │            │
             │  栈帧(Stack   │    │  (Native      │            │
             │   Frame)      │    │   Method      │            │
             │  · 局部变量表  │    │   Stack)      │            │
             │  · 操作数栈    │    │               │            │
             │  · 动态链接    │    │               │            │
             │  · 返回地址    │    │               │            │
             └──────────────┘    └──────────────┘            │
                                                             │
        ┌────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│                 执行引擎                          │
│  解释器 → JIT 编译器(C1/C2) → GC 垃圾回收器       │
│  即时编译：热点代码 → 编译为本地机器码              │
└─────────────────────────────────────────────────┘
```

核心分区：
- **线程共享**：堆、方法区（Metaspace）、直接内存
- **线程私有**：程序计数器、虚拟机栈、本地方法栈

## Java 程序执行流程

```
Hello.java
    │  javac 编译
    ▼
Hello.class (字节码)
    │  java 启动
    ▼
┌─────────────────────────────────┐
│  JVM 启动                        │
│  1. 类加载：加载 Hello.class      │
│  2. 链接：验证 → 准备 → 解析     │
│  3. 初始化：执行 static 代码块    │
│  4. 执行 main() 方法：            │
│     · 解释器逐条解释字节码        │
│     · JIT 编译器发现热点代码      │
│     · 热点代码编译为本地机器码     │
│     · GC 在后台自动回收内存       │
└─────────────────────────────────┘
```

```
解释执行 vs JIT 编译：

解释器模式：字节码 → 逐条翻译 → 执行
  ├── 启动快，执行慢
  └── 适用：启动后很快结束的程序、冷代码

JIT 编译模式：字节码 → 编译为机器码 → 直接执行
  ├── 启动慢（有编译开销），执行快
  └── 适用：长期运行的服务端程序、热点代码

HotSpot 默认：混合模式（解释器 + C1/C2 JIT）
  先解释执行 → 统计热点 → JIT 编译热点方法
```

## Class 文件结构概览

每个 `.class` 文件的结构严格遵循 JVM 规范：

```
ClassFile {
    u4             magic;               // 魔数: 0xCAFEBABE
    u2             minor_version;       // 次版本号
    u2             major_version;       // 主版本号（如 61 = JDK 17）
    u2             constant_pool_count; // 常量池大小
    cp_info        constant_pool[...];  // 常量池：字面量、符号引用
    u2             access_flags;        // 访问标志（public/abstract等）
    u2             this_class;          // 本类索引
    u2             super_class;         // 父类索引
    u2             interfaces_count;    // 接口数量
    u2             interfaces[...];     // 接口索引表
    u2             fields_count;        // 字段数量
    field_info     fields[...];         // 字段表
    u2             methods_count;       // 方法数量
    method_info    methods[...];        // 方法表（含字节码）
    u2             attributes_count;    // 属性数量
    attribute_info attributes[...];     // 属性表（SourceFile、LineNumberTable等）
}
```

用 `javap -verbose HelloWorld.class` 可以反编译查看完整结构。

## 字节码简介

Java 字节码是 JVM 的"汇编语言"——约 200 多个指令，每个指令 1 字节操作码 + 可选操作数：

```java
// Java 源码
public int add(int a, int b) {
    return a + b;
}

// 编译后字节码
// 0: iload_1       ← 将第 1 个参数 a 压入操作数栈
// 1: iload_2       ← 将第 2 个参数 b 压入操作数栈  
// 2: iadd          ← 弹出两个 int 相加，结果压回栈顶
// 3: ireturn       ← 返回栈顶 int 值
```

操作码分类：

| 类别 | 示例 | 用途 |
|------|------|------|
| 加载/存储 | `iload`, `istore`, `aload`, `astore` | 局部变量 ↔ 操作数栈 |
| 算术 | `iadd`, `isub`, `imul`, `idiv` | 基本运算 |
| 类型转换 | `i2l`, `d2i`, `checkcast` | 类型转换 |
| 对象操作 | `new`, `getfield`, `putfield`, `invokevirtual` | 对象创建/访问 |
| 控制转移 | `ifeq`, `goto`, `tableswitch` | 分支/循环/跳转 |
| 方法调用 | `invokevirtual`, `invokestatic`, `invokedynamic` | 方法调用 |
| 异常 | `athrow` | 抛出异常 |
| 同步 | `monitorenter`, `monitorexit` | synchronized 实现 |

## HotSpot JVM 发展

HotSpot 是 Oracle JDK 使用的 JVM 实现（最初由 Sun 开发）：

| 版本 | 关键变化 |
|------|----------|
| JDK 1.3 | HotSpot 成为默认 JVM |
| JDK 1.6 | 引入分层编译、并行 GC |
| JDK 1.7 | G1 GC 引入（实验性） |
| JDK 1.8 | Metaspace 取代 PermGen |
| JDK 9 | G1 成为默认 GC；模块化 |
| JDK 11 | ZGC 引入；Epsilon GC；AppCDS |
| JDK 17 | ZGC 分代；密封类；Pattern Matching |
| JDK 21 | 虚拟线程正式版；分代 ZGC 正式版 |

## 应用场景实战

### 场景一：查看 Class 文件信息

```bash
# 查看魔数和版本号
xxd HelloWorld.class | head -1

# 反编译查看字节码
javap -c HelloWorld.class

# 查看详细信息（常量池、方法表等）
javap -verbose HelloWorld.class

# 查看有哪些方法
javap -p HelloWorld.class
```

### 场景二：确认 JDK 版本兼容性

```java
// Class 文件主版本号对照
// 52 = JDK 8
// 55 = JDK 11
// 61 = JDK 17
// 65 = JDK 21

// 检查 .class 文件的目标版本
// javap -verbose MyClass.class | grep "major"
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `UnsupportedClassVersionError` | 用高版本 JDK 编译，低版本 JVM 运行 | 指定 `-source`/`-target` 或升级 JVM |
| NoClassDefFoundError | 运行时找不到类 | 检查 classpath |
| ClassNotFoundException | 用 `Class.forName` 找不到 | 检查类名和 classpath |
| `javac` 和 `java` 版本不一致 | 多个 JDK 混装 | 检查 `JAVA_HOME` 和 PATH |

## 总结

- JVM = 类加载器 + 运行时数据区 + 执行引擎
- JDK ⊃ JRE ⊃ JVM，JDK 11+ 不再单独发布 JRE
- Class 文件以 0xCAFEBABE 开头，有严格的结构规范
- 字节码是 JVM 的指令集（~200+ 条），javap 可反编译查看
- HotSpot 使用解释器 + JIT 混合模式（C1 客户端编译器 + C2 服务端编译器）
- PermGen 在 JDK 8 被 Metaspace 取代（使用本地内存，不再固定大小）
