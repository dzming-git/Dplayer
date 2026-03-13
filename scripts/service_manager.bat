@echo off
::: DPlayer Service Manager
::: 使用 gevent WSGI + pywin32 方案

echo ============================================================
echo   DPlayer Service Manager (gevent WSGI)
echo ============================================================
echo.

::: Check administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges.
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

::: 处理命令
if "%1"=="install" (
    echo Installing services...
    python "%~dp0install_windows_services.py"
) else if "%1"=="uninstall" (
    echo Uninstalling services...
    python services\admin_service.py remove
    python services/main_service.py remove
    python services/thumbnail_service_win.py remove
) else if "%1"=="start" (
    echo Starting services...
    python services\admin_service.py start
    python services/main_service.py start
    python services/thumbnail_service_win.py start
) else if "%1"=="stop" (
    echo Stopping services...
    python services\admin_service.py stop
    python services/main_service.py stop
    python services/thumbnail_service_win.py stop
) else if "%1"=="restart" (
    echo Restarting services...
    python services\admin_service.py restart
    python services/main_service.py restart
    python services/thumbnail_service_win.py restart
) else if "%1"=="status" (
    echo Checking service status...
    python "%~dp0check_services.py"
) else (
    echo Usage:
    echo   service_manager.bat install   - Install services
    echo   service_manager.bat start     - Start services
    echo   service_manager.bat stop      - Stop services
    echo   service_manager.bat restart   - Restart services
    echo   service_manager.bat uninstall - Uninstall services
    echo   service_manager.bat status    - Check service status
    echo.
    echo Examples:
    echo   service_manager.bat install
    echo   service_manager.bat start
)

pause
