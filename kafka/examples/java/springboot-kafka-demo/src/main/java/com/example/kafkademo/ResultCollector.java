package com.example.kafkademo;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * 汇总消费结果，供命令行 runner 判断何时退出。
 *
 * 示例程序用它是为了「跑完就退出」；真实业务里这个位置通常是数据库或下游服务。
 */
@Component
public class ResultCollector {

    private final List<String> handled = Collections.synchronizedList(new ArrayList<String>());
    private final List<String> deadLettered = Collections.synchronizedList(new ArrayList<String>());
    private final CountDownLatch latch = new CountDownLatch(8);

    public void recordHandled(String orderId) {
        handled.add(orderId);
        latch.countDown();
    }

    public void recordDeadLetter(String orderId) {
        deadLettered.add(orderId);
        latch.countDown();
    }

    public boolean await(long seconds) throws InterruptedException {
        return latch.await(seconds, TimeUnit.SECONDS);
    }

    public List<String> getHandled() {
        return handled;
    }

    public List<String> getDeadLettered() {
        return deadLettered;
    }
}
