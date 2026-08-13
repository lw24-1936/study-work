---
title: JVM 垃圾回收
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, jvm, gc, garbage-collection, memory-management]
---

# JVM 垃圾回收

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [如何判断对象可回收](#如何判断对象可回收)
- [GC Roots 与可达性分析](#gc-roots-与可达性分析)
- [三色标记算法](#三色标记算法)
- [分代回收](#分代回收)
- [Minor GC / Major GC / Full GC](#minor-gc--major-gc--full-gc)
- [Stop-The-World](#stop-the-world)
- [引用类型](#引用类型)
- [GC 日志分析](#gc-日志分析)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Java 不需要手动 `free`——JVM 自动判断哪些对象不再被使用并回收它们的内存。这套自动内存管理系统叫 GC（Garbage Collection）。理解 GC 的原理是 JVM 调优的基础——什么时候触发 GC、GC 干了什么、为什么卡顿。

## 如何判断对象可回收

### 引用计数法（Java 未采用）

```java
A.obj = B;
B.obj = A;
// A 和 B 互相引用，引用计数都不为 0
// 但外部没有任何引用指向它们——引用计数法无法回收循环引用！
```

### 可达性分析（Java 采用）

从一组 **GC Roots** 出发，沿着引用链搜索，能到达的对象是"存活"的，到不了的是"垃圾"：

```
GC Roots:
  ├── User u = new User();     ← u 是 GC Root，引用的对象存活
  ├── 栈帧中的局部变量
  ├── 静态变量
  └── ...

可达：
  GC Root → A → B → C    ← 全部存活

不可达：
  GC Root →     X → Y    ← GC Root 引用链断了，X、Y 被回收
```

## GC Roots 与可达性分析

GC Roots 包括以下内容：

| GC Root 类型 | 示例 |
|-------------|------|
| 虚拟机栈（栈帧中的局部变量表）引用的对象 | 方法中 `new` 的对象 |
| 方法区中静态属性引用的对象 | `static User user = new User()` |
| 方法区中常量引用的对象 | `static final String = "hello"` |
| 本地方法栈中 JNI 引用的对象 | Native 代码中的全局引用 |
| JVM 内部引用 | 系统类加载器、基本类型 Class 对象 |
| 所有被同步锁（synchronized）持有的对象 | Monitor 的持有者 |
| JVM 内部的 JMXBean、JVMTI 回调等 | — |

### finalize() 的"自救"（不推荐）

```java
// 对象被标记为垃圾后，如果实现了 finalize()，会放入 F-Queue
// 由 Finalizer 线程执行 finalize()——在 finalize 中可以"复活"自己
public class SelfRescue {
    static SelfRescue SAVE_HOOK;

    @Override
    protected void finalize() throws Throwable {
        SAVE_HOOK = this;  // 重新被引用 → 复活
    }
}
// 注意：finalize 只执行一次，且 JDK 9+ 已废弃，不要依赖它
```

## 三色标记算法

现代 GC 使用**三色标记**进行并发标记——初始将所有对象标记为白色，逐步推进：

```
白色：未被访问（标记结束后，白色 = 垃圾）
灰色：自身已访问，但其引用的对象还没全部访问
黑色：自身已访问，且引用的对象也都访问了

过程：
1. GC Roots 标记为灰色
2. 从灰色集合中取一个对象：
   a. 将其引用的对象标记为灰色
   b. 将自己标记为黑色
3. 重复 2，直到灰色集合为空
4. 剩余的白色对象 = 垃圾，回收
```

**并发标记的漏标问题**（CMS/G1 需要处理）：

```
条件：同时满足以下两个条件会漏标：
1. 赋值器插入了一条或多条从黑色到白色的新引用
2. 赋值器删除了全部从灰色到该白色的直接/间接引用

解决方案：
- CMS：增量更新（Incremental Update）
  黑色引用白色时，将黑色重新标记为灰色 → SATB（Snapshot At The Beginning）

- G1/ZGC：使用 SATB 写屏障解决
```

## 分代回收

基于"弱分代假说"——绝大多数对象都是朝生夕死：

### 新生代（Young Generation）

- 新对象在 Eden 分配
- Minor GC：Eden 满了触发，复制存活对象到 Survivor
- 对象在 S0 → S1 之间每熬过一次 Minor GC，年龄 +1
- 年龄达到阈值（默认 15，`-XX:MaxTenuringThreshold`）→ 晋升到老年代

### 老年代（Old Generation）

- 存储长期存活的对象
- 空间不足 → Major GC / Full GC
- 大对象（超过 `-XX:PretenureSizeThreshold`）直接分配在老年代

### 回收流程

```
Eden 满了
  │
  ▼
Minor GC:
  ├── Eden 中存活对象 → Survivor (S0)
  ├── S0 中存活且年龄不足的对象 → S1
  ├── S0 中存活且年龄足够的对象 → Old
  └── S0 和 S1 的角色互换（S0↔S1 总有一个是空的）

对象晋升到老年代的四种情况：
  1. 年龄超过 MaxTenuringThreshold
  2. Survivor 区中同年龄的对象超过一半 → 该年龄及以上的全部晋升
  3. 大对象直接进入老年代
  4. Survivor 区空间不够 → 部分对象提前晋升
```

## Minor GC / Major GC / Full GC

| 类型 | 作用区域 | 触发条件 | STW 时长 |
|------|----------|----------|----------|
| Minor GC | 仅新生代 | Eden 满 | 短暂（通常几十 ms） |
| Major GC | 仅老年代 | 老年代空间不足 | 较长（通常几百 ms） |
| Full GC | 整个堆 + Metaspace | System.gc()、老年代持续满、Metaspace 满 | 很长（秒级） |

### Full GC 触发条件

```
1. 老年代空间不足
2. Metaspace 空间不足
3. System.gc() 显式调用
4. Minor GC 时判断要晋升到老年代的对象大小 > 老年代剩余空间
5. CMS GC 出现 Concurrent Mode Failure
```

### 避免 Full GC 的策略

```
- 对象尽量在 Minor GC 中回收（减少晋升）
- 预估老年代增长速率，合理设置老年代大小
- 不要频繁 System.gc()
- 设置 Metaspace 上限防止无限增长
```

## Stop-The-World

STW 是 GC 的"暂停世界"——GC 线程工作时，所有用户线程暂停：

```java
// 此时发生 STW
User user = new User();  // 用户线程被挂起
// ... GC 正在回收 ...
user.getName();           // GC 完成后用户线程恢复
```

不同 GC 的 STW 特征：

| GC | STW 阶段 | 特点 |
|----|----------|------|
| Serial | 全部阶段 | 单线程，暂停长 |
| Parallel | Minor GC + Full GC | 多线程，暂停中等 |
| CMS | 初始标记 + 重新标记 | 两次短暂 STW |
| G1 | 初始标记 + 重新标记 + 部分清理 | 多次短暂 STW |
| ZGC | 极短的初始标记 | 暂停 < 1ms（JDK 21 < 0.1ms） |

## 引用类型

Java 提供四种引用强度：

```java
// 1. 强引用（Strong Reference）—— 默认，死不回收
Object obj = new Object();
// obj = null; → 才会被回收

// 2. 软引用（Soft Reference）—— 内存不够才回收
SoftReference<byte[]> soft = new SoftReference<>(new byte[100 * 1024 * 1024]);
// 适合：缓存（内存够用就留着，不够就回收）

// 3. 弱引用（Weak Reference）—— 下一次 GC 就回收
WeakReference<Object> weak = new WeakReference<>(new Object());
// 适合：WeakHashMap、ThreadLocal 的 key

// 4. 虚引用（Phantom Reference）—— 幽灵引用，get() 永远返回 null
ReferenceQueue<Object> queue = new ReferenceQueue<>();
PhantomReference<Object> phantom = new PhantomReference<>(new Object(), queue);
// 适合：对象被回收时收到通知（管理直接内存）
```

## GC 日志分析

JDK 9+ 统一 GC 日志格式：

```bash
# 开启 GC 日志（JDK 9+）
-Xlog:gc*:file=/tmp/gc.log:time,level,tags

# JDK 8 的格式
-XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:/tmp/gc.log
```

```log
# 日志示例（G1）
[2026-08-12T10:30:00.123+0000] GC(1) Pause Young (Normal) (G1 Evacuation Pause) 50M->30M(200M) 15.2ms
  │                  │  │         │                                   │          │       │
  时间              序号 GC暂停  年轻代                               堆使用变化  堆总量  耗时

[2026-08-12T10:35:00.456+0000] GC(3) Pause Full (G1 Compaction Pause) 180M->100M(200M) 250.7ms
```

关键指标：GC 频率、堆回收量、单次 GC 耗时——这三者决定 GC 是否健康。

## 应用场景实战

### 场景一：大对象直接进入老年代

```java
// 配置
// -XX:PretenureSizeThreshold=1048576  (1MB，仅 Serial/ParNew 有效)

// 超过此大小的对象直接进入老年代
byte[] big = new byte[2 * 1024 * 1024];  // 2MB → 直接进入老年代
// 避免大对象在新生代来回复制
```

### 场景二：内存泄漏排查思路

```
1. 获取 Heap Dump: jmap -dump:format=b,file=heap.hprof <pid>
2. 用 MAT / JProfiler 打开
3. 查看 Dominator Tree —— 谁占用了最多内存
4. 追踪 GC Root 路径 —— 为什么这个对象没被回收
5. 常见泄漏点：ThreadLocal 未清理、HashMap 只增不减、Listener 未注销
```

### 场景三：减少 STW 的策略

```
1. 降低 -Xms 和 -Xmx 的差距（减少扩容时间）
2. 选用低延迟 GC（G1/ZGC）
3. 减少 Full GC 频率（避免 System.gc()）
4. 控制对象晋升速率（减小 Survivor 区溢出）
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| GC 频繁（每秒多次） | Eden 太小或对象创建太快 | 增大新生代；排查代码中频繁 `new` 的地方 |
| Full GC 频繁 | 老年代增长过快 | 增大老年代；检查内存泄漏 |
| GC 时间过长 | 堆太大或使用了串行 GC | 换 G1/ZGC；减小堆或拆分实例 |
| Promotion Failed | Survivor 空间不够，老年代也装不下 | 增大 Survivor；增加 `MaxTenuringThreshold` |
| Concurrent Mode Failure | CMS 并发回收速度 < 对象分配速度 | 增大老年代；提前 CMS 触发阈值 |

### 关键参数

```bash
-Xms2g -Xmx2g                       # 堆 2GB，初始=最大（减少动态扩容）
-XX:NewRatio=2                      # 老年代/新生代 = 2
-XX:SurvivorRatio=8                 # Eden/Survivor = 8
-XX:MaxTenuringThreshold=15         # 晋升年龄阈值
-XX:+UseG1GC                        # 使用 G1
-XX:MaxGCPauseMillis=200            # G1 目标暂停时间
-XX:+HeapDumpOnOutOfMemoryError     # OOM 时自动 dump
```

## 总结

- 可达性分析：从 GC Roots 出发，不可达的对象 = 垃圾
- 三色标记：白色(垃圾)、灰色(待扫描)、黑色(已扫描)，并发标记需要处理漏标
- 分代回收：新生代(Eden+Survivor×2) 用复制算法，老年代一般用标记-清除/整理
- Minor GC 清理新生代(快)，Full GC 清理全堆(慢)，避免 Full GC 是调优核心目标
- STW = GC 暂停用户线程的时间，ZGC 做到 < 1ms
- 四种引用强度：强 > 软 > 弱 > 虚
