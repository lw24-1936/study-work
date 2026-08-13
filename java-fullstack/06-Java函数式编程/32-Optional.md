---
title: Optional
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, optional, null-safety, functional-programming]
---

# Optional

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [创建 Optional](#创建-optional)
- [值提取](#值提取)
- [条件执行](#条件执行)
- [转换操作 map 与 flatMap](#转换操作-map-与-flatmap)
- [orElse vs orElseGet vs orElseThrow](#orelse-vs-orelseget-vs-orelsethrow)
- [结合 Stream 使用](#结合-stream-使用)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`Optional` 是 JDK 8 引入的容器类——它要么包含一个非 null 值，要么为空。设计目标是**消除 NPE**，让"值可能不存在"这个语义在类型系统中明确表达。

Tony Hoare（null 的发明者）称 null 是他"十亿美元的错误"——Optional 是 Java 给出的补救方案。

| 对比 | null | Optional |
|------|------|----------|
| 表达"不存在" | 隐式（全靠约定和注释） | 显式（类型系统强制执行） |
| 编译器检查 | 不检查（NPE 是运行时） | API 引导你处理两种可能 |
| 代码清晰度 | `if (x != null)` 散落各处 | 流畅的链式 API |
| 额外开销 | 没有 | 多一个包装对象（极小） |

核心原则：**Optional 是返回值类型，不是字段类型，不是方法参数类型**。

## 创建 Optional

```java
// 创建包含值的 Optional —— 值不能为 null
Optional<String> opt1 = Optional.of("hello");
// Optional.of(null);  // NullPointerException！

// 创建可能为 null 的 Optional
Optional<String> opt2 = Optional.ofNullable(getFromDB());  // null 则返回 Optional.empty()

// 创建空 Optional
Optional<String> empty = Optional.empty();

// 判断是否有值
if (opt1.isPresent()) {
    System.out.println(opt1.get());  // "hello"
}

// JDK 11+ 简化判空
// if (opt1.isEmpty()) { ... }
```

## 值提取

```java
Optional<String> opt = Optional.of("hello");

// get() —— 有值返回值，空则抛 NoSuchElementException（尽量少用）
String s1 = opt.get();

// orElse(T) —— 有值返回值，空则返回默认值
String s2 = opt.orElse("default");  // "hello"

// orElseGet(Supplier) —— 有值返回值，空则调用 Supplier（惰性求值）
String s3 = opt.orElseGet(() -> loadDefault());  // "hello"

// orElseThrow —— 有值返回值，空则抛异常
String s4 = opt.orElseThrow();                          // JDK 10+：抛 NoSuchElementException
String s5 = opt.orElseThrow(() -> new IllegalStateException("用户不存在"));

// or —— JDK 9+：空则返回另一个 Optional
Optional<String> fallback = opt.or(() -> Optional.of("fallback"));
```

## 条件执行

```java
Optional<String> opt = Optional.of("hello");

// ifPresent —— 有值则执行 Consumer
opt.ifPresent(val -> System.out.println("值是: " + val));

// ifPresentOrElse —— JDK 9+：有值执行第一个，空执行第二个
opt.ifPresentOrElse(
    val  -> System.out.println("值是: " + val),
    ()   -> System.out.println("值不存在")
);
```

## 转换操作 map 与 flatMap

```java
Optional<String> opt = Optional.of("hello");

// map —— 有值则转换，空则保持 empty
Optional<Integer> length = opt.map(String::length);     // Optional[5]
Optional<String> upper = opt.map(String::toUpperCase);  // Optional[HELLO]

// 链式 map
Optional<String> result = Optional.of("  hello  ")
    .map(String::trim)
    .map(String::toUpperCase);
System.out.println(result);  // Optional[HELLO]

// flatMap —— 转换函数返回 Optional，自动展平（避免 Optional<Optional<T>>）
public Optional<User> findUser(Long id) { ... }
public Optional<String> getEmail(User user) { ... }

// 如果嵌套调用：
// Optional<Optional<String>> nested = findUser(1L).map(user -> getEmail(user));
// 用 flatMap 展平：
Optional<String> email = findUser(1L).flatMap(user -> getEmail(user));
```

map 和 flatMap 的区别：

```java
// map：T → U，包装成 Optional<U>
opt.map(fn)       // Optional<T> → Optional<U>

// flatMap：T → Optional<U>，展平为 Optional<U>
opt.flatMap(fn)   // Optional<T> → Optional<U>（fn 返回 Optional<U>）
```

## orElse vs orElseGet vs orElseThrow

这是 Optional 最容易犯错的 API——`orElse` 和 `orElseGet` 的执行时机完全不同：

```java
// orElse —— 参数是值，无论 Optional 有没有值都会执行！
public String getUserName(Long id) {
    return findById(id)
        .map(User::getName)
        .orElse(getDefaultName());   // getDefaultName 一定会执行！
}

// orElseGet —— 参数是 Supplier，只在 Optional 为空时才执行
public String getUserName(Long id) {
    return findById(id)
        .map(User::getName)
        .orElseGet(() -> getDefaultName());  // getDefaultName 只在需要时才调用
}
```

```java
// 验证：orElse 会提前执行
Optional<String> opt = Optional.of("hello");
String result = opt.orElse(expensiveOperation());  // expensiveOperation 被执行了！
System.out.println(result);  // "hello" —— 但 expensiveOperation 白白浪费了

// 正确：用 orElseGet
String result2 = opt.orElseGet(() -> expensiveOperation());  // expensiveOperation 不执行
```

规则：**只要默认值需要计算（方法调用、数据库查询、new 对象），就用 `orElseGet`**。只有默认值是常量（`"N/A"`、`0`、`Collections.emptyList()`）时才用 `orElse`。

## 结合 Stream 使用

```java
List<Optional<User>> optUsers = List.of(
    Optional.of(new User("张三")),
    Optional.empty(),
    Optional.of(new User("李四"))
);

// 过滤掉空 Optional，提取值
List<User> users = optUsers.stream()
    .filter(Optional::isPresent)
    .map(Optional::get)                       // 不优雅
    .collect(Collectors.toList());

// JDK 9+ stream() —— Optional 直接转 Stream
List<User> users2 = optUsers.stream()
    .flatMap(Optional::stream)                // 空 Optional 变成空 Stream
    .collect(Collectors.toList());            // [张三, 李四]
```

```java
// Stream 终端操作返回 Optional
Optional<User> first = users.stream()
    .filter(u -> u.getAge() > 30)
    .findFirst();

// 链式处理
String name = users.stream()
    .filter(u -> u.getAge() > 30)
    .findFirst()
    .map(User::getName)
    .orElse("未知用户");
```

## 应用场景实战

### 场景一：深层属性安全访问

```java
// 旧方式——层层判空
public String getCityName(User user) {
    if (user != null) {
        Address address = user.getAddress();
        if (address != null) {
            City city = address.getCity();
            if (city != null) {
                return city.getName();
            }
        }
    }
    return "未知";
}

// Optional 链式
public String getCityName(User user) {
    return Optional.ofNullable(user)
        .map(User::getAddress)
        .map(Address::getCity)
        .map(City::getName)
        .orElse("未知");
}
```

### 场景二：数据库查询

```java
public class UserService {
    public UserDTO getUserDetail(Long userId) {
        return userRepository.findById(userId)           // Optional<User>
            .filter(User::isActive)                       // 只取活跃用户
            .map(user -> {
                UserDTO dto = new UserDTO();
                dto.setId(user.getId());
                dto.setName(user.getName());
                dto.setLevel(user.getLevel());
                return dto;
            })
            .orElseThrow(() -> new NotFoundException("用户不存在或已禁用: " + userId));
    }
}
```

### 场景三：配置项读取

```java
public class ConfigReader {
    public int getInt(String key) {
        return Optional.ofNullable(props.getProperty(key))
            .map(Integer::parseInt)
            .orElse(0);                               // 默认值 0
    }

    public String getRequired(String key) {
        return Optional.ofNullable(props.getProperty(key))
            .filter(s -> !s.isBlank())
            .orElseThrow(() -> new ConfigException("缺少配置项: " + key));
    }

    public List<String> getList(String key) {
        return Optional.ofNullable(props.getProperty(key))
            .map(s -> s.split(","))
            .map(Arrays::asList)
            .map(list -> list.stream()
                .map(String::trim)
                .collect(Collectors.toList()))
            .orElse(List.of());
    }
}
```

### 场景四：缓存查询

```java
public class CacheService {
    public <T> T get(String key, Class<T> type) {
        return Optional.ofNullable(cache.get(key))
            .filter(type::isInstance)      // 类型检查
            .map(type::cast)               // 安全强转
            .orElseGet(() -> {
                T value = loadFromDB(key, type);
                cache.put(key, value);
                return value;
            });
    }
}
```

## 最佳实践与踩坑记录

### 设计原则

```
√ 用 Optional 作为返回值类型 —— 表示"可能没有结果"
√ 用 Optional 做链式安全访问 —— 替代深层判空
√ 用 orElseGet 做延迟默认值 —— 避免不必要的计算

× 不要用 Optional 作为字段类型 —— 增加内存开销，不可序列化
× 不要用 Optional 作为方法参数 —— 调用者被迫包装，语义混乱
× 不要用 Optional.get() 不判空 —— 和直接用 null 没区别
× 不要用 Optional 包装集合 —— Optional<List<T>> 很蠢，空集合就够了
× 不要用 Optional 做 if-else 流程控制 —— 那不如直接 if
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `orElse(expensiveCall())` 被白白执行 | orElse 参数是值，总是先求值 | 用 `orElseGet(() -> expensiveCall())` |
| `Optional` 作为字段无法序列化 | Optional 没有实现 Serializable | 字段用普通类型 + getter 返回 Optional |
| `get()` 抛 NoSuchElementException | 没检查就直接 get | 用 `orElse/orElseGet/orElseThrow` 代替 |
| 嵌套 `Optional<Optional<T>>` | 用了 map 处理返回 Optional 的方法 | 换成 `flatMap` |
| JDK 8 中 Optional 没有 `stream()` | JDK 9 才加的 | 用 `.filter(Optional::isPresent).map(Optional::get)` |

### 典型反模式

```java
// 反模式 1：用 Optional 做 if 判断
Optional<User> opt = findUser(id);
if (opt.isPresent()) {        // 这和直接判断 null 没区别
    doSomething(opt.get());
} else {
    doOtherThing();
}

// 正确：用 Optional 的 API
findUser(id).ifPresentOrElse(
    user -> doSomething(user),
    ()   -> doOtherThing()
);

// 反模式 2：把 Optional 当参数传递
public void process(Optional<String> param) { }  // 不好

// 正确：方法签名用具体类型，内部再判断
public void process(String param) {
    // 如果允许 null，方法内部用 Optional.ofNullable
}

// 反模式 3：Optional 包装集合
Optional<List<User>> findUsers() { }  // 不好

// 正确：直接返回空集合
List<User> findUsers() {
    return result != null ? result : List.of();
}
```

## 总结

- `Optional.ofNullable(x)` 表示"x 可能为 null"；`Optional.of(x)` 要求 x 非 null
- `map` / `flatMap` 做安全链式访问；`filter` 做条件过滤
- `orElseGet` 惰性求值（推荐）；`orElse` 总是求值（仅用于常量）
- `orElseThrow` 抛异常表达"此处不应该为空"的语义
- Optional 只做返回值，不做字段、不做参数
- JDK 9+：`ifPresentOrElse`、`or()`、`stream()` 三个增强让 API 更完整
- Optional 的本质不是消灭 null，而是让"可能没有值"这个事实不可忽略
