---
title: Spring Boot 集成 MyBatis 详解
created: 2026-08-10
updated: 2026-08-10
type: integration
tags: [spring-boot, mybatis, mybatis-plus, database, orm]
---

> 整理日期：2026-08-10

## 目录

1. [概述](#1-概述)
2. [MyBatis vs JPA 选型](#2-mybatis-vs-jpa-选型)
3. [环境搭建](#3-环境搭建)
4. [配置详解](#4-配置详解)
5. [XML Mapper 基础操作](#5-xml-mapper-基础操作)
6. [注解 Mapper 快速开发](#6-注解-mapper-快速开发)
7. [动态 SQL](#7-动态-sql)
8. [高级结果映射](#8-高级结果映射)
9. [PageHelper 分页](#9-pagehelper-分页)
10. [MyBatis-Plus 增强](#10-mybatis-plus-增强)
11. [多数据源配置](#11-多数据源配置)
12. [TypeHandler 自定义类型处理](#12-typehandler-自定义类型处理)
13. [拦截器与插件](#13-拦截器与插件)
14. [应用场景实战](#14-应用场景实战)
15. [最佳实践与踩坑记录](#15-最佳实践与踩坑记录)

---

## 1. 概述

### 1.1 是什么

MyBatis 是一款半自动化的持久层框架，通过 XML 或注解将 Java 对象与 SQL 语句映射。不同于 Hibernate/JPA 的全自动 ORM，MyBatis 让你直接编写原生 SQL，同时提供参数绑定、结果映射、动态 SQL 等便利能力。

### 1.2 核心架构

```
SqlSessionFactory → SqlSession → Executor → MappedStatement → 数据库
     ↑                                                           ↓
  Configuration                                              ResultSet
     ↑                                                           ↓
  mybatis-config.xml / Mapper XML                          ResultMap → POJO
```

### 1.3 为什么选 MyBatis

- **SQL 可控**：复杂查询、多表关联、存储过程直接手写 SQL，不做过度抽象
- **学习曲线平缓**：会写 SQL 就能上手，无 JPA 的持久化上下文、级联状态等概念负担
- **动态 SQL 强大**：`<if>` `<where>` `<foreach>` 等标签解决拼接 SQL 的痛点
- **中国生态好**：MyBatis-Plus、PageHelper 等增强工具成熟，国内团队首选

---

## 2. MyBatis vs JPA 选型

| 维度 | MyBatis | JPA / Hibernate |
|------|---------|-----------------|
| SQL 控制力 | 完全自主，手写 SQL | 自动生成，JPQL/HQL补充 |
| 多表关联 | 直接写 JOIN，灵活 | @OneToMany/@ManyToOne 配置，不直观 |
| 动态查询 | XML 标签，简洁有力 | Criteria API / Specification，代码冗长 |
| 存储过程 | 原生支持 | 通过 @Procedure 调用 |
| 自动 CRUD | 需手写或 MyBatis-Plus | 内置 save()/findById() |
| 缓存 | 一二级缓存，粒度可控 | 一级（Session）/二级（SessionFactory） |
| DBA 协作 | SQL 集中在 XML，DBA 友好 | SQL 由框架生成，DBA 难以优化 |
| 学习成本 | 低（会 SQL 即可） | 高（持久化上下文、懒加载、级联） |
| 适用场景 | 复杂查询多、SQL 优化要求高 | 标准 CRUD 多、对象关系简单 |

**结论**：国内互联网项目首选 MyBatis（或 MyBatis-Plus），复杂查询场景远多于纯 CRUD。参见 [[spring-boot-redis]] 了解 MyBatis 二级缓存集成 Redis。

---

## 3. 环境搭建

### 3.1 依赖引入

**Maven：**

```xml
<!-- MyBatis Spring Boot Starter -->
<dependency>
    <groupId>org.mybatis.spring.boot</groupId>
    <artifactId>mybatis-spring-boot-starter</artifactId>
    <version>3.0.3</version>
</dependency>

<!-- MySQL 驱动 -->
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <scope>runtime</scope>
</dependency>

<!-- Druid 连接池（推荐） -->
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>druid-spring-boot-3-starter</artifactId>
    <version>1.2.23</version>
</dependency>

<!-- PageHelper 分页插件（几乎必装） -->
<dependency>
    <groupId>com.github.pagehelper</groupId>
    <artifactId>pagehelper-spring-boot-starter</artifactId>
    <version>2.1.0</version>
</dependency>
```

**Gradle：**

```groovy
implementation 'org.mybatis.spring.boot:mybatis-spring-boot-starter:3.0.3'
runtimeOnly 'com.mysql:mysql-connector-j'
implementation 'com.alibaba:druid-spring-boot-3-starter:1.2.23'
implementation 'com.github.pagehelper:pagehelper-spring-boot-starter:2.1.0'
```

### 3.2 application.yml 配置

```yaml
spring:
  datasource:
    type: com.alibaba.druid.pool.DruidDataSource      # 连接池类型
    url: jdbc:mysql://localhost:3306/mybatis_demo?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai&useSSL=false
    username: root
    password: ${DB_PASSWORD:root}                      # 环境变量优先
    driver-class-name: com.mysql.cj.jdbc.Driver

    druid:
      initial-size: 5                                  # 初始连接数
      min-idle: 5                                      # 最小空闲连接
      max-active: 20                                   # 最大活跃连接
      max-wait: 60000                                  # 获取连接最大等待
      time-between-eviction-runs-millis: 60000         # 检测间隔
      min-evictable-idle-time-millis: 300000           # 最小存活时间
      # 监控配置
      stat-view-servlet:
        enabled: true                                  # 开启 Druid 监控页
        url-pattern: /druid/*
        login-username: admin
        login-password: admin123
      filter:
        stat:
          enabled: true
          slow-sql-millis: 2000                        # 慢 SQL 阈值

# MyBatis 配置
mybatis:
  mapper-locations: classpath:mapper/**/*.xml          # XML 映射文件路径
  type-aliases-package: com.example.mybatis.entity     # 实体类别名包
  configuration:
    map-underscore-to-camel-case: true                  # 下划线转驼峰（user_name → userName）
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl  # SQL 日志输出
    cache-enabled: true                                 # 开启二级缓存
    lazy-loading-enabled: true                          # 延迟加载
    aggressive-lazy-loading: false                      # 按需延迟加载
```

### 3.3 启动类注解

```java
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.example.mybatis.mapper")  // 扫描 Mapper 接口包
public class MybatisApplication {
    public static void main(String[] args) {
        SpringApplication.run(MybatisApplication.class, args);
    }
}
```

### 3.4 项目结构

```
src/main/java/com/example/mybatis/
├── entity/              # 实体类（对应数据库表）
│   └── User.java
├── mapper/              # Mapper 接口
│   └── UserMapper.java
├── service/             # 业务层
│   ├── UserService.java
│   └── impl/
│       └── UserServiceImpl.java
├── controller/          # 控制器
│   └── UserController.java
└── config/              # 配置类（多数据源等）
    └── MybatisConfig.java

src/main/resources/
├── application.yml
└── mapper/              # XML 映射文件（与接口包结构保持一致）
    └── UserMapper.xml
```

### 3.5 验证连接

```sql
-- 先建表
CREATE DATABASE IF NOT EXISTS mybatis_demo DEFAULT CHARACTER SET utf8mb4;

USE mybatis_demo;

CREATE TABLE `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `age` INT DEFAULT NULL COMMENT '年龄',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-启用 0-禁用',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

```java
import com.example.mybatis.entity.User;
import com.example.mybatis.mapper.UserMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class MybatisConnectionTest {

    @Autowired
    private UserMapper userMapper;

    @Test
    void testConnection() {
        User user = userMapper.selectById(1L);
        // 连接成功即可，无论查没查到数据
        System.out.println(user);
    }
}
```

---

## 4. 配置详解

### 4.1 mybatis 配置参数表

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `mapper-locations` | XML Mapper 文件路径 | `classpath*:**/mapper/**/*.xml` |
| `type-aliases-package` | 实体类别名包扫描 | 无 |
| `config-location` | 全局 mybatis-config.xml 路径 | 无 |
| `map-underscore-to-camel-case` | 下划线自动转驼峰 | false |
| `log-impl` | SQL 日志实现类 | 不输出 |
| `cache-enabled` | 二级缓存开关 | true |
| `lazy-loading-enabled` | 延迟加载开关 | false |
| `aggressive-lazy-loading` | 激进延迟加载（所有属性一起加载） | false |
| `default-statement-timeout` | 默认 SQL 超时（秒） | 无（依赖驱动） |
| `default-fetch-size` | 默认结果集抓取条数 | 无（依赖驱动） |
| `call-setters-on-nulls` | 值为 null 时也调用 setter | false |
| `use-generated-keys` | 自动获取自增主键 | false |

### 4.2 Druid 连接池参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `initial-size` | 初始连接数 | 5 |
| `min-idle` | 最小空闲连接 | 5 |
| `max-active` | 最大活跃连接 | 20 ~ 50（按 QPS） |
| `max-wait` | 获取连接超时（ms） | 60000 |
| `time-between-eviction-runs-millis` | 空闲连接检测间隔 | 60000 |
| `min-evictable-idle-time-millis` | 连接最小空闲时间 | 300000 |

**连接数计算**：`max-active = (QPS × 单次查询平均耗时(ms)) / 1000 + buffer`。例如 QPS 200、查询耗时 50ms，理论需要 10 个连接，设 20 保底。

### 4.3 mybatis-config.xml 全局配置（可选）

如果配置较多，可单独抽取 `mybatis-config.xml`：

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE configuration PUBLIC "-//mybatis.org//DTD Config 3.0//EN"
    "http://mybatis.org/dtd/mybatis-3-config.dtd">
<configuration>
    <settings>
        <!-- 下划线转驼峰 -->
        <setting name="mapUnderscoreToCamelCase" value="true"/>
        <!-- 延迟加载 -->
        <setting name="lazyLoadingEnabled" value="true"/>
        <setting name="aggressiveLazyLoading" value="false"/>
        <!-- 返回主键 -->
        <setting name="useGeneratedKeys" value="true"/>
    </settings>

    <typeAliases>
        <package name="com.example.mybatis.entity"/>
    </typeAliases>

    <plugins>
        <!-- PageHelper 以 Spring Boot Starter 方式引入时无需在此配置 -->
    </plugins>
</configuration>
```

```yaml
# application.yml 中指定 config-location
mybatis:
  config-location: classpath:mybatis-config.xml
```

> **注意**：`config-location` 和 `configuration` 不能同时使用（Spring Boot 中二选一）。推荐直接在 `application.yml` 的 `mybatis.configuration` 下配置，保持简单。

---

## 5. XML Mapper 基础操作

XML Mapper 是 MyBatis 的核心开发方式，SQL 与 Java 代码完全分离，便于 DBA 协作和复杂 SQL 管理。

### 5.1 实体类

```java
package com.example.mybatis.entity;

import java.time.LocalDateTime;

public class User {
    private Long id;
    private String username;
    private String email;
    private Integer age;
    private Integer status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    // getter / setter 省略，实际开发使用 Lombok
}
```

```java
// 实际项目推荐用 Lombok
import lombok.Data;
import java.time.LocalDateTime;

@Data
public class User {
    private Long id;
    private String username;
    private String email;
    private Integer age;
    private Integer status;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
```

### 5.2 Mapper 接口

```java
package com.example.mybatis.mapper;

import com.example.mybatis.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper  // 或通过 @MapperScan 统一扫描
public interface UserMapper {

    // 单条查询
    User selectById(@Param("id") Long id);

    // 条件查询
    List<User> selectByCondition(@Param("username") String username,
                                  @Param("email") String email,
                                  @Param("status") Integer status);

    // 插入（自动回填主键）
    int insert(User user);

    // 批量插入
    int batchInsert(@Param("users") List<User> users);

    // 更新
    int update(User user);

    // 删除（物理删除）
    int deleteById(@Param("id") Long id);

    // 统计
    long count(@Param("status") Integer status);
}
```

### 5.3 XML 映射文件

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
    "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<!-- namespace = Mapper 接口全限定类名 -->
<mapper namespace="com.example.mybatis.mapper.UserMapper">

    <!-- 结果映射 -->
    <resultMap id="BaseResultMap" type="com.example.mybatis.entity.User">
        <id column="id" property="id"/>
        <result column="username" property="username"/>
        <result column="email" property="email"/>
        <result column="age" property="age"/>
        <result column="status" property="status"/>
        <result column="create_time" property="createTime"/>
        <result column="update_time" property="updateTime"/>
    </resultMap>

    <!-- 公共字段 -->
    <sql id="BaseColumns">
        id, username, email, age, status, create_time, update_time
    </sql>

    <!-- ====================== 查询 ====================== -->

    <!-- 按 ID 查询 -->
    <select id="selectById" resultMap="BaseResultMap">
        SELECT <include refid="BaseColumns"/>
        FROM `user`
        WHERE id = #{id}
    </select>

    <!-- 条件查询 -->
    <select id="selectByCondition" resultMap="BaseResultMap">
        SELECT <include refid="BaseColumns"/>
        FROM `user`
        WHERE 1 = 1
        <if test="username != null and username != ''">
            AND username LIKE CONCAT('%', #{username}, '%')
        </if>
        <if test="email != null and email != ''">
            AND email = #{email}
        </if>
        <if test="status != null">
            AND status = #{status}
        </if>
        ORDER BY id DESC
    </select>

    <!-- ====================== 插入 ====================== -->

    <!-- 插入并回填主键 -->
    <insert id="insert" useGeneratedKeys="true" keyProperty="id">
        INSERT INTO `user` (username, email, age, status, create_time, update_time)
        VALUES (#{username}, #{email}, #{age}, #{status}, NOW(), NOW())
    </insert>

    <!-- 批量插入 -->
    <insert id="batchInsert" useGeneratedKeys="true" keyProperty="id">
        INSERT INTO `user` (username, email, age, status, create_time, update_time)
        VALUES
        <foreach collection="users" item="user" separator=",">
            (#{user.username}, #{user.email}, #{user.age}, #{user.status}, NOW(), NOW())
        </foreach>
    </insert>

    <!-- ====================== 更新 ====================== -->

    <update id="update">
        UPDATE `user`
        <set>
            <if test="email != null">email = #{email},</if>
            <if test="age != null">age = #{age},</if>
            <if test="status != null">status = #{status},</if>
            update_time = NOW()
        </set>
        WHERE id = #{id}
    </update>

    <!-- ====================== 删除 ====================== -->

    <delete id="deleteById">
        DELETE FROM `user` WHERE id = #{id}
    </delete>

    <!-- ====================== 统计 ====================== -->

    <select id="count" resultType="long">
        SELECT COUNT(*) FROM `user`
        <where>
            <if test="status != null">
                status = #{status}
            </if>
        </where>
    </select>

</mapper>
```

### 5.4 参数传递方式

```java
// 方式 1：@Param 指定参数名（推荐）
User selectByUsernameAndEmail(@Param("username") String username,
                               @Param("email") String email);

// 方式 2：POJO 传参（多条件查询推荐）
List<User> selectByCondition(UserQueryDTO query);

// 方式 3：Map 传参（不推荐，可读性差）
List<User> selectByMap(Map<String, Object> params);

// 方式 4：单参数可不加 @Param
User selectById(Long id);
```

```xml
<!-- 方式 2：POJO 传参 -->
<select id="selectByCondition" resultMap="BaseResultMap">
    SELECT * FROM `user`
    <where>
        <if test="username != null">AND username = #{username}</if>
        <if test="email != null">AND email = #{email}</if>
    </where>
</select>

<!-- 方式 3：Map 传参 -->
<select id="selectByMap" resultMap="BaseResultMap">
    SELECT * FROM `user`
    <where>
        <if test="username != null">AND username = #{username}</if>
    </where>
</select>
```

---

## 6. 注解 Mapper 快速开发

简单 CRUD 场景下，可以用注解替代 XML，减少文件数量。

### 6.1 基础注解

```java
package com.example.mybatis.mapper;

import com.example.mybatis.entity.User;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface UserAnnoMapper {

    // ===== 查询 =====
    @Select("SELECT id, username, email, age, status, create_time, update_time FROM `user` WHERE id = #{id}")
    User selectById(Long id);

    @Select("SELECT id, username, email, age, status, create_time, update_time FROM `user`")
    List<User> selectAll();

    // ===== 插入 =====
    @Insert("INSERT INTO `user` (username, email, age, status, create_time, update_time) " +
            "VALUES (#{username}, #{email}, #{age}, #{status}, NOW(), NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")  // 回填主键
    int insert(User user);

    // ===== 更新 =====
    @Update("UPDATE `user` SET email = #{email}, age = #{age}, update_time = NOW() WHERE id = #{id}")
    int update(User user);

    // ===== 删除 =====
    @Delete("DELETE FROM `user` WHERE id = #{id}")
    int deleteById(Long id);
}
```

### 6.2 @Result 显式映射

当字段名不一致时，用 `@Result` 声明映射关系：

```java
@Select("SELECT id, username, email, age, status, " +
        "create_time, update_time FROM `user` WHERE id = #{id}")
@Results(id = "userResult", value = {
    @Result(column = "id", property = "id", id = true),
    @Result(column = "username", property = "username"),
    @Result(column = "create_time", property = "createTime"),
    @Result(column = "update_time", property = "updateTime")
})
User selectById(Long id);

// 复用 @Results
@Select("SELECT * FROM `user` ORDER BY id ASC")
@ResultMap("userResult")
List<User> selectAll();
```

### 6.3 @SelectProvider 动态 SQL

```java
import org.apache.ibatis.jdbc.SQL;

public class UserSqlProvider {

    public String selectByCondition(UserQueryDTO query) {
        return new SQL() {{
            SELECT("id, username, email, age, status, create_time, update_time");
            FROM("`user`");
            if (query.getUsername() != null) {
                WHERE("username LIKE CONCAT('%', #{username}, '%')");
            }
            if (query.getStatus() != null) {
                WHERE("status = #{status}");
            }
            ORDER_BY("id DESC");
        }}.toString();
    }
}
```

```java
@Mapper
public interface UserAnnoMapper {

    @SelectProvider(type = UserSqlProvider.class, method = "selectByCondition")
    List<User> selectByCondition(UserQueryDTO query);
}
```

### 6.4 注解 vs XML 选型

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| 简单 CRUD | 注解 | 减少文件，开发快 |
| 复杂多表查询 | XML | SQL 长，注解拼接不可维护 |
| 动态 SQL（条件多） | XML | `<where>` `<if>` 标签比 `@SelectProvider` 直观 |
| 团队 DBA 协查 | XML | SQL 集中管理，方便 DBA 审查和优化 |
| 长期维护项目 | XML | 接口与 SQL 分离，职责更清晰 |

**结论**：实际项目推荐 XML 为主、注解为辅，避免两种风格混用在同一模块。

---

## 7. 动态 SQL

动态 SQL 是 MyBatis 最强大的能力之一，通过 XML 标签在运行时动态拼接 SQL，解决多条件查询的痛点。

### 7.1 `<if>` + `<where>`

```xml
<select id="selectByCondition" resultMap="BaseResultMap">
    SELECT * FROM `user`
    <where>
        <if test="username != null and username != ''">
            AND username LIKE CONCAT('%', #{username}, '%')
        </if>
        <if test="email != null and email != ''">
            AND email = #{email}
        </if>
        <if test="age != null">
            AND age = #{age}
        </if>
        <if test="status != null">
            AND status = #{status}
        </if>
    </where>
    ORDER BY id DESC
</select>
```

`<where>` 会自动处理：
- 第一个 `AND` / `OR` 自动移除
- 所有条件都不满足时不生成 `WHERE` 关键字

### 7.2 `<choose>` `<when>` `<otherwise>`

相当于 Java 的 `switch-case-default`：

```xml
<select id="selectByPriority" resultMap="BaseResultMap">
    SELECT * FROM `user`
    <where>
        <choose>
            <when test="id != null">
                AND id = #{id}
            </when>
            <when test="username != null and username != ''">
                AND username = #{username}
            </when>
            <otherwise>
                AND status = 1
            </otherwise>
        </choose>
    </where>
</select>
```

### 7.3 `<foreach>` 集合遍历

```xml
<!-- IN 查询 -->
<select id="selectByIds" resultMap="BaseResultMap">
    SELECT * FROM `user`
    WHERE id IN
    <foreach collection="ids" item="id" open="(" separator="," close=")">
        #{id}
    </foreach>
</select>
```

```xml
<!-- 批量插入 -->
<insert id="batchInsert">
    INSERT INTO `user` (username, email, age, status, create_time, update_time) VALUES
    <foreach collection="users" item="user" separator=",">
        (#{user.username}, #{user.email}, #{user.age}, #{user.status}, NOW(), NOW())
    </foreach>
</insert>
```

`<foreach>` 属性说明：

| 属性 | 说明 |
|------|------|
| `collection` | 集合参数名（List 默认用 `list`，数组用 `array`，`@Param` 则用指定名） |
| `item` | 迭代变量名 |
| `index` | 迭代索引（可选） |
| `open` | 开始符号 |
| `close` | 结束符号 |
| `separator` | 分隔符 |

### 7.4 `<set>` 动态更新

```xml
<update id="updateSelective">
    UPDATE `user`
    <set>
        <if test="email != null">email = #{email},</if>
        <if test="age != null">age = #{age},</if>
        <if test="status != null">status = #{status},</if>
        update_time = NOW()
    </set>
    WHERE id = #{id}
</update>
```

`<set>` 自动处理末尾多余逗号。

### 7.5 `<trim>` 自定义修剪

`<trim>` 是 `<where>` 和 `<set>` 的底层实现：

```xml
<!-- 等价于 <where> -->
<trim prefix="WHERE" prefixOverrides="AND |OR ">
    <if test="username != null">
        AND username = #{username}
    </if>
</trim>

<!-- 等价于 <set> -->
<trim prefix="SET" suffixOverrides=",">
    <if test="email != null">email = #{email},</if>
</trim>
```

| 属性 | 说明 |
|------|------|
| `prefix` | 前缀（拼在内容前） |
| `suffix` | 后缀（拼在内容后） |
| `prefixOverrides` | 忽略前缀字符（管道符分隔） |
| `suffixOverrides` | 忽略后缀字符（管道符分隔） |

### 7.6 `<bind>` 变量绑定

```xml
<select id="selectByKeyword" resultMap="BaseResultMap">
    <bind name="pattern" value="'%' + keyword + '%'"/>
    SELECT * FROM `user`
    WHERE username LIKE #{pattern}
       OR email LIKE #{pattern}
</select>
```

### 7.7 `<script>` 在注解中使用动态 SQL

```java
@Update({
    "<script>",
    "UPDATE `user`",
    "<set>",
    "  <if test='email != null'>email = #{email},</if>",
    "  <if test='age != null'>age = #{age},</if>",
    "  update_time = NOW()",
    "</set>",
    "WHERE id = #{id}",
    "</script>"
})
int updateSelective(User user);
```

---

## 8. 高级结果映射

### 8.1 `<resultMap>` 详解

```xml
<resultMap id="OrderResultMap" type="Order">
    <!-- 主键 -->
    <id column="order_id" property="orderId"/>

    <!-- 普通字段 -->
    <result column="order_no" property="orderNo"/>
    <result column="total_amount" property="totalAmount"/>
    <result column="create_time" property="createTime"/>

    <!-- 一对一关联 -->
    <association property="user" javaType="User"
                 columnPrefix="user_">
        <id column="id" property="id"/>
        <result column="name" property="username"/>
    </association>

    <!-- 一对多关联 -->
    <collection property="items" ofType="OrderItem"
                columnPrefix="item_">
        <id column="id" property="id"/>
        <result column="product_name" property="productName"/>
        <result column="quantity" property="quantity"/>
        <result column="price" property="price"/>
    </collection>
</resultMap>
```

### 8.2 一对一关联（association）

**SQL：**

```xml
<select id="selectOrderWithUser" resultMap="OrderWithUserMap">
    SELECT
        o.id           AS order_id,
        o.order_no,
        o.total_amount,
        o.create_time,
        u.id           AS user_id,
        u.username     AS user_name
    FROM `order` o
    LEFT JOIN `user` u ON o.user_id = u.id
    WHERE o.id = #{id}
</select>

<resultMap id="OrderWithUserMap" type="Order">
    <id column="order_id" property="id"/>
    <result column="order_no" property="orderNo"/>
    <result column="total_amount" property="totalAmount"/>
    <!-- association 映射关联的 User 对象 -->
    <association property="user" javaType="User">
        <id column="user_id" property="id"/>
        <result column="user_name" property="username"/>
    </association>
</resultMap>
```

**分步查询（懒加载）：**

```xml
<resultMap id="OrderWithUserLazy" type="Order">
    <id column="id" property="id"/>
    <result column="order_no" property="orderNo"/>
    <!-- select: 调用另一个查询   column: 传给该查询的参数列 -->
    <association property="user" javaType="User"
                 select="com.example.mybatis.mapper.UserMapper.selectById"
                 column="user_id" fetchType="lazy"/>
</resultMap>

<select id="selectOrderLazy" resultMap="OrderWithUserLazy">
    SELECT id, order_no, total_amount, user_id FROM `order` WHERE id = #{id}
</select>
```

`fetchType` 取值：`lazy`（延迟加载）、`eager`（立即加载）。当全局开启 `lazyLoadingEnabled=true` 时，`fetchType="eager"` 可以覆盖全局配置。

### 8.3 一对多关联（collection）

```xml
<select id="selectOrderWithItems" resultMap="OrderWithItemsMap">
    SELECT
        o.id            AS order_id,
        o.order_no,
        o.total_amount,
        oi.id           AS item_id,
        oi.product_name AS item_name,
        oi.quantity     AS item_qty,
        oi.price        AS item_price
    FROM `order` o
    LEFT JOIN `order_item` oi ON o.id = oi.order_id
    WHERE o.id = #{id}
</select>

<resultMap id="OrderWithItemsMap" type="Order">
    <id column="order_id" property="id"/>
    <result column="order_no" property="orderNo"/>
    <result column="total_amount" property="totalAmount"/>
    <!-- collection 映射关联的 List<OrderItem> -->
    <collection property="items" ofType="OrderItem">
        <id column="item_id" property="id"/>
        <result column="item_name" property="productName"/>
        <result column="item_qty" property="quantity"/>
        <result column="item_price" property="price"/>
    </collection>
</resultMap>
```

**分步查询（懒加载）：**

```xml
<resultMap id="OrderWithItemsLazy" type="Order">
    <id column="id" property="id"/>
    <result column="order_no" property="orderNo"/>
    <collection property="items" ofType="OrderItem"
                select="com.example.mybatis.mapper.OrderItemMapper.selectByOrderId"
                column="id" fetchType="lazy"/>
</resultMap>
```

### 8.4 构造器注入

```xml
<resultMap id="UserResultMap" type="User">
    <constructor>
        <idArg column="id" javaType="Long"/>
        <arg column="username" javaType="String"/>
    </constructor>
    <result column="email" property="email"/>
</resultMap>
```

对应实体类需要有全参或指定参数的构造器。通常在不可变实体（record / @Value）中使用。

### 8.5 鉴别器 discriminator

根据某个字段值选择不同的映射策略：

```xml
<resultMap id="VehicleResultMap" type="Vehicle">
    <id column="id" property="id"/>
    <result column="name" property="name"/>
    <discriminator javaType="string" column="type">
        <case value="CAR" resultMap="CarResultMap"/>
        <case value="TRUCK" resultMap="TruckResultMap"/>
    </discriminator>
</resultMap>
```

---

## 9. PageHelper 分页

PageHelper 是 MyBatis 生态中最常用的分页插件，通过拦截器自动改写 SQL 实现物理分页。

### 9.1 基础分页

```java
@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    /**
     * 分页查询
     */
    public PageInfo<User> pageByCondition(UserQueryDTO query, int pageNum, int pageSize) {
        // 1. 开启分页（仅对紧跟的下一条查询生效）
        PageHelper.startPage(pageNum, pageSize);

        // 2. 执行查询
        List<User> users = userMapper.selectByCondition(query);

        // 3. 包装为 PageInfo
        return new PageInfo<>(users);
    }
}
```

```java
@RestController
@RequestMapping("/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public Result<PageInfo<User>> list(
            @RequestParam(required = false) String username,
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "10") int pageSize) {

        UserQueryDTO query = new UserQueryDTO();
        query.setUsername(username);

        PageInfo<User> page = userService.pageByCondition(query, pageNum, pageSize);
        return Result.success(page);
    }
}
```

### 9.2 PageInfo 常用字段

```java
PageInfo<User> pageInfo = new PageInfo<>(users);

pageInfo.getTotal();       // 总记录数
pageInfo.getPages();       // 总页数
pageInfo.getPageNum();     // 当前页
pageInfo.getPageSize();    // 每页大小
pageInfo.getSize();        // 当前页实际条数
pageInfo.isHasNextPage(); // 是否有下一页
pageInfo.isHasPreviousPage(); // 是否有上一页
pageInfo.isIsFirstPage();  // 是否第一页
pageInfo.isIsLastPage();   // 是否最后一页
pageInfo.getList();        // 当前页数据
```

### 9.3 安全分页（只分页不 count）

```java
// 仅分页，不查总数（适用于滚动加载）
PageHelper.startPage(pageNum, pageSize, false); // 第三个参数 false 表示不 count
```

### 9.4 排序

```java
// 方式 1：startPage 时指定排序
PageHelper.startPage(pageNum, pageSize, "create_time DESC");

// 方式 2：链式调用
PageHelper.startPage(pageNum, pageSize)
          .orderBy("create_time DESC");

// 方式 3：OrderByHelper（复杂排序）
OrderByHelper.orderBy("create_time DESC, id ASC");
```

### 9.5 注意事项

```java
// ❌ 错误：先查询再 startPage
List<User> users = userMapper.selectAll();       // 不会分页
PageHelper.startPage(1, 10);                      // 对上面那条无效

// ❌ 错误：startPage 后间隔了其他非查询代码
PageHelper.startPage(1, 10);
String something = redisTemplate.opsForValue().get("xx");  // 中断
List<User> users = userMapper.selectAll();       // 可能不受分页影响

// ✅ 正确：startPage 紧邻查询语句
PageHelper.startPage(1, 10);
List<User> users = userMapper.selectAll();
PageInfo<User> pageInfo = new PageInfo<>(users);
```

> 分页后用 `PageInfo` 包装原始 List 之后，务必手动调用 `PageHelper.clearPage()` 清理 ThreadLocal，避免后续查询意外带上分页条件。

---

## 10. MyBatis-Plus 增强

MyBatis-Plus 是 MyBatis 的增强工具，提供通用 CRUD、条件构造器、代码生成器等能力。建议在 MyBatis 项目基础上平滑引入。

### 10.1 依赖引入

```xml
<!-- MyBatis-Plus（与 mybatis-spring-boot-starter 二选一，它已包含 MyBatis） -->
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
    <version>3.5.9</version>
</dependency>
```

> 注意：`mybatis-plus-boot-starter` 已包含 `mybatis-spring-boot-starter`，不要同时引入，否则会冲突。

### 10.2 基础 CRUD

```java
package com.example.mybatis.entity;

import com.baomidou.mybatisplus.annotation.*;
import java.time.LocalDateTime;

@Data
@TableName("user")  // 映射表名
public class User {
    @TableId(type = IdType.AUTO)  // 主键自增策略
    private Long id;

    private String username;
    private String email;
    private Integer age;
    private Integer status;

    @TableField(fill = FieldFill.INSERT)      // 插入时自动填充
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE) // 插入和更新时自动填充
    private LocalDateTime updateTime;

    @TableLogic  // 逻辑删除
    private Integer deleted;
}
```

```java
package com.example.mybatis.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.mybatis.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 继承 BaseMapper 即拥有通用 CRUD 方法，无需手写
    // insert(), deleteById(), updateById(), selectById(), selectList() ...
}
```

```java
@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    public void demo() {
        // 插入
        User user = new User();
        user.setUsername("zhangsan");
        userMapper.insert(user);

        // 按 ID 查询
        User u = userMapper.selectById(1L);

        // 按 ID 更新
        u.setEmail("new@example.com");
        userMapper.updateById(u);

        // 按条件查询（Lambda 写法，类型安全）
        List<User> users = userMapper.selectList(
            new LambdaQueryWrapper<User>()
                .eq(User::getStatus, 1)
                .like(User::getUsername, "zhang")
                .orderByDesc(User::getCreateTime)
        );
    }
}
```

### 10.3 条件构造器 LambdaQueryWrapper

```java
// Lambda 写法（类型安全，字段名由 IDE 自动补全）
List<User> users = userMapper.selectList(
    new LambdaQueryWrapper<User>()
        .eq(User::getStatus, 1)                       // status = 1
        .like(StringUtils::hasText, User::getUsername, "zhang") // 有条件地 like
        .between(User::getAge, 18, 35)                // age BETWEEN 18 AND 35
        .in(User::getId, Arrays.asList(1L, 2L, 3L))   // id IN (1,2,3)
        .orderByDesc(User::getCreateTime)             // ORDER BY create_time DESC
        .last("LIMIT 10")                             // 拼接到末尾
);

// 分页查询
Page<User> page = new Page<>(1, 10);  // 第 1 页，每页 10 条
Page<User> result = userMapper.selectPage(page,
    new LambdaQueryWrapper<User>()
        .eq(User::getStatus, 1)
);
```

### 10.4 自动填充

```java
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {

    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```

### 10.5 逻辑删除

```yaml
# application.yml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted      # 逻辑删除字段名
      logic-delete-value: 1            # 已删除值
      logic-not-delete-value: 0        # 未删除值
```

配置后，`deleteById()` 自动转换为 `UPDATE user SET deleted = 1 WHERE id = ?`，所有查询自动追加 `AND deleted = 0`。

### 10.6 MyBatis-Plus 代码生成器

```java
public class CodeGenerator {

    public static void main(String[] args) {
        FastAutoGenerator.create(
                "jdbc:mysql://localhost:3306/mybatis_demo", "root", "root")
            // 全局配置
            .globalConfig(builder -> builder
                .author("dev")
                .outputDir(System.getProperty("user.dir") + "/src/main/java")
                .commentDate("yyyy-MM-dd"))
            // 包配置
            .packageConfig(builder -> builder
                .parent("com.example.mybatis")
                .entity("entity")
                .mapper("mapper")
                .service("service")
                .serviceImpl("service.impl")
                .controller("controller"))
            // 策略配置
            .strategyConfig(builder -> builder
                .addInclude("user", "order", "order_item")  // 指定表名
                .entityBuilder()
                    .enableLombok()
                    .enableTableFieldAnnotation()
                    .logicDeleteColumnName("deleted")
                .controllerBuilder()
                    .enableRestStyle())
            .execute();
    }
}
```

---

## 11. 多数据源配置

### 11.1 动态数据源（dynamic-datasource）

使用 baomidou 动态数据源，支持注解切换：

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>dynamic-datasource-spring-boot3-starter</artifactId>
    <version>4.3.1</version>
</dependency>
```

```yaml
spring:
  datasource:
    dynamic:
      primary: master                         # 默认主数据源
      strict: false                           # 未匹配数据源时是否报错
      datasource:
        master:                               # 主库（写）
          url: jdbc:mysql://localhost:3306/mybatis_demo?...
          username: root
          password: root
          driver-class-name: com.mysql.cj.jdbc.Driver
        slave:                                # 从库（读）
          url: jdbc:mysql://localhost:3307/mybatis_demo?...
          username: root
          password: root
          driver-class-name: com.mysql.cj.jdbc.Driver
```

```java
@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    @DS("master")  // 走主库
    public void addUser(User user) {
        userMapper.insert(user);
    }

    @DS("slave")   // 走从库
    public List<User> listUsers() {
        return userMapper.selectList(null);
    }

    // 不加 @DS 默认走 primary（master）
    public User getById(Long id) {
        return userMapper.selectById(id);
    }
}
```

### 11.2 手动多数据源配置

```java
@Configuration
public class MultiDataSourceConfig {

    // -------- 主数据源 --------
    @Primary
    @Bean("masterDataSource")
    @ConfigurationProperties(prefix = "spring.datasource.master")
    public DataSource masterDataSource() {
        return DruidDataSourceBuilder.create().build();
    }

    @Primary
    @Bean("masterSqlSessionFactory")
    public SqlSessionFactory masterSqlSessionFactory(
            @Qualifier("masterDataSource") DataSource dataSource) throws Exception {
        return buildSqlSessionFactory(dataSource, "classpath:mapper/master/**/*.xml");
    }

    @Primary
    @Bean("masterSqlSessionTemplate")
    public SqlSessionTemplate masterSqlSessionTemplate(
            @Qualifier("masterSqlSessionFactory") SqlSessionFactory factory) {
        return new SqlSessionTemplate(factory);
    }

    // -------- 从数据源 --------
    @Bean("slaveDataSource")
    @ConfigurationProperties(prefix = "spring.datasource.slave")
    public DataSource slaveDataSource() {
        return DruidDataSourceBuilder.create().build();
    }

    @Bean("slaveSqlSessionFactory")
    public SqlSessionFactory slaveSqlSessionFactory(
            @Qualifier("slaveDataSource") DataSource dataSource) throws Exception {
        return buildSqlSessionFactory(dataSource, "classpath:mapper/slave/**/*.xml");
    }

    @Bean("slaveSqlSessionTemplate")
    public SqlSessionTemplate slaveSqlSessionTemplate(
            @Qualifier("slaveSqlSessionFactory") SqlSessionFactory factory) {
        return new SqlSessionTemplate(factory);
    }

    // -------- MapperScanner 分别扫描不同包 --------
    @Configuration
    @MapperScan(basePackages = "com.example.mybatis.mapper.master",
                sqlSessionTemplateRef = "masterSqlSessionTemplate")
    public static class MasterMapperConfig {}

    @Configuration
    @MapperScan(basePackages = "com.example.mybatis.mapper.slave",
                sqlSessionTemplateRef = "slaveSqlSessionTemplate")
    public static class SlaveMapperConfig {}
}
```

**结论**：中小项目用 `dynamic-datasource` 注解切换，简单够用；大型项目拆 Mapper 包 + 多 SqlSessionFactory 更清晰。

---

## 12. TypeHandler 自定义类型处理

当数据库字段类型与 Java 类型不能自动映射时（如 JSON 字段、枚举），用 TypeHandler 做转换。

### 12.1 枚举 TypeHandler

```java
// 数据库存 TINYINT，Java 用 Enum
public enum GenderEnum {
    MALE(0, "男"),
    FEMALE(1, "女");

    private final int code;
    private final String desc;
    // 构造器 + getter 省略
}
```

```java
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import java.sql.*;

public class GenderEnumTypeHandler extends BaseTypeHandler<GenderEnum> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i,
            GenderEnum parameter, JdbcType jdbcType) throws SQLException {
        ps.setInt(i, parameter.getCode()); // Java Enum → DB INT
    }

    @Override
    public GenderEnum getNullableResult(ResultSet rs, String columnName)
            throws SQLException {
        int code = rs.getInt(columnName);
        return GenderEnum.fromCode(code);  // DB INT → Java Enum
    }

    @Override
    public GenderEnum getNullableResult(ResultSet rs, int columnIndex)
            throws SQLException {
        int code = rs.getInt(columnIndex);
        return GenderEnum.fromCode(code);
    }

    @Override
    public GenderEnum getNullableResult(CallableStatement cs, int columnIndex)
            throws SQLException {
        int code = cs.getInt(columnIndex);
        return GenderEnum.fromCode(code);
    }
}
```

```yaml
# 注册全局 TypeHandler
mybatis:
  type-handlers-package: com.example.mybatis.handler
```

或者在 XML 中指定：

```xml
<resultMap id="BaseResultMap" type="User">
    <result column="gender" property="gender"
            typeHandler="com.example.mybatis.handler.GenderEnumTypeHandler"/>
</resultMap>
```

### 12.2 JSON 字段 TypeHandler

```java
// 实体类中将 JSON 字段存为 Java 对象
@Data
public class User {
    private Long id;
    private String username;

    @TableField(typeHandler = JacksonTypeHandler.class)  // MyBatis-Plus 内置
    private Map<String, Object> extraInfo;  // 对应数据库 JSON 类型
}
```

```java
// 使用
User user = new User();
Map<String, Object> extra = new HashMap<>();
extra.put("avatar", "https://...");
extra.put("vipLevel", 3);
user.setExtraInfo(extra);
userMapper.insert(user);

// 查询时自动反序列化
User u = userMapper.selectById(1L);
Integer vipLevel = (Integer) u.getExtraInfo().get("vipLevel");
```

---

## 13. 拦截器与插件

MyBatis 插件机制基于责任链模式，可拦截 Executor、StatementHandler、ParameterHandler、ResultSetHandler 四个核心对象。

### 13.1 自定义 SQL 日志拦截器

```java
import org.apache.ibatis.executor.statement.StatementHandler;
import org.apache.ibatis.plugin.*;
import org.apache.ibatis.session.ResultHandler;

import java.sql.Statement;
import java.util.Properties;

@Intercepts({
    @Signature(type = StatementHandler.class,
               method = "query",
               args = {Statement.class, ResultHandler.class})
})
public class SlowSqlInterceptor implements Interceptor {

    private long threshold = 2000;  // 默认 2 秒

    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = invocation.proceed();  // 执行原方法
        long elapsed = System.currentTimeMillis() - start;

        if (elapsed > threshold) {
            StatementHandler handler = (StatementHandler) invocation.getTarget();
            String sql = handler.getBoundSql().getSql();
            System.err.printf("[SLOW SQL] %dms: %s%n", elapsed, sql);
        }
        return result;
    }

    @Override
    public void setProperties(Properties properties) {
        if (properties.containsKey("threshold")) {
            this.threshold = Long.parseLong(properties.getProperty("threshold"));
        }
    }
}
```

```java
@Configuration
public class MybatisConfig {

    @Bean
    public SlowSqlInterceptor slowSqlInterceptor() {
        return new SlowSqlInterceptor();
    }

    // 注入到 SqlSessionFactory
    @Bean
    public ConfigurationCustomizer mybatisCustomizer(SlowSqlInterceptor interceptor) {
        return configuration -> configuration.addInterceptor(interceptor);
    }
}
```

### 13.2 MyBatis 可拦截的四个接口

| 接口 | 可拦截方法 | 典型场景 |
|------|-----------|---------|
| `Executor` | update, query, flushStatements, commit, rollback | 分页（PageHelper）、缓存、事务控制 |
| `StatementHandler` | prepare, parameterize, batch, update, query | SQL 改写、慢查询监控 |
| `ParameterHandler` | getParameterObject, setParameters | 参数加密/脱敏 |
| `ResultSetHandler` | handleResultSets, handleOutputParameters | 结果集加密/脱敏 |

拦截器通过 `@Signature` 指定要拦截的接口、方法、参数类型。多个拦截器按注册顺序链式执行。

---

## 14. 应用场景实战

### 场景 1：用户列表模糊搜索 + 分页

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public Result<PageInfo<UserVO>> list(
            @RequestParam(required = false) String keyword,   // 模糊搜索
            @RequestParam(required = false) Integer status,   // 状态筛选
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "10") int pageSize) {

        PageInfo<UserVO> page = userService.searchUsers(keyword, status, pageNum, pageSize);
        return Result.success(page);
    }
}
```

```java
@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    public PageInfo<UserVO> searchUsers(String keyword, Integer status,
                                         int pageNum, int pageSize) {
        PageHelper.startPage(pageNum, pageSize);
        List<UserVO> users = userMapper.searchByKeyword(keyword, status);
        return new PageInfo<>(users);
    }
}
```

```xml
<select id="searchByKeyword" resultType="com.example.mybatis.vo.UserVO">
    SELECT id, username, email, age, status, create_time
    FROM `user`
    <where>
        <if test="keyword != null and keyword != ''">
            AND (username LIKE CONCAT('%', #{keyword}, '%')
                 OR email LIKE CONCAT('%', #{keyword}, '%'))
        </if>
        <if test="status != null">
            AND status = #{status}
        </if>
    </where>
    ORDER BY create_time DESC
</select>
```

### 场景 2：订单 + 订单明细联表查询

```java
@Data
public class OrderDTO {
    private Long orderId;
    private String orderNo;
    private String username;      // 下单用户
    private BigDecimal totalAmount;
    private Integer status;
    private LocalDateTime createTime;
    private List<OrderItemDTO> items;  // 订单明细
}
```

```xml
<select id="selectOrderDetail" resultMap="OrderDetailMap">
    SELECT
        o.id            AS order_id,
        o.order_no,
        o.total_amount,
        o.status        AS order_status,
        o.create_time   AS order_time,
        u.username,
        oi.id           AS item_id,
        oi.product_name AS item_name,
        oi.quantity     AS item_qty,
        oi.price        AS item_price
    FROM `order` o
    LEFT JOIN `user` u ON o.user_id = u.id
    LEFT JOIN `order_item` oi ON o.id = oi.order_id
    WHERE o.id = #{orderId}
</select>

<resultMap id="OrderDetailMap" type="com.example.mybatis.dto.OrderDTO">
    <id column="order_id" property="orderId"/>
    <result column="order_no" property="orderNo"/>
    <result column="total_amount" property="totalAmount"/>
    <result column="order_status" property="status"/>
    <result column="order_time" property="createTime"/>
    <result column="username" property="username"/>
    <collection property="items" ofType="com.example.mybatis.dto.OrderItemDTO">
        <id column="item_id" property="id"/>
        <result column="item_name" property="productName"/>
        <result column="item_qty" property="quantity"/>
        <result column="item_price" property="price"/>
    </collection>
</resultMap>
```

### 场景 3：批量导入 Excel 数据

```java
@Service
public class UserBatchService {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private SqlSessionFactory sqlSessionFactory;

    /**
     * 批量插入（BATCH 模式，10 万条约 3 秒）
     */
    @Transactional
    public int batchImport(List<User> users) {
        // 使用 BATCH ExecutorType，JDBC 批量提交
        try (SqlSession session = sqlSessionFactory.openSession(ExecutorType.BATCH)) {
            UserMapper mapper = session.getMapper(UserMapper.class);

            for (int i = 0; i < users.size(); i++) {
                mapper.insert(users.get(i));
                if (i % 1000 == 0) {   // 每 1000 条提交一次
                    session.commit();
                    session.clearCache();
                }
            }
            session.commit();  // 提交剩余
        }
        return users.size();
    }
}
```

```java
// 或使用 MyBatis-Plus 的 saveBatch
@Service
public class UserBatchService {

    @Autowired
    private UserMapper userMapper;  // extends BaseMapper<User>

    @Transactional
    public int batchImport(List<User> users) {
        userMapper.insert(users, 500);  // 每 500 条为一批
        return users.size();
    }
}
```

### 场景 4：多条件动态查询（组合筛选）

```java
@Data
public class ProductQueryDTO {
    private String keyword;          // 商品名/描述模糊搜索
    private Long categoryId;         // 分类
    private BigDecimal minPrice;     // 最低价
    private BigDecimal maxPrice;     // 最高价
    private List<Integer> statusList; // 状态多选
    private String orderBy;          // 排序字段
    private String orderDir;         // 排序方向 ASC/DESC
}
```

```xml
<select id="searchProducts" resultType="com.example.mybatis.vo.ProductVO">
    SELECT p.id, p.name, p.price, p.sales_volume, c.name AS category_name
    FROM product p
    LEFT JOIN category c ON p.category_id = c.id
    <where>
        <if test="keyword != null and keyword != ''">
            AND (p.name LIKE CONCAT('%', #{keyword}, '%')
                 OR p.description LIKE CONCAT('%', #{keyword}, '%'))
        </if>
        <if test="categoryId != null">
            AND p.category_id = #{categoryId}
        </if>
        <if test="minPrice != null">
            AND p.price >= #{minPrice}
        </if>
        <if test="maxPrice != null">
            AND p.price &lt;= #{maxPrice}
        </if>
        <if test="statusList != null and statusList.size() > 0">
            AND p.status IN
            <foreach collection="statusList" item="status" open="(" separator="," close=")">
                #{status}
            </foreach>
        </if>
    </where>
    <!-- 动态排序（注意 SQL 注入风险，orderBy 需要做白名单校验） -->
    <choose>
        <when test="orderBy == 'price' and orderDir == 'asc'">
            ORDER BY p.price ASC
        </when>
        <when test="orderBy == 'price' and orderDir == 'desc'">
            ORDER BY p.price DESC
        </when>
        <when test="orderBy == 'sales'">
            ORDER BY p.sales_volume DESC
        </when>
        <otherwise>
            ORDER BY p.id DESC
        </otherwise>
    </choose>
</select>
```

### 场景 5：乐观锁更新

```java
@Data
public class Product {
    private Long id;
    private String name;
    private Integer stock;
    private Integer version;  // 版本号
}
```

```xml
<update id="deductStock">
    UPDATE product
    SET stock = stock - #{quantity},
        version = version + 1
    WHERE id = #{id}
      AND stock >= #{quantity}      -- 库存充足
      AND version = #{version}      -- 乐观锁
</update>
```

```java
@Service
public class ProductService {

    @Autowired
    private ProductMapper productMapper;

    /**
     * 扣减库存（乐观锁）
     */
    public boolean deductStock(Long productId, int quantity) {
        Product product = productMapper.selectById(productId);
        if (product.getStock() < quantity) {
            throw new BusinessException("库存不足");
        }

        int rows = productMapper.deductStock(productId, quantity, product.getVersion());
        if (rows == 0) {
            // version 不匹配，被其他事务修改，重试或报错
            throw new BusinessException("操作冲突，请重试");
        }
        return true;
    }
}
```

---

## 15. 最佳实践与踩坑记录

### 15.1 `#{}` vs `${}`

```xml
<!-- ✅ #{} 预编译占位符，防 SQL 注入 -->
<select id="selectById" resultMap="BaseResultMap">
    SELECT * FROM `user` WHERE id = #{id}
</select>

<!-- ❌ ${} 直接拼字符串，有 SQL 注入风险 -->
<select id="selectById" resultMap="BaseResultMap">
    SELECT * FROM `user` WHERE id = ${id}
</select>
```

```xml
<!-- ✅ ${} 唯一合理用法：动态表名/列名（必须白名单校验） -->
<select id="selectByTable" resultType="map">
    SELECT * FROM ${tableName} WHERE id = #{id}
    <!-- tableName 由代码白名单控制，不接受前端传值 -->
</select>
```

| 占位符 | 原理 | 防注入 | 适用 |
|--------|------|--------|------|
| `#{}` | JDBC PreparedStatement `?` 占位 | 是 | 参数值 |
| `${}` | 字符串拼接 | 否 | 表名/列名/ORDER BY（白名单校验） |

### 15.2 返回自增主键

```xml
<!-- ✅ 方式 1：useGeneratedKeys -->
<insert id="insert" useGeneratedKeys="true" keyProperty="id">
    INSERT INTO `user` (username, email) VALUES (#{username}, #{email})
</insert>

<!-- ✅ 方式 2：selectKey（适用于不支持自增的数据库） -->
<insert id="insert">
    <selectKey keyProperty="id" resultType="long" order="AFTER">
        SELECT LAST_INSERT_ID()
    </selectKey>
    INSERT INTO `user` (username, email) VALUES (#{username}, #{email})
</insert>
```

```java
// 调用后 id 自动回填
User user = new User();
user.setUsername("zhangsan");
userMapper.insert(user);
System.out.println(user.getId());  // 自增主键值已回填
```

### 15.3 大字段查询优化

```xml
<!-- 列表查询不查大字段 -->
<sql id="ListColumns">
    id, username, email, age, status, create_time
</sql>

<select id="selectList" resultType="User">
    SELECT <include refid="ListColumns"/> FROM `user`
</select>

<!-- 详情查询才包含大字段 -->
<select id="selectDetail" resultType="User">
    SELECT id, username, email, age, status, create_time,
           CONTENT_TEXT  -- 大字段，仅在详情接口查询
    FROM `user` WHERE id = #{id}
</select>
```

### 15.4 一级缓存陷阱

```java
@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    @Transactional
    public void cachePitfall() {
        // 同一个 SqlSession（同一事务）内一级缓存生效
        User u1 = userMapper.selectById(1L);  // 查库
        User u2 = userMapper.selectById(1L);  // 命中一级缓存，不查库

        // 注意：一级缓存中的对象是引用！修改会影响缓存
        // ❌ 问题：在事务内修改了缓存对象，后续读到脏数据
    }
}
```

**解决**：事务完成后一级缓存自动清除。跨事务场景用二级缓存或手动清缓存。

### 15.5 N+1 查询问题

```java
// ❌ N+1 查询：先查订单列表，再逐个查订单明细
List<Order> orders = orderMapper.selectAll();           // 1 次查询
for (Order order : orders) {
    List<OrderItem> items = itemMapper.selectByOrderId(order.getId()); // N 次查询
}

// ✅ 方案 1：JOIN 联表一次查出（推荐）
OrderDetailDTO dto = orderMapper.selectOrderWithItems(orderId);  // 1 次

// ✅ 方案 2：批量查询
List<Long> orderIds = orders.stream().map(Order::getId).toList();
List<OrderItem> allItems = itemMapper.selectByOrderIds(orderIds);  // 1 次
Map<Long, List<OrderItem>> itemMap = allItems.stream()
    .collect(Collectors.groupingBy(OrderItem::getOrderId));
```

### 15.6 常见问题速查表

| 问题 | 原因 | 解决 |
|------|------|------|
| Mapper 方法找不到 | namespace 与接口全限定类名不一致 | 检查 XML 的 `namespace` |
| 实体字段值为 null | `mapUnderscoreToCamelCase` 未开启 | `mybatis.configuration.map-underscore-to-camel-case: true` |
| `BindingException` | XML 文件路径不在 `mapper-locations` 范围 | 检查路径或通配符 |
| 分页失效 | PageHelper.startPage 和查询之间被其他代码中断 | PageHelper 紧邻查询语句 |
| 批量插入慢 | 默认 SIMPLE ExecutorType，逐条提交 | 使用 BATCH 模式或 MyBatis-Plus `saveBatch` |
| `TooManyResultsException` | 期望单条但查出多条 | 确保查询条件能唯一确定一条记录 |
| `DataIntegrityViolation` | 唯一键冲突 | 用 `INSERT IGNORE` 或先查后插 |
| 事务不回滚 | 异常被 catch 吞掉了 | `@Transactional(rollbackFor = Exception.class)` 且在 Service 层抛出异常 |
| 结果集映射混乱 | 多个表有相同列名（如 `id`） | 用列别名 `AS` + `columnPrefix` |
| 枚举值存储异常 | 未配置 TypeHandler | 注册全局或字段级 TypeHandler |
| Druid 监控页 404 | 未配置 stat-view-servlet | 添加 `spring.datasource.druid.stat-view-servlet.enabled: true` |
| 连接池耗尽 | `max-active` 太小或连接未释放 | 调大 maxActive，检查是否有连接泄露 |

### 15.7 生产环境建议

```yaml
# 生产环境配置
mybatis:
  configuration:
    map-underscore-to-camel-case: true
    cache-enabled: true                     # 开启二级缓存
    lazy-loading-enabled: true              # 延迟加载
    aggressive-lazy-loading: false          # 按需延迟
    default-statement-timeout: 30           # SQL 超时 30 秒
    log-impl: org.apache.ibatis.logging.slf4j.Slf4jImpl  # 用 Slf4j（不用 StdOut）

spring:
  datasource:
    druid:
      max-active: 50                        # 按实际 QPS 调整
      min-idle: 10
      initial-size: 10
      test-while-idle: true                 # 空闲连接校验
      test-on-borrow: false                 # 获取连接时不校验（性能）
      validation-query: SELECT 1
      # 慢 SQL 监控
      filter:
        stat:
          slow-sql-millis: 1000             # 超过 1 秒记录
          log-slow-sql: true
```

```java
// ✅ 事务回滚策略
@Transactional(rollbackFor = Exception.class)  // 任何异常都回滚
public void doBusiness() { ... }

// ✅ 只读事务优化
@Transactional(readOnly = true)
public List<User> listUsers() { ... }

// ✅ 事务隔离级别
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void transfer() { ... }
```

---

## 总结

1. **XML 为主、注解为辅**：复杂 SQL 和动态条件放 XML，简单单表 CRUD 可用注解；团队协作统一风格
2. **`#{}` 防注入，`${}` 做白名单**：参数值用预编译占位符，表名/列名才用字符串拼接且必须校验
3. **PageHelper 紧邻查询**：`startPage` 后紧跟 Mapper 调用，中间不要插入任何代码，用毕调用 `clearPage()`
4. **联表优先 JOIN**：避免 N+1 查询，大列表分页场景用多步批量查询代替 JOIN
5. **MyBatis-Plus 不搞特殊化**：MP 是增强不是替代，条件构造器 + 通用 CRUD 减少样板代码，复杂逻辑仍写 XML
6. **连接池 + 慢 SQL 监控**：Druid 监控页是开发运维利器，上线务必配置 slow-sql-millis

---

*参考链接：*
- MyBatis 官方文档：https://mybatis.org/mybatis-3/
- MyBatis Spring Boot：https://mybatis.org/spring-boot-starter/
- MyBatis-Plus：https://baomidou.com/
- PageHelper：https://pagehelper.github.io/
- Druid：https://github.com/alibaba/druid
