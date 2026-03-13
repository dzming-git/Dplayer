@echo off
chcp 65001 >nul
echo 正在停止所有 Dplayer 服务...
echo.

REM 停止所有 Python 进程（小心使用，会停止所有 python.exe）
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find /V "PID"') do (
    echo 停止 PID: %%~a
    taskkill /F /PID %%~a >nul 2>&1
)

echo.
echo 所有服务已停止
timeout /t 2 >nul
