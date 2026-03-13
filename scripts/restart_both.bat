@echo off
echo Stopping all services...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo Starting admin app...
start /B python admin_app.py

echo Starting main app...
start /B python app.py

echo Waiting for services to start...
timeout /t 5 /nobreak >nul

echo Services started
