---
title: Linux 网络
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [linux, ping, curl, wget, telnet, nc, ss, netstat, ip, traceroute, dns, tcp-ip]
---

# Linux 网络

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [TCP/IP 与 DNS 基础](#tcpip-与-dns-基础)
- [ping 连通性测试](#ping-连通性测试)
- [curl 网络请求](#curl-网络请求)
- [wget 下载](#wget-下载)
- [telnet/nc 端口测试](#telnetnc-端口测试)
- [ss/netstat 网络状态](#ssnetstat-网络状态)
- [ip 网络配置](#ip-网络配置)
- [traceroute 路由追踪](#traceroute-路由追踪)
- [应用场景实战](#应用场景实战)

## 概述

Linux 网络命令用于测试连通性、调试网络、排查服务问题，是后端开发者的必备技能。

```text
网络命令分类：
1. 连通性测试 —— ping、telnet、nc
2. 网络请求 —— curl、wget
3. 网络状态 —— ss、netstat、ip
4. 路由追踪 —— traceroute
5. DNS 解析 —— nslookup、dig
```

## TCP/IP 与 DNS 基础

### TCP/IP 四层模型

```text
应用层    —— HTTP、HTTPS、DNS、SSH
传输层    —— TCP、UDP
网络层    —— IP、ICMP
链路层    —— 以太网、ARP
```

### TCP vs UDP

| 维度 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接（三次握手） | 无连接 |
| 可靠性 | 可靠（确认、重传） | 不可靠 |
| 顺序 | 有序 | 无序 |
| 速度 | 慢 | 快 |
| 场景 | HTTP、数据库、SSH | 视频、DNS、游戏 |

### 三次握手与四次挥手

```text
三次握手（建立连接）：
客户端 → SYN → 服务端
客户端 ← SYN+ACK ← 服务端
客户端 → ACK → 服务端

四次挥手（断开连接）：
客户端 → FIN → 服务端
客户端 ← ACK ← 服务端
客户端 ← FIN ← 服务端
客户端 → ACK → 服务端
```

### 常见端口

```text
22    —— SSH
80    —— HTTP
443   —— HTTPS
3306  —— MySQL
6379  —— Redis
8080  —— 常用 Web 应用
8848  —— Nacos
9092  —— Kafka
```

### DNS 解析

```bash
nslookup example.com       # 查询域名解析
dig example.com            # 详细 DNS 查询
cat /etc/resolv.conf       # 查看 DNS 服务器
cat /etc/hosts             # 本地 hosts 解析（优先级高于 DNS）
```

```text
域名解析顺序：
1. 本地 hosts（/etc/hosts）
2. 本地 DNS 缓存
3. DNS 服务器（/etc/resolv.conf）
```

## ping 连通性测试

ping 测试主机是否可达（基于 ICMP 协议）。

### 基本用法

```bash
ping example.com          # 持续 ping（Ctrl+C 停止）
ping -c 4 example.com     # ping 4 次
ping -i 2 example.com     # 间隔 2 秒
ping -w 10 example.com    # 超时 10 秒
```

```bash
# 输出解读
64 bytes from 93.184.216.34: icmp_seq=1 ttl=56 time=45.2 ms
# time = 往返时间（RTT），越小越快
```

### ping 的局限

```text
1. ping 通不代表服务正常 —— ICMP 通，但 HTTP 服务可能挂了
2. ping 不通不代表网络不通 —— 防火墙可能禁 ICMP
3. ping 测试的是网络层，不是应用层
```

## curl 网络请求

curl 是强大的网络请求工具，测试 HTTP 接口的核心。

### 基本用法

```bash
curl http://localhost:8080/api/users          # GET 请求
curl -X POST http://localhost:8080/api/users  # POST 请求
curl -H "Content-Type: application/json" \
     -d '{"name":"张三"}' \
     http://localhost:8080/api/users           # POST + JSON
curl -X PUT -d '{"name":"李四"}' \
     http://localhost:8080/api/users/1         # PUT
curl -X DELETE http://localhost:8080/api/users/1  # DELETE
```

### 常用参数

```bash
curl -v URL                # 显示详细信息（请求头/响应头）
curl -i URL                # 显示响应头
curl -H "Authorization: Bearer token" URL   # 自定义请求头
curl -d "key=value" URL    # POST 表单数据
curl -o file URL           # 保存到文件
curl -s URL                # 静默模式（不显示进度）
curl -k URL                # 忽略 SSL 证书（测试用）
```

```bash
# Java 开发者最常用：测试接口
curl -X POST http://localhost:8080/api/order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer xxx" \
  -d '{"userId":1,"productId":100,"quantity":2}'

# 查看接口响应头
curl -i http://localhost:8080/api/health
```

### 输出格式化和耗时

```bash
# 查看请求耗时
curl -w "\ntime_total: %{time_total}s\n" http://localhost:8080/api

# 格式化 JSON（配合 jq）
curl -s http://localhost:8080/api/users | jq .
```

## wget 下载

wget 用于下载文件，适合下载大文件、递归下载。

### 基本用法

```bash
wget http://example.com/file.tar.gz      # 下载文件
wget -O newname.tar.gz URL               # 指定文件名
wget -c URL                              # 断点续传
wget -b URL                              # 后台下载
wget -i urls.txt                         # 批量下载（文件列表）
```

```bash
# Java 开发者常用：下载 JDK、Maven 等
wget https://download.java.net/java/GA/jdk21/.../jdk-21_linux-x64_bin.tar.gz
```

### curl vs wget

```text
curl —— 网络请求（测试接口、发送请求）
wget —— 文件下载（下载文件、递归下载）

测试 API 用 curl，下载文件用 wget
```

## telnet/nc 端口测试

telnet 和 nc（netcat）测试端口连通性。

### telnet 测试端口

```bash
telnet localhost 3306       # 测试 MySQL 端口
telnet 192.168.1.1 6379     # 测试 Redis 端口
# 能连接（Connected）说明端口通，不能连接（Connection refused）说明不通
```

### nc（netcat）测试端口

```bash
nc -zv localhost 8080       # 测试端口是否开放
nc -zv 192.168.1.1 80-90    # 测试端口范围
nc -l 8080                  # 监听端口（临时服务）
```

```bash
# 安装 nc
dnf install nc    # RedHat 系
apt install netcat  # Debian 系
```

### 端口测试的意义

```text
服务连不上时，先测试端口：
1. ping 通（网络通）
2. 端口通（服务在监听）
3. 端口不通（服务挂了、防火墙拦截、监听地址错误）
```

## ss/netstat 网络状态

ss 和 netstat 查看网络连接和端口监听状态。

### ss（推荐，替代 netstat）

```bash
ss -tlnp              # 查看监听端口（TCP）
ss -tln               # 监听端口（不含进程）
ss -tunlp             # 所有监听（TCP + UDP）
ss -s                 # 网络统计摘要
ss -tn                # 所有 TCP 连接
```

```bash
# 输出解读
LISTEN  0  128  *:8080  *:*  users:(("java",pid=1234,fd=15))
# LISTEN = 监听中
# *:8080 = 监听所有地址的 8080 端口
# java pid=1234 = 进程 java，PID 1234
```

### netstat（传统）

```bash
netstat -tlnp         # 监听端口
netstat -an           # 所有连接
netstat -an | grep 8080   # 查 8080 端口
```

```bash
# Java 开发者常用：查端口占用
ss -tlnp | grep 8080       # 谁占用 8080
ss -tlnp | grep java       # java 进程监听的端口
```

### 端口占用排查

```bash
# 查 8080 端口被谁占用
ss -tlnp | grep 8080
# 或用 lsof
lsof -i :8080
```

## ip 网络配置

ip 命令查看和配置网络接口（替代 ifconfig）。

### 基本用法

```bash
ip addr               # 查看所有网络接口和 IP
ip addr show eth0     # 查看指定接口
ip route              # 查看路由表
ip link               # 查看链路状态
ip addr add 192.168.1.100/24 dev eth0   # 添加 IP
```

```bash
# 查看本机 IP（Java 开发者常用）
ip addr | grep inet
hostname -I           # 快速查看 IP
```

## traceroute 路由追踪

traceroute 追踪数据包经过的路由节点。

### 基本用法

```bash
traceroute example.com     # 追踪路由
traceroute -n example.com  # 不解析域名（更快）
```

```text
输出解读：
每一跳 = 一个路由节点，显示 IP 和延迟
* * * = 该节点不响应（防火墙拦截 ICMP）
```

```bash
# 安装
dnf install traceroute    # RedHat 系
apt install traceroute    # Debian 系
```

## 应用场景实战

### 场景 1：服务连不上排查流程

```bash
# 1. 测试网络连通性
ping 192.168.1.100

# 2. 测试端口（服务是否监听）
telnet 192.168.1.100 3306

# 3. 查看本机监听状态
ss -tlnp | grep 3306

# 4. 测试接口（服务是否正常）
curl http://192.168.1.100:8080/api/health
```

```text
排查顺序（从网络到应用）：
ping（网络通）→ telnet（端口通）→ curl（服务正常）
```

### 场景 2：测试 HTTP 接口

```bash
# GET 请求
curl http://localhost:8080/api/users

# POST 请求（带 JSON）
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"张三","age":20}'

# 带认证头
curl http://localhost:8080/api/users \
  -H "Authorization: Bearer eyJhbGci..."

# 查看完整信息
curl -v http://localhost:8080/api/users
```

### 场景 3：端口被占用排查

```bash
# 应用启动报 "Port 8080 was already in use"
# 查谁占用 8080
ss -tlnp | grep 8080
# 输出：java pid=1234 占用

# 终止占用进程
kill 1234
```

### 场景 4：DNS 问题排查

```bash
# 域名解析不了
nslookup example.com    # 查 DNS 解析

# 改 hosts 临时解决
echo "93.184.216.34 example.com" >> /etc/hosts
```

## 最佳实践与踩坑记录

### 最佳实践

1. **测试接口用 curl，测试端口用 telnet/nc**。curl 测应用层，telnet 测传输层。

2. **服务连不上按层次排查**。ping → 端口 → 接口，从网络到应用。

3. **查端口占用用 ss -tlnp**。ss 比 netstat 更快，是官方推荐。

4. **DNS 问题先查 /etc/hosts**。本地 hosts 优先级高于 DNS，可能被本地配置干扰。

### 踩坑记录

**坑 1：ping 通但服务连不上**

```text
ping 通（网络层通），但服务连不上，
可能是服务挂了、端口不通、防火墙拦截
```

ping 通不代表服务正常，要测端口（telnet）和接口（curl）。

**坑 2：防火墙拦截导致端口不通**

```bash
telnet localhost 8080   # 本机通
telnet 192.168.1.1 8080 # 其他机器不通 → 防火墙拦截
```

检查防火墙（firewalld/iptables），放行端口。

**坑 3：监听 127.0.0.1 导致外部访问不了**

```text
服务监听 127.0.0.1:8080，只有本机能访问，
其他机器访问不了（监听地址错误）
```

服务监听 0.0.0.0（所有地址），外部才能访问。

**坑 4：curl 不显示 HTTPS 报错**

```bash
curl https://example.com   # SSL 证书问题，加 -v 看详细错误
curl -k https://example.com  # 忽略证书（测试用，生产不要）
```

HTTPS 报错用 -v 查看详细原因，测试用 -k 忽略证书。

**坑 5：netstat 命令找不到**

```bash
netstat -tlnp   # command not found（新系统默认没装 net-tools）
```

用 ss 替代（现代 Linux 默认有 ss），或安装 net-tools。

**坑 6：DNS 缓存导致解析不一致**

```text
改了 DNS 记录，但客户端还是解析到旧 IP（本地缓存）
```

用 nslookup/dig 查询，客户端刷新 DNS 缓存。
