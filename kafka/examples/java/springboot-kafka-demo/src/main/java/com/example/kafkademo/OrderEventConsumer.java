package com.example.kafkademo;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

/**
 * 主业务消费者。
 *
 * 关注四件事：
 *   1. ConsumerRecord 里能拿到 partition / offset / timestamp，排查问题时很有用
 *   2. AckMode.MANUAL_IMMEDIATE + acknowledgment.acknowledge()：业务处理成功才提交位移
 *   3. 抛异常交给 ErrorHandler：重试 2 次后进死信，不会阻塞分区
 *   4. 幂等：同一 orderId 重复消费要能安全处理（这里用内存 Set 演示，生产应落库/Redis 去重）
 */
@Component
public class OrderEventConsumer {

    private static final Logger log = LoggerFactory.getLogger(OrderEventConsumer.class);

    private final ResultCollector collector;

    public OrderEventConsumer(ResultCollector collector) {
        this.collector = collector;
    }

    @KafkaListener(
            topics = "${app.topics.order-events}",
            groupId = "${spring.kafka.consumer.group-id}",
            containerFactory = "kafkaListenerContainerFactory")
    public void onOrderEvent(ConsumerRecord<String, OrderEvent> record,
                             Acknowledgment acknowledgment,
                             @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition) {
        OrderEvent event = record.value();
        log.info("收到事件 topic={} partition={} offset={} key={} value={}",
                record.topic(), partition, record.offset(), record.key(), event);

        if (event.isPoison()) {
            // 故意制造失败：走重试 -> 死信链路
            throw new IllegalStateException("模拟业务处理失败，orderId=" + event.getOrderId());
        }

        // 业务处理（此处只是打印）
        log.info("业务处理成功 orderId={} amount={}", event.getOrderId(), event.getAmount());

        // 处理成功后再提交位移
        acknowledgment.acknowledge();
        collector.recordHandled(event.getOrderId());
    }
}
