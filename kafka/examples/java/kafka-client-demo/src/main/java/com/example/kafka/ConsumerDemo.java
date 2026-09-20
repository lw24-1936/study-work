package com.example.kafka;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRebalanceListener;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.consumer.OffsetAndMetadata;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.serialization.StringDeserializer;

import java.time.Duration;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

/**
 * 消费者：消费组、手动提交位移、Rebalance 监听、按分区统计。
 *
 * 关键点：
 *   1. enable.auto.commit=false —— 处理成功后再提交，避免「提交了但业务没处理完」丢数据
 *   2. auto.offset.reset=earliest —— 新消费组第一次消费从最早开始（默认 latest 会跳过历史消息）
 *   3. onPartitionsRevoked 里提交位移 —— Rebalance 前把已处理到的位置提交掉，减少重复消费
 *
 * 运行：java -cp target/kafka-client-demo-1.0.0-jar-with-dependencies.jar \
 *          com.example.kafka.ConsumerDemo localhost:9092 demo-java 20
 */
public final class ConsumerDemo {

    private ConsumerDemo() {
    }

    public static void main(String[] args) throws Exception {
        String bootstrap = args.length > 0 ? args[0] : "localhost:9092";
        String topic = args.length > 1 ? args[1] : "demo-java";
        int maxRecords = args.length > 2 ? Integer.parseInt(args[2]) : 20;

        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        // 消费组：同组内分区互斥、组间广播；组名是消费进度的归属标识
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "demo-consumer-group");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        // 心跳与超时：session.timeout.ms 内没心跳会被踢出组触发 Rebalance
        props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, "10000");
        // 单次 poll 最多拉多少条，控制单批处理量与内存占用
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "5");

        KafkaConsumer<String, String> consumer = new KafkaConsumer<String, String>(props);
        final Map<Integer, Integer> perPartitionCount = new HashMap<Integer, Integer>();

        try {
            consumer.subscribe(Collections.singletonList(topic), new ConsumerRebalanceListener() {
                @Override
                public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
                    // Rebalance 前提交位移：不提交就会从上次提交点重复消费
                    System.out.println("  [rebalance] 即将失去分区: " + partitions + "，先同步提交位移");
                    consumer.commitSync();
                }

                @Override
                public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
                    System.out.println("  [rebalance] 分配到分区: " + partitions);
                }
            });

            int consumed = 0;
            long deadline = System.currentTimeMillis() + 20000L;
            while (consumed < maxRecords && System.currentTimeMillis() < deadline) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                for (ConsumerRecord<String, String> record : records) {
                    Integer old = perPartitionCount.get(record.partition());
                    perPartitionCount.put(record.partition(), old == null ? 1 : old + 1);
                    System.out.println(String.format("  partition=%d offset=%d key=%s value=%s",
                            record.partition(), record.offset(), record.key(), record.value()));
                    consumed++;
                }
                if (!records.isEmpty()) {
                    // 处理完再提交：提交的是「下一条要消费的位移」，即当前 offset + 1
                    consumer.commitSync();
                }
            }

            System.out.println("本次消费条数: " + consumed);
            System.out.println("各分区消费条数: " + perPartitionCount);
            for (TopicPartition partition : consumer.assignment()) {
                OffsetAndMetadata committed = consumer.committed(partition);
                System.out.println("  已提交位移 " + partition + " -> "
                        + (committed == null ? "无（尚未提交）" : committed.offset()));
            }
        } finally {
            // close 会触发一次 Rebalance，把分区让给组内其它消费者
            consumer.close();
        }
    }
}
