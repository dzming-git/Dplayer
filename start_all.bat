@echo off
REM 双端口架构启动脚本 (Windows)

REM 设置控制台编码为 UTF-8
chcp 65001 >nul

:MENU
cls
echo ========================================
echo   Dplayer 双端口架构启动脚本
echo ========================================
echo.
echo 请选择启动模式:
echo.
echo [1] 只启动管理后台 (端口 8080)
echo [2] 只启动主应用   (端口 80)
echo [3] 同时启动两个应用
echo [4] 配置防火墙白名单
echo [5] 查看使用帮助
echo [0] 退出
echo.
set /p choice="请输入选项 (0-5): "

if "%choice%"=="1" goto START_ADMIN
if "%choice%"=="2" goto START_MAIN
if "%choice%"=="3" goto START_ALL
if "%choice%"=="4" goto SETUP_FIREWALL
if "%choice%"=="5" goto SHOW_HELP
if "%choice%"=="0" goto EXIT
goto MENU

:START_ADMIN
cls
echo ========================================
echo   启动管理后台
echo ========================================
echo.

REM 检查管理后台是否已运行
tasklist | find /i "python.exe" | find /i "admin_app.py" >nul
if not errorlevel 1 (
    echo [警告] 管理后台已在运行
    echo.
    pause
    goto MENU
)

echo [信息] 启动管理后台 (端口 8080)
echo.
echo 访问地址: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务
echo.

start "Dplayer Admin" cmd /k "cd /d "%~dp0" && python admin_app.py"

echo [成功] 管理后台已在后台启动
echo.
pause
goto MENU

:START_MAIN
cls
echo ========================================
echo   启动主应用
echo ========================================
echo.

REM 检查主应用是否已运行
tasklist | find /i "python.exe" | find /i "app.py" >nul
if not errorlevel 1 (
    echo [警告] 主应用已在运行
    echo.
    pause
    goto MENU
)

echo [信息] 启动主应用 (端口 80)
echo.
echo 访问地址: http://localhost:80
echo.
echo 按 Ctrl+C 停止服务
echo.

start "Dplayer Main" cmd /k "cd /d "%~dp0" && python app.py"

echo [成功] 主应用已在后台启动
echo.
pause
goto MENU

:START_ALL
cls
echo ========================================
echo   同时启动两个应用
echo ========================================
echo.

REM 检查是否已运行
tasklist | find /i "python.exe" | find /i "admin_app.py" >nul
if not errorlevel 1 (
    echo [警告] 管理后台已在运行，跳过启动
) else (
    echo [信息] 启动管理后台 (端口 8080)
    start "Dplayer Admin" cmd /k "cd /d "%~dp0" && python admin_app.py"
    timeout /t 2 /nobreak >nul
    echo [成功] 管理后台已启动
)

echo.

tasklist | find /i "python.exe" | find /i "app.py" >nul
if not errorlevel 1 (
    echo [警告] 主应用已在运行，跳过启动
) else (
    echo [信息] 启动主应用 (端口 80)
    start "Dplayer Main" cmd /k "cd /d "%~dp0" && python app.py"
    echo [成功] 主应用已启动
)

echo.
echo ========================================
echo 启动完成!
echo ========================================
echo.
echo 访问地址:
echo   主应用:   http://localhost:80
echo   管理后台: http://localhost:8080
echo.
echo 提示:
echo   - 两个应用都在后台运行
echo   - 使用任务管理器查看进程
echo   - 在管理后台可以控制主应用
echo.
pause
goto MENU

:SETUP_FIREWALL
cls
echo ========================================
echo   配置防火墙白名单
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if errorlevel 1 (
    echo [错误] 此操作需要管理员权限
    echo.
    echo 请右键点击此脚本，选择"以管理员身份运行"
    echo.
    pause
    goto MENU
)

echo [信息] 运行防火墙配置脚本
echo.

if exist "scripts\setup_firewall.ps1" (
    powershell -ExecutionPolicy Bypass -File "scripts\setup_firewall.ps1"
) else (
    echo [错误] 未找到防火墙配置脚本
    echo 请确保 scripts\setup_firewall.ps1 文件存在
)

echo.
pause
goto MENU

:SHOW_HELP
cls
echo ========================================
echo   使用帮助
echo ========================================
echo.
echo 双端口架构说明:
echo.
echo [端口 80]  - 主应用
echo   - 视频播放和浏览
echo   - 用户交互功能
echo   - 访问地址: http://localhost:80
echo.
echo [端口 8080] - 管理后台
echo   - 应用控制和监控
echo   - 数据库管理
echo   - 日志查看
echo   - 访问地址: http://localhost:8080
echo.
echo 优势:
echo   - 独立运行，互不影响
echo   - 主应用卡死可通过管理后台重启
echo   - 细粒度数据清理
echo   - 实时监控和日志
echo.
echo 防火墙配置:
echo   - 运行防火墙配置脚本添加白名单
echo   - 允许局域网设备访问
echo   - 需要管理员权限
echo.
echo 注意事项:
echo   - 确保 Python 环境已安装
echo   - 两个端口需要都可用
echo   - 建议先启动管理后台
echo.
pause
goto MENU

:EXIT
cls
echo 感谢使用 Dplayer!
echo.
timeout /t 2 /nobreak >nul
exit
