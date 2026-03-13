@echo off
cd /d c:\Users\71555\WorkBuddy\Dplayer

echo Finding admin app process...
netstat -ano | findstr :8080

echo.
echo Stopping admin app...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    echo Killing process %%a
    taskkill /F /PID %%a
)

timeout /t 2 /nobreak > nul

echo Starting admin app...
start /B python admin_app.py

timeout /t 3 /nobreak > nul

echo Checking admin app status...
netstat -ano | findstr :8080

echo.
echo Admin app restarted!
