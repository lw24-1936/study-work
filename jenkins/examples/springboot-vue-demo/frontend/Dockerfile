# 前端运行镜像：静态站点交给 nginx，顺便把 /api 反代到后端
FROM nginx:1.27-alpine

# 静态文件（Jenkins 的 npm build 阶段产出 dist/）
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
