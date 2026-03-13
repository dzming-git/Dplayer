@echo off
chcp 65001 >nul
echo ========================================
echo 启动所有服务（含缩略图微服务）
echo ========================================
echo.

REM 启动缩略图微服务
echo [*] 启动缩略图微服务...
start "Thumbnail Microservice" cmd /c start_thumbnail_service.bat
timeout /t 2 /nobreak >nul

REM 启动主应用
echo [*] 启动主应用...
start "Main App" cmd /c start.bat

echo.
echo ========================================
echo 所有服务启动完成！
echo ========================================
echo.
echo [*] 主应用: http://localhost:80
echo [*] 缩略图服务: http://localhost:5001
echo [*] 管理后台: http://localhost:8080
echo.
echo [*] 按任意键关闭此窗口（服务将继续运行）
pause
