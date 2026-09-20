#!/usr/bin/env bash
# 03 三节点集群：副本分布、ISR、broker 宕机与恢复、ack 语义、分区重分配
#
# 用法：bash 03-cluster.sh
# 输出：/opt/kafka-lab/out/03-cluster.log
#
# 前置：先停掉单节点集群，再启动三节点集群（两者都用 9092 之外无冲突，但为了清晰建议只开一个）

set -u
OUT=/opt/kafka-lab/out/03-cluster.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

COMPOSE=/opt/study-work/kafka/examples/compose/docker-compose-cluster.yml
BIN=/opt/kafka/bin
BS=kafka-1:9092
K1="docker exec kafka-1 $BIN"
K2="docker exec kafka-2 $BIN"
K3="docker exec kafka-3 $BIN"

echo "############ 3.1 启动三节点 KRaft 集群（错峰启动：第一个节点就绪后再起其余节点）"
echo "  坑：三个 KRaft 节点同时启动时，controller quorum 会陷入选举风暴（epoch 不断递增、始终没有 leader），"
echo "      随后 broker 因 'unable to register with the controller quorum' 注册超时退出，容器以 exit=1 结束。"
echo "      正确做法是错峰启动：先让第一个节点选出 leader，再拉起其余节点。"
echo "\$ docker compose -f docker-compose-cluster.yml up -d kafka-1"
docker compose -f "$COMPOSE" up -d kafka-1 2>&1 | tail -3
for i in $(seq 1 30); do
  h1=$(docker inspect --format '{{.State.Health.Status}}' kafka-1 2>/dev/null)
  echo "  kafka-1 health=$h1"
  [ "$h1" = "healthy" ] && break
  sleep 3
done
echo
echo "\$ docker compose -f docker-compose-cluster.yml up -d kafka-2 kafka-3"
docker compose -f "$COMPOSE" up -d kafka-2 kafka-3 2>&1 | tail -3
for i in $(seq 1 40); do
  h1=$(docker inspect --format '{{.State.Health.Status}}' kafka-1 2>/dev/null)
  h2=$(docker inspect --format '{{.State.Health.Status}}' kafka-2 2>/dev/null)
  h3=$(docker inspect --format '{{.State.Health.Status}}' kafka-3 2>/dev/null)
  echo "  第 ${i} 次检查: kafka-1=$h1 kafka-2=$h2 kafka-3=$h3"
  [ "$h1" = "healthy" ] && [ "$h2" = "healthy" ] && [ "$h3" = "healthy" ] && break
  sleep 3
done
echo

echo "############ 3.2 集群成员与 controller"
echo "\$ kafka-broker-api-versions.sh --bootstrap-server kafka-1:9092（三行分别对应三个 broker）"
$K1/kafka-broker-api-versions.sh --bootstrap-server $BS 2>/dev/null | grep -E '^kafka-[0-9]'
echo
echo "\$ kafka-metadata-quorum.sh --describe --status"
$K1/kafka-metadata-quorum.sh --bootstrap-server $BS --describe --status 2>/dev/null
echo

echo "############ 3.3 创建 3 副本主题 demo-replicated（3 分区、min.insync.replicas=2）"
$K1/kafka-topics.sh --bootstrap-server $BS --create --topic demo-replicated --partitions 3 \
  --replication-factor 3 --config min.insync.replicas=2 2>&1 | grep -v '^\[' | head -2
echo "\$ kafka-topics.sh --describe --topic demo-replicated"
$K1/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo

echo "############ 3.4 写入 6 条消息，观察分区与位移"
printf 'k1:m1\nk2:m2\nk3:m3\nk1:m4\nk2:m5\nk3:m6\n' \
  | docker exec -i kafka-1 $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: 2>/dev/null
$K1/kafka-get-offsets.sh --bootstrap-server $BS --topic demo-replicated 2>/dev/null
echo

echo "############ 3.5 每个 broker 上的副本目录（同一分区在 3 个 broker 上各有一份）"
for c in kafka-1 kafka-2 kafka-3; do
  echo "  --- $c ---"
  docker exec $c ls /var/lib/kafka/data | grep demo-replicated
done
echo

echo "############ 3.6 宕机演练：停掉 demo-replicated 的某个分区 leader 所在 broker"
LEADER=$(docker exec kafka-1 $BIN/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null \
  | awk -F'Leader: ' '/Partition: 0/{print $2}' | awk '{print $1}')
echo "  分区 0 的 Leader 是 broker $LEADER，现在停掉它（docker stop kafka-$LEADER）"
docker stop kafka-$LEADER > /dev/null
sleep 12
echo "\$ kafka-topics.sh --describe（观察 Leader 切换与 ISR 变化）"
$K1/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo

echo "############ 3.7 在只剩 2 个副本的情况下继续写入（acks=all + min.insync.replicas=2，应成功）"
printf 'k4:m7\nk5:m8\n' \
  | docker exec -i kafka-1 $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: --producer-property acks=all 2>&1 | tail -2
$K1/kafka-get-offsets.sh --bootstrap-server $BS --topic demo-replicated 2>/dev/null
echo

echo "############ 3.8 再停一个 broker：ISR 只剩 1 个，低于 min.insync.replicas=2"
docker stop kafka-2 > /dev/null
sleep 12
echo "\$ kafka-topics.sh --describe（ISR 只剩 1 个）"
$K1/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo
echo "  继续写入：因不满足 min.insync.replicas=2，生产者应报 NotEnoughReplicas"
printf 'k6:m9\n' \
  | docker exec -i kafka-1 $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: --producer-property acks=all 2>&1 | tail -6
echo

echo "############ 3.9 恢复：重启两个 broker，观察 ISR 回补"
docker start kafka-2 kafka-$LEADER > /dev/null
sleep 25
echo "\$ kafka-topics.sh --describe（ISR 应恢复到 3 个，Leader 分布重新均衡）"
$K1/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo
echo "  恢复后写入一条，确认集群可用:"
printf 'k7:m10\n' \
  | docker exec -i kafka-1 $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: --producer-property acks=all 2>&1 | tail -2
$K1/kafka-get-offsets.sh --bootstrap-server $BS --topic demo-replicated 2>/dev/null
echo

echo "############ 3.10 分区重分配：把 demo-replicated 整体迁到 broker 2/3，再迁回来"
$K1/kafka-topics.sh --bootstrap-server $BS --create --topic reassign-json --partitions 1 --replication-factor 1 2>/dev/null
cat > /tmp/reassign.json <<'JSON'
{"version":1,"partitions":[
  {"topic":"demo-replicated","partition":0,"replicas":[2,3,1]},
  {"topic":"demo-replicated","partition":1,"replicas":[3,1,2]},
  {"topic":"demo-replicated","partition":2,"replicas":[1,2,3]}
]}
JSON
echo "\$ kafka-reassign-partitions.sh --reassignment-json-file /tmp/reassign.json --execute"
$K1/kafka-reassign-partitions.sh --bootstrap-server $BS --reassignment-json-file /tmp/reassign.json --execute 2>&1 | grep -v '^\[' | head -8
echo "\$ kafka-reassign-partitions.sh --verify"
$K1/kafka-reassign-partitions.sh --bootstrap-server $BS --reassignment-json-file /tmp/reassign.json --verify 2>&1 | grep -v '^\[' | head -8
echo "\$ kafka-topics.sh --describe（副本顺序已按重分配结果调整）"
$K1/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo

echo "############ 3.11 集群级指标：未同步分区数与每秒消息数（JMX）"
echo "\$ kafka-run-class.sh kafka.tools.JmxTool --object-name kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions"
$K1/kafka-run-class.sh kafka.tools.JmxTool --object-name 'kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions' \
  --jmx-url service:jmx:rmi:///jndi/rmi://kafka-1:9101/jmxrmi --one-time true 2>&1 | head -4 || echo "  （容器未开启 JMX 端口，可用 docker exec 直接读本地 JMX - 见教程说明）"
echo

echo "############ 3.12 清理"
docker compose -f "$COMPOSE" stop 2>&1 | tail -3
echo "############ 03 脚本执行完成"
