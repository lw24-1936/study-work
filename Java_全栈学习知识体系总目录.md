# Java 全栈学习知识体系总目录

> **用途**：作为 Java 全栈知识库的总目录（Index / Roadmap）。
> **整理原则**：保留原目录的知识范围与术语，仅统一标题层级、列表格式、代码块、分隔线与目录导航，并修复明显的 Markdown 格式不一致。

## 学习层级总览

```text
Level 1  Java 基础
   ↓
Level 2  Java SE 核心
   集合 / IO / 泛型 / Stream / 并发 / JVM
   ↓
Level 3  Java 企业开发
   JDBC / MySQL / MyBatis / Spring / Spring MVC / Spring Boot
   ↓
Level 4  Java 高级开发
   Redis / MQ / Elasticsearch / Security / 分布式 / 微服务
   ↓
Level 5  Java 架构与工程化
   高并发 / 高可用 / DDD / CQRS / DevOps / 云原生 / 源码
   ↓
Level 6  现代 Java 与 AI
   Java 21+ / Virtual Threads / Spring AI / RAG / Agent / MCP
```

## 目录

  - [0. Java 学习路线与开发环境](#0-java-学习路线与开发环境)
  - [0.1 Java 语言概述](#01-java-语言概述)
  - [0.2 Java 开发环境](#02-java-开发环境)
  - [0.3 Java IDE](#03-java-ide)
  - [0.4 构建工具](#04-构建工具)
- [第一篇 Java 语言基础](#第一篇-java-语言基础)
  - [1. Java 基础语法](#1-java-基础语法)
    - [1.1 第一个 Java 程序](#11-第一个-java-程序)
    - [1.2 注释](#12-注释)
    - [1.3 标识符](#13-标识符)
    - [1.4 变量](#14-变量)
    - [1.5 数据类型](#15-数据类型)
    - [1.6 类型转换](#16-类型转换)
  - [2. 运算符](#2-运算符)
  - [3. 流程控制](#3-流程控制)
  - [4. 数组](#4-数组)
  - [5. 字符与字符串](#5-字符与字符串)
- [第二篇 Java 面向对象](#第二篇-java-面向对象)
  - [6. 面向对象基础](#6-面向对象基础)
  - [7. 封装](#7-封装)
  - [8. 继承](#8-继承)
  - [9. 多态](#9-多态)
  - [10. 抽象类](#10-抽象类)
  - [11. 接口](#11-接口)
  - [12. Object 类](#12-object-类)
  - [13. Java 包与访问控制](#13-java-包与访问控制)
- [第三篇 Java 核心 API](#第三篇-java-核心-api)
  - [14. 包装类型](#14-包装类型)
  - [15. BigDecimal 与 BigInteger](#15-bigdecimal-与-biginteger)
  - [16. 日期与时间](#16-日期与时间)
  - [17. 正则表达式](#17-正则表达式)
  - [18. Java 枚举](#18-java-枚举)
  - [19. Java 注解](#19-java-注解)
  - [20. Java 异常](#20-java-异常)
- [第四篇 Java 集合框架](#第四篇-java-集合框架)
  - [21. Collection](#21-collection)
  - [22. List](#22-list)
  - [23. Set](#23-set)
  - [24. Map](#24-map)
  - [25. Queue](#25-queue)
  - [26. 集合底层原理](#26-集合底层原理)
- [第五篇 Java 泛型](#第五篇-java-泛型)
  - [27. 泛型基础](#27-泛型基础)
  - [28. 泛型高级](#28-泛型高级)
- [第六篇 Java 函数式编程](#第六篇-java-函数式编程)
  - [29. Lambda](#29-lambda)
  - [30. 函数式接口](#30-函数式接口)
  - [31. Stream](#31-stream)
  - [32. Optional](#32-optional)
- [第七篇 Java IO](#第七篇-java-io)
  - [33. IO 基础](#33-io-基础)
  - [34. 文件操作](#34-文件操作)
  - [35. NIO](#35-nio)
  - [36. NIO.2](#36-nio2)
  - [37. 网络编程](#37-网络编程)
- [第八篇 Java 并发编程](#第八篇-java-并发编程)
  - [38. 线程基础](#38-线程基础)
  - [39. synchronized](#39-synchronized)
  - [40. volatile](#40-volatile)
  - [41. Lock](#41-lock)
  - [42. 原子类](#42-原子类)
  - [43. 并发集合](#43-并发集合)
  - [44. 线程池](#44-线程池)
  - [45. CompletableFuture](#45-completablefuture)
  - [46. ForkJoin](#46-forkjoin)
  - [47. 虚拟线程](#47-虚拟线程)
- [第九篇 JVM](#第九篇-jvm)
  - [48. JVM 基础](#48-jvm-基础)
  - [49. JVM 内存结构](#49-jvm-内存结构)
  - [50. 类加载机制](#50-类加载机制)
  - [51. JVM 字节码](#51-jvm-字节码)
  - [52. JVM 垃圾回收](#52-jvm-垃圾回收)
  - [53. 垃圾收集器](#53-垃圾收集器)
  - [54. JVM 调优](#54-jvm-调优)
  - [55. JVM 工具](#55-jvm-工具)
- [第十篇 Java 反射与动态编程](#第十篇-java-反射与动态编程)
  - [56. 反射](#56-反射)
  - [57. 动态代理](#57-动态代理)
- [第十一篇 Java 模块化](#第十一篇-java-模块化)
  - [58. Java Module System](#58-java-module-system)
- [第十二篇 数据库](#第十二篇-数据库)
  - [59. 数据库基础](#59-数据库基础)
  - [60. SQL](#60-sql)
  - [61. MySQL](#61-mysql)
  - [62. 数据库事务](#62-数据库事务)
  - [63. 数据库连接](#63-数据库连接)
- [第十三篇 JDBC](#第十三篇-jdbc)
  - [64. JDBC](#64-jdbc)
- [第十四篇 ORM](#第十四篇-orm)
  - [65. JPA](#65-jpa)
  - [66. Hibernate](#66-hibernate)
  - [67. MyBatis](#67-mybatis)
  - [68. MyBatis-Plus](#68-mybatis-plus)
- [第十五篇 Java Web](#第十五篇-java-web)
  - [69. Servlet](#69-servlet)
  - [70. JSP](#70-jsp)
- [第十六篇 Spring Framework](#第十六篇-spring-framework)
  - [71. Spring 基础](#71-spring-基础)
  - [72. Spring 配置](#72-spring-配置)
  - [73. Spring AOP](#73-spring-aop)
  - [74. Spring 事务](#74-spring-事务)
- [第十七篇 Spring MVC](#第十七篇-spring-mvc)
  - [75. Spring MVC](#75-spring-mvc)
  - [76. REST API](#76-rest-api)
  - [77. 全局异常](#77-全局异常)
- [第十八篇 Spring Boot](#第十八篇-spring-boot)
  - [78. Spring Boot 基础](#78-spring-boot-基础)
  - [79. 配置体系](#79-配置体系)
  - [80. Starter](#80-starter)
  - [81. Spring Boot Web](#81-spring-boot-web)
- [第十九篇 Spring Security](#第十九篇-spring-security)
  - [82. Security 基础](#82-security-基础)
  - [83. JWT](#83-jwt)
  - [84. OAuth2](#84-oauth2)
- [第二十篇 Spring Data](#第二十篇-spring-data)
  - [85. Spring Data](#85-spring-data)
  - [86. Redis](#86-redis)
  - [87. MongoDB](#87-mongodb)
  - [88. Elasticsearch](#88-elasticsearch)
- [第二十一篇 Spring Cache](#第二十一篇-spring-cache)
  - [89. 缓存](#89-缓存)
- [第二十二篇 Spring Messaging](#第二十二篇-spring-messaging)
  - [90. 消息系统](#90-消息系统)
  - [91. RabbitMQ](#91-rabbitmq)
  - [92. Kafka](#92-kafka)
- [第二十三篇 Spring Cloud](#第二十三篇-spring-cloud)
  - [93. 微服务基础](#93-微服务基础)
  - [94. Nacos](#94-nacos)
  - [95. Gateway](#95-gateway)
  - [96. OpenFeign](#96-openfeign)
  - [97. LoadBalancer](#97-loadbalancer)
  - [98. 服务容错](#98-服务容错)
- [第二十四篇 分布式系统](#第二十四篇-分布式系统)
  - [99. 分布式基础](#99-分布式基础)
  - [100. 分布式锁](#100-分布式锁)
  - [101. 分布式 ID](#101-分布式-id)
  - [102. 分布式事务](#102-分布式事务)
- [第二十五篇 分布式架构](#第二十五篇-分布式架构)
  - [103. 高并发](#103-高并发)
  - [104. 高可用](#104-高可用)
  - [105. 分布式缓存](#105-分布式缓存)
- [第二十六篇 Redis](#第二十六篇-redis)
  - [106. Redis 基础](#106-redis-基础)
  - [107. Redis 高级](#107-redis-高级)
  - [108. Redis 应用](#108-redis-应用)
- [第二十七篇 Elasticsearch](#第二十七篇-elasticsearch)
  - [109. Elasticsearch 基础](#109-elasticsearch-基础)
  - [110. Elasticsearch 查询](#110-elasticsearch-查询)
  - [111. Elasticsearch 高级](#111-elasticsearch-高级)
- [第二十八篇 Linux](#第二十八篇-linux)
  - [112. Linux 基础](#112-linux-基础)
  - [113. Linux 命令](#113-linux-命令)
  - [114. Linux 进程](#114-linux-进程)
  - [115. Linux 网络](#115-linux-网络)
- [第二十九篇 Docker](#第二十九篇-docker)
  - [116. Docker 基础](#116-docker-基础)
  - [117. Docker 命令](#117-docker-命令)
  - [118. Docker Compose](#118-docker-compose)
- [第三十篇 Kubernetes](#第三十篇-kubernetes)
  - [119. Kubernetes 基础](#119-kubernetes-基础)
  - [120. Kubernetes 网络](#120-kubernetes-网络)
  - [121. Kubernetes 配置](#121-kubernetes-配置)
  - [122. Kubernetes 运维](#122-kubernetes-运维)
- [第三十一篇 DevOps](#第三十一篇-devops)
  - [123. Git](#123-git)
  - [124. CI/CD](#124-cicd)
  - [125. DevOps](#125-devops)
- [第三十二篇 测试](#第三十二篇-测试)
  - [126. 单元测试](#126-单元测试)
  - [127. Spring Boot 测试](#127-spring-boot-测试)
  - [128. 集成测试](#128-集成测试)
  - [129. 性能测试](#129-性能测试)
- [第三十三篇 API 与接口设计](#第三十三篇-api-与接口设计)
  - [130. API 设计](#130-api-设计)
  - [131. API 文档](#131-api-文档)
  - [132. API 安全](#132-api-安全)
- [第三十四篇 文件与办公自动化](#第三十四篇-文件与办公自动化)
  - [133. Excel](#133-excel)
  - [134. PDF](#134-pdf)
  - [135. 图片](#135-图片)
- [第三十五篇 工作流](#第三十五篇-工作流)
  - [136. BPMN](#136-bpmn)
  - [137. Flowable](#137-flowable)
- [第三十六篇 规则引擎](#第三十六篇-规则引擎)
  - [138. Drools](#138-drools)
  - [139. 业务规则](#139-业务规则)
- [第三十七篇 大数据](#第三十七篇-大数据)
  - [140. Hadoop](#140-hadoop)
  - [141. Hive](#141-hive)
  - [142. Spark](#142-spark)
  - [143. Flink](#143-flink)
- [第三十八篇 消息与流处理](#第三十八篇-消息与流处理)
  - [144. Kafka](#144-kafka)
  - [145. Kafka Streams](#145-kafka-streams)
  - [146. RocketMQ](#146-rocketmq)
- [第三十九篇 GraphQL](#第三十九篇-graphql)
  - [147. GraphQL](#147-graphql)
- [第四十篇 AI + Java](#第四十篇-ai--java)
  - [148. AI 基础](#148-ai-基础)
  - [149. 大语言模型](#149-大语言模型)
  - [150. Spring AI](#150-spring-ai)
  - [151. RAG](#151-rag)
  - [152. 向量数据库](#152-向量数据库)
  - [153. AI Agent](#153-ai-agent)
  - [154. MCP](#154-mcp)
- [第四十一篇 Java 架构设计](#第四十一篇-java-架构设计)
  - [155. 软件架构](#155-软件架构)
  - [156. 微服务架构](#156-微服务架构)
  - [157. 领域驱动设计](#157-领域驱动设计)
  - [158. CQRS](#158-cqrs)
  - [159. Event Sourcing](#159-event-sourcing)
- [第四十二篇 设计模式](#第四十二篇-设计模式)
  - [160. 创建型](#160-创建型)
  - [161. 结构型](#161-结构型)
  - [162. 行为型](#162-行为型)
  - [163. 企业级模式](#163-企业级模式)
- [第四十三篇 性能优化](#第四十三篇-性能优化)
  - [164. Java 性能](#164-java-性能)
  - [165. JVM 性能](#165-jvm-性能)
  - [166. 数据库性能](#166-数据库性能)
  - [167. Web 性能](#167-web-性能)
- [第四十四篇 高并发架构](#第四十四篇-高并发架构)
  - [168. 高并发基础](#168-高并发基础)
  - [169. 高并发技术](#169-高并发技术)
  - [170. 秒杀系统](#170-秒杀系统)
- [第四十五篇 安全](#第四十五篇-安全)
  - [171. Web 安全](#171-web-安全)
  - [172. 密码学](#172-密码学)
  - [173. 身份认证](#173-身份认证)
- [第四十六篇 Java 企业级项目实战](#第四十六篇-java-企业级项目实战)
  - [174. 项目基础架构](#174-项目基础架构)
  - [175. 通用能力](#175-通用能力)
  - [176. 企业功能](#176-企业功能)
- [第四十七篇 项目工程化](#第四十七篇-项目工程化)
  - [177. 项目结构](#177-项目结构)
  - [178. 代码规范](#178-代码规范)
  - [179. Code Review](#179-code-review)
- [第四十八篇 源码分析](#第四十八篇-源码分析)
  - [180. JDK 源码](#180-jdk-源码)
  - [181. Spring 源码](#181-spring-源码)
  - [182. Spring Boot 源码](#182-spring-boot-源码)
  - [183. MyBatis 源码](#183-mybatis-源码)
  - [184. Spring MVC 源码](#184-spring-mvc-源码)
  - [185. Spring Security 源码](#185-spring-security-源码)
- [第四十九篇 Java 常见问题](#第四十九篇-java-常见问题)
  - [186. Java 基础面试](#186-java-基础面试)
  - [187. 集合面试](#187-集合面试)
  - [188. 并发面试](#188-并发面试)
  - [189. JVM 面试](#189-jvm-面试)
  - [190. Spring 面试](#190-spring-面试)
  - [191. Spring Boot 面试](#191-spring-boot-面试)
  - [192. Spring Cloud 面试](#192-spring-cloud-面试)
  - [193. Redis 面试](#193-redis-面试)
  - [194. MySQL 面试](#194-mysql-面试)
- [第五十篇 综合项目实战](#第五十篇-综合项目实战)
- [项目一：Java 基础项目](#项目一java-基础项目)
- [项目二：Java Web](#项目二java-web)
- [项目三：Spring Boot](#项目三spring-boot)
- [项目四：Spring Boot + Vue](#项目四spring-boot--vue)
- [项目五：消息队列](#项目五消息队列)
- [项目六：微服务](#项目六微服务)
- [项目七：高并发](#项目七高并发)
- [项目八：数据平台](#项目八数据平台)
- [项目九：AI 应用](#项目九ai-应用)
- [最终建议的知识库目录结构](#最终建议的知识库目录结构)
- [如果目标是“真正完整的 Java 文档体系”](#如果目标是真正完整的-java-文档体系)

---

## 正文

## Java 全栈学习知识体系总目录
### 0. Java 学习路线与开发环境
### 0.1 Java 语言概述
- Java 是什么
- Java 的发展历史
- Java 的特点
- Java 的应用领域
- Java SE / Java EE / Jakarta EE
- OpenJDK
- Oracle JDK
- JDK / JRE / JVM
- Java LTS 版本
- Java 8
- Java 11
- Java 17
- Java 21
- Java 25
- Java 版本选择

### 0.2 Java 开发环境
- JDK 安装
- JAVA_HOME
- PATH
- Java 环境变量
- javac
- java
- jar
- javadoc
- jshell
- jdb
- jcmd
- jconsole
- jps
- jstack
- jmap
- jinfo
- jstat

### 0.3 Java IDE
- IntelliJ IDEA
- Eclipse
- VS Code
- IDEA 项目结构
- IDEA 常用快捷键
- Debug
- 断点
- 条件断点
- Evaluate Expression
- Remote Debug

### 0.4 构建工具
- Maven
- Gradle
- Ant
- Maven 生命周期
- Maven 坐标
- Maven 仓库
- Maven 依赖
- Maven Scope
- Maven Profile
- Maven Plugin
- Maven BOM
- Gradle 基础
- Gradle Wrapper
- Gradle Plugin
- Gradle 多模块项目

---

## 第一篇 Java 语言基础
### 1. Java 基础语法
#### 1.1 第一个 Java 程序
- Hello World
- Java 源文件
- 编译
- 运行
- main 方法
- 类
- 包

#### 1.2 注释
- 单行注释
- 多行注释
- 文档注释
- Javadoc

#### 1.3 标识符
- 标识符规则
- 关键字
- 保留字
- 命名规范

#### 1.4 变量
- 局部变量
- 成员变量
- 静态变量
- 常量
- final

#### 1.5 数据类型
- 基本数据类型
- byte
- short
- int
- long
- float
- double
- char
- boolean
- 引用类型

#### 1.6 类型转换
- 自动类型转换
- 强制类型转换
- 数值溢出
- 类型提升

---

### 2. 运算符
- 算术运算符
- 关系运算符
- 逻辑运算符
- 位运算符
- 赋值运算符
- 三元运算符
- 自增自减
- instanceof
- 运算符优先级
- 短路求值

---

### 3. 流程控制
- if
- if else
- switch
- switch 表达式
- for
- while
- do while
- break
- continue
- return
- 嵌套循环
- 标签语句

---

### 4. 数组
- 一维数组
- 二维数组
- 多维数组
- 数组初始化
- 数组遍历
- 数组复制
- 数组排序
- Arrays
- 可变参数
- 数组与集合转换

---

### 5. 字符与字符串
- char
- String
- String 常量池
- String 不可变性
- StringBuilder
- StringBuffer
- 字符编码
- Unicode
- UTF-8
- 字符串比较
- 字符串查找
- 字符串截取
- 字符串替换
- 字符串分割
- 字符串格式化
- Text Blocks

---

## 第二篇 Java 面向对象
### 6. 面向对象基础
- 面向对象思想
- 类
- 对象
- 属性
- 方法
- 构造方法
- this
- new
- 对象创建
- 对象销毁
- 方法重载

---

### 7. 封装
- private
- public
- protected
- 默认访问权限
- getter
- setter
- JavaBean
- 不可变对象

---

### 8. 继承
- extends
- 父类
- 子类
- 方法重写
- super
- 构造方法继承
- 向上转型
- 向下转型
- instanceof

---

### 9. 多态
- 编译时多态
- 运行时多态
- 方法重载
- 方法重写
- 动态绑定
- 虚方法调用

---

### 10. 抽象类
- abstract
- 抽象方法
- 抽象类
- 抽象类继承
- 抽象类设计

---

### 11. 接口
- interface
- implements
- 接口方法
- default 方法
- static 方法
- private 接口方法
- 函数式接口
- 接口继承
- 多接口实现

---

### 12. Object 类
- equals
- hashCode
- toString
- clone
- getClass
- wait
- notify
- notifyAll

---

### 13. Java 包与访问控制
- package
- import
- static import
- 包结构
- 访问修饰符
- 模块访问

---

### 内部类（补充）

- 成员内部类
- 静态内部类
- 局部内部类
- 匿名内部类
- 编译原理
- 应用场景

---

## 第三篇 Java 核心 API
### 14. 包装类型
- Integer
- Long
- Double
- Float
- Boolean
- Character
- Short
- Byte
- Number
- 自动装箱
- 自动拆箱
- Integer 缓存
- valueOf
- parseXXX

---

### 15. BigDecimal 与 BigInteger
- BigDecimal
- BigInteger
- 精确计算
- 金融计算
- rounding
- scale
- precision

---

### 16. 日期与时间
- Date
- Calendar
- TimeZone
- LocalDate
- LocalTime
- LocalDateTime
- Instant
- ZonedDateTime
- OffsetDateTime
- Duration
- Period
- DateTimeFormatter
- 时区
- 时间戳
- 时间转换

---

### 17. 正则表达式
- Pattern
- Matcher
- 正则表达式语法
- 字符类
- 量词
- 分组
- 捕获组
- 非捕获组
- 前瞻
- 后瞻
- 正则替换

---

### 18. Java 枚举
- enum
- 枚举属性
- 枚举方法
- 枚举构造方法
- EnumSet
- EnumMap

---

### 19. Java 注解
- Annotation
- 内置注解
- 自定义注解
- 元注解
- Retention
- Target
- Documented
- Inherited
- Repeatable
- 注解处理器
- Runtime Annotation

---

### 20. Java 异常
- Exception
- Error
- Throwable
- RuntimeException
- Checked Exception
- Unchecked Exception
- try
- catch
- finally
- throw
- throws
- 自定义异常
- 异常链
- 多异常捕获
- try-with-resources
- 异常设计原则

---

## 第四篇 Java 集合框架
### 21. Collection
- Collection
- List
- Set
- Queue
- Deque

---

### 22. List
- ArrayList
- LinkedList
- Vector
- CopyOnWriteArrayList

---

### 23. Set
- HashSet
- LinkedHashSet
- TreeSet
- EnumSet

---

### 24. Map
- HashMap
- LinkedHashMap
- TreeMap
- Hashtable
- WeakHashMap
- IdentityHashMap
- EnumMap
- ConcurrentHashMap

---

### 25. Queue
- Queue
- Deque
- PriorityQueue
- ArrayDeque
- BlockingQueue

---

### 26. 集合底层原理
- ArrayList 扩容
- LinkedList 链表
- HashMap 原理
- Hash 冲突
- 哈希桶
- 红黑树
- TreeMap
- HashSet 原理
- ConcurrentHashMap
- Fail-Fast
- Fail-Safe
- Iterator
- Spliterator

---

## 第五篇 Java 泛型
### 27. 泛型基础
- 泛型是什么
- 泛型类
- 泛型接口
- 泛型方法
- 泛型构造器
- 类型参数

### 28. 泛型高级
- 类型擦除
- 泛型继承
- 通配符
- ?
- extends
- super
- PECS
- 泛型边界
- 类型推断
- 泛型与反射

---

## 第六篇 Java 函数式编程
### 29. Lambda
- Lambda 表达式
- Lambda 语法
- Lambda 类型推断
- Lambda 变量捕获
- effectively final

### 30. 函数式接口
- Function
- Consumer
- Supplier
- Predicate
- UnaryOperator
- BinaryOperator
- BiFunction
- BiConsumer
- BiPredicate

### 31. Stream
- Stream
- 创建 Stream
- filter
- map
- flatMap
- distinct
- sorted
- limit
- skip
- peek
- reduce
- collect
- groupingBy
- partitioningBy
- joining
- counting
- min
- max
- sum
- average
- 并行 Stream

### 32. Optional
- Optional
- of
- ofNullable
- empty
- map
- flatMap
- filter
- orElse
- orElseGet
- orElseThrow

---

## 第七篇 Java IO
### 33. IO 基础
- InputStream
- OutputStream
- Reader
- Writer
- 字节流
- 字符流
- 缓冲流

### 34. 文件操作
- File
- Path
- Files
- Paths
- FileSystem
- 文件创建
- 文件复制
- 文件移动
- 文件删除
- 文件遍历
- 文件属性

### 35. NIO
- NIO
- Buffer
- Channel
- Selector
- ByteBuffer
- FileChannel
- SocketChannel
- ServerSocketChannel
- 非阻塞 IO

### 36. NIO.2
- Path
- Files
- WatchService
- FileVisitor
- AsynchronousFileChannel
- 异步 IO

### 37. 网络编程
- Socket
- ServerSocket
- TCP
- UDP
- DatagramSocket
- HTTP
- URL
- URI
- InetAddress

---

## 第八篇 Java 并发编程
### 38. 线程基础
- Process
- Thread
- Runnable
- Callable
- 线程生命周期
- 线程状态
- start
- run
- sleep
- interrupt
- join
- daemon thread

### 39. synchronized
- synchronized 方法
- synchronized 代码块
- 对象锁
- 类锁
- Monitor
- 锁升级
- synchronized 原理

### 40. volatile
- volatile
- 可见性
- 有序性
- volatile 原理
- happens-before

### 41. Lock
- Lock
- ReentrantLock
- ReentrantReadWriteLock
- StampedLock
- Condition

### 42. 原子类
- AtomicInteger
- AtomicLong
- AtomicBoolean
- AtomicReference
- AtomicIntegerArray
- LongAdder
- LongAccumulator
- CAS

### 43. 并发集合
- ConcurrentHashMap
- CopyOnWriteArrayList
- BlockingQueue
- ConcurrentLinkedQueue
- ConcurrentSkipListMap
- ConcurrentSkipListSet

### 44. 线程池
- Executor
- ExecutorService
- ThreadPoolExecutor
- ScheduledExecutorService
- Future
- FutureTask
- Callable
- CompletionService
- Executors
- 线程池参数
- 拒绝策略
- 线程池监控
- 自定义线程池

### 45. CompletableFuture
- CompletableFuture
- thenApply
- thenCompose
- thenCombine
- allOf
- anyOf
- exceptionally
- handle
- whenComplete
- 异步编排

### 46. ForkJoin
- ForkJoinPool
- ForkJoinTask
- RecursiveTask
- Work Stealing

### 47. 虚拟线程
- Virtual Thread
- Thread.ofVirtual
- Executors.newVirtualThreadPerTaskExecutor
- 平台线程
- 虚拟线程
- 虚拟线程适用场景
- 虚拟线程陷阱

---

## 第九篇 JVM
### 48. JVM 基础
- JVM
- JDK
- JRE
- JVM 架构
- Java 字节码
- Class 文件

### 49. JVM 内存结构
- 程序计数器
- Java 虚拟机栈
- 本地方法栈
- 堆
- 方法区
- Metaspace
- 常量池
- 直接内存

### 50. 类加载机制
- ClassLoader
- Bootstrap ClassLoader
- Platform ClassLoader
- Application ClassLoader
- 双亲委派
- 类加载过程
- 加载
- 验证
- 准备
- 解析
- 初始化
- 自定义 ClassLoader
- 类隔离

### 51. JVM 字节码
- 字节码
- Class 文件结构
- 常量池
- 方法表
- 字段表
- 属性表
- Opcode
- 字节码分析

### 52. JVM 垃圾回收
- GC
- Minor GC
- Major GC
- Full GC
- Stop-The-World
- GC Roots
- 可达性分析
- 三色标记
- 分代回收

### 53. 垃圾收集器
- Serial
- Parallel
- CMS
- G1
- ZGC
- Shenandoah
- GC 选择
- GC 调优

### 54. JVM 调优
- JVM 参数
- 堆内存
- 栈内存
- Metaspace
- GC 日志
- Heap Dump
- Thread Dump
- CPU 飙高
- 内存泄漏
- 内存溢出
- Full GC
- OOM
- 死锁分析

### 55. JVM 工具
- jps
- jstack
- jmap
- jcmd
- jstat
- jinfo
- jconsole
- VisualVM
- Mission Control
- Flight Recorder
- Arthas

---

## 第十篇 Java 反射与动态编程
### 56. 反射
- Class
- Constructor
- Method
- Field
- Modifier
- 反射创建对象
- 反射调用方法
- 反射访问字段
- 泛型反射
- 注解反射

### 57. 动态代理
- JDK Proxy
- InvocationHandler
- CGLIB
- Byte Buddy
- 动态代理原理
- AOP 与动态代理

---

## 第十一篇 Java 模块化
### 58. Java Module System
- module-info.java
- module
- requires
- exports
- opens
- uses
- provides
- ServiceLoader
- 模块路径
- 类路径
- 模块化应用

---

## 第十二篇 数据库
### 59. 数据库基础
- 数据库概念
- DB
- DBMS
- RDBMS
- 数据模型
- 关系模型
- ER 模型
- 主键
- 外键
- 索引
- 事务

### 60. SQL
- DDL
- DML
- DQL
- DCL
- TCL
- SELECT
- INSERT
- UPDATE
- DELETE
- JOIN
- GROUP BY
- HAVING
- ORDER BY
- 子查询
- CTE
- 窗口函数

### 61. MySQL
- MySQL 安装
- MySQL 架构
- InnoDB
- MVCC
- Redo Log
- Undo Log
- Binlog
- Buffer Pool
- 索引
- B+Tree
- 聚簇索引
- 非聚簇索引
- 覆盖索引
- 最左匹配
- EXPLAIN
- SQL 优化

### 62. 数据库事务
- ACID
- 隔离级别
- Read Uncommitted
- Read Committed
- Repeatable Read
- Serializable
- 脏读
- 不可重复读
- 幻读
- MVCC
- 悲观锁
- 乐观锁

### 63. 数据库连接
- JDBC
- Driver
- Connection
- Statement
- PreparedStatement
- ResultSet
- Batch
- Connection Pool
- HikariCP
- Druid

---

## 第十三篇 JDBC
### 64. JDBC
- JDBC 架构
- JDBC Driver
- Connection
- Statement
- PreparedStatement
- CallableStatement
- ResultSet
- ResultSetMetaData
- DatabaseMetaData
- 事务
- Batch
- Connection Pool
- SQL 注入

---

## 第十四篇 ORM
### 65. JPA
- JPA
- Entity
- Repository
- EntityManager
- Persistence Context
- Entity 生命周期
- OneToOne
- OneToMany
- ManyToOne
- ManyToMany
- JPQL
- Criteria API
- Specification
- Lazy Loading
- Cascade
- Orphan Removal

### 66. Hibernate
- Hibernate Session
- 一级缓存
- 二级缓存
- Dirty Checking
- Flush
- N+1
- Fetch Join
- Hibernate Validator

### 67. MyBatis
- MyBatis
- Mapper
- XML
- 动态 SQL
- ResultMap
- TypeHandler
- Interceptor
- 一级缓存
- 二级缓存
- SqlSession

### 68. MyBatis-Plus
- BaseMapper
- Service
- Wrapper
- LambdaQueryWrapper
- LambdaUpdateWrapper
- 分页
- 自动填充
- 逻辑删除
- 乐观锁
- 代码生成器

---

## 第十五篇 Java Web
### 69. Servlet
- Servlet
- Servlet Container
- Servlet 生命周期
- Filter
- Listener
- HttpServlet
- HttpServletRequest
- HttpServletResponse
- Session
- Cookie
- ServletContext

### 70. JSP
- JSP
- EL
- JSTL
- Tag
- JSP 生命周期

JSP 属于传统 Java Web 技术，建议作为历史知识了解，现代 Spring Boot 项目通常不以 JSP 作为主要前端技术。

---

## 第十六篇 Spring Framework
### 71. Spring 基础
- Spring Framework
- IoC
- DI
- Bean
- ApplicationContext
- BeanFactory
- Bean 生命周期
- Bean Scope
- Singleton
- Prototype

### 72. Spring 配置
- XML
- Java Config
- 注解配置
- @Configuration
- @Bean
- @Component
- @Service
- @Repository
- @Controller

### 73. Spring AOP
- AOP
- Aspect
- Join Point
- Pointcut
- Advice
- Around
- Before
- After
- AfterReturning
- AfterThrowing
- Proxy
- AspectJ

### 74. Spring 事务
- @Transactional
- TransactionManager
- 声明式事务
- 编程式事务
- 事务传播
- 事务隔离
- 事务回滚
- 事务失效场景

---

## 第十七篇 Spring MVC
### 75. Spring MVC
- DispatcherServlet
- Controller
- RequestMapping
- RequestParam
- PathVariable
- RequestBody
- ResponseBody
- ResponseEntity
- HandlerMapping
- HandlerAdapter
- Converter
- Formatter
- Interceptor
- Filter

### 76. REST API
- REST
- RESTful
- GET
- POST
- PUT
- DELETE
- PATCH
- HTTP Status
- JSON
- API 设计
- API 版本

### 77. 全局异常
- ControllerAdvice
- ExceptionHandler
- ErrorResponse
- ProblemDetail
- 统一异常
- 统一错误码

---

## 第十八篇 Spring Boot
### 78. Spring Boot 基础
- Spring Boot
- 自动配置
- Starter
- AutoConfiguration
- @SpringBootApplication
- Configuration
- Profile
- Environment
- Actuator

### 79. 配置体系
- application.properties
- application.yml
- Profile
- 外部配置
- 环境变量
- 配置绑定
- ConfigurationProperties

### 80. Starter
- Starter 原理
- 自定义 Starter
- 自动配置
- AutoConfiguration.imports
- 条件注解
- Conditional

### 81. Spring Boot Web
- Spring MVC
- WebFlux
- REST API
- JSON
- 文件上传
- 文件下载
- CORS
- WebSocket
- SSE

---

## 第十九篇 Spring Security
### 82. Security 基础
- Authentication
- Authorization
- SecurityContext
- Filter Chain
- PasswordEncoder
- UserDetails
- UserDetailsService

### 83. JWT
- JWT
- Access Token
- Refresh Token
- Token 过期
- Token 黑名单
- Token 刷新

### 84. OAuth2
- OAuth2
- Authorization Code
- Client Credentials
- Resource Owner Password
- Refresh Token
- OpenID Connect
- OAuth2 Client
- Resource Server
- Authorization Server

---

## 第二十篇 Spring Data
### 85. Spring Data
- Spring Data Commons
- Repository
- CrudRepository
- PagingAndSortingRepository
- JpaRepository
- Query Method

### 86. Redis
- Spring Data Redis
- RedisTemplate
- StringRedisTemplate
- Serialization
- Redis Pub/Sub
- Redis Stream
- Redis Lock

### 87. MongoDB
- Spring Data MongoDB
- MongoTemplate
- MongoRepository
- Document
- Query
- Aggregation

### 88. Elasticsearch
- Spring Data Elasticsearch
- Index
- Document
- Mapping
- Query
- Aggregation
- Search

---

## 第二十一篇 Spring Cache
### 89. 缓存
- Cache
- CacheManager
- @Cacheable
- @CachePut
- @CacheEvict
- Redis Cache
- Caffeine
- 多级缓存
- 缓存一致性

---

## 第二十二篇 Spring Messaging
### 90. 消息系统
- Message
- MessageChannel
- MessageConverter
- Event
- Listener

### 91. RabbitMQ
- Exchange
- Queue
- Binding
- Routing Key
- Direct
- Topic
- Fanout
- Headers
- ACK
- NACK
- Dead Letter
- TTL
- Retry

### 92. Kafka
- Broker
- Topic
- Partition
- Offset
- Consumer
- Producer
- Consumer Group
- ACK
- ISR
- Replication
- Kafka Streams

---

## 第二十三篇 Spring Cloud
### 93. 微服务基础
- 单体架构
- SOA
- 微服务
- 服务拆分
- 服务治理
- 服务注册
- 服务发现

### 94. Nacos
- 服务注册
- 服务发现
- 配置中心
- 动态配置
- 命名空间
- 分组
- 集群

### 95. Gateway
- Gateway
- Route
- Predicate
- Filter
- GlobalFilter
- 限流
- 鉴权
- 路由
- 灰度发布

### 96. OpenFeign
- Feign
- OpenFeign
- 服务调用
- 编码器
- 解码器
- 拦截器
- 超时
- 重试

### 97. LoadBalancer
- 服务负载均衡
- Round Robin
- Random
- 自定义负载均衡

### 98. 服务容错
- Circuit Breaker
- Resilience4j
- Sentinel
- Retry
- RateLimiter
- Bulkhead
- Timeout
- Fallback

---

## 第二十四篇 分布式系统
### 99. 分布式基础
- CAP
- BASE
- 一致性
- 可用性
- 分区容错
- 强一致性
- 最终一致性

### 100. 分布式锁
- Redis Lock
- Redisson
- Zookeeper Lock
- 数据库锁

### 101. 分布式 ID
- UUID
- Snowflake
- Leaf
- 数据库号段

### 102. 分布式事务
- Seata
- XA
- AT
- TCC
- Saga
- 本地消息表
- Outbox
- 事务消息

---

## 第二十五篇 分布式架构
### 103. 高并发
- QPS
- TPS
- 并发量
- 响应时间
- 吞吐量
- 限流
- 熔断
- 降级
- 排队
- 异步化

### 104. 高可用
- 主从
- 集群
- 故障转移
- Failover
- 熔断
- 降级
- 重试
- 超时
- 健康检查

### 105. 分布式缓存
- Redis Cluster
- Sentinel
- 主从
- 一致性 Hash
- Cache Aside
- Read Through
- Write Through

---

## 第二十六篇 Redis
### 106. Redis 基础
- Redis
- String
- List
- Set
- Hash
- ZSet
- Stream
- Bitmap
- HyperLogLog
- Geo

### 107. Redis 高级
- RDB
- AOF
- 混合持久化
- 主从
- Sentinel
- Cluster
- Pipeline
- Lua
- Pub/Sub
- Stream

### 108. Redis 应用
- 缓存
- Session
- 分布式锁
- 限流
- 排行榜
- 延迟队列
- 消息队列
- 布隆过滤器

---

## 第二十七篇 Elasticsearch
### 109. Elasticsearch 基础
- Index
- Document
- Field
- Mapping
- Shard
- Replica

### 110. Elasticsearch 查询
- Match
- Term
- Bool
- Range
- Prefix
- Wildcard
- Query String
- Aggregation

### 111. Elasticsearch 高级
- 分片
- 副本
- 集群
- 倒排索引
- Analyzer
- 分词器
- 中文分词
- 性能优化

---

## 第二十八篇 Linux
### 112. Linux 基础
- Linux
- CentOS
- Rocky Linux
- Ubuntu
- Debian
- 文件系统
- 用户
- 用户组
- 权限

### 113. Linux 命令
- ls
- cd
- pwd
- cp
- mv
- rm
- mkdir
- touch
- cat
- less
- head
- tail
- grep
- find
- sed
- awk
- sort
- uniq
- xargs
- cut
- wc
- tar
- gzip
- zip

### 114. Linux 进程
- ps
- top
- htop
- kill
- killall
- systemd
- systemctl
- journalctl

### 115. Linux 网络
- ping
- curl
- wget
- telnet
- nc
- ss
- netstat
- ip
- traceroute
- DNS
- TCP/IP

---

## 第二十九篇 Docker
### 116. Docker 基础
- Docker
- Image
- Container
- Registry
- Dockerfile
- Volume
- Network

### 117. Docker 命令
- docker pull
- docker run
- docker ps
- docker exec
- docker logs
- docker inspect
- docker stop
- docker restart
- docker rm
- docker rmi

### 118. Docker Compose
- compose
- Service
- Network
- Volume
- Environment
- Healthcheck
- Dependency

---

## 第三十篇 Kubernetes
### 119. Kubernetes 基础
- Kubernetes
- Cluster
- Node
- Pod
- Deployment
- ReplicaSet
- StatefulSet
- DaemonSet
- Job
- CronJob

### 120. Kubernetes 网络
- Service
- ClusterIP
- NodePort
- LoadBalancer
- Ingress
- DNS

### 121. Kubernetes 配置
- ConfigMap
- Secret
- Namespace
- Resource
- Limit
- Request

### 122. Kubernetes 运维
- kubectl
- Helm
- Probe
- HPA
- Rolling Update
- Rollback
- ConfigMap
- Secret

---

## 第三十一篇 DevOps
### 123. Git
- Git
- Repository
- Commit
- Branch
- Merge
- Rebase
- Tag
- Cherry-pick
- Stash
- Git Flow

### 124. CI/CD
- Jenkins
- GitHub Actions
- GitLab CI
- GitHub Actions Runner
- Pipeline
- Build
- Test
- Package
- Deploy

### 125. DevOps
- CI
- CD
- DevOps
- IaC
- Terraform
- Ansible
- Argo CD
- GitOps

---

## 第三十二篇 测试
### 126. 单元测试
- JUnit 5
- Mockito
- AssertJ
- Mock
- Stub
- Spy

### 127. Spring Boot 测试
- SpringBootTest
- MockMvc
- WebTestClient
- Test Slice
- DataJpaTest

### 128. 集成测试
- Testcontainers
- WireMock
- Embedded Database
- API Test

### 129. 性能测试
- JMeter
- Gatling
- Locust
- Load Test
- Stress Test
- Benchmark
- JMH

---

## 第三十三篇 API 与接口设计
### 130. API 设计
- REST
- RESTful
- URI
- HTTP Method
- Status Code
- Header
- Cookie
- JSON
- Pagination
- Sorting
- Filtering

### 131. API 文档
- OpenAPI
- Swagger
- Swagger UI
- Knife4j
- Spring REST Docs

### 132. API 安全
- JWT
- OAuth2
- API Key
- Signature
- HMAC
- Rate Limit
- Idempotency

---

## 第三十四篇 文件与办公自动化
### 133. Excel
- Apache POI
- EasyExcel
- Excel 导入
- Excel 导出
- 大文件 Excel
- 流式 Excel
- Excel 模板

### 134. PDF
- PDF 生成
- PDF 解析
- PDF 模板
- PDF 合并
- PDF 拆分

### 135. 图片
- ImageIO
- Thumbnailator
- 图片压缩
- 图片裁剪
- 水印
- OCR

---

## 第三十五篇 工作流
### 136. BPMN
- BPMN
- Process
- Task
- Gateway
- Event
- Sequence Flow

### 137. Flowable
- 流程部署
- 流程启动
- 用户任务
- 服务任务
- 网关
- 会签
- 或签
- 流程变量
- 历史任务

---

## 第三十六篇 规则引擎
### 138. Drools
- Rule
- Fact
- Working Memory
- Agenda
- DRL
- Decision Table

### 139. 业务规则
- 规则管理
- 动态规则
- 规则版本
- 规则发布
- 规则执行

---

## 第三十七篇 大数据
### 140. Hadoop
- HDFS
- MapReduce
- YARN

### 141. Hive
- Hive
- HQL
- Data Warehouse
- Partition
- Bucket

### 142. Spark
- Spark
- RDD
- DataFrame
- Dataset
- Spark SQL
- Spark Streaming

### 143. Flink
- Flink
- DataStream
- Table API
- SQL
- Window
- State
- Checkpoint
- Exactly Once

---

## 第三十八篇 消息与流处理
### 144. Kafka
- Producer
- Consumer
- Topic
- Partition
- Offset
- Consumer Group
- Replication
- ISR

### 145. Kafka Streams
- Stream
- KTable
- Processor
- State Store
- Window

### 146. RocketMQ
- Producer
- Consumer
- Topic
- Tag
- 顺序消息
- 延迟消息
- 事务消息

---

## 第三十九篇 GraphQL
### 147. GraphQL
- Schema
- Query
- Mutation
- Subscription
- Resolver
- DataFetcher
- Scalar
- Object Type
- Interface
- Union
- Input
- Directive

---

## 第四十篇 AI + Java
### 148. AI 基础
- 人工智能
- Machine Learning
- Deep Learning
- LLM
- Generative AI
- AIGC

### 149. 大语言模型
- Transformer
- Token
- Context Window
- Prompt
- Temperature
- Top-P
- Embedding
- Function Calling

### 150. Spring AI
- Spring AI
- ChatClient
- ChatModel
- Prompt
- Prompt Template
- Structured Output
- Embedding
- Vector Store

### 151. RAG
- RAG
- Document
- Document Loader
- Text Splitter
- Embedding
- Vector Database
- Similarity Search
- Retriever
- Reranker
- Context
- Prompt

### 152. 向量数据库
- Milvus
- Qdrant
- Weaviate
- Chroma
- pgvector
- Elasticsearch Vector Search
- OpenSearch Vector Search

### 153. AI Agent
- Agent
- Tool
- Tool Calling
- Function Calling
- Agent Memory
- Planning
- Reasoning
- Workflow Agent
- Multi-Agent

### 154. MCP
- Model Context Protocol
- MCP Client
- MCP Server
- MCP Tool
- MCP Resource
- MCP Prompt
- MCP Transport

---

## 第四十一篇 Java 架构设计
### 155. 软件架构
- 分层架构
- 三层架构
- N 层架构
- MVC
- MVP
- MVVM
- 六边形架构
- Clean Architecture
- Onion Architecture

### 156. 微服务架构
- 服务拆分
- 服务边界
- API Gateway
- 服务注册
- 服务发现
- 配置中心
- 服务调用
- 消息驱动
- 分布式事务
- 分布式锁
- 服务治理

### 157. 领域驱动设计
- DDD
- Entity
- Value Object
- Aggregate
- Repository
- Domain Service
- Application Service
- Domain Event
- Bounded Context
- Context Mapping

### 158. CQRS
- Command
- Query
- Command Model
- Query Model
- Event
- Event Store

### 159. Event Sourcing
- Event
- Event Store
- Aggregate
- Event Replay
- Snapshot

---

## 第四十二篇 设计模式
### 160. 创建型
- 单例模式
- 工厂模式
- 抽象工厂
- 建造者
- 原型

### 161. 结构型
- 适配器
- 装饰器
- 代理
- 外观
- 桥接
- 组合
- 享元

### 162. 行为型
- 策略
- 模板方法
- 责任链
- 观察者
- 状态
- 命令
- 迭代器
- 中介者
- 备忘录
- 访问者
- 解释器

### 163. 企业级模式
- DAO
- DTO
- VO
- BO
- Service
- Repository
- Factory
- Specification
- Unit of Work
- Dependency Injection

---

## 第四十三篇 性能优化
### 164. Java 性能
- CPU
- 内存
- GC
- 线程
- 锁
- IO
- 网络
- 数据库

### 165. JVM 性能
- Heap
- Stack
- Metaspace
- GC
- JIT
- Escape Analysis
- JIT Compilation

### 166. 数据库性能
- SQL 优化
- 索引优化
- 慢 SQL
- 连接池
- 分库分表
- 读写分离

### 167. Web 性能
- HTTP
- Keep-Alive
- Connection Pool
- CDN
- Cache
- Compression
- Async
- Batch

---

## 第四十四篇 高并发架构
### 168. 高并发基础
- QPS
- TPS
- RT
- Throughput
- Concurrency

### 169. 高并发技术
- 缓存
- 异步
- 消息队列
- 限流
- 熔断
- 降级
- 分库分表
- 读写分离
- 数据分片
- CDN

### 170. 秒杀系统
- 流量削峰
- Redis
- MQ
- 限流
- 防超卖
- 幂等
- 分布式锁

---

## 第四十五篇 安全
### 171. Web 安全
- XSS
- CSRF
- SQL Injection
- SSRF
- XXE
- 文件上传漏洞
- 路径遍历
- 命令注入

### 172. 密码学
- MD5
- SHA
- HMAC
- AES
- DES
- RSA
- ECC
- Base64
- 数字签名
- 数字证书

### 173. 身份认证
- Session
- Cookie
- JWT
- OAuth2
- OpenID Connect
- SSO
- MFA

---

## 第四十六篇 Java 企业级项目实战
### 174. 项目基础架构
- 项目分层
- Controller
- Service
- Repository
- Mapper
- Entity
- DTO
- VO
- Converter

### 175. 通用能力
- 统一响应
- 统一异常
- 参数校验
- 日志
- 操作日志
- 审计
- 权限
- 数据字典
- 文件管理

### 176. 企业功能
- 用户
- 角色
- 权限
- 菜单
- 部门
- 岗位
- 字典
- 参数配置
- 登录
- 消息
- 通知
- 操作日志

---

## 第四十七篇 项目工程化
### 177. 项目结构
- 单模块
- 多模块
- Maven Multi Module
- Domain
- Application
- Infrastructure
- Interfaces

### 178. 代码规范
- 命名规范
- 注释规范
- 异常规范
- 日志规范
- API 规范
- 数据库规范
- Git 规范

### 179. Code Review
- PR
- Review
- 静态分析
- SonarQube
- Code Smell
- Technical Debt

---

## 第四十八篇 源码分析
### 180. JDK 源码
- ArrayList
- LinkedList
- HashMap
- ConcurrentHashMap
- ThreadPoolExecutor
- CompletableFuture
- ReentrantLock

### 181. Spring 源码
- IoC
- BeanFactory
- ApplicationContext
- BeanDefinition
- BeanPostProcessor
- AOP
- Transaction

### 182. Spring Boot 源码
- SpringApplication
- 启动流程
- 自动配置
- Starter
- 条件装配
- Configuration Properties

### 183. MyBatis 源码
- SqlSession
- Executor
- MapperProxy
- StatementHandler
- ParameterHandler
- ResultSetHandler

### 184. Spring MVC 源码
- DispatcherServlet
- HandlerMapping
- HandlerAdapter
- HandlerMethod
- ArgumentResolver
- ReturnValueHandler

### 185. Spring Security 源码
- FilterChain
- Authentication
- SecurityContext
- Authorization

---

## 第四十九篇 Java 常见问题
### 186. Java 基础面试
- == 与 equals
- hashCode
- String
- 基本数据类型与包装类
- final
- static
- abstract
- interface
- 重载与重写
- 异常体系
- 泛型
- 反射
- 注解
- 值传递与引用传递
- 深拷贝与浅拷贝
- Object 类方法
- Java 8 新特性
- BigDecimal 精度

### 187. 集合面试
- 集合框架总览
- HashMap
- ConcurrentHashMap
- ArrayList
- LinkedList
- HashSet
- TreeMap
- LinkedHashMap 与 LRU
- fail-fast 与 fail-safe
- CopyOnWriteArrayList
- Queue 队列

### 188. 并发面试
- 线程基础
- synchronized
- volatile
- CAS
- AQS
- Lock
- ThreadLocal
- ThreadPoolExecutor
- CompletableFuture
- 原子类
- 并发工具类
- 死锁
- happens-before

### 189. JVM 面试
- JVM 内存结构
- 对象创建与内存布局
- GC
- 垃圾收集器
- 类加载
- 双亲委派
- G1
- ZGC
- 引用类型
- OOM
- JVM 调优
- 逃逸分析

### 190. Spring 面试
- IoC
- DI
- AOP
- Bean 生命周期
- Bean 作用域
- BeanFactory 与 ApplicationContext
- 循环依赖
- 事务
- 自动配置
- @Autowired 与 @Resource
- FactoryBean 与 BeanFactory
- Spring 事件机制
- Spring 设计模式

### 191. Spring Boot 面试
- 自动配置
- Starter
- 配置文件
- Actuator
- 启动流程
- 核心注解
- Spring Boot 3 变化

### 192. Spring Cloud 面试
- 微服务与 CAP
- Nacos
- Gateway
- Feign
- LoadBalancer
- CircuitBreaker
- Sentinel 限流
- 分布式事务
- 链路追踪
- 服务雪崩

### 193. Redis 面试
- 数据结构
- 底层数据结构
- 持久化
- 过期策略与淘汰策略
- 缓存问题
- 分布式锁
- 集群
- Redis 事务与 Lua
- 大 key 与热 key

### 194. MySQL 面试
- 存储引擎
- 索引
- B+Tree
- MVCC
- 事务
- 锁
- 日志与两阶段提交
- SQL 优化
- 主从复制
- 分库分表
## 第五十篇 综合项目实战
建议最终至少完成以下项目。

## 项目一：Java 基础项目
- 学生成绩管理系统
- 命令行
- 集合
- IO
- 文件存储

## 项目二：Java Web
- 用户管理系统
- Servlet
- JDBC
- MySQL

## 项目三：Spring Boot
- 企业员工管理系统
- Spring Boot
- MyBatis
- MySQL
- Redis
- Security

## 项目四：Spring Boot + Vue
- 企业管理平台
- RBAC
- JWT
- 文件管理
- Excel
- 操作日志

## 项目五：消息队列
- 订单系统
- RabbitMQ / Kafka
- 异步处理
- 重试
- 死信

## 项目六：微服务
```plain
Gateway
   ↓
User Service
Order Service
Product Service
Payment Service
   ↓
Nacos
   ↓
Redis
MySQL
RabbitMQ/Kafka
```

## 项目七：高并发
- 秒杀系统
- Redis
- MQ
- 分布式锁
- 限流
- 熔断
- 降级

## 项目八：数据平台
- Spring Boot
- Oracle / MySQL
- Redis
- Elasticsearch
- Kafka
- 大屏
- 数据分析

## 项目九：AI 应用
- Spring Boot
- Spring AI
- DeepSeek / Qwen / OpenAI
- RAG
- Elasticsearch / Vector DB
- Agent
- MCP

## 项目十：博客内容管理系统（新增落地项目）
- Spring Boot
- MyBatis-Plus
- Redis 缓存（详情/计数/热门榜）
- Elasticsearch 全文搜索
- 评论审核

## 项目十一：在线考试系统（新增落地项目）
- Spring Boot
- MyBatis-Plus
- Redis
- 随机组卷
- 自动判分
- 防作弊

## 项目十二：医院预约挂号系统（新增落地项目）
- Spring Boot
- Redis
- Redisson 分布式锁
- MQ
- 号源池 / 定时放号
- 预约状态机

## 项目十三：酒店预订管理系统（新增落地项目）
- Spring Boot
- Redis
- 分布式锁
- 房态日历
- 订单状态机

## 项目十四：短链接服务（新增落地项目）
- Spring Boot
- Redis
- DB 号段发号器
- 布隆过滤器
- 302 重定向
- PV/UV 统计

## 项目十五：任务协作看板系统（新增落地项目）
- Spring Boot
- WebSocket
- RBAC
- 看板 / 列表 / 卡片模型
- 拖拽状态流转

## 项目十六：会员积分与营销系统（新增落地项目）
- Spring Boot
- MySQL
- Redis
- 积分流水 / 余额一致性
- 签到日历
- 积分排行榜

## 项目十七：企业网盘系统（新增落地项目）
- Spring Boot
- MinIO
- 分片上传 / 断点续传 / 秒传
- 预签名 URL
- 分享链接
- 回收站

## 项目十八：企业即时通讯系统（新增落地项目）
- Spring Boot
- WebSocket
- 离线消息
- 已读回执
- 在线状态

## 项目十九：工单客服系统（新增落地项目）
- Spring Boot
- 状态机
- SLA 时效管理
- 智能分派
- 满意度评价

---

## 最终建议的知识库目录结构
如果你准备真正开始**一个章节一个章节编写 Markdown 文档**，我强烈建议最终采用下面这种目录：

```plain
Java-学习知识库/
│
├── 00-Java学习路线/
│
├── 01-Java语言基础/
│   ├── 01-变量与数据类型.md
│   ├── 02-运算符.md
│   ├── 03-流程控制.md
│   └── ...
│
├── 02-Java面向对象/
│
├── 03-Java核心API/
│
├── 04-Java集合/
│
├── 05-Java泛型/
│
├── 06-Java函数式编程/
│
├── 07-JavaIO/
│
├── 08-Java并发/
│
├── 09-JVM/
│
├── 10-Java反射/
│
├── 11-Java模块化/
│
├── 12-JDBC/
│
├── 13-MySQL/
│
├── 14-JPA-Hibernate/
│
├── 15-MyBatis/
│
├── 16-Spring/
│
├── 17-SpringMVC/
│
├── 18-SpringBoot/
│
├── 19-SpringSecurity/
│
├── 20-SpringData/
│
├── 21-SpringCache/
│
├── 22-RabbitMQ/
│
├── 23-Kafka/
│
├── 24-Redis/
│
├── 25-Elasticsearch/
│
├── 26-SpringCloud/
│
├── 27-Nacos/
│
├── 28-Gateway/
│
├── 29-OpenFeign/
│
├── 30-分布式系统/
│
├── 31-分布式事务/
│
├── 32-高并发/
│
├── 33-Linux/
│
├── 34-Docker/
│
├── 35-Kubernetes/
│
├── 36-Git/
│
├── 37-DevOps/
│
├── 38-测试/
│
├── 39-API设计/
│
├── 40-工作流/
│
├── 41-规则引擎/
│
├── 42-大数据/
│
├── 43-GraphQL/
│
├── 44-SpringAI/
│
├── 45-RAG/
│
├── 46-Agent/
│
├── 47-MCP/
│
├── 48-设计模式/
│
├── 49-DDD/
│
├── 50-架构设计/
│
├── 51-性能优化/
│
├── 52-安全/
│
├── 53-源码分析/
│
├── 54-企业级项目实战/
│
└── 55-Java面试/
```

## 如果目标是“真正完整的 Java 文档体系”
我建议把它进一步拆成 **6 个学习层级**：

```plain
Level 1
Java 基础
    ↓
Level 2
Java SE
集合 / IO / 泛型 / Stream / 并发 / JVM
    ↓
Level 3
Java 企业开发
JDBC / MySQL / MyBatis / Spring / Spring MVC / Spring Boot
    ↓
Level 4
Java 高级开发
Redis / MQ / Elasticsearch / Security / 分布式 / 微服务
    ↓
Level 5
Java 架构
高并发 / 高可用 / DDD / CQRS / 微服务 / 云原生 / DevOps
    ↓
Level 6
现代 Java
Java 21+ / Virtual Threads / AOT / Native
Spring AI / RAG / Agent / MCP
```
