---
title: BigDecimal 与 BigInteger
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, core-api, bigdecimal, biginteger, precision]
---

# BigDecimal 与 BigInteger

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [为什么不能用 float / double](#为什么不能用-float--double)
- [BigInteger 核心用法](#biginteger-核心用法)
- [BigDecimal 创建方式](#bigdecimal-创建方式)
- [BigDecimal 运算](#bigdecimal-运算)
- [舍入模式详解](#舍入模式详解)
- [精度与标度](#精度与标度)
- [格式化输出](#格式化输出)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

Java 的 `float` 和 `double` 基于 IEEE 754 二进制浮点数——能准确表示二进制的 1/2、1/4、1/8，但十进制的 0.1 是无限循环二进制小数，存储时产生误差。涉及钱的场景，`double` 绝对不能用。

`BigInteger` 和 `BigDecimal` 是 Java 数学的"精确武器"：
- **BigInteger**：任意大的整数，没有 `long` 的 19 位数上限
- **BigDecimal**：任意精度的十进制小数，金融计算标配

两个类都是不可变对象（`final class`），运算返回新对象。

## 为什么不能用 float / double

```java
// 经典翻车案例
double a = 0.1;
double b = 0.2;
System.out.println(a + b);           // 0.30000000000000004
System.out.println(0.1 + 0.2);       // 0.30000000000000004
System.out.println(1.0 - 0.9);       // 0.09999999999999998

// float 同理
float f = 0.1f + 0.2f;               // 0.3 显示没问题但内部有误差
```

这些误差来自 IEEE 754 的二进制表示。0.1 在二进制中是一个无限循环小数 `0.000110011...`，`double` 只能截取前 52 位尾数——剩下的被丢掉，误差因此产生。

涉及钱的场景这个误差是致命的：`0.1 + 0.2 = 0.30000000000000004` 已经被发现了，在循环累加中误差会放大。

## BigInteger 核心用法

```java
import java.math.BigInteger;

// 创建
BigInteger a = new BigInteger("12345678901234567890");
BigInteger b = BigInteger.valueOf(Long.MAX_VALUE);    // 9223372036854775807
BigInteger c = BigInteger.ONE;
BigInteger d = BigInteger.ZERO;
BigInteger e = BigInteger.TEN;

// 运算 —— 全部返回新对象
BigInteger sum = a.add(b);           // 加
BigInteger diff = a.subtract(b);     // 减
BigInteger prod = a.multiply(b);     // 乘
BigInteger quot = a.divide(b);       // 除（整除，舍去余数）
BigInteger rem = a.remainder(b);     // 取余
BigInteger[] divRem = a.divideAndRemainder(b);  // 商和余数一起取
BigInteger neg = a.negate();         // 取反
BigInteger abs = a.abs();            // 绝对值
BigInteger pow = a.pow(10);          // a 的 10 次方

// 比较
int cmp = a.compareTo(b);            // -1, 0, 1
boolean eq = a.equals(b);            // 值相等
BigInteger min = a.min(b);
BigInteger max = a.max(b);

// 位运算
BigInteger and = a.and(b);
BigInteger or  = a.or(b);
BigInteger xor = a.xor(b);
BigInteger not = a.not();
BigInteger shiftLeft  = a.shiftLeft(3);   // << 3
BigInteger shiftRight = a.shiftRight(3);  // >> 3
```

BigInteger 没有大小上限（受限于可用内存），适合大数运算、加密算法（RSA 密钥生成）、组合数学（阶乘 1000!）。

## BigDecimal 创建方式

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

// 推荐：用字符串构造，精确
BigDecimal d1 = new BigDecimal("0.1");
BigDecimal d2 = new BigDecimal("0.2");
System.out.println(d1.add(d2));      // 0.3 —— 精确！

// 绝对不要用 double 构造！传入的是近似值
BigDecimal danger = new BigDecimal(0.1);
System.out.println(danger);
// 输出：0.1000000000000000055511151231257827021181583404541015625

// 快捷方法
BigDecimal zero   = BigDecimal.ZERO;
BigDecimal one    = BigDecimal.ONE;
BigDecimal ten    = BigDecimal.TEN;
BigDecimal val    = BigDecimal.valueOf(0.1);  // 内部用了 Double.toString，比 new BigDecimal(0.1) 好
BigDecimal fromLong = BigDecimal.valueOf(100L);
```

构造方法对比：

| 方式 | 精确？ | 推荐？ |
|------|--------|--------|
| `new BigDecimal("0.1")` | 精确 | 推荐 |
| `BigDecimal.valueOf(0.1)` | 精确（内部调了 `Double.toString`） | 可用 |
| `new BigDecimal(0.1)` | 不精确 | 绝对不要用 |
| `BigDecimal.valueOf(100)` | 精确（long 直接转） | 推荐 |

## BigDecimal 运算

```java
BigDecimal price = new BigDecimal("19.99");
BigDecimal qty   = new BigDecimal("3");
BigDecimal tax   = new BigDecimal("0.13");

BigDecimal subtotal  = price.multiply(qty);                       // 乘法
BigDecimal taxAmount = subtotal.multiply(tax);                    // 再乘法
BigDecimal total     = subtotal.add(taxAmount);                   // 加法

// 除法必须指定舍入模式（否则无限小数时抛 ArithmeticException）
BigDecimal a = new BigDecimal("10");
BigDecimal b = new BigDecimal("3");

// a.divide(b);                           // ArithmeticException！10/3 无限小数
BigDecimal result = a.divide(b, 2, RoundingMode.HALF_UP);       // 3.33
BigDecimal result2 = a.divide(b, 4, RoundingMode.HALF_UP);      // 3.3333

// 取余
BigDecimal rem = a.remainder(b);          // 1

// 比较 —— 必须用 compareTo，不能用 equals！
BigDecimal x = new BigDecimal("2.0");
BigDecimal y = new BigDecimal("2.00");
System.out.println(x.equals(y));          // false —— equals 比较值和标度（scale）
System.out.println(x.compareTo(y) == 0);  // true  —— compareTo 只比较数值
```

## 舍入模式详解

Java 的 `RoundingMode` 来自 `java.math.RoundingMode` 枚举，共 8 种：

| 模式 | 行为 | 典型场景 |
|------|------|----------|
| `UP` | 远离零方向入 | 计算不省料的上限 |
| `DOWN` | 向零方向舍 | 取整不超出的下限 |
| `CEILING` | 向正无穷入 | 天花板取整 |
| `FLOOR` | 向负无穷舍 | 地板取整 |
| `HALF_UP` | 四舍五入 | **金融最常用** |
| `HALF_DOWN` | 五舍六入 | 统计用（减少偏倚） |
| `HALF_EVEN` | 银行家舍入（四舍六入五留偶） | 大量数据累加用 |
| `UNNECESSARY` | 不指定，精确除法失败就抛异常 | 除法的默认行为 |

```java
BigDecimal val = new BigDecimal("2.5");

// 注意负数下的方向
System.out.println(val.setScale(0, RoundingMode.HALF_UP));    // 3（2.5 → 入）
System.out.println(val.setScale(0, RoundingMode.HALF_DOWN));  // 2（2.5 → 舍）

BigDecimal neg = new BigDecimal("-2.5");
System.out.println(neg.setScale(0, RoundingMode.HALF_UP));    // -3（远离零）
System.out.println(neg.setScale(0, RoundingMode.HALF_DOWN));  // -2（向零）
```

HALF_EVEN（银行家舍入）在大量数据累加中更公平——遇到 .5 时看前一位奇偶，偶数则舍、奇数则入，避免整体上偏或下偏。

## 精度与标度

- **precision（精度）**：有效数字的总位数
- **scale（标度）**：小数点后的位数

```java
BigDecimal d = new BigDecimal("123.4500");

System.out.println(d.precision());   // 7（1234500 的总位数）
System.out.println(d.scale());       // 4（小数点后有 4 位）

// 调整 scale
BigDecimal trimmed = d.stripTrailingZeros();
System.out.println(trimmed);         // 123.45
System.out.println(trimmed.scale()); // 2

// 设定位数
BigDecimal rounded = d.setScale(2, RoundingMode.HALF_UP);
System.out.println(rounded);         // 123.45
```

## 格式化输出

```java
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.Locale;

BigDecimal amount = new BigDecimal("1234567.89");

// DecimalFormat —— 自定义格式
DecimalFormat df = new DecimalFormat("#,##0.00");
System.out.println(df.format(amount));    // 1,234,567.89

// NumberFormat —— 本地化货币格式
NumberFormat cny = NumberFormat.getCurrencyInstance(Locale.CHINA);
NumberFormat usd = NumberFormat.getCurrencyInstance(Locale.US);
System.out.println(cny.format(amount));   // ¥1,234,567.89
System.out.println(usd.format(amount));   // $1,234,567.89

// 千分位
NumberFormat nf = NumberFormat.getNumberInstance();
System.out.println(nf.format(amount));    // 1,234,567.89

// BigDecimal 转字符串
System.out.println(amount.toPlainString());  // 1234567.89（无科学计数法）
System.out.println(amount.toString());       // 1234567.89（可能用科学计数法）

// 科学计数法场景
BigDecimal tiny = new BigDecimal("0.000000001");
System.out.println(tiny.toString());         // 1E-9
System.out.println(tiny.toPlainString());    // 0.000000001
```

## 应用场景实战

### 场景一：订单金额计算

```java
public class OrderService {
    public OrderResult calculate(Order order) {
        BigDecimal total = BigDecimal.ZERO;

        for (OrderItem item : order.getItems()) {
            BigDecimal price  = new BigDecimal(item.getPrice());
            BigDecimal qty    = new BigDecimal(item.getQuantity());
            BigDecimal lineTotal = price.multiply(qty);
            total = total.add(lineTotal);
        }

        // 折扣（85 折）
        if (order.hasDiscount()) {
            BigDecimal discount = new BigDecimal("0.85");
            total = total.multiply(discount);
        }

        // 四舍五入到分
        total = total.setScale(2, RoundingMode.HALF_UP);

        return new OrderResult(order.getId(), total);
    }
}
```

### 场景二：分期付款计算

```java
public class InstallmentService {
    // 等额本息：每期金额 = 本金 × 月利率 × (1+月利率)^期数 / ((1+月利率)^期数 - 1)
    public BigDecimal monthlyPayment(BigDecimal principal, 
                                      BigDecimal annualRate, 
                                      int months) {
        BigDecimal monthlyRate = annualRate.divide(
            new BigDecimal("12"), 10, RoundingMode.HALF_UP);
        
        BigDecimal onePlusRate = BigDecimal.ONE.add(monthlyRate);
        BigDecimal pow = onePlusRate.pow(months);
        
        BigDecimal numerator = principal.multiply(monthlyRate).multiply(pow);
        BigDecimal denominator = pow.subtract(BigDecimal.ONE);
        
        return numerator.divide(denominator, 2, RoundingMode.HALF_UP);
    }
}
```

### 场景三：利率和汇率计算

```java
public class FinanceService {
    // 汇率转换
    public BigDecimal convertCurrency(BigDecimal amount, BigDecimal rate) {
        // 保留 4 位小数（汇率小数位多），最后再四舍五入到分
        BigDecimal converted = amount.multiply(rate);
        return converted.setScale(2, RoundingMode.HALF_UP);
    }

    // 年化利率
    public BigDecimal annualizedRate(BigDecimal totalReturn,
                                      BigDecimal principal,
                                      int days) {
        BigDecimal ratio = totalReturn.divide(principal, 10, RoundingMode.HALF_UP);
        BigDecimal dailyRate = ratio.subtract(BigDecimal.ONE);
        return dailyRate.multiply(new BigDecimal("365"))
                        .divide(new BigDecimal(days), 6, RoundingMode.HALF_UP);
    }
}
```

### 场景四：大数阶乘

```java
// 计算 1000! —— long 绝对装不下
public static BigInteger factorial(int n) {
    if (n < 0) throw new IllegalArgumentException("n 必须非负");
    BigInteger result = BigInteger.ONE;
    for (int i = 2; i <= n; i++) {
        result = result.multiply(BigInteger.valueOf(i));
    }
    return result;
}

BigInteger f1000 = factorial(1000);
System.out.println(f1000.toString().length());  // 2568 位！
```

## 最佳实践与踩坑记录

### 创建与比较

```java
// 正确：用字符串构造
BigDecimal price = new BigDecimal("19.99");

// 错误：用 double 构造，带入了二进制误差
BigDecimal wrong = new BigDecimal(19.99);
// 实际值：19.989999999999998436805981327779591083526611328125

// 正确：比较值
if (price.compareTo(BigDecimal.ZERO) > 0) { ... }

// 错误：equals 比较值 + scale
BigDecimal a = new BigDecimal("2.0");    // scale = 1
BigDecimal b = new BigDecimal("2.00");   // scale = 2
if (a.equals(b)) { ... }                 // false！
```

### 除法与舍入

```java
// 错误：不指定舍入模式
BigDecimal result = a.divide(b);            // 可能抛 ArithmeticException

// 正确：指定舍入模式（内置舍入方式，相当于先除再加舍入模式参数）
BigDecimal result = a.divide(b, 2, RoundingMode.HALF_UP);
```

### 性能注意

```java
// 简单整数计算不需要 BigDecimal
// 开销对比：int 运算 < 1ns，BigDecimal 运算 ~ 20ns+

// 如果只是存储金额但不需要大量运算，BigDecimal 没问题
// 如果每秒钟做上万次金额运算，考虑用 long 存"分"（整数），最后再转 BigDecimal
long priceInCents = 1999L;   // 19.99 元 = 1999 分
long total = priceInCents * quantity;
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| `ArithmeticException: Non-terminating decimal expansion` | 除法未指定舍入模式 | 用 `divide(divisor, scale, RoundingMode)` |
| `equals` 比较两个看似相等的 BigDecimal 返回 false | 标度不同（2.0 vs 2.00） | 用 `compareTo` 替换 `equals` |
| 构造的 BigDecimal 值不是想要的 | 用了 `new BigDecimal(double)` | 用 `new BigDecimal(String)` 或 `BigDecimal.valueOf` |
| 大量 BigDecimal 运算性能慢 | 每次运算创建新对象 | 考虑用 long 存最小单位（分、厘），或者只在最终显示时转 BigDecimal |

## 总结

- `float` / `double` 有二进制舍入误差，涉及金额绝对不要用
- `BigDecimal` 必须用字符串构造，`equals` 比较会带上标度——用 `compareTo`
- 除法必须指定舍入模式，金融场景用 `HALF_UP`（四舍五入）
- `BigInteger` 用于任意大的整数运算，密码学和组合数学常用
- 高频计算可以用 `long` 存"分"，避免 BigDecimal 的对象创建开销
