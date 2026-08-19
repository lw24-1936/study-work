---
title: 多租户SaaS平台
created: 2026-08-19
updated: 2026-08-19
type: concept
tags: [综合项目, 项目实战, saas, multitenant, tenant, springboot]
---

# 多租户SaaS平台

整理日期：2026-08-19

## 目录

- [项目背景](#项目背景)
- [功能介绍](#功能介绍)
- [技术选型](#技术选型)
- [架构设计](#架构设计)
- [数据库设计](#数据库设计)
- [核心实现](#核心实现)
- [实际应用场景](#实际应用场景)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)
- [相关文档](#相关文档)

## 项目背景

多租户SaaS平台（Multi-Tenant SaaS Platform）解决的是 SaaS 软件「一套代码服务多个客户」的底座问题：客户（租户）自助开通、数据隔离、套餐订阅、用量计量与账单生成。传统项目交付模式是一个客户一套独立部署（独立数据库、独立应用），客户越多运维成本越高、版本分裂越严重；SaaS 模式则是所有租户共用一套应用与数据库资源，靠「租户隔离机制」保证每个租户只能看到自己的数据，靠「套餐 + 计量」实现按量计费。这个项目的核心不是业务功能本身，而是三个框架级能力：租户隔离（行级 tenant_id 或 schema 隔离，业务代码无感）、租户上下文传递（请求头 → ThreadLocal → SQL 条件全链路）、套餐变更与用量计费（开通/停用/升降级/账单）。它适合作为各类 SaaS 产品的公共底座，也是理解「多租户架构」这个高频面试话题的最佳实战载体。

业务痛点：

```text
1. 一套代码多客户难维护：传统项目一个客户一套部署，数据库与应用全部独立，运维成本随客户数线性增长
2. 数据混在一起风险高：多租户共用一个库一个表，任何查询漏加 tenant_id 条件就是跨租户数据泄露事故
3. 隔离全靠自觉：共享表方案里「查询带租户条件」依赖开发自律，缺少机制层的强制兜底
4. 计费靠人工估算：客户用了多少 API、多少存储、多少用户没有自动计量，账单靠销售拍脑袋
5. 套餐变更没有标准流程：免费版升专业版涉及配额调整、数据搬迁，全靠手工操作容易出错
6. 开通租户慢：新客户开通要手动建库建表导初始化数据，耗时数小时，无法自助化
```

目标用户与核心诉求：

```text
1. SaaS 平台运营：自助开通/停用租户、配置套餐与价格、查看各租户用量与账单
2. 租户管理员：管理本租户成员与角色、查看本租户用量与配额剩余、购买/变更套餐
3. 平台研发：在框架层统一处理租户隔离与上下文传递，业务代码完全无感知租户概念
```

项目要解决的核心问题一句话概括：构建一套多租户 SaaS 底座——租户开通/停用/套餐管理 + 框架级租户隔离（行级 tenant_id 或 schema 隔离）+ API/存储/用户数用量计量 + 月度账单自动生成，让业务团队在这个底座上开发功能时不用再关心「数据是谁的」。

## 功能介绍

功能按角色与模块拆分：租户管理（运营端）、租户隔离（框架层）、套餐与订阅（计费端）、用量计量（数据端）、账单生成（财务端）。

```text
一、租户管理（平台运营端）
1. 租户开通 —— 填写租户信息、选择套餐，系统自动初始化：行级模式插入租户记录，schema 模式自动建库建表并导入初始化数据
2. 租户停用/启用 —— 停用后该租户所有请求被拦截（返回 403 租户已停用），数据保留不删除
3. 套餐变更 —— 升级/降级套餐，配额即时生效，超配额场景按迁移策略处理（冻结写入/提示扩容）
4. 租户列表 —— 按状态/套餐/创建时间筛选，展示每个租户的用量概览与订阅到期时间
5. 操作审计 —— 开通/停用/套餐变更/迁移全部留痕，可追溯

二、租户隔离（框架层，业务无感）
1. 行级隔离 —— 共享表 + tenant_id 列，MyBatis-Plus TenantLineInnerInterceptor 在 SQL 层强制追加 tenant_id 条件
2. Schema 隔离 —— 每个租户独立 schema（独立表空间），按租户切换 schema 访问
3. 上下文传递 —— 请求头 X-Tenant-Id → 拦截器 → ThreadLocal → SQL 条件，全链路自动
4. 隔离兜底 —— 未带租户头的请求直接拒绝；平台侧接口与租户侧接口路径分离，互不串扰

三、套餐与订阅
1. 套餐定义 —— 免费版/专业版/企业版：月费、API 调用配额、存储配额、用户数配额、超量单价、功能清单
2. 订阅管理 —— 订阅生效期、自动续费、到期提醒
3. 配额查询 —— 租户随时查看当前用量与剩余配额，超配额预警

四、用量计量
1. API 调用量 —— 计量拦截器统计每次租户 API 请求，Redis 计数，按日聚合落库
2. 存储用量 —— 上传/删除文件时实时增减，定时任务校准（扫描对象存储）
3. 用户数 —— 租户成员增删实时更新，按当前值计费
4. 配额控制 —— 用量达到配额 80% 发预警，超配额可配置为限流或拒绝（429）

五、账单生成（财务端）
1. 月度账单 —— 每月 1 日生成上月账单：套餐费 + 超量费
2. 超量计费 —— API 超出配额部分按套餐单价计费，存储超量同理
3. 账单导出 —— 账单明细导出 Excel 对账
4. 账单状态 —— 待支付/已支付/已作废，与支付系统对接
```

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 开发框架 | Spring Boot 2.7/3.x | 生态成熟，快速搭建 |
| 持久层 | MyBatis-Plus | 内置 TenantLineInnerInterceptor 多租户插件 |
| 数据库 | MySQL 8.0 | 平台库 + 租户 schema |
| 缓存 | Redis | 用量计数器（INCR 原子）、租户状态缓存 |
| 上下文传递 | ThreadLocal + HandlerInterceptor | 租户上下文全链路自动传递 |
| 隔离策略 | 行级 tenant_id（默认）+ schema 隔离（高级租户） | 成本与隔离强度按需权衡 |
| 账单导出 | EasyExcel | 大数据量流式导出 |
| 定时任务 | Spring @Scheduled | 用量聚合、账单生成、到期提醒 |
| 前端 | Vue 3 + Element Plus | 平台管理后台与租户控制台 |
| 构建 | Maven | 依赖管理标准工具 |

选型说明：

```text
1. 默认行级隔离：共享表 + tenant_id 列，成本最低、运维最简单，90% 租户够用；MyBatis-Plus 拦截器在 SQL 层强制追加 tenant_id，从机制上堵住「漏加条件」这个最大风险
2. Schema 隔离按需启用：金融、医疗等强合规大客户用独立 schema，隔离强度最高，通过动态切换 schema 实现，与行级模式共用同一套业务代码
3. 用量计量用 Redis 计数器：API 调用量是高频写入（每秒几千次），先 INCR 进 Redis，定时任务聚合落库，避免每次请求都写 MySQL
4. 租户上下文用 ThreadLocal：拦截器从请求头读取写入 ThreadLocal，业务代码通过 TenantContext 访问；异步线程用包装器显式传递，防止线程池复用串号
5. 套餐数据模型化：套餐、配额、单价全部入库配置，改价格/加套餐不用发版；账单明细按指标拆分，财务可核对
```

## 架构设计

系统分层与请求链路：

```text
┌──────────────────────────────────────────────────────────────┐
│                         客户端                               │
│   平台管理端（超管）：租户/套餐/账单/用量（Vue3）              │
│   租户控制台（租户管理员）：成员/用量/配额/订阅（Vue3）        │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP（Header: X-Tenant-Id + Token）
┌───────────────────────────▼──────────────────────────────────┐
│                Spring Boot 应用层（多租户框架）               │
│   ┌─────────────┐ ┌─────────────┐ ┌───────────────────────┐  │
│   │ 租户拦截器   │ │ 租户上下文   │ │ 数据源/Schema 路由     │  │
│   │ 解析头->TTL  │ │ ThreadLocal │ │ 行级/模式级切换        │  │
│   └─────────────┘ └─────────────┘ └───────────────────────┘  │
│   ┌─────────────┐ ┌─────────────┐ ┌───────────────────────┐  │
│   │ 业务服务     │ │ 用量计量服务  │ │ 套餐/订阅/账单服务     │  │
│   │ CRUD/查询   │ │ 拦截器+Redis │ │ 订阅/计费/导出         │  │
│   └─────────────┘ └─────────────┘ └───────────────────────┘  │
└──────┬──────────────────┬──────────────────┬──────────────────┘
       │                  │                  │
┌──────▼────────────┐   ┌──▼───────┐   ┌─────▼─────────────────┐
│ MySQL 平台库       │   │  Redis   │   │ MySQL 租户 schema     │
│ 租户/套餐/账单/用量 │   │ 用量计数  │   │ （schema 模式租户）    │
│                   │   │ 租户缓存  │   │                      │
└───────────────────┘   └──────────┘   └───────────────────────┘
```

一次租户内请求的隔离链路：

```text
1. 租户 A 的用户登录后请求 GET /api/orders，请求头带 X-Tenant-Id: t_1001
2. TenantInterceptor 校验租户存在且未停用（先查 Redis 缓存），把 t_1001 写入 TenantContext（ThreadLocal）
3. 行级模式：业务执行 SELECT * FROM orders，MyBatis-Plus 拦截器自动追加 WHERE tenant_id = 't_1001'
4. schema 模式：SchemaRouter 根据 t_1001 找到对应 schema 名，切换当前连接默认库后执行同一 SQL
5. 业务代码全程无感知租户概念，只写业务 SQL，测试/排查也按普通单租户逻辑进行
6. 计量拦截器同一请求统计 API 调用量：Redis INCR saas:usage:t_1001:日期:api_call
7. 响应返回后，拦截器 finally 清理 ThreadLocal，防止连接池/线程池复用导致租户串号
```

## 数据库设计

核心表设计（7 张表）：

```sql
-- 租户表（平台库）
CREATE TABLE `saas_tenant` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT,
  `tenant_code`   VARCHAR(64)  NOT NULL COMMENT '租户编码（X-Tenant-Id 值，对外标识）',
  `tenant_name`   VARCHAR(200) NOT NULL COMMENT '租户名称',
  `plan_id`       BIGINT       NOT NULL COMMENT '当前套餐 id',
  `isolate_mode`  VARCHAR(20)  NOT NULL DEFAULT 'row' COMMENT '隔离模式：row（行级）/schema（独立 schema）',
  `schema_name`   VARCHAR(64)  DEFAULT NULL COMMENT 'schema 模式下的库名（行级模式为空）',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1正常 0停用',
  `expire_time`   DATETIME     DEFAULT NULL COMMENT '订阅到期时间',
  `contact`       VARCHAR(100) DEFAULT NULL COMMENT '联系人',
  `create_time`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`tenant_code`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SaaS 租户表';

-- 套餐表（平台库）
CREATE TABLE `saas_plan` (
  `id`             BIGINT        NOT NULL AUTO_INCREMENT,
  `plan_code`      VARCHAR(32)   NOT NULL COMMENT '套餐编码：free/pro/enterprise',
  `plan_name`      VARCHAR(100)  NOT NULL COMMENT '套餐名称：免费版/专业版/企业版',
  `price_month`    DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '月费（元）',
  `api_quota`      BIGINT        NOT NULL DEFAULT 0 COMMENT '月 API 调用配额（次）',
  `storage_quota`  BIGINT        NOT NULL DEFAULT 0 COMMENT '存储配额（MB）',
  `user_quota`     INT           NOT NULL DEFAULT 0 COMMENT '用户数配额',
  `api_over_price` DECIMAL(10,4) NOT NULL DEFAULT 0 COMMENT 'API 超量单价（元/千次）',
  `storage_over_price` DECIMAL(10,4) NOT NULL DEFAULT 0 COMMENT '存储超量单价（元/GB/月）',
  `features`       VARCHAR(1000) DEFAULT NULL COMMENT '功能清单 JSON（哪些功能对套餐开放）',
  `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`plan_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SaaS 套餐表';

-- 订阅表（平台库，订阅变更历史）
CREATE TABLE `saas_subscription` (
  `id`            BIGINT      NOT NULL AUTO_INCREMENT,
  `tenant_id`     BIGINT      NOT NULL,
  `plan_id`       BIGINT      NOT NULL,
  `status`        TINYINT     NOT NULL DEFAULT 1 COMMENT '状态：1生效 0已过期',
  `start_time`    DATETIME    NOT NULL,
  `end_time`      DATETIME    NOT NULL,
  `auto_renew`    TINYINT     NOT NULL DEFAULT 1 COMMENT '是否自动续费',
  `change_reason` VARCHAR(200) DEFAULT NULL COMMENT '变更原因：开通/升级/降级/续费',
  `create_time`   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_tenant` (`tenant_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订阅表';

-- 租户用户表（平台库，全局用户与租户的关联）
CREATE TABLE `saas_tenant_user` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `tenant_id`   BIGINT       NOT NULL,
  `user_id`     BIGINT       NOT NULL COMMENT '全局用户 id',
  `user_name`   VARCHAR(100) NOT NULL,
  `role`        VARCHAR(20)  NOT NULL DEFAULT 'member' COMMENT '角色：admin/member',
  `status`      TINYINT      NOT NULL DEFAULT 1 COMMENT '1正常 0已移除',
  `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_user` (`tenant_id`, `user_id`),
  KEY `idx_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户用户表';

-- 用量日聚合表（平台库，计量落库结果）
CREATE TABLE `saas_usage_daily` (
  `id`           BIGINT      NOT NULL AUTO_INCREMENT,
  `tenant_id`    BIGINT      NOT NULL,
  `metric_type`  VARCHAR(20) NOT NULL COMMENT '指标类型：api_call/storage/user_count',
  `metric_value` BIGINT      NOT NULL DEFAULT 0 COMMENT '当日值（api_call 为次数，storage 为 MB 峰值，user_count 为人数）',
  `stat_date`    DATE        NOT NULL COMMENT '统计日期',
  `create_time`  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_metric` (`tenant_id`, `metric_type`, `stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户用量日表';

-- 账单表（平台库）
CREATE TABLE `saas_bill` (
  `id`          BIGINT        NOT NULL AUTO_INCREMENT,
  `bill_no`     VARCHAR(64)   NOT NULL COMMENT '账单编号',
  `tenant_id`   BIGINT        NOT NULL,
  `period`      VARCHAR(7)    NOT NULL COMMENT '账期（如 2026-08）',
  `plan_fee`    DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '套餐费',
  `over_fee`    DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '超量费',
  `total_fee`   DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '合计',
  `detail_json` TEXT          DEFAULT NULL COMMENT '明细：各指标用量/配额/超量/单价',
  `status`      TINYINT       NOT NULL DEFAULT 0 COMMENT '状态：0待支付 1已支付 2已作废',
  `create_time` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bill` (`tenant_id`, `period`),
  KEY `idx_period` (`period`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户账单表';

-- 租户操作审计表（平台库）
CREATE TABLE `saas_tenant_log` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `tenant_id`   BIGINT       NOT NULL,
  `action`      VARCHAR(30)  NOT NULL COMMENT '动作：create/disable/enable/plan_change/migrate',
  `operator`    VARCHAR(100) DEFAULT NULL COMMENT '操作人',
  `detail`      VARCHAR(500) DEFAULT NULL COMMENT '详情（变更前后套餐等）',
  `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_tenant` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户操作审计表';
```

租户业务表（行级模式示例，业务库/共享表）：

```sql
-- 共享表 + tenant_id 列（所有租户共用）
CREATE TABLE `orders` (
  `id`         BIGINT       NOT NULL AUTO_INCREMENT,
  `tenant_id`  VARCHAR(64)  NOT NULL COMMENT '租户编码（隔离键，索引必须带上）',
  `order_no`   VARCHAR(64)  NOT NULL,
  `amount`     DECIMAL(10,2) NOT NULL,
  `status`     TINYINT      NOT NULL DEFAULT 0,
  `create_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_order` (`tenant_id`, `order_no`),
  KEY `idx_tenant_time` (`tenant_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表（共享表，tenant_id 隔离）';
```

Redis Key 设计：

```text
saas:tenant:{tenantCode}              租户状态缓存（status/plan/schema_name，拦截器高频读，变更即刷新）
saas:usage:{tenantCode}:{date}:{metric}  用量计数器（INCR 原子累加，日粒度）
saas:quota:lock:{tenantCode}          套餐变更/迁移互斥锁（SETNX，防并发变更）
saas:tenant:seq:{date}                租户编码序号生成（INCR，租户编码唯一）
```

## 核心实现

### 1. 租户上下文：ThreadLocal 传递与清理

```java
public class TenantContext {

    // ThreadLocal 存储当前请求的租户信息
    private static final ThreadLocal<TenantInfo> HOLDER = new ThreadLocal<>();

    public static void set(TenantInfo info) {
        HOLDER.set(info);
    }

    public static TenantInfo get() {
        return HOLDER.get();
    }

    public static String tenantCode() {
        TenantInfo info = HOLDER.get();
        return info == null ? null : info.getTenantCode();
    }

    /** 请求结束必须清理，防止线程池复用导致租户串号 */
    public static void clear() {
        HOLDER.remove();
    }

    /** 异步任务包装器：把当前租户上下文显式传递给子线程 */
    public static Runnable wrap(Runnable task) {
        TenantInfo info = HOLDER.get();
        return () -> {
            TenantContext.set(info);
            try {
                task.run();
            } finally {
                TenantContext.clear();
            }
        };
    }
}

// 租户信息（缓存反序列化对象）
public class TenantInfo {
    private String tenantCode;
    private Long tenantId;
    private String isolateMode;   // row / schema
    private String schemaName;    // schema 模式下的库名
    private Integer status;
    // getter / setter 省略
}
```

### 2. 租户拦截器：解析请求头、校验、设置与清理上下文

```java
@Component
public class TenantInterceptor implements HandlerInterceptor {

    @Autowired
    private StringRedisTemplate redisTemplate;
    @Autowired
    private ObjectMapper objectMapper;

    // 平台侧接口前缀：不解析租户头，走平台库
    private static final String PLATFORM_PREFIX = "/saas/";
    // 白名单：登录、健康检查等
    private static final List<String> WHITE_LIST =
            List.of("/api/auth/login", "/actuator/health");

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response, Object handler) throws Exception {
        String uri = request.getRequestURI();
        if (uri.startsWith(PLATFORM_PREFIX) || WHITE_LIST.contains(uri)) {
            return true;   // 平台侧接口不进入租户上下文
        }
        String tenantCode = request.getHeader("X-Tenant-Id");
        if (tenantCode == null || tenantCode.isEmpty()) {
            response.setStatus(400);
            response.getWriter().write("缺少 X-Tenant-Id 请求头");
            return false;
        }
        // 租户状态缓存优先（Redis），未命中查库
        TenantInfo info = loadTenant(tenantCode);
        if (info == null) {
            response.setStatus(404);
            response.getWriter().write("租户不存在");
            return false;
        }
        if (info.getStatus() != 1) {
            response.setStatus(403);
            response.getWriter().write("租户已停用");
            return false;
        }
        TenantContext.set(info);
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        TenantContext.clear();   // 必须清理
    }

    /** 从缓存或数据库加载租户信息 */
    private TenantInfo loadTenant(String tenantCode) throws Exception {
        String cacheKey = "saas:tenant:" + tenantCode;
        String json = redisTemplate.opsForValue().get(cacheKey);
        if (json != null) {
            return objectMapper.readValue(json, TenantInfo.class);
        }
        TenantInfo info = tenantMapper.selectByCode(tenantCode);
        if (info != null) {
            redisTemplate.opsForValue().set(cacheKey,
                    objectMapper.writeValueAsString(info), 30, TimeUnit.MINUTES);
        }
        return info;
    }
}
```

### 3. 租户开通服务：行级 / schema 两种模式的初始化

```java
@Service
public class TenantService {

    @Autowired
    private TenantMapper tenantMapper;
    @Autowired
    private SubscriptionMapper subscriptionMapper;
    @Autowired
    private TenantLogMapper tenantLogMapper;
    @Autowired
    private StringRedisTemplate redisTemplate;
    @Autowired
    private JdbcTemplate jdbcTemplate;
    @Autowired
    private ObjectMapper objectMapper;

    /**
     * 开通租户：创建租户记录 + 订阅 + （schema 模式）建库初始化
     * 行级模式：只需插入租户记录与订阅，业务表共享无需初始化
     * schema 模式：执行 CREATE DATABASE + 初始化 DDL（tenant-init.sql）
     */
    @Transactional(rollbackFor = Exception.class)
    public Long createTenant(CreateTenantRequest req) {
        // 生成唯一租户编码
        long seq = redisTemplate.opsForValue().increment(
                "saas:tenant:seq:" + LocalDate.now());
        String tenantCode = "t_" + LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"))
                + "_" + seq;

        TenantInfo tenant = new TenantInfo();
        tenant.setTenantCode(tenantCode);
        tenant.setTenantName(req.getTenantName());
        tenant.setPlanId(req.getPlanId());
        tenant.setIsolateMode(req.getIsolateMode());
        tenant.setStatus(1);
        tenant.setExpireTime(LocalDateTime.now().plusMonths(1));

        if ("schema".equals(req.getIsolateMode())) {
            // schema 模式：建库 + 执行初始化 DDL（从 classpath 读取）
            String schemaName = "db_" + tenantCode;
            jdbcTemplate.execute("CREATE DATABASE IF NOT EXISTS `" + schemaName
                    + "` DEFAULT CHARACTER SET utf8mb4");
            Resource initSql = new ClassPathResource("tenant-init.sql");
            String ddl = new String(initSql.getInputStream().readAllBytes(),
                    StandardCharsets.UTF_8);
            // 在新建 schema 中执行 DDL（切换默认库）
            jdbcTemplate.execute("USE `" + schemaName + "`");
            jdbcTemplate.execute(ddl);
            jdbcTemplate.execute("USE `saas_platform`");   // 切回平台库
            tenant.setSchemaName(schemaName);
        }
        tenantMapper.insert(tenant);

        // 创建订阅
        Subscription sub = new Subscription();
        sub.setTenantId(tenant.getId());
        sub.setPlanId(req.getPlanId());
        sub.setStartTime(LocalDateTime.now());
        sub.setEndTime(LocalDateTime.now().plusMonths(1));
        sub.setChangeReason("开通");
        subscriptionMapper.insert(sub);

        // 审计 + 刷新缓存
        tenantLogMapper.insert(tenant.getId(), "create",
                req.getOperator(), "开通租户，模式=" + req.getIsolateMode());
        refreshCache(tenant);
        return tenant.getId();
    }

    /** 停用/启用租户：状态翻转 + 缓存刷新（拦截器实时生效） */
    public void changeStatus(Long tenantId, int status, String operator) {
        TenantInfo tenant = tenantMapper.selectById(tenantId);
        tenant.setStatus(status);
        tenantMapper.updateById(tenant);
        tenantLogMapper.insert(tenantId, status == 1 ? "enable" : "disable",
                operator, "租户状态变更");
        refreshCache(tenant);
    }

    private void refreshCache(TenantInfo tenant) {
        try {
            redisTemplate.opsForValue().set("saas:tenant:" + tenant.getTenantCode(),
                    objectMapper.writeValueAsString(tenant), 30, TimeUnit.MINUTES);
        } catch (Exception e) {
            // 缓存写失败不影响主流程，拦截器会回源查库
        }
    }
}
```

### 4. 用量计量：拦截器计数 + 定时聚合

```java
@Component
public class UsageMeterInterceptor implements HandlerInterceptor {

    @Autowired
    private StringRedisTemplate redisTemplate;

    // 不计量的路径：平台侧接口、登录、健康检查
    private static final List<String> SKIP =
            List.of("/saas/", "/api/auth/login", "/actuator/");

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response, Object handler) {
        String uri = request.getRequestURI();
        String tenantCode = TenantContext.tenantCode();
        if (tenantCode == null || SKIP.stream().anyMatch(uri::startsWith)) {
            return true;
        }
        // Redis 原子计数：saas:usage:{tenant}:{yyyyMMdd}:api_call
        String key = "saas:usage:" + tenantCode + ":"
                + LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE)
                + ":api_call";
        redisTemplate.opsForValue().increment(key);
        return true;
    }
}

@Service
public class UsageAggService {

    @Autowired
    private StringRedisTemplate redisTemplate;
    @Autowired
    private UsageDailyMapper usageDailyMapper;
    @Autowired
    private TenantMapper tenantMapper;

    /** 每日 1 点执行：把 Redis 计数器聚合落库（saas_usage_daily） */
    @Scheduled(cron = "0 0 1 * * ?")
    public void aggregateDaily() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.format(DateTimeFormatter.BASIC_ISO_DATE);
        for (TenantInfo tenant : tenantMapper.selectAll()) {
            String key = "saas:usage:" + tenant.getTenantCode() + ":" + dateStr + ":api_call";
            String val = redisTemplate.opsForValue().get(key);
            long count = val == null ? 0 : Long.parseLong(val);
            if (count > 0) {
                UsageDaily daily = new UsageDaily();
                daily.setTenantId(tenant.getId());
                daily.setMetricType("api_call");
                daily.setMetricValue(count);
                daily.setStatDate(yesterday);
                usageDailyMapper.insertOrUpdate(daily);   // 唯一键冲突则累加
            }
            // 存储用量与用户数由各自的服务实时/定时写入，逻辑相同
        }
    }

    /** 配额检查：月累计用量是否超过套餐配额 */
    public boolean checkQuota(Long tenantId, String metricType, long need) {
        TenantInfo tenant = tenantMapper.selectById(tenantId);
        Plan plan = planMapper.selectById(tenant.getPlanId());
        LocalDate firstDay = LocalDate.now().withDayOfMonth(1);
        long used = usageDailyMapper.sumSince(tenantId, metricType, firstDay);
        long quota = switch (metricType) {
            case "api_call" -> plan.getApiQuota();
            case "storage" -> plan.getStorageQuota();
            case "user_count" -> plan.getUserQuota();
            default -> Long.MAX_VALUE;
        };
        return used + need <= quota;
    }
}
```

### 5. 套餐与订阅服务：变更套餐与配额生效

```java
@Service
public class SubscriptionService {

    @Autowired
    private SubscriptionMapper subscriptionMapper;
    @Autowired
    private TenantMapper tenantMapper;
    @Autowired
    private TenantLogMapper tenantLogMapper;
    @Autowired
    private UsageAggService usageAggService;
    @Autowired
    private StringRedisTemplate redisTemplate;

    /**
     * 套餐变更：校验 → 配额兼容检查 → 更新订阅与租户 → 刷新缓存
     * 降级时数据超配额：提示租户清理或拒绝降级（按策略）
     */
    @Transactional(rollbackFor = Exception.class)
    public void changePlan(Long tenantId, Long newPlanId, String operator) {
        // 变更互斥锁：防止并发变更与迁移冲突
        String lockKey = "saas:quota:lock:" + tenantId;
        Boolean locked = redisTemplate.opsForValue()
                .setIfAbsent(lockKey, "1", 60, TimeUnit.SECONDS);
        if (!Boolean.TRUE.equals(locked)) {
            throw new BizException("租户正在变更中，请稍后重试");
        }
        try {
            TenantInfo tenant = tenantMapper.selectById(tenantId);
            Plan newPlan = planMapper.selectById(newPlanId);
            Plan oldPlan = planMapper.selectById(tenant.getPlanId());

            // 降级兼容检查：当前存储用量是否超新套餐配额
            long storageUsed = usageAggService.currentUsage(tenantId, "storage");
            if (storageUsed > newPlan.getStorageQuota()) {
                throw new BizException("当前存储用量 " + storageUsed + "MB 超过目标套餐配额 "
                        + newPlan.getStorageQuota() + "MB，请先清理数据");
            }
            long userCount = usageAggService.currentUsage(tenantId, "user_count");
            if (userCount > newPlan.getUserQuota()) {
                throw new BizException("当前用户数 " + userCount + " 超过目标套餐配额");
            }

            // 结束旧订阅，创建新订阅
            subscriptionMapper.expireActive(tenantId);
            Subscription sub = new Subscription();
            sub.setTenantId(tenantId);
            sub.setPlanId(newPlanId);
            sub.setStartTime(LocalDateTime.now());
            sub.setEndTime(LocalDateTime.now().plusMonths(1));
            sub.setChangeReason(oldPlan.getPriceMonth() > newPlan.getPriceMonth()
                    ? "降级" : "升级");
            subscriptionMapper.insert(sub);

            tenant.setPlanId(newPlanId);
            tenantMapper.updateById(tenant);
            tenantLogMapper.insert(tenantId, "plan_change", operator,
                    oldPlan.getPlanCode() + " -> " + newPlan.getPlanCode());
            refreshTenantCache(tenant);
        } finally {
            redisTemplate.delete(lockKey);
        }
    }
}
```

### 6. 账单生成服务：月度账单与超量计费

```java
@Service
public class BillingService {

    @Autowired
    private TenantMapper tenantMapper;
    @Autowired
    private PlanMapper planMapper;
    @Autowired
    private UsageDailyMapper usageDailyMapper;
    @Autowired
    private BillMapper billMapper;

    /** 每月 1 日生成上月账单：套餐费 + 各指标超量费 */
    @Scheduled(cron = "0 30 1 1 * ?")
    public void generateMonthlyBill() {
        YearMonth period = YearMonth.now().minusMonths(1);   // 上个月
        for (TenantInfo tenant : tenantMapper.selectAll()) {
            if (tenant.getStatus() != 1) {
                continue;
            }
            Plan plan = planMapper.selectById(tenant.getPlanId());

            // 聚合上月用量
            long apiCalls = usageDailyMapper.sumRange(tenant.getId(),
                    "api_call", period.atDay(1), period.atEndOfMonth());
            long storage = usageDailyMapper.peakRange(tenant.getId(),
                    "storage", period.atDay(1), period.atEndOfMonth());

            // 超量费：超出配额部分 × 单价
            long apiOver = Math.max(0, apiCalls - plan.getApiQuota());
            long storageOver = Math.max(0, storage - plan.getStorageQuota());
            BigDecimal overFee = BigDecimal.valueOf(apiOver)
                    .divide(BigDecimal.valueOf(1000))
                    .multiply(plan.getApiOverPrice())
                    .add(BigDecimal.valueOf(storageOver)
                            .divide(BigDecimal.valueOf(1024))
                            .multiply(plan.getStorageOverPrice()));

            Bill bill = new Bill();
            bill.setBillNo("BILL" + period.toString().replace("-", "") + tenant.getId());
            bill.setTenantId(tenant.getId());
            bill.setPeriod(period.toString());
            bill.setPlanFee(plan.getPriceMonth());
            bill.setOverFee(overFee.setScale(2, RoundingMode.HALF_UP));
            bill.setTotalFee(bill.getPlanFee().add(bill.getOverFee()));
            bill.setDetailJson(buildDetail(plan, apiCalls, storage, apiOver, storageOver));
            bill.setStatus(0);
            try {
                billMapper.insert(bill);
            } catch (DuplicateKeyException e) {
                // 本月账单已生成（幂等）
            }
        }
    }

    private String buildDetail(Plan plan, long apiCalls, long storage,
                               long apiOver, long storageOver) {
        // 明细 JSON：各指标用量/配额/超量/单价，供财务核对
        return "{ \"apiCall\": { \"used\": " + apiCalls + ", \"quota\": "
                + plan.getApiQuota() + ", \"over\": " + apiOver + " },"
                + " \"storage\": { \"used\": " + storage + ", \"quota\": "
                + plan.getStorageQuota() + ", \"over\": " + storageOver + " } }";
    }
}
```

### 7. 数据迁移服务：行级模式升级为 schema 隔离

```java
@Service
public class TenantMigrationService {

    @Autowired
    private TenantMapper tenantMapper;
    @Autowired
    private TenantLogMapper tenantLogMapper;
    @Autowired
    private JdbcTemplate jdbcTemplate;
    @Autowired
    private StringRedisTemplate redisTemplate;

    /**
     * 行级 → schema 迁移（合规大客户专属）：
     * 建库 → 建表 → 按 tenant_id 分批复制 → 校验 → 切换模式
     * 全程持租户变更锁，期间该租户请求短暂只读（或接受秒级抖动）
     */
    @Transactional(rollbackFor = Exception.class)
    public void migrateRowToSchema(Long tenantId, String operator) {
        String lockKey = "saas:quota:lock:" + tenantId;
        Boolean locked = redisTemplate.opsForValue()
                .setIfAbsent(lockKey, "1", 300, TimeUnit.SECONDS);
        if (!Boolean.TRUE.equals(locked)) {
            throw new BizException("租户正在变更中");
        }
        try {
            TenantInfo tenant = tenantMapper.selectById(tenantId);
            if (!"row".equals(tenant.getIsolateMode())) {
                throw new BizException("仅行级模式租户可迁移");
            }
            String schemaName = "db_" + tenant.getTenantCode();
            jdbcTemplate.execute("CREATE DATABASE IF NOT EXISTS `" + schemaName
                    + "` DEFAULT CHARACTER SET utf8mb4");
            jdbcTemplate.execute("USE `" + schemaName + "`");
            jdbcTemplate.execute(new String(
                    new ClassPathResource("tenant-init.sql").getInputStream()
                            .readAllBytes(), StandardCharsets.UTF_8));
            // 逐表分批复制：SELECT 共享表 WHERE tenant_id=xx LIMIT 500 -> INSERT 新 schema
            copyTable(tenant.getTenantCode(), "orders");
            copyTable(tenant.getTenantCode(), "products");
            // 校验：两边计数一致才切换
            long srcCount = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM saas_platform.orders WHERE tenant_id = ?",
                    Long.class, tenant.getTenantCode());
            jdbcTemplate.execute("USE `saas_platform`");
            long dstCount = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM `" + schemaName + "`.orders", Long.class);
            if (srcCount != dstCount) {
                throw new RuntimeException("迁移校验失败: 源 " + srcCount + " 目标 " + dstCount);
            }
            // 切换模式并刷新缓存
            tenant.setIsolateMode("schema");
            tenant.setSchemaName(schemaName);
            tenantMapper.updateById(tenant);
            tenantLogMapper.insert(tenantId, "migrate", operator,
                    "row -> schema，迁移表: orders/products");
            refreshCache(tenant);
        } catch (Exception e) {
            throw new BizException("迁移失败: " + e.getMessage() + "（已回滚，租户仍为行级模式）");
        } finally {
            redisTemplate.delete(lockKey);
        }
    }

    private void copyTable(String tenantCode, String table) {
        int offset = 0;
        while (true) {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                    "SELECT * FROM saas_platform." + table + " WHERE tenant_id = ? LIMIT 500 OFFSET ?",
                    tenantCode, offset);
            if (rows.isEmpty()) {
                break;
            }
            for (Map<String, Object> row : rows) {
                // 按表结构拼 INSERT（列名白名单，防注入）
                jdbcTemplate.update(buildInsertSql(table, row), row.values().toArray());
            }
            offset += rows.size();
        }
    }

    private String buildInsertSql(String table, Map<String, Object> row) {
        // 生成 INSERT INTO `db_xxx`.`orders` (col1,col2...) VALUES (?,?...)
        String cols = String.join(",", row.keySet());
        String marks = String.join(",", Collections.nCopies(row.size(), "?"));
        return "INSERT INTO `" + table + "` (" + cols + ") VALUES (" + marks + ")";
    }
}
```

## 实际应用场景

### 场景一：SaaS 客户从免费版升级专业版

某初创公司用了 2 个月免费版，数据量上来后要升级专业版（更多 API 配额、存储、用户数）：

```text
1. 租户管理员在控制台点「升级专业版」，选择按月支付
2. SubscriptionService 加变更锁，校验目标套餐配额（升级方向不做超配额拦截）
3. 结束免费版订阅，创建专业版订阅（次月生效新账单），租户 plan_id 更新
4. Redis 租户缓存刷新，配额检查逻辑立即按新配额生效（拦截器读缓存无感知）
5. 运营在平台端看到该租户套餐变更审计记录（free -> pro，操作人）
6. 下月账单生成：套餐费按专业版月费计，API 超量按专业版单价计
7. 若客户想降级回免费版：系统检测存储用量超免费版配额，提示先清理数据再降级
```

### 场景二：金融客户合规要求独立数据库

某银行客户采购企业版，安全合规要求数据必须物理隔离（不能与其他租户共表）：

```text
1. 运营为该租户发起「迁移到独立 schema」操作（TenantMigrationService）
2. 系统加租户变更锁（5 分钟），期间该租户请求短暂等待
3. 创建独立数据库 db_t_20260801_3，执行 tenant-init.sql 初始化全部业务表
4. 按 tenant_id 分批复制 orders/products 等业务表数据（每批 500 条）
5. 迁移校验：源表与目标表计数一致，不一致自动回滚，租户仍为行级模式
6. 校验通过后租户 isolate_mode 切换为 schema，Redis 缓存刷新
7. 后续该租户请求由 SchemaRouter 自动路由到独立库，业务代码零改动
8. 迁移全程留痕，审计日志可作为合规证据提供给客户
```

### 场景三：月度账单生成与超量计费

月末平台财务要对全部租户出账，某专业版租户当月 API 调用 350 万次（配额 200 万）：

```text
1. 每月 1 日 01:30 定时任务扫描全部正常租户生成上月账单
2. 聚合该租户上月 API 调用量：Redis 日计数落库后 SUM 得到 350 万
3. 读取专业版套餐：月费 299 元，API 配额 200 万，超量单价 0.5 元/千次
4. 计算超量费：(350万 - 200万) / 1000 × 0.5 = 750 元，账单合计 1049 元
5. 账单明细 JSON 记录各指标用量/配额/超量/单价，财务可逐项核对
6. 账单状态置为待支付，推送通知给租户管理员
7. 财务导出全部账单 Excel 对账，与支付系统对接收款后状态置为已支付
```

## 最佳实践与踩坑记录

### 最佳实践

1. 租户隔离框架层兜底：用 MyBatis-Plus TenantLineInnerInterceptor 在 SQL 层强制追加 tenant_id 条件，业务代码零侵入，从机制上杜绝「漏加条件」导致的跨租户泄露
2. ThreadLocal 必须 finally 清理：拦截器 afterCompletion 清理租户上下文，异步任务用 TenantContext.wrap() 显式传递，防止线程池复用串号
3. 默认行级、大客户 schema：隔离强度与成本按需选择；迁移流程（建库 → 复制 → 校验 → 切换）标准化并留痕，可回滚
4. 平台接口与租户接口路径分离：/saas/** 平台库无租户上下文，/api/** 强制租户上下文，从路径上避免两类接口互相污染
5. 用量先 Redis 后落库：高频计数不直接写 MySQL，定时聚合；Redis 丢失可接受（从日志重算），MySQL 只存日聚合结果
6. 租户状态缓存化：拦截器先查 Redis 缓存再放行，停用/启用即时生效，不用重启应用；缓存与库双写保证最终一致
7. 套餐变更加互斥锁：变更期间禁止并发变更与迁移，降级先做配额兼容检查（数据超配额直接拒绝），避免变更出脏状态

### 踩坑记录

```text
坑 1：漏加 tenant_id 导致跨租户数据泄露
结论：某查询没带租户条件，A 租户看到了 B 租户的订单数据，重大安全事故。
原因：隔离依赖开发自觉，业务 SQL 忘了写 WHERE tenant_id = ?。
解法：引入 MyBatis-Plus TenantLineInnerInterceptor，所有 SQL 自动追加 tenant_id 条件；唯一键/索引全部带 tenant_id 前缀；敏感接口做数据级抽查。

坑 2：线程池复用导致租户串号
结论：异步导出任务里，后一个租户的数据被前一个租户的上下文过滤，导出结果错乱。
原因：线程池线程复用时 ThreadLocal 没有清理，且异步任务没有传递租户上下文。
解法：异步任务用 TenantContext.wrap() 包装（进入时 set、结束 finally clear）；拦截器 afterCompletion 统一清理。

坑 3：平台接口被套上租户条件查不到数据
结论：平台管理端查租户列表时 SQL 被拦截器追加了 tenant_id，返回空。
原因：拦截器对所有接口生效，平台侧接口也走了租户上下文。
解法：路径约定 /saas/** 为平台侧接口，拦截器直接放行不设置上下文；租户侧接口强制校验租户头。

坑 4：停用租户还能访问
结论：租户被停用后仍能正常调用接口，运营反馈停用不生效。
原因：停用只改了数据库 status，拦截器每次查库有缓存延迟，且停用后缓存没刷新。
解法：租户状态缓存到 Redis，停用/启用即时刷新缓存；拦截器先查缓存再放行，缓存未命中回源查库。

坑 5：用量直接写库拖垮主库
结论：高峰期每秒几千次 API 请求都 INSERT 用量表，主库写入压力暴涨。
原因：用量计量直接落 MySQL，高频写放大。
解法：计量先 Redis INCR（原子计数），定时任务聚合落库；Redis 抖动可接受，缺失数据从访问日志重算。

坑 6：schema 模式切换后查到空数据
结论：租户迁移到独立库后，接口返回空数据，业务报障。
原因：连接池复用了旧连接，USE schema 只对单连接生效，其他连接还在平台库。
解法：schema 切换基于连接级路由（每次获取连接时按租户设置默认库，或按租户路由到独立数据源），并在拦截器中强制设置；连接归还前清理。

坑 7：降级套餐后数据超配额
结论：企业版降级免费版后，存储用量远超免费版配额，计费与限额失控。
原因：降级时没做配额兼容检查，直接改套餐。
解法：变更前检查当前用量 vs 新套餐配额，超配额拒绝降级并提示清理；允许强制降级时冻结写入（只读模式）直到清理完成。
```

## 相关文档

- [[195-综合项目实战]] — 项目进阶路线总览
- [[68-MyBatis-Plus]] — TenantLineInnerInterceptor 多租户插件使用
- [[74-Spring事务]] — 开通/变更/迁移的事务控制
- [[86-Redis]] — 用量计数与租户状态缓存
- [[108-Redis应用]] — 计数器与缓存一致性场景
- [[82-Security基础]] — 认证授权与租户权限体系
- [[133-Excel]] — 账单导出
- [[191-SpringBoot面试]] — Spring Boot 相关面试考点
