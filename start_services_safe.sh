#!/bin/bash

# XConfKit 安全启动脚本 - 集成数据保护功能
# 防止数据丢失和异常重构

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    log_success "Python3 环境正常"
}

# 检查数据完整性
check_data_integrity() {
    log_info "检查数据完整性..."
    
    if [ ! -f "data/xconfkit.db" ]; then
        log_warning "数据库文件不存在，将创建新数据库"
        return 1
    fi
    
    # 使用Python脚本检查数据完整性
    if python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('data/xconfkit.db')
    cursor = conn.cursor()
    
    # 检查关键表
    required_tables = ['devices', 'backups', 'strategies', 'configs', 'ai_configs', 'analysis_prompts']
    missing_tables = []
    
    for table in required_tables:
        cursor.execute(f\"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'\")
        if not cursor.fetchone():
            missing_tables.append(table)
    
    if missing_tables:
        print(f'缺少表: {missing_tables}')
        exit(1)
    
    # 检查数据量
    device_count = cursor.execute('SELECT COUNT(*) FROM devices').fetchone()[0]
    backup_count = cursor.execute('SELECT COUNT(*) FROM backups').fetchone()[0]
    
    print(f'设备: {device_count}, 备份: {backup_count}')
    
    if device_count == 0 and backup_count > 0:
        print('数据异常: 设备数为0但备份数不为0')
        exit(1)
    
    conn.close()
    exit(0)
except Exception as e:
    print(f'检查失败: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "数据完整性检查通过"
        return 0
    else
        log_warning "数据完整性检查失败"
        return 1
    fi
}

# 创建数据备份
create_backup() {
    log_info "创建数据备份..."
    
    backup_dir="data/auto_backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 备份数据库
    if [ -f "data/xconfkit.db" ]; then
        cp "data/xconfkit.db" "$backup_dir/"
        log_success "数据库已备份到 $backup_dir/"
    fi
    
    # 备份配置文件
    if [ -d "data/backups" ]; then
        cp -r "data/backups" "$backup_dir/"
        log_success "备份文件已复制到 $backup_dir/"
    fi
    
    echo "$backup_dir"
}

# 从备份恢复
restore_from_backup() {
    log_info "尝试从备份恢复..."
    
    backup_base="data/auto_backups"
    if [ ! -d "$backup_base" ]; then
        log_error "没有找到备份目录"
        return 1
    fi
    
    # 找到最新的备份
    latest_backup=$(ls -t "$backup_base" | head -1)
    if [ -z "$latest_backup" ]; then
        log_error "没有找到备份"
        return 1
    fi
    
    backup_path="$backup_base/$latest_backup"
    log_info "使用备份: $latest_backup"
    
    # 恢复数据库
    if [ -f "$backup_path/xconfkit.db" ]; then
        cp "$backup_path/xconfkit.db" "data/xconfkit.db"
        log_success "数据库已恢复"
    fi
    
    # 恢复备份文件
    if [ -d "$backup_path/backups" ]; then
        rm -rf "data/backups" 2>/dev/null || true
        cp -r "$backup_path/backups" "data/"
        log_success "备份文件已恢复"
    fi
    
    return 0
}

# 停止现有服务
stop_existing_services() {
    log_info "停止现有服务..."
    
    # 停止后端服务
    if [ -f ".backend.pid" ]; then
        backend_pid=$(cat .backend.pid)
        if kill -0 "$backend_pid" 2>/dev/null; then
            kill "$backend_pid"
            log_info "后端服务已停止 (PID: $backend_pid)"
        fi
        rm -f .backend.pid
    fi
    
    # 停止前端服务
    if [ -f ".frontend.pid" ]; then
        frontend_pid=$(cat .frontend.pid)
        if kill -0 "$frontend_pid" 2>/dev/null; then
            kill "$frontend_pid"
            log_info "前端服务已停止 (PID: $frontend_pid)"
        fi
        rm -f .frontend.pid
    fi
    
    # 等待端口释放
    sleep 2
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    # 检查端口是否可用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "端口 8000 已被占用"
        return 1
    fi
    
    # 启动后端
    cd backend
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    backend_pid=$!
    echo $backend_pid > ../.backend.pid
    cd ..
    
    # 等待服务启动
    log_info "等待后端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            log_success "后端服务启动成功 (PID: $backend_pid)"
            return 0
        fi
        sleep 1
    done
    
    log_error "后端服务启动超时"
    return 1
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    
    # 检查端口是否可用
    if lsof -Pi :5174 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_error "端口 5174 已被占用"
        return 1
    fi
    
    # 启动前端
    cd frontend
    nohup npm run dev > ../frontend.log 2>&1 &
    frontend_pid=$!
    echo $frontend_pid > ../.frontend.pid
    cd ..
    
    # 等待服务启动
    log_info "等待前端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:5174 >/dev/null 2>&1; then
            log_success "前端服务启动成功 (PID: $frontend_pid)"
            return 0
        fi
        sleep 1
    done
    
    log_error "前端服务启动超时"
    return 1
}

# 验证服务状态
verify_services() {
    log_info "验证服务状态..."
    
    # 检查后端
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_success "后端服务正常"
    else
        log_error "后端服务异常"
        return 1
    fi
    
    # 检查前端
    if curl -s http://localhost:5174 >/dev/null; then
        log_success "前端服务正常"
    else
        log_error "前端服务异常"
        return 1
    fi
    
    return 0
}

# 主函数
main() {
    echo "=========================================="
    echo "XConfKit 安全启动脚本"
    echo "=========================================="
    
    # 1. 检查环境
    check_python
    
    # 2. 检查数据完整性
    if ! check_data_integrity; then
        log_warning "数据完整性检查失败"
        
        # 尝试从备份恢复
        if restore_from_backup; then
            log_success "数据已从备份恢复"
        else
            log_warning "无法从备份恢复，将使用当前数据"
        fi
    fi
    
    # 3. 创建当前状态备份
    backup_dir=$(create_backup)
    
    # 4. 停止现有服务
    stop_existing_services
    
    # 5. 启动后端服务
    if ! start_backend; then
        log_error "后端服务启动失败"
        exit 1
    fi
    
    # 6. 启动前端服务
    if ! start_frontend; then
        log_error "前端服务启动失败"
        exit 1
    fi
    
    # 7. 验证服务状态
    if ! verify_services; then
        log_error "服务验证失败"
        exit 1
    fi
    
    echo "=========================================="
    echo "🎉 所有服务启动完成！"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo "  前端界面: http://localhost:5174"
    echo "  后端API:  http://localhost:8000"
    echo "  API文档:  http://localhost:8000/docs"
    echo ""
    echo "停止服务:"
    echo "  ./stop_services.sh"
    echo ""
    echo "安全重启:"
    echo "  ./start_services_safe.sh"
    echo ""
    echo "数据备份位置:"
    echo "  $backup_dir"
    echo "=========================================="
}

# 执行主函数
main "$@"
