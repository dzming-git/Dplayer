@echo off
chcp 65001 >nul
echo ============================================================
echo   Stop All DPlayer Services
echo ============================================================
echo.

cd /d "%~dp0.."

echo [1/3] Stopping DPlayer-Admin service...
python services/admin_service.py stop
echo.

echo [2/3] Stopping DPlayer-Main service...
python services/main_service.py stop
echo.

echo [3/3] Stopping DPlayer-Thumbnail service...
python services/thumbnail_service_win.py stop
echo.

echo ============================================================
echo   All service stop commands executed
echo ============================================================
echo.

pause
