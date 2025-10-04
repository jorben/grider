# 多阶段构建 - ETF网格交易策略设计工具
# 阶段1: 前端构建
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装所有依赖
RUN npm ci

# 复制前端源码
COPY frontend/ ./

# 构建前端应用
RUN npm run build

# 阶段2: 后端运行环境
FROM python:3.13-slim

ENV FLASK_ENV=production

# 设置工作目录
WORKDIR /app

VOLUME /app/backend/cache
VOLUME /app/backend/logs

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY backend/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建结果到Flask静态目录
COPY --from=frontend-builder /app/frontend/dist ./static

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# 暴露端口
EXPOSE 5000

# 复制启动脚本
COPY deploy/entrypoint.sh ./
RUN chmod +x entrypoint.sh

# 创建日志目录
RUN mkdir -p /app/backend/logs && chown -R app:app /app/backend/logs
RUN mkdir -p /app/backend/cache && chown -R app:app /app/backend/cache

# 切换到非root用户
USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# 启动命令
CMD ["./entrypoint.sh"]