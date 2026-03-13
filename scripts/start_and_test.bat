@echo off
cd /d %~dp0
echo Starting admin app on port 8080...
start /B python admin_app.py

echo Starting main app on port 80...
start /B python app.py

echo Waiting 5 seconds for services to initialize...
ping 127.0.0.1 -n 6 >nul

echo Testing services...
python test_quick.py

pause
