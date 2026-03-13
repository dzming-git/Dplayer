@echo off
chcp 65001 >nul
echo Installing DPlayer Services with Python 3.11
echo ================================================
echo.
echo IMPORTANT: Run this script as ADMINISTRATOR
echo.
pause

cd /d "%~dp0"

echo [1/3] Removing old services...
sc delete DPlayer-Admin 2>nul
sc delete DPlayer-Main 2>nul
sc delete DPlayer-Thumbnail 2>nul
timeout /t 2 >nul
echo.

echo [2/3] Installing new services with Python 3.11...
py services\admin_service.py install
py services\main_service.py install
py services\thumbnail_service_win.py install
echo.

echo [3/3] Starting services...
py services\admin_service.py start
py services\main_service.py start
py services\thumbnail_service_win.py start
echo.

echo Checking service status...
echo.
sc query DPlayer-Admin
echo.
sc query DPlayer-Main
echo.
sc query DPlayer-Thumbnail
echo.
echo ================================================
echo Installation complete!
echo.
pause
