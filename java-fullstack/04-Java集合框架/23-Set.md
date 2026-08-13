---
title: Set
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, collection, set, hashset, treeset]
---

# Set

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [HashSet](#hashset)
- [LinkedHashSet](#linkedhashset)
- [TreeSet](#treeset)
- [EnumSet](#enumset)
- [Set 实现对比](#set-实现对比)
- [equals 与 hashCode 契约](#equals-与-hashcode-契约)
- [SortedSet 与 NavigableSet](#sortedset-与-navigableset)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`Set` 是不允许重复元素的集合——`equals()` 判定相等的两个对象不能同时存在于同一个 Set 中。核心特性：

- **不允许重复**：`add()` 一个已存在元素返回 `false`
- **null 支持**：`HashSet`/`LinkedHashSet` 允许一个 null，`TreeSet` 不允许（因为需要比较）
- **不保证顺序**：`HashSet` 不保证；`LinkedHashSet` 按插入顺序；`TreeSet` 按自然排序或 Comparator

四种常用实现：

| 实现类 | 底层结构 | 顺序 | 基本操作复杂度 | null |
|--------|----------|------|----------------|------|
| `HashSet` | `HashMap`（key 存元素，value 是 dummy） | 无序 | O(1) | 允许一个 |
| `LinkedHashSet` | `LinkedHashMap` | 插入顺序 | O(1) | 允许一个 |
| `TreeSet` | `TreeMap`（红黑树） | 排序 | O(log n) | 不允许 |
| `EnumSet` | 位向量 | 枚举声明顺序 | O(1)（位运算） | 不允许 |

## HashSet

`HashSet` 是最常用的 Set 实现——底层就是 `HashMap`，元素作为 key，value 统一指向一个 `PRESENT` 哨兵对象。

```java
Set<String> set = new HashSet<>();

// 基本操作
set.add("apple");
set.add("banana");
set.add("apple");             // 返回 false —— 已存在
System.out.println(set);      // [banana, apple] 或 [apple, banana] —— 无序

set.remove("apple");
boolean has = set.contains("banana");  // true
int size = set.size();

// 批量操作
Set<String> other = Set.of("banana", "cherry");
Set<String> union = new HashSet<>(set);
union.addAll(other);                 // 并集

Set<String> intersection = new HashSet<>(set);
intersection.retainAll(other);       // 交集

Set<String> difference = new HashSet<>(set);
difference.removeAll(other);         // 差集

// 遍历（无序）
for (String s : set) {
    System.out.println(s);
}
```

### 构造参数

```java
new HashSet<>();                    // 默认容量 16，负载因子 0.75
new HashSet<>(100);                 // 指定初始容量
new HashSet<>(100, 0.5f);          // 指定容量 + 负载因子
new HashSet<>(existingCollection); // 从其他集合复制
```

### 元素相等性

HashSet 判断元素是否相等分两步：
1. `hashCode()` 是否相等
2. 如果 hashCode 相等，再 `equals()` 是否返回 true

两个都满足才算"已存在"——这就是为什么往 HashSet 放自定义对象时必须**同时重写 `equals()` 和 `hashCode()`**。

```java
// 错误示例：只重写了 equals，没重写 hashCode
class BadUser {
    private String name;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BadUser)) return false;
        return Objects.equals(name, ((BadUser) o).name);
    }
    // hashCode 用的是 Object 的默认实现（内存地址）！
}

Set<BadUser> set = new HashSet<>();
set.add(new BadUser("张三"));
System.out.println(set.contains(new BadUser("张三")));  // false！因为 hashCode 不同
```

## LinkedHashSet

`LinkedHashSet` 继承 `HashSet`，底层用 `LinkedHashMap`——哈希表 + 双向链表，保证**插入顺序**：

```java
Set<String> set = new LinkedHashSet<>();
set.add("banana");
set.add("apple");
set.add("cherry");
System.out.println(set);  // [banana, apple, cherry] —— 严格按插入顺序

// 适用于：去重且需要保持原始顺序
List<String> withDups = List.of("c", "a", "b", "a", "c");
Set<String> unique = new LinkedHashSet<>(withDups);
System.out.println(unique);  // [c, a, b]
```

性能略差于 HashSet（多了链表维护开销），但仍是 O(1)。

## TreeSet

`TreeSet` 基于 `TreeMap`（红黑树），**元素自动排序**——实现 `SortedSet` 和 `NavigableSet` 接口：

```java
Set<Integer> set = new TreeSet<>();
set.add(5);
set.add(1);
set.add(3);
set.add(1);       // 拒绝重复
System.out.println(set);  // [1, 3, 5] —— 自动排序

// 自定义排序
Set<User> usersByAge = new TreeSet<>(Comparator.comparing(User::getAge));
// 或让 User 实现 Comparable

// TreeSet 不允许 null
// set.add(null);    // NullPointerException！
```

### NavigableSet 特有操作

```java
TreeSet<Integer> set = new TreeSet<>(List.of(1, 3, 5, 7, 9));

// 范围查找
Integer lower  = set.lower(5);     // 3 —— 小于 5 的最大元素
Integer floor  = set.floor(5);     // 5 —— 小于等于 5 的最大元素
Integer ceiling = set.ceiling(6);  // 7 —— 大于等于 6 的最小元素
Integer higher = set.higher(5);    // 7 —— 大于 5 的最小元素

// 首尾
Integer first = set.first();       // 1
Integer last  = set.last();        // 9

// 子集视图
SortedSet<Integer> head = set.headSet(5);      // [1, 3]
SortedSet<Integer> tail = set.tailSet(5);      // [5, 7, 9]
SortedSet<Integer> sub  = set.subSet(3, 7);    // [3, 5]

// 反向遍历
NavigableSet<Integer> descending = set.descendingSet();  // [9, 7, 5, 3, 1]

// 删除极值
Integer polled = set.pollFirst();    // 1（删除并返回）
set.pollLast();                       // 删除 9
```

这些操作是 TreeSet 的杀手锏——范围查询、排序、取极值都是 O(log n)。用 HashSet 做同样的事需要扫描整个集合。

## EnumSet

`EnumSet` 是专门给枚举设计的 Set——内部用**位向量**，所有操作都是位运算，极快：

```java
enum Color { RED, GREEN, BLUE, YELLOW }

// 创建 —— 不能用 new，用工厂方法
EnumSet<Color> primary    = EnumSet.of(Color.RED, Color.GREEN, Color.BLUE);
EnumSet<Color> all        = EnumSet.allOf(Color.class);
EnumSet<Color> none       = EnumSet.noneOf(Color.class);
EnumSet<Color> range      = EnumSet.range(Color.RED, Color.BLUE);  // [RED, GREEN, BLUE]
EnumSet<Color> complement = EnumSet.complementOf(primary);          // [YELLOW]

// 常规 Set 操作 —— 全部 O(1)
primary.contains(Color.RED);   // true
primary.add(Color.YELLOW);     // OK
EnumSet<Color> copy = EnumSet.copyOf(primary);

// 遍历顺序 = 枚举声明顺序
for (Color c : all) {
    System.out.println(c);  // RED, GREEN, BLUE, YELLOW
}
```

限制：
- 只能装一个枚举类型的所有常量
- null 不允许
- 线程不安全

位向量的本质：把每个枚举常量映射到一个 long（64 位）的某一位——add 就是 `bits |= 1 << ordinal`，contains 就是 `(bits & (1 << ordinal)) != 0`。这也是为什么 64 个以内的枚举常量用 `RegularEnumSet`（一个 long），超过 64 个自动切换 `JumboEnumSet`（long 数组）。

## Set 实现对比

```java
// 综合性能对比
//                  HashSet  LinkedHashSet  TreeSet  EnumSet
// add              O(1)     O(1)          O(log n) O(1)
// remove           O(1)     O(1)          O(log n) O(1)
// contains         O(1)     O(1)          O(log n) O(1)
// 迭代顺序          无序      插入顺序       排序     声明顺序
// null 支持         允许      允许          不允许   不允许
// 内存占用          中等      中高          中等     极低
// 需要 hashCode?    是        是            否(Comparator) 否
```

## equals 与 hashCode 契约

这是 Set 正确工作的前提——理解这个契约可以避免 90% 的 Set 相关 bug：

**契约**：
1. 如果 `a.equals(b)` 返回 true，那么 `a.hashCode() == b.hashCode()` 必须成立
2. 如果 `a.hashCode() == b.hashCode()`，`a.equals(b)` 不一定返回 true（哈希碰撞）
3. 同一个对象多次调用 `hashCode()` 应返回相同值（对象没被修改的前提下）

**违反契约的后果**：
- HashSet/HashMap 找不到元素
- 同一个"相等"的元素被添加了两次

```java
// 正确实现
class Point {
    private final int x;
    private final int y;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Point p)) return false;
        return x == p.x && y == p.y;
    }

    @Override
    public int hashCode() {
        return Objects.hash(x, y);   // JDK 7+ 便利方法
    }
}

// 放入 Set 后才修改参与 hashCode/equals 的字段 → 灾难
Set<Point> set = new HashSet<>();
Point p = new Point(1, 2);
set.add(p);
// p.setX(3);         // 改变了 hashCode！
// set.contains(p);   // 很可能 false —— 找不到！
```

**原则**：放入 HashSet/HashMap 作为 key 的对象，其参与 `equals`/`hashCode` 的字段不应再改变。

## SortedSet 与 NavigableSet

```java
// SortedSet —— JDK 1.2
public interface SortedSet<E> extends Set<E> {
    Comparator<? super E> comparator();
    SortedSet<E> subSet(E from, E to);
    SortedSet<E> headSet(E to);
    SortedSet<E> tailSet(E from);
    E first();
    E last();
}

// NavigableSet —— JDK 6+（扩展 SortedSet）
public interface NavigableSet<E> extends SortedSet<E> {
    E lower(E e);           // < e
    E floor(E e);           // <= e
    E ceiling(E e);         // >= e
    E higher(E e);          // > e
    E pollFirst();
    E pollLast();
    NavigableSet<E> descendingSet();
    Iterator<E> descendingIterator();
    NavigableSet<E> subSet(E from, boolean fromInclusive, E to, boolean toInclusive);
}
```

## 应用场景实战

### 场景一：集合运算工具类

```java
public class SetUtils {
    // 并集
    public static <T> Set<T> union(Set<T> a, Set<T> b) {
        Set<T> result = new HashSet<>(a);
        result.addAll(b);
        return result;
    }

    // 交集
    public static <T> Set<T> intersection(Set<T> a, Set<T> b) {
        Set<T> result = new HashSet<>(a);
        result.retainAll(b);
        return result;
    }

    // 差集 (a - b)
    public static <T> Set<T> difference(Set<T> a, Set<T> b) {
        Set<T> result = new HashSet<>(a);
        result.removeAll(b);
        return result;
    }

    // 对称差集 (a ∪ b) - (a ∩ b)
    public static <T> Set<T> symmetricDifference(Set<T> a, Set<T> b) {
        Set<T> result = union(a, b);
        result.removeAll(intersection(a, b));
        return result;
    }
}
```

### 场景二：访问频率统计 + 热门 Top N

```java
public class AccessStats {
    public static List<String> topPages(Collection<String> accessLog, int n) {
        // 1. 统计频率（Map 章节会详细讲）
        Map<String, Long> countMap = accessLog.stream()
            .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));

        // 2. 按频率排序取 Top N
        return countMap.entrySet().stream()
            .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
            .limit(n)
            .map(Map.Entry::getKey)
            .collect(Collectors.toList());
    }
}
```

### 场景三：去重 + 排序

```java
// 需求：List 去重并按自然顺序排序
List<Integer> list = List.of(3, 1, 4, 1, 5, 9, 2, 6);

// 方式一：HashSet 去重 + List 排序
Set<Integer> unique = new HashSet<>(list);
List<Integer> sorted = new ArrayList<>(unique);
Collections.sort(sorted);        // [1, 2, 3, 4, 5, 6, 9]

// 方式二：TreeSet 一步完成（O(n log n) 全程）
TreeSet<Integer> set = new TreeSet<>(list);  // [1, 2, 3, 4, 5, 6, 9]

// 方式三：Stream 一步（内部用 TreeSet）
List<Integer> result = list.stream().distinct().sorted().toList();
```

### 场景四：权限集合判断

```java
public class PermissionChecker {
    private final Set<String> userPermissions;

    public PermissionChecker(Set<String> userPermissions) {
        this.userPermissions = Set.copyOf(userPermissions);  // 不可变副本
    }

    // 是否拥所有所需权限？
    public boolean hasAll(Set<String> required) {
        return userPermissions.containsAll(required);
    }

    // 是否有任一所需权限？
    public boolean hasAny(Set<String> any) {
        for (String perm : any) {
            if (userPermissions.contains(perm)) return true;
        }
        return false;
    }
}
```

## 最佳实践与踩坑记录

### 选型指南

| 场景 | 推荐 |
|------|------|
| 去重，不关心顺序 | `HashSet` |
| 去重，需要保持插入顺序 | `LinkedHashSet` |
| 需要排序、范围查询 | `TreeSet` |
| 枚举类型 | `EnumSet` |
| 只读常量集合 | `Set.of(...)` |
| 多线程读写 | `ConcurrentHashMap.newKeySet()` 或 `Collections.synchronizedSet` |

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| Set 里出现了"重复"元素 | 只重写了 equals，没重写 hashCode | 同时重写 equals 和 hashCode |
| `contains` 找不到刚放进去的元素 | 放入后修改了参与 hashCode 的字段 | 不要在加入 Set 后修改这些字段 |
| `null` 放入 TreeSet 抛 NPE | TreeSet 需要 compareTo 比较 null | 不允许 null，先判空 |
| `ConcurrentModificationException` | 遍历时直接修改 Set | 用 Iterator.remove() 或 removeIf |
| `Set.of(...)` 抛 NPE | Set.of 不接受 null 元素 | 提前过滤 null |

### 自定义对象放入 Set 的检查清单

1. `equals()` 和 `hashCode()` 都重写了
2. 参与比较的字段都是不可变的，或对象放入 Set 后不再改变这些字段
3. `hashCode()` 实现不要把字段值直接加减（`x + y` 导致 `(1,2)` 和 `(2,1)` 同 hash）

## 总结

- `HashSet` 底层是 `HashMap`，不保证顺序，O(1) 操作
- `LinkedHashSet` 是 `LinkedHashMap`，保持插入顺序，略多内存
- `TreeSet` 是红黑树，自动排序，支持范围/极值查询，O(log n)
- `EnumSet` 用位向量，给枚举专用，所有操作 O(1)
- 放入 Set 的元素必须正确实现 `equals()` + `hashCode()`，且放入后不修改参与计算的字段
- `Set.of()` 返回不可变 Set，`Set.copyOf()` 返回不可变副本
