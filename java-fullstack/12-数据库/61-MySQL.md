---
title: MySQL
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [mysql, innodb, mvcc, redo-log, undo-log, binlog, buffer-pool, index, b+tree, explain, sql-optimization]
---

# MySQL

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [MySQL 安装](#mysql-安装)
- [MySQL 架构](#mysql-架构)
- [InnoDB 存储引擎](#innodb-存储引擎)
- [Buffer Pool](#buffer-pool)
- [Redo Log / Undo Log / Binlog](#redo-log--undo-log--binlog)
- [MVCC](#mvcc)
- [索引详解](#索引详解)
- [B+Tree 索引](#btree-索引)
- [EXPLAIN 执行计划](#explain-执行计划)
- [SQL 优化](#sql-优化)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

MySQL 是互联网公司使用最广泛的开源关系型数据库。核心存储引擎是 InnoDB（5.5.5 起成为默认引擎），支持事务、行级锁、MVCC、崩溃恢复。

## MySQL 安装

### Linux（Ubuntu/Debian）

```bash
# 安装
sudo apt update
sudo apt install mysql-server

# 安全配置
sudo mysql_secure_installation
# 设置 root 密码 → 移除匿名用户 → 禁止远程 root → 删除 test 库

# 启动
sudo systemctl start mysql
sudo systemctl enable mysql
```

### Docker 安装（推荐开发环境）

```bash
docker run -d \
  --name mysql8 \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -v mysql_data:/var/lib/mysql \
  mysql:8.0
```

### 创建用户和数据库

```sql
-- 创建数据库
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'app'@'%' IDENTIFIED BY 'app123';

-- 授权
GRANT ALL PRIVILEGES ON mydb.* TO 'app'@'%';
FLUSH PRIVILEGES;
```

## MySQL 架构

MySQL 采用分层架构：

```
┌──────────────────────────────────────────────┐
│              客户端 / 连接器                     │
│         (认证、权限校验、连接管理)                  │
├──────────────────────────────────────────────┤
│              SQL 层（Server 层）                │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │
│  │  解析器  │→ │ 优化器   │→ │  执行器      │  │
│  └─────────┘  └─────────┘  └─────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 查询缓存  │  │ 内置函数  │  │  binlog  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├──────────────────────────────────────────────┤
│              存储引擎层（可插拔）                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  InnoDB  │  │  MyISAM  │  │  Memory  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├──────────────────────────────────────────────┤
│               文件系统层                        │
│       (数据文件、日志文件、配置文件)               │
└──────────────────────────────────────────────┘
```

一条 SELECT 的执行路径：

1. **连接器**：建立连接、验证身份、检查权限
2. **查询缓存**（8.0 已移除）：命中直接返回
3. **解析器**：词法分析（识别关键字和标识符）→ 语法分析（生成解析树）
4. **优化器**：选择索引、决定 JOIN 顺序、生成执行计划
5. **执行器**：调用存储引擎 API 读取数据并返回
6. **存储引擎**：实际读写磁盘数据

## InnoDB 存储引擎

### InnoDB vs MyISAM

| 特性 | InnoDB | MyISAM |
|------|--------|--------|
| 事务 | 支持 | 不支持 |
| 行级锁 | 支持 | 不支持（表锁） |
| 外键 | 支持 | 不支持 |
| 崩溃恢复 | 支持（Redo Log） | 不支持 |
| MVCC | 支持 | 不支持 |
| 全文索引 | 5.6+ 支持 | 支持 |
| 压缩 | 支持 | 支持 |
| 适用场景 | 高并发 OLTP | 只读/日志/数据仓库 |

### InnoDB 磁盘结构

```
表空间（Tablespace）
├── 系统表空间（ibdata1）
│   ├── InnoDB 数据字典（元数据）
│   ├── Double Write Buffer（防止页部分写）
│   ├── Change Buffer（缓存非唯一二级索引的变更）
│   └── Undo 表空间（5.6+ 可独立）
├── 独立表空间（*.ibd，innodb_file_per_table=ON）
│   └── 每个表一个 .ibd 文件，存数据和索引
├── Redo Log（ib_logfile0, ib_logfile1）
│   └── 循环写，用于崩溃恢复
└── 临时表空间（ibtmp1）
```

### InnoDB 内存结构

核心是 Buffer Pool（缓冲池），后面单独讲。此外还有 Change Buffer、Adaptive Hash Index、Log Buffer。

## Buffer Pool

Buffer Pool 是 InnoDB 最重要的内存结构——缓存数据页和索引页，减少磁盘 IO。

### 基本参数

```sql
-- 默认 128MB，生产环境建议设为物理内存的 50%-80%
SET GLOBAL innodb_buffer_pool_size = 4G;

-- 查看命中率
SHOW STATUS LIKE 'Innodb_buffer_pool_read%';
-- Innodb_buffer_pool_read_requests: 总读取请求
-- Innodb_buffer_pool_reads:        从磁盘读取的次数
-- 命中率 = 1 - (reads / read_requests)
```

### LRU 链表

Buffer Pool 用改进的 LRU 管理数据页：

```
│←── 新生代（Young，5/8）──│←── 老年代（Old，3/8）──│
  热点数据                     冷数据

新页先插入 Old 区头部，再次被访问时移到 Young 区
```

这样避免了全表扫描把热点数据踢出——全表扫描的页在 Old 区，很快被淘汰。

### 脏页刷盘

Buffer Pool 中被修改但未写入磁盘的页叫脏页。刷盘时机：

- Redo Log 写满时强制刷盘
- Buffer Pool 空间不足时淘汰脏页
- MySQL 空闲时
- 正常关闭时

## Redo Log / Undo Log / Binlog

### Redo Log（重做日志）

InnoDB 的事务日志，保证持久性。

```
WAL（Write-Ahead Logging）：先写日志，再写数据

UPDATE user SET name='李四' WHERE id=1;

1. 从磁盘读取 id=1 的数据页到 Buffer Pool
2. 修改数据页（Buffer Pool 中的脏页）
3. 写 Redo Log（记录"在页 X 偏移 Y 处把张三改为李四"）
4. 事务提交，Redo Log 刷盘
5. 后续某个时间点，脏页异步刷回磁盘
```

Redo Log 是循环写的固定大小文件（默认两个，每个 48MB），有 write pos（写位置）和 checkpoint（已刷盘位置）。如果 write pos 追上 checkpoint，需要暂停等待刷盘。

崩溃恢复：重启时重放 Redo Log 中 checkpoint 之后的记录，把未刷盘的修改补上。

参数：

```sql
SET GLOBAL innodb_log_file_size = 512M;    -- 单文件大小
SET GLOBAL innodb_log_files_in_group = 3;  -- 文件数量
SET GLOBAL innodb_flush_log_at_trx_commit = 1;  -- 每次提交刷盘（最安全）
```

`innodb_flush_log_at_trx_commit` 的值：

- 0：每秒刷一次（性能最好，可能丢 1 秒数据）
- 1：每次提交刷盘（默认，最安全）
- 2：每次提交写 OS 缓存，每秒刷盘（折中）

### Undo Log（回滚日志）

记录修改前的数据，用于回滚和 MVCC。事务回滚时通过 Undo Log 将数据恢复到修改前状态。

```sql
-- 执行 UPDATE 时：
-- Undo Log 记录：id=1 这行，name 旧值是 '张三'

-- 事务回滚时，用 Undo Log 还原
ROLLBACK;   -- name 恢复为 '张三'
```

Undo Log 存储在 Undo 表空间（ibdata1 或独立的 undo 文件），不在 Redo Log 中。Undo Log 本身也受 Redo Log 保护。

### Binlog（归档日志）

MySQL Server 层的日志，与存储引擎无关。记录所有修改数据库的语句（逻辑日志），用于主从复制和数据恢复。

```sql
STATEMENT 格式：记录 SQL 语句本身
ROW 格式：    记录每行数据的变化（推荐，精确）
MIXED 格式：  混合使用
```

参数：

```sql
SET GLOBAL log_bin = ON;                          -- 开启 binlog
SET GLOBAL binlog_format = ROW;                   -- ROW 格式
SET GLOBAL sync_binlog = 1;                       -- 每次提交刷盘
SET GLOBAL expire_logs_days = 7;                  -- 7 天后自动清理
```

### 两阶段提交

一个 UPDATE 涉及 Binlog + Redo Log，必须保证两者一致：

```
1. Prepare 阶段：写 Redo Log（状态为 prepare）
2. 写 Binlog
3. Commit 阶段：Redo Log 状态改为 commit
```

崩溃恢复时：
- Redo Log 是 prepare 但没有对应 Binlog → 回滚
- Redo Log 是 prepare 且有对应 Binlog → 提交

这保证了主从数据一致——如果已写 Binlog 就必须提交，否则从库会多数据。

## MVCC

MVCC（Multi-Version Concurrency Control）是 InnoDB 实现非锁定一致性读的机制——读不阻塞写，写不阻塞读。

### 核心概念

**隐藏列**：每行数据有三个隐藏列：

- `DB_TRX_ID`（6 字节）：最近修改该行的事务 ID
- `DB_ROLL_PTR`（7 字节）：指向 Undo Log 中旧版本数据的指针（回滚指针）
- `DB_ROW_ID`（6 字节）：行 ID（没有主键时自动生成）

**Read View**：快照读时创建的数据快照，包含：
- `m_ids`：当前活跃事务 ID 列表
- `min_trx_id`：活跃事务中最小 ID
- `max_trx_id`：下一个要分配的事务 ID
- `creator_trx_id`：创建 Read View 的事务 ID

### 可见性判断

对于数据行版本，如果 `trx_id`：

1. `== creator_trx_id` → 可见（自己的修改）
2. `< min_trx_id` → 可见（事务已提交）
3. `>= max_trx_id` → 不可见（在 Read View 之后创建）
4. `min_trx_id <= trx_id < max_trx_id` → 如果 `trx_id` 在 `m_ids` 中则不可见（活跃但未提交），否则可见

不可见时，通过回滚指针沿着 Undo Log 链往前找旧版本，直到找到可见版本。

### 当前读 vs 快照读

```sql
-- 快照读（普通 SELECT）：读 MVCC 快照，不加锁
SELECT * FROM user WHERE id = 1;

-- 当前读：读最新已提交版本，加锁
SELECT * FROM user WHERE id = 1 FOR UPDATE;    -- 排他锁
SELECT * FROM user WHERE id = 1 LOCK IN SHARE MODE;  -- 共享锁（8.0+ 改为 FOR SHARE）
UPDATE user SET name = 'x' WHERE id = 1;       -- 排他锁
DELETE FROM user WHERE id = 1;                 -- 排他锁
```

## 索引详解

### 聚簇索引 vs 非聚簇索引（二级索引）

**聚簇索引（Clustered Index）**：数据行按主键顺序物理存储。主键就是聚簇索引键，叶子节点存整行数据。

```
聚簇索引的 B+Tree：
         [1-100]
        /       \
    [1-50]      [51-100]
    /    \       /     \
  [行1] [行2] [行50] [行51]
```

**二级索引（Secondary Index）**：非主键索引。叶子节点存索引列 + 主键值。

```
二级索引的 B+Tree（以 name 列为例）：
       [A-M]
      /     \
  [A-G]     [H-M]
  /    \     /    \
[Alice,1][Bob,2][Mary,50][Mike,51]
```

**回表**：二级索引找到主键后，再去聚簇索引查完整行。

```
SELECT * FROM user WHERE name = 'Alice';
1. 走 name 索引，定位到 (Alice, id=1)
2. 拿 id=1 去聚簇索引查完整行 ← 这就是回表
```

### 覆盖索引

如果查询的所有列都在索引中，不需要回表：

```sql
-- 有索引 idx_name_age(name, age)
-- 覆盖索引：无需回表
SELECT name, age FROM user WHERE name = 'Alice';

-- 非覆盖索引：需要回表取 email
SELECT name, age, email FROM user WHERE name = 'Alice';
```

EXPLAIN 中 Extra 列显示 `Using index` 表示走了覆盖索引。

### 最左匹配原则

复合索引按定义的列顺序匹配。例如 `INDEX(a, b, c)`：

```sql
WHERE a = 1              -- 走索引（匹配 a）
WHERE a = 1 AND b = 2    -- 走索引（匹配 a + b）
WHERE a = 1 AND c = 3    -- 走索引（匹配 a，c 用不上）
WHERE b = 2              -- 不走索引（跳过了 a）
WHERE a = 1 AND b > 2    -- a 精确 + b 范围，c 用不上
```

范围查询（>、<、BETWEEN、LIKE 'xxx%'）会中断后续列的匹配。

### 索引下推（ICP，Index Condition Pushdown）

MySQL 5.6+ 优化。将部分 WHERE 条件下推到存储引擎层，在索引层面过滤，减少回表次数。

```sql
-- 有索引 idx(name, age)
SELECT * FROM user WHERE name LIKE '张%' AND age = 20;

-- 无 ICP：name 走索引，把所有 "张%" 的行都回表，再过滤 age=20
-- 有 ICP：在索引中直接过滤 age=20，只回表满足两条件的行
```

## B+Tree 索引

InnoDB 使用 B+Tree 作为索引结构。为什么不用其他数据结构？

**Hash**：等值查询 O(1)，但不支持范围查询和排序。Memory 引擎支持 Hash 索引，InnoDB 有 Adaptive Hash Index（自动创建）。

**二叉树 / 红黑树**：树太高，磁盘 IO 次数多。100 万数据，红黑树高度约 20，一次查询 20 次磁盘 IO。

**B-Tree**：节点存数据，叶子节点无链表，范围查询需要中序遍历。

**B+Tree**：

```
                    [50 | 100]               ← 非叶子节点（只存键，不存数据）
                   /     |      \
          [10|20|30]  [60|70|80]  [110|120]  ← 内节点
          / |  |  \    / |  |  \    /  |   \
        [1][10][20][30][50][60][70][80][100][110]  ← 叶子节点（存数据，双向链表）
```

优势：
- 所有数据在叶子节点，查询效率稳定 O(log n)
- 叶子节点是双向链表，范围查询只需找到起点然后沿链表遍历
- 非叶子节点只存键，一个节点能存更多键 → 树更矮 → 磁盘 IO 更少

一个 B+Tree 节点默认 16KB（一个数据页），假设键 8 字节 + 指针 6 字节 = 14 字节，一个节点约存 1170 个键。三层 B+Tree 可存约 1170^2 * 16 ≈ 2000 万条记录。实际查询只需 2-3 次磁盘 IO（根节点常驻内存后更少）。

### 索引失效场景

```sql
-- 1. 对索引列用函数/运算
WHERE YEAR(hire_date) = 2024     -- 失效
WHERE hire_date >= '2024-01-01'  -- 走索引

-- 2. 隐式类型转换（字段是 VARCHAR，传了数字）
WHERE phone = 13800138000        -- 失效！字符串转数字
WHERE phone = '13800138000'      -- 走索引

-- 3. LIKE 前置通配符
WHERE name LIKE '%张'             -- 失效
WHERE name LIKE '张%'             -- 走索引

-- 4. OR 条件中有非索引列
WHERE name = '张三' OR age = 25   -- 如果只有 name 索引，OR 让整个查询不走索引
-- 改为 UNION ALL
SELECT * FROM user WHERE name = '张三'
UNION ALL
SELECT * FROM user WHERE name != '张三' AND age = 25;

-- 5. NOT / != / <> 通常不走索引

-- 6. IS NULL / IS NOT NULL —— 视数据分布，大部分不为 NULL 时 IS NOT NULL 不走索引
```

## EXPLAIN 执行计划

```sql
EXPLAIN SELECT * FROM user WHERE name = '张三' AND age > 20;
```

关键列：

| 列 | 含义 |
|----|------|
| id | 查询序号，越大优先级越高 |
| select_type | SIMPLE / PRIMARY / SUBQUERY / DERIVED / UNION |
| type | 访问类型（性能从好到差）：system > const > eq_ref > ref > range > index > ALL |
| possible_keys | 可能用到的索引 |
| key | 实际使用的索引 |
| key_len | 索引使用长度（字节），同列数下越短越好 |
| rows | 预估扫描行数 |
| Extra | 额外信息：Using index（覆盖索引）、Using filesort（文件排序）、Using temporary（临时表） |

### type 访问类型

```
const:   主键/唯一索引等值查询，最多一行（WHERE id = 1）
eq_ref:  JOIN 时用主键/唯一索引关联（最多一行匹配）
ref:     非唯一索引等值查询（可能多行）
range:   索引范围扫描（BETWEEN、>、<、IN）
index:   全索引扫描（扫描整个索引）
ALL:     全表扫描（最差）
```

目标：type 至少达到 range 级别，Extra 不要出现 Using filesort 和 Using temporary。

## SQL 优化

### 慢查询定位

```sql
-- 开启慢查询日志
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;   -- 超过 1 秒记录
SET GLOBAL log_queries_not_using_indexes = ON;

-- 查看慢查询
-- 日志文件通常在 /var/log/mysql/slow-query.log

-- 或用 performance_schema
SELECT * FROM events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;
```

### 常见优化手段

**1. 索引优化**

为 WHERE、JOIN、ORDER BY 的列建索引。但不要过度——每多一个索引，写入就多一份开销。

**2. 查询重写**

```sql
-- 用 UNION ALL 替代 OR
-- 用 JOIN 替代子查询（视情况）
-- 大偏移量分页改为基于主键的游标分页
-- COUNT(*) 频繁的表，考虑用汇总表
```

**3. 避免 SELECT ***

**4. 批量操作**

```sql
INSERT INTO t VALUES (1,'a'),(2,'b'),(3,'c');  -- 批量
-- 而非逐条 INSERT
```

**5. 合理的表结构**

- 大字段（TEXT、BLOB）独立存储
- 适当的冗余（反范式化）减少 JOIN
- 垂直拆分：常用列和非常用列分开

**6. 连接池配置**

应用层使用 HikariCP 等连接池，避免频繁创建/销毁连接。

## 应用场景实战

### 场景一：千万级用户表优化

```sql
-- 优化前
SELECT * FROM user WHERE age BETWEEN 20 AND 30 ORDER BY create_time DESC LIMIT 20;

-- EXPLAIN 显示 type=ALL, rows=10000000, Extra=Using filesort

-- 优化：建复合索引
CREATE INDEX idx_age_ctime ON user(age, create_time);
-- EXPLAIN 显示 type=range, rows=1000, Extra=Using index condition
```

### 场景二：分页优化

```sql
-- 问题场景：第 50001 页，每页 20 条
SELECT * FROM user ORDER BY id LIMIT 1000000, 20;  -- 扫描 1000020 行

-- 优化：基于 id 的游标
SELECT * FROM user WHERE id > 1000000 ORDER BY id LIMIT 20;  -- 扫描 20 行
-- 前端需要传上一页的最后一条 id 作为参数
```

### 场景三：JOIN 优化

```sql
-- 优化前：小表驱动大表
SELECT * FROM big_table b
JOIN small_table s ON b.type_id = s.id;  -- 大表驱动小表

-- 优化后
SELECT * FROM small_table s
JOIN big_table b ON s.id = b.type_id;    -- 小表驱动大表

-- 也可以加 STRAIGHT_JOIN 强制指定驱动表
```

## 最佳实践与踩坑记录

**实践 1：字段默认值**

- `NOT NULL` 加 `DEFAULT`，避免 NULL 的特殊处理
- 时间字段用 `CURRENT_TIMESTAMP` 或 `'1970-01-01'` 作为默认值

**实践 2：字符集统一用 utf8mb4**

`utf8` 在 MySQL 中只支持 3 字节 UTF-8（不支持 emoji），`utf8mb4` 才是完整的 UTF-8。

```sql
CREATE DATABASE db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**实践 3：定期维护**

```sql
ANALYZE TABLE user;      -- 更新索引统计信息
OPTIMIZE TABLE user;     -- 整理碎片（会锁表，低峰期执行）
```

**踩坑 1**：varchar 长度不是越大越好。临时表和排序时会按最大长度分配内存，导致内存浪费。

**踩坑 2**：int(11) 中的 11 不是存储长度，是显示宽度（配合 ZEROFILL 使用）。INT 始终占 4 字节，范围不变。

**踩坑 3**：delete from 不会释放磁盘空间，只是标记删除。想释放空间用 `ALTER TABLE t ENGINE=InnoDB;` 或 `OPTIMIZE TABLE`。

**踩坑 4**：MySQL 8.0 移除了查询缓存，不要在项目中依赖它。

**踩坑 5**：InnoDB 的 count(*) 是全表扫描（MVCC 下没有精确行数缓存）。频繁 count 的表可以维护计数表或用 Redis 缓存。
