---
title: Map
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, collection, map, hashmap, treemap]
---

# Map

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [HashMap](#hashmap)
- [LinkedHashMap](#linkedhashmap)
- [TreeMap](#treemap)
- [Hashtable](#hashtable)
- [WeakHashMap](#weakhashmap)
- [IdentityHashMap](#identityhashmap)
- [EnumMap](#enummap)
- [ConcurrentHashMap 概览](#concurrenthashmap-概览)
- [Map 操作进阶](#map-操作进阶)
- [应用场景实战](#应用场景实战)
- [最佳实践与选型指南](#最佳实践与选型指南)

## 概述

`Map<K,V>` 是键值对集合，每个键最多映射到一个值。Map 不在 Collection 体系中，是独立的接口。

Java 提供 8 种 Map 实现，各有用武之地：

| 实现类 | 底层结构 | 顺序 | 线程安全 | null 键 | null 值 |
|--------|----------|------|----------|---------|---------|
| `HashMap` | 数组+链表+红黑树 | 无序 | 否 | 允许一个 | 允许 |
| `LinkedHashMap` | HashMap + 双向链表 | 插入/访问顺序 | 否 | 允许一个 | 允许 |
| `TreeMap` | 红黑树 | 键排序 | 否 | 不允许 | 允许 |
| `Hashtable` | 数组+链表 | 无序 | 是 | 不允许 | 不允许 |
| `WeakHashMap` | 数组+链表+弱引用 | 无序 | 否 | 允许 | 允许 |
| `IdentityHashMap` | 数组 | 无序 | 否 | 允许 | 允许 |
| `EnumMap` | 数组 | 枚举声明顺序 | 否 | 不允许 | 允许 |
| `ConcurrentHashMap` | 分段/桶锁 | 无序 | 是 | 不允许 | 不允许 |

## HashMap

`HashMap` 是 Map 的默认选择，内部结构在 Java 8 后是 **数组 + 链表 + 红黑树**（链表长度达到阈值则树化）。

```java
import java.util.HashMap;
import java.util.Map;

Map<String, Integer> map = new HashMap<>();

// 基本 CRUD
map.put("apple", 1);                     // 添加/更新
map.put("banana", 2);
map.put("apple", 10);                    // 更新

Integer value = map.get("apple");        // 10 —— 通过 key 取 value
Integer missing = map.get("cherry");     // null —— key 不存在
Integer withDefault = map.getOrDefault("cherry", 0);  // 0 —— JDK 8+

map.remove("banana");                    // 删除
map.remove("cherry");                    // 删不存在的 key，返回 null，无异常

boolean hasKey = map.containsKey("apple");   // true
boolean hasVal = map.containsValue(10);      // true
int size = map.size();                       // 1
map.clear();                                 // 清空
```

### 构造参数

```java
new HashMap<>();                     // 默认容量 16，负载因子 0.75
new HashMap<>(64);                   // 指定容量
new HashMap<>(64, 0.5f);            // 容量 + 负载因子
new HashMap<>(existingMap);          // 从其他 Map 复制
```

- **初始容量**：哈希桶的数量（自动调整为 2 的幂）
- **负载因子**：何时扩容——默认 0.75，即装满 75% 时扩容。降低负载因子减少冲突但增加内存，提高则反之

### 遍历

```java
// 1. 遍历键
for (String key : map.keySet()) {
    System.out.println(key + " -> " + map.get(key));
}

// 2. 遍历值
for (Integer val : map.values()) {
    System.out.println(val);
}

// 3. 遍历键值对（最常用）
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    System.out.println(entry.getKey() + " -> " + entry.getValue());
}

// 4. forEach（JDK 8+）
map.forEach((key, val) -> System.out.println(key + " -> " + val));
```

### JDK 8+ 的便利方法

```java
Map<String, Integer> map = new HashMap<>();

// putIfAbsent —— key 不存在才放
map.putIfAbsent("apple", 1);     // key 不存在 → 放入，返回 null
map.putIfAbsent("apple", 100);   // key 已存在 → 不放入，返回旧值 1

// compute —— 原子计算
map.compute("count", (k, v) -> v == null ? 1 : v + 1);   // 递增

// computeIfAbsent —— key 不存在时计算并放入（惰性初始化）
map.computeIfAbsent("list", k -> new ArrayList<>());      // 常用于分组

// computeIfPresent —— key 存在时才计算
map.computeIfPresent("score", (k, v) -> v + 10);

// merge —— 合并值
map.merge("count", 1, Integer::sum);   // key 不存在 → 放 1；存在 → 旧值 + 1

// 这些方法返回的是新值（不是旧值！）
Integer newVal = map.merge("count", 1, Integer::sum);  // newVal 是合并后的值
```

### HashMap 的 key 要求

和 HashSet 一样，HashMap 的 key 必须正确实现 `equals()` 和 `hashCode()`：

```java
class User {
    private String name;
    private int age;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User u)) return false;
        return age == u.age && Objects.equals(name, u.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
}

Map<User, String> map = new HashMap<>();
User u1 = new User("张三", 25);
map.put(u1, "data");
System.out.println(map.get(new User("张三", 25)));  // "data" —— equals + hashCode 正确
```

## LinkedHashMap

`LinkedHashMap` 在 `HashMap` 基础上加了双向链表，维护键值对的顺序：

```java
Map<String, Integer> map = new LinkedHashMap<>();
map.put("c", 3);
map.put("a", 1);
map.put("b", 2);
System.out.println(map);  // {c=3, a=1, b=2} —— 按插入顺序

// 访问顺序模式（access-order = true）
Map<String, Integer> accessOrder = new LinkedHashMap<>(16, 0.75f, true);
accessOrder.put("c", 3);
accessOrder.put("a", 1);
accessOrder.put("b", 2);
accessOrder.get("c");      // 访问 c，c 被移到末尾
accessOrder.get("a");      // 访问 a，a 被移到末尾
System.out.println(accessOrder);  // {b=2, c=3, a=1}
```

LRU 缓存原型：

```java
public class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private final int maxSize;

    public LRUCache(int maxSize) {
        super(16, 0.75f, true);  // access-order = true
        this.maxSize = maxSize;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > maxSize;  // 超过容量自动删除最老的条目
    }
}

LRUCache<String, String> cache = new LRUCache<>(3);
cache.put("a", "1");
cache.put("b", "2");
cache.put("c", "3");
cache.get("a");              // a 被访问 → 移到队尾
cache.put("d", "4");         // 超过 3 个 → 删除最老的 b
System.out.println(cache);   // {c=3, a=1, d=4}
```

## TreeMap

`TreeMap` 基于红黑树，**键自动排序**，实现 `SortedMap` 和 `NavigableMap`：

```java
Map<String, Integer> map = new TreeMap<>();
map.put("ccc", 3);
map.put("aaa", 1);
map.put("bbb", 2);
System.out.println(map);  // {aaa=1, bbb=2, ccc=3} —— 按 key 自然排序

// 自定义排序
Map<String, Integer> reversed = new TreeMap<>(Comparator.reverseOrder());
reversed.putAll(map);
System.out.println(reversed);  // {ccc=3, bbb=2, aaa=1}

// TreeMap 不允许 null key
// map.put(null, 1);  // NullPointerException
```

### NavigableMap 特有操作

```java
TreeMap<Integer, String> map = new TreeMap<>();
map.put(1, "一"); map.put(3, "三"); map.put(5, "五"); map.put(7, "七");

// 极值
Map.Entry<Integer, String> first = map.firstEntry();   // 1=一
Map.Entry<Integer, String> last  = map.lastEntry();    // 7=七

// 范围查找
Map.Entry<Integer, String> lower  = map.lowerEntry(5);   // 3=三（< 5）
Map.Entry<Integer, String> floor  = map.floorEntry(5);   // 5=五（<= 5）
Map.Entry<Integer, String> ceiling = map.ceilingEntry(4); // 5=五（>= 4）
Map.Entry<Integer, String> higher = map.higherEntry(5);  // 7=七（> 5）

// 子 Map 视图
SortedMap<Integer,String> head = map.headMap(5);        // {1=一, 3=三}
SortedMap<Integer,String> tail = map.tailMap(5);        // {5=五, 7=七}
NavigableMap<Integer,String> sub = map.subMap(3, true, 7, false); // {3=三, 5=五}

// 反向
NavigableMap<Integer, String> desc = map.descendingMap();  // {7=七, 5=五, 3=三, 1=一}
```

## Hashtable

`Hashtable` 是 JDK 1.0 的遗留类——线程安全版 HashMap，但**不再推荐**：

```java
// 和 HashMap 的区别
Hashtable<String, Integer> table = new Hashtable<>();
table.put("a", 1);          // null key → NullPointerException
table.put("b", null);       // null value → NullPointerException
```

不推荐理由：
- 所有方法 `synchronized`，粒度粗，并发性能差
- 不允许 null 键和 null 值
- Enumerator 迭代器老旧

替代方案：
- 需要线程安全 Map → `ConcurrentHashMap`
- 需要简单的同步包装 → `Collections.synchronizedMap(new HashMap<>())`

## WeakHashMap

键使用**弱引用**——当 key 不再被其他地方引用时，GC 会回收它，对应的条目自动从 Map 中移除：

```java
WeakHashMap<Object, String> map = new WeakHashMap<>();

Object key1 = new Object();
Object key2 = new Object();
map.put(key1, "data1");
map.put(key2, "data2");

System.out.println(map.size());   // 2

key1 = null;  // 断开强引用
System.gc();  // 建议 GC（不保证立即执行）
Thread.sleep(1000);
System.out.println(map.size());   // 可能变成 1 —— key1 的条目被清除了
```

适用场景：缓存、监听器注册表——不想手动清理，希望对象不用时自动消失。

## IdentityHashMap

使用**引用相等**（`==`）而不是 `equals()` 来比较键——即使两个对象的 `equals` 返回 true，只要不是同一个引用，就算不同的键：

```java
Map<String, String> normalMap = new HashMap<>();
Map<String, String> identityMap = new IdentityHashMap<>();

String a = new String("hello");
String b = new String("hello");

normalMap.put(a, "normal");
normalMap.put(b, "normal2");
System.out.println(normalMap.size());    // 1 —— equals 判定相等，覆盖了

identityMap.put(a, "identity");
identityMap.put(b, "identity2");
System.out.println(identityMap.size());  // 2 —— 引用不同，算两个 key
```

底层用开放地址法（不用链表），不要求 key 实现 `hashCode()`——用 `System.identityHashCode()`。

适用场景：序列化框架、代理对象映射——需要精确区分对象身份而非内容的场景。

## EnumMap

```java
enum Color { RED, GREEN, BLUE }

EnumMap<Color, String> map = new EnumMap<>(Color.class);
map.put(Color.RED, "红色");
map.put(Color.GREEN, "绿色");
map.put(Color.BLUE, "蓝色");

// 内部就是数组，key 的 ordinal 做索引，O(1) 且无哈希计算
System.out.println(map.get(Color.RED));  // 红色

// 遍历顺序 = 枚举声明顺序
map.forEach((k, v) -> System.out.println(k + " -> " + v));
```

## ConcurrentHashMap 概览

`ConcurrentHashMap` 是并发环境下的首选 Map——JDK 8 用 CAS + synchronized 锁桶头节点，告别了分段锁：

```java
import java.util.concurrent.ConcurrentHashMap;

ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();

// API 和 HashMap 一样，但线程安全
map.put("a", 1);
map.get("a");            // 无锁读
map.putIfAbsent("b", 2); // 原子操作
map.compute("c", (k, v) -> (v == null) ? 1 : v + 1);  // 原子计算

// 不允许 null（key 和 value 都不可为 null）
// map.put(null, 1);   // NullPointerException
// map.put("a", null);  // NullPointerException

// 复合操作是原子的
// 不需要这样写：
// synchronized(map) { map.put(k, map.get(k) + 1); }
// 直接：
map.merge("counter", 1, Integer::sum);   // 原子递增
```

`ConcurrentHashMap` 的底层原理在 26-集合底层原理中有详细展开。

## Map 操作进阶

### Map 的视图

```java
// keySet()、values()、entrySet() 返回的都是**视图**——修改视图会影响原 Map
Map<String, Integer> map = new HashMap<>();
map.put("a", 1);

Set<String> keys = map.keySet();
keys.remove("a");
System.out.println(map.size());   // 0 —— 原 Map 也被修改！
```

### JDK 9+ 不可变 Map

```java
// Map.of —— 最多 10 个键值对
Map<String, Integer> m1 = Map.of("a", 1, "b", 2, "c", 3);

// Map.ofEntries —— 无限制
Map<String, Integer> m2 = Map.ofEntries(
    Map.entry("a", 1),
    Map.entry("b", 2),
    Map.entry("c", 3)
);

// Map.copyOf
Map<String, Integer> m3 = Map.copyOf(existingMap);
```

### 分组（groupingBy）

```java
List<User> users = List.of(
    new User("张三", "北京"),
    new User("李四", "上海"),
    new User("王五", "北京")
);

// 按城市分组
Map<String, List<User>> byCity = users.stream()
    .collect(Collectors.groupingBy(User::getCity));

System.out.println(byCity.get("北京"));  // [张三, 王五]
```

## 应用场景实战

### 场景一：缓存 + TTL

```java
public class CacheWithTTL<K, V> {
    private final Map<K, CacheEntry<V>> cache = new ConcurrentHashMap<>();

    private record CacheEntry<V>(V value, long expireAt) {}

    public void put(K key, V value, long ttlMs) {
        cache.put(key, new CacheEntry<>(value, System.currentTimeMillis() + ttlMs));
    }

    public V get(K key) {
        CacheEntry<V> entry = cache.get(key);
        if (entry == null) return null;
        if (System.currentTimeMillis() > entry.expireAt) {
            cache.remove(key);
            return null;
        }
        return entry.value;
    }

    // 定期清理过期条目
    public void cleanExpired() {
        cache.entrySet().removeIf(e -> System.currentTimeMillis() > e.getValue().expireAt);
    }
}
```

### 场景二：统计词频并打印

```java
public Map<String, Long> wordCount(List<String> words) {
    return words.stream()
        .collect(Collectors.groupingBy(
            Function.identity(),
            Collectors.counting()
        ));
}

// 打印 Top 10
wordCount.entrySet().stream()
    .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
    .limit(10)
    .forEach(e -> System.out.println(e.getKey() + ": " + e.getValue()));
```

### 场景三：用 Map 实现简单图

```java
// 邻接表表示的无向图
Map<String, Set<String>> graph = new HashMap<>();

public void addEdge(String from, String to) {
    graph.computeIfAbsent(from, k -> new HashSet<>()).add(to);
    graph.computeIfAbsent(to, k -> new HashSet<>()).add(from);
}

public Set<String> neighbors(String node) {
    return graph.getOrDefault(node, Set.of());
}
```

### 场景四：配置项的层级合并

```java
// 系统默认配置 < 环境配置 < 用户自定义配置
public Properties mergeConfig(Map<String, String>... layers) {
    Map<String, String> result = new HashMap<>();
    for (Map<String, String> layer : layers) {
        if (layer != null) {
            result.putAll(layer);  // 后覆盖前
        }
    }
    return result;
}
```

## 最佳实践与选型指南

### 选型流程

```
需要排序吗？
  ├── 是 → TreeMap
  └── 否 → 
      需要线程安全吗？
        ├── 是 → ConcurrentHashMap
        └── 否 →
            需要插入/访问顺序吗？
              ├── 是 → LinkedHashMap
              └── 否 →
                  key 是枚举吗？
                    ├── 是 → EnumMap
                    └── 否 → HashMap
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `ConcurrentModificationException` | 遍历时修改 Map（put/remove） | 用 `Iterator.remove()`、`ConcurrentHashMap` 或用 `entrySet().removeIf()` |
| key 变了找不到 | 放入 Map 后修改了 key 的字段 | key 用不可变对象 |
| `get` 返回 null 无法区分"不存在"和"值为 null" | HashMap 允许 null value | 用 `containsKey` 判断 或 `getOrDefault` |
| TreeMap key 为 null 抛 NPE | TreeMap 需要比较 key | 不允许 null key |
| 多线程同时 put HashMap | 可能导致死循环（JDK 7）或数据错乱 | 用 ConcurrentHashMap |

### 性能建议

- **提前指定 HashMap 容量**：`new HashMap<>(expectedSize / 0.75 + 1)`，避免扩容
- **不要用 keySet() 遍历再 get()**：多一次哈希查找；用 `entrySet()` 一次拿全
- **EnumMap > HashMap**：能用枚举做 key 的场景优先 EnumMap

## 总结

- `HashMap` 是默认选择：数组+链表+红黑树，O(1) 操作，允许 null 键值
- `LinkedHashMap` 保持插入顺序，access-order 模式可做 LRU 缓存
- `TreeMap` 红黑树，键排序，支持范围查询和极值操作
- `Hashtable` 是遗留类，用 `ConcurrentHashMap` 替代
- `WeakHashMap` 键是弱引用，GC 自动清理——适合缓存
- `IdentityHashMap` 用 == 而不是 equals，适合区分对象身份
- `EnumMap` 内部数组，极快，枚举 key 的首选
- JDK 8+ 的 `computeIfAbsent`、`merge`、`putIfAbsent` 让复杂操作原子化
