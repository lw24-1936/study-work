---
title: MyBatis 源码分析
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [mybatis源码, sqlsession, executor, mapperproxy, statementhandler, parameterhandler, resultsethandler]
---

# MyBatis 源码分析

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [SqlSession](#sqlsession)
- [Executor 执行器](#executor-执行器)
- [MapperProxy 动态代理](#mapperproxy-动态代理)
- [StatementHandler 与 ParameterHandler](#statementhandler-与-parameterhandler)
- [ResultSetHandler 结果映射](#resultsethandler-结果映射)
- [执行流程总结](#执行流程总结)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

MyBatis 是优秀的 ORM 框架，理解其源码能深入理解 SQL 执行的完整链路。

```text
MyBatis 的核心组件：
SqlSession —— 会话（执行入口）
Executor —— 执行器（SQL 执行）
MapperProxy —— Mapper 接口代理
StatementHandler —— 处理 SQL 语句
ParameterHandler —— 参数处理
ResultSetHandler —— 结果映射
```

## SqlSession

SqlSession 是 MyBatis 的执行入口。

### SqlSession 的作用

```text
SqlSession 提供：
1. select/insert/update/delete —— 执行 SQL
2. getMapper —— 获取 Mapper 代理
3. 事务管理
```

```java
// 获取 SqlSession
SqlSession session = sqlSessionFactory.openSession();
try {
    // 方式 1：直接执行
    User user = session.selectOne("com.example.UserMapper.findById", 1);

    // 方式 2：获取 Mapper 代理
    UserMapper mapper = session.getMapper(UserMapper.class);
    user = mapper.findById(1);
} finally {
    session.close();
}
```

### SqlSession 的实现

```text
SqlSession → DefaultSqlSession（默认实现）
→ 委托给 Executor 执行
```

## Executor 执行器

Executor 是 SQL 的执行器，负责查询、更新、缓存。

### Executor 类型

```text
1. SimpleExecutor —— 简单执行器（默认，每次新建 Statement）
2. ReuseExecutor —— 复用 Statement
3. BatchExecutor —— 批量执行
4. CachingExecutor —— 缓存装饰器（二级缓存）
```

### 执行流程

```text
Executor 的执行：
1. 从 MappedStatement 获取 SQL
2. 处理参数（ParameterHandler）
3. 执行 SQL（StatementHandler）
4. 映射结果（ResultSetHandler）
5. 处理缓存
```

## MapperProxy 动态代理

MapperProxy 是 Mapper 接口的动态代理，接口方法转 SQL 执行。

### 动态代理原理

```text
Mapper 接口没有实现类，通过 JDK 动态代理：
1. getMapper 时创建代理
2. 调用接口方法 → MapperProxy 拦截
3. 根据方法找到 MappedStatement（SQL）
4. 交给 Executor 执行
```

```java
// MapperProxy 的 invoke（简化）
public Object invoke(Object proxy, Method method, Object[] args) {
    // 1. 获取 MappedStatement（SQL 映射）
    MappedStatement ms = configuration.getMappedStatement(method);

    // 2. 执行 SQL
    return executor.query(ms, args);
}
```

### 为什么接口能执行

```text
MyBatis 的核心：Mapper 接口 + XML/注解

1. 接口方法名 = XML 的 id
2. 代理拦截方法调用
3. 找到对应的 SQL 执行
```

## StatementHandler 与 ParameterHandler

### StatementHandler

StatementHandler 负责创建 Statement、执行 SQL。

```text
StatementHandler 的职责：
1. 创建 Statement（PreparedStatement）
2. 设置参数（委托 ParameterHandler）
3. 执行 SQL
4. 处理结果（委托 ResultSetHandler）
```

### ParameterHandler

ParameterHandler 负责设置 SQL 参数。

```java
public interface ParameterHandler {
    // 设置参数（把 Java 对象映射到 SQL 的 ?）
    void setParameters(PreparedStatement ps);
}
```

```text
参数处理：#{} 和 ${} 的区别在这里体现：
#{} —— 参数化（? 占位符，PreparedStatement 设置）
${} —— 直接拼接（字符串替换，有 SQL 注入风险）
```

## ResultSetHandler 结果映射

ResultSetHandler 负责把结果集映射到对象。

### 结果映射流程

```text
1. 获取 ResultSet
2. 遍历结果集
3. 每行映射到一个对象（反射 set 字段）
4. 处理关联（一对一、一对多）
```

```text
结果映射的关键：
1. 列名和属性名的映射（驼峰转换）
2. resultMap 的配置（自定义映射）
3. 关联查询（association/collection）
```

## 执行流程总结

```text
MyBatis 完整执行流程：

调用 mapper.findById(1)
        ↓
MapperProxy.invoke（动态代理拦截）
        ↓
Executor.query（执行器）
        ↓
创建 StatementHandler（处理 SQL）
        ↓
ParameterHandler.setParameters（设置参数 #{}）
        ↓
执行 SQL
        ↓
ResultSetHandler（结果映射成对象）
        ↓
返回结果
```

## 最佳实践与踩坑记录

### 最佳实践

1. **用 #{} 不用 ${}**。#{} 参数化防 SQL 注入。

2. **理解一级缓存**。同一 SqlSession 内，相同查询走缓存。

3. **批量操作用 BatchExecutor**。批量插入快。

4. **合理用 resultMap**。复杂映射用 resultMap。

5. **理解 N+1**。关联查询用延迟加载或 join。

### 踩坑记录

**坑 1：${} SQL 注入**

```xml
<!-- ${} 直接拼接，SQL 注入风险 -->
SELECT * FROM users WHERE name = '${name}'
```

用 #{} 参数化，${} 只用于表名/列名（白名单）。

**坑 2：一级缓存脏数据**

```text
同一 SqlSession 内，先查后改，再查走缓存（旧数据）
```

理解一级缓存作用域（SqlSession），或手动清缓存。

**坑 3：N+1 查询**

```xml
<!-- 关联查询：查 N 个用户，每个查一次订单（N+1） -->
<collection property="orders" select="findOrders" .../>
```

用 join 或延迟加载（懒加载）。

**坑 4：字段映射不匹配**

```text
数据库列 create_time，Java 属性 createTime，映射不上
```

开启驼峰转换（map-underscore-to-camel-case=true）。

**坑 5：忘记关闭 SqlSession**

```java
SqlSession session = sqlSessionFactory.openSession();
// 用完不 close，连接泄漏
```

try-finally 关闭（Spring 集成时自动管理）。

**坑 6：批量插入用循环单条**

```java
for (User u : users) {
    mapper.insert(u);   // 循环单条，慢
}
```

批量插入（batch 或 foreach）。
