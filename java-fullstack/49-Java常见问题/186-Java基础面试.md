---
title: Java 基础面试
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [java面试, equals, hashcode, string, final, static, abstract, interface, 重载, 重写]
---

# Java 基础面试

整理日期：2026-08-13

## 目录

- [== 与 equals](#-与-equals)
- [hashCode 与 equals](#hashcode-与-equals)
- [String 相关](#string-相关)
- [final、static、abstract](#finalstaticabstract)
- [接口与抽象类](#接口与抽象类)
- [重载与重写](#重载与重写)

## == 与 equals

**问题：== 和 equals 的区别？**

```text
== —— 比较引用（地址），基本类型比较值
equals —— 比较内容（对象重写 equals 后）
```

```java
String s1 = new String("hello");
String s2 = new String("hello");
s1 == s2;        // false（不同对象，地址不同）
s1.equals(s2);   // true（内容相同）
```

```text
补充：
1. 基本类型用 == 比较值
2. 对象用 == 比较地址，equals 比较内容
3. String 重写了 equals（比较内容）
4. 自定义对象要重写 equals 才有意义
```

## hashCode 与 equals

**问题：为什么重写 equals 必须重写 hashCode？**

```text
hashCode 和 equals 的约定：
1. 两个对象 equals 相等，hashCode 必须相等
2. hashCode 相等，equals 不一定相等（哈希冲突）
```

```text
为什么必须同时重写：
HashMap/HashSet 先用 hashCode 定位桶，再用 equals 比较

如果只重写 equals 不重写 hashCode：
两个 equals 相等的对象，hashCode 不同，定位到不同桶
→ HashMap 中会出现"两个相等对象"（违反约定）
```

```java
// 正确：同时重写 equals 和 hashCode
@Override
public boolean equals(Object o) {
    // 比较所有关键字段
}

@Override
public int hashCode() {
    // 基于相同字段计算
    return Objects.hash(id, name);
}
```

## String 相关

**问题 1：String 为什么不可变？**

```text
1. String 用 final char[]（JDK 8）或 byte[]（JDK 9）存储
2. 没有提供修改字符数组的方法
3. 不可变的好处：线程安全、常量池复用、HashMap key 安全
```

**问题 2：String、StringBuilder、StringBuffer 区别？**

```text
String —— 不可变（每次修改创建新对象）
StringBuilder —— 可变，线程不安全（快）
StringBuffer —— 可变，线程安全（synchronized，慢）
```

**问题 3：String 的 intern() 和常量池？**

```java
String s1 = "hello";           // 字面量，放常量池
String s2 = new String("hello");  // new 对象，放堆
s1 == s2;   // false

String s3 = s2.intern();       // intern 返回常量池的引用
s1 == s3;   // true
```

## final、static、abstract

### final

```text
final 修饰：
1. 类 —— 不能被继承（String）
2. 方法 —— 不能被重写
3. 变量 —— 不能修改（常量）
```

### static

```text
static 修饰：
1. 变量 —— 类变量（所有实例共享）
2. 方法 —— 类方法（不依赖实例）
3. 代码块 —— 类加载时执行一次
```

### abstract

```text
abstract 修饰：
1. 类 —— 抽象类（不能实例化）
2. 方法 —— 抽象方法（子类必须实现）
```

## 接口与抽象类

**问题：接口和抽象类的区别？**

| 维度 | 接口 | 抽象类 |
|------|------|--------|
| 关键字 | interface | abstract class |
| 多继承 | 可多实现 | 单继承 |
| 方法 | 抽象（JDK8+ 可默认方法） | 抽象 + 具体 |
| 字段 | 常量（public static final） | 任意字段 |
| 构造器 | 无 | 有 |
| 关系 | 实现（implements） | 继承（extends） |

```text
使用场景：
1. 定义能力/契约 → 接口（Runnable、Comparable）
2. 有共同实现/状态 → 抽象类
```

```text
JDK 8+ 接口的新特性：
1. default 方法 —— 默认实现
2. static 方法 —— 静态方法
```

## 重载与重写

**问题：重载和重写的区别？**

| 维度 | 重载 Overload | 重写 Override |
|------|--------------|--------------|
| 定义 | 同类，方法名相同参数不同 | 子类重写父类方法 |
| 参数 | 必须不同 | 必须相同 |
| 返回值 | 可不同 | 相同或子类 |
| 运行时 | 编译期确定 | 运行期确定（多态） |
| 注解 | 无 | @Override |

```java
// 重载：同类，参数不同
public void print(int i) { ... }
public void print(String s) { ... }

// 重写：子类重写父类方法
@Override
public String toString() { ... }
```

## 面试重点总结

```text
高频考点：
1. == vs equals（必考）
2. hashCode 和 equals 的关系（必考）
3. String 不可变 + 常量池
4. String/StringBuilder/StringBuffer 区别
5. 接口 vs 抽象类
6. 重载 vs 重写
7. final/static/abstract 关键字
```
