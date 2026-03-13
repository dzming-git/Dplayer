@echo off
chcp 65001 >nul
echo DPlayer 服务启动配置查看
echo ================================================
echo.

echo 检查服务安装状态和启动配置...
echo.

echo ================================================
echo 1. DPlayer-Admin 服务
echo ================================================
sc query DPlayer-Admin 2>nul
if %errorlevel% neq 0 (
    echo [错误] 服务未安装
) else (
    echo.
    echo 启动配置:
    sc qc DPlayer-Admin | findstr "START_TYPE DISPLAY_NAME DESCRIPTION"
)
echo.

echo ================================================
echo 2. DPlayer-Main 服务
echo ================================================
sc query DPlayer-Main 2>nul
if %errorlevel% neq 0 (
    echo [错误] 服务未安装
) else (
    echo.
    echo 启动配置:
    sc qc DPlayer-Main | findstr "START_TYPE DISPLAY_NAME DESCRIPTION"
)
echo.

echo ================================================
echo 3. DPlayer-Thumbnail 服务
echo ================================================
sc query DPlayer-Thumbnail 2>nul
if %errorlevel% neq 0 (
    echo [错误] 服务未安装
) else (
    echo.
    echo 启动配置:
    sc qc DPlayer-Thumbnail | findstr "START_TYPE DISPLAY_NAME DESCRIPTION"
)
echo.

echo ================================================
echo 启动类型说明:
echo ================================================
echo AUTO_START     (2) - 自动启动 (开机自启)
echo DEMAND_START   (3) - 手动启动 (需要手动启动)
echo DISABLED       (4) - 已禁用
echo.
pause
