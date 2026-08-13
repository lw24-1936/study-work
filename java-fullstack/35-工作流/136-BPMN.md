---
title: BPMN
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [bpmn, process, task, gateway, event, sequence-flow]
---

# BPMN

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [BPMN 核心元素](#bpmn-核心元素)
- [Task 任务](#task-任务)
- [Gateway 网关](#gateway-网关)
- [Event 事件](#event-事件)
- [Sequence Flow 顺序流](#sequence-flow-顺序流)
- [应用场景实战](#应用场景实战)

## 概述

BPMN（Business Process Model and Notation）是业务流程建模的标准，用图形化符号描述业务流程。

```text
BPMN 是什么：
1. 标准 —— OMG 制定的业务流程建模规范
2. 图形化 —— 用图形符号描述流程
3. 可执行 —— 配合引擎（Flowable）可执行
```

```text
BPMN 的价值：
1. 业务和技术沟通的桥梁 —— 业务画图，技术实现
2. 流程可视化 —— 流程一目了然
3. 可执行 —— BPMN 图可直接被流程引擎执行
```

## BPMN 核心元素

### 五大核心元素

```text
1. 事件（Event）—— 流程的开始、结束、中间事件
2. 任务（Task）—— 要执行的工作
3. 网关（Gateway）—— 流程分支、汇聚
4. 顺序流（Sequence Flow）—— 连接元素的有向线
5. 泳道（Lane/Pool）—— 参与者/角色划分
```

```text
图形符号：
○ 圆        —— 事件（Event）
□ 圆角矩形   —— 任务（Task）
◇ 菱形       —— 网关（Gateway）
→ 箭头       —— 顺序流（Sequence Flow）
```

### 一个简单的 BPMN 流程

```xml
<process id="leaveProcess" name="请假流程">
    <startEvent id="start"/>
    <userTask id="apply" name="提交申请"/>
    <userTask id="approve" name="审批"/>
    <endEvent id="end"/>
    <sequenceFlow id="f1" sourceRef="start" targetRef="apply"/>
    <sequenceFlow id="f2" sourceRef="apply" targetRef="approve"/>
    <sequenceFlow id="f3" sourceRef="approve" targetRef="end"/>
</process>
```

```text
流程：开始 → 提交申请 → 审批 → 结束
```

## Task 任务

任务（Task）是流程中要执行的工作单元。

### 任务类型

| 任务 | 说明 | 执行方式 |
|------|------|---------|
| User Task | 用户任务 | 人工处理（审批） |
| Service Task | 服务任务 | 自动调用（Java 方法） |
| Script Task | 脚本任务 | 执行脚本 |
| Manual Task | 手动任务 | 线下人工 |
| Send Task | 发送任务 | 发送消息 |

### User Task（用户任务）

```xml
<userTask id="approve" name="审批"
    flowable:assignee="${approver}"/>   <!-- 指定审批人 -->
```

```text
User Task：需要人工处理（审批、确认）
- assignee —— 指定处理人
- candidateUsers —— 候选处理人
```

### Service Task（服务任务）

```xml
<serviceTask id="sendNotify" name="发送通知"
    flowable:class="com.example.NotifyDelegate"/>   <!-- 指定 Java 类 -->
```

```java
// 服务任务对应的 Java 类
public class NotifyDelegate implements JavaDelegate {
    @Override
    public void execute(DelegateExecution execution) {
        // 自动执行
        System.out.println("发送通知");
    }
}
```

## Gateway 网关

网关（Gateway）控制流程的分支和汇聚。

### 网关类型

| 网关 | 说明 | 场景 |
|------|------|------|
| Exclusive | 排他网关（二选一） | 条件分支 |
| Parallel | 并行网关（同时执行） | 并行任务 |
| Inclusive | 包容网关（多选） | 多条件分支 |
| Event-based | 事件网关 | 等待事件 |

### 排他网关（Exclusive）

```text
排他网关：只走一个分支（类似 if-else）
```

```xml
<exclusiveGateway id="gateway1"/>
<sequenceFlow id="f1" sourceRef="gateway1" targetRef="approve">
    <conditionExpression>${amount < 1000}</conditionExpression>
</sequenceFlow>
<sequenceFlow id="f2" sourceRef="gateway1" targetRef="managerApprove">
    <conditionExpression>${amount >= 1000}</conditionExpression>
</sequenceFlow>
```

### 并行网关（Parallel）

```text
并行网关：所有分支同时执行（类似 fork/join）
```

```xml
<parallelGateway id="fork"/>
<!-- 分叉：三个任务同时执行 -->
<sequenceFlow sourceRef="fork" targetRef="task1"/>
<sequenceFlow sourceRef="fork" targetRef="task2"/>
<sequenceFlow sourceRef="fork" targetRef="task3"/>

<parallelGateway id="join"/>
<!-- 汇聚：等所有任务完成后继续 -->
<sequenceFlow sourceRef="task1" targetRef="join"/>
<sequenceFlow sourceRef="task2" targetRef="join"/>
<sequenceFlow sourceRef="task3" targetRef="join"/>
```

## Event 事件

事件（Event）标记流程的开始、结束和中间状态。

### 事件类型

```text
开始事件（Start Event）—— 流程起点
结束事件（End Event）—— 流程终点
中间事件（Intermediate Event）—— 流程中的事件
```

### 开始事件

```xml
<startEvent id="start"/>                          <!-- 普通开始 -->
<startEvent id="start" flowable:initiator="initiator"/>  <!-- 记录发起人 -->
```

### 结束事件

```xml
<endEvent id="end"/>                              <!-- 普通结束 -->
<terminateEndEvent id="end"/>                     <!-- 终止（立即结束整个流程） -->
```

### 定时事件

```xml
<!-- 定时器中间事件：等待指定时间 -->
<intermediateCatchEvent id="wait">
    <timerEventDefinition>
        <timeDuration>PT1H</timeDuration>   <!-- 等待 1 小时 -->
    </timerEventDefinition>
</intermediateCatchEvent>
```

## Sequence Flow 顺序流

顺序流（Sequence Flow）连接流程元素，表示执行顺序。

### 顺序流类型

```text
1. 普通顺序流 —— 无条件，直接流转
2. 条件顺序流 —— 带条件（conditionExpression）
```

### 条件表达式

```xml
<sequenceFlow id="f1" sourceRef="gateway" targetRef="task1">
    <conditionExpression>${amount > 1000}</conditionExpression>
</sequenceFlow>
```

```text
条件表达式用 UEL（统一表达式语言）：
${amount > 1000}       —— 变量判断
${status == 'APPROVED'} —— 字符串比较
```

### 默认顺序流

```xml
<!-- 默认流：所有条件都不满足时走这条 -->
<sequenceFlow id="default" sourceRef="gateway" targetRef="defaultTask"/>
```

## 应用场景实战

### 场景 1：请假审批流程

```xml
<process id="leaveProcess" name="请假流程">
    <startEvent id="start"/>

    <userTask id="apply" name="提交请假申请"
        flowable:assignee="${applicant}"/>

    <!-- 排他网关：根据请假天数分支 -->
    <exclusiveGateway id="gateway"/>

    <!-- 3 天以内：直接经理审批 -->
    <userTask id="managerApprove" name="经理审批"
        flowable:assignee="manager"/>

    <!-- 3 天以上：经理 + 总监审批 -->
    <userTask id="directorApprove" name="总监审批"
        flowable:assignee="director"/>

    <endEvent id="end"/>

    <sequenceFlow sourceRef="start" targetRef="apply"/>
    <sequenceFlow sourceRef="apply" targetRef="gateway"/>
    <sequenceFlow sourceRef="gateway" targetRef="managerApprove">
        <conditionExpression>${days <= 3}</conditionExpression>
    </sequenceFlow>
    <sequenceFlow sourceRef="gateway" targetRef="directorApprove">
        <conditionExpression>${days > 3}</conditionExpression>
    </sequenceFlow>
    <sequenceFlow sourceRef="managerApprove" targetRef="end"/>
    <sequenceFlow sourceRef="directorApprove" targetRef="end"/>
</process>
```

### 场景 2：订单处理流程（含并行）

```xml
<process id="orderProcess" name="订单处理">
    <startEvent id="start"/>
    <userTask id="confirm" name="确认订单"/>

    <parallelGateway id="fork"/>
    <serviceTask id="deductStock" name="扣库存" flowable:class="..."/>
    <serviceTask id="sendNotify" name="发通知" flowable:class="..."/>
    <parallelGateway id="join"/>

    <endEvent id="end"/>
    <!-- 扣库存和发通知并行执行 -->
</process>
```

## 最佳实践与踩坑记录

### 最佳实践

1. **流程先画图再实现**。用 BPMN 建模工具（Flowable Modeler）可视化设计。

2. **条件表达式用 UEL**。`${amount > 1000}` 简洁清晰。

3. **复杂分支用排他网关**。避免多个条件顺序流混乱。

4. **并行任务用并行网关**。fork/join 清晰表达并行。

5. **审批类任务用 User Task**。指定 assignee 或 candidateUsers。

### 踩坑记录

**坑 1：排他网关没有默认流**

```xml
<exclusiveGateway id="gateway"/>
<!-- 条件都没匹配，流程卡死 -->
```

排他网关要设置默认流（default flow）。

**坑 2：并行网关缺 join**

```text
只有 fork 没有 join，分支执行完流程不继续
```

并行网关要成对（fork + join）。

**坑 3：条件表达式语法错误**

```xml
<conditionExpression>${amount > 1000}</conditionExpression>
<!-- 变量名错误或语法错误，流程走默认流 -->
```

条件表达式的变量名要和流程变量一致。

**坑 4：User Task 没指定处理人**

```xml
<userTask id="approve" name="审批"/>
<!-- 没 assignee，任务无人处理 -->
```

User Task 要指定 assignee 或 candidateUsers。

**坑 5：Service Task 类路径错误**

```xml
<serviceTask flowable:class="com.example.NotifyDelegate"/>
<!-- 类不存在，执行报错 -->
```

Service Task 的类路径要正确，类实现 JavaDelegate。

**坑 6：流程变量未设置**

```text
条件表达式引用未设置的变量，判断为 false，走默认流
```

启动流程时设置所有需要的流程变量。
