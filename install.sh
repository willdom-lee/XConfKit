#!/bin/bash

# XConfKit 一键安装脚本
# 适用于 Linux 环境

set -e

echo "=========================================="
echo "XConfKit 网络设备配置备份系统"
echo "一键安装脚本"
echo "=========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 检查系统类型
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "检测到 Linux 系统"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到 macOS 系统"
else
    echo "不支持的操作系统: $OSTYPE"
    exit 1
fi

# 更新包管理器
echo "更新系统包..."
if command -v apt-get &> /dev/null; then
    apt-get update
elif command -v yum &> /dev/null; then
    yum update -y
elif command -v brew &> /dev/null; then
    brew update
fi

# 安装 Python 3
echo "检查 Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "安装 Python 3..."
    if command -v apt-get &> /dev/null; then
        apt-get install -y python3 python3-pip
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    elif command -v brew &> /dev/null; then
        brew install python3
    fi
fi

# 安装 Node.js
echo "检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "安装 Node.js..."
    if command -v apt-get &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
        apt-get install -y nodejs
    elif command -v yum &> /dev/null; then
        curl -fsSL https://rpm.nodesource.com/setup_lts.x | bash -
        yum install -y nodejs
    elif command -v brew &> /dev/null; then
        brew install node
    fi
fi

# 安装后端依赖
echo "安装 Python 依赖..."
pip3 install -r requirements.txt

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install
cd ..

# 创建数据目录
echo "创建数据目录..."
mkdir -p data/backups

# 设置权限
echo "设置文件权限..."
chmod +x start_backend.py

# 创建服务文件
echo "创建系统服务..."
cat > /etc/systemd/system/xconfkit.service << EOF
[Unit]
Description=XConfKit Network Device Backup System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/start_backend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload

# 启用服务
systemctl enable xconfkit.service

echo "=========================================="
echo "安装完成！"
echo ""
echo "启动服务:"
echo "  sudo systemctl start xconfkit"
echo ""
echo "查看状态:"
echo "  sudo systemctl status xconfkit"
echo ""
echo "查看日志:"
echo "  sudo journalctl -u xconfkit -f"
echo ""
echo "停止服务:"
echo "  sudo systemctl stop xconfkit"
echo ""
echo "前端开发服务器:"
echo "  cd frontend && npm run dev"
echo ""
echo "访问地址:"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  前端界面: http://localhost:5173"
echo "=========================================="
