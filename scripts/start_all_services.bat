@echo off
chcp 65001 >nul
echo ============================================================
echo   Start All DPlayer Services
echo ============================================================
echo.

cd /d "%~dp0.."

echo [1/3] Starting DPlayer-Admin service...
python services/admin_service.py start
echo.

echo [2/3] Starting DPlayer-Main service...
python services/main_service.py start
echo.

echo [3/3] Starting DPlayer-Thumbnail service...
python services/thumbnail_service_win.py start
echo.

echo ============================================================
echo   All service start commands executed
echo ============================================================
echo.
echo Check service status:
echo   services\check_services.bat
echo.
echo Stop all services:
echo   services\stop_all_services.bat
echo.

pause
