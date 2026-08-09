# SCHEMA.md

## 领域

Java 后端技术学习笔记，涵盖框架集成、中间件使用、分布式架构、设计模式等。
目的是将零散的学习总结变成可交叉引用、可增量更新的结构化知识库。

## 约定

- 文件名：小写英文 + 连字符（如 `spring-boot-redisson.md`），中文名仅用于显示标题
- 每篇文档以 YAML frontmatter 开头（见下方格式）
- 用 `[[filename]]` 做交叉引用，最少 1 个出站链接
- 更新文档时更新 `updated` 日期
- 所有新文档必须注册到 `index.md`
- 所有操作追加到 `log.md`
- 整理日期为 `created`，最后一次修改为 `updated`

## Frontmatter

```yaml
---
title: 文档标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: integration | concept | comparison | troubleshooting
tags: [redis, spring-boot, distributed]
sources: []
---
```

## 标签分类

- **框架/工具**：spring-boot, spring-cloud, mybatis, redis, kafka, rabbitmq, elasticsearch, docker, kubernetes
- **中间件**：redis, kafka, rabbitmq, nginx, zookeeper, nacos, sentinel
- **概念**：distributed, microservices, concurrency, cache, message-queue, design-pattern
- **类型**：integration, concept, comparison, troubleshooting, best-practice

规则：标签先加到这里，再用到文档里。

## 页面阈值

- **创建新文档**：一个技术主题足够独立、需要代码示例和场景说明时
- **补充已有文档**：内容与已有文档高度关联时，直接追加章节
- **拆分为独立文档**：单篇超过 300 行时考虑拆分

## 文档结构规范

每篇学习文档建议包含以下章节：

1. 概述（是什么、解决什么问题）
2. 环境搭建（依赖、配置）
3. 核心用法（代码示例）
4. 应用场景（至少 2 个完整场景）
5. 踩坑记录（常见问题 + 解决方案）
6. 参考链接（官方文档、源码）

## 编辑原则

- 代码块标注语言类型，确保高亮正确
- 配置项附说明注释，不要只贴配置
- 场景示例必须是可运行的完整代码片段
- 对比用表格，不写长篇对比文字
- 不使用 emoji 作为装饰符号，保持专业简洁
