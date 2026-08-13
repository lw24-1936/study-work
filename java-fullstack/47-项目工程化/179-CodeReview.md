---
title: Code Review
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [code-review, pr, review, 静态分析, sonarqube, code-smell, technical-debt]
---

# Code Review

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [PR 与 Review 流程](#pr-与-review-流程)
- [Review 关注点](#review-关注点)
- [静态分析工具](#静态分析工具)
- [SonarQube](#sonarqube)
- [Code Smell 与 Technical Debt](#code-smell-与-technical-debt)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Code Review 是代码质量保障的重要手段，通过同行评审发现 bug、提升质量、共享知识。

```text
Code Review 的价值：
1. 发现 bug —— 提前发现潜在问题
2. 提升质量 —— 统一代码规范
3. 知识共享 —— 团队互相学习
4. 降低风险 —— 减少线上事故
```

## PR 与 Review 流程

### PR 流程

```text
1. 开发者创建 feature 分支
2. 提交代码，创建 PR（Pull Request）
3. 指定 reviewer 评审
4. 评审意见修改
5. 通过后合并
```

```bash
# 创建分支
git checkout -b feature/user-query

# 提交并推送
git commit -m "feat(user): 添加用户查询接口"
git push origin feature/user-query

# 创建 PR（GitHub/GitLab），等待 review
```

### Review 流程

```text
1. 查看 diff（代码变更）
2. 检查功能正确性
3. 检查代码规范
4. 提出修改意见
5. 作者修改，再次 review
```

## Review 关注点

### Review 检查清单

```text
1. 正确性 —— 逻辑是否正确，边界条件是否处理
2. 安全 —— SQL 注入、XSS、敏感信息
3. 性能 —— N+1、循环拼接、不必要的查询
4. 规范 —— 命名、注释、异常处理
5. 可维护 —— 是否可读、是否过度设计
6. 测试 —— 是否有测试覆盖
```

### Review 重点

```java
// Review 发现的问题示例

// 1. 安全问题：SQL 注入
String sql = "SELECT * FROM users WHERE name = '" + name + "'";   // 应该用 #{}

// 2. 性能问题：N+1 查询
for (User user : users) {
    user.setOrders(orderMapper.findByUserId(user.getId()));   // 循环查询
}

// 3. 异常问题：吞异常
try { doSomething(); } catch (Exception e) { }   // 吞异常

// 4. 规范问题：魔法值
if (status == 1) { ... }   // 1 是什么？
```

## 静态分析工具

静态分析工具自动检查代码，发现潜在问题。

### 常见工具

```text
1. Checkstyle —— 代码风格检查
2. SpotBugs —— 潜在 bug 检查（原 FindBugs）
3. PMD —— 代码缺陷检查
4. SonarQube —— 综合（集成以上所有）
```

### 工具对比

| 工具 | 检查内容 | 特点 |
|------|---------|------|
| Checkstyle | 代码风格 | 命名、格式 |
| SpotBugs | 潜在 bug | 空指针、并发 |
| PMD | 代码缺陷 | 死代码、重复 |
| SonarQube | 综合 | 全部 + 覆盖率 |

## SonarQube

SonarQube 是综合的代码质量管理平台，集成多种静态分析。

### SonarQube 的能力

```text
1. 代码质量 —— bug、漏洞、坏味道
2. 代码覆盖率 —— 单元测试覆盖率
3. 技术债务 —— 修复成本评估
4. 质量门禁 —— 不达标不能合并
```

### 质量门禁（Quality Gate）

```text
质量门禁：代码质量不达标，CI 阻断

默认门禁：
1. 新增代码覆盖率 >= 80%
2. 无新增 bug
3. 无新增漏洞
4. 代码重复率 < 3%
```

### 集成 CI

```yaml
# GitHub Actions 集成 SonarQube
- name: SonarQube Scan
  run: mvn sonar:sonar \
    -Dsonar.host.url=$SONAR_URL \
    -Dsonar.token=$SONAR_TOKEN
```

## Code Smell 与 Technical Debt

### Code Smell 代码坏味道

代码坏味道是代码中潜在问题的迹象。

```text
常见坏味道：
1. 重复代码 —— 复制粘贴
2. 过长方法 —— 方法几百行
3. 过大类 —— 类职责太多
4. 过多参数 —— 方法参数 > 5 个
5. 魔法值 —— 硬编码数字
6. 死代码 —— 未使用的代码
```

### 常见坏味道处理

```java
// 坏味道：魔法值
if (user.getStatus() == 1) { ... }

// 重构：用枚举/常量
if (user.getStatus() == UserStatus.ACTIVE) { ... }

// 坏味道：过长方法
public void process() {
    // 500 行代码
}

// 重构：拆分方法
public void process() {
    validate();
    calculate();
    save();
}
```

### Technical Debt 技术债务

技术债务是"走捷径"累积的问题，需要未来偿还。

```text
技术债务的来源：
1. 赶工期 —— 快速实现，没时间重构
2. 复制粘贴 —— 重复代码
3. 没有测试 —— 不敢重构
4. 过时技术 —— 旧框架不升级
```

```text
管理技术债务：
1. 记录债务 —— 用 TODO/工具标记
2. 定期偿还 —— 每个迭代还一部分
3. 质量门禁 —— 防止新债务
```

## 最佳实践与踩坑记录

### 最佳实践

1. **Review 要小**。PR 太大难 review，拆小。

2. **Review 关注重点**。安全、性能、正确性优先。

3. **集成 SonarQube**。自动检查 + 质量门禁。

4. **Review 要友好**。对事不对人，提出建设性意见。

5. **及时还技术债**。定期重构，不累积。

### 踩坑记录

**坑 1：PR 太大**

```text
一个 PR 几千行，review 困难，问题漏检
```

PR 要小（几百行），拆分成多个。

**坑 2：只靠人工 review**

```text
没有静态分析，人工 review 遗漏常见问题
```

集成 SonarQube 等自动检查。

**坑 3：质量门禁形同虚设**

```text
配置了门禁但不强制（可以绕过），等于没有
```

质量门禁强制（CI 阻断合并）。

**坑 4：Review 只挑格式**

```text
只关注命名、格式，忽略逻辑、安全
```

Review 重点：安全、性能、正确性。

**坑 5：技术债无限累积**

```text
一直赶需求，从不重构，技术债滚雪球
```

定期偿还技术债，防止累积。

**坑 6：Review 变成批斗**

```text
Review 语言攻击，作者抵触，Review 流于形式
```

Review 对事不对人，建设性意见。
