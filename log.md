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

## [2026-08-09] create | Spring Boot 集成定时任务文档

- 新建 spring-boot-scheduled.md，覆盖四层定时任务方案
- @Scheduled 三种调度方式（fixedRate/fixedDelay/cron）+ 线程池配置
- 动态定时任务（ThreadPoolTaskScheduler + REST API + 数据库加载）
- 分布式方案对比：Redis SETNX、Redisson 锁、ShedLock、Quartz 集群、XXL-JOB
- 5 个应用场景：订单超时取消、数据同步、健康检查告警、缓存预热、统计报表
- 与 spring-boot-redis.md、spring-boot-redisson.md 建立交叉引用
