---
title: SQL
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [sql, ddl, dml, dql, dcl, tcl, select, join, subquery, cte, window-function]
---

# SQL

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [SQL 分类](#sql-分类)
- [DDL —— 数据定义语言](#ddl--数据定义语言)
- [DML —— 数据操纵语言](#dml--数据操纵语言)
- [DQL —— 数据查询语言](#dql--数据查询语言)
- [JOIN 连接查询](#join-连接查询)
- [GROUP BY 与 HAVING](#group-by-与-having)
- [子查询](#子查询)
- [CTE —— 公用表表达式](#cte--公用表表达式)
- [窗口函数](#窗口函数)
- [DCL —— 数据控制语言](#dcl--数据控制语言)
- [TCL —— 事务控制语言](#tcl--事务控制语言)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

SQL（Structured Query Language）是操作关系型数据库的标准语言。声明式——你描述"要什么"，DBMS 决定"怎么拿"。无论 MySQL、PostgreSQL 还是 Oracle，核心 SQL 语法高度一致。

## SQL 分类

按功能分为五类：

| 分类 | 全称 | 代表语句 | 作用 |
|------|------|----------|------|
| DDL | Data Definition Language | CREATE / ALTER / DROP / TRUNCATE | 定义表结构 |
| DML | Data Manipulation Language | INSERT / UPDATE / DELETE | 操作数据 |
| DQL | Data Query Language | SELECT | 查询数据 |
| DCL | Data Control Language | GRANT / REVOKE | 权限控制 |
| TCL | Transaction Control Language | COMMIT / ROLLBACK / SAVEPOINT | 事务控制 |

以下以 MySQL 语法为主，建表作为示例：

```sql
CREATE TABLE employee (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    age INT,
    salary DECIMAL(10,2),
    dept_id INT,
    hire_date DATE
);
```

## DDL —— 数据定义语言

操作的是表结构，不是数据。

### CREATE

```sql
-- 建表（完整语法）
CREATE TABLE employee (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    dept_id INT COMMENT '部门ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_dept_id (dept_id),
    CONSTRAINT fk_emp_dept FOREIGN KEY (dept_id) REFERENCES dept(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工表';

-- 根据查询结果建表（复制结构+数据）
CREATE TABLE employee_backup AS SELECT * FROM employee;

-- 只复制结构
CREATE TABLE employee_copy LIKE employee;
```

### ALTER

```sql
-- 添加列
ALTER TABLE employee ADD COLUMN phone VARCHAR(20);

-- 修改列类型
ALTER TABLE employee MODIFY COLUMN name VARCHAR(100);

-- 重命名列
ALTER TABLE employee CHANGE COLUMN phone mobile VARCHAR(20);

-- 删除列
ALTER TABLE employee DROP COLUMN mobile;

-- 添加索引
ALTER TABLE employee ADD INDEX idx_name (name);

-- 添加外键
ALTER TABLE employee ADD CONSTRAINT fk_dept
    FOREIGN KEY (dept_id) REFERENCES dept(id);
```

### DROP vs TRUNCATE vs DELETE

```sql
-- DROP：删除表结构和数据，不可回滚（DDL 隐式提交）
DROP TABLE employee_backup;

-- TRUNCATE：清空表数据，保留结构，不可回滚，重置自增计数器
TRUNCATE TABLE employee;

-- DELETE：逐行删除数据，可回滚，触发触发器，不重置自增
DELETE FROM employee WHERE id > 100;
```

## DML —— 数据操纵语言

### INSERT

```sql
-- 单行插入
INSERT INTO employee (name, gender, age, salary, dept_id)
VALUES ('张三', 'M', 28, 15000, 1);

-- 多行插入（性能远优于逐行插入）
INSERT INTO employee (name, gender, age, salary, dept_id) VALUES
    ('李四', 'F', 25, 12000, 2),
    ('王五', 'M', 30, 18000, 1),
    ('赵六', 'F', 27, 14000, 3);

-- 从查询结果插入
INSERT INTO employee_archive
SELECT * FROM employee WHERE hire_date < '2020-01-01';

-- INSERT ... ON DUPLICATE KEY UPDATE（存在则更新）
INSERT INTO user_stats (user_id, login_count, last_login)
VALUES (1, 1, NOW())
ON DUPLICATE KEY UPDATE
    login_count = login_count + 1,
    last_login = NOW();
```

### UPDATE

```sql
-- 更新单表
UPDATE employee SET salary = salary * 1.1 WHERE dept_id = 1;

-- 多表关联更新
UPDATE employee e
JOIN dept d ON e.dept_id = d.id
SET e.salary = e.salary * 1.2
WHERE d.name = '研发部';

-- 注意：不加 WHERE 会更新全表——生产环境先写 WHERE 再写 SET
```

### DELETE

```sql
-- 删除单表
DELETE FROM employee WHERE id = 100;

-- 多表关联删除
DELETE e FROM employee e
JOIN dept d ON e.dept_id = d.id
WHERE d.name = '已解散部门';

-- 软删除（推荐）
-- ALTER TABLE employee ADD COLUMN is_deleted TINYINT DEFAULT 0;
UPDATE employee SET is_deleted = 1 WHERE id = 100;
```

## DQL —— 数据查询语言

### SELECT 基础语法

```sql
SELECT [DISTINCT] 列名 | 表达式 | 函数
FROM 表名
[WHERE 条件]
[GROUP BY 分组列]
[HAVING 分组后过滤]
[ORDER BY 排序列 [ASC|DESC]]
[LIMIT 偏移量, 行数];
```

### WHERE 过滤

```sql
-- 比较运算
SELECT * FROM employee WHERE salary > 15000;
SELECT * FROM employee WHERE age BETWEEN 25 AND 35;
SELECT * FROM employee WHERE dept_id IN (1, 2, 3);
SELECT * FROM employee WHERE name LIKE '张%';   -- % 匹配任意，_ 匹配单字符
SELECT * FROM employee WHERE phone IS NULL;
SELECT * FROM employee WHERE phone IS NOT NULL;

-- 逻辑运算（AND 优先级高于 OR，用括号明确）
SELECT * FROM employee
WHERE (dept_id = 1 OR dept_id = 2)
  AND salary > 10000;
```

### ORDER BY

```sql
-- 单列排序
SELECT * FROM employee ORDER BY salary DESC;

-- 多列排序
SELECT * FROM employee ORDER BY dept_id ASC, salary DESC;

-- 用表达式排序
SELECT name, salary, salary * 12 AS annual
FROM employee
ORDER BY annual DESC;
```

### LIMIT

```sql
-- 前 10 条
SELECT * FROM employee ORDER BY id LIMIT 10;

-- 跳过 10 条，取 10 条（分页）
SELECT * FROM employee ORDER BY id LIMIT 10, 10;

-- 分页公式：LIMIT (page - 1) * pageSize, pageSize
```

## JOIN 连接查询

### JOIN 类型

```sql
-- 假设数据：
-- employee: (1, '张三', 1), (2, '李四', 2), (3, '王五', NULL)
-- dept:     (1, '研发部'), (2, '市场部'), (3, '财务部')

-- INNER JOIN：只返回匹配行
SELECT e.name, d.name AS dept_name
FROM employee e
INNER JOIN dept d ON e.dept_id = d.id;
-- 结果：张三-研发部, 李四-市场部（王五的 dept_id 是 NULL，不匹配）

-- LEFT JOIN：左表全保留，右表无匹配填 NULL
SELECT e.name, d.name AS dept_name
FROM employee e
LEFT JOIN dept d ON e.dept_id = d.id;
-- 结果：张三-研发部, 李四-市场部, 王五-NULL

-- RIGHT JOIN：右表全保留
SELECT e.name, d.name AS dept_name
FROM employee e
RIGHT JOIN dept d ON e.dept_id = d.id;
-- 结果：张三-研发部, 李四-市场部, NULL-财务部

-- FULL OUTER JOIN（MySQL 不支持，用 UNION 模拟）
SELECT e.name, d.name FROM employee e
LEFT JOIN dept d ON e.dept_id = d.id
UNION
SELECT e.name, d.name FROM employee e
RIGHT JOIN dept d ON e.dept_id = d.id;

-- CROSS JOIN：笛卡尔积
SELECT * FROM employee CROSS JOIN dept;
-- 结果：3 * 3 = 9 行
```

### 多表 JOIN

```sql
-- 员工 → 部门 → 公司
SELECT e.name, d.name AS dept, c.name AS company
FROM employee e
JOIN dept d ON e.dept_id = d.id
JOIN company c ON d.company_id = c.id;

-- 自连接：查询员工及其上级
SELECT e.name AS emp, m.name AS manager
FROM employee e
LEFT JOIN employee m ON e.manager_id = m.id;
```

### JOIN 性能注意

- JOIN 列必须建索引——否则走全表扫描
- 小表驱动大表——把小结果集的表放前面（MySQL 优化器会自动处理）
- 避免超过 3 个表的 JOIN——拆成多次查询在应用层组装

## GROUP BY 与 HAVING

GROUP BY 将数据分组，聚合函数对每组计算。

```sql
-- 聚合函数
COUNT(*)      -- 统计行数（包含 NULL）
COUNT(列名)   -- 统计非 NULL 值
SUM(列名)     -- 求和
AVG(列名)     -- 平均值
MAX(列名)     -- 最大值
MIN(列名)     -- 最小值

-- 每部门人数和平均薪资
SELECT dept_id,
       COUNT(*) AS emp_count,
       AVG(salary) AS avg_salary,
       MAX(salary) AS max_salary
FROM employee
GROUP BY dept_id;

-- HAVING：分组后过滤（WHERE 是分组前过滤）
SELECT dept_id, AVG(salary) AS avg_salary
FROM employee
WHERE hire_date > '2020-01-01'    -- 分组前：只要 2020 年后入职的
GROUP BY dept_id
HAVING AVG(salary) > 12000;       -- 分组后：只要平均薪资 > 12000 的部门
```

### SQL 执行顺序

```sql
SELECT   dept_id, COUNT(*) AS cnt      -- 5. 选择最终列
FROM     employee                      -- 1. 确定数据来源
WHERE    age > 25                      -- 2. 过滤行
GROUP BY dept_id                       -- 3. 分组
HAVING   COUNT(*) > 3                  -- 4. 过滤分组
ORDER BY cnt DESC                      -- 6. 排序
LIMIT    5;                            -- 7. 取前几行
```

理解这个顺序能避免常见错误——比如 WHERE 中不能用别名（WHERE 执行时别名还没定义），ORDER BY 中可以。

## 子查询

子查询嵌套在另一个查询中，可以出现在 SELECT / FROM / WHERE 中。

### 标量子查询（返回单个值）

```sql
-- 查询薪资高于平均值的员工
SELECT name, salary
FROM employee
WHERE salary > (SELECT AVG(salary) FROM employee);
```

### 行子查询（返回一行多列）

```sql
-- 查询与张三同部门同年龄的员工
SELECT * FROM employee
WHERE (dept_id, age) = (
    SELECT dept_id, age FROM employee WHERE name = '张三'
);
```

### 列子查询（返回一列多行）

```sql
-- IN：查询研发部和技术部的员工
SELECT name FROM employee
WHERE dept_id IN (
    SELECT id FROM dept WHERE name IN ('研发部', '技术部')
);

-- ANY / ALL
-- 查询薪资高于所有技术人员的员工
SELECT name, salary FROM employee
WHERE salary > ALL (
    SELECT salary FROM employee
    WHERE dept_id = (SELECT id FROM dept WHERE name = '技术部')
);

-- EXISTS：查询有员工的部门
SELECT name FROM dept d
WHERE EXISTS (
    SELECT 1 FROM employee e WHERE e.dept_id = d.id
);
```

### FROM 子查询（派生表）

```sql
-- 查询各部门薪资 Top 2
SELECT e.name, e.salary, e.dept_id
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rn
    FROM employee
) e
WHERE e.rn <= 2;
```

### 子查询 vs JOIN

子查询语义更直观，但某些场景 JOIN 性能更好。MySQL 5.6+ 优化器对子查询优化已很成熟，优先写清晰的 SQL，分析慢查询时再优化。

## CTE —— 公用表表达式

CTE（Common Table Expression）用 WITH 子句定义临时结果集，查询中可多次引用。

```sql
-- 基础 CTE
WITH high_salary AS (
    SELECT * FROM employee WHERE salary > 15000
)
SELECT name, salary FROM high_salary ORDER BY salary DESC;

-- 多个 CTE
WITH
dept_stats AS (
    SELECT dept_id, AVG(salary) AS avg_sal FROM employee GROUP BY dept_id
),
company_avg AS (
    SELECT AVG(salary) AS avg_sal FROM employee
)
SELECT d.name, ds.avg_sal,
       CASE WHEN ds.avg_sal > ca.avg_sal THEN '高于平均' ELSE '低于平均' END
FROM dept_stats ds
CROSS JOIN company_avg ca
JOIN dept d ON d.id = ds.dept_id;
```

### 递归 CTE

处理树形结构（部门层级、分类树、评论嵌套）：

```sql
-- 从某个节点向下递归找所有子节点
WITH RECURSIVE dept_tree AS (
    -- 基础：根节点
    SELECT id, name, parent_id, 0 AS level
    FROM dept
    WHERE parent_id IS NULL

    UNION ALL

    -- 递归：子节点 = 父节点的 id 等于当前节点的 id
    SELECT d.id, d.name, d.parent_id, dt.level + 1
    FROM dept d
    JOIN dept_tree dt ON d.parent_id = dt.id
)
SELECT CONCAT(REPEAT('  ', level), name) AS dept_name
FROM dept_tree
ORDER BY level, id;
```

MySQL 递归 CTE 默认最大递归 1000 层，可通过 `SET SESSION cte_max_recursion_depth = 10000;` 调整。

## 窗口函数

窗口函数在不折叠行的情况下做分组计算——保留原始行 + 附加聚合列。

```sql
窗口函数名([表达式]) OVER (
    [PARTITION BY 分组列]
    [ORDER BY 排序列]
    [窗口范围]
)
```

### 序号函数

```sql
-- ROW_NUMBER()：连续序号，不跳号
-- RANK()：跳跃序号，同值同号（1,1,3,4）
-- DENSE_RANK()：连续序号，同值同号（1,1,2,3）

SELECT name, dept_id, salary,
       ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rn,
       RANK()       OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rk,
       DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS dr
FROM employee;
```

### 聚合窗口

```sql
-- 累计求和
SELECT name, salary,
       SUM(salary) OVER (ORDER BY id) AS running_total
FROM employee;

-- 移动平均（前 2 行 + 当前行 + 后 2 行）
SELECT name, salary,
       AVG(salary) OVER (ORDER BY id ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING) AS moving_avg
FROM employee;
```

### 偏移函数

```sql
-- LAG：取前一行
-- LEAD：取后一行
SELECT name, salary,
       LAG(salary, 1)  OVER (ORDER BY id) AS prev_salary,
       LEAD(salary, 1) OVER (ORDER BY id) AS next_salary,
       salary - LAG(salary, 1) OVER (ORDER BY id) AS diff
FROM employee;
```

### 窗口范围（Frame）

```sql
-- ROWS：物理行数
ROWS BETWEEN 3 PRECEDING AND CURRENT ROW

-- RANGE：值范围（ORDER BY 的值）
RANGE BETWEEN INTERVAL 7 DAY PRECEDING AND CURRENT ROW

-- 默认窗口（无 ORDER BY 时为所有行，有 ORDER BY 时为累积）
RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

## DCL —— 数据控制语言

```sql
-- 创建用户
CREATE USER 'app'@'%' IDENTIFIED BY 'password';

-- 授权
GRANT SELECT, INSERT, UPDATE ON shop.* TO 'app'@'%';
GRANT ALL PRIVILEGES ON shop.* TO 'app'@'%';

-- 回收权限
REVOKE DELETE ON shop.* FROM 'app'@'%';

-- 查看权限
SHOW GRANTS FOR 'app'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 删除用户
DROP USER 'app'@'%';
```

## TCL —— 事务控制语言

```sql
-- 开启事务（三种方式）
START TRANSACTION;
-- 或
BEGIN;
-- 或
SET autocommit = 0;    -- 之后每条 SQL 都自动开启事务

-- 提交
COMMIT;

-- 回滚
ROLLBACK;

-- 部分回滚（保存点）
SAVEPOINT sp1;
UPDATE account SET balance = balance - 100 WHERE id = 1;
SAVEPOINT sp2;
UPDATE account SET balance = balance + 100 WHERE id = 999;  -- id=999 不存在
ROLLBACK TO sp2;   -- 回滚到 sp2，只撤销第二条 UPDATE
COMMIT;            -- 第一条 UPDATE 生效
```

## 应用场景实战

### 场景一：用户行为漏斗分析

需求：统计"访问首页 → 搜索商品 → 加入购物车 → 下单"各环节转化率。

```sql
WITH funnel AS (
    SELECT user_id,
           MAX(CASE WHEN event = 'page_view'   THEN 1 ELSE 0 END) AS step1,
           MAX(CASE WHEN event = 'search'      THEN 1 ELSE 0 END) AS step2,
           MAX(CASE WHEN event = 'add_cart'    THEN 1 ELSE 0 END) AS step3,
           MAX(CASE WHEN event = 'place_order' THEN 1 ELSE 0 END) AS step4
    FROM user_events
    WHERE event_date = CURDATE()
    GROUP BY user_id
)
SELECT
    COUNT(*)                                   AS total_users,
    SUM(step1)                                 AS view_home,
    SUM(step2)                                 AS search,
    SUM(step3)                                 AS add_cart,
    SUM(step4)                                 AS place_order,
    ROUND(SUM(step2) * 1.0 / SUM(step1), 2)    AS search_rate,
    ROUND(SUM(step3) * 1.0 / SUM(step2), 2)    AS cart_rate,
    ROUND(SUM(step4) * 1.0 / SUM(step3), 2)    AS order_rate
FROM funnel;
```

### 场景二：连续登录天数

需求：找出连续登录超过 3 天的用户。

```sql
WITH daily_login AS (
    SELECT DISTINCT user_id, login_date
    FROM login_log
    WHERE login_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
),
ranked AS (
    SELECT user_id, login_date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM daily_login
),
streak_groups AS (
    SELECT user_id, login_date,
           DATE_SUB(login_date, INTERVAL rn DAY) AS grp
    FROM ranked
)
SELECT user_id, COUNT(*) AS streak_days
FROM streak_groups
GROUP BY user_id, grp
HAVING COUNT(*) >= 3;
```

核心思路：连续日期减去连续序号 = 相同的分组标记。例如 1号/2号/4号 的序号是 1/2/3，日期减序号 = 同一天 / 同一天 / 1号后一天（不同），自然分组。

## 最佳实践与踩坑记录

**实践 1：只查需要的列**

```sql
-- 差
SELECT * FROM employee WHERE dept_id = 1;

-- 好
SELECT id, name, salary FROM employee WHERE dept_id = 1;
```

`SELECT *` 无法利用覆盖索引，传输多余数据，而且表结构变化会导致代码 bug。

**实践 2：WHERE 列不加函数**

```sql
-- 差：索引失效
SELECT * FROM employee WHERE DATE(hire_date) = '2024-01-01';

-- 好：索引可用
SELECT * FROM employee WHERE hire_date >= '2024-01-01' AND hire_date < '2024-01-02';
```

**实践 3：分页优化**

```sql
-- 差：大偏移量时性能极差（OFFSET 1000000 需要扫描并丢弃前 100 万行）
SELECT * FROM employee ORDER BY id LIMIT 1000000, 20;

-- 好：基于上一页最后一条的 id 定位
SELECT * FROM employee WHERE id > 1000000 ORDER BY id LIMIT 20;
```

**实践 4：批量操作优于逐行操作**

```sql
-- 逐行插入：每行一个事务，极慢
-- for (User u : users) { jdbc.execute("INSERT ..."); }

-- 批量插入：一个事务
INSERT INTO user (name, email) VALUES
    ('a', 'a@x.com'), ('b', 'b@x.com'), ('c', 'c@x.com');
```

**踩坑 1**：NULL 的比较用 `IS NULL` 而不是 `= NULL`。`NULL = NULL` 结果是 NULL（不是 TRUE），WHERE 会过滤掉。

**踩坑 2**：COUNT(列名) 不统计 NULL，COUNT(*) 统计所有行。要统计人数用 COUNT(*)。

**踩坑 3**：GROUP BY 的列必须在 SELECT 中出现或用于聚合。MySQL 的 ONLY_FULL_GROUP_BY 模式（5.7+ 默认开启）会严格检查。

**踩坑 4**：DELETE 不带 WHERE 清空全表，且触发每行的删除操作。清空数据用 TRUNCATE。
