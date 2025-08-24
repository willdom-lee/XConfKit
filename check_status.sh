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

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}XConfKit 服务状态检查${NC}"
echo -e "${BLUE}==========================================${NC}"

# 函数：检查进程状态
check_process_status() {
    local pattern=$1
    local service_name=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo -e "${GREEN}✅ $service_name 正在运行${NC}"
        echo -e "  进程ID: $pids"
        
        # 显示进程详细信息
        for pid in $pids; do
            local process_info=$(ps -p $pid -o pid,ppid,cmd,etime --no-headers 2>/dev/null)
            if [ ! -z "$process_info" ]; then
                echo -e "  详细信息: $process_info"
            fi
        done
        return 0
    else
        echo -e "${RED}❌ $service_name 未运行${NC}"
        return 1
    fi
}

# 函数：检查端口状态
check_port_status() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pids=$(lsof -ti:$port 2>/dev/null)
        echo -e "${GREEN}✅ $service_name 端口 $port 正在监听${NC}"
        echo -e "  占用进程: $pids"
        return 0
    else
        echo -e "${RED}❌ $service_name 端口 $port 未监听${NC}"
        return 1
    fi
}

# 函数：检查服务健康状态
check_health_status() {
    local url=$1
    local service_name=$2
    
    if curl -s --connect-timeout 3 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name 健康检查通过${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name 健康检查失败${NC}"
        return 1
    fi
}

# 函数：检查PID文件
check_pid_files() {
    echo -e "${BLUE}检查PID文件...${NC}"
    
    local pid_files=(".backend.pid" ".frontend.pid")
    
    for pid_file in "${pid_files[@]}"; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file" 2>/dev/null)
            if [ ! -z "$pid" ]; then
                if kill -0 $pid 2>/dev/null; then
                    echo -e "${GREEN}✅ PID文件 $pid_file 存在且进程运行中 (PID: $pid)${NC}"
                else
                    echo -e "${YELLOW}⚠️  PID文件 $pid_file 存在但进程已停止 (PID: $pid)${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️  PID文件 $pid_file 存在但内容为空${NC}"
            fi
        else
            echo -e "${RED}❌ PID文件 $pid_file 不存在${NC}"
        fi
    done
}

# 函数：检查日志文件
check_log_files() {
    echo -e "${BLUE}检查日志文件...${NC}"
    
    local log_files=("backend.log" "frontend.log")
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            local size=$(du -h "$log_file" | cut -f1)
            local lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
            echo -e "${GREEN}✅ 日志文件 $log_file 存在${NC}"
            echo -e "  大小: $size, 行数: $lines"
            
            # 显示最后几行日志
            if [ "$1" = "--show-logs" ]; then
                echo -e "${YELLOW}  最后10行日志:${NC}"
                tail -10 "$log_file" | sed 's/^/    /'
            fi
        else
            echo -e "${RED}❌ 日志文件 $log_file 不存在${NC}"
        fi
    done
}

# 函数：显示系统资源使用情况
show_system_resources() {
    echo -e "${BLUE}系统资源使用情况...${NC}"
    
    # 显示相关进程的资源使用
    local backend_pids=$(pgrep -f "python start_backend.py" 2>/dev/null)
    local frontend_pids=$(pgrep -f "npm run dev" 2>/dev/null)
    
    if [ ! -z "$backend_pids" ] || [ ! -z "$frontend_pids" ]; then
        echo -e "${YELLOW}相关进程资源使用:${NC}"
        ps -p "$backend_pids $frontend_pids" -o pid,ppid,%cpu,%mem,vsz,rss,cmd --no-headers 2>/dev/null | while read line; do
            echo -e "  $line"
        done
    fi
    
    # 显示端口使用情况
    echo -e "${YELLOW}端口使用情况:${NC}"
    lsof -i :$BACKEND_PORT -i :$FRONTEND_PORT 2>/dev/null | grep LISTEN || echo -e "  没有发现相关端口监听"
}

# 主执行流程
main() {
    local show_logs=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --show-logs)
                show_logs=true
                shift
                ;;
            *)
                echo -e "${RED}未知参数: $1${NC}"
                echo -e "用法: $0 [--show-logs]"
                exit 1
                ;;
        esac
    done
    
    # 检查进程状态
    echo -e "${BLUE}检查进程状态...${NC}"
    check_process_status "python start_backend.py" "后端服务"
    check_process_status "npm run dev" "前端服务"
    echo ""
    
    # 检查端口状态
    echo -e "${BLUE}检查端口状态...${NC}"
    check_port_status $BACKEND_PORT "后端"
    check_port_status $FRONTEND_PORT "前端"
    echo ""
    
    # 检查健康状态
    echo -e "${BLUE}检查服务健康状态...${NC}"
    check_health_status "http://localhost:$BACKEND_PORT/health" "后端服务"
    check_health_status "http://localhost:$FRONTEND_PORT" "前端服务"
    echo ""
    
    # 检查PID文件
    check_pid_files
    echo ""
    
    # 检查日志文件
    if [ "$show_logs" = true ]; then
        check_log_files --show-logs
    else
        check_log_files
    fi
    echo ""
    
    # 显示系统资源
    show_system_resources
    echo ""
    
    # 总结
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}服务访问地址:${NC}"
    echo -e "  前端界面: http://localhost:$FRONTEND_PORT"
    echo -e "  后端API: http://localhost:$BACKEND_PORT"
    echo -e "  API文档: http://localhost:$BACKEND_PORT/docs"
    echo -e "${BLUE}==========================================${NC}"
}

# 执行主函数
main "$@"

