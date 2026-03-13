@echo off
chcp 65001 >nul
echo ============================================================
echo   DPlayer 服务管理 - 快捷方式
echo ============================================================
echo.
echo 1. 服务控制（批处理版本）
echo.
echo    status     - 查看所有服务状态
echo    start all  - 启动所有服务
echo    stop all   - 停止所有服务
echo    restart all - 重启所有服务
echo.
echo 2. 服务控制（PowerShell版本）
echo.
echo    ps1 status     - 查看所有服务状态
echo    ps1 start all  - 启动所有服务
echo    ps1 stop all   - 停止所有服务
echo    ps1 restart all - 重启所有服务
echo.
echo 3. 验证脚本
echo.
echo    verify      - 验证脚本和服务状态
echo.
echo 4. 服务安装
echo.
echo    install      - 安装所有服务
echo.
echo 5. 其他
echo.
echo    install_services.bat  - 原始安装脚本
echo    restart_services.py   - Python重启脚本
echo.
echo ============================================================
echo.
set /p CHOICE=请选择操作:

if "%CHOICE%"=="status" (
    scripts\service_controller.bat status
) else if "%CHOICE%"=="start all" (
    scripts\service_controller.bat start all
) else if "%CHOICE%"=="stop all" (
    scripts\service_controller.bat stop all
) else if "%CHOICE%"=="restart all" (
    scripts\service_controller.bat restart all
) else if "%CHOICE%"=="ps1 status" (
    powershell -ExecutionPolicy Bypass -File scripts\service_controller.ps1 status
) else if "%CHOICE%"=="ps1 start all" (
    powershell -ExecutionPolicy Bypass -File scripts\service_controller.ps1 start all
) else if "%CHOICE%"=="ps1 stop all" (
    powershell -ExecutionPolicy Bypass -File scripts\service_controller.ps1 stop all
) else if "%CHOICE%"=="ps1 restart all" (
    powershell -ExecutionPolicy Bypass -File scripts\service_controller.ps1 restart all
) else if "%CHOICE%"=="verify" (
    python scripts\verify_controller.py
) else if "%CHOICE%"=="install" (
    scripts\install_services.bat
) else if "%CHOICE%"=="install_services" (
    scripts\install_services.bat
) else if "%CHOICE%"=="restart_services" (
    echo 用法: python scripts\restart_services.py [admin^|main^|thumbnail^|all]
    pause
) else (
    echo 无效的选择: %CHOICE%
    pause
)
