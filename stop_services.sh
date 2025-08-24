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
MAX_WAIT_TIME=30

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}XConfKit 服务停止脚本${NC}"
echo -e "${BLUE}==========================================${NC}"

# 函数：检查进程是否存在
check_process() {
    local pid=$1
    local process_name=$2
    
    if [ -z "$pid" ]; then
        return 1
    fi
    
    if kill -0 $pid 2>/dev/null; then
        echo -e "${YELLOW}发现运行中的 $process_name 进程: $pid${NC}"
        return 0
    else
        return 1
    fi
}

# 函数：优雅停止进程
graceful_stop() {
    local pid=$1
    local process_name=$2
    local max_wait=$3
    
    if [ -z "$pid" ]; then
        return 0
    fi
    
    echo -e "${BLUE}正在停止 $process_name (PID: $pid)...${NC}"
    
    # 发送TERM信号
    kill -TERM $pid 2>/dev/null
    
    # 等待进程优雅停止
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if ! kill -0 $pid 2>/dev/null; then
            echo -e "${GREEN}✅ $process_name 已优雅停止${NC}"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
        echo -e "${YELLOW}⏳ 等待 $process_name 停止... ($waited/$max_wait)${NC}"
    done
    
    # 如果优雅停止失败，强制终止
    echo -e "${YELLOW}⚠️  $process_name 未能优雅停止，强制终止...${NC}"
    kill -KILL $pid 2>/dev/null
    sleep 2
    
    if ! kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $process_name 已强制停止${NC}"
        return 0
    else
        echo -e "${RED}❌ 无法停止 $process_name${NC}"
        return 1
    fi
}

# 函数：停止端口上的所有进程
stop_port_processes() {
    local port=$1
    local service_name=$2
    
    echo -e "${BLUE}检查端口 $port 上的进程...${NC}"
    
    # 查找占用端口的进程
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}发现端口 $port 上的进程: $pids${NC}"
        
        for pid in $pids; do
            graceful_stop $pid "$service_name 进程" 10
        done
    else
        echo -e "${GREEN}✅ 端口 $port 上没有运行中的进程${NC}"
    fi
}

# 函数：停止特定类型的进程
stop_processes_by_pattern() {
    local pattern=$1
    local process_name=$2
    
    echo -e "${BLUE}查找 $process_name 进程...${NC}"
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}发现 $process_name 进程: $pids${NC}"
        
        for pid in $pids; do
            graceful_stop $pid "$process_name" 10
        done
    else
        echo -e "${GREEN}✅ 没有发现 $process_name 进程${NC}"
    fi
}

# 函数：清理PID文件
cleanup_pid_files() {
    echo -e "${BLUE}清理PID文件...${NC}"
    
    local pid_files=(".backend.pid" ".frontend.pid")
    
    for pid_file in "${pid_files[@]}"; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file" 2>/dev/null)
            if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}发现PID文件 $pid_file 中的进程仍在运行: $pid${NC}"
                graceful_stop $pid "PID文件中的进程" 5
            fi
            rm -f "$pid_file"
            echo -e "${GREEN}✅ 已删除PID文件: $pid_file${NC}"
        fi
    done
}

# 函数：验证服务是否已停止
verify_services_stopped() {
    echo -e "${BLUE}验证服务状态...${NC}"
    
    local backend_running=0
    local frontend_running=0
    local backend_port_in_use=0
    local frontend_port_in_use=0
    
    # 检查进程
    if pgrep -f "python start_backend.py" >/dev/null 2>&1; then
        backend_running=1
    fi
    
    if pgrep -f "npm run dev" >/dev/null 2>&1; then
        frontend_running=1
    fi
    
    # 检查端口
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        backend_port_in_use=1
    fi
    
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        frontend_port_in_use=1
    fi
    
    # 报告状态
    if [ $backend_running -eq 0 ] && [ $frontend_running -eq 0 ] && [ $backend_port_in_use -eq 0 ] && [ $frontend_port_in_use -eq 0 ]; then
        echo -e "${GREEN}✅ 所有服务已成功停止${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  部分服务可能仍在运行:${NC}"
        if [ $backend_running -eq 1 ]; then
            echo -e "${YELLOW}  - 后端进程仍在运行${NC}"
        fi
        if [ $frontend_running -eq 1 ]; then
            echo -e "${YELLOW}  - 前端进程仍在运行${NC}"
        fi
        if [ $backend_port_in_use -eq 1 ]; then
            echo -e "${YELLOW}  - 后端端口 $BACKEND_PORT 仍被占用${NC}"
        fi
        if [ $frontend_port_in_use -eq 1 ]; then
            echo -e "${YELLOW}  - 前端端口 $FRONTEND_PORT 仍被占用${NC}"
        fi
        return 1
    fi
}

# 函数：强制清理
force_cleanup() {
    echo -e "${YELLOW}执行强制清理...${NC}"
    
    # 强制终止所有相关进程
    pkill -f "python start_backend.py" 2>/dev/null
    pkill -f "npm run dev" 2>/dev/null
    pkill -f "uvicorn" 2>/dev/null
    pkill -f "python.*main" 2>/dev/null
    
    # 强制释放端口
    local backend_pids=$(lsof -ti:$BACKEND_PORT 2>/dev/null)
    if [ ! -z "$backend_pids" ]; then
        echo -e "${YELLOW}强制终止后端端口进程: $backend_pids${NC}"
        for pid in $backend_pids; do
            kill -KILL $pid 2>/dev/null
        done
    fi
    
    local frontend_pids=$(lsof -ti:$FRONTEND_PORT 2>/dev/null)
    if [ ! -z "$frontend_pids" ]; then
        echo -e "${YELLOW}强制终止前端端口进程: $frontend_pids${NC}"
        for pid in $frontend_pids; do
            kill -KILL $pid 2>/dev/null
        done
    fi
    
    sleep 3
}

# 主执行流程
main() {
    # 1. 清理PID文件中的进程
    cleanup_pid_files
    
    # 2. 停止特定进程
    stop_processes_by_pattern "python start_backend.py" "后端服务"
    stop_processes_by_pattern "npm run dev" "前端服务"
    
    # 3. 停止端口上的进程
    stop_port_processes $BACKEND_PORT "后端"
    stop_port_processes $FRONTEND_PORT "前端"
    
    # 4. 验证服务状态
    if verify_services_stopped; then
        echo -e "${GREEN}==========================================${NC}"
        echo -e "${GREEN}🎉 所有服务已成功停止！${NC}"
        echo -e "${GREEN}==========================================${NC}"
    else
        echo -e "${YELLOW}==========================================${NC}"
        echo -e "${YELLOW}⚠️  部分服务可能仍在运行，执行强制清理...${NC}"
        echo -e "${YELLOW}==========================================${NC}"
        
        force_cleanup
        
        if verify_services_stopped; then
            echo -e "${GREEN}✅ 强制清理成功，所有服务已停止${NC}"
        else
            echo -e "${RED}❌ 强制清理后仍有服务在运行，请手动检查${NC}"
            echo -e "${YELLOW}可以使用以下命令手动检查:${NC}"
            echo -e "  ps aux | grep -E '(python start_backend.py|npm run dev)'"
            echo -e "  lsof -i :$BACKEND_PORT"
            echo -e "  lsof -i :$FRONTEND_PORT"
        fi
    fi
    
    # 5. 清理日志文件（可选）
    if [ "$1" = "--clean-logs" ]; then
        echo -e "${BLUE}清理日志文件...${NC}"
        rm -f backend.log frontend.log
        echo -e "${GREEN}✅ 日志文件已清理${NC}"
    fi
}

# 错误处理
trap 'echo -e "\n${RED}收到中断信号，正在强制清理...${NC}"; force_cleanup; exit 1' INT TERM

# 执行主函数
main "$@"
