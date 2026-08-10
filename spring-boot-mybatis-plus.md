---
title: Spring Boot 集成 MyBatis-Plus 详解
created: 2026-08-10
updated: 2026-08-10
type: integration
tags: [spring-boot, mybatis, mybatis-plus, database, orm]
---

> 整理日期：2026-08-10

## 目录

1. [概述](#1-概述)
2. [环境搭建](#2-环境搭建)
3. [BaseMapper 通用 CRUD](#3-basemapper-通用-crud)
4. [条件构造器](#4-条件构造器)
5. [分页查询](#5-分页查询)
6. [主键策略](#6-主键策略)
7. [逻辑删除](#7-逻辑删除)
8. [自动填充](#8-自动填充)
9. [乐观锁](#9-乐观锁)
10. [代码生成器](#10-代码生成器)
11. [多租户](#11-多租户)
12. [字段类型处理器](#12-字段类型处理器)
13. [数据权限](#13-数据权限)
14. [应用场景实战](#14-应用场景实战)
15. [最佳实践与踩坑记录](#15-最佳实践与踩坑记录)
16. [参考链接](#16-参考链接)

---

## 1. 概述

### 1.1 MyBatis-Plus 是什么

MyBatis-Plus（简称 MP）是 MyBatis 的增强工具，在 MyBatis 基础上只做增强不做改变。核心思路：**单表 CRUD 不需要写一行 SQL，复杂查询继续用 MyBatis 的灵活能力**。

一句话：让你少写样板代码，但不在复杂场景拖你后腿。

### 1.2 解决了什么问题

| 痛点 | MyBatis 原生 | MyBatis-Plus |
|------|------------|-------------|
| 单表 CRUD 要手写 XML | 每个表写一套 | 继承 BaseMapper 即可 |
| 条件查询拼接麻烦 | Example/Criteria 笨重 | Lambda 表达式构造条件 |
| 分页需要 PageHelper | 额外引入依赖 | 内置分页插件 |
| 主键生成策略 | 手动处理 | 注解驱动，多种策略 |
| 逻辑删除 | 每次 UPDATE xxx=1 | 注解 + 自动拼接 |
| 通用字段填充 | 手动 set | 注解 + 处理器 |
| 乐观锁 | 自己实现 | 注解 + 插件 |

### 1.3 与 MyBatis 的关系

MP 不是替代 MyBatis——底层还是 MyBatis。MP 做了两件事：

- 启动时分析实体类，自动生成单表 CRUD 的 SQL
- 运行时通过插件机制增强 MyBatis 的行为（分页、乐观锁、多租户等）

你随时可以绕过 MP 写原生 MyBatis SQL，互不干扰。

参见 [[spring-boot-mybatis]] 了解 MyBatis 基础用法。

---

## 2. 环境搭建

### 2.1 版本选择

MyBatis-Plus 3.5.5+ 适配 Spring Boot 3.x（jakarta 命名空间）。Spring Boot 2.x 用 3.5.x 但注意 artifactId 不带 "boot3"。

本文以 Spring Boot 3.x + MyBatis-Plus 3.5.7 为例。

### 2.2 依赖引入

**Maven：**

```xml
<!-- MyBatis-Plus Starter（已包含 MyBatis、MyBatis-Spring、自动配置） -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
    <version>3.5.7</version>
</dependency>

<!-- 数据库驱动 -->
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <scope>runtime</scope>
</dependency>

<!-- 代码生成器（可选，单独引入） -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-generator</artifactId>
    <version>3.5.7</version>
</dependency>

<!-- 生成器模板引擎（可选，默认使用 Velocity） -->
<dependency>
    <groupId>org.apache.velocity</groupId>
    <artifactId>velocity-engine-core</artifactId>
    <version>2.3</version>
</dependency>
```

**Gradle：**

```groovy
implementation 'com.baomidou:mybatis-plus-spring-boot3-starter:3.5.7'
runtimeOnly 'com.mysql:mysql-connector-j'
```

注意：不要同时引入 `mybatis-spring-boot-starter`，MP 的 starter 已经包含，同时出现会冲突。

### 2.3 application.yml 配置

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/mp_demo?useUnicode=true&characterEncoding=utf8mb4&serverTimezone=Asia/Shanghai
    username: root
    password: root
    driver-class-name: com.mysql.cj.jdbc.Driver
    # 连接池（默认 HikariCP）
    hikari:
      minimum-idle: 5                              # 最小空闲连接
      maximum-pool-size: 20                        # 最大连接数
      idle-timeout: 300000                         # 空闲超时（ms）
      connection-timeout: 30000                    # 连接超时（ms）

# MyBatis-Plus 配置
mybatis-plus:
  # 实体类扫描路径（多个用逗号分隔）
  type-aliases-package: com.example.mp.entity
  # XML 映射文件位置（默认 classpath*:/mapper/**/*.xml）
  mapper-locations: classpath*:/mapper/**/*.xml
  configuration:
    # 日志输出（开发时建议开启，生产关闭）
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl
    # 下划线转驼峰（默认开启）
    map-underscore-to-camel-case: true
    # 懒加载
    lazy-loading-enabled: true
  global-config:
    db-config:
      # 主键类型：AUTO=数据库自增，ASSIGN_ID=雪花算法，INPUT=手动输入
      id-type: ASSIGN_ID
      # 逻辑删除字段名
      logic-delete-field: deleted
      # 逻辑删除-未删除值
      logic-not-delete-value: 0
      # 逻辑删除-已删除值
      logic-delete-value: 1
      # 字段填充策略（3.5.0+ 已移除，改用 @TableField(fill=...) 注解控制）
      # 表名前缀
      table-prefix: t_
```

### 2.4 启动类配置

```java
package com.example.mp;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.example.mp.mapper")  // 扫描 Mapper 接口
public class MpApplication {
    public static void main(String[] args) {
        SpringApplication.run(MpApplication.class, args);
    }
}
```

`@MapperScan` 指定 Mapper 接口所在包路径，启动时自动生成代理实现。

---

## 3. BaseMapper 通用 CRUD

### 3.1 实体类定义

```java
package com.example.mp.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("t_user")  // 指定表名（不写则默认驼峰转下划线：UserInfo -> user_info）
public class User {

    @TableId(type = IdType.ASSIGN_ID)  // 主键策略：雪花算法
    private Long id;

    private String username;

    private String email;

    private Integer age;

    @TableField(value = "phone_number")  // 字段名与列名不一致时指定
    private String phoneNumber;

    @TableField(exist = false)  // 非数据库字段
    private String remark;

    @TableLogic  // 逻辑删除字段
    private Integer deleted;

    @TableField(fill = FieldFill.INSERT)  // 插入时自动填充
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)  // 插入和更新时自动填充
    private LocalDateTime updateTime;
}
```

### 3.2 Mapper 接口

```java
package com.example.mp.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.mp.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 继承 BaseMapper 之后，以下方法全部可用，不需要写任何实现：
    //
    //   int insert(T entity)
    //   int deleteById(Serializable id)
    //   int deleteByMap(Map<String, Object> columnMap)
    //   int delete(Wrapper<T> wrapper)
    //   int updateById(T entity)
    //   int update(T entity, Wrapper<T> updateWrapper)
    //   T selectById(Serializable id)
    //   List<T> selectBatchIds(Collection<?> idList)
    //   List<T> selectByMap(Map<String, Object> columnMap)
    //   T selectOne(Wrapper<T> wrapper)  -- 小心：多条结果抛异常
    //   long selectCount(Wrapper<T> wrapper)
    //   List<T> selectList(Wrapper<T> wrapper)
    //   List<Map<String, Object>> selectMaps(Wrapper<T> wrapper)
    //   List<Object> selectObjs(Wrapper<T> wrapper)
    //   IPage<T> selectPage(IPage<T> page, Wrapper<T> wrapper)
}
```

### 3.3 基本操作示例

```java
@SpringBootTest
class UserMapperTest {

    @Autowired
    private UserMapper userMapper;

    // ==================== 插入 ====================

    @Test
    void insert() {
        User user = new User();
        user.setUsername("张三");
        user.setEmail("zhangsan@example.com");
        user.setAge(25);
        userMapper.insert(user);  // 自动回填主键到 user.id
        System.out.println("生成的主键：" + user.getId());
    }

    // ==================== 查询 ====================

    @Test
    void selectById() {
        User user = userMapper.selectById(1L);
        System.out.println(user);
    }

    @Test
    void selectBatchIds() {
        List<User> users = userMapper.selectBatchIds(Arrays.asList(1L, 2L, 3L));
        users.forEach(System.out::println);
    }

    @Test
    void selectByMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("age", 25);  // 列名用数据库字段名
        List<User> users = userMapper.selectByMap(map);
    }

    // ==================== 更新 ====================

    @Test
    void updateById() {
        User user = userMapper.selectById(1L);
        user.setAge(30);
        userMapper.updateById(user);
    }

    // ==================== 删除 ====================

    @Test
    void deleteById() {
        userMapper.deleteById(1L);
    }

    @Test
    void deleteBatchIds() {
        userMapper.deleteBatchIds(Arrays.asList(1L, 2L, 3L));
    }
}
```

### 3.4 Service 层封装

MP 提供 `IService` 接口和 `ServiceImpl` 实现类，进一步封装 Mapper 层：

```java
// 接口
package com.example.mp.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.example.mp.entity.User;

public interface UserService extends IService<User> {
    // 自定义方法在这里声明
    boolean checkUsernameExists(String username);
}

// 实现
package com.example.mp.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.mp.entity.User;
import com.example.mp.mapper.UserMapper;
import org.springframework.stereotype.Service;

@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    @Override
    public boolean checkUsernameExists(String username) {
        return this.lambdaQuery()
                .eq(User::getUsername, username)
                .count() > 0;
    }
}
```

IService 比 BaseMapper 多了批量操作和链式调用的便捷方法：

```java
// 批量保存（每批 1000 条）
boolean success = userService.saveBatch(userList, 1000);

// 批量保存或更新（根据主键是否存在决定）
boolean success = userService.saveOrUpdateBatch(userList);

// 链式查询
List<User> list = userService.lambdaQuery()
        .gt(User::getAge, 18)
        .like(User::getUsername, "张")
        .list();

// 链式更新
boolean updated = userService.lambdaUpdate()
        .set(User::getAge, 99)
        .eq(User::getUsername, "张三")
        .update();
```

---

## 4. 条件构造器

条件构造器是 MP 最常用的功能，替代在 XML 里拼动态 SQL。

### 4.1 三种 Wrapper

| 类型 | 用途 | 特点 |
|------|------|------|
| `QueryWrapper<T>` | 查询条件 | 字段名用字符串，硬编码 |
| `UpdateWrapper<T>` | 更新条件 | 支持 set 字段值 |
| `LambdaQueryWrapper<T>` | 查询条件（Lambda） | 字段名用 Lambda 表达式，编译期检查，重构友好 |
| `LambdaUpdateWrapper<T>` | 更新条件（Lambda） | 同上 |

推荐使用 Lambda 系列——重构实体类字段名后发现不了的问题，Lambda 写法编译期直接报错。

### 4.2 QueryWrapper

```java
// 字符串方式（字段名写死，不推荐）
QueryWrapper<User> query = new QueryWrapper<>();
query.select("id", "username", "email")        // 指定查询列
     .eq("age", 25)                             // =
     .ne("status", 0)                           // !=
     .gt("age", 18)                             // >
     .ge("age", 18)                             // >=
     .lt("age", 60)                             // <
     .le("age", 60)                             // <=
     .between("create_time", start, end)        // BETWEEN
     .notBetween("age", 18, 30)                 // NOT BETWEEN
     .like("username", "张")                    // LIKE '%张%'
     .notLike("username", "李")                 // NOT LIKE '%李%'
     .likeLeft("username", "张")                // LIKE '%张'
     .likeRight("username", "张")               // LIKE '张%'
     .isNull("email")                           // IS NULL
     .isNotNull("email")                        // IS NOT NULL
     .in("age", Arrays.asList(18, 20, 25))      // IN
     .notIn("age", Arrays.asList(1, 2, 3))      // NOT IN
     .inSql("id", "SELECT user_id FROM order WHERE amount > 100")  // IN (子查询)
     .groupBy("dept_id")                        // GROUP BY
     .having("COUNT(*) > {0}", 5)               // HAVING
     .orderByAsc("age")                         // ORDER BY ASC
     .orderByDesc("create_time");               // ORDER BY DESC

List<User> users = userMapper.selectList(query);
```

### 4.3 LambdaQueryWrapper（推荐）

```java
LambdaQueryWrapper<User> lambdaQuery = new LambdaQueryWrapper<>();
lambdaQuery.select(User::getId, User::getUsername)
        .eq(User::getAge, 25)
        .like(User::getUsername, "张")
        .orderByDesc(User::getCreateTime);
List<User> users = userMapper.selectList(lambdaQuery);

// 链式写法（需声明变量类型，否则编译器推断不出来）
LambdaQueryWrapper<User> wrapper = Wrappers.<User>lambdaQuery()
        .eq(User::getAge, 25)
        .like(User::getUsername, "张");
```

### 4.4 LambdaUpdateWrapper

```java
// 方式一：用 UpdateWrapper
LambdaUpdateWrapper<User> updateWrapper = new LambdaUpdateWrapper<>();
updateWrapper.set(User::getAge, 30)             // SET age = 30
        .set(User::getEmail, "new@example.com") // SET email = 'new@example.com'
        .eq(User::getId, 1L);                   // WHERE id = 1
userMapper.update(null, updateWrapper);         // 第一个参数传 null

// 方式二：链式
LambdaUpdateWrapper<User> wrapper = Wrappers.<User>lambdaUpdate()
        .set(User::getAge, 30)
        .eq(User::getId, 1L);
userMapper.update(null, wrapper);
```

### 4.5 条件嵌套

复杂 WHERE 条件用 `and()` 和 `or()` 嵌套：

```java
// SQL: WHERE (age < 30 AND age > 18) OR (email IS NOT NULL AND status = 1)
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.and(w -> w.lt(User::getAge, 30).gt(User::getAge, 18))
        .or(w -> w.isNotNull(User::getEmail).eq(User::getStatus, 1));
```

### 4.6 动态条件

配合前端传入的查询参数，只拼接非空条件：

```java
// 传统的 if-else 拼接
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
if (StringUtils.hasText(query.getUsername())) {
    wrapper.like(User::getUsername, query.getUsername());
}
if (query.getAge() != null) {
    wrapper.eq(User::getAge, query.getAge());
}
if (CollectionUtils.hasLength(query.getStatusList())) {
    wrapper.in(User::getStatus, query.getStatusList());
}

// 简化版：用 condition 参数（第1个参数为 false 时跳过该条件）
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.like(StringUtils.hasText(query.getUsername()), User::getUsername, query.getUsername())
        .eq(query.getAge() != null, User::getAge, query.getAge())
        .in(CollectionUtils.hasLength(query.getStatusList()), User::getStatus, query.getStatusList());
```

两种写法都可以，选择团队统一的就行。condition 参数写法更紧凑，但可读性略差。

---

## 5. 分页查询

### 5.1 分页插件配置

```java
package com.example.mp.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        // 分页插件（必须指定数据库类型）
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

### 5.2 基础分页

```java
// Page 对象
Page<User> page = new Page<>(1, 10);  // 第1页，每页10条
Page<User> result = userMapper.selectPage(page, null);  // null = 无查询条件

System.out.println("总记录数：" + result.getTotal());
System.out.println("总页数：" + result.getPages());
System.out.println("当前页数据：" + result.getRecords());
```

### 5.3 带条件分页

```java
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.gt(User::getAge, 18)
        .orderByDesc(User::getCreateTime);

Page<User> page = new Page<>(1, 10);
Page<User> result = userMapper.selectPage(page, wrapper);
```

### 5.4 自定义 SQL 分页

遇到多表联查时，在 Mapper 里自定义方法，分页参数放第一个，MP 拦截器自动处理：

```java
// Mapper 接口
@Mapper
public interface UserMapper extends BaseMapper<User> {

    @Select("SELECT u.*, o.order_count FROM t_user u " +
            "LEFT JOIN (SELECT user_id, COUNT(*) AS order_count FROM t_order GROUP BY user_id) o " +
            "ON u.id = o.user_id")
    IPage<UserVO> selectUserWithOrderCount(Page<?> page);
}

// 调用
Page<UserVO> page = new Page<>(1, 10);
IPage<UserVO> result = userMapper.selectUserWithOrderCount(page);
```

注意：如果不传 Page 参数，MP 不会自动分页，会返回全量数据。一定要在 SQL 语句前放 Page 参数。

### 5.5 分页结果转换

```java
// 把 Page<User> 转成 Page<UserVO>
Page<User> userPage = userMapper.selectPage(new Page<>(1, 10), null);
Page<UserVO> voPage = new Page<>();
BeanUtils.copyProperties(userPage, voPage, "records");  // 跳过 records 字段
List<UserVO> voList = userPage.getRecords().stream()
        .map(user -> {
            UserVO vo = new UserVO();
            BeanUtils.copyProperties(user, vo);
            vo.setDisplayName(user.getUsername() + " - " + user.getEmail());
            return vo;
        })
        .collect(Collectors.toList());
voPage.setRecords(voList);
```

---

## 6. 主键策略

### 6.1 支持的策略

```java
public enum IdType {
    AUTO(0),            // 数据库自增（需数据库支持，如 MySQL AUTO_INCREMENT）
    NONE(1),            // 无策略（3.5.0+ 已移除，等同于 INPUT）
    INPUT(2),           // 手动输入（插入前自己 set 主键值）
    ASSIGN_ID(3),       // 雪花算法（默认，推荐）
    ASSIGN_UUID(4);     // 32位 UUID 去除横线
}
```

### 6.2 雪花算法（ASSIGN_ID）

默认策略，生成 19 位纯数字 Long 型 ID。

**优点**：不依赖数据库，分布式环境下不冲突，趋势递增利于索引。

**缺点**：Long 型传给前端 JS 会精度丢失（JS number 最大安全整数 9007199254740991，16 位）。解决方案：

```java
// 在 Jackson 序列化时将 Long 转 String
@TableId(type = IdType.ASSIGN_ID)
@JsonSerialize(using = ToStringSerializer.class)  // Jackson 注解
private Long id;
```

全局配置方式（一次性解决所有实体类）：

```yaml
spring:
  jackson:
    generator:
      write-numbers-as-strings: true   # 所有数字都序列化为字符串（慎用）
```

更精确的全局配置：

```java
@Configuration
public class JacksonConfig {
    @Bean
    public Jackson2ObjectMapperBuilderCustomizer customizer() {
        return builder -> builder.serializerByType(Long.class, ToStringSerializer.instance)
                .serializerByType(Long.TYPE, ToStringSerializer.instance);
    }
}
```

### 6.3 自定义 ID 生成器

```java
@Component
public class CustomIdGenerator implements IdentifierGenerator {

    @Override
    public Number nextId(Object entity) {
        // 根据实体类名返回不同策略
        // 可以用美团 Leaf、百度 UidGenerator 等
        return SnowflakeIdWorker.generateId();
    }
}
```

### 6.4 各策略适用场景

| 策略 | 适用场景 | 注意 |
|------|----------|------|
| AUTO | 单库 MySQL | 分库分表时冲突 |
| ASSIGN_ID | 分布式系统（推荐） | JS 精度丢失需处理 |
| ASSIGN_UUID | 非数字主键 | 字符串索引性能差 |
| INPUT | 已有 ID 系统 | 手动管理 ID |

---

## 7. 逻辑删除

### 7.1 配置

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted   # 逻辑删除字段名（实体类中的属性名）
      logic-not-delete-value: 0     # 未删除值
      logic-delete-value: 1         # 已删除值
```

### 7.2 实体类标记

```java
@Data
public class User {
    @TableId
    private Long id;

    @TableLogic  // 标记为逻辑删除字段
    private Integer deleted;
}
```

### 7.3 效果

标注 `@TableLogic` 后，所有 MP 的方法会自动处理逻辑删除：

```java
// deleteById —— 实际执行：UPDATE t_user SET deleted = 1 WHERE id = ?
userMapper.deleteById(1L);

// selectList —— 实际执行：SELECT ... FROM t_user WHERE deleted = 0
List<User> users = userMapper.selectList(null);

// selectById —— 会自动加上 WHERE deleted = 0
User user = userMapper.selectById(1L);

// 自定义 SQL 需要手动加条件
// XML 里写：AND deleted = 0
```

如果你明确要查已删除的数据，用 `selectList` 还是会被自动过滤。绕过方式：自己写 XML 中的 SQL——MP 不会注入非 MP 方法的 SQL。

---

## 8. 自动填充

处理 createTime、updateTime、createBy 这类每个表都有的审计字段。

### 8.1 实体类标记

```java
@Data
public class User {

    @TableField(fill = FieldFill.INSERT)            // 插入时填充
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)     // 插入和更新时填充
    private LocalDateTime updateTime;

    @TableField(fill = FieldFill.INSERT)            // 插入时填充
    private Long createBy;
}
```

### 8.2 处理器实现

```java
package com.example.mp.handler;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import org.apache.ibatis.reflection.MetaObject;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class MyMetaObjectHandler implements MetaObjectHandler {

    @Override
    public void insertFill(MetaObject metaObject) {
        // 参数：字段名、填充值、metaObject
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());

        // 如果需要从 SecurityContext 获取当前用户
        // Long currentUserId = SecurityUtils.getCurrentUserId();
        // this.strictInsertFill(metaObject, "createBy", Long.class, currentUserId);
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```

### 8.3 小心 strictFill 的陷阱

`strictFill` 要求实体类中字段值为 null 才填充。如果你手动 set 了 null 想让它填充，用 `fillStrategy` 或 `setFieldValByName`：

```java
@Override
public void insertFill(MetaObject metaObject) {
    // 不论字段是否为 null 都填充
    this.setFieldValByName("createTime", LocalDateTime.now(), metaObject);
}
```

---

## 9. 乐观锁

### 9.1 使用场景

并发更新时防止数据覆盖。核心思路：读数据时拿到 version 值，更新时 WHERE 里加上 version = 旧值，更新成功代表没被改过。

### 9.2 配置

```java
@Configuration
public class MybatisPlusConfig {
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new OptimisticLockerInnerInterceptor());  // 乐观锁插件
        return interceptor;
    }
}
```

### 9.3 实体类标记

```java
@Data
public class Product {
    @TableId
    private Long id;
    private String name;
    private Integer stock;

    @Version  // 乐观锁版本号字段
    private Integer version;
}
```

### 9.4 使用示例

```java
// 扣库存的并发安全写法
public boolean deductStock(Long productId, int quantity) {
    // 1. 查询当前库存和版本号
    Product product = productMapper.selectById(productId);
    if (product.getStock() < quantity) {
        throw new RuntimeException("库存不足");
    }

    // 2. 设置新库存——MP 会自动在 WHERE 条件里加 version
    product.setStock(product.getStock() - quantity);

    // 实际 SQL：UPDATE t_product SET stock=?, version=version+1
    //          WHERE id=? AND version=?（旧版本号）
    int rows = productMapper.updateById(product);

    // 3. 返回 false 说明版本号已变，被其他线程改过
    return rows > 0;
}
```

### 9.5 乐观锁 vs 悲观锁

| 维度 | 乐观锁 | 悲观锁 |
|------|--------|--------|
| 实现方式 | version 字段 | SELECT ... FOR UPDATE |
| 适用场景 | 读多写少，冲突概率低 | 写多，冲突概率高 |
| 性能 | 无锁等待 | 锁等待，可能死锁 |
| 重试 | 业务层自行重试 | 数据库层串行化 |

---

## 10. 代码生成器

MyBatis-Plus Generator 可以根据数据库表自动生成 Entity、Mapper、Service、Controller 等代码。

### 10.1 快速生成（3.5.3+ 推荐写法）

```java
// 放在 test 目录运行
public class CodeGenerator {

    public static void main(String[] args) {
        // 数据源配置
        DataSourceConfig dataSourceConfig = new DataSourceConfig.Builder(
                "jdbc:mysql://localhost:3306/mp_demo?useUnicode=true&characterEncoding=utf8mb4",
                "root",
                "root"
        ).build();

        FastAutoGenerator.create(dataSourceConfig)
                // 全局配置
                .globalConfig(builder -> builder
                        .author("Your Name")                   // 作者名（生成到 @author）
                        .outputDir("/path/to/src/main/java")   // 输出目录
                        .commentDate("yyyy-MM-dd")             // 日期格式
                        .disableOpenDir()                      // 生成后不打开目录
                )
                // 包配置
                .packageConfig(builder -> builder
                        .parent("com.example.mp")              // 父包名
                        .entity("entity")
                        .mapper("mapper")
                        .service("service")
                        .serviceImpl("service.impl")
                        .controller("controller")
                        .xml("mapper.xml")                     // XML 文件在 resources 下
                )
                // 策略配置
                .strategyConfig(builder -> builder
                        .addInclude("t_user", "t_order")       // 要生成的表（全部生成可省略）
                        .addTablePrefix("t_")                  // 过滤表前缀（t_user -> User）
                        .entityBuilder()
                        .enableLombok()                        // 实体使用 Lombok
                        .enableTableFieldAnnotation()          // 生成 @TableField
                        .logicDeleteColumnName("deleted")      // 逻辑删除字段
                        .versionColumnName("version")          // 乐观锁字段
                        .enableFileOverride()                  // 覆盖已有文件
                        .controllerBuilder()
                        .enableRestStyle()                     // @RestController
                        .mapperBuilder()
                        .enableBaseResultMap()                 // 生成 ResultMap
                        .enableBaseColumnList()                // 生成 Base_Column_List
                )
                // 模板引擎
                .templateEngine(new VelocityTemplateEngine())
                .execute();
    }
}
```

### 10.2 交互式生成

不写硬编码配置，运行时代入参：

```java
FastAutoGenerator.create("jdbc:mysql://localhost:3306/mp_demo", "root", "root")
        .globalConfig(builder -> builder.author("Your Name").outputDir("/path/to/src/main/java"))
        .packageConfig(builder -> builder.parent("com.example.mp"))
        .strategyConfig(builder -> builder
                .addInclude(scanner("表名，多个用逗号分隔：").split(","))
                .addTablePrefix("t_")
        )
        .templateEngine(new VelocityTemplateEngine())
        .execute();
```

生成后的文件结构：

```
src/main/java/com/example/mp/
├── entity/
│   └── User.java
├── mapper/
│   └── UserMapper.java
├── service/
│   └── UserService.java
│   └── impl/
│       └── UserServiceImpl.java
└── controller/
    └── UserController.java

src/main/resources/
└── mapper/
    └── UserMapper.xml
```

---

## 11. 多租户

SaaS 系统中，不同租户共享同一套表，通过 tenant_id 隔离数据。

### 11.1 插件配置

```java
@Configuration
public class MybatisPlusConfig {
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();

        // 多租户插件
        interceptor.addInnerInterceptor(new TenantLineInnerInterceptor(new TenantLineHandler() {
            @Override
            public Expression getTenantId() {
                // 从当前请求上下文获取租户 ID（如 ThreadLocal）
                Long tenantId = TenantContextHolder.getCurrentTenantId();
                return new LongValue(tenantId);
            }

            @Override
            public String getTenantIdColumn() {
                return "tenant_id";  // 数据库中的租户字段列名
            }

            @Override
            public boolean ignoreTable(String tableName) {
                // 忽略不需要隔离的表（如系统配置表）
                return "sys_config".equalsIgnoreCase(tableName)
                        || "sys_dict".equalsIgnoreCase(tableName);
            }
        }));

        return interceptor;
    }
}
```

### 11.2 上下文工具类

```java
public class TenantContextHolder {
    private static final ThreadLocal<Long> CURRENT_TENANT = new ThreadLocal<>();

    public static void setCurrentTenantId(Long tenantId) {
        CURRENT_TENANT.set(tenantId);
    }

    public static Long getCurrentTenantId() {
        return CURRENT_TENANT.get();
    }

    public static void clear() {
        CURRENT_TENANT.remove();
    }
}
```

### 11.3 拦截器中设置租户

```java
@Component
public class TenantInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        // 从请求头或 JWT 中解析租户 ID
        String tenantId = request.getHeader("X-Tenant-Id");
        if (tenantId != null) {
            TenantContextHolder.setCurrentTenantId(Long.parseLong(tenantId));
        }
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        TenantContextHolder.clear();  // 防止内存泄漏
    }
}
```

### 11.4 效果

配置后所有 MP 的 CRUD 操作会自动拼接 `tenant_id = ?`：

```java
// 原生 SQL：SELECT * FROM t_user WHERE age > 18
// MP 注入后：SELECT * FROM t_user WHERE age > 18 AND tenant_id = 100
List<User> users = userMapper.selectList(
        new LambdaQueryWrapper<User>().gt(User::getAge, 18)
);
```

注意：自定义 XML 里的 SQL 不会被 MP 自动注入 tenant_id，需要手动加。

---

## 12. 字段类型处理器

用于处理 Java 类型与数据库类型的映射，最典型的场景是 JSON 字段。

### 12.1 JSON 类型处理器（MySQL 5.7+ JSON 列）

```java
@Data
@TableName(value = "t_user", autoResultMap = true)  // 注意：必须开启 autoResultMap
public class User {
    @TableId
    private Long id;

    // 将 Java 对象序列化为 JSON 存入数据库，读取时反序列化回来
    @TableField(typeHandler = JacksonTypeHandler.class)
    private UserExtraInfo extraInfo;  // 自定义对象，存入 JSON 列
}

// 值对象
@Data
public class UserExtraInfo {
    private String nickname;
    private String avatar;
    private List<String> tags;
}
```

数据库 DDL：

```sql
CREATE TABLE t_user (
    id BIGINT PRIMARY KEY,
    extra_info JSON COMMENT '扩展信息'
);
```

### 12.2 集合类型处理器

```java
// 将 List<String> 存为逗号分隔的字符串
@TableField(typeHandler = CommaDelimitedListTypeHandler.class)
private List<String> hobbies;  // 数据库存 '篮球,足球,游泳'，读取自动转 List
```

### 12.3 自定义类型处理器

```java
// 加密处理器：存库时加密，读库时解密
public class EncryptTypeHandler extends BaseTypeHandler<String> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, String parameter, JdbcType jdbcType)
            throws SQLException {
        ps.setString(i, AESUtils.encrypt(parameter));  // 加密
    }

    @Override
    public String getNullableResult(ResultSet rs, String columnName) throws SQLException {
        return AESUtils.decrypt(rs.getString(columnName));  // 解密
    }

    @Override
    public String getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        return AESUtils.decrypt(rs.getString(columnIndex));
    }

    @Override
    public String getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        return AESUtils.decrypt(cs.getString(columnIndex));
    }
}

// 使用
@TableField(typeHandler = EncryptTypeHandler.class)
private String phone;  // 存库加密，读库解密
```

---

## 13. 数据权限

数据权限和多租户的原理一致：通过拦截器在 SQL 层面注入额外的 WHERE 条件。

### 13.1 简易数据权限拦截器

```java
@Component
public class DataScopeInnerInterceptor implements InnerInterceptor {

    @Override
    public void beforeQuery(Executor executor, MappedStatement ms, Object parameter,
                            RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql) throws SQLException {
        // 从上下文获取当前用户的数据权限范围
        DataScope dataScope = DataScopeContextHolder.get();
        if (dataScope == null) return;

        // 在原始 SQL 上追加数据权限条件
        String originalSql = boundSql.getSql();
        String scopeCondition = buildScopeCondition(dataScope);
        String newSql = originalSql + " AND " + scopeCondition;

        // 通过反射替换 BoundSql 中的 SQL（具体实现略）
        // Field field = BoundSql.class.getDeclaredField("sql");
        // field.setAccessible(true);
        // field.set(boundSql, newSql);
    }

    private String buildScopeCondition(DataScope scope) {
        switch (scope.getScopeType()) {
            case ALL:
                return "1 = 1";
            case DEPT:
                return "dept_id = " + scope.getDeptId();
            case DEPT_AND_CHILD:
                return "dept_id IN (" + String.join(",", scope.getDeptIds()) + ")";
            case SELF:
                return "create_by = " + scope.getUserId();
            default:
                return "1 = 0";  // 没有权限
        }
    }
}
```

### 13.2 使用方式

在 Controller 层根据当前用户设置数据权限范围，Service 层执行 SQL 时自动生效。

```java
// Controller
@GetMapping("/orders")
public R listOrders() {
    // 当前用户是部门经理，设置可看本部门及子部门数据
    DataScopeContextHolder.set(new DataScope(ScopeType.DEPT_AND_CHILD, currentUser.getDeptIds()));
    List<Order> orders = orderService.list();
    DataScopeContextHolder.clear();
    return R.ok(orders);
}
```

---

## 14. 应用场景实战

### 场景一：用户管理系统 CRUD

通用后台管理的典型实现——Controller + Service + Mapper 三层。

**数据库表：**

```sql
CREATE TABLE t_user (
    id          BIGINT PRIMARY KEY COMMENT '主键',
    username    VARCHAR(50)  NOT NULL COMMENT '用户名',
    password    VARCHAR(255) NOT NULL COMMENT '密码',
    email       VARCHAR(100) COMMENT '邮箱',
    phone       VARCHAR(20)  COMMENT '手机号',
    age         INT          COMMENT '年龄',
    status      TINYINT      DEFAULT 1 COMMENT '状态: 0禁用 1启用',
    deleted     TINYINT      DEFAULT 0 COMMENT '逻辑删除: 0未删除 1已删除',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) COMMENT '用户表';
```

**查询请求 DTO：**

```java
@Data
public class UserQueryDTO {
    private String username;        // 用户名（模糊搜索）
    private String email;           // 邮箱（精确搜索）
    private Integer minAge;         // 最小年龄
    private Integer maxAge;         // 最大年龄
    private Integer status;         // 状态
    private List<Long> deptIds;     // 部门 ID 列表
    private String beginTime;       // 创建时间起
    private String endTime;         // 创建时间止
}
```

**Service 实现：**

```java
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    @Override
    public IPage<User> pageQuery(UserQueryDTO query) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();

        // 动态条件拼接
        wrapper.like(StringUtils.hasText(query.getUsername()), User::getUsername, query.getUsername())
                .eq(StringUtils.hasText(query.getEmail()), User::getEmail, query.getEmail())
                .ge(query.getMinAge() != null, User::getAge, query.getMinAge())
                .le(query.getMaxAge() != null, User::getAge, query.getMaxAge())
                .eq(query.getStatus() != null, User::getStatus, query.getStatus())
                .in(CollectionUtils.isNotEmpty(query.getDeptIds()), User::getDeptId, query.getDeptIds())
                .ge(StringUtils.hasText(query.getBeginTime()), User::getCreateTime, query.getBeginTime())
                .le(StringUtils.hasText(query.getEndTime()), User::getCreateTime, query.getEndTime())
                .orderByDesc(User::getCreateTime);

        return this.page(new Page<>(query.getPageNum(), query.getPageSize()), wrapper);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean createUser(UserCreateDTO dto) {
        // 校验用户名唯一
        long count = this.lambdaQuery()
                .eq(User::getUsername, dto.getUsername())
                .count();
        if (count > 0) {
            throw new BusinessException("用户名已存在");
        }

        User user = new User();
        BeanUtils.copyProperties(dto, user);
        user.setPassword(BCrypt.hashpw(dto.getPassword(), BCrypt.gensalt()));  // 密码加密
        return this.save(user);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateUser(UserUpdateDTO dto) {
        User user = this.getById(dto.getId());
        if (user == null) {
            throw new BusinessException("用户不存在");
        }

        // 只更新非 null 字段
        if (StringUtils.hasText(dto.getEmail())) {
            user.setEmail(dto.getEmail());
        }
        if (StringUtils.hasText(dto.getPhone())) {
            user.setPhone(dto.getPhone());
        }
        if (dto.getStatus() != null) {
            user.setStatus(dto.getStatus());
        }

        return this.updateById(user);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchDelete(List<Long> ids) {
        // 逻辑删除——实际上是 UPDATE
        return this.removeBatchByIds(ids);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchUpdateStatus(List<Long> ids, Integer status) {
        // 批量更新状态（只发一条 SQL）
        LambdaUpdateWrapper<User> wrapper = new LambdaUpdateWrapper<>();
        wrapper.set(User::getStatus, status)
                .in(User::getId, ids);
        return this.update(wrapper);
    }
}
```

**Controller 实现：**

```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping
    public R<IPage<User>> page(UserQueryDTO query) {
        return R.ok(userService.pageQuery(query));
    }

    @GetMapping("/{id}")
    public R<User> getById(@PathVariable Long id) {
        return R.ok(userService.getById(id));
    }

    @PostMapping
    public R<Void> create(@RequestBody @Valid UserCreateDTO dto) {
        userService.createUser(dto);
        return R.ok();
    }

    @PutMapping("/{id}")
    public R<Void> update(@PathVariable Long id, @RequestBody @Valid UserUpdateDTO dto) {
        dto.setId(id);
        userService.updateUser(dto);
        return R.ok();
    }

    @DeleteMapping("/batch")
    public R<Void> batchDelete(@RequestBody List<Long> ids) {
        userService.batchDelete(ids);
        return R.ok();
    }

    @PutMapping("/batch/status")
    public R<Void> batchUpdateStatus(@RequestBody @Valid BatchStatusDTO dto) {
        userService.batchUpdateStatus(dto.getIds(), dto.getStatus());
        return R.ok();
    }
}
```

### 场景二：订单系统——多表联合查询 + 乐观锁扣库存

订单创建需要：校验库存并发安全、生成订单号、关联订单明细。

**实体类：**

```java
@Data
@TableName("t_product")
public class Product {
    @TableId(type = IdType.ASSIGN_ID)
    private Long id;
    private String name;
    private BigDecimal price;
    private Integer stock;      // 库存

    @Version                     // 乐观锁
    private Integer version;
}

@Data
@TableName("t_order")
public class Order {
    @TableId(type = IdType.ASSIGN_ID)
    private Long id;
    private String orderNo;      // 订单号
    private Long userId;
    private BigDecimal totalAmount;
    private Integer status;      // 0待支付 1已支付 2已取消

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}

@Data
@TableName("t_order_item")
public class OrderItem {
    @TableId(type = IdType.ASSIGN_ID)
    private Long id;
    private Long orderId;
    private Long productId;
    private String productName;
    private BigDecimal price;    // 下单时单价（快照）
    private Integer quantity;
}
```

**订单创建的 Service：**

```java
@Service
public class OrderServiceImpl extends ServiceImpl<OrderMapper, Order> implements OrderService {

    @Autowired
    private ProductMapper productMapper;
    @Autowired
    private OrderItemMapper orderItemMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OrderCreateVO createOrder(Long userId, List<OrderItemDTO> items) {
        // 1. 查询商品信息
        List<Long> productIds = items.stream()
                .map(OrderItemDTO::getProductId)
                .collect(Collectors.toList());
        List<Product> products = productMapper.selectBatchIds(productIds);

        // 构建 productId -> Product 映射
        Map<Long, Product> productMap = products.stream()
                .collect(Collectors.toMap(Product::getId, Function.identity()));

        BigDecimal totalAmount = BigDecimal.ZERO;

        // 2. 逐个扣库存（乐观锁保证并发安全）
        for (OrderItemDTO item : items) {
            Product product = productMap.get(item.getProductId());
            if (product == null) {
                throw new BusinessException("商品不存在: " + item.getProductId());
            }
            if (product.getStock() < item.getQuantity()) {
                throw new BusinessException("库存不足: " + product.getName());
            }

            // 扣减库存——MP 自动加 version 条件
            product.setStock(product.getStock() - item.getQuantity());
            int rows = productMapper.updateById(product);
            if (rows == 0) {
                throw new BusinessException("下单失败，库存变动，请重试");
            }

            // 累加金额（单价从数据库取，不用前端传的值）
            totalAmount = totalAmount.add(
                    product.getPrice().multiply(BigDecimal.valueOf(item.getQuantity()))
            );
        }

        // 3. 创建订单
        Order order = new Order();
        order.setOrderNo(generateOrderNo());  // ORD + 时间戳 + 随机数
        order.setUserId(userId);
        order.setTotalAmount(totalAmount);
        order.setStatus(0);
        this.save(order);

        // 4. 批量插入订单明细
        List<OrderItem> orderItems = items.stream().map(dto -> {
            OrderItem item = new OrderItem();
            item.setOrderId(order.getId());
            item.setProductId(dto.getProductId());
            // 快照：记录下单时的商品名和单价
            Product product = productMap.get(dto.getProductId());
            item.setProductName(product.getName());
            item.setPrice(product.getPrice());
            item.setQuantity(dto.getQuantity());
            return item;
        }).collect(Collectors.toList());
        orderItemMapper.insert(orderItems);  // 批量插入（需 XML）

        // 5. 组装返回
        OrderCreateVO vo = new OrderCreateVO();
        vo.setOrderId(order.getId());
        vo.setOrderNo(order.getOrderNo());
        vo.setTotalAmount(totalAmount);
        return vo;
    }

    private String generateOrderNo() {
        String date = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String random = String.format("%06d", new Random().nextInt(999999));
        return "ORD" + date + random;
    }
}
```

**订单明细批量插入的 Mapper XML：**

```xml
<!-- OrderItemMapper.xml -->
<mapper namespace="com.example.mp.mapper.OrderItemMapper">
    <insert id="insert" parameterType="list">
        INSERT INTO t_order_item (id, order_id, product_id, product_name, price, quantity)
        VALUES
        <foreach collection="list" item="item" separator=",">
            (#{item.id}, #{item.orderId}, #{item.productId}, #{item.productName}, #{item.price}, #{item.quantity})
        </foreach>
    </insert>
</mapper>
```

**订单列表查询（多表关联）：**

```java
// Mapper 接口
@Mapper
public interface OrderMapper extends BaseMapper<Order> {

    // 多表关联分页查询
    IPage<OrderVO> selectOrderPage(Page<?> page,
                                    @Param("userId") Long userId,
                                    @Param("status") Integer status,
                                    @Param("beginTime") String beginTime,
                                    @Param("endTime") String endTime);
}
```

```xml
<!-- OrderMapper.xml -->
<mapper namespace="com.example.mp.mapper.OrderMapper">
    <select id="selectOrderPage" resultType="com.example.mp.vo.OrderVO">
        SELECT
            o.id,
            o.order_no,
            o.total_amount,
            o.status,
            o.create_time,
            u.username AS userName,
            COUNT(oi.id) AS itemCount
        FROM t_order o
        LEFT JOIN t_user u ON o.user_id = u.id
        LEFT JOIN t_order_item oi ON o.id = oi.order_id
        <where>
            <if test="userId != null">
                AND o.user_id = #{userId}
            </if>
            <if test="status != null">
                AND o.status = #{status}
            </if>
            <if test="beginTime != null and beginTime != ''">
                AND o.create_time >= #{beginTime}
            </if>
            <if test="endTime != null and endTime != ''">
                AND o.create_time &lt;= #{endTime}
            </if>
        </where>
        GROUP BY o.id
        ORDER BY o.create_time DESC
    </select>
</mapper>
```

---

## 15. 最佳实践与踩坑记录

### 15.1 推荐做法

**1. Lambda 表达式写条件，不用字符串**

字符串字段名重构时不会报错，上线才发现。Lambda 编译期检查。

```java
// 不推荐
wrapper.eq("user_name", "张三");

// 推荐
wrapper.eq(User::getUsername, "张三");
```

**2. 复杂查询回归 MyBatis XML**

不要把什么都塞进 Wrapper。超过 3 个表 JOIN、复杂子查询、CASE WHEN 之类，直接在 XML 里写 SQL——MP 不是 SQL 的替代品。

**3. 显式指定 @TableName 和 @TableField**

命名规范一改就坏。显式声明，心里踏实。

```java
@TableName("t_user")          // 就算表名不变，显式写出来
@TableField("phone_number")   // 同上
```

**4. 分页查询统一封装**

```java
// 避免每个方法 new Page
public class PageQuery {
    private Integer pageNum = 1;
    private Integer pageSize = 10;

    public <T> Page<T> toPage() {
        return new Page<>(pageNum, pageSize);
    }
}
```

**5. 主键用 ASSIGN_ID，全局配置 Jackson 序列化**

雪花算法是分布式默认选择。顺手配好 Jackson 避免前端精度丢失。

**6. 逻辑删除字段加索引**

逻辑删除后，所有查询自动拼接 `deleted = 0`。如果你的查询频繁，给 deleted 字段加联合索引：

```sql
INDEX idx_deleted_create_time (deleted, create_time)  -- 常用排序字段
```

### 15.2 踩坑记录

**坑 1：selectOne 查到多条抛异常**

`selectOne(wrapper)` 查不到返回 null，查到多条抛 `TooManyResultsException`。不确认唯一性时用 `selectList` 取第一条，或用 `selectCount` 先判断。

**坑 2：MyBatis-Plus 和 MyBatis Starter 冲突**

`mybatis-plus-boot-starter` 已包含 `mybatis-spring-boot-starter`。两个同时引入会出现：
- DataSource 循环依赖
- SqlSessionFactory 冲突

排错方法：`mvn dependency:tree | grep mybatis` 确认只有一个版本。

**坑 3：3.5.x 升级 3.5.5+ 后 pageSize 默认值变了**

3.5.5 之前分页默认 pageSize=10，3.5.5+ 改成了 -1（无限制，返回全量）。设置 `mybatis-plus.page.size-limit` 或显式传 pageSize。

**坑 4：逻辑删除后关联查询漏数据**

A 表逻辑删除，B 表通过 A.id 关联查询时，B 表的数据成了"幽灵数据"。关联查询必须在 SQL 里手动过滤 A 表的 deleted：

```sql
LEFT JOIN t_article a ON c.article_id = a.id AND a.deleted = 0
```

MP 不会自动注入 JOIN 语句的 ON 条件。

**坑 5：批量操作用的是循环单条**

`saveBatch(userList)` 和 `updateBatchById(userList)` 底层默认是循环逐条执行。数据量大的时候效率很低，建议自己写 XML 批量 INSERT：

```
<!-- 批量插入 -->
INSERT INTO t_user (id, username, email) VALUES
<foreach collection="list" item="item" separator=",">
    (#{item.id}, #{item.username}, #{item.email})
</foreach>
```

或者配置 JDBC URL 参数 `rewriteBatchedStatements=true`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/mp_demo?rewriteBatchedStatements=true
```

**坑 6：乐观锁更新失败返回 0 但不是异常**

`updateById` 因为 version 不匹配返回 0 行，MP 不抛异常。业务层必须检查返回值，失败后重试或提示用户。

**坑 7：@TableField(exist = false) 在 XML resultMap 里无效**

仅仅是 MP 自动映射时忽略该字段。XML 的 `<resultMap>` 写了 exist=false 的字段，照样会报错（找不到列）。要么用 `<result column="..." property="...">` 但 SQL 里不 select，要么去掉。

**坑 8：字段自动填充和手动 set 同时存在**

`strictInsertFill` 的规则：字段值非 null 时不填充。如果你显式 set 了一个值又期望自动填充覆盖，用 `setFieldValByName` 替代。

---

## 16. 参考链接

- MyBatis-Plus 官方文档：https://baomidou.com/
- MyBatis-Plus GitHub：https://github.com/baomidou/mybatis-plus
- MyBatis-Plus 示例项目：https://github.com/baomidou/mybatis-plus-samples
- MyBatis 官方文档：https://mybatis.org/mybatis-3/zh/index.html
- Spring Boot 官方文档：https://docs.spring.io/spring-boot/docs/current/reference/html/
- [[spring-boot-mybatis]] — MyBatis 基础用法
- [[spring-boot-redis]] — MyBatis 二级缓存集成 Redis
