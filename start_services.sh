#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKEND_PORT=8000
FRONTEND_PORT=5174
MAX_RETRIES=3
WAIT_TIME=5

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}XConfKit 服务启动脚本${NC}"
echo -e "${BLUE}==========================================${NC}"

# 免责声明提示
echo -e "${RED}⚠️  重要安全警告 ⚠️${NC}"
echo -e "${YELLOW}本软件为演示版本，仅供学习和研究使用${NC}"
echo -e "${YELLOW}使用前请仔细阅读 DISCLAIMER.md 免责声明${NC}"
echo -e "${YELLOW}建议仅在隔离的测试环境中使用${NC}"
echo -e "${YELLOW}作者不承担任何安全风险和责任${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -f "start_backend.py" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 函数：检查端口是否被占用
check_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 被占用，正在尝试释放...${NC}"
        return 1
    else
        echo -e "${GREEN}✅ 端口 $port 可用${NC}"
        return 0
    fi
}

# 函数：强制释放端口
release_port() {
    local port=$1
    local service_name=$2
    
    echo -e "${YELLOW}正在释放端口 $port...${NC}"
    
    # 查找占用端口的进程
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}发现占用端口的进程: $pids${NC}"
        
        # 尝试优雅停止
        for pid in $pids; do
            echo -e "${YELLOW}尝试优雅停止进程 $pid...${NC}"
            kill -TERM $pid 2>/dev/null
        done
        
        # 等待进程停止
        sleep 3
        
        # 检查是否还有进程在运行
        local remaining_pids=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$remaining_pids" ]; then
            echo -e "${YELLOW}强制终止剩余进程...${NC}"
            for pid in $remaining_pids; do
                kill -KILL $pid 2>/dev/null
            done
            sleep 2
        fi
    fi
    
    # 再次检查端口
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 端口 $port 已释放${NC}"
        return 0
    else
        echo -e "${RED}❌ 无法释放端口 $port${NC}"
        return 1
    fi
}

# 函数：停止现有服务
stop_existing_services() {
    echo -e "${BLUE}停止现有服务...${NC}"
    
    # 停止后端服务
    local backend_pids=$(pgrep -f "python start_backend.py" 2>/dev/null)
    if [ ! -z "$backend_pids" ]; then
        echo -e "${YELLOW}发现运行中的后端进程: $backend_pids${NC}"
        for pid in $backend_pids; do
            kill -TERM $pid 2>/dev/null
        done
        sleep 2
    fi
    
    # 停止前端服务
    local frontend_pids=$(pgrep -f "npm run dev" 2>/dev/null)
    if [ ! -z "$frontend_pids" ]; then
        echo -e "${YELLOW}发现运行中的前端进程: $frontend_pids${NC}"
        for pid in $frontend_pids; do
            kill -TERM $pid 2>/dev/null
        done
        sleep 2
    fi
    
    # 强制清理可能的残留进程
    pkill -f "uvicorn" 2>/dev/null
    pkill -f "python.*main" 2>/dev/null
    
    sleep 2
}

# 函数：检查服务健康状态
check_service_health() {
    local url=$1
    local service_name=$2
    local max_attempts=$3
    
    echo -e "${BLUE}检查 $service_name 健康状态...${NC}"
    
    for i in $(seq 1 $max_attempts); do
        if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name 启动成功${NC}"
            return 0
        else
            echo -e "${YELLOW}⏳ 等待 $service_name 启动... (尝试 $i/$max_attempts)${NC}"
            sleep 2
        fi
    done
    
    echo -e "${RED}❌ $service_name 启动失败${NC}"
    return 1
}

# 函数：启动后端服务
start_backend() {
    echo -e "${BLUE}启动后端服务...${NC}"
    
    # 检查端口
    if ! check_port $BACKEND_PORT "后端"; then
        if ! release_port $BACKEND_PORT "后端"; then
            echo -e "${RED}❌ 无法启动后端服务：端口 $BACKEND_PORT 被占用${NC}"
            return 1
        fi
    fi
    
    # 启动后端
    python start_backend.py > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 等待启动
    sleep 3
    
    # 检查进程是否还在运行
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ 后端进程启动失败${NC}"
        echo -e "${YELLOW}查看后端日志:${NC}"
        tail -10 backend.log
        return 1
    fi
    
    # 检查健康状态
    if check_service_health "http://localhost:$BACKEND_PORT/health" "后端服务" 5; then
        echo -e "${GREEN}✅ 后端服务启动成功 (PID: $BACKEND_PID)${NC}"
        echo $BACKEND_PID > .backend.pid
        return 0
    else
        echo -e "${RED}❌ 后端服务启动失败${NC}"
        echo -e "${YELLOW}查看后端日志:${NC}"
        tail -10 backend.log
        return 1
    fi
}

# 函数：启动前端服务
start_frontend() {
    echo -e "${BLUE}启动前端服务...${NC}"
    
    # 检查端口
    if ! check_port $FRONTEND_PORT "前端"; then
        if ! release_port $FRONTEND_PORT "前端"; then
            echo -e "${RED}❌ 无法启动前端服务：端口 $FRONTEND_PORT 被占用${NC}"
            return 1
        fi
    fi
    
    # 检查前端目录
    if [ ! -d "frontend" ]; then
        echo -e "${RED}❌ 前端目录不存在${NC}"
        return 1
    fi
    
    # 启动前端
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # 等待启动
    sleep 5
    
    # 检查进程是否还在运行
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ 前端进程启动失败${NC}"
        echo -e "${YELLOW}查看前端日志:${NC}"
        tail -10 frontend.log
        return 1
    fi
    
    # 检查健康状态
    if check_service_health "http://localhost:$FRONTEND_PORT" "前端服务" 8; then
        echo -e "${GREEN}✅ 前端服务启动成功 (PID: $FRONTEND_PID)${NC}"
        echo $FRONTEND_PID > .frontend.pid
        return 0
    else
        echo -e "${RED}❌ 前端服务启动失败${NC}"
        echo -e "${YELLOW}查看前端日志:${NC}"
        tail -10 frontend.log
        return 1
    fi
}

# 主执行流程
main() {
    # 停止现有服务
    stop_existing_services
    
    # 启动后端服务
    if ! start_backend; then
        echo -e "${RED}❌ 后端服务启动失败，退出${NC}"
        exit 1
    fi
    
    # 启动前端服务
    if ! start_frontend; then
        echo -e "${RED}❌ 前端服务启动失败，停止后端服务${NC}"
        kill -TERM $BACKEND_PID 2>/dev/null
        rm -f .backend.pid
        exit 1
    fi
    
    # 显示成功信息
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}🎉 所有服务启动完成！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo -e "  ${GREEN}前端界面:${NC} http://localhost:$FRONTEND_PORT"
    echo -e "  ${GREEN}后端API:${NC} http://localhost:$BACKEND_PORT"
    echo -e "  ${GREEN}API文档:${NC} http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo -e "${BLUE}停止服务:${NC}"
    echo -e "  ${YELLOW}./stop_services.sh${NC}"
    echo ""
    echo -e "${BLUE}查看日志:${NC}"
    echo -e "  ${YELLOW}后端日志:${NC} tail -f backend.log"
    echo -e "  ${YELLOW}前端日志:${NC} tail -f frontend.log"
    echo -e "${GREEN}==========================================${NC}"
}

# 错误处理
trap 'echo -e "\n${RED}收到中断信号，正在清理...${NC}"; kill -TERM $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 1' INT TERM

# 执行主函数
main
