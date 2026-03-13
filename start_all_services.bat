@echo off
chcp 65001 >nul
echo ================================================================================
echo Dplayer 服务启动脚本
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/3] 检查端口占用...
netstat -ano | findstr ":80 " >nul
if %errorlevel% == 0 (
    echo [警告] 端口80已被占用，请先停止相关服务
    pause
    exit /b 1
)

netstat -ano | findstr ":8080 " >nul
if %errorlevel% == 0 (
    echo [警告] 端口8080已被占用，请先停止相关服务
    pause
    exit /b 1
)

echo [OK] 端口检查完成
echo.

echo [2/3] 启动主应用（端口80）...
start "Dplayer-Main" cmd /k "python app.py"
timeout /t 3 /nobreak >nul

echo [OK] 主应用已启动
echo.

echo [3/3] 启动管理后台（端口8080）...
start "Dplayer-Admin" cmd /k "python admin_app.py"
timeout /t 2 /nobreak >nul

echo [OK] 管理后台已启动
echo.

echo ================================================================================
echo 所有服务启动完成！
echo ================================================================================
echo.
echo 访问地址:
echo   - 用户界面: http://localhost:80
echo   - 管理后台: http://localhost:8080
echo.
echo 按 Ctrl+C 可关闭此窗口（服务将继续在后台运行）
echo.

pause
