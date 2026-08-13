---
title: JPA
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [jpa, entity, repository, entitymanager, jpql, criteria, specification, lazy-loading, cascade, orm]
---

# JPA

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [JPA 与 Hibernate 的关系](#jpa-与-hibernate-的关系)
- [Entity —— 实体映射](#entity--实体映射)
- [Repository —— 数据访问层](#repository--数据访问层)
- [EntityManager —— 持久化上下文操作](#entitymanager--持久化上下文操作)
- [Persistence Context —— 持久化上下文](#persistence-context--持久化上下文)
- [Entity 生命周期](#entity-生命周期)
- [关联关系映射](#关联关系映射)
- [Cascade 与 Orphan Removal](#cascade-与-orphan-removal)
- [Lazy Loading —— 延迟加载](#lazy-loading--延迟加载)
- [JPQL](#jpql)
- [Criteria API](#criteria-api)
- [Specification —— 动态查询](#specification--动态查询)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JPA（Jakarta Persistence API，原名 Java Persistence API）是 Java 官方的 ORM 规范。它定义了一套标准的接口和注解，由 Hibernate、EclipseLink 等厂商实现。JPA 只定义"怎么做"，不定义"怎么实现"——你写的 JPA 代码可以在 Hibernate 和 EclipseLink 之间切换而无需改动。

核心思想：将 Java 对象与数据库表映射，让开发者用操作对象的方式操作数据库，而不写 SQL。

## JPA 与 Hibernate 的关系

```
JPA  = 接口规范（javax.persistence / jakarta.persistence）
Hibernate = JPA 的实现 + 自己的扩展功能

类比：
JPA      → JDBC 接口（java.sql）
Hibernate → MySQL Driver（实现了 JDBC 接口）
```

这意味着：
- 只用 JPA 注解和 API，代码可以切换实现（虽然实际很少切换）
- Hibernate 提供了 JPA 没有的功能（如二级缓存策略、批量操作）
- Spring Data JPA 在 JPA 之上再封装一层，提供 Repository 自动实现

## Entity —— 实体映射

Entity 是 JPA 的核心——一个 POJO 通过注解与数据库表建立映射。

### 基本映射

```java
@Entity                         // 标记为实体类
@Table(name = "t_user")        // 映射到表 t_user
@Data
public class User {

    @Id                        // 主键
    @GeneratedValue(strategy = GenerationType.IDENTITY)  // 自增
    private Long id;

    @Column(name = "username", length = 50, nullable = false, unique = true)
    private String username;

    @Column(name = "nickname", length = 100)
    private String nickname;

    @Column(name = "age")
    private Integer age;

    @Enumerated(EnumType.STRING)  // 枚举存为字符串（推荐）
    private Gender gender;

    @Temporal(TemporalType.TIMESTAMP)  // Date → SQL 类型
    private Date createdAt;

    @Transient                    // 不映射到数据库
    private String tempField;
}
```

### 主键生成策略

```java
@GeneratedValue(strategy = GenerationType.IDENTITY)
// MySQL 自增，ID 在 INSERT 执行后由数据库生成

@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "seq_user")
@SequenceGenerator(name = "seq_user", sequenceName = "user_seq", allocationSize = 50)
// 数据库序列（PostgreSQL / Oracle），allocationSize 用于批量预取提升性能

@GeneratedValue(strategy = GenerationType.TABLE, generator = "tbl_gen")
@TableGenerator(name = "tbl_gen", table = "id_generator", pkColumnName = "gen_name",
                valueColumnName = "gen_value", allocationSize = 100)
// 用一张表模拟序列（兼容所有数据库，性能最差）

@GeneratedValue(strategy = GenerationType.AUTO)
// 由 JPA 实现自动选择（Hibernate 下默认 TABLE，性能差。生产环境显式指定）
```

### 字段类型映射

| Java 类型 | @Column 默认映射 | 说明 |
|-----------|-----------------|------|
| String | VARCHAR(255) | 用 @Column(length=N) 指定 |
| int / Integer | INTEGER | |
| long / Long | BIGINT | |
| BigDecimal | DECIMAL | @Column(precision=18, scale=2) |
| boolean / Boolean | BIT(1) 或 BOOLEAN | |
| LocalDate (JPA 2.2+) | DATE | |
| LocalDateTime | TIMESTAMP | |
| Enum | ORDINAL(数字, 默认) 或 STRING(字符串) | **永远用 STRING**，ORDINAL 在枚举顺序变化时数据错乱 |
| byte[] | BLOB | |
| String + @Lob | CLOB | 大文本 |

### 复合主键

```java
// @IdClass 方式
@Entity
@IdClass(OrderItemId.class)
public class OrderItem {
    @Id private Long orderId;
    @Id private Long productId;
    private Integer quantity;
}

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OrderItemId implements Serializable {
    private Long orderId;
    private Long productId;
}

// @EmbeddedId 方式（更面向对象）
@Entity
public class OrderItem {
    @EmbeddedId
    private OrderItemId id;
    private Integer quantity;
}

@Embeddable
@Data
public class OrderItemId implements Serializable {
    private Long orderId;
    private Long productId;
}
```

## Repository —— 数据访问层

Repository 接口由 Spring Data JPA 自动生成实现，无需手写 DAO 代码。

### 三种 Repository

```java
// 1. CrudRepository —— CRUD 基础
public interface UserRepo extends CrudRepository<User, Long> {
    // 自带：save / saveAll / findById / findAll / count / delete / deleteById
}

// 2. PagingAndSortingRepository —— 分页排序
public interface UserRepo extends PagingAndSortingRepository<User, Long> {
    // 自带：findAll(Pageable) / findAll(Sort)
}

// 3. JpaRepository —— 全功能（最常用）
public interface UserRepo extends JpaRepository<User, Long> {
    // 自带除上述外还有：flush / saveAndFlush / deleteInBatch / findAll(Example)
}
```

### 方法命名查询

Spring Data JPA 根据方法名自动生成 SQL——这是它最方便的特性：

```java
public interface UserRepo extends JpaRepository<User, Long> {

    // 等值查询
    User findByUsername(String username);

    // 多条件
    List<User> findByAgeAndGender(Integer age, Gender gender);

    // 模糊查询
    List<User> findByUsernameLike(String pattern);

    // 范围查询
    List<User> findByAgeBetween(Integer min, Integer max);

    // 排序
    List<User> findByAgeGreaterThanOrderByCreatedAtDesc(Integer age);

    // Top N
    List<User> findTop10ByOrderByCreatedAtDesc();

    // IN 查询
    List<User> findByIdIn(List<Long> ids);

    // 判断存在
    boolean existsByUsername(String username);

    // 计数
    long countByGender(Gender gender);

    // 关联表查询
    List<User> findByDeptName(String deptName);
}
```

方法命名关键字对照：

| 关键字 | SQL | 示例 |
|--------|-----|------|
| And | ... AND ... | findByAgeAndGender |
| Or | ... OR ... | findByAgeOrGender |
| Between | BETWEEN ... AND ... | findByAgeBetween |
| LessThan / GreaterThan | < / > | findByAgeGreaterThan |
| Like | LIKE | findByUsernameLike |
| NotNull / IsNull | IS NOT NULL / IS NULL | findByEmailIsNull |
| In | IN(...) | findByIdIn |
| OrderBy | ORDER BY | ...OrderByCreatedAtDesc |
| Top / First | LIMIT | findTop10By... |

### @Query 自定义查询

方法名太长或逻辑复杂时，用 @Query：

```java
// JPQL
@Query("SELECT u FROM User u WHERE u.age > :age AND u.gender = :gender")
List<User> findAdults(@Param("age") Integer age, @Param("gender") Gender gender);

// 原生 SQL
@Query(value = "SELECT * FROM t_user WHERE age > ?1 LIMIT ?2", nativeQuery = true)
List<User> findTopAdults(Integer age, int limit);

// 更新操作
@Modifying
@Transactional
@Query("UPDATE User u SET u.status = :status WHERE u.createdAt < :date")
int deactivateOldUsers(@Param("status") Integer status, @Param("date") LocalDateTime date);
```

## EntityManager —— 持久化上下文操作

EntityManager 是 JPA 最底层的 API，负责所有实体的 CRUD 和持久化上下文管理。Spring Data JPA 的 Repository 内部也是通过 EntityManager 实现的。

```java
@PersistenceContext
private EntityManager em;

// ——— 查询 ———
User user = em.find(User.class, 1L);  // 按主键查

List<User> users = em.createQuery("SELECT u FROM User u WHERE u.age > :age", User.class)
        .setParameter("age", 18)
        .setFirstResult(0)
        .setMaxResults(20)
        .getResultList();

// ——— 增删改 ———
em.persist(user);     // INSERT（实体变为 managed）
em.merge(user);       // UPDATE（detached 实体重新回到 managed）
em.remove(user);      // DELETE（managed 实体变为 removed）

// ——— 刷新 ———
em.flush();                     // 强制 SQL 立即发送到数据库
em.clear();                     // 清空持久化上下文（所有 managed 实体变为 detached）
em.detach(user);               // 将指定实体从持久化上下文中分离

// ——— 获取代理 ———
User proxy = em.getReference(User.class, 1L);  // 返回代理对象（不查库），访问属性时才查
```

## Persistence Context —— 持久化上下文

持久化上下文是 JPA 最核心的概念，可以理解为一个"实体缓存"——管理着所有从数据库读取或要写入数据库的实体对象。

### 核心特性

**1. 同主键保证同一个 Java 对象**

```java
User u1 = em.find(User.class, 1L);
User u2 = em.find(User.class, 1L);
System.out.println(u1 == u2);  // true —— 同一个对象
```

这是 JPA 的一级缓存：同一个 EntityManager 内，相同主键返回同一个 Java 实例。

**2. 脏检查（Dirty Checking）**

```java
User u = em.find(User.class, 1L);
u.setNickname("新昵称");       // 只修改了 Java 对象
// 不需要显式调用 em.merge(u) 或 update
em.flush();                    // 自动生成 UPDATE SQL
```

持久化上下文在 flush 时对比实体快照，自动生成 UPDATE——这就是 Dirty Checking。

## Entity 生命周期

JPA 中每个实体有四种状态：

```
                  persist()
        NEW ─────────────────→ MANAGED
         ↑                      │   │
         │  find()/query        │   │ remove()
         │                      │   │
         │                      ↓   ↓
        ─────────────────→    REMOVED
         DETACHED ←── clear()/detach()/close()
                    ←── merge()
```

### 四种状态

| 状态 | 说明 | 数据库有对应行 | EntityManager 管理 |
|------|------|:---:|:---:|
| New（瞬时） | `new User()`，刚创建 | 否 | 否 |
| Managed（托管） | persist/find 之后 | 是 | 是 |
| Detached（游离） | em.clear/close 之后，或序列化后 | 是 | 否 |
| Removed（删除） | em.remove 之后 | 待删除 | 是 |

```java
// 状态转换演示
User user = new User();           // New
em.persist(user);                 // → Managed
em.detach(user);                  // → Detached
user = em.merge(user);            // → Managed（注意：merge 返回新的 Managed 对象）
em.remove(user);                  // → Removed
em.flush();                       // DELETE 发送到数据库
```

### merge vs persist

```java
// persist：把新实体变为 managed
User u = new User();
u.setUsername("test");
em.persist(u);     // INSERT 在 flush 时执行，u 变为 managed

// merge：把 detached 实体的属性复制到 managed 对象
User detached = new User();
detached.setId(1L);              // 数据库存在的 ID
detached.setNickname("updated");
User managed = em.merge(detached); // SELECT id=1 → managed 对象 → UPDATE managed 对象
System.out.println(detached == managed);  // false —— 不是同一个对象
```

核心区别：`persist` 不返回对象（原地修改），`merge` 返回新的 managed 对象（原对象仍是 detached）。

## 关联关系映射

### OneToOne

```java
@Entity
public class User {
    @Id private Long id;

    @OneToOne(cascade = CascadeType.ALL)
    @JoinColumn(name = "profile_id", unique = true)  // 外键在 User 表
    private UserProfile profile;
}

@Entity
public class UserProfile {
    @Id private Long id;

    @OneToOne(mappedBy = "profile")  // 由 User.profile 维护关联，Profile 表无外键
    private User user;
}
```

谁持有外键，谁是关联的维护方（owner）。`mappedBy` 方是"被维护方"，对它的修改不会触发外键更新。

### OneToMany / ManyToOne

```java
@Entity
public class Dept {
    @Id private Long id;
    private String name;

    @OneToMany(mappedBy = "dept", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Employee> employees = new ArrayList<>();
}

@Entity
public class Employee {
    @Id private Long id;
    private String name;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "dept_id")    // 外键在 Employee 表
    private Dept dept;
}
```

OneToMany 的默认 fetch 是 LAZY，ManyToOne 是 EAGER。**生产环境 ManyToOne 务必显式设为 LAZY**。

### ManyToMany

```java
@Entity
public class Student {
    @Id private Long id;
    private String name;

    @ManyToMany
    @JoinTable(
        name = "student_course",
        joinColumns = @JoinColumn(name = "student_id"),
        inverseJoinColumns = @JoinColumn(name = "course_id")
    )
    private Set<Course> courses = new HashSet<>();
}

@Entity
public class Course {
    @Id private Long id;
    private String name;

    @ManyToMany(mappedBy = "courses")  // 由 Student 维护
    private Set<Student> students = new HashSet<>();
}
```

### 双向关联的便利方法

双向关联时，需要在代码层面同时维护两边：

```java
public void addEmployee(Employee emp) {
    employees.add(emp);
    emp.setDept(this);   // 同时设置对方的引用
}

public void removeEmployee(Employee emp) {
    employees.remove(emp);
    emp.setDept(null);
}
```

## Cascade 与 Orphan Removal

### CascadeType

Cascade 定义对父实体的操作是否级联到关联的子实体：

```java
@OneToMany(mappedBy = "dept", cascade = CascadeType.ALL)
private List<Employee> employees;
```

| CascadeType | 效果 |
|-------------|------|
| PERSIST | 持久化父实体时，同时持久化子实体 |
| MERGE | 合并父实体时，同时合并子实体 |
| REMOVE | 删除父实体时，同时删除子实体 |
| REFRESH | 刷新父实体时，同时刷新子实体 |
| DETACH | 分离父实体时，同时分离子实体 |
| ALL | 以上全部 |

```java
Dept dept = new Dept();
dept.setName("研发部");

Employee emp1 = new Employee(); emp1.setName("张三");
Employee emp2 = new Employee(); emp2.setName("李四");
dept.addEmployee(emp1);
dept.addEmployee(emp2);

deptRepo.save(dept);   // 如果 CascadeType.PERSIST，emp1 和 emp2 也一起保存
```

### Orphan Removal

`orphanRemoval = true`：从集合中移除子实体时，自动删除数据库中对应的行。

```java
@OneToMany(mappedBy = "dept", cascade = CascadeType.ALL, orphanRemoval = true)
private List<Employee> employees;

// 使用
dept.getEmployees().remove(emp1);  // 从集合移除
deptRepo.save(dept);               // emp1 被 DELETE
```

CascadeType.REMOVE vs orphanRemoval：
- CascadeType.REMOVE：删除父实体时删除子实体
- orphanRemoval：从集合中移除子实体（脱离关联）时删除子实体——父实体还在，子实体被删

## Lazy Loading —— 延迟加载

```java
@ManyToOne(fetch = FetchType.LAZY)   // 访问时才加载
private Dept dept;

@OneToMany(fetch = FetchType.LAZY)   // 默认是 LAZY
private List<Employee> employees;

@ManyToMany(fetch = FetchType.LAZY)
private Set<Course> courses;
```

### LazyInitializationException

最经典的 JPA 踩坑点——延迟加载需要在事务内访问：

```java
// Controller
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) {
    return userRepo.findById(id).orElseThrow();
    // 事务在 Service 层就结束了
    // 返回的 User 变成 Detached，dept 是 Hibernate 代理
    // 前端序列化时访问 user.getDept().getName() → 抛 LazyInitializationException
}
```

解决方案：

```java
// 方案 1：JOIN FETCH —— 一次查出来
@Query("SELECT u FROM User u JOIN FETCH u.dept WHERE u.id = :id")
User findByIdWithDept(@Param("id") Long id);

// 方案 2：@EntityGraph —— 声明式
@EntityGraph(attributePaths = {"dept", "roles"})
@Query("SELECT u FROM User u WHERE u.id = :id")
User findByIdWithGraph(@Param("id") Long id);

// 方案 3：@Transactional 标记在 Controller（不推荐，违反分层）
// 方案 4：DTO 投影 —— 只查需要的字段（最佳实践）
@Query("SELECT new com.example.dto.UserDTO(u.id, u.username, d.name) " +
       "FROM User u JOIN u.dept d WHERE u.id = :id")
UserDTO findUserDTO(@Param("id") Long id);
```

## JPQL

JPQL（Jakarta Persistence Query Language）是面向对象的查询语言。它操作的是实体类和属性，不是表名和字段。

```java
// SQL: SELECT * FROM t_user WHERE age > 18
// JPQL:  SELECT u FROM User u WHERE u.age > 18

// 基本查询
TypedQuery<User> query = em.createQuery(
    "SELECT u FROM User u WHERE u.dept.name = :deptName ORDER BY u.createdAt DESC",
    User.class
);
query.setParameter("deptName", "研发部");
List<User> users = query.getResultList();

// JOIN
List<Object[]> result = em.createQuery(
    "SELECT u.username, d.name FROM User u JOIN u.dept d"
).getResultList();

// FETCH JOIN（解决 N+1）
List<User> users = em.createQuery(
    "SELECT DISTINCT u FROM User u JOIN FETCH u.dept JOIN FETCH u.roles"
).getResultList();

// 聚合
Long count = em.createQuery(
    "SELECT COUNT(u) FROM User u WHERE u.gender = :gender", Long.class
).setParameter("gender", Gender.MALE).getSingleResult();

// 更新/删除
em.createQuery("UPDATE User u SET u.status = 0 WHERE u.lastLoginAt < :date")
  .setParameter("date", LocalDateTime.now().minusYears(1))
  .executeUpdate();
```

### JPQL vs SQL

| | JPQL | SQL |
|--|------|-----|
| 操作对象 | 实体类和属性 | 表和列 |
| 查询结果 | 实体对象 | 原始数据 |
| 可移植性 | 跨数据库 | 绑定特定数据库 |
| 功能 | 无法使用数据库特有函数 | 全部 SQL 功能 |
| JOIN 语法 | `u.dept.name`（点号遍历） | `JOIN dept ON ...` |

## Criteria API

Criteria API 用 Java 代码构建查询——类型安全、可动态拼条件：

```java
CriteriaBuilder cb = em.getCriteriaBuilder();

// 1. 创建查询
CriteriaQuery<User> cq = cb.createQuery(User.class);
Root<User> root = cq.from(User.class);

// 2. 构建条件
List<Predicate> predicates = new ArrayList<>();
if (name != null) {
    predicates.add(cb.like(root.get("username"), "%" + name + "%"));
}
if (minAge != null) {
    predicates.add(cb.greaterThan(root.get("age"), minAge));
}
if (deptId != null) {
    predicates.add(cb.equal(root.get("dept").get("id"), deptId));
}

// 3. 组装查询
cq.where(predicates.toArray(new Predicate[0]));
cq.orderBy(cb.desc(root.get("createdAt")));

// 4. 执行
TypedQuery<User> query = em.createQuery(cq);
query.setFirstResult(0).setMaxResults(20);
List<User> users = query.getResultList();
```

优点：类型安全（编译期检查），IDE 提示，无拼字符串风险。
缺点：代码冗长，可读性不如 JPQL。

## Specification —— 动态查询

Spring Data JPA 提供的 Specification 接口，基于 Criteria API 封装，是动态查询最实用的方式：

```java
public interface UserRepo extends JpaRepository<User, Long>,
                                  JpaSpecificationExecutor<User> {
}

// 构建 Specification
public class UserSpec {

    public static Specification<User> hasNameLike(String name) {
        return (root, query, cb) ->
            name == null ? null : cb.like(root.get("username"), "%" + name + "%");
    }

    public static Specification<User> hasAgeGreaterThan(Integer age) {
        return (root, query, cb) ->
            age == null ? null : cb.greaterThan(root.get("age"), age);
    }

    public static Specification<User> belongsToDept(Long deptId) {
        return (root, query, cb) ->
            deptId == null ? null : cb.equal(root.get("dept").get("id"), deptId);
    }
}

// 组合使用
Specification<User> spec = Specification
    .where(UserSpec.hasNameLike(keyword))
    .and(UserSpec.hasAgeGreaterThan(18))
    .and(UserSpec.belongsToDept(deptId));

Page<User> page = userRepo.findAll(spec, PageRequest.of(0, 20, Sort.by("createdAt").descending()));
```

## 应用场景实战

### 场景一：树形结构（部门树）

```java
@Entity
public class Dept {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_id")
    private Dept parent;

    @OneToMany(mappedBy = "parent", cascade = CascadeType.ALL)
    @OrderBy("id ASC")
    private List<Dept> children = new ArrayList<>();
}

// 查整棵树
@Query("SELECT d FROM Dept d LEFT JOIN FETCH d.children WHERE d.parent IS NULL")
List<Dept> findRootDepts();
```

### 场景二：软删除 + 审计字段基类

```java
@MappedSuperclass
@Getter @Setter
public abstract class BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;

    @Column(nullable = false)
    private Boolean deleted = false;
}

@Entity
public class User extends BaseEntity {
    // 只写业务字段
    private String username;
}

// Repository 中过滤软删除
@Query("SELECT u FROM User u WHERE u.deleted = false")
List<User> findAllActive();
```

### 场景三：一对多分页避免 N+1

```java
// 问题：查询所有部门及其员工 → 每个部门触发一次 SELECT 查员工
List<Dept> depts = deptRepo.findAll();            // 1 条 SQL
for (Dept d : depts) {
    System.out.println(d.getEmployees().size());  // N 条 SQL
}

// 解决 1：JOIN FETCH（但有分页时会出现内存分页警告）
@Query("SELECT DISTINCT d FROM Dept d LEFT JOIN FETCH d.employees")
List<Dept> findAllWithEmployees();

// 解决 2：BatchSize —— 批量加载（推荐）
@Entity
public class Dept {
    @OneToMany(mappedBy = "dept")
    @BatchSize(size = 100)   // 一次加载 100 个部门的员工
    private List<Employee> employees;
}
// 生成 SQL: SELECT * FROM employee WHERE dept_id IN (?,?,?,...)
```

## 最佳实践与踩坑记录

**实践 1：ManyToOne 显式设为 LAZY**

JPA 规范中 ManyToOne 默认 EAGER——这是常见的性能陷阱，隐式地触发 N+1 查询。所有 `@ManyToOne` 都显式加 `fetch = FetchType.LAZY`。

**实践 2：双向关联维护便利方法**

```java
public void addEmployee(Employee emp) {
    employees.add(emp);
    emp.setDept(this);
}
```
不写便利方法是"只维护了一边"的 bug 来源。

**实践 3：@Enumerated(EnumType.STRING)**

永远用 STRING 而非 ORDINAL。ORDINAL 存的是序号(0,1,2)，枚举顺序一变数据全乱。

**实践 4：DTO 投影优于返回 Entity**

Controller 不要直接返回 Entity——会导致懒加载异常、暴露敏感字段、序列化循环引用。用 DTO 投影。

**踩坑 1**：`toString()` 导致循环引用 StackOverflow。User 和 Dept 双向关联 → `toString()` 互相调用 → 栈溢出。用 `@ToString.Exclude`（Lombok）排除关联字段。

**踩坑 2**：`merge` 的参数对象仍是 detached。

```java
User detached = userRepo.findById(1L).orElseThrow();
em.clear();                     // 使所有实体 detached
User merged = em.merge(detached); // merged 是新的 managed 对象
detached.setUsername("new");    // 无效——detached 对象不受管理
```

**踩坑 3**：`@OneToMany` 集合用 `Set` 而非 `List`。List 在同一事务内添加多个子实体时可能违反唯一约束，Set 天然去重。如果需要排序，用 `@OrderBy` 或 `@OrderColumn`。

**踩坑 4**：`CascadeType.ALL` 不意味着 `orphanRemoval = true`。删除父实体时级联删除子实体是 ALL 中 REMOVE 的效果。从集合中移除子实体是 `orphanRemoval`，两者独立。
