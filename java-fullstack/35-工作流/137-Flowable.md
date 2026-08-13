---
title: Flowable
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [flowable, 流程部署, 流程启动, 用户任务, 服务任务, 网关, 会签, 或签, 流程变量, 历史任务]
---

# Flowable

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [依赖与配置](#依赖与配置)
- [流程部署](#流程部署)
- [流程启动](#流程启动)
- [任务处理](#任务处理)
- [网关与会签或签](#网关与会签或签)
- [流程变量与历史](#流程变量与历史)
- [应用场景实战](#应用场景实战)

## 概述

Flowable 是 Java 工作流引擎，执行 BPMN 定义的流程，是 Activiti 的分支（Activiti 核心团队创立）。

```text
Flowable 是什么：
1. 工作流引擎 —— 执行 BPMN 流程
2. 轻量级 —— 嵌入 Java 应用
3. 开源 —— Apache 2.0 协议
4. 功能全 —— 审批流、会签、定时任务、历史
```

```text
Flowable vs Activiti：
Flowable —— Activiti 核心团队 2016 年创立，更活跃
Activiti —— 老牌工作流引擎
两者 API 高度相似（同源）
```

## 依赖与配置

### 依赖

```xml
<dependency>
    <groupId>org.flowable</groupId>
    <artifactId>flowable-spring-boot-starter-process</artifactId>
    <version>7.0.0</version>
</dependency>
```

### 配置

```yaml
flowable:
  database-schema-update: true    # 自动建表
  async-executor-activate: true   # 异步执行器
```

### 核心服务

```java
@Autowired
private RepositoryService repositoryService;   // 流程定义管理
@Autowired
private RuntimeService runtimeService;         // 流程实例管理
@Autowired
private TaskService taskService;               // 任务管理
@Autowired
private HistoryService historyService;         // 历史数据
```

## 流程部署

流程部署是把 BPMN 文件加载到引擎。

### 部署流程

```java
// 部署 BPMN 文件
Deployment deployment = repositoryService.createDeployment()
    .addClasspathResource("processes/leave.bpmn20.xml")
    .name("请假流程")
    .deploy();

// 查询已部署的流程定义
List<ProcessDefinition> definitions = repositoryService.createProcessDefinitionQuery()
    .list();
```

### 删除流程定义

```java
repositoryService.deleteDeployment(deploymentId, true);   // true 级联删除
```

## 流程启动

流程启动是创建流程实例。

### 启动流程

```java
// 启动流程实例（带变量）
Map<String, Object> variables = new HashMap<>();
variables.put("applicant", "张三");
variables.put("days", 5);

ProcessInstance instance = runtimeService.startProcessInstanceByKey(
    "leaveProcess",       // 流程定义 key
    variables);           // 流程变量
```

### 查询流程实例

```java
List<ProcessInstance> instances = runtimeService.createProcessInstanceQuery()
    .processDefinitionKey("leaveProcess")
    .active()             // 运行中的
    .list();
```

## 任务处理

任务是流程中需要处理的工作。

### 查询待办任务

```java
// 查询某人的待办任务
List<Task> tasks = taskService.createTaskQuery()
    .taskAssignee("张三")       // 处理人
    .list();

for (Task task : tasks) {
    System.out.println(task.getId() + ": " + task.getName());
}
```

### 完成任务

```java
// 完成任务（流转到下一步）
Map<String, Object> variables = new HashMap<>();
variables.put("approved", true);

taskService.complete(taskId, variables);
```

### 任务操作

```java
taskService.claim(taskId, userId);       // 认领任务
taskService.setAssignee(taskId, userId); // 指派任务
taskService.delegateTask(taskId, userId);// 委派任务
```

## 网关与会签或签

### 网关

```java
// 排他网关和并行网关在 BPMN 里定义（见 136-BPMN）
// 引擎根据条件表达式自动路由
```

### 会签（全部通过）

```xml
<!-- 会签：多人全部审批通过 -->
<userTask id="approve" name="会签审批">
    <multiInstanceLoopCharacteristics isSequential="false"
        flowable:collection="${approvers}"     <!-- 审批人列表 -->
        flowable:elementVariable="approver">
        <completionCondition>${nrOfCompletedInstances == nrOfInstances}</completionCondition>
    </multiInstanceLoopCharacteristics>
</userTask>
```

```text
会签：所有审批人都要审批（全部通过才通过）
isSequential=false —— 并行（同时审批）
isSequential=true —— 串行（逐个审批）
```

### 或签（一人通过即可）

```xml
<!-- 或签：任一审批人通过即通过 -->
<userTask id="approve" name="或签审批">
    <multiInstanceLoopCharacteristics isSequential="false"
        flowable:collection="${approvers}"
        flowable:elementVariable="approver">
        <completionCondition>${nrOfCompletedInstances == 1}</completionCondition>
    </multiInstanceLoopCharacteristics>
</userTask>
```

```text
会签 vs 或签：
会签 —— 所有人都要通过（nrOfCompletedInstances == nrOfInstances）
或签 —— 一人通过即可（nrOfCompletedInstances == 1）
```

## 流程变量与历史

### 流程变量

```java
// 设置变量
runtimeService.setVariable(processInstanceId, "amount", 1000);

// 获取变量
Object amount = runtimeService.getVariable(processInstanceId, "amount");

// 任务级变量
taskService.setVariable(taskId, "approved", true);
```

### 历史查询

```java
// 查询历史任务
List<HistoricTaskInstance> historicTasks = historyService
    .createHistoricTaskInstanceQuery()
    .processInstanceId(processInstanceId)
    .list();

// 查询已完成的流程实例
List<HistoricProcessInstance> finished = historyService
    .createHistoricProcessInstanceQuery()
    .finished()
    .list();
```

### 流程状态查询

```java
// 判断流程是否结束
ProcessInstance instance = runtimeService.createProcessInstanceQuery()
    .processInstanceId(processInstanceId)
    .singleResult();
if (instance == null) {
    // 流程已结束
}
```

## 应用场景实战

### 场景 1：请假审批完整流程

```java
@Service
public class LeaveService {

    @Autowired
    private RuntimeService runtimeService;
    @Autowired
    private TaskService taskService;

    // 提交请假申请
    public String submitLeave(String applicant, int days) {
        Map<String, Object> variables = new HashMap<>();
        variables.put("applicant", applicant);
        variables.put("days", days);

        ProcessInstance instance = runtimeService.startProcessInstanceByKey(
            "leaveProcess", variables);
        return instance.getId();
    }

    // 查询待办
    public List<Task> getTodos(String approver) {
        return taskService.createTaskQuery()
            .taskAssignee(approver)
            .list();
    }

    // 审批
    public void approve(String taskId, boolean approved) {
        Map<String, Object> variables = new HashMap<>();
        variables.put("approved", approved);
        taskService.complete(taskId, variables);
    }
}
```

### 场景 2：会签审批

```java
// 启动会签流程（多个审批人）
Map<String, Object> variables = new HashMap<>();
variables.put("approvers", Arrays.asList("经理", "总监", "HR"));

runtimeService.startProcessInstanceByKey("multiApproveProcess", variables);

// 每个审批人审批自己的任务
// 所有人审批完，流程继续
```

### 场景 3：查询流程历史

```java
// 查询某人的历史审批记录
List<HistoricTaskInstance> history = historyService
    .createHistoricTaskInstanceQuery()
    .taskAssignee("张三")
    .finished()   // 已完成的
    .list();

for (HistoricTaskInstance task : history) {
    System.out.println(task.getName() + " 完成于 " + task.getEndTime());
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **流程定义版本管理**。修改流程后重新部署，用版本区分。

2. **流程变量要序列化**。变量对象要实现 Serializable。

3. **会签用 multiInstanceLoopCharacteristics**。不要手动循环创建任务。

4. **异步任务用 Service Task**。耗时操作（发邮件、调接口）用 Service Task 异步执行。

5. **历史数据定期归档**。历史表增长快，定期归档清理。

### 踩坑记录

**坑 1：流程变量对象不序列化**

```java
variables.put("user", new User());   // User 没实现 Serializable
// 反序列化报错
```

流程变量对象要实现 Serializable。

**坑 2：修改流程定义后新老版本混乱**

```text
修改 BPMN 后重新部署，生成新版本
旧流程实例还在用旧版本，新流程用新版本
```

明确版本管理，用 processDefinitionVersion 区分。

**坑 3：会签人数动态变化**

```xml
flowable:collection="${approvers}"   <!-- 启动时固定，中途加人无效 -->
```

会签人数在启动时确定，中途加人要特殊处理。

**坑 4：完成任务后流程没流转**

```text
完成任务但没设置网关需要的变量，流程走默认流
```

完成任务时设置所有后续网关需要的变量。

**坑 5：Service Task 阻塞主流程**

```text
Service Task 里做了耗时操作（调用外部接口 5 秒），阻塞流程
```

耗时 Service Task 用异步执行（flowable:async="true"）。

**坑 6：历史表膨胀**

```text
历史数据只增不减，表越来越大，查询变慢
```

定期归档或清理历史数据。
