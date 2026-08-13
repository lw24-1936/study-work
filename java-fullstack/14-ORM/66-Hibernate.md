---
title: Hibernate
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [hibernate, session, cache, dirty-checking, flush, n-plus-one, fetch-join, validator, orm]
---

# Hibernate

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Hibernate Session](#hibernate-session)
- [一级缓存](#一级缓存)
- [Dirty Checking —— 脏检查](#dirty-checking--脏检查)
- [Flush —— 刷新时机](#flush--刷新时机)
- [二级缓存](#二级缓存)
- [Fetch Join —— 解决 N+1](#fetch-join--解决-n1)
- [N+1 问题全景](#n1-问题全景)
- [Hibernate Validator](#hibernate-validator)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Hibernate 是 Java 领域最老牌、最成熟的 ORM 框架。它是 JPA 规范的事实标准实现——Spring Data JPA 底层用的就是 Hibernate。掌握 Hibernate 的 Session、缓存、Dirty Checking、Flush 机制，才能真正用好 JPA。

本章聚焦 Hibernate 独有的机制和概念。JPA 通用知识（Entity 映射、关联关系、JPQL 等）见第 65 章 JPA。

## Hibernate Session

Session 是 Hibernate 的核心接口，对应 JPA 的 EntityManager。它代表一次数据库会话。

### 获取 Session

```java
// 纯 Hibernate
SessionFactory sf = new Configuration().configure().buildSessionFactory();
Session session = sf.openSession();

// JPA 方式（Spring Boot 中最常用）
@PersistenceContext
private EntityManager em;
// em.unwrap(Session.class) 获取底层 Hibernate Session
Session session = em.unwrap(Session.class);
```

### Session vs EntityManager

| | Hibernate Session | JPA EntityManager |
|--|-------------------|-------------------|
| 来源 | Hibernate 原生 | JPA 标准接口 |
| 持久化上下文 | 相同 | 相同 |
| 特有方法 | save / update / saveOrUpdate / lock / createCriteria | persist / merge |
| Criteria API | `session.createCriteria(User.class)` | JPA CriteriaBuilder |

### Session 核心方法

```java
Session session = sf.openSession();
Transaction tx = session.beginTransaction();

// 保存
session.save(user);           // 返回主键
session.persist(user);        // JPA 标准，无返回值

// 更新
session.update(detachedUser); // 把 detached 对象重新关联回 session
session.saveOrUpdate(user);   // 有 ID 则 update，无则 save

// 删除
session.delete(user);         // 等价于 remove

// 查询
User user = session.get(User.class, 1L);          // 立即查库
User proxy = session.load(User.class, 1L);        // 返回代理，访问属性时才查
List<User> users = session.createQuery(
    "FROM User WHERE age > :age", User.class)
    .setParameter("age", 18)
    .list();

// 刷新与清空
session.flush();              // 同步到数据库
session.clear();              // 清空一级缓存
session.evict(user);          // 从一级缓存中移除指定对象
```

### get vs load

```java
// get：立即查询，返回实体对象或 null
User u1 = session.get(User.class, 1L);  // 立即 SELECT

// load：返回代理对象，不查库
User u2 = session.load(User.class, 1L); // 无 SQL
System.out.println(u2.getClass());      // User$HibernateProxy$xxx
u2.getUsername();                       // 此时才 SELECT
// 如果 ID 不存在，load 不抛异常，访问属性时才抛 ObjectNotFoundException
```

## 一级缓存

一级缓存（Session 缓存 / Persistence Context）是 Session 级别的缓存，默认开启，无法关闭。生命周期 = 一次数据库会话。

### 工作原理

```
同一 Session 内：

session.get(User.class, 1L);   // SELECT * FROM user WHERE id = 1 → 缓存
session.get(User.class, 1L);   // 不查数据库，直接从一级缓存返回
session.get(User.class, 2L);   // SELECT * FROM user WHERE id = 2 → 缓存
```

### 对批量操作的影响

一级缓存在批量处理时可能导致 OOM：

```java
// 批量插入 10 万条——一级缓存持续累积
for (int i = 0; i < 100_000; i++) {
    session.save(new User("user" + i));
}
// 10 万个对象全在一级缓存 → OOM

// 正确：定时清理
for (int i = 0; i < 100_000; i++) {
    session.save(new User("user" + i));
    if (i % 50 == 0) {        // 每 50 条
        session.flush();      // 刷到数据库
        session.clear();      // 清空一级缓存
    }
}
```

### StatelessSession —— 无状态会话

批量操作时也可用 StatelessSession——不维护一级缓存，不进行脏检查：

```java
StatelessSession ss = sf.openStatelessSession();
Transaction tx = ss.beginTransaction();

for (int i = 0; i < 100_000; i++) {
    ss.insert(new User("user" + i));
}
tx.commit();
ss.close();
```

代价：没有一级缓存，不自动级联，不维护关联关系，每次操作直接查库。

## Dirty Checking —— 脏检查

Hibernate 在 flush 时自动检测 managed 实体的变化，生成 UPDATE 语句。这是 JPA/Hibernate 最强大的特性之一——你不需要调用任何 update 方法。

### 工作原理

```
1. 实体从数据库加载到一级缓存时，Hibernate 保留一份快照（snapshot）
2. flush 时，Hibernate 逐字段对比当前对象和快照
3. 不一致的字段 → 生成 UPDATE SQL
```

```java
Session session = sf.openSession();
Transaction tx = session.beginTransaction();

User u = session.get(User.class, 1L);  // 加载实体 + 生成快照
u.setNickname("新昵称");                // 修改对象
// 不需要 session.update(u)

tx.commit();  // flush → 对比快照 → UPDATE t_user SET nickname='新昵称' WHERE id=1
session.close();
```

### Dirty Checking 的性能隐患

如果不小心，大量实体进入 managed 状态会导致 flush 时昂贵的对比操作：

```java
// 错误：查询 10000 条记录，全在 session 管理下
List<User> users = session.createQuery("FROM User", User.class).list();
// 10000 个实体 + 10000 份快照 = 大量内存
tx.commit();  // 对比 10000 个实体 → 慢

// 正确：只读查询用 StatelessSession 或设为只读
List<User> users = session.createQuery("FROM User", User.class)
    .setReadOnly(true)          // 不生成快照，不脏检查
    .list();
```

## Flush —— 刷新时机

Flush 将一级缓存中的变更同步到数据库（生成 INSERT/UPDATE/DELETE SQL）。Flush 不等于 Commit——Flush 只是同步 SQL，Commit 才是提交事务。

### Flush 触发时机

FlushMode 决定 Hibernate 何时刷：

```java
// AUTO（默认）
// 在以下时机自动 flush：
// 1. 事务提交前
// 2. 执行查询前（保证查询能看到之前的修改）
session.setFlushMode(FlushModeType.AUTO);

// COMMIT
// 只在事务提交时 flush。查询前不 flush——可能查到过期数据
session.setFlushMode(FlushModeType.COMMIT);

// ALWAYS（已废弃）
// 每次查询前都 flush

// MANUAL
// 只在显式调用 session.flush() 时刷
session.setFlushMode(FlushModeType.MANUAL);
```

### 为什么查询前可能触发 Flush

```java
User u = session.get(User.class, 1L);
u.setAge(30);  // 修改了 age

// 现在执行查询
List<User> users = session.createQuery("FROM User WHERE age = 30", User.class).list();
// Hibernate 发现一级缓存中有对 User 的修改，但 age 字段还没刷到数据库
// 如果此时查数据库，刚修改的 u 可能查不到（数据库中是旧值）
// 所以 Hibernate 在查询前先 flush → UPDATE age=30 → 再 SELECT age=30 → 一致性保证
```

### 显式 Flush 的场景

```java
// 场景：先插入再获取自增 ID
User u = new User();
u.setUsername("test");
session.save(u);
session.flush();     // 立即发送 INSERT → 数据库生成 ID
System.out.println(u.getId());  // 此时 ID 已可用
```

## 二级缓存

一级缓存是 Session 级别的，二级缓存是 SessionFactory 级别的——多个 Session 共享。

### 架构

```
请求1 → Session1 → 一级缓存 → 未命中 → 二级缓存 → 未命中 → 数据库
请求2 → Session2 → 一级缓存 → 未命中 → 二级缓存 → 命中（返回）
```

### 启用二级缓存

```yaml
spring:
  jpa:
    properties:
      hibernate:
        cache:
          use_second_level_cache: true
          region:
            factory_class: org.hibernate.cache.jcache.JCacheRegionFactory
        javax:
          cache:
            provider: org.ehcache.jsr107.EhcacheCachingProvider
            uri: classpath:ehcache.xml
```

```java
// 实体级别启用缓存
@Entity
@Cacheable
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class User {
    // ...
}

// 查询缓存（缓存 Query + 参数 → 结果）
@QueryHints(@QueryHint(name = "org.hibernate.cacheable", value = "true"))
@Query("SELECT u FROM User u WHERE u.age > :age")
List<User> findAdults(@Param("age") int age);
```

### 缓存策略

| 策略 | 适用场景 | 并发 |
|------|----------|------|
| READ_ONLY | 永不修改的数据（字典表） | 无锁，最高性能 |
| NONSTRICT_READ_WRITE | 很少修改，允许短暂不一致 | 轻量锁 |
| READ_WRITE | 读写频繁，强一致性 | 读写锁（软锁） |
| TRANSACTIONAL | 完全事务隔离 | 完全事务支持（JTA） |

### 二级缓存的陷阱

- Hibernate 本身不实现二级缓存，需要引入 Ehcache / Hazelcast / Redis
- 二级缓存存的是实体对象——对所有 Session 共享，意味着 `session1.get(User.class, 1L)` 和 `session2.get(User.class, 1L)` 返回同一个对象引用（如果命中二级缓存）
- 分布式环境下二级缓存需要分布式缓存方案，否则节点间数据不一致
- **互联网项目一般不开启二级缓存**——用 Redis 做应用层缓存更可控

## Fetch Join —— 解决 N+1

N+1 是 ORM 最常见性能问题：查 N 个主实体 + 每个主实体再查 1 次关联 = N+1 次 SQL。

### 问题演示

```java
List<User> users = session.createQuery("FROM User", User.class).list();
// 1 条 SQL: SELECT * FROM t_user

for (User u : users) {
    System.out.println(u.getDept().getName());
    // 每个 User 触发 1 条 SQL: SELECT * FROM t_dept WHERE id = ?
}
// 100 个 User → 1 + 100 = 101 条 SQL
```

### Fetch Join 解决

```java
// JPQL 方式
List<User> users = session.createQuery(
    "SELECT DISTINCT u FROM User u JOIN FETCH u.dept", User.class
).list();
// 1 条 SQL: SELECT u.*, d.* FROM t_user u JOIN t_dept d ON u.dept_id = d.id

// 多级 Fetch Join
List<User> users = session.createQuery(
    "SELECT DISTINCT u FROM User u " +
    "JOIN FETCH u.dept " +
    "JOIN FETCH u.roles", User.class
).list();

// Criteria API 方式
CriteriaQuery<User> cq = cb.createQuery(User.class);
Root<User> root = cq.from(User.class);
root.fetch("dept", JoinType.LEFT);
List<User> users = session.createQuery(cq).list();
```

### Fetch Join 的限制

**无法同时 Fetch Join 两个 @OneToMany 集合**——会产生笛卡尔积，Hibernate 直接报 MultipleBagFetchException：

```java
// 报错
@Query("SELECT u FROM User u JOIN FETCH u.orders JOIN FETCH u.roles")
// HibernateException: cannot simultaneously fetch multiple bags
```

解决方案：

```java
// 方案 1：将 Set 改为 List（但效率低）
// 方案 2：分两次查询
@Query("SELECT DISTINCT u FROM User u JOIN FETCH u.orders WHERE u.id = :id")
User findWithOrders(@Param("id") Long id);

@Query("SELECT DISTINCT u FROM User u JOIN FETCH u.roles WHERE u.id = :id")
User findWithRoles(@Param("id") Long id);

// 方案 3：用 @BatchSize 替代 Fetch Join
```

**Fetch Join + 分页**：会生成内存分页警告（Hibernate 无法在 SQL 层面分页），数据量大时不要用。

## N+1 问题全景

除了 Fetch Join，还有几种解决 N+1 的方式：

### @BatchSize

```java
@Entity
public class Dept {
    @OneToMany(mappedBy = "dept")
    @BatchSize(size = 50)
    private List<Employee> employees;
}

// 100 个 Dept → 原本 1 + 100 条 SQL
// 加 @BatchSize(50) → 1 + 2 条 SQL
// SELECT * FROM employee WHERE dept_id IN (?,?,?,...,?)  -- 一批 50 个
```

### @Fetch(FetchMode.SUBSELECT)

```java
@OneToMany(mappedBy = "dept")
@Fetch(FetchMode.SUBSELECT)
private List<Employee> employees;

// 生成的 SQL:
// SELECT * FROM t_dept
// SELECT * FROM employee WHERE dept_id IN (SELECT id FROM t_dept)
// 100 个 Dept → 2 条 SQL
```

### EntityGraph

```java
// 定义
@NamedEntityGraph(name = "User.withDept",
    attributeNodes = @NamedAttributeNode("dept"))
@Entity
public class User { ... }

// 使用
@EntityGraph("User.withDept")
@Query("SELECT u FROM User u WHERE u.age > :age")
List<User> findByAge(@Param("age") int age);

// 动态 EntityGraph
EntityGraph<User> graph = em.createEntityGraph(User.class);
graph.addAttributeNodes("dept", "roles");

Map<String, Object> hints = new HashMap<>();
hints.put("javax.persistence.fetchgraph", graph);  // 或 loadgraph
User user = em.find(User.class, 1L, hints);
```

### fetchgraph vs loadgraph

- `fetchgraph`：只加载 graph 中指定的属性，其余全是 LAZY
- `loadgraph`：graph 中指定的属性用 EAGER 加载，其余按实体定义的 fetch 策略

## Hibernate Validator

Hibernate Validator 是 Bean Validation（JSR 380）的参考实现，与 Hibernate ORM 属于同一个基金会但独立的项目。Spring Boot 默认集成，可直接用：

```java
@Entity
public class User {

    @Id @GeneratedValue
    private Long id;

    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度 3-50")
    private String username;

    @Email(message = "邮箱格式不正确")
    private String email;

    @Min(value = 0, message = "年龄不能为负")
    @Max(value = 150, message = "年龄不合法")
    private Integer age;

    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    @NotNull(message = "部门不能为空")
    @ManyToOne(fetch = FetchType.LAZY)
    private Dept dept;
}
```

### 常用校验注解

| 注解 | 说明 |
|------|------|
| @NotNull | 不为 null |
| @NotBlank | 不为 null 且 trim 后长度 > 0 |
| @NotEmpty | 不为 null 且不为空集合/字符串 |
| @Size(min, max) | 字符串/集合长度范围 |
| @Min / @Max | 数值最小/最大值 |
| @Email | 邮箱格式 |
| @Pattern | 正则匹配 |
| @Positive / @Negative | 正数 / 负数 |
| @Digits(integer, fraction) | 整数位和小数位数 |
| @Future / @Past | 未来 / 过去时间 |

### 自定义校验

```java
// 1. 注解
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = {EnumValueValidator.class})
public @interface EnumValue {
    String message() default "枚举值不合法";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
    Class<? extends Enum<?>> enumClass();
}

// 2. 校验器
public class EnumValueValidator implements ConstraintValidator<EnumValue, Object> {
    private Set<Object> validValues = new HashSet<>();

    @Override
    public void initialize(EnumValue constraintAnnotation) {
        for (Enum<?> e : constraintAnnotation.enumClass().getEnumConstants()) {
            validValues.add(e.name());
        }
    }

    @Override
    public boolean isValid(Object value, ConstraintValidatorContext context) {
        return value == null || validValues.contains(value.toString());
    }
}

// 3. 使用
@EnumValue(enumClass = Gender.class, message = "性别只能是 MALE 或 FEMALE")
private String gender;
```

### 分组校验

同一实体在不同场景需要不同校验规则：

```java
public interface CreateGroup {}
public interface UpdateGroup {}

public class User {
    @NotNull(groups = UpdateGroup.class)          // 更新时必填
    @Null(groups = CreateGroup.class)             // 创建时不能有 ID
    private Long id;

    @NotBlank(groups = {CreateGroup.class, UpdateGroup.class})
    private String username;
}

// Controller 中使用
@PostMapping
public Result create(@Validated(CreateGroup.class) @RequestBody User user) { }

@PutMapping("/{id}")
public Result update(@Validated(UpdateGroup.class) @RequestBody User user) { }
```

## 应用场景实战

### 场景一：批量处理（Session 清理）

百万级数据迁移的正确姿势：

```java
public void batchMigrateUsers() {
    Session session = sf.openSession();
    Transaction tx = session.beginTransaction();

    int batchSize = 50;
    int count = 0;

    ScrollableResults<User> results = session.createQuery(
        "FROM OldUser", OldUser.class
    ).setFetchSize(50).scroll(ScrollMode.FORWARD_ONLY);

    while (results.next()) {
        OldUser old = results.get();
        NewUser nu = new NewUser();
        nu.setName(old.getUsername());
        nu.setEmail(old.getEmail());
        session.save(nu);

        if (++count % batchSize == 0) {
            session.flush();
            session.clear();      // 清空缓存防止 OOM
        }
    }

    tx.commit();
    session.close();
}
```

### 场景二：Row-Level Security 用 Filter

Hibernate 提供 `@Filter` 注解实现多租户、软删除等行级过滤：

```java
@Entity
@FilterDef(name = "tenantFilter", parameters = @ParamDef(name = "tenantId", type = Long.class))
@Filter(name = "tenantFilter", condition = "tenant_id = :tenantId")
public class User {
    @Column(name = "tenant_id")
    private Long tenantId;
}

// 使用
Session session = em.unwrap(Session.class);
session.enableFilter("tenantFilter").setParameter("tenantId", currentTenantId);

// 此后该 session 的所有 User 查询都自动加上 WHERE tenant_id = ?
List<User> users = session.createQuery("FROM User", User.class).list();
// SQL: SELECT * FROM t_user WHERE tenant_id = 100
```

## 最佳实践与踩坑记录

**实践 1：用 DTO 投影而非实体**

```java
// 差：返回全部字段 + 懒加载陷阱
List<User> users = em.createQuery("FROM User", User.class).getResultList();

// 好：只选需要的字段
List<UserDTO> dtos = em.createQuery(
    "SELECT new com.example.UserDTO(u.id, u.username, d.name) " +
    "FROM User u JOIN u.dept d", UserDTO.class
).getResultList();
```

**实践 2：批量操作的 flush+clear 节奏**

每 50 条 flush+clear 是一个经过验证的批量大小。太大可能 OOM，太小影响性能。

**实践 3：查询设为只读**

```java
@Query("SELECT u FROM User u")
@QueryHints(@QueryHint(name = "org.hibernate.readOnly", value = "true"))
List<User> findAllReadOnly();
```

只读查询不生成快照，不参与脏检查，内存占用减半。

**踩坑 1**：`session.save()` 后立即在查询中看不到。flush 模式是 AUTO 时，JPQL 查询前会 flush，但原生 SQL（nativeQuery）不会。`session.save()` 后执行 `session.createNativeQuery("SELECT * FROM t_user WHERE ...")` 查不到刚保存的数据——手动 `session.flush()`。

**踩坑 2**：`Transaction` 和 `Session` 的生命周期管理。Session 关闭后所有 managed 对象变 detached，懒加载抛出 `LazyInitializationException`。Controller 中访问懒加载属性是常见错误。

**踩坑 3**：`@OneToMany` 的 `List` 重复问题。当 Fetch Join 与 `@OneToMany` List 一起使用时，如果关联表有多条记录，会导致结果集膨胀（笛卡尔积），Hibernate 可能返回重复的主实体。用 `SELECT DISTINCT` 或改用 Set。

**踩坑 4**：二级缓存的"脏读"。二级缓存在多 Session 场景下，A Session 修改了实体但未提交，B Session 通过二级缓存读到旧值。用 READ_WRITE 策略可以避免，但性能开销大，不如直接用 Redis。
