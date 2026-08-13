---
title: JVM 工具
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, jvm, tools, jstack, jmap, arthas, diagnostics]
---

# JVM 工具

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [jps —— 查看 Java 进程](#jps--查看-java-进程)
- [jstack —— 线程堆栈](#jstack--线程堆栈)
- [jmap —— 堆内存快照](#jmap--堆内存快照)
- [jstat —— GC 统计](#jstat--gc-统计)
- [jcmd —— 全能命令](#jcmd--全能命令)
- [jinfo —— JVM 参数查看](#jinfo--jvm-参数查看)
- [jconsole / VisualVM —— 可视化监控](#jconsole--visualvm--可视化监控)
- [Mission Control + Flight Recorder](#mission-control--flight-recorder)
- [Arthas —— 在线诊断神器](#arthas--在线诊断神器)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JDK 自带一套强大的诊断工具集，位于 `<JAVA_HOME>/bin/` 目录下。掌握它们是排查线上问题的基本功——从信息收集到 Dump 分析，再到 Arthas 这种在线诊断神器。

## jps —— 查看 Java 进程

```bash
# 列出所有 Java 进程
jps -l                    # 显示完整主类名
jps -v                    # 显示 JVM 参数
jps -m                    # 显示 main 方法参数

# 输出示例
# 12345 com.example.Application
# 12346 sun.tools.jps.Jps
```

## jstack —— 线程堆栈

```bash
# 获取线程快照
jstack <pid>              # 打印所有线程堆栈
jstack -l <pid>           # 额外显示锁信息
jstack -F <pid>           # 强制输出（进程无响应时）

# 输出分析
jstack <pid> > thread.dump

# 关键信息：
# - 线程状态：RUNNABLE / BLOCKED / WAITING / TIMED_WAITING
# - 死锁检测：输出末尾会标注 "Found one Java-level deadlock"
# - 锁竞争："waiting to lock <0x...>" 表示等锁
```

常用分析技巧：

```bash
# 统计线程状态分布
jstack <pid> | grep java.lang.Thread.State | sort | uniq -c

# 找 CPU 最高的线程（配合 top）
top -Hp <pid>                    # 找到最高 CPU 的线程 ID
printf "%x\n" <tid>              # 转 16 进制
jstack <pid> | grep -A 20 <hex>  # 定位线程堆栈
```

## jmap —— 堆内存快照

```bash
# 堆使用概况
jmap -heap <pid>               # 堆配置 + 各代使用情况

# 堆中对象统计（直方图）
jmap -histo <pid>              # 所有对象（含不可达）
jmap -histo:live <pid>         # 仅存活对象（触发一次 Full GC）

# 输出示例：
#  num     #instances         #bytes  class name
#    1:       1254000      120384000  [C          (char 数组)
#    2:        500000       40000000  java.lang.String
#    3:        200000       12800000  com.example.User

# 导出堆 Dump
jmap -dump:live,format=b,file=/tmp/heap.hprof <pid>
# live: 只导出存活对象
# format=b: 二进制格式
# 注意：Dump 期间进程会暂停（STW）
```

### histo 分析技巧

```bash
# 快速定位内存大户
jmap -histo:live <pid> | head -20     # Top 20 对象类型
# 如果 User 类实例数远超预期 → 内存泄漏
# 如果 char[] 占用最多 → 正常（字符串）
```

## jstat —— GC 统计

```bash
# 实时 GC 监控
jstat -gc <pid> 1000               # 每 1 秒打印 GC 统计
jstat -gcutil <pid> 1000           # GC 使用率百分比
jstat -gccapacity <pid>            # 各代容量

# 输出列含义（-gcutil）：
# S0  S1  E   O   M   YGC YGCT FGC FGCT GCT
# S0/S1: Survivor 使用率
# E: Eden 使用率
# O: Old 使用率
# M: Metaspace 使用率
# YGC/YGCT: Young GC 次数/耗时
# FGC/FGCT: Full GC 次数/耗时
# GCT: 总 GC 耗时
```

```bash
# 关键监控脚本
jstat -gcutil <pid> 1000 | awk '{print "Eden:"$3"% Old:"$4"% FGC:"$9" GCT:"$11"s"}'
```

## jcmd —— 全能命令

JDK 7+ 引入的"瑞士军刀"——一个命令取代 jstack/jmap/jinfo 的大部分功能：

```bash
# 列出所有可用命令
jcmd <pid> help

# 常用命令
jcmd <pid> VM.version          # JVM 版本
jcmd <pid> VM.flags            # JVM 参数
jcmd <pid> VM.system_properties # 系统属性
jcmd <pid> Thread.print        # 线程堆栈（= jstack）
jcmd <pid> GC.run              # 触发 Full GC
jcmd <pid> GC.class_histogram  # 类直方图（= jmap -histo）
jcmd <pid> VM.native_memory summary  # 本地内存使用（需开启 NMT）

# Dump
jcmd <pid> GC.heap_dump /tmp/heap.hprof   # Heap Dump
jcmd <pid> Thread.dump_to_file /tmp/thread.txt  # Thread Dump 到文件
```

## jinfo —— JVM 参数查看

```bash
# 查看所有参数（含默认值）
jinfo <pid>

# 查看单个参数
jinfo -flag MaxHeapSize <pid>
jinfo -flag UseG1GC <pid>

# 动态修改参数（仅限部分 manageable 参数）
jinfo -flag +PrintGC <pid>
jinfo -flag -PrintGC <pid>
```

## jconsole / VisualVM —— 可视化监控

### jconsole（JDK 自带）

```bash
jconsole                     # 启动 GUI，选择要连接的 Java 进程
# 功能：
# - 堆内存实时图表（年轻代/老年代/Metaspace）
# - 线程数/状态统计
# - CPU 使用率
# - 类加载数
# - MBean 监控（自定义指标）
```

### VisualVM（功能更强）

```bash
jvisualvm                    # 启动 GUI
# 额外功能：
# - 堆 Dump 分析（内置 OQL 查询）
# - Thread Dump 对比
# - CPU/内存 Profiling（方法级热点）
# - 远程 JVM 监控（需 JMX）
```

## Mission Control + Flight Recorder

JDK 11+ 需单独下载，JDK 8 自带 JFR：

```bash
# 启动 Flight Recorder 记录
-XX:StartFlightRecording=duration=60s,filename=recording.jfr

# jcmd 控制
jcmd <pid> JFR.start name=myrec duration=60s filename=/tmp/rec.jfr
jcmd <pid> JFR.check
jcmd <pid> JFR.stop name=myrec

# 用 JDK Mission Control (jmc) 打开 .jfr 文件分析
# 可以看到：
# - 方法级热点（CPU 消耗 top 方法）
# - 锁竞争热点
# - GC 事件时间线
# - IO 耗时
# - 异常统计
```

JFR 是生产可用的——开销 < 1%，不像传统 Profiler 拖慢应用。

## Arthas —— 在线诊断神器

Arthas 是阿里巴巴开源的 Java 诊断工具——无需重启、无需改代码即可查看运行时信息：

```bash
# 安装
curl -O https://arthas.aliyun.com/arthas-boot.jar
java -jar arthas-boot.jar      # 选择目标进程

# === 核心命令 ===

# thread —— 线程诊断
thread                          # 所有线程
thread -n 3                     # 最忙的 3 个线程
thread -b                       # 查找死锁线程
thread <id>                     # 查看指定线程堆栈

# dashboard —— 实时面板（类似 top）
dashboard                       # 实时刷新 CPU、内存、GC、线程

# watch —— 方法调用观测（无侵入！）
watch com.example.UserService getUser '{params, returnObj, throwExp}'

# trace —— 方法调用链追踪
trace com.example.UserService getUser
# 输出：getUser 方法内部每一步的耗时

# jad —— 反编译
jad com.example.UserService     # 在线反编译，检查线上代码是否和预期一致
jad --source-only com.example.UserService getUser

# ognl —— 表达式执行（查看/修改变量）
ognl '@com.example.Config@MAX_SIZE'
ognl '@com.example.Config@MAX_SIZE=200'

# heapdump —— 在线 Dump
heapdump /tmp/arthas-dump.hprof

# vmtool —— 强制 GC
vmtool --action forceGc

# logger —— 动态修改日志级别
logger --name com.example --level DEBUG
```

### Arthas 典型排查场景

```bash
# 场景 1：哪个方法最慢？
trace com.example.*Service *    # 追踪所有 Service 方法

# 场景 2：线上代码和仓库一致吗？
jad com.example.CriticalLogic   # 反编译直接看

# 场景 3：某个请求的参数是什么？
watch com.example.Controller create '{params[0].mobile,params[0].amount}'

# 场景 4：配置值是否正确？
ognl '@com.example.AppConfig@getEndpoint()'
```

## 应用场景实战

### 场景一：线上 CPU 100% 排查

```bash
# 1. 找到 CPU 最高的 Java 进程
top

# 2. 找到进程中 CPU 最高的线程
top -Hp <pid>

# 3. 线程 ID 转 16 进制
printf "%x\n" <tid>

# 4. 查看线程堆栈
jstack <pid> | grep -A 20 <hex_tid>

# 5. 如果 jstack 不够快，用 Arthas
thread -n 5                     # 直接显示最忙的 5 个线程
```

### 场景二：内存泄漏应急处理

```bash
# 1. 确认泄漏（jstat）
jstat -gcutil <pid> 1000 10    # Old 区持续增长不回落

# 2. 获取 Dump
jcmd <pid> GC.heap_dump /tmp/leak.hprof
# 或 OOM 前自动 Dump（-XX:+HeapDumpOnOutOfMemoryError）

# 3. MAT 分析 Dominator Tree

# 4. 如果无法 Dump（进程挂起），用 Arthas
heapdump /tmp/leak.hprof
```

### 场景三：接口偶发超时

```bash
# 用 Arthas trace 追踪
trace com.example.Controller order ' #cost > 1000'
# 只追踪耗时 > 1 秒的调用，输出调用链每一步的耗时
```

## 最佳实践与踩坑记录

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| jmap -dump 时进程挂起 | Dump 触发 STW | 换 `jcmd GC.heap_dump`；或在低峰期操作 |
| jstat 显示 FGC 次数很多但看不到停顿 | G1 的并发标记不算 Full GC | 看 `-gcutil` 的 YGC 和 GCT 即可 |
| jstack 输出不完整 | 进程负载高或即将 OOM | 用 `jstack -F` 强制输出 |
| Arthas 卸载不干净 | `stop` 只是停止，class 已加载 | 重启应用才能完全卸载 |

### 工具选择指南

```
日常监控     → jstat (命令行) / jconsole (GUI)
CPU 高       → top -Hp + jstack / Arthas thread -n 5
内存分析     → jmap -histo / MAT / Arthas heapdump
方法耗时     → Arthas trace / JFR
代码对账     → Arthas jad
GC 分析      → jstat + GC 日志 / GCeasy
死锁         → jstack / Arthas thread -b
全面诊断     → Arthas dashboard + JFR
```

## 总结

- `jps` 找进程，`jstat` 看 GC，`jstack` 看线程，`jmap` 看内存，`jcmd` 全能
- `jstat -gcutil <pid> 1000` 是最常用的命令行监控
- Arthas 是线上排查的终极武器——trace 追踪耗时、jad 反编译对账、watch 观测入参出参、ognl 动态修改
- JFR 是生产可用的 Profiler（开销 < 1%）
- Heap Dump 用 MAT 分析 Dominator Tree + Path to GC Roots
- 日志是事后分析的唯一依据：GC 日志必开，OOM 时自动 Dump 必配置
