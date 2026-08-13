---
title: Java 性能优化
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [性能优化, 性能指标, 性能分析, 代码优化, 集合优化, 字符串优化, io优化]
---

# Java 性能优化

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [性能分析方法](#性能分析方法)
- [字符串优化](#字符串优化)
- [集合优化](#集合优化)
- [IO 优化](#io-优化)
- [代码优化](#代码优化)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Java 性能优化是在代码层面提升程序执行效率，避免常见性能陷阱。

```text
性能优化的原则：
1. 先测量再优化 —— 不要盲目优化
2. 优化热点 —— 只优化真正的瓶颈
3. 过早优化是万恶之源 —— 先保证正确性
```

```text
性能优化的层次（从低到高）：
代码优化 → JVM 优化 → 数据库优化 → 架构优化
```

## 性能分析方法

### 定位瓶颈

```text
1. 性能监控 —— 监控指标（CPU、内存、响应时间）
2. 日志分析 —— 慢请求日志
3. 性能剖析 —— Profiler（JProfiler、Arthas）
4. 基准测试 —— JMH（详见 129）
```

### Arthas 分析

```bash
# Arthas 是阿里开源的 Java 诊断工具
# 查看最耗时的线程
thread -n 3

# 查看方法耗时（trace）
trace com.example.OrderService createOrder

# 查看热点方法（dashboard）
dashboard
```

## 字符串优化

### StringBuilder 代替 String 拼接

```java
// 慢：每次 + 创建新 String 对象
String result = "";
for (int i = 0; i < 10000; i++) {
    result += i;   // O(n²)，每次创建新对象
}

// 快：StringBuilder 原地追加
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 10000; i++) {
    sb.append(i);   // O(n)
}
String result = sb.toString();
```

### 字符串常量池

```java
// 用字面量（常量池复用）
String s1 = "hello";
String s2 = "hello";
s1 == s2   // true（同一个对象）

// 用 new（每次创建新对象）
String s3 = new String("hello");   // 不推荐
```

### 字符串优化要点

```text
1. 循环拼接用 StringBuilder
2. 常量用字面量（常量池）
3. 频繁比较用 intern()（慎用）
```

## 集合优化

### ArrayList vs LinkedList

```text
ArrayList —— 数组，随机访问快（O(1)），增删慢（O(n)）
LinkedList —— 链表，增删快（O(1)），随机访问慢（O(n)）
```

```java
// 随机访问用 ArrayList（99% 场景）
List<User> list = new ArrayList<>();

// 频繁头插/删除用 LinkedList（少见）
List<User> list = new LinkedList<>();
```

### HashMap 优化

```java
// 指定初始容量（避免频繁扩容）
Map<String, User> map = new HashMap<>(expectedSize * 4 / 3 + 1);
// 扩容是性能杀手（rehash），预分配容量

// 用 int key 考虑 Int2ObjectMap（避免装箱）
```

### 集合优化要点

```text
1. 集合预分配容量 —— 避免扩容
2. 随机访问用 ArrayList
3. 遍历用 for-each 或 stream
4. 避免不必要的装箱拆箱
```

## IO 优化

### 缓冲 IO

```java
// 慢：逐字节读（每次系统调用）
try (FileInputStream fis = new FileInputStream("file")) {
    int b;
    while ((b = fis.read()) != -1) { ... }   // 逐字节，极慢
}

// 快：缓冲读（批量）
try (BufferedReader reader = new BufferedReader(new FileReader("file"))) {
    String line;
    while ((line = reader.readLine()) != null) { ... }
}
```

### NIO vs BIO

```text
BIO —— 阻塞 IO（一连接一线程）
NIO —— 非阻塞 IO（多路复用，高并发）
```

```text
高并发网络场景用 NIO（Netty），
普通文件读写用缓冲 IO 即可
```

### IO 优化要点

```text
1. 用缓冲流（BufferedReader/BufferedWriter）
2. 大文件用 NIO（FileChannel）
3. 高并发网络用 Netty（NIO）
```

## 代码优化

### 避免重复计算

```java
// 慢：循环里重复计算
for (int i = 0; i < list.size(); i++) { ... }   // 每次调 size()

// 快：提前计算
int size = list.size();
for (int i = 0; i < size; i++) { ... }
```

### 避免不必要的对象创建

```java
// 慢：循环里创建对象
for (User u : users) {
    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");   // 每次创建
    sdf.format(u.getDate());
}

// 快：复用对象（或用 ThreadLocal）
SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
for (User u : users) {
    sdf.format(u.getDate());
}
```

### 懒加载

```java
// 懒加载：用到才初始化
private volatile ExpensiveObject obj;

public ExpensiveObject getObj() {
    if (obj == null) {
        synchronized (this) {
            if (obj == null) obj = new ExpensiveObject();
        }
    }
    return obj;
}
```

## 应用场景实战

### 场景 1：接口响应慢排查

```text
1. 定位慢的方法（Arthas trace）
2. 分析慢的原因（循环拼接、重复查询、N+1）
3. 优化（StringBuilder、缓存、批量查询）
4. 验证（重新压测）
```

### 场景 2：内存占用高

```text
1. 分析内存（jmap 导出堆、MAT 分析）
2. 定位大对象（集合过大、缓存过多）
3. 优化（释放、懒加载、限制大小）
```

## 最佳实践与踩坑记录

### 最佳实践

1. **先测量再优化**。用 Arthas/JProfiler 定位瓶颈。

2. **字符串拼接用 StringBuilder**。循环里尤其重要。

3. **集合预分配容量**。避免频繁扩容。

4. **IO 用缓冲流**。批量读写。

5. **避免循环里创建对象**。复用或懒加载。

### 踩坑记录

**坑 1：循环里字符串拼接**

```java
for (...) { result += s; }   // 每次创建新 String，O(n²)
```

循环里用 StringBuilder。

**坑 2：HashMap 频繁扩容**

```java
Map<String, User> map = new HashMap<>();   // 默认 16，频繁扩容
```

预分配容量（expectedSize * 4/3 + 1）。

**坑 3：逐字节读文件**

```java
fis.read()   // 逐字节系统调用，极慢
```

用缓冲流批量读。

**坑 4：盲目优化**

```text
没有定位瓶颈就优化，优化了不重要的代码
```

先测量（Arthas/JMH），优化真正的热点。

**坑 5：循环里创建 SimpleDateFormat**

```java
for (...) { new SimpleDateFormat("yyyy-MM-dd"); }   // 频繁创建，慢且线程不安全
```

复用（ThreadLocal）或用 java.time（DateTimeFormatter）。

**坑 6：忽略装箱开销**

```java
Map<Integer, User> map;   // key 装箱
map.get(1);   // 每次装箱
```

大量装箱场景用 Int2ObjectMap 等特化集合。
