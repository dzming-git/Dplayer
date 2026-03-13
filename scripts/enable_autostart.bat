@echo off
chcp 65001 >nul
echo 设置 DPlayer 服务开机自启动
echo ================================================
echo.
echo IMPORTANT: Run this script as ADMINISTRATOR
echo.
pause

cd /d "%~dp0"

echo [1/3] 设置 DPlayer-Admin 服务为自动启动...
sc config DPlayer-Admin start= auto
if %errorlevel% equ 0 (
    echo    ✓ DPlayer-Admin 启动模式已设置为 AUTO
) else (
    echo    ✗ 设置失败
)
timeout /t 1 >nul

echo [2/3] 设置 DPlayer-Main 服务为自动启动...
sc config DPlayer-Main start= auto
if %errorlevel% equ 0 (
    echo    ✓ DPlayer-Main 启动模式已设置为 AUTO
) else (
    echo    ✗ 设置失败
)
timeout /t 1 >nul

echo [3/3] 设置 DPlayer-Thumbnail 服务为自动启动...
sc config DPlayer-Thumbnail start= auto
if %errorlevel% equ 0 (
    echo    ✓ DPlayer-Thumbnail 启动模式已设置为 AUTO
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
echo - 所有服务已设置为开机自动启动
echo - 启动类型: AUTO_START (2)
echo.
echo 验证方法：
echo - 重启电脑后检查服务是否自动启动
echo - 使用: sc query DPlayer-Admin
echo.
pause
