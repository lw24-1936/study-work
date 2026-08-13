---
title: List
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, collection, list, arraylist, linkedlist]
---

# List

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [ArrayList](#arraylist)
- [LinkedList](#linkedlist)
- [Vector 与 Stack](#vector-与-stack)
- [CopyOnWriteArrayList](#copyonwritearraylist)
- [ArrayList vs LinkedList 性能对比](#arraylist-vs-linkedlist-性能对比)
- [遍历方式选择](#遍历方式选择)
- [子列表与视图](#子列表与视图)
- [排序与自定义比较](#排序与自定义比较)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`List` 是有序集合——元素按插入顺序排列，允许重复，支持索引访问。Java 提供四种主要实现：

| 实现类 | 底层结构 | 随机访问 | 增删效率 | 线程安全 | 特性 |
|--------|----------|----------|----------|----------|------|
| `ArrayList` | 动态数组 | O(1) | 尾部 O(1)，中间 O(n) | 否 | 最常用，读多写少 |
| `LinkedList` | 双向链表 | O(n) | 头尾 O(1)，中间 O(n) | 否 | 实现了 Deque，可作队列/栈 |
| `Vector` | 动态数组 | O(1) | 同 ArrayList | 是（synchronized） | 遗留类，不推荐 |
| `CopyOnWriteArrayList` | 数组 + 写时复制 | O(1) | O(n)（复制整个数组） | 是 | 读多写极少场景 |

## ArrayList

`ArrayList` 是使用最广泛的 List 实现。底层是一个 `Object[]`，容量不够时自动扩容。

```java
import java.util.ArrayList;
import java.util.List;

// 创建
List<String> list = new ArrayList<>();            // 默认容量 10
List<String> list2 = new ArrayList<>(100);        // 指定初始容量
List<String> list3 = new ArrayList<>(list2);      // 复制另一个集合

// 基本 CRUD
list.add("apple");                                // 尾部追加
list.add(0, "first");                             // 指定位置插入
String item = list.get(2);                        // 按索引取
list.set(1, "updated");                           // 更新
list.remove(0);                                   // 按索引删除
list.remove("apple");                             // 按值删除（第一个匹配）
boolean exists = list.contains("apple");          // 是否存在
int idx = list.indexOf("apple");                  // 首次出现位置

// 批量操作
list.addAll(List.of("x", "y", "z"));
list.removeAll(List.of("x", "y"));                // 删除交集
list.retainAll(List.of("z"));                     // 只保留交集
```

### 扩容机制

```java
// ArrayList 内部
public boolean add(E e) {
    // ensureCapacityInternal(size + 1);  // 先检查容量
    // elementData[size++] = e;           // 再追加
}
```

扩容流程：
1. 第一次添加：如果没指定容量，默认**空数组**（JDK 7+ 改为懒初始化），第一次添加时扩容到 10
2. 容量不足时：新容量 = 旧容量 × 1.5（`oldCapacity + (oldCapacity >> 1)`）
3. 通过 `Arrays.copyOf` 把旧数组复制到新数组

```java
// 如果提前知道大概元素数量，指定初始容量避免多次扩容
List<String> list = new ArrayList<>(10000);
```

### 裁剪到实际大小

```java
ArrayList<String> list = new ArrayList<>(100);  // 容量 100
list.add("a");
list.add("b");
list.trimToSize();                               // 容量缩减到 2
```

## LinkedList

`LinkedList` 基于双向链表，实现了 `List` 和 `Deque` 两个接口——既可以当 List 用，也可以当队列或栈用：

```java
import java.util.LinkedList;

LinkedList<String> list = new LinkedList<>();

// List 操作（和 ArrayList 一样的 API）
list.add("first");
list.add("second");
list.get(0);      // 注意：O(n)！

// Deque 操作（队列/双端队列）
list.addFirst("head");        // 头部插入
list.addLast("tail");         // 尾部插入（同 add）
String first = list.removeFirst();  // 头部移除
String last  = list.removeLast();   // 尾部移除

// Queue 操作
list.offer("item");     // 入队（尾部）
String item = list.poll();  // 出队（头部）
String peek = list.peek();  // 查看头部（不移除）

// 栈操作（JDK 6+ 推荐用 Deque 替代 Stack）
list.push("top");        // 压栈（addFirst）
String top = list.pop(); // 弹栈（removeFirst）
```

LinkedList 的节点结构：

```
Node {
    E item;
    Node<E> next;
    Node<E> prev;
}
```

每个节点有 3 个引用，内存开销大，而且链表节点分散在堆中，缓存不友好。

## Vector 与 Stack

`Vector` 是 JDK 1.0 就存在的"线程安全版 ArrayList"。`Stack` 继承自 Vector，是 LIFO 栈。

```java
Vector<String> vector = new Vector<>();
vector.add("a");
vector.addElement("b");     // 遗留方法，等价于 add
String first = vector.firstElement();
String last  = vector.lastElement();

Stack<String> stack = new Stack<>();
stack.push("bottom");
stack.push("middle");
stack.push("top");
String popped = stack.pop();    // "top"
String peeked = stack.peek();   // "middle"（不弹出）
```

为什么不推荐：
- 所有方法都用 `synchronized` 修饰，粒度太粗，性能差
- `Stack` 继承 `Vector` 违反了"is-a"原则——栈不是向量，不应该继承那些索引访问方法
- JDK 1.2 以后有更好的选择：需要线程安全用 `Collections.synchronizedList` 或 `CopyOnWriteArrayList`，需要栈用 `ArrayDeque`

```java
// 栈的正确替代
Deque<String> stack = new ArrayDeque<>();
stack.push("bottom");
stack.push("top");
String top = stack.pop();  // "top"
```

## CopyOnWriteArrayList

适合**读多写极少**的并发场景——读操作无锁，写操作加锁并复制整个数组：

```java
import java.util.concurrent.CopyOnWriteArrayList;

CopyOnWriteArrayList<String> list = new CopyOnWriteArrayList<>();
list.add("a");
list.add("b");

// 读操作——无锁，O(1)，极快
String s = list.get(0);
boolean has = list.contains("a");

// 写操作——加 ReentrantLock，复制整个数组，O(n)
list.add("c");          // 拿到锁 → 复制数组 → 追加 → 替换引用 → 释放锁
list.remove("a");       // 同上

// 迭代器是"快照"——遍历时看到的是创建迭代器那一刻的数据
// 其他线程的写操作不会影响当前迭代
for (String item : list) {
    list.add("new");    // 不影响本次迭代！
    System.out.println(item);
}
```

**使用场景**：
- 黑名单、白名单（读多写少）
- 事件监听器列表（注册/注销频率低，遍历频率高）
- 配置信息缓存

**绝对不要**在写频繁的场景用——每次 `add` 都复制整个数组，数据量越大越灾难。

## ArrayList vs LinkedList 性能对比

```java
// 尾部追加 —— 都是 O(1)
// ArrayList 偶尔扩容，均摊 O(1)；LinkedList 新建节点 O(1)

// 头部插入 —— ArrayList O(n)，LinkedList O(1)
list.add(0, item);

// 中间插入 —— 都是 O(n)
// ArrayList：移动元素 O(n)；LinkedList：遍历到位置 O(n) + 插节点 O(1)

// 随机访问 —— ArrayList O(1)，LinkedList O(n)
list.get(5000);

// 遍历 —— ArrayList 优于 LinkedList
// ArrayList 连续内存，CPU 缓存友好
// LinkedList 节点分散，每次访问都要跟踪引用
```

实测结论（百万级数据）：
- 随机访问 `get(i)`：ArrayList 完胜（纳秒级 vs 毫秒级）
- 遍历：ArrayList 快 3-5 倍（连续内存 vs 随机访问）
- 头部插入/删除：LinkedList 胜
- **大部分实际场景**：ArrayList 是更好的默认选择。LinkedList 只有在你明确需要频繁头尾操作 + 不需要随机访问时才考虑。

## 遍历方式选择

```java
List<String> list = new ArrayList<>();  // 100 万元素

// 1. 增强 for（最终编译成 Iterator）—— 最通用，性能好
for (String s : list) { }

// 2. Iterator —— 需要边遍历边删除时
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    if (someCondition(it.next())) {
        it.remove();
    }
}

// 3. 传统 for（按索引）—— ArrayList 可以，LinkedList 是灾难
for (int i = 0; i < list.size(); i++) {
    String s = list.get(i);   // LinkedList 每次 get 都要从头遍历，O(n^2)！
}

// 4. forEach + Lambda —— 简洁，但不能抛 checked exception
list.forEach(System.out::println);

// 5. Stream —— 需要过滤/转换时用
list.stream().filter(s -> s.length() > 3).forEach(System.out::println);
```

## 子列表与视图

`subList(from, to)` 返回的是原始列表的**视图**，不是独立副本：

```java
List<Integer> list = new ArrayList<>(List.of(1, 2, 3, 4, 5));
List<Integer> sub = list.subList(1, 4);    // [2, 3, 4]（视图！）

sub.set(0, 99);
System.out.println(list);   // [1, 99, 3, 4, 5] —— 原列表也被改了！

list.set(2, 88);
System.out.println(sub);    // [99, 88, 4] —— 子列表跟着变

// 子列表上的结构性修改会导致原列表失效
// sub.add(100); // 原列表的 modCount 变了
// list.get(0);  // 再次访问原列表会抛 ConcurrentModificationException
```

如果需要独立副本：

```java
List<Integer> copy = new ArrayList<>(list.subList(1, 4));
```

## 排序与自定义比较

```java
List<User> users = new ArrayList<>();
users.add(new User("张三", 25));
users.add(new User("李四", 30));
users.add(new User("王五", 20));

// 方式一：User 实现 Comparable
class User implements Comparable<User> {
    private String name;
    private int age;

    @Override
    public int compareTo(User other) {
        return Integer.compare(this.age, other.age);  // 按年龄升序
    }
}

Collections.sort(users);   // 或用 list.sort(null)

// 方式二：Comparator（不需要修改 User 类）
users.sort((u1, u2) -> u1.getName().compareTo(u2.getName()));           // 按姓名
users.sort(Comparator.comparing(User::getAge));                          // 按年龄
users.sort(Comparator.comparing(User::getAge).reversed());               // 按年龄降序
users.sort(Comparator.comparing(User::getAge).thenComparing(User::getName)); // 年龄相同再比姓名

// 方式三：null 处理
users.sort(Comparator.nullsLast(Comparator.comparing(User::getAge)));    // null 排最后
users.sort(Comparator.nullsFirst(Comparator.comparing(User::getAge)));   // null 排最前
```

## 应用场景实战

### 场景一：分页工具

```java
public class PageUtil {
    public static <T> List<T> paginate(List<T> list, int page, int pageSize) {
        if (page < 1 || pageSize < 1) {
            throw new IllegalArgumentException("页码和页大小必须为正数");
        }
        int from = (page - 1) * pageSize;
        if (from >= list.size()) {
            return List.of();
        }
        int to = Math.min(from + pageSize, list.size());
        return new ArrayList<>(list.subList(from, to));
    }
}

// 用法
List<String> page2 = PageUtil.paginate(totalList, 2, 10);
```

### 场景二：批量处理（分批）

```java
public class BatchUtil {
    public static <T> void processInBatches(List<T> list, int batchSize, 
                                             Consumer<List<T>> processor) {
        for (int i = 0; i < list.size(); i += batchSize) {
            int end = Math.min(i + batchSize, list.size());
            List<T> batch = list.subList(i, end);
            processor.accept(new ArrayList<>(batch));  // 副本，避免并发问题
        }
    }
}

// 用法：每 100 条处理一次
BatchUtil.processInBatches(largeList, 100, batch -> {
    repository.batchInsert(batch);
});
```

### 场景三：不可变列表缓存

```java
public class ListCache<K, V> {
    private final Map<K, List<V>> cache = new ConcurrentHashMap<>();

    public void put(K key, List<V> values) {
        // 存入不可变副本，防止外部修改
        cache.put(key, List.copyOf(values));
    }

    public List<V> get(K key) {
        return cache.getOrDefault(key, List.of());
    }
}
```

### 场景四：去重保持顺序

```java
// ArrayList 直接去重（O(n^2) —— 每次 contains 都要扫描）
public static <T> List<T> deduplicate(List<T> list) {
    List<T> result = new ArrayList<>();
    for (T item : list) {
        if (!result.contains(item)) {
            result.add(item);
        }
    }
    return result;
}

// 更好的方式（O(n)）—— 用 LinkedHashSet
public static <T> List<T> deduplicateFast(List<T> list) {
    return new ArrayList<>(new LinkedHashSet<>(list));
}
```

## 最佳实践与踩坑记录

### 选型指南

| 场景 | 推荐 | 原因 |
|------|------|------|
| 默认选择 | `ArrayList` | 性能好，够用 |
| 频繁头尾增删 + 不需要索引 | `LinkedList` | 但还要考虑内存开销 |
| 读多写极少 + 并发 | `CopyOnWriteArrayList` | 写时复制，读无锁 |
| 固定大小的常量列表 | `List.of(...)` | 不可变，内存小 |
| 已知大致数量 | `new ArrayList<>(N)` | 避免扩容 |

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `Arrays.asList(arr).add()` 抛异常 | asList 返回固定大小列表 | `new ArrayList<>(Arrays.asList(arr))` |
| `subList` 修改后原列表无法访问 | subList 的非结构性修改会影响原列表的 modCount | subList 用完就复制一份 |
| `for (int i=0; i<list.size(); i++) { list.remove(i); }` | 删除后索引移位，部分元素被跳过 | 用 Iterator 或从后往前删 |
| `for (String s : list) { list.remove(s); }` | 增强 for 中修改集合 | 用 `Iterator.remove()` 或 `removeIf()` |
| `ArrayList` 频繁中间插入 | O(n) 元素移动 | 考虑 LinkedList 或重新设计数据结构 |

### 线程安全

```java
// ArrayList 自身不是线程安全的
// 临时需要线程安全，用包装视图（但要明白这只是方法级的同步）
List<String> syncList = Collections.synchronizedList(new ArrayList<>());

// synchronizedList 的迭代仍需要手动加锁
synchronized (syncList) {
    for (String s : syncList) {
        // ...
    }
}
```

### Stream 与 List 的互操作

```java
// 收集到 List
List<String> result = stream.collect(Collectors.toList());        // 可变 ArrayList
List<String> unmod = stream.collect(Collectors.toUnmodifiableList()); // JDK 10+ 不可变

// 收集到特定 List 实现
LinkedList<String> linked = stream.collect(Collectors.toCollection(LinkedList::new));
```

## 总结

- `ArrayList` 是默认选择——动态数组，读 O(1)，写尾 O(1)，写中 O(n)
- `LinkedList` 既是 List 也是 Deque——头尾增删 O(1)，随机访问 O(n)，内存开销大
- 遍历 LinkedList 用增强 for/Iterator，绝对不要用 `get(i)` 循环
- `Vector`/`Stack` 是遗留类，用 `ArrayList`/`ArrayDeque` 替代
- `CopyOnWriteArrayList` 读多写极少场景的并发利器——写时复制全数组
- `subList` 是视图不是副本，用完尽快复制；`Arrays.asList` 返回固定大小列表
- JDK 9+ 用 `List.of()` 创建不可变列表，简洁且安全
