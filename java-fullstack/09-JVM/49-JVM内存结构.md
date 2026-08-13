---
title: JVM 内存结构
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, jvm, memory, heap, stack, metaspace]
---

# JVM 内存结构

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [程序计数器](#程序计数器)
- [Java 虚拟机栈](#java-虚拟机栈)
- [本地方法栈](#本地方法栈)
- [堆（Heap）](#堆heap)
- [方法区 / Metaspace](#方法区--metaspace)
- [常量池](#常量池)
- [直接内存](#直接内存)
- [各区域对比总表](#各区域对比总表)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JVM 运行时数据区分为 5 大区域+1 个扩展区：

```
线程私有（每线程一份）         线程共享（进程唯一）
─────────────────────       ─────────────────────
1. 程序计数器                 4. 堆 (Heap)
2. Java 虚拟机栈             5. 方法区 (Metaspace)
3. 本地方法栈                 
                           扩展区：直接内存 (Direct Memory)
```

每个区域存储不同类型的数据、有不同的生命周期和内存溢出异常类型。

## 程序计数器

**程序计数器**（Program Counter Register）是当前线程执行的字节码行号指示器：

- 每个线程独立拥有
- 记录当前正在执行的字节码指令地址（Native 方法时为 undefined）
- 唯一一个 **不会 OOM** 的区域（不需要动态扩展）

```
线程 A: PC=42  (正在执行第 42 条字节码)
线程 B: PC=128 (正在执行第 128 条字节码)
线程 C: PC=0   (刚启动)
```

## Java 虚拟机栈

每个线程有一个**虚拟机栈**，每个方法调用创建一个**栈帧**：

```
┌──────────────────────────────┐
│         虚拟机栈              │
│ ┌──────────────────────────┐ │
│ │  栈帧 (method3 当前方法)   │ │ ← 栈顶
│ │  · 局部变量表              │ │
│ │  · 操作数栈                │ │
│ │  · 动态链接                │ │
│ │  · 返回地址                │ │
│ ├──────────────────────────┤ │
│ │  栈帧 (method2)           │ │
│ ├──────────────────────────┤ │
│ │  栈帧 (method1)           │ │
│ ├──────────────────────────┤ │
│ │  栈帧 (main)              │ │ ← 栈底
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

### 局部变量表

存储方法参数和局部变量（基本类型存值，引用类型存指针）：

```java
public void method(int a, String b) {  // a=0号槽, b=1号槽
    double c = 3.14;                   // c=2-3号槽 (double占2个槽)
    int d = 42;                        // d=4号槽
}
```

### 操作数栈

字节码指令执行时的"工作台"——用于计算：

```java
// int a = 1 + 2;
iconst_1        // 操作数栈: [1]
iconst_2        // 操作数栈: [1, 2]
iadd            // 操作数栈: [3]  ← 弹出两个，加完压回
istore_0        // 操作数栈: []   ← 弹出存入局部变量表
```

### 栈异常

| 异常 | 原因 | 典型触发 |
|------|------|----------|
| StackOverflowError | 栈深度超出限制（默认 1MB） | 无限递归 |
| OutOfMemoryError | 无法分配更多栈内存 | 创建过多线程 |

```java
// StackOverflowError 示例
public static void recursive() {
    recursive();  // 每次调用入栈一个新栈帧 → 直到栈满
}
// 栈深度默认 1024（不同 JVM 实现不同），递归超过此深度即溢出
```

## 本地方法栈

与虚拟机栈类似，但服务于 **Native 方法**（JNI 调用）——用 C/C++ 实现的底层操作。HotSpot 将本地方法栈和虚拟机栈合二为一。

## 堆（Heap）

堆是 JVM 管理的**最大一块内存**，所有对象实例和数组在此分配。堆是 GC 的主要工作区域：

### 分代结构

```
┌────────────────────────────────────┐
│             堆 (Heap)               │
│ ┌────────────────────────────────┐ │
│ │         新生代 (Young)          │ │
│ │ ┌──────┬──────┬──────────────┐ │ │
│ │ │ Eden │ S0   │ S1           │ │ │
│ │ │ 8/10 │ 1/10 │ 1/10         │ │ │
│ │ └──────┴──────┴──────────────┘ │ │
│ └────────────────────────────────┘ │
│ ┌────────────────────────────────┐ │
│ │        老年代 (Old/Tenured)     │ │
│ │   长期存活的大对象               │ │
│ └────────────────────────────────┘ │
│                                    │
│  默认比例：Young : Old = 1 : 2     │
│  Eden : S0 : S1 = 8 : 1 : 1       │
└────────────────────────────────────┘
```

| 区域 | 存放内容 | GC 类型 |
|------|----------|---------|
| Eden | 新创建的对象 | Minor GC 频繁清理 |
| Survivor (S0/S1) | 经历 GC 仍存活的对象 | Minor GC 时在两区之间复制 |
| Old/Tenured | 长期存活或大对象 | Major GC/Full GC |

### 对象分配流程

```
new 对象
  │
  ├── 尝试栈上分配（逃逸分析，JIT 优化） → 栈上，方法结束自动释放
  │
  ├── 尝试 TLAB (Thread Local Allocation Buffer)
  │    每个线程在 Eden 区有一小块私用缓冲区，避免竞争
  │
  ├── Eden 区分配
  │     │
  │     ├── Eden 够 → 分配成功
  │     │
  │     └── Eden 不够 → Minor GC
  │           │
  │           ├── 回收后 Eden 够 → 分配
  │           │
  │           └── 对象太大(超过 -XX:PretenureSizeThreshold)
  │               │
  │               └── 直接分配在老年代
  │
  └── 老年代也满了 → Full GC
        │
        └── Full GC 后还不够 → OutOfMemoryError
```

### 堆参数

```bash
-Xms2g          # 初始堆大小
-Xmx4g          # 最大堆大小
-Xmn1g          # 新生代大小
-XX:NewRatio=2  # 老年代/新生代比例（默认 2）
-XX:SurvivorRatio=8  # Eden/Survivor 比例（默认 8）
```

## 方法区 / Metaspace

JDK 7 及之前叫 **PermGen**（永久代），JDK 8 起改为 **Metaspace**（元空间）。核心变化：

| 维度 | PermGen (JDK 7-) | Metaspace (JDK 8+) |
|------|-------------------|---------------------|
| 存储位置 | JVM 堆内 | 本地内存（堆外） |
| 大小限制 | 固定（默认 82MB，`-XX:MaxPermSize`） | 默认无上限（受本地内存限制） |
| OOM 风险 | 容易（类太多就爆） | 低（可设置上限 `-XX:MaxMetaspaceSize`） |
| GC | Full GC 回收 | GC 时可回收（类卸载） |

Metaspace 存储内容：
- 类的元数据（类名、方法信息、字段描述）
- 运行时常量池
- 静态变量（JDK 7+ 移到堆中）
- JIT 编译后的代码缓存（CodeCache）

```bash
-XX:MetaspaceSize=256m      # Metaspace 初始大小
-XX:MaxMetaspaceSize=512m   # Metaspace 最大限制（建议设置！）
```

## 常量池

Java 有两种常量池：

### Class 文件常量池（静态常量池）

.class 文件中的常量池——存储编译期确定的字面量和符号引用：

```java
String s = "hello";   // "hello" 在 Class 常量池中
int MAX = 100;         // 100 在 Class 常量池中
```

### 运行时常量池（Runtime Constant Pool）

Class 文件常量池被加载到 Metaspace 后的运行时表示——所有类共享，且支持动态添加（`String.intern()`）：

```java
// String.intern() —— 把字符串放入运行时常量池
String s1 = new String("hello");    // 堆中的新对象
String s2 = s1.intern();           // 常量池中的引用
String s3 = "hello";               // 常量池中的引用
System.out.println(s1 == s2);      // false（堆 vs 常量池）
System.out.println(s2 == s3);      // true（都是常量池引用）
```

### JDK 7 的 String Pool 迁移

JDK 7 将 String 常量池从 PermGen 移到了堆——GC 可以正常回收字符串常量，解决了 PermGen OOM 问题。

## 直接内存

不属于 JVM 堆，是 OS 的本地内存——NIO 通过 `ByteBuffer.allocateDirect()` 使用：

```java
// 分配 100MB 直接内存
ByteBuffer direct = ByteBuffer.allocateDirect(100 * 1024 * 1024);
```

直接内存的优点：**零拷贝**——数据从磁盘/网络到本地内存再到 JVM 堆时省去了一次拷贝。代价：不受 JVM GC 管理，需要手动释放或等待 Cleaner 回收。

```bash
-XX:MaxDirectMemorySize=1g  # 限制直接内存大小（默认等于 -Xmx）
```

## 各区域对比总表

| 区域 | 线程 | 存储内容 | 异常类型 | 关键参数 |
|------|------|----------|----------|----------|
| 程序计数器 | 私有 | 字节码行号 | 无 | - |
| 虚拟机栈 | 私有 | 栈帧（局部变量表、操作数栈） | StackOverflowError | `-Xss` |
| 本地方法栈 | 私有 | Native 方法栈帧 | StackOverflowError | - |
| 堆 | 共享 | 对象实例、数组 | OutOfMemoryError | `-Xms`/`-Xmx` |
| Metaspace | 共享 | 类元数据、常量池 | OutOfMemoryError | `-XX:MaxMetaspaceSize` |
| 直接内存 | 共享 | NIO Buffer | OutOfMemoryError | `-XX:MaxDirectMemorySize` |

## 应用场景实战

### 场景一：估算对象内存占用

```java
// 一个 Integer 对象的内存占用（64 位 JVM，压缩指针开启）：
// 对象头(Mark Word + Klass Pointer): 8 + 4 = 12 字节
// int 值: 4 字节
// 对齐填充: 4 → 共 24 字节
// 对比 int: 4 字节 —— 包装类是基本类型的 6 倍！

// 估算一个 HashMap 的内存
// 100 万条 String → String 条目
// 每个 Node: 32 字节 + key + value
// 总计可能达到上百 MB
```

### 场景二：栈溢出排查

```bash
# 查看线程堆栈
jstack <pid> > thread.dump

# 统计线程栈使用
# 每个线程默认栈大小 1MB，1000 个线程 ≈ 1GB 栈内存

# 减少栈大小（风险：深度递归会溢出）
-Xss256k
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| StackOverflowError | 无限递归/栈太小 | 检查递归终止条件；调大 `-Xss` |
| OOM: Java heap space | 堆内存不足/内存泄漏 | 扩大 `-Xmx`；分析 Heap Dump |
| OOM: Metaspace | 类加载过多（动态代理、Groovy） | 设置 `-XX:MaxMetaspaceSize`；排查类加载器泄漏 |
| OOM: Direct buffer memory | 直接内存用尽 | 增大 `-XX:MaxDirectMemorySize`；及时释放 Buffer |
| OOM: unable to create native thread | OS 线程数上限 | 减少线程数；调小 `-Xss` 释放虚拟地址空间 |

### 关键参数速查

```bash
-Xms2g -Xmx4g                             # 堆
-Xss256k                                  # 栈
-XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=256m  # 元空间
-XX:MaxDirectMemorySize=512m              # 直接内存
-XX:+HeapDumpOnOutOfMemoryError           # OOM 时自动 Dump
-XX:HeapDumpPath=/tmp/heapdump.hprof      # Dump 文件路径
```

## 总结

- 5+1 区：程序计数器、虚拟机栈、本地方法栈（线程私有）+ 堆、Metaspace（线程共享）+ 直接内存
- 堆是 GC 主战场：Eden → Survivor(S0↔S1) → Old，对象在此分代流转
- JDK 8 Metaspace 取代 PermGen——类元数据放入本地内存，默认无上限
- 栈存方法调用（栈帧），堆存对象实例，Metaspace 存类信息
- 所有 OOM 都可通过对应参数调大或 Dump 分析定位
