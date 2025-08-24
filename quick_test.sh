#!/bin/bash

# XConfKit 快速测试脚本
# 用于快速验证核心功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}🚀 $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_section() {
    echo -e "\n${YELLOW}📋 $1${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 检查服务状态
check_service() {
    print_section "检查服务状态"
    
    # 检查后端服务
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "后端服务运行正常"
        return 0
    else
        print_error "后端服务未运行"
        return 1
    fi
}

# 快速API测试
quick_api_test() {
    print_section "快速API测试"
    
    local base_url="http://localhost:8000"
    local test_count=0
    local success_count=0
    
    # 测试健康检查
    test_count=$((test_count + 1))
    if curl -s "$base_url/health" | grep -q "healthy"; then
        print_success "健康检查API正常"
        success_count=$((success_count + 1))
    else
        print_error "健康检查API失败"
    fi
    
    # 测试设备API
    test_count=$((test_count + 1))
    if curl -s "$base_url/api/devices/" > /dev/null 2>&1; then
        print_success "设备API正常"
        success_count=$((success_count + 1))
    else
        print_error "设备API失败"
    fi
    
    # 测试配置API
    test_count=$((test_count + 1))
    if curl -s "$base_url/api/configs/categories" > /dev/null 2>&1; then
        print_success "配置API正常"
        success_count=$((success_count + 1))
    else
        print_error "配置API失败"
    fi
    
    # 测试备份API
    test_count=$((test_count + 1))
    if curl -s "$base_url/api/backups/" > /dev/null 2>&1; then
        print_success "备份API正常"
        success_count=$((success_count + 1))
    else
        print_error "备份API失败"
    fi
    
    # 测试策略API
    test_count=$((test_count + 1))
    if curl -s "$base_url/api/strategies/" > /dev/null 2>&1; then
        print_success "策略API正常"
        success_count=$((success_count + 1))
    else
        print_error "策略API失败"
    fi
    
    # 测试AI分析API
    test_count=$((test_count + 1))
    if curl -s "$base_url/api/analysis/config/ai" > /dev/null 2>&1; then
        print_success "AI分析API正常"
        success_count=$((success_count + 1))
    else
        print_error "AI分析API失败"
    fi
    
    echo -e "\n${BLUE}API测试结果: $success_count/$test_count 通过${NC}"
    
    if [ $success_count -eq $test_count ]; then
        return 0
    else
        return 1
    fi
}

# 数据库连接测试
test_database() {
    print_section "数据库连接测试"
    
    if [ -f "data/xconfkit.db" ]; then
        print_success "数据库文件存在"
        
        # 检查数据库完整性
        if sqlite3 data/xconfkit.db "SELECT COUNT(*) FROM devices;" > /dev/null 2>&1; then
            print_success "数据库连接正常"
            return 0
        else
            print_error "数据库连接失败"
            return 1
        fi
    else
        print_error "数据库文件不存在"
        return 1
    fi
}

# 前端构建测试
test_frontend_build() {
    print_section "前端构建测试"
    
    if [ ! -d "frontend" ]; then
        print_warning "前端目录不存在，跳过前端测试"
        return 0
    fi
    
    cd frontend
    
    # 检查依赖
    if [ ! -d "node_modules" ]; then
        print_warning "前端依赖未安装，尝试安装..."
        if npm install > /dev/null 2>&1; then
            print_success "前端依赖安装成功"
        else
            print_error "前端依赖安装失败"
            cd ..
            return 1
        fi
    fi
    
    # 测试构建
    if npm run build > /dev/null 2>&1; then
        print_success "前端构建成功"
        cd ..
        return 0
    else
        print_error "前端构建失败"
        cd ..
        return 1
    fi
}

# 性能测试
performance_test() {
    print_section "性能测试"
    
    local base_url="http://localhost:8000"
    local total_time=0
    local test_count=5
    
    for i in $(seq 1 $test_count); do
        local start_time=$(date +%s%N)
        curl -s "$base_url/api/devices/" > /dev/null 2>&1
        local end_time=$(date +%s%N)
        local duration=$(((end_time - start_time) / 1000000))  # 转换为毫秒
        total_time=$((total_time + duration))
        echo "  测试 $i: ${duration}ms"
    done
    
    local avg_time=$((total_time / test_count))
    echo -e "\n平均响应时间: ${avg_time}ms"
    
    if [ $avg_time -lt 1000 ]; then
        print_success "性能表现良好"
        return 0
    elif [ $avg_time -lt 3000 ]; then
        print_warning "性能需要优化"
        return 0
    else
        print_error "性能较差"
        return 1
    fi
}

# 安全测试
security_test() {
    print_section "安全测试"
    
    local base_url="http://localhost:8000"
    local security_issues=0
    
    # 测试SQL注入防护
    if curl -s "$base_url/api/devices/';%20DROP%20TABLE%20devices;--" | grep -q "404"; then
        print_success "SQL注入防护正常"
    else
        print_error "SQL注入防护可能存在问题"
        security_issues=$((security_issues + 1))
    fi
    
    # 测试XSS防护
    if curl -s -X POST "$base_url/api/devices/" \
        -H "Content-Type: application/json" \
        -d '{"name":"<script>alert(\"xss\")</script>","ip_address":"192.168.1.100"}' | grep -q "422"; then
        print_success "XSS防护正常"
    else
        print_error "XSS防护可能存在问题"
        security_issues=$((security_issues + 1))
    fi
    
    if [ $security_issues -eq 0 ]; then
        print_success "安全测试通过"
        return 0
    else
        print_error "发现 $security_issues 个安全问题"
        return 1
    fi
}

# 主函数
main() {
    print_header "XConfKit 快速测试"
    
    local total_tests=0
    local passed_tests=0
    
    # 检查服务状态
    total_tests=$((total_tests + 1))
    if check_service; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 快速API测试
    total_tests=$((total_tests + 1))
    if quick_api_test; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 数据库测试
    total_tests=$((total_tests + 1))
    if test_database; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 前端构建测试
    total_tests=$((total_tests + 1))
    if test_frontend_build; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 性能测试
    total_tests=$((total_tests + 1))
    if performance_test; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 安全测试
    total_tests=$((total_tests + 1))
    if security_test; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 输出结果
    print_header "测试结果汇总"
    echo -e "总测试数: $total_tests"
    echo -e "通过: $passed_tests"
    echo -e "失败: $((total_tests - passed_tests))"
    
    local success_rate=$((passed_tests * 100 / total_tests))
    echo -e "成功率: ${success_rate}%"
    
    if [ $success_rate -ge 80 ]; then
        print_success "快速测试通过！系统状态良好"
        exit 0
    elif [ $success_rate -ge 60 ]; then
        print_warning "快速测试完成！系统需要改进"
        exit 0
    else
        print_error "快速测试失败！系统存在严重问题"
        exit 1
    fi
}

# 运行主函数
main "$@"
