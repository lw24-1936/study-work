---
title: volatile
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, concurrency, volatile, memory-visibility, happens-before]
---

# volatile

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Java 内存模型与可见性](#java-内存模型与可见性)
- [volatile 的可见性](#volatile-的可见性)
- [volatile 的有序性（禁止指令重排）](#volatile-的有序性禁止指令重排)
- [volatile 不保证原子性](#volatile-不保证原子性)
- [happens-before 原则](#happens-before-原则)
- [内存屏障](#内存屏障)
- [DCL 单例中的 volatile](#dcl-单例中的-volatile)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`volatile` 是 Java 中最轻量的同步机制——它不互斥，但解决两个问题：

1. **可见性**：一个线程修改 volatile 变量后，其他线程立即可见
2. **有序性**：禁止指令重排（部分）

它**不解决**：
- 原子性：`count++` 这种复合操作仍然不安全
- 互斥：多个线程仍可以同时操作 volatile 变量

volatile 是性能最高的共享变量同步方式——开销远小于 synchronized，前提是只用它解决可见性和有序性问题。

## Java 内存模型与可见性

理解 volatile 之前必须先理解"为什么变量不可见"：

```
JMM (Java Memory Model) 中的内存层次：

线程 A                    线程 B
┌──────────┐           ┌──────────┐
│ 工作内存  │           │ 工作内存  │
│ (L1/L2)  │           │ (L1/L2)  │
│ count=0  │           │ count=0  │  ← 各自的副本
└────┬─────┘           └────┬─────┘
     │                      │
     ▼                      ▼
┌──────────────────────────────────┐
│          主内存（堆）             │
│          count = 0               │
└──────────────────────────────────┘

线程 A：count = 1  ← 只写到了工作内存，还没刷新到主内存
线程 B：读 count   ← 读到的是自己的副本，仍然是 0！
```

这就是"可见性"问题的根源：每个线程有自己**工作内存**（CPU 缓存 + 寄存器），修改不立即写回主内存，读取也不一定从主内存取。

```java
// 问题演示：没有 volatile
public class VisibilityProblem {
    private static boolean running = true;  // 没有 volatile

    public static void main(String[] args) throws InterruptedException {
        new Thread(() -> {
            while (running) {   // 线程可能永远看不到 running 变成 false！
                // 空循环
            }
            System.out.println("线程结束");
        }).start();

        Thread.sleep(1000);
        running = false;  // 主线程修改了，但被优化的线程可能看不到
        System.out.println("已设置 running=false");
    }
}
```

## volatile 的可见性

加了 `volatile` 后：**写 volatile 变量会立即刷新到主内存，读 volatile 变量会直接从主内存读取**。

```java
private static volatile boolean running = true;  // 加上 volatile

// 现在线程能正确看到 running 的变化了
// volatile 写：把工作内存的值刷到主内存
// volatile 读：从主内存加载最新值
```

volatile 的可见性保证：

```
线程 A 写 volatile 变量：
  → 立即刷新工作内存到主内存
  → 使其他线程工作内存中的该变量缓存失效

线程 B 读 volatile 变量：
  → 缓存失效 → 直接从主内存读取最新值
```

## volatile 的有序性（禁止指令重排）

JVM 和 CPU 会对指令进行重排以提高性能——但 volatile 禁止这种优化：

```java
// 场景：两个线程通过共享变量协调
// 线程 A
config = loadConfig();    // 1
ready = true;             // 2  ← 如果 ready 不是 volatile，1 和 2 可能被重排！

// 线程 B
while (!ready) { }        // 3
use(config);              // 4  ← 可能用到未初始化的 config！
```

volatile 通过**内存屏障**禁止重排：
- **写屏障**：volatile 写之前的操作不会被重排到 volatile 写之后
- **读屏障**：volatile 读之后的操作不会被重排到 volatile 读之前

## volatile 不保证原子性

这是最常见的误解——volatile 不能让 `i++` 变成原子操作：

```java
private static volatile int count = 0;

// 启动 1000 个线程各执行 1000 次 count++
// 期望结果 = 1,000,000，实际结果 < 1,000,000

// 原因：count++ 是三个操作：
// 1. 读 count 的值
// 2. 值 +1
// 3. 写回 count
// volatile 只保证 1 和 3 的可见性，不保证 1-2-3 这整个过程的原子性
```

复合操作需要锁或原子类：

```java
// synchronized —— 保证原子性
private static synchronized void increment() { count++; }

// AtomicInteger —— 保证原子性
private static AtomicInteger count = new AtomicInteger();
count.incrementAndGet();
```

## happens-before 原则

happens-before 是 JMM 定义的操作间偏序关系——如果 A happens-before B，那么 A 的结果对 B 可见：

**volatile 的 happens-before 规则**：
- 对一个 volatile 变量的**写** happens-before 后续对这个 volatile 变量的**读**

```java
// 线程 A
data = 42;           // 普通写
ready = true;        // volatile 写

// 线程 B
if (ready) {         // volatile 读 —— 看到 ready=true 时，data=42 也可见！
    System.out.println(data);  // 打印 42（保证）
}
```

这引出了 volatile 的经典使用模式——**状态标志**：

```java
volatile boolean initialized = false;

// 初始化线程
context = init();     // 所有初始化工作
initialized = true;   // volatile 写 —— 之前的操作对后续 volatile 读者可见

// 工作线程
if (initialized) {    // volatile 读
    context.doWork();  // 可见到完整初始化结果
}
```

## 内存屏障

volatile 的底层是通过 CPU 内存屏障指令实现的：

| 屏障类型 | 指令 | 作用 |
|----------|------|------|
| LoadLoad | `Load1; LoadLoad; Load2` | 确保 Load1 在 Load2 之前完成 |
| StoreStore | `Store1; StoreStore; Store2` | 确保 Store1 在 Store2 之前完成 |
| LoadStore | `Load1; LoadStore; Store2` | 确保 Load1 在 Store2 之前完成 |
| StoreLoad | `Store1; StoreLoad; Load2` | 确保 Store1 在 Load2 之前完成（最重的屏障） |

```java
// volatile 写前后的内存屏障：
// StoreStore 屏障
// volatile 写
// StoreLoad 屏障

// volatile 读前后的内存屏障：
// LoadLoad 屏障
// volatile 读
// LoadStore 屏障
```

## DCL 单例中的 volatile

双重检查锁定（DCL）必须用 volatile——不只是可见性，更重要的是**有序性**：

```java
public class Singleton {
    private static volatile Singleton instance;  // 必须 volatile！

    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();  // 这行不是原子操作！
                }
            }
        }
        return instance;
    }
}
```

`new Singleton()` 的三步（可能被重排）：
```
1. 分配内存空间
2. 初始化对象（调用构造方法）
3. 将 instance 指向分配的内存空间

如果没有 volatile，2 和 3 可能重排：
→ 另一个线程拿到 instance（非 null）时可能对象还没初始化完毕！
```

volatile 的写屏障保证了 1→2→3 的顺序不被重排。

## 应用场景实战

### 场景一：开关控制

```java
public class TaskController {
    private volatile boolean running = true;

    public void start() {
        new Thread(() -> {
            while (running) {
                doWork();
            }
        }).start();
    }

    public void stop() {
        running = false;  // 所有线程立即看到
    }
}
```

### 场景二：状态标志

```java
public class Configuration {
    private volatile boolean initialized = false;
    private Map<String, String> config;

    public void init() {
        config = loadFromDB();  // 1. 加载
        // ... 各种初始化
        initialized = true;      // 2. 设置标志（volatile 写——之前的普通写都对后续读者可见）
    }

    public String get(String key) {
        if (!initialized) {
            throw new IllegalStateException("未初始化");
        }
        return config.get(key);  // 可见到完整配置
    }
}
```

### 场景三：中断状态替代

```java
// 不用 isInterrupted()，用 volatile 标志
public class InterruptibleTask implements Runnable {
    private volatile boolean cancelled = false;

    public void cancel() {
        cancelled = true;
    }

    @Override
    public void run() {
        while (!cancelled) {  // 配合 volatile 立即可见
            processNext();
        }
    }
}
```

## 最佳实践与踩坑记录

### 使用条件

```
满足以下两个条件时，volatile 是安全的替代方案：

1. 对变量的写入不依赖当前值（volatile 不保证 i++ 的原子性）
   或者：能确保只有一个线程写这个变量

2. 变量不参与与其他状态变量的不变性约束
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `i++` 用 volatile 仍然出错 | `i++` 是读-改-写三步复合操作 | 用 `AtomicInteger` 或 `synchronized` |
| DCL 单例没有 volatile | new 操作可能被重排 | 必须加 volatile |
| volatile 数组只保证引用可见 | volatile 修饰的是数组引用，不是元素 | 用 `AtomicIntegerArray` |
| 误认为 volatile 比 synchronized 快很多 | JIT 优化的 synchronized 在很多场景下性能接近 | 实测后再优化 |

### 性能

```
volatile 读 ≈ 普通变量读（只需一次 LoadLoad 屏障）
volatile 写 ≈ 略慢于普通变量写（需要 StoreStore + StoreLoad 屏障）
volatile 读写的开销远小于 synchronized 的加解锁
```

## 总结

- volatile 两大保证：可见性（写立即可见） + 有序性（禁止重排）；不保证原子性
- 本质是通过 CPU 内存屏障指令实现——StoreLoad 是最重的屏障
- volatile 的 happens-before：写 happens-before 后续的读
- 典型场景：状态标志、开关控制、DCL 单例的配套
- `i++` 这种复合操作必须用 AtomicInteger 或 synchronized
- volatile 是轻量级同步——只为可见性/有序性服务，不要越俎代庖
