#!/usr/bin/env bash
# 03b 三节点 KRaft 集群（KIP-853 动态 quorum 写法：controller.quorum.bootstrap.servers）
#
# 背景：本机实测发现，用静态 controller.quorum.voters=1@kafka-1:9093,... 启动三个 4.1.2 节点时，
#       controller quorum 会一直处在选举风暴（epoch 递增、没有 leader），broker 60 秒后
#       因 "unable to register with the controller quorum" 退出。
#       改用 4.x 推荐的动态 quorum 配置（只给 bootstrap.servers，不给 voters）后集群正常成型。
#
# 用法：bash 03b-cluster-dynamic.sh

set -u
OUT=/opt/kafka-lab/out/03b-cluster.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

BIN=/opt/kafka/bin
NET=kafka-net
IMG=apache/kafka:4.1.2
CLUSTER_ID=MvQ3yQ8kT1WxZ7bPcJdR2Q
BS=kafka-1:9092

echo "############ 3b.1 建网络与三个节点（错峰启动，等第一个节点选出 leader 再起其余）"
docker network create $NET 2>/dev/null || echo "  网络 $NET 已存在"
docker rm -f kafka-1 kafka-2 kafka-3 2>/dev/null | head -3

start_node() {
  local id=$1 name=$2
  docker run -d --name $name --hostname $name --network $NET \
    -e CLUSTER_ID=$CLUSTER_ID \
    -e KAFKA_NODE_ID=$id \
    -e KAFKA_PROCESS_ROLES=broker,controller \
    -e KAFKA_CONTROLLER_QUORUM_BOOTSTRAP_SERVERS=kafka-1:9093,kafka-2:9093,kafka-3:9093 \
    -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
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
  echo "  已启动 $name (node.id=$id)"
}

echo "\$ docker run -d --name kafka-1 ... apache/kafka:4.1.2"
start_node 1 kafka-1
sleep 25
echo "  kafka-1 是否已选出 leader:"
docker exec kafka-1 $BIN/kafka-metadata-quorum.sh --bootstrap-server kafka-1:9092 --describe --status 2>&1 | head -8
echo
echo "\$ docker run -d --name kafka-2/3 ... （其余两个节点）"
start_node 2 kafka-2
start_node 3 kafka-3
sleep 30
echo

echo "############ 3b.2 集群成员与 controller"
echo "\$ kafka-broker-api-versions.sh --bootstrap-server $BS | grep '^kafka-'"
docker exec kafka-1 $BIN/kafka-broker-api-versions.sh --bootstrap-server $BS 2>/dev/null | grep -E '^kafka-'
echo
echo "\$ kafka-metadata-quorum.sh --describe --status"
docker exec kafka-1 $BIN/kafka-metadata-quorum.sh --bootstrap-server $BS --describe --status 2>/dev/null
echo
echo "\$ kafka-metadata-quorum.sh --describe --replication"
docker exec kafka-1 $BIN/kafka-metadata-quorum.sh --bootstrap-server $BS --describe --replication 2>/dev/null

echo "############ 3b 完成"
