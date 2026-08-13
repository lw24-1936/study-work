---
title: CompletableFuture
created: 2026-08-12
updated: 2026-08-12
type: concept
tags: [java, concurrency, completablefuture, async, composition]
---

# CompletableFuture

整理日期：2026-08-12

## 目录

- [概述](#概述)
- [创建 CompletableFuture](#创建-completablefuture)
- [thenApply / thenAccept / thenRun](#thenapply--thenaccept--thenrun)
- [thenCompose 与 thenCombine](#thencompose-与-thencombine)
- [allOf 与 anyOf](#allof-与-anyof)
- [异常处理](#异常处理)
- [异步编排实战](#异步编排实战)
- [应用场景实战](#应用场景实战)
- [最佳实践与踩坑记录](#最佳实践与踩坑记录)

## 概述

`CompletableFuture` 是 JDK 8 引入的异步编程利器——结合了 Future 的异步能力和函数式编程的组合能力。它可以：

- 链式编排异步任务（thenApply → thenAccept → thenRun）
- 组合多个异步结果（thenCombine、allOf）
- 异常处理（exceptionally、handle、whenComplete）
- 自定义线程池执行

和 Future 的对比：

| 能力 | Future | CompletableFuture |
|------|--------|-------------------|
| 获取结果 | 阻塞 get() | 阻塞 get() 或回调 |
| 任务编排 | 不支持 | 链式 thenXxx |
| 组合多个任务 | 不支持 | allOf / anyOf |
| 异常处理 | try-catch 包裹 call() | exceptionally / handle |
| 手动完成 | 不支持 | complete() / completeExceptionally() |

## 创建 CompletableFuture

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;

// 1. supplyAsync —— 有返回值
CompletableFuture<String> cf1 = CompletableFuture.supplyAsync(() -> {
    // 在 ForkJoinPool.commonPool() 中执行
    return "结果";
});

// 2. runAsync —— 无返回值
CompletableFuture<Void> cf2 = CompletableFuture.runAsync(() -> {
    System.out.println("异步执行");
});

// 3. 指定线程池
Executor pool = Executors.newFixedThreadPool(4);
CompletableFuture<String> cf3 = CompletableFuture.supplyAsync(() -> "结果", pool);

// 4. 手动完成
CompletableFuture<String> cf4 = new CompletableFuture<>();
cf4.complete("手动设置");
// cf4.completeExceptionally(new RuntimeException("失败"));  // 异常完成

// 5. 已完成的结果
CompletableFuture<String> cf5 = CompletableFuture.completedFuture("直接完成");
```

## thenApply / thenAccept / thenRun

```java
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> "Hello");

// thenApply —— 转换结果（有入有出）
CompletableFuture<Integer> length = future.thenApply(String::length);

// thenAccept —— 消费结果（有入无出）
CompletableFuture<Void> print = future.thenAccept(System.out::println);

// thenRun —— 不依赖结果（无入无出）
CompletableFuture<Void> done = future.thenRun(() -> System.out.println("完成"));

// 异步版本（在独立线程执行）
future.thenApplyAsync(s -> s.toUpperCase());  // 异步线程池中执行
future.thenAcceptAsync(System.out::println, executor);  // 指定线程池
```

## thenCompose 与 thenCombine

```java
// thenCompose —— 串行组合（第二个依赖第一个的结果）
// 相当于 flatMap
CompletableFuture<String> result = getUser(1L)
    .thenCompose(user -> getOrders(user.getId()));  // 用 user 查订单

// thenCombine —— 并行组合（两个独立任务的结果）
CompletableFuture<String> userFuture = getUser(1L);
CompletableFuture<String> orderFuture = getOrders(1L);

CompletableFuture<String> combined = userFuture.thenCombine(
    orderFuture,
    (user, orders) -> user + " 的订单: " + orders
);

// 方法签名速查：
// thenCompose:  T → CompletableFuture<U>   → CompletableFuture<U>
// thenCombine:  (T, U) → V                  → CompletableFuture<V>
```

`thenCompose` vs `thenApply`：

```java
// thenApply: 返回普通值 → 自动包装
CompletableFuture<String> s = future.thenApply(x -> x + "!");

// thenCompose: 返回 CompletableFuture → 需要展平
CompletableFuture<String> s = future.thenCompose(x -> anotherAsyncMethod(x));
// 如果这里用 thenApply(x -> anotherAsyncMethod(x))，会得到 CompletableFuture<CompletableFuture<String>>
```

## allOf 与 anyOf

```java
CompletableFuture<String> f1 = CompletableFuture.supplyAsync(() -> "任务1");
CompletableFuture<String> f2 = CompletableFuture.supplyAsync(() -> "任务2");
CompletableFuture<String> f3 = CompletableFuture.supplyAsync(() -> "任务3");

// allOf —— 等全部完成
CompletableFuture<Void> all = CompletableFuture.allOf(f1, f2, f3);
all.join();  // 阻塞等待全部完成

// anyOf —— 任意一个完成即返回
CompletableFuture<Object> any = CompletableFuture.anyOf(f1, f2, f3);
Object firstResult = any.get();  // 返回第一个完成的结果

// allOf 后获取所有结果
List<String> results = Stream.of(f1, f2, f3)
    .map(CompletableFuture::join)  // join 不抛 checked exception
    .collect(Collectors.toList());
```

## 异常处理

```java
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    if (Math.random() > 0.5) throw new RuntimeException("随机失败");
    return "成功";
});

// exceptionally —— 只处理异常
CompletableFuture<String> recovered = future
    .exceptionally(ex -> "降级默认值");

// handle —— 处理成功和失败（相当于 catch + finally）
CompletableFuture<String> handled = future
    .handle((result, ex) -> {
        if (ex != null) {
            log.error("任务失败", ex);
            return "降级值";
        }
        return result.toUpperCase();
    });

// whenComplete —— 查看结果但不修改（相当于 finally）
CompletableFuture<String> logged = future
    .whenComplete((result, ex) -> {
        if (ex != null) log.error("失败: {}", ex.getMessage());
        else log.info("成功: {}", result);
    });
```

异常传播规则：
- 没有指定 `exceptionally`/`handle` 时，异常沿链传播
- `exceptionally` 能"修复"异常链，返回正常值
- `handle` 的 `result` 在异常时为 null

## 异步编排实战

```java
// 电商下单流程的异步编排
public CompletableFuture<OrderResult> placeOrder(OrderRequest request) {
    return CompletableFuture
        // 1. 并行查询用户和库存
        .supplyAsync(() -> userService.getUser(request.getUserId()))
        .thenCombine(
            CompletableFuture.supplyAsync(() -> inventoryService.check(request.getSkuId())),
            (user, inventory) -> {
                // 2. 校验
                if (!inventory.isAvailable()) throw new BusinessException("库存不足");
                return user;
            })
        // 3. 创建订单
        .thenCompose(user -> CompletableFuture.supplyAsync(
            () -> orderService.create(user, request)))
        // 4. 异步扣减库存（不阻塞返回）
        .whenComplete((order, ex) -> {
            if (ex == null) {
                inventoryService.deductAsync(request.getSkuId());
            }
        })
        .exceptionally(ex -> {
            log.error("下单失败", ex);
            return OrderResult.failure(ex.getMessage());
        });
}
```

## 应用场景实战

### 场景一：多数据源聚合

```java
public ProductDetail getProductDetail(Long productId) {
    // 并行查询三个数据源
    CompletableFuture<Product> productFuture = 
        CompletableFuture.supplyAsync(() -> productRepo.findById(productId));
    CompletableFuture<List<Review>> reviewsFuture = 
        CompletableFuture.supplyAsync(() -> reviewRepo.findByProductId(productId));
    CompletableFuture<Price> priceFuture = 
        CompletableFuture.supplyAsync(() -> pricingService.getPrice(productId));

    // 等所有完成
    CompletableFuture.allOf(productFuture, reviewsFuture, priceFuture).join();

    return new ProductDetail(
        productFuture.join(),
        reviewsFuture.join(),
        priceFuture.join()
    );
}
```

### 场景二：超时降级

```java
public String queryWithTimeout(String param) {
    CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
        return remoteService.query(param);  // 可能很慢
    });

    try {
        return future.get(3, TimeUnit.SECONDS);
    } catch (TimeoutException e) {
        return "超时降级值";  // 超过 3 秒返回降级值
    }
}

// JDK 9+ 直接支持超时
future.completeOnTimeout("超时值", 3, TimeUnit.SECONDS);
future.orTimeout(3, TimeUnit.SECONDS);  // 超时抛 TimeoutException
```

### 场景三：批量异步任务 + 结果聚合

```java
public Map<Long, User> batchQuery(List<Long> userIds) {
    List<CompletableFuture<Map.Entry<Long, User>>> futures = userIds.stream()
        .map(id -> CompletableFuture.supplyAsync(
                () -> Map.entry(id, userRepo.findById(id)),
                executor
        ))
        .collect(Collectors.toList());

    return futures.stream()
        .map(CompletableFuture::join)
        .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
}
```

## 最佳实践与踩坑记录

### 方法选择速查

```
任务链：
  转换结果           → thenApply(fn)
  消费结果           → thenAccept(consumer)
  最终操作           → thenRun(runnable)
  异步回调返回CF     → thenCompose(fn)    （展平 CF<CF<T>>）

任务组合：
  两个独立组合       → thenCombine(other, fn)
  等所有完成         → allOf(futures...)
  等任一完成         → anyOf(futures...)

异常：
  异常恢复           → exceptionally(fn)
  异常+成功都处理     → handle(fn)
  观察不修改          → whenComplete(fn)
```

### 常见问题表

| 问题 | 原因 | 修复 |
|------|------|------|
| 默认线程池线程不够 | `supplyAsync` 用 `ForkJoinPool.commonPool()`，默认核数-1 | 传入自定义线程池 |
| `thenApply` 返回 `CF<CF<T>>` | 回调方法返回了 CompletableFuture | 换 `thenCompose` |
| `join()` 抛出 CompletionException | 内部异常被包装 | 用 `getCause()` 获取根因 |
| 异步任务"丢失" | 没持有 CompletableFuture 引用，GC 回收 | 保存引用或 join 等待 |

### 线程池建议

```
计算密集型异步任务 → ForkJoinPool.commonPool()（默认）
IO 密集型异步任务 → 自定义线程池（必须！）
  Executor pool = Executors.newFixedThreadPool(10);
  CompletableFuture.supplyAsync(() -> ioCall(), pool);
```

## 总结

- `CompletableFuture` = Future + 函数式异步编排
- `thenApply` 转换结果，`thenCompose` 串行异步，`thenCombine` 并行合并
- `allOf` 等全部完成，`anyOf` 等任意一个完成
- `exceptionally` 恢复异常，`handle` 处理成功+失败
- 默认使用 `ForkJoinPool.commonPool()`，IO 密集型务必传自定义线程池
- 链式 API 的核心：每个 `thenXxx` 返回新的 CompletableFuture，可以继续链下去
