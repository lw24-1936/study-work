---
title: Java 枚举
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, core-api, enum, enumset, enummap]
---

# Java 枚举

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [枚举基础](#枚举基础)
- [枚举的属性与方法](#枚举的属性与方法)
- [枚举构造方法](#枚举构造方法)
- [枚举实现接口](#枚举实现接口)
- [枚举的抽象方法](#枚举的抽象方法)
- [EnumSet 与 EnumMap](#enumset-与-enummap)
- [枚举常用方法](#枚举常用方法)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

枚举是 JDK 5 引入的语法糖——`enum` 关键字声明一个特殊的类，编译器自动让它继承 `java.lang.Enum`。枚举的每个常量本质是该类的 `public static final` 实例。

Java 枚举比其他语言（C/C++ 就是整数别名）强大得多：可以有属性、构造方法、普通方法、抽象方法、实现接口。本质上是一个**实例数量在编译期就固定的类**。

| 对比维度 | C/C++ 枚举 | Java 枚举 |
|----------|------------|-----------|
| 本质 | 整数常量 | 类的实例对象 |
| 能否有方法 | 不能 | 能 |
| 能否有属性 | 不能 | 能 |
| 类型安全 | 弱（可隐式转 int） | 强（完全不同类型） |
| switch 支持 | 支持 | 支持 |
| 能否序列化 | N/A | 天然支持，不可反序列化破坏单例 |

## 枚举基础

```java
// 最简单的枚举
public enum Color {
    RED, GREEN, BLUE
}

// 使用
Color c = Color.RED;                    // 不需要 new！

// switch
switch (c) {
    case RED   -> System.out.println("红色");
    case GREEN -> System.out.println("绿色");
    case BLUE  -> System.out.println("蓝色");
}

// 比较：== 就够了（枚举是单例）
if (c == Color.RED) { ... }

// 遍历
for (Color color : Color.values()) {
    System.out.println(color.name());     // RED, GREEN, BLUE
}
```

几个关键性质：
- 枚举构造方法是**私有的**（即使你不写 private，编译器也强制）
- 枚举不能被继承（`final class`），也不能继承其他类（已经继承 `Enum`）
- 枚举常量**天然是单例**——JVM 保证每个常量只有一个实例，且反序列化不会破坏
- `==` 和 `equals` 等价——用 `==` 即可，还能避免 NPE

## 枚举的属性与方法

```java
public enum OrderStatus {
    //            code  label
    PENDING      (0,    "待支付"),
    PAID         (1,    "已支付"),
    SHIPPED      (2,    "已发货"),
    DELIVERED    (3,    "已签收"),
    CANCELLED    (4,    "已取消");

    // 属性
    private final int code;
    private final String label;

    // 构造方法 —— 只能是 private（不写也是 private）
    OrderStatus(int code, String label) {
        this.code = code;
        this.label = label;
    }

    // 普通方法
    public int getCode() { return code; }
    public String getLabel() { return label; }

    // 根据 code 查找（常用模式）
    public static OrderStatus fromCode(int code) {
        for (OrderStatus status : values()) {
            if (status.code == code) {
                return status;
            }
        }
        throw new IllegalArgumentException("未知状态码: " + code);
    }
}

// 使用
OrderStatus status = OrderStatus.PAID;
System.out.println(status.getCode());   // 1
System.out.println(status.getLabel());  // 已支付
```

## 枚举构造方法

```java
public enum Planet {
    MERCURY(3.303e+23, 2.4397e6),
    VENUS  (4.869e+24, 6.0518e6),
    EARTH  (5.976e+24, 6.37814e6);

    private final double mass;    // kg
    private final double radius;  // m

    Planet(double mass, double radius) {
        this.mass = mass;
        this.radius = radius;
    }

    public double surfaceGravity() {
        final double G = 6.67300E-11;
        return G * mass / (radius * radius);
    }

    public double surfaceWeight(double otherMass) {
        return otherMass * surfaceGravity();
    }
}

// 用法
double earthWeight = 175.0;
double mass = earthWeight / Planet.EARTH.surfaceGravity();
for (Planet p : Planet.values()) {
    System.out.printf("在 %s 上的体重: %.2f%n", p, p.surfaceWeight(mass));
}
```

## 枚举实现接口

```java
public interface Calculator {
    double apply(double a, double b);
}

public enum BasicOperation implements Calculator {
    PLUS {
        public double apply(double a, double b) { return a + b; }
    },
    MINUS {
        public double apply(double a, double b) { return a - b; }
    },
    TIMES {
        public double apply(double a, double b) { return a * b; }
    },
    DIVIDE {
        public double apply(double a, double b) { return a / b; }
    };
}

// 用法：策略模式 + 枚举
double result = BasicOperation.PLUS.apply(10, 5);   // 15
```

## 枚举的抽象方法

每个枚举常量可以有不同的行为实现——这就是"常量特定方法（constant-specific method）"：

```java
public enum PayMethod {
    ALIPAY {
        @Override
        public String pay(BigDecimal amount) {
            return "支付宝支付 " + amount + " 元";
        }
    },
    WECHAT {
        @Override
        public String pay(BigDecimal amount) {
            return "微信支付 " + amount + " 元";
        }
    },
    BANK_CARD {
        @Override
        public String pay(BigDecimal amount) {
            return "银行卡支付 " + amount + " 元";
        }
    };

    public abstract String pay(BigDecimal amount);
}

// 用法
System.out.println(PayMethod.ALIPAY.pay(new BigDecimal("100")));
// 支付宝支付 100 元
```

这种模式本质是每个常量是一个匿名子类——枚举声明里带方法体的常量都生成了匿名内部类。

## EnumSet 与 EnumMap

这两个类是专门为枚举优化的集合实现，比通用的 `HashSet` / `HashMap` 快很多。

```java
import java.util.EnumSet;
import java.util.EnumMap;

// EnumSet —— 内部用位向量（bit vector），极其高效
EnumSet<Color> primary = EnumSet.of(Color.RED, Color.GREEN, Color.BLUE);
EnumSet<Color> all = EnumSet.allOf(Color.class);
EnumSet<Color> none = EnumSet.noneOf(Color.class);
EnumSet<Color> range = EnumSet.range(Color.RED, Color.BLUE);  // 按声明顺序
EnumSet<Color> complement = EnumSet.complementOf(primary);     // 补集

// EnumSet 支持所有 Set 操作
primary.add(Color.GREEN);            // 已存在，无变化
boolean has = primary.contains(Color.RED);  // true
EnumSet<Color> copy = EnumSet.copyOf(primary);
```

```java
// EnumMap —— 内部用数组，key 必须是枚举类型
EnumMap<Color, String> colorMap = new EnumMap<>(Color.class);
colorMap.put(Color.RED, "红色");
colorMap.put(Color.GREEN, "绿色");
colorMap.put(Color.BLUE, "蓝色");

// 遍历（按枚举声明顺序！）
for (Map.Entry<Color, String> entry : colorMap.entrySet()) {
    System.out.println(entry.getKey() + " -> " + entry.getValue());
}

// 用 Stream 构造
EnumMap<Color, String> fromStream = Arrays.stream(Color.values())
    .collect(Collectors.toMap(
        c -> c,
        Color::name,
        (a, b) -> a,
        () -> new EnumMap<>(Color.class)
    ));
```

性能对比：`EnumSet` 的所有基本操作都在 O(1) 内完成（位运算），`EnumMap` 的 get/put 也是数组直接索引 O(1)，没有哈希计算和冲突处理。

## 枚举常用方法

编译器为每个枚举自动生成以下方法：

```java
public enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

// values() —— 返回所有常量数组（编译器生成，不是 Enum 的方法）
Day[] days = Day.values();

// valueOf(String) —— 按名称查找（编译器生成）
Day tue = Day.valueOf("TUE");        // TUE
// Day x = Day.valueOf("XXX");       // IllegalArgumentException

// 继承自 Enum 的方法
String name = Day.MON.name();             // "MON" —— 和声明一样，不可重写
int ordinal = Day.MON.ordinal();          // 0 —— 声明顺序（从 0 开始）
int cmp = Day.MON.compareTo(Day.TUE);     // -1

// 继承自 Object 的方法
String str = Day.MON.toString();          // "MON" —— 可以重写
boolean eq = Day.MON.equals(Day.MON);     // true —— 本质就是 ==

// 反射相关
Class<Day> cls = Day.MON.getDeclaringClass();
boolean isEnum = Day.class.isEnum();      // true
```

一般不要依赖 `ordinal()`——它基于声明顺序，插入新常量会改变后面的序号。如果要一个稳定的标识，自己定义 int code 属性。

## 应用场景实战

### 场景一：状态机

```java
public enum DocumentState {
    DRAFT {
        @Override
        public DocumentState submit() { return REVIEW; }
        @Override
        public DocumentState reject() { return this; }   // 不可操作
    },
    REVIEW {
        @Override
        public DocumentState submit() { return this; }
        @Override
        public DocumentState reject() { return DRAFT; }
        @Override
        public DocumentState approve() { return PUBLISHED; }
    },
    PUBLISHED {
        @Override
        public DocumentState submit() { return this; }
        @Override
        public DocumentState reject() { return this; }
    };

    // 每种状态定义自己的合法转换
    public DocumentState submit() { throw new UnsupportedOperationException(); }
    public DocumentState reject() { throw new UnsupportedOperationException(); }
    public DocumentState approve() { throw new UnsupportedOperationException(); }
}
```

### 场景二：HTTP 状态码

```java
public enum HttpStatus {
    OK(200, "成功"),
    CREATED(201, "已创建"),
    BAD_REQUEST(400, "请求错误"),
    UNAUTHORIZED(401, "未授权"),
    FORBIDDEN(403, "禁止访问"),
    NOT_FOUND(404, "未找到"),
    INTERNAL_SERVER_ERROR(500, "服务器内部错误");

    private final int code;
    private final String message;

    HttpStatus(int code, String message) {
        this.code = code;
        this.message = message;
    }

    public int getCode() { return code; }
    public String getMessage() { return message; }

    // 判断类别
    public boolean isSuccess() { return code >= 200 && code < 300; }
    public boolean isError() { return code >= 400; }
}
```

### 场景三：替换 if-else / switch

```java
public enum UserRole {
    ADMIN {
        @Override
        public Set<String> permissions() {
            return Set.of("READ", "WRITE", "DELETE", "MANAGE");
        }
    },
    EDITOR {
        @Override
        public Set<String> permissions() {
            return Set.of("READ", "WRITE");
        }
    },
    VIEWER {
        @Override
        public Set<String> permissions() {
            return Set.of("READ");
        }
    };

    public abstract Set<String> permissions();

    public boolean hasPermission(String permission) {
        return permissions().contains(permission);
    }
}

// 用法清爽，新增角色只需要加一个枚举值
if (user.getRole().hasPermission("DELETE")) {
    deleteResource();
}
```

### 场景四：单例模式

```java
// 枚举单例 —— 最简单、最安全的单例实现
public enum ConfigManager {
    INSTANCE;

    private Properties props = new Properties();

    public void load(String path) {
        // 加载配置
    }

    public String get(String key) {
        return props.getProperty(key);
    }
}

// 用法
ConfigManager.INSTANCE.load("config.properties");
String dbUrl = ConfigManager.INSTANCE.get("db.url");
```

枚举单例是 Josh Bloch（《Effective Java》作者）推荐的最佳单例实现方式——天然防反射破坏、防序列化破坏、线程安全。

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| 新增常量后逻辑出错 | 依赖了 `ordinal()` | 自己定义 int code 属性，不要依赖声明顺序 |
| `valueOf` 抛 IllegalArgumentException | 字符串和枚举常量名不严格匹配（含空格、大小写不一致） | 自己写 `fromString(String)` 方法做容错处理 |
| EnumSet 存储超过 64 个常量的枚举 | EnumSet 内部用 RegularEnumSet（long 位向量）只支持 <=64 个 | 自动降级为 JumboEnumSet（long 数组），无感知 |
| 枚举序列化后反序列化不是同一个对象 | 不会发生 —— 枚举的序列化机制保证这点 | 放心用 |

### 设计原则

```java
// 正确：枚举常量少且固定
public enum Season { SPRING, SUMMER, AUTUMN, WINTER }

// 错误：用枚举存储可能变化的数据
public enum Country { ... }   // 国家列表会变，不应该硬编码成枚举
// 应该从数据库或配置文件读取
```

### 性能建议

- `EnumSet` 和 `EnumMap` 比通用集合快一个数量级，能用就用
- `values()` 每次调用都返回新数组（防御性复制）——如果有频繁调用，缓存起来
- `valueOf` 内部用了 `Enum.valueOf(Class, String)` 加 HashMap 查找，开销不大

## 总结

- Java 枚举是完整的类，可以有属性、方法、构造方法、实现接口
- 枚举常量是天然单例，`==` 比较安全，序列化不破坏单例
- `EnumSet` 和 `EnumMap` 性能远超通用集合——能用枚举当 key 的场合优先考虑
- 用枚举替代常量（`public static final int`）获得类型安全
- 不要依赖 `ordinal()`，自己维护 int code；`values()` 频繁调用时缓存起来
- 枚举最适合表示**编译期就确定的固定常量集合**——状态、类型、操作码、单例
