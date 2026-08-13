---
title: AI Agent
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [ai-agent, tool, tool-calling, function-calling, agent-memory, planning, reasoning, multi-agent]
---

# AI Agent

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [Agent 的核心组成](#agent-的核心组成)
- [Tool 与 Tool Calling](#tool-与-tool-calling)
- [Agent Memory 记忆](#agent-memory-记忆)
- [Planning 与 Reasoning](#planning-与-reasoning)
- [Workflow Agent 与 Multi-Agent](#workflow-agent-与-multi-agent)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

AI Agent 是能自主决策、调用工具、执行任务的智能体，是 LLM 从"聊天"到"干活"的进化。

```text
LLM vs Agent：
LLM —— 只会聊天（输入文本，输出文本）
Agent —— 能干活（自主规划、调用工具、执行任务）
```

```text
Agent 的典型能力：
1. 调用工具 —— 查数据库、调 API、执行代码
2. 自主规划 —— 拆解任务、分步执行
3. 记忆 —— 记住上下文、历史
4. 反思 —— 评估结果、调整策略
```

```text
Agent 的典型应用：
1. 智能客服 —— 查订单、退换货
2. 代码助手 —— 写代码、调试、提交
3. 数据分析 —— 查数据、生成报告
4. 自动化办公 —— 发邮件、安排日程
```

## Agent 的核心组成

### Agent 四要素

```text
1. LLM（大脑）—— 理解、推理、决策
2. Tool（工具）—— 执行操作（查库、调 API）
3. Memory（记忆）—— 上下文、历史
4. Planning（规划）—— 任务拆解、执行策略
```

```text
Agent 工作流程：
用户任务 → LLM 理解 → 规划（拆解任务）→ 调用工具 → 观察结果 → 反思调整 → 完成
```

## Tool 与 Tool Calling

Tool（工具）是 Agent 执行操作的能力，通过 Function Calling 实现。

### Tool 是什么

```text
Tool = 函数（Function），Agent 可以调用来执行操作

工具类型：
1. 查询工具 —— 查数据库、查天气、查股价
2. 操作工具 —— 发邮件、下单、执行代码
3. 计算工具 —— 数学计算
```

### Tool 定义（Spring AI）

```java
// 定义工具（用 @Tool 注解）
public class WeatherTools {

    @Tool(description = "查询指定城市的天气")
    public String getWeather(@ToolParam(description = "城市名") String city) {
        return weatherService.getWeather(city);
    }
}

// 注册工具
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultTools(new WeatherTools())   // 注册工具
    .build();
```

### Tool Calling 流程

```text
1. 用户："北京天气怎么样？"
2. Agent 识别需要调用 getWeather 工具
3. 调用 getWeather("北京")，得到结果
4. Agent 综合结果回答
```

### Function Calling 与 Tool Calling

```text
本质相同：让 LLM 调用外部函数
Function Calling —— LLM API 层面的能力
Tool Calling —— Agent 框架层面的封装（更高级）
```

## Agent Memory 记忆

Memory 让 Agent 记住上下文和历史。

### 记忆类型

```text
1. 短期记忆 —— 当前对话上下文（Context Window）
2. 长期记忆 —— 历史对话（存数据库/向量库）
3. 工作记忆 —— 任务执行中的中间状态
```

### 记忆的实现

```text
短期记忆：对话历史传入 prompt
长期记忆：历史对话存向量库，检索相关历史
```

```java
// 短期记忆：传历史对话
List<Message> history = getConversationHistory(userId);
String response = chatClient.prompt()
    .messages(history)      // 历史（短期记忆）
    .user(currentMessage)
    .call()
    .content();
```

## Planning 与 Reasoning

Planning（规划）和 Reasoning（推理）让 Agent 拆解复杂任务。

### Planning 模式

```text
1. ReAct —— 推理 + 行动交替（Reasoning + Acting）
2. Chain of Thought —— 逐步思考
3. Plan and Execute —— 先规划再执行
```

### ReAct 模式

```text
ReAct = 思考（Thought）→ 行动（Action）→ 观察（Observation）循环

Thought：我需要查用户的订单
Action：调用 getOrders(userId)
Observation：返回 3 个订单
Thought：用户要取消订单 1
Action：调用 cancelOrder(orderId=1)
Observation：取消成功
Answer：订单已取消
```

### Reasoning 推理

```text
推理能力让 Agent 能：
1. 分析 —— 理解问题本质
2. 拆解 —— 把大任务拆成小步骤
3. 决策 —— 选择执行方案
4. 反思 —— 评估结果、纠错
```

## Workflow Agent 与 Multi-Agent

### Workflow Agent（工作流）

```text
Workflow Agent：按固定流程执行（可预测、可控）
适合：明确的业务流程（审批、数据处理）
```

### Multi-Agent（多智能体）

```text
Multi-Agent：多个 Agent 协作，各司其职
适合：复杂任务（一个 Agent 拆解，多个 Agent 执行）
```

```text
多智能体模式：
1. 主从模式 —— 主 Agent 调度，从 Agent 执行
2. 协作模式 —— 多个 Agent 平等协作
3. 竞争模式 —— 多个 Agent 竞争，择优
```

### 框架

```text
Java Agent 框架：
1. Spring AI —— Spring 官方，集成 Agent 能力
2. LangChain4j —— LangChain 的 Java 版
3. 自研 —— 基于 Function Calling 自己实现
```

## 应用场景实战

### 场景 1：智能客服 Agent

```java
// 客服 Agent：查订单、退换货、解答问题
public class CustomerServiceAgent {

    @Tool(description = "查询用户订单")
    public List<Order> getOrders(@ToolParam Long userId) {
        return orderService.getByUser(userId);
    }

    @Tool(description = "取消订单")
    public boolean cancelOrder(@ToolParam Long orderId) {
        return orderService.cancel(orderId);
    }

    // Agent 自动判断调用哪个工具
    public String handle(String question, Long userId) {
        return chatClient.prompt()
            .system("你是客服，可以查询和取消订单")
            .user(question)
            .call()
            .content();
    }
}
```

### 场景 2：数据分析 Agent

```java
// 数据分析 Agent：查数据、计算、生成报告
public class DataAnalysisAgent {

    @Tool(description = "查询销售数据")
    public List<Sale> querySales(@ToolParam String dateRange) {
        return saleService.query(dateRange);
    }

    @Tool(description = "计算统计指标")
    public Map<String, Object> calculate(List<Sale> sales) {
        // 计算总额、均值等
        return statisticsService.calculate(sales);
    }
}
```

### 场景 3：Multi-Agent 协作

```text
任务：市场调研报告

规划 Agent：拆解任务（市场分析、竞品分析、趋势分析）
研究 Agent 1：市场分析
研究 Agent 2：竞品分析
研究 Agent 3：趋势分析
汇总 Agent：整合成报告
```

## 最佳实践与踩坑记录

### 最佳实践

1. **工具描述要清晰**。@Tool 的 description 要准确，模型才能正确调用。

2. **工具要幂等**。Agent 可能重复调用工具。

3. **危险操作要确认**。删除、支付等操作要人工确认。

4. **限制工具权限**。Agent 只能调用授权的工具。

5. **记录执行日志**。Agent 的每一步决策和工具调用要可追溯。

### 踩坑记录

**坑 1：工具描述模糊导致调用错误**

```java
@Tool(description = "查询")   // 描述太模糊，模型不知道这工具干嘛的
public Object query(String param) { ... }
```

工具描述要具体（查什么、参数是什么）。

**坑 2：无限循环调用工具**

```text
Agent 反复调用工具，陷入死循环（没有终止条件）
```

设置最大迭代次数，或让 Agent 判断任务完成。

**坑 3：危险操作自动执行**

```java
@Tool(description = "删除用户")
public void deleteUser(Long id) { ... }
// Agent 误判，直接删除用户
```

危险操作要人工确认，工具要校验权限。

**坑 4：上下文超限**

```text
多轮工具调用，上下文累积超限
```

控制工具返回结果的大小，及时总结历史。

**坑 5：工具返回结果过大**

```text
工具返回几万行数据，塞进上下文，超限且成本高
```

工具返回精简结果，或让 Agent 用工具分页查询。

**坑 6：幻觉调用工具**

```text
Agent 编造工具调用（幻觉），或调用不存在的工具
```

校验工具调用，用结构化的 Function Calling。
