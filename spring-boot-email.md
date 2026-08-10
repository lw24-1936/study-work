---
title: Spring Boot 集成邮件详解
created: 2026-08-10
updated: 2026-08-10
type: integration
tags: [spring-boot, email, java-mail, smtp]
---

> 整理日期：2026-08-10

## 目录

1. [概述](#1-概述)
2. [环境搭建](#2-环境搭建)
3. [发送简单文本邮件](#3-发送简单文本邮件)
4. [发送 HTML 富文本邮件](#4-发送-html-富文本邮件)
5. [发送带附件的邮件](#5-发送带附件的邮件)
6. [发送带内联图片的邮件](#6-发送带内联图片的邮件)
7. [模板邮件](#7-模板邮件)
8. [异步发送](#8-异步发送)
9. [发送可靠性](#9-发送可靠性)
10. [多账号发送](#10-多账号发送)
11. [邮件发送记录与追踪](#11-邮件发送记录与追踪)
12. [应用场景实战](#12-应用场景实战)
13. [最佳实践与踩坑记录](#13-最佳实践与踩坑记录)
14. [参考链接](#14-参考链接)

---

## 1. 概述

### 1.1 JavaMail 是什么

JavaMail 是 Java EE 的标准邮件 API，Spring Boot 通过 `spring-boot-starter-mail` 对它做了自动配置，核心类是 `JavaMailSender`。

邮件发送的本质：通过 SMTP 协议把邮件内容提交到邮件服务器，由邮件服务器完成实际的投递。

### 1.2 适用场景

| 场景 | 说明 |
|------|------|
| 注册验证码 | 用户注册时发送邮箱验证码 |
| 密码重置 | 忘记密码，通过邮箱重置 |
| 系统告警 | 服务异常、磁盘满等触发邮件通知 |
| 报表推送 | 定时生成报表发送到管理者邮箱 |
| 订单通知 | 下单、发货、签收等状态变更通知 |
| 批量订阅 | 新闻订阅、周报月报群发 |

---

## 2. 环境搭建

### 2.1 获取 SMTP 授权码

QQ 邮箱为例（其他邮箱步骤类似）：

1. 登录 QQ 邮箱 -> 设置 -> 账户
2. 找到 "POP3/IMAP/SMTP 服务"，开启 SMTP 服务
3. 生成授权码（不是登录密码，是 16 位字符串）

常用 SMTP 服务器：

| 邮箱 | SMTP 地址 | 端口（SSL） | 端口（TLS） |
|------|-----------|:---------:|:---------:|
| QQ | smtp.qq.com | 465 | 587 |
| 163 | smtp.163.com | 465 | — |
| Gmail | smtp.gmail.com | 465 | 587 |
| 企业微信 | smtp.exmail.qq.com | 465 | — |
| 阿里企业邮 | smtp.mxhichina.com | 465 | — |

### 2.2 依赖引入

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-mail</artifactId>
</dependency>
```

### 2.3 application.yml 配置

```yaml
spring:
  mail:
    host: smtp.qq.com                          # SMTP 服务器地址
    port: 465                                  # 端口（SSL）
    username: your-email@qq.com                # 邮箱账号
    password: xxxxxxxxxxxxxxxx                 # SMTP 授权码，不是登录密码
    protocol: smtps                            # 协议（SSL 方式为 smtps）
    default-encoding: UTF-8                    # 默认编码
    properties:
      mail:
        smtp:
          auth: true                           # 需要认证
          ssl:
            enable: true                       # 开启 SSL
          starttls:
            enable: true                       # 开启 STARTTLS
            required: true
          connection-timeout: 10000            # 连接超时（ms）
          timeout: 10000                       # 读写超时（ms）
          write-timeout: 10000                 # 写超时（ms）
          socket-factory:
            port: 465
            class: javax.net.ssl.SSLSocketFactory
        debug: false                           # 调试日志（开发时可开）
```

TLS 587 端口的配置方式：

```yaml
spring:
  mail:
    host: smtp.qq.com
    port: 587
    username: your-email@qq.com
    password: xxxxxxxxxxxxxxxx
    protocol: smtp
    properties:
      mail:
        smtp:
          auth: true
          starttls:
            enable: true
            required: true
```

### 2.4 测试连接

```java
@SpringBootTest
class MailTest {

    @Autowired
    private JavaMailSender mailSender;

    @Test
    void testConnection() {
        // 能发一封空邮件就说明连接通了
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom("sender@qq.com");
        message.setTo("receiver@qq.com");
        message.setSubject("Test");
        message.setText("Connection OK");
        mailSender.send(message);
    }
}
```

---

## 3. 发送简单文本邮件

`SimpleMailMessage` 适用于纯文本邮件，不含 HTML 和附件。

```java
@Service
@Slf4j
public class MailService {

    @Autowired
    private JavaMailSender mailSender;

    @Value("${spring.mail.username}")
    private String from;   // 发件人，从配置读取

    /**
     * 发送纯文本邮件
     */
    public void sendSimpleMail(String to, String subject, String content) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(from);         // 发件人
        message.setTo(to);             // 收件人
        message.setSubject(subject);   // 主题
        message.setText(content);      // 正文
        message.setSentDate(new Date()); // 发送时间

        mailSender.send(message);
        log.info("邮件发送成功: to={}, subject={}", to, subject);
    }
}
```

### 3.1 一封发给多人

```java
public void sendToMultiple(String[] to, String subject, String content) {
    SimpleMailMessage message = new SimpleMailMessage();
    message.setFrom(from);
    message.setTo(to);              // 数组，收件人都能看到彼此
    message.setCc("cc@qq.com");     // 抄送
    message.setBcc("bcc@qq.com");   // 密送（收件人看不到密送列表）
    message.setSubject(subject);
    message.setText(content);
    mailSender.send(message);
}
```

收件人能看到的是 To 和 Cc 里的人，Bcc 中的人对所有其他收件人都不可见。

### 3.2 设置回复地址

```java
message.setReplyTo("reply-to@qq.com");  // 用户点回复时默认发到这个地址
```

---

## 4. 发送 HTML 富文本邮件

用 `MimeMessage` + `MimeMessageHelper`，正文传 HTML 字符串。

```java
public void sendHtmlMail(String to, String subject, String htmlContent) {
    try {
        MimeMessage mimeMessage = mailSender.createMimeMessage();
        // true = multipart（支持附件和内联资源）
        MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

        helper.setFrom(from);
        helper.setTo(to);
        helper.setSubject(subject);
        // 第二个参数 true = content 是 HTML
        helper.setText(htmlContent, true);
        helper.setSentDate(new Date());

        mailSender.send(mimeMessage);
        log.info("HTML 邮件发送成功: to={}", to);

    } catch (MessagingException e) {
        log.error("HTML 邮件发送失败", e);
        throw new RuntimeException("邮件发送失败", e);
    }
}
```

调用示例：

```java
String html = """
    <div style="max-width:600px;margin:0 auto;font-family:Arial,sans-serif;">
        <h2 style="color:#333;">账号注册成功</h2>
        <p>您好，<b>张三</b>：</p>
        <p>感谢注册 XX 平台，点击下方链接完成身份验证：</p>
        <a href="https://example.com/verify?token=abc123"
           style="display:inline-block;padding:12px 24px;background:#1890ff;
                  color:#fff;text-decoration:none;border-radius:4px;">
            立即验证
        </a>
        <p style="color:#999;font-size:12px;margin-top:20px;">
            如果不是您本人操作，请忽略此邮件。
        </p>
    </div>
    """;
mailService.sendHtmlMail("user@qq.com", "欢迎注册", html);
```

HTML 邮件要点：

- CSS 写在标签内联 style 中（多数邮件客户端不支持外部样式表和 `<style>` 标签）
- 不要用 JS（所有邮件客户端都会过滤）
- 图片用绝对路径 URL
- 正文和 HTML 都提供，防止客户端不支持 HTML：

```java
helper.setText(plainText, htmlContent);  // 第一个参数是纯文本降级内容
```

---

## 5. 发送带附件的邮件

```java
public void sendWithAttachment(String to, String subject, String content,
                                String filePath) {
    try {
        MimeMessage mimeMessage = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

        helper.setFrom(from);
        helper.setTo(to);
        helper.setSubject(subject);
        helper.setText(content, true);

        // 添加附件
        FileSystemResource file = new FileSystemResource(new File(filePath));
        String fileName = file.getFilename();
        helper.addAttachment(fileName, file);

        mailSender.send(mimeMessage);
        log.info("带附件邮件发送成功: to={}, file={}", to, fileName);

    } catch (MessagingException e) {
        log.error("带附件邮件发送失败", e);
        throw new RuntimeException("邮件发送失败", e);
    }
}

// 多个附件
public void sendWithAttachments(String to, String subject, String content,
                                 List<String> filePaths) {
    try {
        MimeMessage mimeMessage = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

        helper.setFrom(from);
        helper.setTo(to);
        helper.setSubject(subject);
        helper.setText(content, true);

        for (String path : filePaths) {
            FileSystemResource file = new FileSystemResource(new File(path));
            helper.addAttachment(file.getFilename(), file);
        }

        mailSender.send(mimeMessage);

    } catch (MessagingException e) {
        log.error("邮件发送失败", e);
        throw new RuntimeException("邮件发送失败", e);
    }
}
```

### 5.1 发送字节数组附件

不落盘，直接发内存中的数据（比如刚生成的 PDF 流）：

```java
public void sendWithByteAttachment(String to, String subject, String content,
                                    byte[] data, String fileName) {
    try {
        MimeMessage mimeMessage = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

        helper.setFrom(from);
        helper.setTo(to);
        helper.setSubject(subject);
        helper.setText(content, true);

        helper.addAttachment(fileName, new ByteArrayResource(data));

        mailSender.send(mimeMessage);

    } catch (MessagingException e) {
        log.error("邮件发送失败", e);
        throw new RuntimeException("邮件发送失败", e);
    }
}
```

### 5.2 附件中文名乱码

`MimeMessageHelper.addAttachment` 默认用 ISO-8859-1 编码文件名，中文会乱码。解决方式：构造 helper 时指定 UTF-8，或手动设置：

```java
// 方式一：用自定义 DataSource
ByteArrayResource resource = new ByteArrayResource(data) {
    @Override
    public String getFilename() {
        return MimeUtility.encodeText("月度报表.pdf", "UTF-8", "B");
    }
};
helper.addAttachment("月度报表.pdf", resource);
```

如果构造 helper 时传了 `"UTF-8"` 且字附名不含特殊字符，Spring 5.x/6.x 会自动处理。生产环境验证一下，不同版本的兼容性有差异。

---

## 6. 发送带内联图片的邮件

邮件正文中嵌入图片（不是以附件形式），HTML 引用 cid。

```java
public void sendWithInlineImage(String to, String subject, String htmlContent,
                                 String imagePath, String contentId) {
    try {
        MimeMessage mimeMessage = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

        helper.setFrom(from);
        helper.setTo(to);
        helper.setSubject(subject);

        // HTML 中用 cid:contentId 引用图片
        helper.setText(htmlContent, true);

        // 添加内联资源
        FileSystemResource image = new FileSystemResource(new File(imagePath));
        helper.addInline(contentId, image);

        mailSender.send(mimeMessage);

    } catch (MessagingException e) {
        log.error("邮件发送失败", e);
        throw new RuntimeException("邮件发送失败", e);
    }
}
```

调用示例：

```java
String contentId = "logo";
String html = """
    <h2>欢迎注册</h2>
    <p>以下是我们为您准备的新手引导：</p>
    <img src='cid:%s' style='width:200px;'/>
    """.formatted(contentId);

mailService.sendWithInlineImage("user@qq.com", "欢迎", html,
        "/path/to/logo.png", contentId);
```

---

## 7. 模板邮件

解决邮件正文拼接字符串带来的维护噩梦。

### 7.1 Thymeleaf 模板（推荐）

依赖：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-thymeleaf</artifactId>
</dependency>
```

模板文件 `resources/templates/mail/register.html`：

```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 th:text="${title}">默认标题</h2>
    <p th:text="'您好，' + ${username} + '：'"></p>
    <p th:text="${content}"></p>

    <div th:if="${link != null}" style="margin-top: 20px;">
        <a th:href="${link}"
           style="display:inline-block;padding:12px 24px;background:#1890ff;
                  color:#fff;text-decoration:none;border-radius:4px;"
           th:text="${linkText}">按钮文字</a>
    </div>

    <p style="color: #999; font-size: 12px; margin-top: 20px;"
       th:text="${footer}">默认页脚</p>
</body>
</html>
```

渲染并发送：

```java
@Service
@Slf4j
public class TemplateMailService {

    @Autowired
    private JavaMailSender mailSender;
    @Autowired
    private TemplateEngine templateEngine;

    @Value("${spring.mail.username}")
    private String from;

    public void sendRegisterMail(String to, String username, String verifyLink) {
        // 构建模板上下文
        Context context = new Context();
        context.setVariable("title", "欢迎注册 XX 平台");
        context.setVariable("username", username);
        context.setVariable("content", "感谢注册，请点击下方按钮完成邮箱验证：");
        context.setVariable("link", verifyLink);
        context.setVariable("linkText", "立即验证");
        context.setVariable("footer", "如果不是您本人操作，请忽略此邮件。");

        // 渲染 HTML
        String htmlContent = templateEngine.process("mail/register", context);

        // 发送
        sendHtmlMail(to, "欢迎注册 XX 平台", htmlContent);
    }

    private void sendHtmlMail(String to, String subject, String html) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(from);
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(html, true);
            mailSender.send(message);
            log.info("模板邮件发送成功: to={}", to);
        } catch (MessagingException e) {
            log.error("邮件发送失败", e);
            throw new RuntimeException("邮件发送失败", e);
        }
    }
}
```

### 7.2 FreeMarker 模板

依赖：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-freemarker</artifactId>
</dependency>
```

模板文件 `resources/templates/mail/register.ftl`：

```html
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>${title}</h2>
    <p>您好，${username}：</p>
    <p>${content}</p>

    <#if link??>
    <div style="margin-top: 20px;">
        <a href="${link}"
           style="display:inline-block;padding:12px 24px;background:#1890ff;
                  color:#fff;text-decoration:none;border-radius:4px;">
            ${linkText}
        </a>
    </div>
    </#if>

    <p style="color: #999; font-size: 12px; margin-top: 20px;">${footer}</p>
</body>
</html>
```

渲染发送：

```java
@Autowired
private freemarker.template.Configuration freemarkerConfig;

public void sendRegisterMail(String to, String username, String verifyLink) {
    try {
        Map<String, Object> model = new HashMap<>();
        model.put("title", "欢迎注册 XX 平台");
        model.put("username", username);
        model.put("content", "感谢注册，请点击下方按钮完成邮箱验证：");
        model.put("link", verifyLink);
        model.put("linkText", "立即验证");
        model.put("footer", "如果不是您本人操作，请忽略此邮件。");

        // 渲染
        Template template = freemarkerConfig.getTemplate("mail/register.ftl");
        StringWriter writer = new StringWriter();
        template.process(model, writer);
        String htmlContent = writer.toString();

        sendHtmlMail(to, "欢迎注册 XX 平台", htmlContent);

    } catch (Exception e) {
        log.error("模板渲染失败", e);
        throw new RuntimeException("邮件发送失败", e);
    }
}
```

### 7.3 Thymeleaf vs FreeMarker

| 维度 | Thymeleaf | FreeMarker |
|------|-----------|------------|
| 语法 | 属性增强（`th:text`） | 模板插值（`${}`） |
| HTML 原生预览 | 支持（浏览器可直接打开看效果） | 不支持 |
| Spring Boot 集成 | 自动配置，开箱即用 | 自动配置，开箱即用 |
| 性能 | 缓存解析后略差 | 编译为 AST，性能更好 |
| 推荐 | 和前端共用模板时 | 纯后端邮件模板 |

选哪个都行。如果邮件模板可能被前端开发查看修改，用 Thymeleaf；如果是后端团队独立维护，用 FreeMarker 性能更好。

---

## 8. 异步发送

邮件发送是典型的 IO 密集操作，不阻塞主线程。

### 8.1 开启异步

```java
@SpringBootApplication
@EnableAsync   // 启用异步支持
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

```java
@Service
public class AsyncMailService {

    @Autowired
    private MailService mailService;

    @Async("mailExecutor")  // 指定线程池
    public CompletableFuture<Boolean> sendAsync(String to, String subject, String content) {
        try {
            mailService.sendSimpleMail(to, subject, content);
            return CompletableFuture.completedFuture(true);
        } catch (Exception e) {
            log.error("异步邮件发送失败", e);
            return CompletableFuture.completedFuture(false);
        }
    }
}
```

### 8.2 邮件专用线程池

```java
@Configuration
public class MailAsyncConfig {

    @Bean("mailExecutor")
    public Executor mailExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);                        // 核心线程
        executor.setMaxPoolSize(5);                         // 最大线程
        executor.setQueueCapacity(200);                     // 等待队列
        executor.setKeepAliveSeconds(60);
        executor.setThreadNamePrefix("mail-");
        // 拒绝策略：由调用线程执行（不丢任务）
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```

并发度不用设太大——IO 端（邮件服务器）通常有频率限制，线程再多也是排队。

---

## 9. 发送可靠性

### 9.1 问题分析

邮件发不出去的原因通常有三类：

| 原因 | 表现 | 解决 |
|------|------|------|
| 网络/服务不可达 | 连接超时 | 重试 + 落库 |
| SMTP 频率限制 | 返回 450/451 | 降低并发、延时重试 |
| 授权码/密码错误 | 535 Authentication failed | 修正配置 |
| 内容被拒（垃圾邮件） | 554 rejected | 优化内容、配置 SPF/DKIM |

### 9.2 发送前落库 + 重试

```java
@Entity
@Table(name = "t_mail_record")
@Data
public class MailRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String messageId;         // MimeMessage.getMessageID()
    private String fromAddr;
    private String toAddr;
    private String subject;
    @Column(columnDefinition = "TEXT")
    private String content;
    private Integer status;           // 0-待发送 1-已发送 2-发送失败
    private Integer retryCount = 0;
    private String errorMsg;
    private LocalDateTime createTime;
    private LocalDateTime sendTime;
}
```

```java
@Service
public class ReliableMailService {

    @Autowired
    private JavaMailSender mailSender;
    @Autowired
    private MailRecordMapper recordMapper;
    @Value("${spring.mail.username}")
    private String from;

    private static final int MAX_RETRY = 3;

    /**
     * 可靠的邮件发送：先落库再发送，失败后更新状态
     */
    public void sendReliably(String to, String subject, String content) {
        // 1. 先落库
        MailRecord record = new MailRecord();
        record.setFromAddr(from);
        record.setToAddr(to);
        record.setSubject(subject);
        record.setContent(content);
        record.setStatus(0);
        record.setCreateTime(LocalDateTime.now());
        recordMapper.insert(record);

        // 2. 尝试发送
        sendWithRetry(record);
    }

    private void sendWithRetry(MailRecord record) {
        int attempts = 0;
        Exception lastException = null;

        while (attempts < MAX_RETRY) {
            try {
                MimeMessage message = mailSender.createMimeMessage();
                MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
                helper.setFrom(record.getFromAddr());
                helper.setTo(record.getToAddr());
                helper.setSubject(record.getSubject());
                helper.setText(record.getContent(), true);

                mailSender.send(message);

                // 发送成功，更新状态
                String msgId = message.getMessageID();
                MailRecord update = new MailRecord();
                update.setId(record.getId());
                update.setStatus(1);
                update.setMessageId(msgId);
                update.setSendTime(LocalDateTime.now());
                recordMapper.updateById(update);

                log.info("邮件发送成功: {} -> {}", record.getToAddr(), record.getSubject());
                return;

            } catch (MessagingException e) {
                lastException = e;
                attempts++;
                log.warn("邮件发送失败，第{}次重试: {}", attempts, record.getToAddr());

                if (attempts < MAX_RETRY) {
                    try {
                        Thread.sleep(attempts * 3000L);  // 逐次延长等待
                    } catch (InterruptedException ignored) {}
                }
            }
        }

        // 全部重试失败
        MailRecord update = new MailRecord();
        update.setId(record.getId());
        update.setStatus(2);
        update.setRetryCount(attempts);
        update.setErrorMsg(lastException != null ? lastException.getMessage() : "未知错误");
        recordMapper.updateById(update);

        log.error("邮件发送彻底失败: id={}, to={}", record.getId(), record.getToAddr());
    }

    /**
     * 定时任务：重扫失败记录
     */
    @Scheduled(fixedDelay = 300000)  // 每 5 分钟扫一次
    public void retryFailed() {
        List<MailRecord> failedRecords = recordMapper.selectList(
                new LambdaQueryWrapper<MailRecord>()
                        .eq(MailRecord::getStatus, 2)
                        .lt(MailRecord::getRetryCount, MAX_RETRY)
                        .last("LIMIT 50")
        );
        for (MailRecord record : failedRecords) {
            sendWithRetry(record);
        }
    }
}
```

### 9.3 生产者-消费者架构

如果邮件量大且可靠性要求高，把邮件发送拆成两步：生产者落库并投递 MQ，消费者从 MQ 取消息发送邮件。MQ 保证了 Broker 侧的持久化。参见 [[spring-boot-rabbitmq]] 了解 RabbitMQ 集成。

---

## 10. 多账号发送

一个应用可能需要用不同的邮箱发不同类型的邮件（系统通知用 A 账号，营销邮件用 B 账号）。

### 10.1 多配置

```yaml
spring:
  mail:
    primary:
      host: smtp.qq.com
      port: 465
      username: notice@qq.com
      password: xxxxxxxx
      protocol: smtps
      properties:
        mail:
          smtp:
            auth: true
            ssl:
              enable: true
    marketing:
      host: smtp.163.com
      port: 465
      username: marketing@163.com
      password: xxxxxxxx
      protocol: smtps
      properties:
        mail:
          smtp:
            auth: true
            ssl:
              enable: true
```

### 10.2 多 JavaMailSender Bean

```java
@Configuration
public class MultiMailConfig {

    @Primary
    @Bean("primaryMailSender")
    public JavaMailSender primaryMailSender(
            @Value("${spring.mail.primary.host}") String host,
            @Value("${spring.mail.primary.port}") int port,
            @Value("${spring.mail.primary.username}") String username,
            @Value("${spring.mail.primary.password}") String password,
            @Value("${spring.mail.primary.protocol}") String protocol) {

        return createMailSender(host, port, username, password, protocol);
    }

    @Bean("marketingMailSender")
    public JavaMailSender marketingMailSender(
            @Value("${spring.mail.marketing.host}") String host,
            @Value("${spring.mail.marketing.port}") int port,
            @Value("${spring.mail.marketing.username}") String username,
            @Value("${spring.mail.marketing.password}") String password,
            @Value("${spring.mail.marketing.protocol}") String protocol) {

        return createMailSender(host, port, username, password, protocol);
    }

    private JavaMailSender createMailSender(String host, int port,
                                             String username, String password, String protocol) {
        JavaMailSenderImpl sender = new JavaMailSenderImpl();
        sender.setHost(host);
        sender.setPort(port);
        sender.setUsername(username);
        sender.setPassword(password);
        sender.setProtocol(protocol);
        sender.setDefaultEncoding("UTF-8");

        Properties props = sender.getJavaMailProperties();
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.ssl.enable", "true");
        props.put("mail.smtp.starttls.enable", "true");
        props.put("mail.smtp.connection-timeout", "10000");
        props.put("mail.smtp.timeout", "10000");

        return sender;
    }
}
```

### 10.3 使用

```java
@Service
public class MultiAccountMailService {

    @Autowired
    @Qualifier("primaryMailSender")
    private JavaMailSender primaryMailSender;

    @Autowired
    @Qualifier("marketingMailSender")
    private JavaMailSender marketingMailSender;

    public void sendNotice(String to, String subject, String content) {
        sendWith(primaryMailSender, to, subject, content);
    }

    public void sendMarketing(String to, String subject, String content) {
        sendWith(marketingMailSender, to, subject, content);
    }

    private void sendWith(JavaMailSender sender, String to, String subject, String content) {
        try {
            MimeMessage message = sender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(content, true);
            sender.send(message);
        } catch (MessagingException e) {
            throw new RuntimeException("邮件发送失败", e);
        }
    }
}
```

---

## 11. 邮件发送记录与追踪

### 11.1 记录表设计

```sql
CREATE TABLE t_mail_log (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    message_id    VARCHAR(128) COMMENT 'MimeMessage ID（唯一标识）',
    sender        VARCHAR(100) NOT NULL COMMENT '发件人',
    recipients    VARCHAR(500) NOT NULL COMMENT '收件人（多个用逗号分隔）',
    cc            VARCHAR(500) COMMENT '抄送',
    subject       VARCHAR(200) COMMENT '主题',
    content_type  VARCHAR(20) COMMENT 'TEXT / HTML',
    content       LONGTEXT COMMENT '正文',
    attachments   VARCHAR(500) COMMENT '附件列表',
    status        TINYINT DEFAULT 0 COMMENT '0待发送 1成功 2失败',
    retry_count   INT DEFAULT 0 COMMENT '重试次数',
    error_msg     TEXT COMMENT '失败原因',
    biz_type      VARCHAR(50) COMMENT '业务类型（REGISTER/PASSWORD_RESET/NOTIFY）',
    biz_id        VARCHAR(64) COMMENT '关联业务ID',
    send_time     DATETIME COMMENT '发送时间',
    create_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_biz (biz_type, biz_id),
    INDEX idx_create_time (create_time)
) COMMENT '邮件发送记录表';
```

### 11.2 AOP 切面记录和报警

```java
@Aspect
@Component
@Slf4j
public class MailSendAspect {

    @Autowired
    private MailLogService mailLogService;

    private static final double ALERT_THRESHOLD = 0.1;  // 失败率超过 10% 告警

    @Around("@annotation(mailLog)")
    public Object around(ProceedingJoinPoint pjp, MailLog mailLog) throws Throwable {
        MailLogEntity logEntity = new MailLogEntity();
        logEntity.setBizType(mailLog.bizType());
        logEntity.setCreateTime(LocalDateTime.now());

        long start = System.currentTimeMillis();
        try {
            Object result = pjp.proceed();
            long elapsed = System.currentTimeMillis() - start;

            logEntity.setStatus(1);
            logEntity.setSendTime(LocalDateTime.now());
            mailLogService.save(logEntity);

            if (elapsed > 5000) {
                log.warn("邮件发送耗时过长: {}ms", elapsed);
            }
            return result;

        } catch (Exception e) {
            logEntity.setStatus(2);
            logEntity.setErrorMsg(limit(e.getMessage(), 500));
            mailLogService.save(logEntity);

            // 检查近期失败率
            double failRate = mailLogService.getFailureRate(60);  // 最近 60 分钟
            if (failRate > ALERT_THRESHOLD) {
                log.error("邮件发送失败率过高: {}%", String.format("%.1f", failRate * 100));
                // 触发告警（钉钉/企业微信/webhook）
            }

            throw e;
        }
    }

    private String limit(String msg, int maxLen) {
        return msg != null && msg.length() > maxLen ? msg.substring(0, maxLen) : msg;
    }
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface MailLog {
    String bizType();   // 业务类型
}
```

---

## 12. 应用场景实战

### 场景一：注册邮件验证码

用户注册时发 6 位数字验证码，5 分钟内有效。

**验证码生成和存储：**

```java
@Service
public class EmailVerifyCodeService {

    @Autowired
    private StringRedisTemplate redisTemplate;     // 参见 [[spring-boot-redis]]
    @Autowired
    private MailService mailService;

    private static final String CODE_PREFIX = "email:code:";
    private static final long CODE_EXPIRE = 5;     // 5 分钟

    /**
     * 发送验证码
     */
    public void sendVerifyCode(String email) {
        // 1. 检查发送频率（60 秒内不允许重复发送）
        String rateKey = "email:rate:" + email;
        Boolean lock = redisTemplate.opsForValue().setIfAbsent(rateKey, "1", 60, TimeUnit.SECONDS);
        if (Boolean.FALSE.equals(lock)) {
            throw new BusinessException("验证码已发送，请 60 秒后再试");
        }

        // 2. 生成 6 位数字验证码
        String code = String.valueOf(new Random().nextInt(900000) + 100000);

        // 3. 存入 Redis
        String codeKey = CODE_PREFIX + email;
        redisTemplate.opsForValue().set(codeKey, code, CODE_EXPIRE, TimeUnit.MINUTES);

        // 4. 发送邮件
        String html = buildCodeEmail(code);
        mailService.sendHtmlMail(email, "【XX平台】邮箱验证码", html);

        log.info("验证码已发送: email={}", email);
    }

    /**
     * 校验验证码
     */
    public boolean verify(String email, String code) {
        String key = CODE_PREFIX + email;
        String storedCode = redisTemplate.opsForValue().get(key);
        if (storedCode == null) {
            throw new BusinessException("验证码已过期，请重新获取");
        }
        if (!storedCode.equals(code)) {
            throw new BusinessException("验证码错误");
        }
        // 验证通过后删除（一次性使用）
        redisTemplate.delete(key);
        return true;
    }

    private String buildCodeEmail(String code) {
        return """
            <div style="max-width:480px;margin:40px auto;padding:30px;
                        background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
                <h2 style="color:#333;margin-bottom:24px;">邮箱验证码</h2>
                <p style="color:#666;">您正在进行邮箱验证，验证码如下：</p>
                <div style="background:#f5f5f5;padding:20px;text-align:center;margin:24px 0;
                            border-radius:6px;">
                    <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#333;">
                        %s
                    </span>
                </div>
                <p style="color:#999;font-size:13px;">
                    验证码 %d 分钟内有效。请勿泄露给他人。
                </p>
            </div>
            """.formatted(code, CODE_EXPIRE);
    }
}
```

**Controller：**

```java
@RestController
@RequestMapping("/api/email")
public class EmailCodeController {

    @Autowired
    private EmailVerifyCodeService verifyCodeService;

    @PostMapping("/send-code")
    public R<Void> sendCode(@RequestParam String email) {
        verifyCodeService.sendVerifyCode(email);
        return R.ok();
    }
}

// 注册接口
@PostMapping("/register")
public R<Void> register(@RequestBody @Valid RegisterDTO dto) {
    // 先校验验证码
    verifyCodeService.verify(dto.getEmail(), dto.getCode());
    // 再执行注册逻辑
    userService.register(dto);
    return R.ok();
}
```

### 场景二：异常告警邮件

服务异常时自动发邮件给运维。和定时任务 + 健康检查配合。

```java
@Service
public class AlertMailService {

    @Autowired
    private MailService mailService;

    @Value("${alert.mail.to:admin@qq.com}")
    private String alertRecipient;

    /**
     * 发送系统异常告警
     */
    public void sendExceptionAlert(Throwable exception, String serviceName) {
        String html = """
            <div style="max-width:600px;padding:20px;">
                <h2 style="color:#e74c3c;border-bottom:2px solid #e74c3c;
                           padding-bottom:10px;">系统异常告警</h2>
                <table style="width:100%%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:8px;border:1px solid #eee;background:#f9f9f9;
                                width:120px;">服务名称</td>
                        <td style="padding:8px;border:1px solid #eee;">%s</td></tr>
                    <tr><td style="padding:8px;border:1px solid #eee;background:#f9f9f9;">
                                异常类型</td>
                        <td style="padding:8px;border:1px solid #eee;">%s</td></tr>
                    <tr><td style="padding:8px;border:1px solid #eee;background:#f9f9f9;">
                                异常信息</td>
                        <td style="padding:8px;border:1px solid #eee;">%s</td></tr>
                    <tr><td style="padding:8px;border:1px solid #eee;background:#f9f9f9;">
                                发生时间</td>
                        <td style="padding:8px;border:1px solid #eee;">%s</td></tr>
                </table>
                <details style="margin-top:16px;">
                    <summary style="cursor:pointer;color:#666;">异常堆栈</summary>
                    <pre style="background:#f5f5f5;padding:12px;border-radius:4px;
                                font-size:12px;overflow-x:auto;max-height:400px;">%s</pre>
                </details>
            </div>
            """.formatted(
                serviceName,
                exception.getClass().getName(),
                exception.getMessage() != null ? exception.getMessage() : "(无)",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")),
                joinStackTrace(exception)
            );

        mailService.sendHtmlMail(alertRecipient,
                "【告警】" + serviceName + " 发生异常", html);
    }

    /**
     * 发送资源使用率告警
     */
    public void sendResourceAlert(String resource, double usagePercent, double threshold) {
        String color = usagePercent > 90 ? "#e74c3c" : "#f39c12";  // 红色 vs 橙色
        String html = """
            <div style="padding:20px;">
                <h2 style="color:%s;">资源使用率告警</h2>
                <p>%s 使用率达到 <b style="font-size:18px;">%.1f%%</b>，阈值 %.0f%%。</p>
                <p style="color:#999;">请及时排查处理。</p>
            </div>
            """.formatted(color, resource, usagePercent, threshold);

        mailService.sendHtmlMail(alertRecipient,
                "【资源告警】" + resource + " 使用率 " + String.format("%.0f", usagePercent) + "%", html);
    }

    private String joinStackTrace(Throwable e) {
        StringWriter sw = new StringWriter();
        e.printStackTrace(new PrintWriter(sw));
        return sw.toString();
    }
}
```

**与全局异常处理器配合：**

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @Autowired
    private AlertMailService alertMailService;

    @ExceptionHandler(Exception.class)
    public R<Void> handle(Exception e) {
        log.error("未捕获异常", e);

        // 异步发送告警邮件，不阻塞响应
        CompletableFuture.runAsync(() -> {
            try {
                alertMailService.sendExceptionAlert(e, "api-service");
            } catch (Exception ex) {
                log.error("告警邮件发送失败", ex);
            }
        });

        return R.fail("服务器内部错误");
    }
}
```

**定时巡检磁盘和内存：**

```java
@Component
public class ResourceHealthChecker {

    @Autowired
    private AlertMailService alertMailService;

    @Scheduled(fixedDelay = 300000)  // 每 5 分钟
    public void checkDisk() {
        File root = new File("/");
        long total = root.getTotalSpace();
        long free = root.getFreeSpace();
        double usagePercent = (1.0 - (double) free / total) * 100;

        if (usagePercent > 85) {
            alertMailService.sendResourceAlert("磁盘 /", usagePercent, 85);
        }
    }

    @Scheduled(fixedDelay = 60000)   // 每 1 分钟
    public void checkMemory() {
        Runtime runtime = Runtime.getRuntime();
        long used = runtime.totalMemory() - runtime.freeMemory();
        double usagePercent = (double) used / runtime.maxMemory() * 100;

        if (usagePercent > 90) {
            alertMailService.sendResourceAlert("JVM 内存", usagePercent, 90);
        }
    }
}
```

---

## 13. 最佳实践与踩坑记录

### 13.1 推荐做法

**1. HTML 邮件同时提供纯文本降级**

```java
helper.setText(plainText, htmlText);
```

第一个参数是客户端不支持 HTML 时显示的纯文本，养成习惯写上。

**2. 异步发送，线程池隔离**

邮件是典型的非核心链路，主线程不该等邮件发完再返回。用独立线程池 + `CallerRunsPolicy` 防止丢任务。

**3. CSS 全部内联**

邮件客户端（Gmail/Outlook/QQ邮箱）几乎都过滤 `<style>` 标签和外部 CSS 文件。所有样式写在元素 style 属性里。

**4. 发送频率控制**

防止被 SMTP 服务器限流。在发送验证码的场景中，同一邮箱 60 秒内只允许发一次。

**5. 不要信任 HTML 内容的用户输入**

如果邮件内容拼接了用户输入的字段（如用户名），必须转义 HTML：

```java
String safeName = HtmlUtils.htmlEscape(user.getName());
context.setVariable("username", safeName);
```

否则用户名叫 `<script>alert(1)</script>` 会让你被投诉。

### 13.2 踩坑记录

**坑 1：阿里云/腾讯云封禁 25 端口**

云服务器默认封 25 端口（防垃圾邮件）。用 465（SSL）或 587（TLS），不要用 25。

**坑 2：授权码不是邮箱密码**

QQ/163/Gmail 的 SMTP 密码是独立生成的授权码，在邮箱设置里找。用登录密码连不上。

**坑 3：`@Async` 不生效**

`@Async` 必须通过 Spring 代理调用——同一个类内直接调 `this.asyncMethod()` 不走代理，注解无效。要么把异步方法拆到单独的 Service，要么注入自己：

```java
@Service
public class UserService {
    @Autowired
    private UserService self;  // 注入代理

    public void register(RegisterDTO dto) {
        // ...
        self.sendMail(dto.getEmail());  // 通过代理调用，@Async 生效
    }

    @Async
    public void sendMail(String email) { ... }
}
```

**坑 4：连接池耗尽**

JavaMail 默认没有连接池。高并发场景下频繁创建 SMTP 连接会很慢。解决方案：用 Spring 的 `JavaMailSenderImpl`，它的 session 会复用连接；或者引入 Commons Email 的连接池。

**坑 5：附件名中文乱码**

Spring 5.3+ 在构造 `MimeMessageHelper` 时传 UTF-8 后附件中文名基本正常。如果仍有问题，手动 `MimeUtility.encodeText` 编码：

```java
helper.addAttachment(
    MimeUtility.encodeText("月度报表.pdf", "UTF-8", "B"),
    file
);
```

**坑 6：HTML 邮件在 Gmail 中布局错乱**

Gmail 会删除 `<head>` 中的所有内容。把 CSS 全部移到元素内联 style，不要依赖外部样式。

**坑 7：`FileSystemResource` 找不到文件**

`FileSystemResource` 是绝对路径，用相对路径会被解析为 JVM 启动目录。运行时找不到文件的原因通常在这。

```java
// 不推荐
new FileSystemResource("templates/report.pdf");

// 推荐
new FileSystemResource(new File("/absolute/path/to/report.pdf"));
// 或者从 classpath 读取
new ClassPathResource("templates/report.pdf");
```

**坑 8：QQ 邮箱的每日发送上限**

个人 QQ 邮箱每日发送上限约 500 封，企业邮箱按套餐不同。超出后 SMTP 返回 550 错误。如果批量发送，用企业邮箱或专门的邮件服务（SendCloud / 阿里云邮件推送）。

**坑 9：Gmail 要求 "允许不够安全的应用" 或使用应用专用密码**

Gmail 从 2022 年起不再支持"允许不够安全的应用"。正确做法：
1. 开启两步验证
2. 生成应用专用密码
3. 用应用专用密码作为 `spring.mail.password`

---

## 14. 参考链接

- Spring Boot Mail 官方文档：https://docs.spring.io/spring-boot/reference/io/email.html
- Spring Framework Mail 文档：https://docs.spring.io/spring-framework/reference/integration/email.html
- Thymeleaf 官方文档：https://www.thymeleaf.org/doc/tutorials/3.0/usingthymeleaf.html
- FreeMarker 官方文档：https://freemarker.apache.org/docs/
- QQ 邮箱 SMTP 设置指引：https://service.mail.qq.com/detail/0/310
- [[spring-boot-redis]] — 验证码存储与频率控制
- [[spring-boot-scheduled]] — 定时巡检配合告警邮件
- [[spring-boot-rabbitmq]] — MQ 解耦邮件发送
