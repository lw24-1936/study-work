<p align="center">
  <a href="./README.md">简体中文</a> ·
  <a href="./README.en.md">English</a>
</p>

<h1 align="center">Tech Learning Knowledge Base</h1>

<p align="center">
  Structured technical study notes for <b>Java Backend</b> · <b>Frontend</b> · <b>Algorithm Engineer</b> · <b>Big Data</b> · <b>Linux Operations</b><br/>
  Wiki-style structure · Cross-referencing · Obsidian-compatible · Continuously updated
</p>

<p align="center">
  <img src="https://img.shields.io/badge/docs-1046-2ea44f" alt="docs"/>
  <img src="https://img.shields.io/badge/knowledge%20bases-5-0969da" alt="knowledge bases"/>
  <img src="https://img.shields.io/badge/Spring%20Boot-8-eb6f2d" alt="Spring Boot"/>
  <img src="https://img.shields.io/badge/Obsidian-compatible-7c3aed" alt="Obsidian"/>
  <img src="https://img.shields.io/badge/updated-2026.08.19-6e7781" alt="updated"/>
</p>

## Table of Contents

- [About](#about)
- [Highlights](#highlights)
- [Statistics](#statistics)
- [Directory Structure](#directory-structure)
- [Knowledge Bases](#knowledge-bases)
- [Reading with Obsidian](#reading-with-obsidian)
- [Getting Started](#getting-started)
- [Writing Conventions](#writing-conventions)

## About

This repository is a collection of structured technical study notes for five tracks: **Java Backend**, **Frontend**, **Algorithm Engineer**, **Big Data**, and **Linux Operations**. Knowledge is organized into systematic chapters, with one standalone document per topic. Documents cross-reference each other via `[[filename]]`, forming an incrementally updatable, cross-searchable knowledge network.

See [index.md](./index.md) for the content index, [SCHEMA.md](./SCHEMA.md) for writing conventions, and [log.md](./log.md) for the changelog.

## Highlights

- **Five systematic tracks**: 51 chapters of Java Full-Stack, 103 chapters of Frontend, 20 chapters of Algorithm Engineer, 30 chapters of Big Data, 26 chapters of Linux Operations, plus 8 Spring Boot integration guides
- **Wiki-style cross-referencing**: documents link to each other via `[[filename]]`, so you can follow a topic to related ones
- **Obsidian-native**: `[[filename]]` backlinks + frontmatter tags are Obsidian syntax, so the whole repo opens directly as a Vault
- **Unified conventions**: YAML frontmatter + fixed section structure keep the whole library consistent, see [SCHEMA.md](./SCHEMA.md)
- **Incremental updates**: every document carries `created` / `updated` dates, and every operation is logged in [log.md](./log.md)
- **Roadmaps included**: five roadmap files outline the five tracks

## Statistics

| Track | Directory | Chapters | Documents | Status |
| --- | --- | --- | --- | --- |
| Java Full-Stack | [java-fullstack/](./java-fullstack/README.md) | 51 (preface + 50 chapters) | 202 | Complete |
| Frontend | [frontend-fullstack/](./frontend-fullstack/README.md) | 103 | 433 | Complete |
| Algorithm Engineer | [algorithm-engineer/](./algorithm-engineer/README.md) | 20 | 142 | Complete |
| Spring Boot Integration | [spring-boot/](./spring-boot/) | — | 8 | Complete |
| Big Data | [bigdata/](./bigdata/README.md) | 30 | 133 | Complete |
| Linux Operations | [linux/](./linux/README.md) | 26 | 128 | Complete |

**1046 documents** in total ([index.md](./index.md) registers 1050 entries, 3 of which are knowledge-base entry links).

## Directory Structure

```text
study-work/
├── java-fullstack/                  # Java Full-Stack knowledge base (preface + 50 chapters / 202 docs)
├── frontend-fullstack/              # Frontend knowledge base (103 chapters / 433 docs)
├── algorithm-engineer/              # Algorithm Engineer knowledge base (20 chapters / 142 docs)
├── spring-boot/                     # Spring Boot integration guides (8 docs)
├── bigdata/                         # Big Data knowledge base (30 chapters / 133 docs)
├── linux/                            # Linux Operations knowledge base (26 chapters / 128 docs)
├── index.md                         # Content index (start here to find documents)
├── SCHEMA.md                        # Writing conventions (frontmatter / tags / structure)
├── log.md                           # Changelog
├── Java_全栈学习知识体系总目录.md     # Java Full-Stack roadmap
├── 前端完整知识库总目录.md            # Frontend roadmap
├── 算法工程师学习知识库总目录.md      # Algorithm Engineer roadmap
├── 大数据学习知识库总目录.md          # Big Data roadmap
└── Linux学习知识库总目录.md           # Linux roadmap
```

## Knowledge Bases

### Java Full-Stack — [java-fullstack/](./java-fullstack/README.md)

From Java language fundamentals, collections, concurrency, and JVM, to Spring Framework, Spring Boot, Spring Cloud, distributed systems, microservices, and performance tuning — 51 chapter directories (preface + 50 chapters) and 202 documents.

### Frontend — [frontend-fullstack/](./frontend-fullstack/README.md)

From computer fundamentals, HTML/CSS/JavaScript, to TypeScript, React/Vue, engineering, performance, security, micro-frontends, and AI frontend — 103 chapters and 433 documents.

### Algorithm Engineer — [algorithm-engineer/](./algorithm-engineer/README.md)

From Python, mathematics, data structures and algorithms, to machine learning, deep learning, CV, LLM/RAG/Agent, and engineering — 20 chapters and 142 documents.

### Big Data — [bigdata/](./bigdata/README.md)

From computer fundamentals, SQL, Hadoop/Hive/Kafka/Spark/Flink, to data warehouse, Lakehouse, CDC, real-time warehouse, big data algorithms, data governance, cloud-native, and enterprise data platform — 30 chapters and 133 documents.

### Linux Operations — [linux/](./linux/README.md)

From the command line, Shell scripting, and the text-processing trio, to user permissions, file systems, processes and memory, networking and firewalls, logging and monitoring, performance tuning, and troubleshooting — and on to virtualization and containers, automation, security hardening, kernel and eBPF, interviews and system design, and hands-on projects — 26 chapters and 128 documents.

### Spring Boot Integration — [spring-boot/](./spring-boot/)

8 standalone integration guides: Redis, Redisson, MyBatis, MyBatis-Plus, RabbitMQ, AOP, Email, and Scheduled Tasks.

## Reading with Obsidian

The documents use Obsidian-native syntax — `[[filename]]` backlinks + YAML frontmatter tags — so the whole repository can be opened directly as an Obsidian Vault, with cross-references, backlinks, and graph view working out of the box.

1. Clone or download this repository locally
2. Open Obsidian → Open folder as vault → select the `study-work` directory
3. Once open, you get:

- **Backlinks**: `[[document name]]` references become clickable links; Ctrl/Cmd + click to jump
- **Backlink panel**: each document shows "what links here"
- **Graph view**: visualize the knowledge network across the five tracks
- **Tag browsing**: frontmatter tags (spring-boot, redis, distributed…) appear in the tag pane; click to group related documents
- **Full-text search**: Ctrl/Cmd + Shift + F across all 1046 documents

Start with [index.md](./index.md), or use graph view to survey the whole system.

## Getting Started

1. Start with [index.md](./index.md) and pick a track — every document has a one-line summary
2. Or enter a knowledge-base directory and read its `README.md` (ascii directory tree + progress tracker)
3. Or open the whole repository in Obsidian (see [Reading with Obsidian](#reading-with-obsidian)) for backlinks, the backlink panel, and graph view

## Writing Conventions

- Every document starts with a YAML frontmatter (`title` / `created` / `updated` / `type` / `tags`)
- File names are lowercase English with hyphens (e.g. `spring-boot-redisson.md`); Chinese names are used for titles only
- Cross-references use `[[filename]]` (by file name, without path or `.md` extension)
- New documents are registered in [index.md](./index.md); every operation is appended to [log.md](./log.md)
- No emoji in documents; technical terms keep their English names; code first
- Full conventions in [SCHEMA.md](./SCHEMA.md)

---

This repository contains personal study notes and is continuously updated. Corrections are welcome.
