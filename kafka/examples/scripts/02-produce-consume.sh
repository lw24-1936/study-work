#!/usr/bin/env bash
# 02 生产与消费：命令行生产者/消费者、消费组与 Rebalance、位移重置、保留策略、segment 结构、性能测试
#
# 用法：bash 02-produce-consume.sh
# 输出：/opt/kafka-lab/out/02-produce-consume.log
#
# 注意：命令行消费统一加 --timeout-ms，否则没有新消息时会一直等下去（生产排障时最常见的误判点）

set -u
OUT=/opt/kafka-lab/out/02-produce-consume.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

BIN=/opt/kafka/bin
KAFKA_IN="docker exec -i kafka-single $BIN"       # 需要读 stdin 的场景
KAFKA="docker exec kafka-single $BIN"
BS=localhost:9092
TOPIC=demo-orders

echo "############ 2.0 准备一个干净的主题 $TOPIC（3 分区、1 副本）"
$KAFKA/kafka-topics.sh --bootstrap-server $BS --delete --topic $TOPIC 2>/dev/null | head -2
sleep 3
$KAFKA/kafka-topics.sh --bootstrap-server $BS --create --topic $TOPIC --partitions 3 --replication-factor 1 2>&1 | grep -v '^\[' | head -2
echo

echo "############ 2.1 命令行生产者：写入 8 条带 key 的消息（parse.key + key.separator）"
echo "\$ printf 'order-1:v1\n...' | kafka-console-producer.sh --topic $TOPIC --property parse.key=true --property key.separator=:"
printf 'order-1:v1\norder-2:v2\norder-3:v3\norder-1:v4\norder-2:v5\norder-3:v6\norder-1:v7\norder-2:v8\n' \
  | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic $TOPIC \
      --property parse.key=true --property key.separator=: 2>/dev/null
echo "写入完成"
echo

echo "############ 2.2 从最早位移消费全部消息（打印分区与 key）"
echo "\$ kafka-console-consumer.sh --topic $TOPIC --from-beginning --max-messages 8 --timeout-ms 20000"
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic $TOPIC --from-beginning \
  --max-messages 8 --timeout-ms 20000 --property print.partition=true --property print.key=true \
  --property key.separator=' -> ' 2>/dev/null
echo

echo "############ 2.3 同一 key 落同一分区（只过滤 order-2 看分区号）"
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic $TOPIC --from-beginning \
  --max-messages 8 --timeout-ms 20000 --property print.partition=true --property print.key=true \
  --property key.separator=' -> ' 2>/dev/null | grep order-2
echo

echo "############ 2.4 消费组：固定 group 消费 8 条"
echo "\$ kafka-console-consumer.sh --group order-cg --from-beginning --max-messages 8"
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic $TOPIC --group order-cg \
  --from-beginning --max-messages 8 --timeout-ms 20000 2>/dev/null
echo
echo "\$ kafka-consumer-groups.sh --describe --group order-cg（LAG 应为 0）"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group order-cg 2>/dev/null
echo
echo "\$ kafka-consumer-groups.sh --list"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --list 2>/dev/null
echo

echo "############ 2.5 组内两个消费者：观察分区分配与 Rebalance（--members）"
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic $TOPIC --group rebalance-cg \
  --from-beginning --timeout-ms 40000 > /tmp/rebalance-cg-1.out 2>/dev/null &
PID1=$!
sleep 5
echo "  第一个消费者已加入，成员列表:"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --members --group rebalance-cg 2>/dev/null
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic $TOPIC --group rebalance-cg \
  --from-beginning --timeout-ms 30000 > /tmp/rebalance-cg-2.out 2>/dev/null &
PID2=$!
sleep 8
echo "  第二个消费者加入后，成员列表（分区被重新分配）:"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --members --group rebalance-cg 2>/dev/null
echo
echo "\$ kafka-consumer-groups.sh --describe --group rebalance-cg（看每个消费者的分区与 LAG）"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group rebalance-cg 2>/dev/null
kill $PID1 $PID2 2>/dev/null
wait $PID1 $PID2 2>/dev/null
echo

echo "############ 2.6 位移重置：把 order-cg 的位移回退到最早"
echo "\$ kafka-consumer-groups.sh --reset-offsets --group order-cg --topic $TOPIC --to-earliest --execute"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --reset-offsets --group order-cg \
  --topic $TOPIC --to-earliest --execute 2>/dev/null
echo
echo "\$ kafka-consumer-groups.sh --describe --group order-cg（LAG 回到 8）"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group order-cg 2>/dev/null
echo

echo "############ 2.7 各分区最新位移（生产端视角）"
echo "\$ kafka-get-offsets.sh --topic $TOPIC"
$KAFKA/kafka-get-offsets.sh --bootstrap-server $BS --topic $TOPIC 2>/dev/null
echo

echo "############ 2.8 自动创建主题：向不存在的主题发消息"
echo "hello-auto" | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic auto-created-topic 2>/dev/null
echo "\$ kafka-topics.sh --list（auto-created-topic 已被自动创建）"
$KAFKA/kafka-topics.sh --bootstrap-server $BS --list 2>/dev/null | grep -v __
echo

echo "############ 2.9 保留策略实测：retention.ms=10000 + 清理线程间隔调到 5 秒"
echo "\$ kafka-configs.sh --alter --entity-type brokers --entity-name 1 --add-config log.retention.check.interval.ms=5000"
$KAFKA/kafka-configs.sh --bootstrap-server $BS --alter --entity-type brokers --entity-name 1 \
  --add-config log.retention.check.interval.ms=5000 2>&1 | grep -v '^\[' | head -3
echo
$KAFKA/kafka-topics.sh --bootstrap-server $BS --create --topic short-lived --partitions 1 \
  --replication-factor 1 --config retention.ms=10000 2>&1 | grep -v '^\[' | head -2
printf 'expire-me-1\nexpire-me-2\n' | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic short-lived 2>/dev/null
echo "  写入 2 条后立即读取:"
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic short-lived --from-beginning \
  --max-messages 2 --timeout-ms 8000 2>/dev/null
echo "  再写入 2 条 mark 消息，记录位移:"
printf 'mark-3\nmark-4\n' | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic short-lived 2>/dev/null
$KAFKA/kafka-get-offsets.sh --bootstrap-server $BS --topic short-lived 2>/dev/null
echo "  等待 45 秒让清理线程执行..."
sleep 45
echo "  \$ kafka-get-offsets.sh（最新位移）与 log-start-offset（最早可读位移）:"
$KAFKA/kafka-get-offsets.sh --bootstrap-server $BS --topic short-lived 2>/dev/null
echo "  log-start-offset（-2 表示最早）:"
$KAFKA/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list $BS --topic short-lived --time -2 2>/dev/null
echo "  从最早读：前两条应已被物理删除（只剩 mark-3/mark-4）:"
$KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic short-lived --from-beginning \
  --timeout-ms 8000 2>/dev/null
echo

echo "############ 2.10 分区目录与 segment 文件"
echo "\$ docker exec kafka-single ls -la /var/lib/kafka/data/$TOPIC-0"
docker exec kafka-single ls -la /var/lib/kafka/data/$TOPIC-0
echo

echo "############ 2.11 dump-log 查看 segment 内部结构"
SEG=$(docker exec kafka-single ls /var/lib/kafka/data/$TOPIC-0 | grep '\.log$' | head -1)
echo "\$ kafka-dump-log.sh --files /var/lib/kafka/data/$TOPIC-0/$SEG --print-data-log"
$KAFKA/kafka-dump-log.sh --files /var/lib/kafka/data/$TOPIC-0/$SEG --print-data-log 2>/dev/null | head -12
echo

echo "############ 2.12 性能测试：10 万条 1KB 消息（lz4 压缩 + 16KB 批量）"
$KAFKA/kafka-topics.sh --bootstrap-server $BS --create --topic perf-test --partitions 3 --replication-factor 1 2>&1 | grep -v '^\[' | head -2
echo "\$ kafka-producer-perf-test.sh --num-records 100000 --record-size 1024 --throughput -1"
$KAFKA/kafka-producer-perf-test.sh --topic perf-test --num-records 100000 --record-size 1024 \
  --throughput -1 --producer-props bootstrap.servers=$BS acks=1 batch.size=16384 linger.ms=5 \
  compression.type=lz4 2>/dev/null | tail -3
echo
echo "\$ kafka-consumer-perf-test.sh --messages 100000"
$KAFKA/kafka-consumer-perf-test.sh --bootstrap-server $BS --topic perf-test --messages 100000 \
  --group perf-cg --timeout 60000 2>/dev/null | tail -3
echo
echo "\$ kafka-log-dirs.sh --topic-list perf-test（10 万条 × 1KB = 约 100MB 原始数据，压缩后磁盘占用）"
$KAFKA/kafka-log-dirs.sh --bootstrap-server $BS --topic-list perf-test --describe 2>/dev/null | tail -2

echo "############ 02 脚本执行完成"
