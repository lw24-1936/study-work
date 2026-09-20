package com.example.kafkademo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Spring Boot 集成 Kafka 的完整示例。
 *
 * 启动前先确保：
 *   1. Kafka 已启动（docker compose -f docker-compose-single.yml up -d）
 *   2. 主题 order-events、order-events.DLT 已存在（见 application.yml 与启动脚本）
 *
 * 运行：mvn spring-boot:run
 *      或 java -jar target/springboot-kafka-demo-1.0.0.jar
 */
@SpringBootApplication
@EnableKafka
public class KafkaDemoApplication {

    public static void main(String[] args) {
        SpringApplication.run(KafkaDemoApplication.class, args);
    }
}
