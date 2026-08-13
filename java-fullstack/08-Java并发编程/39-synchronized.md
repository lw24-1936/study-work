---
title: synchronized
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, concurrency, synchronized, lock, monitor]
---

# synchronized

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [synchronized 的三种用法](#synchronized-的三种用法)
- [对象锁 vs 类锁](#对象锁-vs-类锁)
- [Monitor 机制](#monitor-机制)
- [锁升级（偏向锁 → 轻量锁 → 重量锁）](#锁升级偏向锁--轻量锁--重量锁)
- [synchronized 底层原理](#synchronized-底层原理)
- [可重入性](#可重入性)
- [wait / notify / notifyAll](#wait--notify--notifyall)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`synchronized` 是 Java 内置的互斥同步机制——JDK 1.0 就存在，至今仍是使用最广泛的锁。它的设计哲学是"使用简单，优化深入"：

- **JDK 1.0-1.5**：重量级锁，每次都调用 OS 的 mutex，性能差
- **JDK 1.6**：引入偏向锁、轻量级锁、自旋锁——大部分场景下性能接近无锁
- **JDK 15+**：偏向锁被默认禁用（因为维护成本高，实际收益有限）

## synchronized 的三种用法

### 1. 修饰实例方法

```java
public class Counter {
    private int count = 0;

    public synchronized void increment() {
        count++;  // 锁的是 this（当前实例）
    }

    // 等价于
    public void increment2() {
        synchronized (this) {
            count++;
        }
    }
}
```

### 2. 修饰静态方法

```java
public class StaticCounter {
    private static int count = 0;

    public static synchronized void increment() {
        count++;  // 锁的是 StaticCounter.class（类对象）
    }

    // 等价于
    public static void increment2() {
        synchronized (StaticCounter.class) {
            count++;
        }
    }
}
```

### 3. 修饰代码块（指定锁对象）

```java
public class BlockSync {
    private final Object lock = new Object();
    private int count = 0;

    public void increment() {
        synchronized (lock) {  // 显式指定锁对象，推荐用 private final
            count++;
        }
    }
}
```

## 对象锁 vs 类锁

关键区别：实例锁和类锁**不互斥**——两把不同的锁：

```java
public class Wallet {
    // 实例锁 —— 锁 this
    public synchronized void deduct() { ... }

    // 类锁 —— 锁 Wallet.class
    public static synchronized void check() { ... }
}

// 场景：一个线程调用 deduct()，另一个调用 check()——不会互斥！
// 它们拿的是不同的锁（this vs Wallet.class）

Wallet w1 = new Wallet();
Wallet w2 = new Wallet();

// w1.deduct() 和 w2.deduct() —— 不互斥（不同实例，锁的是各自的 this）
// Wallet.check() 和 Wallet.check() —— 互斥（同一把类锁）
```

## Monitor 机制

每个 Java 对象都有一个关联的 **Monitor**（监视器），synchronized 的底层就是 Monitor：

```
Monitor 结构（简化）：
┌─────────────────┐
│  Owner (持有线程)  │  ← 拿到锁的线程
├─────────────────┤
│  EntryList (等待队列)│ ← 等待获取锁的线程（BLOCKED）
├─────────────────┤
│  WaitSet (等待集合) │  ← 调了 wait() 的线程（WAITING）
└─────────────────┘

加锁：线程进入 EntryList 竞争 → 拿到 Owner → 执行同步代码 → 释放 Owner
wait()：Owner 线程进入 WaitSet，释放锁
notify()：从 WaitSet 中随机唤醒一个线程进入 EntryList
notifyAll()：唤醒 WaitSet 中所有线程进入 EntryList
```

```java
synchronized (obj) {
    while (conditionNotMet()) {  // 必须 while 而不是 if！
        obj.wait();              // 释放锁，进入 WaitSet
    }
    // 条件满足，执行业务...
    obj.notifyAll();             // 唤醒所有等待线程
}
```

## 锁升级（偏向锁 → 轻量锁 → 重量锁）

JDK 1.6 引入的锁升级机制是无锁到重量锁之间的平滑过渡：

```
无锁状态
  │ 第一次获取
  ▼
偏向锁（Biased Locking）
  │ 有竞争
  ▼
轻量级锁（Lightweight Locking）—— CAS 自旋
  │ 自旋次数达到阈值（默认 10 次或等待线程数 > CPU 核数/2）
  ▼
重量级锁（Heavyweight Locking）—— 调用 OS mutex
```

| 锁状态 | 原理 | 开销 | 适用场景 |
|--------|------|------|----------|
| 偏向锁 | 在 Mark Word 记录线程 ID | 极低 | 只有一个线程反复获取锁 |
| 轻量级锁 | CAS 操作 + 自旋等待 | 较低 | 多线程交替执行（不激烈竞争） |
| 重量级锁 | OS Mutex，未获取则阻塞 | 高（用户态→内核态） | 竞争激烈 |

Mark Word 是对象头中用于存储锁状态和 GC 信息的区域——锁升级时 Mark Word 内容会变化。

## synchronized 底层原理

```java
// Java 代码
public synchronized void method() {
    System.out.println("hello");
}

// 编译后字节码（javap -v）：
// 方法标志中多了 ACC_SYNCHRONIZED —— JVM 根据这个标志自动加锁/解锁

// 代码块 synchronized(obj) {} 的字节码：
//   monitorenter   ← 获取 Monitor
//   ... 同步代码 ...
//   monitorexit    ← 释放 Monitor（正常退出）
//   monitorexit    ← 释放 Monitor（异常退出，编译器自动插入）
```

关键点：
- 方法级的 synchronized 通过方法标志 `ACC_SYNCHRONIZED` 隐式加锁
- 代码块级的通过 `monitorenter`/`monitorexit` 指令显式加锁
- 编译器自动为异常路径插入 `monitorexit`，确保锁一定释放

## 可重入性

synchronized 是**可重入锁**——同一个线程可以多次获取同一把锁：

```java
public class ReentrantDemo {
    public synchronized void outer() {
        System.out.println("outer");
        inner();  // 已经持有 this 锁，可以再次进入
    }

    public synchronized void inner() {
        System.out.println("inner");
        // 如果没有可重入性，这里会死锁
    }
}
```

JVM 维护了锁的持有线程和重入计数器——每次 `monitorenter` 计数器 +1，每次 `monitorexit` 计数器 -1，降到 0 时释放锁。

## wait / notify / notifyAll

这三个方法是 `Object` 类的方法（不是 Thread 的方法），必须在 `synchronized` 块内调用：

```java
// 生产者-消费者经典模型
public class MessageQueue {
    private String message;
    private boolean hasMessage = false;

    public synchronized void put(String msg) throws InterruptedException {
        while (hasMessage) {       // 必须用 while，不能用 if
            wait();                // 释放锁，等待消费者消费
        }
        this.message = msg;
        hasMessage = true;
        notifyAll();               // 唤醒等待的消费者
    }

    public synchronized String take() throws InterruptedException {
        while (!hasMessage) {      // 必须用 while
            wait();
        }
        hasMessage = false;
        notifyAll();               // 唤醒等待的生产者
        return message;
    }
}
```

关键规则：
1. 必须在 `synchronized` 块内调用，否则抛 `IllegalMonitorStateException`
2. `wait()` 释放锁，`sleep()` 不释放锁
3. 用 `while` 而不是 `if` 检查条件（防止虚假唤醒）
4. 优先用 `notifyAll()` 而不是 `notify()`——避免信号丢失

## 应用场景实战

### 场景一：线程安全的懒汉单例

```java
public class Singleton {
    // volatile 防止指令重排（详见 volatile 章节）
    private static volatile Singleton instance;

    public static Singleton getInstance() {
        if (instance == null) {                    // 第一次检查（无锁）
            synchronized (Singleton.class) {        // 加锁
                if (instance == null) {             // 第二次检查（有锁）
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

### 场景二：线程安全的计数器

```java
public class SafeCounter {
    private long count = 0;

    public synchronized void increment() {
        count++;
    }

    public synchronized long get() {
        return count;
    }
}
```

### 场景三：转账（锁顺序）

```java
public static void transfer(Account from, Account to, int amount) {
    // 按 hash 排序获取锁，避免死锁
    Account first = from.hashCode() < to.hashCode() ? from : to;
    Account second = from.hashCode() < to.hashCode() ? to : from;

    synchronized (first) {
        synchronized (second) {
            if (from.getBalance() >= amount) {
                from.debit(amount);
                to.credit(amount);
            }
        }
    }
}
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `IllegalMonitorStateException` | 没在 synchronized 块内调 wait/notify | 确保在同步块内调用 |
| 虚假唤醒导致逻辑出错 | 用 `if` 而不是 `while` 检查条件 | 始终用 `while` |
| 死锁 | 多线程以不同顺序获取多把锁 | 统一锁顺序，或使用 `tryLock(timeout)` |
| `notify()` 信号丢失 | notify 随机唤醒一个，可能不是目标线程 | 用 `notifyAll()` |
| 锁 String 对象导致死锁 | String 常量池共享 | 不要用 String 做锁对象 |

### 选择建议

```
简单互斥 → synchronized（JDK 1.6+ 优化后性能足够）
需要 tryLock、定时锁、公平锁 → ReentrantLock
读写锁 → ReentrantReadWriteLock / StampedLock
简单计数 → AtomicInteger

优先 synchronized——代码简洁、自动释放、JVM 优化
性能瓶颈时再考虑 Lock 接口
```

## 总结

- synchronized 三种形态：实例方法（锁 this）、静态方法（锁 Class）、代码块（锁指定对象）
- 底层基于 Monitor：每个对象关联的 EntryList/WaitSet/Owner 机制
- JDK 1.6 引入锁升级：偏向锁 → 轻量锁（CAS自旋） → 重量锁（OS mutex）
- 可重入锁：同一线程可重复获取，通过计数器管理
- `wait/notify/notifyAll` 必须在 synchronized 块内调用，条件检查用 while
- DCL 单例需要 volatile 防止指令重排（synchronized 只保证互斥，不保证可见性/有序性）
