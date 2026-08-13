---
title: JVM 调优
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, jvm, tuning, performance, oom, memory-leak]
---

# JVM 调优

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [调优思路与方法论](#调优思路与方法论)
- [堆内存调优](#堆内存调优)
- [栈内存调优](#栈内存调优)
- [Metaspace 调优](#metaspace-调优)
- [GC 日志分析](#gc-日志分析)
- [Heap Dump 分析](#heap-dump-分析)
- [Thread Dump 分析](#thread-dump-分析)
- [CPU 飙高排查](#cpu-飙高排查)
- [内存泄漏排查](#内存泄漏排查)
- [内存溢出（OOM）排查](#内存溢出oom排查)
- [死锁排查](#死锁排查)
- [常用 JVM 参数速查](#常用-jvm-参数速查)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JVM 调优不是改一个参数就能解决所有问题——它是一套系统方法论：发现问题（监控+日志）→ 定位瓶颈（Dump+分析）→ 调整参数（JVM+应用）→ 验证效果。核心目标：**减少 Full GC、降低停顿时间、避免 OOM**。

## 调优思路与方法论

```
1. 明确目标
   ├── 提高吞吐量？→ 侧重 Parallel GC
   ├── 降低延迟？→ 侧重 G1/ZGC
   ├── 减少内存？→ 堆大小 + 对象复用
   └── 解决 OOM？→ 分析 Dump 找泄漏点

2. 收集数据
   ├── GC 日志：频率、耗时、回收量
   ├── 堆快照：谁占了内存
   ├── 线程快照：线程在干什么
   └── 系统指标：CPU、内存、磁盘 IO

3. 分析定位
   ├── GC 频繁？→ Eden 太小 / 对象创建太快
   ├── Full GC 频繁？→ 老年代增长过快
   ├── OOM？→ 堆不够 / 内存泄漏
   └── CPU 高？→ 死循环 / 频繁 GC

4. 调整验证
   ├── 改一个参数
   ├── 灰度上线观察
   └── 对比 GC 日志 → 判断效果
```

## 堆内存调优

### 基础参数

```bash
-Xms2g -Xmx2g          # 初始 = 最大（避免动态扩容开销）
-Xmn512m               # 新生代大小（一般 = Xmx × 1/4 ~ 1/3）
-XX:NewRatio=2         # 老年代/新生代 = 2（不设 Xmn 时生效）
-XX:SurvivorRatio=8    # Eden/Survivor = 8（默认）
```

### 何时调大堆

```
现象：GC 频繁（每秒多次）、Full GC 后堆使用率仍很高
动作：增大 -Xmx
风险：堆越大，单次 GC 时间越长 → 换 G1/ZGC
```

### 何时调小堆

```
现象：GC 次数少但每次时间长
动作：减小 -Xmx（让 GC 更频繁但每次更快）
```

### 新生代调优

```
新生代太小的表现：
  → Minor GC 非常频繁（每秒多次）
  → 刚创建的小对象被过早晋升到老年代
  → 老年代增长快 → Full GC 频繁

新生代太大的表现：
  → Minor GC 不频繁但每次时间长
  → 老年代空间被挤压

建议：新生代 = 堆总量 × 1/4 ~ 1/3
```

## 栈内存调优

```bash
-Xss256k               # 每个线程的栈大小（默认 1MB，Linux 下可能不同）
```

何时调整：
- 线程数多（> 500）→ 调小 `-Xss`，省出虚拟地址空间
- 递归深度大 → 调大 `-Xss`，或重构为循环
- `OOM: unable to create native thread` → 调小 `-Xss`

## Metaspace 调优

```bash
-XX:MetaspaceSize=128m               # 初始大小（触发首次 GC 的阈值）
-XX:MaxMetaspaceSize=256m            # 最大上限（建议设置！）
-XX:MinMetaspaceFreeRatio=40         # GC 后 Metaspace 最小空闲比
-XX:MaxMetaspaceFreeRatio=70         # GC 后 Metaspace 最大空闲比
```

现象 vs 对策：
- Metaspace OOM → 增大 `MaxMetaspaceSize`；检查是否有类加载器泄漏
- Metaspace 频繁 Full GC → 增大 `MetaspaceSize`（减少过早 GC）

## GC 日志分析

```bash
# JDK 9+ 统一 GC 日志
-Xlog:gc*:file=/var/log/app/gc.log:time,level,tags:filecount=10,filesize=10M

# 关键日志指标解读
[gc,phases   ] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 50M->30M(200M) 15.2ms
                  │     │        │                                    │    │       │
                  │     │      年轻代GC                             变化  总量    耗时
                  │    序号

# 关注点：
# 1. GC 频率 —— 每分钟多少次？是否异常频繁？
# 2. 回收量 —— 每次回收了多少？如果回收量少 → 对象都活着 → 可能内存泄漏
# 3. 暂停时间 —— 单次 GC 耗时是否稳定？是否逐步增长？
```

### GC 日志工具

```bash
# GCeasy —— 在线分析 GC 日志（上传即分析）
# https://gceasy.io

# GCViewer —— 本地工具
# java -jar gcviewer.jar gc.log
```

## Heap Dump 分析

```bash
# 1. 获取 Heap Dump
jmap -dump:live,format=b,file=/tmp/heap.hprof <pid>

# 2. 自动 Dump（OOM 时）
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/tmp/heap.hprof
```

### MAT（Memory Analyzer Tool）分析步骤

```
1. 打开 heap.hprof
2. 查看 Dominator Tree —— 按占用内存排序
3. 找到最大的几个对象
4. 右键 → Path to GC Roots → 排除弱/软引用
5. 分析为什么这个对象没被回收：
   ├── HashMap 不断增长未清理
   ├── ThreadLocal 未 remove
   ├── 静态集合持续添加
   └── 连接池/线程池未关闭
```

## Thread Dump 分析

```bash
# 获取线程快照
jstack <pid> > thread.dump
# 或连续多次（对比分析）
jstack <pid> > thread1.dump; sleep 3; jstack <pid> > thread2.dump
```

### 线程状态分析

```
RUNNABLE      —— 正在运行或等待 CPU（检查是否死循环）
BLOCKED       —— 等待获取锁（可能锁竞争激烈）
WAITING       —— 无限等待（wait/join/park）
TIMED_WAITING —— 限时等待（sleep/wait(timeout)）

重点关注：
- 大量线程 BLOCKED 在同一个锁 → 锁竞争热点
- 大量线程 WAITING → 资源不足（连接池满、线程池满）
- 多次 Dump 中线程一直卡在同一个方法 → 死循环或耗时过长
```

## CPU 飙高排查

```
1. top -Hp <pid>               # 找到 CPU 最高的线程 tid

2. printf "%x\n" <tid>         # 转成 16 进制

3. jstack <pid> | grep <hex> -A 20  # 找到对应线程的堆栈

4. 分析堆栈：
   ├── GC 线程 CPU 高 → GC 频繁 → 调优 GC 或增大堆
   ├── 业务线程 CPU 高 → 死循环或复杂计算
   └── JIT 编译线程 CPU 高 → 正常（编译热点代码）
```

## 内存泄漏排查

### 常见内存泄漏模式

```java
// 1. ThreadLocal 未清理
public class ThreadLocalLeak {
    private static ThreadLocal<byte[]> local = ThreadLocal.withInitial(
        () -> new byte[10 * 1024 * 1024]  // 10MB
    );
    // 线程池中的线程复用 → ThreadLocal 永不释放！
    // 解决：finally { local.remove(); }
}

// 2. HashMap 只增不减
Map<String, Object> cache = new HashMap<>();
// 随着时间推移不断 put，从不 remove → 最终 OOM
// 解决：用 LRU 缓存（LinkedHashMap 或 Caffeine）

// 3. 监听器未注销
eventSource.addListener(listener);
// ... 使用完后未 removeListener
// listener 持有大对象的引用 → 大对象无法 GC

// 4. 连接未关闭
Connection conn = dataSource.getConnection();
// 忘记 close → 连接对象 + 关联的 Statement/ResultSet 都泄漏

// 5. 静态集合持有对象
static List<Object> list = new ArrayList<>();
// 持续 add → 永不释放
```

## 内存溢出（OOM）排查

### OOM 类型

| 错误信息 | 原因 | 排查方向 |
|----------|------|----------|
| `Java heap space` | 堆内存不足 | 分析 Heap Dump |
| `GC overhead limit exceeded` | GC 占用 > 98% 时间，回收 < 2% 堆 | 堆太小或内存泄漏严重 |
| `Metaspace` | 类元数据区不足 | 增大 `MaxMetaspaceSize`；排查类加载泄漏 |
| `Direct buffer memory` | 直接内存用尽 | 增大 `MaxDirectMemorySize`；检查 NIO Buffer 释放 |
| `unable to create native thread` | OS 线程数上限 | 减少线程数或调小 `-Xss` |
| `Requested array size exceeds VM limit` | 数组太大（> Integer.MAX_VALUE 附近） | 检查数组创建逻辑 |

### OOM 排查步骤

```
1. 确认 OOM 类型（看日志）
2. Java heap space → 获取 Heap Dump → MAT 分析
3. Metaspace → 检查是否用了大量动态代理/CGLIB/Groovy 脚本
4. Direct buffer → 检查 NIO 使用是否正确
5. 线程 → 检查是否有线程泄漏
```

## 死锁排查

```bash
jstack <pid> | grep -A 10 "Found.*deadlock"
# 或
jcmd <pid> Thread.print | grep -A 10 "deadlock"
```

```java
// 典型死锁
// Thread A: lock1 → 等 lock2
// Thread B: lock2 → 等 lock1

// jstack 会直接指出 Found one Java-level deadlock
// 并列出死锁的线程和它们持有的锁
```

## 常用 JVM 参数速查

```bash
# ===== 堆 =====
-Xms2g -Xmx2g                                      # 堆大小
-XX:NewRatio=2                                     # 老年代/新生代
-XX:SurvivorRatio=8                                # Eden/Survivor

# ===== 元空间 =====
-XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=256m

# ===== GC 选择 =====
-XX:+UseG1GC                                       # G1
-XX:+UseZGC -XX:+ZGenerational                     # ZGC (JDK 21+)
-XX:MaxGCPauseMillis=200                           # 暂停目标

# ===== 日志与诊断 =====
-Xlog:gc*:file=gc.log:time,level,tags              # GC 日志 (JDK 9+)
-XX:+HeapDumpOnOutOfMemoryError                    # OOM 时自动 Dump
-XX:HeapDumpPath=/tmp/heap.hprof                   # Dump 路径
-XX:+PrintFlagsFinal                               # 打印所有 JVM 参数

# ===== 线程 =====
-Xss256k                                           # 栈大小

# ===== 直接内存 =====
-XX:MaxDirectMemorySize=512m

# ===== 调试 =====
-XX:+TraceClassLoading                             # 打印类加载日志
-XX:+TraceClassUnloading                           # 打印类卸载日志
```

## 应用场景实战

### 场景一：4GB 堆的 Web 应用配置

```bash
java -Xms4g -Xmx4g \
     -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=100 \
     -XX:MaxMetaspaceSize=256m \
     -Xlog:gc*:file=/var/log/app/gc.log:time,level,tags:filecount=10,filesize=50M \
     -XX:+HeapDumpOnOutOfMemoryError \
     -XX:HeapDumpPath=/var/log/app/heap.hprof \
     -jar app.jar
```

### 场景二：容器化环境

```bash
# 容器中必须设置堆大小，否则 JVM 可能看到宿主机的全部内存
# JDK 10+ 自动感知容器内存限制
-XX:+UseContainerSupport         # JDK 10+ 默认开启
-XX:MaxRAMPercentage=75.0        # 使用容器内存的 75% 作为堆最大值
-XX:InitialRAMPercentage=50.0    # 初始 50%
# 替代 -Xms/-Xmx：不需要写死具体大小
```

### 场景三：死锁定位脚本

```bash
#!/bin/bash
PID=$1
for i in {1..5}; do
    jstack $PID > thread_$i.dump
    sleep 2
done
# 用文本对比工具打开多个 dump，找到状态不变的 BLOCKED 线程
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| OOM 了但没有 Dump | 没开 `HeapDumpOnOutOfMemoryError` | 加上该参数 |
| GC 日志没有时间戳 | JDK 9+ 需要显式加 `time` tag | `-Xlog:gc*:file=gc.log:time` |
| 调大堆后 GC 时间暴涨 | 堆越大单次 GC 越长 | 切换到 G1/ZGC |
| 容器 OOMKilled | 堆设置超过了容器限制 | 用 `MaxRAMPercentage` 替代写死 `-Xmx` |

### 调优禁忌

```
1. 不要在生产环境用 -Xlog:gc*=debug（日志量爆炸）
2. 不要在同一个 JVM 反复调参数（一次一个，对比效果）
3. 不要用 System.gc() 来"帮忙"（打乱 GC 节奏）
4. 不要以为调大堆就能解决一切问题（内存泄漏再大也会 OOM）
5. 不要在容器中硬编码 -Xmx（应该用 MaxRAMPercentage）
```

## 总结

- 调优四步：明确目标 → 收集数据 → 分析定位 → 调整验证
- 堆：`-Xms`=`-Xmx` 避免动态扩容，关注 GC 频率和回收量
- GC 日志是调优的眼睛——`-Xlog:gc*` 必开
- Heap Dump 看谁占内存，Thread Dump 看线程在干什么
- CPU 飙高：top -Hp → 16 进制 tid → jstack → 分析堆栈
- 内存泄漏 Top 5：ThreadLocal、HashMap 膨胀、监听器未注销、连接未关闭、静态集合
- 容器环境用 `-XX:MaxRAMPercentage` 而不是写死 `-Xmx`
