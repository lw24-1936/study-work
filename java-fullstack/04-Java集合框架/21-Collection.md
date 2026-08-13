---
title: Collection
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, collection, framework]
---

# Collection

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [集合框架全景图](#集合框架全景图)
- [Collection 接口](#collection-接口)
- [List 接口](#list-接口)
- [Set 接口](#set-接口)
- [Queue 与 Deque 接口](#queue-与-deque-接口)
- [集合与数组互转](#集合与数组互转)
- [集合遍历方式](#集合遍历方式)
- [Collections 工具类](#collections-工具类)
- [应用场景实战](#应用场景实战)
- [最佳实践与选型指南](#最佳实践与选型指南)

## 概述

Java 集合框架（Java Collections Framework，JCF）是 JDK 1.2 引入的一套统一的数据结构体系。在它出现之前，Java 只有 `Vector`、`Stack`、`Hashtable` 和 `Array`——没有统一的接口，没有算法复用，换一种数据结构就要换一套 API。

集合框架通过接口-抽象类-实现类的三层体系统一了一切：

```
接口（Interface） → 定义行为契约
抽象类（Abstract Class） → 提供通用骨架实现
具体类（Concrete Class） → 完整的数据结构实现
```

核心设计原则：
- **接口与实现分离**：你用 `List` 编程，具体是 `ArrayList` 还是 `LinkedList` 可以随时换
- **算法复用**：`Collections.sort()` 对所有 `List` 有效；`Collections.binarySearch()` 对所有有序集合有效
- **泛型安全**：JDK 5 引入泛型后，编译期就能检查类型错误

## 集合框架全景图

```
                        Iterable
                           |
                    Collection<E>
                    /     |      \
               List<E>  Set<E>  Queue<E>
               /    \    /   \    /    \
         ArrayList  HashSet  PriorityQueue
         LinkedList TreeSet  ArrayDeque
         Vector     LinkedHashSet
         ..

Map 是独立的体系（不继承 Collection）：
                        Map<K,V>
                    /      |      \
              HashMap   TreeMap  Hashtable
              LinkedHashMap      ConcurrentHashMap
              WeakHashMap
              IdentityHashMap
              EnumMap
```

记忆口诀：
- **List**：有序，可重复，按索引访问
- **Set**：无序（大部分），不重复
- **Queue**：先进先出（FIFO），支持优先级
- **Map**：键值对，键不重复

## Collection 接口

`Collection<E>` 是所有单值集合（List/Set/Queue）的根接口：

```java
public interface Collection<E> extends Iterable<E> {
    // 基本操作
    int size();
    boolean isEmpty();
    boolean contains(Object o);
    Iterator<E> iterator();

    // 增删
    boolean add(E e);
    boolean remove(Object o);
    void clear();

    // 批量操作
    boolean addAll(Collection<? extends E> c);
    boolean removeAll(Collection<?> c);        // 差集
    boolean retainAll(Collection<?> c);        // 交集
    boolean containsAll(Collection<?> c);

    // 转数组
    Object[] toArray();
    <T> T[] toArray(T[] a);

    // JDK 8+ 默认方法
    default boolean removeIf(Predicate<? super E> filter) { ... }
    default Stream<E> stream() { ... }
    default Stream<E> parallelStream() { ... }
}
```

### 基本操作演示

```java
Collection<String> c = new ArrayList<>();
c.add("apple");
c.add("banana");
c.add("cherry");

System.out.println(c.size());          // 3
System.out.println(c.contains("apple")); // true
System.out.println(c.isEmpty());       // false

c.remove("banana");
System.out.println(c);                 // [apple, cherry]

// 条件删除（JDK 8+）
c.removeIf(s -> s.startsWith("a"));
System.out.println(c);                 // [cherry]
```

### 集合运算

```java
Collection<String> a = List.of("a", "b", "c", "d");
Collection<String> b = new ArrayList<>(List.of("c", "d", "e", "f"));

// 交集
Collection<String> intersection = new ArrayList<>(a);
intersection.retainAll(b);     // [c, d]

// 并集
Collection<String> union = new ArrayList<>(a);
union.addAll(b);               // [a, b, c, d, c, d, e, f]

// 差集（a - b）
Collection<String> difference = new ArrayList<>(a);
difference.removeAll(b);       // [a, b]
```

## List 接口

`List<E>` 是有序集合，按插入顺序保持元素，支持索引访问和位置操作：

```java
public interface List<E> extends Collection<E> {
    // 索引访问
    E get(int index);
    E set(int index, E element);
    void add(int index, E element);
    E remove(int index);

    // 查找
    int indexOf(Object o);
    int lastIndexOf(Object o);

    // 子列表视图
    List<E> subList(int fromIndex, int toIndex);

    // 迭代器
    ListIterator<E> listIterator();
    ListIterator<E> listIterator(int index);

    // JDK 9+ 静态工厂
    static <E> List<E> of(E... elements) { ... }
    static <E> List<E> copyOf(Collection<? extends E> coll) { ... }
}
```

`List.of()` 返回的是**不可变 List**——不能增删改，null 元素直接抛 NPE。适合用作常量列表。

## Set 接口

`Set<E>` 是不允许重复元素的集合，`equals()` 判定相等：

```java
public interface Set<E> extends Collection<E> {
    // 接口和 Collection 几乎一样，但语义上是"不重复"
    // add 时如果元素已存在，返回 false 并忽略

    static <E> Set<E> of(E... elements) { ... }
    static <E> Set<E> copyOf(Collection<? extends E> coll) { ... }
}

Set<String> set = new HashSet<>();
System.out.println(set.add("apple"));   // true
System.out.println(set.add("apple"));   // false —— 已存在，拒绝
System.out.println(set.add("banana"));  // true
System.out.println(set);                // [apple, banana] 或 [banana, apple]（无序）
```

## Queue 与 Deque 接口

```java
// Queue —— 队列，FIFO
public interface Queue<E> extends Collection<E> {
    // 入队（失败时行为不同）
    boolean add(E e);        // 失败抛异常（如容量满了）
    boolean offer(E e);      // 失败返回 false

    // 出队（队列空时行为不同）
    E remove();              // 空抛 NoSuchElementException
    E poll();                // 空返回 null

    // 查看队首（不移除）
    E element();             // 空抛异常
    E peek();                // 空返回 null
}

// Deque —— 双端队列（两端都能进出），继承 Queue
public interface Deque<E> extends Queue<E> {
    void addFirst(E e);      // 从头部入
    void addLast(E e);       // 从尾部入（同 add）
    E removeFirst();         // 从头部出
    E removeLast();          // 从尾部出
    E peekFirst();
    E peekLast();
    // ... 还有 offer/poll 的非抛异常版本
}
```

Queue 的核心是两套 API：一套抛异常，一套返回特殊值。多数场景用 `offer()`/`poll()`/`peek()` 更安全：

```java
Queue<String> queue = new ArrayDeque<>();
queue.offer("first");
queue.offer("second");
queue.offer("third");

System.out.println(queue.peek());  // first（不取出）
System.out.println(queue.poll());  // first（取出并移除）
System.out.println(queue.poll());  // second
System.out.println(queue.poll());  // third
System.out.println(queue.poll());  // null —— 队列已空
```

## 集合与数组互转

```java
// 数组 → List
String[] arr = {"a", "b", "c"};

// 方式一：Arrays.asList —— 固定大小列表，不能 add/remove
List<String> fixed = Arrays.asList(arr);
fixed.set(0, "x");            // 可以修改元素
// fixed.add("d");            // UnsupportedOperationException！
arr[0] = "changed";           // 和原数组共享数据，改了数组也影响 List

// 方式二：new ArrayList —— 完全独立的可变列表
List<String> dynamic = new ArrayList<>(Arrays.asList(arr));

// 方式三：List.of —— 完全不可变（JDK 9+）
List<String> immutable = List.of("a", "b", "c");

// List → 数组
List<String> list = new ArrayList<>(List.of("a", "b", "c"));

// toArray 的正确用法（预分配数组大小）
String[] array1 = list.toArray(new String[0]);    // JDK 6+ 推荐，更短
String[] array2 = list.toArray(new String[list.size()]); // 性能略好

// 基本类型数组和 List 的互转不直接——需要循环或用 Stream（后面章节会覆盖）
```

## 集合遍历方式

```java
List<String> list = List.of("apple", "banana", "cherry");

// 1. 增强 for（最常用）
for (String item : list) {
    System.out.println(item);
}

// 2. Iterator（需要边遍历边删除时）
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    String item = it.next();
    if (item.startsWith("a")) {
        it.remove();          // 安全删除
    }
}

// 3. 传统 for —— 只在需要索引时用
for (int i = 0; i < list.size(); i++) {
    System.out.println(i + ": " + list.get(i));
    // 注意：LinkedList 的 get(i) 是 O(n)，用这个循环会变成 O(n^2)
}

// 4. forEach（JDK 8+）
list.forEach(item -> System.out.println(item));
list.forEach(System.out::println);     // 方法引用

// 5. Stream（JDK 8+）
list.stream()
    .filter(s -> s.length() > 5)
    .map(String::toUpperCase)
    .forEach(System.out::println);
```

关键规则：**遍历时删除元素必须用迭代器的 `remove()`**，增强 for 里直接调 `list.remove()` 会抛 `ConcurrentModificationException`。

## Collections 工具类

`java.util.Collections` 提供静态工具方法，操作 Collection/List/Set/Map：

```java
List<Integer> list = new ArrayList<>(List.of(3, 1, 4, 1, 5, 9, 2, 6));

// 排序与查找
Collections.sort(list);                    // [1, 1, 2, 3, 4, 5, 6, 9]
Collections.reverse(list);                 // [9, 6, 5, 4, 3, 2, 1, 1]
Collections.shuffle(list);                 // 随机打乱
Collections.swap(list, 0, 1);              // 交换

// 极值
Integer min = Collections.min(list);       // 最小值
Integer max = Collections.max(list);       // 最大值

// 查找（list 必须先排序）
Collections.sort(list);
int idx = Collections.binarySearch(list, 4);   // 返回索引

// 线程安全的包装视图
List<Integer> syncList = Collections.synchronizedList(new ArrayList<>());
Set<String> syncSet = Collections.synchronizedSet(new HashSet<>());
Map<String, String> syncMap = Collections.synchronizedMap(new HashMap<>());

// 不可变包装视图
List<Integer> unmodifiable = Collections.unmodifiableList(list);
// unmodifiable.add(10);   // UnsupportedOperationException

// 填充
Collections.fill(list, 0);                 // 所有元素变成 0

// 频次
int freq = Collections.frequency(list, 1); // 元素出现的次数

// 空集合（不可变）
List<String> emptyList = Collections.emptyList();
Set<Integer> emptySet = Collections.emptySet();
Map<String, Integer> emptyMap = Collections.emptyMap();
```

## 应用场景实战

### 场景一：去重 + 保持原始顺序

```java
// LinkedHashSet 保持插入顺序同时去重
List<String> names = List.of("张三", "李四", "张三", "王五", "李四");
List<String> unique = new ArrayList<>(new LinkedHashSet<>(names));
System.out.println(unique);  // [张三, 李四, 王五]
```

### 场景二：求两个列表的差集（新增、删除）

```java
public class ListDiff<T> {
    public static <T> List<T> added(List<T> oldList, List<T> newList) {
        List<T> result = new ArrayList<>(newList);
        result.removeAll(oldList);
        return result;
    }

    public static <T> List<T> removed(List<T> oldList, List<T> newList) {
        List<T> result = new ArrayList<>(oldList);
        result.removeAll(newList);
        return result;
    }
}
```

### 场景三：LRU 缓存的简单实现

```java
// 利用 LinkedHashMap 的 access-order 模式（后面 Map 章节会详细讲）
// 这里先给一个 Collections 版本的概念
public class SimpleLRU<K, V> {
    private final int capacity;
    private final Map<K, V> cache = new LinkedHashMap<>(16, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity;
        }
    };

    public SimpleLRU(int capacity) { this.capacity = capacity; }
    public V get(K key) { return cache.get(key); }
    public void put(K key, V value) { cache.put(key, value); }
}
```

### 场景四：统计词频

```java
public Map<String, Integer> wordFrequency(List<String> words) {
    Map<String, Integer> freq = new HashMap<>();
    for (String word : words) {
        freq.merge(word, 1, Integer::sum);  // JDK 8+ —— 如果 key 不存在就放 1，否则加 1
    }
    return freq;
}
```

## 最佳实践与选型指南

### 集合选型决策树

```
是否需要键值对？
  ├── 是 → Map
  │     ├── 需要排序？ → TreeMap
  │     ├── 需要保持插入顺序？ → LinkedHashMap
  │     ├── 需要线程安全？ → ConcurrentHashMap
  │     └── 通用 → HashMap
  └── 否 → Collection
        ├── 需要不重复？ → Set
        │     ├── 需要排序？ → TreeSet
        │     ├── 需要保持插入顺序？ → LinkedHashSet
        │     └── 通用 → HashSet
        ├── 需要队列（FIFO）？ → Queue/Deque
        │     ├── 双端操作？ → ArrayDeque
        │     └── 优先级？ → PriorityQueue
        └── 需要按索引访问？ → List
              ├── 频繁随机访问？ → ArrayList
              ├── 频繁头尾增删？ → LinkedList
              └── 线程安全？ → CopyOnWriteArrayList
```

### 常见错误

| 错误 | 后果 | 修复 |
|------|------|------|
| `Arrays.asList` 返回的 List 调 `add()/remove()` | UnsupportedOperationException | 包一层 `new ArrayList<>(Arrays.asList(...))` |
| 遍历中 `list.remove()` 或 `list.add()` | ConcurrentModificationException | 用 `Iterator.remove()` 或先收集再处理 |
| `List` 存基本类型 | 自动装箱到包装类，性能差 | 大量基本类型用数组或第三方库（Trove、fastutil） |
| 大 `LinkedList` 用 `get(i)` 遍历 | O(n^2) 性能灾难 | LinkedList 只用增强 for / Iterator |
| `synchronizedList` 的迭代仍需手动同步 | 并发修改导致异常 | 迭代时加 `synchronized(list)` 块 |

### 不可变集合

```java
// JDK 9+ 静态工厂 —— 推荐
List<String> list = List.of("a", "b", "c");
Set<Integer> set = Set.of(1, 2, 3);
Map<String, Integer> map = Map.of("k1", 1, "k2", 2);

// JDK 10+ copyOf
List<String> copy = List.copyOf(existingCollection);

// 这些集合：
// - 不可修改（add/remove/clear 全抛异常）
// - 拒绝 null 元素
// - 线程安全（不可变天然安全）
// - 空间更紧凑（专门实现，不是包装视图）
```

## 总结

- `Collection` 是 List/Set/Queue 的根接口，`Map` 独立体系
- 面向接口编程：声明用 `List`/`Map`，只在构造时指定具体实现
- 遍历时删除用 `Iterator.remove()`，不要直接调集合的 remove/add
- `Arrays.asList` 返回固定大小的视图，要可变就 new ArrayList 包一层
- `Collections` 工具类提供排序、查找、同步包装、不可变视图——都是视图，不是复制
- 选集合先问四个问题：键值对？可重复？有序？线程安全？——对照决策树秒选
