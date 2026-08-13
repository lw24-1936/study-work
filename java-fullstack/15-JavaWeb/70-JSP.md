---
title: JSP
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [jsp, el, jstl, tag, jsp-lifecycle, java-web]
---

# JSP

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [JSP 生命周期](#jsp-生命周期)
- [JSP 基本语法](#jsp-基本语法)
- [JSP 九大内置对象](#jsp-九大内置对象)
- [JSP 四大作用域](#jsp-四大作用域)
- [EL 表达式](#el-表达式)
- [JSTL 标准标签库](#jstl-标准标签库)
- [自定义标签（Tag）](#自定义标签tag)
- [JSP 与 Servlet 的关系](#jsp-与-servlet-的关系)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

JSP（Jakarta Server Pages，原名 JavaServer Pages）是 Servlet 的扩展——它本质上就是一个 Servlet。JSP 让开发者可以用 HTML 的方式写页面，在其中嵌入 Java 代码，由容器自动编译为 Servlet 类并执行。

JSP 属于传统 Java Web 技术。在现代项目中，前后端分离是主流，Spring Boot 默认也不推荐 JSP 作为视图层（更推荐 Thymeleaf 或纯前后端分离）。但理解 JSP 对阅读遗留项目代码和面试仍有价值。

```text
.jsp 文件 --> 容器翻译为 .java（Servlet 源码） --> 编译为 .class --> 执行
```

## JSP 生命周期

JSP 的生命周期与 Servlet 类似，但多了一个"翻译"阶段：

```text
翻译阶段 --> 编译阶段 --> 加载/实例化 --> 初始化 --> 服务 --> 销毁
                    jspInit()         _jspService()   jspDestroy()
```

### 阶段详解

**阶段 1 & 2：翻译与编译**

容器将 .jsp 文件翻译为 Servlet 源码（类名如 `index_jsp`），然后编译为 .class。这个过程发生在：
- 第一次请求该 JSP 时（默认）
- 或者在 `<jsp-file>` 中配置 load-on-startup 时

Tomcat 生成的 Servlet 源码可以在 `tomcat/work/Catalina/localhost/<app>/org/apache/jsp/` 下找到。

**阶段 3 & 4：加载与初始化 —— jspInit()**

```java
public void jspInit() {
    // 等价于 Servlet 的 init()
    // 只调用一次，可重写来做初始化
}
```

**阶段 5：服务 —— _jspService()**

容器自动生成 `_jspService()` 方法，包含所有 JSP 页面内容的执行逻辑。每次请求都会调用。

```java
// 容器自动生成的 _jspService() 大致结构
public void _jspService(HttpServletRequest request, HttpServletResponse response) {
    // 1. 声明内置对象（request、response、session、out 等）
    // 2. HTML 模板内容逐行输出 out.write("<html>...")
    // 3. Java 脚本片段直接嵌入
    // 4. EL 表达式求值
}
```

**关键**：`_jspService()` 是容器自动生成的，开发者不能重写它。

**阶段 6：销毁 —— jspDestroy()**

```java
public void jspDestroy() {
    // 容器关闭时调用，释放资源
}
```

### 完整示例：JSP 翻译后的源码结构

假设有一个 `hello.jsp`：

```jsp
<%@ page contentType="text/html;charset=UTF-8" %>
<html>
<body>
<% String name = "World"; %>
<h1>Hello, <%= name %></h1>
</body>
</html>
```

翻译后的大致结构：

```java
public final class hello_jsp extends HttpJspBase {
    public void _jspService(HttpServletRequest request, HttpServletResponse response) {
        // 内置对象声明
        PageContext pageContext = null;
        HttpSession session = null;
        ServletContext application = null;
        ServletConfig config = null;
        JspWriter out = null;

        response.setContentType("text/html;charset=UTF-8");
        pageContext = _jspxFactory.getPageContext(this, request, response, null, true, 8192, true);
        application = pageContext.getServletContext();
        config = pageContext.getServletConfig();
        session = pageContext.getSession();
        out = pageContext.getOut();

        // HTML 模板
        out.write("<html>\r\n");
        out.write("<body>\r\n");

        // 脚本片段
        String name = "World";

        out.write("<h1>Hello, ");
        out.print(name);   // 表达式输出
        out.write("</h1>\r\n");
        out.write("</body>\r\n");
        out.write("</html>\r\n");
    }
}
```

可以看到：JSP 中的 HTML 变成了 `out.write()`，Java 代码原样保留，表达式变成了 `out.print()`。这就是 JSP 的本质——HTML 中嵌入 Java 代码的 Servlet。

## JSP 基本语法

### 1. 脚本元素

```jsp
<%-- 声明 —— 定义成员变量和方法 --%>
<%!
    private int count = 0;
    public int getCount() { return ++count; }
%>

<%-- 脚本片段 —— 方法中的 Java 代码 --%>
<%
    String message = "Hello";
    List<String> names = Arrays.asList("张三", "李四");
    for (String name : names) {
%>
    <p>名字：<%= name %></p>  <%-- 表达式 —— 输出变量 --%>
<%
    }
%>
```

**比较**：

| 元素 | 语法 | 翻译后位置 | 线程安全 |
|------|------|-----------|---------|
| 声明 `<%! %>` | 成员变量/方法 | 类级别 | 共享变数，线程不安全 |
| 脚本 `<% %>` | Java 代码块 | `_jspService()` 方法内 | 局部变量，线程安全 |
| 表达式 `<%= %>` | 输出值 | `out.print()` | 与脚本同 |

### 2. 指令（Directive）

```jsp
<%-- page 指令：页面配置 --%>
<%@ page contentType="text/html;charset=UTF-8" language="java"
         import="java.util.*,java.text.*"
         errorPage="/error.jsp"
         isErrorPage="false"
         session="true"
         buffer="8kb"
         autoFlush="true"
         isELIgnored="false"
         pageEncoding="UTF-8" %>

<%-- include 指令：静态包含，编译时合并（多个文件合并为一个 Servlet） --%>
<%@ include file="header.jsp" %>

<%-- taglib 指令：引入标签库 --%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
```

### 3. 动作（Action）

```jsp
<%-- 动态包含：运行时包含（每个文件单独编译为独立的 Servlet） --%>
<jsp:include page="header.jsp">
    <jsp:param name="title" value="首页" />
</jsp:include>

<%-- 转发 --%>
<jsp:forward page="result.jsp">
    <jsp:param name="message" value="操作成功" />
</jsp:forward>

<%-- JavaBean 操作 --%>
<jsp:useBean id="user" class="com.example.User" scope="session" />
<jsp:setProperty name="user" property="username" value="zhangsan" />
<jsp:getProperty name="user" property="username" />
```

### `<%-- --%>` vs `<!-- -->`

```jsp
<%-- JSP 注释：服务端注释，不会发送到浏览器 --%>
<!-- HTML 注释：客户端注释，浏览器查看源码可见 -->
```

### `<%@ include %>` vs `<jsp:include>`

| 维度 | `<%@ include %>` | `<jsp:include>` |
|------|-----------------|----------------|
| 时机 | 编译时（翻译阶段） | 运行时（服务阶段） |
| 合并方式 | 源码合并为一个 Servlet | 各自编译，运行时调 include() |
| 文件个数 | 生成 1 个 .class | 各自生成 .class |
| 性能 | 快（无运行时开销） | 慢（运行时调用） |
| 适用场景 | 不变的内容（公共头/尾） | 动态变化的内容 |

## JSP 九大内置对象

JSP 在 `_jspService()` 方法中自动创建了九个可直接使用的对象：

| 对象 | 类型 | 说明 |
|------|------|------|
| request | HttpServletRequest | 请求对象 |
| response | HttpServletResponse | 响应对象 |
| session | HttpSession | 会话对象（page 指令 session="false" 时不可用） |
| application | ServletContext | 应用上下文 |
| out | JspWriter | 输出流（缓冲，最终整合到 response.getWriter()） |
| page | Object | 当前 Servlet 实例（this） |
| pageContext | PageContext | 页面上下文，可获取其他 8 个对象 + 操作四大作用域 |
| config | ServletConfig | Servlet 配置信息 |
| exception | Throwable | 异常对象（仅 isErrorPage="true" 时可用） |

### pageContext —— 作用域操作的统一入口

```jsp
<%
    // 向四个作用域存取属性
    pageContext.setAttribute("key", "page");
    request.setAttribute("key", "request");
    session.setAttribute("key", "session");
    application.setAttribute("key", "application");

    // pageContext 按顺序搜索：page -> request -> session -> application
    Object value = pageContext.findAttribute("key");  // 返回 "page"

    // 跨作用域存取
    pageContext.setAttribute("key", "value", PageContext.SESSION_SCOPE);
    Object sessionVal = pageContext.getAttribute("key", PageContext.SESSION_SCOPE);
%>
```

## JSP 四大作用域

| 作用域 | 类型 | 生命周期 | 使用场景 |
|--------|------|---------|---------|
| page | PageContext | 当前页面 | 当前页面的临时数据 |
| request | HttpServletRequest | 一次请求（含转发） | 转发间传递数据 |
| session | HttpSession | 一次会话 | 登录信息、用户偏好 |
| application | ServletContext | 整个应用 | 全局配置、在线人数 |

```jsp
<%
    pageContext.setAttribute("scope", "pageScope");
    request.setAttribute("scope", "requestScope");
    session.setAttribute("scope", "sessionScope");
    application.setAttribute("scope", "appScope");
%>

<%-- EL 表达式取值 --%>
${pageScope.scope}       <%-- pageScope --%>
${requestScope.scope}    <%-- requestScope --%>
${sessionScope.scope}    <%-- sessionScope --%>
${applicationScope.scope} <%-- appScope --%>
${scope}                 <%-- 省略域对象：按 page -> request -> session -> application 搜索 --%>
```

## EL 表达式

EL（Expression Language）最初是 JSTL 1.0 的一部分，后来成为 JSP 2.0 标准。它的作用是替代 JSP 中的 Java 脚本表达式 `<%= %>`，让页面更简洁。

```jsp
<%-- 旧方式 --%>
<%= ((User) request.getAttribute("user")).getName() %>

<%-- EL 方式 --%>
${user.name}
```

### EL 语法

```jsp
<%-- 基本用法 --%>
${user}                         // 从四个作用域查找 "user" 属性
${user.name}                    // 访问对象的 getName()，等价 user["name"]
${list[0]}                      // 列表元素
${map["key"]}                   // Map 取值（key 含特殊字符时必须用此语法）
${map.key}                      // Map 取值（key 为简单字符串）

<%-- 运算符 --%>
${1 + 2}                        // 算数
${1 > 2}                        // 比较（也可用 gt、lt 等）
${empty list}                   // 判断 null 或空集合
${not empty list}               // 非空
${a && b}                       // 逻辑与（也可用 and）
${a || b}                       // 逻辑或（也可用 or）
${a ? b : c}                    // 三元运算

<%-- 隐式对象 --%>
${pageContext.request.contextPath}    // 获取应用路径
${param.username}                     // request.getParameter("username")
${paramValues.hobby}                  // request.getParameterValues("hobby") —— 数组
${header["User-Agent"]}              // 请求头
${headerValues["Accept-Encoding"]}    // 多值头
${cookie.JSESSIONID.value}            // Cookie 值
${initParam.appName}                  // ServletContext 初始化参数
```

### EL 隐式对象一览

| 隐式对象 | 说明 |
|---------|------|
| pageScope | page 域属性 Map |
| requestScope | request 域属性 Map |
| sessionScope | session 域属性 Map |
| applicationScope | application 域属性 Map |
| param | 请求参数 Map（单值） |
| paramValues | 请求参数 Map（多值 String[]） |
| header | 请求头 Map（单值） |
| headerValues | 请求头 Map（多值） |
| cookie | Cookie Map |
| initParam | 上下文初始化参数 Map |
| pageContext | PageContext 对象 |

### EL 值获取原理

当写 `${user.name}` 时，EL 引擎不是直接反射调用 `getUser().getName()`，而是按以下顺序解析：

1. `user` → 从 pageScope/requestScope/sessionScope/applicationScope 中查找属性名为 "user" 的对象
2. 找到对象后，`name` → 先尝试 `user.getName()`，如果不存在则尝试 `user.get("name")`（对 Map）
3. 如果都不成功，返回 `null`（但页面不显示，EL 对 null 友好——直接显示空而不是 NPE）

**注意**：要使用 JavaBean 的对象属性和 Map 值，属性名（如 `name`）必须遵循 JavaBean 命名规范——实际上对应 `getName()` 方法。

### EL 空值处理

EL 对 null 非常友好——不会抛 NullPointerException：

```jsp
${nullValue}             <%-- 输出空字符串，不是 "null" --%>
${nullValue.name}        <%-- 输出空字符串，不会 NPE --%>
${empty nullValue}       <%-- true --%>
```

## JSTL 标准标签库

JSTL（JSP Standard Tag Library）是 JSP 的标准标签库，提供了一套标签替代 JSP 中的 Java 脚本片段。

### 引入 JSTL

```xml
<dependency>
    <groupId>jakarta.servlet.jsp.jstl</groupId>
    <artifactId>jakarta.servlet.jsp.jstl-api</artifactId>
    <version>3.0.0</version>
</dependency>
<dependency>
    <groupId>org.glassfish.web</groupId>
    <artifactId>jakarta.servlet.jsp.jstl</artifactId>
    <version>3.0.1</version>
</dependency>
```

JSP 中使用：

```jsp
<%@ taglib prefix="c" uri="jakarta.tags.core" %>        <%-- 核心标签 --%>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>        <%-- 格式化标签 --%>
<%@ taglib prefix="fn" uri="jakarta.tags.functions" %>   <%-- 函数标签 --%>
<%@ taglib prefix="sql" uri="jakarta.tags.sql" %>        <%-- SQL 标签（不推荐用） --%>
```

### Core 标签库（c:）

```jsp
<%-- 变量操作 --%>
<c:set var="username" value="zhangsan" scope="session" />
<c:out value="${username}" default="匿名用户" escapeXml="true" />
<c:remove var="username" scope="session" />

<%-- 条件判断 --%>
<c:if test="${not empty user}">
    <p>欢迎，${user.name}</p>
</c:if>

<c:choose>
    <c:when test="${score >= 90}">优秀</c:when>
    <c:when test="${score >= 60}">及格</c:when>
    <c:otherwise>不及格</c:otherwise>
</c:choose>

<%-- 循环 --%>
<c:forEach var="user" items="${userList}" varStatus="status">
    <tr>
        <td>${status.index + 1}</td>     <%-- 索引从 0 开始 --%>
        <td>${status.count}</td>          <%-- 计数从 1 开始 --%>
        <td>${user.name}</td>
        <td>${user.email}</td>
    </tr>
</c:forEach>

<%-- 遍历 Map --%>
<c:forEach var="entry" items="${myMap}">
    <p>${entry.key} : ${entry.value}</p>
</c:forEach>

<%-- forTokens 分割字符串 --%>
<c:forTokens var="item" items="apple,banana,orange" delims=",">
    <span>${item}</span>
</c:forTokens>

<%-- URL 构建（自动追加 contextPath 和 sessionId） --%>
<c:url var="profileUrl" value="/user/profile">
    <c:param name="id" value="${user.id}" />
    <c:param name="tab" value="settings" />
</c:url>
<a href="${profileUrl}">个人中心</a>

<%-- 重定向 --%>
<c:redirect url="/login" />

<%-- 导入外部资源 --%>
<c:import url="https://example.com/api/data" var="externalData" />
```

### 格式化标签库（fmt:）

```jsp
<%-- 数字格式化 --%>
<fmt:formatNumber value="12345.678" pattern="#,##0.00" />
<%-- 输出：12,345.68 --%>

<%-- 货币格式化 --%>
<fmt:formatNumber value="12345.67" type="currency" currencyCode="CNY" />
<%-- 输出：CNY12,345.67 --%>

<%-- 日期格式化 --%>
<jsp:useBean id="now" class="java.util.Date" />
<fmt:formatDate value="${now}" pattern="yyyy-MM-dd HH:mm:ss" />
<%-- 输出：2026-08-12 14:30:00 --%>

<%-- 解析字符串为日期 --%>
<fmt:parseDate value="2026-08-12" pattern="yyyy-MM-dd" var="parsedDate" />

<%-- 国际化资源绑定 --%>
<fmt:setBundle basename="messages" />
<fmt:message key="welcome" />
```

### 函数标签库（fn:）

```jsp
<%@ taglib prefix="fn" uri="jakarta.tags.functions" %>

${fn:length(list)}               <%-- 集合大小/字符串长度 --%>
${fn:contains(str, "keyword")}   <%-- 是否包含 --%>
${fn:startsWith(str, "prefix")}
${fn:endsWith(str, "suffix")}
${fn:substring(str, 0, 10)}      <%-- 截取 --%>
${fn:replace(str, "old", "new")}
${fn:trim(str)}
${fn:toUpperCase(str)}
${fn:toLowerCase(str)}
${fn:split(str, ",")}            <%-- 分割为数组 --%>
${fn:join(array, ",")}           <%-- 拼接 --%>
${fn:escapeXml(html)}            <%-- HTML 转义防 XSS --%>
```

## 自定义标签（Tag）

自定义标签允许开发者封装可复用的 JSP 逻辑，替代页面中的 Java 脚本。

### 传统标签（Tag 接口，已过时）

需要实现 Tag / BodyTag 接口，编写 TLD 描述文件。这套 API 比较冗长，Spring 框架也提供了自己的自定义标签（如 `<spring:bind>`）。

### 简单标签（SimpleTag，JSP 2.0+）

继承 SimpleTagSupport，比传统标签简单很多：

```java
// 自定义 if 标签
public class IfTag extends SimpleTagSupport {

    private boolean test;

    public void setTest(boolean test) {
        this.test = test;
    }

    @Override
    public void doTag() throws JspException, IOException {
        if (test) {
            getJspBody().invoke(null);  // 执行标签体内容
        }
    }
}
```

TLD 文件（/WEB-INF/custom.tld）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<taglib xmlns="https://jakarta.ee/xml/ns/jakartaee"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="https://jakarta.ee/xml/ns/jakartaee
                            https://jakarta.ee/xml/ns/jakartaee/web-jsptaglibrary_3_0.xsd"
        version="3.0">
    <tlib-version>1.0</tlib-version>
    <short-name>custom</short-name>
    <uri>http://example.com/tags</uri>

    <tag>
        <name>if</name>
        <tag-class>com.example.IfTag</tag-class>
        <body-content>scriptless</body-content>
        <attribute>
            <name>test</name>
            <required>true</required>
            <rtexprvalue>true</rtexprvalue>  <%-- 支持 EL 表达式 --%>
        </attribute>
    </tag>
</taglib>
```

JSP 中使用：

```jsp
<%@ taglib prefix="my" uri="http://example.com/tags" %>

<my:if test="${not empty user}">
    <p>欢迎您，${user.name}</p>
</my:if>
```

### 标签文件（Tag File，最简单的方式）

JSP 2.0 引入，将 JSP 片段直接作为标签使用，无需写 Java 类。

文件：`/WEB-INF/tags/hello.tag`

```jsp
<%@ tag pageEncoding="UTF-8" %>
<%@ attribute name="name" required="true" rtexprvalue="true" %>
<div style="color:blue;">
    Hello, ${name}!
</div>
```

JSP 中使用：

```jsp
<%@ taglib prefix="my" tagdir="/WEB-INF/tags" %>
<my:hello name="${user.username}" />
```

标签文件是快速创建可复用 JSP 组件的最简单方式，适合内网管理系统的组件化。

## JSP 与 Servlet 的关系

```text
                  ┌─────────────────────┐
                  │       浏览器         │
                  └────────┬────────────┘
                           │ HTTP Request
                           v
                  ┌─────────────────────┐
                  │    Servlet Container │
                  │    (Tomcat)          │
                  └────────┬────────────┘
                           │
              ┌────────────┴────────────┐
              v                         v
    ┌─────────────────┐       ┌─────────────────┐
    │   Servlet        │       │   JSP            │
    │  (控制器/逻辑层) │<----->│  (视图/展示层)  │
    │                  │  转发 │                  │
    │  doGet/doPost    │       │  HTML + EL + JSTL │
    │  处理业务逻辑    │       │  渲染页面         │
    └─────────────────┘       └─────────────────┘
```

**核心关系**：JSP 就是 Servlet。传统 MVC 模式（Model 1 / Model 2）中，Servlet 充当 Controller 处理业务逻辑，JSP 充当 View 负责页面渲染。

### Model 2（MVC）模式示例

```java
// Controller: UserServlet
@WebServlet("/users")
public class UserServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        List<User> userList = userService.findAll();
        req.setAttribute("userList", userList);
        req.getRequestDispatcher("/WEB-INF/views/userList.jsp").forward(req, resp);
    }
}
```

```jsp
<%-- View: userList.jsp --%>
<%@ page contentType="text/html;charset=UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<html>
<head><title>用户列表</title></head>
<body>
    <table>
        <c:forEach var="user" items="${userList}">
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.email}</td>
            </tr>
        </c:forEach>
    </table>
</body>
</html>
```

**将 JSP 放在 WEB-INF 下的原因**：WEB-INF 目录下的资源不能通过浏览器直接访问，只能通过 Servlet 转发到达。这防止用户绕过 Controller 直接访问 JSP。

## 应用场景实战

### 场景 1：传统 MVC 用户管理系统

使用 Servlet + JSP + JSTL 构建经典的 Model 2 模式 CRUD 系统。

**UserServlet.java**（Controller）

```java
@WebServlet("/admin/users/*")
public class UserServlet extends HttpServlet {

    // 模拟数据库
    private List<User> users = new ArrayList<>(
        Arrays.asList(
            new User(1, "张三", "zhangsan@example.com"),
            new User(2, "李四", "lisi@example.com")
        )
    );

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        String pathInfo = req.getPathInfo();

        if ("/list".equals(pathInfo)) {
            // 用户列表
            req.setAttribute("userList", users);
            req.getRequestDispatcher("/WEB-INF/views/userList.jsp").forward(req, resp);

        } else if ("/add".equals(pathInfo)) {
            // 新增页面
            req.getRequestDispatcher("/WEB-INF/views/userForm.jsp").forward(req, resp);

        } else if (pathInfo != null && pathInfo.startsWith("/edit/")) {
            // 编辑页面
            String idStr = pathInfo.substring(6);
            int id = Integer.parseInt(idStr);
            User user = users.stream().filter(u -> u.getId() == id).findFirst().orElse(null);
            req.setAttribute("user", user);
            req.getRequestDispatcher("/WEB-INF/views/userForm.jsp").forward(req, resp);
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        String pathInfo = req.getPathInfo();
        String name = req.getParameter("name");
        String email = req.getParameter("email");

        if ("/add".equals(pathInfo)) {
            int newId = users.stream().mapToInt(User::getId).max().orElse(0) + 1;
            users.add(new User(newId, name, email));
            req.setAttribute("message", "添加成功");

        } else if ("/delete".equals(pathInfo)) {
            int id = Integer.parseInt(req.getParameter("id"));
            users.removeIf(u -> u.getId() == id);
            req.setAttribute("message", "删除成功");
        }

        resp.sendRedirect(req.getContextPath() + "/admin/users/list");
    }
}
```

**userList.jsp**（View —— 列表页）

```jsp
<%@ page contentType="text/html;charset=UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<html>
<head>
    <title>用户列表</title>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h2>用户列表</h2>
    <a href="${pageContext.request.contextPath}/admin/users/add">新增用户</a>

    <c:if test="${not empty message}">
        <p style="color:green;">${message}</p>
    </c:if>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>姓名</th>
                <th>邮箱</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            <c:choose>
                <c:when test="${not empty userList}">
                    <c:forEach var="user" items="${userList}" varStatus="s">
                        <tr>
                            <td>${user.id}</td>
                            <td><c:out value="${user.name}" /></td>
                            <td><c:out value="${user.email}" /></td>
                            <td>
                                <a href="edit/${user.id}">编辑</a>
                                <form method="post" action="delete" style="display:inline">
                                    <input type="hidden" name="id" value="${user.id}">
                                    <button type="submit">删除</button>
                                </form>
                            </td>
                        </tr>
                    </c:forEach>
                </c:when>
                <c:otherwise>
                    <tr><td colspan="4">暂无数据</td></tr>
                </c:otherwise>
            </c:choose>
        </tbody>
    </table>
</body>
</html>
```

**userForm.jsp**（View —— 表单页）

```jsp
<%@ page contentType="text/html;charset=UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<html>
<head><title>用户表单</title></head>
<body>
    <h2><c:choose>
        <c:when test="${not empty user}">编辑用户</c:when>
        <c:otherwise>新增用户</c:otherwise>
    </c:choose></h2>

    <form method="post"
          action="${pageContext.request.contextPath}/admin/users/${empty user ? 'add' : 'update'}">
        <c:if test="${not empty user}">
            <input type="hidden" name="id" value="${user.id}">
        </c:if>
        <p>姓名：<input type="text" name="name" value="${user.name}"></p>
        <p>邮箱：<input type="email" name="email" value="${user.email}"></p>
        <p><button type="submit">保存</button></p>
    </form>
</body>
</html>
```

### 场景 2：EL + JSTL 构建数据仪表盘

```jsp
<%@ page contentType="text/html;charset=UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<jsp:useBean id="now" class="java.util.Date" />
<html>
<head><title>数据仪表盘</title></head>
<body>
    <h2>数据概览 - <fmt:formatDate value="${now}" pattern="yyyy-MM-dd HH:mm" /></h2>

    <!-- 统计卡片 -->
    <div class="stats">
        <c:set var="totalUsers" value="${stats.totalUsers}" />
        <c:set var="activeUsers" value="${stats.activeUsers}" />
        <c:set var="todayOrders" value="${stats.todayOrders}" />
        <c:set var="revenue" value="${stats.todayRevenue}" />

        <p>总用户数：<fmt:formatNumber value="${totalUsers}" /></p>
        <p>活跃用户：<fmt:formatNumber value="${activeUsers}" />
           （占比：<fmt:formatNumber value="${activeUsers / totalUsers}" type="percent" maxFractionDigits="1" />）</p>
        <p>今日订单：${todayOrders}</p>
        <p>今日营收：<fmt:formatNumber value="${revenue}" type="currency" currencyCode="CNY" /></p>
    </div>

    <!-- 订单列表 -->
    <table>
        <thead><tr><th>订单号</th><th>金额</th><th>状态</th></tr></thead>
        <tbody>
            <c:forEach var="order" items="${orderList}">
                <tr>
                    <td>${order.orderNo}</td>
                    <td><fmt:formatNumber value="${order.amount}" pattern="0.00" /></td>
                    <td>
                        <c:choose>
                            <c:when test="${order.status == 'PAID'}">已支付</c:when>
                            <c:when test="${order.status == 'PENDING'}">待支付</c:when>
                            <c:when test="${order.status == 'SHIPPED'}">已发货</c:when>
                            <c:otherwise>未知</c:otherwise>
                        </c:choose>
                    </td>
                </tr>
            </c:forEach>
        </tbody>
    </table>
</body>
</html>
```

## 最佳实践与踩坑记录

### 最佳实践

1. **JSP 只做展示，不做业务逻辑**。商业逻辑放在 Servlet/Service/DAO 中，JSP 只用 EL + JSTL 渲染数据。看到页面中的 `<% %>` 脚本片段应该警觉——几乎总有更好的方式。

2. **JSP 放在 WEB-INF 下**。防止通过 URL 直接访问 JSP，强制走 Controller 转发。这是 Model 2 模式的标准做法。

3. **用 `<c:out>` 代替直接 `${}` 输出用户输入的数据**。`<c:out>` 默认会转义 HTML（`escapeXml="true"`），防止 XSS 攻击：

```jsp
<%-- 不安全：用户输入 <script>alert('XSS')</script> 会执行 --%>
${user.nickname}

<%-- 安全：HTML 特殊字符会被转义 --%>
<c:out value="${user.nickname}" />
```

4. **用 JSTL 和 EL 替代所有 Scriptlet**。`<%= %>` 和 `<% %>` 让页面难以维护和测试。JSP 2.0+ 完全可以只用 EL + JSTL 写页面。

5. **避免在 JSP 中创建数据库连接**。这是经典的坏味道——数据库连接应由容器管理（数据源 JNDI），或通过 Service 层注入。

### 踩坑记录

**坑 1：EL 表达式不生效**

检查 `web.xml` 或 page 指令中的 `isELIgnored` 配置：
- JSP 2.0（Servlet 2.4）默认支持 EL
- 如果使用 Servlet 2.3 的 web.xml（DOCTYPE 声明），EL 默认被忽略，需要在 page 指令中设置 `<%@ page isELIgnored="false" %>`

**坑 2：`<c:forEach>` 遍历大集合 OOM**

JSTL 标签在处理大量数据时会把整个集合加载到内存。百万级数据不要直接传给 JSP——用分页。

**坑 3：`<c:import>` 引用外部慢 URL 导致页面卡死**

`<c:import>` 会同步等待外部资源。外部 API 超时会导致整个页面不可用：

```jsp
<%-- 危险 --%>
<c:import url="https://slow-external-api.com/data" var="data" />
```

**坑 4：JSP 修改后不生效**

JSP 修改后若迟迟不更新，通常有两个原因：
1. 开发模式未开启：检查 web.xml 中 `<servlet>` 的 `<init-param>` 中 `development` 是否设为 `true`
2. 浏览器缓存：开启了强缓存

在 Tomcat 中，可以配置 `development=true` 和 `checkInterval=0` 让每次请求都检查 JSP 是否更新（开发用，生产环境不要这样配）：

```xml
<servlet>
    <servlet-name>jsp</servlet-name>
    <servlet-class>org.apache.jasper.servlet.JspServlet</servlet-class>
    <init-param>
        <param-name>development</param-name>
        <param-value>true</param-value>
    </init-param>
    <init-param>
        <param-name>checkInterval</param-name>
        <param-value>0</param-value>  <!-- 每次请求都检查 -->
    </init-param>
</servlet>
```

**坑 5：Session 中存大对象序列化失败**

JSP 中的 `<jsp:useBean scope="session">` 或手动存入 Session 的对象必须实现 `Serializable`（如果容器要钝化到磁盘）。遗漏会导致 `NotSerializableException`。

**坑 6：JSP 不能直接放在 Spring Boot 的 jar 包中**

Spring Boot 打包为 executable jar 时，内嵌 Tomcat 不支持 jar 包内的 JSP（Servlet 规范限制）。需要使用 war 部署到独立 Tomcat，或切换到 Thymeleaf / FreeMarker 等模板引擎。
