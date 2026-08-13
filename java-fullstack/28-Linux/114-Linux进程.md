---
title: Linux 进程
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [linux, ps, top, htop, kill, killall, systemd, systemctl, journalctl]
---

# Linux 进程

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [ps 查看进程](#ps-查看进程)
- [top/htop 实时监控](#tophtop-实时监控)
- [kill/killall 终止进程](#killkillall-终止进程)
- [systemd 系统管理](#systemd-系统管理)
- [systemctl 服务管理](#systemctl-服务管理)
- [journalctl 日志查看](#journalctl-日志查看)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

进程是运行中的程序实例。进程管理是 Linux 运维的核心，Java 应用的部署、监控、故障排查都离不开进程管理。

```text
进程 vs 程序：
程序：磁盘上的可执行文件（静态）
进程：运行中的程序实例（动态，有 PID、内存、CPU）

进程管理的内容：
1. 查看进程 —— ps、top
2. 终止进程 —— kill
3. 服务管理 —— systemctl（systemd）
4. 日志查看 —— journalctl
```

## ps 查看进程

ps（process status）查看进程快照。

### 常用命令

```bash
ps aux              # 查看所有进程（BSD 风格，最常用）
ps -ef              # 查看所有进程（System V 风格）
ps -ef | grep java  # 查找 java 进程
ps -u app           # 查看 app 用户的进程
```

### ps aux 输出解读

```text
USER   PID  %CPU %MEM  VSZ    RSS   TTY  STAT  START  TIME  COMMAND
app    1234  2.1  5.0  5123456 204800 ?   Sl    10:00  0:30  java -jar app.jar
```

```text
USER   —— 进程所属用户
PID    —— 进程 ID（核心标识）
%CPU   —— CPU 使用率
%MEM   —— 内存使用率
VSZ    —— 虚拟内存大小（KB）
RSS    —— 物理内存大小（KB）
STAT   —— 进程状态（S 睡眠、R 运行、Z 僵尸）
TIME   —— CPU 累计使用时间
COMMAND —— 启动命令
```

### 进程状态 STAT

```text
R —— 运行中（Running）
S —— 可中断睡眠（Sleeping，等待事件）
D —— 不可中断睡眠（等待 IO，通常是磁盘）
Z —— 僵尸进程（Zombie，已结束但父进程未回收）
T —— 停止（Stopped）
```

```bash
# Java 开发者常用
ps aux | grep java           # 查看 java 进程
ps -ef | grep app.jar        # 查特定应用
pgrep -f app.jar             # 直接查 PID
```

## top/htop 实时监控

top 是实时进程监控，类似 Windows 任务管理器。

### top 命令

```bash
top                # 实时监控（q 退出）
top -u app         # 只看 app 用户的进程
top -p 1234        # 只看指定 PID
```

### top 输出解读

```text
第一行：系统负载
  top - 10:00:00 up 30 days, 3:05, 1 user, load average: 0.5, 0.8, 0.6
  load average：1/5/15 分钟平均负载（核心指标！）

第二行：进程统计
  Tasks: 200 total, 1 running, 199 sleeping

第三行：CPU 使用率
  %Cpu(s): 2.0 us, 1.0 sy, 0.0 ni, 96.0 id, 1.0 wa
  us = 用户态，sy = 系统态，id = 空闲，wa = 等待 IO

第四行：内存
  MiB Mem: 8192 total, 4096 free, 2048 used, 2048 cache
```

### load average（负载）

```text
load average 是 1/5/15 分钟的平均负载：
- 单核：1.0 = 满载，超过 1 = 过载
- 多核：核数 = 满载（4 核 4.0 = 满载）

经验值：
- 长期 > 核数：系统过载，需要排查
- 短期 > 核数：可能瞬时高峰
```

### top 交互命令

```text
q —— 退出
P —— 按 CPU 排序
M —— 按内存排序
k —— 杀死进程（输入 PID）
1 —— 显示每个 CPU 核
```

### htop（增强版 top）

```bash
htop               # 彩色界面，更友好（需安装）
# 支持鼠标、上下键选择进程、F9 杀进程
```

```bash
# 安装 htop
dnf install htop     # RedHat 系
apt install htop     # Debian 系
```

## kill/killall 终止进程

kill 向进程发送信号，最常用的是终止进程。

### 常用信号

```text
SIGTERM（15）—— 优雅终止（默认，允许进程清理）
SIGKILL（9）—— 强制终止（立即杀死，不清理）
SIGHUP（1）—— 挂起（重载配置）
SIGINT（2）—— 中断（Ctrl+C）
```

```bash
kill 1234           # 发送 SIGTERM（优雅终止）
kill -9 1234        # 发送 SIGKILL（强制终止）
kill -15 1234       # 显式 SIGTERM
kill -l             # 查看所有信号
```

### 最佳实践

```text
先 SIGTERM（15），给进程清理机会（释放资源、保存状态）
等几秒还在，再 SIGKILL（9）强制终止

Java 应用：SIGTERM 触发优雅停机（Spring Boot 的 Graceful Shutdown）
```

### killall 按名称终止

```bash
killall java        # 终止所有 java 进程（危险！）
killall -9 nginx    # 强制终止所有 nginx
```

```bash
# 更安全的做法：先查 PID 再 kill
pgrep -f app.jar    # 查 PID
kill <PID>          # 精确终止
```

## systemd 系统管理

systemd 是 Linux 的初始化系统（init），负责管理服务和进程，是现代 Linux 的标准。

### systemd 是什么

```text
systemd 是 Linux 的系统和服务管理器：
1. 系统启动时初始化（PID 1）
2. 管理服务（启动、停止、重启）
3. 管理服务依赖和并行启动
4. 收集日志（journald）
```

### systemd 单元（Unit）

```text
Unit 是 systemd 管理的基本单元：
1. service —— 服务（最常用）
2. socket —— 套接字
3. target —— 目标（一组服务）
4. timer —— 定时器（替代 cron）
```

### 服务单元文件

```text
服务单元文件位置：
/etc/systemd/system/ —— 管理员自定义（优先）
/usr/lib/systemd/system/ —— 软件包自带
```

## systemctl 服务管理

systemctl 是管理 systemd 服务的命令，Java 应用部署的核心。

### 常用命令

```bash
systemctl start app          # 启动服务
systemctl stop app           # 停止服务
systemctl restart app        # 重启服务
systemctl reload app         # 重载配置（不停服务）
systemctl status app         # 查看状态
systemctl enable app         # 开机自启
systemctl disable app        # 取消开机自启
systemctl is-active app      # 是否运行中
systemctl is-enabled app     # 是否开机自启
systemctl list-units --type=service  # 列出所有服务
systemctl daemon-reload      # 重载单元文件（修改后必须执行）
```

### Java 应用的 systemd 服务

```ini
# /etc/systemd/system/app.service
[Unit]
Description=My Java Application
After=network.target          # 网络就绪后启动

[Service]
Type=simple
User=app                      # 运行用户（不用 root）
WorkingDirectory=/opt/app     # 工作目录
ExecStart=/usr/bin/java -jar /opt/app/app.jar    # 启动命令
ExecStop=/bin/kill -15 $MAINPID                   # 停止（优雅终止）
Restart=on-failure            # 失败自动重启
RestartSec=5                  # 重启间隔
SuccessExitStatus=143         # 143 = 128+15（SIGTERM 正常退出）

[Install]
WantedBy=multi-user.target    # 多用户模式启动
```

```bash
# 部署 Java 应用
systemctl daemon-reload       # 重载单元文件
systemctl start app           # 启动
systemctl enable app          # 开机自启
systemctl status app          # 查看状态
```

### systemd 服务的好处

```text
1. 开机自启 —— enable 后自动启动
2. 崩溃重启 —— Restart=on-failure 自动拉起
3. 日志收集 —— 输出到 journald，journalctl 查看
4. 优雅停机 —— 停止时发 SIGTERM，应用优雅退出
5. 统一管理 —— 一个命令管理所有服务
```

## journalctl 日志查看

journalctl 查看 systemd 的日志（journald）。

### 常用命令

```bash
journalctl -u app              # 查看 app 服务的日志
journalctl -u app -f           # 实时跟踪（类似 tail -f）
journalctl -u app --since "1 hour ago"   # 最近 1 小时
journalctl -u app -n 100       # 最近 100 行
journalctl -u app -p err       # 只看错误级别
journalctl -u app --since today   # 今天
journalctl --disk-usage        # 日志占用磁盘
```

```bash
# Java 开发者常用
journalctl -u app -f                        # 实时看应用日志
journalctl -u app -n 100 --no-pager         # 最近 100 行（不分页）
journalctl -u app --since "30 min ago" | grep ERROR   # 查错误
```

### journalctl vs 应用日志

```text
journalctl —— 看服务的标准输出/标准错误（System.out、System.err）
应用日志 —— 应用自己写的日志文件（logback 输出到 /opt/app/logs）

Java 应用通常两者都有：
1. 启动日志、异常堆栈 → journalctl（标准输出）
2. 业务日志 → 应用日志文件（logback 配置）
```

## 应用场景实战

### 场景 1：排查 CPU 占用过高

```bash
# 1. 找 CPU 占用高的进程
top -c

# 2. 找到后查看该进程的线程
top -H -p <PID>

# 3. 查看进程详细信息
ps -ef | grep <PID>

# 4. 如果是 Java 进程，导出线程栈分析
jstack <PID> > thread_dump.txt
```

### 场景 2：优雅重启 Java 应用

```bash
# 用 systemd 管理，优雅重启
systemctl restart app    # systemd 发 SIGTERM，应用优雅停机后重启
```

### 场景 3：查看应用日志排查问题

```bash
# 实时查看 systemd 日志
journalctl -u app -f

# 结合 grep 过滤错误
journalctl -u app -f | grep -i error
```

### 场景 4：僵尸进程排查

```bash
# 查找僵尸进程
ps aux | grep Z

# 僵尸进程的父进程没有回收，杀掉父进程
ps -ef | grep <父进程 PID>
kill <父进程 PID>
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Java 应用用 systemd 管理**。开机自启、崩溃重启、优雅停机、日志收集。

2. **终止进程先 SIGTERM 再 SIGKILL**。给进程清理机会。

3. **服务用专用用户运行**。不用 root，最小权限。

4. **关注 load average**。长期超过核数说明过载，要排查。

5. **修改单元文件后 daemon-reload**。否则修改不生效。

### 踩坑记录

**坑 1：kill -9 滥用**

```bash
kill -9 <PID>   # 直接强杀，应用来不及释放资源
# 数据库连接、文件句柄没释放，可能数据不一致
```

先 kill（SIGTERM），等几秒，再 kill -9。

**坑 2：修改 service 文件不 daemon-reload**

```bash
vim /etc/systemd/system/app.service
systemctl restart app    # 报错或还是旧配置
```

修改单元文件后必须 `systemctl daemon-reload`。

**坑 3：Restart 策略配置 always 导致无限重启**

```ini
Restart=always    # 应用启动失败也无限重启
# 配置错误的应用反复崩溃重启，占用资源
```

用 Restart=on-failure（启动失败不重启，运行中崩溃才重启）。

**坑 4：ExecStart 路径或权限错误**

```ini
ExecStart=/usr/bin/java -jar /opt/app/app.jar
# java 路径不对，或 app 用户没有 /opt/app 权限
```

确认 java 路径（which java）和目录权限（chown）。

**坑 5：进程杀不死**

```bash
kill -9 <PID>   # 还是杀不死
# 可能是 D 状态（不可中断睡眠，等待 IO），只能等 IO 完成或重启
```

D 状态进程（通常是磁盘/网络 IO 卡死）无法用 kill 杀死。

**坑 6：僵尸进程堆积**

```text
大量僵尸进程（Z 状态），虽然不占 CPU 内存，
但会占用 PID，PID 耗尽导致无法创建新进程
```

僵尸进程要找父进程，让父进程回收（或杀父进程）。
