---
title: SpEL 表达式语言
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [spring, spel, expression, evaluationcontext, spelparser, elvis, collection-projection, bean-reference]
---

# SpEL 表达式语言

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [SpEL 基础 API](#spel-基础-api)
- [字面量与对象访问](#字面量与对象访问)
- [运算符](#运算符)
- [类型表达式与赋值](#类型表达式与赋值)
- [变量与函数](#变量与函数)
- [Bean 引用](#bean-引用)
- [安全导航与集合操作](#安全导航与集合操作)
- [模板表达式](#模板表达式)
- [SpEL 编译优化](#spel-编译优化)
- [Spring 中的 SpEL 应用](#spring-中的-spel-应用)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

SpEL（Spring Expression Language）是 Spring 官方的表达式语言，支持在**运行时**查询和操作对象图。语法类似 Jakarta EL，但额外提供了方法调用、字符串模板等能力。

SpEL 定位：为整个 Spring 生态提供统一的表达式语言。它不是 Spring 专属的——可以脱离 Spring 独立使用，但在 Spring 中广泛用于 `@Value`、`@Cacheable(key)`、`@PreAuthorize`、XML/注解配置等场景。

```text
SpEL 功能全景：
- 字面量、属性/数组/List/Map 访问
- 内联 List/Map、数组构造
- 方法调用、构造器调用
- 关系/逻辑/字符串/数学/正则运算符
- 类型表达式、变量、用户自定义函数
- Bean 引用
- 三元、Elvis、安全导航运算符
- 集合投影、集合选择
- 模板表达式
```

## SpEL 基础 API

### 解析与求值

```java
import org.springframework.expression.Expression;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.StandardEvaluationContext;

public class SpelDemo {
    public static void main(String[] args) {
        // 1. 创建解析器
        ExpressionParser parser = new SpelExpressionParser();

        // 2. 解析表达式（编译为内部 AST）
        Expression expression = parser.parseExpression("'Hello ' + 'World'");

        // 3. 求值
        String result = expression.getValue(String.class);
        System.out.println(result);  // Hello World
    }
}
```

### EvaluationContext

求值上下文，提供表达式求值所需的变量、函数、类型信息：

```java
// 默认上下文（无变量）
Expression exp = parser.parseExpression("T(java.lang.Math).random()");
Double value = exp.getValue(Double.class);

// 标准上下文（可设置变量、根对象、类型定位器）
StandardEvaluationContext context = new StandardEvaluationContext();

// 设置根对象
User user = new User("张三", 25);
context.setRootObject(user);

// 设置变量
context.setVariable("threshold", 100);

// 注册函数
context.registerFunction("reverse", StringUtils.class
    .getDeclaredMethod("reverse", String.class));
```

### getValue 的多种形式

```java
// 返回 Object（自动装箱）
Object value = expression.getValue();

// 指定返回类型
String str = expression.getValue(String.class);
Integer num = expression.getValue(Integer.class);

// 带上下文
Object value = expression.getValue(context);

// 带上下文 + 指定类型
User user = expression.getValue(context, User.class);
```

## 字面量与对象访问

### 字面量

```java
// 字符串（单引号包裹）
"'Hello SpEL'"

// 数字
"42"          // int
"3.14"        // double
"6.0221415E+23"  // 科学计数法
"0xFF"        // 十六进制

// 布尔
"true"
"false"

// null
"null"
```

### 属性访问

```java
// 访问对象的 getter（属性名对应 getName()）
"user.name"              // 等价 user.getName()
"user.address.city"      // 嵌套属性

// 也可以直接用方括号
"user['name']"

// 数组、List、Map 索引
"list[0]"                // List 第 0 个元素
"array[1]"               // 数组第 1 个元素
"map['key']"             // Map 取值
"map.key"                // Map 取值（key 为简单字符串时）
```

```java
public class PropertyDemo {
    public static void main(String[] args) {
        ExpressionParser parser = new SpelExpressionParser();

        User user = new User();
        user.setName("张三");
        user.setAddress(new Address("北京市", "朝阳区"));

        StandardEvaluationContext context = new StandardEvaluationContext(user);

        String name = parser.parseExpression("name").getValue(context, String.class);
        String city = parser.parseExpression("address.city").getValue(context, String.class);

        System.out.println(name);  // 张三
        System.out.println(city);  // 朝阳区
    }
}
```

### 内联 List、Map、数组构造

```java
// 内联 List
"{1, 2, 3, 4}"
"{'a', 'b', 'c'}"

// 内联 Map
"{'name': '张三', 'age': 25}"
"{key1: 'value1', key2: 'value2'}"

// 数组构造（new 关键字）
"new int[]{1, 2, 3}"
"new String[]{'a', 'b'}"
```

```java
List<Integer> list = parser.parseExpression("{1, 2, 3, 4}").getValue(List.class);
Map<String, Object> map = parser.parseExpression("{'name': '张三', 'age': 25}")
    .getValue(Map.class);
int[] arr = parser.parseExpression("new int[]{1, 2, 3}").getValue(int[].class);
```

## 运算符

### 关系运算符

```java
"2 == 2"      // true
"2 eq 2"      // 等价写法
"2 != 3"
"2 < 3"       // 也可用 lt
"2 <= 3"      // le
"2 > 3"       // gt
"2 >= 3"      // ge
"name instanceof T(String)"   // instanceof
```

### 逻辑运算符

```java
"true and false"     // && 的等价写法
"true && false"
"true or false"      // || 的等价写法
"!true"              // not
"not true"
```

### 数学运算符

```java
"1 + 2"
"5 - 3"
"2 * 3"
"10 / 4"     // 整数除法
"10.0 / 4"   // 浮点除法
"7 % 3"      // 取模
"2 ^ 3"      // 幂运算 = 8
```

### 字符串运算符

```java
"'Hello' + ' ' + 'World'"    // 拼接
"'abc'.length()"              // 方法调用
"'hello'.toUpperCase()"       // 转大写
"'abc'.substring(0, 2)"       // 截取
```

### 正则匹配（matches）

```java
// matches 关键字
"'123456' matches '\\d+'"
"'abc@example.com' matches '^[\\w-\\.]+@[\\w-]+\\.\\w+$'"

Boolean valid = parser.parseExpression("'abc@example.com' matches '^[\\\\w-\\\\.]+@[\\\\w-]+\\\\.\\\\w+$'")
    .getValue(Boolean.class);
```

## 类型表达式与赋值

### 类型表达式 T()

`T()` 用于引用类（类型）本身，访问静态成员：

```java
// 访问静态常量
"T(java.lang.Math).PI"
"T(java.lang.Math).random()"

// 访问枚举
"T(com.example.Color).RED"

// 创建对象（构造器调用）
"new com.example.User('张三', 25)"
```

```java
double pi = parser.parseExpression("T(java.lang.Math).PI").getValue(Double.class);
double random = parser.parseExpression("T(java.lang.Math).random()").getValue(Double.class);
```

### 赋值

SpEL 支持赋值操作，用 `setValue()` 或表达式内的 `=`：

```java
// 方式 1：表达式内赋值
parser.parseExpression("name").setValue(context, "李四");
// 等价于 context.getRootObject().setName("李四")

// 方式 2：setValue 直接修改
User user = new User();
StandardEvaluationContext ctx = new StandardEvaluationContext(user);
parser.parseExpression("name").setValue(ctx, "王五");

// 方式 3：完整赋值表达式（较少用）
parser.parseExpression("name = '赵六'").getValue(ctx);
```

## 变量与函数

### 变量（#variable）

变量通过 `#` 前缀引用，在 EvaluationContext 中设置：

```java
StandardEvaluationContext context = new StandardEvaluationContext();
context.setVariable("discount", 0.8);
context.setVariable("taxRate", 0.13);

// 使用变量
Double price = parser.parseExpression("#discount * 100").getValue(context, Double.class);

// 变量参与复杂表达式
Double total = parser.parseExpression(
    "100 * #discount * (1 + #taxRate)").getValue(context, Double.class);
```

Spring 内置变量：

```java
// #root —— 根对象
"#root.name"

// #this —— 当前对象（在集合投影/选择中）
"list.?[#this > 5]"
```

### 函数（#function）

通过 `registerFunction()` 注册自定义函数：

```java
StandardEvaluationContext context = new StandardEvaluationContext();

// 注册函数
context.registerFunction("reverse",
    StringUtils.class.getDeclaredMethod("reverse", String.class));
context.registerFunction("max",
    Math.class.getDeclaredMethod("max", int.class, int.class));

// 调用函数
String reversed = parser.parseExpression("#reverse('hello')").getValue(context, String.class);
Integer max = parser.parseExpression("#max(10, 20)").getValue(context, Integer.class);
```

Spring 内置函数（在特定场景可用）：

```java
// 在 @Cacheable 等注解中可用 #参数名 引用方法参数
@Cacheable(key = "#userId")
public User getUser(Long userId) { ... }
```

## Bean 引用

在 Spring 容器中，SpEL 可以用 `@beanName` 引用其他 Bean：

```java
// 引用 Bean 的属性
"@userService.defaultName"

// 调用 Bean 的方法
"@userService.getDefaultRole()"

// 引用 Bean 工厂
"&userService"   // 引用 FactoryBean 本身（带 & 前缀）
```

```java
@Component
public class OrderService {

    // @Value 中引用其他 Bean 的属性
    @Value("#{@configService.getDefaultTimeout()}")
    private int timeout;

    @Value("#{@configService.maxRetry}")
    private int maxRetry;
}
```

在 XML 配置中的用法：

```xml
<bean id="orderService" class="com.example.OrderService">
    <property name="timeout" value="#{@configService.defaultTimeout}" />
    <property name="userDao" value="#{@userDao}" />
</bean>
```

## 安全导航与集合操作

### 三元运算符

```java
"age > 18 ? '成年' : '未成年'"
```

### Elvis 运算符（?:）

三元运算符的简写，用于默认值：

```java
// 如果 name 为 null，则用 '匿名' 代替
"name ?: '匿名'"
```

```java
// 传统写法 vs Elvis
"name != null ? name : '匿名'"   // 传统三元
"name ?: '匿名'"                  // Elvis 简写
```

### 安全导航运算符（?.）

避免 NullPointerException，属性为 null 时返回 null 而不是抛异常：

```java
// 如果 address 为 null，整个表达式返回 null（不抛 NPE）
"address?.city"

// 链式安全导航
"user?.address?.city"
```

```java
// 没有安全导航时：address 为 null 会抛 NPE
// String city = parser.parseExpression("address.city").getValue(ctx, String.class);

// 有安全导航时：address 为 null 返回 null
String city = parser.parseExpression("address?.city").getValue(ctx, String.class);
```

### 集合投影（.![]）

对集合的每个元素应用表达式，返回新集合：

```java
// 语法：集合.![投影表达式]
"members.!name"                      // 提取所有成员的 name
"members.!['name']"                  // 等价写法
"members.![name.toUpperCase()]"      // 投影后转换
```

```java
List<String> names = parser.parseExpression("members.![name]")
    .getValue(context, List.class);
// 返回所有成员的 name 列表
```

### 集合选择（.?[]）

从集合中筛选满足条件的元素：

```java
// 语法：集合.?[选择表达式]
"members.?[age > 18]"                // 筛选年龄大于 18 的成员
"members.?[name == '张三']"           // 筛选名字为张三的
"map.?[value > 100]"                 // 筛选 Map 中 value 大于 100 的条目
```

```java
// 第一个匹配元素 .^[ ]
"members.^[age > 18]"   // 第一个满足条件的

// 最后一个匹配元素 .$[ ]
"members.$[age > 18]"   // 最后一个满足条件的
```

```java
// 组合使用：先选择再投影
List<String> adultNames = parser.parseExpression("members.?[age > 18].![name]")
    .getValue(context, List.class);
```

## 模板表达式

模板表达式用 `#{}` 包裹，可以在字符串中嵌入 SpEL 表达式：

```java
// 模板中混合字面量和表达式
parser.parseExpression("Hello #{name}", new TemplateParserContext())
    .getValue(context, String.class);
// 结果：Hello 张三

// 多个表达式
parser.parseExpression("#{firstName} #{lastName}", new TemplateParserContext())
    .getValue(context, String.class);
```

在 Spring 配置中的模板用法（`#{}` 是 Spring 的模板前缀，`${}` 是属性占位符）：

```properties
app.welcome=欢迎 #{systemProperties['user.name']}
```

```java
@Value("欢迎 #{systemProperties['user.name']}")
private String welcome;
```

## SpEL 编译优化

SpEL 表达式默认每次求值都重新解释执行。对于**高频调用**的表达式，可以开启编译模式，将表达式编译为 Java 字节码以提升性能。

```java
// 开启编译模式
SpelParserConfiguration config = new SpelParserConfiguration(
    SpelCompilerMode.IMMEDIATE,   // 立即编译
    SpelDemo.class.getClassLoader()
);
ExpressionParser parser = new SpelExpressionParser(config);
```

三种编译模式：

| 模式 | 说明 |
|------|------|
| OFF（默认） | 不编译，解释执行 |
| IMMEDIATE | 第一次求值后立即编译 |
| MIXED | 解释执行，多次调用后自动切换到编译模式 |

```java
// MIXED 模式示例
SpelParserConfiguration config = new SpelParserConfiguration(
    SpelCompilerMode.MIXED,
    SpelDemo.class.getClassLoader()
);
SpelExpressionParser parser = new SpelExpressionParser(config);

Expression exp = parser.parseExpression("user.age > 18 && user.vip");
// 前几次解释执行，频繁调用后自动编译
```

**注意**：编译模式有类型限制——表达式涉及的类型必须稳定。如果表达式每次操作不同类型的对象，编译会失败并回退到解释执行。大多数场景下默认的解释执行已足够，只有循环中的高频表达式才需要编译优化。

## Spring 中的 SpEL 应用

SpEL 在 Spring 生态中的典型应用场景：

### 1. @Value 注入

```java
// 属性占位符 ${...}
@Value("${app.name}")
private String appName;

// SpEL 表达式 #{...}
@Value("#{systemProperties['user.home']}")
private String userHome;

@Value("#{T(java.lang.Math).random()}")
private double random;

@Value("#{@configService.maxRetry}")
private int maxRetry;

// 混合：先占位符后 SpEL
@Value("#{${app.timeout} * 1000}")
private long timeoutMillis;
```

### 2. @Cacheable 的 key

```java
@Cacheable(value = "users", key = "#id")
public User getUserById(Long id) { ... }

@Cacheable(value = "users", key = "#user.id", condition = "#user.age > 18")
public User getUser(User user) { ... }

// 组合多个参数
@Cacheable(value = "users", key = "#type + ':' + #id")
public User getUser(String type, Long id) { ... }
```

### 3. Spring Security 权限表达式

```java
@PreAuthorize("hasRole('ADMIN')")
public void deleteUser(Long id) { ... }

@PreAuthorize("#userId == authentication.principal.id")
public User getProfile(Long userId) { ... }

@PreAuthorize("hasPermission(#order, 'write')")
public void updateOrder(Order order) { ... }
```

### 4. XML 配置

```xml
<bean id="userService" class="com.example.UserService">
    <property name="maxUsers" value="#{systemProperties['app.maxUsers'] ?: 100}" />
    <property name="defaultRole" value="#{@configService.defaultRole}" />
</bean>
```

## 应用场景实战

### 场景 1：动态规则引擎（用 SpEL 表达业务规则）

```java
@Service
public class RuleEngine {

    private final ExpressionParser parser = new SpelExpressionParser();

    // 规则存数据库，形如：age > 18 && score >= 60 && vip == true
    public boolean evaluate(String ruleExpression, Map<String, Object> variables) {
        StandardEvaluationContext context = new StandardEvaluationContext();
        variables.forEach(context::setVariable);

        Expression expression = parser.parseExpression(ruleExpression);
        return Boolean.TRUE.equals(expression.getValue(context, Boolean.class));
    }
}

// 使用
Map<String, Object> vars = Map.of("age", 25, "score", 80, "vip", true);
boolean pass = ruleEngine.evaluate("age > 18 && score >= 60 && vip == true", vars);
```

### 场景 2：配置中的条件表达式

```java
@Component
public class FeatureFlagService {

    @Value("#{${feature.enabled} && ${feature.beta}}")
    private boolean betaFeatureEnabled;

    @Value("#{'${env}' == 'prod' ? 'prod-config' : 'dev-config'}")
    private String configName;
}
```

### 场景 3：集合数据的灵活处理

```java
public class ReportService {

    private final ExpressionParser parser = new SpelExpressionParser();

    // 从订单列表提取金额并筛选
    public List<BigDecimal> getHighValueAmounts(List<Order> orders, BigDecimal threshold) {
        StandardEvaluationContext context = new StandardEvaluationContext();
        context.setVariable("orders", orders);
        context.setVariable("threshold", threshold);

        // 先筛选金额大于阈值的订单，再投影出金额
        String expression = "#orders.?[amount > #threshold].![amount]";
        return parser.parseExpression(expression).getValue(context, List.class);
    }
}
```

## 最佳实践与踩坑记录

### 最佳实践

1. **表达式字符串尽量简单**。复杂的 SpEL 难以调试和维护。如果逻辑超过一行，考虑提取为 Java 方法。

2. **优先用变量（#var）而不是硬编码**。通过 EvaluationContext 注入变量，表达式保持纯净。

3. **集合操作优先用投影/选择**。`.![]` 和 `.?[]` 比 Java 循环简洁，适合配置驱动的场景。

4. **注意 `${}` 和 `#{}` 的区别**：
   - `${}`：属性占位符，从 Environment 读取配置值
   - `#{}`：SpEL 表达式，运行时求值

```java
@Value("${app.name}")      // 占位符：读配置
@Value("#{1 + 2}")          // SpEL：求值 = 3
@Value("#{${app.timeout} * 1000}")  // 混合：先读配置，再 SpEL 计算
```

5. **动态规则用 SpEL 前先评估安全风险**。SpEL 能调用任意方法（含 `T(Runtime).getRuntime().exec()`），不要直接执行不可信来源的表达式字符串。Spring Security 提供 `SimpleEvaluationContext` 用于限制能力。

### 踩坑记录

**坑 1：字符串必须用单引号**

```java
parser.parseExpression("Hello World");       // 错误！解析失败
parser.parseExpression("'Hello World'");     // 正确：单引号
```

SpEL 字符串字面量用单引号 `'`，双引号在 SpEL 中是 Java 字符串的边界（源码中写表达式时）。

**坑 2：Elvis 运算符的优先级**

```java
// Elvis 优先级低于算术运算
"100 + discount ?: 0"    // 解析为 100 + (discount ?: 0)，不是 (100 + discount) ?: 0
```

不确定优先级时加括号。

**坑 3：安全导航只对属性访问生效**

```java
// 安全导航不能用于方法调用
"user?.getName()"    // 如果 user 为 null，仍会抛 NPE（方法调用不受 ?. 保护）
```

`?.` 只保护属性链（`user?.name`），不保护方法调用链。

**坑 4：集合投影/选择中的 #this**

```java
// 投影/选择中，当前元素用 #this 引用
"members.?[#this.age > 18]"   // #this 是当前成员
"members.![#this.name]"        // 等价于 members.![name]
```

省略时默认对当前元素操作，但显式用 `#this` 更清晰。

**坑 5：SpEL 表达式的性能**

```java
// 解释执行每次都重新解析语义，循环中高频调用开销大
for (int i = 0; i < 100000; i++) {
    expression.getValue(context);  // 慢
}

// 优化：开启编译模式，或缓存结果
```

高频循环中的 SpEL 求值应开启 `SpelCompilerMode.IMMEDIATE`，或避免在热路径使用 SpEL。

**坑 6：Map 取值时 key 的类型**

```java
// map 的 key 是 Integer 时
"map[1]"      // 可能解析为 int 1，匹配不上 Integer key
"map[T(Integer).valueOf(1)]"  // 显式构造 Integer key
```

Map 取值时，如果 key 类型不匹配（int vs Integer、String vs 枚举），会取不到值。
