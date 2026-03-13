#!/bin/bash

# Linux/Mac 防火墙配置脚本
# 自动为 Dplayer 应用端口添加防火墙白名单

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 端口配置
MAIN_APP_PORT=80
ADMIN_PORT=8080

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Dplayer 防火墙配置脚本${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo -e "${GREEN}✅ 检测到 Linux 系统${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo -e "${GREEN}✅ 检测到 macOS 系统${NC}"
else
    echo -e "${RED}❌ 错误: 不支持的操作系统${NC}"
    exit 1
fi

echo ""

# 显示当前配置
echo -e "${CYAN}配置信息:${NC}"
echo -e "${WHITE}  主应用端口: $MAIN_APP_PORT (http://0.0.0.0:$MAIN_APP_PORT)${NC}"
echo -e "${WHITE}  管理端口: $ADMIN_PORT (http://0.0.0.0:$ADMIN_PORT)${NC}"
echo ""

# 获取本机IP地址
echo -e "${YELLOW}正在获取本机IP地址...${NC}"

if command -v ip &> /dev/null; then
    # Linux 使用 ip 命令
    IP_ADDRESSES=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1')
elif command -v ifconfig &> /dev/null; then
    # macOS 或旧版 Linux 使用 ifconfig
    IP_ADDRESSES=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
else
    echo -e "${YELLOW}⚠️  警告: 无法获取IP地址${NC}"
    IP_ADDRESSES=""
fi

echo ""

if [ -n "$IP_ADDRESSES" ]; then
    echo -e "${GREEN}本机IP地址:${NC}"
    while IFS= read -r ip; do
        echo -e "${WHITE}  • $ip${NC}"
        echo -e "${CYAN}    主应用: http://$ip:$MAIN_APP_PORT${NC}"
        echo -e "${CYAN}    管理后台: http://$ip:$ADMIN_PORT${NC}"
        echo ""
    done <<< "$IP_ADDRESSES"
else
    echo -e "${YELLOW}⚠️  警告: 未找到有效的IP地址${NC}"
    echo ""
fi

# 配置防火墙规则
echo -e "${YELLOW}配置防火墙规则...${NC}"
echo ""

if [ "$OS" == "linux" ]; then
    # Linux 防火墙配置 (使用 ufw)
    if command -v ufw &> /dev/null; then
        echo -e "${WHITE}使用 UFW 配置防火墙...${NC}"
        echo ""

        # 配置主应用端口
        echo -e "${WHITE}检查主应用端口规则 ($MAIN_APP_PORT)...${NC}"
        ufw allow $MAIN_APP_PORT/tcp comment "Dplayer Main App Port" &> /dev/null
        echo -e "${GREEN}  ✅ 主应用端口规则已添加${NC}"
        echo ""

        # 配置管理后台端口
        echo -e "${WHITE}检查管理后台端口规则 ($ADMIN_PORT)...${NC}"
        ufw allow $ADMIN_PORT/tcp comment "Dplayer Admin Dashboard Port" &> /dev/null
        echo -e "${GREEN}  ✅ 管理后台端口规则已添加${NC}"
        echo ""

        # 显示 UFW 状态
        echo -e "${CYAN}========================================${NC}"
        echo -e "${CYAN}防火墙规则配置完成${NC}"
        echo -e "${CYAN}========================================${NC}"
        echo ""
        echo -e "${GREEN}UFW 状态:${NC}"
        echo ""
        ufw status numbered
        echo ""

    elif command -v firewall-cmd &> /dev/null; then
        # 使用 firewalld
        echo -e "${WHITE}使用 firewalld 配置防火墙...${NC}"
        echo ""

        # 检查 firewalld 是否运行
        if systemctl is-active --quiet firewalld; then
            # 配置主应用端口
            echo -e "${WHITE}检查主应用端口规则 ($MAIN_APP_PORT)...${NC}"
            firewall-cmd --permanent --add-port=$MAIN_APP_PORT/tcp --zone=public &> /dev/null
            firewall-cmd --reload &> /dev/null
            echo -e "${GREEN}  ✅ 主应用端口规则已添加${NC}"
            echo ""

            # 配置管理后台端口
            echo -e "${WHITE}检查管理后台端口规则 ($ADMIN_PORT)...${NC}"
            firewall-cmd --permanent --add-port=$ADMIN_PORT/tcp --zone=public &> /dev/null
            firewall-cmd --reload &> /dev/null
            echo -e "${GREEN}  ✅ 管理后台端口规则已添加${NC}"
            echo ""

            # 显示 firewalld 状态
            echo -e "${CYAN}========================================${NC}"
            echo -e "${CYAN}防火墙规则配置完成${NC}"
            echo -e "${CYAN}========================================${NC}"
            echo ""
            echo -e "${GREEN}firewalld 状态:${NC}"
            echo ""
            firewall-cmd --list-all | grep -A 20 "ports"
            echo ""
        else
            echo -e "${RED}❌ 错误: firewalld 未运行${NC}"
            echo -e "${YELLOW}请启动 firewalld: sudo systemctl start firewalld${NC}"
            exit 1
        fi

    else
        echo -e "${YELLOW}⚠️  警告: 未检测到 UFW 或 firewalld${NC}"
        echo -e "${WHITE}请手动配置防火墙规则${NC}"
        echo ""
        echo -e "${CYAN}UFW 示例:${NC}"
        echo -e "${WHITE}  sudo ufw allow $MAIN_APP_PORT/tcp${NC}"
        echo -e "${WHITE}  sudo ufw allow $ADMIN_PORT/tcp${NC}"
        echo ""
        echo -e "${CYAN}firewalld 示例:${NC}"
        echo -e "${WHITE}  sudo firewall-cmd --permanent --add-port=$MAIN_APP_PORT/tcp${NC}"
        echo -e "${WHITE}  sudo firewall-cmd --permanent --add-port=$ADMIN_PORT/tcp${NC}"
        echo -e "${WHITE}  sudo firewall-cmd --reload${NC}"
        echo ""
    fi

elif [ "$OS" == "macos" ]; then
    # macOS 防火墙配置 (使用 pf)
    echo -e "${WHITE}使用 pf 配置防火墙...${NC}"
    echo ""

    # 创建 pf 配置文件
    PF_CONF="/etc/pf.anchors/dplayer"

    # 检查是否需要 sudo
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ 错误: 此脚本需要 root 权限运行${NC}"
        echo -e "${YELLOW}请使用: sudo $0${NC}"
        exit 1
    fi

    # 备份现有配置
    if [ -f "$PF_CONF" ]; then
        echo -e "${YELLOW}备份现有配置...${NC}"
        cp "$PF_CONF" "${PF_CONF}.backup"
    fi

    # 创建新配置
    cat > "$PF_CONF" << EOF
# Dplayer 防火墙规则
# 主应用端口
pass in proto tcp from any to any port $MAIN_APP_PORT

# 管理后台端口
pass in proto tcp from any to any port $ADMIN_PORT
EOF

    echo -e "${GREEN}✅ 防火墙配置文件已创建${NC}"
    echo ""

    # 加载配置
    echo -e "${WHITE}加载防火墙规则...${NC}"

    if pfctl -e -f "$PF_CONF" 2>/dev/null; then
        echo -e "${GREEN}✅ 防火墙规则已加载${NC}"
        echo ""

        echo -e "${CYAN}========================================${NC}"
        echo -e "${CYAN}防火墙规则配置完成${NC}"
        echo -e "${CYAN}========================================${NC}"
        echo ""
        echo -e "${GREEN}pf 状态:${NC}"
        echo ""
        pfctl -sr | grep -E "port ($MAIN_APP_PORT|$ADMIN_PORT)"
        echo ""
    else
        echo -e "${RED}❌ 错误: 加载防火墙规则失败${NC}"
        echo -e "${YELLOW}请检查配置文件: $PF_CONF${NC}"
        exit 1
    fi
fi

# 显示访问信息
echo -e "${CYAN}🌐 局域网访问地址:${NC}"
echo ""
echo -e "${WHITE}本机访问:${NC}"
echo -e "${CYAN}  • 主应用: http://localhost:$MAIN_APP_PORT${NC}"
echo -e "${CYAN}  • 管理后台: http://localhost:$ADMIN_PORT${NC}"
echo ""

if [ -n "$IP_ADDRESSES" ]; then
    echo -e "${WHITE}局域网访问:${NC}"
    while IFS= read -r ip; do
        echo -e "${CYAN}  • 主应用: http://$ip:$MAIN_APP_PORT${NC}"
        echo -e "${CYAN}  • 管理后台: http://$ip:$ADMIN_PORT${NC}"
    done <<< "$IP_ADDRESSES"
    echo ""
fi

echo -e "${GREEN}✅ 防火墙配置完成!${NC}"
echo ""
echo -e "${YELLOW}注意事项:${NC}"
echo -e "${WHITE}1. 确保两个应用都已启动${NC}"
echo -e "${WHITE}2. 局域网设备可以通过上述地址访问${NC}"
echo -e "${WHITE}3. 如需修改端口，请编辑此脚本中的端口号${NC}"
echo ""
