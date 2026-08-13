---
title: DevOps
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [devops, ci, cd, iac, terraform, ansible, argo-cd, gitops]
---

# DevOps

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [DevOps 文化与实践](#devops-文化与实践)
- [IaC 基础设施即代码](#iac-基础设施即代码)
- [Terraform](#terraform)
- [Ansible](#ansible)
- [GitOps 与 Argo CD](#gitops-与-argo-cd)
- [应用场景实战](#应用场景实战)

## 概述

DevOps 是开发（Development）和运维（Operations）的融合，通过文化和工具打破开发和运维的壁垒。

```text
DevOps 的核心：
1. 文化 —— 开发和运维协作，共同负责
2. 自动化 —— CI/CD、IaC 自动化一切
3. 度量 —— 监控、日志、指标
4. 共享 —— 共享工具、责任、知识
```

```text
传统模式 vs DevOps：
传统：开发（写代码）→ 运维（部署维护），职责分离，沟通成本高
DevOps：开发运维一体化，自动化流水线，快速交付
```

## DevOps 文化与实践

### DevOps 的核心实践

```text
1. CI/CD —— 自动化构建、测试、部署
2. IaC —— 基础设施即代码（Terraform/Ansible）
3. 监控告警 —— 全链路监控（Prometheus/Grafana）
4. 日志管理 —— 集中日志（ELK）
5. 容器化 —— Docker/K8s
6. GitOps —— 声明式配置 + Git 为唯一来源
```

### DevOps 工具链

```text
代码管理   —— Git（GitHub/GitLab）
CI/CD      —— GitHub Actions/GitLab CI/Jenkins
容器       —— Docker
编排       —— Kubernetes
IaC        —— Terraform/Ansible
监控       —— Prometheus/Grafana
日志       —— ELK/Loki
```

### DevOps 的价值

```text
1. 快速交付 —— 从月级到天级/小时级
2. 质量提升 —— 自动化测试
3. 减少风险 —— 小步快速发布
4. 协作高效 —— 打破壁垒
```

## IaC 基础设施即代码

IaC（Infrastructure as Code）用代码定义和管理基础设施，替代手动操作。

### IaC 是什么

```text
传统：手动创建服务器、配置网络（点鼠标、敲命令）
IaC：用代码定义基础设施（声明式/命令式），自动化管理
```

```text
IaC 的好处：
1. 可重复 —— 同样的代码创建同样的环境
2. 版本控制 —— 基础设施变更可追踪、可回滚
3. 自动化 —— 一条命令创建整套环境
4. 一致性 —— 避免手动操作的不一致
```

### IaC 的两类工具

```text
声明式（描述目标状态）：
Terraform、CloudFormation —— 描述"我要什么"，工具自动实现

命令式（描述步骤）：
Ansible —— 描述"怎么做"，逐步执行
```

## Terraform

Terraform 是 HashiCorp 开源的 IaC 工具，声明式管理云基础设施。

### Terraform 特点

```text
1. 声明式 —— 描述目标状态
2. 多云支持 —— AWS、阿里云、腾讯云等
3. 状态管理 —— 记录基础设施状态
4. 依赖管理 —— 自动处理资源依赖
```

### Terraform 配置

```hcl
# main.tf（阿里云示例）
provider "alicloud" {
  region = "cn-hangzhou"
}

# 创建 ECS 实例
resource "alicloud_instance" "web" {
  instance_name   = "web-server"
  instance_type   = "ecs.g6.large"
  image_id        = "ubuntu_20_04_x64"
  vswitch_id      = alicloud_vswitch.default.id
  system_disk_category = "cloud_essd"
  system_disk_size = 40
}

# 创建安全组
resource "alicloud_security_group" "web" {
  name = "web-sg"
  vpc_id = alicloud_vpc.default.id
}
```

### 常用命令

```bash
terraform init          # 初始化（下载 provider）
terraform plan          # 预览变更（不实际执行）
terraform apply         # 应用变更（创建/修改）
terraform destroy       # 销毁资源
terraform state list    # 查看管理的资源
```

### Terraform 工作流

```text
1. 编写 .tf 配置（声明目标状态）
2. terraform plan（预览变更）
3. terraform apply（应用变更）
4. 状态存 state 文件（记录实际状态）
```

## Ansible

Ansible 是配置管理和自动化工具，命令式（agentless）管理服务器。

### Ansible 特点

```text
1. Agentless —— 无需安装 agent（SSH 连接）
2. 幂等 —— 重复执行结果一致
3. YAML 语法 —— 简单易读
4. 模块化 —— 丰富的内置模块
```

### Playbook

```yaml
# deploy.yml
- name: 部署 Java 应用
  hosts: web-servers
  become: yes
  tasks:
    - name: 安装 JDK
      apt:
        name: openjdk-17-jdk
        state: present

    - name: 创建应用目录
      file:
        path: /opt/app
        state: directory

    - name: 上传 jar 包
      copy:
        src: ./app.jar
        dest: /opt/app/app.jar

    - name: 启动应用
      systemd:
        name: app
        state: restarted
        enabled: yes
```

### Inventory（主机清单）

```yaml
# hosts.yml
web-servers:
  hosts:
    web1:
      ansible_host: 192.168.1.1
    web2:
      ansible_host: 192.168.1.2
```

### 常用命令

```bash
ansible-playbook deploy.yml          # 执行 playbook
ansible all -m ping                  # 测试连接
ansible web-servers -m shell -a "uptime"   # 执行命令
```

### Terraform vs Ansible

| 维度 | Terraform | Ansible |
|------|-----------|---------|
| 类型 | 声明式 | 命令式 |
| 适用 | 基础设施（云资源） | 配置管理（软件安装） |
| 状态 | 有状态管理 | 无状态（幂等） |
| 场景 | 创建服务器、网络 | 安装软件、配置应用 |

```text
两者常配合：
Terraform 创建基础设施（服务器、网络）
Ansible 配置服务器（安装软件、部署应用）
```

## GitOps 与 Argo CD

GitOps 是 DevOps 的延伸，以 Git 作为唯一来源（Single Source of Truth）。

### GitOps 核心原则

```text
1. Git 是唯一来源 —— 一切配置都在 Git
2. 声明式 —— 声明目标状态（K8s YAML）
3. 自动同步 —— 自动对比并应用变更
4. 可审计 —— Git 历史就是变更历史
```

### GitOps 工作流

```text
开发提交代码 → CI 构建镜像 → 更新 Git 配置（镜像版本）
→ Argo CD 检测到 Git 变更 → 自动同步到 K8s
```

```text
传统部署 vs GitOps：
传统：CI 直接部署到环境（kubectl apply）
GitOps：CI 更新 Git，Argo CD 从 Git 同步到环境
```

### Argo CD

```text
Argo CD 是 GitOps 的 K8s 实现：
1. 监控 Git 仓库的 K8s 配置
2. 检测到变更，自动同步到集群
3. 提供可视化界面和回滚
```

```yaml
# Argo CD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
spec:
  project: default
  source:
    repoURL: https://github.com/example/myapp-config  # Git 配置仓库
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    automated:              # 自动同步
      prune: true           # 删除多余资源
      selfHeal: true        # 自动修复漂移
```

### GitOps 的价值

```text
1. 回滚简单 —— git revert 即可回滚
2. 变更可审计 —— Git 历史完整记录
3. 声明式 —— 环境状态可预测
4. 安全 —— 不需要给 CI 集群权限
```

## 应用场景实战

### 场景 1：完整 DevOps 流水线

```text
1. 开发提交代码（Git）
2. CI 构建测试（GitHub Actions）
3. 构建 Docker 镜像，推送仓库
4. 更新 Git 配置仓库的镜像版本
5. Argo CD 检测变更，同步到 K8s
6. 监控告警（Prometheus/Grafana）
```

### 场景 2：IaC 创建环境

```bash
# 1. Terraform 创建基础设施
terraform init
terraform apply
# 创建了 ECS、VPC、安全组、数据库

# 2. Ansible 配置服务器
ansible-playbook setup.yml
# 安装了 JDK、Docker、配置了应用

# 3. 应用部署
kubectl apply -f app.yaml
```

## 最佳实践与踩坑记录

### 最佳实践

1. **IaC 管理所有基础设施**。手动操作不可重复、不可审计。

2. **Git 作为唯一来源（GitOps）**。一切变更通过 Git，可审计可回滚。

3. **Terraform 管基础设施，Ansible 管配置**。各司其职。

4. **Terraform 先 plan 后 apply**。预览变更，避免误操作。

5. **基础设施变更也要 review**。IaC 代码和业务代码一样 review。

### 踩坑记录

**坑 1：Terraform 手动改资源导致状态不一致**

```text
手动在控制台改了资源，Terraform state 还记录旧状态
下次 apply 会尝试恢复或报错
```

通过 Terraform 管理资源，不要手动改，或 terraform refresh。

**坑 2：Ansible 幂等性没保证**

```yaml
- name: 执行脚本
  shell: ./init.sh    # 每次执行都跑，可能重复执行
```

用幂等模块（file/copy/systemd），或脚本加幂等判断。

**坑 3：GitOps 自动同步导致意外变更**

```text
Argo CD 自动同步，Git 里的错误配置直接应用到生产
```

关键环境用手动同步（需要人工确认），或配置 review 流程。

**坑 4：Terraform state 文件泄露**

```text
state 文件包含敏感信息（密钥、密码），提交到 Git 泄露
```

state 文件存远程后端（S3/OSS），不提交到 Git。

**坑 5：忽视监控告警**

```text
DevOps 只做了 CI/CD，没有监控，故障发现不了
```

监控（Prometheus）+ 告警（Alertmanager）+ 日志（ELK）是 DevOps 的必备。

**坑 6：Ansible 连接配置错误**

```text
Ansible 默认用 SSH 连接，但没配置密钥或用户错误
```

配置 inventory 的 ansible_user、ansible_ssh_private_key_file。
