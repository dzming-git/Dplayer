@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
::  DPlayer Service Controller - Windows Batch Script
::  提供对DPlayer所有服务的完整控制功能
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

:: 服务名称定义
set SVC_ADMIN=DPlayer-Admin
set SVC_MAIN=DPlayer-Main
set SVC_THUMB=DPlayer-Thumbnail

:: 服务包装器脚本
set SVC_ADMIN_SCRIPT=services\admin_service.py
set SVC_MAIN_SCRIPT=services\main_service.py
set SVC_THUMB_SCRIPT=services\thumbnail_service_win.py

:: ============================================================
::  函数: 显示帮助
:: ============================================================
:show_help
echo.
echo ============================================================
echo   DPlayer Service Controller
echo ============================================================
echo.
echo 用法: service_controller.bat [操作] [服务]
echo.
echo   [操作] 必选:
echo     install        - 注册所有DPlayer服务到Windows
echo     uninstall      - 从Windows卸载所有DPlayer服务
echo     start         - 启动服务
echo     stop          - 停止服务
echo     restart       - 重启服务
echo     status        - 查询服务状态
echo     install-one    - 注册单个服务
echo     uninstall-one  - 卸载单个服务
echo.
echo   [服务] 可选(用于特定操作):
echo     admin      - 管理服务 (DPlayer-Admin)
echo     main       - 主应用服务 (DPlayer-Main)
echo     thumbnail  - 缩略图服务 (DPlayer-Thumbnail)
echo     all        - 所有DPlayer服务(默认)
echo.
echo 示例:
echo   service_controller.bat install
echo   service_controller.bat start all
echo   service_controller.bat restart admin
echo   service_controller.bat status main
echo   service_controller.bat uninstall
echo.
goto :eof

:: ============================================================
::  函数: 检查管理员权限
:: ============================================================
:check_admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] 此脚本需要管理员权限!
    echo 请右键点击脚本并选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)
exit /b 0

:: ============================================================
::  函数: 检查服务是否存在
:: ============================================================
:check_service_exists
set "SVC_NAME=%~1"
sc query "%SVC_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    exit /b 0
) else (
    exit /b 1
)

:: ============================================================
::  函数: 获取服务状态
:: ============================================================
:get_service_status
set "SVC_NAME=%~1"
sc query "%SVC_NAME%" 2>nul | findstr /i "RUNNING" >nul
if %errorLevel% equ 0 (
    echo RUNNING
) else (
    sc query "%SVC_NAME%" 2>nul | findstr /i "STOPPED" >nul
    if %errorLevel% equ 0 (
        echo STOPPED
    ) else (
        sc query "%SVC_NAME%" 2>nul | findstr /i "START_PENDING" >nul
        if %errorLevel% equ 0 (
            echo START_PENDING
        ) else (
            echo UNKNOWN
        )
    )
)
exit /b 0

:: ============================================================
::  函数: 安装所有服务
:: ============================================================
:install_all
echo.
echo ============================================================
echo   [1/2] 注册所有DPlayer服务
echo ============================================================
echo.

:: 删除旧服务(如果存在)
echo [1/3] 删除旧服务...
call :delete_service "%SVC_ADMIN%" "Admin"
call :delete_service "%SVC_MAIN%" "Main"
call :delete_service "%SVC_THUMB%" "Thumbnail"
timeout /t 2 >nul

:: 安装新服务
echo.
echo [2/3] 注册新服务...
echo.

echo 注册管理服务...
py "%SVC_ADMIN_SCRIPT%" install
if %errorLevel% neq 0 (
    echo [ERROR] 管理服务注册失败
    exit /b 1
)
echo [OK] 管理服务已注册

echo.
echo 注册主应用服务...
py "%SVC_MAIN_SCRIPT%" install
if %errorLevel% neq 0 (
    echo [ERROR] 主应用服务注册失败
    exit /b 1
)
echo [OK] 主应用服务已注册

echo.
echo 注册缩略图服务...
py "%SVC_THUMB_SCRIPT%" install
if %errorLevel% neq 0 (
    echo [ERROR] 缩略图服务注册失败
    exit /b 1
)
echo [OK] 缩略图服务已注册

:: 验证服务注册
echo.
call :verify_services

echo.
echo ============================================================
echo   注册完成!
echo ============================================================
echo.
goto :eof

:: ============================================================
::  函数: 安装单个服务
:: ============================================================
:install_one
if "%~2"=="" (
    echo [ERROR] 请指定要注册的服务: admin, main, 或 thumbnail
    exit /b 1
)

set "SVC_TYPE=%~2"
set "SVC_NAME="
set "SVC_SCRIPT="
set "SVC_LABEL="

if /i "%SVC_TYPE%"=="admin" (
    set "SVC_NAME=%SVC_ADMIN%"
    set "SVC_SCRIPT=%SVC_ADMIN_SCRIPT%"
    set "SVC_LABEL=管理服务"
) else if /i "%SVC_TYPE%"=="main" (
    set "SVC_NAME=%SVC_MAIN%"
    set "SVC_SCRIPT=%SVC_MAIN_SCRIPT%"
    set "SVC_LABEL=主应用服务"
) else if /i "%SVC_TYPE%"=="thumbnail" (
    set "SVC_NAME=%SVC_THUMB%"
    set "SVC_SCRIPT=%SVC_THUMB_SCRIPT%"
    set "SVC_LABEL=缩略图服务"
) else (
    echo [ERROR] 未知的服务类型: %SVC_TYPE%
    echo 请使用: admin, main, 或 thumbnail
    exit /b 1
)

echo.
echo ============================================================
echo   注册 %SVC_LABEL%
echo ============================================================
echo.

:: 先删除旧服务
call :delete_service "%SVC_NAME%" "%SVC_TYPE%"

:: 注册新服务
py "%SVC_SCRIPT%" install
if %errorLevel% neq 0 (
    echo [ERROR] %SVC_LABEL% 注册失败
    exit /b 1
)

echo [OK] %SVC_LABEL% 已注册

:: 验证
echo.
echo 验证服务状态...
sc query "%SVC_NAME%"

echo.
goto :eof

:: ============================================================
::  函数: 卸载所有服务
:: ============================================================
:uninstall_all
echo.
echo ============================================================
echo   [1/2] 卸载所有DPlayer服务
echo ============================================================
echo.

echo 停止所有服务...
call :stop_all_internal

echo.
echo [2/2] 卸载服务...
echo.

call :delete_service "%SVC_ADMIN%" "Admin"
call :delete_service "%SVC_MAIN%" "Main"
call :delete_service "%SVC_THUMB%" "Thumbnail"

:: 验证卸载
echo.
call :verify_services

echo.
echo ============================================================
echo   卸载完成!
echo ============================================================
echo.
goto :eof

:: ============================================================
::  函数: 卸载单个服务
:: ============================================================
:uninstall_one
if "%~2"=="" (
    echo [ERROR] 请指定要卸载的服务: admin, main, 或 thumbnail
    exit /b 1
)

set "SVC_TYPE=%~2"
set "SVC_NAME="
set "SVC_LABEL="

if /i "%SVC_TYPE%"=="admin" (
    set "SVC_NAME=%SVC_ADMIN%"
    set "SVC_LABEL=管理服务"
) else if /i "%SVC_TYPE%"=="main" (
    set "SVC_NAME=%SVC_MAIN%"
    set "SVC_LABEL=主应用服务"
) else if /i "%SVC_TYPE%"=="thumbnail" (
    set "SVC_NAME=%SVC_THUMB%"
    set "SVC_LABEL=缩略图服务"
) else (
    echo [ERROR] 未知的服务类型: %SVC_TYPE%
    echo 请使用: admin, main, 或 thumbnail
    exit /b 1
)

echo.
echo ============================================================
echo   卸载 %SVC_LABEL%
echo ============================================================
echo.

:: 停止服务
call :stop_single_service "%SVC_NAME%" "%SVC_TYPE%"

:: 删除服务
call :delete_service "%SVC_NAME%" "%SVC_TYPE%"

echo.
echo [OK] %SVC_LABEL% 已卸载
goto :eof

:: ============================================================
::  函数: 删除服务(内部)
:: ============================================================
:delete_service
set "SVC_NAME=%~1"
set "SVC_LABEL=%~2"

sc delete "%SVC_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] %SVC_NAME% 已删除(旧服务)
) else (
    if "%SVC_LABEL%"=="%SVC_LABEL%" (
        :: 忽略删除失败(可能服务不存在)
    )
)
exit /b 0

:: ============================================================
::  函数: 启动所有服务
:: ============================================================
:start_all
echo.
echo ============================================================
echo   启动所有DPlayer服务
echo ============================================================
echo.

call :start_single_service "%SVC_ADMIN%" "Admin" "管理服务"
call :start_single_service "%SVC_MAIN%" "Main" "主应用服务"
call :start_single_service "%SVC_THUMB%" "Thumbnail" "缩略图服务"

echo.
echo ============================================================
echo   所有服务启动命令已执行
echo ============================================================
echo.

:: 验证服务状态
call :verify_services

goto :eof

:: ============================================================
::  函数: 启动单个服务
:: ============================================================
:start_single_service
set "SVC_NAME=%~1"
set "SVC_TYPE=%~2"
set "SVC_LABEL=%~3"

echo [%SVC_TYPE%] 启动 %SVC_LABEL%...

:: 检查服务是否已注册
sc query "%SVC_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARN] %SVC_NAME% 未注册, 请先运行: service_controller.bat install %SVC_TYPE%
    exit /b 1
)

:: 启动服务
sc start "%SVC_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] %SVC_LABEL% 启动中...

    :: 等待服务启动
    timeout /t 3 >nul

    :: 验证状态
    for /L %%i in (1,1,10) do (
        call :get_service_status "%SVC_NAME%" >nul
        set /p "STATUS=" <nul

        if "!STATUS!"=="RUNNING" (
            echo [OK] %SVC_LABEL% 已启动
            exit /b 0
        )
        timeout /t 1 >nul
    )

    echo [WARN] %SVC_LABEL% 启动超时, 请检查日志
) else (
    echo [ERROR] %SVC_LABEL% 启动失败
    sc query "%SVC_NAME%"
)
exit /b 0

:: ============================================================
::  函数: 停止所有服务
:: ============================================================
:stop_all
echo.
echo ============================================================
echo   停止所有DPlayer服务
echo ============================================================
echo.

call :stop_all_internal

echo.
echo ============================================================
echo   所有服务停止命令已执行
echo ============================================================
echo.

:: 验证服务状态
call :verify_services

goto :eof

:: ============================================================
::  函数: 停止所有服务(内部)
:: ============================================================
:stop_all_internal
call :stop_single_service "%SVC_ADMIN%" "Admin" "管理服务"
call :stop_single_service "%SVC_MAIN%" "Main" "主应用服务"
call :stop_single_service "%SVC_THUMB%" "Thumbnail" "缩略图服务"
exit /b 0

:: ============================================================
::  函数: 停止单个服务
:: ============================================================
:stop_single_service
set "SVC_NAME=%~1"
set "SVC_TYPE=%~2"
set "SVC_LABEL=%~3"

echo [%SVC_TYPE%] 停止 %SVC_LABEL%...

:: 检查服务是否存在
sc query "%SVC_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] %SVC_NAME% 未注册, 跳过
    exit /b 0
)

:: 停止服务
sc stop "%SVC_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] %SVC_LABEL% 停止中...

    :: 等待服务停止
    timeout /t 3 >nul

    :: 验证状态
    for /L %%i in (1,1,10) do (
        call :get_service_status "%SVC_NAME%" >nul
        set /p "STATUS=" <nul

        if "!STATUS!"=="STOPPED" (
            echo [OK] %SVC_LABEL% 已停止
            exit /b 0
        )
        if "!STATUS!"=="RUNNING" (
            :: 仍在运行, 继续等待
        ) else (
            :: 状态未知, 假定已停止
            echo [OK] %SVC_LABEL% 已停止
            exit /b 0
        )
        timeout /t 1 >nul
    )

    echo [WARN] %SVC_LABEL% 停止超时
) else (
    :: 检查是否已经停止
    sc query "%SVC_NAME%" 2>nul | findstr /i "STOPPED" >nul
    if %errorLevel% equ 0 (
        echo [INFO] %SVC_LABEL% 已经停止
    ) else (
        echo [ERROR] %SVC_LABEL% 停止失败
        sc query "%SVC_NAME%"
    )
)
exit /b 0

:: ============================================================
::  函数: 重启所有服务
:: ============================================================
:restart_all
echo.
echo ============================================================
echo   重启所有DPlayer服务
echo ============================================================
echo.

call :restart_single_service "%SVC_ADMIN%" "Admin" "管理服务"
call :restart_single_service "%SVC_MAIN%" "Main" "主应用服务"
call :restart_single_service "%SVC_THUMB%" "Thumbnail" "缩略图服务"

echo.
echo ============================================================
echo   所有服务重启命令已执行
echo ============================================================
echo.

:: 验证服务状态
call :verify_services

goto :eof

:: ============================================================
::  函数: 重启单个服务
:: ============================================================
:restart_single_service
set "SVC_NAME=%~1"
set "SVC_TYPE=%~2"
set "SVC_LABEL=%~3"

echo.
echo [%SVC_TYPE%] 重启 %SVC_LABEL%...
echo ------------------------------------------------------------
echo.

:: 先停止
call :stop_single_service "%SVC_NAME%" "%SVC_TYPE%" "%SVC_LABEL%"

:: 等待完全停止
timeout /t 2 >nul

:: 再启动
echo.
call :start_single_service "%SVC_NAME%" "%SVC_TYPE%" "%SVC_LABEL%"

echo.
exit /b 0

:: ============================================================
::  函数: 查询服务状态
:: ============================================================
:status_all
echo.
echo ============================================================
echo   DPlayer 服务状态
echo ============================================================
echo.

call :status_single_service "%SVC_ADMIN%" "Admin" "管理服务" "8080"
echo.
call :status_single_service "%SVC_MAIN%" "Main" "主应用服务" "80"
echo.
call :status_single_service "%SVC_THUMB%" "Thumbnail" "缩略图服务" "5001"

echo.
goto :eof

:: ============================================================
::  函数: 查询单个服务状态
:: ============================================================
:status_single_service
set "SVC_NAME=%~1"
set "SVC_TYPE=%~2"
set "SVC_LABEL=%~3"
set "SVC_PORT=%~4"

echo ============================================================
echo %SVC_LABEL% (%SVC_NAME%)
echo ============================================================

:: 检查服务是否注册
sc query "%SVC_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo [NOT REGISTERED] 服务未注册
    goto :eof
)

:: 获取详细状态
sc query "%SVC_NAME%" 2>nul | findstr /i "STATE" >nul
if %errorLevel% equ 0 (
    for /f "tokens=2" %%a in ('sc query "%SVC_NAME%" ^| findstr /i "STATE"') do (
        set "STATE=%%a"
    )
)

echo 状态: %STATE%
echo 端口: %SVC_PORT%

:: 检查端口监听
netstat -ano | findstr ":%SVC_PORT% " >nul 2>&1
if %errorLevel% equ 0 (
    echo 端口监听: [OK]
) else (
    echo 端口监听: [未监听]
)

exit /b 0

:: ============================================================
::  函数: 验证所有服务状态
:: ============================================================
:verify_services
echo.
echo ============================================================
echo   验证服务状态
echo ============================================================
echo.

call :status_single_service "%SVC_ADMIN%" "Admin" "管理服务" "8080"
echo.
call :status_single_service "%SVC_MAIN%" "Main" "主应用服务" "80"
echo.
call :status_single_service "%SVC_THUMB%" "Thumbnail" "缩略图服务" "5001"

echo.
goto :eof

:: ============================================================
::  主程序入口
:: ============================================================

:: 检查管理员权限
call :check_admin

:: 检查参数
if "%~1"=="" (
    goto :show_help
)

set "COMMAND=%~1"
set "SVC_ARG=%~2"

:: 根据命令执行操作
if /i "%COMMAND%"=="help" (
    goto :show_help
) else if /i "%COMMAND%"=="install" (
    call :install_all
) else if /i "%COMMAND%"=="install-one" (
    call :install_one %SVC_ARG%
) else if /i "%COMMAND%"=="uninstall" (
    call :uninstall_all
) else if /i "%COMMAND%"=="uninstall-one" (
    call :uninstall_one %SVC_ARG%
) else if /i "%COMMAND%"=="start" (
    if "%SVC_ARG%"=="" (
        call :start_all
    ) else (
        call :start_single_service "%SVC_NAME%" "%SVC_TYPE%" "%SVC_LABEL%"
        call :verify_services
    )
) else if /i "%COMMAND%"=="stop" (
    if "%SVC_ARG%"=="" (
        call :stop_all
    ) else (
        call :stop_single_service "%SVC_NAME%" "%SVC_TYPE%" "%SVC_LABEL%"
        call :verify_services
    )
) else if /i "%COMMAND%"=="restart" (
    if "%SVC_ARG%"=="" (
        call :restart_all
    ) else (
        call :restart_single_service "%SVC_NAME%" "%SVC_TYPE%" "%SVC_LABEL%"
        call :verify_services
    )
) else if /i "%COMMAND%"=="status" (
    if "%SVC_ARG%"=="" (
        call :status_all
    ) else (
        call :status_single_service "%SVC_NAME%" "%SVC_TYPE%" "%SVC_LABEL%" "%SVC_PORT%"
    )
) else (
    echo [ERROR] 未知命令: %COMMAND%
    echo.
    goto :show_help
)

echo.
echo 操作完成!
echo.
pause
