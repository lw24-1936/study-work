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

## [2026-08-18] update | Linux 学习知识库 04 篇章完成

- 编写「04-Shell 脚本编程」7 篇：04.1 Bash 基础、04.2 运算符与流程控制、04.3 函数、04.4 数组与字符串处理、04.5 输入输出重定向、04.6 进程与子 Shell、04.7 调试与规范
- 按「真实执行」标准：写演示脚本实跑（脚本结构/位置参数/函数/数组/重定向/子shell/后台任务/trap/set选项），真实输出嵌入文档
- 全部通过质量校验，行数 165~211
- 同步更新：index.md（+7 条 wikilink，总数 935→942）、linux/README.md 进度表（04 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 05 篇章完成

- 编写「05-用户与权限管理」6 篇：05.1 用户与组、05.2 基本权限、05.3 特殊权限与 ACL、05.4 提权与 sudo、05.5 PAM 可插拔认证、05.6 资源限制
- 按「真实执行」标准：实跑 useradd/usermod/userdel、umask、SUID 程序（passwd/sudo）、visudo -c、ulimit -a、cgroup2 挂载等，真实输出嵌入文档；/etc/shadow 哈希已脱敏
- 全部通过质量校验，行数 157~188
- 同步更新：index.md（+6 条 wikilink，总数 942→948）、linux/README.md 进度表（05 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 06 篇章完成

- 编写「06-磁盘与文件系统」6 篇：06.1 磁盘与分区、06.2 文件系统、06.3 逻辑卷管理 LVM、06.4 RAID、06.5 交换空间、06.6 磁盘配额与工具
- 按「真实执行」标准：实跑 lsblk/df -hT/blkid/fdisk/fstab/swapon/swappiness 等，真实输出嵌入文档（本机双系统：sda ext4 + sdb ntfs，swap 为 8G 文件）
- 全部通过质量校验，行数 144~196
- 同步更新：index.md（+6 条 wikilink，总数 948→954）、linux/README.md 进度表（06 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 07 篇章完成

- 编写「07-进程与作业管理」6 篇：07.1 进程基础、07.2 进程管理命令、07.3 进程优先级、07.4 信号、07.5 进程间通信 IPC、07.6 守护进程
- 按「真实执行」标准：实跑 ps -ef/ps aux/pgrep nginx/kill -l/ipcs/systemctl list-units 等，真实输出嵌入文档（nginx master+8 worker、内核线程 nice=-20、ipcs 当前为空）
- 全部通过质量校验，行数 159~198
- 同步更新：index.md（+6 条 wikilink，总数 954→960）、linux/README.md 进度表（07 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 08 篇章完成

- 编写「08-内存管理」4 篇：08.1 虚拟内存、08.2 内存分配与回收、08.3 Swap 与 OOM、08.4 内存监控与调优
- 按「真实执行」标准：实跑 free -h//proc/meminfo/vmstat/ps 等，真实输出嵌入文档（free used=10Gi 但 available=8.7Gi 的页缓存教材、nacos/chrome/jenkins 内存大户、swappiness=60/overcommit=0/min_free_kbytes=67584）
- 全部通过质量校验，行数 173~186
- 同步更新：index.md（+4 条 wikilink，总数 960→964）、linux/README.md 进度表（08 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 09 篇章完成

- 编写「09-软件包管理」5 篇：09.1 Debian 系、09.2 Red Hat 系、09.3 源码编译、09.4 通用包格式、09.5 软件源与镜像
- 参考 linux-command（wangchujiang.com）资料：DNF 取代 yum（libsolv/hawkey）等背景；Debian + CentOS 双系完整覆盖（apt/dpkg 与 dnf/yum/rpm 对照）
- 真实执行：实跑 apt/dpkg（apt 2.8.3、dpkg 1.22.6、1846 包）、gcc 13.3.0、snap 已装/flatpak 未装、Ubuntu 24.04 deb822 .sources 源格式
- 全部通过质量校验，行数 171~189
- 同步更新：index.md（+5 条 wikilink，总数 964→969）、linux/README.md 进度表（09 篇章 → 已完成）

## [2026-08-18] update | 补充 CentOS 系统内容（01.1 发行版选择）

- 01.1 发行版选择新增「Ubuntu 与 CentOS/RHEL 关键差异」对比表：包管理器（apt/dpkg vs dnf/yum/rpm）、默认文件系统（ext4 vs XFS）、防火墙（ufw vs firewalld）、安全模块（AppArmor vs SELinux）、软件源配置路径
- 新增「选型建议」：学习用 Ubuntu、企业生产用 CentOS/Rocky/AlmaLinux、本库以 Ubuntu 实测为主 + Red Hat 系差异标注
- 说明：命令层面 95% 相同，差异集中在包管理/防火墙/安全模块/文件系统默认值，各章节已按「Red Hat 系」标注

## [2026-08-18] update | Linux 学习知识库 10 篇章完成

- 编写「10-系统启动与 systemd」5 篇：10.1 开机启动流程、10.2 systemd、10.3 编写 Service Unit、10.4 运行级别与 target、10.5 启动排错
- 按「真实执行」标准：实跑 systemd 255、systemctl get-default（graphical.target）、systemd-analyze（发现本机开机 4min55s、docker.service 拖 2min33s）、systemctl --failed（0 失败单元）、ls /boot 内核与 initramfs
- 全部通过质量校验，行数 167~200
- 同步更新：index.md（+5 条 wikilink，总数 969→974）、linux/README.md 进度表（10 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 11、12 篇章完成（一次 2 篇）

- 编写「11-网络基础」6 篇：11.1 TCP/IP 协议栈、11.2 网络配置、11.3 路由与转发、11.4 DNS 与主机名、11.5 网络诊断工具、11.6 TCP 深入
- 编写「12-防火墙与网络安全」4 篇：12.1 netfilter 框架、12.2 nftables、12.3 firewalld 与 ufw、12.4 安全通信
- 真实执行：ip addr（WiFi 192.168.1.167 + docker 网桥 + tailscale）、ip route（默认网关 192.168.1.1）、iptables/nft list ruleset（Docker+tailscale 链）、ufw 未启用、ss -tlnp（22/80/3306/2379/3000/19530）、ss -tan 状态统计、sshd -T（发现 PermitRootLogin yes 安全隐患）
- 全部通过质量校验，行数 166~213
- 同步更新：index.md（+10 条 wikilink，总数 974→984）、linux/README.md 进度表（11、12 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 13、14 篇章完成（一次 2 篇）

- 编写「13-日志管理与监控」5 篇：13.1 系统日志、13.2 日志轮转与集中、13.3 系统监控、13.4 监控体系、13.5 日志分析实战
- 编写「14-定时任务与自动化」4 篇：14.1 cron、14.2 systemd timer、14.3 at 与一次性任务、14.4 任务可靠性
- 真实执行：journalctl/var/log 清单、logrotate 3.21.0 + logrotate.d、监控工具可用性（sysstat 系列齐全、htop 无）、systemctl list-timers（sysstat/logrotate/anacron）、crontab -l（root 空）+ /etc/cron.d（dsh-cert-renew）
- 全部通过质量校验，行数 151~202
- 同步更新：index.md（+9 条 wikilink，总数 984→993）、linux/README.md 进度表（13、14 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 15、16 篇章完成（一次 2 篇）

- 编写「15-系统调用与内核基础」4 篇：15.1 系统调用、15.2 内核模块、15.3 内核参数与伪文件系统、15.4 内核编译与升级
- 编写「16-性能优化与调优」6 篇：16.1 性能分析方法论、16.2 CPU 性能、16.3 内存性能、16.4 IO 性能、16.5 网络性能、16.6 综合调优工具
- 真实执行：strace 6.8（ls 发 75 次系统调用）、lsmod（nvidia 105MB + 239 模块 + 4 内核）、sysctl（3264 参数）、uname（7.0.0-28）、uptime（8 核 load 0.91）、perf 7.0.12、IO 调度器 mq-deadline、/proc/interrupts
- 全部通过质量校验，行数 150~206
- 同步更新：index.md（+10 条 wikilink，总数 993→1003）、linux/README.md 进度表（15、16 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 17、18 篇章完成（一次 2 篇）

- 编写「17-故障排查与调试」4 篇：17.1 排查方法论、17.2 系统追踪、17.3 调试工具、17.4 常见故障案例
- 编写「18-共享存储与数据备份」4 篇：18.1 共享存储、18.2 数据备份与恢复、18.3 文件同步、18.4 存储性能与容量
- 真实执行：strace/ltrace/gdb/addr2line 工具可用性、core_pattern（apport）、ulimit -n=1024 + lsof 330847 打开文件、df/df -i（8%/2%）、rsync 3.2.7、无 nfs/samba 挂载
- 全部通过质量校验，行数 164~196
- 同步更新：index.md（+8 条 wikilink，总数 1003→1011）、linux/README.md 进度表（17、18 篇章 → 已完成）

## [2026-08-18] update | Linux 学习知识库 19、20 篇章完成（完整模板，一次 2 篇）

- 编写「19-高可用与负载均衡」5 篇：19.1 高可用基础、19.2 Keepalived 与 VRRP、19.3 LVS 负载均衡、19.4 HAProxy 与 Nginx、19.5 集群与一致性
- 编写「20-网络服务」5 篇：20.1 Web 服务、20.2 DNS 服务、20.3 DHCP 与时间同步、20.4 文件共享服务、20.5 邮件与消息
- 响应反馈升级为「完整模板」：每篇含 概述/核心概念/工作原理/常用命令与配置/配置文件解析/应用场景实战/性能与调优/安全与权限/故障排查/常见问题/面试题/最佳实践与踩坑记录/相关文档 共 13 节（此前 5~7 节偏薄）
- 真实执行：nginx 1.24.0（3 站点：default/deepseek-harness/new-admin）、dnsmasq/dig 9.18、timedatectl（Asia/Shanghai、NTP active）、etcd 2379、keepalived/haproxy/LVS/chrony/postfix 未装
- 全部通过质量校验，行数 265~291
- 同步更新：index.md（+10 条 wikilink，总数 1011→1021）、linux/README.md 进度表（19、20 篇章 → 已完成）
## [2026-08-19] update | Linux 学习知识库全部完成

- 补全 04.6/04.7、05.1~05.6、11.5/11.6 共 10 篇为完整 13 节模板（01~20 篇章全部完整版）
- 从零完成 21~26 篇章共 29 篇：虚拟化与容器、自动化运维 IaC、安全加固审计、内核源码驱动 eBPF、面试与系统设计、综合项目实战
- 全库 26 篇章 128 篇文档全部「已完成」，内容完整优先（不设行数上限）
## [2026-08-19] update | bigdata 知识库 07/08 章升级为完整 13 节模板

- 07-Hadoop生态 5 篇 + 08-Hive与大数据SQL 2 篇，从偏薄版升级为完整 13 节模板（补核心概念/工作原理/常用命令与配置/配置文件解析/性能与调优/安全与权限/故障排查/常见问题/面试题 9 节）
- 内容完整优先、不设行数上限，保留全部原内容与既有知识点
## [2026-08-19] update | bigdata 知识库 10-Spark 升级为完整 13 节模板

- 10-Spark 6 篇（架构/RDD/Spark SQL/Structured Streaming/性能优化/源码解析）从偏薄版升级为完整 13 节模板
- 内容完整优先、不设行数上限，保留全部原内容与既有知识点
## [2026-08-19] update | 根 README 补充 Linux 知识库

- README.md / README.en.md 补充 Linux 运维方向：数据统计表加 Linux 行（26 篇章 / 128 篇）、目录结构树、知识库总览、五大方向文案
- 合计文档数 918 -> 1046，index.md 注册数更新为 1050

## [2026-08-19] update | Linux 知识库 11-网络基础 6 篇内容完整度扩充（全部 13 节模板）

- 11 章 6 篇从偏薄版（258~358 行）扩充为完整 13 节模板：11.1-TCP-IP 协议栈（660 行）、11.2-网络配置（759 行）、11.3-路由与转发（705 行）、11.4-DNS 与主机名（747 行）、11.5-网络诊断工具（787 行）、11.6-TCP 深入（937 行），合计约 4595 行
- 硬性指标全达标：场景 3~6 个、坑 9~10 个、问答 7~8 条、面试题 8~10 道、故障排查子案例 4~5 个
- 实测输出：ip addr/route/neigh/rule、ping/mtr/tracepath（TTL 推断跳数）、ss -tlnp/-s/-ti（SYN 重传退避 RTO:64000 backoff:6 实证）、tcpdump 真实握手 seq/ack、curl -v TLS 握手、ethtool tx_retries 80 万次、resolvectl/dig 缓存命中统计、15 项 sysctl 实测（tcp_tw_reuse=2、tcp_tw_recycle 已废弃实证）
- 主要新增：四层 vs OSI 对照表、CIDR 换算、ARP 状态机、MTU/MSS/巨型帧、netplan YAML 详解、DHCP DORA、策略路由 fwmark（结合本机 Tailscale 规则）、bond/VLAN、DNS 解析链路图与五步排错法、TCP 队列与 2MSL、Nagle+延迟确认、BBR、长肥管道调优
- Red Hat 系差异标注：ifcfg/nmcli/firewalld 对照表、RHEL 8+ BBR 内置、Red Hat route-<iface> 持久化三方对比
- wikilink 全部有效（脚本校验无失效链接），frontmatter updated=2026-08-19

## [2026-08-19] update | Linux 知识库 12-防火墙与网络安全 4 篇内容完整度扩充（全部 13 节模板）

- 12 章 4 篇从偏薄版（294~331 行）扩充为完整 13 节模板：12.1-netfilter 框架（710 行）、12.2-nftables（687 行）、12.3-firewalld-ufw（858 行）、12.4-安全通信（852 行），合计约 3107 行
- 硬性指标全达标：场景 4~5 个、坑 9~10 个、问答 7~8 条、面试题 7~8 道、故障排查子案例 3~4 个
- 实测输出：iptables --version 证实 nf_tables 后端、update-alternatives 软链、iptables -L/-S/-t nat -S、lsmod 引用数、nf_conntrack 参数与 6 个超时、nft list ruleset（iptables-nft 警告实证）、nft 临时表安全实验、ufw status/app list、firewall-cmd 未装标注、sshd -T 实测 PermitRootLogin/PasswordAuthentication 隐患、DOCKER/DOCKER-USER 链实证、tailscale status、openssl s_client 百度证书链 verify return:1
- 主要新增：钩子点与表对应关系、三条包路径流程图、conntrack 状态匹配、NAT 三兄弟、iptables-save 逐字段解析、DOCKER-USER 链、nft 字节码虚拟机与 iptables-nft 翻译机制、set 区间匹配+动态封禁、nft -f 原子提交、zone 九区语义、runtime vs permanent、firewalld↔ufw 双栏对照、Docker 绕过 ufw 机制、SSH 握手五阶段、TLS 1.2 vs 1.3、WireGuard Noise 协议与 AllowedIPs、SSH 隧道三模式、证书链验证三错
- Red Hat 系差异标注：RHEL 8+ nftables 后端、firewalld 管理 nftables、iptables-services 持久化对照
- 格式修正：12.1/12.2 踩坑记录由 `**坑 N**+bullet` 统一为库内标准 `坑 N：` 三行式
- wikilink 全部有效，frontmatter updated=2026-08-19

## [2026-08-19] update | Linux 知识库 13-日志管理与监控 5 篇内容完整度扩充（全部 13 节模板）

- 13 章 5 篇从偏薄版（245~280 行）扩充为完整 13 节模板：13.1-系统日志（758 行）、13.2-日志轮转与集中（786 行）、13.3-系统监控（946 行）、13.4-监控体系（945 行）、13.5-日志分析实战（902 行），合计约 4337 行
- 硬性指标全达标：场景 4~6 个、坑 9~11 个、问答 8~10 条、面试题 8 道、故障排查子案例 4 个
- 实测输出：journalctl 全命令族（-n/-u/-p/-o json/short-iso/--since/-t/--list-boots/--disk-usage 637.9M）、rsyslog.conf 与 journald.conf 全文、logrotate -d 预演与 timer 触发、du 实测 journal 638M 最大、uptime/top/vmstat/free/df/iostat（r_await 235ms/%util 90.5% 实测）/mpstat/sar/sadf/pidstat、sysstat systemd timer 驱动实证（ENABLED 开关失效坑）、apt 装 prometheus-node-exporter 抓 2655 个 node_* 指标、nginx access.log 合并分析（状态码分布/PV=1118/IP 排行/23 物理字段）、auth.log Accepted 统计、last/lastb、grep -B1 -A2、awk RS 多行堆栈合并、OOM 检查、fail2ban 未装确认
- 主要新增：facility/priority 数值表、/var/log 文件用途表、journald 与 rsyslog 双通道、create vs copytruncate inode 原理、rsyslog 集中服务器 imtcp+模板、logrotate 指令速查表、USE 法/红黑法、top/vmstat/iostat 全列含义表、监控基线健康阈值表、Prometheus 架构与 PromQL、node_exporter 指标对照、Alertmanager 告警路由、Zabbix vs Prometheus 对比、日志分析四步法与命令速查表、fail2ban jail 配置、日志脱敏与合规
- Red Hat 系差异标注：messages vs syslog、secure vs auth.log、RHEL journald 默认持久化、sar 默认启用差异、tuned、/var/log/audit 对照
- 备注：13.4 实测时本机安装了 prometheus-node-exporter（systemd 服务，9100 端口）用于抓取真实指标，未清理（用户未批准卸载命令），如不需要可自行停止并卸载
- wikilink 全部有效，frontmatter updated=2026-08-19

## [2026-08-19] update | Linux 知识库 14-定时任务与自动化 4 篇内容完整度扩充（全部 13 节模板）

- 14 章 4 篇从偏薄版（260~285 行）扩充为完整 13 节模板：14.1-cron（692 行）、14.2-systemd timer（746 行）、14.3-at 与一次性任务（789 行）、14.4-任务可靠性（872 行），合计约 3099 行
- 硬性指标全达标：场景 4~6 个、坑 9~12 个、问答 8~10 条、面试题 8~9 道、故障排查子案例 4~5 个
- 实测输出：/etc/crontab 与 cron.d/daily 目录实拍、grep CRON /var/log/syslog、systemctl list-timers 19 个全量、systemd-analyze calendar 5 连测（含 cron 语法不兼容实测报错）、实测 @every_minute 被 Debian cron 拒绝（纠正网传说法）、systemd-run --on-active/--on-calendar 一次性任务实测（--collect 自动回收、0 timers listed）、flock -n 非阻塞与阻塞 22s 拿锁实测、timeout 124 超时实测、可靠任务模板脚本全场景（成功 0/并发冲突 1/超时 124）、at 未安装标注
- 主要新增：crontab 五字段详解与特殊字符串、cron vs anacron、@reboot 场景、cron.allow/deny、Monotonic vs Realtime、OnCalendar 三段式语法、Persistent 补跑、AccuracySec vs RandomizedDelaySec、cron→timer 迁移对照表、at 队列与权限、systemd-run Transient unit、flock 全参数、systemd 可靠性字段表、分布式锁三原则、幂等三招、错峰与告警防抖
- Red Hat 系差异标注：cronie vs cron、anacron 机制、/etc/anacrontab、RHEL 7 systemd 219 无秒精度/RandomizedDelaySec、at 包差异
- 实测发现并纠正：@every_minute 在 Debian cron 不支持（bad time specifier）
- wikilink 全部有效，frontmatter updated=2026-08-19
