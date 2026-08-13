---
title: Java 注解
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, core-api, annotation, reflection]
---

# Java 注解

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [内置注解](#内置注解)
- [元注解](#元注解)
- [自定义注解](#自定义注解)
- [注解的属性类型](#注解的属性类型)
- [运行时注解处理（反射）](#运行时注解处理反射)
- [编译时注解处理（Annotation Processor）](#编译时注解处理annotation-processor)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

注解（Annotation）是 JDK 5 引入的元数据机制——给代码贴上标签，本身不影响代码执行，但可以被编译器、IDE、框架、运行时反射读取并据此执行特定逻辑。

Java 注解体系分三个层次：
1. **内置注解**：Java 语言提供的（`@Override`、`@Deprecated` 等）
2. **元注解**：用来定义其他注解的注解（`@Retention`、`@Target` 等）
3. **自定义注解**：开发者自己定义的注解

三个典型处理时机：
- **编译期**：编译器检测（`@Override` 检查是否真的重写了方法）
- **编译时**：注解处理器（APT）生成代码（Lombok、MapStruct）
- **运行时**：反射读取注解并执行逻辑（Spring、JUnit）

## 内置注解

Java 提供的内置注解分为两类：编译器使用的和标记过时/抑制警告的。

```java
// 1. @Override —— 告诉编译器这是重写方法
class Parent {
    public void doWork() { }
}
class Child extends Parent {
    @Override
    public void doWork() { }  // 如果方法签名不对，编译报错
}

// 2. @Deprecated —— 标记已过时（JDK 9+ 有 since 和 forRemoval 属性）
@Deprecated(since = "9", forRemoval = true)
public class OldClass { }

// 3. @SuppressWarnings —— 抑制编译警告
@SuppressWarnings({"unchecked", "rawtypes"})
public List getRawList() { return new ArrayList(); }

// 4. @SafeVarargs —— 声明可变参数方法不是类型不安全的（JDK 7+）
@SafeVarargs
public final <T> List<T> asList(T... elements) { ... }

// 5. @FunctionalInterface —— 标记函数式接口（JDK 8+）
@FunctionalInterface
public interface Runnable {
    void run();
}
```

## 元注解

元注解是写在（自定义）注解定义上的注解，控制注解的行为和适用范围：

```java
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)   // 保留到运行时
@Target(ElementType.TYPE)             // 只能用在类/接口上
@Documented                           // 生成 Javadoc 时包含此注解
@Inherited                            // 子类继承父类的此注解
public @interface MyAnnotation { }
```

### @Retention —— 保留策略

| RetentionPolicy | 保留阶段 | 能否反射获取 | 典型用途 |
|-----------------|----------|--------------|----------|
| `SOURCE` | 源码，编译时丢弃 | 不能 | `@Override`、`@SuppressWarnings` |
| `CLASS` | class 文件，JVM 不加载 | 不能 | Lombok 的 `@Data`、APT 处理的注解 |
| `RUNTIME` | 运行时保留在 JVM 中 | 能 | Spring 的 `@Autowired`、JUnit 的 `@Test` |

未指定 `@Retention` 时默认是 `CLASS`。

### @Target —— 适用范围

| ElementType | 适用范围 |
|-------------|----------|
| `TYPE` | 类、接口、枚举 |
| `FIELD` | 字段（含枚举常量） |
| `METHOD` | 方法 |
| `PARAMETER` | 方法参数 |
| `CONSTRUCTOR` | 构造方法 |
| `LOCAL_VARIABLE` | 局部变量 |
| `ANNOTATION_TYPE` | 注解类型 |
| `PACKAGE` | 包（用在 `package-info.java`） |
| `TYPE_PARAMETER` | 泛型类型参数（JDK 8+） |
| `TYPE_USE` | 任何使用类型的地方（JDK 8+） |
| `MODULE` | 模块声明（JDK 9+） |

```java
@Target({ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface NotNull { }
```

### @Documented 与 @Inherited

```java
// @Documented —— 生成 Javadoc 时把此注解也写入文档
@Documented
@Retention(RetentionPolicy.RUNTIME)
public @interface ApiDoc { String value(); }

// @Inherited —— 子类自动继承父类的此注解
// 注意：@Inherited 只对 TYPE 的注解有效（类继承链），接口实现不继承
@Inherited
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface Inheritable { }

@Inheritable
class Parent { }

class Child extends Parent { }
// Child 继承了 @Inheritable，Child.class.isAnnotationPresent(Inheritable.class) 为 true
```

### @Repeatable —— 可重复注解（JDK 8+）

```java
// 容器注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Roles {
    Role[] value();
}

// 标注 @Repeatable，指向容器注解
@Repeatable(Roles.class)
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Role {
    String value();
}

// 使用 —— 可以写多个同名的 @Role 注解
@Role("admin")
@Role("editor")
public class UserService { }

// 反射获取
Role[] roles = UserService.class.getAnnotationsByType(Role.class);
// 或
Roles container = UserService.class.getAnnotation(Roles.class);
```

## 自定义注解

```java
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Test {
    // 没有属性 —— 标记注解（Marker Annotation）
}
```

带属性的注解：

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface ApiOperation {
    String value();                    // 默认名 value —— 使用时可以省略名
    String notes() default "";         // 带默认值的属性
    String[] tags() default {};        // 数组属性
}

// 使用
@ApiOperation(value = "查询用户", notes = "根据ID查询", tags = {"user", "read"})
// 如果只给 value 赋值，可以省略属性名：
@ApiOperation("查询用户")
```

## 注解的属性类型

注解方法（属性）的返回值只能是以下类型：

- 八种基本类型（`int`、`boolean` 等）
- `String`
- `Class`
- 枚举
- 其他注解
- 以上类型的**一维数组**

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Config {
    String name();                     // String
    int port() default 8080;           // int + 默认值
    Class<?> handler() default Void.class;  // Class
    Retry retry() default @Retry;      // 注解
    String[] profiles() default {"dev"};    // String 数组
}

// 嵌套注解
public @interface Retry {
    int times() default 3;
    int delay() default 1000;  // ms
}

// 使用
@Config(
    name = "order-service",
    port = 8081,
    retry = @Retry(times = 5, delay = 2000),
    profiles = {"dev", "staging"}
)
public class AppConfig { }
```

## 运行时注解处理（反射）

运行时注解通过反射读取，这是 Spring 框架的基石：

```java
// 定义一个注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Column {
    String name();
}

// 使用
public class User {
    @Column(name = "user_id")
    private Long id;

    @Column(name = "user_name")
    private String name;
}

// 运行时处理
public class AnnotationProcessor {
    public static void printColumns(Class<?> clazz) {
        for (Field field : clazz.getDeclaredFields()) {
            if (field.isAnnotationPresent(Column.class)) {
                Column column = field.getAnnotation(Column.class);
                System.out.println(field.getName() + " -> " + column.name());
            }
        }
    }
}

// 输出：
// id -> user_id
// name -> user_name
```

```java
// 反射获取注解的完整 API
Class<MyClass> clazz = MyClass.class;

// 判断注解是否存在（考虑 @Inherited）
boolean present = clazz.isAnnotationPresent(MyAnnotation.class);

// 获取指定注解
MyAnnotation ann = clazz.getAnnotation(MyAnnotation.class);

// 获取所有注解
Annotation[] all = clazz.getAnnotations();

// 获取直接声明的注解（不考虑 @Inherited）
Annotation[] declared = clazz.getDeclaredAnnotations();

// JDK 8+ 获取可重复注解
MyAnnotation[] repeats = clazz.getAnnotationsByType(MyAnnotation.class);
```

## 编译时注解处理（Annotation Processor）

APT（Annotation Processing Tool）在编译期处理注解，常用于生成代码——Lombok、MapStruct、Dagger 都是这么干的。

```java
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import javax.tools.Diagnostic;
import java.util.Set;

@SupportedAnnotationTypes("com.example.Builder")
@SupportedSourceVersion(SourceVersion.RELEASE_17)
public class BuilderProcessor extends AbstractProcessor {

    @Override
    public boolean process(Set<? extends TypeElement> annotations, 
                           RoundEnvironment roundEnv) {
        for (TypeElement annotation : annotations) {
            for (Element element : roundEnv.getElementsAnnotatedWith(annotation)) {
                // element 是被 @Builder 标注的类
                processingEnv.getMessager().printMessage(
                    Diagnostic.Kind.NOTE, 
                    "Processing: " + element.getSimpleName()
                );
                // 生成 Builder 类...
            }
        }
        return true;
    }
}
```

APT 的核心在 `javax.annotation.processing` 和 `javax.lang.model` 包——`javax.lang.model` 提供源码级的元素模型（比反射更底层），可以遍历类结构、字段、方法然后生成 Java 源文件。

## 应用场景实战

### 场景一：自定义校验框架

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface NotBlank {
    String message() default "不能为空";
}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Range {
    int min() default Integer.MIN_VALUE;
    int max() default Integer.MAX_VALUE;
    String message() default "值不在范围内";
}

// 校验引擎
public class Validator {
    public static void validate(Object obj) throws ValidationException {
        Class<?> clazz = obj.getClass();
        for (Field field : clazz.getDeclaredFields()) {
            field.setAccessible(true);
            try {
                Object value = field.get(obj);
                
                if (field.isAnnotationPresent(NotBlank.class)) {
                    NotBlank ann = field.getAnnotation(NotBlank.class);
                    if (value == null || value.toString().isBlank()) {
                        throw new ValidationException(field.getName() + ": " + ann.message());
                    }
                }
                
                if (field.isAnnotationPresent(Range.class) && value instanceof Number num) {
                    Range ann = field.getAnnotation(Range.class);
                    if (num.intValue() < ann.min() || num.intValue() > ann.max()) {
                        throw new ValidationException(field.getName() + ": " + ann.message());
                    }
                }
            } catch (IllegalAccessException e) {
                throw new ValidationException("无法访问字段: " + field.getName());
            }
        }
    }
}
```

### 场景二：ORM 映射

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Table {
    String name();
}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Id { }

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Column {
    String name();
    boolean nullable() default true;
}

// 实体类
@Table(name = "t_user")
public class User {
    @Id
    @Column(name = "id", nullable = false)
    private Long id;

    @Column(name = "username")
    private String username;
}

// SQL 生成器
public class SqlGenerator {
    public static String generateInsert(Object entity) {
        Class<?> clazz = entity.getClass();
        if (!clazz.isAnnotationPresent(Table.class)) {
            throw new IllegalArgumentException("不是实体类");
        }
        
        Table table = clazz.getAnnotation(Table.class);
        StringBuilder columns = new StringBuilder();
        StringBuilder values = new StringBuilder();
        
        for (Field field : clazz.getDeclaredFields()) {
            if (field.isAnnotationPresent(Column.class)) {
                Column col = field.getAnnotation(Column.class);
                field.setAccessible(true);
                try {
                    if (columns.length() > 0) {
                        columns.append(", ");
                        values.append(", ");
                    }
                    columns.append(col.name());
                    values.append("'").append(field.get(entity)).append("'");
                } catch (IllegalAccessException e) {
                    throw new RuntimeException(e);
                }
            }
        }
        
        return String.format("INSERT INTO %s (%s) VALUES (%s)", 
            table.name(), columns, values);
    }
}
```

### 场景三：权限控制

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface RequirePermission {
    String value();
}

public class AuthInterceptor {
    public static boolean checkPermission(Method method, User user) {
        if (method.isAnnotationPresent(RequirePermission.class)) {
            RequirePermission rp = method.getAnnotation(RequirePermission.class);
            return user.hasPermission(rp.value());
        }
        return true;   // 无注解的方法默认允许
    }
}
```

### 场景四：API 文档生成

```java
// 利用注解自动生成 API 文档
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface ApiDoc {
    String path();
    String method() default "GET";
    String description() default "";
    String[] params() default {};
    String response() default "";
}

public class ApiDocGenerator {
    public static String generateDoc(Class<?> controllerClass) {
        StringBuilder doc = new StringBuilder();
        doc.append("# ").append(controllerClass.getSimpleName()).append("\n\n");
        
        for (Method method : controllerClass.getDeclaredMethods()) {
            if (method.isAnnotationPresent(ApiDoc.class)) {
                ApiDoc api = method.getAnnotation(ApiDoc.class);
                doc.append("## ").append(api.method()).append(" ").append(api.path()).append("\n");
                doc.append(api.description()).append("\n\n");
                if (api.params().length > 0) {
                    doc.append("参数: ").append(String.join(", ", api.params())).append("\n\n");
                }
            }
        }
        return doc.toString();
    }
}
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| 自定义注解在运行时获取不到 | `@Retention` 不是 `RUNTIME` | 加上 `@Retention(RetentionPolicy.RUNTIME)` |
| 注解放在接口上但实现类获取不到 | `@Inherited` 只对类继承有效，接口不继承 | 自己遍历接口链用 `getInterfaces()` 查找 |
| `getAnnotation` 返回 null | 注解不存在或被包在容器里（可重复注解） | 可重复注解用 `getAnnotationsByType` |
| 反射读取 private 字段上的注解失败 | `field.getAnnotation()` 不需要 setAccessible，但 get 字段值需要 | 注解本身不需要 setAccessible |
| 注解属性值在编译时必须确定 | 所有值必须是编译期常量 | 不能用 `new`、不能调方法 |

### 设计建议

1. **慎用 RUNTIME**：如果可以编译期处理（SOURCE/CLASS），就不要保留到 RUNTIME——减少运行时反射开销
2. **value() 作为默认属性名**：如果只有一个属性，叫 `value`——使用时可以省略属性名，更简洁
3. **提供合理的默认值**：让使用者在多数场景下不需要显式指定每个属性
4. **一维数组的属性用空数组做默认值**：不要用 null，避免 NPE
5. **不要过度设计**：不是所有事情都需要注解——简单的配置文件和约定优于配置可能更清晰

## 总结

- 注解是给代码贴标签的元数据机制，本身不改变代码行为
- `@Retention` 决定生命周期：SOURCE（编译丢弃）、CLASS（class 保留）、RUNTIME（运行时可用）
- `@Target` 限制适用范围（类/字段/方法等）；`@Repeatable` 支持重复标注
- 运行时通过反射读取注解；编译时通过 APT 处理注解生成代码
- 设计注解时提供默认属性值，兼容未来的扩展场景
- Spring 全家桶的核心机制就是运行时注解处理——理解注解是理解 Spring 的前提
