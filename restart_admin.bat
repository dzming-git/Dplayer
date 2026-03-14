@echo off
echo Stopping admin service...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do (
    echo Killing process %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo Starting admin service...
python admin_app.py
pause
