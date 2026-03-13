@echo off
chcp 65001 >nul
echo ========================================
echo 缩略图微服务启动脚本
echo ========================================
echo.

REM 设置环境变量
set THUMBNAIL_SERVICE_PORT=5001
set THUMBNAIL_SERVICE_HOST=0.0.0.0
set MAX_CONCURRENT_TASKS=5
set QUEUE_SIZE=100
set TASK_TIMEOUT=30
set LOG_LEVEL=INFO

REM 检查端口占用
echo [*] 检查端口 %THUMBNAIL_SERVICE_PORT% 是否被占用...
netstat -ano | findstr :%THUMBNAIL_SERVICE_PORT% >nul
if %errorlevel% == 0 (
    echo [!] 端口 %THUMBNAIL_SERVICE_PORT% 已被占用
    echo [*] 正在查找占用端口的进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%THUMBNAIL_SERVICE_PORT%') do (
        echo     PID: %%a
        tasklist /FI "PID eq %%a" | findstr %%a
    )
    echo.
    echo [!] 请手动终止占用端口的进程后再试
    pause
    exit /b 1
)

echo [√] 端口 %THUMBNAIL_SERVICE_PORT% 可用
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

REM 保存进程ID
echo [*] 启动缩略图微服务...
echo [%date% %time%] Starting thumbnail service on port %THUMBNAIL_SERVICE_PORT%
echo [%date% %time%] PID: %PID% > logs\thumbnail_service_start.log

REM 启动服务
start "Thumbnail Microservice" python thumbnail_service.py

REM 等待服务启动
echo [*] 等待服务启动...
timeout /t 3 /nobreak >nul

REM 检查服务是否启动成功
echo [*] 检查服务状态...
curl -s http://localhost:%THUMBNAIL_SERVICE_PORT%/health >nul
if %errorlevel% == 0 (
    echo [√] 缩略图微服务启动成功！
    echo [*] 服务地址: http://localhost:%THUMBNAIL_SERVICE_PORT%
    echo [*] 健康检查: http://localhost:%THUMBNAIL_SERVICE_PORT%/health
    echo [*] 服务指标: http://localhost:%THUMBNAIL_SERVICE_PORT%/metrics
    echo.
    echo [*] 按任意键关闭此窗口（服务将继续运行）
    pause
) else (
    echo [!] 缩略图微服务启动失败，请查看日志文件
    echo [*] 日志位置: logs\thumbnail_service.log
    pause
)

exit /b %errorlevel%
