#!/usr/bin/env bash
# JENKINS_HOME 的备份与恢复。
# 只有大约 100MB 左右是真正需要备份的配置数据，构建产物（jobs/*/builds）要不要备看需求。
set -euo pipefail

JENKINS_HOME="${JENKINS_HOME:-/var/jenkins_home}"
BACKUP_DIR="${BACKUP_DIR:-/data/backup/jenkins}"
STAMP="$(date +%Y%m%d-%H%M)"
TARBALL="$BACKUP_DIR/jenkins-home-$STAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

# 1) 先做一致性快照：thinBackup 插件能在线备份；手工方式用「安全重启 + 停写」最稳
echo "== 建议先静默："
echo "   curl -X POST -u user:token \$JENKINS_URL/quietDown   # 不接受新构建，等现有构建结束"

# 2) 备份：只备配置与任务定义，排除工作区、构建日志、插件 jar（插件用 plugins.txt 重建）
echo "== 备份配置到 $TARBALL"
tar -czf "$TARBALL" \
  -C "$(dirname "$JENKINS_HOME")" \
  --exclude="$(basename "$JENKINS_HOME")/workspace" \
  --exclude="$(basename "$JENKINS_HOME")/jobs/*/workspace" \
  --exclude="$(basename "$JENKINS_HOME")/jobs/*/builds" \
  --exclude="$(basename "$JENKINS_HOME")/plugins" \
  --exclude="$(basename "$JENKINS_HOME")/war" \
  --exclude="$(basename "$JENKINS_HOME")/logs" \
  "$(basename "$JENKINS_HOME")"

echo "== 需要保留的顶层文件（恢复时按这个清单核对）"
tar -tzf "$TARBALL" | awk -F/ 'NF<=3' | grep -vE '/$' | head -n 30

# 3) 恢复：停容器 -> 解包 -> 起容器（版本必须能读旧数据，向前兼容是 Jenkins 的硬要求）
cat <<'EOF'
== 恢复步骤 ==
docker compose down
docker run --rm -v jenkins_home:/var/jenkins_home -v /data/backup/jenkins:/backup alpine \
  sh -c 'cd /var/jenkins_home && tar -xzf /backup/jenkins-home-YYYYmmdd-HHMM.tar.gz --strip-components=1'
docker compose up -d
# 插件不在备份里：用 plugins.txt 重新安装（jenkins-plugin-cli --plugin-file plugins.txt）
EOF

# 4) 定期清理旧备份
find "$BACKUP_DIR" -name 'jenkins-home-*.tar.gz' -mtime +30 -print -delete
