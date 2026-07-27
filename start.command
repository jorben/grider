#!/bin/bash
# ETFer 网格交易分析工具 - macOS 启动脚本
# 使用：双击本文件即可（首次需在"系统设置-隐私与安全性"允许运行）

# 切换到脚本所在目录的 backend 子目录
cd "$(dirname "$0")/backend" || exit 1

echo "============================================"
echo "  ETFer 网格交易分析工具 - 启动中"
echo "============================================"
echo ""

# 找到可用的 python3
PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then
        PY="$c"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "[错误] 未检测到 Python。"
    echo "请先安装 Python 3：https://www.python.org/downloads/macos/"
    echo "或用 Homebrew： brew install python"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

echo "使用 Python: $($PY --version 2>&1)"
echo ""

# 首次运行：创建虚拟环境
if [ ! -f ".venv/bin/python" ]; then
    echo "[首次运行] 正在创建虚拟环境..."
    "$PY" -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败。"
        read -p "按回车键退出..."
        exit 1
    fi
    echo "[首次运行] 正在安装依赖（约需 2-5 分钟，请耐心等待）..."
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 安装依赖失败，请检查网络后重试。"
        read -p "按回车键退出..."
        exit 1
    fi
    echo "[首次运行] 依赖安装完成！"
    echo ""
fi

echo "启动服务中... 启动后浏览器将自动打开 http://127.0.0.1:5000"
echo "（关闭此窗口即可停止服务）"
echo ""

# 生产模式：后端同时托管前端页面，单端口访问
export FLASK_ENV=production
export FLASK_HOST=127.0.0.1
export FLASK_PORT=5000

# 延迟 8 秒后自动打开浏览器
( sleep 8 && open http://127.0.0.1:5000 ) &

.venv/bin/python main.py --port 5000 --host 127.0.0.1
