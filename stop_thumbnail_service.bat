@echo off
chcp 65001 >nul
echo ========================================
echo 停止缩略图微服务
echo ========================================
echo.

set PORT=5001

echo [*] 查找占用端口 %PORT% 的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT%') do (
    echo     找到进程 PID: %%a
    tasklist /FI "PID eq %%a" | findstr %%a
    
    echo [*] 正在终止进程...
    taskkill /PID %%a /F
    
    if %errorlevel% == 0 (
        echo [√] 进程 %%a 已终止
    ) else (
        echo [!] 终止进程 %%a 失败
    )
)

echo.
echo ========================================
echo 缩略图微服务已停止
echo ========================================
pause
