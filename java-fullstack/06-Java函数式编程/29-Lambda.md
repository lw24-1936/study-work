---
title: Lambda
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, lambda, functional-programming]
---

# Lambda

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Lambda 语法](#lambda-语法)
- [Lambda 与匿名内部类](#lambda-与匿名内部类)
- [函数描述符](#函数描述符)
- [类型推断](#类型推断)
- [变量捕获](#变量捕获)
- [effectively final](#effectively-final)
- [方法引用](#方法引用)
- [构造器引用](#构造器引用)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Lambda 表达式是 JDK 8 最重大的语言级变革——它让 Java 终于能以简洁的方式表达"一段可传递的代码"。在 Lambda 出现之前，Java 只能用匿名内部类传递行为，臃肿的样板代码让函数式风格毫无美感。

核心概念：Lambda 是**函数式接口的实例**——它不是新类型，而是 JDK 1.1 就存在的"单抽象方法接口"的简洁写法。

| 对比 | 匿名内部类 | Lambda |
|------|-----------|--------|
| 代码量 | 多（必须写 new、方法名、参数类型） | 少（只写参数和 body） |
| `this` 指向 | 匿名类自身 | 所在外部类 |
| 生成 .class 文件 | 是（`$1.class`） | 否（invokedynamic） |
| 外部变量限制 | 必须是 final | effectively final |

## Lambda 语法

Lambda 完整语法包含三部分：`(参数列表) -> { 方法体 }`

```java
// 语法变体一览

// 1. 无参数
Runnable r1 = () -> System.out.println("Hello");

// 2. 单参数（可省略括号）
Consumer<String> c = s -> System.out.println(s);
Consumer<String> c2 = (s) -> System.out.println(s);  // 等价

// 3. 多参数
BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;

// 4. 显式参数类型
Comparator<String> cmp = (String a, String b) -> a.compareTo(b);

// 5. 多行方法体（需要大括号和 return）
Function<String, Integer> len = s -> {
    System.out.println("处理: " + s);
    return s.length();
};

// 6. 没有返回值的方法体
Consumer<String> printer = s -> {
    System.out.println("开始");
    System.out.println(s);
    System.out.println("结束");
};
```

规则总结：
- **单参数可省略括号**：`s -> ...` 等价于 `(s) -> ...`
- **单表达式可省略 return 和大括号**：`(a, b) -> a + b` 等价于 `(a, b) -> { return a + b; }`
- **类型可以省略**：编译器从上下文推断
- **无参数必须用空括号**：`() -> ...`
- **多行必须加大括号**：必须写 return

## Lambda 与匿名内部类

```java
// JDK 1.2 - 7：匿名内部类（臃肿）
Runnable r1 = new Runnable() {
    @Override
    public void run() {
        System.out.println("Hello");
    }
};

// JDK 8：Lambda（简洁）
Runnable r2 = () -> System.out.println("Hello");
```

两者关键区别：

```java
public class LambdaVsAnonymous {
    private int value = 100;

    public void test() {
        // 匿名内部类：this 指向匿名类实例
        Runnable anonymous = new Runnable() {
            private int value = 999;          // 遮蔽了外部类的 value
            @Override
            public void run() {
                System.out.println(this.value);  // 999 —— 匿名类的 value
                System.out.println(LambdaVsAnonymous.this.value);  // 100 —— 需要显式引用外部类
            }
        };

        // Lambda：this 指向外部类实例
        Runnable lambda = () -> {
            System.out.println(this.value);  // 100 —— Lambda 没有自己的 this
        };
    }
}
```

Lambda 不创建新作用域——`this` 就是定义 Lambda 的那个类的 `this`。这是一个常见坑：把匿名内部类换成 Lambda 时，`this` 的语义变了。

## 函数描述符

函数式接口的抽象方法签名叫做**函数描述符**（Function Descriptor）——Lambda 表达式必须和这个签名匹配：

```java
// Runnable 的函数描述符：() -> void
Runnable r = () -> System.out.println("run");

// Consumer<T> 的函数描述符：T -> void
Consumer<String> c = s -> System.out.println(s);

// Function<T, R> 的函数描述符：T -> R
Function<String, Integer> f = s -> s.length();

// Predicate<T> 的函数描述符：T -> boolean
Predicate<String> p = s -> s.isEmpty();

// Supplier<T> 的函数描述符：() -> T
Supplier<Double> s = () -> Math.random();

// Comparator<T> 的函数描述符：(T, T) -> int
Comparator<String> cmp = (a, b) -> a.compareTo(b);
```

Lambda 表达的代码必须和函数描述符完全匹配——参数数量、类型、返回值类型。这是编译期检查的。

## 类型推断

Lambda 的类型由**目标类型**（Target Type）——也就是它被赋值给的函数式接口——决定：

```java
// 同一个 Lambda，不同上下文推断出不同目标类型
// s -> s.length() 可以是：
Function<String, Integer> f1 = s -> s.length();    // T=String, R=Integer
ToIntFunction<String> f2 = s -> s.length();         // T=String
// 表达式相同，但目标类型不同

// JDK 8 增强的类型推断让泛型方法调用更流畅
List<String> names = Arrays.asList("a", "b", "c");
// JDK 7：需要显式类型
Collections.sort(names, (String a, String b) -> a.compareTo(b));
// JDK 8：完全推断
names.sort((a, b) -> a.compareTo(b));
```

JDK 11 的 `var` 也可以用于 Lambda 参数（需要显式类型注解来帮助推断）：

```java
// JDK 11+
// Predicate<String> p = (var s) -> s.isEmpty();   // var 替代显式类型
// 但通常没必要——直接省略类型即可
```

## 变量捕获

Lambda 可以访问外部变量，但有限制：

```java
public class CapturingLambda {
    private int instanceVar = 10;          // 实例变量 —— 可以读写

    public void test() {
        int localVar = 20;                 // 局部变量 —— 只能读
        // localVar = 30;                  // 如果修改了，Lambda 里就不能用

        Runnable r = () -> {
            System.out.println(instanceVar);  // OK —— 读实例变量
            instanceVar = 100;                // OK —— 甚至可以修改实例变量

            System.out.println(localVar);     // OK —— 读局部变量
            // localVar = 30;                 // 错误！不能修改捕获的局部变量
        };
    }
}
```

| 变量类型 | 能否读取 | 能否修改 |
|----------|----------|----------|
| 实例变量 | 能 | 能 |
| 静态变量 | 能 | 能 |
| 局部变量 | 能（如果 effectively final） | 不能 |
| 方法参数 | 能（如果 effectively final） | 不能 |

为什么局部变量不能修改？Lambda 的本质是在某个时间点被调用——它捕获的是变量的**值**副本。如果允许修改，就产生"改了副本还是原变量"的歧义。实例变量没有这个问题，因为捕获的是 `this` 引用，通过 `this` 修改的是同一个对象。

## effectively final

"effectively final" 的意思是：虽然没有 `final` 修饰符，但变量在初始化后**从未被重新赋值**——编译器会帮你检查：

```java
void test() {
    // 情形 1：effectively final——OK
    int x = 10;
    Runnable r1 = () -> System.out.println(x);  // OK

    // 情形 2：显式 final——OK
    final int y = 20;
    Runnable r2 = () -> System.out.println(y);  // OK

    // 情形 3：被重新赋值了——不是 effectively final
    int z = 30;
    z = 31;
    // Runnable r3 = () -> System.out.println(z);  // 编译错误！

    // 情形 4：对象引用不变，但内部状态变了——OK
    List<String> list = new ArrayList<>();
    // list = new ArrayList<>();   // 重新赋值就不行
    Runnable r4 = () -> {
        list.add("hello");         // OK —— 修改的是对象内容，不是引用
    };

    // 情形 5：循环变量——JDK 8 之前不行（每次迭代是一个新变量）
    for (int i = 0; i < 10; i++) {
        int j = i;                   // 需要复制到 effectively final 变量
        // Runnable r5 = () -> System.out.println(i);  // i 不是 effectively final
        Runnable r5 = () -> System.out.println(j);      // j 是
    }
}
```

要点：effectively final 只看**变量引用是否被重新赋值**，不关心引用指向的对象是否有变化。

## 方法引用

方法引用（Method Reference）是 Lambda 的更简洁形式——当 Lambda 只是调用一个已有方法时，可以直接引用该方法：

```java
// 四种方法引用

// 1. 静态方法引用：Class::staticMethod
Function<String, Integer> f1 = Integer::parseInt;     // 等价于 s -> Integer.parseInt(s)

// 2. 特定对象的实例方法引用：instance::method
String prefix = "Hello ";
Function<String, String> f2 = prefix::concat;          // 等价于 s -> prefix.concat(s)

// 3. 类的实例方法引用：Class::instanceMethod
//    第一个参数成为方法调用的接收者
Function<String, Integer> f3 = String::length;         // 等价于 s -> s.length()
BiFunction<String, String, Boolean> f4 = String::equals; // 等价于 (a,b) -> a.equals(b)

// 4. 构造器引用：Class::new
Supplier<ArrayList<String>> f5 = ArrayList::new;       // 等价于 () -> new ArrayList<>()
Function<Integer, ArrayList<String>> f6 = ArrayList::new; // 等价于 size -> new ArrayList<>(size)
```

原则：**能用方法引用就用方法引用**——比 Lambda 更短且语义更明确。`String::length` 和 `s -> s.length()` 做的是同一件事，但前者一眼就知道"调用了 length 方法"。

### 规则速查

```java
// 给定一个函数式接口的抽象方法签名，方法引用规则如下：

// (args) -> Class.staticMethod(args)    → Class::staticMethod
// (args) -> expr.instanceMethod(args)   → expr::instanceMethod
// (x, args) -> x.instanceMethod(args)   → Class::instanceMethod
// (args) -> new Class(args)             → Class::new
```

## 构造器引用

```java
// 无参构造
Supplier<User> userSupplier = User::new;
User user = userSupplier.get();

// 有参构造
Function<String, User> userCreator = User::new;  // 调用 User(String name)
User u = userCreator.apply("张三");

// 多参构造 —— 没有现成的函数式接口，自己定义或组合
@FunctionalInterface
interface TriFunction<T, U, V, R> {
    R apply(T t, U u, V v);
}
TriFunction<String, Integer, String, User> creator = User::new;

// 数组构造器引用
Function<Integer, String[]> arrayCreator = String[]::new;
String[] arr = arrayCreator.apply(10);   // new String[10]

IntFunction<int[][]> matrixCreator = int[][]::new;
int[][] matrix = matrixCreator.apply(5); // new int[5][]
```

## 应用场景实战

### 场景一：策略模式替代

```java
// 传统：每种策略一个类
// Lambda：策略用函数表达
public class PriceCalculator {
    private static final Map<String, Function<Double, Double>> STRATEGIES = Map.of(
        "NORMAL",  price -> price,
        "VIP",     price -> price * 0.8,
        "SVIP",    price -> price * 0.6,
        "NEW_USER", price -> price - 10 > 0 ? price - 10 : 0
    );

    public static double calculate(String level, double price) {
        return STRATEGIES.getOrDefault(level, p -> p).apply(price);
    }
}
```

### 场景二：条件筛选

```java
public class FilterUtils {
    // 泛型筛选方法
    public static <T> List<T> filter(List<T> list, Predicate<T> condition) {
        List<T> result = new ArrayList<>();
        for (T item : list) {
            if (condition.test(item)) {
                result.add(item);
            }
        }
        return result;
    }
}

// 用法
List<User> adults = FilterUtils.filter(users, u -> u.getAge() >= 18);
List<User> active = FilterUtils.filter(users, u -> u.isActive());
List<User> vip = FilterUtils.filter(users, u -> "VIP".equals(u.getLevel()));

// 组合条件
Predicate<User> isAdult = u -> u.getAge() >= 18;
Predicate<User> isActive = User::isActive;
List<User> activeAdults = FilterUtils.filter(users, isAdult.and(isActive));
```

### 场景三：延迟执行

```java
// 日志——只有需要时才执行昂贵的计算
public class LazyLogger {
    private boolean debug = true;

    public void debug(Supplier<String> messageSupplier) {
        if (debug) {
            System.out.println(messageSupplier.get());  // 只在 debug 时才计算
        }
    }
}

// 用法
logger.debug(() -> "用户 " + getUser() + " 执行了 " + expensiveOperation());
// 如果 debug=false，getUser() 和 expensiveOperation() 都不会执行
```

### 场景四：监听器简化

```java
public class Button {
    private final List<Consumer<ClickEvent>> listeners = new ArrayList<>();

    public void onClick(Consumer<ClickEvent> listener) {
        listeners.add(listener);
    }

    public void click() {
        ClickEvent event = new ClickEvent();
        listeners.forEach(l -> l.accept(event));
    }
}

// 用法
Button btn = new Button();
btn.onClick(e -> System.out.println("按钮被点击"));
btn.onClick(e -> saveData());
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| Lambda 里修改局部变量报错 | 局部变量不是 effectively final | 用数组或 AtomicReference 包装 |
| `this` 在 Lambda 中不是内部类 | Lambda 没有自己的 this | 理解 Lambda 的 this = 外部类 |
| Lambda 抛出 Checked Exception | Lambda 签名的抽象方法没声明异常 | 包装成 Unchecked 或自定义函数式接口 |
| 方法引用和 Lambda 混淆 | `String::length` vs `s -> s.length()` | 语法不同，语义等价 |
| 空指针时 Lambda 未执行 | Lambda 本身是对象，不调用不执行 | 确认真的调用了 `get()`/`accept()` 等 |

### 编写规范

```java
// 正确：短的 Lambda 单行
names.forEach(name -> System.out.println(name));

// 正确：长的 Lambda 提取成方法
names.forEach(name -> processName(name));

// 甚至更好：用方法引用
names.forEach(this::processName);

// 错误：嵌套 Lambda 太深
list.stream()
    .filter(a -> {
        return bList.stream().anyMatch(b -> {
            return cList.stream().anyMatch(c -> { ... });
        });
    });  // 不可读！

// 正确：提取成方法
list.stream().filter(this::matchesAnyB).collect(...);
```

### 性能注意

```
Lambda 不是语法糖，是 invokedynamic + MethodHandle 实现
- 首次调用有引导开销，JIT 后会内联掉
- 不生成 .class 文件，比匿名内部类省内存
- 无状态 Lambda 会被 JVM 优化为单例
- 捕获变量的 Lambda 每次创建新实例（有开销）
```

## 总结

- Lambda = 函数式接口的简洁写法，核心语法：`(参数) -> { 方法体 }`
- `this` 在 Lambda 中指向外部类，和匿名内部类的行为不同
- 方法引用比 Lambda 更短更清晰——能用则用：`String::length` > `s -> s.length()`
- Lambda 捕获的局部变量必须是 effectively final（初始化后未重新赋值）
- 目标类型决定 Lambda 的类型——同一个 `s -> s.length()` 可以是 Function 也可以是 ToIntFunction
- Lambda 不是语法糖——基于 invokedynamic，不生成 class 文件，首次有开销但 JIT 后可消除
