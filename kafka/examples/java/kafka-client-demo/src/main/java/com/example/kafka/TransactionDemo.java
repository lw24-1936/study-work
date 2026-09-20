package com.example.kafka;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;

import java.time.Duration;
import java.util.Collections;
import java.util.Properties;

/**
 * 事务生产者：consume-transform-produce 的原子写。
 *
 * 场景：从源主题读一条消息，处理后写入目标主题，同时提交源主题位移——
 *      这三步要在同一个事务里，否则「写成功但位移没提交」会重复，「位移提交了但写失败」会丢。
 *
 * 关键配置：
 *   transactional.id    事务 ID，同一 ID 的僵尸生产者会被 fencing（新实例让旧实例失效）
 *   read_committed      消费者只读已提交的消息；默认 read_uncommitted 会读到回滚的消息
 *
 * 运行：java -cp target/kafka-client-demo-1.0.0-jar-with-dependencies.jar \
 *          com.example.kafka.TransactionDemo localhost:9092 txn-source txn-target
 */
public final class TransactionDemo {

    private TransactionDemo() {
    }

    public static void main(String[] args) throws Exception {
        String bootstrap = args.length > 0 ? args[0] : "localhost:9092";
        String sourceTopic = args.length > 1 ? args[1] : "txn-source";
        String targetTopic = args.length > 2 ? args[2] : "txn-target";

        // ---- 1. 先造 3 条源消息 ----
        Properties producerProps = new Properties();
        producerProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);
        producerProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        producerProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        producerProps.put(ProducerConfig.ACKS_CONFIG, "all");
        producerProps.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        // 事务要求 transactional.id；同一个 ID 只能有一个活跃生产者
        producerProps.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "txn-demo-1");
        // 事务超时：超过后 broker 会中止这个事务，防止悬挂
        producerProps.put(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, "60000");

        KafkaProducer<String, String> producer = new KafkaProducer<String, String>(producerProps);
        producer.initTransactions();
        try {
            producer.beginTransaction();
            for (int i = 1; i <= 3; i++) {
                producer.send(new ProducerRecord<String, String>(sourceTopic, "tx-" + i, "源消息 " + i));
            }
            producer.commitTransaction();
            System.out.println("已写入 3 条源消息到 " + sourceTopic);
        } finally {
            producer.close();
        }

        // ---- 2. 事务化地「读源 -> 写目标 + 提交位移」----
        Properties consumerProps = new Properties();
        consumerProps.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);
        consumerProps.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        consumerProps.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        consumerProps.put(ConsumerConfig.GROUP_ID_CONFIG, "txn-demo-group");
        consumerProps.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
        consumerProps.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        // 只读已提交的消息
        consumerProps.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed");

        KafkaConsumer<String, String> consumer = new KafkaConsumer<String, String>(consumerProps);
        consumer.subscribe(Collections.singletonList(sourceTopic));

        int processed = 0;
        try {
            producer = new KafkaProducer<String, String>(producerProps);
            producer.initTransactions();
            long deadline = System.currentTimeMillis() + 20000L;

            while (processed < 3 && System.currentTimeMillis() < deadline) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                if (records.isEmpty()) {
                    continue;
                }
                producer.beginTransaction();
                try {
                    for (ConsumerRecord<String, String> record : records) {
                        String transformed = "已处理: " + record.value();
                        producer.send(new ProducerRecord<String, String>(targetTopic, record.key(), transformed));
                        processed++;
                    }
                    // 把「消费位移」也放进同一个事务里提交
                    // 用 consumer.groupMetadata() 传消费组元数据（3.0 起的新签名，
                    // 旧的 sendOffsetsToTransaction(offsets, String groupId) 已废弃并在 4.0 移除）
                    producer.sendOffsetsToTransaction(currentOffsets(consumer), consumer.groupMetadata());
                    producer.commitTransaction();
                    System.out.println("事务提交成功，本批处理 " + records.count() + " 条");
                } catch (Exception e) {
                    // 任何一步失败都回滚：目标和位移一起撤销，恢复到「没处理过」的状态
                    producer.abortTransaction();
                    System.out.println("事务回滚: " + e.getMessage());
                    throw e;
                }
            }
        } finally {
            consumer.close();
            producer.close();
        }

        System.out.println("共处理 " + processed + " 条，写入目标主题 " + targetTopic);
    }

    private static java.util.Map<org.apache.kafka.common.TopicPartition, org.apache.kafka.clients.consumer.OffsetAndMetadata>
    currentOffsets(KafkaConsumer<String, String> consumer) {
        java.util.Map<org.apache.kafka.common.TopicPartition, org.apache.kafka.clients.consumer.OffsetAndMetadata> offsets =
                new java.util.HashMap<org.apache.kafka.common.TopicPartition, org.apache.kafka.clients.consumer.OffsetAndMetadata>();
        for (org.apache.kafka.common.TopicPartition partition : consumer.assignment()) {
            offsets.put(partition, new org.apache.kafka.clients.consumer.OffsetAndMetadata(consumer.position(partition)));
        }
        return offsets;
    }
}
