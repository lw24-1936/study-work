---
title: Java 异常
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, core-api, exception, error-handling]
---

# Java 异常

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [异常继承体系](#异常继承体系)
- [Checked vs Unchecked Exception](#checked-vs-unchecked-exception)
- [try-catch-finally](#try-catch-finally)
- [try-with-resources](#try-with-resources)
- [throw 与 throws](#throw-与-throws)
- [自定义异常](#自定义异常)
- [异常链](#异常链)
- [多异常捕获](#多异常捕获)
- [异常设计原则](#异常设计原则)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Java 的异常机制是一套完整的错误处理体系——程序运行中发生意外情况时，抛出一个异常对象，调用栈上的代码可以选择捕获处理，也可以让它继续向上传播直到 JVM 默认处理器打印堆栈并终止线程。

与 C 语言返回错误码的对比：

| 维度 | C 错误码 | Java 异常 |
|------|----------|-----------|
| 错误信息 | 一个 int 值 | 完整的异常对象 + 堆栈跟踪 |
| 忽略难度 | 容易（忘检查返回码） | 困难（Checked Exception 强制处理） |
| 调用者负担 | 需要层层检查返回码 | 异常自动沿调用栈传播 |
| 性能开销 | 几乎没有 | 创建异常时要填充堆栈（有成本） |

## 异常继承体系

```
java.lang.Throwable
├── java.lang.Error        // 严重错误，程序不应尝试处理
│   ├── OutOfMemoryError
│   ├── StackOverflowError
│   └── NoClassDefFoundError
└── java.lang.Exception    // 可处理的异常
    ├── RuntimeException   // Unchecked（运行时异常）
    │   ├── NullPointerException
    │   ├── IllegalArgumentException
    │   ├── IndexOutOfBoundsException
    │   ├── ArithmeticException
    │   └── ConcurrentModificationException
    └── 其他 Exception     // Checked（编译时异常）
        ├── IOException
        ├── SQLException
        └── ClassNotFoundException
```

核心规则只有一条：**除了 `RuntimeException` 及其子类和 `Error` 及其子类，其他异常都是 Checked Exception。**

## Checked vs Unchecked Exception

这是 Java 异常体系中最具争议的设计。原则很清晰：

| 异常类型 | 父类 | 编译器强制处理？ | 典型场景 |
|----------|------|-----------------|----------|
| **Checked** | `Exception`（非 RuntimeException） | 是——不处理就编译报错 | IO 失败、数据库连接断、反射找不到类 |
| **Unchecked** | `RuntimeException` / `Error` | 否 | NPE、数组越界、逻辑 bug |

```java
// Checked Exception —— 编译器强制你处理
public void readFile() {
    // 下面这行如果不 try-catch 也不 throws，编译不过
    FileReader reader = new FileReader("data.txt");  // throws FileNotFoundException
}

// 两种处理方式：
// 方式一：try-catch 吃掉
public void readFile1() {
    try {
        FileReader reader = new FileReader("data.txt");
    } catch (FileNotFoundException e) {
        System.err.println("文件未找到");
    }
}

// 方式二：throws 向上抛
public void readFile2() throws FileNotFoundException {
    FileReader reader = new FileReader("data.txt");
}

// Unchecked Exception —— 编译器不管
public void divide(int a, int b) {
    int result = a / b;             // b=0 会抛 ArithmeticException，编译器不报错
}

public void process(String s) {
    int len = s.length();           // s==null 会抛 NullPointerException，编译器不报错
}
```

## try-catch-finally

```java
try {
    // 可能抛出异常的代码
    connection = DriverManager.getConnection(url, user, password);
    statement = connection.createStatement();
    resultSet = statement.executeQuery("SELECT * FROM users");
    // 处理结果...
} catch (SQLException e) {
    // 处理数据库异常
    System.err.println("数据库错误: " + e.getMessage());
    e.printStackTrace();
} catch (Exception e) {
    // 捕获其他异常 —— 多 catch 从上到下匹配，子类放前面
    System.err.println("未知错误: " + e.getMessage());
} finally {
    // 无论是否抛异常都执行（即使 try 里有 return！）
    if (resultSet != null) {
        try { resultSet.close(); } catch (SQLException e) { /* 忽略 */ }
    }
    if (statement != null) {
        try { statement.close(); } catch (SQLException e) { /* 忽略 */ }
    }
    if (connection != null) {
        try { connection.close(); } catch (SQLException e) { /* 忽略 */ }
    }
}
```

### finally 的关键行为

```java
// 情形 1：try 有 return，finally 也会执行
public static int test() {
    try {
        return 1;
    } finally {
        System.out.println("finally 执行了");
    }
}
// 输出 "finally 执行了"，返回 1

// 情形 2：finally 里的 return 会覆盖 try 的 return
public static int test2() {
    try {
        return 1;
    } finally {
        return 2;    // 实际返回 2！不要这样写
    }
}

// 情形 3：System.exit(0) 会阻止 finally 执行
try {
    System.exit(0);
} finally {
    System.out.println("这行不会打印");
}
```

## try-with-resources

JDK 7 引入的语法糖——自动关闭实现了 `AutoCloseable` 接口的资源，不再需要手工在 finally 里 close：

```java
// 旧写法（JDK 1.6 及以前）
Connection conn = null;
Statement stmt = null;
ResultSet rs = null;
try {
    conn = dataSource.getConnection();
    stmt = conn.createStatement();
    rs = stmt.executeQuery("SELECT 1");
} catch (SQLException e) {
    e.printStackTrace();
} finally {
    if (rs != null) try { rs.close(); } catch (SQLException e) {}
    if (stmt != null) try { stmt.close(); } catch (SQLException e) {}
    if (conn != null) try { conn.close(); } catch (SQLException e) {}
}

// 新写法（JDK 7+）
try (Connection conn = dataSource.getConnection();
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT 1")) {
    // 处理结果
} catch (SQLException e) {
    e.printStackTrace();
}
// 不需要 finally——rs、stmt、conn 按声明顺序的逆序自动关闭
```

JDK 9 可以引用外部变量：

```java
Connection conn = dataSource.getConnection();
try (conn; Statement stmt = conn.createStatement()) {
    // conn 已经被声明了，try-with-resources 只需要接收它
}
```

### 自定义 AutoCloseable

```java
public class ManagedResource implements AutoCloseable {
    public void doWork() {
        System.out.println("工作中...");
    }

    @Override
    public void close() {
        System.out.println("资源已关闭");
    }
}

try (ManagedResource res = new ManagedResource()) {
    res.doWork();
}  // 自动调用 res.close()
// 输出:
// 工作中...
// 资源已关闭
```

### 抑制异常

如果 try 块和 close() 都抛了异常，try 的异常是"主异常"，close() 的异常作为"被抑制异常"附在主异常上：

```java
try (FailingResource res = new FailingResource()) {
    throw new RuntimeException("try 中的异常");
    // close() 也抛异常时：
    // 主异常 = "try 中的异常"
    // 抑制异常 = close() 的异常（通过 e.getSuppressed() 获取）
}
```

## throw 与 throws

```java
// throws —— 声明可能抛出的异常（用在方法签名）
public byte[] readBytes(String path) throws IOException {
    return Files.readAllBytes(Path.of(path));
}

// throw —— 主动抛出异常（用在方法体内）
public void validateAge(int age) {
    if (age < 0 || age > 150) {
        throw new IllegalArgumentException("年龄不合法: " + age);
    }
}

// 重新抛出 —— 保持异常链
try {
    doSomething();
} catch (SQLException e) {
    // 包装后重新抛出，保留原始异常信息
    throw new ServiceException("服务调用失败", e);
}
```

## 自定义异常

自定义异常分两种：继承 `Exception`（Checked）还是 `RuntimeException`（Unchecked）。

```java
// 业务异常 —— 继承 RuntimeException（推荐，不强制调用者处理）
public class BusinessException extends RuntimeException {
    private final String errorCode;

    public BusinessException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public BusinessException(String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}

// Checked 异常 —— 继承 Exception（不那么推荐）
public class ConfigException extends Exception {
    public ConfigException(String message) {
        super(message);
    }

    public ConfigException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

自定义异常的核心价值是**语义清晰**：看到 `OrderNotFoundException` 就知道是订单不存在，而不是一个泛泛的 `RuntimeException`。

## 异常链

异常链（Exception Chaining）允许在转换异常时保留原始异常，形成因果链：

```java
try {
    // 底层：数据库操作失败
    jdbcTemplate.update(sql, params);
} catch (DataAccessException e) {
    // 包装成业务异常，保留原始异常
    throw new OrderServiceException("创建订单失败，订单号: " + orderId, e);
}

// 上层捕获
try {
    orderService.createOrder(order);
} catch (OrderServiceException e) {
    logger.error("订单服务异常", e);
    Throwable root = e.getCause();    // 获取原始异常
    if (root instanceof DataAccessException) {
        // 数据库问题，触发告警
    }
}
```

打印异常链时，`printStackTrace()` 会输出完整链——从最外层异常开始，追踪到最原始根因：

```text
com.example.OrderServiceException: 创建订单失败
    at com.example.OrderService.createOrder(OrderService.java:42)
Caused by: org.springframework.dao.DataAccessException: ...
    at org.springframework.jdbc.core.JdbcTemplate.update(JdbcTemplate.java:...)
Caused by: java.sql.SQLException: Connection refused
    ...
```

## 多异常捕获

JDK 7+ 可以用一个 catch 捕获多种异常：

```java
// 旧写法（1.6-）
try {
    doWork();
} catch (IOException e) {
    log(e);
} catch (SQLException e) {
    log(e);
}

// 新写法（JDK 7+）
try {
    doWork();
} catch (IOException | SQLException e) {
    log(e);   // e 是隐式 final 的，不能修改
}
```

注意：多异常捕获的变量 `e` 是隐式 `final` 的——你不能在 catch 块中给它赋新值。

## 异常设计原则

### 1. 优先使用 Unchecked Exception

Spring 框架把 Checked Exception 全部转成了 Unchecked（`DataAccessException`），这是业界共识——Checked Exception 强制调用者处理，常常导致空 catch 块和代码臃肿。

```java
// 不好：Checked Exception 被空 catch 吞掉
try {
    service.call();
} catch (CheckedException e) {
    // 什么都不做，错误被隐藏
}

// 好：Unchecked Exception，不处理会自动向上抛
service.call();
```

### 2. 永远不要吞异常

```java
// 错误：吞异常
try {
    doSomething();
} catch (Exception e) {
    // 空块 —— 生产事故的温床
}

// 至少记日志
try {
    doSomething();
} catch (Exception e) {
    logger.error("操作失败", e);
    throw new ServiceException("操作失败", e);   // 或者重新抛出
}
```

### 3. 在正确的层级处理异常

```java
// 错误：在数据访问层就返回默认值
public User findById(Long id) {
    try {
        return jdbc.query(...);
    } catch (Exception e) {
        return null;   // 调用者不知道是"不存在"还是"数据库挂了"
    }
}

// 正确：让异常向上传播，在合适的层级处理
public User findById(Long id) {
    return jdbc.query(...);   // 让 SQLException 自然向上传播
}
```

### 4. 异常不是流程控制

```java
// 错误：用异常做正常流程控制
public User findUser(Long id) {
    try {
        return userMap.get(id);  // 可能抛 NPE
    } catch (NullPointerException e) {
        return null;
    }
}

// 正确：用条件判断
public User findUser(Long id) {
    if (userMap.containsKey(id)) {
        return userMap.get(id);
    }
    return null;
}
```

### 5. 尽早抛，延迟捕

- **尽早抛**：在检测到错误的最近处抛出异常，别试图"修复"一个已经无效的状态
- **延迟捕**：在有能力处理的地方捕获——底层只知道"出错了"，上层才知道"如何应对"（重试？降级？提示用户？）

## 应用场景实战

### 场景一：全局异常处理器（Spring Boot）

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusiness(BusinessException e) {
        ErrorResponse resp = new ErrorResponse(e.getErrorCode(), e.getMessage());
        return ResponseEntity.badRequest().body(resp);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
            .map(err -> err.getField() + ": " + err.getDefaultMessage())
            .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest().body(new ErrorResponse("VALIDATION_ERROR", msg));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnknown(Exception e) {
        logger.error("未预期的异常", e);
        return ResponseEntity.status(500)
            .body(new ErrorResponse("INTERNAL_ERROR", "服务器内部错误"));
    }
}
```

### 场景二：重试机制

```java
public class RetryUtil {
    public static <T> T executeWithRetry(Supplier<T> action, 
                                          int maxRetries, 
                                          long delayMs) {
        int attempt = 0;
        while (true) {
            try {
                return action.get();
            } catch (Exception e) {
                attempt++;
                if (attempt >= maxRetries) {
                    throw new RuntimeException("重试 " + maxRetries + " 次后仍失败", e);
                }
                logger.warn("第 {} 次尝试失败，{}ms 后重试", attempt, delayMs, e);
                try {
                    Thread.sleep(delayMs);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException("重试被中断", ie);
                }
            }
        }
    }
}

// 用法
String result = RetryUtil.executeWithRetry(
    () -> callRemoteApi(),
    3,
    2000
);
```

### 场景三：检查型异常转非检查型

```java
// 工具方法：把 Checked Exception 悄悄转成 Unchecked
public class ExceptionUtils {
    @SuppressWarnings("unchecked")
    public static <T extends Throwable> RuntimeException sneakyThrow(Throwable e) throws T {
        throw (T) e;
    }
}

// 用法：在 Lambda 中处理 Checked Exception
List<String> files = Arrays.asList("a.txt", "b.txt");
List<String> contents = files.stream()
    .map(file -> {
        try {
            return Files.readString(Path.of(file));
        } catch (IOException e) {
            throw new UncheckedIOException(e);   // 包装成 Unchecked
        }
    })
    .collect(Collectors.toList());
```

### 场景四：资源清理与异常安全

```java
// 确保发生异常时文件被正确删除
Path tempFile = null;
try {
    tempFile = Files.createTempFile("process", ".tmp");
    // 处理文件...
} catch (Exception e) {
    if (tempFile != null) {
        try {
            Files.deleteIfExists(tempFile);
        } catch (IOException deleteEx) {
            e.addSuppressed(deleteEx);   // 删除失败也作为抑制异常保留
        }
    }
    throw new RuntimeException("处理失败", e);
}
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| 空 catch 块 | 懒得处理，随手 catch Exception | 至少记录日志并重新抛出 |
| finally 里写 return | finally 的 return 覆盖 try 的返回值/异常 | finally 只做清理，不做控制流 |
| 循环里抛异常效率极低 | 每次 `new Exception` 都要 `fillInStackTrace()` 遍历调用栈 | 异常只能用于异常情况，不要当流程控制 |
| catch 后不处理也不抛 | 异常被吞，生产环境找不出问题 | catch 后要么处理、要么转译重抛 |
| `e.printStackTrace()` 留在生产代码 | 生产日志渠道可能不同，stdout 不被收集 | 用日志框架（logback/log4j2） |
| 自定义异常忘记加 cause | 异常链断裂，丢失根因 | 构造方法加 `Throwable cause` 参数 |

### 异常性能

```java
// 创建异常很昂贵 —— 调用 fillInStackTrace() 遍历当前调用栈
// 正常业务控制流不要用异常！

// 不好：用异常来控制循环
for (int i = 0; ; i++) {
    try {
        String s = list.get(i);  // 靠 IndexOutOfBoundsException 退出循环
    } catch (IndexOutOfBoundsException e) {
        break;
    }
}

// 好：用条件判断
for (int i = 0; i < list.size(); i++) {
    String s = list.get(i);
}
```

### 关键建议

1. **永远不要吞异常**（`catch (Exception e) {}`），至少记日志
2. **优先使用 Unchecked Exception**（继承 RuntimeException）
3. **try-with-resources 替代 finally 手动 close**——更安全、更简洁
4. **异常链不要断**——重抛时把原始异常作为 cause 传入
5. **异常消息要具体**——`"订单号 12345 创建失败，原因: 库存不足"` 远比 `"error"` 有用
6. **在 API 边界统一处理异常**——Controller 层用全局异常处理器，底层让它自然向上传播

## 总结

- `Throwable` → `Error`（不可恢复） + `Exception`（可处理）
- `RuntimeException`（Unchecked，编译器不强求）vs 其他 Exception（Checked，必须处理）
- `try-catch-finally` 中 finally 一定执行（除 System.exit 外），避免 finally 中写 return
- `try-with-resources`（JDK 7+）自动关闭 AutoCloseable 资源，替代 finally 中的样板代码
- 自定义异常建议继承 `RuntimeException`，提供 `errorCode` 和 cause 构造方法
- "尽早抛，延迟捕"——检测到错误就抛，在能处理的地方才捕
- 不要用异常当流程控制、不要吞异常、保持异常链完整
