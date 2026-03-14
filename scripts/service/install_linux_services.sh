#!/bin/bash
# DPlayer Linux 系统服务安装脚本
# 将 systemd 单元文件复制到 /etc/systemd/system/ 并 enable
# 需要 root 权限运行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASEDIR="$(dirname "$SCRIPT_DIR")"
SYSTEMD_DIR="/etc/systemd/system"
INSTALL_DIR="/opt/dplayer"
SERVICE_USER="${DPLAYER_USER:-www-data}"

echo "============================================================"
echo " DPlayer 服务安装脚本 (Linux / systemd)"
echo " 项目目录: $BASEDIR"
echo " 安装目录: $INSTALL_DIR"
echo " 运行用户: $SERVICE_USER"
echo "============================================================"
echo

# 检查 root
if [ "$EUID" -ne 0 ]; then
    echo "[错误] 请以 root 身份运行: sudo $0"
    exit 1
fi

# 检查 systemd
if ! command -v systemctl &> /dev/null; then
    echo "[错误] 未找到 systemctl，此脚本需要 systemd"
    exit 1
fi

PYTHON_BIN=$(which python3 || which python)
echo "[信息] Python: $PYTHON_BIN"

# 确保安装目录存在，若项目不在 /opt/dplayer，创建软链接
if [ "$BASEDIR" != "$INSTALL_DIR" ]; then
    echo "[信息] 创建软链接 $INSTALL_DIR -> $BASEDIR"
    ln -sfn "$BASEDIR" "$INSTALL_DIR"
fi

# 确保日志目录存在
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/instance"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR/logs" "$INSTALL_DIR/instance" 2>/dev/null || true

# ---- 生成并安装三个 unit 文件 ----
install_service() {
    local name=$1
    local script=$2
    local desc=$3
    local extra_env=${4:-""}

    local unit_file="$SYSTEMD_DIR/${name}.service"
    echo "[信息] 安装 $name ..."

    cat > "$unit_file" << EOF
[Unit]
Description=$desc
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_BIN $INSTALL_DIR/$script
ExecStop=/bin/kill -TERM \$MAINPID
Restart=on-failure
RestartSec=5s
StartLimitIntervalSec=60
StartLimitBurst=5
StandardOutput=append:$INSTALL_DIR/logs/${name#dplayer-}.log
StandardError=append:$INSTALL_DIR/logs/${name#dplayer-}.log
Environment=FLASK_ENV=production
Environment=PYTHONUNBUFFERED=1
$extra_env

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$name"
    echo "  ✔ $name 已安装并设为开机自启"
}

install_service "dplayer-thumbnail" "services/thumbnail_service.py" \
    "DPlayer 缩略图微服务" \
    "Environment=THUMBNAIL_SERVICE_PORT=5001"

install_service "dplayer-main" "app.py" \
    "DPlayer 主应用"

install_service "dplayer-admin" "admin_app.py" \
    "DPlayer 管理后台"

echo
echo "============================================================"
echo " 安装完成！常用命令："
echo
echo "   # 使用 process_manager.py（推荐）："
echo "   python3 $INSTALL_DIR/process_manager.py start   all"
echo "   python3 $INSTALL_DIR/process_manager.py status"
echo "   python3 $INSTALL_DIR/process_manager.py restart thumbnail"
echo
echo "   # 或直接使用 systemctl："
echo "   systemctl start   dplayer-main"
echo "   systemctl stop    dplayer-admin"
echo "   systemctl restart dplayer-thumbnail"
echo "   systemctl status  dplayer-main"
echo "   journalctl -u dplayer-main -f    # 查看实时日志"
echo "============================================================"
