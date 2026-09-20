#!/usr/bin/env bash
# 04 裸机部署：二进制包安装 + KRaft 格式化 + systemd 托管 + JMX 指标
#
# 用法：bash 04-native-systemd.sh
# 输出：/opt/kafka-lab/out/04-native-systemd.log
#
# 说明：本脚本会把 Kafka 装在 /opt/kafka，数据放 /opt/kafka-data，用 kafka 系统用户运行，
#       监听 9092（broker）/ 9093（controller）/ 9101（JMX）。
#       执行前会先停掉容器版单节点，避免端口冲突。

set -u
OUT=/opt/kafka-lab/out/04-native-systemd.log
mkdir -p /opt/kafka-lab/out
exec > >(tee "$OUT") 2>&1

TARBALL=/opt/kafka-lab/kafka_2.13-4.1.2.tgz
KAFKA_HOME=/opt/kafka
DATA_DIR=/opt/kafka-data
BS=localhost:9092

echo "############ 4.1 停掉容器版单节点（避免 9092 端口冲突）"
docker stop kafka-single 2>&1 | tail -1
docker ps --format '{{.Names}}' | grep -c kafka || echo "  当前没有运行中的 kafka 容器"
echo

echo "############ 4.2 创建专用系统用户与目录"
echo "\$ useradd --system --home $KAFKA_HOME --shell /usr/sbin/nologin kafka"
id kafka > /dev/null 2>&1 || useradd --system --home $KAFKA_HOME --shell /usr/sbin/nologin kafka
id kafka
mkdir -p $DATA_DIR
echo

echo "############ 4.3 解压二进制包"
echo "\$ tar -xzf $TARBALL -C /opt && ln -sfn /opt/kafka_2.13-4.1.2 /opt/kafka"
tar -xzf $TARBALL -C /opt
ln -sfn /opt/kafka_2.13-4.1.2 $KAFKA_HOME
ls -l /opt | grep kafka
echo
echo "############ 4.3.1 坑：kafka-server-start.sh 会把 GC 日志写到 \$KAFKA_HOME/logs，该目录必须存在且可写"
echo "  本机第一次以 systemd 启动时真实报错（logs 目录不存在，kafka 用户无权创建）："
echo "    mkdir: 无法创建目录 \"/opt/kafka/bin/../logs\": 权限不够"
echo "    Error opening log file '/opt/kafka/bin/../logs/kafkaServer-gc.log': No such file or directory"
echo "    Invalid -Xlog option '-Xlog:gc*:file=/opt/kafka/bin/../logs/kafkaServer-gc.log:...'"
echo "    Error: Could not create the Java Virtual Machine."
echo "  解法：先把 logs 目录建好并交给 kafka 用户（也可以用 LOG_DIR 环境变量指到别处）"
echo "\$ mkdir -p \$KAFKA_HOME/logs && chown -R kafka:kafka \$KAFKA_HOME/logs \$DATA_DIR"
mkdir -p $KAFKA_HOME/logs
chown -R kafka:kafka $KAFKA_HOME/logs $DATA_DIR
ls -ld $KAFKA_HOME/logs $DATA_DIR
echo

echo "\$ ls $KAFKA_HOME/bin | head -12（命令都在 bin 下，.sh 结尾）"
ls $KAFKA_HOME/bin | head -12
echo "... 共 $(ls $KAFKA_HOME/bin | wc -l) 个脚本"
echo

echo "############ 4.4 KRaft 模式的 server.properties（去掉注释后的有效配置）"
echo "\$ grep -vE '^#|^$' $KAFKA_HOME/config/server.properties"
grep -vE '^#|^$' $KAFKA_HOME/config/server.properties
echo

echo "############ 4.5 本实验的配置（/opt/kafka/config/kraft-single.properties）"
cat > $KAFKA_HOME/config/kraft-single.properties <<'PROPS'
############################# Server Basics #############################
# KRaft 模式下每个节点都要有唯一 ID
node.id=1
# 该节点的角色：broker 负责数据，controller 负责元数据；单机实验两者合一
process.roles=broker,controller
# 静态 controller 集群成员：nodeId@host:controllerPort
# 三节点集群时写成 1@h1:9093,2@h2:9093,3@h3:9093
controller.quorum.voters=1@localhost:9093

############################# Socket Server Settings #############################
# 容器场景用 :9092 绑定所有网卡；裸机可用 PLAINTEXT://0.0.0.0:9092
listeners=PLAINTEXT://:9092,CONTROLLER://:9093
# 客户端拿到的地址（关键配置，写错会让客户端连不上或连到错误节点）
advertised.listeners=PLAINTEXT://localhost:9092
listener.security.protocol.map=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
inter.broker.listener.name=PLAINTEXT
controller.listener.names=CONTROLLER
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

############################# Log Basics #############################
# 数据目录：生产务必单独挂盘，且不要与操作系统盘混用
log.dirs=/opt/kafka-data
num.partitions=3
# 副本因子：单节点只能 1；内部主题（位移/事务）也要跟着改，否则消费组不可用
default.replication.factor=1
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1

############################# Log Retention Policy #############################
log.retention.hours=168
log.segment.bytes=1073741824
# 清理线程检查间隔：默认 5 分钟，实验时调小便于观察过期删段
log.retention.check.interval.ms=300000
log.cleaner.enable=true

############################# Group Coordinator #############################
group.initial.rebalance.delay.ms=0
offsets.retention.minutes=10080
PROPS
cat $KAFKA_HOME/config/kraft-single.properties
echo

echo "############ 4.6 生成集群 ID 并格式化存储目录"
echo "\$ kafka-storage.sh random-uuid"
CLUSTER_ID=$($KAFKA_HOME/bin/kafka-storage.sh random-uuid)
echo "$CLUSTER_ID"
echo
echo "\$ kafka-storage.sh format -t \$CLUSTER_ID -c config/kraft-single.properties"
# --ignore-formatted：目录已格式化过时不报错，脚本可重复执行
$KAFKA_HOME/bin/kafka-storage.sh format -t "$CLUSTER_ID" -c $KAFKA_HOME/config/kraft-single.properties --ignore-formatted
echo
echo "\$ ls -la $DATA_DIR"
ls -la $DATA_DIR
echo
echo "\$ cat $DATA_DIR/meta.properties"
cat $DATA_DIR/meta.properties
echo

echo "############ 4.7 写入 systemd unit"
cat > /etc/systemd/system/kafka.service <<'UNIT'
[Unit]
Description=Apache Kafka 4.1.2 (KRaft mode, combined broker+controller)
Documentation=https://kafka.apache.org/documentation/
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=kafka
Group=kafka
# 堆内存：生产按页缓存优先原则，Kafka 堆不用很大（6GB~8GB 常见），
# 真正的性能来自 OS 页缓存，所以磁盘内存越大越好
Environment="KAFKA_HEAP_OPTS=-Xmx1G -Xms1G"
# JMX 采集端口：Prometheus JMX Exporter / jmxterm 从这里读指标
Environment="JMX_PORT=9101"
Environment="KAFKA_OPTS=-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=9101 -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Djava.rmi.server.hostname=127.0.0.1"
# 句柄数：每个 segment 文件、每个连接都占 fd，默认 1024 远远不够
LimitNOFILE=100000
# Kafka 的优雅关闭靠 SIGTERM，超时后 systemd 会发 SIGKILL
KillSignal=SIGTERM
TimeoutStopSec=60
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/kraft-single.properties
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
echo "\$ cat /etc/systemd/system/kafka.service"
cat /etc/systemd/system/kafka.service
echo

echo "############ 4.8 启动服务并查看状态"
EFFECTIVE_CLUSTER_ID=$CLUSTER_ID
echo "  格式化时用的集群 ID: $EFFECTIVE_CLUSTER_ID"
echo "\$ systemctl daemon-reload && systemctl enable --now kafka"
systemctl daemon-reload
systemctl enable --now kafka
sleep 25
echo "\$ systemctl status kafka --no-pager"
systemctl status kafka --no-pager | head -20
echo
echo "\$ journalctl -u kafka -n 15 --no-pager"
journalctl -u kafka -n 15 --no-pager
echo

echo "############ 4.9 端口与进程"
echo "\$ ss -lntp | grep -E '9092|9093|9101'"
ss -lntp | grep -E '9092|9093|9101'
echo
echo "\$ ps -eo user,pid,%mem,rss,args | grep -E 'kafka.Kafka' | grep -v grep"
ps -eo user,pid,%mem,rss,args | grep -E 'kafka.Kafka' | grep -v grep | cut -c1-140
echo

echo "############ 4.10 验证集群可用（用发行包自带的 CLI，不依赖容器）"
echo "\$ kafka-topics.sh --list"
$KAFKA_HOME/bin/kafka-topics.sh --bootstrap-server $BS --list 2>/dev/null
echo
echo "\$ kafka-topics.sh --create --topic native-demo --partitions 2"
$KAFKA_HOME/bin/kafka-topics.sh --bootstrap-server $BS --create --topic native-demo \
  --partitions 2 --replication-factor 1 2>&1 | grep -v '^\[' | head -2
printf 'native-1\nnative-2\nnative-3\n' | $KAFKA_HOME/bin/kafka-console-producer.sh --bootstrap-server $BS --topic native-demo 2>/dev/null
echo "\$ kafka-console-consumer.sh --from-beginning"
$KAFKA_HOME/bin/kafka-console-consumer.sh --bootstrap-server $BS --topic native-demo \
  --from-beginning --max-messages 3 --timeout-ms 15000 2>/dev/null
echo

echo "############ 4.11 JMX 指标（监控章节用到的真实数据）"
echo "\$ kafka-run-class.sh org.apache.kafka.tools.JmxTool --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec"
$KAFKA_HOME/bin/kafka-run-class.sh org.apache.kafka.tools.JmxTool \
  --object-name 'kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec'   # 4.x 类名带 org.apache.kafka.tools 前缀 \
  --jmx-url service:jmx:rmi:///jndi/rmi://127.0.0.1:9101/jmxrmi --one-time true 2>/dev/null | head -3
echo
echo "\$ 同一方式读取其它关键指标"
for metric in 'kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions' 'kafka.server:type=ReplicaManager,name=PartitionCount' 'kafka.controller:type=KafkaController,name=ActiveControllerCount' 'kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent'; do
  echo "  --- $metric"
  $KAFKA_HOME/bin/kafka-run-class.sh org.apache.kafka.tools.JmxTool --object-name "$metric" \
    --jmx-url service:jmx:rmi:///jndi/rmi://127.0.0.1:9101/jmxrmi --one-time true 2>/dev/null | head -2
done
echo

echo "############ 4.12 优雅停止 + 重启，验证数据持久化"
systemctl stop kafka
sleep 5
echo "\$ systemctl is-active kafka"
systemctl is-active kafka || true
echo "\$ journalctl -u kafka -n 4（应能看到优雅关闭日志）"
journalctl -u kafka -n 4 --no-pager | tail -4
systemctl start kafka
sleep 20
echo "\$ systemctl is-active kafka"
systemctl is-active kafka
echo "\$ 重启后主题与消息仍在（数据落在 $DATA_DIR）"
$KAFKA_HOME/bin/kafka-topics.sh --bootstrap-server $BS --list 2>/dev/null
$KAFKA_HOME/bin/kafka-console-consumer.sh --bootstrap-server $BS --topic native-demo \
  --from-beginning --max-messages 3 --timeout-ms 15000 2>/dev/null
echo

echo "############ 04 脚本执行完成"
