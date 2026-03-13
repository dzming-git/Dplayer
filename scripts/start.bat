@echo off
REM DPlayer 视频播放器启动脚本
REM 用于在指定端口启动Flask服务器

echo ============================================================
echo            DPlayer 视频播放器启动工具
echo ============================================================
echo.

REM 设置端口
set PORT=80

REM 检查端口是否已被占用
echo [1/4] 检查端口 %PORT% 是否可用...
netstat -ano | findstr :%PORT% >nul
if %errorlevel% == 0 (
    echo [警告] 端口 %PORT% 已被占用!
    echo.
    echo 正在查找占用该端口的进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT%') do (
        echo 进程ID: %%a
        tasklist /fi "PID eq %%a" /nh
    )
    echo.
    echo 请选择操作:
    echo 1. 杀死占用端口的进程并启动
    echo 2. 退出
    choice /c 12 /n /m "请输入选项 [1-2]: "
    if errorlevel 2 goto :end
    if errorlevel 1 (
        echo.
        echo 正在杀死占用端口的进程...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT%') do (
            taskkill /F /PID %%a >nul 2>&1
            if !errorlevel! == 0 (
                echo [成功] 已终止进程 %%a
            ) else (
                echo [错误] 无法终止进程 %%a (可能需要管理员权限)
            )
        )
        echo.
        timeout /t 2 >nul
    )
) else (
    echo [OK] 端口 %PORT% 可用
)

echo.
echo [2/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python环境!
    echo 请确保Python已安装并添加到PATH环境变量
    pause
    exit /b 1
)
python --version

echo.
echo [3/4] 检查依赖包...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] Flask未安装,正在尝试安装...
    pip install flask flask-sqlalchemy
)

echo.
echo [4/4] 启动Flask服务器...
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

echo ============================================================
echo 服务器正在启动...
echo 访问地址: http://127.0.0.1:%PORT%
echo 访问地址: http://localhost:%PORT%
echo 按 Ctrl+C 停止服务器
echo ============================================================
echo.

REM 启动Flask服务器
python app.py

:end
echo.
echo 程序已退出
pause
