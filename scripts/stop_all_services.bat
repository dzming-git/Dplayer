@echo off
chcp 65001 >nul
echo ================================================================================
echo Dplayer 服务停止脚本
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/2] 查找并停止主应用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":80 "') do (
    echo 找到进程 %%a
    taskkill /F /PID %%a >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] 主应用已停止
    ) else (
        echo [警告] 无法停止进程 %%a
    )
)

echo.
echo [2/2] 查找并停止管理后台...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 "') do (
    echo 找到进程 %%a
    taskkill /F /PID %%a >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] 管理后台已停止
    ) else (
        echo [警告] 无法停止进程 %%a
    )
)

echo.
echo ================================================================================
echo 服务停止完成
echo ================================================================================
echo.

timeout /t 2 /nobreak >nul
