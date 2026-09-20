package com.example.kafka;

import org.apache.kafka.clients.admin.Admin;
import org.apache.kafka.clients.admin.AdminClientConfig;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.admin.TopicDescription;
import org.apache.kafka.common.TopicPartitionInfo;

import java.util.Collections;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.ExecutionException;

/**
 * 用 AdminClient 管理主题：创建、列举、查看分区与副本分布。
 *
 * 运行：java -cp target/kafka-client-demo-1.0.0-jar-with-dependencies.jar \
 *          com.example.kafka.TopicAdmin localhost:9092 create demo-admin
 */
public final class TopicAdmin {

    private TopicAdmin() {
    }

    public static void main(String[] args) throws Exception {
        String bootstrap = args.length > 0 ? args[0] : "localhost:9092";
        String action = args.length > 1 ? args[1] : "describe";
        String topic = args.length > 2 ? args[2] : "demo-admin";

        Properties props = new Properties();
        // 只需要一个能连通的 broker 地址即可，客户端会自己发现整个集群
        props.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrap);
        // AdminClient 操作要设置超时，否则集群不可达时线程会一直挂着
        props.put(AdminClientConfig.REQUEST_TIMEOUT_MS_CONFIG, "5000");
        props.put(AdminClientConfig.DEFAULT_API_TIMEOUT_MS_CONFIG, "10000");

        Admin admin = Admin.create(props);
        try {
            if ("create".equals(action)) {
                // 3 分区、1 副本（单节点集群副本只能为 1）
                NewTopic newTopic = new NewTopic(topic, 3, (short) 1);
                // 主题级配置：保留 1 小时、清理策略为 delete
                newTopic.configs(Collections.singletonMap("retention.ms", "3600000"));
                admin.createTopics(Collections.singletonList(newTopic)).all().get();
                System.out.println("已创建主题: " + topic);
            } else if ("delete".equals(action)) {
                admin.deleteTopics(Collections.singletonList(topic)).all().get();
                System.out.println("已删除主题: " + topic);
            } else if ("list".equals(action)) {
                Set<String> names = admin.listTopics().names().get();
                System.out.println("主题总数: " + names.size());
                for (String name : names) {
                    System.out.println("  " + name);
                }
            } else {
                describe(admin, topic);
            }
        } catch (ExecutionException e) {
            // AdminClient 把服务端返回的错误包装成 ExecutionException，取 cause 才是真实原因
            System.out.println("操作失败: " + e.getCause().getClass().getSimpleName() + " - " + e.getCause().getMessage());
        } finally {
            admin.close();
        }
    }

    private static void describe(Admin admin, String topic) throws Exception {
        TopicDescription description = admin.describeTopics(Collections.singletonList(topic))
                .allTopicNames().get().get(topic);
        System.out.println("主题: " + description.name() + "  内部主题: " + description.isInternal());
        List<TopicPartitionInfo> partitions = description.partitions();
        for (TopicPartitionInfo partition : partitions) {
            StringBuilder replicas = new StringBuilder();
            for (org.apache.kafka.common.Node node : partition.replicas()) {
                if (replicas.length() > 0) {
                    replicas.append(", ");
                }
                replicas.append(node.id());
            }
            StringBuilder isr = new StringBuilder();
            for (org.apache.kafka.common.Node node : partition.isr()) {
                if (isr.length() > 0) {
                    isr.append(", ");
                }
                isr.append(node.id());
            }
            System.out.println("  分区 " + partition.partition()
                    + "  leader=" + partition.leader().id()
                    + "  副本=[" + replicas + "]"
                    + "  ISR=[" + isr + "]");
        }
        System.out.println("分区数: " + partitions.size());
    }
}
