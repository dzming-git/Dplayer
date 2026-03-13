@echo off
chcp 65001 >nul
echo 禁用 DPlayer 服务开机自启动
echo ================================================
echo.
echo IMPORTANT: Run this script as ADMINISTRATOR
echo.
pause

cd /d "%~dp0"

echo [1/3] 设置 DPlayer-Admin 服务为手动启动...
sc config DPlayer-Admin start= demand
if %errorlevel% equ 0 (
    echo    ✓ DPlayer-Admin 启动模式已设置为 DEMAND (手动)
) else (
    echo    ✗ 设置失败
)
timeout /t 1 >nul

echo [2/3] 设置 DPlayer-Main 服务为手动启动...
sc config DPlayer-Main start= demand
if %errorlevel% equ 0 (
    echo    ✓ DPlayer-Main 启动模式已设置为 DEMAND (手动)
) else (
    echo    ✗ 设置失败
)
timeout /t 1 >nul

echo [3/3] 设置 DPlayer-Thumbnail 服务为手动启动...
sc config DPlayer-Thumbnail start= demand
if %errorlevel% equ 0 (
    echo    ✓ DPlayer-Thumbnail 启动模式已设置为 DEMAND (手动)
) else (
    echo    ✗ 设置失败
)
timeout /t 1 >nul

echo.
echo ================================================
echo 验证服务启动配置...
echo.

echo DPlayer-Admin:
sc qc DPlayer-Admin | findstr START_TYPE
echo.

echo DPlayer-Main:
sc qc DPlayer-Main | findstr START_TYPE
echo.

echo DPlayer-Thumbnail:
sc qc DPlayer-Thumbnail | findstr START_TYPE
echo.

echo ================================================
echo 配置完成！
echo.
echo 说明：
echo - 所有服务已设置为手动启动
echo - 启动类型: DEMAND_START (3)
echo - 需要手动启动服务或使用启动脚本
echo.
pause
