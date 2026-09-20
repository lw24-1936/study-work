package com.example.kafka;

import org.apache.kafka.clients.producer.Callback;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.apache.kafka.common.serialization.StringSerializer;

import java.util.Properties;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;

/**
 * 生产者三件事：发送、带 key 发送（决定分区）、同步发送看返回的元数据。
 *
 * 这里的配置是「不丢消息」的最小集合：
 *   acks=all + enable.idempotence=true + retries=Integer.MAX_VALUE
 * 配合服务端 min.insync.replicas=2，可以在 3 副本集群上容忍 1 个 broker 宕机而不丢消息。
 *
 * 运行：java -cp target/kafka-client-demo-1.0.0-jar-with-dependencies.jar \
 *          com.example.kafka.ProducerDemo localhost:9092 demo-java
 */
public final class ProducerDemo {

    private ProducerDemo() {
    }

    public static void main(String[] args) throws Exception {
        String bootstrap = args.length > 0 ? args[0] : "localhost:9092";
        String topic = args.length > 1 ? args[1] : "demo-java";

        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

        // ---- 可靠性相关 ----
        // 所有同步副本都写入后才算成功；只写 leader 就返回（acks=1）时 leader 宕机会丢数据
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        // 幂等生产者：防止重试导致的重复写入（同一生产者会话内按 (pid, 序列号) 去重）
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        // 幂等模式下 retries 默认就是 MAX_VALUE，显式写出来便于阅读
        props.put(ProducerConfig.RETRIES_CONFIG, Integer.toString(Integer.MAX_VALUE));
        // 同一分区内最多 5 个未确认请求（幂等模式下上限就是 5）
        props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, "5");

        // ---- 性能相关 ----
        // 攒批：16KB 或 10ms 触发一次发送，吞吐显著提升，代价是最多 10ms 延迟
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, Integer.toString(16 * 1024));
        props.put(ProducerConfig.LINGER_MS_CONFIG, "10");
        // 压缩算法：lz4 是吞吐与 CPU 的常用折中
        props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "lz4");
        // 客户端 IO 缓冲，单位字节；不够时 send() 会阻塞 max.block.ms
        props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, Long.toString(32L * 1024 * 1024));

        KafkaProducer<String, String> producer = new KafkaProducer<String, String>(props);
        try {
            System.out.println("== 1. 同步发送（等 broker 确认，能拿到分区与位移）==");
            for (int i = 1; i <= 3; i++) {
                ProducerRecord<String, String> record =
                        new ProducerRecord<String, String>(topic, "order-" + i, "{\"orderId\":\"order-" + i + "\",\"amount\":" + (i * 100) + "}");
                RecordMetadata metadata = producer.send(record).get();
                System.out.println("  topic=" + metadata.topic()
                        + " partition=" + metadata.partition()
                        + " offset=" + metadata.offset()
                        + " key=" + record.key());
            }

            System.out.println("== 2. 相同 key 必落同一分区（分区器对 key 做 murmur2 哈希）==");
            for (int i = 0; i < 6; i++) {
                ProducerRecord<String, String> record =
                        new ProducerRecord<String, String>(topic, "user-42", "第 " + (i + 1) + " 次操作");
                RecordMetadata metadata = producer.send(record).get();
                System.out.println("  key=user-42 -> partition=" + metadata.partition() + " offset=" + metadata.offset());
            }

            System.out.println("== 3. 异步发送 + 回调（高吞吐场景）==");
            for (int i = 1; i <= 3; i++) {
                final String key = "async-" + i;
                producer.send(new ProducerRecord<String, String>(topic, key, "async payload " + i),
                        new Callback() {
                            @Override
                            public void onCompletion(RecordMetadata metadata, Exception exception) {
                                if (exception != null) {
                                    System.out.println("  " + key + " 发送失败: " + exception.getMessage());
                                } else {
                                    System.out.println("  " + key + " -> partition=" + metadata.partition() + " offset=" + metadata.offset());
                                }
                            }
                        });
            }
            // flush 会阻塞直到缓冲区全部发送完成；进程退出前必须调用，否则缓冲里的消息会丢
            producer.flush();

            System.out.println("== 4. 显式指定分区（业务自己做分区策略时）==");
            ProducerRecord<String, String> pinned = new ProducerRecord<String, String>(topic, 2, "pinned-key", "指定写入分区 2");
            RecordMetadata metadata = producer.send(pinned).get();
            System.out.println("  partition=" + metadata.partition() + " offset=" + metadata.offset());

            System.out.println("== 5. 用非法主题名发送：观察异常类型 ==");
            try {
                Future<RecordMetadata> future = producer.send(new ProducerRecord<String, String>("bad topic name", "k", "v"));
                future.get();
            } catch (ExecutionException e) {
                System.out.println("  异常: " + e.getCause().getClass().getSimpleName() + " - " + firstLine(e.getCause().getMessage()));
            }
        } finally {
            producer.close();
        }
    }

    private static String firstLine(String text) {
        if (text == null) {
            return "null";
        }
        int index = text.indexOf('\n');
        return index < 0 ? text : text.substring(0, index);
    }
}
