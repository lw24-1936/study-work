---
title: ForkJoin
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, concurrency, forkjoin, work-stealing, parallel]
---

# ForkJoin

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [ForkJoinPool](#forkjoinpool)
- [ForkJoinTask 与 RecursiveTask](#forkjointask-与-recursivetask)
- [RecursiveAction（无返回值）](#recursiveaction无返回值)
- [Work Stealing 工作窃取](#work-stealing-工作窃取)
- [CountedCompleter](#countedcompleter)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Fork/Join 框架是 JDK 7 引入的并行计算框架——专为**分治算法**设计。它的核心思想：

```
Fork（分解）：把大任务递归拆分成小任务
Join（合并）：等待子任务完成，合并结果

            [总任务]
           /       \
      [子任务]   [子任务]
       /    \     /    \
    [叶]  [叶] [叶]  [叶]
      ↓     ↓    ↓     ↓
    计算结果 ←────────────── 合并 ←
```

ForkJoin 不是通用的线程池——它是为**可递归分解**的计算任务优化的（归并排序、数组求和、文件遍历等）。

## ForkJoinPool

```java
// ForkJoinPool —— 每个线程有自己的双端队列
ForkJoinPool pool = new ForkJoinPool();  // 默认：CPU 核数

// 或指定并行度
ForkJoinPool pool = new ForkJoinPool(4);

// 提交任务
ForkJoinTask<Integer> task = pool.submit(new MyRecursiveTask(data));
Integer result = task.get();

// 常用：commonPool（JDK 8 并行流内部使用）
ForkJoinPool common = ForkJoinPool.commonPool();
System.out.println(common.getParallelism());  // CPU 核数 - 1
```

和 ThreadPoolExecutor 关键区别：
- ForkJoinPool 的每个工作线程有自己的**双端工作队列**
- 支持工作窃取——空闲线程从忙碌线程的队尾"偷"任务

## ForkJoinTask 与 RecursiveTask

`RecursiveTask<V>` 是有返回值的分治任务：

```java
import java.util.concurrent.RecursiveTask;
import java.util.concurrent.ForkJoinPool;

// 计算 1+2+...+n 的并行版本
class SumTask extends RecursiveTask<Long> {
    private static final int THRESHOLD = 10000;  // 阈值：小于此直接计算
    private final long[] numbers;
    private final int start, end;

    SumTask(long[] numbers, int start, int end) {
        this.numbers = numbers;
        this.start = start;
        this.end = end;
    }

    @Override
    protected Long compute() {
        int length = end - start;
        
        // 足够小 → 直接计算
        if (length <= THRESHOLD) {
            long sum = 0;
            for (int i = start; i < end; i++) {
                sum += numbers[i];
            }
            return sum;
        }
        
        // 太大 → 拆分
        int mid = start + length / 2;
        SumTask leftTask = new SumTask(numbers, start, mid);
        SumTask rightTask = new SumTask(numbers, mid, end);
        
        leftTask.fork();              // 异步执行左半部分
        Long rightResult = rightTask.compute();  // 同步执行右半部分
        Long leftResult = leftTask.join();       // 等待左半部分完成
        
        return leftResult + rightResult;
    }
}

// 使用
long[] data = new long[10_000_000];
Arrays.fill(data, 1);
ForkJoinPool pool = new ForkJoinPool();
Long result = pool.invoke(new SumTask(data, 0, data.length));
System.out.println(result);  // 10_000_000
```

## RecursiveAction（无返回值）

当不需要返回值时，用 `RecursiveAction`：

```java
import java.util.concurrent.RecursiveAction;

// 并行排序（归并排序）
class MergeSortAction extends RecursiveAction {
    private static final int THRESHOLD = 1000;
    private final int[] array;
    private final int start, end;

    MergeSortAction(int[] array, int start, int end) {
        this.array = array;
        this.start = start;
        this.end = end;
    }

    @Override
    protected void compute() {
        if (end - start <= THRESHOLD) {
            Arrays.sort(array, start, end);  // 小数组直接排序
            return;
        }
        
        int mid = (start + end) / 2;
        MergeSortAction left = new MergeSortAction(array, start, mid);
        MergeSortAction right = new MergeSortAction(array, mid, end);
        
        invokeAll(left, right);  // 并行执行然后等待
        merge(array, start, mid, end);  // 合并两个有序子数组
    }
}
```

## Work Stealing 工作窃取

这是 ForkJoin 相比普通线程池最核心的优化：

```
工作线程的双端队列：
  Thread 1: [任务A, 任务B, 任务C, 任务D]  ← 自己从头部取
  Thread 2: [任务E, 任务F]               ← 空闲！
  Thread 3: []                           ← 空闲！
  Thread 4: [任务G]

空闲线程从其他线程队列的**尾部**窃取任务
→ 减少竞争（窃取者从尾部取，拥有者从头部取）
→ 自动负载均衡
```

对比普通线程池（所有线程共享一个队列）：
- 单队列有竞争瓶颈（每次取任务都要争锁）
- 无负载均衡——某些线程闲着而其他线程队列积压

## CountedCompleter

`CountedCompleter` 是 ForkJoin 中处理大量子任务的工具——当所有子任务完成时自动触发父任务的完成回调：

```java
// 场景：遍历文件树，每发现一个文件就 fork 一个处理任务
class FileSearchTask extends CountedCompleter<Void> {
    private final Path dir;

    @Override
    public void compute() {
        try (Stream<Path> entries = Files.list(dir)) {
            List<Path> children = entries.collect(Collectors.toList());
            setPendingCount(children.size());  // 设置待完成计数
            
            for (Path child : children) {
                if (Files.isDirectory(child)) {
                    new FileSearchTask(this, child).fork();  // 子目录递归
                } else {
                    // 处理文件...完成后计数 -1
                    tryComplete();  // 或者 propagateCompletion()
                }
            }
        } catch (IOException e) {
            completeExceptionally(e);
        }
    }
}
```

## 应用场景实战

### 场景一：并行斐波那契（教学用）

```java
class FibonacciTask extends RecursiveTask<Long> {
    private final int n;

    FibonacciTask(int n) { this.n = n; }

    @Override
    protected Long compute() {
        if (n <= 1) return (long) n;
        
        FibonacciTask f1 = new FibonacciTask(n - 1);
        f1.fork();
        FibonacciTask f2 = new FibonacciTask(n - 2);
        return f2.compute() + f1.join();
    }
}
// 注意：fork 的合理顺序——f1.fork() + f2.compute() 比两个都 fork 高效
// compute 在当前线程执行，减少一次 fork 开销
```

### 场景二：大规模数组求和

见前面的 SumTask 示例——10M 元素的数组，并行比串行快 3-5 倍（4 核机器）。

### 场景三：并行批量发送消息

```java
public class BatchMessageSender extends RecursiveAction {
    private static final int THRESHOLD = 100;
    private final List<Message> messages;
    private final int start, end;

    @Override
    protected void compute() {
        if (end - start <= THRESHOLD) {
            for (int i = start; i < end; i++) {
                sendMessage(messages.get(i));
            }
            return;
        }
        int mid = (start + end) / 2;
        invokeAll(
            new BatchMessageSender(messages, start, mid),
            new BatchMessageSender(messages, mid, end)
        );
    }
}
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| ForkJoin 性能不如串行 | 任务拆分粒度过细，调度开销大 | 提高阈值，不要让任务太细 |
| 线程池不关闭导致程序挂起 | ForkJoinPool 是守护线程池 | `pool.shutdown()` 或 awaitQuiescence |
| `fork` 后 `join` 死锁 | 在一个任务中等待自己的子任务（递归错） | 确保 fork 的是真正的子任务 |
| `get()` 抛 CancellationException | 任务被取消 | 检查 cancel 逻辑 |

### 使用条件

```
适合 ForkJoin 的场景：
  ✓ 可递归分解（树形结构）
  ✓ 子任务独立无依赖
  ✓ 任务量大（几千以上）
  ✓ 计算密集型（非 IO）

不适合：
  ✗ 单次计算就很小的任务
  ✗ 有数据依赖的任务
  ✗ IO 密集型（阻塞线程）
```

### fork 和 compute 的顺序

```java
// 推荐：一个 fork，一个 compute（高效）
leftTask.fork();
rightResult = rightTask.compute();  // 当前线程做其中一个
leftResult = leftTask.join();

// 不推荐：两个都 fork（低效）
leftTask.fork();
rightTask.fork();
rightResult = rightTask.join();
leftResult = leftTask.join();
// 当前线程什么都没做，浪费了一个线程
```

## 总结

- ForkJoin = 分治并行框架，通过 fork/join 递归拆分合并任务
- ForkJoinPool 为每个线程分配独立的双端队列，支持 Work Stealing 自动负载均衡
- `RecursiveTask<V>` 有返回值，`RecursiveAction` 无返回值
- 拆分阈值要合理——太大没效果，太小调度开销抵消收益
- JDK 8 的 `parallelStream()` 和 `CompletableFuture.supplyAsync()` 底层都是 ForkJoinPool.commonPool()
- 一个 `fork()` 一个 `compute()` 比两个 `fork()` 更高效
