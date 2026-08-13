---
title: Linux 命令
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [linux, ls, cd, pwd, cp, mv, rm, mkdir, touch, cat, less, head, tail, grep, find, sed, awk, sort, uniq, xargs, cut, wc, tar, gzip, zip]
---

# Linux 命令

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [文件目录操作](#文件目录操作)
- [文件查看](#文件查看)
- [文件搜索](#文件搜索)
- [文本处理](#文本处理)
- [压缩打包](#压缩打包)
- [命令组合实战](#命令组合实战)

## 概述

Linux 命令是日常运维的基础，本篇覆盖 Java 开发者最常用的 23 个命令，按功能分类。

```text
命令分类：
1. 文件目录操作 —— ls、cd、pwd、cp、mv、rm、mkdir、touch
2. 文件查看 —— cat、less、head、tail
3. 文件搜索 —— grep、find
4. 文本处理 —— sed、awk、sort、uniq、xargs、cut、wc
5. 压缩打包 —— tar、gzip、zip
```

## 文件目录操作

### ls —— 列出目录内容

```bash
ls              # 列出当前目录
ls -l           # 详细信息（权限、大小、时间）
ls -a           # 显示隐藏文件（.开头的）
ls -lh          # 人类可读大小（K/M/G）
ls -lt          # 按修改时间排序
ls -ltr         # 按时间倒序（最新的在最后）
```

```bash
# 常用组合
ls -lht /var/log        # 日志目录，按时间排序，人类可读
```

### cd —— 切换目录

```bash
cd /opt/app        # 切换到绝对路径
cd app             # 切换到相对路径
cd ..              # 上一级
cd ~               # 家目录
cd -               # 上一次目录
```

### pwd —— 显示当前路径

```bash
pwd                # /opt/app
pwd -P             # 显示物理路径（软链接解析后）
```

### cp —— 复制文件

```bash
cp file1 file2             # 复制文件
cp -r dir1 dir2            # 递归复制目录
cp -i file1 file2          # 覆盖前确认
cp -p file1 file2          # 保留权限、时间戳
cp -a dir1 dir2            # 完整复制（含权限、软链接）
```

### mv —— 移动/重命名

```bash
mv file1 file2             # 重命名
mv file /opt/app/          # 移动到目录
mv -i file1 file2          # 覆盖前确认
```

### rm —— 删除

```bash
rm file               # 删除文件
rm -r dir             # 递归删除目录
rm -f file            # 强制删除（不确认）
rm -rf dir            # 强制递归删除（危险！）
```

```text
警告：rm -rf 极其危险，删除不可恢复！
生产环境删除前要再三确认路径。
```

### mkdir —— 创建目录

```bash
mkdir dir             # 创建目录
mkdir -p a/b/c        # 递归创建多级目录
```

### touch —— 创建文件/更新时间戳

```bash
touch file.txt        # 创建空文件
touch -t 202601011200 file.txt   # 修改时间戳
```

## 文件查看

### cat —— 查看文件（全文输出）

```bash
cat file.txt          # 查看全文
cat -n file.txt       # 显示行号
cat file1 file2       # 合并输出多个文件
cat > file.txt << EOF # 创建文件（heredoc）
```

### less —— 分页查看（推荐大文件）

```bash
less file.txt         # 分页查看
# 操作：
# 空格/PageDown —— 下一页
# b/PageUp —— 上一页
# /keyword —— 搜索（n 下一个，N 上一个）
# q —— 退出
# G —— 跳到末尾
```

### head —— 查看开头

```bash
head file.txt         # 前 10 行（默认）
head -n 20 file.txt   # 前 20 行
head -n 5 log.txt     # 日志前 5 行
```

### tail —— 查看末尾

```bash
tail file.txt         # 后 10 行（默认）
tail -n 20 file.txt   # 后 20 行
tail -f log.txt       # 实时跟踪（查看日志，核心！）
tail -f -n 100 log.txt  # 从后 100 行开始跟踪
```

```bash
# Java 开发者最常用：实时查看应用日志
tail -f /opt/app/logs/app.log
```

## 文件搜索

### grep —— 文本搜索

```bash
grep "keyword" file.txt         # 搜索包含 keyword 的行
grep -i "keyword" file.txt      # 忽略大小写
grep -v "keyword" file.txt      # 反向（不包含）
grep -n "keyword" file.txt      # 显示行号
grep -r "keyword" /opt/app/     # 递归搜索目录
grep -c "keyword" file.txt      # 统计匹配行数
grep -E "a|b" file.txt          # 正则（扩展）
```

```bash
# Java 开发者常用场景
grep "ERROR" app.log                       # 查错误日志
grep -n "NullPointerException" app.log     # 查 NPE 位置
grep -i "exception" app.log | head         # 查异常（忽略大小写）
grep -r "localhost" config/                # 查配置中的地址
```

### find —— 文件查找

```bash
find /opt -name "app.jar"          # 按名称查找
find /opt -name "*.log"            # 通配符
find /opt -type f -size +100M      # 大于 100M 的文件
find /opt -type f -mtime -7        # 7 天内修改的文件
find /opt -name "*.log" -delete    # 查找并删除
find / -name "java" -type f        # 全局查找 java
```

```bash
# 常用组合
find /opt -name "*.log" -mtime +30 -delete   # 删除 30 天前的日志
find /var/log -name "*.log" -type f -exec ls -lh {} \;   # 查找并查看大小
```

### grep 与 find 的区别

```text
grep：搜索文件内容（文件里找文字）
find：搜索文件（目录里找文件）
```

## 文本处理

### sed —— 流编辑器

```bash
sed 's/old/new/' file.txt        # 替换（每行第一个）
sed 's/old/new/g' file.txt       # 替换（全局）
sed -n '10,20p' file.txt         # 打印 10-20 行
sed -i 's/old/new/g' file.txt    # 直接修改文件
sed '/^$/d' file.txt             # 删除空行
```

```bash
# Java 开发者常用
sed -i 's/localhost/192.168.1.100/g' application.yml  # 批量替换配置
sed -n '100,200p' app.log                              # 查看日志 100-200 行
```

### awk —— 文本分析（按列处理）

```bash
awk '{print $1}' file.txt        # 打印第一列
awk '{print $1, $3}' file.txt    # 打印第 1、3 列
awk -F':' '{print $1}' /etc/passwd   # 指定分隔符
awk '{sum += $1} END {print sum}'    # 求和
awk '$3 > 100 {print $0}'        # 条件过滤
```

```bash
# Java 开发者常用
ps aux | awk '{print $2, $11}'        # 提取进程 ID 和命令
cat access.log | awk '{print $1}' | sort | uniq -c   # 统计 IP 访问次数
```

### sort —— 排序

```bash
sort file.txt           # 排序（默认字典序）
sort -n file.txt        # 按数值排序
sort -r file.txt        # 倒序
sort -k2 file.txt       # 按第 2 列排序
sort -t: -k3 -n /etc/passwd   # 指定分隔符按第 3 列数值排序
```

### uniq —— 去重（配合 sort）

```bash
sort file.txt | uniq            # 去重（先排序）
sort file.txt | uniq -c         # 去重并计数
sort file.txt | uniq -d         # 只显示重复的行
```

### xargs —— 参数传递

```bash
find . -name "*.log" | xargs rm          # 删除所有 log
echo "1 2 3" | xargs -n1 echo            # 逐个处理
find . -name "*.java" | xargs grep "TODO"  # 在所有 java 文件里搜 TODO
```

### cut —— 按列截取

```bash
cut -d':' -f1 /etc/passwd        # 按 : 分隔取第 1 列
cut -c1-5 file.txt               # 取每行前 5 个字符
```

### wc —— 统计

```bash
wc file.txt             # 行数、单词数、字节数
wc -l file.txt          # 行数
wc -w file.txt          # 单词数
wc -c file.txt          # 字节数
```

```bash
# Java 开发者常用
wc -l app.log                    # 日志行数
ls | wc -l                       # 文件数量
grep -c "ERROR" app.log          # 错误数量（等同 grep -c）
```

## 压缩打包

### tar —— 打包归档

```bash
tar -cvf archive.tar dir/        # 打包（c=创建，v=详细，f=文件）
tar -xvf archive.tar             # 解包
tar -czvf archive.tar.gz dir/    # 打包 + gzip 压缩
tar -xzvf archive.tar.gz         # 解压 tar.gz
tar -cjvf archive.tar.bz2 dir/   # 打包 + bzip2 压缩
tar -xjvf archive.tar.bz2        # 解压 tar.bz2
tar -xzf archive.tar.gz -C /opt  # 解压到指定目录
```

```bash
# 参数速记
# c = create（创建）
# x = extract（解压）
# z = gzip
# j = bzip2
# v = verbose（显示过程）
# f = file（指定文件）
# C = 解压到指定目录
```

### gzip —— 压缩单文件

```bash
gzip file.txt           # 压缩为 file.txt.gz
gunzip file.txt.gz      # 解压
gzip -d file.txt.gz     # 解压（同上）
```

### zip —— 压缩（跨平台）

```bash
zip -r archive.zip dir/     # 压缩目录
unzip archive.zip           # 解压
unzip archive.zip -d /opt   # 解压到指定目录
```

```text
tar.gz  vs zip：
tar.gz —— Linux 标准（打包 + 压缩）
zip —— 跨平台（Windows 也支持）
Linux 环境优先 tar.gz
```

## 命令组合实战

### 场景 1：分析访问日志

```bash
# 统计访问最多的 10 个 IP
cat access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

### 场景 2：查看应用错误

```bash
# 查看最近的错误日志
grep "ERROR" app.log | tail -20

# 统计每种异常出现次数
grep "Exception" app.log | awk '{print $NF}' | sort | uniq -c | sort -rn
```

### 场景 3：清理磁盘

```bash
# 查找大文件
find / -type f -size +500M 2>/dev/null

# 删除 30 天前的日志
find /var/log -name "*.log" -mtime +30 -delete

# 查看磁盘使用
df -h
du -sh /opt/*
```

### 场景 4：批量替换配置

```bash
# 把所有 yml 中的 localhost 换成生产地址
find config/ -name "*.yml" | xargs sed -i 's/localhost/prod-server/g'
```
