---
title: Spring Data
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring-data, repository, crudrepository, pagingandsortingrepository, jparepository, query-method, projection, auditing]
---

# Spring Data

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [Spring Data 模块全景](#spring-data-模块全景)
- [Repository 接口体系](#repository-接口体系)
- [Query Method 派生查询](#query-method-派生查询)
- [@Query 注解查询](#query-注解查询)
- [投影（Projection）](#投影projection)
- [审计（Auditing）](#审计auditing)
- [Query by Example](#query-by-example)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring Data 是 Spring 生态的数据访问层统一抽象。它的核心使命是：**让不同数据存储（JPA、Redis、MongoDB、Elasticsearch 等）的数据访问方式一致**。

```text
Spring Data 解决的问题：
1. 每个数据存储都要写大量样板 CRUD 代码
2. 不同存储的 API 风格不一致，学习成本高
3. 分页、排序、审计等通用功能重复实现

Spring Data 的核心价值：
1. Repository 抽象 —— 统一的数据访问接口
2. 方法名派生查询 —— 自动从方法名生成查询
3. 分页排序 —— 统一的分页排序支持
4. 审计 —— 自动填充创建时间、创建人等字段
```

## Spring Data 模块全景

```text
Spring Data Commons          —— 通用抽象（Repository、分页、审计）
├── Spring Data JPA          —— 关系数据库（JPA/Hibernate）
├── Spring Data Redis        —— Redis
├── Spring Data MongoDB      —— MongoDB
├── Spring Data Elasticsearch —— Elasticsearch
├── Spring Data JDBC         —— 轻量级 JDBC
├── Spring Data Cassandra    —— Cassandra
└── Spring Data Neo4j        —— 图数据库

核心：Spring Data Commons 定义统一的 Repository 抽象，
各模块基于它提供存储特定的实现。
```

所有模块共享同一套 Repository 编程模型——学会一个，其他都类似。

## Repository 接口体系

Spring Data 的 Repository 接口层级：

```text
Repository<T, ID>                         —— 标记接口，无方法
    ├── CrudRepository<T, ID>              —— 增删改查
    │       └── PagingAndSortingRepository<T, ID> —— 分页排序
    │               └── JpaRepository<T, ID>      —— JPA 增强（JPA 模块特有）
    └── ListCrudRepository<T, ID>          —— 返回 List 的 CRUD（Spring Data 3.0+）
```

### Repository —— 标记接口

```java
// 空接口，只是标记类型
public interface Repository<T, ID> {}
```

### CrudRepository —— 基础 CRUD

```java
public interface CrudRepository<T, ID> extends Repository<T, ID> {
    <S extends T> S save(S entity);              // 保存（新增或更新）
    <S extends T> Iterable<S> saveAll(Iterable<S> entities);
    Optional<T> findById(ID id);                 // 按 ID 查询
    boolean existsById(ID id);
    Iterable<T> findAll();                       // 查询所有
    long count();                                // 计数
    void deleteById(ID id);                      // 按 ID 删除
    void delete(T entity);
    void deleteAll(Iterable<? extends T> entities);
    void deleteAll();                            // 清空
}
```

### PagingAndSortingRepository —— 分页排序

```java
public interface PagingAndSortingRepository<T, ID> extends CrudRepository<T, ID> {
    Iterable<T> findAll(Sort sort);              // 排序
    Page<T> findAll(Pageable pageable);          // 分页
}
```

### JpaRepository —— JPA 增强

```java
public interface JpaRepository<T, ID> extends PagingAndSortingRepository<T, ID> {
    List<T> findAll();                           // 返回 List（覆盖父接口的 Iterable）
    void flush();                                // 强制刷写
    <S extends T> S saveAndFlush(S entity);
    void deleteAllInBatch();                     // 批量删除
    // ... 更多 JPA 特有方法
}
```

### 定义自己的 Repository

```java
// 继承 JpaRepository，自动获得所有 CRUD + 分页能力
public interface UserRepository extends JpaRepository<User, Long> {
    // 只需声明自定义查询方法，实现由 Spring Data 自动生成
}
```

```java
// 使用
@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    public User save(User user) {
        return userRepository.save(user);           // 自动实现
    }

    public User findById(Long id) {
        return userRepository.findById(id).orElse(null);  // 自动实现
    }

    public Page<User> findByPage(int page, int size) {
        return userRepository.findAll(PageRequest.of(page, size));  // 分页
    }
}
```

**关键**：Repository 接口只需要声明，不需要实现类。Spring Data 通过动态代理在运行时自动生成实现。

### 分页与排序

```java
// 排序
Sort sort = Sort.by(Sort.Direction.DESC, "createdAt");
List<User> users = userRepository.findAll(sort);

// 多字段排序
Sort sort = Sort.by(
    Sort.Order.desc("createdAt"),
    Sort.Order.asc("username")
);

// 分页
Pageable pageable = PageRequest.of(0, 20, sort);  // 第 0 页，每页 20 条，按 sort 排序
Page<User> page = userRepository.findAll(pageable);

// Page 对象
page.getContent();        // 当前页数据
page.getTotalElements();  // 总记录数
page.getTotalPages();     // 总页数
page.getNumber();         // 当前页码
page.getSize();           // 每页大小
page.hasNext();           // 是否有下一页
```

## Query Method 派生查询

Spring Data 最强大的特性：**根据方法名自动生成查询**。

### 方法名解析规则

```java
public interface UserRepository extends JpaRepository<User, Long> {

    // findBy + 属性名
    List<User> findByUsername(String username);

    // And / Or 组合
    List<User> findByUsernameAndAge(String username, int age);
    List<User> findByUsernameOrEmail(String username, String email);

    // 比较操作符
    List<User> findByAgeGreaterThan(int age);
    List<User> findByAgeLessThan(int age);
    List<User> findByAgeBetween(int min, int max);
    List<User> findByCreatedAtAfter(LocalDateTime time);
    List<User> findByCreatedAtBefore(LocalDateTime time);

    // 模糊查询
    List<User> findByUsernameLike(String pattern);       // like '%xx%'
    List<User> findByUsernameStartingWith(String prefix); // like 'xx%'
    List<User> findByUsernameEndingWith(String suffix);   // like '%xx'
    List<User> findByUsernameContaining(String keyword);  // like '%xx%'

    // 空值判断
    List<User> findByEmailIsNull();
    List<User> findByEmailIsNotNull();

    // In / NotIn
    List<User> findByAgeIn(Collection<Integer> ages);

    // 忽略大小写
    List<User> findByUsernameIgnoreCase(String username);

    // 排序（方法名末尾 + OrderBy）
    List<User> findByAgeGreaterThanOrderByCreatedAtDesc(int age);

    // 取前 N 条（Top/First）
    List<User> findTop10ByOrderByCreatedAtDesc();
    User findFirstByOrderByCreatedAtAsc();
}
```

### 常用查询关键字

| 关键字 | 示例 | 生成条件 |
|--------|------|---------|
| And / Or | findByXAndY | x = ? and y = ? |
| Is / Equals | findByUsernameIs | username = ? |
| Between | findByAgeBetween | age between ? and ? |
| LessThan / GreaterThan | findByAgeGreaterThan | age > ? |
| Like | findByUsernameLike | username like ? |
| StartingWith / EndingWith / Containing | findByXContaining | x like %?% |
| In / NotIn | findByAgeIn | age in (?) |
| IsNull / IsNotNull | findByEmailIsNull | email is null |
| OrderBy | findByXOrderByYDesc | order by y desc |
| Top / First | findTop10By | limit 10 |
| Exists | existsByUsername | exists (select ...) |
| Count | countByAge | count(...) |
| Delete | deleteByUsername | delete where username=? |

### 方法名派生查询的局限

```text
优点：不用写 SQL，方法名即查询，简洁直观
局限：
1. 方法名过长可读性差（findByUsernameAndAgeGreaterThanAndStatusOrderBy...）
2. 复杂查询（多表关联、子查询、聚合）表达不了
3. 属性名变更时方法名要同步改

复杂查询用 @Query 注解，简单查询用派生查询
```

## @Query 注解查询

当方法名派生查询表达不了时，用 @Query 直接写查询语句。

### JPA 的 @Query（JPQL）

```java
public interface UserRepository extends JpaRepository<User, Long> {

    // JPQL 查询
    @Query("select u from User u where u.age > ?1 and u.status = ?2")
    List<User> findAdults(int age, String status);

    // 命名参数
    @Query("select u from User u where u.username = :username")
    User findByUsername(@Param("username") String username);

    // 原生 SQL
    @Query(value = "select * from user where age > ?1", nativeQuery = true)
    List<User> findAdultsNative(int age);

    // 更新操作
    @Modifying
    @Query("update User u set u.status = :status where u.id = :id")
    @Transactional  // 修改操作需要事务
    int updateStatus(@Param("id") Long id, @Param("status") String status);
}
```

### 位置参数 vs 命名参数

```java
// 位置参数（?1、?2）
@Query("select u from User u where u.age > ?1 and u.age < ?2")
List<User> findByAgeBetween(int min, int max);

// 命名参数（:name，推荐，可读性好）
@Query("select u from User u where u.username = :username")
User findByUsername(@Param("username") String username);
```

### @Modifying 修改操作

```java
// 修改/删除需要 @Modifying + @Transactional
@Modifying
@Query("delete from User u where u.status = :status")
@Transactional
int deleteByStatus(@Param("status") String status);

@Modifying
@Query("update User u set u.loginCount = u.loginCount + 1 where u.id = :id")
@Transactional
int incrementLoginCount(@Param("id") Long id);
```

## 投影（Projection）

投影用于查询部分字段，而不是整个实体。

### 接口投影

```java
// 只查询 username 和 email 两个字段
public interface UserSummary {
    String getUsername();
    String getEmail();
}

public interface UserRepository extends JpaRepository<User, Long> {
    List<UserSummary> findByAgeGreaterThan(int age);
}
```

### 闭投影（只投影指定的字段）

```java
public interface UserSummary {
    @Value("#{target.username + ' (' + target.email + ')'}")
    String getFullInfo();   // 组合字段
}
```

### 类投影（DTO）

```java
public record UserDTO(String username, String email) {}

public interface UserRepository extends JpaRepository<User, Long> {
    List<UserDTO> findByAgeGreaterThan(int age);  // 自动映射到 DTO
}
```

### 动态投影

```java
// 同一查询方法，根据传入的投影类型返回不同结果
public interface UserRepository extends JpaRepository<User, Long> {
    <T> List<T> findByUsername(String username, Class<T> type);
}

// 使用
List<UserSummary> summaries = userRepository.findByUsername("zhangsan", UserSummary.class);
List<User> fullUsers = userRepository.findByUsername("zhangsan", User.class);
```

投影的价值：只查需要的字段，减少数据传输量，尤其适合列表页。

## 审计（Auditing）

Spring Data 审计自动填充创建时间、修改时间、创建人等审计字段。

### 启用审计

```java
@Configuration
@EnableJpaAuditing  // 启用审计
public class JpaConfig { }
```

### 实体添加审计字段

```java
@EntityListeners(AuditingEntityListener.class)
@Entity
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreatedDate                    // 创建时间（自动填充）
    private LocalDateTime createdAt;

    @LastModifiedDate               // 修改时间（自动填充）
    private LocalDateTime updatedAt;

    @CreatedBy                      // 创建人（需配置 AuditorAware）
    private String createdBy;

    @LastModifiedBy                 // 修改人
    private String updatedBy;
}
```

### 配置创建人/修改人

```java
@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorProvider")
public class JpaConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        // 从安全上下文获取当前用户
        return () -> Optional.ofNullable(
            SecurityContextHolder.getContext().getAuthentication())
            .map(Authentication::getName)
            .or(() -> Optional.of("system"));
    }
}
```

审计字段注解：

| 注解 | 含义 |
|------|------|
| @CreatedDate | 创建时间 |
| @LastModifiedDate | 最后修改时间 |
| @CreatedBy | 创建人 |
| @LastModifiedBy | 最后修改人 |

## Query by Example

Query by Example（QBE）用实体实例作为查询条件，适合简单、动态的查询。

```java
public interface UserRepository extends JpaRepository<User, Long>,
        QueryByExampleExecutor<User> { }

// 使用
User probe = new User();
probe.setStatus("ACTIVE");  // 只设置要匹配的字段

Example<User> example = Example.of(probe);
List<User> users = userRepository.findAll(example);
```

```java
// 更精细的控制
ExampleMatcher matcher = ExampleMatcher.matching()
    .withIgnorePaths("id", "createdAt")          // 忽略某些字段
    .withIgnoreNullValues()                      // 忽略 null 字段
    .withStringMatcher(ExampleMatcher.StringMatcher.CONTAINING)  // 字符串模糊匹配
    .withIgnoreCase();                           // 忽略大小写

Example<User> example = Example.of(probe, matcher);
```

QBE 适用场景：管理后台的简单筛选查询。复杂查询还是要用派生查询或 @Query。

## 应用场景实战

### 场景 1：完整的分页查询接口

```java
public interface UserRepository extends JpaRepository<User, Long> {

    // 分页 + 条件查询
    Page<User> findByStatus(String status, Pageable pageable);

    // 分页 + 模糊查询
    Page<User> findByUsernameContaining(String keyword, Pageable pageable);
}

@Service
public class UserService {

    public Page<User> search(String keyword, String status, int page, int size) {
        Sort sort = Sort.by(Sort.Direction.DESC, "createdAt");
        Pageable pageable = PageRequest.of(page, size, sort);

        if (StringUtils.hasText(keyword)) {
            return userRepository.findByUsernameContaining(keyword, pageable);
        }
        if (StringUtils.hasText(status)) {
            return userRepository.findByStatus(status, pageable);
        }
        return userRepository.findAll(pageable);
    }
}
```

### 场景 2：审计字段自动填充

```java
@Entity
@EntityListeners(AuditingEntityListener.class)
public class Order {

    @Id
    @GeneratedValue
    private Long id;

    private String orderNo;

    @CreatedDate
    private LocalDateTime createdAt;   // 保存时自动填充

    @LastModifiedDate
    private LocalDateTime updatedAt;   // 更新时自动填充
}

// 保存时无需手动设置审计字段
Order order = new Order();
order.setOrderNo("ORD001");
orderRepository.save(order);  // createdAt/updatedAt 自动填充
```

### 场景 3：投影优化列表查询

```java
// 列表页只查必要字段，不加载大字段
public interface OrderListItem {
    String getOrderNo();
    BigDecimal getAmount();
    String getStatus();
}

public interface OrderRepository extends JpaRepository<Order, Long> {
    List<OrderListItem> findTop100ByOrderByCreatedAtDesc();
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **简单查询用派生查询，复杂查询用 @Query**。方法名超过 4 个条件就考虑 @Query，保持可读性。

2. **修改操作必须加 @Modifying + @Transactional**。否则会报异常或修改不生效。

3. **列表查询用投影**。减少字段传输，提升性能。

4. **分页查询用 Pageable 参数**。不要 `findAll()` 全查再内存分页。

5. **审计字段统一用 @CreatedDate/@LastModifiedDate**。不要手动设置时间戳。

### 踩坑记录

**坑 1：方法名派生查询的属性名写错**

```java
List<User> findByUserName(String username);  // 属性是 username，写成了 userName
// 启动时报 No property 'userName' found for type User
```

派生查询严格依赖属性名，属性名写错会在启动时抛异常（好事，能提前发现）。

**坑 2：@Modifying 缺 @Transactional**

```java
@Modifying
@Query("update User u set u.status = ?1 where u.id = ?2")
int updateStatus(String status, Long id);  // 缺 @Transactional
// 报 TransactionRequiredException
```

修改操作必须在事务中执行，加 @Transactional（通常加在 Service 层）。

**坑 3：findById 返回 Optional 直接 get()**

```java
User user = userRepository.findById(id).get();  // 不存在时 NoSuchElementException
```

用 `orElse(null)` 或 `orElseThrow(() -> new NotFoundException())` 处理空值。

**坑 4：派生查询方法名过长**

```java
List<User> findByUsernameAndAgeGreaterThanAndStatusAndCreatedAtAfterOrderByCreatedAtDesc(...);
// 可读性极差，应该用 @Query
```

超过 3-4 个条件用 @Query，可读性优先。

**坑 5：N+1 查询问题**

```java
// 查询用户列表，每个用户又懒加载查询其订单
List<User> users = userRepository.findAll();
for (User user : users) {
    user.getOrders();  // 每个用户触发一次查询
}
// 100 个用户 = 101 次查询
```

解法：用 @EntityGraph 或 JPQL join fetch 预加载关联数据。

**坑 6：审计不生效**

```java
@Entity
public class User {
    @CreatedDate
    private LocalDateTime createdAt;  // 缺少 @EntityListeners(AuditingEntityListener.class)
}
```

实体类要加 `@EntityListeners(AuditingEntityListener.class)`，配置类要加 `@EnableJpaAuditing`，两者缺一不可。
