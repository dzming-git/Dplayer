@echo off
chcp 65001 >nul
echo ========================================
echo 安装 DPlayer 视频站依赖
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)
echo.

echo [2/3] 升级 pip...
python -m pip install --upgrade pip
echo.

echo [3/3] 安装依赖包...
pip install Flask Flask-SQLAlchemy SQLAlchemy Pillow requests opencv-python imageio imageio-ffmpeg
echo.

if %errorlevel% equ 0 (
    echo ========================================
    echo ✓ 依赖安装成功！
    echo ========================================
    echo.
    echo 已安装的包：
    echo - Flask (Web 框架)
    echo - Flask-SQLAlchemy (数据库 ORM)
    echo - Pillow (图像处理)
    echo - opencv-python (视频处理)
    echo - imageio (GIF 生成)
    echo - imageio-ffmpeg (视频解码)
    echo.
    echo 现在可以运行 start_server.bat 启动服务器了
) else (
    echo ========================================
    echo ✗ 依赖安装失败
    echo ========================================
    echo.
    echo 请尝试以下方法：
    echo 1. 使用国内镜像源安装：
    echo    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo 2. 或手动安装每个包
)

echo.
pause
