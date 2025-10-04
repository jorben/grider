#!/bin/bash

# ETF网格交易策略设计工具 - Docker容器启动脚本

set -e

echo "🚀 启动网格交易策略设计工具..."

# 环境变量默认值
FLASK_ENV=${FLASK_ENV:-production}
HOST=${FLASK_HOST:-0.0.0.0}
PORT=${FLASK_PORT:-5000}

# 创建必要目录
mkdir -p /app/backend/logs /app/backend/cache

# 切换到backend目录以解决模块导入问题
cd /app/backend

# 根据环境选择启动方式
if [ "$FLASK_ENV" = "development" ]; then
    echo "🔧 开发环境模式启动..."
    exec python main.py
elif [ "$FLASK_ENV" = "production" ]; then
    echo "🏭 生产环境模式启动..."

    if [ -f "/app/backend/app/config/gunicorn.conf.py" ]; then
        echo "📋 使用Gunicorn配置文件启动..."
        exec gunicorn --config /app/backend/app/config/gunicorn.conf.py main:app
    else
        exec gunicorn \
            --bind ${HOST}:${PORT} \
            --workers ${WORKERS:-4} \
            --worker-class sync \
            --worker-connections 1000 \
            --timeout ${TIMEOUT:-30} \
            --keep-alive 65 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --preload \
            --access-logfile /app/backend/logs/access.log \
            --error-logfile /app/backend/logs/error.log \
            --log-level ${LOG_LEVEL:-info} \
            main:app
    fi
else
    echo "🔧 直接启动Flask应用..."
    exec python main.py
fi
