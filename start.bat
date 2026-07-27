@echo off
chcp 65001 >nul
title ETFer 网格交易分析工具
cd /d "%~dp0backend"

echo ============================================
echo   ETFer Grid Trading Tool - Starting
echo ============================================
echo.

REM ---- 查找可用的 Python 解释器 ----
REM 依次尝试: PATH 中的 python -> py 启动器 -> 用户本地安装路径
set "PYEXE="

python --version >nul 2>&1
if not errorlevel 1 set "PYEXE=python"

if not defined PYEXE (
    py --version >nul 2>&1
    if not errorlevel 1 set "PYEXE=py"
)

if not defined PYEXE (
    if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PYEXE=%LOCALAPPDATA%\Python\bin\python.exe"
)

if not defined PYEXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
)

if not defined PYEXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

if not defined PYEXE (
    echo [ERROR] Python not found / 未检测到 Python
    echo Install Python 3.10-3.13 from https://www.python.org/downloads/
    echo 安装时务必勾选 Add Python to PATH
    echo.
    pause
    exit /b 1
)

echo [OK] Using Python: %PYEXE%
echo.

REM ---- 首次运行：创建虚拟环境 ----
if not exist ".venv\Scripts\python.exe" (
    echo [Setup] Creating virtual environment / 正在创建虚拟环境...
    "%PYEXE%" -m venv .venv
    if errorlevel 1 (
        echo [ERROR] venv creation failed / 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [Setup] Installing dependencies / 正在安装依赖（约 2-5 分钟）...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] dependency install failed / 安装依赖失败，请检查网络
        pause
        exit /b 1
    )
    echo [Setup] Done / 依赖安装完成
    echo.
)

echo Starting... browser opens at http://127.0.0.1:5000
echo 启动后浏览器将自动打开。关闭此窗口即可停止服务。
echo.

set FLASK_ENV=production
set FLASK_HOST=127.0.0.1
set FLASK_PORT=5000

REM 延迟 8 秒后自动打开浏览器
start "" cmd /c "timeout /t 8 >nul && start http://127.0.0.1:5000"

.venv\Scripts\python.exe main.py --port 5000 --host 127.0.0.1

pause
