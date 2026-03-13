@echo off
REM 管理后台启动脚本 (Windows)

REM 设置控制台编码为 UTF-8
chcp 65001 >nul

echo ========================================
echo   Dplayer 管理后台启动脚本
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python 环境
    echo 请确保 Python 已安装并添加到 PATH
    pause
    exit /b 1
)

echo [信息] 检测到 Python 环境
python --version
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

REM 切换到脚本所在目录
cd /d "%~dp0"

echo [信息] 启动管理后台...
echo.

REM 启动管理后台 (端口 8080)
echo 访问地址:
echo   管理后台: http://localhost:8080
echo   主应用:   http://localhost:80
echo.
echo 按 Ctrl+C 停止服务
echo.

python admin_app.py

pause
