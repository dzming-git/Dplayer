#!/bin/bash

echo "========================================"
echo "安装 DPlayer 视频站依赖"
echo "========================================"
echo

echo "[1/3] 检查 Python 环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到 Python，请先安装 Python"
    exit 1
fi
echo

echo "[2/3] 升级 pip..."
python3 -m pip install --upgrade pip
echo

echo "[3/3] 安装依赖包..."
pip3 install Flask Flask-SQLAlchemy SQLAlchemy Pillow requests opencv-python-headless imageio imageio-ffmpeg
echo

if [ $? -eq 0 ]; then
    echo "========================================"
    echo "✓ 依赖安装成功！"
    echo "========================================"
    echo
    echo "已安装的包："
    echo "- Flask (Web 框架)"
    echo "- Flask-SQLAlchemy (数据库 ORM)"
    echo "- Pillow (图像处理)"
    echo "- opencv-python-headless (视频处理)"
    echo "- imageio (GIF 生成)"
    echo "- imageio-ffmpeg (视频解码)"
    echo
    echo "现在可以运行 python3 app.py 启动服务器了"
else
    echo "========================================"
    echo "✗ 依赖安装失败"
    echo "========================================"
    echo
    echo "请尝试以下方法："
    echo "1. 使用国内镜像源安装："
    echo "   pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
    echo "2. 或手动安装每个包"
    exit 1
fi

echo
