---
title: JVM 字节码
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, jvm, bytecode, class-file, javap]
---

# JVM 字节码

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Class 文件结构详解](#class-文件结构详解)
- [常量池](#常量池)
- [方法表与 Code 属性](#方法表与-code-属性)
- [字段表](#字段表)
- [属性表](#属性表)
- [关键操作码 (Opcode)](#关键操作码-opcode)
- [javap 反编译实战](#javap-反编译实战)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

字节码是 JVM 的"中间语言"——Java 代码编译后不是机器码，而是字节码指令。理解字节码让你能看懂编译器的优化行为、分析方法调用的本质、读懂 IDE 反编译的结果。

常用工具：
- `javap -c` — 反编译方法字节码
- `javap -verbose` — 查看完整 Class 文件结构
- `javap -p` — 显示所有成员（含 private）

## Class 文件结构详解

每个 `.class` 文件严格遵循以下格式：

```
ClassFile {
    u4             magic;               // 0xCAFEBABE
    u2             minor_version;       // 次版本号
    u2             major_version;       // 主版本号
    u2             constant_pool_count; // 常量池条目数 + 1
    cp_info        constant_pool[constant_pool_count-1];
    u2             access_flags;        // 访问标志
    u2             this_class;          // 本类 → 常量池索引
    u2             super_class;         // 父类 → 常量池索引
    u2             interfaces_count;
    u2             interfaces[interfaces_count];
    u2             fields_count;
    field_info     fields[fields_count];
    u2             methods_count;
    method_info    methods[methods_count];
    u2             attributes_count;
    attribute_info attributes[attributes_count];
}
```

### 版本号对照

| 主版本号 | JDK 版本 |
|----------|----------|
| 52 | JDK 8 |
| 55 | JDK 11 |
| 61 | JDK 17 |
| 65 | JDK 21 |

### 访问标志 (access_flags)

```
ACC_PUBLIC    0x0001  public
ACC_FINAL     0x0010  final
ACC_SUPER     0x0020  JDK 1.0.2 后始终有
ACC_INTERFACE 0x0200  接口
ACC_ABSTRACT  0x0400  抽象类
ACC_SYNTHETIC 0x1000  编译器生成
ACC_ANNOTATION 0x2000 注解
ACC_ENUM      0x4000 枚举
```

## 常量池

常量池是 Class 文件中**最大、最复杂**的部分——存两类常量：

### 字面量（Literal）

```java
String s = "hello";   // "hello" 进入常量池（CONSTANT_String_info）
int MAX = 100;         // 100 进入常量池（CONSTANT_Integer_info）
long BIG = 999999L;   // 进入常量池（CONSTANT_Long_info）
```

### 符号引用（Symbolic Reference）

```
CONSTANT_Class_info          → 类/接口的全限定名
CONSTANT_Fieldref_info       → 字段的类名+字段名+描述符
CONSTANT_Methodref_info      → 方法的类名+方法名+描述符
CONSTANT_InterfaceMethodref_info → 接口方法引用
CONSTANT_NameAndType_info    → 名称+类型描述符
```

用 `javap -verbose` 可以看到常量池的完整内容：

```
#1 = Methodref    #6.#20    // java/lang/Object."<init>":()V
#2 = String       #21       // hello
#3 = Fieldref     #5.#22    // HelloWorld.message:Ljava/lang/String;
#4 = Class        #23       // HelloWorld
...
```

## 方法表与 Code 属性

每个方法的字节码存在 `Code` 属性中：

```
method_info {
    access_flags     // public/static/native 等
    name_index       // 方法名 → 常量池索引
    descriptor_index // 方法描述符 → 常量池索引
    attributes[] {
        Code {
            max_stack      // 操作数栈最大深度
            max_locals     // 局部变量表大小
            code[]         // 字节码指令数组
            exception_table[] // 异常处理表
            attributes[] {
                LineNumberTable  // 字节码行号 → 源码行号
                LocalVariableTable // 局部变量信息
                StackMapTable     // 类型检查用
            }
        }
        Exceptions   // 方法声明的 throws 异常
    }
}
```

### 方法描述符

```
(I)J                  → long method(int)
(Ljava/lang/String;)V → void method(String)
(II)I                 → int method(int, int)
()Ljava/lang/String;  → String method()
```

## 字段表

```java
field_info {
    access_flags      // public/private/static/final/volatile/transient
    name_index        // 字段名
    descriptor_index  // 字段类型描述符
    attributes[] {
        ConstantValue  // static final 常量的值
        Signature      // 泛型签名
    }
}
```

## 属性表

常用属性：

| 属性 | 位置 | 作用 |
|------|------|------|
| Code | method_info | 方法的字节码指令 |
| LineNumberTable | Code | 字节码 ↔ 源码行号映射（调试用） |
| LocalVariableTable | Code | 局部变量名和类型（调试用） |
| StackMapTable | Code | 类型检查框架使用 |
| ConstantValue | field_info | static final 常量值 |
| Exceptions | method_info | throws 声明的异常 |
| Signature | 类/方法/字段 | 泛型类型签名 |
| SourceFile | ClassFile | 源文件名 |

## 关键操作码 (Opcode)

### 加载与存储

```
iconst_0 ~ iconst_5  // 将 int 常量 0-5 压栈
bipush 100           // 将 byte 值 100 压栈
sipush 1000          // 将 short 值 1000 压栈
ldc "hello"          // 从常量池加载字符串/常量
iload_0              // 从局部变量槽 0 加载 int
istore_0             // 将栈顶 int 存入槽 0
aload_0              // 从槽 0 加载引用
astore_1             // 将栈顶引用存入槽 1
```

### 算术运算

```
iadd / isub / imul / idiv / irem  // int 加减乘除取余
ladd / lsub / ...                 // long 版本
dadd / dsub / ...                 // double 版本
iinc 0, 1                         // 局部变量槽 0 的值 +1
```

### 对象操作

```
new #5               // 创建对象（常量池索引 #5 指向类）
getfield #6          // 获取实例字段
putfield #7          // 设置实例字段
getstatic #8         // 获取静态字段
putstatic #9         // 设置静态字段
checkcast #10        // 类型转换检查
instanceof #11       // instanceof 检查
```

### 方法调用（最重要）

```
invokevirtual #12    // 调用实例方法（虚方法，按实际类型分派）
invokespecial #13    // 调用构造方法、private 方法、父类方法
invokestatic  #14    // 调用静态方法
invokeinterface #15  // 调用接口方法
invokedynamic  #16   // 动态方法调用（Lambda 的底层实现）
```

### 控制转移

```
ifeq 20     // 栈顶 int == 0 则跳转到偏移量 20
ifne 20     // 栈顶 int != 0 则跳转
if_icmpeq 20 // 栈顶两个 int 相等则跳转
goto 20     // 无条件跳转
tableswitch // switch-case（密集）—— 跳转表
lookupswitch // switch-case（稀疏）—— 二分查找
```

### 同步

```
monitorenter  // 进入 synchronized 块
monitorexit   // 退出 synchronized 块
```

## javap 反编译实战

```java
// 源码
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    public static void main(String[] args) {
        Calculator c = new Calculator();
        System.out.println(c.add(1, 2));
    }
}
```

```bash
javac Calculator.java
javap -c Calculator
```

输出分析：

```
public int add(int, int);
  Code:
     0: iload_1        # 加载参数 a 到栈顶
     1: iload_2        # 加载参数 b 到栈顶
     2: iadd           # a + b
     3: ireturn        # 返回结果

public static void main(java.lang.String[]);
  Code:
     0: new           #2  // class Calculator
     3: dup               // 复制栈顶引用（一个给构造，一个给变量）
     4: invokespecial #3  // Calculator."<init>":()V
     7: astore_1          // c = 新对象
     8: getstatic     #4  // System.out
    11: aload_1           // 加载 c
    12: iconst_1          // 常量 1
    13: iconst_2          // 常量 2
    14: invokevirtual #5  // c.add(1, 2)
    17: invokevirtual #6  // println(结果)
    20: return
```

## 应用场景实战

### 场景一：确认 try-finally 的编译结果

```bash
javap -c SomeClass | grep -A 20 "someMethod"
# 可以看到编译器自动在每条 return 前插入了 finally 的逻辑
# 以及异常表中有 "any" 类型的 handler 指向 finally
```

### 场景二：理解 String 拼接的优化

```java
String s = "a" + "b" + "c";
// 编译优化后：String s = "abc"; （常量折叠）

String s = a + b + c;
// 编译为：new StringBuilder().append(a).append(b).append(c).toString()
```

### 场景三：确认 synchronized 的 monitorenter/monitorexit

```bash
javap -c SyncClass
# 可以看到 monitorenter 和两组 monitorexit
# （一组正常退出 + 一组异常退出）
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `UnsupportedClassVersionError` | class 文件版本 > JVM 支持的版本 | `javac --release 8` 降低目标版本 |
| `VerifyError` | 字节码不符合规范（字节码增强出错） | 检查字节码增强库版本 |
| Lambda 实现看不懂 | 编译器生成 `invokedynamic` + 静态方法 | 用 `javap -p -c` 查看生成的合成方法 |

### Opcode 速查卡片

```
加载：aload/iload_0..3、iconst_0..5、ldc、bipush
存储：astore/istore_0..3
算术：iadd/isub/imul/idiv/iinc
对象：new、getfield/putfield、getstatic/putstatic
方法：invokevirtual/special/static/interface/dynamic
跳转：ifeq/ifne/goto/tableswitch
返回：ireturn/lreturn/areturn/return
```

## 总结

- `.class` 文件 = 魔数(CAFEBABE) + 版本号 + 常量池 + 访问标志 + 字段表 + 方法表 + 属性表
- 常量池存字面量(字符串/数字)和符号引用(类/方法/字段)
- 方法的 Code 属性含 max_stack、max_locals、字节码指令数组、异常表
- 5 种方法调用指令：invokevirtual(实例)、invokespecial(构造/private)、invokestatic(静态)、invokeinterface(接口)、invokedynamic(Lambda)
- javap -c 是最常用的字节码分析工具——编译器的秘密都在这
- 字节码增强库（ASM、Byte Buddy、Javassist）就是对 class 文件结构的读写
