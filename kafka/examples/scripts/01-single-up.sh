#!/usr/bin/env bash
# 01 单节点 KRaft 集群：启动、健康检查、启动日志、CLI 基本操作
#
# 用法：bash 01-single-up.sh
# 输出：/opt/kafka-lab/out/01-single-up.log

set -u
OUT=/opt/kafka-lab/out/01-single-up.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

COMPOSE=/opt/study-work/kafka/examples/compose/docker-compose-single.yml
BIN=/opt/kafka/bin
KAFKA="docker exec kafka-single $BIN"

echo "############ 1.1 启动单节点集群（KRaft 模式，broker + controller 合并角色）"
echo "\$ docker compose -f docker-compose-single.yml up -d"
docker compose -f "$COMPOSE" up -d
echo

echo "############ 1.2 等待健康检查通过"
for i in $(seq 1 30); do
  status=$(docker inspect --format '{{.State.Health.Status}}' kafka-single 2>/dev/null)
  echo "  第 ${i} 次检查: health=$status"
  [ "$status" = "healthy" ] && break
  sleep 3
done
echo

echo "############ 1.3 容器与端口状态"
echo "\$ docker compose ps"
docker compose -f "$COMPOSE" ps
echo
echo "\$ docker inspect --format '{{.State.Health.Status}} {{.State.StartedAt}}' kafka-single"
docker inspect --format '{{.State.Health.Status}} {{.State.StartedAt}}' kafka-single
echo

echo "############ 1.4 KRaft 元数据：集群 ID 与 controller 选举（启动日志）"
echo "\$ docker logs kafka-single | grep -E 'Kafka Server started|KafkaRaftServer nodeId|Cluster ID|RaftManager.*becoming the leader'"
docker logs kafka-single 2>&1 | grep -E 'Kafka Server started|KafkaRaftServer nodeId|Cluster ID|becoming the leader' | head -10
echo

echo "############ 1.5 元数据目录结构（KRaft 的 meta.properties 与 __cluster_metadata 日志）"
echo "\$ docker exec kafka-single ls -la /var/lib/kafka/data"
docker exec kafka-single ls -la /var/lib/kafka/data
echo
echo "\$ docker exec kafka-single cat /var/lib/kafka/data/meta.properties"
docker exec kafka-single cat /var/lib/kafka/data/meta.properties
echo

echo "############ 1.6 集群信息：broker 列表与 API 版本"
echo "\$ kafka-broker-api-versions.sh --bootstrap-server localhost:9092 | head -5"
$KAFKA/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 2>/dev/null | head -5
echo "..."
echo "\$ kafka-cluster.sh cluster-id --bootstrap-server localhost:9092"
$KAFKA/kafka-cluster.sh cluster-id --bootstrap-server localhost:9092
echo

echo "############ 1.7 初始主题列表（自动创建的内部主题）"
echo "\$ kafka-topics.sh --bootstrap-server localhost:9092 --list"
$KAFKA/kafka-topics.sh --bootstrap-server localhost:9092 --list 2>/dev/null
echo

echo "############ 1.8 创建业务主题 orders（3 分区、1 副本）"
echo "\$ kafka-topics.sh --create --topic orders --partitions 3 --replication-factor 1"
$KAFKA/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic orders --partitions 3 --replication-factor 1 2>&1 | grep -v '^\[' 
echo
echo "\$ kafka-topics.sh --describe --topic orders"
$KAFKA/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic orders 2>/dev/null
echo

echo "############ 1.9 主题详情（含分区目录大小）"
echo "\$ kafka-log-dirs.sh --topic-list orders"
$KAFKA/kafka-log-dirs.sh --bootstrap-server localhost:9092 --topic-list orders --describe 2>/dev/null | head -30
echo

echo "############ 1.10 广播：创建主题时副本数超过 broker 数会怎样"
echo "\$ kafka-topics.sh --create --topic too-many-replicas --partitions 1 --replication-factor 3"
$KAFKA/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic too-many-replicas --partitions 1 --replication-factor 3 2>&1 | grep -v '^\[' | head -5
echo

echo "############ 1.11 重复创建同名主题"
echo "\$ kafka-topics.sh --create --topic orders --partitions 3 --replication-factor 1"
$KAFKA/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic orders --partitions 3 --replication-factor 1 2>&1 | grep -v '^\[' | head -5
