---
title: Queue
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, collection, queue, deque, priorityqueue]
---

# Queue

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Queue 接口](#queue-接口)
- [Deque 接口（双端队列）](#deque-接口双端队列)
- [ArrayDeque](#arraydeque)
- [PriorityQueue](#priorityqueue)
- [BlockingQueue 概览](#blockingqueue-概览)
- [队列选型对比](#队列选型对比)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`Queue`（队列）是 FIFO（先进先出）的数据结构。Java 的队列体系围绕 `Queue` 和 `Deque` 两个核心接口展开，提供了从无界到有界、从非阻塞到阻塞的完整实现。

Java 队列全景：

```
Queue<E>                          ← FIFO 队列
├── Deque<E>                      ← 双端队列（两端都能进出）
│   ├── ArrayDeque               ← 循环数组，最常用的栈/队列
│   └── LinkedList               ← 双向链表，同时是 List 和 Deque
├── PriorityQueue                 ← 二叉堆，按优先级出队
└── BlockingQueue<E>              ← 阻塞队列（并发）
    ├── ArrayBlockingQueue        ← 有界，数组
    ├── LinkedBlockingQueue       ← 可选有界，链表
    ├── PriorityBlockingQueue     ← 无界，优先级
    ├── DelayQueue                ← 延迟队列
    └── SynchronousQueue          ← 无容量，直接传递
```

## Queue 接口

Queue 有两套方法——一套抛异常，一套返回特殊值：

| 操作 | 抛异常版本 | 返回特殊值版本 |
|------|-----------|----------------|
| 入队 | `add(e)` | `offer(e)` —— 失败返回 false |
| 出队 | `remove()` | `poll()` —— 空返回 null |
| 查看队首 | `element()` | `peek()` —— 空返回 null |

```java
Queue<String> queue = new ArrayDeque<>();

// 入队
queue.offer("first");
queue.offer("second");
queue.offer("third");

// 查看队首（不移除）
System.out.println(queue.peek());  // first
System.out.println(queue.peek());  // first —— 还在

// 出队
System.out.println(queue.poll());  // first（移除）
System.out.println(queue.poll());  // second
System.out.println(queue.poll());  // third
System.out.println(queue.poll());  // null —— 队列已空

// 如果用 remove()，空队列会抛 NoSuchElementException
```

## Deque 接口（双端队列）

`Deque` 在 Queue 的基础上增加了两端操作：

```java
Deque<String> deque = new ArrayDeque<>();

// 头部操作
deque.addFirst("head1");           // 抛异常版
deque.offerFirst("head2");         // 返回 boolean 版
String h = deque.removeFirst();    // 抛异常版
String h2 = deque.pollFirst();     // 返回 null 版
String h3 = deque.getFirst();      // 查看头部（抛异常）
String h4 = deque.peekFirst();     // 查看头部（返回 null）

// 尾部操作（和 Queue 的那套一致）
deque.addLast("tail");             // 同 add
deque.offerLast("tail2");          // 同 offer
deque.removeLast();                // 尾部移除（抛异常）
deque.pollLast();                  // 尾部移除（返回 null）
deque.getLast();                   // 查看尾部（抛异常）
deque.peekLast();                  // 查看尾部（返回 null）

// 栈操作
deque.push("top");                 // addFirst
String top = deque.pop();          // removeFirst
```

### Deque 作为栈

JDK 官方推荐用 `ArrayDeque` 替代 `Stack`：

```java
// 旧（不推荐）
Stack<String> stack = new Stack<>();

// 新（推荐）
Deque<String> stack = new ArrayDeque<>();
stack.push("a");
stack.push("b");
stack.push("c");
while (!stack.isEmpty()) {
    System.out.println(stack.pop());  // c, b, a
}
```

## ArrayDeque

`ArrayDeque` 是 JDK 6 引入的循环数组实现的双端队列——没有容量限制，所有操作 O(1)：

```java
ArrayDeque<String> deque = new ArrayDeque<>();
// 默认容量 16，自动扩容（翻倍）

// 队列入队
deque.offer("a");
deque.offer("b");
// 栈操作
deque.push("c");

System.out.println(deque);  // [c, a, b]（顺序取决于操作）

// 不允许 null 元素
// deque.offer(null);  // NullPointerException
```

内部是循环数组：
```
head → [c] [a] [b] [ ] [ ] [ ] [ ] [ ] ← tail
```

扩容：当 head 和 tail 相遇时，新容量 = 旧容量 × 2（且必须为 2 的幂）。

优点：比 `LinkedList` 快（连续内存，无节点对象开销），比 `Stack` 规范，比 `ArrayList` 更适合队列操作。

## PriorityQueue

`PriorityQueue` 是基于**二叉堆**的优先级队列——出队顺序由元素的优先级决定，不是插入顺序：

```java
// 最小堆（默认）
PriorityQueue<Integer> pq = new PriorityQueue<>();
pq.offer(5);
pq.offer(1);
pq.offer(3);
pq.offer(2);

while (!pq.isEmpty()) {
    System.out.print(pq.poll() + " ");  // 1 2 3 5 —— 从小到大出队
}

// 最大堆（自定义 Comparator）
PriorityQueue<Integer> maxHeap = new PriorityQueue<>(Comparator.reverseOrder());
maxHeap.offer(5);
maxHeap.offer(1);
maxHeap.offer(3);
while (!maxHeap.isEmpty()) {
    System.out.print(maxHeap.poll() + " ");  // 5 3 1
}
```

内部结构：

```
        1              ← 根最小
      /   \
     2     3
    /
   5

数组表示：[1, 2, 3, 5]
父节点索引 = (i-1)/2
左子节点 = 2i+1
右子节点 = 2i+2
```

时间复杂度：
- `offer` / `poll`：O(log n)
- `peek`：O(1)
- `remove(Object)`：O(n)（需要遍历查找）

### 自定义优先级

```java
public class Task implements Comparable<Task> {
    private String name;
    private int priority;  // 数字越小优先级越高

    @Override
    public int compareTo(Task other) {
        return Integer.compare(this.priority, other.priority);
    }
}

PriorityQueue<Task> pq = new PriorityQueue<>();
pq.offer(new Task("紧急任务", 1));
pq.offer(new Task("普通任务", 5));
pq.offer(new Task("重要任务", 3));

Task next = pq.poll();  // 紧急任务（priority=1）
```

注意：PriorityQueue 的迭代顺序**不保证**按优先级——只有 `poll()`/`peek()` 保证拿到优先级最高的。遍历时用 `poll()` 循环（会清空队列），或者先转数组排序。

## BlockingQueue 概览

`BlockingQueue` 是并发队列的核心——线程安全的队列，支持阻塞操作：

```java
// 阻塞队列的核心方法
public interface BlockingQueue<E> extends Queue<E> {
    void put(E e) throws InterruptedException;       // 入队，满时阻塞
    E take() throws InterruptedException;            // 出队，空时阻塞
    boolean offer(E e, long timeout, TimeUnit unit); // 入队，满时等待超时
    E poll(long timeout, TimeUnit unit);             // 出队，空时等待超时
    int remainingCapacity();                         // 剩余容量
    int drainTo(Collection<? super E> c);            // 批量排出
}
```

常用实现：

```java
// ArrayBlockingQueue —— 有界，数组，需要指定容量
BlockingQueue<String> abq = new ArrayBlockingQueue<>(100);
abq.put("item");           // 满则阻塞
String item = abq.take();  // 空则阻塞

// LinkedBlockingQueue —— 可选有界（默认 Integer.MAX_VALUE，约等于无界）
BlockingQueue<String> lbq = new LinkedBlockingQueue<>(1000);

// PriorityBlockingQueue —— 无界，按优先级出队，线程安全
BlockingQueue<Integer> pbq = new PriorityBlockingQueue<>();

// SynchronousQueue —— 容量为 0，put 必须等 take（直接传递）
BlockingQueue<String> sq = new SynchronousQueue<>();
// 线程 A: sq.put("data");   // 阻塞直到线程 B 取走
// 线程 B: sq.take();       // 阻塞直到线程 A 放入

// DelayQueue —— 元素实现 Delayed 接口，到期后才能取出
// 常用作定时任务调度
```

BlockingQueue 是生产者-消费者模式的基石，也是线程池任务队列的核心（ThreadPoolExecutor 内部用的就是 BlockingQueue）。

## 队列选型对比

| 实现 | 有界？ | 线程安全？ | 数据结构 | 典型场景 |
|------|--------|-----------|----------|----------|
| `ArrayDeque` | 否 | 否 | 循环数组 | 普通队列/栈 |
| `LinkedList` | 否 | 否 | 双向链表 | 需要 List + Deque 双能力 |
| `PriorityQueue` | 否 | 否 | 二叉堆 | 任务调度、Top K |
| `ArrayBlockingQueue` | 是 | 是 | 数组 | 生产者消费者 |
| `LinkedBlockingQueue` | 可选 | 是 | 链表 | Executor 默认队列 |
| `SynchronousQueue` | 是(0) | 是 | 无存储 | 直接交付 |
| `DelayQueue` | 否 | 是 | PriorityQueue | 定时任务、缓存过期 |

## 应用场景实战

### 场景一：BFS 广度优先搜索

```java
public class BFS {
    public static <T> Optional<T> search(T start, 
                                          Function<T, List<T>> neighbors,
                                          Predicate<T> isTarget) {
        Set<T> visited = new HashSet<>();
        Queue<T> queue = new ArrayDeque<>();
        queue.offer(start);
        visited.add(start);

        while (!queue.isEmpty()) {
            T current = queue.poll();
            if (isTarget.test(current)) {
                return Optional.of(current);
            }
            for (T next : neighbors.apply(current)) {
                if (visited.add(next)) {
                    queue.offer(next);
                }
            }
        }
        return Optional.empty();
    }
}
```

### 场景二：生产者-消费者（BlockingQueue）

```java
public class ProducerConsumer {
    private final BlockingQueue<String> queue = new LinkedBlockingQueue<>(10);

    public void startProducer() {
        new Thread(() -> {
            try {
                for (int i = 0; i < 100; i++) {
                    String item = "Item-" + i;
                    queue.put(item);   // 满了阻塞
                    System.out.println("生产: " + item);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }).start();
    }

    public void startConsumer() {
        new Thread(() -> {
            try {
                while (true) {
                    String item = queue.take();   // 空了阻塞
                    System.out.println("消费: " + item);
                    Thread.sleep(500);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }).start();
    }
}
```

### 场景三：Top K 问题

```java
// 找最大的 K 个数（用小顶堆）
public static List<Integer> topK(List<Integer> nums, int k) {
    PriorityQueue<Integer> minHeap = new PriorityQueue<>(k);
    for (int num : nums) {
        minHeap.offer(num);
        if (minHeap.size() > k) {
            minHeap.poll();  // 超出 k 个，移除最小的
        }
    }
    // 剩下的 k 个就是最大的 k 个（但堆内是最小堆顺序）
    List<Integer> result = new ArrayList<>(minHeap);
    result.sort(Comparator.reverseOrder());
    return result;
}

// 找第 K 大的元素
public static int kthLargest(List<Integer> nums, int k) {
    PriorityQueue<Integer> minHeap = new PriorityQueue<>();
    for (int num : nums) {
        minHeap.offer(num);
        if (minHeap.size() > k) {
            minHeap.poll();
        }
    }
    return minHeap.peek();  // k 个最大的中最小的 = 第 k 大
}
```

### 场景四：滑动窗口最大值

```java
// 用双端队列 O(n) 求滑动窗口内的最大值
public static int[] maxSlidingWindow(int[] nums, int k) {
    if (nums.length == 0 || k == 0) return new int[0];
    int[] result = new int[nums.length - k + 1];
    Deque<Integer> deque = new ArrayDeque<>();  // 存索引，保持递减

    for (int i = 0; i < nums.length; i++) {
        // 移除超出窗口范围的
        while (!deque.isEmpty() && deque.peekFirst() <= i - k) {
            deque.pollFirst();
        }
        // 维护递减：小于当前值的都没有用了
        while (!deque.isEmpty() && nums[deque.peekLast()] <= nums[i]) {
            deque.pollLast();
        }
        deque.offerLast(i);
        // 窗口已形成
        if (i >= k - 1) {
            result[i - k + 1] = nums[deque.peekFirst()];
        }
    }
    return result;
}
```

## 最佳实践与踩坑记录

### 选型指南

| 场景 | 推荐 |
|------|------|
| 普通队列 | `ArrayDeque` |
| 普通栈 | `ArrayDeque`（替代 Stack） |
| 优先级/TOP K | `PriorityQueue` |
| 生产者消费者 | `ArrayBlockingQueue` 或 `LinkedBlockingQueue` |
| 线程池任务队列 | `LinkedBlockingQueue`（默认）或 `SynchronousQueue`（CachedThreadPool） |
| 需要 List + 队列双身份 | `LinkedList` |

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| PriorityQueue 迭代顺序不对 | 迭代器不保证优先级顺序 | 用 poll() 循环取出，或排序后遍历 |
| `ArrayDeque.offer(null)` 抛 NPE | ArrayDeque 不允许 null | 用 Optional 包装或用特殊值标记 |
| LinkedList 做队列比 ArrayDeque 慢 | 节点对象开销 + 缓存不友好 | 用 ArrayDeque |
| `Stack` 的 `pop()` 不是 FIFO | Stack 是 LIFO，继承自 Vector | 用 ArrayDeque 的 push/pop |
| PriorityQueue 中修改元素属性 | 堆结构被破坏 | 先 remove 再 add，或只用不可变元素 |

### 关键建议

- **默认用 ArrayDeque**：代替 Stack（更快），代替 LinkedList（队列场景，更省内存）
- **PriorityQueue 要确保元素不可变**：放入后不要修改影响 compareTo 的字段
- **BlockingQueue 的 put/take 会阻塞**：不要在主线程中调用，用 offer/poll + 超时更可控
- **生产者消费者中注意结束信号**：常用"毒丸"（特殊对象）或 `Thread.interrupt()`

## 总结

- Queue = 抛异常版（add/remove/element）vs 返回特殊值版（offer/poll/peek）
- Deque 是双端队列，ArrayDeque 是最佳通用实现——队列 + 栈都不在话下
- PriorityQueue 二叉堆实现，O(log n) 出队，适合 Top K 和任务调度
- BlockingQueue 是并发队列的核心——put/take 阻塞，生产者消费者基石
- ArrayDeque 替代 Stack，BlockingQueue 选型看是否需要有界/阻塞/优先级
