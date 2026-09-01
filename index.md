# 学习笔记索引

> 内容目录。每篇文档附一句话摘要。先读这里找到相关文档。
> 最后更新：2026-09-01 | 总文档数：1189

## 参考资源

> 常用计算机学习链接的归类索引，来源《常用计算机学习链接汇总.xlsx》。

- [[计算机学习链接汇总]] — 200+ 条计算机学习链接，按 14 个领域分类：Java 后端、前端框架/UI/可视化/动画、AI 算法大数据、DevOps 与效率工具

## 集成实践

> 位于 spring-boot/ 目录，共 9 篇 Spring Boot 集成类文档。

- [[spring-boot-redis]] — Spring Boot 集成 Redis 详解：RedisTemplate 五种数据类型、Spring Cache 注解、Pipeline、序列化，含 5 个应用场景
- [[spring-boot-redisson]] — Spring Boot 集成 Redisson 详解：分布式锁、集合、限流器、布隆过滤器，含 6 个应用场景
- [[spring-boot-scheduled]] — Spring Boot 集成定时任务详解：@Scheduled、动态调度、分布式锁、Quartz、XXL-JOB，含 5 个应用场景
- [[spring-boot-mybatis]] — Spring Boot 集成 MyBatis 详解：XML/注解 Mapper、动态 SQL、高级结果映射、PageHelper、MyBatis-Plus、多数据源，含 5 个应用场景
- [[spring-boot-aop]] — Spring Boot 集成 AOP 详解：五种通知类型、切点表达式、16个应用场景（日志/耗时/权限/缓存/锁/限流/幂等/脱敏/加解密/重试/XSS/读写分离/traceId等）
- [[spring-boot-email]] — Spring Boot 集成邮件详解：JavaMailSender、HTML/附件/内联图片、Thymeleaf/FreeMarker模板、异步发送、可靠性（落库+重试）、多账号、验证码与异常告警场景
- [[spring-boot-rabbitmq]] — Spring Boot 集成 RabbitMQ 详解：4种交换机、消息发送接收、JSON序列化、可靠性投递、死信队列、延迟消息、幂等设计，含2个完整应用场景
- [[spring-boot-mybatis-plus]] — Spring Boot 集成 MyBatis-Plus 详解：BaseMapper、Lambda 条件构造器、分页插件、主键策略、逻辑删除、自动填充、乐观锁、代码生成器、多租户、数据权限，含 2 个完整应用场景
- [[spring-boot-tika]] — Spring Boot 文件识别与 Apache Tika 详解：文件签名（魔数）原理与常用签名表、自研魔数匹配、Tika 检测/文本抽取/元数据/OCR/自定义 MIME，对比 JDK/Spring/libmagic 等替代方案，含 3 个应用场景

## Java 全栈基础

> 基于 Java 全栈学习知识体系编排，目前已覆盖前置章节 + 第一篇到第五十篇，共 233 篇。

### 前置 — 学习路线与开发环境

- [[00.1-Java语言概述]] — Java 发展历史、JDK/JRE/JVM、LTS 版本、OpenJDK vs Oracle JDK
- [[00.2-Java开发环境]] — JDK 安装、JAVA_HOME、javac/java/jar 命令、jps/jstack/jmap 等诊断工具
- [[00.3-Java IDE]] — IntelliJ IDEA 项目结构、常用快捷键、Debug/条件断点/远程调试
- [[00.4-构建工具]] — Maven 生命周期/坐标/依赖/Scope/Profile/Plugin、Gradle 基础

### 第一篇 — Java 语言基础

- [[01-Java基础语法]] — 第一个程序、注释、标识符、变量、8 种基本数据类型、类型转换
- [[02-运算符]] — 算术/关系/逻辑/位/赋值/三元运算符、自增自减、instanceof、短路求值
- [[03-流程控制]] — if/switch/switch表达式、for/while/do-while、break/continue/标签语句
- [[04-数组]] — 一维/二维/多维数组、初始化/遍历/复制/排序、Arrays 工具类、可变参数
- [[05-字符与字符串]] — char/String/StringBuilder/StringBuffer、字符串常量池、编码与格式化

### 第二篇 — Java 面向对象

- [[06-面向对象基础]] — 类与对象、属性/方法/构造方法、this、方法重载、对象生命周期
- [[07-封装]] — private/public/protected/默认访问修饰符、Getter/Setter、JavaBean 规范、不可变对象
- [[08-继承]] — extends、方法重写、super、向上/向下转型、构造方法继承链
- [[09-多态]] — 编译时多态（重载）vs 运行时多态（重写）、动态绑定、虚方法调用
- [[10-抽象类]] — abstract 类与方法、抽象类继承、模板方法模式
- [[11-接口]] — interface/implements、default/static 方法、函数式接口、接口多继承
- [[12-Object类]] — equals/hashCode/toString/clone、wait/notify/notifyAll、getClass
- [[13-Java包与访问控制]] — package/import/static import、四种访问修饰符详解
- [[InnerClass]] — 内部类：成员/静态/局部/匿名四种、编译原理(this$0/access$xxx)、Builder 与 Holder 单例、内存泄漏与序列化踩坑

### 第三篇 — Java 核心 API

- [[14-包装类型]] — 八种包装类、自动装箱拆箱、Integer 缓存(-128~127)、valueOf vs parseInt、Number 抽象类
- [[15-BigDecimal与BigInteger]] — 浮点误差原理、字符串构造、8 种舍入模式、金融计算、大数运算
- [[16-日期与时间]] — Date/Calendar 旧 API vs java.time 新 API、LocalDate/Instant/ZonedDateTime、DateTimeFormatter
- [[17-正则表达式]] — Pattern/Matcher、字符类/量词/分组/捕获组、前瞻后瞻、正则替换、ReDoS 防范
- [[18-Java枚举]] — enum 属性/构造/抽象方法、EnumSet 位向量、EnumMap 数组索引、状态机与策略模式
- [[19-Java注解]] — @Retention/@Target/@Repeatable、运行时反射读取、编译时 APT 注解处理器、自定义校验框架
- [[20-Java异常]] — Throwable→Error+Exception、Checked vs Unchecked、try-with-resources、异常链、全局异常处理器

### 第四篇 — Java 集合框架

- [[21-Collection]] — 集合框架全景、List/Set/Queue/Deque 接口、数组互转、遍历方式、Collections 工具类、选型决策树
- [[22-List]] — ArrayList 1.5倍扩容、LinkedList 双向链表、Vector/Stack 淘汰、CopyOnWriteArrayList 写时复制、subList 视图陷阱
- [[23-Set]] — HashSet/LinkedHashSet/TreeSet/EnumSet 对比、equals+hashCode 契约、NavigableSet 范围查询
- [[24-Map]] — HashMap 8 种实现、LinkedHashMap LRU、TreeMap 红黑树、WeakHashMap 弱引用、EnumMap/IdentityHashMap、computeIfAbsent/merge
- [[25-Queue]] — Queue/Deque 两套 API、ArrayDeque 循环数组(替代 Stack)、PriorityQueue 二叉堆、BlockingQueue 生产者消费者
- [[26-集合底层原理]] — ArrayList 扩容源码、HashMap hash 算法 `(h ^ h>>>16)`、链表8树化6退化、JDK 7头插死循环→JDK 8尾插、ConcurrentHashMap CAS+synchronized 桶锁、Fail-Fast modCount

### 第五篇 — Java 泛型

- [[27-泛型基础]] — 泛型类/接口/方法/构造器、类型边界 `<T extends Number>`、类型参数命名约定(E/K/V/T)、原始类型陷阱、泛型数组限制
- [[28-泛型高级]] — 类型擦除三规则(源码→字节码)、`? extends T`(生产者) vs `? super T`(消费者)、PECS 原则推导、`Comparable<? super T>` 经典设计、桥方法原理

### 第六篇 — Java 函数式编程

- [[29-Lambda]] — Lambda 语法变体、函数描述符、effectively final 变量捕获、4种方法引用、this 语义差异、invokedynamic 实现原理
- [[30-函数式接口]] — Function/Consumer/Supplier/Predicate 四大家族、原始类型特化、Bi 双参数系列、andThen/compose/and/or/negate 组合
- [[31-Stream]] — 惰性求值三段式、filter/map/flatMap/reduce/collect、groupingBy 分组、IntStream 原始流、并行流适用条件
- [[32-Optional]] — of/ofNullable/empty、map/flatMap 链式安全访问、orElse vs orElseGet 执行时机陷阱、ifPresentOrElse、反模式

### 第七篇 — Java IO

- [[33-IO基础]] — 字节流/字符流四大基类、装饰器模式叠加链、缓冲流性能原理、PrintStream/PrintWriter、InputStreamReader 编码桥、DataStream/ObjectStream、Piped Streams
- [[34-文件操作]] — File(旧) vs Path+Files(新)、Files 创建/复制/移动/删除、walk/list/find 遍历、POSIX 权限、磁盘空间、临时文件管理
- [[35-NIO]] — Buffer 四属性状态机、Channel 双向管道、FileChannel.transferTo 零拷贝、MappedByteBuffer 内存映射、Selector 多路复用事件循环、Scatter/Gather
- [[36-NIO.2]] — WatchService 文件监控(inotify/kqueue)、FileVisitor 回调生命周期、异步 IO Future/CompletionHandler、文件热加载实战
- [[37-网络编程]] — TCP Socket/ServerSocket、UDP DatagramSocket 广播多播、URL/HttpURLConnection POST、端口扫描/局域网发现、InetAddress 解析

### 第八篇 — Java 并发编程

- [[38-线程基础]] — 进程vs线程、四种创建方式、6种状态生命周期、start vs run、sleep/interrupt/join、daemon 线程
- [[39-synchronized]] — 三种用法(实例/静态/代码块)、Monitor 机制、锁升级(偏向→轻量→重量)、底层 monitorenter/monitorexit、wait/notify/notifyAll
- [[40-volatile]] — Java 内存模型可见性、有序性禁止重排、不保证原子性、happens-before 原则、内存屏障、DCL 单例必须 volatile
- [[41-Lock]] — ReentrantLock(tryLock/公平/可中断)、Condition、ReadWriteLock、StampedLock 乐观读、LockSupport park/unpark 底层原语、AQS 框架原理、Java 锁全景对比(互斥/读写/信号量/无锁/原语)
- [[42-原子类]] — CAS 原理、AtomicInteger/LongAdder/LongAccumulator、AtomicReference、ABA 问题与 AtomicStampedReference、无锁栈
- [[43-并发集合]] — ConcurrentHashMap 原子复合操作、CopyOnWriteArrayList 写时复制、BlockingQueue/ConcurrentLinkedQueue/ConcurrentSkipListMap
- [[44-线程池]] — Executor 框架、ThreadPoolExecutor 核心参数、四种拒绝策略、Future/FutureTask、CompletionService、监控与动态调参
- [[45-CompletableFuture]] — thenApply/thenCompose/thenCombine 链式编排、allOf/anyOf 并行聚合、exceptionally/handle/whenComplete 异常处理
- [[46-ForkJoin]] — ForkJoinPool/RecursiveTask、Work Stealing 工作窃取、分治拆分阈值、fork+compute 高效模式
- [[47-虚拟线程]] — JDK 21 虚拟线程、Thread.ofVirtual/newVirtualThreadPerTaskExecutor、Carrier mounting、synchronized pinning 陷阱、ThreadLocal 替代

### 第九篇 — JVM

- [[48-JVM基础]] — JDK/JRE/JVM 关系、JVM 整体架构图、Class 文件 0xCAFEBABE、字节码指令分类、HotSpot 版本演进
- [[49-JVM内存结构]] — 5+1 区全景（程序计数器/栈/堆/Metaspace/直接内存）、栈帧结构、分代模型(Eden+S0/S1+Old)、String Pool 迁移、Metaspace vs PermGen
- [[50-类加载机制]] — 加载→验证→准备→解析→初始化五阶段、三层类加载器、双亲委派源码、SPI 破坏/Tomcat 破坏/模块化破坏、自定义 ClassLoader、类隔离
- [[51-JVM字节码]] — Class 文件 10 段结构、常量池字面量+符号引用、方法 Code 属性、5 种 invoke 指令、javap -c 实战、操作码速查表
- [[52-JVM垃圾回收]] — 可达性分析/GC Roots、三色标记+漏标处理、分代回收全流程、Minor/Major/Full GC 对比、四种引用(强/软/弱/虚)、GC 日志解读
- [[53-垃圾收集器]] — Serial/Parallel/CMS/G1/ZGC/Shenandoah/Epsilon 七大收集器、G1 Region+RSet+Mixed GC、ZGC 染色指针+读屏障(<1ms)、JDK 版本选型矩阵
- [[54-JVM调优]] — 四步调优法、堆/栈/Metaspace 参数、GC 日志+Heap Dump+Thread Dump 三大分析手段、CPU 飙高/内存泄漏/死锁/OOM 排查流程、容器化 MaxRAMPercentage
- [[55-JVM工具]] — jps/jstack/jmap/jstat/jcmd/jinfo 命令行六件套、jconsole/VisualVM 可视化、JFR 生产 Profiler、Arthas trace/jad/watch/ognl 在线诊断

### 第十篇 — Java 反射与动态编程

- [[56-反射]] — Class 入口四种获取、Constructor.newInstance/Method.invoke/Field.getSet 三大操作、Modifier 修饰符解析、泛型反射(TypeToken 模式)、注解反射、setAccessible 模块化限制、Bean 拷贝/ORM 映射/配置注入实战
- [[57-动态代理]] — JDK Proxy(接口+InvocationHandler)、CGLIB(子类继承+MethodInterceptor)、Byte Buddy(现代字节码)、$Proxy0 底层生成原理、Spring AOP 代理选择逻辑、MyBatis Mapper/RPC 客户端/统一异常代理实战

### 第十一篇 — Java 模块化

- [[58-Java Module System]] — module-info.java 九大指令、requires(依赖)/exports(导出)/opens(反射)、模块路径 vs 类路径对比、ServiceLoader 服务发现(provides/uses)、JDK 内置 26 模块概览、jlink 裁剪定制 JRE、反射访问 opens/--add-opens、插件系统实战

### 第十二篇 — 数据库

- [[59-数据库基础]] — DB/DBMS/RDBMS 概念辨析、层次/网状/关系三种数据模型、ER 模型与表设计、主键策略(自增/UUID/雪花)、外键约束与权衡、索引基础、事务 ACID 概念
- [[60-SQL]] — DDL/DML/DQL/DCL/TCL 五类 SQL、JOIN/子查询/CTE/窗口函数详解、GROUP BY+HAVING 聚合分析、SQL 执行顺序、分页优化、连续登录天数漏斗分析实战
- [[61-MySQL]] — MySQL 分层架构、InnoDB 磁盘与内存结构、Buffer Pool LRU 算法、Redo/Undo/Binlog 三日志两阶段提交、MVCC 可见性判断、B+Tree 聚簇/二级/覆盖索引、EXPLAIN 执行计划与 SQL 优化
- [[62-数据库事务]] — ACID 实现原理(Undo+Redo)、四种隔离级别与并发问题、MVCC Read View 时机差异、行锁/间隙锁/Next-Key Lock 死锁预防、悲观锁 vs 乐观锁(CAS+版本号)、Spring @Transactional 失效排查
- [[63-数据库连接]] — JDBC Driver/Connection/PreparedStatement/ResultSet/Batch 核心接口、HikariCP 与 Druid 连接池配置与选型、连接泄漏检测、rewriteBatchedStatements 批量优化、多数据源与监控

### 第十三篇 — JDBC

- [[64-JDBC]] — JDBC 架构与驱动注册机制(SPI)、Connection/Statement/PreparedStatement/CallableStatement 四种语句、ResultSet 可滚动与游标、ResultSetMetaData 通用结果映射、DatabaseMetaData 遍历表列键索引、Batch 合并优化、事务 Savepoint、SQL 注入 5 种攻击与白名单防御

### 第十四篇 — ORM

- [[65-JPA]] — JPA 规范与 Hibernate 关系、Entity 映射/主键策略/字段类型、Repository 命名查询与 @Query、EntityManager 与 Persistence Context、Entity 四状态生命周期、四种关联映射(1:1/1:N/N:1/M:N)、Cascade 与 Orphan Removal、Lazy 加载陷阱、JPQL/Criteria/Specification 三种查询方式
- [[66-Hibernate]] — Session 与 EntityManager 对比、一级缓存与 Dirty Checking 原理、FlushMode 四种时机、二级缓存架构与策略、Fetch Join 解决 N+1 与 MultipleBagFetchException、@BatchSize/@Fetch(SUBSELECT)/EntityGraph 替代方案、StatelessSession 批量处理、Hibernate Validator 分组校验与自定义注解
- [[67-MyBatis]] — SqlSession/Executor 架构、Mapper 动态代理实现、XML 映射文件与 #{} vs ${}、动态 SQL 七种标签(if/where/set/foreach/choose/trim/sql)、ResultMap 关联映射(association/collection/discriminator)、TypeHandler 自定义类型处理器、Interceptor 四层拦截、一级/二级缓存
- [[68-MyBatis-Plus]] — BaseMapper 17 种内置方法、IService 链式调用、QueryWrapper/LambdaQueryWrapper 条件构造、分页插件配置与 PageDTO、主键策略(ASSIGN_ID/ASSIGN_UUID)、MetaObjectHandler 自动填充审计字段、@TableLogic 逻辑删除、@Version 乐观锁重试、FastAutoGenerator 代码生成器

### 第十五篇 — Java Web

- [[69-Servlet]] — Servlet 核心概念：Servlet Container 与生命周期(init/service/destroy)、HttpServlet 方法分发(doGet/doPost/doPut/doDelete)、HttpServletRequest 请求信息获取、HttpServletResponse 响应构建、ServletConfig/ServletContext 配置与上下文、Filter 过滤器链(责任链模式)、Listener 八种监听器、Session 会话管理(Cookie/URL重写)、请求转发 vs 重定向、文件上传下载
- [[70-JSP]] — JSP 本质(Servlet)、生命周期(翻译/编译/jspInit/_jspService/jspDestroy)、脚本元素(声明/脚本/表达式)、九大内置对象与四大作用域、EL 表达式隐式对象与空值处理、JSTL Core/Fmt/Fn 标签库、自定义标签(SimpleTag/Tag File)、JSP+Servlet MVC(Model 2)

### 第十六篇 — Spring Framework

- [[71-Spring基础]] — Spring Framework 分层架构、IoC 控制反转与 DI 依赖注入(构造器/Setter/字段)、泛型作为限定符、JSR-330 标准注解(@Inject/@Named/@Singleton)与 @Autowired 对比、Null-safety(@NonNull/@Nullable)、Bean 定义与 BeanDefinition、Bean 定义继承(abstract/parent)、BeanFactory 与 ApplicationContext(事件/国际化/资源)、refresh() 12 步启动流程、Bean 生命周期(实例化→属性填充→Aware→BPP→@PostConstruct→InitializingBean→就绪→@PreDestroy→DisposableBean)及 BeanFactoryPostProcessor、五种 Bean Scope(singleton/prototype/request/session/application)及 singleton 注入 prototype 问题
- [[72-Spring配置]] — XML 配置(bean/property/constructor-arg/命名空间)、注解配置(@Component/@Service/@Repository/@Controller)、Java Config(@Configuration+@Bean+CGLIB代理)、编程式注册 Bean(GenericApplicationContext.registerBean)、@ComponentScan 扫描机制与过滤、@Import/@ImportResource、条件化配置(@Profile/@Conditional及 Spring Boot 内置条件注解)、Environment 抽象(PropertyResolver/PropertySource/属性优先级)、@Value 与 @ConfigurationProperties 属性注入
- [[73-Spring-AOP]] — AOP 核心概念(Aspect/JoinPoint/Pointcut/Advice/Weaving)、JDK 动态代理 vs CGLIB 代理及自调用陷阱、@Aspect+@Component 切面定义、五种通知(@Before/@AfterReturning/@AfterThrowing/@After/@Around)及执行顺序、@Order 控制切面优先级、切点表达式(execution/within/this/target/args/@annotation/bean)、JoinPoint 与 ProceedingJoinPoint、Introductions 引入(@DeclareParents)、Aspect 实例化模型(singleton/perthis/pertarget)、AspectJ 编译时织入、Schema-based AOP(XML)与 AspectJProxyFactory 编程式代理
- [[74-Spring事务]] — PlatformTransactionManager 事务抽象、声明式事务(@Transactional + tx:advice XML)与编程式事务(TransactionTemplate)、事务同步与事务事件(TransactionSynchronizationManager/@TransactionalEventListener)、七种传播行为(REQUIRED/REQUIRES_NEW/NESTED/SUPPORTS/NOT_SUPPORTED/MANDATORY/NEVER)对比、四种隔离级别、回滚规则(RuntimeException默认回滚/rollbackFor/noRollbackFor)、八种事务失效场景(非public/自调用/异常吞没/异常类型/引擎不支持/多线程/未配置管理器/非Spring管理)及排查口诀
- [[Resources]] — Spring 资源抽象：Resource 接口(InputStreamSource/exists/getFile)、内置实现(ClassPathResource/FileSystemResource/UrlResource/ServletContextResource/InputStreamResource/ByteArrayResource)、ResourceLoader 前缀解析(classpath:/file:/http:)、ResourcePatternResolver 通配符匹配(classpath*:/Ant 风格)、资源作为 @Value 依赖注入、5 个踩坑(流重复读取/jar内资源 getFile 失败等)
- [[SpEL]] — Spring 表达式语言：SpelExpressionParser/EvaluationContext 基础 API、字面量/属性/List/Map 访问、内联集合与数组构造、运算符(关系/逻辑/数学/字符串/matches正则)、类型表达式 T()、变量 #var 与函数注册、Bean 引用 @beanName、三元/Elvis(?:)/安全导航(?.)、集合投影(.![])与选择(.?[])、模板表达式 #{...}、SpEL 编译优化、@Value/@Cacheable/@PreAuthorize 应用

### 第十七篇 — Spring MVC

- [[75-Spring-MVC]] — DispatcherServlet 前端控制器与 8 步请求处理流程、@Controller/@RestController、@RequestMapping 及方法级快捷注解、参数绑定(@RequestParam/@PathVariable/@RequestBody/@RequestHeader/@CookieValue/@ModelAttribute)、返回值处理(ModelAndView/对象/ResponseEntity)、HandlerMapping 与 HandlerAdapter 扩展点、Converter 与 Formatter 类型转换、HandlerInterceptor 拦截器(preHandle/postHandle/afterCompletion)、Filter vs Interceptor 对比
- [[76-REST-API]] — REST 核心原则(资源导向/无状态/统一接口/HATEOAS)、HTTP 方法语义(GET/POST/PUT/PATCH/DELETE 的安全性与幂等性)、HTTP 状态码(2xx/3xx/4xx/5xx 详解)、JSON 数据格式与命名规范、API 设计规范(URI/分页/统一响应/幂等)、API 版本管理(URL/头/参数)、Jackson 序列化控制、6 个踩坑(Long精度丢失/DELETE带body/PUT语义)
- [[77-全局异常]] — @ExceptionHandler 局部处理、@ControllerAdvice 全局处理(限定范围/常见异常类型)、统一响应体与错误码设计(枚举/业务异常)、ProblemDetail 与 RFC 7807 标准、ErrorResponse 接口、异常处理优先级(精确匹配/局部优先/@Order)、6 个踩坑(404默认不处理/校验异常类型区分/异常处理器再抛异常)

### 第十八篇 — Spring Boot

- [[78-SpringBoot基础]] — Spring Boot 核心特性(Starter/内嵌服务器/自动配置)、@SpringBootApplication 三合一拆解(@SpringBootConfiguration/@EnableAutoConfiguration/@ComponentScan)、自动配置原理(AutoConfigurationImportSelector/条件评估/优先级)、Starter 机制与命名规范、SpringApplication 启动流程(10 步)、ApplicationRunner/CommandLineRunner、Actuator 生产就绪特性(health/metrics/loggers 端点)、6 个踩坑
- [[79-配置体系]] — application.properties vs application.yml 对比、yml 特殊语法(多文档/占位符/引用)、Profile 多环境配置(application-{profile}.yml/激活方式/合并规则)、外部配置(命令行/环境变量/spring.config.location/import)、配置优先级 10 级清单、@Value 与 @ConfigurationProperties 绑定、松散绑定(kebab-case/camelCase/UPPER_CASE)、随机值与敏感信息处理
- [[80-Starter]] — Starter 两模块结构(starter 聚合依赖 + autoconfigure 实现逻辑)、AutoConfiguration.imports 注册机制、自动配置类写法(@AutoConfiguration/@EnableConfigurationProperties)、条件注解详解(@ConditionalOnClass/OnMissingBean/OnProperty/自定义 Condition)、自定义 Starter 完整 7 步(以短信服务为例)、配置元数据生成(spring-configuration-processor)、6 个踩坑
- [[81-SpringBoot-Web]] — 内嵌服务器配置与切换(Tomcat/Jetty/Undertow)、优雅停机、Spring MVC vs WebFlux 对比(Mono/Flux)、Jackson JSON 全局配置(日期/时区/null)、文件上传下载(@RequestParam MultipartFile/大小限制/流式下载)、CORS 跨域(全局配置/注解/预检原理)、WebSocket(端点配置/广播)、SSE 服务器推送(SseEmitter/WebFlux Flux)、静态资源映射

### 第十九篇 — Spring Security

- [[82-Security基础]] — Authentication vs Authorization 区别、SecurityContext/SecurityContextHolder(ThreadLocal 存储策略)、Filter Chain(DelegatingFilterProxy/核心 Filter 顺序)、UserDetails 与 UserDetailsService 自定义实现、PasswordEncoder(BCrypt/DelegatingPasswordEncoder 多算法)、DaoAuthenticationProvider 认证流程、URL 级与 @PreAuthorize 方法级授权、前后端分离 JSON 认证配置、6 个踩坑
- [[83-JWT]] — JWT 结构(Header/Payload/Signature)、签名防篡改原理(非加密)、jjwt 工具类(生成/解析/过期校验)、Access Token + Refresh Token 双 Token 机制、Token 过期处理(jjwt 异常类型)、Token 黑名单(Redis 实现/登出失效)、Token 刷新流程(旧 refreshToken 作废)、JWT 集成 Spring Security(OncePerRequestFilter + STATELESS)、6 个踩坑
- [[84-OAuth2]] — OAuth2 四角色(Resource Owner/Client/Authorization Server/Resource Server)、四种授权模式(Authorization Code/Client Credentials/Password/Implicit)对比与 PKCE、Refresh Token 模式(旋转刷新/防重放)、OpenID Connect(ID Token/UserInfo/OAuth2 vs OIDC)、OAuth2 Client 第三方登录、Resource Server(JWT 验证/权限映射)、Authorization Server(Spring Authorization Server/推荐托管方案)、6 个踩坑

### 第二十篇 — Spring Data

- [[85-Spring-Data]] — Spring Data Commons 模块全景、Repository 接口体系(Repository/CrudRepository/PagingAndSortingRepository/JpaRepository)、Query Method 派生查询(方法名解析规则/20+ 查询关键字)、@Query 注解(JPQL/原生 SQL/@Modifying)、投影(接口/闭/类/动态)、审计(@CreatedDate/@LastModifiedDate/@CreatedBy)、Query by Example、6 个踩坑(N+1/审计不生效)
- [[86-Redis]] — RedisTemplate 与 StringRedisTemplate 对比、序列化机制(JDK vs JSON/常见序列化器/自定义配置)、五种数据类型操作(String/Hash/List/Set/ZSet)、Pub/Sub 发布订阅(消息监听/即发即失)、Redis Stream(持久化/消费组/ack)、分布式锁(SET NX PX/Lua 原子解锁/Redisson 看门狗)、6 个踩坑(乱码/setIfAbsent null/锁过期)
- [[87-MongoDB]] — @Document 实体映射(@Id/@Field/@Indexed/嵌套文档)、MongoRepository(派生查询/@Query)、MongoTemplate(CRUD/Update/upsert/findAndModify)、Query 与 Criteria(条件构建/组合/投影)、Aggregation 聚合框架($match/$group/$sort/$unwind)、6 个踩坑(嵌套字段覆盖/正则大小写/16MB 限制)
- [[88-Elasticsearch]] — @Document 与 @Field 映射(Text vs Keyword/分词器)、索引操作(创建/删除/自动创建)、ElasticsearchRepository(派生查询/@Query DSL)、ElasticsearchOperations(Criteria/NativeQuery/分页排序)、全文搜索(match/multi_match/bool)、Aggregation 聚合(terms/stats)、6 个踩坑(版本匹配/Text 用 term 查不到/中文分词)

### 第二十一篇 — Spring Cache

- [[89-缓存]] — Cache 与 CacheManager 抽象、@Cacheable/@CachePut/@CacheEvict/@Caching 注解、condition vs unless、缓存 Key 策略(SpEL/KeyGenerator)、Redis Cache(RedisCacheManager 配置/TTL)、Caffeine 本地缓存、多级缓存(Caffeine+Redis)、缓存一致性(Cache Aside/延迟双删)、缓存三大问题(穿透/击穿/雪崩)及解法、6 个踩坑

### 第二十二篇 — Spring Messaging

- [[90-消息系统]] — Message(消息体+消息头)、MessageChannel 消息通道、MessageConverter 消息转换(JSON 序列化)、@RabbitListener/@KafkaListener 消息监听、Spring 事件机制(@EventListener/@TransactionalEventListener)、消息中间件选型(RabbitMQ vs Kafka vs RocketMQ)、消息幂等消费、6 个踩坑
- [[91-RabbitMQ]] — 核心概念(Exchange/Queue/Binding/Routing Key)、四种交换机(Direct/Topic/Fanout/Headers)对比、消息确认(ACK/NACK/manual)、死信队列(DLX)、消息 TTL(队列级/消息级)、延迟队列(TTL+死信)、消息重试、可靠性投递(Confirm/Return/持久化)、6 个踩坑
- [[92-Kafka]] — 核心概念(Broker/Topic/Partition/Offset)、Producer(acks/幂等/分区策略)、Consumer 与 Consumer Group(手动提交 offset)、ACK 机制(acks=0/1/all)、ISR 与 Replication(副本/Leader 选举)、Kafka Streams(流处理/窗口聚合)、Kafka vs RabbitMQ 对比、7 个踩坑(consumer>partition/顺序问题)

### 第二十三篇 — Spring Cloud

- [[93-微服务基础]] — 架构演进(单体/SOA/微服务)对比、微服务核心特性(独立部署/独立数据库/轻量通信)、服务拆分原则(单一职责/高内聚低耦合/DDD)、服务治理全景(注册发现/负载均衡/配置/网关/容错)、服务注册与发现流程、Spring Cloud 组件全景、6 个踩坑
- [[94-Nacos]] — Nacos 安装启动、服务注册与发现(@EnableDiscoveryClient/DiscoveryClient)、配置中心(Data ID 规则/bootstrap)、动态配置刷新(@RefreshScope/@NacosValue)、命名空间 Namespace(环境隔离)、分组 Group、Nacos 集群(AP/CP 模式/MySQL 存储)、6 个踩坑
- [[95-Gateway]] — 核心概念(Route/Predicate/Filter)、路由配置(YAML/服务发现路由)、Predicate 断言(Path/Method/Header/Weight)、Filter 过滤器(StripPrefix/自定义)、GlobalFilter 全局过滤器(统一鉴权)、限流(RequestRateLimiter 令牌桶)、灰度发布(权重/请求头/参数)、6 个踩坑
- [[96-OpenFeign]] — 声明式服务调用(@FeignClient)、编码器/解码器(Jackson 配置)、拦截器(传递 token/traceId)、超时配置(connectTimeout/readTimeout)、重试机制(Retryer)、日志配置(Logger.Level)、fallback/fallbackFactory 降级、6 个踩坑(@PathVariable value/GET 带 body)
- [[97-LoadBalancer]] — 服务端 vs 客户端负载均衡对比、LoadBalancer 核心接口(ReactorLoadBalancer)、内置策略(RoundRobin 默认/Random)、自定义策略(权重负载均衡)、@LoadBalanced RestTemplate、配合 OpenFeign 自动负载均衡、6 个踩坑
- [[98-服务容错]] — 服务雪崩原理、Circuit Breaker 熔断器三态(Closed/Open/Half-Open)、Resilience4j(熔断/重试/限流/隔离/超时五种模式)、Sentinel(注解/控制台/流控降级规则)、Fallback 降级策略、6 个踩坑(fallback 签名/降级返回 null)

### 第二十四篇 — 分布式系统

- [[99-分布式基础]] — 分布式系统的挑战(网络不可靠/时钟不一致/部分失败)、CAP 定理(一致性/可用性/分区容错/为何 P 必选)、CP vs AP 取舍、BASE 理论(基本可用/软状态/最终一致)、一致性模型(强一致/弱一致/最终一致)、CAP 与 BASE 关系、常见中间件 CAP 选择表、6 个踩坑
- [[100-分布式锁]] — 分布式锁设计目标(互斥/无死锁/可重入/高可用)、Redis 实现(SET NX PX/Lua 原子解锁)、手写锁的四个问题(过期/不可重入/不可续期/误删)、Redisson(看门狗/可重入/公平锁/读写锁)、Zookeeper 实现(临时顺序节点/Curator)、数据库实现(唯一索引/FOR UPDATE)、四种方案对比、6 个踩坑
- [[101-分布式ID]] — 分布式 ID 要求(全局唯一/趋势递增/高性能/高可用)、UUID(优缺点/适用场景)、数据库自增(单库/多库步长/独立 ID 表)、Snowflake 雪花算法(64 位结构/Java 实现/时钟回拨)、数据库号段模式、美团 Leaf(双 buffer/机器 ID 分配)、方案对比选型、6 个踩坑(UUID 主键/时钟回拨/前端精度丢失)
- [[102-分布式事务]] — 分布式事务挑战(原子性/一致性/隔离性)、XA 两阶段提交(Prepare/Commit/优缺点)、TCC(Try/Confirm/Cancel/空回滚/悬挂)、Saga(编排式/控制式/补偿)、本地消息表(业务+消息同库事务/定时重发)、Outbox 模式(CDC/事件驱动)、事务消息(RocketMQ half 消息/回查)、Seata(AT/TCC/Saga/XA 四模式)、方案对比选型、6 个踩坑

### 第二十五篇 — 分布式架构

- [[103-高并发]] — 核心指标(QPS/TPS/并发量/响应时间/吞吐量及其关系)、四种限流算法(计数器/滑动窗口/漏桶/令牌桶)对比与实现、熔断降级限流的区别、排队削峰(消息队列缓冲)、异步化(线程池/@Async/CompletableFuture)、秒杀系统设计、6 个踩坑(临界突发/异步丢上下文)
- [[104-高可用]] — 可用性衡量(SLA/MTBF/MTTR/几个 9)、主从复制(读写分离/同步异步复制)、集群(分片/协调/一致性)、故障转移 Failover(流程/自动 vs 手动)、容错机制组合(超时/重试/熔断/降级)、健康检查(存活/就绪/深度)、无状态化、6 个踩坑(复制延迟/脑裂/重试雪崩)
- [[105-分布式缓存]] — 缓存架构演进(单机→主从→哨兵→集群)、主从复制流程、Sentinel 哨兵(监控/自动故障转移)、Redis Cluster(16384 槽/分片/hash tag/限制)、一致性 Hash(环/虚拟节点/Java 实现)、四种读写模式(Cache Aside/Read Through/Write Through/Write Behind)对比、6 个踩坑(跨槽操作/复制延迟/双写不一致)

### 第二十六篇 — Redis

- [[106-Redis基础]] — Redis 特点与高性能原因(纯内存/单线程/多路复用)、10 种数据类型(String/Hash/List/Set/ZSet/Bitmap/HyperLogLog/Geo/Stream)、每种类型的常用命令/底层编码/应用场景、数据类型选型速记表、底层编码(ziplist/hashtable/skiplist)
- [[107-Redis高级]] — 持久化(RDB 快照/AOF 日志/混合持久化)原理与优缺点对比、事务(原子性/无回滚/与 Lua 区别)、Pipeline 管道(减少 RTT/与事务区别)、Lua 脚本(原子执行/限流锁示例)、Pub/Sub(广播/无持久化)、主从/Sentinel/Cluster 回顾、6 个踩坑(fork 内存翻倍/脚本阻塞)
- [[108-Redis应用]] — 八大应用场景(缓存/Session 共享/分布式锁/限流/排行榜/延迟队列/消息队列/布隆过滤器)、排行榜 ZSet 实现、延迟队列 ZSet 时间戳实现、消息队列 List vs Stream、布隆过滤器原理(Guava/Redisson)、应用场景总结表

### 第二十七篇 — Elasticsearch

- [[109-Elasticsearch基础]] — ES 与 MySQL 概念对照表、Index/Document/Field 操作、10 种字段类型(text vs keyword 核心区别)、Mapping 映射(动态 vs 显式/常用参数/修改限制)、Shard 分片与 Replica 副本(作用/分片数设计)、6 个踩坑(动态映射误判/字段类型不可改)
- [[110-Elasticsearch查询]] — Match 全文匹配(operator/multi_match/match_phrase)、Term 精确匹配(term vs match 区别/terms)、Bool 组合查询(must/should/must_not/filter 与 filter vs must)、Range 范围(gt/gte/lt/lte)、Prefix 前缀、Wildcard 通配符、Query String 语法、Aggregation 聚合(指标/桶/嵌套)、查询选型总结表
- [[111-Elasticsearch高级]] — 倒排索引原理(正排 vs 倒排/构建过程/为什么快)、Analyzer 分析器(三组件/内置分析器)、分词器(英文 vs 中文)、中文分词(IK 分词器/ik_max_word vs ik_smart/自定义词典)、集群架构(节点角色/健康状态/分片分配)、性能优化(查询/写入/内存三维度)、6 个踩坑(中文不分词/text 排序报错)

### 第二十八篇 — Linux

- [[112-Linux基础]] — 常见发行版(RedHat 系/Debian 系/包管理器对比)、目录结构(FHS 规范/核心目录)、文件类型(软硬链接)、用户与用户组(useradd/groupadd/passwd)、文件权限(rwx/数字权限/chmod/chown)、6 个踩坑(chmod 777 滥用/SSH 密钥权限)
- [[113-Linux命令]] — 23 个常用命令分类(文件目录/文件查看/文件搜索/文本处理/压缩打包)、ls/cd/cp/mv/rm/mkdir/touch、cat/less/head/tail、grep/find、sed/awk/sort/uniq/xargs/cut/wc、tar/gzip/zip、命令组合实战(日志分析/磁盘清理)
- [[114-Linux进程]] — ps 查看进程(aux 输出解读/进程状态)、top/htop 实时监控(load average 负载)、kill/killall 终止进程(SIGTERM vs SIGKILL)、systemd 系统管理(Unit 类型)、systemctl 服务管理(Java 应用 systemd 服务文件)、journalctl 日志查看、6 个踩坑(kill -9 滥用/daemon-reload)
- [[115-Linux网络]] — TCP/IP 四层模型、三次握手四次挥手、常见端口、ping 连通性测试、curl 网络请求(常用参数/测试接口)、wget 下载、telnet/nc 端口测试、ss/netstat 网络状态(端口占用排查)、ip 网络配置、traceroute 路由追踪、DNS 解析、6 个踩坑(ping 通不代表服务通/监听地址)

### 第二十九篇 — Docker

- [[116-Docker基础]] — Docker 三大概念(Image/Container/Registry)、镜像分层结构、容器生命周期、Registry 仓库与镜像加速器、Dockerfile 指令(多阶段构建/CMD vs ENTRYPOINT)、Volume 数据卷(命名卷/绑定挂载)、Network 网络(bridge/host/自定义网络)、6 个踩坑(数据丢失/时区/镜像过大)
- [[117-Docker命令]] — 镜像命令(pull/images/build/tag/rmi)、容器生命周期(run/start/stop/restart/rm)、容器操作(ps/exec/cp)、日志排查(logs/inspect/top/stats)、资源清理(prune/system df)、部署排查实战
- [[118-Docker-Compose]] — 多容器编排(Service/Network/Volume)、compose.yml 详解、常用命令(up/down/logs/exec)、Service 定义方式(image/build)、Network 与 Volume、Environment 环境变量(.env 替换)、Healthcheck 与 depends_on 条件依赖、6 个踩坑(localhost 连库/数据卷丢失)

### 第三十篇 — Kubernetes

- [[119-Kubernetes基础]] — Cluster 与 Node 架构、Pod 最小调度单元(共享网络/存储)、Deployment 与 ReplicaSet(副本管理/滚动更新/自愈)、StatefulSet 有状态应用(稳定标识/独立存储)、DaemonSet 守护进程、Job 与 CronJob、6 个踩坑(Pending/ImagePullBackOff/CrashLoopBackOff)
- [[120-Kubernetes网络]] — Service 服务抽象(稳定入口/负载均衡)、四种类型(ClusterIP/NodePort/LoadBalancer/ExternalName)、Ingress 七层路由(路径/域名路由/Ingress Controller)、DNS 服务发现(服务名解析/Headless Service)、6 个踩坑(selector 不匹配/跨 namespace)
- [[121-Kubernetes配置]] — ConfigMap 配置管理(环境变量/文件挂载)、Secret 敏感信息(base64/类型/与 ConfigMap 区别)、Namespace 命名空间(环境隔离/资源配额)、Resource 资源管理(requests vs limits/CPU 内存单位)、6 个踩坑(Secret 非加密/OOMKilled)
- [[122-Kubernetes运维]] — kubectl 常用命令(get/describe/logs/exec)、Probe 探针(liveness/readiness/startup)、HPA 自动伸缩、Rolling Update 滚动更新与 Rollback 回滚、Helm 包管理(Chart/Release/模板)、6 个踩坑(探针路径/滚动更新卡住)

### 第三十一篇 — DevOps

- [[123-Git]] — Git 四区域(工作区/暂存区/本地仓库/远程仓库)、基本工作流(add/commit/push/pull)、Branch 分支、Merge 与 Rebase 区别、Tag 标签(语义化版本)、Cherry-pick 与 Stash、Git Flow 分支模型(main/develop/feature/release/hotfix)、6 个踩坑(reset --hard 误删/rebase 公共分支)
- [[124-CICD]] — CI 与 CD 概念、Pipeline 流水线(build/test/package/deploy 阶段)、GitHub Actions(工作流/Job/Step/Action)、GitLab CI(.gitlab-ci.yml/stages)、Jenkins(Jenkinsfile)、三大工具对比、6 个踩坑(缓存不生效/敏感信息硬编码)
- [[125-DevOps]] — DevOps 文化与实践(CI/CD/IaC/监控/工具链)、IaC 基础设施即代码(声明式 vs 命令式)、Terraform(provider/resource/plan/apply)、Ansible(Playbook/Inventory/幂等)、GitOps 与 Argo CD(Git 唯一来源/自动同步)、6 个踩坑(state 文件泄露/忽视监控)

### 第三十二篇 — 测试

- [[126-单元测试]] — JUnit 5(注解/断言/参数化/生命周期)、AssertJ 流式断言、Mockito(stub/verify/参数匹配)、Mock vs Stub vs Spy 区别、AAA 测试模式、6 个踩坑(假绿/依赖顺序/mock 被测对象)
- [[127-SpringBoot测试]] — @SpringBootTest 集成测试(webEnvironment/TestRestTemplate)、MockMvc Web 层测试(jsonPath 断言)、@WebMvcTest + @MockBean、WebTestClient 响应式测试、Test Slice 切片测试(@DataJpaTest 等)、分层测试策略、6 个踩坑(找不到配置类/H2 与 MySQL 差异)
- [[128-集成测试]] — Testcontainers 容器化测试(MySQL/Redis 真实环境/@DynamicPropertySource)、WireMock 模拟外部服务(成功/故障模拟)、Embedded Database 内嵌数据库(H2 vs Testcontainers 对比)、API Test 接口测试(MockMvc/REST Assured)、6 个踩坑(H2 通过 MySQL 失败/容器启动慢)
- [[129-性能测试]] — 性能测试类型(负载/压力/稳定性/基准)、核心指标(RT/P95/P99/QPS/错误率)、JMeter(线程组/压测步骤/命令行)、Gatling(Scala 场景)、JMH 基准测试(@Benchmark/@Warmup/为什么需要)、6 个踩坑(没预热/压测打爆生产/只看平均值)

### 第三十三篇 — API 与接口设计

- [[130-API设计]] — REST 设计原则(资源导向/无状态/统一接口)、URI 命名规范(小写/连字符/复数/层级)、HTTP Method 语义(GET/POST/PUT/PATCH/DELETE 幂等安全表)、状态码使用(201/204/409/422)、JSON 统一响应体、分页排序过滤(page/size/sort/操作符)、6 个踩坑(URI 用动词/GET 带 body)
- [[131-API文档]] — OpenAPI 规范、Swagger 集成(springdoc-openapi/@Tag/@Operation/@Schema/分组)、Knife4j 增强(界面/导出/与 Swagger 对比)、Spring REST Docs(测试驱动文档)、6 个踩坑(生产暴露文档/版本冲突)
- [[132-API安全]] — 四种认证方式对比(JWT/OAuth2/API Key/Signature)、JWT 认证(过滤器集成)、API Key 认证、签名认证 HMAC(签名流程/时间戳/nonce/恒时比较)、限流与幂等(幂等键/Redis 去重)、6 个踩坑(secret 硬编码前端/HTTP 明文)

### 第三十四篇 — 文件与办公自动化

- [[133-Excel]] — Apache POI 基础(Workbook/Sheet/Row/Cell/单元格类型)、EasyExcel(实体注解/监听器流式读/流式写)、Excel 导入(校验/批量入库/错误反馈)、Excel 导出(分页查询/流式写/下载)、大文件处理(POI OOM 问题/EasyExcel 流式)、6 个踩坑(POI 大文件 OOM/科学计数法/中文乱码)
- [[134-PDF]] — PDF 生成(iText/OpenPDF/中文字体)、PDF 模板(HTML 转 PDF/AcroForm/方案对比)、PDF 解析(PDFBox 提取文本/局限)、PDF 合并与拆分(PDFBox)、6 个踩坑(中文乱码/扫描件提取为空/iText 版权)
- [[135-图片]] — ImageIO 基础(读写/支持格式)、Thumbnailator(缩放/旋转/水印/链式 API)、图片压缩(质量压缩/缩放压缩/策略)、图片裁剪(中心裁剪/区域裁剪)、水印(图片/文字)、OCR 文字识别(Tesseract/预处理/注意事项)、6 个踩坑(JPEG 转 PNG/WebP 不支持)

### 第三十五篇 — 工作流

- [[136-BPMN]] — BPMN 五大核心元素(事件/任务/网关/顺序流/泳道)、Task 任务类型(User/Service/Script)、Gateway 网关(排他/并行/包容)、Event 事件(开始/结束/定时)、Sequence Flow 顺序流(条件表达式 UEL/默认流)、请假审批/订单处理示例、6 个踩坑(排他网关无默认流/并行缺 join)
- [[137-Flowable]] — Flowable 概述(与 Activiti 关系)、依赖配置与核心服务(Repository/Runtime/Task/History)、流程部署、流程启动(带变量)、任务处理(查询待办/完成/认领)、会签与或签(multiInstanceLoopCharacteristics)、流程变量与历史查询、6 个踩坑(变量不序列化/版本混乱)

### 第三十六篇 — 规则引擎

- [[138-Drools]] — 规则引擎价值、核心概念(Fact/Working Memory/Rule/Agenda)、DRL 规则语法(when LHS/then RHS)、规则引擎使用(KieSession/Spring Boot 集成)、Decision Table 决策表(Excel 维护规则)、优惠券/风控/积分示例、6 个踩坑(modify 死循环/规则顺序不确定)
- [[139-业务规则]] — 规则管理(存储/表设计)、动态规则(运行时加载/不重启/变更通知)、规则版本(版本表/回滚/审计)、规则发布(流程/灰度发布)、规则执行(同步/异步/监控)、动态优惠系统/灰度示例、6 个踩坑(热加载线程安全/版本混乱)

### 第三十七篇 — 大数据

- [[140-Hadoop]] — Hadoop 三大组件(HDFS/MapReduce/YARN)、HDFS 分布式文件系统(NameNode/DataNode/数据块副本)、MapReduce 计算模型(Map/Reduce 两阶段/WordCount)、YARN 资源调度、6 个踩坑(小文件/NameNode 单点)
- [[141-Hive]] — Hive 数据仓库(与 MySQL 区别)、HQL 查询语言(建表/查询/导入)、Partition 分区(性能优化/动态分区)、Bucket 分桶(抽样/join 优化)、6 个踩坑(不分区全表扫描/分区字段重名)
- [[142-Spark]] — Spark 内存计算(vs MapReduce 快 10-100 倍)、RDD 弹性分布式数据集(Transformation/Action 惰性)、DataFrame 与 Dataset(结构化 API/三者对比)、Spark SQL、Spark Streaming 微批处理、6 个踩坑(collect OOM/shuffle 过多)
- [[143-Flink]] — Flink 真流处理(vs Spark Streaming 微批)、DataStream 流处理(核心算子)、Table API 与 SQL、Window 窗口(滚动/滑动/会话)、State 状态与 Checkpoint、Exactly Once 精确一次、6 个踩坑(状态无限增长/没配 Checkpoint)

### 第三十八篇 — 消息与流处理

- [[144-Kafka]] — 核心架构(Broker/Topic/Partition/Offset)、Producer 与 Consumer(acks/手动提交)、Consumer Group 与 Offset(组内负载均衡/组间广播)、Replication 与 ISR(副本/Leader 选举)、高性能原理(顺序写/零拷贝/页缓存/批量)、6 个踩坑
- [[145-Kafka-Streams]] — Kafka Streams 流处理库(vs Flink)、KStream 与 KTable(记录流 vs 变更流)、Processor API(底层/DSL vs Processor)、State Store 状态存储、Window 窗口(滚动/滑动/会话)、实时统计示例、6 个踩坑(状态无限增长)
- [[146-RocketMQ]] — RocketMQ 核心概念(Topic/Tag/Queue/NameServer)、Producer 与 Consumer(Spring Boot 集成)、顺序消息(队列选择/顺序监听)、延迟消息(18 个固定级别)、事务消息(half 消息/回查)、6 个踩坑(延迟级别限制/顺序消息用并发监听)

### 第三十九篇 — GraphQL

- [[147-GraphQL]] — GraphQL 概述(按需查询/单一端点/vs REST 过度获取)、Schema 与类型系统(SDL/标量/类型修饰符)、Query 查询(嵌套/别名/片段)、Mutation 变更(变量)、Subscription 订阅、Resolver 解析器(Spring GraphQL/@QueryMapping/@SchemaMapping)、6 个踩坑(N+1 用 DataLoader/深度嵌套攻击)

### 第四十篇 — AI + Java

- [[148-AI基础]] — 概念层次(AI→ML→DL→LLM→生成式AI)、机器学习三类型(监督/无监督/强化)、深度学习(CNN/RNN/Transformer)、大语言模型(特点/主流模型)、生成式 AI 与 AIGC、概念关系总结
- [[149-大语言模型]] — Transformer 架构(注意力机制)、Token 分词(计费/上下文)、Context Window 上下文窗口、Prompt 提示词(要素/技巧)、Temperature 与 Top-P(随机性控制)、Embedding 向量(语义/相似度)、Function Calling 函数调用、6 个踩坑
- [[150-Spring-AI]] — Spring AI 统一抽象(vs 多模型)、依赖配置(对接 DeepSeek 换 base-url)、ChatModel 与 ChatClient(流式/历史)、Prompt 与 Prompt Template、Structured Output 结构化输出(entity())、Embedding 与 Vector Store、智能客服/分类/代码生成示例、6 个踩坑
- [[151-RAG]] — RAG 工作流程(索引/检索两阶段)、Document Loader、Text Splitter 文本切分(块大小/重叠)、Embedding 向量化、Retriever 检索(相似性/关键词/混合)、Reranker 重排序、企业知识库示例、6 个踩坑(块太大太小/LLM 编造)
- [[152-向量数据库]] — 向量数据库作用(vs 传统数据库)、主流方案(Milvus/Qdrant/Chroma/pgvector/ES)、Milvus(分布式/Spring AI 集成)、pgvector(PostgreSQL 扩展)、选型对比表、6 个踩坑(维度不匹配/没建索引)
- [[153-AI-Agent]] — Agent 核心组成(LLM/Tool/Memory/Planning)、Tool 与 Tool Calling(@Tool 定义/流程)、Agent Memory 记忆(短期/长期)、Planning 与 Reasoning(ReAct/CoT)、Workflow 与 Multi-Agent、智能客服/数据分析示例、6 个踩坑(工具描述模糊/无限循环)
- [[154-MCP]] — MCP 概述(统一协议/USB-C 类比)、MCP 架构(Client/Server)、MCP Server 与 Client 实现、MCP 三大能力(Tool/Resource/Prompt)、Transport 传输(STDIO/SSE/HTTP)、6 个踩坑(工具描述不清/安全风险)

### 第四十一篇 — Java 架构设计

- [[155-软件架构]] — 架构风格(分层/六边形/微服务/事件驱动)、分层架构(经典三层/优缺点)、六边形架构(端口适配器/领域独立)、事件驱动架构(事件解耦)、架构选型(从单体开始/演进)、架构演进建议
- [[156-微服务架构]] — 服务拆分(原则/拆分示例/度)、服务注册与发现(Nacos)、服务通信(REST/RPC/消息对比)、服务网关(Gateway 职责)、服务容错(熔断/降级/重试/限流)、服务配置与监控、6 个踩坑(过早微服务/拆太细)
- [[157-DDD]] — DDD 战略设计(子域/限界上下文/上下文映射)、限界上下文(同一概念不同含义)、战术设计(构建块表)、Entity 实体(唯一标识)、Value Object 值对象(不可变/按值相等)、Aggregate 聚合与聚合根、领域服务与领域事件、6 个踩坑(过度设计/聚合太大)
- [[158-CQRS]] — Command 与 Query 分离、Command Handler/Query Handler、读写分离(主从/读模型优化)、CQRS 与 Event Sourcing 搭配、订单系统示例、6 个踩坑(简单系统过度设计/读写一致性)
- [[159-Event-Sourcing]] — 事件溯源思想(不存状态存事件)、Event 事件(不可变/过去式)、Event Store 事件存储(追加/有序/重放)、Snapshot 快照、Projection 投影(事件→读模型)、与 CQRS 搭配、银行账户示例、6 个踩坑(重放性能/修改事件)

### 第四十二篇 — 设计模式

- [[160-创建型设计模式]] — 单例(饿汉/双重检查锁/枚举)、工厂方法(子类决定类型)、抽象工厂(产品家族)、建造者(链式构建/Lombok @Builder)、原型(克隆/深浅拷贝)、5 种模式总结对比
- [[161-结构型设计模式]] — 适配器(接口转换/HandlerAdapter)、桥接(抽象实现分离)、组合(树形结构)、装饰器(动态增强/IO 流)、外观(简化接口/Service 层)、代理(控制访问/AOP)、总结对比
- [[162-行为型设计模式]] — 观察者(事件/发布订阅)、策略(消除 if-else/支付)、模板方法(流程骨架/JdbcTemplate)、命令(封装请求/撤销)、状态(状态行为/订单状态)、责任链(过滤器链)、迭代器、总结对比
- [[163-企业级设计模式]] — 事务脚本 vs 领域模型、持久化模式(Repository/DAO/工作单元)、缓存模式(Cache Aside 等)、消息模式(Outbox)、领域模式(实体/值对象/聚合)、总结对比

### 第四十三篇 — 性能优化

- [[164-Java性能优化]] — 性能分析方法(Arthas/JProfiler/JMH)、字符串优化(StringBuilder/常量池)、集合优化(预分配容量/ArrayList vs LinkedList)、IO 优化(缓冲流/NIO)、代码优化(避免重复计算/懒加载)、6 个踩坑(循环拼接/盲目优化)
- [[165-JVM性能]] — JVM 内存结构(堆/栈/Metaspace/JDK8 前后)、Heap 堆(新生代/老年代/对象分配)、GC 优化(算法/收集器对比/G1/ZGC)、JIT 编译与逃逸分析、JVM 参数调优(生产配置)、6 个踩坑(堆大小/忽略 Metaspace)
- [[166-数据库性能]] — SQL 优化(避免 SELECT */隐式转换/函数/深分页)、索引优化(最左前缀/覆盖索引/EXPLAIN)、慢 SQL 排查、连接池优化(HikariCP)、分库分表与读写分离、6 个踩坑(索引失效/索引过多)
- [[167-Web性能]] — HTTP 优化(HTTP/2 多路复用)、Keep-Alive 与连接池、CDN 加速、缓存策略(Cache-Control/ETag)、Compression 压缩(gzip)、Async 与 Batch、6 个踩坑(图片也 gzip/N+1)

### 第四十四篇 — 高并发架构

- [[168-高并发基础]] — 核心指标(QPS/TPS/RT/吞吐量/并发量)、Little's Law(并发量=QPS×响应时间)、容量评估(单机压测/冗余)、压测与验证(wrk/JMeter)、6 个踩坑(只看平均值/压测机瓶颈)
- [[169-高并发技术]] — 缓存(层次/三大问题)、异步与消息队列(削峰/解耦)、限流熔断降级(令牌桶/Guava RateLimiter)、分库分表与读写分离、数据分片与 CDN、技术选型总结、6 个踩坑
- [[170-秒杀系统]] — 秒杀挑战(流量洪峰/库存竞争)、流量削峰(令牌/排队/动静分离)、Redis 与 MQ 运用(预热/原子扣库存/异步下单)、限流与防刷、防超卖(方案对比/Redis DECR/条件更新)、幂等与分布式锁、完整架构设计、6 个踩坑

### 第四十五篇 — 安全

- [[171-Web安全]] — OWASP Top 10、XSS(类型/转义/HttpOnly)、CSRF(原理/Token/SameSite)、SQL 注入(参数化/#{} 与 ${})、SSRF 与 XXE(白名单/禁用外部实体)、文件上传与路径遍历、命令注入、8 种攻击防护总结、6 个踩坑
- [[172-密码学]] — 哈希算法(MD5/SHA/密码加盐 BCrypt)、HMAC 消息认证码、对称加密(AES/DES/模式)、非对称加密(RSA/ECC)、Base64 编码(非加密)、数字签名与数字证书、混合加密(HTTPS)、6 个踩坑(Base64 当加密/密码 MD5/AES ECB)
- [[173-身份认证]] — Session 与 Cookie(流程/优缺点)、JWT 认证(无状态/vs Session)、OAuth2 与 OpenID Connect(授权 vs 认证)、SSO 单点登录、MFA 多因素认证(TOTP)、认证方案选型表、6 个踩坑(密码明文/JWT 无法注销)

### 第四十六篇 — Java 企业级项目实战

- [[174-项目基础架构]] — 项目分层(Controller/Service/Repository)、Entity/DTO/VO 区别(为什么分离)、Converter 转换(手动/MapStruct)、完整分层示例、6 个踩坑(Controller 跨层/Entity 返回前端/BeanUtils)
- [[175-通用能力]] — 统一响应(Result/错误码)、统一异常处理(@RestControllerAdvice)、参数校验(注解/@Valid)、日志与操作日志(占位符/AOP 切面)、权限(RBAC)与数据字典、文件管理(OSS/MinIO)、6 个踩坑
- [[176-企业功能]] — RBAC(用户-角色-权限/表设计)、菜单与部门(树形结构)、岗位与字典、参数配置、登录(验证码/BCrypt/JWT)与消息通知、6 个踩坑(权限硬编码/魔法值)

### 第四十七篇 — 项目工程化

- [[177-项目结构]] — 单模块 vs 多模块、Maven 多模块(父 POM/模块依赖)、DDD 分层结构(interfaces/application/domain/infrastructure)、模块划分实践(按层/按领域)、6 个踩坑(循环依赖/领域层依赖框架)
- [[178-代码规范]] — 命名规范(大驼峰/小驼峰/常量)、注释规范(解释为什么/Javadoc)、异常规范(不吞异常/业务异常)、日志规范(占位符/脱敏/级别)、API 与数据库规范、Git 规范(分支/Commit)、6 个踩坑
- [[179-CodeReview]] — PR 与 Review 流程、Review 关注点(正确性/安全/性能)、静态分析工具(Checkstyle/SpotBugs/PMD)、SonarQube(质量门禁/CI 集成)、Code Smell 与 Technical Debt、6 个踩坑(PR 太大/技术债累积)

### 第四十八篇 — 源码分析

- [[180-JDK源码]] — ArrayList(数组/扩容 1.5 倍)、HashMap(哈希表/红黑树/hash 函数/JDK7 vs 8)、ConcurrentHashMap(CAS + synchronized)、ThreadPoolExecutor(参数/执行流程/拒绝策略)、CompletableFuture、ReentrantLock(AQS)、6 个踩坑
- [[181-Spring源码]] — IoC 容器、BeanFactory 与 ApplicationContext、BeanDefinition 与 Bean 生命周期、BeanPostProcessor(AOP 代理生成)、AOP 实现原理(JDK/CGLIB)、事务实现原理(失效场景)、6 个踩坑
- [[182-SpringBoot源码]] — SpringApplication 启动流程、@SpringBootApplication 拆解、自动配置原理(AutoConfiguration.imports)、Starter 机制、条件装配(@ConditionalOnXxx)、ConfigurationProperties、6 个踩坑
- [[183-MyBatis源码]] — SqlSession(执行入口)、Executor 执行器(四种类型)、MapperProxy 动态代理(接口转 SQL)、StatementHandler 与 ParameterHandler(#{} 与 ${})、ResultSetHandler、完整执行流程、6 个踩坑
- [[184-SpringMVC源码]] — DispatcherServlet(前端控制器/doDispatch)、HandlerMapping(RequestMappingHandlerMapping)、HandlerAdapter(适配器)、ArgumentResolver 参数解析、ReturnValueHandler 返回值处理、完整请求流程、6 个踩坑
- [[185-SpringSecurity源码]] — FilterChain 过滤器链(核心过滤器)、Authentication 认证(Manager/Provider)、SecurityContext(ThreadLocal)、Authorization 授权(@PreAuthorize 原理)、完整流程、6 个踩坑(过滤器顺序/异步丢失)

### 第四十九篇 — Java 常见问题

- [[186-Java基础面试]] — == 与 equals、hashCode 约定、String 不可变/常量池/拼接原理、基本类型与包装类(Integer 缓存)、final/static/abstract、接口与抽象类、重载与重写、异常体系、泛型擦除/PECS、反射、注解、值传递、深拷贝浅拷贝、Object 方法、Java 8 特性、BigDecimal 精度
- [[187-集合面试]] — 集合框架总览、HashMap(底层/put 流程/扩容/2 的幂/JDK7 死循环/负载因子)、ConcurrentHashMap(CAS+synchronized/分段锁)、ArrayList 与 LinkedList、HashSet/TreeMap/TreeSet、LinkedHashMap 实现 LRU、fail-fast 与 fail-safe、CopyOnWriteArrayList、阻塞队列
- [[188-并发面试]] — 线程基础(创建/状态/sleep 与 wait)、synchronized(原理/锁升级)、volatile(可见性/有序性/双重检查锁)、CAS 与 AQS、Lock 对比、ThreadLocal(原理/内存泄漏)、ThreadPoolExecutor(7 参数/流程/拒绝策略/为什么不用 Executors)、CompletableFuture、原子类、CountDownLatch/CyclicBarrier/Semaphore、死锁、happens-before
- [[189-JVM面试]] — JVM 内存结构、对象创建与内存布局(对象头/指针压缩)、GC(可达性分析/算法/Minor 与 Full GC)、垃圾收集器(Serial/Parallel/CMS/G1/ZGC)、类加载与双亲委派(破坏场景)、引用类型、OOM 排查、JVM 调优、逃逸分析
- [[190-Spring面试]] — IoC 与 DI(注入方式)、AOP(动态代理/通知类型)、Bean 生命周期、Bean 作用域、BeanFactory 与 ApplicationContext、循环依赖(三级缓存)、事务(传播/隔离/失效)、自动配置、@Autowired 与 @Resource、FactoryBean、事件机制、设计模式
- [[191-SpringBoot面试]] — 自动配置原理、条件注解、Starter 机制、配置文件加载顺序与 @ConfigurationProperties、Actuator、启动流程、@SpringBootApplication 组成、Spring Boot 3 变化、fat jar、优雅停机
- [[192-SpringCloud面试]] — 微服务与 CAP、Nacos(注册/配置/心跳)、Gateway(三大核心)、Feign(原理/优化)、LoadBalancer、CircuitBreaker(三态)、Sentinel 限流、分布式事务(Seata/TCC/SAGA)、链路追踪、服务雪崩
- [[193-Redis面试]] — 数据结构(类型/场景/为什么快)、底层结构(SDS/跳表)、持久化(RDB/AOF/混合)、过期与淘汰策略、缓存问题(穿透/击穿/雪崩/一致性)、分布式锁(SET NX PX/Redisson 看门狗)、集群(主从/哨兵/Cluster)、事务与 Lua、大 key 热 key
- [[194-MySQL面试]] — 存储引擎、索引与 B+Tree、聚簇索引与回表/覆盖索引、索引失效、最左前缀、MVCC 原理、事务(ACID/隔离级别)、锁(行锁/间隙锁/乐观悲观)、redo/undo/binlog 与两阶段提交、SQL 优化、主从复制、分库分表

### 第五十篇 — 综合项目实战

- [[195-综合项目实战]] — 39 个项目进阶路线：前 9 个进阶项目（学生成绩管理系统 Java SE、用户管理系统 Servlet/JDBC、企业员工管理系统 Spring Boot/Redis、企业管理平台 RBAC/JWT/Vue、订单系统 RabbitMQ、微服务电商 Spring Cloud/Nacos/Feign、秒杀系统 Redis/MQ、数据平台 ES/Kafka、AI 应用 Spring AI/RAG/Agent/MCP），后 10 个独立落地项目（196-205）
- [[196-博客内容管理系统]] — CMS 实战：Redis 三级缓存(详情/计数/热门榜)、ES 全文搜索(IK 分词)、浏览量异步刷库、评论审核，应用场景技术社区/企业知识库/个人博客
- [[197-在线考试系统]] — 在线考试实战：题库管理、随机组卷、自动判分、切屏防作弊、考试限时、成绩统计
- [[198-医院预约挂号系统]] — 医院挂号实战：号源池定时放号、Redis 预扣不超卖、Redisson 分布式锁、预约状态机、黑名单防刷
- [[199-酒店预订管理系统]] — 酒店预订实战：房态日历、同房型同日期并发锁房、订单状态机、超时未支付自动取消、收益统计
- [[200-短链接服务]] — 短链接实战：DB 号段发号器、短码生成、302 跳转缓存、布隆过滤器防穿透、PV/UV 统计
- [[201-任务协作看板系统]] — 看板协作实战：看板/列表/卡片三级模型、拖拽状态流转、WebSocket 实时同步、乐观锁防覆盖
- [[202-会员积分与营销系统]] — 会员积分实战：积分流水与余额一致性、防重复领取、签到日历、积分排行榜(ZSet)、过期清理
- [[203-企业网盘系统]] — 企业网盘实战：MinIO 对象存储、分片上传/断点续传/秒传、预签名 URL、分享链接、回收站
- [[204-企业即时通讯系统]] — 企业 IM 实战：WebSocket 会话管理、单聊/群聊、离线消息补拉、已读回执、在线状态
- [[205-工单客服系统]] — 工单客服实战：工单状态机流转、SLA 超时提醒与升级、按技能组智能分派、满意度评价
- [[206-秒杀系统实战]] — 秒杀实战：Lua 原子扣库存防超卖、Redis SETNX 限购、MQ 削峰异步落单、支付超时自动取消回补、Sentinel 限流熔断
- [[207-数据平台实战]] — 数据平台实战：Kafka 数据管道、ES 按天索引明细+聚合、Redis 实时计数(PV/UV/GMV)、ECharts 大屏
- [[208-电商后台管理系统]] — 电商后台实战：SPU/SKU 商品模型、库存与订单联动、优惠券/满减促销、会员管理
- [[209-在线支付系统]] — 在线支付实战：支付宝/微信网关、回调验签、回调幂等、原路退款、日对账与差错处理
- [[210-物流配送管理系统]] — 物流配送实战：运单状态机(揽收/运输/派送/签收)、轨迹链、按区域路由分派、异常件处理
- [[211-招聘管理系统]] — 招聘管理实战：简历上传解析、筛选标签、面试流程状态机、Offer 管理、人才库
- [[212-企业知识库系统]] — 知识库实战：文档树形目录、版本管理回滚、ES 全文检索、阅读权限、审批发布
- [[213-图书馆借阅管理系统]] — 图书馆实战：借阅状态机、逾期罚款计算、在借图书预约、续借、热门排行
- [[214-停车场管理系统]] — 停车场实战：阶梯计费规则引擎、入场出场状态机、月卡管理、道闸联动、防重复计费
- [[215-问卷调查系统]] — 问卷实战：动态题型数据模型、防重复提交、选项分布统计与交叉分析、Excel 导出
- [[216-会议室预约系统]] — 会议室预约实战：时间段冲突检测、并发预约防冲突、审批流程、会议提醒与纪要
- [[217-外卖点餐系统]] — 外卖实战：Redis 购物车、下单事务(订单+明细+库存)、订单状态机、配送管理
- [[218-低代码表单引擎]] — 低代码实战：JSON Schema 驱动表单、拖拽设计器、后端权威校验、防重提交、模板套用
- [[219-可视化流程编排引擎]] — 流程编排实战：自研 DAG 执行引擎、条件分支求值、定时/事件触发、执行日志与重试
- [[220-多租户SaaS平台]] — SaaS 实战：租户隔离策略(tenant_id/schema)、套餐订阅、用量计量、账单生成
- [[221-实时协作白板]] — 协作白板实战：WebSocket 广播、CRDT 无冲突合并、光标同步、历史版本回放
- [[222-网约车调度系统]] — 网约车实战：Redis GEO 就近匹配、派单策略、动态计价、行程状态机
- [[223-共享充电宝系统]] — 共享充电宝实战：租借归还状态机、归还计费结算、设备离线补偿、押金退还
- [[224-社区团购系统]] — 社区团购实战：成团判定、未成团自动退款、团长佣金分账、自提点管理
- [[225-电子合同签署系统]] — 电子合同实战：RSA 数字签名、时间戳存证、PDF 坐标签章、哈希链防篡改
- [[226-统一认证中心]] — SSO 实战：OAuth2 授权码、JWT+Redis 会话、一处登录处处登录、Token 黑名单
- [[227-定时任务调度平台]] — 任务调度实战：分布式防重复执行、执行日志链路、失败重试、DAG 编排、告警

## 前端知识库

> 基于「前端完整知识库总目录」搭建目录骨架（103 篇章、416 个主题），内容已全部完成（01~103 篇章全部完成）。入口见 `frontend-fullstack/README.md`。

- [[frontend-fullstack/README]] — 前端完整知识库：目录树（103 篇章）+ 进度追踪表，覆盖计算机基础/网络/HTML/CSS/JS/TS/工程化/React/Vue/Node/BFF/性能安全/架构全链路

### 01-计算机基础与开发环境

- [[01.1-计算机组成原理]] — CPU/GPU/ALU/寄存器/指令集、存储层次与 Cache、内存与虚拟内存、SSD/HDD、IO/DMA/中断、总线、字节序、字符编码，前端视角解析缓存友好遍历/TypedArray/位运算/乱码
- [[01.2-操作系统]] — 操作系统核心概念：进程/线程/协程、上下文切换与调度、内存管理（虚拟内存/页表/Page Fault）、文件系统与文件描述符、Socket、系统调用、IPC、信号、权限、用户态与内核态，结合浏览器多进程架构与 Node.js 场景讲解
- [[01.3-Linux]] — Linux 文件系统、Shell/Bash/Zsh、文本三剑客、find/xargs、网络与传输工具、进程与网络排查、systemd/cron、权限与环境变量、日志，前端部署排障视角
- [[01.4-Git]] — Git 从基础概念到协作工作流：commit/branch/tag、merge/rebase/cherry-pick、reset/revert/stash/reflog、diff/blame/bisect、submodule/worktree、hooks、Conventional Commits、Git Flow 与主干开发、Monorepo、PR 与 Code Review
- [[01.5-IDE 与开发环境]] — 前端开发环境全链路：VS Code 与 JetBrains、Chrome/Firefox DevTools、Node.js、npm/pnpm/Yarn 包管理器、Corepack、nvm/fnm/Volta 版本管理、Docker、Dev Container、WSL

### 02-计算机网络

- [[02.1-网络基础]] — OSI/TCP-IP 分层模型、数据链路层 MAC/ARP、网络层 IP/IPv4/IPv6、子网划分、路由、NAT、DHCP、ICMP，数据包从浏览器到服务器的完整旅程
- [[02.2-TCP]] — TCP 报文结构与标志位（SYN/ACK/FIN/RST）、三次握手/四次挥手、序号与确认号、流量控制、拥塞控制（慢启动/快重传/快恢复）、重传机制、Keep Alive 与半连接、粘包拆包
- [[02.3-UDP]] — UDP 数据报与无连接、丢包与乱序、QUIC 与 HTTP/3、TCP vs UDP 对比，WebRTC 与 DNS 场景
- [[02.4-DNS]] — 域名结构（Root/TLD）、解析流程（Resolver/权威服务器）、A/AAAA/CNAME/TXT/MX/NS 记录、DNS Cache 与 TTL、DoH/DoT 加密 DNS
- [[02.5-HTTP]] — HTTP 版本演进（0.9~3）、请求/响应报文结构、方法语义（GET/POST/PUT/PATCH/DELETE/OPTIONS/HEAD）、状态码（2xx/3xx/4xx/5xx）
- [[02.6-HTTP Header]] — 请求头（Host/User-Agent/Accept/Authorization）、实体头、Cookie 相关、缓存头（Cache-Control/ETag/Last-Modified）、安全跨域（Origin/Referer/CSP/CORS）、Range 与 Connection
- [[02.7-HTTPS-TLS]] — TLS/SSL、对称与非对称加密（RSA/ECC/AES）、SHA/HMAC、证书与 CA、TLS 握手、SNI/ALPN、HSTS、证书锁定
- [[02.8-CDN]] — CDN 原理（边缘节点/源站）、缓存命中与回源、刷新与预热、静态资源/图片 CDN、动态加速、DNS 调度

### 03-Web 标准与浏览器基础

- [[03.1-Web 标准]] — W3C/WHATWG/TC39 标准组织、ECMAScript 与 JavaScript、Web Platform 平台能力、渐进增强与优雅降级、可访问性（a11y）
- [[03.2-URL]] — URL 结构（Scheme/Host/Port/Path/Query/Fragment）、URL Encoding 百分号编码、URL API 解析、Origin 与同源策略
- [[03.3-MIME]] — MIME 类型与 Content-Type、text/html 与 text/css、application/javascript 与 json、image/font/video/audio 多媒体类型
- [[03.4-字符编码]] — ASCII、Unicode 码点、UTF-8/UTF-16/UTF-32 编码方案、Base64、URL Encoding 与 HTML Entity

### 04-HTML 完整知识体系

- [[04.1-HTML 基础]] — 文档结构、DOCTYPE 与标准模式、html/head/body、meta（charset/viewport）、title/link/style、script 加载策略（defer/async/module）、noscript
- [[04.2-语义化标签]] — header/nav/main/footer、section/article/aside、address/figure/figcaption/time/mark、details/summary 原生折叠
- [[04.3-文本]] — h1-h6/p、strong/em/b/i/small 语义区分、code/pre、blockquote/q/cite、span/abbr/sub/sup
- [[04.4-链接]] — a/href、target 与 rel="noopener" 安全、download 下载、mailto/tel 协议、锚点与 :target
- [[04.5-列表]] — ul/ol/li、dl/dt/dd 定义列表、列表嵌套与语义
- [[04.6-表格]] — table/tr/th/td、thead/tbody/tfoot、caption、colspan/rowspan 合并、scope 可访问性
- [[04.7-表单]] — form、input 全部类型、textarea/select/option/optgroup/datalist、button/label、fieldset/legend、autocomplete、原生校验
- [[04.8-多媒体]] — img、picture/source、audio/video、track 字幕、iframe 安全（sandbox）、embed/object
- [[04.9-图片]] — src/srcset/sizes、picture 与艺术指导、响应式图片、loading="lazy"、decoding="async"
- [[04.10-SEO]] — title/description、canonical、robots 与 Robots.txt、sitemap、Open Graph/Twitter Card、JSON-LD 结构化数据、SSR SEO
- [[04.11-Accessibility]] — WCAG、ARIA 与 role、aria-* 属性、键盘导航、焦点管理、屏幕阅读器、颜色对比度、reduced motion

### 05-CSS 核心

- [[05.1-CSS 基础]] — CSS 语法、Cascade 层叠、Specificity 优先级、Inheritance 继承、initial/unset/revert、!important
- [[05.2-选择器]] — 基础/属性/组合选择器、状态伪类（hover/focus/focus-visible）、结构伪类（nth-child）、函数伪类（not/is/where/has）
- [[05.3-Box Model]] — content/padding/border/margin、box-sizing（border-box）、width/height 与 min/max、overflow
- [[05.4-Display]] — block/inline/inline-block、none 隐藏、flex/grid、table/flow-root/contents
- [[05.5-Position]] — static/relative/absolute/fixed/sticky、z-index、层叠上下文
- [[05.6-Flex]] — 容器属性（direction/wrap/justify/align/gap）、子项属性（grow/shrink/basis）、order/align-self
- [[05.7-Grid]] — grid-template-columns/rows、fr 与 minmax、grid-column/row/area、显式/隐式网格、auto-fit/auto-fill
- [[05.8-定位与层叠]] — containing block 包含块、stacking context 层叠上下文、z-index 深入、fixed/sticky/absolute 层叠行为

### 06-CSS 高级布局

- [[06.1-响应式布局]] — Media Query 与 Breakpoint、Mobile First/Desktop First、流式布局、响应式字体与图片、Container Query
- [[06.2-CSS 单位]] — px、%/em/rem、vw/vh 与 svh/lvh/dvh、vmin/vmax、ch/ex
- [[06.3-函数]] — calc、min/max/clamp、var、env 安全区域、color-mix、attr
- [[06.4-CSS 变量]] — Custom Properties、作用域、Theme 与 Design Token、动态主题、Dark Mode
- [[06.5-CSS Grid 高级]] — 命名网格线、命名区域、自动放置（dense）、Subgrid、Masonry 瀑布流
- [[06.6-Container Query]] — container-type/name、@container 查询、容器单位（cqw）

### 07-CSS 视觉与动画

- [[07.1-背景]] — background、linear/radial/conic 渐变、background-size/position/repeat
- [[07.2-边框]] — border、border-radius、outline 焦点、box-shadow 与 inset 内阴影
- [[07.3-文本]] — font-family/size/weight、line-height、letter-spacing、text-align、white-space、text-overflow、word-break、overflow-wrap
- [[07.4-Transform]] — translate/rotate/scale/skew、transform-origin、perspective 与 3D transform
- [[07.5-Transition]] — transition-property/duration/delay、timing-function 与 cubic-bezier
- [[07.6-Animation]] — @keyframes、animation 各属性、direction/fill-mode/play-state
- [[07.7-CSS 性能]] — Layout/Paint/Composite 渲染流水线、transform/opacity 高性能、will-change、GPU 合成

### 08-CSS 工程化

- [[08.1-CSS Architecture]] — BEM/OOCSS/SMACSS/ITCSS 分层、Utility First、CSS Modules、Scoped CSS
- [[08.2-CSS 预处理]] — Sass/SCSS/Less、变量、嵌套、Mixin、函数、Extend
- [[08.3-CSS-in-JS]] — Styled Components、Emotion、Vanilla Extract、运行时与零运行时
- [[08.4-原子化 CSS]] — Tailwind、UnoCSS、Windi、工具类、Design Token
- [[08.5-CSS 构建]] — PostCSS、Autoprefixer、Minify、Tree Shaking、Code Splitting、Extraction

### 09-JavaScript 基础

- [[09.1-ECMAScript]] — TC39 提案流程、ES5/ES6、ES2016+ 到 ES2025+
- [[09.2-数据类型]] — Undefined/Null/Boolean/Number/BigInt/String/Symbol/Object
- [[09.3-原始类型]] — Primitive、Immutable、Value Semantics、Boxing
- [[09.4-Number]] — IEEE 754、NaN、Infinity、-0、安全整数、BigInt
- [[09.5-String]] — UTF-16、Unicode、模板字符串、方法、迭代器、RegExp
- [[09.6-Object]] — 属性描述符、原型链、Object.create/assign、Reflect

### 10-JavaScript 语法与执行机制

- [[10.1-变量]] — var/let/const、TDZ、Hoisting、Scope
- [[10.2-运算符]] — 算术/比较/逻辑、空值合并、可选链、位运算、typeof/instanceof
- [[10.3-控制流]] — if/switch、for/for...in/for...of、while、break/continue、try/catch
- [[10.4-函数]] — 函数声明/表达式、箭头函数、默认参数、Rest、高阶函数与回调
- [[10.5-闭包]] — 词法环境、作用域链、私有变量、函数工厂、模块模式

### 11-JavaScript 高级机制

- [[11.1-执行上下文]] — 全局/函数上下文、词法环境、变量环境、环境记录
- [[11.2-this]] — 绑定规则、call/apply/bind、箭头函数
- [[11.3-原型]] — prototype/__proto__/constructor、原型链、继承、Object.create
- [[11.4-类]] — class、constructor、extends/super、static、私有字段、getter/setter、mixin
- [[11.5-Symbol]] — 唯一值、Symbol.iterator/asyncIterator/toPrimitive/toStringTag
- [[11.6-Iterator]] — Iterator/Iterable、Generator、yield/yield*、异步迭代器、for...of
- [[11.7-Proxy-Reflect]] — Proxy 陷阱、get/set/has/apply/construct、Reflect

### 12-JavaScript 异步编程

- [[12.1-Callback]] — 回调、Error-First、回调地狱
- [[12.2-Promise]] — 状态、then/catch/finally、all/allSettled/race/any
- [[12.3-Async-Await]] — async/await、错误处理、串行与并发、队列
- [[12.4-Event Loop]] — 调用栈、宏任务/微任务、渲染时机、rAF/rIC
- [[12.5-并发控制]] — 并发池、限流、重试、指数退避、超时、取消

### 13-JavaScript 模块化

- [[13.1-CommonJS]] — require、module.exports、exports、require cache
- [[13.2-ES Modules]] — import/export、默认/命名导出、动态导入、import.meta
- [[13.3-Module Resolution]] — exports 条件导出、imports、main/module/browser/types
- [[13.4-Module Systems]] — AMD、UMD、CommonJS、ESM、SystemJS

### 14-JavaScript 内置对象与 API

- [[14.1-Object]] — keys/values/entries、fromEntries、freeze/seal、defineProperty
- [[14.2-Array]] — map/filter/reduce、find、some/every、flat/flatMap、sort/toSorted
- [[14.3-Map-Set]] — Map/WeakMap、Set/WeakSet
- [[14.4-Date-Temporal]] — Date、时区、UTC、Intl.DateTimeFormat、Temporal
- [[14.5-RegExp]] — 模式、字符类、分组、断言、反向引用、标志
- [[14.6-JSON]] — parse、stringify、序列化/反序列化
- [[14.7-Intl]] — NumberFormat、DateTimeFormat、Collator、RelativeTimeFormat 等

### 15-DOM

- [[15.1-DOM 树]] — Document、Element、Node、Text、DocumentFragment、ShadowRoot
- [[15.2-查询]] — getElementById、querySelector、closest、matches
- [[15.3-修改]] — createElement、append、remove、cloneNode、innerHTML、insertAdjacentHTML
- [[15.4-属性]] — getAttribute、dataset、classList、style
- [[15.5-DOM 遍历]] — parentNode、children、firstChild、nextSibling 等

### 16-DOM 事件

- [[16.1-Event]] — 事件对象、MouseEvent、KeyboardEvent、PointerEvent
- [[16.2-事件机制]] — 捕获/目标/冒泡、stopPropagation、preventDefault、passive/once
- [[16.3-Event Delegation]] — 事件委托、动态节点、冒泡机制
- [[16.4-常见事件]] — 鼠标/键盘/表单/焦点/滚动事件

### 17-BOM 与 Web API

- [[17.1-Window]] — window、location、history、navigator、screen、document
- [[17.2-Location]] — URL 组成、href、search/hash、assign/replace/reload
- [[17.3-History]] — pushState、replaceState、popstate、back/forward/go
- [[17.4-Storage]] — localStorage、sessionStorage、Storage Event、IndexedDB、Cache API
- [[17.5-Clipboard]] — Clipboard API、readText/writeText、ClipboardItem
- [[17.6-Notification]] — Notification API、Permission、Push Notification
- [[17.7-File]] — File/Blob、FileReader、ArrayBuffer、TypedArray、createObjectURL

### 18-Fetch-网络请求

- [[18.1-Fetch]] — fetch、Request/Response、Headers、Body、流式处理
- [[18.2-Axios]] — 拦截器、请求配置、响应转换、重试/超时/取消
- [[18.3-REST]] — 资源与 CRUD、幂等性、分页、过滤排序、版本、错误码
- [[18.4-GraphQL]] — Schema、Query/Mutation/Subscription、Resolver、Fragment
- [[18.5-WebSocket]] — 握手、帧、心跳、重连、背压
- [[18.6-SSE]] — EventSource、事件流、自动重连、Last-Event-ID
- [[18.7-WebTransport]] — QUIC、Stream、Datagram、双向流

### 19-浏览器原理

- [[19.1-浏览器架构]] — 多进程、渲染进程、GPU/网络进程、沙箱、站点隔离
- [[19.2-渲染流程]] — DOM/CSSOM、渲染树、Layout/Paint/Raster/Composite
- [[19.3-JavaScript 执行]] — 解析、AST、字节码、JIT、反优化
- [[19.4-V8]] — 分代 GC、Mark-Sweep、隐藏类、Ignition/TurboFan
- [[19.5-Layout]] — 布局、回流、重绘、强制同步布局、布局抖动
- [[19.6-Composite]] — 图层、合成、GPU 光栅化、transform 图层

### 20-浏览器存储

- [[20.1-Cookie]] — Domain/Path、过期、Secure/HttpOnly、SameSite、Partitioned
- [[20.2-Web Storage]] — localStorage、sessionStorage
- [[20.3-IndexedDB]] — 对象仓库、事务、索引、游标、版本升级、结构化克隆
- [[20.4-Cache Storage]] — Cache、CacheStorage、Service Worker 缓存

### 21-浏览器缓存

- [[21.1-HTTP Cache]] — Cache-Control、ETag、Last-Modified、协商缓存、304
- [[21.2-缓存策略]] — 新鲜度、重新验证、immutable、max-age、stale-while-revalidate
- [[21.3-前端缓存]] — 内存缓存、磁盘缓存、Service Worker、CDN 缓存

### 22-Service Worker-PWA

- [[22.1-Service Worker]] — Install/Activate/Fetch、生命周期、Scope、更新
- [[22.2-PWA]] — Manifest、离线、可安装、推送、后台同步
- [[22.3-Cache Strategy]] — Cache First、Network First、Stale While Revalidate

### 23-Web Components

- [[23.1-Custom Elements]] — customElements.define、HTMLElement、生命周期回调
- [[23.2-Shadow DOM]] — Shadow Root、封装、open/closed、阴影边界
- [[23.3-Templates]] — template、slot、named slot、slotchange
- [[23.4-CSS Shadow Parts]] — ::part、::slotted

### 24-TypeScript 基础

- [[24.1-类型系统]] — 原始类型、unknown/any/never/void
- [[24.2-Interface]] — 可选/只读、索引签名、extends、声明合并
- [[24.3-Type]] — 类型别名、联合/交叉、字面量、元组、函数类型
- [[24.4-类型推断]] — 推断、上下文类型、拓宽、收窄、控制流分析

### 25-TypeScript 高级

- [[25.1-Generics]] — 泛型函数/接口/类、约束、keyof、typeof、infer
- [[25.2-Utility Types]] — Partial/Pick/Omit/Record 等内置工具类型
- [[25.3-Advanced Types]] — 条件/映射/模板字面量类型、可辨识联合、类型守卫
- [[25.4-类型工程]] — API 类型生成、OpenAPI、GraphQL Codegen、Zod

### 26-npm-pnpm-Yarn 与包管理

- [[26.1-package.json]] — 依赖字段、scripts、engines、exports、bin、files
- [[26.2-Lockfile]] — 锁文件、依赖解析、完整性、确定性安装
- [[26.3-SemVer]] — major/minor/patch、caret/tilde、prerelease
- [[26.4-包发布]] — npm publish、私有源、scoped 包、provenance

### 27-前端工程化

- [[27.1-工程规范]] — ESLint、Prettier、Stylelint、Husky、Commitlint、Conventional Commits
- [[27.2-代码质量]] — 静态分析、类型检查、复杂度、技术债
- [[27.3-Git Hooks]] — pre-commit、commit-msg、pre-push、CI 校验
- [[27.4-环境管理]] — development/test/staging/production、环境变量、feature flags

### 28-Webpack

- [[28.1-核心概念]] — Entry、Output、Loader、Plugin、Module、Chunk、Bundle
- [[28.2-Loader]] — babel/css/style/postcss/sass-loader、file/url-loader
- [[28.3-Plugin]] — HtmlWebpackPlugin、MiniCssExtractPlugin、DefinePlugin 等
- [[28.4-优化]] — Tree Shaking、Code Splitting、懒加载、缓存、Module Federation

### 29-Vite

- [[29.1-Vite 原理]] — Native ESM、Dev Server、预打包、esbuild、HMR
- [[29.2-配置]] — vite.config、plugins、alias、server、build、optimizeDeps
- [[29.3-Plugin]] — Plugin API、transform、resolveId、configureServer
- [[29.4-Vite 优化]] — 依赖优化、分包、资源处理、CSS 分割

### 30-Rollup-esbuild-SWC-Babel

- [[30.1-Rollup]] — ESM、Tree Shaking、插件、库构建
- [[30.2-esbuild]] — Parser、Bundler、Transformer、Minifier
- [[30.3-SWC]] — Rust、Parser、Transformer、Minifier
- [[30.4-Babel]] — AST、Transform、Plugin、Preset、Polyfill
- [[30.5-编译原理]] — Lexer、Parser、AST、Transform、Codegen、Source Map

### 31-前端资源与构建优化

- [[31.1-JavaScript]] — 压缩、Tree Shaking、代码分割、懒加载、Vendor Chunk
- [[31.2-CSS]] — 压缩、Purge、关键 CSS、提取
- [[31.3-图片]] — WebP/AVIF、响应式图片、懒加载、压缩、雪碧图
- [[31.4-字体]] — WOFF2、子集化、font-display、Preload、可变字体

### 32-Source Map 与调试

- [[32.1-Source Map]] — mappings、sources、inline/hidden source map
- [[32.2-Debug]] — 断点、条件断点、watch、调用栈、性能/内存分析

### 33-React 完整知识体系

- [[33.1-React 基础]] — JSX、Component、Props、State、条件/列表渲染
- [[33.2-Hooks]] — useState/useEffect 等全部内置 Hook
- [[33.3-React 生命周期思想]] — Mount/Update/Unmount、Render/Commit Phase
- [[33.4-Fiber]] — Fiber 树、Reconciliation、Diff、Scheduler、Lane
- [[33.5-Concurrent Rendering]] — 并发模式、Transition、Suspense、可中断渲染

### 34-React 高级

- [[34.1-Context]] — Provider/Consumer、性能、Context 拆分
- [[34.2-Suspense]] — Suspense 边界、Lazy、流式 SSR
- [[34.3-Error Boundary]] — 错误边界、Fallback、错误恢复
- [[34.4-React Server Components]] — 服务端/客户端组件、Server Action、RSC Payload
- [[34.5-React Compiler]] — 自动记忆化、Rules of React

### 35-Vue 完整知识体系

- [[35.1-Vue 基础]] — Template、组件、Props/Emits/Slots、指令、生命周期
- [[35.2-Vue 3]] — Composition API、setup、ref/reactive、provide/inject
- [[35.3-Vue 响应式原理]] — Proxy、依赖追踪、Effect、调度
- [[35.4-Vue 编译]] — 模板编译器、AST、Codegen、VNode、Patch
- [[35.5-Vue Router]] — 路由、导航守卫、动态/嵌套/懒加载路由

### 36-状态管理

- [[36.1-状态分类]] — 本地/全局/服务端/URL/表单/缓存状态
- [[36.2-Redux]] — Store、Action、Reducer、Middleware、Redux Toolkit
- [[36.3-Zustand]] — Store、Selector、Middleware、持久化
- [[36.4-MobX]] — Observable、Action、Computed、Reaction
- [[36.5-Pinia]] — Store、State、Getter、Action、Plugin
- [[36.6-TanStack Query]] — Query、Mutation、缓存、乐观更新、无限查询

### 37-前端路由

- [[37.1-SPA Routing]] — Hash/History 路由、嵌套/动态路由
- [[37.2-路由守卫]] — 认证、授权、权限、导航守卫、重定向
- [[37.3-路由优化]] — 懒加载、Prefetch、Preload、代码分割

### 38-表单工程

- [[38.1-表单基础]] — Input/Select/Checkbox、上传、日期、富文本、校验
- [[38.2-表单状态]] — 受控/非受控、Dirty/Touched、错误、提交
- [[38.3-表单库]] — React Hook Form、Formik、Zod 校验
- [[38.4-高级表单]] — 动态/嵌套表单、异步校验、多步、自动保存

### 39-UI 组件库

- [[39.1-基础组件]] — Button/Input/Modal/Dropdown 等 18 种
- [[39.2-数据展示]] — Table、Tree、Tabs、Pagination、Descriptions
- [[39.3-反馈]] — Alert、Message、Progress、Skeleton、Result
- [[39.4-UI 框架]] — Ant Design、Material UI、shadcn/ui、Element Plus 等

### 40-Design System

- [[40.1-Design Token]] — 颜色、排版、间距、圆角、阴影、动效、Z-index
- [[40.2-Theme]] — 亮/暗色、高对比度、品牌主题、运行时主题、CSS 变量
- [[40.3-Component API]] — Variant、Size、State、Slot、组合、可访问性
- [[40.4-Design System 工程]] — Figma、Storybook、Chromatic、Token 同步

### 41-前端数据可视化

- [[41.1-图表基础]] — 柱/线/饼/散点/雷达/热力/漏斗/桑基/树/图
- [[41.2-D3]] — Scale、Axis、Selection、Data Join、Transition、SVG/Canvas
- [[41.3-ECharts]] — Series、Dataset、Tooltip、Legend、DataZoom、VisualMap
- [[41.4-Three.js]] — Scene、Camera、Renderer、Mesh、材质、光照、Raycaster
- [[41.5-WebGL]] — Shader、顶点/片元着色器、Buffer、Uniform、渲染管线

### 42-Node.js

- [[42.1-Node.js 基础]] — Runtime、V8、libuv、Event Loop、Process、Buffer
- [[42.2-Node API]] — fs/path/os/crypto/http、child_process、worker_threads
- [[42.3-Stream]] — Readable/Writable/Duplex/Transform、背压、pipe/pipeline
- [[42.4-Node 性能]] — Event Loop Lag、CPU/堆分析、GC、内存泄漏、Worker

### 43-Node.js Web 服务

- [[43.1-Express]] — Middleware、Router、Request/Response、错误处理
- [[43.2-Koa]] — 中间件、Context、异步中间件
- [[43.3-Fastify]] — Plugin、Schema、校验、序列化
- [[43.4-NestJS]] — Module、Controller、Provider、依赖注入、Guard/Interceptor

### 44-BFF

- [[44.1-BFF 原理]] — 后端面向前端、聚合、数据塑形、鉴权、缓存
- [[44.2-BFF 工程]] — Node.js、NestJS、GraphQL、gRPC、限流、熔断

### 45-前端性能优化

- [[45.1-性能指标]] — TTFB/FCP/LCP/CLS/INP/TTI/TBT
- [[45.2-网络性能]] — DNS/TCP/TLS、HTTP/2/3、CDN、压缩、资源提示
- [[45.3-资源优化]] — 代码分割、懒加载、Preload/Prefetch、图片/字体优化
- [[45.4-JavaScript 优化]] — 长任务、防抖节流、Web Worker、rIC
- [[45.5-Rendering Optimization]] — 减少回流重绘、批量 DOM、虚拟化
- [[45.6-React 性能]] — memo/useMemo、Context 拆分、虚拟列表、Profiler
- [[45.7-Vue 性能]] — Computed、v-once/v-memo、KeepAlive、异步组件

### 46-Web Worker

- [[46.1-Worker]] — Dedicated/Shared Worker、postMessage、Transferable、Atomics
- [[46.2-Worker 应用]] — 图片处理、大数据计算、加密、AI 推理

### 47-WebAssembly

- [[47.1-WASM 基础]] — Module、Instance、Memory、Table、Import/Export
- [[47.2-语言生态]] — C/C++、Rust、AssemblyScript、Go
- [[47.3-WASM 工程]] — wasm-bindgen、Emscripten、WASI、SIMD、流式编译
- [[47.4-WASM 应用]] — 图像、音视频、游戏、加密、AI 推理

### 48-前端安全

- [[48.1-XSS]] — 反射/存储/DOM 型、innerHTML、净化、CSP
- [[48.2-CSRF]] — SameSite、CSRF Token、Origin 校验
- [[48.3-CORS]] — 同源策略、预检、Access-Control-Allow-Origin
- [[48.4-Clickjacking]] — iframe、X-Frame-Options、frame-ancestors
- [[48.5-DOM Clobbering]] — DOM 劫持、Trusted Types
- [[48.6-Supply Chain]] — 依赖攻击、抢注、依赖混淆、SBOM

### 49-Web 安全高级

- [[49.1-CSP]] — 各指令、nonce/hash、strict-dynamic、report
- [[49.2-Trusted Types]] — TrustedHTML/TrustedScript、Policy
- [[49.3-安全 Header]] — CSP、HSTS、Referrer-Policy、COOP/CORP/COEP
- [[49.4-身份认证]] — Session、JWT、OAuth 2.0、OIDC、Passkey/WebAuthn

### 50-前端认证与权限

- [[50.1-Authentication]] — 登录、Session、Token、Refresh Token、JWT
- [[50.2-Authorization]] — RBAC、ABAC、ACL、路由/按钮/数据权限
- [[50.3-OAuth]] — 授权码、客户端凭证、PKCE、Refresh Token
- [[50.4-SSO]] — OAuth SSO、OIDC、SAML、CAS

### 51-前端测试

- [[51.1-测试类型]] — 单元/集成/组件/E2E/视觉/性能/可访问性测试
- [[51.2-Jest-Vitest]] — Test、Expect、Mock、Snapshot、Coverage、Fake Timer
- [[51.3-Testing Library]] — React/Vue/DOM Testing Library、User Event
- [[51.4-Playwright]] — Browser、Locator、Assertion、Trace、Network Mock
- [[51.5-Cypress]] — 组件测试、E2E、Intercept、Fixture
- [[51.6-Mock]] — MSW、API Mock、Mock Data

### 52-可访问性测试

- [[52.1-可访问性测试]] — axe、Lighthouse、键盘/屏幕阅读器测试、WCAG 审计

### 53-前端错误处理

- [[53.1-JavaScript Error]] — try/catch、Error 类型、RangeError、AggregateError
- [[53.2-Promise Error]] — rejection、unhandledrejection
- [[53.3-Resource Error]] — 脚本/图片/CSS/网络错误
- [[53.4-Framework Error]] — React Error Boundary、Vue Error Handler
- [[53.5-错误上报]] — Error ID、堆栈、Source Map、Breadcrumb

### 54-前端可观测性

- [[54.1-Logs]] — 结构化日志、错误日志、用户行为日志
- [[54.2-Metrics]] — 错误率、延迟、LCP/INP/CLS、API 延迟
- [[54.3-Tracing]] — Trace、Span、Trace ID、上下文传播
- [[54.4-RUM]] — 真实用户监控、设备/浏览器/网络/地区
- [[54.5-工具]] — Sentry、OpenTelemetry、Prometheus、Grafana

### 55-前端监控系统

- [[55.1-错误监控]] — JS/Promise/资源/API/Chunk 错误
- [[55.2-性能监控]] — Web Vitals、Navigation/Resource Timing、Long Task
- [[55.3-业务监控]] — PV/UV、转化、漏斗、留存
- [[55.4-Source Map]] — Source Map 上传、Release、堆栈还原

### 56-SSR-SSG-ISR

- [[56.1-SSR]] — 服务端渲染、请求时渲染、Hydration、流式 SSR
- [[56.2-SSG]] — 静态生成、构建时渲染、静态 HTML
- [[56.3-ISR]] — 增量静态再生成、Revalidate、按需再验证
- [[56.4-Hydration]] — Hydration、部分/选择性 Hydration、不匹配

### 57-Next.js

- [[57.1-Routing]] — App/Pages Router、文件路由、动态/并行/拦截路由
- [[57.2-Rendering]] — SSR/SSG/ISR、Streaming、RSC
- [[57.3-Server]] — Server Component、Server Action、Route Handler、Middleware
- [[57.4-Cache]] — 请求/数据/全路由/路由器缓存、Revalidation
- [[57.5-Next.js 优化]] — Image、Font、Script、动态导入、Metadata

### 58-Nuxt

- [[58.1-Nuxt]] — 文件路由、自动导入、SSR/SSG、混合渲染、Nitro
- [[58.2-Nitro]] — Server Routes、API Routes、Presets、Edge Runtime
- [[58.3-Nuxt 优化]] — 懒加载组件、Route Rules、Payload、缓存

### 59-微前端

- [[59.1-微前端思想]] — 独立部署、团队自治、领域拆分
- [[59.2-技术方案]] — iframe、Module Federation、qiankun、single-spa、Web Components
- [[59.3-微前端核心问题]] — 加载、路由、样式/JS 隔离、通信、监控
- [[59.4-Module Federation]] — Host/Remote、Shared、Exposes、版本冲突

### 60-Monorepo

- [[60.1-Monorepo]] — Workspace、Package、共享/内部包、依赖图
- [[60.2-工具]] — pnpm workspace、Nx、Turborepo、Rush、Lerna
- [[60.3-Monorepo 工程]] — Task Graph、缓存、增量/受影响构建、依赖约束

### 61-前端组件库工程

- [[61.1-组件库]] — Component API、Theme/Token、可访问性、国际化
- [[61.2-Storybook]] — Story、Args/Controls、Docs、交互测试、视觉回归
- [[61.3-组件发布]] — ESM/CJS/UMD、类型声明、Tree Shaking、SemVer
- [[61.4-组件质量]] — 单元/组件/视觉测试、可访问性、Bundle Size

### 62-国际化 i18n

- [[62.1-国际化]] — i18n/l10n、Locale、时区、货币
- [[62.2-翻译]] — Message Catalog、复数、ICU Message Format、动态翻译
- [[62.3-RTL]] — RTL/LTR、逻辑属性
- [[62.4-国际化工程]] — 懒加载翻译、翻译提取/管理、Fallback

### 63-前端动画

- [[63.1-CSS Animation]] — Transition、Keyframes、Transform
- [[63.2-Web Animations API]] — Animation、KeyframeEffect、AnimationTimeline
- [[63.3-requestAnimationFrame]] — 帧、60 FPS、Frame Budget、Jank
- [[63.4-动画库]] — GSAP、Framer Motion、Motion、Lottie

### 64-音视频

- [[64.1-Media]] — Audio/Video、MediaSource、MediaRecorder、Web Audio API
- [[64.2-播放]] — HTMLMediaElement、字幕、HLS/DASH
- [[64.3-实时通信]] — WebRTC、PeerConnection、ICE/STUN/TURN、SDP
- [[64.4-WebRTC]] — 摄像头/麦克风、屏幕共享、码率、弱网适配

### 65-WebRTC 工程

- [[65.1-WebRTC 工程]] — 信令、SFU/MCU/Mesh、Simulcast、录制、直播

### 66-移动端 Web

- [[66.1-移动浏览器]] — Mobile Safari、Chrome Android、Viewport、安全区
- [[66.2-移动适配]] — Responsive、Rem、视口单位、触控目标、手势
- [[66.3-移动性能]] — 首屏、Bundle、网络、内存、电池、滚动性能

### 67-跨端开发

- [[67.1-React Native]] — Component、Bridge、JSI、Fabric、Hermes
- [[67.2-Flutter]] — Widget、Dart、渲染引擎、Platform Channel、Isolate
- [[67.3-UniApp]] — Vue、H5、小程序、App
- [[67.4-Taro]] — React、小程序、H5、Native
- [[67.5-Electron]] — Main/Renderer Process、Preload、IPC、Context Isolation
- [[67.6-Tauri]] — Rust、WebView、IPC、Native API

### 68-Electron

- [[68.1-架构]] — Main、Renderer、Preload、IPC、ContextBridge
- [[68.2-安全]] — Context Isolation、Sandbox、Node Integration、CSP
- [[68.3-工程]] — 自动更新、打包、代码签名、原生模块

### 69-WebView

- [[69.1-WebView]] — Android/iOS WebView、JS Bridge、Deep Link、Cookie、Hybrid

### 70-Serverless-Edge

- [[70.1-Serverless]] — Function/Trigger/Cold Start/Warm Start、Stateless 无状态约束、Event Driven 事件驱动
- [[70.2-Edge Computing]] — Edge Runtime/Edge Function、CDN Compute、Low Latency 低延迟
- [[70.3-平台]] — Cloudflare Workers、Vercel Functions、AWS Lambda、Deno Deploy、Edge Middleware

### 71-前端 AI

- [[71.1-AI SDK]] — LLM API、Streaming、Chat、Tool Calling、Structured Output
- [[71.2-浏览器 AI]] — WebGPU/WebNN/WASM、ONNX Runtime Web、Transformers.js
- [[71.3-AI UI]] — Chat UI、Streaming UI、Markdown/Code Highlight、Citation、Tool/Reasoning Status、Human-in-the-loop
- [[71.4-RAG 前端]] — Document Upload、Chunk Preview、Retrieval、Citation、Source Preview、Vector Search UI

### 72-WebGPU

- [[72.1-WebGPU]] — Adapter/Device/Queue、Buffer/Texture、Shader/Bind Group、Pipeline、Compute/Render Pipeline
- [[72.2-WGSL]] — Vertex/Fragment/Compute Shader、Uniform、Storage Buffer
- [[72.3-WebGPU 应用]] — AI Inference、Image Processing、3D、Physics、Data Visualization、Scientific Computing

### 73-前端数据层架构

- [[73.1-数据来源]] — REST/GraphQL/WebSocket/SSE、IndexedDB/Local Storage
- [[73.2-数据状态]] — UI State/Server State/Cache/Persistent State/Derived State
- [[73.3-数据同步]] — Polling/Revalidation/Optimistic Update/Conflict Resolution/Offline First/Event Driven

### 74-离线优先

- [[74.1-Offline First]] — Offline Cache/Local Database/Sync Queue/Conflict Resolution
- [[74.2-数据同步]] — Delta/Incremental Sync、Retry/Idempotency、Version/Timestamp
- [[74.3-CRDT]] — CRDT/LWW/G-Counter/PN-Counter/OR-Set/Vector Clock、Conflict Free Replication

### 75-前端实时系统

- [[75.1-实时通信]] — WebSocket/SSE/WebRTC/Long Polling
- [[75.2-实时状态]] — Presence/Online Status/Cursor、Notification/Chat/Collaboration
- [[75.3-实时协作]] — OT/CRDT、Conflict Resolution、Awareness、Sync Protocol

### 76-前端架构模式

- [[76.1-架构]] — MPA/SPA/SSR/SSG/ISR、Islands Architecture、Micro Frontend、BFF、Edge Rendering
- [[76.2-代码架构]] — MVC/MVVM/MVP、Clean/Hexagonal/Layered Architecture、Feature Sliced Design
- [[76.3-设计模式]] — Factory/Singleton/Adapter/Decorator/Proxy/Observer/Strategy/Command/State/Facade/Composite/Builder

### 77-前端领域驱动设计

- [[77.1-DDD]] — Domain/Entity/Value Object/Aggregate/Repository/Domain Service/Application Service
- [[77.2-前端领域拆分]] — Feature/Domain/Shared/UI/API/State
- [[77.3-Feature-Sliced Design]] — App/Pages/Widgets/Features/Entities/Shared

### 78-前端 API 架构

- [[78.1-REST API]] — Resource/Version/Pagination/Cursor Pagination/Error/Idempotency
- [[78.2-GraphQL]] — Schema/Resolver/Query/Mutation/Subscription/DataLoader
- [[78.3-RPC]] — gRPC/Connect/Protobuf/Serialization
- [[78.4-API Contract]] — OpenAPI/JSON Schema/Type Generation/Contract Testing

### 79-前端工程性能

- [[79.1-Build Performance]] — Dependency Cache/Incremental Build/Parallel Build/Persistent Cache/Remote Cache
- [[79.2-CI Performance]] — Dependency/Docker/Build Cache、Test Parallelization、Artifact Cache
- [[79.3-Bundle Analysis]] — Bundle Analyzer/Source Map Explorer/Bundle Size/Dependency Graph

### 80-CI-CD

- [[80.1-CI]] — GitHub Actions/GitLab CI/Jenkins、Build/Lint/Test/Security Scan
- [[80.2-CD]] — Deployment/Artifact、Docker/Kubernetes、CDN/Static Hosting
- [[80.3-Deployment Strategy]] — Rolling/Blue Green/Canary/Shadow、Feature Flag/Rollback

### 81-Docker

- [[81.1-Docker]] — Image/Container/Layer、Dockerfile/Registry、Volume/Network
- [[81.2-前端 Docker]] — Node Build、Multi-stage Build、Nginx、Static Asset、Runtime Configuration

### 82-Kubernetes

- [[82.1-基础]] — Pod/Deployment/Service/Ingress、ConfigMap/Secret/Namespace
- [[82.2-前端部署]] — Static Server/Nginx/CDN/Ingress、TLS/Autoscaling

### 83-Nginx

- [[83.1-静态服务]] — root/location/index/try_files
- [[83.2-反向代理]] — proxy_pass/proxy_set_header/upstream/load balancing
- [[83.3-缓存]] — Cache-Control/expires/proxy_cache、gzip/brotli
- [[83.4-SPA]] — history fallback/try_files/404

### 84-前端架构设计

- [[84.1-大型应用]] — Modularization/Componentization、Domain/Feature/Shared、Dependency Management
- [[84.2-高并发]] — CDN/Cache/Static Rendering/SSR、Edge/API Gateway/Rate Limit
- [[84.3-高可用]] — Failover/Retry/Timeout、Circuit Breaker/Graceful Degradation/Fallback
- [[84.4-可扩展]] — Plugin/Micro Frontend/Module Federation、Monorepo/Design System

### 85-大型前端应用工程治理

- [[85.1-代码治理]] — Coding Standard/Lint/Type Check、Review/Architecture Review
- [[85.2-依赖治理]] — Dependency Graph/Version Policy、Security/License Audit、Bundle Budget
- [[85.3-组件治理]] — Design System/Component Registry、API Standard/Deprecation/Migration
- [[85.4-技术债务]] — Refactoring/Legacy/Migration、Deprecation/Compatibility

### 86-前端国际大厂工程实践

- [[86.1-Engineering Excellence]] — Code/Design Review、RFC/ADR、Technical Proposal
- [[86.2-Development Process]] — Scrum/Kanban、Trunk Based Development、Continuous Delivery
- [[86.3-Quality]] — Test Pyramid、SLO/Error Budget、Performance Budget、Security Review

### 87-前端架构文档体系

- [[87.1-文档]] — README/Architecture/ADR/RFC、API/Component Spec、Runbook
- [[87.2-架构图]] — Context/Container/Component/Sequence/Deployment Diagram
- [[87.3-文档工具]] — Markdown/Mermaid、Docusaurus/VitePress/Storybook

### 88-前端算法与数据结构

- [[88.1-数据结构]] — Array/Linked List/Stack/Queue/Deque/Hash Table/Heap/Tree/Trie/Graph
- [[88.2-算法]] — Binary Search/Two Pointer/Sliding Window/Prefix Sum/Difference Array/Greedy/DP/Backtracking/Divide and Conquer
- [[88.3-前端常用算法]] — Virtual List/Diff/Reconciliation、LRU Cache/Debounce/Throttle、Event Delegation/Scheduler/Dependency Graph/Topological Sort

### 89-前端框架原理

- [[89.1-Virtual DOM]] — VNode/Diff/Patch/Reconciliation/Key
- [[89.2-Compiler]] — Parser/AST/Transform/Codegen/Runtime
- [[89.3-Reactive System]] — Dependency Tracking/Effect/Trigger/Scheduler/Batch Update
- [[89.4-Scheduler]] — Priority/Task Queue/Microtask/Macrotask/Yield/Time Slice

### 90-React-Vue 源码学习

- [[90.1-React 源码]] — JSX Transform/Fiber/Reconciler/Scheduler、Hooks/Context/Suspense/Server Components
- [[90.2-Vue 源码]] — Reactivity/Runtime Core/DOM、Compiler Core/DOM、Renderer/Scheduler/VNode/Diff

### 91-前端编译原理

- [[91.1-Lexer]] — Token/Tokenization
- [[91.2-Parser]] — AST/Recursive Descent/Pratt Parser
- [[91.3-Transform]] — AST Transform/Optimization
- [[91.4-Code Generation]] — Codegen/Source Map
- [[91.5-前端应用]] — Babel/TypeScript/SWC/esbuild、Vue/JSX Compiler、CSS Parser

### 92-浏览器 DevTools 实战

- [[92.1-Elements]] — DOM/CSS/Layout/Accessibility
- [[92.2-Console]] — JavaScript/Error/Warning/Network
- [[92.3-Network]] — Request/Response/Headers、Timing/Waterfall/Blocking/Initiator
- [[92.4-Performance]] — Flame Chart/Main Thread/Long Task、Layout/Paint/Composite/FPS
- [[92.5-Memory]] — Heap Snapshot/Allocation Timeline、Detached DOM/Retainers
- [[92.6-Application]] — Storage/Cookies/IndexedDB、Cache/Service Worker

### 93-前端性能诊断方法论

- [[93.1-前端性能诊断方法论]] — 发现问题/建立基线/定位瓶颈、假设/实验验证/优化/回归/监控/持续治理

### 94-前端内存管理

- [[94.1-GC]] — Reachability/Mark/Sweep/Compact/Generational GC
- [[94.2-内存泄漏]] — Global Variable/Event Listener/Timer/Closure/Detached DOM/Cache/Subscription
- [[94.3-内存诊断]] — Heap Snapshot/Allocation Timeline、Retainer/Dominator Tree

### 95-前端兼容性

- [[95.1-Browser Compatibility]] — Chrome/Firefox/Safari/Edge、iOS Safari/Android Browser
- [[95.2-Compatibility]] — Feature Detection/Polyfill/Transpile、Browserslist/Autoprefixer
- [[95.3-Polyfill]] — core-js/regenerator、Promise/Fetch、IntersectionObserver/ResizeObserver

### 96-浏览器 API 高级

- [[96.1-Observer]] — Mutation/Resize/Intersection/PerformanceObserver
- [[96.2-Scheduling]] — requestAnimationFrame/requestIdleCallback/scheduler API
- [[96.3-Performance]] — Performance API/Mark/Measure、Navigation/Resource/Paint Timing、Long Tasks

### 97-文件与大文件处理

- [[97.1-文件上传]] — File/Blob/FormData/Multipart
- [[97.2-大文件]] — Chunk/Resume/Parallel Upload、Hash/MD5/SHA、Multipart Upload
- [[97.3-下载]] — Blob/Stream Download、Range Request/Resume Download

### 98-前端加密与安全编程

- [[98.1-Web Crypto API]] — crypto.subtle/Digest/GenerateKey/ImportKey/ExportKey/Encrypt/Decrypt/Sign/Verify
- [[98.2-算法]] — SHA-256/384/512、AES-GCM/RSA-OAEP/ECDSA/ECDH
- [[98.3-安全原则]] — 不在前端保存 Secret/HTTPS/Least Privilege/Input Validation/Output Encoding/CSP/Secure Cookie

### 99-前端项目实战

- [[99.1-企业后台管理系统]] — React/Vue + TS + Router + 状态管理、RBAC 权限、Form/Table/Dashboard/ECharts、测试与 CI/CD
- [[99.2-电商前端]] — 商品/搜索/推荐/购物车/订单/支付/优惠券/用户中心、SSR/SEO/性能优化
- [[99.3-实时聊天系统]] — WebSocket/Presence/Message、离线消息/通知/文件上传/表情/已读回执/重连
- [[99.4-在线协作编辑器]] — Canvas/WebSocket、CRDT/OT/Cursor/Presence/冲突解决/离线同步
- [[99.5-低代码平台]] — Schema/组件注册/拖拽/Renderer、表单/页面构建器、Plugin/DSL/代码生成
- [[99.6-企业级组件库]] — Design Token/React/Vue/TS、Storybook/可访问性/视觉回归/单测/npm 发布
- [[99.7-微前端平台]] — Host/Remote/Module Federation、路由/共享依赖/CSS 隔离/认证/监控
- [[99.8-SSR 全栈应用]] — Next.js/Nuxt、SSR/SSG/ISR/RSC、API/数据库/缓存/CDN/SEO
- [[99.9-AI Chat 应用]] — LLM API/Streaming/Markdown/代码高亮、Tool Calling/文件上传/RAG/引用/对话/记忆
- [[99.10-浏览器端 AI 应用]] — WebGPU/WASM/ONNX Runtime Web、Transformers.js/本地推理/模型缓存/Worker/流式 UI

### 100-前端系统设计实战

- [[100.1-设计大型 SPA]] — Module/Routing/State/API/Cache/Error/Monitoring/Deployment
- [[100.2-设计企业级 Design System]] — Token/Component/Documentation/Versioning/Accessibility/Testing/Publishing
- [[100.3-设计微前端平台]] — Host/Remote/Shared/Routing/Auth/Communication/Isolation/Deployment
- [[100.4-设计高性能首页]] — SSR/CDN/Cache/Critical CSS/Image Optimization/Code Splitting/Preload/Streaming
- [[100.5-设计实时协作系统]] — WebSocket/CRDT/Presence/Sync/Conflict Resolution/Offline
- [[100.6-设计前端监控平台]] — Error/Performance/RUM/Metrics/Trace/Source Map/Alert

### 101-前端源码阅读路线

- [[101.1-前端源码阅读路线]] — V8/Node.js、Chromium/Blink/WebKit、React/Vue/Angular、Webpack/Vite/Rollup/esbuild/SWC/Babel、UI 库、监控工具

### 102-前端论文与研究方向

- [[102.1-浏览器]] — Rendering/JavaScript Engine/JIT/Garbage Collection/Scheduling
- [[102.2-编程语言]] — Type Systems/Compilers/Static Analysis/Program Optimization
- [[102.3-UI]] — Human Computer Interaction/Accessibility/UI Generation/Design Systems
- [[102.4-AI + Frontend]] — Code Generation/UI Generation/Multimodal UI/Agentic UI/Natural Language Interface

### 103-前端职业方向

- [[103.1-前端开发工程师]] — HTML/CSS/JS/TS、React/Vue、工程化
- [[103.2-高级前端工程师]] — Architecture/Performance/Security/Testing/Monitoring
- [[103.3-前端架构师]] — Architecture/Micro Frontend/Design System/Platform/Engineering Governance
- [[103.4-全栈工程师]] — Frontend/Node.js/Database/API/Cloud
- [[103.5-AI Frontend Engineer]] — AI UI/LLM/RAG/Agent/WebGPU/WASM

## 算法工程师知识库

> 基于「算法工程师学习知识库总目录」搭建目录骨架（20 篇章、142 个主题），全部 20 篇章、142 个主题已完成。入口见 `algorithm-engineer/README.md`。

- [[algorithm-engineer/README]] — 算法工程师知识库：目录树（20 篇章）+ 进度追踪表，覆盖 Python/数学/机器学习/深度学习/推荐搜索/图/时间序列/CV/LLM/MLOps/工程化全链路

### 01-学习路线与开发环境

- [[01.1-学习路线与开发环境]] — 能力模型、学习阶段与先修、Linux/Git、语言、IDE、构建工具、Docker、大数据本地环境

### 02-计算机基础

- [[02.1-计算机组成]] — CPU/GPU/内存/Cache/磁盘/IO/中断/DMA
- [[02.2-操作系统]] — 进程/线程/虚拟内存/文件系统/系统调用/cgroups/namespace
- [[02.3-Linux]] — 进程/权限/网络/日志/systemd/cron/ulimit
- [[02.4-计算机网络]] — TCP/IP/HTTP/HTTPS/DNS/TLS/RPC/负载均衡/CDN
- [[02.5-编程]] — Java/Python/Scala/并发/IO/序列化/测试/调试

### 03-数学基础

- [[03.1-离散数学]] — 集合/逻辑/关系/函数/组合/递推/图论/证明
- [[03.2-概率论]] — 随机变量/分布/条件概率/贝叶斯/期望方差/大数定律/中心极限定理
- [[03.3-统计学]] — 抽样/估计/MLE/MAP/假设检验/置信区间/t检验/卡方/ANOVA/Bootstrap
- [[03.4-线性代数]] — 向量/矩阵/秩/特征值/正交/QR/SVD/PCA
- [[03.5-微积分与优化]] — 导数/梯度/Hessian/凸优化/拉格朗日/GD/SGD/牛顿法
- [[03.6-信息论]] — 熵/交叉熵/KL散度/互信息/信息增益

### 04-数据结构与算法

- [[04.1-复杂度]] — Big-O/Ω/Θ/摊销分析
- [[04.2-线性结构]] — 数组/链表/栈/队列/Deque/Priority Queue
- [[04.3-哈希]] — Hash Table/Bloom Filter/Cuckoo Hash/HyperLogLog
- [[04.4-树]] — BST/AVL/红黑树/B/B+Tree/Trie/Radix/Heap/Segment Tree/Fenwick/LSM Tree
- [[04.5-图]] — BFS/DFS/拓扑排序/并查集/最短路/MST/SCC/PageRank
- [[04.6-排序查找]] — 二分/归并/快排/堆排/计数/基数/外排/Top-K
- [[04.7-思想]] — 贪心/分治/动态规划/回溯/随机化/近似算法
- [[04.8-字符串]] — KMP/Z/Rabin-Karp/AC自动机/后缀数组/编辑距离
- [[04.9-算法工程]] — Benchmark/Profiling/并行/测试/边界与数据规模

### 05-Python 编程语言与算法工程基础

- [[05.1-Python 语言核心]] — 解释器/字节码/CPython、对象与引用、可变不可变、容器/迭代器/生成器/装饰器/上下文管理器
- [[05.2-Python 面向对象]] — class/继承/组合/多态/抽象基类/dataclass/property/描述符/magic methods
- [[05.3-Python 类型系统]] — type hints/Generic/TypeVar/Protocol/TypedDict/Literal/Optional/Union/mypy
- [[05.4-Python 工程化]] — venv/Poetry/uv/pip/pyproject.toml、logging/argparse/pathlib/配置管理
- [[05.5-测试与质量]] — pytest/fixture/mock/coverage/hypothesis/ruff/black/pre-commit
- [[05.6-并发与异步]] — threading/multiprocessing/asyncio/GIL/CPU-bound vs IO-bound
- [[05.7-Python 性能]] — cProfile/line_profiler/向量化/NumPy/Numba/Cython
- [[05.8-Python 数据处理]] — NumPy/Pandas/Polars/PyArrow/DuckDB/SciPy
- [[05.9-Python 数据科学]] — ndarray/broadcasting/ufunc/线性代数/Pandas groupby/merge/pivot/时序
- [[05.10-Python 数据工程]] — SQLAlchemy/redis-py/kafka/FastAPI/Pydantic
- [[05.11-Notebook 与实验]] — Jupyter/IPython/实验可复现/random seed/数据版本化

### 06-算法数学完整体系

- [[06.1-线性代数]] — 向量空间/范数/内积/特征值/SVD/QR/矩阵微积分/Jacobian/Hessian
- [[06.2-概率论]] — 分布/联合与条件分布/条件独立/Bayes/大数定律/中心极限定理
- [[06.3-数理统计]] — 抽样/估计/MLE/MAP/置信区间/假设检验/t检验/卡方/ANOVA/Bootstrap
- [[06.4-信息论]] — 熵/交叉熵/KL散度/JS散度/互信息/信息增益/困惑度
- [[06.5-微积分]] — 导数/偏导/梯度/Jacobian/Hessian/链式法则/泰勒展开
- [[06.6-优化]] — 凸优化/Lagrange/KKT/对偶/GD/SGD/Momentum/Adam/Newton/L-BFGS/学习率调度

### 07-传统机器学习完整体系

- [[07.1-学习范式]] — 监督/无监督/半监督/自监督/迁移/在线/持续/主动/联邦/强化学习
- [[07.2-学习理论]] — 偏差方差/过拟合欠拟合/正则化/泛化/VC维/PAC/样本复杂度
- [[07.3-线性模型]] — 线性回归/多项式/Ridge/Lasso/ElasticNet/逻辑回归/GLM/泊松回归
- [[07.4-概率模型]] — 朴素贝叶斯/贝叶斯模型/GMM/EM/HMM/CRF/贝叶斯网络
- [[07.5-树模型]] — ID3/C4.5/CART/随机森林/ExtraTrees/AdaBoost/GBDT/XGBoost/LightGBM/CatBoost
- [[07.6-SVM 与核方法]] — 硬/软间隔/Hinge Loss/核技巧/RBF/多项式核/SVR/One-Class SVM
- [[07.7-邻近与度量学习]] — KNN/马氏距离/度量学习/对比损失/三元组损失/孪生网络
- [[07.8-聚类]] — K-Means/K-Means++/K-Medoids/DBSCAN/HDBSCAN/OPTICS/层次聚类/GMM
- [[07.9-降维]] — PCA/SVD/LDA/ICA/NMF/Kernel PCA/t-SNE/UMAP/Isomap/LLE/MDS
- [[07.10-异常检测]] — Z-Score/IQR/马氏距离/Isolation Forest/LOF/One-Class SVM/自编码器/变点

### 08-特征工程与模型评估

- [[08.1-数据清洗]] — 缺失值/异常值/重复值/数据校验/泄漏检测
- [[08.2-数值特征]] — 标准化/Min-Max/Robust/分位数变换/Log/Box-Cox/Yeo-Johnson
- [[08.3-类别特征]] — One-Hot/Ordinal/Frequency/Count/Target/CatBoost/Hashing
- [[08.4-特征选择]] — 方差阈值/相关性/卡方/ANOVA/互信息/RFE/L1/树重要性/SHAP
- [[08.5-时间特征]] — Lag/Rolling/Expanding/EWMA/Trend/Seasonality/Fourier
- [[08.6-模型评估]] — 准确率/精确率/召回/F1/ROC-AUC/PR-AUC/LogLoss/Brier/校准/MAE/MSE/RMSE/R²
- [[08.7-数据划分]] — Train/Valid/Test/K-Fold/Stratified/Group/TimeSeries Split/Nested CV/OOF
- [[08.8-超参数优化]] — Grid/Random/Bayesian/TPE/Hyperband/ASHA

### 09-推荐系统算法

- [[09.1-推荐系统架构]] — 数据采集/画像/召回/排序/重排/在线服务/反馈回路
- [[09.2-经典召回]] — Popularity/UserCF/ItemCF/内容召回/共现/关联规则/图召回
- [[09.3-矩阵分解]] — MF/SVD/SVD++/ALS/BPR/隐式反馈
- [[09.4-深度推荐]] — Wide&Deep/DeepFM/xDeepFM/DCN/DIN/DIEN/MMOE/PLE/Two-Tower/DSSM
- [[09.5-ANN]] — LSH/KD-Tree/HNSW/IVF/PQ/OPQ/ScaNN/FAISS/DiskANN
- [[09.6-重排]] — 多样性/新颖性/新鲜度/业务规则/公平性/约束优化
- [[09.7-推荐评估]] — CTR/CVR/Recall@K/NDCG@K/MAP@K/MRR/Coverage/多样性/A/B Test
- [[09.8-冷启动]] — 用户/物品/场景冷启动、探索利用、Bandit

### 10-搜索与信息检索算法

- [[10.1-倒排索引]] — Token/Dictionary/Posting List/Skip List/Segment/压缩/FST
- [[10.2-相关性]] — Boolean/TF-IDF/BM25/Query Likelihood/语言模型
- [[10.3-Query Understanding]] — 改写/同义词/拼写纠错/意图/实体识别/扩展
- [[10.4-Learning to Rank]] — Pointwise/Pairwise/Listwise/RankNet/LambdaRank/LambdaMART
- [[10.5-Hybrid Search]] — BM25+向量/加权融合/RRF/Reranker/Cross Encoder/ColBERT

### 11-图算法与图学习

- [[11.1-图基础]] — 顶点/边/有向无向/加权/属性图/知识图谱
- [[11.2-图算法]] — BFS/DFS/最短路/MST/PageRank/连通分量/SCC/三角计数/社区发现/中心性
- [[11.3-图表示学习]] — DeepWalk/Node2Vec/GCN/GraphSAGE/GAT/GNN/知识图谱嵌入

### 12-时间序列算法

- [[12.1-统计方法]] — Trend/Seasonality/平稳性/ACF/PACF/AR/MA/ARMA/ARIMA/SARIMA/VAR/ETS
- [[12.2-机器学习]] — Lag/Rolling 特征、XGBoost/LightGBM
- [[12.3-深度学习]] — RNN/LSTM/GRU/TCN/Transformer/TFT
- [[12.4-异常与变点]] — 残差检测/动态阈值/变点/预测式检测

### 13-计算机视觉与 OpenCV 全栈

- [[13.1-计算机视觉基础]] — 图像/像素/分辨率/通道/颜色空间/位深/动态范围
- [[13.2-OpenCV 基础]] — imread/imwrite/VideoCapture/颜色转换/Resize/Crop/Rotate/Warp
- [[13.3-图像处理]] — 阈值/Otsu/模糊/双边滤波/锐化/形态学（腐蚀膨胀开闭）
- [[13.4-边缘与轮廓]] — Sobel/Scharr/Laplacian/Canny/轮廓/包围盒/凸包
- [[13.5-几何视觉]] — 仿射/透视/单应性/相机标定/立体视觉/对极几何/PnP/位姿
- [[13.6-特征点]] — Harris/FAST/ORB/SIFT/SURF/BRIEF/BRISK/AKAZE/特征匹配/BFMatcher/FLANN
- [[13.7-目标检测传统方法]] — Haar Cascade/HOG/滑动窗口/Selective Search/DPM
- [[13.8-深度视觉]] — 图像分类/目标检测/语义分割/实例分割/全景分割/关键点/OCR/人脸/跟踪
- [[13.9-现代视觉模型]] — ResNet/EfficientNet/YOLO/SSD/Faster R-CNN/Mask R-CNN/DETR/ViT/Swin/SAM/CLIP
- [[13.10-视频分析]] — 光流/背景减除/目标跟踪/MOT/Kalman/SORT/DeepSORT/ByteTrack
- [[13.11-OCR]] — 文本检测/识别/PaddleOCR/CTC/CRNN/Transformer OCR/版面分析/Document AI
- [[13.12-OpenCV 工程]] — 摄像头/RTSP/视频流/多线程/GPU-CUDA/性能优化/批处理/服务化/FastAPI

### 14-深度学习与 PyTorch

- [[14.1-神经网络]] — Perceptron/MLP/激活/损失/反向传播/初始化
- [[14.2-激活函数]] — Sigmoid/Tanh/ReLU/LeakyReLU/GELU/SiLU-Swish/Softmax
- [[14.3-正则化]] — Dropout/BatchNorm/LayerNorm/GroupNorm/Weight Decay/Early Stopping
- [[14.4-优化]] — SGD/Momentum/Adam/AdamW/Warmup/Cosine Decay/梯度裁剪/混合精度
- [[14.5-CNN]] — 卷积/Padding/Stride/Dilation/池化/残差/ResNet/DenseNet/EfficientNet/ConvNeXt
- [[14.6-序列]] — RNN/LSTM/GRU/Seq2Seq/Teacher Forcing/Attention
- [[14.7-Transformer]] — Self-Attention/MHA/QKV/位置编码/RoPE/ALiBi/Encoder/Decoder/Causal Mask/KV Cache
- [[14.8-PyTorch]] — Tensor/DataLoader/nn.Module/Autograd/Optimizer/Scheduler/AMP/DDP/FSDP/TensorBoard
- [[14.9-训练工程]] — 数据版本化/可复现/实验追踪/Early Stopping/Checkpoint/GPU利用率/显存优化

### 15-生成模型、LLM、RAG 与 Agent

- [[15.1-生成模型]] — Autoencoder/VAE/GAN/WGAN/Normalizing Flow/Diffusion/DDPM/Latent Diffusion
- [[15.2-Tokenization]] — BPE/WordPiece/SentencePiece/Unigram/Token Budget
- [[15.3-LLM]] — Decoder-Only/Causal LM/Pretraining/Scaling Laws/MoE/RMSNorm/SwiGLU/RoPE/KV Cache
- [[15.4-微调]] — Full Fine-Tuning/SFT/LoRA/QLoRA/Adapter/Prefix/Prompt Tuning
- [[15.5-对齐]] — RLHF/PPO/DPO/IPO/ORPO
- [[15.6-推理]] — Greedy/Temperature/Top-K/Top-P/Beam Search/量化/GPTQ/AWQ/投机解码/Continuous Batching
- [[15.7-RAG]] — 文档加载/Chunking/Embedding/稀疏与稠密检索/Hybrid/Reranking/Query Rewrite/HyDE/引用/RAG评估
- [[15.8-Agent]] — ReAct/Plan-and-Execute/Reflection/Tool Calling/Planning/Memory/Routing/Multi-Agent/评估
- [[15.9-MCP]] — Client/Server/Tool/Resource/Prompt/Transport/认证/授权/安全
- [[15.10-多模态]] — VLM/CLIP/Image-Text Embedding/OCR+LLM/Document AI/图像生成/音视频

### 16-算法工程化与服务部署

- [[16.1-服务框架]] — FastAPI/Flask/gRPC/REST/WebSocket/Pydantic
- [[16.2-模型服务]] — 批量/在线/流式推理、Model Server/Registry/版本化/Canary/Shadow/Blue-Green
- [[16.3-推理优化]] — ONNX/TensorRT/TensorRT-LLM/OpenVINO/torch.compile/CUDA/量化/剪枝/蒸馏
- [[16.4-容器与部署]] — Docker/Kubernetes/Helm/GPU调度/服务发现/ConfigMap/Secret/Ingress
- [[16.5-MLOps]] — 数据/特征/训练/评估流水线、Model Registry/MLflow/Kubeflow/KServe/BentoML/Ray/Feast
- [[16.6-监控]] — 延迟/吞吐/错误率/GPU利用率/数据漂移/概念漂移/Prometheus/Grafana/OpenTelemetry
- [[16.7-实验与可复现]] — Git/DVC/数据版本/实验追踪/配置/Seed/Artifact/Model Card

### 17-高级算法与竞赛级能力

- [[17.1-基础技巧]] — 双指针/滑动窗口/前缀和/差分/二分答案/单调栈/单调队列/贪心/分治/回溯
- [[17.2-高级数据结构]] — Union Find/树状数组/线段树/Sparse Table/Trie/可持久化/Treap/跳表
- [[17.3-图论]] — Dijkstra/Bellman-Ford/Floyd/0-1 BFS/MST/SCC/Tarjan/桥/割点/二分图/最大流/最小割
- [[17.4-动态规划]] — 背包/区间/树形/状压/数位/概率 DP/DAG DP/单调队列优化/凸包优化/分治优化
- [[17.5-字符串]] — KMP/Z/AC 自动机/Manacher/Rolling Hash/后缀数组/后缀自动机
- [[17.6-数学算法]] — GCD/扩展欧几里得/筛法/快速幂/模运算/矩阵快速幂/组合/容斥/CRT/FFT/NTT

### 18-算法工程师综合项目

- [[18.1-Python 数据分析与机器学习平台]] — NumPy/Pandas/Scikit-learn 全流程 ML 平台
- [[18.2-端到端推荐系统]] — Spark/Flink + Feature Store + 召回排序 + 在线服务 + A/B
- [[18.3-搜索与语义检索系统]] — 倒排/BM25/Embedding/ANN/Hybrid/Reranker/LTR
- [[18.4-OpenCV 智能视觉分析平台]] — RTSP/OpenCV/检测/跟踪/OCR/服务化/GPU
- [[18.5-时间序列预测与异常检测平台]] — ARIMA/LightGBM/LSTM/异常/变点/告警
- [[18.6-RAG 知识库]] — 解析/Chunk/Embedding/向量库/BM25/Hybrid/Rerank/LLM/评估
- [[18.7-Agent 数据分析系统]] — SQL/Python/Search Tool + ReAct + Planning + Memory + MCP
- [[18.8-算法模型服务平台]] — FastAPI/gRPC + ONNX/TensorRT + K8s/KServe + 监控
- [[18.9-企业级算法平台]] — 数据/特征/训练/评估/Registry/Serving/Monitoring/A-B

### 19-算法论文与研究能力

- [[19.1-论文阅读]] — Abstract/Problem/Related Work/Method/Experiment/Ablation/Limitation
- [[19.2-经典机器学习]] — SVM/随机森林/AdaBoost/GBDT/XGBoost/LightGBM/PCA/EM/HMM 论文
- [[19.3-深度学习]] — AlexNet/VGG/ResNet/BatchNorm/Adam/Attention/Transformer/ViT 论文
- [[19.4-推荐]] — Matrix Factorization/Wide&Deep/DeepFM/DIN/Two-Tower 论文
- [[19.5-LLM]] — Transformer/BERT/GPT/Scaling Laws/LoRA/RLHF/DPO/RAG 论文

### 20-算法工程师面试与系统设计

- [[20.1-Python]] — 数据类型/装饰器/生成器/迭代器/GIL/asyncio/多进程/性能优化/内存管理
- [[20.2-算法]] — 复杂度/数据结构/图/DP/贪心/字符串/数学算法
- [[20.3-机器学习]] — LR/SVM/Tree/GBDT/XGBoost/LightGBM/K-Means/PCA/GMM
- [[20.4-深度学习]] — BP/CNN/RNN/LSTM/Attention/Transformer/Normalization/Optimizer
- [[20.5-视觉]] — OpenCV/图像处理/特征点/目标检测/OCR/Tracking/相机标定
- [[20.6-推荐与搜索]] — Recall/Ranking/ANN/BM25/LTR/Rerank
- [[20.7-LLM]] — Tokenizer/Transformer/SFT/LoRA/DPO/RAG/Agent/MCP
- [[20.8-系统设计]] — 推荐/搜索/实时风控/CV 服务/RAG 平台/Model Serving/Feature Store/ML Platform

## 大数据知识库

> 基于《大数据学习知识库总目录》编排，覆盖计算机基础、SQL、Hadoop/Hive/Kafka/Spark/Flink、数仓、Lakehouse、CDC、实时数仓、大数据算法、数据治理、云原生与企业级数据平台，共 133 篇。

### 学习路线与开发环境
- [[01.1-学习路线与开发环境]] — 大数据与算法全栈能力模型、学习阶段与先修关系、Linux Shell 与 Git、Java Python 与 Scala、IDE 与 Jupyter Notebook 等

### 计算机基础
- [[02.1-计算机组成]] — CPU、GPU、内存、Cache、磁盘 等
- [[02.2-操作系统]] — 进程、线程、虚拟内存、文件系统、系统调用 等
- [[02.3-Linux]] — 进程管理、权限、网络、日志、systemd 等
- [[02.4-计算机网络]] — TCP、IP、HTTP、HTTPS、DNS 等
- [[02.5-编程基础]] — Java、Python、Scala、并发、IO 等

### 数学基础
- [[03.1-离散数学]] — 集合、逻辑、关系、函数、组合 等
- [[03.2-概率论]] — 随机变量、常见分布、条件概率、贝叶斯、期望 等
- [[03.3-统计学]] — 抽样、估计、MLE、MAP、假设检验 等
- [[03.4-线性代数]] — 向量、矩阵、秩、特征值、正交 等
- [[03.5-微积分与优化]] — 导数与偏导、梯度与 Hessian、链式法则与反向传播、凸优化与凸函数、拉格朗日乘子与约束优化 等
- [[03.6-信息论]] — 熵、交叉熵、KL 散度、互信息、信息增益

### 数据结构与算法
- [[04.1-复杂度分析]] — Big-O、Ω、Θ、摊销分析
- [[04.2-线性结构]] — 数组、链表、栈、队列、Deque 等
- [[04.3-哈希]] — Hash Table、Bloom Filter、Cuckoo Hash、HyperLogLog
- [[04.4-树]] — BST、AVL、红黑树、B 树、B+Tree 等
- [[04.5-图]] — BFS、DFS、拓扑排序、并查集、最短路 等
- [[04.6-排序查找]] — 二分查找、归并排序、快排、堆排、计数排序 等
- [[04.7-算法思想]] — 贪心、分治、动态规划、回溯、随机化 等
- [[04.8-字符串算法]] — KMP、Z、Rabin-Karp、AC 自动机、后缀数组 等
- [[04.9-算法工程]] — Benchmark、Profiling、并行、测试、边界与数据规模

### 数据库与SQL
- [[05.1-关系模型与范式]] — 关系模型、范式、反范式、主外键、约束
- [[05.2-SQL]] — SELECT 与投影、WHERE 与过滤、GROUP BY 与聚合、JOIN 与多表关联、UNION 与集合运算 等
- [[05.3-高级SQL]] — Recursive CTE 递归查询、Rollup 上卷、Cube 多维聚合、Grouping Sets 分组集合、Pivot 行列转换 等
- [[05.4-MySQL 与 PostgreSQL]] — InnoDB、MVCC、WAL、Redo、Undo 等
- [[05.5-OLAP 引擎]] — ClickHouse、StarRocks、Doris、Druid、Pinot 等
- [[05.6-NoSQL]] — Redis、MongoDB、Cassandra、HBase、DynamoDB 等
- [[05.7-数据库原理]] — CAP、PACELC、分片、复制、读写分离 等

### 数据存储与文件格式
- [[06.1-文件格式]] — CSV、JSON、XML、Avro、Protobuf 等
- [[06.2-存储系统与列式原理]] — 行存与列存、字典编码、RLE、Bit Packing、压缩 等

### Hadoop生态
- [[07.1-Hadoop 概述与架构]] — Hadoop 架构、Common、HDFS、YARN、MapReduce
- [[07.2-HDFS]] — NameNode 与 DataNode、Block 与副本机制、Rack Awareness 机架感知、HA 高可用、Federation 联邦 等
- [[07.3-MapReduce]] — Mapper、Reducer、Combiner、Partitioner、Shuffle 等
- [[07.4-YARN]] — ResourceManager、NodeManager、ApplicationMaster、Container、Scheduler 等
- [[07.5-Hadoop 生态]] — Hive、HBase、Sqoop、Oozie、ZooKeeper 等

### Hive与大数据SQL
- [[08.1-Hive 架构与表管理]] — Hive Architecture、Metastore、Beeline、Managed/External Table、Partition 等
- [[08.2-Hive SQL 与查询优化]] — Hive SQL、UDF/UDAF/UDTF、窗口函数、Tez、向量化 等

### Kafka与消息流
- [[09.1-Kafka 架构与存储]] — 知识点章节
- [[09.2-Kafka Producer]] — 知识点章节
- [[09.3-Kafka Consumer]] — 知识点章节
- [[09.4-Kafka 生态与数据集成]] — 知识点章节

### Spark
- [[10.1-Spark 架构]] — Driver、Executor、Cluster Manager、Application、Job 等
- [[10.2-RDD]] — Partition、Transformation、Action、Lazy、Dependency 等
- [[10.3-Spark SQL]] — DataFrame、Dataset、Catalyst、Tungsten、AQE 等
- [[10.4-Structured Streaming]] — Source、Sink、Trigger、Checkpoint、Watermark 等
- [[10.5-Spark 性能优化]] — Partition 分区、Repartition 重分区、Coalesce 合并分区、Broadcast 广播、SortMerge Join 等
- [[10.6-Spark 源码解析]] — SparkContext、DAG Scheduler、Task Scheduler、BlockManager、MemoryManager 等

### Flink
- [[11.1-Flink 架构]] — JobManager、TaskManager、Slot、Operator、JobGraph 等
- [[11.2-DataStream API]] — Source、Transformation、Sink、KeyBy、ProcessFunction
- [[11.3-时间与水位线]] — Processing Time、Event Time、Ingestion Time、Timestamp、Watermark 等
- [[11.4-窗口]] — Tumbling、Sliding、Session、Global、Trigger 等
- [[11.5-State 状态管理]] — Keyed State、Operator State、ValueState、ListState、MapState 等
- [[11.6-Checkpoint 与容错]] — Checkpoint、Savepoint、Barrier、Unaligned Checkpoint、State Backend 等
- [[11.7-Flink SQL]] — Dynamic Table、Changelog、Catalog、Connector、Temporal Join 等
- [[11.8-CEP 与运行时进阶]] — CEP、Backpressure、Network Buffer、Chaining、Slot Sharing 等

### Trino与联邦查询
- [[12.1-Trino 与联邦查询]] — Trino/Presto 架构、Coordinator/Worker、Connector/Catalog/Schema、Split、Exchange 等

### 数据仓库
- [[13.1-数仓建模与分层]] — OLTP 与 OLAP、数仓分层：ODS-DWD-DWS-ADS、数据集市、星型模型与雪花模型、事实表与维度表 等
- [[13.2-维度建模与缓慢变化维]] — SCD 0/1/2/3、拉链表、快照表、全量/增量、历史回溯
- [[13.3-ETL 与数仓架构]] — ETL/ELT、CDC、Full/Incremental、Upsert/Merge、数据校验 等

### 数据湖与Lakehouse
- [[14.1-数据湖概述]] — Data Lake 数据湖、Object Storage 对象存储、Schema-on-Read 读时模式、Bronze-Silver-Gold 分层、数据湖与数仓、Lakehouse 的关系
- [[14.2-Iceberg]] — Metadata 元数据层、Snapshot 快照、Manifest 与数据文件、Catalog 目录、Schema 与分区演进 等
- [[14.3-Hudi]] — COW 与 MOR 两种表类型、Timeline 时间轴、Instant 与 Action、Upsert 更新机制、Index 索引 等
- [[14.4-Delta Lake]] — Transaction Log 事务日志、ACID 事务保证、Version 版本与 Time Travel、Schema Enforcement 模式强制、Schema Evolution 模式演进 等
- [[14.5-Lakehouse 实践]] — 小文件治理、Compaction 合并、分区策略、数据质量、成本治理

### 数据集成与CDC
- [[15.1-CDC 原理与工具]] — Binlog 二进制日志、WAL 预写日志、Logical Replication 逻辑复制、Debezium、Canal 等
- [[15.2-数据集成工具与同步语义]] — 批量与流式 ETL、全量与增量同步、同步一致性、Kafka Connect、NiFi 等

### 实时计算与实时数仓
- [[16.1-实时数仓架构与分层]] — 流与事件、事件时间、处理时间、窗口、状态 等
- [[16.2-实时指标与实时应用]] — UVPV、DAUMAU、GMV、CTRCVR、留存 等

### 大数据算法
- [[17.1-数据采样]] — Random Sampling 随机采样、Reservoir Sampling 蓄水池采样、Stratified Sampling 分层采样、Weighted Sampling 加权采样、Systematic Sampling 系统采样 等
- [[17.2-基数估计]] — Linear Counting 线性计数、HyperLogLog、HLL++、KMV、Theta Sketch 等
- [[17.3-频率与 Top-K]] — Count-Min Sketch、Count Sketch、Misra-Gries、Frequent Items 频繁项、Heavy Hitters 重磅项 等
- [[17.4-成员判定]] — Bloom Filter 布隆过滤器、Counting Bloom Filter 计数布隆、Cuckoo Filter 布谷鸟过滤器、Quotient Filter 商过滤器、XOR Filter
- [[17.5-分位数与统计摘要]] — t-digest、KLL、Greenwald-Khanna、Quantile Sketch 分位数摘要、Approximate Median 近似中位数 等
- [[17.6-流式算法]] — Sliding Window、Exponential Histogram、Time Decay、Online Aggregation、Approximate Join 等
- [[17.7-外存算法]] — External Sort、External Hashing、External Merge、B-Tree、B+Tree 等
- [[17.8-分布式算法]] — Partitioning、Consistent Hashing、Rendezvous Hashing、MapReduce、Distributed Join 等
- [[17.9-算法工程]] — 时间复杂度、空间复杂度、IO Complexity、Network Complexity、Benchmark 等

### 数据科学与实验
- [[26.1-数据探索与分析]] — EDA、描述统计、相关性分析、分布分析、异常检测 等
- [[26.2-A-B 实验]] — 随机化、样本量、显著性、置信区间、多重检验 等
- [[26.3-因果推断]] — DAG、Confounder、Potential Outcomes、ATE、ATT 等
- [[26.4-数据可视化]] — Matplotlib 基础绘图、Seaborn 统计可视化、Plotly 交互式图表、ECharts 前端图表库、Superset 自助式 BI 等

### 数据质量与治理
- [[27.1-数据质量维度与规则]] — Accuracy 准确性、Completeness 完整性、Consistency 一致性、Timeliness 及时性、Uniqueness 唯一性 等
- [[27.2-元数据与数据目录]] — Metadata 元数据、Catalog 数据目录、Ownership 数据归属、Classification 数据分类分级、Dictionary 数据字典 等
- [[27.3-数据血缘]] — 表级血缘、列级血缘、任务血缘、管道血缘、影响分析
- [[27.4-数据安全与权限]] — Authentication、Authorization、RBAC、ABAC、Encryption 等

### 数据开发工程化
- [[28.1-数据调度与工作流]] — Pipeline、DAG、Task、Dependency、Retry 等
- [[28.2-数据测试与工程规范]] — Unit Test、Integration Test、Data Test、Regression Test、Schema Test 等

### MLOps
- [[29.1-MLOps 流水线与模型服务]] — Data Pipeline、Feature Pipeline、Training Pipeline、Evaluation Pipeline、Deployment Pipeline 等
- [[29.2-MLOps 工具链与监控]] — Latency 延迟、Throughput 吞吐、Error Rate 错误率、Data Drift 数据漂移、Concept Drift 概念漂移 等

### 分布式系统
- [[30.1-分布式理论]] — CAP 定理、PACELC、一致性模型、可用性与分区容错、复制 等
- [[30.2-分布式共识与事务]] — Leader Election 选举、Consensus 共识、Raft、Paxos、ZooKeeper 等

### 大数据性能优化
- [[31.1-性能优化基础]] — CPU、内存、IO、网络、GC 等
- [[31.2-SQL 优化]] — 执行计划、Join 优化、分区裁剪、谓词下推、统计信息 等
- [[31.3-Spark 优化]] — 分区、Shuffle、Join 策略、Cache 缓存、AQE 自适应查询执行 等
- [[31.4-Flink 优化]] — 并行度、Backpressure 反压、State 状态、Checkpoint 检查点、Buffer 缓冲 等
- [[31.5-Kafka 优化]] — Batch 批量、Compression 压缩、Partition 分区、Broker IO、Page Cache
- [[31.6-OLAP 优化]] — Sort Key 排序键、Primary Key 主键、Materialized View 物化视图、Compaction 合并、Pre-Aggregation 预聚合

### 云原生与DevOps
- [[32.1-Docker 与容器]] — Docker 基础、镜像、容器、Volume 数据卷、Network 网络 等
- [[32.2-Kubernetes]] — Pod、Deployment、Service、ConfigMap、Secret 等
- [[32.3-大数据组件上云]] — Spark on K8s、Flink Operator、Kafka on K8s、Airflow on K8s、Trino on K8s 等
- [[32.4-CI-CD 与基础设施即代码]] — GitHub Actions、GitLab CI、Jenkins、Terraform、Helm 等
- [[32.5-可观测性与运维]] — Metrics、Logs、Traces、OpenTelemetry、Prometheus 等

### 数据架构
- [[33.1-数据架构演进]] — Data Warehouse、Data Lake、Lakehouse、Data Mesh、Data Fabric 等
- [[33.2-企业数据平台]] — 数据采集、数据存储、数据处理、数仓、数据服务 等
- [[33.3-实时数仓架构]] — Kafka、Flink、Iceberg、StarRocks、ES 等
- [[33.4-AI 数据架构]] — Data Lake、Feature Store、Vector DB、Embedding、RAG 等

### 数据产品与指标体系
- [[34.1-指标体系]] — 原子指标、派生指标、复合指标、业务口径、指标血缘 等
- [[34.2-用户画像与分群]] — 用户画像、分群、Cohort、Retention、Churn 等
- [[34.3-行业指标体系]] — GMV、订单、转化、复购、Funnel 等

### 源码与论文
- [[35.1-Hadoop 源码]] — HDFS 源码、YARN 源码、MapReduce 源码
- [[35.2-Kafka 源码]] — Producer 源码、Consumer 源码、Broker 源码、Replication 复制源码、KRaft 源码
- [[35.3-Spark 源码]] — Scheduler 调度源码、RDD 源码、Shuffle 源码、Catalyst 优化器源码、Tungsten 源码 等
- [[35.4-Flink 源码]] — Runtime 运行时源码、Network 网络栈源码、State 状态源码、Checkpoint 源码、Watermark 源码
- [[35.5-Hive 与 Trino 源码]] — Hive Parser 解析器、Hive Planner 与 Optimizer、Hive 执行引擎、Trino Parser 解析器、Trino Planner 与 Optimizer 等
- [[35.6-Lakehouse 源码]] — Iceberg Metadata 元数据、Iceberg Snapshot 与 Manifest、Iceberg Commit 提交、Hudi Timeline、Delta Transaction Log
- [[35.7-经典论文]] — MapReduce、BigTable、Dynamo、Pregel、Spanner 等
- [[35.8-推荐与深度学习论文]] — MF 矩阵分解、Wide-Deep、DeepFM、DIN、Transformer 等

### 安全与隐私
- [[36.1-数据安全]] — 数据分类分级、权限、加密、密钥管理、脱敏 等
- [[36.2-隐私计算]] — Differential Privacy、Federated Learning、SMPC、Homomorphic Encryption
- [[36.3-AI 安全]] — Prompt Injection（提示词注入）、Data Poisoning（数据投毒）、Model Extraction（模型窃取）、Jailbreak（越狱攻击）、PII Leakage（隐私数据泄露） 等

### 面试与系统设计
- [[37.1-大数据基础面试]] — 数据结构与算法面试、SQL 与执行计划面试、Hadoop 面试、Hive 面试
- [[37.2-消息与计算引擎面试]] — Kafka 面试、Spark 面试、Flink 面试、Event Time 与 Watermark 面试、Window 面试 等
- [[37.3-数仓与 Lakehouse 面试]] — 数仓建模面试、SCD 面试、拉链表面试、实时数仓面试、CDC 面试 等
- [[37.4-治理与分布式面试]] — 数据质量面试、数据治理面试、分布式系统面试、性能优化面试、容量规划面试
- [[37.5-机器学习与推荐面试]] — 机器学习面试、推荐系统面试、搜索系统面试、ANN 面试、特征工程面试
- [[37.6-系统设计面试]] — 数据平台设计、实时平台设计、推荐系统设计、搜索系统设计、日志系统设计 等

### 综合项目实战
- [[38.1-离线数据分析平台]] — 技术选型、架构设计、数据采集模块、存储与数仓模块、计算与加工模块 等
- [[38.2-电商离线数仓]] — 技术选型、架构设计、数仓分层设计、维度建模与缓慢变化维、拉链表与快照表设计 等
- [[38.3-实时数仓]] — 技术选型、架构设计、数据接入与链路、时间语义与水印、窗口计算 等
- [[38.4-CDC 数据同步平台]] — 技术选型、架构设计、Binlog 原理与解析、Debezium 数据采集、Schema Evolution 等
- [[38.5-Lakehouse 平台]] — 技术选型、架构设计、对象存储与 Iceberg 表格式、Catalog 与元数据管理、计算引擎统一接入 等
- [[38.6-实时风控数据平台]] — 技术选型、架构设计、事件接入与 Kafka 缓冲、Flink CEP 规则引擎、黑白名单过滤 等
- [[38.7-企业级数据平台]] — 技术选型、架构设计、采集与 CDC 接入、消息总线与流批计算、存储层与查询层 等

## 微信小程序与后台知识库

> 基于《微信小程序与后台学习知识库总目录》编排（24 篇章、106 篇文档，2026-08-20 全部完成），覆盖小程序注册、WXML/WXSS/JS、组件、API、登录支付、订阅消息、分享、分包性能、安全合规、测试、发布上线，以及 SpringBoot 后台、Vue 管理后台、前后端联调、部署运维、全栈项目实战与面试。入口见 `weapp-fullstack/README.md`。

- [[weapp-fullstack/README]] — 微信小程序与后台知识库：目录树（24 篇章）+ 进度追踪表，覆盖小程序开发全流程（开发、测试、联调、部署、上线）与 SpringBoot+Vue 全栈

### 01-小程序注册与开发环境

- [[01.1-小程序概述与学习路线]] — 微信小程序是微信生态内的轻量级应用形态，用户通过扫码、搜索、分享、下拉等入口直接打开，无需安装下载
- [[01.2-注册与开发者工具]] — 开发微信小程序的第一步是拥有一个可用的账号与一套可运行的开发环境：账号（含 AppID）是代码上传、真机预览、调用微信开放能力的身份凭证，微信开发者工具则是本地
- [[01.3-项目创建与目录结构]] — 创建项目是代码之旅的真正起点：在微信开发者工具中填入项目名称、选择目录、指定 AppID，工具就会生成一套标准的小程序工程骨架
- [[01.4-开发调试基础]] — 写完代码只是开始，调试才是开发日常的主旋律

### 02-小程序基础与全局配置

- [[02.1-全局配置 app.json]] — app.json 是小程序的全局配置文件，位于项目根目录，定义整个小程序的「骨架与默认行为」：哪些页面存在、首页是哪个、导航栏长什么样、底部 tabBar 如何
- [[02.2-页面配置与页面生命周期]] — 每个小程序页面由四个文件组成（.wxml / .wxss / .js / .json），其中页面级的 .json 文件用于覆盖 app.json 中的全局窗口配
- [[02.3-sitemap 与微信搜索]] — sitemap.json 是小程序根目录下的搜索收录配置文件，用于声明哪些页面允许被微信搜索索引（收录）、哪些页面禁止收录，并可通过 params 精确控制带特
- [[02.4-基础库与版本兼容]] — 基础库（Base Library）是微信客户端内置的一套运行库，小程序的所有 API（wx.*）与组件都来自基础库，相当于「小程序的系统」
- [[02.5-全局样式与公共样式]] — app.wxss 是小程序的全局样式文件，位于项目根目录，其中的样式对所有页面生效，是页面样式的公共底座

### 03-WXML 模板语法

- [[03.1-数据绑定]] — 数据绑定是 WXML 最核心的机制：逻辑层（JS）通过 Page 的 data 保存页面状态，视图层（WXML）用 Mustache 语法（双花括号 {{ }}
- [[03.2-条件渲染与列表渲染]] — 条件渲染与列表渲染是 WXML 控制属性的两大主力：wx:if / wx:elif / wx:else 根据条件决定节点是否渲染，hidden 用样式控制显示隐
- [[03.3-模板与引用]] — 模板与引用解决「结构复用」问题：同一段 WXML 结构（商品卡片、订单行、空态提示）在多个页面重复出现时，用 template 定义一次、随处引用，避免复制粘贴
- [[03.4-事件系统]] — 事件系统是 WXML 交互的基石：用户触摸、输入、提交表单时产生事件，通过 bind/catch 等绑定方式把事件与页面 JS 中的处理函数关联起来
- [[03.5-数据通信]] — 小程序是双线程架构：逻辑层（JavaScript 运行环境）与视图层（WXML/WXSS 渲染环境）相互隔离，逻辑层不能直接操作 DOM，视图层也不能直接拿到 

### 04-WXSS 样式与布局

- [[04.1-WXSS 与 rpx]] — WXSS（WeChat Style Sheets）是小程序的样式语言，语法与 CSS 高度一致，任何会写 CSS 的开发者都能零成本上手
- [[04.2-选择器与样式特性]] — 选择器决定「样式规则作用到哪些节点」，是 WXSS 的地基
- [[04.3-Flex 布局]] — Flex（Flexible Box，弹性盒）是移动端页面布局的事实标准，也是小程序 WXSS 中最常用的布局方案
- [[04.4-Grid 与经典布局]] — CSS Grid 是二维网格布局方案，在 WXSS 中与 Flex 形成互补：Flex 擅长一维排列（行或列），Grid 擅长同时控制行与列，适合九宫格入口、卡
- [[04.5-暗黑模式与主题适配]] — 微信小程序从基础库 2.11.0 起支持暗黑模式（DarkMode）：在 app.json 中开启 `darkmode` 后，小程序会跟随系统外观（浅色/深色）

### 05-JS 逻辑层

- [[05.1-小程序 JS 与运行环境]] — 小程序代码运行在微信客户端提供的容器中，分为逻辑层与视图层两个线程：逻辑层（App Service）运行 JavaScript，承载业务逻辑；视图层（WebVi
- [[05.2-App 与 Page 注册]] — 小程序由 App 与 Page 两类注册入口构成：app.js 中的 `App()` 注册小程序实例，承载全局生命周期与全局数据；每个页面目录下的 js 文件用
- [[05.3-生命周期详解]] — 生命周期是小程序运行时对「应用、页面、组件」从创建到销毁全过程的阶段划分，每个阶段对应一个回调函数，开发者在这些回调里完成初始化、数据加载、状态刷新与资源清理
- [[05.4-模块化与代码组织]] — 小程序逻辑层（JS）运行在独立的 JS 引擎中，代码按「模块」组织：每个 .js 文件就是一个模块，通过 CommonJS 规范（module.exports 
- [[05.5-WXS 脚本]] — WXS（WeiXin Script）是小程序视图层的一套脚本语言，运行在视图层（渲染线程）中，与 WXML 处于同一线程，因此可以在模板渲染时直接完成数据计算与

### 06-小程序内置组件

- [[06.1-视图容器组件]] — 视图容器组件是小程序布局体系的地基，负责页面的块级布局、滚动、轮播、拖拽与原生组件覆盖
- [[06.2-基础内容组件]] — 基础内容组件负责页面中最常见的内容展示：文本、富文本、进度条与图标
- [[06.3-表单组件]] — 表单组件是页面与用户交互输入的核心，涵盖按钮、单行输入、多行输入、单选、多选、开关、滑块与各类选择器
- [[06.4-导航与媒体组件]] — 导航与媒体组件解决两类问题：页面之间的跳转（navigator）和多媒体内容的展示（image、video、audio、camera、live-player）
- [[06.5-开放能力组件]] — 开放能力组件是微信生态能力的载体：open-data 展示微信开放数据，web-view 内嵌 H5 网页，map 提供腾讯地图渲染，canvas 提供 2D 

### 07-自定义组件

- [[07.1-Component 构造器]] — Component 构造器是微信小程序自定义组件的唯一入口，它比 Page 构造器多出 properties、observers、externalClasses
- [[07.2-组件通信]] — 小程序组件化之后，页面、组件、组件之间需要交换数据与状态，这就是组件通信
- [[07.3-behaviors 与插槽]] — behaviors 是小程序组件间的代码复用机制，类似前端常说的 mixin：把一组公共的 properties、data、methods、observers、
- [[07.4-组件进阶]] — 自定义组件的基础能力（Component 构造器、properties、通信、behaviors、插槽）覆盖了常规开发，进阶特性解决的是工程化场景：纯数据字段避
- [[07.5-组件库实践]] — 组件库是自定义组件开发的规模化阶段：单个组件解决局部复用，组件库解决整站复用、设计一致性与研发效率

### 08-小程序 API

- [[08.1-网络请求 API]] — wx.request 是小程序发起 HTTPS 网络请求的唯一标准 API，小程序没有浏览器环境的 fetch/XHR，所有与 SpringBoot 后台的交互
- [[08.2-数据存储 API]] — 数据存储 API 是 wx 命名空间中与网络请求并列的高频 API 组，提供键值对的本地缓存能力：wx.setStorage 写入、wx.getStorage 
- [[08.3-路由 API]] — 路由 API 控制小程序页面之间的跳转与返回，包括 wx.navigateTo（保留当前页入栈）、wx.redirectTo（关闭当前页替换）、wx.switc
- [[08.4-界面交互 API]] — 界面交互 API 是 wx 命名空间下与用户反馈、页面外观、滚动行为相关的 API 集合，包括消息提示（wx.showToast / wx.showModal 
- [[08.5-设备与系统 API]] — 设备与系统 API 是 wx 命名空间下与硬件环境、系统状态相关的 API 集合，包括系统信息（wx.getSystemInfoSync 系列）、网络状态（wx
- [[08.6-媒体 API]] — 媒体 API 是 wx 命名空间下与图片、录音、视频、音频相关的 API 集合，覆盖「采集 → 上传 → 展示 → 播放」全链路：图片选择（wx.chooseM

### 09-登录与用户体系

- [[09.1-登录流程设计]] — 小程序登录不是传统意义的「用户名密码登录」，而是「微信身份凭证换发」流程：小程序端调用 wx.login 拿到临时登录凭证 code，交给自己的后端，后端拿 c
- [[09.2-会话保持与 Token]] — 09.1 篇章解决了「用户是谁」的问题：wx.login 换回 openid 并建立用户
- [[09.3-用户信息获取]] — 2021 年之前，小程序可以用 wx.getUserInfo 或 wx.getUserProfile 弹一个授权框，用户点同意后一次性拿到头像、昵称、性别等完整
- [[09.4-用户中心与多端打通]] — 前三个篇章解决了「登录怎么来、会话怎么保、资料怎么拿」，本篇章解决「用户数据怎么存、怎么用」

### 10-微信支付

- [[10.1-支付开通与准备]] — 微信支付是交易类小程序（电商、预约、知识付费等）的核心闭环能力
- [[10.2-小程序支付流程]] — 小程序支付的完整链路是「前端下单 -> 后端创建订单 -> 后端调用微信 JSAPI 下单接口获取 prepay_id -> 后端生成支付参数并签名 -> 小程
- [[10.3-支付回调与订单]] — 用户支付成功后，微信支付服务器会向商户后台的 notify_url 异步发送支付结果通知，商户后台必须完成「验签 -> 解密 -> 幂等更新订单」三步才能可靠地
- [[10.4-退款与对账]] — 退款是支付体系的资金反向操作：商户把用户已支付的金额按原路退回其微信零钱或原支付渠道

### 11-订阅消息

- [[11.1-订阅消息基础]] — 订阅消息是微信小程序向用户主动下发通知的核心能力：用户在小程序内通过授权弹窗或订阅按钮明确同意订阅某个模板后，服务端便可在符合条件时向该用户推送一条服务通知，消
- [[11.2-小程序端订阅]] — 小程序端订阅是整个订阅消息链路的第一环：用户在小程序内同意订阅某个模板后，微信服务端才会为「用户 + 模板」登记一条下发额度，后续服务端才能调用 subscri
- [[11.3-服务端下发]] — 服务端下发是订阅消息链路中由 SpringBoot 后台承担的环节：小程序端完成用户订阅后，后台在业务事件发生时（订单发货、支付成功、预约提醒）调用微信订阅消息
- [[11.4-订阅消息实践]] — 订阅消息的工程实现只是第一步，真正决定业务价值的是运营层面的设计：什么时机发、发什么内容、用户拒绝了怎么办、如何衡量触达效果、如何满足合规要求

### 12-分享与开放能力

- [[12.1-分享能力]] — 微信分享是社交裂变的核心能力：用户把小程序卡片发给好友或群聊，或分享到朋友圈，为产品带来低成本的自然流量
- [[12.2-扫码与外部跳转]] — 扫码与外部跳转解决「小程序之外的用户如何进来」的问题：线下物料扫码、短信/邮件链接、App 内跳转等场景，通过二维码、URL Scheme、URL Link 与
- [[12.3-客服与反馈]] — 客服与反馈是产品与用户之间的双向沟通通道：用户在小程序内通过 contact 按钮进入客服会话咨询问题，通过意见反馈提交建议与投诉；开发者既可以使用微信托管的客
- [[12.4-广告与商业化]] — 小程序商业化最直接的路径是接入微信广告（流量主）

### 13-分包与性能优化

- [[13.1-分包加载]] — 小程序对代码包体积有严格限制：主包不能超过 2M，整个小程序（主包 + 所有分包）不能超过 30M
- [[13.2-分包预下载与按需注入]] — 分包解决了「包太大不能上传」的问题，但「进入分包页面时才下载分包」会带来等待：用户点进商品详情，白屏转圈等分包下载完成
- [[13.3-setData 性能优化]] — 小程序是双线程架构：逻辑层（JS 线程）与视图层（渲染线程）分离，两层之间唯一的桥梁就是 `setData`
- [[13.4-渲染与启动优化]] — 用户对小程序的第一印象由两个时间决定：从点击到看到首页的「启动时间」，以及页面内容完整可用的「首屏时间」

### 14-安全与合规

- [[14.1-内容安全]] — 微信小程序的内容安全检测是平台提供的 UGC（用户生成内容）合规基础设施，通过 security.msgSecCheck、security.imgSecChec
- [[14.2-隐私合规]] — 隐私合规是小程序上线的硬性要求
- [[14.3-接口安全]] — 小程序后台接口安全的目标是保证「数据不被窃听、请求不被伪造、参数不被篡改、数据不被泄露」
- [[14.4-审核规范与红线]] — 小程序发布上线必须通过微信平台审核，审核规范围绕类目资质、内容规范、隐私合规三个维度展开

### 15-小程序测试

- [[15.1-测试概述与体系]] — 小程序全栈项目（小程序 + SpringBoot 后台 + Vue 管理端）涉及多端联动，任何一个环节出错都会直接呈现在用户面前：接口字段对不上、支付回调丢失、
- [[15.2-单元测试]] — 单元测试是测试金字塔的底座：对工具函数、组件逻辑等最小可测单元做隔离验证，不依赖网络、不依赖真机，在 Node 环境中毫秒级运行
- [[15.3-集成测试与自动化]] — 单元测试验证的是「单个函数对不对」，集成测试与自动化验证的是「整条链路通不通」
- [[15.4-真机调试与性能测试]] — 模拟器再方便，也无法替代真机：真机上的渲染性能、内存占用、网络切换、触摸手感、基础库版本差异，只有在真实设备上才能暴露

### 16-发布与上线

- [[16.1-版本管理与提审]] — 小程序与普通 Web 应用最大的区别之一在于「版本」概念：代码写好不能直接上线，必须通过微信开发者工具上传到微信服务器，在后台提交审核，审核通过后手动发布，用户
- [[16.2-发布与灰度]] — 审核通过只是「可以上线」，真正把新版本交到用户手里的是发布环节
- [[16.3-运营与监控]] — 发布上线只是开始，运营与监控决定产品能走多远
- [[16.4-更新迭代流程]] — 小程序的竞争力来自迭代速度：需求 -> 开发 -> 提审 -> 发布 -> 数据验证 -> 下一个迭代，这个循环跑得越快越稳，产品进化就越快

### 17-SpringBoot 后台基础

- [[17.1-工程搭建与分层]] — Spring Boot 是构建微信小程序后台服务的首选框架，它基于 Spring Framework 自动配置机制，让开发者用最少的配置快速启动一个可运行的 W
- [[17.2-统一返回与异常处理]] — 小程序端（wx.request）与后台交互时，期望收到一种「固定结构」的 JSON，无论成功失败都能用同一套逻辑解析，这是统一响应体的价值
- [[17.3-参数校验与日志]] — 小程序端传来的参数不可信，后台必须做两层防线：第一层是声明式参数校验（JSR-380 / Bean Validation），用注解声明规则，框架自动校验；第二层
- [[17.4-数据库访问]] — 数据库访问层是后台与 MySQL 之间的桥梁
- [[17.5-Redis 缓存]] — Redis 是后台的「性能加速器」与「分布式协调器」：商品详情、首页推荐、验证码、登录 Token、购物车等高频读写场景全部落在 Redis 上，避免每次请求都

### 18-后台认证与安全

- [[18.1-JWT 认证]] — JWT（JSON Web Token）是一种基于 JSON 的开放标准（RFC 7519）令牌格式，用于在客户端与服务端之间安全地传递身份与授权信息
- [[18.2-Spring Security 集成]] — Spring Security 是 Spring 生态的事实标准安全框架，提供认证（Authentication，你是谁）、授权（Authorization，你
- [[18.3-接口签名与防重放]] — JWT 解决的是「你是谁」的认证问题，但接口安全还有另一层威胁：请求被篡改、被重放、被高频刷
- [[18.4-权限模型与 RBAC]] — RBAC（Role-Based Access Control，基于角色的访问控制）是目前最主流的权限模型：不直接给用户授权，而是把权限授予角色，再把角色授予用户

### 19-微信集成服务端

- [[19.1-微信开放接口调用]] — 微信开放接口（Open API）是服务端与微信能力交互的唯一通道：登录换 openid、订阅消息下发、内容安全检查、用户手机号获取等，全部通过 https://
- [[19.2-登录对接]] — 小程序登录的核心诉求是「服务端拿到用户的微信身份（openid）并建立会话」
- [[19.3-支付服务端]] — 微信支付服务端是整个交易系统的资金咽喉：统一下单生成支付凭证、回调确认收款、退款原路退回、对账保证账实相符
- [[19.4-订阅消息服务端]] — 订阅消息是服务端主动触达用户的官方通道：订单状态变更、预约提醒、活动通知等场景，服务端可以下发一条微信消息，用户在小程序「服务通知」里查看

### 20-Vue 管理后台

- [[20.1-Vue3 工程搭建]] — Vue 管理后台是整个「微信小程序 + SpringBoot + Vue 管理后台」全栈架构中的 B 端部分，负责商品、订单、用户、运营配置等管理功能
- [[20.2-UI 框架与布局]] — Element Plus 是 Vue3 生态最主流的桌面端组件库，基于 TypeScript 开发，提供表单、表格、弹窗、菜单、分页等 60+ 组件，覆盖管理后
- [[20.3-路由与权限]] — 路由（vue-router）与权限是管理后台的骨架：路由决定「页面长什么样、怎么跳转」，权限决定「谁能看、谁能点」
- [[20.4-状态管理与请求封装]] — 管理后台是典型的多页面协作场景：用户信息、权限、全局配置等数据需要跨组件共享，接口请求需要统一的鉴权、错误处理与提示
- [[20.5-管理功能开发]] — 本章把前四章的知识串成真实业务功能：登录页（表单校验 + 登录请求 + token 存储 + 跳转）、用户管理（列表 + 分页 + 搜索 + 弹窗表单 + 删除

### 21-前后端联调

- [[21.1-API 设计与规范]] — 前后端联调的第一步，是把接口定义清楚
- [[21.2-联调流程与工具]] — 联调（联调测试）是前后端协作的核心环节：小程序端、SpringBoot 后端、Vue 管理端三方按接口文档把系统打通
- [[21.3-跨域与网络问题]] — 跨域与网络问题贯穿整个联调周期：Vue 管理端在浏览器里访问后端会触发 CORS 跨域拦截，小程序真机访问需要 HTTPS 合法域名，上线后还会遇到证书过期、D
- [[21.4-环境管理]] — 一套代码要跑在多个环境：开发环境（本地联调）、测试环境（提测验收）、生产环境（线上运行）

### 22-部署与运维

- [[22.1-服务器与域名]] — 小程序前端运行在微信客户端内，但它的业务数据全部来自自有后台（SpringBoot 服务）
- [[22.2-Nginx 部署]] — Nginx 是「小程序 + SpringBoot + Vue」全栈架构中的流量入口：它监听 80/443 端口，把 /api 开头的请求反向代理给后端 Java
- [[22.3-应用部署]] — 后台是 SpringBoot 单体服务，部署方式从简单到工程化依次是：jar 手工部署（java -jar + nohup）、systemd 托管（开机自启 +
- [[22.4-监控与告警]] — 上线只是开始，让服务「看得见、可预警、能恢复」才是运维的核心

### 23-全栈项目实战

- [[23.1-电商小程序]] — 电商小程序是微信生态内最常见的商业形态：用户在小程序内浏览商品、选择规格、加入购物车、下单，并通过微信支付完成交易；后台（SpringBoot）负责商品、库存、
- [[23.2-内容社区小程序]] — 内容社区小程序是「UGC 内容生产与消费」的轻量社区形态：用户发布图文帖、评论互动、点赞分享，后台负责内容安全检测与 feed 流分发，管理端完成内容审核治理
- [[23.3-预约服务小程序]] — 预约服务小程序是生活服务类业务（美容美发、健身、家政、医疗、汽车保养等）的标准 C 端形态：用户在小程序内完成「选服务 → 选门店 → 选日期时段 → 提交 →
- [[23.4-工具类小程序]] — 工具类小程序（证件照、计算器、翻译、天气、二维码、垃圾分类查询等）是微信生态里数量最多、门槛最低的一类小程序：单次任务 30 秒到 2 分钟即可完成，用完即走，

### 24-面试与常见问题

- [[24.1-小程序基础面试]] — 本篇章汇总微信小程序基础面试的高频考点，覆盖双线程模型、WXML 渲染原理、WXSS 与 rpx 适配、生命周期执行顺序、页面栈、组件通信、wx API 常见问
- [[24.2-小程序进阶面试]] — 本篇章覆盖小程序进阶面试的高频考点：性能优化（分包加载、setData 优化、首屏提速）、登录流程（wx.login + code2session + toke
- [[24.3-后台与全栈面试]] — 本篇章汇总小程序全栈后台方向的面试考点：SpringBoot 分层架构与统一返回、异常处理、JWT 认证与 Spring Security、Redis 缓存（穿
- [[24.4-系统设计面试]] — 本篇章汇总系统设计方向的高频面试题，围绕本知识库的全栈项目展开：电商小程序系统设计（商品、购物车、订单、支付、库存的完整链路）、消息推送设计（订阅消息 + 定时

## Linux 知识库

> 基于《Linux学习知识库总目录》搭建目录骨架（26 篇章、128 个主题），全部 26 篇章已完成。入口见 `linux/README.md`。

- [[linux/README]] — Linux 知识库：目录树（26 篇章）+ 进度追踪表，覆盖命令行、Shell 脚本与三剑客、权限与文件系统、进程与内存、软件包与 systemd、网络与防火墙、日志监控、性能调优、故障排查、存储与高可用、容器与自动化运维、内核与 eBPF 全链路

### 01-学习路线与开发环境

- [[01.1-学习路线与开发环境]] — Linux 运维/SRE/平台工程师能力模型、五阶段学习路线与先修关系、发行版选型、虚拟机/WSL2/Vagrant、SSH 密钥免密、Shell 环境与 tmux、Vim、编译工具链、curl/wget/scp/rsync、man/tldr 帮助、容器化实验与故障演练

### 02-Linux 系统基础

- [[02.1-内核与发行版]] — 内核概念、宏内核与微内核、版本号规则、主线与 LTS、发行版与内核关系、Debian/Red Hat/Arch 三大系
- [[02.2-文件系统层级标准 FHS]] — 根目录结构（/bin /etc /usr /var /opt 等职责）、/proc /sys /dev /run 伪文件系统
- [[02.3-文件与目录操作]] — 增删改查（ls/cd/mkdir/touch/cp/mv/rm）、文件查看（cat/less/head/tail/od/hexdump）、文件查找（find/locate/which/whereis/type）
- [[02.4-文件类型与属性]] — 七种文件类型、inode 与目录项、stat、硬链接与符号链接、atime/mtime/ctime 时间戳
- [[02.5-压缩与归档]] — tar 归档、gzip/bzip2/xz/zstd/zip 压缩、分卷、增量备份、归档校验
- [[02.6-重定向与管道]] — 标准输入输出错误、重定向符号、管道、tee、xargs

### 03-文本处理与三剑客

- [[03.1-正则表达式]] — 元字符/字符类/量词/锚点/分组/交替、贪婪与懒惰、BRE/ERE/PCRE 三种方言
- [[03.2-grep]] — 基本与扩展正则、常用选项(-i/-v/-c/-n/-o)、递归搜索、上下文、多模式
- [[03.3-sed]] — 替换/删除/插入追加、地址范围、模式空间与保持空间
- [[03.4-awk]] — 字段与记录、内置变量、模式与动作、条件/循环/数组、字符串与数值函数、BEGIN/END
- [[03.5-其他文本工具]] — sort/uniq/tr/cut/paste/join/comm/diff/patch/wc 十件套
- [[03.6-实战案例]] — Nginx 日志统计、CSV 与配置文件处理、批量改名

### 04-Shell 脚本编程

- [[04.1-Bash 基础]] — 脚本结构与执行、变量与作用域、环境变量、位置参数、特殊变量
- [[04.2-运算符与流程控制]] — 算术与字符串运算、test/[[]]、if/case、for/while/until/select
- [[04.3-函数]] — 函数定义、参数传递、返回值、局部变量、函数库
- [[04.4-数组与字符串处理]] — 一维与关联数组、字符串截取与替换、参数扩展
- [[04.5-输入输出重定向]] — 文件描述符、Here Document、Here String、进程替换
- [[04.6-进程与子 Shell]] — 子 shell、命令替换、后台任务、作业控制、trap
- [[04.7-调试与规范]] — set -x/-e/-u/-o pipefail、shellcheck、编码规范与可移植性

### 05-用户与权限管理

- [[05.1-用户与组]] — passwd/shadow/group/gshadow 四个账号文件、useradd/usermod/userdel/groupadd
- [[05.2-基本权限]] — rwx 权限、chmod/chown/chgrp、umask 与默认权限
- [[05.3-特殊权限与 ACL]] — SUID/SGID/Sticky Bit、setfacl/getfacl、ACL 掩码与默认 ACL
- [[05.4-提权与 sudo]] — su/sudo、sudoers、visudo、sudo 日志与审计、Polkit
- [[05.5-PAM 可插拔认证]] — PAM 模块、认证流程、pam_unix/pam_tally2/pam_limits
- [[05.6-资源限制]] — ulimit、limits.conf、cgroups 资源限制

### 06-磁盘与文件系统

- [[06.1-磁盘与分区]] — 磁盘结构、MBR/GPT、fdisk/parted/gdisk 分区工具
- [[06.2-文件系统]] — VFS、ext4/XFS/Btrfs/ZFS、格式化挂载、fstab/UUID、fsck
- [[06.3-逻辑卷管理 LVM]] — PV/VG/LV 三层、创建扩容缩容快照
- [[06.4-RAID]] — RAID 0/1/5/6/10、软 RAID mdadm
- [[06.5-交换空间]] — swap 分区与文件、swappiness
- [[06.6-磁盘配额与工具]] — quota、df/du/lsblk/blkid/iostat

### 07-进程与作业管理

- [[07.1-进程基础]] — 进程/线程/任务、PID/PPID、进程状态、fork/exec
- [[07.2-进程管理命令]] — ps/top/htop/pgrep/pkill/kill/killall/jobs/fg/bg/nohup
- [[07.3-进程优先级]] — nice/renice、调度器与优先级、cgroups CPU 限制
- [[07.4-信号]] — 信号机制、SIGTERM/SIGKILL/SIGINT/SIGHUP、signal/trap
- [[07.5-进程间通信 IPC]] — 管道/命名管道/信号量/共享内存/消息队列/socket
- [[07.6-守护进程]] — 守护进程特征、nohup、systemd 托管、日志重定向

### 08-内存管理

- [[08.1-虚拟内存]] — 虚拟地址空间、分页、页表与 TLB、mmap 内存映射
- [[08.2-内存分配与回收]] — 页缓存、Buffer/Cache、匿名页、内存水位线、回收机制
- [[08.3-Swap 与 OOM]] — 交换、swappiness、OOM Killer、内存超售与隔离
- [[08.4-内存监控与调优]] — free/vmstat/top/sar、内存泄漏排查、cgroups 内存限制

### 09-软件包管理

- [[09.1-Debian 系]] — apt/dpkg、软件源、依赖解析、apt-get/apt-cache
- [[09.2-Red Hat 系]] — yum/dnf/rpm、仓库管理、dnf 常用操作
- [[09.3-源码编译]] — configure/make/make install、configure 选项、编译依赖
- [[09.4-通用包格式]] — Snap/Flatpak/AppImage
- [[09.5-软件源与镜像]] — 官方源与镜像源、自建本地源、密钥签名校验

### 10-系统启动与 systemd

- [[10.1-开机启动流程]] — BIOS/UEFI、GRUB2、内核加载、initramfs、systemd
- [[10.2-systemd]] — unit 类型、systemctl 操作、依赖关系、启动顺序
- [[10.3-编写 Service Unit]] — unit 配置、Type/ExecStart/Restart、日志集成
- [[10.4-运行级别与 target]] — multi-user/graphical.target、rescue/emergency
- [[10.5-启动排错]] — 单用户模式、grub 修复、急救模式

### 11-网络基础

- [[11.1-TCP-IP 协议栈]] — OSI/TCP/IP 模型、IP 地址与子网、路由、ARP、ICMP
- [[11.2-网络配置]] — ip/ifconfig、网卡配置、静态与 DHCP、NetworkManager/systemd-networkd
- [[11.3-路由与转发]] — 路由表、默认网关、IP 转发、策略路由
- [[11.4-DNS 与主机名]] — /etc/hosts、resolv.conf、dig/nslookup/host、hostnamectl
- [[11.5-网络诊断工具]] — ping/traceroute/ss/netstat/nc/tcpdump/mtr/ethtool
- [[11.6-TCP 深入]] — 三次握手、四次挥手、状态机、TIME_WAIT、Keepalive、拥塞控制

### 12-防火墙与网络安全

- [[12.1-netfilter 框架]] — iptables 表与链、规则匹配、NAT、端口转发
- [[12.2-nftables]] — nft 语法、表/链/规则、与 iptables 对比
- [[12.3-firewalld-ufw]] — 区域、服务、富规则、直接规则
- [[12.4-安全通信]] — SSH 加固、OpenSSL、证书、TLS、VPN

### 13-日志管理与监控

- [[13.1-系统日志]] — syslog/rsyslog、journald、日志级别与设施
- [[13.2-日志轮转与集中]] — logrotate、日志归档、rsyslog 远程转发、ELK/Loki
- [[13.3-系统监控]] — top/htop/vmstat/iostat/mpstat/sar/pidstat
- [[13.4-监控体系]] — Prometheus/node_exporter、Grafana、告警（Alertmanager）
- [[13.5-日志分析实战]] — 日志检索、异常定位、审计追踪

### 14-定时任务与自动化

- [[14.1-cron]] — crontab 语法、系统级与用户级、特殊字符串、环境变量
- [[14.2-systemd timer]] — timer unit、OnCalendar、与 cron 对比
- [[14.3-at 与一次性任务]] — at/batch、anacron
- [[14.4-任务可靠性]] — 任务锁、日志、失败重试、邮件通知

### 15-系统调用与内核基础

- [[15.1-系统调用]] — 系统调用机制、用户态与内核态、strace 追踪
- [[15.2-内核模块]] — lsmod/modprobe/insmod、模块依赖、/lib/modules
- [[15.3-内核参数与伪文件系统]] — sysctl、/proc/sys、内核调优参数
- [[15.4-内核编译与升级]] — 内核源码、make menuconfig、内核升级与回滚

### 16-性能优化与调优

- [[16.1-性能分析方法论]] — 性能指标、USE 方法、容量规划、基线
- [[16.2-CPU 性能]] — 负载、上下文切换、中断、CPU 亲和性、perf
- [[16.3-内存性能]] — 页缓存、内存水位、swap、内存分配
- [[16.4-IO 性能]] — IO 调度器、磁盘吞吐与延迟、块设备调优
- [[16.5-网络性能]] — 网络吞吐、延迟、TCP 调优、网卡多队列
- [[16.6-综合调优工具]] — perf/bcc/bpftrace/eBPF、火焰图

### 17-故障排查与调试

- [[17.1-排查方法论]] — 故障分类、分层排查、信息收集、根因分析
- [[17.2-系统追踪]] — strace/ltrace、系统调用追踪、性能问题定位
- [[17.3-调试工具]] — gdb/pstack/addr2line/coredump 分析
- [[17.4-常见故障案例]] — 磁盘满、OOM、CPU 飙高、网络异常、无法登录、文件句柄耗尽

### 18-共享存储与数据备份

- [[18.1-共享存储]] — NFS/Samba/iSCSI、Ceph/GlusterFS
- [[18.2-数据备份与恢复]] — 备份策略、rsync/restic/borg、快照与恢复演练
- [[18.3-文件同步]] — rsync 增量同步、inotify/lsyncd 实时同步
- [[18.4-存储性能与容量]] — 存储性能评估、容量规划、磁盘老化与替换

### 19-高可用与负载均衡

- [[19.1-高可用基础]] — 高可用概念、心跳、脑裂、仲裁、故障转移
- [[19.2-Keepalived 与 VRRP]] — VRRP 协议、主备切换、健康检查、VIP 漂移
- [[19.3-LVS 负载均衡]] — NAT/DR/TUN 模式、调度算法、持久化连接
- [[19.4-HAProxy 与 Nginx]] — 七层/四层负载均衡、健康检查、会话保持、限流
- [[19.5-集群与一致性]] — 主从复制、主主、共享存储集群、分布式锁

### 20-网络服务

- [[20.1-Web 服务]] — Nginx/Apache、虚拟主机、反向代理、TLS 证书
- [[20.2-DNS 服务]] — BIND/dnsmasq/CoreDNS、区域、记录类型、解析流程
- [[20.3-DHCP 与时间同步]] — dnsmasq/isc-dhcp、NTP/chrony、时区
- [[20.4-文件共享服务]] — Samba/NFS/FTP/SFTP/rsync
- [[20.5-邮件与消息]] — Postfix、邮件协议、基础邮件服务

### 21-虚拟化与容器

- [[21.1-虚拟化基础]] — 虚拟化类型、KVM/QEMU/libvirt、virt-manager
- [[21.2-容器原理]] — namespace/cgroups、镜像分层、容器运行时
- [[21.3-Docker]] — 镜像/容器/网络/存储/Dockerfile/Compose
- [[21.4-容器编排基础]] — Kubernetes 概念、Pod/Service/Deployment、kubectl
- [[21.5-容器运行时生态]] — Podman/containerd/LXC、CRI、OCI 运行时

### 22-自动化运维与 IaC

- [[22.1-配置管理]] — Ansible、inventory/playbook/role/module
- [[22.2-基础设施即代码]] — Terraform、基础设施定义与状态管理
- [[22.3-持续集成部署]] — Git、GitLab CI/Jenkins、部署流水线
- [[22.4-配置与密钥管理]] — 配置中心、Vault 密钥管理、变更管理

### 23-安全加固与审计

- [[23.1-系统加固]] — 最小化安装、用户与权限、服务裁剪、内核加固参数
- [[23.2-强制访问控制]] — SELinux/AppArmor、策略与排错
- [[23.3-安全审计]] — auditd、审计规则、日志分析
- [[23.4-入侵检测与响应]] — AIDE 文件完整性、漏洞扫描、应急响应流程
- [[23.5-合规]] — 等保/CIS 基线、安全基线检查工具

### 24-内核源码、驱动与 eBPF

- [[24.1-内核源码阅读]] — 内核源码结构、进程调度、内存管理、文件系统、网络子系统
- [[24.2-驱动开发基础]] — 字符设备、设备树、模块开发、内核调试
- [[24.3-eBPF]] — eBPF 原理、bcc/bpftrace、可观测性与性能

### 25-Linux 面试与系统设计

- [[25.1-基础与命令]] — 文件系统、权限、进程、内存、网络、常用命令面试题
- [[25.2-原理深入]] — 系统调用、虚拟内存、TCP、IO、调度、内核机制面试题
- [[25.3-运维与排错]] — 常见故障、性能优化、高可用、安全面试题
- [[25.4-系统设计]] — 高并发架构、可观测性平台、CICD、容器平台设计题

### 26-综合项目实战

- [[26.1-Linux 服务器基础环境搭建]] — 系统安装、分区规划、用户与权限、SSH 加固、基础软件部署
- [[26.2-Web 站点与反向代理部署]] — Nginx 反向代理、多站点、TLS 证书、静态资源与缓存
- [[26.3-日志集中与监控告警平台]] — rsyslog/journald、Prometheus+Grafana、Alertmanager 告警
- [[26.4-自动化运维平台]] — Ansible 批量管理、巡检脚本、定时任务、发布流水线
- [[26.5-高可用集群与负载均衡]] — Keepalived+LVS/HAProxy、VIP 漂移、故障切换演练
- [[26.6-容器化与 K8s 部署]] — Dockerfile、Compose、Kubernetes 部署、滚动更新
- [[26.7-安全加固与合规基线]] — 系统加固、防火墙策略、SELinux、CIS 基线检查
- [[26.8-性能调优与故障演练]] — 压测、火焰图定位、内存/IO/网络调优、混沌演练

