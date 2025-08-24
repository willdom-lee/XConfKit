#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}XConfKit 服务重启脚本${NC}"
echo -e "${BLUE}==========================================${NC}"

# 检查是否在正确的目录
if [ ! -f "start_services.sh" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 函数：显示进度
show_progress() {
    local message=$1
    echo -e "${YELLOW}⏳ $message${NC}"
}

# 函数：显示成功
show_success() {
    local message=$1
    echo -e "${GREEN}✅ $message${NC}"
}

# 函数：显示错误
show_error() {
    local message=$1
    echo -e "${RED}❌ $message${NC}"
}

# 主执行流程
main() {
    local clean_logs=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean-logs)
                clean_logs=true
                shift
                ;;
            *)
                echo -e "${RED}未知参数: $1${NC}"
                echo -e "用法: $0 [--clean-logs]"
                exit 1
                ;;
        esac
    done
    
    # 1. 停止服务
    show_progress "正在停止现有服务..."
    if ./stop_services.sh; then
        show_success "服务停止完成"
    else
        show_error "服务停止失败"
        exit 1
    fi
    
    # 2. 等待一段时间确保端口释放
    show_progress "等待端口释放..."
    sleep 3
    
    # 3. 清理日志（可选）
    if [ "$clean_logs" = true ]; then
        show_progress "清理日志文件..."
        rm -f backend.log frontend.log
        show_success "日志文件已清理"
    fi
    
    # 4. 启动服务
    show_progress "正在启动服务..."
    if ./start_services.sh; then
        show_success "服务启动完成"
    else
        show_error "服务启动失败"
        exit 1
    fi
    
    # 5. 显示最终状态
    echo ""
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}🎉 服务重启完成！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${BLUE}检查服务状态:${NC}"
    echo -e "  ${YELLOW}./check_status.sh${NC}"
    echo ""
    echo -e "${BLUE}查看详细状态:${NC}"
    echo -e "  ${YELLOW}./check_status.sh --show-logs${NC}"
}

# 错误处理
trap 'echo -e "\n${RED}收到中断信号，重启过程中断${NC}"; exit 1' INT TERM

# 执行主函数
main "$@"






