#!/usr/bin/env bash
# 06 应用场景：削峰与积压追平（日志采集链路的真实演示）
#
# 演示流程：
#   6.2 业务高峰写入 10000 条日志（生产者只关心写成功，不管下游快慢）
#   6.3 各分区位移分布（按服务名做 key）
#   6.4 消费者在线：消费完初始数据，LAG 归零
#   6.5 消费者离线：期间再写入 10000 条，LAG 增长到 10000（真实积压）
#   6.6 消费者恢复：并行消费，LAG 逐步归零
#
# 用法：bash 06-scenario-backlog.sh

set -u
OUT=/opt/kafka-lab/out/06-scenario.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

BIN=/opt/kafka/bin
KAFKA_IN="docker exec -i kafka-single $BIN"
KAFKA="docker exec kafka-single $BIN"
BS=localhost:9092
TOPIC=app-log
GROUP=log-consumer

gen_logs() {
  local from=$1 to=$2
  seq "$from" "$to" | awk '{n=($1-1)%4; name=(n==0)?"order-service":(n==1)?"pay-service":(n==2)?"user-service":"cart-service"; print name":{\"seq\":"$1",\"level\":\"INFO\",\"msg\":\"request handled\"}"}'
}

total_lag() {
  $KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group $GROUP 2>/dev/null \
    | awk '/^[a-z]/ && $6 ~ /^[0-9]+$/ {sum += $6} END {print sum+0}'
}

echo "############ 6.1 准备主题：日志按服务名做 key，6 分区"
$KAFKA/kafka-topics.sh --bootstrap-server $BS --delete --topic $TOPIC 2>/dev/null | head -1
sleep 3
$KAFKA/kafka-topics.sh --bootstrap-server $BS --create --topic $TOPIC --partitions 6 \
  --replication-factor 1 --config retention.ms=86400000 2>&1 | grep -v '^\[' | head -2
echo

echo "############ 6.2 模拟高峰写入：10000 条日志"
echo "\$ seq 1 10000 | awk '{...服务名作为 key...}' | kafka-console-producer.sh --property parse.key=true"
gen_logs 1 10000 \
  | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic $TOPIC \
      --property parse.key=true --property key.separator=: 2>/dev/null
echo "写入完成"
echo

echo "############ 6.3 各分区位移（同 key 落同一分区，服务名只用到 4 个分区）"
echo "\$ kafka-get-offsets.sh --topic $TOPIC"
$KAFKA/kafka-get-offsets.sh --bootstrap-server $BS --topic $TOPIC 2>/dev/null
echo

echo "############ 6.4 消费者在线：6 个并行消费者（对应 6 个分区）消费初始数据"
PIDS=""
for i in 1 2 3 4 5 6; do
  timeout 40 $KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic $TOPIC \
    --group $GROUP --consumer-property enable.auto.commit=true --timeout-ms 20000 > /dev/null 2>&1 &
  PIDS="$PIDS $!"
done
# 注意：不能用裸 wait —— 顶部的 exec > >(tee ...) 会派生 tee 进程，wait 会连它一起等，
# 而 tee 要等脚本结束才退出，于是脚本假死。必须按 PID 精确等待。
for pid in $PIDS; do wait $pid; done
echo "\$ kafka-consumer-groups.sh --describe --group $GROUP（消费完成后 LAG 应为 0）"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group $GROUP 2>/dev/null
echo

echo "############ 6.5 消费者离线期间继续写入：再写入 10000 条（模拟持续高峰 + 消费端故障）"
echo "  注意：此刻没有任何消费者进程在线"
gen_logs 10001 20000 \
  | $KAFKA_IN/kafka-console-producer.sh --bootstrap-server $BS --topic $TOPIC \
      --property parse.key=true --property key.separator=: 2>/dev/null
echo "\$ kafka-get-offsets.sh（分区位移翻倍）"
$KAFKA/kafka-get-offsets.sh --bootstrap-server $BS --topic $TOPIC 2>/dev/null
echo "\$ kafka-consumer-groups.sh --describe（LAG 增长，CONSUMER-ID 为空表示无人消费）"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group $GROUP 2>/dev/null
printf "  LAG 合计: "
total_lag
echo

echo "############ 6.6 消费者恢复：再次启动 6 个消费者，观察积压被追平"
PIDS=""
for i in 1 2 3 4 5 6; do
  timeout 60 $KAFKA/kafka-console-consumer.sh --bootstrap-server $BS --topic $TOPIC \
    --group $GROUP --timeout-ms 30000 --max-messages 2000 > /dev/null 2>&1 &
  PIDS="$PIDS $!"
done
for i in 1 2 3 4 5; do
  sleep 4
  printf "  第 %d 次采样 LAG 合计: " $i
  total_lag
done
for pid in $PIDS; do wait $pid; done
echo
echo "\$ kafka-consumer-groups.sh --describe（消费端追平后 LAG 回到 0）"
$KAFKA/kafka-consumer-groups.sh --bootstrap-server $BS --describe --group $GROUP 2>/dev/null
echo

echo "############ 6.7 结论"
echo "  1) 写入与消费完全解耦：消费者不在线，生产者照样 1 秒内写完 1 万条并返回"
echo "  2) 积压量就是 LAG 之和，是「消费者是否需要扩容」的唯一客观指标"
echo "  3) 消费者恢复后按分区并行追平：分区数决定了追平速度的上限"
echo "  4) 坑：命令行消费者在退出时会为「所有被分配的分区」提交位移（即使没处理完），"
echo "     所以用 kafka-console-consumer 演示积压时，必须让组先消费完一批、再离线写入，"
echo "     否则一启动就把 LAG 抹平了"
echo
echo "############ 06 脚本执行完成"
