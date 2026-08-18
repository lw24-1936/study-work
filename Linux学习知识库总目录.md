# Linux学习知识库总目录

> 目标：从 Linux 命令行与系统基础出发，系统掌握 Shell 脚本、文本处理、用户权限、文件系统、进程与内存管理、软件包管理、systemd、网络与防火墙、日志监控、定时任务、系统调用与内核基础、性能调优、故障排查、存储与高可用、网络服务、虚拟化与容器、自动化运维、安全加固、内核源码与 eBPF，最终具备 Linux 运维 / SRE / 平台工程师的完整能力体系。
>
> 本目录按「基础 → 脚本 → 系统核心 → 网络 → 运维 → 性能 → 高级」的递进关系编排，覆盖从日常运维到内核级排查与系统设计的完整链路。

## 学习主线

```text
Linux 基础与命令行
  ↓
Shell 脚本与文本处理三剑客
  ↓
用户权限 / 文件系统 / 进程 / 内存
  ↓
软件包管理与 systemd
  ↓
网络基础与防火墙
  ↓
日志监控 / 定时任务 / 自动化
  ↓
系统调用与内核基础
  ↓
性能调优 / 故障排查
  ↓
存储 / 高可用 / 负载均衡
  ↓
网络服务 / 虚拟化 / 容器
  ↓
自动化运维 / 安全加固
  ↓
内核 / eBPF
  ↓
系统设计与综合项目
```

# 01 学习路线与开发环境

- Linux 运维 / SRE / 平台工程师能力模型
- 学习阶段与先修关系
- 发行版选择：Ubuntu / Debian / CentOS Stream / Rocky / AlmaLinux / openSUSE / Alpine
- 虚拟机 / 双系统 / 云主机 / 裸金属
- WSL2 / Multipass / Vagrant / Packer
- SSH 远程连接、密钥认证与免密登录
- Shell 环境：bash / zsh / fish、配置文件与别名
- 终端多路复用：tmux / screen
- 编辑器：Vim / Neovim / nano
- 编译工具链：GCC / Clang / Make / CMake / autotools
- 网络下载与请求：curl / wget / scp / rsync
- 帮助与手册：man / info / apropos / tldr / help
- 环境与实验：容器化练习环境、故障演练

# 02 Linux 系统基础

## 1. 内核与发行版
  - 操作系统与内核概念、宏内核与微内核
  - Linux 内核版本号、主线与 LTS
  - 发行版与内核的关系、Debian / Red Hat / Arch 系
## 2. 文件系统层级标准 FHS
  - 根目录结构：/bin /sbin /etc /usr /var /home /tmp /opt /lib
  - 伪文件系统：/proc /sys /dev /run
## 3. 文件与目录操作
  - 常用命令：ls / cd / pwd / mkdir / touch / cp / mv / rm / rmdir
  - 文件查看：cat / less / more / head / tail / nl / od / hexdump
  - 文件查找：find / locate / which / whereis / type
## 4. 文件类型与属性
  - 普通文件、目录、符号链接、设备文件、管道、socket
  - inode 与目录项、stat
  - 硬链接与符号链接
  - 时间戳：atime / mtime / ctime
## 5. 压缩与归档
  - tar / gzip / bzip2 / xz / zstd / zip / unzip
  - 分卷、增量备份、归档校验
## 6. 重定向与管道
  - 标准输入输出错误、重定向、管道、tee、xargs

# 03 文本处理与三剑客

## 1. 正则表达式
  - 元字符、字符类、量词、锚点、分组、反向引用、交替
  - 贪婪与懒惰、BRE 与 ERE、PCRE
## 2. grep
  - 基本与扩展正则、常用选项、递归搜索、上下文、多模式
## 3. sed
  - 替换、删除、插入、追加、地址范围、模式空间与保持空间
## 4. awk
  - 字段与记录、内置变量（NR / NF / FS / OFS / RS）、模式与动作
  - 条件、循环、数组、字符串与数值函数、BEGIN / END
## 5. 其他文本工具
  - sort / uniq / tr / cut / paste / join / comm / wc / diff / patch
## 6. 实战案例
  - Nginx / 应用日志统计分析、CSV 与配置文件处理、批量改名

# 04 Shell 脚本编程

## 1. Bash 基础
  - 脚本结构与执行方式、变量与作用域、环境变量、位置参数、特殊变量
## 2. 运算符与流程控制
  - 算术与字符串运算、条件判断（test / [[]]）、if / case、for / while / until / select
## 3. 函数
  - 函数定义、参数传递、返回值、局部变量、函数库
## 4. 数组与字符串处理
  - 一维与关联数组、字符串截取与替换、参数扩展
## 5. 输入输出重定向
  - 文件描述符、Here Document、Here String、进程替换
## 6. 进程与子 Shell
  - 子 shell、命令替换、后台任务、作业控制、信号处理 trap
## 7. 调试与规范
  - set -x / -e / -u / -o pipefail、shellcheck、编码规范与可移植性

# 05 用户与权限管理

## 1. 用户与组
  - passwd / shadow / group / gshadow、useradd / usermod / userdel / groupadd
## 2. 基本权限
  - rwx 权限、chmod / chown / chgrp、umask、默认权限
## 3. 特殊权限与 ACL
  - SUID / SGID / Sticky Bit
  - setfacl / getfacl、ACL 掩码与默认 ACL
## 4. 提权与 sudo
  - su / sudo、sudoers、visudo、sudo 日志与审计、Polkit
## 5. PAM 可插拔认证
  - PAM 模块、认证流程、常用模块（pam_unix / pam_tally2 / pam_limits）
## 6. 资源限制
  - ulimit、limits.conf、cgroups 资源限制

# 06 磁盘与文件系统

## 1. 磁盘与分区
  - 磁盘结构、MBR / GPT、fdisk / parted / gdisk
## 2. 文件系统
  - VFS 虚拟文件系统、ext4 / XFS / Btrfs / ZFS、格式化与挂载
  - mount / umount、fstab、UUID、文件系统检查 fsck
## 3. 逻辑卷管理 LVM
  - PV / VG / LV、创建、扩容、缩容、快照
## 4. RAID
  - RAID 0 / 1 / 5 / 6 / 10、软 RAID mdadm
## 5. 交换空间
  - swap 分区与 swap 文件、swappiness
## 6. 磁盘配额与工具
  - quota、df / du / lsblk / blkid / iostat

# 07 进程与作业管理

## 1. 进程基础
  - 进程 / 线程 / 任务、PID / PPID、进程状态、fork / exec
## 2. 进程管理命令
  - ps / top / htop / pgrep / pkill / kill / killall / jobs / fg / bg / nohup
## 3. 进程优先级
  - nice / renice、调度器与优先级、cgroups CPU 限制
## 4. 信号
  - 信号机制、常用信号（SIGTERM / SIGKILL / SIGINT / SIGHUP）、signal / trap
## 5. 进程间通信 IPC
  - 管道、命名管道、信号量、共享内存、消息队列、socket
## 6. 守护进程
  - 守护进程特征、nohup、systemd 托管、日志重定向

# 08 内存管理

## 1. 虚拟内存
  - 虚拟地址空间、分页、页表、TLB、内存映射 mmap
## 2. 内存分配与回收
  - 页缓存、Buffer / Cache、匿名页、内存水位线、回收机制
## 3. Swap 与 OOM
  - 交换、swappiness、OOM Killer、内存超售与隔离
## 4. 内存监控与调优
  - free / vmstat / top / sar、内存泄漏排查、cgroups 内存限制

# 09 软件包管理

## 1. Debian 系
  - apt / dpkg、软件源、依赖解析、apt-get / apt-cache
## 2. Red Hat 系
  - yum / dnf / rpm、仓库管理、dnf 常用操作
## 3. 源码编译
  - configure / make / make install、./configure 选项、编译依赖
## 4. 通用包格式
  - Snap / Flatpak / AppImage
## 5. 软件源与镜像
  - 官方源与镜像源、自建本地源、密钥与签名校验

# 10 系统启动与 systemd

## 1. 开机启动流程
  - BIOS / UEFI、GRUB2、内核加载、initramfs、systemd
## 2. systemd
  - unit 类型、service / timer / target / socket / mount
  - systemctl 常用操作、依赖关系、启动顺序
## 3. 编写 Service Unit
  - unit 配置、Type / ExecStart / Restart、日志集成
## 4. 运行级别与 target
  - multi-user.target、graphical.target、rescue / emergency
## 5. 启动排错
  - 单用户模式、grub 修复、急救模式

# 11 网络基础

## 1. TCP/IP 协议栈
  - OSI / TCP/IP 模型、IP 地址与子网、路由、ARP、ICMP
## 2. 网络配置
  - ip / ifconfig、网卡配置、静态与 DHCP、NetworkManager / systemd-networkd
## 3. 路由与转发
  - 路由表、默认网关、IP 转发、策略路由
## 4. DNS 与主机名
  - /etc/hosts、resolv.conf、dig / nslookup / host、hostnamectl
## 5. 网络诊断工具
  - ping / traceroute / ss / netstat / nc / tcpdump / mtr / ethtool
## 6. TCP 深入
  - 三次握手、四次挥手、状态机、TIME_WAIT、Keepalive、拥塞控制

# 12 防火墙与网络安全

## 1. netfilter 框架
  - iptables 表与链、规则匹配、NAT、端口转发
## 2. nftables
  - nft 语法、表 / 链 / 规则、与传统 iptables 对比
## 3. firewalld / ufw
  - 区域、服务、富规则、直接规则
## 4. 安全通信
  - SSH 加固、OpenSSL、证书、TLS、VPN（WireGuard / OpenVPN / IPsec）

# 13 日志管理与监控

## 1. 系统日志
  - syslog / rsyslog、journald、日志级别与设施
## 2. 日志轮转与集中
  - logrotate、日志归档、rsyslog 远程转发、ELK / Loki 简介
## 3. 系统监控
  - top / htop / vmstat / iostat / mpstat / sar / pidstat
## 4. 监控体系
  - Prometheus / node_exporter、Grafana、告警（Alertmanager）
## 5. 日志分析实战
  - 日志检索、异常定位、审计追踪

# 14 定时任务与自动化

## 1. cron
  - crontab 语法、系统级与用户级、特殊字符串、环境变量
## 2. systemd timer
  - timer unit、OnCalendar、与 cron 对比
## 3. at 与一次性任务
  - at / batch、anacron
## 4. 任务可靠性
  - 任务锁、日志、失败重试、邮件通知

# 15 系统调用与内核基础

## 1. 系统调用
  - 系统调用机制、用户态与内核态、strace 追踪
## 2. 内核模块
  - lsmod / modprobe / insmod、模块依赖、/lib/modules
## 3. 内核参数与伪文件系统
  - sysctl、/proc / sys、内核调优参数
## 4. 内核编译与升级
  - 内核源码、make menuconfig、内核升级与回滚

# 16 性能优化与调优

## 1. 性能分析方法论
  - 性能指标、USE 方法、容量规划、基线
## 2. CPU 性能
  - 负载、上下文切换、中断、CPU 亲和性、perf
## 3. 内存性能
  - 页缓存、内存水位、swap、内存分配
## 4. IO 性能
  - IO 调度器、磁盘吞吐与延迟、块设备调优
## 5. 网络性能
  - 网络吞吐、延迟、TCP 调优、网卡多队列
## 6. 综合调优工具
  - perf / bcc / bpftrace / eBPF、火焰图

# 17 故障排查与调试

## 1. 排查方法论
  - 故障分类、分层排查、信息收集、根因分析
## 2. 系统追踪
  - strace / ltrace、系统调用追踪、性能问题定位
## 3. 调试工具
  - gdb / pstack / addr2line / coredump 分析
## 4. 常见故障案例
  - 磁盘满、OOM、CPU 飙高、网络异常、无法登录、文件句柄耗尽

# 18 共享存储与数据备份

## 1. 共享存储
  - NFS / Samba / iSCSI、分布式存储简介（Ceph / GlusterFS）
## 2. 数据备份与恢复
  - 备份策略、rsync / restic / borg、快照与恢复演练
## 3. 文件同步
  - rsync 增量同步、inotify / lsyncd 实时同步
## 4. 存储性能与容量
  - 存储性能评估、容量规划、磁盘老化与替换

# 19 高可用与负载均衡

## 1. 高可用基础
  - 高可用概念、心跳、脑裂、仲裁、故障转移
## 2. Keepalived 与 VRRP
  - VRRP 协议、主备切换、健康检查、VIP 漂移
## 3. LVS 负载均衡
  - NAT / DR / TUN 模式、调度算法、持久化连接
## 4. HAProxy 与 Nginx
  - 七层 / 四层负载均衡、健康检查、会话保持、限流
## 5. 集群与一致性
  - 主从复制、主主、共享存储集群、分布式锁

# 20 网络服务

## 1. Web 服务
  - Nginx / Apache、虚拟主机、反向代理、TLS 证书
## 2. DNS 服务
  - BIND / dnsmasq / CoreDNS、区域、记录类型、解析流程
## 3. DHCP 与时间同步
  - dnsmasq / isc-dhcp、NTP / chrony、时区
## 4. 文件共享服务
  - Samba / NFS / FTP / SFTP / rsync
## 5. 邮件与消息
  - Postfix、邮件协议、基础邮件服务

# 21 虚拟化与容器

## 1. 虚拟化基础
  - 虚拟化类型、KVM / QEMU / libvirt、virt-manager
## 2. 容器原理
  - namespace / cgroups、镜像分层、容器运行时
## 3. Docker
  - 镜像 / 容器 / 网络 / 存储 / Dockerfile / Compose
## 4. 容器编排基础
  - Kubernetes 概念、Pod / Service / Deployment、kubectl
## 5. 容器运行时生态
  - Podman / containerd / LXC、CRI、OCI 运行时

# 22 自动化运维与 IaC

## 1. 配置管理
  - Ansible、inventory / playbook / role / module
## 2. 基础设施即代码
  - Terraform、基础设施定义与状态管理
## 3. 持续集成部署
  - Git 版本控制、GitLab CI / Jenkins、部署流水线
## 4. 配置与密钥管理
  - 配置中心、Vault 密钥管理、变更管理

# 23 安全加固与审计

## 1. 系统加固
  - 最小化安装、用户与权限、服务裁剪、内核加固参数
## 2. 强制访问控制
  - SELinux / AppArmor、策略与排错
## 3. 安全审计
  - auditd、审计规则、日志分析
## 4. 入侵检测与响应
  - 文件完整性校验（AIDE）、漏洞扫描、应急响应流程
## 5. 合规
  - 等保 / CIS 基线、安全基线检查工具

# 24 内核源码、驱动与 eBPF

## 1. 内核源码阅读
  - 内核源码结构、进程调度、内存管理、文件系统、网络子系统
## 2. 驱动开发基础
  - 字符设备、设备树、模块开发、内核调试
## 3. eBPF
  - eBPF 原理、bcc / bpftrace、可观测性与性能

# 25 Linux 面试与系统设计

## 1. 基础与命令
  - 文件系统、权限、进程、内存、网络、常用命令
## 2. 原理深入
  - 系统调用、虚拟内存、TCP、IO、调度、内核机制
## 3. 运维与排错
  - 常见故障、性能优化、高可用、安全
## 4. 系统设计
  - 高并发架构、可观测性平台、CICD、容器平台设计

# 26 综合项目实战

## 项目 01：Linux 服务器基础环境搭建
  - 系统安装、分区规划、用户与权限、SSH 加固、基础软件部署
## 项目 02：Web 站点与反向代理部署
  - Nginx 反向代理、多站点、TLS 证书、静态资源与缓存
## 项目 03：日志集中与监控告警平台
  - rsyslog / journald、Prometheus + Grafana、Alertmanager 告警
## 项目 04：自动化运维平台
  - Ansible 批量管理、巡检脚本、定时任务、发布流水线
## 项目 05：高可用集群与负载均衡
  - Keepalived + LVS/HAProxy、VIP 漂移、故障切换演练
## 项目 06：容器化与 K8s 部署
  - Dockerfile、Compose、Kubernetes 部署、滚动更新
## 项目 07：安全加固与合规基线
  - 系统加固、防火墙策略、SELinux、CIS 基线检查
## 项目 08：性能调优与故障演练
  - 压测、火焰图定位、内存/IO/网络调优、混沌演练

# 27 Linux 能力认证清单

## 基础与命令
- [ ] Linux 内核与发行版
- [ ] FHS 目录结构
- [ ] 常用命令与文件操作
- [ ] 文件查找与压缩归档
- [ ] 重定向与管道

## 脚本与文本处理
- [ ] 正则表达式
- [ ] grep / sed / awk
- [ ] Shell 脚本编程
- [ ] 脚本调试与规范

## 系统核心
- [ ] 用户与权限、ACL、sudo、PAM
- [ ] 磁盘分区、文件系统、LVM、RAID
- [ ] 进程管理与 IPC
- [ ] 内存管理与 Swap / OOM
- [ ] 软件包管理（apt / dnf / 源码）
- [ ] systemd 与服务管理

## 网络与安全
- [ ] TCP/IP、路由、DNS
- [ ] 网络诊断工具
- [ ] iptables / nftables / firewalld
- [ ] SSH 加固与 TLS
- [ ] SELinux / AppArmor
- [ ] 安全审计与入侵检测

## 运维与监控
- [ ] 日志管理（rsyslog / journald）
- [ ] 监控体系（Prometheus / Grafana）
- [ ] 定时任务（cron / systemd timer）
- [ ] 备份恢复与共享存储
- [ ] 高可用与负载均衡
- [ ] 网络服务（Nginx / DNS / DHCP）

## 进阶
- [ ] 系统调用与内核基础
- [ ] 性能优化与调优
- [ ] 故障排查与调试（strace / gdb）
- [ ] 虚拟化与容器（KVM / Docker / K8s）
- [ ] 自动化运维（Ansible / Terraform）
- [ ] 内核源码与 eBPF

# 28 推荐知识库目录结构

```text
Linux学习知识库/
├── 01-学习路线与开发环境/
├── 02-Linux系统基础/
├── 03-文本处理与三剑客/
├── 04-Shell脚本编程/
├── 05-用户与权限管理/
├── 06-磁盘与文件系统/
├── 07-进程与作业管理/
├── 08-内存管理/
├── 09-软件包管理/
├── 10-系统启动与systemd/
├── 11-网络基础/
├── 12-防火墙与网络安全/
├── 13-日志管理与监控/
├── 14-定时任务与自动化/
├── 15-系统调用与内核基础/
├── 16-性能优化与调优/
├── 17-故障排查与调试/
├── 18-共享存储与数据备份/
├── 19-高可用与负载均衡/
├── 20-网络服务/
├── 21-虚拟化与容器/
├── 22-自动化运维与IaC/
├── 23-安全加固与审计/
├── 24-内核源码、驱动与eBPF/
├── 25-Linux面试与系统设计/
└── 26-综合项目实战/
```

# 29 单篇知识文档标准模板

```markdown
# 主题名称

## 1. 概述
## 2. 核心概念
## 3. 工作原理
## 4. 常用命令与配置
## 5. 配置文件解析
## 6. 应用场景实战
## 7. 性能与调优
## 8. 安全与权限
## 9. 故障排查
## 10. 常见问题
## 11. 面试题
## 12. 相关文档
```

# 总结

> **完整 Linux 能力链**：命令行与系统基础 → Shell 脚本与文本处理 → 用户权限 / 文件系统 / 进程 / 内存 → 软件包与 systemd → 网络与防火墙 → 日志监控 / 定时任务 → 系统调用 / 内核基础 → 性能调优 / 故障排查 → 存储 / 高可用 / 负载均衡 → 网络服务 / 虚拟化 / 容器 → 自动化运维 / 安全加固 → 内核 / eBPF → 系统设计与综合项目。
