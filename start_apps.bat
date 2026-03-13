@echo off
cd /d c:\Users\71555\WorkBuddy\Dplayer

echo Stopping existing Python processes...
wmic process where "name='python.exe'" delete

echo Waiting for processes to stop...
timeout /t 3 /nobreak > nul

echo Starting main application...
start /B python app.py

echo Waiting for main app to start...
timeout /t 3 /nobreak > nul

echo Starting admin dashboard...
start /B python admin_app.py

echo Waiting for admin app to start...
timeout /t 3 /nobreak > nul

echo Checking processes...
tasklist | findstr python

echo.
echo Services started!
echo Main app: http://127.0.0.1:80
echo Admin dashboard: http://127.0.0.1:8080
