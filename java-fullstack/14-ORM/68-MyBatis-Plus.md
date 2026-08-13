---
title: MyBatis-Plus
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [mybatis-plus, basemapper, wrapper, lambda, pagination, auto-fill, logic-delete, optimistic-lock, code-generator]
---

# MyBatis-Plus

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [BaseMapper —— 基础 CRUD](#basemapper--基础-crud)
- [Service —— 服务层封装](#service--服务层封装)
- [Wrapper —— 条件构造器](#wrapper--条件构造器)
- [LambdaQueryWrapper / LambdaUpdateWrapper](#lambdaquerywrapper--lambdaupdatewrapper)
- [分页插件](#分页插件)
- [主键策略](#主键策略)
- [自动填充](#自动填充)
- [逻辑删除](#逻辑删除)
- [乐观锁](#乐观锁)
- [代码生成器](#代码生成器)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

MyBatis-Plus 是 MyBatis 的增强工具，在 MyBatis 基础上只做增强不做改变。它解决了 MyBatis 最大的痛点——简单 CRUD 也需要手写 XML。通过 BaseMapper 和条件构造器，单表操作基本不需要写任何 SQL。

核心设计理念：**单表操作零 SQL，复杂查询保留 MyBatis 全部能力**。

## BaseMapper —— 基础 CRUD

继承 BaseMapper 后，自动获得 17 个内置方法，无需编写 XML。

```java
@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 只需写复杂查询，简单 CRUD 全部继承
}
```

### 内置方法一览

```java
// 插入
int insert(T entity);                        // 插入一条
int insertBatch(List<T> entityList);        // 批量插入（需开启批处理）

// 删除
int deleteById(Serializable id);             // 按 ID 删
int deleteByMap(Map<String, Object> map);    // 按条件删
int delete(Wrapper<T> wrapper);              // 按 Wrapper 删
int deleteBatchIds(Collection<?> ids);       // 按 ID 批量删

// 更新
int updateById(T entity);                    // 按 ID 更新
int update(T entity, Wrapper<T> wrapper);    // 按条件更新

// 查询
T selectById(Serializable id);               // 按 ID 查
List<T> selectBatchIds(Collection<?> ids);   // 按 ID 批量查
List<T> selectByMap(Map<String, Object> map);// 按 Map 条件查
T selectOne(Wrapper<T> wrapper);             // 按 Wrapper 查单条
List<T> selectList(Wrapper<T> wrapper);      // 按 Wrapper 查列表
List<Map<String, Object>> selectMaps(Wrapper<T> wrapper);  // 返回 Map
List<Object> selectObjs(Wrapper<T> wrapper); // 只返回第一列
Long selectCount(Wrapper<T> wrapper);        // 计数
Page<T> selectPage(Page<T> page, Wrapper<T> wrapper);  // 分页查询
Page<Map<String, Object>> selectMapsPage(Page<T> page, Wrapper<T> wrapper);

// 存在性
default boolean exists(Wrapper<T> wrapper);  // 3.5.6+
```

### 使用示例

```java
// 插入
User user = new User();
user.setUsername("张三");
user.setEmail("zhang@example.com");
userMapper.insert(user);
// 默认策略下，如果主键为空，自动填充雪花 ID
System.out.println(user.getId());   // 1756112345678901234

// 按 ID 查询
User u = userMapper.selectById(1L);

// 按条件更新——只更新非 null 字段
User update = new User();
update.setId(1L);
update.setEmail("new@example.com");
userMapper.updateById(update);
// SQL: UPDATE t_user SET email='new@example.com' WHERE id=1
// username 不会被更新（null 值自动忽略）

// 按 Wrapper 更新——不会忽略 null
userMapper.update(user, Wrappers.<User>lambdaUpdate()
    .set(User::getStatus, 0)
    .eq(User::getId, 1L));
```

## Service —— 服务层封装

MyBatis-Plus 提供了 IService 接口和 ServiceImpl 实现类，在 BaseMapper 基础上增加批量操作和链式调用。

```java
// 接口
public interface UserService extends IService<User> {
}

// 实现类
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User>
                              implements UserService {
}
```

### IService 新增方法

```java
// 批量操作
boolean saveBatch(Collection<T> list);         // 批量保存
boolean saveOrUpdateBatch(Collection<T> list); // 批量新增或更新
boolean updateBatchById(Collection<T> list);    // 批量按 ID 更新

// SaveOrUpdate
boolean saveOrUpdate(T entity);                // 有 ID 则更新，无则插入

// 链式操作
userService.lambdaQuery()
    .eq(User::getStatus, 1)
    .gt(User::getAge, 18)
    .list();

userService.lambdaUpdate()
    .set(User::getStatus, 0)
    .eq(User::getId, 1L)
    .update();
```

### BaseMapper vs IService

| | BaseMapper | IService |
|--|------------|----------|
| 层次 | Mapper 层（DAO） | Service 层 |
| 批量操作 | 需要手动开启批处理 | 内置 saveBatch/updateBatchById |
| 链式调用 | 不支持 | 支持 lambdaQuery/lambdaUpdate |
| 业务逻辑 | 不参与 | 可添加 |

**推荐**：Controller → Service（IService）→ Mapper（BaseMapper）。Service 层保持纯粹的业务逻辑，不直接调 Mapper。

## Wrapper —— 条件构造器

Wrapper 是 MyBatis-Plus 最核心的设计——用链式调用构建 WHERE 条件，代替 XML 中的 `<if>` 标签。

### 基本用法

```java
// 构建条件
QueryWrapper<User> wrapper = new QueryWrapper<>();
wrapper.eq("username", "张三")        // =
       .ne("status", 2)              // !=
       .gt("age", 18)                // >
       .ge("age", 18)                // >=
       .lt("age", 60)                // <
       .le("age", 60)                // <=
       .between("age", 18, 35)       // BETWEEN
       .notBetween("age", 18, 35)
       .like("username", "张")       // LIKE '%张%'
       .likeLeft("username", "张")    // LIKE '%张'
       .likeRight("username", "张")   // LIKE '张%'
       .isNull("email")              // IS NULL
       .isNotNull("phone")           // IS NOT NULL
       .in("status", 1, 2, 3)        // IN
       .notIn("status", 4, 5)        // NOT IN
       .inSql("dept_id", "SELECT id FROM dept WHERE name = '研发部'")  // IN 子查询
       .groupBy("dept_id")           // GROUP BY
       .having("COUNT(*) > {0}", 5)  // HAVING
       .orderByAsc("age")            // ORDER BY ASC
       .orderByDesc("created_at")    // ORDER BY DESC
       .last("LIMIT 10");            // 尾部追加 SQL
```

### 动态条件

```java
QueryWrapper<User> wrapper = new QueryWrapper<>();
wrapper.eq(StringUtils.hasText(username), "username", username)
       .gt(minAge != null, "age", minAge)
       .eq(status != null, "status", status)
       .like(StringUtils.hasText(keyword), "username", keyword)
       .or(w -> w.eq("status", 1).isNull("email"));  // 嵌套 OR
// SQL: WHERE username = ? AND age > ? AND (status = 1 OR email IS NULL)
```

条件方法的第一个 boolean 参数控制是否添加该条件——一行代码替代 `<if test="...">`。

### 复杂条件

```java
wrapper.and(w -> w.eq("status", 1).gt("age", 18))
       .or(w -> w.eq("status", 2).lt("age", 25));
// WHERE (status = 1 AND age > 18) OR (status = 2 AND age < 25)

wrapper.nested(w -> w.eq("username", "admin").or().eq("email", "admin@x.com"))
       .eq("status", 1);
// WHERE (username = 'admin' OR email = 'admin@x.com') AND status = 1
```

### 查询指定列、排除列

```java
// 只查某些列
wrapper.select("id", "username", "email");        // SELECT id, username, email

// 排除某些列
wrapper.select(User.class, info ->
    !info.getColumn().equals("password"));        // 排除 password
```

### UpdateWrapper

```java
UpdateWrapper<User> wrapper = new UpdateWrapper<>();
wrapper.set("status", 0)                     // SET status = 0
       .set("updated_at", LocalDateTime.now())
       .eq("status", 1)                      // WHERE status = 1
       .lt("last_login_at", threeMonthsAgo); // AND last_login_at < ?

userMapper.update(null, wrapper);            // entity 传 null，条件全部在 wrapper
```

## LambdaQueryWrapper / LambdaUpdateWrapper

Lambda 条件构造器用 Lambda 表达式替代字符串列名，编译期检查，不会写错字段名。

```java
// QueryWrapper：字符串列名，无编译检查
wrapper.eq("username", "张三");   // 字段名写错编译期不报错

// LambdaQueryWrapper：Lambda 表达式，字段名依赖编译检查
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(User::getUsername, "张三")      // 编译期检查字段名
       .gt(User::getAge, 18)
       .between(User::getCreatedAt, startDate, endDate)
       .orderByDesc(User::getCreatedAt);
```

### 链式 Lambda —— 最简洁写法

MyBatis-Plus 3.5.1+ 支持 Service 层的链式 Lambda 调用，代码最简洁：

```java
// 查询
List<User> users = userService.lambdaQuery()
    .eq(User::getStatus, 1)
    .gt(User::getAge, 18)
    .orderByDesc(User::getCreatedAt)
    .list();

// 单条查询
User user = userService.lambdaQuery()
    .eq(User::getUsername, "admin")
    .one();

// 计数
long count = userService.lambdaQuery()
    .eq(User::getStatus, 1)
    .count();

// 更新
userService.lambdaUpdate()
    .set(User::getStatus, 0)
    .eq(User::getId, 1L)
    .update();

// 删除
userService.lambdaUpdate()
    .eq(User::getStatus, 3)   // 删除状态 3 的用户
    .remove();
```

### 应该用哪个

| 场景 | 推荐 |
|------|------|
| 开发阶段、简单查询 | LambdaQueryWrapper（编译安全） |
| 复杂动态 SQL | QueryWrapper（字符串方式灵活） |
| Service 层 CRUD | lambdaQuery().list()（最简洁） |
| 方法传参 | 传 LambdaQueryWrapper 对象 |

## 分页插件

### 配置

```java
@Configuration
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

### 使用

```java
// 方式一：Page 对象
Page<User> page = new Page<>(1, 20);      // 第 1 页，每页 20 条
page.addOrder(OrderItem.desc("created_at"));
page = userMapper.selectPage(page, null);

// 结果
System.out.println(page.getCurrent());     // 1
System.out.println(page.getSize());        // 20
System.out.println(page.getTotal());       // 总记录数
System.out.println(page.getPages());       // 总页数
System.out.println(page.getRecords());     // 当前页数据

// 方式二：需要连表时，自定义查询传 Page 参数
Page<User> selectPageWithDept(@Param("page") Page<User> page,
                              @Param("status") Integer status);
```

```xml
<select id="selectPageWithDept" resultMap="userDeptMap">
    SELECT u.*, d.name AS dept_name
    FROM t_user u
    LEFT JOIN t_dept d ON u.dept_id = d.id
    <where>
        <if test="status != null">AND u.status = #{status}</if>
    </where>
    ORDER BY u.created_at DESC
</select>
```

### PageDTO 转换

```java
public class PageDTO<T> {
    private long current;
    private long size;
    private long total;
    private List<T> records;

    public static <T> PageDTO<T> of(Page<T> page) {
        PageDTO<T> dto = new PageDTO<>();
        dto.current = page.getCurrent();
        dto.size = page.getSize();
        dto.total = page.getTotal();
        dto.records = page.getRecords();
        return dto;
    }
}
```

## 主键策略

```java
public class User {
    @TableId(type = IdType.ASSIGN_ID)
    private Long id;
}
```

| IdType | 说明 | 适用 |
|--------|------|------|
| AUTO | 数据库自增 | 单库单表 |
| NONE | 无策略（全局配置） | |
| INPUT | 用户手动输入 | 用户自定义 ID |
| ASSIGN_ID | 雪花算法（默认） | 分布式，长整型 |
| ASSIGN_UUID | UUID（去掉中划线） | 分布式，字符串 |

全局配置（application.yml）：

```yaml
mybatis-plus:
  global-config:
    db-config:
      id-type: assign_id
```

## 自动填充

用于自动填充创建时间（createdAt）、更新时间（updatedAt）、操作人（createdBy）等审计字段。

### 配置

```java
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {

    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createdAt", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "updatedAt", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "createdBy", Long.class, getCurrentUserId());
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updatedAt", LocalDateTime.class, LocalDateTime.now());
        this.strictUpdateFill(metaObject, "updatedBy", Long.class, getCurrentUserId());
    }

    // 从 ThreadLocal 或 SecurityContext 获取当前用户 ID
    private Long getCurrentUserId() {
        return UserContext.getUserId();  // 自定义
    }
}
```

### 实体类

```java
public class User {

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableField(fill = FieldFill.INSERT)
    private Long createdBy;

    @TableField(fill = FieldFill.UPDATE)
    private Long updatedBy;
}
```

| FieldFill | 触发时机 |
|-----------|----------|
| INSERT | insert 时填充 |
| UPDATE | update 时填充 |
| INSERT_UPDATE | insert 和 update 时都填充 |

### 注意事项

`strictInsertFill` 在字段已有值时不会覆盖。如果希望强制更新用 `setFieldValByName`：

```java
this.setFieldValByName("updatedAt", LocalDateTime.now(), metaObject);
```

## 逻辑删除

```java
@TableLogic
private Integer deleted;    // 0=未删除, 1=已删除 或 null=未删除, 非null=已删除
```

全局配置：

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted        # 逻辑删除字段（实体类字段名）
      logic-delete-value: 1              # 删除后的值
      logic-not-delete-value: 0          # 未删除的值
```

配置后，所有操作自动加上逻辑删除条件：

```java
userMapper.deleteById(1L);
// SQL: UPDATE t_user SET deleted = 1 WHERE id = 1 AND deleted = 0

userMapper.selectList(null);
// SQL: SELECT * FROM t_user WHERE deleted = 0
```

如果确实需要查询已删除数据，使用自定义 SQL 或注入：

```java
@Select("SELECT * FROM t_user WHERE deleted = 1")
List<User> selectDeleted();
```

## 乐观锁

### 配置

```java
@Bean
public MybatisPlusInterceptor mybatisPlusInterceptor() {
    MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
    interceptor.addInnerInterceptor(new OptimisticLockerInnerInterceptor());
    return interceptor;
}
```

### 实体类

```java
public class Product {
    private Long id;
    private String name;
    private Integer stock;

    @Version
    private Integer version;    // 版本号字段
}
```

### 使用

```java
// 更新时自动带上版本号
Product p = productMapper.selectById(1L);  // version = 1
p.setStock(p.getStock() - 10);
productMapper.updateById(p);
// SQL: UPDATE t_product SET stock = ..., version = 2 WHERE id = 1 AND version = 1

// 如果 version 不匹配（被其他事务更新了），updateById 返回 0
if (productMapper.updateById(p) == 0) {
    throw new OptimisticLockException("数据已被修改，请重试");
}
```

### 乐观锁重试

```java
public boolean deductStock(Long productId, int quantity) {
    for (int retry = 0; retry < 3; retry++) {
        Product p = productMapper.selectById(productId);
        if (p.getStock() < quantity) return false;
        p.setStock(p.getStock() - quantity);

        if (productMapper.updateById(p) > 0) {
            return true;  // 更新成功
        }
        // 版本冲突，重试
        try { Thread.sleep(50L * (retry + 1)); } catch (InterruptedException e) { }
    }
    throw new BizException("系统繁忙，请稍后重试");
}
```

## 代码生成器

MyBatis-Plus 的代码生成器可以根据数据库表自动生成 Entity、Mapper、Service、Controller。

### 依赖

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-generator</artifactId>
    <version>3.5.5</version>
</dependency>
<dependency>
    <groupId>org.apache.velocity</groupId>
    <artifactId>velocity-engine-core</artifactId>
    <version>2.3</version>
</dependency>
```

### 生成代码

```java
public class CodeGenerator {
    public static void main(String[] args) {
        FastAutoGenerator.create(
                "jdbc:mysql://localhost:3306/mydb?useSSL=false&serverTimezone=Asia/Shanghai",
                "root", "password")
            .globalConfig(builder -> builder
                .author("开发者")
                .outputDir("/path/to/project/src/main/java")
                .disableOpenDir())
            .packageConfig(builder -> builder
                .parent("com.example")
                .moduleName("system")
                .entity("entity")
                .mapper("mapper")
                .service("service")
                .serviceImpl("service.impl")
                .controller("controller"))
            .strategyConfig(builder -> builder
                .addInclude("t_user", "t_dept")             // 要生成的表
                .addTablePrefix("t_")                        // 去掉表前缀
                .entityBuilder()
                    .enableLombok()                          // 使用 Lombok
                    .enableTableFieldAnnotation()            // 字段生成 @TableField
                    .logicDeleteColumnName("deleted")        // 逻辑删除字段
                    .versionColumnName("version")            // 乐观锁字段
                .controllerBuilder()
                    .enableRestStyle())                      // @RestController
            .execute();
    }
}
```

### 生成的文件

```
src/main/java/com/example/system/
├── entity/
│   └── User.java            // @TableName, @TableId, @TableField
├── mapper/
│   └── UserMapper.java      // extends BaseMapper<User>
├── service/
│   ├── UserService.java     // extends IService<User>
│   └── impl/
│       └── UserServiceImpl.java  // extends ServiceImpl<UserMapper, User>
└── controller/
    └── UserController.java  // 基本 CRUD 接口
```

实际项目中，代码生成器主要生成 Mapper 和 Entity 层。Service 和 Controller 通常有业务逻辑，生成后再手动调整。

## 应用场景实战

### 场景一：多条件动态查询

前端传了 5 个可选筛选条件，后端用一个方法处理：

```java
@GetMapping("/users")
public PageDTO<UserVO> listUsers(
        @RequestParam(required = false) String keyword,
        @RequestParam(required = false) Integer status,
        @RequestParam(required = false) Long deptId,
        @RequestParam(required = false) @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate startDate,
        @RequestParam(required = false) @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate endDate,
        @RequestParam(defaultValue = "1") int pageNum,
        @RequestParam(defaultValue = "20") int pageSize) {

    Page<User> page = new Page<>(pageNum, pageSize);

    LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
    wrapper.like(StringUtils.hasText(keyword), User::getUsername, keyword)
           .or().like(StringUtils.hasText(keyword), User::getEmail, keyword)
           .eq(status != null, User::getStatus, status)
           .eq(deptId != null, User::getDeptId, deptId)
           .ge(startDate != null, User::getCreatedAt, startDate)
           .le(endDate != null, User::getCreatedAt, endDate)
           .orderByDesc(User::getCreatedAt);

    Page<User> result = userMapper.selectPage(page, wrapper);
    return PageDTO.of(result, UserVO::from);  // Entity → VO
}
```

### 场景二：分组统计

```java
public Map<Long, Long> countByDept() {
    QueryWrapper<User> wrapper = new QueryWrapper<>();
    wrapper.select("dept_id", "COUNT(*) AS cnt")
           .groupBy("dept_id");

    List<Map<String, Object>> list = userMapper.selectMaps(wrapper);
    return list.stream().collect(Collectors.toMap(
        m -> (Long) m.get("dept_id"),
        m -> (Long) m.get("cnt")
    ));
}
```

### 场景三：存在性判断（不返回完整数据）

```java
// 检查用户名是否已存在（只查 COUNT，不返回数据）
boolean exists = userService.lambdaQuery()
    .eq(User::getUsername, username)
    .exists();

// 等价 SQL: SELECT COUNT(*) FROM t_user WHERE username = ? LIMIT 1
```

## 最佳实践与踩坑记录

**实践 1：Lambda 方式优先于字符串方式**

```java
// 差：字段名写错编译期不报错
wrapper.eq("usernmae", "张三");    // 拼写错误，运行时才暴露

// 好：编译期检查
wrapper.eq(User::getUsername, "张三");
```

**实践 2：Service 层优先使用链式 Lambda**

`userService.lambdaQuery().eq(...).list()` 比 `new LambdaQueryWrapper<>()` + `userMapper.selectList()` 更简洁。复杂查询才退回到 Mapper + XML。

**实践 3：更新操作区分 updateById 和 UpdateWrapper**

- `updateById(entity)`：只更新非 null 字段（null 自动忽略）
- `UpdateWrapper` + `update(null, wrapper)`：精确控制 SET 哪些字段（不做 null 判断）

```java
// updateById：null 字段不参与更新
User u = new User();
u.setId(1L);
u.setUsername(null);    // 忽略
u.setEmail("e@x.com");
userMapper.updateById(u);  // 只更新 email

// UpdateWrapper：精确控制，可以 SET NULL
userMapper.update(null, Wrappers.<User>lambdaUpdate()
    .set(User::getUsername, null)   // 显式 SET NULL
    .set(User::getEmail, "e@x.com")
    .eq(User::getId, 1L));
```

**实践 4：分页必须配置 PaginationInterceptor**

不配置则 `Page` 参数被忽略，查询返回全部数据——内存分页。

**踩坑 1**：自动填充的 `strictInsertFill` 不覆盖已有值。如果使用 `saveOrUpdate` 时需要强制更新时间，用 `setFieldValByName`。

**踩坑 2**：逻辑删除字段不要在 Mapper.xml 中手动加 `WHERE deleted = 0`。MyBatis-Plus 自动拼接，手动加会导致重复条件。

**踩坑 3**：乐观锁插件 + `updateById` 时，入参的 version 字段不能为 null。`updateById` 从 entity 中取值，如果 entity 是 new 出来的且没设 version，更新条件中 version=null 导致匹配不到任何行。

```java
// 正确
Product p = productMapper.selectById(1L);  // p 带有最新 version
p.setStock(p.getStock() - 10);
productMapper.updateById(p);    // WHERE version = p.version

// 错误
Product p = new Product();
p.setId(1L);
p.setStock(100);
productMapper.updateById(p);    // version 是 null，WHERE version IS NULL
```

**踩坑 4**：批量操作 `saveBatch` 默认是一条条 INSERT，不是真正的批量。需要开启 JDBC 的 `rewriteBatchedStatements=true` 才能真正合并为单条多 VALUES。

**踩坑 5**：`LambdaQueryWrapper` 的 `or()` 和 `and()` 的优先级。`or()` 会先清空前后的括号，嵌套条件必须用 `and(w -> ...)` 或 `or(w -> ...)`。
