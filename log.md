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

## [2026-08-10] create | Spring Boot 集成 RabbitMQ 文档

- 新建 spring-boot-rabbitmq.md，RabbitMQ 全栈集成专题文档
- 内容：4种交换机（Direct/Fanout/Topic/Headers）完整示例、RabbitTemplate 发送（对象/Message/后处理器）、@RabbitListener 接收（手动Ack/并发/重试/@RabbitHandler多态分发）、JSON序列化（Jackson2JsonMessageConverter + TypeId映射）、可靠性三环节（生产者Confirm/Return、消息持久化、消费者Ack）、死信队列架构、延迟消息两种方案（TTL死信 vs Delay Exchange插件）、消息幂等三种方式（DB/Redis/业务状态）
- 2个完整应用场景：订单通知系统（邮件+短信 Direct Exchange 路由）、文章审核系统（重试3次 + 死信人工处理）
- 8个踩坑记录：启动连接失败、@RabbitListener未纳入Spring容器、序列化不匹配、无限重试、忘ack、事务不一致、延迟消息顺序问题、消息头过大
- 与 spring-boot-redisson.md、spring-boot-scheduled.md 建立交叉引用


## [2026-08-10] create | Spring Boot 集成邮件文档

- 新建 spring-boot-email.md，邮件发送全栈集成专题
- 内容：JavaMailSender（文本/HTML/附件/内联图片）、模板邮件（Thymeleaf + FreeMarker）、异步发送（@Async + 独立线程池）、发送可靠性（落库 + 3次重试 + 定时扫失败记录）、多账号发送、发送记录追踪（AOP + 失败率告警）
- 2个完整应用场景：注册验证码（Redis存储 + 频率控制）、异常告警（全局异常拦截 + 资源巡检）
- 9个踩坑记录：25端口被封、授权码非密码、@Async不生效、连接池耗尽、附件中文乱码、Gmail布局错乱、FileSystemResource路径、QQ每日上限、Gmail应用专用密码
- 与 spring-boot-redis.md、spring-boot-scheduled.md、spring-boot-rabbitmq.md 建立交叉引用


## [2026-08-10] create | Spring Boot 集成 AOP 文档

- 新建 spring-boot-aop.md，AOP 全栈集成专题
- 内容：AOP 核心概念、五种通知类型（Before/After/AfterReturning/AfterThrowing/Around）+ 执行顺序、6 种切点表达式（execution/@annotation/within/args/bean/组合）、@Order 洋葱模型
- 16 个完整应用场景：操作日志、接口耗时、权限校验、参数校验、声明式缓存、分布式锁、限流、幂等、异常重试、数据脱敏、加解密、XSS过滤、ThreadLocal清理、统一异常记录、读写分离、全局 traceId——每个场景含注解定义 + 切面实现 + 使用示例
- 7 个踩坑记录：同类内部调用不走代理、final/private 方法无效、@Around 吞异常、切点范围过大、忘调 proceed()、@Transactional 顺序冲突、忘加 @Component
- 与 spring-boot-redisson.md、spring-boot-redis.md、spring-boot-mybatis-plus.md 建立交叉引用

## [2026-08-13] update | 49-Java常见问题 面试文档全面扩充

- 以 15 年高级后端视角重写 9 篇面试文档（186-194），每题从 3-5 行简短回答扩充为完整技术点 + 常见面试题
- 186-Java基础面试：新增异常体系、泛型擦除/PECS、反射、注解、值传递、深拷贝浅拷贝、Object 方法、Java 8 特性、BigDecimal 精度、基本类型与包装类(Integer 缓存)
- 187-集合面试：新增 JDK7 死循环、负载因子 0.75、红黑树阈值 8/6、fail-fast 与 fail-safe、CopyOnWriteArrayList、LinkedHashMap LRU、阻塞队列
- 188-并发面试：新增线程基础(创建/状态/sleep 与 wait)、ThreadLocal 内存泄漏、原子类/LongAdder、CountDownLatch/CyclicBarrier/Semaphore、死锁、happens-before
- 189-JVM面试：新增对象创建与内存布局、四种引用、逃逸分析、JVM 调优参数、排查工具、破坏双亲委派(SPI/Tomcat)
- 190-Spring面试：新增 Bean 作用域、BeanFactory 与 ApplicationContext、FactoryBean、事件机制、设计模式、事务隔离级别
- 191-SpringBoot面试：新增配置文件加载顺序、@ConfigurationProperties、Spring Boot 3 变化、fat jar、优雅停机
- 192-SpringCloud面试：新增 CAP 理论、Sentinel 限流、分布式事务(Seata/TCC/SAGA)、链路追踪、服务雪崩
- 193-Redis面试：新增底层数据结构(SDS/跳表)、过期与淘汰策略、事务与 Lua、大 key/热 key
- 194-MySQL面试：新增存储引擎、redo/undo/binlog 与两阶段提交、主从复制、分库分表、count(*) 与深分页优化
- 同步更新 index.md 摘要与 Java_全栈学习知识体系总目录.md 第 49 篇主题清单
## [2026-08-13] create | 内部类专题文档

- 新建 java-fullstack/02-Java面向对象/InnerClass.md，补齐内部类知识（原知识库中无系统讲解，仅零散提及）
- 内容：四种内部类（成员/静态/局部/匿名）语法与区别、编译原理（Outer$Inner.class、this$0、access$xxx 桥接方法）、访问私有成员原理、4 个应用场景（迭代器/Builder/Holder 单例/事件监听）、5 条踩坑记录（内存泄漏/序列化/this 语义/局部变量 final/静态成员限制）
- 186-Java基础面试 补"内部类"面试小节（5 题）
- 同步更新 index.md 第二篇条目、总目录第二篇补充主题
## [2026-08-13] create | 前端完整知识库目录骨架

- 按「前端完整知识库总目录.md」搭建 frontend-fullstack/ 目录结构
- 103 个篇章目录（01-计算机基础 到 103-前端职业方向）+ 416 个子主题骨架文件
- 每篇骨架含 frontmatter + 知识点清单（来自总目录），状态「待编写」
- README.md 含完整目录树 + 进度追踪表（103 篇全部待编写）
- index.md 加「前端知识库」入口，顺手修复重复 12 次的「概念解析」标题

## [2026-08-13] create | 前端文档 计算机组成原理

- 文件名：01.1-计算机组成原理.md
- 摘要：CPU/GPU/ALU/寄存器/指令集、存储层次与 Cache、内存与虚拟内存、SSD/HDD、IO/DMA/中断、总线、字节序、字符编码，前端视角解析缓存友好遍历/TypedArray/位运算/乱码
