@echo off
chcp 65001 >nul
echo ========================================
echo 停止所有服务
echo ========================================
echo.

REM 停止缩略图微服务
echo [*] 停止缩略图微服务...
call stop_thumbnail_service.bat
echo.

REM 停止主应用
echo [*] 停止主应用...
call stop_services.bat
echo.

echo ========================================
echo 所有服务已停止
echo ========================================
pause
