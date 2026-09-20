package com.example.kafkademo;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.config.TopicBuilder;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.support.serializer.ErrorHandlingDeserializer;
import org.springframework.kafka.support.serializer.JsonDeserializer;
import org.springframework.kafka.support.serializer.JsonSerializer;
import org.springframework.util.backoff.FixedBackOff;

import java.util.HashMap;
import java.util.Map;

/**
 * Kafka 相关 Bean 的集中配置。
 *
 * 三个容易踩的点都写在这里：
 *   1. 手动提交（AckMode.MANUAL_IMMEDIATE）：处理完业务再提交位移
 *   2. ErrorHandlingDeserializer：反序列化失败不炸消费者线程，而是交给错误处理器
 *   3. DefaultErrorHandler + DeadLetterPublishingRecoverer：重试 N 次仍失败进死信主题
 */
@Configuration
public class KafkaConfig {

    @Value("${spring.kafka.bootstrap-servers}")
    private String bootstrapServers;

    @Value("${app.topics.order-events}")
    private String orderEventsTopic;

    // ---------------------------------------------------------------- 主题

    /**
     * 声明式建主题：应用启动时 KafkaAdmin 会检查并创建缺失的主题。
     *
     * 注意：主题名写错时 KafkaAdmin 会创建一个垃圾主题，所以生产环境通常
     * 关闭应用自动建主题（spring.kafka.admin.fail-fast + 运维统一建主题）。
     */
    @Bean
    public NewTopic orderEventsTopicBean() {
        return TopicBuilder.name(orderEventsTopic)
                .partitions(3)
                .replicas(1)
                // 保留 24 小时，演示环境不必堆积数据
                .config("retention.ms", "86400000")
                .build();
    }

    @Bean
    public NewTopic orderEventsDltTopicBean() {
        return TopicBuilder.name(orderEventsTopic + ".DLT")
                .partitions(3)
                .replicas(1)
                // 死信主题保留更久，给人工回放留时间
                .config("retention.ms", "604800000")
                .build();
    }

    // ---------------------------------------------------------------- 生产者

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> props = new HashMap<String, Object>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class.getName());
        // 不丢消息的最小集合
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        props.put(ProducerConfig.RETRIES_CONFIG, Integer.toString(Integer.MAX_VALUE));
        // 批量与延迟的折中
        props.put(ProducerConfig.LINGER_MS_CONFIG, "10");
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, Integer.toString(16 * 1024));
        return new DefaultKafkaProducerFactory<String, Object>(props);
    }

    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate(ProducerFactory<String, Object> producerFactory) {
        KafkaTemplate<String, Object> template = new KafkaTemplate<String, Object>(producerFactory);
        // 默认发送主题，省去每次 send 都传 topic
        template.setDefaultTopic(orderEventsTopic);
        return template;
    }

    // ---------------------------------------------------------------- 消费者

    @Bean
    public ConsumerFactory<String, OrderEvent> consumerFactory() {
        Map<String, Object> props = new HashMap<String, Object>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        // 用 ErrorHandlingDeserializer 包一层：坏消息交给错误处理器，而不是无限重试到卡死
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, ErrorHandlingDeserializer.class.getName());
        props.put(ErrorHandlingDeserializer.VALUE_DESERIALIZER_CLASS, JsonDeserializer.class.getName());
        props.put(JsonDeserializer.VALUE_DEFAULT_TYPE, OrderEvent.class.getName());
        props.put(JsonDeserializer.TRUSTED_PACKAGES, "com.example.kafkademo");
        // 关闭自动提交，交给容器按 AckMode 处理
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        return new DefaultKafkaConsumerFactory<String, OrderEvent>(props);
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, OrderEvent> kafkaListenerContainerFactory(
            ConsumerFactory<String, OrderEvent> consumerFactory,
            KafkaTemplate<String, Object> kafkaTemplate) {

        ConcurrentKafkaListenerContainerFactory<String, OrderEvent> factory =
                new ConcurrentKafkaListenerContainerFactory<String, OrderEvent>();
        factory.setConsumerFactory(consumerFactory);
        // 并发消费者数：不要超过主题分区数，多出来的线程会空闲
        factory.setConcurrency(2);
        // 手动提交：监听方法里 ack.acknowledge() 才会提交位移
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);

        // 重试 2 次、每次间隔 1 秒；仍失败则把消息投到死信主题
        FixedBackOff backOff = new FixedBackOff(1000L, 2L);
        DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(kafkaTemplate);
        DefaultErrorHandler errorHandler = new DefaultErrorHandler(recoverer, backOff);
        // 反序列化异常重试没有意义，直接进死信
        errorHandler.addNotRetryableExceptions(org.springframework.kafka.support.serializer.DeserializationException.class);
        factory.setCommonErrorHandler(errorHandler);
        return factory;
    }
}
