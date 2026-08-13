---
title: Java 基础面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [java面试, equals, hashcode, string, final, static, abstract, interface, 重载, 重写, 异常, 泛型, 反射, 注解, 包装类, 值传递, 深浅拷贝, java8, bigdecimal]
---

# Java 基础面试

整理日期：2026-08-13

## 目录

- [== 与 equals](#-与-equals)
- [hashCode 与 equals](#hashcode-与-equals)
- [String 相关](#string-相关)
- [基本数据类型与包装类](#基本数据类型与包装类)
- [final、static、abstract](#finalstaticabstract)
- [接口与抽象类](#接口与抽象类)
- [重载与重写](#重载与重写)
- [异常体系](#异常体系)
- [泛型](#泛型)
- [反射](#反射)
- [注解](#注解)
- [值传递与引用传递](#值传递与引用传递)
- [深拷贝与浅拷贝](#深拷贝与浅拷贝)
- [Object 类方法](#object-类方法)
- [Java 8 新特性](#java-8-新特性)
- [BigDecimal 精度](#bigdecimal-精度)
- [面试重点总结](#面试重点总结)

## == 与 equals

**问题 1：== 和 equals 的区别？**

```text
== —— 基本类型比较值，引用类型比较内存地址
equals —— Object 的方法，默认比较地址（等价于 ==），String/包装类重写后比较内容
```

```java
int a = 10, b = 10;
a == b;                          // true（基本类型比值）

String s1 = new String("hello");
String s2 = new String("hello");
s1 == s2;                        // false（不同对象）
s1.equals(s2);                   // true（String 重写 equals 比较内容）

Integer x = 200, y = 200;
x == y;                          // false（超出缓存，不同对象）
```

**问题 2：equals 的重写约定（自反性/对称性/传递性/一致性）？**

```text
重写 equals 必须满足：
1. 自反性 —— x.equals(x) 为 true
2. 对称性 —— x.equals(y) 则 y.equals(x)
3. 传递性 —— x.equals(y) 且 y.equals(z) 则 x.equals(z)
4. 一致性 —— 多次调用结果一致
5. 非空性 —— x.equals(null) 为 false
```

## hashCode 与 equals

**问题 1：为什么重写 equals 必须重写 hashCode？**

```text
约定：equals 相等的对象 hashCode 必须相等；hashCode 相等 equals 不一定相等（哈希冲突）。

原因：HashMap/HashSet 先用 hashCode 定位桶，再用 equals 比较。
只重写 equals 不重写 hashCode → 两个 equals 相等的对象落到不同桶，
HashMap 中会出现"两个相等对象"，get 时找不到。
```

```java
// 正确：同时重写 equals 和 hashCode，基于相同字段
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof User u)) return false;
    return id == u.id && Objects.equals(name, u.name);
}

@Override
public int hashCode() {
    return Objects.hash(id, name);
}
```

**问题 2：哈希冲突如何解决？**

```text
1. 链地址法 —— 冲突元素放链表（HashMap 用，链表过长转红黑树）
2. 开放寻址法 —— 冲突时找下一个空位（ThreadLocal 用）
3. 再哈希法 —— 换一个哈希函数
```

## String 相关

**问题 1：String 为什么不可变？**

```text
1. 底层用 final 修饰的 char[]（JDK 8）或 byte[]（JDK 9 紧凑字符串）
2. 没有提供任何修改字符数组的方法，所有"修改"操作都返回新对象
3. 类本身是 final 的，不能被继承篡改
```

```text
不可变的好处：
1. 线程安全 —— 多线程共享无需同步
2. 常量池复用 —— 相同字面量共享，节省内存
3. HashMap key 安全 —— hashCode 稳定，不会因值变化导致找不到
4. 安全 —— 不会被篡改（数据库连接串、类名等）
```

**问题 2：String、StringBuilder、StringBuffer 区别？**

| 类型 | 可变性 | 线程安全 | 性能 | 场景 |
|------|--------|---------|------|------|
| String | 不可变 | 是（不可变即安全） | 低（拼接创建新对象） | 少量拼接、常量 |
| StringBuilder | 可变 | 否 | 高 | 单线程频繁拼接 |
| StringBuffer | 可变 | 是（synchronized） | 中 | 多线程频繁拼接 |

**问题 3：字符串拼接的底层原理？**

```java
String s = "a" + "b" + "c";      // 编译期优化，直接常量折叠为 "abc"

String s2 = a + b;               // 编译成 new StringBuilder().append(a).append(b).toString()
```

```text
循环内拼接务必用 StringBuilder：
for 循环里用 String += 会每次 new StringBuilder + new String，O(n²)
用 StringBuilder 复用，O(n)
```

**问题 4：intern() 和字符串常量池？**

```java
String s1 = "hello";                    // 字面量，放入字符串常量池
String s2 = new String("hello");        // 堆上 new 对象
s1 == s2;                               // false

String s3 = s2.intern();                // 返回常量池中已有 "hello" 的引用
s1 == s3;                               // true
```

```text
常量池位置变化：
JDK 6 及之前 —— 永久代（PermGen），有大小限制，易 OOM
JDK 7 起 —— 移到堆，可被 GC 回收
JDK 8 —— 元空间替代永久代，字符串常量池仍在堆
```

## 基本数据类型与包装类

**问题 1：Java 的 8 种基本数据类型？**

```text
整型：byte(1) short(2) int(4) long(8)
浮点：float(4) double(8)
字符：char(2)
布尔：boolean(1，实际虚拟机用 int 表示)
```

**问题 2：自动装箱与拆箱？**

```java
Integer i = 10;        // 装箱：Integer.valueOf(10)
int n = i;             // 拆箱：i.intValue()
```

```text
装箱调 valueOf，拆箱调 xxxValue。
装箱发生在：赋值给包装类型、放入集合、方法参数。
拆箱发生在：赋值给基本类型、算术运算、比较运算。
```

**问题 3：Integer 缓存机制？**

```java
Integer a = 100, b = 100;
a == b;                          // true（-128~127 缓存，同一对象）

Integer c = 200, d = 200;
c == d;                          // false（超出缓存，各自 new）
```

```text
Integer 缓存 -128~127（IntegerCache），valueOf 在此范围内直接返回缓存对象。
可 -XX:AutoBoxCacheMax=size 调整上限。
```

**问题 4：包装类比较要用 equals？**

```text
两个包装类型对象用 == 比较的是地址，应改用 equals。
混合比较时（int 和 Integer），== 会触发拆箱，比的是值，但推荐统一用 equals 或拆箱后比。
```

## final、static、abstract

### final

```text
final 修饰：
1. 类 —— 不能被继承（String、Integer）
2. 方法 —— 不能被重写
3. 变量 —— 引用不可变，基本类型值不可变
4. final 修饰引用类型，引用不可变，但对象内容可变（final List 仍可 add）
```

### static

```text
static 修饰：
1. 变量 —— 类变量，所有实例共享，类加载时初始化
2. 方法 —— 类方法，不依赖实例，不能访问非静态成员、不能用 this/super
3. 代码块 —— 类加载时执行一次（静态代码块）
4. 内部类 —— 静态内部类不依赖外部类实例
```

```text
static 方法为什么不能调用非 static 方法/变量：
static 属于类，非 static 属于实例，static 方法执行时可能还没有实例存在。
```

### abstract

```text
abstract 修饰：
1. 类 —— 抽象类，不能实例化，可以有抽象方法和具体方法
2. 方法 —— 抽象方法，无方法体，子类必须实现（除非子类也是抽象类）
```

## 接口与抽象类

**问题 1：接口和抽象类的区别？**

| 维度 | 接口 | 抽象类 |
|------|------|--------|
| 关键字 | interface | abstract class |
| 继承数量 | 可多实现 | 单继承 |
| 方法 | 抽象 + default/static（JDK8+） | 抽象 + 具体 |
| 字段 | 常量（public static final） | 任意字段 |
| 构造器 | 无 | 有 |
| 访问修饰 | 方法默认 public | 无限制 |

```text
使用场景：
1. 定义能力/契约，多种无关类都需要 → 接口（Runnable、Comparable、Serializable）
2. 有共同状态或部分共同实现 → 抽象类
3. 既需要模板方法又需要多种契约 → 抽象类实现接口
```

**问题 2：JDK 8+ 接口的新特性？**

```text
JDK 8：
1. default 方法 —— 默认实现，实现类可继承可重写，用于向后兼容扩展
2. static 方法 —— 接口静态方法，只能接口名调用

JDK 9：
3. private 方法 —— 供 default/static 方法复用内部逻辑

冲突解决：类继承的父类方法和接口 default 方法冲突时，父类方法优先。
实现多个接口的 default 方法冲突时，必须显式重写。
```

## 重载与重写

**问题：重载和重写的区别？**

| 维度 | 重载 Overload | 重写 Override |
|------|--------------|--------------|
| 位置 | 同类 | 父子类 |
| 方法名 | 相同 | 相同 |
| 参数 | 必须不同（个数/类型/顺序） | 必须相同 |
| 返回值 | 可不同 | 相同或协变（子类型） |
| 访问权限 | 无限制 | 不能比父类更严格 |
| 异常 | 无限制 | 不能抛比父类更宽泛的受检异常 |
| 时机 | 编译期（静态分派） | 运行期（动态分派） |

```java
// 重载：同类，参数不同
public void print(int i) { }
public void print(String s) { }

// 重写：子类重写父类方法，访问权限不缩小
@Override
public String toString() { return name; }
```

```text
注意：仅返回值不同不构成重载，编译报错。
重写不能用 static/private/final 方法（这些不可被重写）。
```

## 异常体系

**问题 1：Exception 和 Error 的区别？**

```text
Throwable
├── Error —— 系统级错误，程序无法处理（OutOfMemoryError、StackOverflowError）
└── Exception
    ├── 受检异常（Checked）—— 编译期强制处理（IOException、SQLException）
    └── 非受检异常（Unchecked）—— RuntimeException 及子类（NPE、IndexOutOfBounds）
```

```text
处理原则：
1. 可恢复的错误 → 捕获处理
2. 不可恢复的程序 bug → 让它抛出来，别吞异常
3. 受检异常要么 try-catch 要么 throws 声明
```

**问题 2：finally 中 return 的执行顺序？**

```java
public int test() {
    try {
        return 1;          // 先计算返回值 1，暂存
    } finally {
        return 2;          // finally 的 return 覆盖暂存值
    }
}
// 返回 2
```

```text
finally 中避免写 return，会覆盖 try/catch 的返回值，掩盖异常。
只有 System.exit() 才能阻止 finally 执行。
```

**问题 3：try-with-resources？**

```java
try (BufferedReader br = new BufferedReader(new FileReader("a.txt"))) {
    return br.readLine();
}   // 自动调用 close()，无需 finally 手动关闭
```

```text
try-with-resources 要求资源实现 AutoCloseable（JDK 7+）。
关闭顺序与声明顺序相反，先声明后关闭。
```

## 泛型

**问题 1：什么是类型擦除？**

```text
泛型只在编译期生效，编译后擦除为原始类型（上界或 Object）。
ArrayList<Integer> 和 ArrayList<String> 编译后都是 ArrayList。

好处：向后兼容旧字节码。
坏处：运行时拿不到泛型类型信息，不能 new T()、不能 instanceof 泛型。
```

**问题 2：泛型通配符？**

```text
? —— 无界通配符，List<?>
? extends T —— 上界，只能读不能写（生产者，PECS 中的 P）
? super T —— 下界，只能写不能读（消费者，PECS 中的 S）
```

```java
// PECS：Producer Extends, Consumer Super
void copy(List<? extends Number> src, List<? super Number> dest) {
    for (Number n : src) {   // 读，用 extends
        dest.add(n);          // 写，用 super
    }
}
```

## 反射

**问题 1：反射是什么？有什么用？**

```text
反射：运行时动态获取类的信息（构造器、字段、方法、注解）并操作对象。

应用场景：
1. 框架核心 —— Spring 依赖注入、MyBatis 映射、序列化框架
2. JDK 动态代理
3. 注解处理器
4. 读取配置文件动态创建对象
```

```java
Class<?> clazz = Class.forName("com.example.User");
Object obj = clazz.getDeclaredConstructor().newInstance();
Method m = clazz.getDeclaredMethod("setName", String.class);
m.setAccessible(true);         // 绕过访问控制
m.invoke(obj, "zhangsan");
```

**问题 2：获取 Class 对象的三种方式？**

```text
1. Class.forName("全限定类名") —— 会触发类加载初始化
2. 对象.getClass()
3. 类名.class —— 不触发初始化
```

## 注解

**问题 1：注解的元注解？**

```text
@Target —— 注解作用位置（TYPE/METHOD/FIELD/PARAMETER 等）
@Retention —— 保留级别（SOURCE 源码 / CLASS 字节码 / RUNTIME 运行时）
@Documented —— 是否写入 javadoc
@Inherited —— 是否被子类继承
```

**问题 2：自定义注解 + 处理？**

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Log {
    String value() default "";
}

// 通过反射读取
Method m = obj.getClass().getMethod("test");
Log log = m.getAnnotation(Log.class);
```

```text
RUNTIME 级别注解可通过反射读取（Spring @Transactional 等）。
注解处理三大方式：反射（运行时）、APT 注解处理器（编译期，如 Lombok）、AOP 切面。
```

## 值传递与引用传递

**问题：Java 是值传递还是引用传递？**

```text
Java 只有值传递（Pass by Value）：
1. 基本类型 —— 传值副本，方法内修改不影响原值
2. 引用类型 —— 传引用副本（指向同一对象），方法内修改对象内容影响原对象，
   但修改引用本身（重新 new）不影响原引用
```

```java
void change(int x, User u) {
    x = 100;                 // 改副本，不影响调用方
    u.setName("new");        // 改对象内容，影响调用方
    u = new User();          // 改引用本身，不影响调用方
}
```

## 深拷贝与浅拷贝

**问题：深拷贝和浅拷贝的区别？**

```text
浅拷贝 —— 复制对象本身，引用字段仍指向原对象（共享内部对象）
深拷贝 —— 复制对象及所有引用字段指向的对象（完全独立）
```

```java
// 深拷贝实现方式
1. 实现 Cloneable + 重写 clone，内部对象也 clone
2. 序列化（实现 Serializable，序列化再反序列化）
3. 手动 new 并逐字段复制
4. 用第三方库（commons-lang SerializationUtils、fastjson）
```

```text
Cloneable 的 clone() 默认是浅拷贝，需要深拷贝必须手动实现。
注意：clone() 是 protected native 方法，重写时访问权限放宽为 public。
```

## Object 类方法

**问题：Object 类有哪些方法？**

```text
1. equals() —— 判断相等（默认比地址）
2. hashCode() —— 哈希值
3. toString() —— 对象字符串表示（默认 类名@十六进制哈希）
4. getClass() —— 运行时类
5. clone() —— 克隆（protected，需实现 Cloneable）
6. finalize() —— 垃圾回收前回调（JDK 9 已废弃，不可靠）
7. notify/notifyAll/wait —— 线程等待唤醒
8. finalize 之外，还有 registerNatives 等 native 方法
```

```text
重写 equals 必重写 hashCode；重写 toString 便于日志排查。
finalize 不要依赖它做资源释放，用 try-with-resources 或显式 close。
```

## Java 8 新特性

**问题 1：Java 8 有哪些新特性？**

```text
1. Lambda 表达式 —— 简化匿名内部类
2. 函数式接口 —— @FunctionalInterface（Consumer/Supplier/Function/Predicate）
3. Stream API —— 流式处理集合（filter/map/reduce/collect）
4. Optional —— 优雅处理 null
5. 接口 default/static 方法
6. 新时间 API —— java.time（LocalDate/LocalDateTime）
7. 方法引用 —— Class::method
```

**问题 2：Optional 的作用？**

```java
Optional<User> user = Optional.ofNullable(findById(id));
String name = user.map(User::getName).orElse("unknown");
user.ifPresent(u -> save(u));
```

```text
Optional 强制调用方显式处理 null，避免 NPE。
不要用 Optional 做字段、方法参数，只用于返回值。
```

## BigDecimal 精度

**问题：浮点数运算为什么有精度问题？**

```java
System.out.println(0.1 + 0.2);   // 0.30000000000000004
```

```text
double/float 用二进制无法精确表示十进制小数（0.1 是无限循环二进制），
金额计算必须用 BigDecimal。
```

```java
// 正确：用字符串构造
BigDecimal a = new BigDecimal("0.1");
BigDecimal b = new BigDecimal("0.2");
a.add(b);                     // 0.3

// 错误：new BigDecimal(0.1) 仍是近似值
// 除法要指定精度和舍入模式，否则可能 ArithmeticException
a.divide(b, 2, RoundingMode.HALF_UP);
```

## 面试重点总结

```text
高频考点：
1. == vs equals，hashCode 与 equals 约定（必考）
2. String 不可变 + 常量池 + StringBuilder 区别（必考）
3. Integer 缓存（-128~127，必考）
4. 接口 vs 抽象类（必考）
5. 重载 vs 重写（必考）
6. 异常体系（受检/非受检、finally return）
7. 泛型类型擦除、PECS
8. 反射机制与应用场景
9. Java 只有值传递
10. 深拷贝 vs 浅拷贝
11. Java 8 新特性（Lambda/Stream/Optional）
12. BigDecimal 精度
```
