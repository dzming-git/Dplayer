#!/bin/bash

# 管理后台启动脚本 (Linux/Mac)

echo "========================================"
echo "  Dplayer 管理后台启动脚本"
echo "========================================"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[错误] 未找到 Python 环境"
        echo "请确保 Python 已安装并添加到 PATH"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "[信息] 检测到 Python 环境"
$PYTHON_CMD --version
echo ""

# 创建日志目录
mkdir -p logs

echo "[信息] 启动管理后台..."
echo ""

echo "访问地址:"
echo "  管理后台: http://localhost:8080"
echo "  主应用:   http://localhost:80"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动管理后台 (端口 8080)
$PYTHON_CMD admin_app.py
