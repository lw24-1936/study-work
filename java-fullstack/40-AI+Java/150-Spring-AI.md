---
title: Spring AI
created: 2026-08-13
updated: 2026-08-13
type: concept
tags: [spring-ai, chatclient, chatmodel, prompt, prompt-template, structured-output, embedding, vector-store]
---

# Spring AI

整理日期：2026-08-13

## 目录

- [概述](#概述)
- [依赖与配置](#依赖与配置)
- [ChatModel 与 ChatClient](#chatmodel-与-chatclient)
- [Prompt 与 Prompt Template](#prompt-与-prompt-template)
- [Structured Output 结构化输出](#structured-output-结构化输出)
- [Embedding 与 Vector Store](#embedding-与-vector-store)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Spring AI 是 Spring 官方的 AI 集成框架，让 Java 开发者用熟悉的 Spring 方式集成 LLM。

```text
Spring AI 的价值：
1. 统一抽象 —— 一套 API 对接多个模型（OpenAI/DeepSeek/Qwen）
2. Spring 风格 —— 自动配置、依赖注入
3. 完整能力 —— Chat、Embedding、RAG、Function Calling
```

```text
Spring AI 的核心组件：
1. ChatModel —— 对话模型抽象
2. ChatClient —— 对话客户端（新 API）
3. Prompt Template —— 提示词模板
4. Embedding —— 向量化
5. Vector Store —— 向量存储（RAG）
```

## 依赖与配置

### 依赖

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-openai</artifactId>
    <version>1.0.0</version>
</dependency>
```

### 配置

```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      base-url: https://api.openai.com
      chat:
        options:
          model: gpt-4o
          temperature: 0.7
```

### 对接 DeepSeek（国内）

```yaml
spring:
  ai:
    openai:
      api-key: ${DEEPSEEK_API_KEY}
      base-url: https://api.deepseek.com   # 换 base-url
      chat:
        options:
          model: deepseek-chat
```

```text
关键：Spring AI 用 OpenAI 兼容协议，
DeepSeek、Qwen、Kimi 等兼容 OpenAI 的模型，换 base-url 即可
```

## ChatModel 与 ChatClient

### ChatModel（基础）

```java
@Autowired
private ChatModel chatModel;

public String chat(String message) {
    return chatModel.call(message);   // 简单对话
}
```

### ChatClient（推荐，新 API）

```java
@Autowired
private ChatClient chatClient;

public String chat(String message) {
    return chatClient.prompt()
        .user(message)
        .call()
        .content();
}
```

### 流式输出

```java
// 流式返回（逐字输出）
public Flux<String> stream(String message) {
    return chatClient.prompt()
        .user(message)
        .stream()
        .content();
}
```

### 携带历史对话

```java
public String chatWithHistory(List<Message> history, String message) {
    return chatClient.prompt()
        .messages(history)          // 历史消息
        .user(message)              // 新消息
        .call()
        .content();
}
```

## Prompt 与 Prompt Template

### Prompt Template 模板

```java
// 用占位符模板
String template = "你是 {role}，请帮我 {task}，要求 {requirements}";

Prompt prompt = new PromptTemplate(template)
    .create(Map.of(
        "role", "Java 专家",
        "task", "写一个线程安全的单例",
        "requirements", "使用双重检查锁"));

String result = chatModel.call(prompt).getResult().getOutput().getContent();
```

### System Prompt（系统提示）

```java
public String chat(String message) {
    return chatClient.prompt()
        .system("你是专业的 Java 开发助手，回答要简洁准确")   // 系统提示
        .user(message)
        .call()
        .content();
}
```

### 参数设置

```java
public String chat(String message) {
    return chatClient.prompt()
        .user(message)
        .options(ChatOptions.builder()
            .temperature(0.0)      // 低温（代码/事实）
            .build())
        .call()
        .content();
}
```

## Structured Output 结构化输出

结构化输出让模型返回结构化的对象（如 JSON），而不是纯文本。

### 实体类 + 结构化输出

```java
// 定义输出结构
record UserInfo(String name, Integer age, String email) {}
```

```java
public UserInfo extractUserInfo(String text) {
    return chatClient.prompt()
        .user("从以下文本提取用户信息：" + text)
        .call()
        .entity(UserInfo.class);   // 自动解析为 UserInfo
}
```

### BeanOutputConverter（手动转换）

```java
// 用 converter 手动转换
BeanOutputConverter<UserInfo> converter = new BeanOutputConverter<>(UserInfo.class);
String format = converter.getFormat();

String content = chatModel.call("提取用户信息，格式：" + format);
UserInfo userInfo = converter.convert(content);
```

### 结构化输出的用途

```text
1. 信息提取 —— 从文本提取结构化数据
2. 分类 —— 文本分类（返回枚举）
3. 实体识别 —— 提取实体
```

## Embedding 与 Vector Store

### Embedding

```java
@Autowired
private EmbeddingModel embeddingModel;

public float[] embed(String text) {
    return embeddingModel.embed(text);   // 文本转向量
}
```

### Vector Store（向量存储）

```java
@Autowired
private VectorStore vectorStore;

// 添加文档（向量化 + 存储）
public void addDocument(String text, Map<String, Object> metadata) {
    Document doc = new Document(text, metadata);
    vectorStore.add(List.of(doc));
}

// 相似性搜索
public List<Document> search(String query) {
    return vectorStore.similaritySearch(
        SearchRequest.query(query).withTopK(5));   // 找最相似的 5 条
}
```

### Vector Store 实现

```text
Spring AI 支持的 Vector Store：
1. Redis（RedisVectorStore）
2. Milvus
3. Qdrant
4. pgvector
5. Elasticsearch
```

## 应用场景实战

### 场景 1：智能客服（对话）

```java
@Service
public class CustomerServiceBot {

    @Autowired
    private ChatClient chatClient;

    public String answer(String question) {
        return chatClient.prompt()
            .system("你是电商客服，回答要友好、准确，不知道就说不知道")
            .user(question)
            .call()
            .content();
    }
}
```

### 场景 2：文本分类（结构化输出）

```java
enum Sentiment { POSITIVE, NEGATIVE, NEUTRAL }

public Sentiment classify(String comment) {
    return chatClient.prompt()
        .user("判断以下评论的情感倾向：" + comment)
        .call()
        .entity(Sentiment.class);   // 返回 POSITIVE/NEGATIVE/NEUTRAL
}
```

### 场景 3：代码生成

```java
public String generateCode(String requirement) {
    return chatClient.prompt()
        .system("你是 Java 专家，只输出代码，不要解释")
        .user(requirement)
        .options(ChatOptions.builder().temperature(0.0).build())
        .call()
        .content();
}
```

### 场景 4：RAG 基础（向量检索 + 对话）

```java
public String ragChat(String question) {
    // 1. 检索相关文档
    List<Document> docs = vectorStore.similaritySearch(
        SearchRequest.query(question).withTopK(3));

    // 2. 拼接上下文
    String context = docs.stream()
        .map(Document::getContent)
        .collect(Collectors.joining("\n"));

    // 3. 带上下文对话
    return chatClient.prompt()
        .system("根据以下资料回答问题：\n" + context)
        .user(question)
        .call()
        .content();
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **用 ChatClient（新 API）**。比 ChatModel 更灵活（流式、结构化）。

2. **API Key 用环境变量**。不硬编码在配置。

3. **结构化输出用 entity()**。自动解析，不用手动处理 JSON。

4. **国内模型换 base-url**。DeepSeek/Qwen 兼容 OpenAI 协议。

5. **向量检索用 Vector Store 抽象**。换向量库不用改代码。

### 踩坑记录

**坑 1：API Key 泄露**

```yaml
spring:
  ai:
    openai:
      api-key: sk-xxxx   # 硬编码，提交 git 泄露
```

用环境变量（${OPENAI_API_KEY}），不硬编码。

**坑 2：结构化输出解析失败**

```text
模型返回格式不规范（多了文字），entity() 解析失败
```

用 BeanOutputConverter 手动解析，或 prompt 明确格式。

**坑 3：国内模型不兼容**

```text
直接对接 Qwen/DeepSeek 用错协议，调用失败
```

用 OpenAI 兼容 base-url，或对应 starter。

**坑 4：向量维度不匹配**

```text
Embedding 模型和 Vector Store 维度不一致，存储失败
```

确认 Embedding 模型维度和向量库配置一致。

**坑 5：忽略流式输出**

```text
长回答用 call() 一次性返回，用户等待久
```

长回答用 stream() 流式返回，体验更好。

**坑 6：成本失控**

```text
不限制 token、不缓存，API 费用飙升
```

限制 token、缓存常见回答、监控用量。
