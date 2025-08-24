#!/bin/bash

# XConfKit Ubuntu 安装脚本
# 支持中国大陆网络环境，具有完善的错误处理和重试机制

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日志文件
LOG_FILE="./install.log"
ERROR_LOG="./install_errors.log"

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}🚀 XConfKit Ubuntu 安装脚本${NC}"
echo -e "${BLUE}==========================================${NC}"
echo -e "${CYAN}专为中国大陆网络环境优化${NC}"
echo -e "${CYAN}具有完善的错误处理和重试机制${NC}"
echo -e "${BLUE}==========================================${NC}"

# 日志函数
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

error_log() {
    echo -e "$1" | tee -a "$ERROR_LOG"
}

# 网络检测函数
check_network() {
    log "${YELLOW}检测网络连接...${NC}"
    
    # 检测是否能访问外网
    if ! ping -c 1 -W 3 8.8.8.8 &> /dev/null; then
        log "${RED}⚠️  网络连接异常，可能影响安装${NC}"
        log "${YELLOW}建议检查网络设置或使用代理${NC}"
        read -p "是否继续安装？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "${RED}安装已取消${NC}"
            exit 1
        fi
    else
        log "${GREEN}✅ 网络连接正常${NC}"
    fi
}

# 系统检查
check_system() {
    log "${YELLOW}检查系统环境...${NC}"
    
    # 检查是否为Ubuntu
    if ! grep -q "Ubuntu" /etc/os-release; then
        log "${RED}❌ 此脚本仅支持Ubuntu系统${NC}"
        exit 1
    fi
    
    # 检查用户权限
    if [[ $EUID -eq 0 ]]; then
        log "${RED}❌ 请不要使用root用户运行此脚本${NC}"
        log "${YELLOW}请使用普通用户运行，脚本会自动请求sudo权限${NC}"
        exit 1
    fi
    
    # 检查磁盘空间
    local available_space=$(df . | awk 'NR==2 {print $4}')
    if [ $available_space -lt 1048576 ]; then  # 1GB
        log "${RED}❌ 磁盘空间不足，需要至少1GB可用空间${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ 系统环境检查通过${NC}"
}

# 更新系统
update_system() {
    log "${YELLOW}更新系统包...${NC}"
    
    # 配置apt镜像源（中国大陆用户）
    if ! grep -q "mirrors.tuna.tsinghua.edu.cn" /etc/apt/sources.list; then
        log "${BLUE}配置apt镜像源...${NC}"
        sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
        sudo sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
        sudo sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
    fi
    
    # 更新包列表
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "${BLUE}更新包列表 (第 $attempt 次)...${NC}"
        if sudo apt update 2>> "$ERROR_LOG"; then
            log "${GREEN}✅ 系统包更新完成${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log "${RED}⚠️  系统包更新失败，但继续安装${NC}"
            else
                log "${YELLOW}更新失败，等待5秒后重试...${NC}"
                sleep 5
            fi
        fi
        ((attempt++))
    done
}

# 安装基础依赖
install_basic_deps() {
    log "${YELLOW}安装基础依赖...${NC}"
    
    local packages=("curl" "wget" "git" "unzip" "build-essential" "python3" "python3-pip" "python3-venv" "nodejs" "npm" "sqlite3" "openssh-client")
    
    for package in "${packages[@]}"; do
        log "${BLUE}安装 $package...${NC}"
        local max_attempts=3
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if sudo apt install -y "$package" 2>> "$ERROR_LOG"; then
                log "${GREEN}✅ $package 安装成功${NC}"
                break
            else
                if [ $attempt -eq $max_attempts ]; then
                    log "${RED}⚠️  $package 安装失败${NC}"
                else
                    log "${YELLOW}安装失败，等待3秒后重试...${NC}"
                    sleep 3
                fi
            fi
            ((attempt++))
        done
    done
    
    log "${GREEN}✅ 基础依赖安装完成${NC}"
}

# 安装Python依赖
install_python_deps() {
    log "${YELLOW}安装Python依赖...${NC}"
    
    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        log "${BLUE}创建Python虚拟环境...${NC}"
        python3 -m venv .venv
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 升级pip
    log "${BLUE}升级pip...${NC}"
    pip install --upgrade pip 2>> "$ERROR_LOG" || log "${RED}⚠️  pip升级失败${NC}"
    
    # 配置pip镜像源（中国大陆用户）
    log "${BLUE}配置pip镜像源...${NC}"
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple 2>> "$ERROR_LOG" || true
    
    if [ -f "requirements.txt" ]; then
        log "${BLUE}安装Python包...${NC}"
        local max_attempts=3
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            log "${BLUE}尝试安装Python包 (第 $attempt 次)...${NC}"
            if pip install -r requirements.txt 2>> "$ERROR_LOG"; then
                log "${GREEN}✅ Python包安装完成${NC}"
                break
            else
                if [ $attempt -eq $max_attempts ]; then
                    log "${RED}⚠️  Python包安装失败${NC}"
                    log "${YELLOW}尝试手动安装关键包...${NC}"
                    
                    # 手动安装关键包
                    local critical_packages=("fastapi" "uvicorn[standard]" "sqlalchemy" "paramiko" "pydantic" "ping3")
                    for pkg in "${critical_packages[@]}"; do
                        log "${BLUE}安装 $pkg...${NC}"
                        pip install "$pkg" 2>> "$ERROR_LOG" || log "${RED}⚠️  $pkg 安装失败${NC}"
                    done
                else
                    log "${YELLOW}安装失败，等待10秒后重试...${NC}"
                    sleep 10
                fi
            fi
            ((attempt++))
        done
    else
        log "${RED}❌ requirements.txt 文件不存在${NC}"
        exit 1
    fi
}

# 安装Node.js依赖
install_node_deps() {
    log "${YELLOW}安装Node.js依赖...${NC}"
    
    if [ -d "frontend" ]; then
        cd frontend
        if [ ! -f "package.json" ]; then
            log "${RED}❌ frontend/package.json 文件不存在${NC}"
            exit 1
        fi
        
        # 配置npm镜像源（中国大陆用户）
        log "${BLUE}配置npm镜像源...${NC}"
        npm config set registry https://registry.npmmirror.com 2>> "../$ERROR_LOG" || true
        npm config set disturl https://npmmirror.com/dist 2>> "../$ERROR_LOG" || true
        
        # 清理npm缓存
        log "${BLUE}清理npm缓存...${NC}"
        npm cache clean --force 2>> "../$ERROR_LOG" || true
        
        # 删除旧的依赖文件
        log "${BLUE}清理旧的依赖文件...${NC}"
        rm -rf node_modules package-lock.json 2>/dev/null || true
        
        # 安装依赖
        log "${BLUE}安装npm包...${NC}"
        local max_attempts=3
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            log "${BLUE}尝试安装npm包 (第 $attempt 次)...${NC}"
            if npm install --no-audit --no-fund 2>> "../$ERROR_LOG"; then
                log "${GREEN}✅ npm包安装完成${NC}"
                break
            else
                if [ $attempt -eq $max_attempts ]; then
                    log "${RED}⚠️  npm包安装失败${NC}"
                    log "${YELLOW}尝试手动安装关键包...${NC}"
                    
                    # 手动安装关键包
                    local critical_packages=("react" "react-dom" "react-router-dom" "antd" "@ant-design/icons" "axios" "dayjs" "vite")
                    for pkg in "${critical_packages[@]}"; do
                        log "${BLUE}安装 $pkg...${NC}"
                        npm install "$pkg" --no-audit --no-fund 2>> "../$ERROR_LOG" || log "${RED}⚠️  $pkg 安装失败${NC}"
                    done
                else
                    log "${YELLOW}安装失败，等待15秒后重试...${NC}"
                    sleep 15
                fi
            fi
            ((attempt++))
        done
        cd ..
    else
        log "${RED}❌ frontend 目录不存在${NC}"
        exit 1
    fi
}

# 设置环境
setup_environment() {
    log "${YELLOW}设置环境...${NC}"
    
    # 创建必要目录
    mkdir -p data/backups logs backups
    
    # 设置执行权限
    chmod +x *.sh 2>/dev/null || true
    chmod +x backend/*.py 2>/dev/null || true
    
    log "${GREEN}✅ 环境设置完成${NC}"
}

# 初始化数据库
init_database() {
    log "${YELLOW}初始化数据库...${NC}"
    
    source .venv/bin/activate
    
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "${BLUE}尝试初始化数据库 (第 $attempt 次)...${NC}"
        if python3 -c "from backend.database import engine, Base; Base.metadata.create_all(bind=engine)" 2>> "$ERROR_LOG"; then
            log "${GREEN}✅ 数据库初始化成功${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                log "${RED}⚠️  数据库初始化失败${NC}"
                log "${YELLOW}请检查Python环境和依赖包${NC}"
            else
                log "${YELLOW}初始化失败，等待3秒后重试...${NC}"
                sleep 3
            fi
        fi
        ((attempt++))
    done
}

# 显示结果
show_result() {
    log "${GREEN}==========================================${NC}"
    log "${GREEN}🎉 XConfKit 安装完成！${NC}"
    log "${GREEN}==========================================${NC}"
    
    log "${YELLOW}📋 下一步操作:${NC}"
    log "  🚀 启动服务: ./start_services.sh"
    log "  🌐 访问系统: http://localhost:5174"
    log "  📚 API文档: http://localhost:8000/docs"
    
    log "${YELLOW}🔧 常用命令:${NC}"
    log "  ▶️  启动: ./start_services.sh"
    log "  ⏹️  停止: ./stop_services.sh"
    log "  🔄 重启: ./restart_services.sh"
    log "  📊 状态: ./check_status.sh"
    
    log "${YELLOW}⚠️  注意事项:${NC}"
    log "  • 如果安装过程中出现警告，请检查日志文件"
    log "  • 首次启动可能需要较长时间"
    log "  • 如遇网络问题，请检查网络连接或使用代理"
    
    log "${GREEN}==========================================${NC}"
}

# 主流程
main() {
    # 清理日志文件
    > "$LOG_FILE"
    > "$ERROR_LOG"
    
    # 执行安装步骤
    check_network
    check_system
    update_system
    install_basic_deps
    install_python_deps
    install_node_deps
    setup_environment
    init_database
    show_result
}

# 错误处理
trap 'log "${RED}❌ 安装过程中发生错误，请检查日志文件${NC}"; exit 1' ERR

# 运行主流程
main "$@"
