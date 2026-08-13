---
title: Linux 基础
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [linux, centos, rocky-linux, ubuntu, debian, 文件系统, 用户, 用户组, 权限]
---

# Linux 基础

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [常见发行版](#常见发行版)
- [目录结构](#目录结构)
- [文件类型](#文件类型)
- [用户与用户组](#用户与用户组)
- [文件权限](#文件权限)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Linux 是开源的类 Unix 操作系统，是服务器端的事实标准，Java 开发者必须掌握。

```text
为什么 Java 开发者要会 Linux：
1. 部署 —— 应用部署到 Linux 服务器
2. 运维 —— 排查问题、查看日志、监控性能
3. 容器 —— Docker/K8s 底层都是 Linux
4. 面试 —— Linux 命令是后端面试高频考点
```

```text
Linux 特点：
1. 开源免费 —— 免费使用和修改
2. 稳定安全 —— 服务器长期稳定运行
3. 多用户多任务 —— 多个用户同时使用
4. 一切皆文件 —— 设备、进程、网络都是文件
```

## 常见发行版

Linux 发行版众多，主要分为两大派系。

### 发行版分类

```text
两大派系（按包管理器）：
1. RedHat 系（rpm/yum/dnf）—— CentOS、Rocky Linux、RHEL、Fedora
2. Debian 系（deb/apt）—— Ubuntu、Debian
```

| 发行版 | 派系 | 包管理器 | 特点 |
|--------|------|---------|------|
| CentOS | RedHat | yum/dnf | 服务器经典（已停维护） |
| Rocky Linux | RedHat | dnf | CentOS 替代（推荐） |
| Ubuntu | Debian | apt | 桌面/服务器流行 |
| Debian | Debian | apt | 稳定，Ubuntu 的父发行版 |

```text
选型建议：
1. 服务器：Rocky Linux 或 Ubuntu Server（CentOS 已停止维护）
2. 学习/桌面：Ubuntu（生态完善）
3. 容器基础镜像：Debian（alpine 更小）
```

### 包管理器对比

```bash
# RedHat 系（Rocky/CentOS）
dnf install nginx          # 安装
dnf remove nginx           # 卸载
dnf update                 # 更新所有
dnf search nginx           # 搜索

# Debian 系（Ubuntu/Debian）
apt install nginx          # 安装
apt remove nginx           # 卸载
apt update && apt upgrade  # 更新
apt search nginx           # 搜索
```

## 目录结构

Linux 目录结构遵循 FHS（Filesystem Hierarchy Standard）。

### 核心目录

```text
/         —— 根目录（一切目录的起点）
/bin      —— 基本命令（ls、cp 等）
/sbin     —— 系统管理命令（root 使用）
/etc      —— 配置文件（nginx.conf、hosts）
/home     —— 普通用户主目录
/root     —— root 用户主目录
/var      —— 可变数据（日志 /var/log、缓存）
/usr      —— 应用程序（/usr/bin、/usr/local）
/tmp      —— 临时文件（重启可清空）
/dev      —— 设备文件（磁盘、终端）
/proc     —— 进程信息（虚拟文件系统）
/opt      —— 可选软件（第三方软件）
```

### 目录速记

```text
/etc —— 配置（everything to configure）
/var —— 变化的数据（日志、运行数据）
/usr —— 用户程序（Unix System Resources）
/home —— 用户家目录
/tmp —— 临时文件
/opt —— 第三方软件（optional）
```

## 文件类型

Linux 一切皆文件，文件类型通过第一个字符标识。

### 文件类型标识

```bash
ls -l 的第一个字符：
-  普通文件
d  目录
l  符号链接（软链接）
b  块设备（磁盘）
c  字符设备（键盘、终端）
s  套接字（socket）
p  管道（pipe）
```

```bash
# 查看文件类型
ls -l /etc/hosts
# -rw-r--r-- 1 root root 220 Jan 1 12:00 /etc/hosts
# - 表示普通文件

ls -ld /home
# drwxr-xr-x ... /home
# d 表示目录
```

### 软链接 vs 硬链接

```bash
# 软链接（符号链接）：类似快捷方式，指向目标路径
ln -s /opt/app/app.jar /usr/local/app.jar

# 硬链接：指向同一 inode，删除原文件不影响
ln /opt/app/app.jar /usr/local/app.jar
```

```text
软链接：可以跨文件系统，目标删除后链接失效
硬链接：不能跨文件系统，不能链接目录，删除任一不影响
```

## 用户与用户组

Linux 是多用户系统，每个用户属于一个或多个用户组。

### 用户管理

```bash
# 创建用户
useradd -m -s /bin/bash zhangsan   # -m 创建主目录，-s 指定 shell

# 设置密码
passwd zhangsan

# 删除用户
userdel -r zhangsan                # -r 删除主目录

# 切换用户
su - zhangsan                      # 切换到 zhangsan

# 查看当前用户
whoami

# 查看用户信息
id zhangsan                        # 查看 uid、gid、所属组
```

### 用户组管理

```bash
# 创建用户组
groupadd dev

# 把用户加入组
usermod -aG dev zhangsan           # -aG 追加到组

# 查看用户所属组
groups zhangsan
```

### 关键文件

```text
/etc/passwd —— 用户信息（用户名、UID、主目录、shell）
/etc/shadow —— 用户密码（加密存储）
/etc/group  —— 用户组信息
```

### root 与 sudo

```bash
# root：超级用户，拥有所有权限
# sudo：普通用户临时获取 root 权限执行命令

sudo apt install nginx    # 以 root 权限执行
sudo -i                   # 切换到 root
```

## 文件权限

文件权限是 Linux 安全的核心，控制谁可以读、写、执行文件。

### 权限表示

```bash
ls -l 输出：-rwxr-xr--
```

```text
权限分为三组（所有者/所属组/其他人）：
-rwx r-x r--
 │││  │││  │││
 │││  │││  └└└ 其他人（other）
 │││  └└└────── 所属组（group）
 └└└─────────── 所有者（owner）

r = 读（read）    = 4
w = 写（write）   = 2
x = 执行（execute）= 1
```

### 权限修改

```bash
# 数字方式
chmod 755 file      # 所有者 rwx(7)，组 r-x(5)，其他 r-x(5)
chmod 644 file      # 所有者 rw(6)，组 r(4)，其他 r(4)
chmod 777 file      # 所有人 rwx（不安全）

# 符号方式
chmod u+x file      # 所有者加执行权限
chmod g-w file      # 组去掉写权限
chmod o=r file      # 其他人只读
chmod a+x file      # 所有人加执行权限
```

### 常用权限组合

```text
644 —— 普通文件（所有者可读写，其他人只读）
755 —— 目录/可执行文件（所有者可写，其他人读执行）
600 —— 私密文件（只有所有者可读写，如密钥）
777 —— 危险！所有人可读写执行
```

### 修改所有者

```bash
chown zhangsan file            # 修改所有者
chown zhangsan:dev file        # 修改所有者和组
chown -R zhangsan:dev /opt/app # 递归修改目录
```

### 权限应用（Java 开发者场景）

```bash
# 部署脚本需要执行权限
chmod +x deploy.sh

# 日志文件需要应用用户可写
chown -R app:app /var/log/app

# 密钥文件必须私密
chmod 600 ~/.ssh/id_rsa
```

## 应用场景实战

### 场景 1：部署用户和目录规划

```bash
# 创建应用专用用户
useradd -m -s /bin/bash app

# 创建应用目录
mkdir -p /opt/app /opt/app/logs

# 设置权限（app 用户拥有）
chown -R app:app /opt/app

# 切换 app 用户部署
su - app
```

### 场景 2：Java 应用部署目录

```text
/opt/app/                    # 应用根目录
├── app.jar                  # 可执行 jar
├── config/                  # 配置文件
│   └── application.yml
├── logs/                    # 日志
└── deploy.sh                # 部署脚本
```

### 场景 3：SSH 密钥权限

```bash
# SSH 密钥的权限要求严格
chmod 700 ~/.ssh          # 目录仅所有者可访问
chmod 600 ~/.ssh/id_rsa   # 私钥仅所有者可读写
chmod 644 ~/.ssh/id_rsa.pub  # 公钥可读
# 权限不对 SSH 会拒绝使用密钥
```

## 最佳实践与踩坑记录

### 最佳实践

1. **不要用 root 跑应用**。创建专用用户（如 app），最小权限原则。

2. **密钥文件权限 600**。私钥、证书文件必须仅所有者可读写。

3. **生产环境用最小权限**。文件 644、目录 755，不要 777。

4. **服务用 systemd 管理**。开机自启、崩溃重启、日志收集。

5. **配置放 /etc，数据放 /var，应用放 /opt**。遵循 FHS 规范。

### 踩坑记录

**坑 1：chmod 777 滥用**

```bash
chmod -R 777 /opt/app   # 图省事全放开，安全风险巨大
```

777 让任何用户都能改文件，生产环境严禁。用最小权限（644/755）+ 正确的所有者。

**坑 2：SSH 密钥权限错误**

```bash
chmod 644 ~/.ssh/id_rsa   # 私钥权限太宽松
# SSH 报错：Permissions 0644 for 'id_rsa' are too open
```

私钥必须 600，否则 SSH 拒绝使用。

**坑 3：软链接目标被删**

```bash
ln -s /opt/app/v1/app.jar /opt/app/app.jar
# 升级到 v2 后删除 v1，软链接失效
```

软链接指向的目标删除后链接失效，用相对路径或更新链接。

**坑 4：用户组修改后不生效**

```bash
usermod -aG docker zhangsan
# 需要重新登录才生效
```

修改用户组后需要重新登录（或 newgrp）才生效。

**坑 5：忘记 -m 创建用户主目录**

```bash
useradd zhangsan        # 没加 -m，没有主目录
su - zhangsan           # 登录报错或没有家目录
```

创建用户加 -m 创建主目录。

**坑 6：文件所有者错误导致应用无法写**

```text
root 部署了应用，应用以 app 用户运行，
但日志目录是 root 的，app 用户写不了日志
```

部署时确保应用目录和日志目录的所有者是运行用户。
