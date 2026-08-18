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

## [2026-08-13] create | 前端文档 操作系统

- 文件名：01.2-操作系统.md
- 摘要：操作系统核心概念：进程/线程/协程、上下文切换与调度、内存管理（虚拟内存/页表/Page Fault）、文件系统与文件描述符、Socket、系统调用、IPC、信号、权限、用户态与内核态，结合浏览器多进程架构与 Node.js 场景讲解

## [2026-08-13] create | 前端文档 Linux

- 文件名：01.3-Linux.md
- 摘要：Linux 文件系统、Shell/Bash/Zsh、文本三剑客、find/xargs、网络与传输工具、进程与网络排查、systemd/cron、权限与环境变量、日志，前端部署排障视角

## [2026-08-13] create | 前端文档 Git

- 文件名：01.4-Git.md
- 摘要：Git 从基础概念到协作工作流：commit/branch/tag、merge/rebase/cherry-pick、reset/revert/stash/reflog、diff/blame/bisect、submodule/worktree、hooks、Conventional Commits、Git Flow 与主干开发、Monorepo、PR 与 Code Review

## [2026-08-13] create | 前端文档 IDE 与开发环境

- 文件名：01.5-IDE 与开发环境.md
- 摘要：前端开发环境全链路：VS Code 与 JetBrains、Chrome/Firefox DevTools、Node.js、npm/pnpm/Yarn 包管理器、Corepack、nvm/fnm/Volta 版本管理、Docker、Dev Container、WSL

## [2026-08-14] 整理 | 项目结构整理

- 新建 spring-boot/ 目录，将 8 篇 Spring Boot 集成文档移入（aop/email/mybatis/mybatis-plus/rabbitmq/redis/redisson/scheduled）
- 删除空目录 concepts/、comparisons/、troubleshooting/（模式一遗留，未被使用）
- 生成根目录 README.md（知识库总览、目录结构、文档规范）
- index.md：集成实践节加 spring-boot/ 目录说明，移除「概念解析/对比分析/排错笔记」三个空章节，更新日期为 2026-08-14

## [2026-08-14] update | README 优化与多语言支持

- README.md 参照优秀开源项目风格重写：语言切换、shields 徽章、锚点目录、特性、数据统计、知识库总览
- 新增 README.en.md 英文版，结构与中文版一致
- 默认简体中文（README.md），顶部提供 简体中文 / English 切换

## [2026-08-14] update | README 优化 + Obsidian 阅读说明

- README.md / README.en.md 新增「用 Obsidian 阅读 / Reading with Obsidian」章节：知识库用 [[wikilink]] + frontmatter tags（Obsidian 原生语法），整库可直接作为 Vault 打开
- 副标题、徽章行、特性列表、TOC、快速开始同步加入 Obsidian 相关说明（badge 用 7c3aed 紫）
- 说明双向链接/反向链接/关系图谱/标签面板/全文搜索开箱即用
## [2026-08-14] create | 大数据学习知识库（bigdata/）

- 基于《大数据学习知识库总目录》新建「大数据学习知识库」，共 30 篇章、133 篇文档
- 覆盖：学习路线/计算机基础/数学/数据结构算法/SQL/存储/文件格式/Hadoop/Hive/Kafka/Spark/Flink/Trino/数仓/Lakehouse/CDC/实时数仓/大数据算法/数据科学/数据治理/工程化/MLOps/分布式/性能优化/云原生/数据架构/指标体系/源码与论文/安全隐私/面试/项目实战
- 总目录预处理：重复篇章合并（17/18 大数据算法→「17-大数据算法」、35/39 源码与论文→「35-源码与论文」、37/40 面试与系统设计→「37-面试与系统设计」），41/42 元信息篇章不建目录
- 编写方式：骨架 scaffold + delegate_task 并行委派（4 篇/子代理批）+ 手工编写核心篇章（14 数据湖/Lakehouse、17 大数据算法部分、35 源码与论文、37 面试、38 项目）
- 全部 133 篇通过质量校验：frontmatter 完整、围栏偶数、无 emoji、踩坑非空、wikilink 与磁盘一一对应（0 问题）
- 同步更新：index.md（+133 条 wikilink，总数 920）、README.md / README.en.md（四大方向、数据统计、目录树、知识库总览）、bigdata/README.md 进度表

## [2026-08-15] create | 计算机学习链接汇总

- 解析《常用计算机学习链接汇总.xlsx》6 个工作表，去重后 200 条链接
- 按 14 个技术领域重新分类：学习路线与面试、在线文档与教程、Java 后端框架、Java 工具库与开源项目、数据库缓存与中间件、前端框架与构建工具、前端 UI 组件库与模板、数据可视化与地图、动画与 3D、CSS 与设计资源、表单富文本与低代码、AI 算法与大数据、DevOps 容器与运维、效率与协作工具
- 修正源表数据错误：mini-spring 的链接误填为 mini-spring-cloud 地址，按项目真实仓库地址补为独立条目
- 注册到 index.md「参考资源」分区

## [2026-08-18] create | Linux 学习知识库（linux/）

- 基于《Linux学习知识库总目录》新建「Linux 学习知识库」，共 26 篇章、128 篇骨架文档（全部「待编写」状态）
- 覆盖：学习路线/系统基础/文本三剑客/Shell 脚本/权限/磁盘文件系统/进程/内存/软件包/systemd/网络/防火墙/日志监控/定时任务/系统调用/性能调优/故障排查/存储/高可用/网络服务/虚拟化容器/自动化运维/安全加固/内核 eBPF/面试/项目实战
- 总目录预处理：01 扁平篇章→单文件「01.1-学习路线与开发环境.md」、26 项目篇章（## 项目 NN：编号）→ 8 篇「26.1~26.8」、27/28/29 元信息篇章（能力认证清单/目录结构/文档模板）不建目录
- 自定义 scaffold 脚本（scaffold-kb.py 无法处理扁平+项目篇章），一次性生成 26 目录 + 128 骨架 + README 进度表
- 质量校验通过：无空目录、无「（待补充）」占位符、无 emoji、围栏偶数、frontmatter 完整
- 同步更新：index.md（+1 条入口链接 [[linux/README]]，总数 921→922）、linux/README.md 进度表（26 篇待编写）

## [2026-08-18] update | Linux 学习知识库 01 篇章完成

- 编写「01.1-学习路线与开发环境.md」：Linux 运维/SRE/平台工程师能力模型、五阶段学习路线与先修关系、发行版选型、虚拟机/WSL2/Vagrant/Packer、SSH 密钥免密、Shell 环境与别名、tmux/screen、Vim/Neovim、编译工具链、curl/wget/scp/rsync、man/tldr 帮助、容器化实验与故障演练
- 13 个知识点章节 + 概述 + 2 个应用场景实战 + 5 条踩坑，435 行，通过质量校验（frontmatter 完整/围栏偶数/无 emoji/踩坑非空/wikilink 与磁盘一一对应）
- 同步更新：index.md（+1 条 wikilink [[01.1-学习路线与开发环境]]，总数 922→923）、linux/README.md 进度表（01 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 02 篇章完成

- 编写「02-Linux 系统基础」6 篇：02.1 内核与发行版、02.2 文件系统层级标准 FHS、02.3 文件与目录操作、02.4 文件类型与属性、02.5 压缩与归档、02.6 重定向与管道
- 每篇含概述 + 知识点章节 + 3 个应用场景实战 + 5~6 条踩坑记录，行数 191~255，全部通过质量校验（frontmatter 完整/围栏偶数/无 emoji/踩坑非空/wikilink 与磁盘一一对应）
- 同步更新：index.md（+6 条 wikilink，总数 923→929）、linux/README.md 进度表（02 篇章 → 已完成）

## [2026-08-18] update | Linux 知识库 01/02 篇章按「真实执行」标准优化

- 逐个执行文档命令并在本机（Ubuntu 24.04.4 LTS + nginx + docker）验证，把真实输出以 ```text 块贴入文档并逐条解释
- 真实发现：本机 Docker 跑 nacos/jenkins/rabbitmq/milvus/mysql/redis 等十几个容器；nginx 日志 824 次请求中 401 占 527 条（鉴权拦截为主）；/var 占 36G；压缩对比 zstd(511B) < xz(892B) < bzip2(957B) < gzip(12K)；4 个已装内核（6.17.0-29/35/40 + 7.0.0-28 HWE）
- 应用场景贴合企业实际（磁盘满定位、访问日志分析、内核识别、备份校验、环境隔离等）
- 新增标准（后续所有学习文档沿用）：命令逐个实际执行并贴真实输出 + 逐条解释 + 企业场景；需网页访问用浏览器截图

## [2026-08-18] update | Linux 学习知识库 03 篇章完成

- 编写「03-文本处理与三剑客」6 篇：03.1 正则表达式、03.2 grep、03.3 sed、03.4 awk、03.5 其他文本工具、03.6 实战案例
- 按「真实执行」标准：命令逐个在本机实跑（含真实 nginx 日志分析），真实输出以 ```text 块嵌入并逐条解释
- 真实发现：/api/pair/heartbeat 接口 527 次全 401（鉴权失败客户端反复重试）、状态码 401:527 / 200:279 / 101:18、请求路径 TOP 榜
- 全部通过质量校验（frontmatter/围栏/emoji/踩坑/wikilink），行数 165~268
- 同步更新：index.md（+6 条 wikilink，总数 929→935）、linux/README.md 进度表（03 篇章 → 已完成）
