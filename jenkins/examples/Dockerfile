# 自定义镜像：把插件烧进镜像，容器第一次启动就已经装好
#
# 构建（国内网络加镜像源参数，见下）：
#   docker build -t my-jenkins:2.580.1 -f Dockerfile .
#   docker run -d --name jenkins -p 8080:8080 -p 50000:50000 -v jenkins_home:/var/jenkins_home my-jenkins:2.580.1
#
# 说明：
# - jenkins-plugin-cli 会从 Update Center 解析插件与依赖；--cleanup-downloads 让它下完即删临时目录
# - 下载慢时把 update-center 换成国内镜像（清华）：
#   RUN jenkins-plugin-cli -i https://mirrors.tuna.tsinghua.edu.cn/jenkins/updates/update-center.json \
#         --plugin-file /usr/share/jenkins/ref/plugins.txt --cleanup-downloads

FROM jenkins/jenkins:2.580.1-lts-jdk21

# 运行容器的用户（镜像自带 jenkins，UID 1000）
USER root

# 构建期需要的常用工具：git 用于拉代码、curl 用于健康检查
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

USER jenkins

# 插件清单
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt --cleanup-downloads

# 用 Configuration as Code 预置基础配置（可选）
COPY --chown=jenkins:jenkins casc/jenkins.yaml /usr/share/jenkins/ref/casc/jenkins.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc/jenkins.yaml
