---
title: 内部类
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [java, oop, inner-class, nested-class]
---

# 内部类

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [内部类分类](#内部类分类)
- [成员内部类](#成员内部类)
- [静态内部类](#静态内部类)
- [局部内部类](#局部内部类)
- [匿名内部类](#匿名内部类)
- [编译原理](#编译原理)
- [内部类访问外部类成员](#内部类访问外部类成员)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

内部类（Nested Class）是定义在另一个类内部的类。Java 官方把"定义在类内部的类"统称为**嵌套类**，再按是否带 `static` 分为两类：

```text
嵌套类（Nested Class）
├── 静态嵌套类（Static Nested Class）—— 带 static，独立于外部类实例
└── 内部类（Inner Class）—— 非 static，持有外部类引用
    ├── 成员内部类（Member Inner Class）—— 定义在类体，方法外
    ├── 局部内部类（Local Inner Class）—— 定义在方法/代码块内
    └── 匿名内部类（Anonymous Inner Class）—— 没有类名，一次性的
```

中文语境下"内部类"常泛指以上所有，面试和日常说的"内部类"基本等价于"嵌套类"。

为什么需要内部类：

1. 封装 —— 内部类只被外部类使用，对外隐藏实现（迭代器的实现类）
2. 逻辑分组 —— 关系紧密的类放一起，可读性更好
3. 访问外部类私有成员 —— 内部类可以直接访问外部类的 private 字段
4. 实现"多继承"的替代 —— 匿名内部类实现回调，绕开单继承限制
5. 延迟初始化 —— 静态内部类单例利用类加载机制懒加载

## 内部类分类

| 类型 | 位置 | 是否 static | 持有外部类引用 | 访问外部类成员 |
|------|------|-------------|---------------|---------------|
| 成员内部类 | 类体内 | 否 | 是（this$0） | 任意 |
| 静态内部类 | 类体内 | 是 | 否 | 仅静态成员 |
| 局部内部类 | 方法/块内 | 否 | 是 | 任意 + 局部变量(final) |
| 匿名内部类 | 表达式里 | 否 | 是 | 任意 |

## 成员内部类

成员内部类是定义在类体中、方法外的非静态内部类，和字段、方法平级。

```java
public class Outer {
    private String name = "outer";
    private int age = 18;

    class Inner {                       // 成员内部类
        void show() {
            // 直接访问外部类私有成员
            System.out.println(name);   // Outer.this.name
            System.out.println(age);
        }
    }

    public Inner createInner() {
        return new Inner();
    }
}

// 外部创建内部类实例：必须先有外部类实例
Outer outer = new Outer();
Outer.Inner inner = outer.new Inner();   // 语法：outer.new Inner()
inner.show();
```

```text
特点：
1. 内部类可以直接访问外部类的所有成员（含 private）
2. 外部类访问内部类成员，需要先创建内部类实例（new Inner().xxx）
3. 内部类里用 Outer.this 引用外部类实例，用 this 引用内部类实例
4. 成员内部类不能定义 static 字段和方法（除非是常量 static final）
```

```java
public class Outer {
    private int x = 1;

    class Inner {
        private int x = 2;

        void test() {
            int x = 3;
            System.out.println(x);           // 3，局部变量
            System.out.println(this.x);      // 2，内部类字段
            System.out.println(Outer.this.x);// 1，外部类字段
        }
    }
}
```

## 静态内部类

静态内部类（Static Nested Class）用 `static` 修饰，**不持有外部类引用**，行为上更像一个独立的顶层类，只是嵌套在外部类里做命名空间隔离。

```java
public class Outer {
    private static String staticName = "outer-static";
    private String instanceName = "outer-instance";

    static class StaticInner {
        void show() {
            System.out.println(staticName);      // 能访问静态成员
            // System.out.println(instanceName); // 编译错误：不能访问实例成员
        }
    }
}

// 直接 new，不需要外部类实例
Outer.StaticInner inner = new Outer.StaticInner();
```

```text
特点：
1. 不持有外部类引用，创建时不需要外部类实例
2. 只能访问外部类的静态成员
3. 可以定义 static 字段和方法
4. 静态内部类是最推荐的内部类形式——没有隐式引用，避免内存泄漏
```

```text
成员内部类 vs 静态内部类（核心区别）：
成员内部类隐式持有外部类引用（Outer.this），能访问实例成员；
静态内部类不持有外部类引用，只能访问静态成员。
这条区别直接决定了两者的使用场景和内存泄漏风险。
```

## 局部内部类

局部内部类定义在方法或代码块内部，作用域仅限于该方法。

```java
public void process(int threshold) {
    final int localVar = 100;        // 局部内部类访问的局部变量必须是 effectively final

    class LocalInner {               // 局部内部类
        void check() {
            System.out.println(localVar);      // 能访问
            System.out.println(threshold);     // 能访问（effectively final）
        }
    }

    new LocalInner().check();
}
```

```text
为什么访问的局部变量必须 effectively final：

局部变量的生命周期短于内部类对象——方法结束后局部变量销毁，
但内部类对象可能还活着（被返回、被其他对象持有）。

编译器的处理：把局部变量"复制"进内部类的一个字段（capture）。
如果变量可变，两份副本会不一致，语义就乱了。
所以 Java 强制要求局部变量赋值后不再改变（effectively final），
保证复制后内部类看到的值和外部一致。
```

```text
effectively final：变量没有被 final 修饰，但赋值后从未改变，也算。
JDK 8 之前要求显式写 final，JDK 8 起放宽为 effectively final。
```

## 匿名内部类

匿名内部类没有类名，在 `new` 表达式里同时定义类和创建实例，用于一次性实现接口或继承类。

```java
// 实现接口
Runnable r = new Runnable() {
    @Override
    public void run() {
        System.out.println("running");
    }
};

// 继承类并重写方法
Thread t = new Thread() {
    @Override
    public void run() {
        System.out.println("thread running");
    }
};
```

```text
特点：
1. 没有类名，创建后无法复用
2. 只能继承一个类或实现一个接口
3. 不能定义构造方法（用初始化块代替）
4. 编译后生成 Outer$1.class 这类文件
5. 访问的外部局部变量也必须 effectively final
```

```text
匿名内部类 vs Lambda：

匿名内部类只能用于"只含一个抽象方法的接口"时，才能替换成 Lambda。
两者的关键区别是 this 语义：
1. 匿名内部类 —— this 指向匿名类实例
2. Lambda —— this 指向定义 Lambda 的外部类实例

此外 Lambda 用 invokedynamic 实现，不生成 .class 文件，比匿名内部类省内存。
详见 [[29-Lambda]]。
```

```java
public class Test {
    private String name = "outer";

    void test() {
        // 匿名内部类：this 是匿名类实例
        Runnable anon = new Runnable() {
            @Override
            public void run() {
                System.out.println(this.getClass());   // Test$1
            }
        };

        // Lambda：this 是 Test 实例
        Runnable lambda = () -> System.out.println(this.getClass());   // Test
    }
}
```

## 编译原理

内部类在 JVM 层面没有特殊支持，编译后每个内部类都是独立的 .class 文件：

```text
Outer.java 编译产物：
Outer.class                 —— 外部类
Outer$Inner.class           —— 成员内部类
Outer$StaticInner.class     —— 静态内部类
Outer$1LocalInner.class     —— 局部内部类（编号）
Outer$1.class               —— 匿名内部类（按出现顺序编号）
```

```text
非静态内部类的关键机制：
1. 构造器里隐式传入外部类引用，存在字段 this$0 里
2. 内部类通过 this$0 访问外部类成员

用 javap -p Outer$Inner 可以看到：
final Outer this$0;   // 编译器生成的隐式字段
```

## 内部类访问外部类成员

**问题：内部类为什么能访问外部类的 private 成员？**

```text
private 的访问控制是编译期约束，JVM 层面没有 private 屏障。
编译器为了让内部类访问外部类私有成员，做了两件事：

1. 内部类持有外部类引用 this$0（非静态内部类）
2. 外部类为被访问的私有成员生成"静态桥接方法"（合成方法）：
   static int access$000(Outer o) { return o.age; }

内部类通过调用 access$000(this$0) 间接拿到私有字段的值。
```

```java
// 源码
public class Outer {
    private int age = 18;

    class Inner {
        int readAge() {
            return age;              // 直接访问 private
        }
    }
}

// 编译后等效（概念示意，实际是字节码）
class Outer {
    private int age = 18;

    static int access$000(Outer o) {   // 编译器生成的桥接方法
        return o.age;
    }
}

class Outer$Inner {
    final Outer this$0;

    int readAge() {
        return Outer.access$000(this$0);   // 通过桥接方法访问
    }
}
```

```text
副作用：这些 access$xxx 合成方法会被反射、字节码工具看到，
也是某些安全框架（如序列化、代码混淆）需要额外处理内部类的原因。
```

## 应用场景实战

### 场景 1：迭代器模式

集合的迭代器几乎都用内部类实现——迭代器需要访问集合内部的数组/链表结构，用内部类封装最自然。

```java
public class SimpleList<E> {
    private Object[] elements;
    private int size;

    // 内部类迭代器：直接访问外部类私有数组
    private class Itr implements Iterator<E> {
        private int cursor = 0;

        @Override
        public boolean hasNext() {
            return cursor < size;        // 访问外部类私有字段 size
        }

        @Override
        public E next() {
            return (E) elements[cursor++];   // 访问外部类私有数组
        }
    }

    public Iterator<E> iterator() {
        return new Itr();
    }
}
```

JDK 里 `ArrayList.Itr`、`HashMap.Node` 都是这个思路。

### 场景 2：Builder 构建者模式

Builder 用静态内部类实现，链式构建对象，解决构造参数过多的问题。

```java
public class User {
    private final String name;
    private final int age;
    private final String email;

    private User(Builder builder) {
        this.name = builder.name;
        this.age = builder.age;
        this.email = builder.email;
    }

    public static class Builder {        // 静态内部类
        private String name;
        private int age;
        private String email;

        public Builder name(String name) { this.name = name; return this; }
        public Builder age(int age) { this.age = age; return this; }
        public Builder email(String email) { this.email = email; return this; }

        public User build() {
            return new User(this);       // 静态内部类可以访问外部类私有构造器
        }
    }
}

User user = new User.Builder()
    .name("zhangsan")
    .age(20)
    .email("a@b.com")
    .build();
```

### 场景 3：静态内部类单例（Holder 模式）

利用"类在使用时才加载"的机制，实现线程安全的懒加载单例。

```java
public class Singleton {
    private Singleton() { }

    private static class Holder {                    // 静态内部类
        private static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;     // 首次访问 Holder 时才触发类加载，创建实例
    }
}
```

```text
原理：JVM 保证类加载的线程安全，Holder 在首次访问时加载，
INSTANCE 在类加载阶段初始化，既懒加载又线程安全，还不加锁。
```

### 场景 4：事件监听与回调

GUI 和事件驱动场景里，匿名内部类是经典的回调实现。

```java
button.addActionListener(new ActionListener() {
    @Override
    public void actionPerformed(ActionEvent e) {
        System.out.println("clicked");
    }
});
```

## 最佳实践与踩坑记录

### 最佳实践

1. 能用静态内部类就用静态内部类 —— 不持有外部类引用，避免内存泄漏，行为可预测
2. 只在确实需要访问外部类实例成员时才用非静态内部类
3. 需要"一次性"实现接口/回调时用 Lambda（函数式接口）或匿名内部类
4. Builder、Helper、Holder 这类辅助类用静态内部类
5. 内部类不要写得太复杂，逻辑重就抽成独立顶层类

### 踩坑记录

```text
坑 1：非静态内部类导致内存泄漏
结论：非静态内部类隐式持有外部类引用，内部类对象被长期持有（静态集合、线程、回调）
      时外部类无法回收。
原因：内部类的 this$0 强引用外部类，外部类生命周期被内部类拖住。
解法：改用静态内部类 + 显式传入需要的引用，或用完及时解除引用。

坑 2：内部类序列化报错
结论：非静态内部类序列化时，外部类也必须可序列化，否则抛 NotSerializableException。
原因：序列化内部类会连带序列化外部类引用 this$0。
解法：用静态内部类（无外部引用），或让外部类也实现 Serializable。

坑 3：匿名内部类里的 this 不是外部类
结论：匿名内部类里 this 指向匿名类实例，不是外部类，容易写错。
原因：匿名类有自己的 this。
解法：需要外部类引用时用 Outer.this，Lambda 场景直接换 Lambda（this 语义不同）。

坑 4：局部变量修改报错
结论：局部内部类/匿名内部类访问的局部变量必须是 effectively final，修改就编译报错。
原因：编译器把局部变量复制进内部类字段，可变会导致两份数据不一致。
解法：用数组、AtomicReference、成员变量，或改用返回值传递结果。

坑 5：成员内部类里不能定义静态成员
结论：非静态内部类不能有 static 字段和 static 方法（编译报错）。
原因：非静态内部类依赖外部类实例，static 成员不依赖实例，语义冲突。
解法：改成静态内部类，或把静态成员移到外部类。
```

## 相关文档

- [[29-Lambda]] —— 匿名内部类与 Lambda 的区别、this 语义差异
- [[11-接口]] —— 接口与函数式接口
- [[186-Java基础面试]] —— 内部类相关面试题
