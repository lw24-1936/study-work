---
title: Java 基础语法
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, syntax, basics]
---

# Java 基础语法

整理日期：2026-08-12

## 目录

- [1.1 第一个 Java 程序](#11-第一个-java-程序)
- [1.2 注释](#12-注释)
- [1.3 标识符与关键字](#13-标识符与关键字)
- [1.4 变量](#14-变量)
- [1.5 数据类型](#15-数据类型)
- [1.6 类型转换](#16-类型转换)

## 1.1 第一个 Java 程序

### Hello World

```java
// HelloWorld.java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
```

### Java 源文件

Java 源文件以 `.java` 为后缀，文件名必须与其中 `public` 类的类名完全一致（包括大小写）。

一个源文件可以包含多个类，但最多一个 `public` 类：

```java
// User.java — 文件名必须匹配 public class User
public class User {
    String name;
}

class Address {     // 非 public 类，可以共存
    String city;
}
```

### 编译与运行

```bash
# 编译：生成 HelloWorld.class
javac HelloWorld.java

# 运行：JVM 加载 class 并执行 main 方法
java HelloWorld
```

两步分开的好处是 `.class` 文件可以分发到任何装有 JVM 的机器上执行，不需要重新编译。

Java 11 起支持直接运行单个源文件（适合脚本场景）：

```bash
java HelloWorld.java
```

原理是 JVM 在内存中编译后直接执行，不产生 `.class` 文件。

### main 方法

```java
public static void main(String[] args) {
    // 程序入口
}
```

逐个拆解：

- `public` — JVM 需要从外部调用这个方法
- `static` — JVM 还没有创建任何对象，只能调静态方法
- `void` — 程序退出通过 `System.exit(code)` 或自然结束，不靠返回值
- `main` — JVM 约定的入口方法名，大小写敏感
- `String[] args` — 命令行参数。`java HelloWorld a b c` → args = ["a", "b", "c"]

`main` 方法签名也可以用 `String... args`（可变参数），完全等效。

### 类与包

```java
package com.example.study;   // 包声明，必须在文件第一行

public class HelloWorld {     // 类声明
    // 类体
}
```

包的作用：组织代码、避免类名冲突。`com.example.study.HelloWorld` 是全限定类名，编译后的 `.class` 文件在 `com/example/study/HelloWorld.class` 路径下。

## 1.2 注释

Java 有三种注释：

```java
// 单行注释：从 // 到行尾

/*
 * 多行注释：可以跨多行
 * 但不能嵌套
 */

/**
 * 文档注释：用 javadoc 工具生成 API 文档
 * @param name 用户名
 * @return 问候语
 */
public String greet(String name) {
    return "Hello, " + name;
}
```

### Javadoc

```bash
javadoc -d doc -encoding UTF-8 -charset UTF-8 *.java
```

常用 Javadoc 标签：

| 标签 | 用途 | 位置 |
|------|------|------|
| `@param` | 参数说明 | 方法上方 |
| `@return` | 返回值说明 | 方法上方 |
| `@throws` / `@exception` | 抛出的异常 | 方法上方 |
| `@see` | 引用其他类/方法 | 任意位置 |
| `@since` | 引入版本 | 类/方法上方 |
| `@deprecated` | 标记过时 | 类/方法上方 |
| `{@code ...}` | 行内代码格式 | 任意位置 |

编写文档注释的两个原则：1）只写"为什么"不写"是什么"——方法名已经说明了是什么；2）给调用方看，不是给维护者看——关注契约和副作用，不关注内部实现。

## 1.3 标识符与关键字

### 标识符规则

标识符就是给类、方法、变量起的名字。规则：

1. 由字母、数字、下划线 `_`、美元符 `$` 组成
2. 不能以数字开头
3. 不能是关键字或保留字
4. 大小写敏感——`name` 和 `Name` 是两个标识符

### 关键字

Java 有 50+ 个关键字，这里按用途分类：

| 类别 | 关键字 |
|------|--------|
| 访问控制 | `private`, `protected`, `public` |
| 类/方法/变量修饰 | `abstract`, `class`, `extends`, `final`, `implements`, `interface`, `native`, `new`, `static`, `strictfp`, `synchronized`, `transient`, `volatile` |
| 流程控制 | `break`, `case`, `continue`, `default`, `do`, `else`, `for`, `if`, `return`, `switch`, `while` |
| 异常处理 | `try`, `catch`, `finally`, `throw`, `throws` |
| 包相关 | `import`, `package` |
| 基本类型 | `boolean`, `byte`, `char`, `double`, `float`, `int`, `long`, `short` |
| 变量引用 | `super`, `this`, `void` |
| 其他 | `enum`, `assert`, `instanceof` |

### 保留字

`goto` 和 `const` 是保留字——Java 从未使用但也不允许用作标识符。

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 包名 | 全小写，点分隔 | `com.example.study` |
| 类名 | 大驼峰（PascalCase） | `HelloWorld`, `UserService` |
| 方法名 | 小驼峰（camelCase） | `getUserById`, `sendMessage` |
| 变量名 | 小驼峰 | `userId`, `totalPrice` |
| 常量 | 全大写，下划线分隔 | `MAX_SIZE`, `DEFAULT_TIMEOUT` |

方法名通常用动词或动词短语，变量名用名词。布尔类型变量常用 `is` / `has` / `can` 开头（`isEmpty`, `hasNext`, `canExecute`）。

## 1.4 变量

Java 的变量按声明位置和作用域分为三类：

```java
public class User {
    private String name;          // 成员变量（实例变量）
    private static int count;     // 静态变量（类变量）

    public void setName(String n) {
        String trimmed = n.trim(); // 局部变量
        name = trimmed;
    }
}
```

### 局部变量

- 声明在方法、构造方法或代码块内部
- 必须**显式初始化**后才能使用——编译器会阻止读取未初始化的局部变量
- 作用域从声明处到所在代码块结束
- 不存在默认值

### 成员变量（实例变量）

- 声明在类内、方法外，没有 `static` 修饰
- 每个对象拥有独立的副本
- 有默认值：数字类型为 `0`，boolean 为 `false`，引用类型为 `null`
- 只要对象还活着，成员变量就一直存在

### 静态变量（类变量）

- 用 `static` 修饰的成员变量
- 属于类本身，所有对象共享同一个副本
- 在类加载时初始化，类卸载时销毁
- 通过 `类名.变量名` 访问（也支持 `对象.变量名`，但不推荐）

### 常量

`final` 修饰的变量一旦赋值就不能再修改：

```java
final int MAX_USERS = 100;              // 局部常量
private static final String APP_NAME = "MyApp";  // 静态常量（推荐）
```

静态常量是 Java 中"常量"的标准写法：`static final` 组合，命名全大写。编译时常量（用字面量或常量表达式初始化）会被编译器内联——替换到使用处而不是在运行时读取。

## 1.5 数据类型

Java 的数据类型分两大类：基本类型和引用类型。

### 基本数据类型

8 种基本类型，直接存值，不是对象：

| 类型 | 大小 | 范围 | 默认值 | 示例 |
|------|------|------|--------|------|
| `byte` | 1 字节 | -128 ~ 127 | 0 | `byte b = 100;` |
| `short` | 2 字节 | -32768 ~ 32767 | 0 | `short s = 30000;` |
| `int` | 4 字节 | -2^31 ~ 2^31-1 | 0 | `int i = 100000;` |
| `long` | 8 字节 | -2^63 ~ 2^63-1 | 0L | `long l = 100000L;` |
| `float` | 4 字节 | IEEE 754 单精度 | 0.0f | `float f = 3.14f;` |
| `double` | 8 字节 | IEEE 754 双精度 | 0.0d | `double d = 3.14;` |
| `char` | 2 字节 | 0 ~ 65535 (Unicode) | '\u0000' | `char c = 'A';` |
| `boolean` | JVM 相关 | `true` / `false` | false | `boolean ok = true;` |

几个容易踩坑的点：

**整数字面量默认是 `int`**，超过 int 范围要加 `L`：

```java
long big = 10000000000L;  // 不加 L 编译报错：integer number too large
```

**小数字面量默认是 `double`**，赋值给 float 要加 `f`：

```java
float pi = 3.14f;         // 不加 f 编译报错：不兼容的类型
double e = 2.718;          // 默认就是 double，不需要 d
```

**浮点数比较不能直接用 `==`**：

```java
double a = 0.1 + 0.2;      // 0.30000000000000004
double b = 0.3;
System.out.println(a == b); // false

// 正确做法：比较差值
System.out.println(Math.abs(a - b) < 0.000001); // true
```

**char 存 Unicode 码点**，本质是 0-65535 的整数：

```java
char c1 = 'A';
char c2 = 65;             // 等价于 'A'
char c3 = '\u0041';       // Unicode 转义，也等价于 'A'
System.out.println(c1 + 1); // 66（char 参与运算时自动提升为 int）
```

### 引用类型

除了 8 种基本类型，所有其他类型都是引用类型——变量存的是对象的引用（内存地址），不是对象本身。

```java
String s = "hello";           // s 是引用，指向堆中的 "hello" 对象
int[] arr = new int[5];       // arr 是引用，指向堆中的数组对象
User user = new User();       // user 是引用，指向堆中的 User 实例
```

引用类型的默认值是 `null`。对 `null` 调用方法或访问属性会抛 `NullPointerException`。

## 1.6 类型转换

### 自动类型转换（隐式转换）

小范围类型自动转大范围类型，不会丢数据：

```
byte → short → int → long → float → double
                ↑
               char
```

```java
int i = 100;
long l = i;          // int → long，自动
double d = l;        // long → double，自动（可能丢精度）
float f = 3.14f;
double d2 = f;       // float → double，自动

char c = 'A';
int code = c;        // char → int，自动，code = 65
```

### 强制类型转换（显式转换）

大范围转小范围，需要显式写 `(目标类型)`，可能丢数据或溢出：

```java
double d = 3.99;
int i = (int) d;       // i = 3，截断小数，不是四舍五入

long l = 1000L;
int j = (int) l;       // 1000 在 int 范围内，安全

// 溢出示例
int max = Integer.MAX_VALUE;    // 2147483647
int overflow = max + 1;         // -2147483648，静默溢出，不报错
```

### 数值溢出

整型运算结果超出范围不会抛异常，而是静默溢出——这是一个很常见的线上 bug 来源。

```java
int a = 2_000_000_000;
int b = 2_000_000_000;
int c = a + b;                  // 溢出为 -294967296
System.out.println(c);          // 负值，逻辑上的错误结果

// 用 long 接也不行——溢出发生在 int 运算时，赋值之前就错了
long wrong = a + b;             // 仍然是 -294967296

// 正确：至少一个操作数强转成 long
long correct = (long) a + b;    // 4000000000L
```

BigDecimal 和 BigInteger 可以处理任意精度的数值，但性能差很多——只在确实需要时用。

### 类型提升

表达式中混合不同类型时，所有操作数自动提升为"最大"的类型：

- 如果有 `double` → 全部提升为 `double`
- 如果有 `float` → 全部提升为 `float`
- 如果有 `long` → 全部提升为 `long`
- 否则 → 全部提升为 `int`（即使全是 `byte`/`short`/`char`）

```java
byte a = 10;
byte b = 20;
// byte c = a + b;       // 编译错误：a+b 结果是 int
int c = a + b;           // 正确
byte d = (byte) (a + b); // 或者强制转

short s1 = 1;
short s2 = 2;
// short s3 = s1 + s2;   // 编译错误：结果是 int
```

这是新手高频踩坑点：两个 byte 相加结果是 int，赋值给 byte 需要强转。
