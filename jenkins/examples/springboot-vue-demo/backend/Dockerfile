# 运行镜像：只放 JRE 与 jar，镜像约 90MB
# 构建：docker build -t demo-backend:1.0.0 .
# 跑：  docker run -d -p 9090:9090 -e SPRING_PROFILES_ACTIVE=prod demo-backend:1.0.0
FROM eclipse-temurin:21-jre-alpine

# 时区与健康检查用的 wget（alpine 自带 busybox wget）
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

WORKDIR /app
# 构建产物由 Jenkins 的 maven 阶段产出后拷进来
COPY target/demo-backend.jar /app/app.jar

# 以非 root 运行
RUN addgroup -S app && adduser -S app -G app && chown -R app:app /app
USER app

EXPOSE 9090

HEALTHCHECK --interval=15s --timeout=3s --start-period=40s --retries=3 \
    CMD wget -qO- http://127.0.0.1:9090/api/todos/health || exit 1

ENV JAVA_OPTS="-XX:MaxRAMPercentage=75 -XX:+UseZGC"
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar"]
