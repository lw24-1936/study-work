# 操作日志

> 按时间顺序记录所有知识库操作。只追加不修改。
> 格式：`## [YYYY-MM-DD] 操作类型 | 内容摘要`

## [2026-08-09] create | 知识库初始化

- 创建 SCHEMA.md、index.md、log.md
- 建立目录结构：concepts/、comparisons/、troubleshooting/
- 初始化标签体系：spring-boot, redis, distributed, cache 等

## [2026-08-09] update | Spring Boot 集成 Redisson 文档重构

- 文件移至 spring-boot-redisson.md，遵循 wiki 命名规范
- 增加 application.yml 配置方式详解（3.2 节），覆盖单机/哨兵/集群
- 增加两种配置方式对比表（3.4 节）
- 增加版本兼容注意事项（10.7 节）
- 去掉 emoji 装饰符号，统一使用纯文本标记
- 添加 YAML frontmatter 和交叉引用能力

## [2026-08-09] create | Spring Boot 集成 Redis 文档

- 新建 spring-boot-redis.md，覆盖 Spring Data Redis 全部基础操作
- 内容：RedisTemplate 5 种数据类型操作、Spring Cache 注解、Pipeline、发布订阅、序列化
- 5 个应用场景：短信验证码、分布式 Session、实时排行榜、接口幂等、分布式 ID
- 踩坑记录：缓存穿透/击穿/雪崩、大 Key、keys 命令、@Cacheable 失效、一致性方案
- 与 spring-boot-redisson.md 建立交叉引用

## [2026-08-10] create | Spring Boot 集成 MyBatis 文档

- 新建 spring-boot-mybatis.md，覆盖 MyBatis 全栈集成
- 内容：XML Mapper 基础 CRUD、注解开发、动态 SQL 七大标签、高级结果映射（association/collection）、PageHelper 分页、MyBatis-Plus 增强、多数据源配置
- TypeHandler 自定义类型处理（枚举/JSON）、拦截器插件机制
- 5 个应用场景：用户搜索+分页、订单联表查询、批量导入 Excel、组合筛选动态查询、乐观锁库存扣减
- 踩坑记录：#{} vs ${}、N+1 查询、一级缓存陷阱、PageHelper 注意事项等 10+ 常见问题
- 移除 emoji，纯文本标记，与现有文档风格一致
- 与 spring-boot-redis.md 建立交叉引用（MyBatis 二级缓存集成 Redis）

## [2026-08-10] create | Spring Boot 集成 MyBatis-Plus 文档

- 新建 spring-boot-mybatis-plus.md，MyBatis-Plus 独立专题文档
- 内容：BaseMapper 通用 CRUD、Lambda 条件构造器（4 种 Wrapper）、分页插件、6 种主键策略、逻辑删除、自动填充、乐观锁、代码生成器、多租户、字段类型处理器、数据权限拦截器
- 2 个完整应用场景：用户管理系统 CRUD（Controller+Service+Mapper 三层）、订单系统（乐观锁扣库存 + 多表联合查询）
- 8 个踩坑记录：selectOne 多条异常、与 MyBatis Starter 冲突、3.5.5+ 分页默认值变化、逻辑删除关联查询漏数据、批量操作伪批量、乐观锁返回 0 不抛异常、exist=false 在 XML resultMap 无效、自动填充 strictFill 陷阱
- 所有条件构造器示例使用 Lambda 方式，避免字符串硬编码
- 与 spring-boot-mybatis.md 建立交叉引用

## [2026-08-09] create | Spring Boot 集成定时任务文档

- 新建 spring-boot-scheduled.md，覆盖四层定时任务方案
- @Scheduled 三种调度方式（fixedRate/fixedDelay/cron）+ 线程池配置
- 动态定时任务（ThreadPoolTaskScheduler + REST API + 数据库加载）
- 分布式方案对比：Redis SETNX、Redisson 锁、ShedLock、Quartz 集群、XXL-JOB
- 5 个应用场景：订单超时取消、数据同步、健康检查告警、缓存预热、统计报表
- 与 spring-boot-redis.md、spring-boot-redisson.md 建立交叉引用
