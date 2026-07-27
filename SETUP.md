# ETFer-Clone 在其他电脑上运行指南

复刻 etfer.top 的网格交易分析工具。数据源用免费的 **AkShare**（无需 token、无到期、不花钱）。
后端 Flask(Python) 已内置托管前端页面，**运行时不需要 Node**，只需要 **Python**。

> 全程免费：GitHub 免费、AkShare 免费、本地运行无服务器费。唯一前提是装一次 Python（免费）。

---

## ⚠️ 重要：不能直接把 Windows 文件夹拷到 Mac 用

`backend/.venv`（Python 环境）和 `start.bat` 是 **Windows 专用**的，拷到 Mac 不能用。
正确做法是：**只传源代码**（不含 .venv / node_modules），到 Mac 上重新生成环境。
推荐用 GitHub 或 zip（见下）。

---

## 一、目标电脑装好 Python（一次性，免费）

- **macOS**：
  - 方式1：https://www.python.org/downloads/macos/ 下载 3.12/3.13 安装包
  - 方式2（推荐）：装 Homebrew 后 `brew install python`
  - 验证：终端输入 `python3 --version`
- **Windows**：https://www.python.org/downloads/ ，安装时勾选 “Add Python to PATH”
  - 验证：`python --version`

---

## 二、把代码拿到目标电脑（二选一）

### 方式 A：GitHub（推荐，多台机器同步方便）
```
git clone https://github.com/vickingwu/grider.git etfer-clone
cd etfer-clone
```
> 注意：当前改造代码需先在本机 `git push` 后，clone 下来的才是这份可用版本。

### 方式 B：打包 zip 拷贝（不依赖 GitHub）
在本机把 `etfer-clone` 文件夹压缩成 zip，但**先删掉这三个目录**（目标机会重建）：
- `backend/.venv`
- `frontend/node_modules`
- `frontend/dist`（可选）

`static/`（已编译好的前端）**要保留**，这样目标机无需装 Node。

---

## 三、启动

### macOS
1. 打开“终端”，给启动脚本加执行权限（仅首次）：
   ```
   cd /路径/到/etfer-clone
   chmod +x start.command
   ```
2. 之后**双击 `start.command`** 即可（或终端 `./start.command`）。
   - 首次会自动创建环境并装依赖（2-5 分钟）。
   - 完成后浏览器自动打开 http://127.0.0.1:5000

### Windows
- **双击 `start.bat`** 即可（首次自动建环境装依赖）。

> 两个脚本都会：检测 Python → 首次自动建 venv + 装依赖 → 启动 → 自动开浏览器。
> 关闭弹出的命令行/终端窗口即停止服务。

---

## 四、手动启动（脚本不灵时）

**macOS：**
```
cd etfer-clone/backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export FLASK_ENV=production
.venv/bin/python main.py --port 5000 --host 127.0.0.1
```
**Windows：**
```
cd etfer-clone\backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
set FLASK_ENV=production
.venv\Scripts\python.exe main.py --port 5000 --host 127.0.0.1
```
然后浏览器打开 http://127.0.0.1:5000

---

## 五、常见问题

- **macOS 双击提示“无法打开/未受信任”**：右键 `start.command` → 打开 → 确认；
  或“系统设置 → 隐私与安全性”里点“仍要打开”。
- **日志刷 “Connection aborted”**：正常，主数据源(东方财富)偶发限流，自动切新浪兜底，不影响结果。
- **个股名称首次显示成代码**：首次下载名称表约十几秒，之后缓存到 `backend/cache/`。
- **端口被占用**：换端口启动（如 `--port 5001`），浏览器也用对应端口。
- **改了前端代码想更新页面**：需要重新 `cd frontend && npm run build`，再把 `frontend/dist`
  覆盖到根目录 `static/`（这一步才需要 Node；纯使用不需要）。

---

## 六、如果想“完全不装 Python”（可选，需额外操作）

- **打包成可执行文件**：用 PyInstaller 把后端打成 Mac/Windows 各自的可执行程序，
  目标机零安装双击运行。需要分别在 Mac 和 Windows 上各打包一次（不能跨平台打包）。
- **部署到免费云**：部署到 Fly.io/Render 免费档，任何设备开网页即用，无需拷贝。
  （免费档会休眠、冷启动慢，且依赖服务器能访问国内行情源。）

需要这两种之一可再找我配置。
