#!/bin/bash

# 自动检测并切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 验证项目根目录
if [ ! -d "$PROJECT_ROOT/backend" ] || [ ! -d "$PROJECT_ROOT/frontend" ] || [ ! -d "$PROJECT_ROOT/script" ]; then
    echo "Error: Could not find project root directory."
    echo "Expected directories: backend, frontend, script"
    exit 1
fi

cd "$PROJECT_ROOT"

# 检查是否提供了版本号参数
if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.1.0"
    exit 1
fi

NEW_VERSION=$1

# 验证版本号格式（简单检查：x.x.x）
if ! echo "$NEW_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Error: Invalid version format. Expected format: x.x.x (e.g., 1.1.0)"
    exit 1
fi

echo "Updating version to $NEW_VERSION..."

# 更新 backend/app/constants.py 中的 APP_VERSION
sed -i 's/APP_VERSION: str = ".*"/APP_VERSION: str = "'"$NEW_VERSION"'"/' backend/app/constants.py

# 更新 backend/pyproject.toml 中的 version
sed -i 's/version = ".*"/version = "'"$NEW_VERSION"'"/' backend/pyproject.toml

# 更新 frontend/package.json 中的 version
sed -i 's/"version": ".*"/"version": "'"$NEW_VERSION"'"/' frontend/package.json

echo "Version updated successfully to $NEW_VERSION in all files."

# 更新依赖
echo "Updating backend dependencies..."
cd backend && uv sync && uv pip compile pyproject.toml --no-deps -o requirements.txt

echo "Updating frontend dependencies..."
cd ../frontend && npm install

echo "All updates completed."