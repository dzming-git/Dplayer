@echo off
chcp 65001 >nul
echo ============================================================
echo   重启所有 DPlayer 服务
echo ============================================================
echo.

set PYTHON=C:\Users\71555\AppData\Local\Programs\Python\Python311\python.exe
cd /d "C:\Users\71555\WorkBuddy\Dplayer"

echo [1/4] 正在停止现有服务...
echo.

echo   停止端口 80 (Main)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":80 " ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo   停止端口 8080 (Admin)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 " ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo   停止端口 5001 (Thumbnail)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001 " ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1

echo.
echo [2/4] 等待端口释放...
timeout /t 2 /nobreak >nul

echo.
echo [3/4] 正在启动服务...
echo.

echo   启动主应用 (端口 80)...
start "Dplayer-Main" cmd /k "cd /d C:\Users\71555\WorkBuddy\Dplayer && %PYTHON% app.py"

echo   启动管理后台 (端口 8080)...
start "Dplayer-Admin" cmd /k "cd /d C:\Users\71555\WorkBuddy\Dplayer && %PYTHON% admin_app.py"

echo   启动缩略图服务 (端口 5001)...
start "Dplayer-Thumbnail" cmd /k "cd /d C:\Users\71555\WorkBuddy\Dplayer && %PYTHON% services\thumbnail_service.py"

echo.
echo [4/4] 等待服务启动...
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo   服务已重启完成！
echo ============================================================
echo.
echo 访问地址:
echo   - 主应用: http://localhost:80
echo   - 管理后台: http://localhost:8080
echo   - 缩略图服务: http://localhost:5001
echo.

pause
