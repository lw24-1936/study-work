---
title: Lock
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, concurrency, lock, reentrantlock, readwritelock, stampedlock]
---

# Lock

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Lock 接口 vs synchronized](#lock-接口-vs-synchronized)
- [ReentrantLock](#reentrantlock)
- [Condition —— 条件变量](#condition--条件变量)
- [ReentrantReadWriteLock 读写锁](#reentrantreadwritelock-读写锁)
- [StampedLock（JDK 8+）](#stampedlockjdk-8)
- [LockSupport —— park / unpark](#locksupport--park--unpark)
- [AQS —— 锁的底层骨架](#aqs--锁的底层骨架)
- [Java 锁全景对比](#java-锁全景对比)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`java.util.concurrent.locks` 包是 JDK 5 引入的更灵活的锁机制。`synchronized` 使用简单但功能受限——不能尝试获取锁、不能超时放弃、不能中断等待、只能是独占锁。Lock 接口解决了这些痛点的同时还提供了读写锁和乐观读。

核心接口与实现类：

```
Lock
├── ReentrantLock          —— 可重入互斥锁
├── ReentrantReadWriteLock —— 读写锁（读共享，写互斥）
│   ├── ReadLock
│   └── WriteLock
└── StampedLock            —— 乐观读 + 悲观读写的读写锁（JDK 8+）

Condition —— Lock 的 wait/notify 替代
```

## Lock 接口 vs synchronized

| 维度 | synchronized | Lock |
|------|-------------|------|
| 获取锁 | 阻塞直到获取 | `lock()` 阻塞、`tryLock()` 非阻塞、`tryLock(timeout)` 超时 |
| 释放锁 | 自动（出了同步块就释放） | 手动（必须在 finally 中 unlock） |
| 中断 | 不可中断 | `lockInterruptibly()` 可响应中断 |
| 公平性 | 不公平 | 可选公平锁 |
| 条件变量 | 一个（隐式的 wait/notify） | 多个 Condition |
| 锁状态 | 无法查询 | 可以查询 `isLocked()`、`getQueueLength()` 等 |
| 读写分离 | 不支持 | ReadWriteLock 支持 |
| 性能 | JDK 6+ 优化后接近 Lock | 在激烈竞争下略好 |

## ReentrantLock

```java
import java.util.concurrent.locks.ReentrantLock;

ReentrantLock lock = new ReentrantLock();       // 不公平锁（默认，性能好）
ReentrantLock fairLock = new ReentrantLock(true); // 公平锁

// 标准用法
lock.lock();
try {
    // 临界区
} finally {
    lock.unlock();  // 必须释放！放在 finally 中
}

// tryLock —— 尝试获取，拿不到立即返回 false
if (lock.tryLock()) {
    try {
        // 临界区
    } finally {
        lock.unlock();
    }
} else {
    // 做备选方案
}

// tryLock(timeout) —— 等待指定时间
if (lock.tryLock(1, TimeUnit.SECONDS)) {
    try { /* ... */ } finally { lock.unlock(); }
} else {
    throw new RuntimeException("获取锁超时");
}

// lockInterruptibly —— 可响应中断
try {
    lock.lockInterruptibly();
    try { /* ... */ } finally { lock.unlock(); }
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    // 被中断，放弃获取锁
}
```

### 公平锁 vs 非公平锁

```java
// 公平锁：排队——等待最久的线程先获取锁
ReentrantLock fair = new ReentrantLock(true);

// 非公平锁（默认）：插队——新来的线程可以"抢"锁
ReentrantLock nonfair = new ReentrantLock(false);
```

非公平锁性能更好——减少了线程切换开销。公平锁适合需要严格按顺序执行的场景。

## Condition —— 条件变量

`Condition` 是 `Lock` 体系的 `wait/notify`——一个 Lock 可以有多个 Condition：

```java
class BoundedBuffer {
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull  = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();
    private final Object[] items = new Object[100];
    private int putIdx, takeIdx, count;

    public void put(Object item) throws InterruptedException {
        lock.lock();
        try {
            while (count == items.length) {  // 满了
                notFull.await();              // 等待"非满"条件
            }
            items[putIdx] = item;
            if (++putIdx == items.length) putIdx = 0;
            count++;
            notEmpty.signal();               // 通知"非空"条件
        } finally {
            lock.unlock();
        }
    }

    public Object take() throws InterruptedException {
        lock.lock();
        try {
            while (count == 0) {             // 空了
                notEmpty.await();             // 等待"非空"条件
            }
            Object item = items[takeIdx];
            if (++takeIdx == items.length) takeIdx = 0;
            count--;
            notFull.signal();                // 通知"非满"条件
            return item;
        } finally {
            lock.unlock();
        }
    }
}
```

Condition 核心 API：

| 方法 | 等价 Object 方法 | 说明 |
|------|-----------------|------|
| `await()` | `wait()` | 释放锁，进入等待 |
| `signal()` | `notify()` | 唤醒一个等待线程 |
| `signalAll()` | `notifyAll()` | 唤醒所有等待线程 |
| `await(timeout, unit)` | `wait(timeout)` | 限时等待 |

## ReentrantReadWriteLock 读写锁

读写锁分离读和写——**读读不互斥**，极大提升读多写少场景的并发度：

```java
import java.util.concurrent.locks.ReentrantReadWriteLock;

class CachedData {
    private Object data;
    private final ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();
    private final Lock readLock  = rwLock.readLock();
    private final Lock writeLock = rwLock.writeLock();

    // 读——多个线程可以同时持有
    public Object read() {
        readLock.lock();
        try {
            return data;
        } finally {
            readLock.unlock();
        }
    }

    // 写——互斥，所有读者和写者都被阻塞
    public void write(Object newData) {
        writeLock.lock();
        try {
            data = newData;
        } finally {
            writeLock.unlock();
        }
    }

    // 锁降级：写锁 → 读锁（持有写锁时可以获取读锁）
    public Object readAfterWrite(Object newData) {
        writeLock.lock();
        try {
            data = newData;
            readLock.lock();     // 获取读锁
        } finally {
            writeLock.unlock();  // 释放写锁（现在只剩读锁）
        }
        try {
            return data;         // 读锁保护
        } finally {
            readLock.unlock();
        }
    }
}
```

读写锁规则：
- 读锁：共享锁，多个线程可同时持有读锁
- 写锁：独占锁，持有写锁时其他线程不能持有读锁或写锁
- 锁降级（写→读）：允许，如上面的示例
- 锁升级（读→写）：**不允许**！会导致死锁

## StampedLock（JDK 8+）

`StampedLock` 是 `ReentrantReadWriteLock` 的改进版——增加了**乐观读**模式（不加锁读）：

```java
import java.util.concurrent.locks.StampedLock;

class Point {
    private double x, y;
    private final StampedLock lock = new StampedLock();

    // 写（互斥）
    public void move(double deltaX, double deltaY) {
        long stamp = lock.writeLock();
        try {
            x += deltaX;
            y += deltaY;
        } finally {
            lock.unlockWrite(stamp);
        }
    }

    // 乐观读（无锁）
    public double distanceFromOrigin() {
        long stamp = lock.tryOptimisticRead();   // 获取乐观读戳记
        double currentX = x;
        double currentY = y;
        if (!lock.validate(stamp)) {             // 校验戳记是否还有效
            stamp = lock.readLock();              // 无效就升级为悲观读
            try {
                currentX = x;
                currentY = y;
            } finally {
                lock.unlockRead(stamp);
            }
        }
        return Math.sqrt(currentX * currentX + currentY * currentY);
    }
}
```

三种读模式对比：

| 模式 | 方法 | 性能 | 适用 |
|------|------|------|------|
| 乐观读 | `tryOptimisticRead()` | 最高（无锁） | 写很少的读多写少场景 |
| 读锁 | `readLock()` | 中 | 常规读多写少 |
| 写锁 | `writeLock()` | 低（互斥） | 写入 |

注意：
- StampedLock **不可重入**——持有锁时不能再次获取同一把锁
- 没有 Condition 支持
- 乐观读用 `validate(stamp)` 校验，失败则退化为悲观读

## LockSupport —— park / unpark

`LockSupport` 是 JDK 锁框架的最底层原语——所有 Lock 实现（ReentrantLock、AQS 等）最终都依赖它来挂起和唤醒线程。它比 `wait/notify` 更灵活：

| 对比 | wait/notify | park/unpark |
|------|------------|-------------|
| 调用前提 | 必须在 synchronized 块内 | 无需锁，任何地方都可调用 |
| 许可机制 | 无（信号不累计） | 有——unpark 可以先于 park 调用（许可累计 1 个） |
| 唤醒精度 | notify 随机、notifyAll 全部 | unpark(Thread) 精确唤醒指定线程 |
| 中断 | wait 抛 InterruptedException | park 返回但不抛异常（需自行检查） |

```java
import java.util.concurrent.locks.LockSupport;

// park —— 挂起当前线程
LockSupport.park();
// 等价于 LockSupport.park(this) —— this 是 blocker 对象，用于调试

// unpark —— 唤醒指定线程
Thread t = new Thread(() -> {
    System.out.println("线程挂起...");
    LockSupport.park();                     // 在此阻塞
    System.out.println("线程被唤醒！");
});
t.start();

Thread.sleep(1000);
LockSupport.unpark(t);                      // 精确唤醒线程 t

// unpark 可以先于 park 调用——许可"预存"
LockSupport.unpark(t);                      // 发放一个许可
LockSupport.park();                         // 消费已有的许可，不阻塞
// 许可不可累积——连续两次 unpark 也只能让一次 park 不阻塞

// 带超时的 park
LockSupport.parkNanos(1_000_000_000L);      // 最多等 1 秒
LockSupport.parkUntil(System.currentTimeMillis() + 5000);  // 等到指定时间

// park 被中断时静默返回（不抛异常）——需要自行检测
Thread t2 = new Thread(() -> {
    while (!Thread.currentThread().isInterrupted()) {
        LockSupport.park();                  // 被中断时返回，不抛异常
        if (Thread.currentThread().isInterrupted()) {
            System.out.println("检测到中断，退出");
        }
    }
});

// 使用 blocker 对象便于 jstack 诊断
Object blocker = new Object();
LockSupport.park(blocker);                   // jstack 会显示 "parking to wait for <blocker>"
```

### park/unpark 的实现原理

底层使用 `Unsafe.park()` / `Unsafe.unpark()`——最终调用 OS 的线程挂起/唤醒原语（Linux 上是 `pthread_cond_wait` / `pthread_cond_signal`）。每个线程持有一个 `_counter`（0 或 1）：

```
park():
  if (_counter > 0) { _counter = 0; return; }  // 有许可，消费并返回
  else { 挂起当前线程; }                         // 无许可，阻塞

unpark(thread):
  if (线程已挂起) { 唤醒线程; }
  else { _counter = 1; }                       // 线程还没 park，许可暂存
```

这就是为什么 unpark 可以先于 park 调用——许可被存起来，下次 park 时直接消费。

## AQS —— 锁的底层骨架

`AbstractQueuedSynchronizer`（AQS）是 `java.util.concurrent.locks` 包的核心——它提供了一个基于 **FIFO 等待队列 + int 状态变量**的同步器框架。你在 Java 中见到的几乎所有并发工具都以它为基础：

```
AQS 的子类（直接或间接）：
├── ReentrantLock    —— Sync extends AQS
├── ReentrantReadWriteLock —— Sync extends AQS
├── Semaphore        —— Sync extends AQS
├── CountDownLatch   —— Sync extends AQS
├── CyclicBarrier    —— 内部用 ReentrantLock（间接依赖 AQS）
├── ThreadPoolExecutor.Worker —— 继承 AQS
└── FutureTask       —— Sync extends AQS
```

### AQS 的核心设计

```
AQS 维护两个东西：

1. int state —— 同步状态（volatile）
   - ReentrantLock: state=0 未锁，state>0 被持有，值为重入次数
   - Semaphore: state=许可证数量
   - CountDownLatch: state=倒计数

2. CLH 队列（FIFO 双向链表）—— 等待线程的队列
   
   head                        tail
    ↓                           ↓
   [Node] ↔ [Node] ↔ [Node] ↔ [Node]
   (持有锁)  (等待)    (等待)    (等待)
   
   每个 Node 包含：
   - thread: 等待的线程
   - waitStatus: SIGNAL(-1)/CANCELLED(1)/CONDITION(-2)/PROPAGATE(-3)
   - prev / next: 双向链表指针
```

### AQS 提供的核心方法

```java
// 需要子类重写的方法（模板方法模式）
protected boolean tryAcquire(int arg);        // 独占式获取
protected boolean tryRelease(int arg);        // 独占式释放
protected int tryAcquireShared(int arg);      // 共享式获取
protected boolean tryReleaseShared(int arg);  // 共享式释放
protected boolean isHeldExclusively();        // 是否被当前线程独占

// AQS 已实现的方法（子类直接使用）
acquire(int arg);             // 独占获取，失败则入队等待
release(int arg);             // 独占释放，唤醒后续节点
acquireShared(int arg);       // 共享获取
releaseShared(int arg);       // 共享释放
```

### 简化版 ReentrantLock 的 AQS 实现

```java
// 展示 AQS 的基本使用模式（概念代码，非源码）
class SimpleLock {
    private final Sync sync = new Sync();

    // 内部 Sync 继承 AQS
    private static class Sync extends AbstractQueuedSynchronizer {
        @Override
        protected boolean tryAcquire(int acquires) {
            Thread current = Thread.currentThread();
            int c = getState();
            if (c == 0) {
                // 没人持有锁 → CAS 抢
                if (compareAndSetState(0, acquires)) {
                    setExclusiveOwnerThread(current);  // 设置持有者
                    return true;
                }
            } else if (current == getExclusiveOwnerThread()) {
                // 重入
                setState(c + acquires);
                return true;
            }
            return false;  // 抢不到 → AQS 会把这个线程加入等待队列
        }

        @Override
        protected boolean tryRelease(int releases) {
            int c = getState() - releases;
            if (Thread.currentThread() != getExclusiveOwnerThread())
                throw new IllegalMonitorStateException();
            boolean free = (c == 0);
            if (free) setExclusiveOwnerThread(null);
            setState(c);
            return free;  // 完全释放 → AQS 会唤醒队列中的下一个节点
        }
    }

    public void lock()    { sync.acquire(1); }
    public void unlock()  { sync.release(1); }
}
```

### ReentrantReadWriteLock 的共享模式

读写锁的 AQS 用 state 的高 16 位存读锁计数、低 16 位存写锁计数：

```
state 的位划分：
┌─────────────────┬─────────────────┐
│  高 16 位(读锁)  │  低 16 位(写锁)  │
│  sharedCount    │  exclusiveCount │
└─────────────────┴─────────────────┘

读锁获取 → tryAcquireShared (允许多个线程同时持有)
写锁获取 → tryAcquire      (互斥)
```

### AQS 中 Condition 的实现

AQS 内部还有一个 **ConditionObject** 类（实现 `Condition` 接口），它维护一个独立的**条件等待队列**：

```
主队列（等待锁）：head → [Node] → [Node] → [Node] → tail
条件队列（等待条件）：firstWaiter → [Node] → [Node] → lastWaiter

await():
  1. 把当前节点从主队列移到条件队列
  2. 释放锁（release）
  3. 在条件队列中 park 等待

signal():
  1. 从条件队列头部取出一个节点
  2. 将它移回主队列（重新竞争锁）
```

## Java 锁全景对比

以下是 Java 中所有同步/锁机制的完整对比——涵盖 synchronized、Lock 体系、原子类、并发工具、Thread 原语：

### 互斥锁

| 机制 | 类/关键字 | 可重入 | 公平性 | 可中断 | 超时 | 读写分离 | 性能 |
|------|----------|--------|--------|--------|------|----------|------|
| synchronized | 关键字 | 是 | 否 | 否 | 否 | 否 | JDK 6+ 优化后接近 Lock |
| ReentrantLock | 类 | 是 | 可选 | 是 | tryLock(timeout) | 否 | 略优于 synchronized（高竞争） |

### 读写锁

| 机制 | 类 | 可重入 | 乐观读 | 锁降级 | 锁升级 | 适用 |
|------|-----|--------|--------|--------|--------|------|
| ReentrantReadWriteLock | 类 | 是 | 否 | 支持(写→读) | 不支持 | 读多写少 |
| StampedLock | 类 | 否 | 是 | 支持 | 不支持 | 读极多写极少 |

### 信号量与屏障

| 机制 | 类 | 核心方法 | 典型场景 |
|------|-----|----------|----------|
| Semaphore | 类 | acquire/release | 限流、连接池 |
| CountDownLatch | 类 | countDown/await | 等待多个任务完成 |
| CyclicBarrier | 类 | await | 多线程步调一致（可重用） |
| Exchanger | 类 | exchange | 两线程交换数据 |
| Phaser | 类 | arrive/awaitAdvance | 分阶段多线程协调（JDK 7+） |

```java
// Semaphore —— 控制同时访问资源的线程数
Semaphore semaphore = new Semaphore(5);  // 最多 5 个并发
semaphore.acquire();                     // 获取许可
try { /* 受保护的代码 */ } 
finally { semaphore.release(); }

// CountDownLatch —— 一次性门闩
CountDownLatch latch = new CountDownLatch(3);
// 三个工作线程完成后调用 latch.countDown()
latch.await();  // 主线程等待直到 count 归零

// CyclicBarrier —— 可重复使用的栅栏
CyclicBarrier barrier = new CyclicBarrier(4, () -> System.out.println("全部就绪"));
barrier.await();  // 等待所有 4 个线程到位，然后一起通过
```

### 无锁机制

| 机制 | 底层 | 适用 |
|------|------|------|
| Atomic 原子类 | CAS 指令 | 简单计数器、标志位、引用更新 |
| volatile | 内存屏障 | 状态标志、可见性保证 |
| ConcurrentLinkedQueue | CAS + 自旋 | 无锁队列 |
| LongAdder | 分散热点 + CAS | 高并发累加 |

### 阻塞与唤醒原语

| 机制 | 调用前提 | 精确唤醒 | 先唤醒后阻塞 |
|------|----------|----------|--------------|
| wait/notify | synchronized 块内 | 否（notify 随机） | 否 |
| LockSupport.park/unpark | 无 | 是（unpark(Thread)） | 是 |
| Condition.await/signal | Lock 持有 | 是 | 否 |

### 选择决策树

```
需要互斥访问？
├── 简单场景、代码块粒度的锁 → synchronized
├── 需要 tryLock/超时/公平锁/可中断 → ReentrantLock
├── 读多写少 → ReentrantReadWriteLock
├── 读极多写极少 + 追求极致性能 → StampedLock（乐观读）
└── 只保护简单状态(计数器/标志) → AtomicInteger / volatile

需要协调多个线程？
├── 等待多个任务完成（一次性） → CountDownLatch
├── 多线程步调一致（可重复） → CyclicBarrier
├── 控制并发数量 → Semaphore
└── 复杂异步编排 → CompletableFuture

只需挂起/唤醒线程？
├── 已在 synchronized 内 → wait/notify
├── 使用 Lock 体系 → Condition
└── 底层/自定义锁 → LockSupport.park/unpark
```

## 应用场景实战

### 场景一：tryLock 防死锁

```java
public static boolean transferWithTimeout(Account from, Account to, int amount,
                                           long timeout, TimeUnit unit) 
        throws InterruptedException {
    long remaining = unit.toNanos(timeout);
    
    while (true) {
        if (from.lock.tryLock(remaining, TimeUnit.NANOSECONDS)) {
            try {
                if (to.lock.tryLock(remaining, TimeUnit.NANOSECONDS)) {
                    try {
                        if (from.getBalance() >= amount) {
                            from.debit(amount);
                            to.credit(amount);
                            return true;
                        }
                        return false;
                    } finally {
                        to.lock.unlock();
                    }
                }
            } finally {
                from.lock.unlock();
            }
        }
        if (remaining <= 0) return false;
    }
}
```

### 场景二：读写锁实现缓存

```java
public class ReadWriteCache<K, V> {
    private final Map<K, V> cache = new HashMap<>();
    private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();

    public V get(K key, Supplier<V> loader) {
        lock.readLock().lock();
        try {
            V value = cache.get(key);
            if (value != null) return value;
        } finally {
            lock.readLock().unlock();
        }

        // 缓存未命中，升级为写锁加载数据
        lock.writeLock().lock();
        try {
            return cache.computeIfAbsent(key, k -> loader.get());
        } finally {
            lock.writeLock().unlock();
        }
    }
}
```

### 场景三：Condition 实现限流器

```java
public class RateLimiter {
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition available = lock.newCondition();
    private final long intervalMs;

    private long nextAvailableTime = System.currentTimeMillis();

    public RateLimiter(int permitsPerSecond) {
        this.intervalMs = 1000 / permitsPerSecond;
    }

    public void acquire() throws InterruptedException {
        lock.lock();
        try {
            long now = System.currentTimeMillis();
            if (now < nextAvailableTime) {
                available.await(nextAvailableTime - now, TimeUnit.MILLISECONDS);
            }
            nextAvailableTime = Math.max(now, nextAvailableTime) + intervalMs;
        } finally {
            lock.unlock();
        }
    }
}
```

## 最佳实践与踩坑记录

### Lock 的标准范式

```java
Lock lock = new ReentrantLock();
lock.lock();          // 1. 在 try 之前加锁
try {
    // 2. 临界区
} finally {
    lock.unlock();    // 3. 在 finally 中解锁
}
// 为什么 lock() 要在 try 外？
// 如果 lock() 自己抛异常（比如 OOM），try-finally 里的 unlock 不该执行
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| 忘记解锁 | Lock 不会自动释放 | 使用 try-finally 模板 |
| lock() 放在 try 块内 | lock() 抛异常时 unlock 了未持有的锁 | lock() 放在 try 之前 |
| StampedLock 重复加锁 | 不可重入 | 注意不要嵌套调用加锁方法 |
| 读锁升级写锁死锁 | ReentrantReadWriteLock 不支持锁升级 | 先释放读锁再获取写锁 |
| Condition.await 后忘记重新检查条件 | 虚假唤醒 | 始终用 `while` 循环 |

### 选型建议

```
简单互斥 → synchronized
需要 tryLock/定时锁/公平锁 → ReentrantLock
读多写少 → ReentrantReadWriteLock
读极多写极少 + 追求极致性能 → StampedLock 乐观读
多个条件变量 → ReentrantLock + Condition
```

## 总结

- Lock 家族：ReentrantLock（可重入互斥）、ReentrantReadWriteLock（读写分离）、StampedLock（乐观读）
- Lock 需要手动释放，标准范式：`lock(); try { ... } finally { unlock(); }`
- Condition = Lock 版的 wait/notify，一个 Lock 可以有多个 Condition
- 读写锁：读读共享、读写互斥、写写互斥；支持锁降级（写→读），不支持锁升级
- StampedLock 是性能利器——乐观读无锁 + validate 校验，适合读极多写极少的场景
- synchronized 用起来简单、JVM 优化好，性能不是选择 Lock 的理由——功能需求才是
