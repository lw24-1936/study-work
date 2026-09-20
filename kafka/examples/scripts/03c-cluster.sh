#!/usr/bin/env bash
# 03c 三 broker + 单 controller 的 KRaft 集群（可靠可复现的拓扑）
#
# 为什么用这个拓扑：
#   本机实测，4.1.2 里用三个 combined 节点 + 静态 controller.quorum.voters 时，
#   controller quorum 一直选不出 leader（epoch 递增直到 broker 注册超时退出）；
#   而 4.x 又要求"格式化时必须给出初始 controller 集合"，动态 quorum 写法（只给
#   controller.quorum.bootstrap.servers）在镜像自动格式化时会被拒绝：
#     Because controller.quorum.voters is not set on this controller, you must specify
#     one of the following: --standalone, --initial-controllers, or --no-initial-controllers.
#   所以这里采用「1 个 controller-only 节点（voters 只有它自己，quorum=1）+ 3 个 broker-only 节点」
#   的拓扑：既能真实演示 3 副本、ISR、Leader 切换，也不受多 voter 选举问题影响。
#
# 用法：bash 03c-cluster.sh

set -u
OUT=/opt/kafka-lab/out/03c-cluster.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

BIN=/opt/kafka/bin
NET=kafka-net
IMG=apache/kafka:4.1.2
CLUSTER_ID=Ct9rXm2pT0KuV6wLbYhN4Q
BS=kafka-1:9092
# 独立的 CLI 客户端容器：所有命令行操作都从它执行，这样停掉任意 broker 都不会影响排查
CLI="docker exec kafka-cli $BIN"
CTRL="docker exec kafka-ctrl $BIN"

echo "############ 3c.1 启动单 controller + 三 broker + 一个 CLI 客户端容器"
docker network create $NET 2>/dev/null || echo "  网络 $NET 已存在"
for n in kafka-ctrl kafka-1 kafka-2 kafka-3 kafka-cli; do docker rm -f $n 2>/dev/null | head -1; done

echo "\$ docker run -d --name kafka-cli apache/kafka:4.1.2 sleep infinity（只跑 CLI，不启 Kafka 进程）"
docker run -d --name kafka-cli --hostname kafka-cli --network $NET $IMG sleep infinity > /dev/null
echo "  已启动 kafka-cli"
echo

echo "\$ docker run -d --name kafka-ctrl（process.roles=controller）"
echo "  坑：controller-only 节点不能设置 KAFKA_ADVERTISED_LISTENERS，镜像会直接拒绝并退出："
echo "      KAFKA_ADVERTISED_LISTENERS is not supported on a KRaft controller."
docker run -d --name kafka-ctrl --hostname kafka-ctrl --network $NET \
  -e CLUSTER_ID=$CLUSTER_ID \
  -e KAFKA_NODE_ID=100 \
  -e KAFKA_PROCESS_ROLES=controller \
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=100@kafka-ctrl:9093 \
  -e KAFKA_LISTENERS=CONTROLLER://:9093 \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT \
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_LOG_DIRS=/var/lib/kafka/data \
  -e KAFKA_HEAP_OPTS="-Xmx512m -Xms512m" \
  -v kafka-ctrl-data:/var/lib/kafka/data \
  $IMG > /dev/null
sleep 20
echo "  controller 侧的 quorum 状态（注意 4.x 的语法：describe 是位置参数，不是 --describe）:"
echo "\$ kafka-metadata-quorum.sh --bootstrap-controller kafka-ctrl:9093 describe --status"
$CTRL/kafka-metadata-quorum.sh --bootstrap-controller kafka-ctrl:9093 describe --status 2>&1 | head -10
echo

start_broker() {
  local id=$1 name=$2
  echo "\$ docker run -d --name $name（process.roles=broker）"
  docker run -d --name $name --hostname $name --network $NET \
    -e CLUSTER_ID=$CLUSTER_ID \
    -e KAFKA_NODE_ID=$id \
    -e KAFKA_PROCESS_ROLES=broker \
    -e KAFKA_CONTROLLER_QUORUM_VOTERS=100@kafka-ctrl:9093 \
    -e KAFKA_LISTENERS=PLAINTEXT://:9092 \
    -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://$name:9092 \
    -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
    -e KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT \
    -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
    -e KAFKA_LOG_DIRS=/var/lib/kafka/data \
    -e KAFKA_NUM_PARTITIONS=3 \
    -e KAFKA_DEFAULT_REPLICATION_FACTOR=3 \
    -e KAFKA_MIN_INSYNC_REPLICAS=2 \
    -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=3 \
    -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=3 \
    -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=2 \
    -e KAFKA_AUTO_CREATE_TOPICS_ENABLE=false \
    -e KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0 \
    -e KAFKA_HEAP_OPTS="-Xmx512m -Xms512m" \
    -v ${name}-data:/var/lib/kafka/data \
    $IMG > /dev/null
}
start_broker 1 kafka-1
start_broker 2 kafka-2
start_broker 3 kafka-3
sleep 35
echo

echo "############ 3c.2 集群成员（三个 broker 都应列出）"
echo "\$ kafka-broker-api-versions.sh --bootstrap-server $BS | grep '^kafka-'"
$CLI/kafka-broker-api-versions.sh --bootstrap-server $BS 2>/dev/null | grep -E '^kafka-'
echo

echo "############ 3c.3 controller 侧 quorum：voter 是 controller，broker 以 observer 身份跟随"
echo "\$ kafka-metadata-quorum.sh --bootstrap-controller kafka-ctrl:9093 describe --replication"
$CTRL/kafka-metadata-quorum.sh --bootstrap-controller kafka-ctrl:9093 describe --replication 2>/dev/null
echo

echo "############ 3c.4 创建 3 副本主题（min.insync.replicas=2）"
echo "\$ kafka-topics.sh --create --topic demo-replicated --partitions 3 --replication-factor 3 --config min.insync.replicas=2"
$CLI/kafka-topics.sh --bootstrap-server $BS --create --topic demo-replicated --partitions 3 \
  --replication-factor 3 --config min.insync.replicas=2 2>&1 | grep -v '^\[' | head -2
echo "\$ kafka-topics.sh --describe --topic demo-replicated"
$CLI/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo

echo "############ 3c.5 每个 broker 上的副本目录（同一分区三份副本）"
for c in kafka-1 kafka-2 kafka-3; do
  printf "  %-9s: " $c
  docker exec $c ls /var/lib/kafka/data 2>/dev/null | grep demo-replicated | tr '\n' ' '
  echo
done
echo

echo "############ 3c.6 写入 6 条消息（带 key）"
printf 'k1:m1\nk2:m2\nk3:m3\nk1:m4\nk2:m5\nk3:m6\n' \
  | docker exec -i kafka-cli $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: 2>/dev/null
$CLI/kafka-get-offsets.sh --bootstrap-server $BS --topic demo-replicated 2>/dev/null
echo

echo "############ 3c.7 宕机演练一：停掉分区 0 的 Leader，观察 Leader 切换与 ISR 缩小"
LEADER=$(docker exec kafka-cli $BIN/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null \
  | awk '/Partition: 0/{for (i = 1; i <= NF; i++) if ($i == "Leader:") print $(i + 1)}')
echo "  分区 0 的 Leader 是 broker $LEADER -> docker stop kafka-$LEADER"
docker stop kafka-$LEADER > /dev/null
sleep 15
echo "\$ kafka-topics.sh --describe（Leader 已重新选举，ISR 缩小为 2）"
$CLI/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo

echo "############ 3c.8 只剩 2 个副本时继续写入（acks=all + min.insync.replicas=2 刚好满足）"
printf 'k4:m7\nk5:m8\n' \
  | docker exec -i kafka-cli $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: --producer-property acks=all 2>&1 | tail -1
$CLI/kafka-get-offsets.sh --bootstrap-server $BS --topic demo-replicated 2>/dev/null
echo

echo "############ 3c.9 宕机演练二：再停一个 broker，ISR 只剩 1，写入应被拒绝"
REMAIN=$(docker ps --format '{{.Names}}' | grep -E '^kafka-[0-9]$' | head -1)
echo "  再停一个: docker stop $REMAIN"
docker stop $REMAIN > /dev/null
sleep 15
echo "\$ kafka-topics.sh --describe --under-replicated-partitions（ISR 只剩 1 个）"
$CLI/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo
echo "\$ 继续写入（预期 NOT_ENOUGH_REPLICAS）"
printf 'k6:m9\n' \
  | docker exec -i kafka-cli $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: --producer-property acks=all 2>&1 | tail -4
echo

echo "############ 3c.10 恢复：重启两个 broker，观察 ISR 回补"
docker start kafka-$LEADER $REMAIN > /dev/null
sleep 30
echo "\$ kafka-topics.sh --describe（ISR 恢复为 3）"
$CLI/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo
echo "\$ 恢复后写入一条确认集群可用"
printf 'k7:m10\n' \
  | docker exec -i kafka-cli $BIN/kafka-console-producer.sh --bootstrap-server $BS --topic demo-replicated \
      --property parse.key=true --property key.separator=: --producer-property acks=all 2>&1 | tail -1
$CLI/kafka-get-offsets.sh --bootstrap-server $BS --topic demo-replicated 2>/dev/null
echo

echo "############ 3c.11 分区重分配（模拟扩容/迁移：把副本顺序换一轮）"
cat > /tmp/reassign.json <<'JSON'
{"version":1,"partitions":[
  {"topic":"demo-replicated","partition":0,"replicas":[3,2,1]},
  {"topic":"demo-replicated","partition":1,"replicas":[1,3,2]},
  {"topic":"demo-replicated","partition":2,"replicas":[2,1,3]}
]}
JSON
docker cp /tmp/reassign.json kafka-cli:/tmp/reassign.json
echo "\$ kafka-reassign-partitions.sh --reassignment-json-file /tmp/reassign.json --execute"
$CLI/kafka-reassign-partitions.sh --bootstrap-server $BS --reassignment-json-file /tmp/reassign.json --execute 2>&1 | grep -v '^\[' | head -8
sleep 10
echo "\$ kafka-reassign-partitions.sh --verify"
$CLI/kafka-reassign-partitions.sh --bootstrap-server $BS --reassignment-json-file /tmp/reassign.json --verify 2>&1 | grep -v '^\[' | head -8
echo "\$ kafka-topics.sh --describe（副本顺序已变化）"
$CLI/kafka-topics.sh --bootstrap-server $BS --describe --topic demo-replicated 2>/dev/null
echo

echo "############ 3c.12 保留容器（后续章节继续用）：docker rm -f kafka-ctrl kafka-1 kafka-2 kafka-3 kafka-cli"
echo "############ 03c 脚本执行完成"
