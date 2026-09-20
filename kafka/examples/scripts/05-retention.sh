#!/usr/bin/env bash
# 05 消息过期删除实测：retention.ms + 静态清理间隔 + log-start-offset
#
# 用法：bash 05-retention.sh
# 输出：/opt/kafka-lab/out/05-retention.log
#
# 前置：单节点容器已按最新的 docker-compose-single.yml 重建
#       （其中 KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS=5000）

set -u
OUT=/opt/kafka-lab/out/05-retention.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

BIN=/opt/kafka/bin
KAFKA_IN="docker exec -i kafka-single $BIN"
KAFKA="docker exec kafka-single $BIN"
BS=localhost:9092

echo "############ 5.1 确认清理线程检查间隔已生效"
echo "\$ kafka-configs.sh --describe --entity-type brokers --entity-name 1 --all | grep retention.check"
$KAFKA/kafka-configs.sh --bootstrap-server $BS --describe --entity-type brokers --entity-name 1 --all 2>/dev/null \
  | grep -E 'log.retention.check.interval.ms'
echo

echo "############ 5.2 尝试动态修改清理间隔（预期被拒绝）"
echo "\$ kafka-configs.sh --alter --entity-type brokers --entity-name 1 --add-config log.retention.check.interval.ms=5000"
$KAFKA/kafka-configs.sh --bootstrap-server $BS --alter --entity-type brokers --entity-name 1 \
  --add-config log.retention.check.interval.ms=5000 2>&1 | grep -E 'InvalidRequestException|Cannot update' | head -2
echo

echo "############ 5.3 创建 retention.ms=10000（10 秒）的主题并写入 4 条"
$KAFKA/kafka-topics.sh --bootstrap-server $BS --delete --topic ttl-demo 2>/dev/null | head -1
sleep 3
$KAFKA/kafka-topics.sh --bootstrap-server $BS --create --topic ttl-demo --partitions 1 \
  --replication-factor 1 --config retention.ms=10000 --config segment.bytes=1048576 2>&1 | grep -v '^\[' | head -2
printf 'msg-1\nmsg-2\n' | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic ttl-demo 2>/dev/null
sleep 12
printf 'msg-3\nmsg-4\n' | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic ttl-demo 2>/dev/null
echo "  写入后位移情况（最新位移 -1）:"
$KAFKA/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list $BS --topic ttl-demo --time -1 2>/dev/null
echo "  最早可读位移（-2，此时应为 0）:"
$KAFKA/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list $BS --topic ttl-demo --time -2 2>/dev/null
echo

echo "############ 5.4 等待 40 秒，让清理线程按 retention.ms=10s 删除过期段"
sleep 40
echo "\$ kafka-run-class.sh kafka.tools.GetOffsetShell --time -1（最新位移不变）"
$KAFKA/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list $BS --topic ttl-demo --time -1 2>/dev/null
echo "\$ kafka-run-class.sh kafka.tools.GetOffsetShell --time -2（最早可读位移前进 = 老消息被物理删除）"
$KAFKA/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list $BS --topic ttl-demo --time -2 2>/dev/null
echo
echo "\$ 从最早读：只剩未被清理的消息"
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic ttl-demo --from-beginning \
  --timeout-ms 8000 2>/dev/null || echo "  （没有可读消息）"
echo
echo "\$ 分区目录（看 segment 文件是否被删除）"
docker exec kafka-single ls -la /var/lib/kafka/data/ttl-demo-0
echo

echo "############ 5.5 消息不丢的边界：如果消息被删除前没有任何消费者读过，它的位移是否还要提交？"
echo "  说明：位移（__consumer_offsets）与消息是两套生命周期。消息过期后位移仍然保留，"
echo "        消费组若把位移重置到已删除区间，broker 会用 log-start-offset 纠正到最早可用位置。"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group ttl-group 2>&1 | head -3
echo

echo "############ 05 脚本执行完成"
