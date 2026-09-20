package com.example.kafkademo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

/**
 * 示例的驱动逻辑：发 8 条事件（其中 1 条故意失败）-> 等消费者处理完 -> 打印汇总 -> 退出。
 *
 * 真实业务里没有这个类：生产者通常是 HTTP 接口或定时任务触发，
 * 消费者是常驻进程，不会自己退出。
 */
@Component
public class DemoRunner implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(DemoRunner.class);

    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final ResultCollector collector;

    @Value("${app.topics.order-events}")
    private String orderEventsTopic;

    @Value("${app.auto-exit:false}")
    private boolean autoExit;

    private final ConfigurableApplicationContext context;

    public DemoRunner(KafkaTemplate<String, Object> kafkaTemplate,
                      ResultCollector collector,
                      ConfigurableApplicationContext context) {
        this.kafkaTemplate = kafkaTemplate;
        this.collector = collector;
        this.context = context;
    }

    @Override
    public void run(ApplicationArguments args) throws Exception {
        // 等一等，让消费组完成第一次分区分配
        Thread.sleep(3000);

        for (int i = 1; i <= 8; i++) {
            // 第 5 条标记为 poison，用来演示「重试 -> 死信」
            boolean poison = (i == 5);
            OrderEvent event = new OrderEvent("order-" + i, "user-" + (i % 3), i * 100L, poison);
            // 用 orderId 作 key：同一订单的事件保证落同一分区，分区内有序
            kafkaTemplate.send(orderEventsTopic, event.getOrderId(), event);
            log.info("已发送 {}", event);
        }
        // 不 flush 也不影响：KafkaTemplate 自身会攒批，进程存活期间会发出去

        boolean done = collector.await(40);
        log.info("等待结果: {}（true 表示 8 条都有归宿）", done);
        log.info("正常处理 {} 条: {}", collector.getHandled().size(), collector.getHandled());
        log.info("进入死信 {} 条: {}", collector.getDeadLettered().size(), collector.getDeadLettered());

        if (autoExit) {
            log.info("演示程序退出（app.auto-exit=true）");
            int code = SpringApplication.exit(context, new org.springframework.boot.ExitCodeGenerator() {
                @Override
                public int getExitCode() {
                    return 0;
                }
            });
            System.exit(code);
        }
    }
}
