# 学习笔记索引

> 内容目录。每篇文档附一句话摘要。先读这里找到相关文档。
> 最后更新：2026-08-13 | 总文档数：209

## 集成实践

- [[spring-boot-redis]] — Spring Boot 集成 Redis 详解：RedisTemplate 五种数据类型、Spring Cache 注解、Pipeline、序列化，含 5 个应用场景
- [[spring-boot-redisson]] — Spring Boot 集成 Redisson 详解：分布式锁、集合、限流器、布隆过滤器，含 6 个应用场景
- [[spring-boot-scheduled]] — Spring Boot 集成定时任务详解：@Scheduled、动态调度、分布式锁、Quartz、XXL-JOB，含 5 个应用场景
- [[spring-boot-mybatis]] — Spring Boot 集成 MyBatis 详解：XML/注解 Mapper、动态 SQL、高级结果映射、PageHelper、MyBatis-Plus、多数据源，含 5 个应用场景
- [[spring-boot-aop]] — Spring Boot 集成 AOP 详解：五种通知类型、切点表达式、16个应用场景（日志/耗时/权限/缓存/锁/限流/幂等/脱敏/加解密/重试/XSS/读写分离/traceId等）
- [[spring-boot-email]] — Spring Boot 集成邮件详解：JavaMailSender、HTML/附件/内联图片、Thymeleaf/FreeMarker模板、异步发送、可靠性（落库+重试）、多账号、验证码与异常告警场景
- [[spring-boot-rabbitmq]] — Spring Boot 集成 RabbitMQ 详解：4种交换机、消息发送接收、JSON序列化、可靠性投递、死信队列、延迟消息、幂等设计，含2个完整应用场景
- [[spring-boot-mybatis-plus]] — Spring Boot 集成 MyBatis-Plus 详解：BaseMapper、Lambda 条件构造器、分页插件、主键策略、逻辑删除、自动填充、乐观锁、代码生成器、多租户、数据权限，含 2 个完整应用场景

## Java 全栈基础

> 基于 Java 全栈学习知识体系编排，目前已覆盖前置章节 + 第一篇到第五十篇，共 201 篇。

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

- [[195-综合项目实战]] — 9 个项目进阶路线、学生成绩管理系统(Java SE)、用户管理系统(Servlet/JDBC)、企业员工管理系统(Spring Boot/Redis)、企业管理平台(RBAC/JWT/Vue)、订单系统(RabbitMQ)、微服务电商(Spring Cloud/Nacos/Feign)、秒杀系统(Redis/MQ)、数据平台(ES/Kafka)、AI 应用(Spring AI/RAG/Agent/MCP)

## 前端知识库

> 基于「前端完整知识库总目录」搭建目录骨架（103 篇章、416 个主题），内容待编写。入口见 `frontend-fullstack/README.md`。

- [[frontend-fullstack/README]] — 前端完整知识库：目录树（103 篇章）+ 进度追踪表，覆盖计算机基础/网络/HTML/CSS/JS/TS/工程化/React/Vue/Node/BFF/性能安全/架构全链路

### 01-计算机基础与开发环境

- [[01.1-计算机组成原理]] — CPU/GPU/ALU/寄存器/指令集、存储层次与 Cache、内存与虚拟内存、SSD/HDD、IO/DMA/中断、总线、字节序、字符编码，前端视角解析缓存友好遍历/TypedArray/位运算/乱码
- [[01.2-操作系统]] — 操作系统核心概念：进程/线程/协程、上下文切换与调度、内存管理（虚拟内存/页表/Page Fault）、文件系统与文件描述符、Socket、系统调用、IPC、信号、权限、用户态与内核态，结合浏览器多进程架构与 Node.js 场景讲解
- [[01.3-Linux]] — Linux 文件系统、Shell/Bash/Zsh、文本三剑客、find/xargs、网络与传输工具、进程与网络排查、systemd/cron、权限与环境变量、日志，前端部署排障视角
- [[01.4-Git]] — Git 从基础概念到协作工作流：commit/branch/tag、merge/rebase/cherry-pick、reset/revert/stash/reflog、diff/blame/bisect、submodule/worktree、hooks、Conventional Commits、Git Flow 与主干开发、Monorepo、PR 与 Code Review
- [[01.5-IDE 与开发环境]] — 前端开发环境全链路：VS Code 与 JetBrains、Chrome/Firefox DevTools、Node.js、npm/pnpm/Yarn 包管理器、Corepack、nvm/fnm/Volta 版本管理、Docker、Dev Container、WSL

## 概念解析

<!-- 待补充 -->

## 对比分析

<!-- 待补充 -->

## 排错笔记

<!-- 待补充 -->
