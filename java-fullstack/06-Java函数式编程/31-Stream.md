---
title: Stream
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, stream, functional-programming, pipeline]
---

# Stream

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Stream 与集合的区别](#stream-与集合的区别)
- [创建 Stream](#创建-stream)
- [中间操作](#中间操作)
- [终端操作](#终端操作)
- [collect 收集器](#collect-收集器)
- [groupingBy 分组](#groupingby-分组)
- [reduce 归约](#reduce-归约)
- [并行 Stream](#并行-stream)
- [原始类型 Stream](#原始类型-stream)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Stream 是 JDK 8 引入的**声明式数据处理 API**。它不存储数据，而是描述对数据源（集合、数组、IO）的一串操作——像一个"装配流水线"，数据流过时被逐步过滤、转换、聚合，最后产出结果。

Stream 操作三阶段：

```
数据源 → 中间操作（惰性） → 终端操作（触发执行）
  │         │                      │
  List     filter                 collect
  Set      map                    forEach
  数组     sorted                  reduce
  IO       distinct               count
           limit                  findFirst
           skip                   anyMatch
           flatMap
           peek
```

**关键特性**：
- **惰性求值**：中间操作不会立即执行，它们只是构建流水线。终端操作触发实际计算
- **不修改数据源**：Stream 操作返回新的 Stream，原集合不变
- **一次性**：一个 Stream 只能被消费一次。终端操作执行后，Stream 关闭
- **内部迭代**：你声明"要什么"，引擎决定"怎么遍历"——和外部迭代（for 循环）的思维方式完全不同

## Stream 与集合的区别

| 维度 | 集合（Collection） | Stream |
|------|--------------------|--------|
| 本质 | 存储数据 | 计算数据 |
| 是否存储 | 是（内存中的数据结构） | 否（只是操作描述） |
| 能否重复消费 | 能（多次遍历） | 不能（消费完即关闭） |
| 迭代方式 | 外部迭代（你控制循环） | 内部迭代（库控制循环） |
| 懒惰性 | 即时操作 | 惰性求值 |
| 容量 | 有无界之分 | 可以无限（惰性 + 短路） |

## 创建 Stream

```java
// 从集合
Stream<String> s1 = list.stream();
Stream<String> s2 = list.parallelStream();    // 并行流

// 从数组
Stream<String> s3 = Arrays.stream(array);
Stream<Integer> s4 = Arrays.stream(new int[]{1, 2, 3});  // IntStream

// 从值
Stream<String> s5 = Stream.of("a", "b", "c");
Stream<Integer> s6 = Stream.of(1, 2, 3);

// 从 Builder
Stream<String> s7 = Stream.<String>builder()
    .add("a").add("b").add("c")
    .build();

// 无限流
Stream<Double> randoms = Stream.generate(Math::random);     // 无限随机数
Stream<Integer> naturals = Stream.iterate(0, n -> n + 1);  // 0, 1, 2, 3...
// 必须用 limit 截断，否则永远运行
List<Integer> first10 = Stream.iterate(0, n -> n + 1)
    .limit(10)
    .collect(Collectors.toList());   // [0, 1, ..., 9]

// JDK 9+ iterate 重载——带终止条件
Stream<Integer> limited = Stream.iterate(0, n -> n < 100, n -> n + 1);

// 空流
Stream<String> empty = Stream.empty();

// 从文件行
Stream<String> lines = Files.lines(Path.of("file.txt"));

// 从正则分割
Stream<String> words = Pattern.compile("\\s+").splitAsStream("hello world java");
```

## 中间操作

中间操作返回新 Stream，惰性执行——只在终端操作触发时才真正计算。

### filter —— 过滤

```java
List<String> names = List.of("Alice", "Bob", "Charlie", "David");
List<String> longNames = names.stream()
    .filter(s -> s.length() > 4)
    .collect(Collectors.toList());   // [Alice, Charlie, David]
```

### map —— 转换

```java
// 一对一映射
List<Integer> lengths = names.stream()
    .map(String::length)
    .collect(Collectors.toList());   // [5, 3, 7, 5]

// 类型转换
List<UserDTO> dtos = users.stream()
    .map(user -> new UserDTO(user.getName(), user.getAge()))
    .collect(Collectors.toList());
```

### flatMap —— 扁平化

```java
// 一对多映射 + 展开：每个元素映射成一个 Stream，再合并成一个 Stream
List<List<String>> nested = List.of(
    List.of("a", "b"),
    List.of("c", "d", "e"),
    List.of("f")
);

List<String> flat = nested.stream()
    .flatMap(List::stream)
    .collect(Collectors.toList());   // [a, b, c, d, e, f]

// 经典场景：获取所有订单的所有商品
List<Product> allProducts = orders.stream()
    .flatMap(order -> order.getProducts().stream())
    .collect(Collectors.toList());

// 不同于 map：map 会得到 List<List<Product>>，flatMap 得到 List<Product>
```

### distinct —— 去重

```java
List<Integer> nums = List.of(1, 2, 2, 3, 3, 3, 4);
List<Integer> unique = nums.stream()
    .distinct()
    .collect(Collectors.toList());   // [1, 2, 3, 4]
```

### sorted —— 排序

```java
// 自然排序
List<String> sorted = names.stream()
    .sorted()
    .collect(Collectors.toList());

// 自定义比较器
List<User> byAge = users.stream()
    .sorted(Comparator.comparing(User::getAge).reversed())
    .collect(Collectors.toList());
```

### limit / skip —— 截取/跳过

```java
Stream.iterate(1, n -> n + 1)
    .skip(5)      // 跳过前 5 个
    .limit(3)     // 只取 3 个
    .forEach(System.out::println);  // 6, 7, 8
```

### peek —— 调试查看

```java
// peek 对每个元素执行一个操作但不改变流的内容——调试用
List<String> result = names.stream()
    .filter(s -> s.length() > 3)
    .peek(s -> System.out.println("after filter: " + s))
    .map(String::toUpperCase)
    .peek(s -> System.out.println("after map: " + s))
    .collect(Collectors.toList());
```

## 终端操作

终端操作触发实际计算，消费 Stream 后关闭。

### forEach / forEachOrdered

```java
// 遍历（不保证顺序——并行时更明显）
stream.forEach(System.out::println);

// 保证顺序的遍历
stream.forEachOrdered(System.out::println);
```

### collect —— 收集成集合

```java
List<String> list = stream.collect(Collectors.toList());
Set<String> set = stream.collect(Collectors.toSet());
Map<Long, User> map = stream.collect(Collectors.toMap(User::getId, Function.identity()));
```

### reduce —— 归约

```java
// 求和
int sum = IntStream.rangeClosed(1, 100).reduce(0, Integer::sum);
// 等价于：int sum = IntStream.rangeClosed(1, 100).sum();

// 求最大值
Optional<Integer> max = Stream.of(3, 1, 4, 1, 5).reduce(Integer::max);

// 字符串连接
Optional<String> concat = Stream.of("a", "b", "c").reduce((a, b) -> a + "," + b);
```

### 匹配与查找

```java
// 全部匹配
boolean allAdult = users.stream().allMatch(u -> u.getAge() >= 18);

// 任一匹配
boolean hasVip = users.stream().anyMatch(u -> "VIP".equals(u.getLevel()));

// 无一匹配
boolean noBanned = users.stream().noneMatch(u -> u.isBanned());

// 查找第一个（常用于短路）
Optional<User> first = users.stream()
    .filter(u -> u.getAge() > 30)
    .findFirst();

// 查找任意一个（并行时有用）
Optional<User> any = users.stream()
    .filter(u -> u.getAge() > 30)
    .findAny();
```

### 统计

```java
long count = stream.count();
Optional<Integer> min = stream.min(Integer::compareTo);
Optional<Integer> max = stream.max(Integer::compareTo);
```

## collect 收集器

`Collectors` 工具类提供几十种预定义收集器：

```java
// 基本收集
List<T>       = Collectors.toList()
Set<T>        = Collectors.toSet()
Map<K,V>      = Collectors.toMap(keyMapper, valueMapper)
Collection<T> = Collectors.toCollection(LinkedList::new)

// 字符串拼接
String joined = stream.collect(Collectors.joining(", "));
String joined2 = stream.collect(Collectors.joining(", ", "[", "]"));  // [a, b, c]

// 统计
long count       = stream.collect(Collectors.counting());
int sum          = stream.collect(Collectors.summingInt(T::getValue));
double avg       = stream.collect(Collectors.averagingInt(T::getValue));
IntSummaryStatistics stats = stream.collect(Collectors.summarizingInt(T::getValue));
// stats.getCount(), stats.getSum(), stats.getMin(), stats.getMax(), stats.getAverage()

// 极值
Optional<T> min  = stream.collect(Collectors.minBy(Comparator.comparing(T::getValue)));
Optional<T> max  = stream.collect(Collectors.maxBy(Comparator.comparing(T::getValue)));
```

### collectingAndThen —— 收集后再加工

```java
// 收集成不可变列表
List<String> unmodifiable = stream.collect(
    Collectors.collectingAndThen(
        Collectors.toList(),
        Collections::unmodifiableList  // 或用 List.copyOf (JDK 10+)
    )
);
```

## groupingBy 分组

```java
// 按单个属性分组
Map<String, List<User>> byCity = users.stream()
    .collect(Collectors.groupingBy(User::getCity));

// 按条件分组
Map<Boolean, List<User>> byAdult = users.stream()
    .collect(Collectors.groupingBy(u -> u.getAge() >= 18));

// 多级分组
Map<String, Map<String, List<User>>> byCityAndLevel = users.stream()
    .collect(Collectors.groupingBy(
        User::getCity,
        Collectors.groupingBy(User::getLevel)
    ));

// 分组 + 下游收集器（分组后做统计）
Map<String, Long> countByCity = users.stream()
    .collect(Collectors.groupingBy(User::getCity, Collectors.counting()));

Map<String, Double> avgAgeByCity = users.stream()
    .collect(Collectors.groupingBy(
        User::getCity,
        Collectors.averagingInt(User::getAge)
    ));

// 分组后取每组中最大年龄的用户
Map<String, Optional<User>> oldestByCity = users.stream()
    .collect(Collectors.groupingBy(
        User::getCity,
        Collectors.maxBy(Comparator.comparing(User::getAge))
    ));
```

### partitioningBy —— 二分法分组

```java
// partitioningBy 是 groupingBy 的特化——key 只能是 Boolean
Map<Boolean, List<User>> partition = users.stream()
    .collect(Collectors.partitioningBy(u -> u.getAge() >= 18));
// {true=[成年用户...], false=[未成年用户...]}

// 下游收集器
Map<Boolean, Long> countByAdult = users.stream()
    .collect(Collectors.partitioningBy(
        u -> u.getAge() >= 18,
        Collectors.counting()
    ));
```

## reduce 归约

```java
// reduce 的三种形式

// 1. reduce(identity, accumulator) —— 有初始值，返回值不是 Optional
int sum1 = Stream.of(1, 2, 3, 4).reduce(0, Integer::sum);  // 10
// 等价于：0 + 1 + 2 + 3 + 4

// 2. reduce(accumulator) —— 无初始值，返回 Optional（流可能为空）
Optional<Integer> sum2 = Stream.of(1, 2, 3, 4).reduce(Integer::sum);  // Optional[10]
Optional<Integer> empty = Stream.<Integer>empty().reduce(Integer::sum); // Optional.empty

// 3. reduce(identity, accumulator, combiner) —— 并行归约使用
int parallelSum = Stream.of(1, 2, 3, 4)
    .parallel()
    .reduce(0, Integer::sum, Integer::sum);
// identity: 初始值
// accumulator: 累积函数（每个线程内部用）
// combiner: 合并函数（不同线程的结果合并）
```

### 自定义 reduce

```java
// 求最高工资
Optional<Employee> highestPaid = employees.stream()
    .reduce((e1, e2) -> e1.getSalary() > e2.getSalary() ? e1 : e2);

// 其实用 max 更清晰：
Optional<Employee> highest = employees.stream()
    .max(Comparator.comparing(Employee::getSalary));
```

## 并行 Stream

```java
// 创建并行流
Stream<T> parallel = list.parallelStream();
Stream<T> parallel2 = list.stream().parallel();

// 转回串行
Stream<T> sequential = parallel.sequential();

// 什么时候用并行流？
// 1. 数据量大（百万级以上）
// 2. 操作计算密集（不是 IO 密集型）
// 3. 操作独立无状态（不依赖外部可变状态）
// 4. 结果顺序不重要

// 适合并行
long sum = IntStream.rangeClosed(1, 1_000_000_000)
    .parallel()
    .sum();

// 不适合并行 —— 有共享可变状态（线程不安全！）
List<Integer> list = new ArrayList<>();   // 不是线程安全的！
// IntStream.range(0, 1000).parallel().forEach(list::add);  // 数据错乱！
```

并行流内部使用 `ForkJoinPool.commonPool()`，默认线程数 = CPU 核心数 - 1。可以通过 JVM 参数调整：`-Djava.util.concurrent.ForkJoinPool.common.parallelism=N`。

## 原始类型 Stream

为了避免装箱，对 int、long、double 有专门的 Stream：

```java
IntStream ints = IntStream.range(1, 100);         // [1, 100) = 1-99
IntStream ints2 = IntStream.rangeClosed(1, 100);  // [1, 100] = 1-100

LongStream longs = LongStream.range(1, 100);
DoubleStream doubles = DoubleStream.of(1.0, 2.0, 3.0);

// 特有方法
int sum = ints.sum();
OptionalDouble avg = ints.average();
OptionalInt max = ints.max();
IntSummaryStatistics stats = ints.summaryStatistics();

// boxed —— 转成 Stream<Integer>
Stream<Integer> boxed = IntStream.range(1, 10).boxed();

// mapToObj —— 转成对象 Stream
Stream<String> strings = IntStream.range(1, 10).mapToObj(i -> "No." + i);

// 对象 Stream 转原始 Stream
IntStream ages = users.stream().mapToInt(User::getAge);
LongStream ids = users.stream().mapToLong(User::getId);
DoubleStream salaries = users.stream().mapToDouble(User::getSalary);
```

## 应用场景实战

### 场景一：订单统计大屏

```java
public class OrderDashboard {
    public static DashboardStats calculate(List<Order> orders) {
        IntSummaryStatistics stats = orders.stream()
            .filter(o -> o.getStatus() == OrderStatus.COMPLETED)
            .mapToInt(Order::getAmount)
            .summaryStatistics();

        Map<String, Long> byCategory = orders.stream()
            .collect(Collectors.groupingBy(Order::getCategory, Collectors.counting()));

        // Top 5 客户
        List<String> topCustomers = orders.stream()
            .collect(Collectors.groupingBy(Order::getCustomerName, Collectors.summingInt(Order::getAmount)))
            .entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(5)
            .map(Map.Entry::getKey)
            .collect(Collectors.toList());

        return new DashboardStats(stats.getCount(), stats.getSum(), 
                                   stats.getAverage(), byCategory, topCustomers);
    }
}
```

### 场景二：分页

```java
public static <T> List<T> paginate(List<T> list, int page, int size) {
    return list.stream()
        .skip((long) (page - 1) * size)
        .limit(size)
        .collect(Collectors.toList());
}
```

### 场景三：去重 + 合并

```java
// 两个用户列表合并去重（按 ID）
List<User> merged = Stream.concat(list1.stream(), list2.stream())
    .collect(Collectors.toMap(
        User::getId,           // key
        Function.identity(),   // value
        (existing, replacement) -> replacement  // 重复时保留后者
    ))
    .values().stream()
    .collect(Collectors.toList());
```

### 场景四：递归用 iterate

```java
// 斐波那契数列前 20 项
List<Long> fibonacci = Stream.iterate(
        new long[]{0, 1},
        arr -> new long[]{arr[1], arr[0] + arr[1]}
    )
    .limit(20)
    .map(arr -> arr[0])
    .collect(Collectors.toList());
// [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, ...]
```

### 场景五：flatMap 实现笛卡尔积

```java
List<String> colors = List.of("红", "蓝", "绿");
List<String> sizes = List.of("S", "M", "L");

List<String> combinations = colors.stream()
    .flatMap(color -> sizes.stream().map(size -> color + "-" + size))
    .collect(Collectors.toList());
// [红-S, 红-M, 红-L, 蓝-S, 蓝-M, 蓝-L, 绿-S, 绿-M, 绿-L]
```

## 最佳实践与踩坑记录

### 操作分类速查

```
中间操作（惰性，返回 Stream）：
  过滤：filter、distinct
  映射：map、flatMap
  排序：sorted
  截取：limit、skip
  调试：peek

终端操作（触发执行，关闭 Stream）：
  收集：collect、toList
  遍历：forEach、forEachOrdered
  归约：reduce、count、sum、min、max、average
  匹配：anyMatch、allMatch、noneMatch
  查找：findFirst、findAny
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `stream has already been operated upon or closed` | 同一个 Stream 消费了两次 | 需要新 Stream 就重新创建 |
| `map` 返回 `List<List<T>>` 而不是 `List<T>` | 应该用 `flatMap` | `flatMap` 展开嵌套结构 |
| 并行流线程安全问题 | `forEach` 中添加到了非线程安全集合 | 用 `collect` 而不是 `forEach` |
| 无限流未截断 | `generate`/`iterate` 没有 `limit` | 加 `limit()` 或 JDK 9+ 用有限 `iterate` |
| `Collectors.toMap` 重复 key 抛异常 | 默认冲突策略是抛异常 | 提供 merge 函数：`(a,b) -> b` |

### 性能建议

```java
// 1. 先 filter 再 map —— 减少处理元素数量
stream.filter(heavy).map(expensive);   // 好
stream.map(expensive).filter(heavy);   // 差 —— 每个都 map 了

// 2. 用原始类型 Stream 避免装箱
users.stream().mapToInt(User::getAge).sum();  // 好
users.stream().map(User::getAge).reduce(0, Integer::sum);  // 差 —— 每个都装箱

// 3. 并行流不是银弹 —— 数据少时串行更快
// 小数据集：串行 >> 并行（线程调度开销）
// 大数据集 + 计算密集：并行有用
// IO 密集：没用（线程只是在等待）
```

## 总结

- Stream 三步：创建 → 中间操作（惰性） → 终端操作（触发）
- 核心操作：`filter`(过滤)、`map`(转换)、`flatMap`(扁平化)、`reduce`(归约)、`collect`(收集)
- `groupingBy` 分组 + 下游收集器是数据分析利器
- 一个 Stream 只能消费一次，消费后关闭
- 并行流用 `parallelStream()`，适合大数据量 + 计算密集 + 无共享状态场景
- 原始类型 Stream（`IntStream`/`LongStream`/`DoubleStream`）避免装箱，性能更好
- 不要用 `forEach` 修改外部集合（线程不安全），用 `collect` 收集结果
