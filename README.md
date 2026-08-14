# 技术学习知识库

整理日期：2026-08-14

本仓库是面向 Java 后端、前端、算法工程师三个方向的技术学习笔记，类 wiki 结构，支持交叉引用与增量更新。内容索引见 `index.md`，文档规范见 `SCHEMA.md`，操作记录见 `log.md`。

## 知识库总览

| 知识库 | 目录 | 篇章数 | 文档数 | 状态 |
|--------|------|--------|--------|------|
| Java 全栈 | `java-fullstack/` | 51（前置 + 50 篇章） | 202 | 已完成 |
| 前端完整知识库 | `frontend-fullstack/` | 103 | 433 | 已完成 |
| 算法工程师 | `algorithm-engineer/` | 20 | 142 | 已完成 |
| Spring Boot 集成 | `spring-boot/` | — | 8 | 已完成 |

合计 785 篇学习文档（`index.md` 注册 787 条索引，含 2 个知识库入口链接）。

## 目录结构

```text
study-work/
├── java-fullstack/                  # Java 全栈学习知识库（前置 + 50 篇章 / 202 篇）
├── frontend-fullstack/              # 前端完整知识库（103 篇章 / 433 篇）
├── algorithm-engineer/              # 算法工程师知识库（20 篇章 / 142 篇）
├── spring-boot/                     # Spring Boot 集成实践（8 篇）
├── index.md                         # 全库内容索引（先读这里找文档）
├── SCHEMA.md                        # 文档规范（frontmatter / 标签 / 结构）
├── log.md                           # 操作日志
├── Java_全栈学习知识体系总目录.md    # Java 全栈总目录
├── 前端完整知识库总目录.md           # 前端总目录
├── 算法工程师学习知识库总目录.md     # 算法工程师总目录
└── 大数据学习知识库总目录.md         # 大数据总目录（知识库尚未搭建）
```

## 快速开始

1. 先读 `index.md`，按方向找到相关文档（每篇附一句话摘要）
2. 或进入对应知识库目录，读其 `README.md`（含 ascii 目录树 + 进度追踪表）

## 文档规范

- 每篇文档以 YAML frontmatter 开头（`title` / `created` / `updated` / `type` / `tags`）
- 文件名小写英文 + 连字符（如 `spring-boot-redisson.md`），中文名仅用于标题
- 交叉引用用 `[[filename]]`（按文件名，不带路径与 `.md` 后缀）
- 新文档注册到 `index.md`，操作追加到 `log.md`
- 文档不出现 emoji 符号，技术术语保留英文原名，代码优先
- 完整规范见 `SCHEMA.md`
