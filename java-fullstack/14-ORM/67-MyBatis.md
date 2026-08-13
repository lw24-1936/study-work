---
title: MyBatis
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [mybatis, mapper, xml, dynamic-sql, resultmap, typehandler, interceptor, cache, sqlsession, orm]
---

# MyBatis

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [MyBatis 架构](#mybatis-架构)
- [SqlSession —— 核心会话](#sqlsession--核心会话)
- [Mapper —— 映射器](#mapper--映射器)
- [XML 映射文件](#xml-映射文件)
- [动态 SQL](#动态-sql)
- [ResultMap —— 结果映射](#resultmap--结果映射)
- [TypeHandler —— 类型处理器](#typehandler--类型处理器)
- [Interceptor —— 拦截器](#interceptor--拦截器)
- [缓存机制](#缓存机制)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

MyBatis 是 Java 领域最流行的半自动化 ORM 框架。与 Hibernate 的全自动不同，MyBatis 让开发者自己写 SQL，框架只负责 SQL 与对象的映射。这给了开发者对 SQL 的完全控制权——复杂查询、性能优化、数据库特有功能，都能直接使用。

Hibernate 追求"不需要写 SQL"，MyBatis 追求"想怎么写 SQL 就怎么写 SQL"。在国内互联网项目中，MyBatis 的使用率远高于 JPA/Hibernate。

## MyBatis 架构

```
┌──────────────────────────────────────────────┐
│            MyBatis 配置                        │
│  mybatis-config.xml / application.yml         │
├──────────────────────────────────────────────┤
│            SqlSessionFactory                   │
│  根据配置创建，全局唯一，线程安全                │
├──────────────────────────────────────────────┤
│              SqlSession                        │
│  一次数据库会话，非线程安全，用完即关            │
├──────────────┬───────────────────────────────┤
│   Mapper 接口  │     XML 映射文件               │
│  UserMapper   │   UserMapper.xml               │
│  (JDK 动态代理) │   (SQL + ResultMap)           │
├──────────────┴───────────────────────────────┤
│                Executor                        │
│  SimpleExecutor / ReuseExecutor / BatchExecutor │
├──────────────────────────────────────────────┤
│            JDBC (Connection / Statement)        │
└──────────────────────────────────────────────┘
```

### 一条查询的完整路径

```
UserMapper.selectById(1L)
  → MapperProxy.invoke()           // JDK 动态代理
    → SqlSession.selectOne()
      → Executor.query()
        → 从 MappedStatement 获取 SQL
        → 创建 Connection / PreparedStatement
        → 设置参数（TypeHandler）
        → 执行 JDBC 查询
        → 用 ResultSetHandler 映射结果（ResultMap/TypeHandler）
        → 返回对象
```

## SqlSession —— 核心会话

SqlSession 是 MyBatis 的核心接口，所有数据库操作都通过它完成。

### 获取 SqlSession

```java
// 方式一：从 SqlSessionFactory 创建
InputStream is = Resources.getResourceAsStream("mybatis-config.xml");
SqlSessionFactory sf = new SqlSessionFactoryBuilder().build(is);
try (SqlSession session = sf.openSession()) {
    User user = session.selectOne("com.example.UserMapper.selectById", 1L);
}

// 方式二：配合 Spring（最常用——SqlSessionTemplate 自动管理）
@Autowired
private SqlSessionTemplate sqlSession;
```

### 核心方法

```java
// 查询
<T> T selectOne(String statement);                   // 查询单条
<T> T selectOne(String statement, Object param);
<E> List<E> selectList(String statement);            // 查询多条
<E> List<E> selectList(String statement, Object param);
<E> List<E> selectList(String statement, Object param, RowBounds rowBounds);  // 分页

// 插入
int insert(String statement);
int insert(String statement, Object param);

// 更新
int update(String statement);
int update(String statement, Object param);

// 删除
int delete(String statement);
int delete(String statement, Object param);

// 事务
void commit();
void rollback();
void close();

// 获取 Mapper
<T> T getMapper(Class<T> type);  // 返回动态代理实现的 Mapper 接口
```

### Executor 类型

```xml
<settings>
    <setting name="defaultExecutorType" value="SIMPLE"/>
</settings>
```

| Executor | 说明 |
|----------|------|
| SIMPLE（默认） | 每次执行创建一个新的 PreparedStatement |
| REUSE | 复用 PreparedStatement（同 SQL 模板） |
| BATCH | 批量执行，专用于批量写入 |

## Mapper —— 映射器

Mapper 接口通过 JDK 动态代理生成实现类，让开发者用接口方法操作数据库。

### 接口定义

```java
@Mapper
public interface UserMapper {

    @Select("SELECT * FROM t_user WHERE id = #{id}")
    User selectById(@Param("id") Long id);

    @Insert("INSERT INTO t_user(username, email) VALUES(#{username}, #{email})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(User user);

    @Update("UPDATE t_user SET username = #{username} WHERE id = #{id}")
    int update(User user);

    @Delete("DELETE FROM t_user WHERE id = #{id}")
    int deleteById(@Param("id") Long id);
}
```

### 两种 SQL 编写方式

**注解方式**（简单 SQL 用）：

```java
@Select("SELECT * FROM t_user WHERE age > #{minAge} AND status = #{status}")
List<User> selectByAgeAndStatus(@Param("minAge") int minAge, @Param("status") int status);
```

**XML 方式**（复杂 SQL 用，推荐）：

```java
@Mapper
public interface UserMapper {
    User selectById(Long id);
    List<User> selectByCondition(UserQuery query);
}

// UserMapper.xml 中编写 SQL
```

### @Param 注解

```java
// 单参数：不用 @Param
User selectById(Long id);           // #{id}

// 多参数：必须用 @Param
User selectByNameAndAge(@Param("name") String name, @Param("age") int age);
// 取参数：#{name}, #{age}

// 对象参数：不用 @Param，直接用属性名
List<User> selectByCondition(UserQuery query);
// 取参数：#{username}, #{minAge}
```

## XML 映射文件

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
    "http://mybatis.org/dtd/mybatis-3-mapper.dtd">

<mapper namespace="com.example.mapper.UserMapper">

    <!-- 基础查询 -->
    <select id="selectById" resultType="com.example.entity.User">
        SELECT id, username, email, age, dept_id AS deptId
        FROM t_user
        WHERE id = #{id}
    </select>

    <!-- 带条件的查询 -->
    <select id="selectByCondition" resultType="com.example.entity.User">
        SELECT * FROM t_user
        <where>
            <if test="username != null and username != ''">
                AND username LIKE CONCAT('%', #{username}, '%')
            </if>
            <if test="minAge != null">
                AND age >= #{minAge}
            </if>
            <if test="status != null">
                AND status = #{status}
            </if>
        </where>
        ORDER BY created_at DESC
    </select>

    <!-- 插入 -->
    <insert id="insert" useGeneratedKeys="true" keyProperty="id">
        INSERT INTO t_user (username, email, age, created_at)
        VALUES (#{username}, #{email}, #{age}, #{createdAt})
    </insert>

    <!-- 批量插入 -->
    <insert id="batchInsert">
        INSERT INTO t_user (username, email) VALUES
        <foreach collection="list" item="user" separator=",">
            (#{user.username}, #{user.email})
        </foreach>
    </insert>

    <!-- 更新 -->
    <update id="update">
        UPDATE t_user
        <set>
            <if test="username != null">username = #{username},</if>
            <if test="email != null">email = #{email},</if>
            <if test="age != null">age = #{age},</if>
        </set>
        WHERE id = #{id}
    </update>

    <!-- 删除 -->
    <delete id="deleteById">
        DELETE FROM t_user WHERE id = #{id}
    </delete>

    <!-- 批量删除 -->
    <delete id="deleteByIds">
        DELETE FROM t_user WHERE id IN
        <foreach collection="ids" item="id" open="(" close=")" separator=",">
            #{id}
        </foreach>
    </delete>
</mapper>
```

### #{} vs ${}

```xml
<!-- #{}：参数占位符（PreparedStatement ?），安全，自动转义 -->
SELECT * FROM t_user WHERE username = #{username}
→ SELECT * FROM t_user WHERE username = ?

<!-- ${}：字符串替换（直接拼接），危险，不能防 SQL 注入 -->
SELECT * FROM t_user ORDER BY ${orderColumn} ${direction}
→ SELECT * FROM t_user ORDER BY username DESC
```

规则：**能用 #{} 就用 #{}**。`${}` 只能用于动态表名、列名、ORDER BY、LIKE 模糊查询（但 LIKE 可以用 CONCAT 替代 `${}`）。

## 动态 SQL

MyBatis 的动态 SQL 是最强大的特性之一——用 XML 标签构建灵活的 WHERE 条件。

### 核心标签

**if**：条件判断

```xml
<select id="selectByCondition" resultType="User">
    SELECT * FROM t_user WHERE 1=1
    <if test="username != null">
        AND username = #{username}
    </if>
    <if test="minAge != null">
        AND age >= #{minAge}
    </if>
</select>
```

**where**：自动处理 AND/OR 前缀，所有条件都不满足时不生成 WHERE

```xml
<select id="selectByCondition" resultType="User">
    SELECT * FROM t_user
    <where>
        <if test="username != null">AND username = #{username}</if>
        <if test="minAge != null">AND age >= #{minAge}</if>
    </where>
</select>
```

**set**：自动处理尾部逗号

```xml
<update id="update">
    UPDATE t_user
    <set>
        <if test="username != null">username = #{username},</if>
        <if test="email != null">email = #{email},</if>
    </set>
    WHERE id = #{id}
</update>
```

**foreach**：遍历集合

```xml
<!-- IN 查询 -->
<select id="selectByIds" resultType="User">
    SELECT * FROM t_user WHERE id IN
    <foreach collection="ids" item="id" open="(" close=")" separator=",">
        #{id}
    </foreach>
</select>

<!-- 批量插入 -->
<insert id="batchInsert">
    INSERT INTO t_user (username, email) VALUES
    <foreach collection="list" item="user" separator=",">
        (#{user.username}, #{user.email})
    </foreach>
</insert>
```

**choose / when / otherwise**：相当于 switch

```xml
<select id="selectByPriority" resultType="User">
    SELECT * FROM t_user
    <where>
        <choose>
            <when test="username != null">AND username = #{username}</when>
            <when test="email != null">AND email = #{email}</when>
            <otherwise>AND status = 1</otherwise>
        </choose>
    </where>
</select>
```

**trim**：自定义前缀/后缀处理

```xml
<!-- 等效于 <where> -->
<trim prefix="WHERE" prefixOverrides="AND |OR ">
    <if test="username != null">AND username = #{username}</if>
    <if test="age != null">AND age = #{age}</if>
</trim>

<!-- 等效于 <set> -->
<trim prefix="SET" suffixOverrides=",">
    <if test="username != null">username = #{username},</if>
    <if test="age != null">age = #{age},</if>
</trim>
```

**sql / include**：SQL 片段复用

```xml
<sql id="baseColumns">
    id, username, email, age, status, created_at
</sql>

<sql id="whereCondition">
    <where>
        <if test="username != null">AND username = #{username}</if>
        <if test="status != null">AND status = #{status}</if>
    </where>
</sql>

<select id="selectById" resultType="User">
    SELECT <include refid="baseColumns"/> FROM t_user WHERE id = #{id}
</select>

<select id="selectByCondition" resultType="User">
    SELECT <include refid="baseColumns"/> FROM t_user
    <include refid="whereCondition"/>
</select>
```

## ResultMap —— 结果映射

ResultMap 是 MyBatis 最强大的映射机制——处理列名与属性名不一致、关联对象、集合映射。

### 基本映射

```xml
<!-- resultType：列名与属性名一致时使用 -->
<select id="selectAll" resultType="com.example.entity.User">
    SELECT id, username, email FROM t_user
</select>

<!-- resultMap：列名与属性名不一致，或需要复杂映射 -->
<resultMap id="userMap" type="com.example.entity.User">
    <id property="id" column="id"/>
    <result property="username" column="username"/>
    <result property="email" column="email"/>
    <result property="deptId" column="dept_id"/>   <!-- 下划线 → 驼峰 -->
</resultMap>

<select id="selectById" resultMap="userMap">
    SELECT * FROM t_user WHERE id = #{id}
</select>
```

开启驼峰自动映射后无需每个字段都写：

```yaml
mybatis:
  configuration:
    map-underscore-to-camel-case: true  # dept_id → deptId
```

### 关联映射 —— association（一对一）

```xml
<resultMap id="userWithDeptMap" type="com.example.entity.User">
    <id property="id" column="id"/>
    <result property="username" column="username"/>
    <!-- 一对一关联 -->
    <association property="dept" javaType="com.example.entity.Dept">
        <id property="id" column="dept_id"/>
        <result property="name" column="dept_name"/>
    </association>
</resultMap>

<select id="selectUserWithDept" resultMap="userWithDeptMap">
    SELECT u.id, u.username,
           d.id AS dept_id, d.name AS dept_name
    FROM t_user u
    LEFT JOIN t_dept d ON u.dept_id = d.id
    WHERE u.id = #{id}
</select>
```

### 关联映射 —— 分步查询（延迟加载）

```xml
<resultMap id="userLazyMap" type="User">
    <id property="id" column="id"/>
    <result property="username" column="username"/>
    <!-- 分步查询：先查 User，需要时再查 Dept -->
    <association property="dept"
                 column="dept_id"
                 select="com.example.mapper.DeptMapper.selectById"
                 fetchType="lazy"/>
</resultMap>

<select id="selectById" resultMap="userLazyMap">
    SELECT * FROM t_user WHERE id = #{id}
</select>
```

延迟加载需要开启配置：

```yaml
mybatis:
  configuration:
    lazy-loading-enabled: true
    aggressive-lazy-loading: false  # 按需加载而非全部加载
```

### 集合映射 —— collection（一对多）

```xml
<resultMap id="deptWithUsersMap" type="Dept">
    <id property="id" column="id"/>
    <result property="name" column="name"/>
    <!-- 一对多集合 -->
    <collection property="users" ofType="User">
        <id property="id" column="user_id"/>
        <result property="username" column="username"/>
    </collection>
</resultMap>

<select id="selectDeptWithUsers" resultMap="deptWithUsersMap">
    SELECT d.id, d.name, u.id AS user_id, u.username
    FROM t_dept d
    LEFT JOIN t_user u ON u.dept_id = d.id
    WHERE d.id = #{id}
</select>
```

### 鉴别器 discriminator

根据某列的值映射不同子类：

```xml
<resultMap id="vehicleMap" type="Vehicle">
    <id property="id" column="id"/>
    <result property="type" column="type"/>
    <discriminator javaType="string" column="type">
        <case value="CAR" resultType="Car">
            <result property="seatCount" column="seat_count"/>
        </case>
        <case value="TRUCK" resultType="Truck">
            <result property="loadCapacity" column="load_capacity"/>
        </case>
    </discriminator>
</resultMap>
```

## TypeHandler —— 类型处理器

TypeHandler 负责 Java 类型与 JDBC 类型之间的转换。MyBatis 内置了大多数常见类型的处理器，但自定义类型需要自己实现。

### 自定义 TypeHandler

```java
// 场景：将 Java 的 List<String> 存为逗号分隔的字符串
@MappedTypes(List.class)
@MappedJdbcTypes(JdbcType.VARCHAR)
public class StringListTypeHandler extends BaseTypeHandler<List<String>> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i,
            List<String> parameter, JdbcType jdbcType) throws SQLException {
        ps.setString(i, String.join(",", parameter));
    }

    @Override
    public List<String> getNullableResult(ResultSet rs, String columnName)
            throws SQLException {
        String value = rs.getString(columnName);
        return value == null ? List.of() : Arrays.asList(value.split(","));
    }

    @Override
    public List<String> getNullableResult(ResultSet rs, int columnIndex)
            throws SQLException {
        String value = rs.getString(columnIndex);
        return value == null ? List.of() : Arrays.asList(value.split(","));
    }

    @Override
    public List<String> getNullableResult(CallableStatement cs, int columnIndex)
            throws SQLException {
        String value = cs.getString(columnIndex);
        return value == null ? List.of() : Arrays.asList(value.split(","));
    }
}
```

### 注册与使用

```yaml
mybatis:
  type-handlers-package: com.example.handler
```

```xml
<!-- 在 XML 中引用 -->
<resultMap id="userMap" type="User">
    <result property="roles" column="roles"
            typeHandler="com.example.handler.StringListTypeHandler"/>
</resultMap>
```

```java
// 或注解方式
@TableField(typeHandler = StringListTypeHandler.class)
private List<String> roles;
```

## Interceptor —— 拦截器

MyBatis 允许拦截以下四种接口的方法调用：

```java
Executor       (update, query, flushStatements, commit, rollback, ...)
StatementHandler (prepare, parameterize, batch, update, query)
ParameterHandler (getParameterObject, setParameters)
ResultSetHandler (handleResultSets, handleOutputParameters)
```

### 自定义分页拦截器

```java
@Intercepts(@Signature(
    type = StatementHandler.class,
    method = "prepare",
    args = {Connection.class, Integer.class}
))
public class PaginationInterceptor implements Interceptor {

    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        StatementHandler handler = (StatementHandler) invocation.getTarget();
        MetaObject metaObject = SystemMetaObject.forObject(handler);
        BoundSql boundSql = handler.getBoundSql();
        String sql = boundSql.getSql();

        // 从参数中提取分页信息
        Object paramObj = boundSql.getParameterObject();
        // ... 获取 pageNum, pageSize ...

        // 拼接 COUNT SQL
        // 拼接 LIMIT SQL
        metaObject.setValue("delegate.boundSql.sql", paginatedSql);

        return invocation.proceed();
    }
}
```

### SQL 耗时时长监控

```java
@Intercepts(@Signature(
    type = Executor.class,
    method = "update",
    args = {MappedStatement.class, Object.class}
))
public class SqlCostInterceptor implements Interceptor {

    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        long start = System.currentTimeMillis();
        try {
            return invocation.proceed();
        } finally {
            long cost = System.currentTimeMillis() - start;
            MappedStatement ms = (MappedStatement) invocation.getArgs()[0];
            String sqlId = ms.getId();
            if (cost > 1000) {
                log.warn("慢 SQL [{}ms] {}", cost, sqlId);
            }
        }
    }
}
```

## 缓存机制

### 一级缓存（SqlSession 级别）

默认开启，同一 SqlSession 内相同查询只执行一次：

```java
try (SqlSession session = sf.openSession()) {
    UserMapper mapper = session.getMapper(UserMapper.class);

    User u1 = mapper.selectById(1L);  // SELECT * FROM t_user WHERE id = 1
    User u2 = mapper.selectById(1L);  // 从缓存取，不再查库
    System.out.println(u1 == u2);     // true（同一对象引用）

    session.clearCache();             // 清空一级缓存
    User u3 = mapper.selectById(1L);  // 重新 SELECT
}
```

一级缓存失效的场景：
- 不同的 SqlSession
- 同一 SqlSession 内执行了 INSERT/UPDATE/DELETE
- 手动调用 `clearCache()`

### 二级缓存（Mapper 级别）

跨 SqlSession，需要显式开启：

```yaml
mybatis:
  configuration:
    cache-enabled: true
```

```xml
<!-- 在 Mapper.xml 中声明 -->
<cache eviction="LRU" flushInterval="60000" size="512" readOnly="true"/>
```

| 属性 | 说明 |
|------|------|
| eviction | 淘汰策略：LRU / FIFO / SOFT / WEAK |
| flushInterval | 刷新间隔（ms），不设则调用时刷新 |
| size | 最大缓存对象数 |
| readOnly | true=返回同一对象（性能好，不能修改）；false=返回副本（安全） |

### 缓存的查询顺序

```
查询请求
  → 二级缓存（命中返回）
    → 一级缓存（命中返回）
      → 数据库
```

### 生产环境对缓存的建议

- 一级缓存不依赖——在不同 SqlSession 中不共享，容易产生"同一数据两次查询不一致"的幻觉
- 二级缓存一般不推荐——在分布式环境下多节点缓存不一致，不如用 Redis
- MyBatis + Redis 做分布式缓存方案更好

## 应用场景实战

### 场景一：动态报表查询（复杂动态 SQL）

```xml
<select id="queryOrders" resultMap="orderMap">
    SELECT o.id, o.order_no, o.amount, o.status, o.created_at,
           u.username, u.phone
    FROM t_order o
    JOIN t_user u ON o.user_id = u.id
    <where>
        <if test="orderNo != null">AND o.order_no = #{orderNo}</if>
        <if test="status != null">AND o.status = #{status}</if>
        <if test="startDate != null">AND o.created_at >= #{startDate}</if>
        <if test="endDate != null">AND o.created_at <![CDATA[ <= ]]> #{endDate}</if>
        <if test="keyword != null">
            AND (o.order_no LIKE CONCAT('%', #{keyword}, '%')
                 OR u.username LIKE CONCAT('%', #{keyword}, '%'))
        </if>
    </where>
    <choose>
        <when test="sortField == 'amount'">ORDER BY o.amount ${sortDir}</when>
        <when test="sortField == 'created_at'">ORDER BY o.created_at ${sortDir}</when>
        <otherwise>ORDER BY o.created_at DESC</otherwise>
    </choose>
</select>
```

`<![CDATA[ <= ]]>`：XML 中 `<` 是保留字符，用 CDATA 包裹避免解析错误。

### 场景二：多对多带中间表查询

```xml
<resultMap id="userWithRolesMap" type="User">
    <id property="id" column="id"/>
    <result property="username" column="username"/>
    <collection property="roles" ofType="Role">
        <id property="id" column="role_id"/>
        <result property="name" column="role_name"/>
    </collection>
</resultMap>

<select id="selectUserWithRoles" resultMap="userWithRolesMap">
    SELECT u.id, u.username,
           r.id AS role_id, r.name AS role_name
    FROM t_user u
    LEFT JOIN t_user_role ur ON u.id = ur.user_id
    LEFT JOIN t_role r ON ur.role_id = r.id
    WHERE u.id = #{id}
</select>
```

## 最佳实践与踩坑记录

**实践 1：XML 中用 resultMap 而非 resultType**

即使字段名完全一致，始终定义 resultMap。它能显式声明映射关系，避免字段改名时的静默 bug。

**实践 2：动态 SQL 优先用 `<where>` 而非 `WHERE 1=1`**

`<where>` 标签自动处理多余的 AND/OR，代码更干净。

**实践 3：大数据量查询用流式**

```java
try (SqlSession session = sf.openSession()) {
    session.select("selectAllUsers", (ResultHandler<User>) resultContext -> {
        User user = resultContext.getResultObject();
        // 逐条处理，不累积到 List
    });
}
```

**踩坑 1**：`#{}` 和 `${}` 混淆。`${}` 在 WHERE 条件中导致 SQL 注入。只有 ORDER BY 和动态表名用 `${}`——且必须白名单校验。

**踩坑 2**：Mapper XML 的 namespace 写错。`namespace` 必须是 Mapper 接口的全限定类名，否则 MyBatis 找不到映射。

**踩坑 3**：一级缓存的"脏数据"幻觉。同一 SqlSession 内修改数据后查询，如果不刷新缓存，可能拿到旧值。Spring 与 MyBatis 集成时，每次查询都是新的 SqlSession（SqlSessionTemplate），不存在此问题。但手动管理 SqlSession 时需注意。

**踩坑 4**：`<if test="username != null and username != ''">` 中的 `and` 而非 `&&`。test 表达式是 OGNL 语法，必须用 `and`/`or`，不能用 `&&`/`||`。

**踩坑 5**：批量插入时 foreach 的 separator 是 `,` 而非 `;`。MyBatis 将 foreach 展开成一条 SQL，`separator` 是每条 VALUES 之间的分隔符。
