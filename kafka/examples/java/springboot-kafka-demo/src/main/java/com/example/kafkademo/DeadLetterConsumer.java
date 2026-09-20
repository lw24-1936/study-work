package com.example.kafkademo;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

/**
 * 死信主题消费者。
 *
 * 重要提醒：DeadLetterPublishingRecoverer 只是把失败消息搬到 order-events.DLT，
 * 如果没有人消费这个主题，消息就在那里躺着——「进了死信」不等于「处理完了」。
 * 生产环境需要：DLT 消费程序 + 告警 + 人工/自动回放机制。
 */
@Component
public class DeadLetterConsumer {

    private static final Logger log = LoggerFactory.getLogger(DeadLetterConsumer.class);

    private final ResultCollector collector;

    public DeadLetterConsumer(ResultCollector collector) {
        this.collector = collector;
    }

    @KafkaListener(
            topics = "${app.topics.order-events}.DLT",
            groupId = "${spring.kafka.consumer.group-id}-dlt",
            containerFactory = "kafkaListenerContainerFactory")
    public void onDeadLetter(ConsumerRecord<String, OrderEvent> record, Acknowledgment acknowledgment) {
        // 头里带着原始主题、分区、位移与失败原因，是回放的关键信息
        log.warn("死信消息 key={} value={} headers={}", record.key(), record.value(), record.headers());
        acknowledgment.acknowledge();
        if (record.value() != null) {
            collector.recordDeadLetter(record.value().getOrderId());
        }
    }
}
