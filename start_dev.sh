#!/bin/bash

# XConfKit 开发环境启动脚本

echo "=========================================="
echo "XConfKit 开发环境启动"
echo "=========================================="

# 检查Python依赖
echo "检查Python依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "错误: 找不到 requirements.txt 文件"
    exit 1
fi

# 检查前端依赖
echo "检查前端依赖..."
if [ ! -f "frontend/package.json" ]; then
    echo "错误: 找不到前端 package.json 文件"
    exit 1
fi

# 创建数据目录
echo "创建数据目录..."
mkdir -p data/backups

# 安装Python依赖
echo "安装Python依赖..."
pip3 install -r requirements.txt

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install
cd ..

echo "=========================================="
echo "依赖安装完成！"
echo ""
echo "启动后端服务:"
echo "  python3 start_backend.py"
echo ""
echo "启动前端服务 (新终端):"
echo "  cd frontend && npm run dev"
echo ""
echo "访问地址:"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  前端界面: http://localhost:5173"
echo "=========================================="
