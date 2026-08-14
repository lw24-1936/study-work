---
title: Spring Boot 集成定时任务详解
created: 2026-08-09
updated: 2026-08-09
type: integration
tags: [spring-boot, scheduled, quartz, thread-pool]
---

> 整理日期：2026-08-09

## 目录

1. [概述](#1-概述)
2. [@Scheduled 注解](#2-scheduled-注解)
3. [线程池配置](#3-线程池配置)
4. [Cron 表达式](#4-cron-表达式)
5. [动态定时任务](#5-动态定时任务)
6. [分布式定时任务](#6-分布式定时任务)
7. [Quartz 集成](#7-quartz-集成)
8. [XXL-JOB 集成](#8-xxl-job-集成)
9. [应用场景实战](#9-应用场景实战)
10. [最佳实践与踩坑记录](#10-最佳实践与踩坑记录)

---

## 1. 概述

定时任务是后端开发的基础能力，Spring Boot 提供了三层方案：

| 方案 | 适用场景 | 复杂度 |
|------|----------|--------|
| `@Scheduled` | 单机简单定时，固定频率执行 | 低 |
| TaskScheduler 动态调度 | 单机，需要运行时增删改任务 | 中 |
| Quartz | 单机/集群，复杂调度策略，任务持久化 | 高 |
| XXL-JOB / Elastic-Job | 分布式，可视化管控，分片执行 | 中-高 |

本文覆盖全部四种方案，从最简 `@Scheduled` 到 XXL-JOB 分布式调度。

---

## 2. @Scheduled 注解

### 2.1 启用定时任务

```java
@SpringBootApplication
@EnableScheduling  // 必须在配置类上启用
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 2.2 三种调度方式

```java
@Component
public class SimpleScheduledTasks {

    // ===== 1. fixedRate：固定频率，以上一次【开始】时间计时 =====
    @Scheduled(fixedRate = 5000) // 每 5 秒执行一次
    public void fixedRateTask() {
        System.out.println("fixedRate: " + LocalTime.now());
    }

    // ===== 2. fixedDelay：固定延迟，以上一次【结束】时间计时 =====
    @Scheduled(fixedDelay = 5000) // 上次结束后等 5 秒再执行
    public void fixedDelayTask() throws InterruptedException {
        System.out.println("fixedDelay 开始: " + LocalTime.now());
        Thread.sleep(2000); // 模拟耗时 2 秒
        System.out.println("fixedDelay 结束: " + LocalTime.now());
        // 实际间隔 = 2秒(执行时间) + 5秒(延迟) = 7秒
    }

    // ===== 3. cron：Cron 表达式，灵活精确 =====
    @Scheduled(cron = "0 0 3 * * ?") // 每天凌晨 3 点
    public void cronTask() {
        System.out.println("cron 执行: " + LocalDateTime.now());
    }

    // ===== fixedRate + initialDelay：首次延迟 =====
    @Scheduled(fixedRate = 60000, initialDelay = 30000) // 30 秒后首次执行，之后每 60 秒
    public void delayedStartTask() {
        System.out.println("首次延迟后执行: " + LocalTime.now());
    }
}
```

### 2.3 fixedRate vs fixedDelay 对比

```
fixedRate（固定频率）：
  开始 → 5s → 开始 → 5s → 开始
  （不管上次是否结束，按开始时间算间隔）

  如果任务执行 7 秒：
  开始 ────7s────┤
         开始 ────7s────┤   ← 两个任务并行执行
                开始 ────7s────┤

fixedDelay（固定延迟）：
  开始 ──结束──→ 5s → 开始 ──结束──→ 5s → 开始
  （等上次结束后才开始计时）

  如果任务执行 7 秒：
  开始 ────7s──── 结束 → 5s → 开始 ────7s──── 结束
  （永远不会并行）
```

### 2.4 从配置文件读取配置

```java
@Component
public class ConfigurableScheduledTask {

    // 从 application.yml 读取
    @Scheduled(cron = "${task.clean.cron:0 0 2 * * ?}")
    public void cleanTask() {
        System.out.println("清理任务执行");
    }

    @Scheduled(fixedRateString = "${task.sync.interval:30000}")
    public void syncTask() {
        System.out.println("同步任务执行");
    }
}
```

```yaml
# application.yml
task:
  clean:
    cron: 0 0 2 * * ?      # 每天凌晨 2 点，可被运维覆盖
  sync:
    interval: 30000          # 30 秒
```

---

## 3. 线程池配置

### 3.1 默认行为的隐患

Spring Boot 默认用单线程执行所有 `@Scheduled` 任务。如果一个任务阻塞，其他所有定时任务都会延迟。

```java
// 问题演示：
@Scheduled(fixedRate = 1000)
public void task1() throws InterruptedException {
    Thread.sleep(5000); // 阻塞 5 秒
}

@Scheduled(fixedRate = 1000)
public void task2() {
    System.out.println("task2 也被阻塞，无法每秒执行");
}
```

### 3.2 配置线程池

```java
@Configuration
@EnableScheduling
public class SchedulingConfig implements SchedulingConfigurer {

    @Override
    public void configureTasks(ScheduledTaskRegistrar registrar) {
        registrar.setScheduler(taskScheduler());
    }

    @Bean("taskScheduler")
    public ThreadPoolTaskScheduler taskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();

        // 核心参数
        scheduler.setPoolSize(10);                   // 核心线程数
        scheduler.setThreadNamePrefix("scheduled-"); // 线程名前缀，便于日志排查
        scheduler.setAwaitTerminationSeconds(60);    // 关闭时等待任务完成
        scheduler.setWaitForTasksToCompleteOnShutdown(true); // 优雅关闭
        scheduler.setRejectedExecutionHandler(
                new ThreadPoolExecutor.CallerRunsPolicy()); // 拒绝策略：主线程执行

        return scheduler;
    }
}
```

### 3.3 对不同任务分配不同线程池

```java
@Configuration
@EnableScheduling
public class MultiPoolSchedulingConfig {

    // 快速任务线程池
    @Bean("fastTaskScheduler")
    public ThreadPoolTaskScheduler fastTaskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(5);
        scheduler.setThreadNamePrefix("fast-");
        return scheduler;
    }

    // 慢速任务线程池
    @Bean("slowTaskScheduler")
    public ThreadPoolTaskScheduler slowTaskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(3);
        scheduler.setThreadNamePrefix("slow-");
        return scheduler;
    }

    @Override
    public void configureTasks(ScheduledTaskRegistrar registrar) {
        // 默认使用快速池
        registrar.setScheduler(fastTaskScheduler());
    }
}

@Component
public class MultiPoolTasks {

    // 用慢速池执行
    @Scheduled(fixedRate = 60000)
    public void slowReportTask() {
        // 耗时较长的报表生成...
    }
}
```

对于需要指定不同线程池的任务，可以通过 `TaskScheduler` 手动调度（见第 5 节动态定时任务）。

---

## 4. Cron 表达式

### 4.1 语法结构

```
 ┌──── 秒（0-59）
 │ ┌──── 分钟（0-59）
 │ │ ┌──── 小时（0-23）
 │ │ │ ┌──── 日期（1-31）
 │ │ │ │ ┌──── 月份（1-12）
 │ │ │ │ │ ┌──── 星期（0-7，0 和 7 都是周日）
 │ │ │ │ │ │
 * * * * * *
```

Spring 的 Cron 是 **6 位**（多了秒），允许的字符：

| 字符 | 含义 | 示例 |
|------|------|------|
| `*` | 所有值 | `* * * * * *` 每秒 |
| `?` | 不指定（日期/星期二选一） | `0 0 3 * * ?` |
| `-` | 范围 | `0 0 9-18 * * ?` 9 点到 18 点 |
| `,` | 列举 | `0 0 9,13,18 * * ?` 9 点、13 点、18 点 |
| `/` | 步长 | `0/5 * * * * ?` 每 5 秒 |
| `L` | 最后 | `0 0 0 L * ?` 每月最后一天 |
| `W` | 最近工作日 | `0 0 0 1W * ?` 1 号最近工作日 |
| `#` | 第几个 | `0 0 0 ? * 2#3` 每月第 3 个周一 |

### 4.2 常用表达式速查

```yaml
# 每 5 秒
cron: "0/5 * * * * ?"

# 每 5 分钟
cron: "0 0/5 * * * ?"

# 每小时整点
cron: "0 0 * * * ?"

# 每天凌晨 2 点
cron: "0 0 2 * * ?"

# 每天上午 9 点和下午 6 点
cron: "0 0 9,18 * * ?"

# 每周一上午 10 点
cron: "0 0 10 ? * MON"

# 每月 1 号凌晨 1 点
cron: "0 0 1 1 * ?"

# 每月最后一天 23:59
cron: "0 59 23 L * ?"

# 工作日（周一至周五）上午 9 点
cron: "0 0 9 ? * MON-FRI"

# 每 30 分钟，工作时间（9-18 点）
cron: "0 0/30 9-18 * * MON-FRI"
```

### 4.3 在线验证

写复杂表达式时建议用在线工具验证：https://cron.qqe2.com/

---

## 5. 动态定时任务

`@Scheduled` 注解的值是编译期固定的。当需要运行时启停或修改周期时，用 `ThreadPoolTaskScheduler` 动态调度。

### 5.1 核心 API

```java
@Component
public class DynamicScheduleManager {

    @Autowired
    private ThreadPoolTaskScheduler taskScheduler;

    // 记录所有已注册的任务
    private final Map<String, ScheduledFuture<?>> futures = new ConcurrentHashMap<>();

    /**
     * 启动一个定时任务。
     */
    public void startTask(String taskId, Runnable task, String cron) {
        // 如果已存在，先停止
        stopTask(taskId);

        ScheduledFuture<?> future = taskScheduler.schedule(task,
                new CronTrigger(cron));

        futures.put(taskId, future);
        System.out.println("任务已启动: " + taskId);
    }

    /**
     * 以固定频率启动。
     */
    public void startFixedRateTask(String taskId, Runnable task, long millis) {
        stopTask(taskId);
        ScheduledFuture<?> future = taskScheduler.scheduleAtFixedRate(task, millis);
        futures.put(taskId, future);
    }

    /**
     * 停止一个任务。
     */
    public void stopTask(String taskId) {
        ScheduledFuture<?> future = futures.remove(taskId);
        if (future != null) {
            future.cancel(false); // false: 不中断正在执行的任务
            System.out.println("任务已停止: " + taskId);
        }
    }

    /**
     * 修改任务周期（原地重启）。
     */
    public void rescheduleTask(String taskId, Runnable task, String newCron) {
        stopTask(taskId);
        startTask(taskId, task, newCron);
    }

    /**
     * 列出所有运行中的任务。
     */
    public Set<String> listRunningTasks() {
        return futures.keySet();
    }
}
```

### 5.2 通过 REST 接口启停任务

```java
@RestController
@RequestMapping("/schedule")
public class ScheduleController {

    @Autowired
    private DynamicScheduleManager manager;

    // 启动任务
    @PostMapping("/{taskId}/start")
    public String start(@PathVariable String taskId,
                        @RequestParam String cron) {
        manager.startTask(taskId, () -> {
            System.out.println("[" + taskId + "] 执行: " + LocalDateTime.now());
        }, cron);
        return "任务 " + taskId + " 已启动";
    }

    // 停止任务
    @PostMapping("/{taskId}/stop")
    public String stop(@PathVariable String taskId) {
        manager.stopTask(taskId);
        return "任务 " + taskId + " 已停止";
    }

    // 查看所有任务
    @GetMapping("/list")
    public Set<String> list() {
        return manager.listRunningTasks();
    }
}
```

### 5.3 从数据库加载定时任务

```java
@Component
public class DbBasedScheduleLoader implements ApplicationListener<ApplicationReadyEvent> {

    @Autowired
    private DynamicScheduleManager manager;
    @Autowired
    private ScheduleTaskMapper taskMapper;

    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        List<ScheduleTask> tasks = taskMapper.selectEnabledTasks();

        for (ScheduleTask task : tasks) {
            manager.startTask(task.getId(), () -> {
                // 根据 task.getBeanName() 反射调用业务方法
                executeTask(task);
            }, task.getCronExpression());

            System.out.println("加载任务: " + task.getName());
        }
    }

    private void executeTask(ScheduleTask task) {
        // 通过 ApplicationContext 获取 Bean 并执行
        // ...
    }
}
```

---

## 6. 分布式定时任务

单机定时任务在集群部署时有严重问题：同一个任务在每个节点上都会执行。需要分布式协调，确保同一时刻只有一个节点执行。

### 6.1 问题场景

```
节点A: @Scheduled(cron="0 0 3 * * ?") → 凌晨 3 点执行 ✓
节点B: @Scheduled(cron="0 0 3 * * ?") → 凌晨 3 点执行 ✓ (重复!)
节点C: @Scheduled(cron="0 0 3 * * ?") → 凌晨 3 点执行 ✓ (重复!)
```

### 6.2 方案一：Redis 分布式锁（轻量级）

```java
@Component
public class DistributedScheduledTask {

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    /**
     * 使用 Redis SETNX 确保只有一个节点执行。
     * 适用于任务较少、不要求可观测性的场景。
     */
    @Scheduled(cron = "0 0 3 * * ?")
    public void dailyReport() {
        String lockKey = "schedule:lock:dailyReport";
        String lockValue = getHostName() + ":" + Thread.currentThread().getId();

        // 尝试获取锁，10 分钟自动释放
        Boolean acquired = stringRedisTemplate.opsForValue()
                .setIfAbsent(lockKey, lockValue, 10, TimeUnit.MINUTES);

        if (!Boolean.TRUE.equals(acquired)) {
            System.out.println("其他节点正在执行，跳过");
            return;
        }

        try {
            // ---- 业务逻辑 ----
            System.out.println("生成日报: " + LocalDateTime.now());
        } finally {
            // 释放锁前检查：防止误删其他节点的锁
            String currentValue = stringRedisTemplate.opsForValue().get(lockKey);
            if (lockValue.equals(currentValue)) {
                stringRedisTemplate.delete(lockKey);
            }
        }
    }

    private String getHostName() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException e) {
            return "unknown";
        }
    }
}
```

### 6.3 方案二：Redisson 分布式锁（更健壮）

```java
@Component
public class RedissonScheduledTask {

    @Autowired
    private RedissonClient redissonClient;

    @Scheduled(cron = "0 0 4 * * ?")
    public void syncData() {
        RLock lock = redissonClient.getLock("schedule:lock:syncData");

        // tryLock 获取失败直接返回，不等待
        if (!lock.tryLock()) {
            return; // 其他节点持有锁，跳过
        }

        try {
            // 看门狗自动续期，不担心任务执行过长
            System.out.println("数据同步: " + LocalDateTime.now());
        } finally {
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
```

### 6.4 方案三：ShedLock（专为定时任务设计）

ShedLock 是一个专门解决分布式定时任务的小型库，支持 Redis / MySQL / ZooKeeper 等多种存储。

```xml
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-spring</artifactId>
    <version>5.16.0</version>
</dependency>
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-provider-redis-spring</artifactId>
    <version>5.16.0</version>
</dependency>
```

```java
@SpringBootApplication
@EnableScheduling
@EnableSchedulerLock(defaultLockAtMostFor = "PT10M") // 全局默认锁持有时间
public class Application {
    // ...
}
```

```java
@Component
public class ShedLockTasks {

    /**
     * ShedLock 注解：
     * - name：锁的唯一标识，集群中唯一
     * - lockAtLeastFor：最小锁持有时间，防止时钟不同步导致重复执行
     * - lockAtMostFor：最大锁持有时间，任务执行超时后自动释放
     */
    @Scheduled(cron = "0 0 3 * * ?")
    @SchedulerLock(name = "dailyReport",
            lockAtLeastFor = "PT30S",  // 至少持有 30 秒
            lockAtMostFor = "PT10M")   // 最多持有 10 分钟
    public void dailyReport() {
        System.out.println("执行日报: " + LocalDateTime.now());
    }

    @Scheduled(cron = "0 0/10 * * * ?")
    @SchedulerLock(name = "dataSync", lockAtMostFor = "PT5M")
    public void dataSync() {
        System.out.println("数据同步: " + LocalDateTime.now());
    }
}
```

三种方案对比：

| 方案 | 侵入性 | 可靠性 | 可观测性 | 适用规模 |
|------|--------|--------|----------|----------|
| Redis SETNX | 需手动管理锁 | 一般（需处理锁过期） | 无 | 1-3 个任务 |
| Redisson 锁 | 需手动管理锁 | 高（看门狗续期） | 无 | 3-10 个任务 |
| ShedLock | 一个注解 | 高 | 基础 | 10+ 个任务 |
| XXL-JOB | 需部署调度中心 | 高 | 完善 | 任意规模 |

---

## 7. Quartz 集成

Quartz 是 Java 生态最成熟的定时任务框架，支持任务持久化到数据库、集群部署、任务监听、错过补偿等。

### 7.1 依赖引入

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-quartz</artifactId>
</dependency>
```

### 7.2 定义 Job

```java
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.scheduling.quartz.QuartzJobBean;

/**
 * 定义任务逻辑。
 * QuartzJobBean 自动注入 Spring 上下文。
 */
@Component
public class ReportJob extends QuartzJobBean {

    @Override
    protected void executeInternal(JobExecutionContext context)
            throws JobExecutionException {
        // 从 JobDataMap 获取参数
        String reportType = context.getMergedJobDataMap().getString("reportType");
        System.out.println("生成报表: " + reportType + ", 时间: " + LocalDateTime.now());

        // 业务逻辑...
    }
}
```

### 7.3 配置 Quartz

```java
import org.quartz.*;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class QuartzConfig {

    /**
     * 创建 JobDetail：描述任务本身（做什么）。
     */
    @Bean
    public JobDetail reportJobDetail() {
        return JobBuilder.newJob(ReportJob.class)
                .withIdentity("reportJob")                    // 唯一标识
                .withDescription("日报生成任务")
                .usingJobData("reportType", "daily")          // 传递参数
                .storeDurably()                               // 没有 Trigger 时也保留
                .build();
    }

    /**
     * 创建 Trigger：描述触发规则（什么时候做）。
     */
    @Bean
    public Trigger reportTrigger() {
        return TriggerBuilder.newTrigger()
                .forJob(reportJobDetail())                    // 关联 JobDetail
                .withIdentity("reportTrigger")
                .withDescription("每天凌晨 3 点触发")
                .withSchedule(CronScheduleBuilder.cronSchedule("0 0 3 * * ?")
                        .withMisfireHandlingInstructionDoNothing()) // 错过不补偿
                .build();
    }
}
```

上面的 `application.yml` 配置（使用内存存储）：

```yaml
spring:
  quartz:
    job-store-type: memory         # memory / jdbc
    properties:
      org:
        quartz:
          scheduler:
            instanceName: MyScheduler
            instanceId: AUTO
          threadPool:
            threadCount: 10        # 线程池大小
            threadPriority: 5
```

### 7.4 JDBC 持久化（集群模式）

```yaml
spring:
  quartz:
    job-store-type: jdbc
    jdbc:
      initialize-schema: always    # 首次启动自动建表
    properties:
      org:
        quartz:
          jobStore:
            class: org.quartz.impl.jdbcjobstore.JobStoreTX
            driverDelegateClass: org.quartz.impl.jdbcjobstore.StdJDBCDelegate
            isClustered: true      # 开启集群模式
            clusterCheckinInterval: 20000  # 集群心跳间隔（ms）
```

Quartz JDBC 模式需要创建数据库表，详见 `org/quartz/impl/jdbcjobstore/tables_mysql_innodb.sql`。

### 7.5 运行时管理任务

```java
@Service
public class QuartzJobManager {

    @Autowired
    private Scheduler scheduler;

    /**
     * 动态添加任务。
     */
    public void addJob(String jobName, String cronExpression, String reportType)
            throws SchedulerException {

        JobDetail job = JobBuilder.newJob(ReportJob.class)
                .withIdentity(jobName)
                .usingJobData("reportType", reportType)
                .storeDurably()
                .build();

        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity(jobName + "_trigger")
                .withSchedule(CronScheduleBuilder.cronSchedule(cronExpression))
                .build();

        scheduler.scheduleJob(job, trigger);
    }

    /**
     * 暂停任务。
     */
    public void pauseJob(String jobName) throws SchedulerException {
        scheduler.pauseJob(JobKey.jobKey(jobName));
    }

    /**
     * 恢复任务。
     */
    public void resumeJob(String jobName) throws SchedulerException {
        scheduler.resumeJob(JobKey.jobKey(jobName));
    }

    /**
     * 删除任务。
     */
    public void deleteJob(String jobName) throws SchedulerException {
        scheduler.deleteJob(JobKey.jobKey(jobName));
    }

    /**
     * 修改 Cron 表达式。
     */
    public void updateCron(String jobName, String newCron)
            throws SchedulerException {
        TriggerKey triggerKey = TriggerKey.triggerKey(jobName + "_trigger");
        CronTrigger newTrigger = TriggerBuilder.newTrigger()
                .withIdentity(triggerKey)
                .withSchedule(CronScheduleBuilder.cronSchedule(newCron))
                .build();
        scheduler.rescheduleJob(triggerKey, newTrigger);
    }

    /**
     * 立即执行一次。
     */
    public void triggerNow(String jobName) throws SchedulerException {
        scheduler.triggerJob(JobKey.jobKey(jobName));
    }
}
```

### 7.6 Quartz 集群原理

```
节点 A                 节点 B                 节点 C
   |                      |                      |
   |── 获取数据库行锁 ─────|                      |
   |── 扫描待触发任务 ─────|                      |
   |── 更新任务状态 ───────|                      |
   |── 释放锁 ────────────|                      |
   |── 执行任务 ──────────|── 获取锁 ─────────────|
```

每个节点定时扫描 `QRTZ_TRIGGERS` 表，通过行锁竞争任务执行权。节点故障时，心跳超时后其他节点接管任务。

### 7.7 @Scheduled vs Quartz 选型

| 维度 | @Scheduled | Quartz |
|------|-----------|--------|
| 配置复杂度 | 低，一个注解 | 中，Job + Trigger 配置 |
| 任务持久化 | 不支持 | 支持 MySQL/PG 等 |
| 集群支持 | 需自己加锁 | 内置支持 |
| 错过触发补偿 | 无 | 多种策略 |
| 动态管理 API | 需自己封装 | 内置 Scheduler API |
| 监听器 | 无 | 丰富的 Listener |
| 适用场景 | 简单固定任务 | 复杂调度、需持久化、运维管理 |

---

## 8. XXL-JOB 集成

XXL-JOB 是国产分布式任务调度平台，提供可视化管理界面、任务分片、失败重试、邮件告警等，在国内使用广泛。

### 8.1 架构

```
┌─────────────────┐
│  调度中心 (Admin)  │  Web UI + API
│  端口: 8080       │
└────────┬────────┘
         │ HTTP 调度
    ┌────┴────┬────────┐
    │         │         │
┌───▼──┐ ┌───▼──┐ ┌───▼──┐
│执行器A│ │执行器B│ │执行器C│  应用内嵌
│app #1│ │app #2│ │app #3│
└──────┘ └──────┘ └──────┘
```

### 8.2 依赖与配置

```xml
<dependency>
    <groupId>com.xuxueli</groupId>
    <artifactId>xxl-job-core</artifactId>
    <version>2.4.2</version>
</dependency>
```

```java
@Configuration
public class XxlJobConfig {

    @Bean
    public XxlJobSpringExecutor xxlJobExecutor() {
        XxlJobSpringExecutor executor = new XxlJobSpringExecutor();
        executor.setAdminAddresses("http://127.0.0.1:8080/xxl-job-admin");
        executor.setAppname("my-app");        // 执行器名称
        executor.setIp(null);                  // 自动获取
        executor.setPort(9999);                // 执行器通信端口
        executor.setAccessToken("your_token"); // 安全令牌
        executor.setLogPath("/data/applogs/xxl-job/");
        executor.setLogRetentionDays(30);
        return executor;
    }
}
```

```yaml
# application.yml
xxl:
  job:
    admin:
      addresses: http://127.0.0.1:8080/xxl-job-admin
    executor:
      appname: my-app
      port: 9999
      logpath: /data/applogs/xxl-job/
      logretentiondays: 30
```

### 8.3 编写任务

```java
@Component
public class XxlJobHandlers {

    /**
     * 简单任务。
     * 在 XXL-JOB 管理后台注册 JobHandler = "demoJob"。
     */
    @XxlJob("demoJob")
    public void demoJob() {
        XxlJobHelper.log("开始执行 demoJob: {}", LocalDateTime.now());
        System.out.println("Hello XXL-JOB");
        XxlJobHelper.handleSuccess("执行成功");
    }

    /**
     * 分片任务：多个执行器并行处理数据的不同分片。
     */
    @XxlJob("shardingJob")
    public void shardingJob() {
        // 任务参数：可在管理后台配置
        String param = XxlJobHelper.getJobParam();
        int shardIndex = XxlJobHelper.getShardIndex();  // 当前分片索引
        int shardTotal = XxlJobHelper.getShardTotal();   // 总分片数

        System.out.printf("分片 %d/%d, 参数: %s%n", shardIndex, shardTotal, param);

        // 按 userId 取模，每个分片处理一部分数据
        List<Long> userIds = range(shardIndex, shardTotal, 10000);
        for (Long id : userIds) {
            // 处理该分片的数据...
        }

        XxlJobHelper.handleSuccess();
    }

    /**
     * HTTP 子任务：成功后可触发子任务链。
     */
    @XxlJob("parentJob")
    public void parentJob() {
        System.out.println("父任务执行");
        XxlJobHelper.handleSuccess();
        // 管理后台配置子任务 "childJob"，成功时自动触发
    }
}
```

### 8.4 调度中心路由策略

在 XXL-JOB 管理后台创建任务时可选择：

| 策略 | 说明 |
|------|------|
| 第一个 | 固定选第一个执行器 |
| 最后一个 | 固定选最后一个执行器 |
| 轮询 | 依次分配到不同执行器 |
| 随机 | 随机选择 |
| 一致性 HASH | 相同任务参数路由到同一执行器 |
| 最不经常使用 | 选使用次数最少的 |
| 最近最久未使用 | 选最久没执行的 |
| 故障转移 | 主执行器故障时切到备用 |
| 忙碌转移 | 主执行器忙时切到空闲执行器 |
| 分片广播 | 所有执行器都执行，用分片参数区分 |

### 8.5 XXL-JOB vs Quartz 选型

| 维度 | Quartz | XXL-JOB |
|------|--------|---------|
| 管理界面 | 无 | 可视化 Web UI |
| 部署复杂度 | 嵌入式，零部署 | 需部署调度中心 |
| 任务分片 | 不支持 | 内置分片广播 |
| 失败重试 | 需自己实现 | 内置 + 邮件告警 |
| 任务依赖 | 需自己编排 | 子任务链 |
| 维护状态 | 成熟稳定 | 活跃更新 |
| 适用场景 | 传统企业应用 | 微服务架构、需运维管控 |

---

## 9. 应用场景实战

### 场景 1：订单超时自动取消

```java
@Component
public class OrderTimeoutTask {

    @Autowired
    private OrderMapper orderMapper;

    /**
     * 每分钟扫描一次未支付订单，超时 30 分钟自动取消。
     */
    @Scheduled(fixedRate = 60000)
    public void cancelTimeoutOrders() {
        LocalDateTime deadline = LocalDateTime.now().minusMinutes(30);

        // 查询超时未支付订单
        List<Order> orders = orderMapper.selectTimeoutOrders(
                OrderStatus.UNPAID, deadline);

        for (Order order : orders) {
            order.setStatus(OrderStatus.CANCELLED);
            order.setCancelTime(LocalDateTime.now());
            orderMapper.updateById(order);

            System.out.println("订单取消: " + order.getId());
        }
    }
}
```

注：对于需要精确延迟触发的场景，用 Redisson 延迟队列（见 [[spring-boot-redisson]] 场景 5）或 RocketMQ 延迟消息更合适。

### 场景 2：定时数据同步

```java
@Component
public class DataSyncTask {

    @Autowired
    private RemoteApiClient remoteClient;
    @Autowired
    private DataSyncService syncService;

    /**
     * 每小时从外部 API 同步一次数据。
     */
    @Scheduled(cron = "${sync.cron:0 0 * * * ?}")
    public void syncFromRemote() {
        long start = System.currentTimeMillis();

        try {
            List<DataDTO> data = remoteClient.fetchUpdatedData();
            int synced = syncService.batchSave(data);
            System.out.printf("数据同步完成: %d 条, 耗时 %dms%n",
                    synced, System.currentTimeMillis() - start);
        } catch (Exception e) {
            // 记录失败日志，下次重试
            System.err.println("数据同步失败: " + e.getMessage());
        }
    }
}
```

### 场景 3：健康检查与告警

```java
@Component
public class HealthCheckTask {

    @Autowired
    private RestTemplate restTemplate;

    private final List<String> services = List.of(
            "http://user-service:8081/actuator/health",
            "http://order-service:8082/actuator/health",
            "http://pay-service:8083/actuator/health"
    );

    /**
     * 每 30 秒检查一次下游服务健康状态。
     */
    @Scheduled(fixedRate = 30000)
    public void checkServiceHealth() {
        for (String url : services) {
            try {
                ResponseEntity<String> resp = restTemplate.getForEntity(url, String.class);
                if (!resp.getStatusCode().is2xxSuccessful()) {
                    sendAlert("服务异常", url + " 返回 " + resp.getStatusCode());
                }
            } catch (Exception e) {
                sendAlert("服务不可达", url + " - " + e.getMessage());
            }
        }
    }

    private void sendAlert(String title, String detail) {
        // 发邮件 / 钉钉 / 企微...
        System.err.println("告警: " + title + " - " + detail);
    }
}
```

### 场景 4：缓存预热

```java
@Component
public class CacheWarmUpTask {

    @Autowired
    private ProductService productService;
    @Autowired
    private StringRedisTemplate redisTemplate;

    /**
     * 每天凌晨 4 点预热热点数据到 Redis。
     */
    @Scheduled(cron = "0 0 4 * * ?")
    public void warmUpHotData() {
        System.out.println("开始缓存预热...");

        // 加载 Top 1000 商品
        List<Product> hotProducts = productService.getHotProducts(1000);
        for (Product p : hotProducts) {
            String key = "cache:product:" + p.getId();
            // TTL 加随机值（300-420 分钟），防止缓存雪崩
            long ttl = (300 + ThreadLocalRandom.current().nextInt(120)) * 60;
            redisTemplate.opsForValue().set(key, p, ttl, TimeUnit.SECONDS);
        }

        System.out.println("缓存预热完成: " + hotProducts.size() + " 条");
    }
}
```

### 场景 5：定时生成统计报表

```java
@Component
public class ReportGenerateTask {

    @Autowired
    private OrderMapper orderMapper;
    @Autowired
    private ReportMailService mailService;

    /**
     * 每天凌晨 1 点生成前一日销售报表并邮件发送。
     */
    @Scheduled(cron = "0 0 1 * * ?")
    public void generateDailyReport() {
        LocalDate yesterday = LocalDate.now().minusDays(1);

        // 统计数据
        Map<String, Object> stats = orderMapper.dailyStats(yesterday);

        // 生成报表文件
        String reportPath = generateExcelReport(stats, yesterday);

        // 邮件发送
        mailService.sendReport("daily-sales-" + yesterday + ".xlsx", reportPath);

        System.out.println("日报已发送: " + yesterday);
    }
}
```

---

## 10. 最佳实践与踩坑记录

### 10.1 线程池大小设置

```
计算公式：线程数 = 任务数 * 最大并发度

示例：
- 20 个定时任务，每个最多 3 个并发 → 60 线程（上限）
- 实际用 10-20 个线程通常足够（任务间错峰执行）

建议：
- 快速任务（< 1秒）：poolSize = 5-10
- 慢速任务（> 10秒）：单独线程池 + 小 poolSize
```

### 10.2 避免任务堆积

```java
// 问题：任务执行 10 秒，间隔 3 秒 → 任务严重堆积
@Scheduled(fixedRate = 3000)
public void slowTask() throws InterruptedException {
    Thread.sleep(10000);
}

// 解决 1：用 fixedDelay 而非 fixedRate
@Scheduled(fixedDelay = 3000)

// 解决 2：加并发控制
private final Semaphore semaphore = new Semaphore(1);

@Scheduled(fixedRate = 3000)
public void controlledTask() {
    if (!semaphore.tryAcquire()) {
        System.out.println("上次任务未完成，跳过本次");
        return;
    }
    try {
        Thread.sleep(10000);
    } finally {
        semaphore.release();
    }
}
```

### 10.3 优雅关闭

```java
@Configuration
public class GracefulShutdownConfig {

    @Bean
    public ThreadPoolTaskScheduler taskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(10);

        // 应用关闭时等待任务完成
        scheduler.setWaitForTasksToCompleteOnShutdown(true);
        scheduler.setAwaitTerminationSeconds(120); // 最多等 2 分钟

        return scheduler;
    }
}
```

### 10.4 异常处理

```java
// 问题：@Scheduled 方法抛出异常会导致后续任务停止
@Scheduled(fixedRate = 5000)
public void riskyTask() {
    throw new RuntimeException("异常后此任务不再执行");
}

// 解决：内部 try-catch
@Scheduled(fixedRate = 5000)
public void safeTask() {
    try {
        // 业务逻辑
        throw new RuntimeException("模拟异常");
    } catch (Exception e) {
        System.err.println("任务执行异常: " + e.getMessage());
        // 记录日志、发告警...
    }
}

// 或全局异常处理
@Configuration
public class SchedulingErrorHandler implements ErrorHandler {
    @Override
    public void handleError(Throwable t) {
        System.err.println("定时任务全局异常: " + t.getMessage());
    }
}
```

### 10.5 分布式定时任务的锁粒度

```java
// 问题：锁粒度太粗，所有定时任务共用一把锁
@Scheduled(cron = "0 0 3 * * ?")
public void taskA() {
    if (!redisLock.tryLock("schedule:global")) return; // 影响 taskB
}

// 正确：每个任务独立锁
@Scheduled(cron = "0 0 3 * * ?")
public void taskA() {
    if (!redisLock.tryLock("schedule:lock:taskA")) return;
}

@Scheduled(cron = "0 0 4 * * ?")
public void taskB() {
    if (!redisLock.tryLock("schedule:lock:taskB")) return;
}
```

### 10.6 常见问题速查

| 问题 | 原因 | 解决 |
|------|------|------|
| 定时任务不执行 | 未加 `@EnableScheduling` 或 `@Component` | 检查注解 |
| 任务执行越来越慢 | `fixedRate` + 任务耗时 > 间隔 → 堆积 | 换 `fixedDelay` 或加并发控制 |
| 任务只执行一次 | 方法抛出未捕获异常 | 加 try-catch |
| 集群所有节点都执行 | 未加分布式锁 | 用 ShedLock / Redisson 锁 |
| 修改 Cron 不生效 | `@Scheduled` 值编译期固定 | 改用 `Trigger` 动态调度 |
| Quartz 任务重复执行 | 集群时间不同步 | 配置 NTP 时间同步 |
| XXL-JOB 调度中心连不上执行器 | IP/端口不通 | 检查防火墙 `executor.port` |
| 应用关闭时任务被中断 | 未配置优雅关闭 | 设 `waitForTasksToCompleteOnShutdown` |

### 10.7 生产环境 Checklist

- [ ] 配置了线程池（非默认单线程）
- [ ] `@Scheduled` 方法内部有 try-catch
- [ ] 集群部署时使用了分布式锁 / ShedLock / XXL-JOB
- [ ] 配置了优雅关闭（`waitForTasksToCompleteOnShutdown`）
- [ ] Cron 表达式经过在线工具验证
- [ ] 任务执行日志有记录，方便排查
- [ ] 慢任务和快任务用了不同线程池
- [ ] 关键任务配置了失败告警

---

## 总结

定时任务选型路线图：

```
1 个应用、简单固定任务
  → @Scheduled + 线程池配置

1 个应用、需要运行时启停改周期
  → ThreadPoolTaskScheduler 动态调度

多个实例、轻量分布式
  → @Scheduled + ShedLock

多个实例、任务需持久化到 DB
  → Quartz JDBC 集群模式

微服务架构、需要可视化管控
  → XXL-JOB / Elastic-Job
```

配合 [[spring-boot-redis]] 做分布式锁，[[spring-boot-redisson]] 做更健壮的锁和延迟队列，可以覆盖绝大多数定时任务场景。

---

## 参考链接

- [Spring Scheduling 官方文档](https://docs.spring.io/spring-framework/reference/integration/scheduling.html)
- [ShedLock 官方文档](https://github.com/lukas-krecan/ShedLock)
- [Quartz 官方文档](http://www.quartz-scheduler.org/documentation/)
- [XXL-JOB 官方文档](https://www.xuxueli.com/xxl-job/)
- [Cron 表达式在线验证](https://cron.qqe2.com/)
