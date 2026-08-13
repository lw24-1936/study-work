---
title: Object 类
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, object, equals, hashcode]
---

# Object 类

整理日期：2026-08-12

## 目录

- [Object —— 所有类的根](#object--所有类的根)
- [equals](#equals)
- [hashCode](#hashcode)
- [toString](#tostring)
- [clone](#clone)
- [getClass](#getclass)
- [wait / notify / notifyAll](#wait--notify--notifyall)

## Object — 所有类的根

`java.lang.Object` 是所有 Java 类的超类——每个类都直接或间接继承 Object。Object 定义了 11 个方法（其中 12 个若算上 `finalize` 这个已废弃的），最常用的是以下 6 个：

```java
public class Object {
    public boolean equals(Object obj) { ... }
    public int hashCode() { ... }
    public String toString() { ... }
    protected Object clone() { ... }
    public final Class<?> getClass() { ... }
    // 线程通信方法
    public final void wait() { ... }
    public final void notify() { ... }
    public final void notifyAll() { ... }
}
```

## equals

`equals` 的默认实现就是 `==`——比较引用地址。大多数情况下这不是我们想要的，需要重写。

```java
public class User {
    private Long id;
    private String name;

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;                 // 同一引用
        if (obj == null || getClass() != obj.getClass()) return false;  // null 或类型不同
        User other = (User) obj;
        return Objects.equals(this.id, other.id);     // 业务相等逻辑
    }
}
```

重写 equals 的规则（约定）：

1. **自反性**：`x.equals(x)` 永远为 true
2. **对称性**：`x.equals(y)` 为 true，那么 `y.equals(x)` 也为 true
3. **传递性**：`x.equals(y)` 且 `y.equals(z)` → `x.equals(z)`
4. **一致性**：对象没变，多次调用结果不变
5. **非 null 性**：`x.equals(null)` 永远为 false

> 实际开发中很少手写 equals/hashCode——用 Lombok 的 `@EqualsAndHashCode` 或 IDE 自动生成。JDK 17+ 可以直接用 `record`，它自动实现 equals/hashCode/toString。

## hashCode

`hashCode` 返回对象的哈希码（int），配合基于哈希的集合（HashMap、HashSet）使用。

**equals 和 hashCode 的约定：**

- 两个对象 equals 为 true → hashCode 必须相等
- 两个对象 hashCode 相等 ⇏ equals 为 true（哈希冲突）
- 两个对象 hashCode 不相等 → equals 一定为 false

```java
public class User {
    private Long id;

    @Override
    public boolean equals(Object obj) {
        // ... (基于 id)
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);   // Objects.hash() 是便捷工具
    }
}
```

不重写 hashCode 的后果：两个 User 对象 `id` 相同，`equals` 返回 true，但因为 hashCode 不同（Object 默认实现返回内存地址的哈希），放到 HashSet 里会出现"逻辑上相同的对象存了两份"。

```java
Set<User> set = new HashSet<>();
User u1 = new User(1L);
User u2 = new User(1L);
set.add(u1);
set.add(u2);
System.out.println(set.size());   // 没重写 hashCode: 2（错误）
                                  // 正确重写：1
```

| 场景 | 必须重写什么 |
|------|-------------|
| 不做哈希容器 key | equals 够了（不推荐） |
| 做 HashMap key 或放进 HashSet | equals **和** hashCode |
| Lombok `@Data` / `@EqualsAndHashCode` | 自动生成，不需要手写 |
| 用 record（Java 17+） | 自动生成，不需要手写 |

## toString

默认实现返回 `类名@十六进制哈希码`（如 `User@3e2a8b`）。重写用于调试和日志：

```java
@Override
public String toString() {
    return "User{id=" + id + ", name='" + name + "'}";
}
```

```java
User user = new User(1L, "Tom");
System.out.println(user);  // User{id=1, name='Tom'}
// 不重写的话输出：User@3e2a8b（毫无意义）
```

Lombok `@ToString` 或 IDE 生成的 toString 已经足够好。值得注意的点：`toString` 中包含任何字段都可能被日志系统反射调用，避免在 `toString` 中执行有副作用的操作（比如调 RPC）。

## clone

`clone` 创建对象的浅拷贝。它是 `protected` 的，需要类实现 `Cloneable` 接口并重写为 `public`：

```java
public class User implements Cloneable {
    private String name;
    private List<String> tags;

    @Override
    public User clone() {
        try {
            User cloned = (User) super.clone();    // 浅拷贝
            cloned.tags = new ArrayList<>(this.tags); // 深拷贝可变字段
            return cloned;
        } catch (CloneNotSupportedException e) {
            throw new AssertionError();            // 不应该发生
        }
    }
}
```

浅拷贝：基本类型字段复制值，引用类型字段复制引用（新旧对象指向同一个 List 等可变对象）。

`clone` 设计上有缺陷（Cloneable 没有 clone 方法、默认是浅拷贝、不调构造方法可能破坏不变量）。现代 Java 中更推荐：
- **拷贝构造方法**：`public User(User other) { ... }`
- **静态工厂**：`public static User copyOf(User other) { ... }`

## getClass

返回对象的运行时类型（Class 对象）。`final` 方法，不能重写：

```java
User user = new User();
Class<?> clazz = user.getClass();
System.out.println(clazz.getName());        // "com.example.User"
System.out.println(clazz.getSimpleName());  // "User"
```

`getClass()` 和 `instanceof` 的区别：

```java
Object obj = new Dog();
obj.getClass() == Animal.class        // false — getClass 返回精确类型
obj instanceof Animal                 // true — instanceof 检查继承链
```

## wait / notify / notifyAll

这三个方法是 Java 线程通信的基础机制，用于实现"等待-通知"模式。详细内容在后续并发编程篇展开，这里只讲签名和用途：

```java
Object lock = new Object();

// 线程 A：等待
synchronized (lock) {
    while (conditionNotMet) {       // 用 while 而不是 if！
        lock.wait();                 // 释放锁并阻塞，直到被 notify
    }
    // 条件满足，继续执行
}

// 线程 B：通知
synchronized (lock) {
    conditionMet = true;
    lock.notify();                   // 唤醒一个等待的线程
    // 或 lock.notifyAll();          // 唤醒所有等待的线程
}
```

三个方法都是 `final`，不能重写。调用前提是**当前线程持有该对象的锁**（必须在 synchronized 代码块/方法内调用否则抛 `IllegalMonitorStateException`）。

实际开发中极少直接使用 wait/notify——`java.util.concurrent` 包提供了更好的抽象（Lock、Condition、CountDownLatch、BlockingQueue 等）。
