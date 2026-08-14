<p align="center">
  <a href="./README.md">简体中文</a> ·
  <a href="./README.en.md">English</a>
</p>

<h1 align="center">技术学习知识库</h1>

<p align="center">
  面向 <b>Java 后端</b> · <b>前端</b> · <b>算法工程师</b> · <b>大数据</b> 四大方向的体系化技术学习笔记<br/>
  类 wiki 结构 · 交叉引用 · Obsidian 兼容 · 持续更新
</p>

<p align="center">
  <img src="https://img.shields.io/badge/学习文档-918%20篇-2ea44f" alt="学习文档"/>
  <img src="https://img.shields.io/badge/知识库-4%20个-0969da" alt="知识库"/>
  <img src="https://img.shields.io/badge/Spring%20Boot-8%20篇-eb6f2d" alt="Spring Boot"/>
  <img src="https://img.shields.io/badge/Obsidian-兼容-7c3aed" alt="Obsidian"/>
  <img src="https://img.shields.io/badge/更新-2026.08.14-6e7781" alt="更新"/>
</p>

## 目录

- [项目简介](#项目简介)
- [特性](#特性)
- [数据统计](#数据统计)
- [目录结构](#目录结构)
- [知识库总览](#知识库总览)
- [用 Obsidian 阅读](#用-obsidian-阅读)
- [快速开始](#快速开始)
- [文档规范](#文档规范)

## 项目简介

本仓库是一套面向 **Java 后端**、**前端**、**算法工程师**、**大数据** 四个方向的技术学习笔记。知识按体系化篇章组织，每个主题一篇独立文档；文档间以 `[[filename]]` 交叉引用，形成可增量更新、可交叉检索的知识网络。

内容索引见 [index.md](./index.md)，文档规范见 [SCHEMA.md](./SCHEMA.md)，操作记录见 [log.md](./log.md)。

## 特性

- **四大方向体系化**：Java 全栈 51 篇章、前端 103 篇章、算法工程师 20 篇章、大数据 30 篇章，另附 Spring Boot 集成专题 8 篇
- **类 wiki 交叉引用**：文档间以 `[[filename]]` 互链，从一个主题顺藤摸瓜到相关主题
- **Obsidian 原生兼容**：`[[filename]]` 双向链接 + frontmatter 标签正是 Obsidian 语法，整库可直接作为 Vault 打开
- **统一文档规范**：YAML frontmatter + 固定章节结构，全库格式一致，见 [SCHEMA.md](./SCHEMA.md)
- **可增量更新**：每篇附 `created` / `updated` 日期，操作留痕于 [log.md](./log.md)
- **附总目录 roadmap**：四份总目录文件对应四大方向，是知识库的编排蓝图，是知识库的编排蓝图

## 数据统计

| 方向 | 目录 | 篇章数 | 文档数 | 状态 |
| --- | --- | --- | --- | --- |
| Java 全栈 | [java-fullstack/](./java-fullstack/README.md) | 51（前置 + 50 篇章） | 202 | 已完成 |
| 前端完整知识库 | [frontend-fullstack/](./frontend-fullstack/README.md) | 103 | 433 | 已完成 |
| 算法工程师 | [algorithm-engineer/](./algorithm-engineer/README.md) | 20 | 142 | 已完成 |
| Spring Boot 集成 | [spring-boot/](./spring-boot/) | — | 8 | 已完成 |
| 大数据 | [bigdata/](./bigdata/README.md) | 30 | 133 | 已完成 |

合计 **918 篇**学习文档（[index.md](./index.md) 注册 920 条索引，其中 2 条为知识库入口链接）。

## 目录结构

```text
study-work/
├── java-fullstack/                  # Java 全栈学习知识库（前置 + 50 篇章 / 202 篇）
├── frontend-fullstack/              # 前端完整知识库（103 篇章 / 433 篇）
├── algorithm-engineer/              # 算法工程师知识库（20 篇章 / 142 篇）
├── spring-boot/                     # Spring Boot 集成实践（8 篇）
├── bigdata/                         # 大数据学习知识库（30 篇章 / 133 篇）
├── index.md                         # 全库内容索引（先读这里找文档）
├── SCHEMA.md                        # 文档规范（frontmatter / 标签 / 结构）
├── log.md                           # 操作日志
├── Java_全栈学习知识体系总目录.md     # Java 全栈总目录
├── 前端完整知识库总目录.md            # 前端总目录
├── 算法工程师学习知识库总目录.md      # 算法工程师总目录
└── 大数据学习知识库总目录.md          # 大数据总目录
```

## 知识库总览

### Java 全栈 — [java-fullstack/](./java-fullstack/README.md)

从 Java 语言基础、集合、并发、JVM，到 Spring Framework、Spring Boot、Spring Cloud、分布式与微服务、性能优化，共 51 章节目录（前置 + 50 篇章）、202 篇文档。

### 前端完整知识库 — [frontend-fullstack/](./frontend-fullstack/README.md)

从计算机基础、HTML/CSS/JavaScript，到 TypeScript、React/Vue、工程化、性能、安全、微前端与 AI 前端，共 103 篇章、433 篇文档。

### 算法工程师 — [algorithm-engineer/](./algorithm-engineer/README.md)

从 Python、数学、数据结构与算法，到机器学习、深度学习、CV、LLM/RAG/Agent 与工程化，共 20 篇章、142 篇文档。

### 大数据 — [bigdata/](./bigdata/README.md)

从计算机基础、SQL、Hadoop/Hive/Kafka/Spark/Flink，到数仓、Lakehouse、CDC、实时数仓、大数据算法、数据治理、云原生与企业级数据平台，共 30 篇章、133 篇文档。

### Spring Boot 集成 — [spring-boot/](./spring-boot/)

8 篇独立集成文档：Redis、Redisson、MyBatis、MyBatis-Plus、RabbitMQ、AOP、邮件、定时任务。

## 用 Obsidian 阅读

本知识库的文档用 Obsidian 原生语法编写——`[[filename]]` 双向链接 + YAML frontmatter 标签，整个仓库可以直接作为 Obsidian 库（Vault）打开，交叉引用、反向链接、关系图谱开箱即用。

1. 克隆或下载本仓库到本地
2. 打开 Obsidian → Open folder as vault → 选择 `study-work` 目录
3. 打开后即可使用：

- **双向链接**：正文里的 `[[文档名]]` 自动变为可点击链接，Ctrl/Cmd + 点击跳转
- **反向链接**：每篇文档右侧面板显示「谁引用了这篇」
- **关系图谱**：Graph view 可视化四大方向的知识网络
- **标签浏览**：frontmatter 的 tags（spring-boot、redis、distributed…）进入标签面板，点击聚合同主题文档
- **全文搜索**：Ctrl/Cmd + Shift + F 跨 918 篇文档检索

建议从 [index.md](./index.md) 开始读，或用图谱视图概览整个知识体系。

## 快速开始

1. 先读 [index.md](./index.md)，按方向找到相关文档，每篇附一句话摘要
2. 或进入对应知识库目录，读其 `README.md`（含 ascii 目录树 + 进度追踪表）
3. 或用 Obsidian 打开整个仓库（见[用 Obsidian 阅读](#用-obsidian-阅读)），获得双向链接、反向链接与关系图谱

## 文档规范

- 每篇文档以 YAML frontmatter 开头（`title` / `created` / `updated` / `type` / `tags`）
- 文件名小写英文 + 连字符（如 `spring-boot-redisson.md`），中文名仅用于标题
- 交叉引用用 `[[filename]]`（按文件名，不带路径与 `.md` 后缀）
- 新文档注册到 [index.md](./index.md)，操作追加到 [log.md](./log.md)
- 文档不出现 emoji 符号，技术术语保留英文原名，代码优先
- 完整规范见 [SCHEMA.md](./SCHEMA.md)

---

本仓库为个人学习笔记，持续更新。如发现错误，欢迎指出。
