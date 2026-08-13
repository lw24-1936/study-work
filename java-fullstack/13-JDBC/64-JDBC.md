---
title: JDBC
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [jdbc, driver, connection, statement, preparedstatement, callablestatement, resultset, metadata, transaction, batch, sql-injection]
---

# JDBC

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [JDBC 架构](#jdbc-架构)
- [JDBC Driver —— 驱动加载与注册](#jdbc-driver--驱动加载与注册)
- [Connection —— 数据库连接](#connection--数据库连接)
- [Statement —— 静态语句](#statement--静态语句)
- [PreparedStatement —— 预编译语句](#preparedstatement--预编译语句)
- [CallableStatement —— 存储过程调用](#callablestatement--存储过程调用)
- [ResultSet —— 结果集](#resultset--结果集)
- [ResultSetMetaData —— 结果集元数据](#resultsetmetadata--结果集元数据)
- [DatabaseMetaData —— 数据库元数据](#databasemetadata--数据库元数据)
- [Batch 批处理](#batch-批处理)
- [事务管理](#事务管理)
- [Connection Pool —— 连接池](#connection-pool--连接池)
- [SQL 注入](#sql-注入)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JDBC（Java Database Connectivity）是 Java 访问数据库的标准 API。它定义了一套接口，各数据库厂商提供驱动实现。无论底层是 MySQL、PostgreSQL 还是 Oracle，Java 代码层面都是同一套 `java.sql` 和 `javax.sql` 接口。

JDBC 已经诞生 20 多年，今天几乎没有项目直接裸写 JDBC——都是通过 MyBatis、JPA、Spring JDBC 等框架。但理解 JDBC 是理解这些框架的基础：MyBatis 的 `SqlSession` 内部封装了 JDBC 的 `Connection` 和 `PreparedStatement`，JPA 的 `EntityManager` 最终也是通过 JDBC 与数据库通信。

本章深入 JDBC API 本身的全部接口。连接池（HikariCP / Druid）的配置和管理见第 63 章。

## JDBC 架构

```
┌──────────────────────────────────────────────┐
│             Java 应用                          │
│   (直接 JDBC / Spring JDBC / MyBatis / JPA)   │
├──────────────────────────────────────────────┤
│           JDBC API (java.sql)                  │
│  DriverManager / DataSource                    │
│  Connection / Statement / ResultSet            │
├──────────────────────────────────────────────┤
│         JDBC Driver (厂商实现)                  │
│  mysql-connector-j  /  pgjdbc  /  ojdbc       │
├──────────────────────────────────────────────┤
│     MySQL    /    PostgreSQL    /    Oracle    │
└──────────────────────────────────────────────┘
```

两条获取连接的路径：

```
路径一：DriverManager（简单应用）
  DriverManager.getConnection(url, user, password)
    → 遍历已注册的 Driver，找到匹配的
    → Driver.connect(url, props)
    → 返回 Connection

路径二：DataSource（生产环境）
  DataSource.getConnection()
    → 连接池返回空闲连接或创建新连接
    → 返回 Connection（代理对象，close() 时归还池）
```

## JDBC Driver —— 驱动加载与注册

### 驱动是什么

JDBC Driver 是 JDBC 接口的厂商实现。以 MySQL 为例，`mysql-connector-j` 这个 jar 包就是 MySQL 的 JDBC 驱动，它实现了 `java.sql.Driver` 接口。

### 驱动注册机制

JDBC 4.0（Java 6）起通过 SPI（Service Provider Interface）自动注册，不再需要 `Class.forName()`：

```
mysql-connector-j.jar
└── META-INF/services/java.sql.Driver
    内容: com.mysql.cj.jdbc.Driver
```

`DriverManager` 在初始化时通过 `ServiceLoader` 扫描 classpath 下所有 `META-INF/services/java.sql.Driver` 文件，自动加载并注册驱动。

```java
// 旧写法（JDBC 3.0 及以前，Java 5 以下）
Class.forName("com.mysql.cj.jdbc.Driver");

// 新写法（JDBC 4.0+，Java 6+）
// 不需要任何代码，驱动自动注册
Connection conn = DriverManager.getConnection(url, user, password);
```

### DriverManager 获取连接

```java
// 方式一：完整参数
Connection conn = DriverManager.getConnection(
    "jdbc:mysql://localhost:3306/mydb?useSSL=false&serverTimezone=Asia/Shanghai",
    "root",
    "password"
);

// 方式二：Properties 对象
Properties props = new Properties();
props.setProperty("user", "root");
props.setProperty("password", "password");
props.setProperty("useSSL", "false");
Connection conn = DriverManager.getConnection("jdbc:mysql://localhost:3306/mydb", props);

// 方式三：只传 URL（用户名密码拼接在 URL 中）
Connection conn = DriverManager.getConnection(
    "jdbc:mysql://localhost:3306/mydb?user=root&password=password"
);
```

### 多驱动并存

classpath 中可能有多个驱动（MySQL + PostgreSQL），`DriverManager` 会按 URL 前缀匹配：

```
jdbc:mysql://...     → com.mysql.cj.jdbc.Driver
jdbc:postgresql://... → org.postgresql.Driver
jdbc:h2:mem:...      → org.h2.Driver
```

### 驱动的主要职责

```java
public interface Driver {
    // 尝试连接，返回 Connection；URL 不匹配返回 null
    Connection connect(String url, Properties info) throws SQLException;

    // 判断是否接受此 URL
    boolean acceptsURL(String url) throws SQLException;

    // 获取驱动的版本信息
    int getMajorVersion();
    int getMinorVersion();

    // 是否合规的 JDBC 驱动
    boolean jdbcCompliant();
}
```

## Connection —— 数据库连接

Connection 是 JDBC 的核心接口，所有数据库操作都从一个 Connection 开始。它代表一个与数据库的 TCP 连接会话。

### 创建方式

```java
// DriverManager（不推荐生产环境）
Connection conn = DriverManager.getConnection(url, user, password);

// DataSource（生产环境标准方式）
DataSource ds = new HikariDataSource(config);
Connection conn = ds.getConnection();
```

### Connection 核心方法

```java
// ——— 创建 Statement ———
Statement createStatement()                          // 普通 Statement
PreparedStatement prepareStatement(String sql)       // 预编译
CallableStatement prepareCall(String sql)            // 存储过程

// ——— 事务控制 ———
void setAutoCommit(boolean autoCommit)               // 自动提交开关
void commit()                                        // 提交
void rollback()                                      // 回滚
Savepoint setSavepoint()                             // 设置保存点
Savepoint setSavepoint(String name)                  // 命名保存点
void rollback(Savepoint savepoint)                   // 回滚到保存点
void releaseSavepoint(Savepoint savepoint)           // 释放保存点

// ——— 事务隔离级别 ———
void setTransactionIsolation(int level)               // 设置隔离级别
int getTransactionIsolation()                         // 获取隔离级别
// 常量：TRANSACTION_READ_UNCOMMITTED / TRANSACTION_READ_COMMITTED
//        TRANSACTION_REPEATABLE_READ / TRANSACTION_SERIALIZABLE

// ——— 连接信息 ———
DatabaseMetaData getMetaData()                        // 数据库元数据
boolean isClosed()                                    // 是否已关闭
boolean isValid(int timeout)                          // 连接是否有效（发送 ping）

// ——— 其他 ———
void setReadOnly(boolean readOnly)                    // 只读模式（优化提示）
void setCatalog(String catalog)                       // 切换数据库
String getCatalog()                                   // 当前数据库
void close()                                          // 关闭连接
```

### Connection 生命周期

```
创建 → 使用(执行SQL) → 提交/回滚 → 关闭

DataSource.getConnection()  →  执行业务  →  conn.close()
       ↑                                       ↓
   连接池空闲连接  ←──── 归还(物理连接不断开) ←─┘
```

## Statement —— 静态语句

Statement 用于执行静态 SQL（SQL 字符串在执行时已完全确定，不含参数占位符）。

### 创建与执行

```java
try (Connection conn = ds.getConnection();
     Statement stmt = conn.createStatement()) {

    // 1. executeQuery —— 执行 SELECT，返回 ResultSet
    ResultSet rs = stmt.executeQuery("SELECT id, name FROM user WHERE age > 18");

    // 2. executeUpdate —— 执行 INSERT/UPDATE/DELETE/DDL，返回影响行数
    int rows = stmt.executeUpdate("UPDATE user SET status = 1 WHERE id = 100");

    // 3. execute —— 执行任意 SQL，返回 boolean（true=有ResultSet, false=影响行数）
    boolean hasResultSet = stmt.execute("SELECT * FROM user");
    if (hasResultSet) {
        ResultSet rs = stmt.getResultSet();
        // 处理结果集
    } else {
        int updateCount = stmt.getUpdateCount();
    }

    // 4. executeBatch —— 批量执行
    stmt.addBatch("INSERT INTO log VALUES (1, 'LOGIN')");
    stmt.addBatch("INSERT INTO log VALUES (2, 'LOGOUT')");
    int[] results = stmt.executeBatch();
}
```

### Statement 参数配置

```java
Statement stmt = conn.createStatement();

// 结果集类型
stmt = conn.createStatement(
    ResultSet.TYPE_FORWARD_ONLY,       // 默认：只能向前滚动
    ResultSet.CONCUR_READ_ONLY         // 默认：只读
);

stmt = conn.createStatement(
    ResultSet.TYPE_SCROLL_INSENSITIVE, // 可前后滚动，不感知外部修改
    ResultSet.CONCUR_UPDATABLE          // 可更新
);

// 查询超时（秒）
stmt.setQueryTimeout(10);

// 最大返回行数（防止返回海量数据撑爆内存）
stmt.setMaxRows(1000);

// 批量获取行数（驱动一次网络往返拉取多少行）
stmt.setFetchSize(100);
```

### Statement vs PreparedStatement

| | Statement | PreparedStatement |
|--|-----------|-------------------|
| SQL 注入 | 危险 | 安全（参数转义） |
| 预编译 | 每次编译 | 一次编译多次执行 |
| 二进制数据 | 麻烦 | 原生支持（setBinaryStream） |
| 可读性 | 字符串拼接混乱 | 占位符 ? 清晰 |
| 使用场景 | DDL、一次性的动态表名 | 带参数的 DML/DQL |

**生产环境规则：能用 PreparedStatement 就不用 Statement。** Statement 仅用于少数场景——DDL 语句、动态表名/列名（这些场景 ? 占位符不支持）。

## PreparedStatement —— 预编译语句

PreparedStatement 继承自 Statement，是 JDBC 中最常用的接口。两个核心价值：防止 SQL 注入 + 预编译缓存提升性能。

### 基本用法

```java
String sql = "SELECT id, name, email FROM user WHERE age > ? AND status = ?";

try (Connection conn = ds.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {

    // 设置参数（索引从 1 开始）
    ps.setInt(1, 18);           // 第一个 ? = 18
    ps.setInt(2, 1);            // 第二个 ? = 1

    try (ResultSet rs = ps.executeQuery()) {
        while (rs.next()) {
            // 处理结果
        }
    }
}
```

### 参数设置方法大全

```java
PreparedStatement ps = conn.prepareStatement(
    "INSERT INTO user (name, age, salary, active, bio, avatar, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
);

// 基本类型
ps.setString(1, "张三");
ps.setInt(2, 28);
ps.setLong(3, 1001L);
ps.setDouble(4, 15000.50);
ps.setBoolean(5, true);
ps.setBigDecimal(3, new BigDecimal("15000.50"));

// 日期时间
ps.setDate(7, Date.valueOf("2024-01-15"));                        // java.sql.Date（只有日期）
ps.setTime(7, Time.valueOf("14:30:00"));                          // java.sql.Time（只有时间）
ps.setTimestamp(7, Timestamp.valueOf(LocalDateTime.now()));        // java.sql.Timestamp（日期+时间）
ps.setObject(7, LocalDate.now());                                  // JDBC 4.2+ 支持 java.time

// NULL 处理
ps.setNull(5, Types.BOOLEAN);                                      // 明确类型
ps.setString(5, null);                                             // 也可以（驱动推断类型）

// 二进制数据
ps.setBytes(6, bytes);
ps.setBinaryStream(6, inputStream);
ps.setBlob(6, inputStream);                                        // BLOB 类型

// 大文本
ps.setCharacterStream(7, reader);
ps.setClob(7, reader);                                             // CLOB 类型

// 使用 setObject + SQLType（类型安全）
ps.setObject(1, "张三", JDBCType.VARCHAR);
ps.setObject(2, 28, JDBCType.INTEGER);
```

### 获取自增主键

```java
String sql = "INSERT INTO user (name, email) VALUES (?, ?)";

// 方式一：指定自动生成的列
try (PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
    ps.setString(1, "张三");
    ps.setString(2, "zhangsan@example.com");
    ps.executeUpdate();

    try (ResultSet rs = ps.getGeneratedKeys()) {
        if (rs.next()) {
            long id = rs.getLong(1);   // 自增 ID
        }
    }
}

// 方式二：指定列名（有的驱动支持）
try (PreparedStatement ps = conn.prepareStatement(sql, new String[]{"id"})) {
    ps.setString(1, "张三");
    ps.setString(2, "zhangsan@example.com");
    ps.executeUpdate();

    try (ResultSet rs = ps.getGeneratedKeys()) {
        if (rs.next()) {
            long id = rs.getLong("id");
        }
    }
}
```

### 客户端预编译 vs 服务端预编译

MySQL 的 PreparedStatement 默认是客户端模拟预编译——JDBC 驱动在客户端把 `?` 替换为参数值，拼接成完整 SQL 发送。这不是真正的数据库预编译，每次都是全新的 SQL。

开启服务端预编译：

```
# JDBC URL 参数
jdbc:mysql://localhost:3306/db?useServerPrepStmts=true&cachePrepStmts=true
```

`useServerPrepStmts=true`：启用 MySQL 服务端预编译
`cachePrepStmts=true`：客户端缓存 PreparedStatement 对象，避免每次创建

服务端预编译流程：

```
第一次执行：
  客户端 → PREPARE stmt FROM 'SELECT ... WHERE id = ?'
  服务端 → 解析、优化、生成执行计划并缓存
  客户端 → EXECUTE stmt USING @p1
  服务端 → 执行并返回结果

后续执行（同连接）：
  客户端 → EXECUTE stmt USING @p2
  服务端 → 直接执行（跳过解析优化）
```

## CallableStatement —— 存储过程调用

CallableStatement 用于调用数据库存储过程和函数，继承自 PreparedStatement。

### 调用存储过程

```sql
-- MySQL 存储过程示例
DELIMITER //
CREATE PROCEDURE get_employees_by_dept(IN dept_id INT)
BEGIN
    SELECT id, name, salary FROM employee WHERE dept_id = dept_id;
END //
DELIMITER ;
```

```java
// 调用无参数存储过程
try (CallableStatement cs = conn.prepareCall("{call get_all_users()}")) {
    ResultSet rs = cs.executeQuery();
    // 处理结果
}

// 调用带 IN 参数的存储过程
try (CallableStatement cs = conn.prepareCall("{call get_employees_by_dept(?)}")) {
    cs.setInt(1, 3);                         // IN 参数
    ResultSet rs = cs.executeQuery();
}

// 调用带 OUT 参数的存储过程
try (CallableStatement cs = conn.prepareCall("{call get_employee_count(?)}")) {
    cs.registerOutParameter(1, Types.INTEGER);  // 注册 OUT 参数
    cs.execute();
    int count = cs.getInt(1);                   // 获取 OUT 参数值
}

// 调用带 INOUT 参数的存储过程
try (CallableStatement cs = conn.prepareCall("{call increment_salary(?, ?)}")) {
    cs.setInt(1, 100);                       // IN 值
    cs.registerOutParameter(1, Types.DECIMAL);  // 同时注册为 OUT
    cs.registerOutParameter(2, Types.DECIMAL);
    cs.execute();
    BigDecimal newSalary = cs.getBigDecimal(1);  // 获取 INOUT 结果
    BigDecimal bonus = cs.getBigDecimal(2);
}
```

### 调用函数

```sql
-- MySQL 函数示例
CREATE FUNCTION calc_bonus(salary DECIMAL(10,2), rate DECIMAL(3,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC
RETURN salary * rate;
```

```java
// 调用函数
try (CallableStatement cs = conn.prepareCall("{? = call calc_bonus(?, ?)}")) {
    cs.registerOutParameter(1, Types.DECIMAL);  // 返回值
    cs.setBigDecimal(2, new BigDecimal("15000"));
    cs.setBigDecimal(3, new BigDecimal("0.15"));
    cs.execute();
    BigDecimal bonus = cs.getBigDecimal(1);
}
```

### 存储过程的争议

互联网公司普遍不推荐存储过程：
- 业务逻辑散落在数据库和应用两处，维护困难
- 存储过程是数据库的"黑盒"，难以版本控制和测试
- 数据库的 CPU 是稀缺资源，应在应用层处理业务逻辑
- 迁移数据库（MySQL → TiDB / PolarDB）时存储过程可能不兼容

但传统企业（银行、保险）的遗留系统中仍大量使用。了解即可，新项目不要写存储过程。

## ResultSet —— 结果集

ResultSet 代表查询返回的结果集，内部维护一个游标（cursor）指向当前行。

### 基本遍历

```java
try (ResultSet rs = ps.executeQuery()) {
    while (rs.next()) {       // 游标移到下一行，没有更多行时返回 false
        long id = rs.getLong("id");
        String name = rs.getString("name");
        // ...
    }
}
```

### 数据读取方法

```java
// 按列名读取（推荐：不受 SELECT 列顺序影响）
long id = rs.getLong("id");
String name = rs.getString("name");
BigDecimal salary = rs.getBigDecimal("salary");
boolean active = rs.getBoolean("active");
byte[] avatar = rs.getBytes("avatar");
LocalDate birthDate = rs.getObject("birth_date", LocalDate.class);  // JDBC 4.2+

// 按列索引读取（从 1 开始）
long id = rs.getLong(1);
String name = rs.getString(2);

// NULL 检测
String email = rs.getString("email");
if (rs.wasNull()) {    // 上一次 getXxx() 读到的值是否为 NULL
    email = "unknown";
}

// 推荐用 getObject + 包装类型（直接拿到 null）
Integer age = rs.getObject("age", Integer.class);  // 可能为 null
```

### 可滚动与可更新 ResultSet

```java
// 创建可滚动的 Statement
Statement stmt = conn.createStatement(
    ResultSet.TYPE_SCROLL_INSENSITIVE,  // 可滚动，不感知外部修改
    ResultSet.CONCUR_READ_ONLY          // 只读
);

ResultSet rs = stmt.executeQuery("SELECT * FROM employee ORDER BY salary DESC");

// 游标移动
rs.absolute(5);       // 跳到第 5 行
rs.relative(2);       // 向下移 2 行
rs.relative(-3);      // 向上移 3 行
rs.first();           // 第一行
rs.last();            // 最后一行
rs.previous();        // 上一行
rs.beforeFirst();     // 第一行之前
rs.afterLast();       // 最后一行之后
rs.isFirst();         // 是否在第一行
rs.isLast();          // 是否在最后一行
rs.getRow();          // 当前行号

// 可更新 ResultSet
Statement stmt = conn.createStatement(
    ResultSet.TYPE_SCROLL_INSENSITIVE,
    ResultSet.CONCUR_UPDATABLE
);
ResultSet rs = stmt.executeQuery("SELECT id, name, salary FROM employee");
while (rs.next()) {
    BigDecimal oldSalary = rs.getBigDecimal("salary");
    rs.updateBigDecimal("salary", oldSalary.multiply(new BigDecimal("1.1")));
    rs.updateRow();     // 更新当前行
}
```

### ResultSet 性能参数

```java
Statement stmt = conn.createStatement();

// fetchSize：每次网络往返拉取的行数
// MySQL 默认一次拉所有行到客户端内存。设一个合理值（如 100）来控制内存
stmt.setFetchSize(100);

// FetchDirection：建议的读取方向（只是提示，驱动不一定遵守）
stmt.setFetchDirection(ResultSet.FETCH_FORWARD);
```

对于大结果集（百万行级别），必须设置合适的 fetchSize 或使用游标查询，否则会 OOM。

## ResultSetMetaData —— 结果集元数据

ResultSetMetaData 提供结果集的结构信息——列数、列名、列类型等。这是动态查询和通用结果处理的基础，MyBatis 和 Spring JDBC 的对象映射功能都依赖它。

```java
try (ResultSet rs = stmt.executeQuery("SELECT * FROM employee WHERE 1=0")) {
    ResultSetMetaData meta = rs.getMetaData();

    int columnCount = meta.getColumnCount();     // 列数

    for (int i = 1; i <= columnCount; i++) {
        String columnName  = meta.getColumnName(i);       // 列名（原始列名）
        String columnLabel = meta.getColumnLabel(i);      // 列别名（推荐使用）
        String typeName    = meta.getColumnTypeName(i);   // 数据库类型名（"VARCHAR"）
        int    sqlType     = meta.getColumnType(i);       // java.sql.Types 常量
        String className   = meta.getColumnClassName(i);  // Java 类全名
        int    displaySize = meta.getColumnDisplaySize(i);// 列宽
        int    precision   = meta.getPrecision(i);        // 精度
        int    scale       = meta.getScale(i);            // 小数位数
        int    nullable    = meta.isNullable(i);          // 是否可为 NULL
        boolean autoIncr   = meta.isAutoIncrement(i);    // 是否自增

        System.out.printf("列 %d: %s (%s), SQL类型=%d%n",
                i, columnLabel, typeName, sqlType);
    }
}
```

### 列名 vs 列标签

```sql
SELECT id, name AS employee_name, salary * 12 AS annual FROM employee
```

- `getColumnName(2)` → `"name"`（数据库原始列名）
- `getColumnLabel(2)` → `"employee_name"`（SQL 中的别名）

框架在映射结果集到对象时用的是 `getColumnLabel()`——别名优先。

### 通用结果集 → Map 转换

利用 ResultSetMetaData 写出通用的结果转换工具：

```java
public static List<Map<String, Object>> resultSetToList(ResultSet rs) throws SQLException {
    List<Map<String, Object>> list = new ArrayList<>();
    ResultSetMetaData meta = rs.getMetaData();
    int colCount = meta.getColumnCount();

    while (rs.next()) {
        Map<String, Object> row = new LinkedHashMap<>();
        for (int i = 1; i <= colCount; i++) {
            row.put(meta.getColumnLabel(i), rs.getObject(i));
        }
        list.add(row);
    }
    return list;
}
```

这就是 MyBatis 返回 `Map` 的底层原理。

## DatabaseMetaData —— 数据库元数据

DatabaseMetaData 提供数据库本身的元信息——表、列、索引、主键、外键、存储过程等。

```java
Connection conn = ds.getConnection();
DatabaseMetaData dbMeta = conn.getMetaData();

// ——— 数据库基本信息 ———
String productName    = dbMeta.getDatabaseProductName();    // "MySQL"
String productVersion = dbMeta.getDatabaseProductVersion(); // "8.0.35"
String driverName     = dbMeta.getDriverName();             // "MySQL Connector/J"
String driverVersion  = dbMeta.getDriverVersion();
String url            = dbMeta.getURL();
String userName       = dbMeta.getUserName();

// ——— 功能支持检测 ———
boolean supportsTransactions = dbMeta.supportsTransactions();
boolean supportsBatchUpdates = dbMeta.supportsBatchUpdates();
boolean supportsSavepoints   = dbMeta.supportsSavepoints();
boolean supportsStoredProcs  = dbMeta.supportsStoredProcedures();
```

### 遍历所有表

```java
// 获取当前数据库所有表
try (ResultSet rs = dbMeta.getTables(
        null,           // catalog（MySQL 对应数据库名，null=当前）
        null,           // schemaPattern（MySQL 中为 null）
        "%",            // tableNamePattern（% 匹配所有）
        new String[]{"TABLE", "VIEW"}   // 类型
)) {
    while (rs.next()) {
        String tableName = rs.getString("TABLE_NAME");
        String tableType = rs.getString("TABLE_TYPE");  // TABLE / VIEW
        String remarks   = rs.getString("REMARKS");     // 表注释
    }
}
```

### 遍历表的所有列

```java
try (ResultSet rs = dbMeta.getColumns(null, null, "employee", "%")) {
    while (rs.next()) {
        String colName   = rs.getString("COLUMN_NAME");
        int    sqlType   = rs.getInt("DATA_TYPE");
        String typeName  = rs.getString("TYPE_NAME");
        int    colSize   = rs.getInt("COLUMN_SIZE");
        String isNull    = rs.getString("IS_NULLABLE");   // YES / NO
        String defVal    = rs.getString("COLUMN_DEF");    // 默认值
        String remarks   = rs.getString("REMARKS");       // 列注释
    }
}
```

### 遍历主键

```java
try (ResultSet rs = dbMeta.getPrimaryKeys(null, null, "employee")) {
    while (rs.next()) {
        String colName  = rs.getString("COLUMN_NAME");
        short  keySeq   = rs.getShort("KEY_SEQ");    // 主键中的序号（复合主键时有用）
        String pkName   = rs.getString("PK_NAME");   // 主键名
    }
}
```

### 遍历外键

```java
try (ResultSet rs = dbMeta.getImportedKeys(null, null, "order_item")) {
    while (rs.next()) {
        String fkColName  = rs.getString("FKCOLUMN_NAME");   // 外键列
        String pkTable    = rs.getString("PKTABLE_NAME");    // 引用的表
        String pkColName  = rs.getString("PKCOLUMN_NAME");   // 引用的列
    }
}
```

### 遍历索引

```java
try (ResultSet rs = dbMeta.getIndexInfo(null, null, "employee", false, false)) {
    while (rs.next()) {
        String idxName   = rs.getString("INDEX_NAME");
        String colName   = rs.getString("COLUMN_NAME");
        boolean nonUnique = rs.getBoolean("NON_UNIQUE");     // 是否允许重复
        short   ordinal  = rs.getShort("ORDINAL_POSITION");  // 列在索引中的序号
        String  ascDesc  = rs.getString("ASC_OR_DESC");     // A / D
    }
}
```

### 实际用途：代码生成器

DatabaseMetaData 是 MyBatis Generator、MyBatis-Plus 代码生成器、Flyway 等工具的底层依赖——它们通过 DatabaseMetaData 读取表结构，自动生成 Entity、Mapper、Service 代码。

## Batch 批处理

Batch 将多条 SQL 打包发送，减少网络往返。

### Statement 批处理

```java
try (Statement stmt = conn.createStatement()) {
    stmt.addBatch("INSERT INTO log VALUES (1, 'LOGIN')");
    stmt.addBatch("INSERT INTO log VALUES (2, 'LOGOUT')");
    stmt.addBatch("INSERT INTO log VALUES (3, 'ERROR')");

    int[] results = stmt.executeBatch();  // 返回每条 SQL 的影响行数
}
```

### PreparedStatement 批处理

```java
String sql = "INSERT INTO user (name, email) VALUES (?, ?)";
try (PreparedStatement ps = conn.prepareStatement(sql)) {
    for (int i = 0; i < 10000; i++) {
        ps.setString(1, "user" + i);
        ps.setString(2, "user" + i + "@example.com");
        ps.addBatch();

        if (i % 1000 == 0) {
            ps.executeBatch();
            ps.clearBatch();    // 清空已添加的 SQL
        }
    }
    ps.executeBatch();  // 执行剩余
}
```

### rewriteBatchedStatements

MySQL JDBC 驱动提供了 `rewriteBatchedStatements=true` 参数，将批量 INSERT 合并为单条多 VALUES 的 SQL：

```
默认批量（5 条 INSERT）：
  INSERT INTO t VALUES (1, 'a');  → 1 次往返
  INSERT INTO t VALUES (2, 'b');  → 1 次往返
  INSERT INTO t VALUES (3, 'c');  → 1 次往返
  ...

开启 rewrite（5 条合并为 1 条）：
  INSERT INTO t VALUES (1, 'a'), (2, 'b'), (3, 'c'), (4, 'd'), (5, 'e');
  → 1 次往返
```

性能差距：10000 条插入，逐条 ~60s，Batch ~3s，Batch+rewrite ~0.5s。

### 注意

`rewriteBatchedStatements` 只对 INSERT 生效，且不能与 `ON DUPLICATE KEY UPDATE`、`INSERT IGNORE` 等修饰同时使用。

## 事务管理

### 基本事务操作

```java
Connection conn = null;
try {
    conn = ds.getConnection();
    conn.setAutoCommit(false);          // 关闭自动提交

    // 业务操作
    try (PreparedStatement ps1 = conn.prepareStatement(
            "UPDATE account SET balance = balance - ? WHERE id = ?")) {
        ps1.setBigDecimal(1, amount);
        ps1.setLong(2, fromId);
        ps1.executeUpdate();
    }

    try (PreparedStatement ps2 = conn.prepareStatement(
            "UPDATE account SET balance = balance + ? WHERE id = ?")) {
        ps2.setBigDecimal(1, amount);
        ps2.setLong(2, toId);
        ps2.executeUpdate();
    }

    conn.commit();

} catch (SQLException e) {
    if (conn != null) {
        try { conn.rollback(); } catch (SQLException ex) { /* log */ }
    }
    throw new RuntimeException("转账失败", e);
} finally {
    if (conn != null) {
        try {
            conn.setAutoCommit(true);   // 恢复默认
            conn.close();
        } catch (SQLException e) { /* log */ }
    }
}
```

### 隔离级别

```java
// 设置隔离级别
conn.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);

// 查看当前隔离级别
int level = conn.getTransactionIsolation();
```

JDBC 隔离级别常量：

```java
Connection.TRANSACTION_NONE             = 0
Connection.TRANSACTION_READ_UNCOMMITTED = 1
Connection.TRANSACTION_READ_COMMITTED   = 2
Connection.TRANSACTION_REPEATABLE_READ  = 4
Connection.TRANSACTION_SERIALIZABLE     = 8
```

### Savepoint 部分回滚

```java
conn.setAutoCommit(false);

Savepoint sp1 = conn.setSavepoint("after_insert");
ps1.executeUpdate();   // 插入订单

Savepoint sp2 = conn.setSavepoint("after_inventory");
try {
    ps2.executeUpdate();   // 扣库存（可能失败）
} catch (SQLException e) {
    conn.rollback(sp2);    // 只回滚扣库存，订单保留
}

conn.commit();
```

### 事务超时

JDBC 本身不支持事务超时。需要通过数据库配置或连接池配置实现：

```sql
-- MySQL 超时设置
SET SESSION innodb_lock_wait_timeout = 10;   -- 锁等待超时（秒）
SET SESSION max_execution_time = 5000;        -- 语句执行超时（毫秒，5.7.8+）
```

Spring 通过 `@Transactional(timeout = 5)` 在连接上设置超时。

## Connection Pool —— 连接池

连接池不是 JDBC 规范的一部分，而是 `javax.sql.DataSource` 接口的实现。JDBC 的连接池概念指通过 DataSource 获取连接而非 DriverManager。

详细内容见第 63 章《数据库连接》，这里只梳理 JDBC 视角下的连接池要点。

### JDBC 中的连接池角色

```java
// JDBC 接口
javax.sql.DataSource           // 连接池的 JDBC 标准接口
javax.sql.ConnectionPoolDataSource  // 物理连接池（很少直接用）

// 核心交互
DataSource ds = new HikariDataSource(config);
Connection conn = ds.getConnection();    // 从池中获取
// ... 使用连接 ...
conn.close();                            // 归还到池中（不是真正断开 TCP）
```

### 连接池的 JDBC 代理

连接池返回的 Connection 不是原始的数据库连接对象，而是一个代理：

```java
// 原始连接：conn.close() 断开 TCP 连接
// 池代理连接：conn.close() 将连接归还池中
// 代理还拦截了以下方法，重置连接状态：
// - setAutoCommit(true)       恢复自动提交
// - setTransactionIsolation()  恢复默认隔离级别
// - setReadOnly(false)         恢复读写模式
// - setCatalog()               恢复默认数据库
```

这就是为什么归还连接前连接池会做"连接清理"——避免上一个事务的脏状态污染下一个业务。

## SQL 注入

SQL 注入是 Web 应用中最古老也最致命的安全漏洞之一。通过构造恶意输入，攻击者可以执行任意 SQL。

### 攻击原理

```java
// 危险代码
String username = request.getParameter("username");  // 输入: ' OR '1'='1' --
String password = request.getParameter("password");  // 输入: 任意值

String sql = "SELECT * FROM user WHERE username = '" + username
           + "' AND password = '" + password + "'";

// 拼接后的 SQL:
// SELECT * FROM user WHERE username = '' OR '1'='1' --' AND password = 'xxx'
//                                            ^^^^^^^^
//                                    -- 是 SQL 注释，后面的密码检查被注释掉
//                                    OR '1'='1' 永远为 TRUE
// 结果：返回全部用户，登录绕过
```

### 攻击变种

```sql
-- 1. 注释绕过
username: admin' --
SQL: SELECT * FROM user WHERE username = 'admin' --' AND password = 'xxx'

-- 2. 分号注入多条语句（堆叠查询）
username: '; DROP TABLE user; --
SQL: SELECT * FROM user WHERE username = ''; DROP TABLE user; --'

-- 3. UNION 注入
username: ' UNION SELECT id, password, null FROM user --
SQL: SELECT * FROM user WHERE username = '' UNION SELECT ...

-- 4. 盲注（基于布尔/时间）
username: admin' AND SLEEP(5) --
-- 如果响应延迟 5 秒，说明 admin 存在

-- 5. 报错注入
username: ' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT DATABASE()))) --
-- 利用报错信息泄露数据
```

### 防御方案

**第一线：PreparedStatement 参数化查询**

```java
// 安全：参数被转义，不会被当作 SQL 执行
String sql = "SELECT * FROM user WHERE username = ? AND password = ?";
PreparedStatement ps = conn.prepareStatement(sql);
ps.setString(1, username);   // ' OR '1'='1 被当作普通字符串
ps.setString(2, password);
```

**动态表名/列名/ORDER BY 的处理**

`?` 占位符只能替代值，不能替代表名、列名、ORDER BY 方向。这些场景需要白名单校验：

```java
private static final Set<String> ALLOWED_COLUMNS = Set.of("id", "username", "email", "created_at");
private static final Set<String> ALLOWED_DIRECTIONS = Set.of("ASC", "DESC");

public List<User> getUsersByOrder(String orderBy, String direction) {
    if (orderBy == null || !ALLOWED_COLUMNS.contains(orderBy)) {
        throw new IllegalArgumentException("Invalid column: " + orderBy);
    }
    if (direction == null || !ALLOWED_DIRECTIONS.contains(direction.toUpperCase())) {
        throw new IllegalArgumentException("Invalid direction: " + direction);
    }
    // 现在可以安全拼接
    String sql = "SELECT * FROM user ORDER BY " + orderBy + " " + direction.toUpperCase();
    // ...
}
```

**补充防御层**：

- 最小权限原则：应用账户只有 DML 权限，不给 DDL/DCL
- Druid WallFilter：SQL 防火墙，拦截危险 SQL
- 输入校验：前后端双重校验，拒绝异常字符
- 错误信息脱敏：不把数据库错误栈直接返回给前端

## 应用场景实战

### 场景一：通用查询工具——任意 SQL 返回 List<Map>

利用 ResultSetMetaData 实现一个无依赖的查询工具，适合脚本和工具类应用：

```java
public class JdbcUtil {

    private final DataSource ds;

    public JdbcUtil(DataSource ds) {
        this.ds = ds;
    }

    /**
     * 执行查询，返回 List<Map>
     */
    public List<Map<String, Object>> query(String sql, Object... params) {
        List<Map<String, Object>> result = new ArrayList<>();
        try (Connection conn = ds.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            for (int i = 0; i < params.length; i++) {
                ps.setObject(i + 1, params[i]);
            }

            try (ResultSet rs = ps.executeQuery()) {
                ResultSetMetaData meta = rs.getMetaData();
                int colCount = meta.getColumnCount();

                while (rs.next()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    for (int i = 1; i <= colCount; i++) {
                        row.put(meta.getColumnLabel(i), rs.getObject(i));
                    }
                    result.add(row);
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException("查询失败: " + sql, e);
        }
        return result;
    }

    /**
     * 执行更新，返回影响行数
     */
    public int update(String sql, Object... params) {
        try (Connection conn = ds.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            for (int i = 0; i < params.length; i++) {
                ps.setObject(i + 1, params[i]);
            }
            return ps.executeUpdate();
        } catch (SQLException e) {
            throw new RuntimeException("更新失败: " + sql, e);
        }
    }
}
```

### 场景二：数据库表结构导出为 Markdown

利用 DatabaseMetaData 自动生成数据库文档：

```java
public String exportTableToMarkdown(Connection conn, String tableName) throws SQLException {
    DatabaseMetaData meta = conn.getMetaData();
    StringBuilder sb = new StringBuilder();

    // 表名和注释
    sb.append("## ").append(tableName).append("\n\n");

    // 列信息
    sb.append("| 列名 | 类型 | 长度 | 允许空 | 默认值 | 注释 |\n");
    sb.append("|------|------|------|--------|--------|------|\n");

    try (ResultSet rs = meta.getColumns(null, null, tableName, "%")) {
        while (rs.next()) {
            sb.append("| ")
              .append(rs.getString("COLUMN_NAME")).append(" | ")
              .append(rs.getString("TYPE_NAME")).append(" | ")
              .append(rs.getInt("COLUMN_SIZE")).append(" | ")
              .append("YES".equals(rs.getString("IS_NULLABLE")) ? "是" : "否").append(" | ")
              .append(String.valueOf(rs.getString("COLUMN_DEF"))).append(" | ")
              .append(String.valueOf(rs.getString("REMARKS"))).append(" |\n");
        }
    }

    // 索引
    sb.append("\n### 索引\n\n");
    sb.append("| 索引名 | 列名 | 唯一 |\n");
    sb.append("|--------|------|------|\n");

    try (ResultSet rs = meta.getIndexInfo(null, null, tableName, false, false)) {
        while (rs.next()) {
            sb.append("| ")
              .append(rs.getString("INDEX_NAME")).append(" | ")
              .append(rs.getString("COLUMN_NAME")).append(" | ")
              .append(!rs.getBoolean("NON_UNIQUE")).append(" |\n");
        }
    }

    return sb.toString();
}
```

### 场景三：大数据量分页导出（游标模式）

JDBC 默认一次把所有结果加载到内存——百万行数据直接 OOM。设置 fetchSize 使用游标：

```java
public void exportLargeTable(Connection conn, String sql, Consumer<Map<String, Object>> rowHandler) {
    // 关键设置：告诉 JDBC 使用游标，每次只拉 fetchSize 行
    try (PreparedStatement ps = conn.prepareStatement(
            sql,
            ResultSet.TYPE_FORWARD_ONLY,     // 只能向前（游标要求）
            ResultSet.CONCUR_READ_ONLY)) {

        // MySQL: Integer.MIN_VALUE 表示逐行读取（流式结果集）
        ps.setFetchSize(Integer.MIN_VALUE);
        // PostgreSQL: 设一个合理值（如 5000）
        // ps.setFetchSize(5000);
        // 注意：MySQL 的游标需要在事务中
        conn.setAutoCommit(false);

        try (ResultSet rs = ps.executeQuery()) {
            ResultSetMetaData meta = rs.getMetaData();
            int colCount = meta.getColumnCount();

            while (rs.next()) {
                Map<String, Object> row = new LinkedHashMap<>();
                for (int i = 1; i <= colCount; i++) {
                    row.put(meta.getColumnLabel(i), rs.getObject(i));
                }
                rowHandler.accept(row);
            }
        }
    } catch (SQLException e) {
        throw new RuntimeException(e);
    }
}

// 使用
exportLargeTable(conn, "SELECT * FROM big_table", row -> {
    // 逐行处理，写入文件或发送到 MQ
    fileWriter.write(toCsv(row));
});
```

## 最佳实践与踩坑记录

**实践 1：始终使用 try-with-resources**

```java
// 正确：自动关闭，即使异常也会关闭
try (Connection conn = ds.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql);
     ResultSet rs = ps.executeQuery()) {
    while (rs.next()) { /* ... */ }
}

// 错误：可能泄漏资源
Connection conn = ds.getConnection();
PreparedStatement ps = conn.prepareStatement(sql);
ResultSet rs = ps.executeQuery();
// 如果中间抛异常，conn/ps/rs 永远不会 close
```

**实践 2：获取连接和执行业务必须紧邻**

```java
// 错误：获取连接，但过了很久才用
Connection conn = ds.getConnection();
someRpcCall();       // RPC 调用 500ms
someFileIO();        // 文件 IO 200ms
conn.prepareStatement(sql);  // 连接白白空占了 700ms

// 正确：获取连接后立刻使用
someRpcCall();
someFileIO();
try (Connection conn = ds.getConnection()) {
    // 立即执行 SQL
}
```

**实践 3：关闭连接写在 finally 或 try-with-resources 中**

连接池中 `conn.close()` 是归还连接。如果不关闭，连接泄漏最终导致池耗尽。

**实践 4：PreparedStatement 参数索引用变量**

```java
private static final int PARAM_NAME  = 1;
private static final int PARAM_EMAIL = 2;
private static final int PARAM_AGE   = 3;

ps.setString(PARAM_NAME, name);
ps.setString(PARAM_EMAIL, email);
ps.setInt(PARAM_AGE, age);
// 比硬编码数字可读性高，参数位置变化时只改常量定义
```

**踩坑 1**：`getString("col")` 对 NULL 列返回 "null" 字符串。使用 `wasNull()` 检测或 `getObject("col", String.class)` 返回 Java null。

**踩坑 2**：MySQL JDBC 的 `setFetchSize(Integer.MIN_VALUE)` 是"流式结果集"——逐行从数据库拉取。必须设置 `conn.setAutoCommit(false)` 且使用 `TYPE_FORWARD_ONLY`，否则驱动会忽略 fetchSize 而一次性加载全部数据。

**踩坑 3**：`Statement.close()` 会自动关闭关联的 ResultSet，`Connection.close()` 会自动关闭关联的所有 Statement。但不要在 try-with-resources 中依赖这个——显式关闭每个资源。

**踩坑 4**：`CallableStatement` 是 MySQL 驱动中的"重量级"操作，每次调用都需要与数据库进行额外的元数据交互。互联网项目应避免使用存储过程。

**踩坑 5**：`getConnection()` 和 `close()` 必须成对出现。在循环中获取连接是低效模式——一次循环借一次连接。正确做法是一次连接内完成循环。
