---
title: Drools
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [drools, rule, fact, working-memory, agenda, drl, decision-table]
---

# Drools

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [核心概念](#核心概念)
- [DRL 规则语法](#drl-规则语法)
- [规则引擎使用](#规则引擎使用)
- [Decision Table 决策表](#decision-table-决策表)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Drools 是 Java 规则引擎，用规则（Rule）描述业务逻辑，把业务规则从代码中分离出来。

```text
规则引擎的价值：
1. 规则分离 —— 业务规则和代码解耦
2. 动态修改 —— 改规则不用改代码、重启
3. 业务可读 —— 规则接近自然语言
4. 复杂逻辑 —— 处理大量 if-else 的复杂决策
```

```text
典型场景：
1. 优惠券规则 —— 满减、折扣、限时
2. 风控规则 —— 反欺诈、信用评估
3. 积分规则 —— 积分计算
4. 定价规则 —— 动态定价
```

## 核心概念

### 规则引擎的组件

```text
1. Fact（事实）—— 输入的数据对象
2. Working Memory（工作内存）—— 存储事实
3. Rule（规则）—— when（条件）+ then（动作）
4. Agenda（议程）—— 待执行的规则队列
5. Rule Base（规则库）—— 所有规则的集合
```

### 执行流程

```text
1. 插入事实（Fact）到 Working Memory
2. 匹配规则（when 条件满足）
3. 规则进入 Agenda
4. 执行规则（then 动作）
5. 可能修改事实，重新匹配
```

## DRL 规则语法

DRL（Drools Rule Language）是 Drools 的规则语言。

### 规则文件（.drl）

```java
// rules/discount.drl
package com.example.rules;

import com.example.Order;

// 规则：满 100 减 10
rule "满100减10"
    when
        $order: Order(amount >= 100)
    then
        $order.setDiscount(10);
        System.out.println("满 100 减 10");
end

// 规则：满 500 减 80
rule "满500减80"
    when
        $order: Order(amount >= 500)
    then
        $order.setDiscount(80);
end
```

### 语法结构

```text
rule "规则名"
    when
        条件（LHS，Left Hand Side）
    then
        动作（RHS，Right Hand Side）
end
```

### when 条件（LHS）

```java
// 对象匹配
$order: Order(amount >= 100)

// 属性条件
Order(amount >= 100, status == "PAID")

// 多对象
$order: Order(amount >= 100)
$user: User(vip == true)

// 逻辑运算
Order(amount >= 100 && amount < 500 || type == "special")
```

### then 动作（RHS）

```java
// 修改对象属性
$order.setDiscount(10);

// 插入新事实
insert(new Result("discount", 10));

// 修改事实（触发重新匹配）
modify($order) { setDiscount(10) };
```

## 规则引擎使用

### 依赖

```xml
<dependency>
    <groupId>org.drools</groupId>
    <artifactId>drools-core</artifactId>
    <version>8.44.0.Final</version>
</dependency>
```

### 加载和执行规则

```java
// 1. 加载规则
KieServices ks = KieServices.Factory.get();
KieContainer container = ks.getKieClasspathContainer();
KieSession session = container.newKieSession("rules-session");

// 2. 插入事实
Order order = new Order(200, 0);
session.insert(order);

// 3. 执行规则
session.fireAllRules();

// 4. 获取结果
System.out.println(order.getDiscount());   // 10

// 5. 释放
session.dispose();
```

### Spring Boot 集成

```java
@Configuration
public class DroolsConfig {

    @Bean
    public KieSession kieSession() {
        KieServices ks = KieServices.Factory.get();
        KieContainer container = ks.getKieClasspathContainer();
        return container.newKieSession("rules-session");
    }
}

@Service
public class DiscountService {

    @Autowired
    private KieSession kieSession;

    public void applyDiscount(Order order) {
        kieSession.insert(order);
        kieSession.fireAllRules();
    }
}
```

## Decision Table 决策表

决策表用 Excel 定义规则，业务人员可以直接维护。

### 决策表（Excel）

```text
Excel 决策表结构：
规则名 | 条件1（金额>=）| 条件2（会员）| 结果（折扣）
满100减10 | 100 | - | 10
满500减80 | 500 | - | 80
会员9折  | - | true | 0.9
```

### 加载决策表

```java
// 决策表转 DRL，再加载
Resource resource = ResourceFactory.newClassPathResource("rules/discount.xlsx");
KieHelper helper = new KieHelper();
helper.addResource(resource, ResourceType.DTABLE);
KieBase base = helper.build();
```

### 决策表的优势

```text
1. 业务可维护 —— 业务人员用 Excel 维护规则
2. 规则可视化 —— 表格清晰
3. 批量规则 —— 大量相似规则
```

## 应用场景实战

### 场景 1：优惠券规则

```java
// discount.drl
rule "满100减10"
    when
        $order: Order(amount >= 100, amount < 500)
    then
        $order.setDiscount(10);
end

rule "满500减80"
    when
        $order: Order(amount >= 500)
    then
        $order.setDiscount(80);
end

rule "会员额外95折"
    when
        $order: Order()
        $user: User(vip == true)
    then
        $order.setDiscount($order.getDiscount() + $order.getAmount() * 0.05);
end
```

### 场景 2：风控规则

```java
// risk.drl
rule "异常IP"
    when
        $login: LoginEvent(ip in ("1.2.3.4", "5.6.7.8"))
    then
        $login.setRiskLevel("HIGH");
end

rule "频繁登录"
    when
        $login: LoginEvent(loginCount > 10)
    then
        $login.setRiskLevel("HIGH");
end
```

### 场景 3：积分计算

```java
rule "消费积分"
    when
        $order: Order(amount >= 0)
    then
        int points = $order.getAmount() / 10;   // 每 10 元 1 积分
        $order.setPoints(points);
end
```

## 最佳实践与踩坑记录

### 最佳实践

1. **规则文件单独管理**。规则放 resources/rules 目录，和代码分离。

2. **决策表给业务维护**。大量简单规则用 Excel 决策表。

3. **规则要幂等**。规则可能重复执行，动作要幂等。

4. **规则测试**。用 KieHelper 单元测试规则。

5. **注意 modify 的循环**。modify 触发重新匹配，可能死循环。

### 踩坑记录

**坑 1：modify 导致死循环**

```java
rule "循环"
    when
        $order: Order(amount > 0)
    then
        modify($order) { setAmount($order.getAmount() + 1) };  // 条件又满足，无限循环
end
```

modify 前要确保条件会变 false，或用 no-loop 属性。

**坑 2：规则顺序不确定**

```text
多个规则同时满足，执行顺序不确定
```

用 salience（优先级）或 agenda-group 控制顺序。

**坑 3：规则文件路径错误**

```java
ResourceFactory.newClasspathResource("discount.drl");   // 路径错误
```

规则文件在 resources/rules/ 下，路径要正确。

**坑 4：规则对象属性名拼写错误**

```java
Order(amout >= 100)   // 拼写错误（amount），匹配不到
```

属性名要和 Java 对象的 getter 对应。

**坑 5：规则引擎滥用**

```text
简单 if-else 也用规则引擎，增加复杂度
```

规则引擎适合复杂多变的规则，简单逻辑用代码。

**坑 6：忘记 dispose session**

```java
KieSession session = container.newKieSession();
// 用完后没 dispose，内存泄漏
```

session 用完要 dispose()。
