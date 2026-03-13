#!/bin/bash
# DPlayer 视频播放器启动脚本
# 用于在指定端口启动Flask服务器

echo "============================================================"
echo "           DPlayer 视频播放器启动工具"
echo "============================================================"
echo ""

# 设置端口
PORT=80

# 检查端口是否已被占用
echo "[1/4] 检查端口 $PORT 是否可用..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "[警告] 端口 $PORT 已被占用!"
    echo ""
    echo 正在查找占用该端口的进程...
    lsof -i :$PORT | grep LISTEN
    echo ""
    echo "请选择操作:"
    echo "1. 杀死占用端口的进程并启动"
    echo "2. 退出"
    read -p "请输入选项 [1-2]: " choice
    if [ "$choice" = "1" ]; then
        echo ""
        echo "正在杀死占用端口的进程..."
        PID=$(lsof -t -i:$PORT)
        if [ ! -z "$PID" ]; then
            kill -9 $PID 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "[成功] 已终止进程 $PID"
            else
                echo "[错误] 无法终止进程 $PID (可能需要sudo权限)"
                echo "请尝试: sudo kill -9 $PID"
            fi
        fi
        echo ""
        sleep 2
    else
        exit 0
    fi
else
    echo "[OK] 端口 $PORT 可用"
fi

echo ""
echo "[2/4] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[错误] 未找到Python环境!"
        echo "请确保Python已安装并添加到PATH环境变量"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD --version

echo ""
echo "[3/4] 检查依赖包..."
$PYTHON_CMD -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[警告] Flask未安装,正在尝试安装..."
    pip3 install flask flask-sqlalchemy || pip install flask flask-sqlalchemy
fi

echo ""
echo "[4/4] 启动Flask服务器..."
echo ""
echo "============================================================"
echo "服务器正在启动..."
echo "访问地址: http://127.0.0.1:$PORT"
echo "访问地址: http://localhost:$PORT"
echo "按 Ctrl+C 停止服务器"
echo "============================================================"
echo ""

# 启动Flask服务器
$PYTHON_CMD app.py
