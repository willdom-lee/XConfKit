# XConfKit 服务管理指南

本文档介绍如何使用 XConfKit 的服务管理脚本，这些脚本经过优化，能够处理端口占用、进程清理等常见问题。

## 脚本概览

| 脚本 | 功能 | 特点 |
|------|------|------|
| `start_services.sh` | 启动所有服务 | 自动检查端口、清理进程、健康检查 |
| `stop_services.sh` | 停止所有服务 | 优雅停止、强制清理、状态验证 |
| `restart_services.sh` | 重启所有服务 | 一键重启、可选日志清理 |
| `check_status.sh` | 检查服务状态 | 详细状态报告、资源监控 |

## 使用方法

### 1. 启动服务

```bash
# 基本启动
./start_services.sh

# 启动时会自动：
# - 检查并释放被占用的端口
# - 清理残留进程
# - 验证服务健康状态
# - 生成详细日志
```

**启动流程：**
1. 检查项目目录
2. 停止现有服务
3. 检查端口可用性
4. 启动后端服务（端口8000）
5. 启动前端服务（端口5173）
6. 验证服务健康状态
7. 显示访问地址

### 2. 停止服务

```bash
# 基本停止
./stop_services.sh

# 停止并清理日志
./stop_services.sh --clean-logs
```

**停止流程：**
1. 清理PID文件中的进程
2. 停止特定进程模式
3. 释放端口上的进程
4. 验证服务状态
5. 必要时执行强制清理

### 3. 重启服务

```bash
# 基本重启
./restart_services.sh

# 重启并清理日志
./restart_services.sh --clean-logs
```

**重启流程：**
1. 停止现有服务
2. 等待端口释放
3. 可选清理日志
4. 启动服务
5. 显示状态信息

### 4. 检查服务状态

```bash
# 基本状态检查
./check_status.sh

# 详细状态检查（包含日志）
./check_status.sh --show-logs
```

**检查内容：**
- 进程运行状态
- 端口监听状态
- 服务健康检查
- PID文件状态
- 日志文件状态
- 系统资源使用

## 健壮性特性

### 端口管理
- **自动检测**：启动前检查端口是否被占用
- **智能释放**：自动释放被占用的端口
- **优雅停止**：先尝试优雅停止，再强制终止
- **状态验证**：验证端口是否真正释放

### 进程管理
- **多模式检测**：通过进程名、PID文件、端口等多种方式检测
- **优雅停止**：先发送TERM信号，等待进程自行停止
- **强制清理**：必要时使用KILL信号强制终止
- **状态验证**：验证进程是否真正停止

### 错误处理
- **信号处理**：捕获中断信号，确保清理工作完成
- **详细日志**：记录所有操作步骤和错误信息
- **状态反馈**：实时显示操作进度和结果
- **故障恢复**：启动失败时自动清理已启动的服务

### 健康检查
- **服务验证**：通过HTTP请求验证服务是否正常响应
- **重试机制**：多次尝试连接，避免偶发性失败
- **超时控制**：设置合理的超时时间
- **详细报告**：显示具体的失败原因

## 日志管理

### 日志文件
- `backend.log`：后端服务日志
- `frontend.log`：前端服务日志

### 查看日志
```bash
# 实时查看后端日志
tail -f backend.log

# 实时查看前端日志
tail -f frontend.log

# 查看最后N行
tail -20 backend.log
```

### 清理日志
```bash
# 停止时清理日志
./stop_services.sh --clean-logs

# 重启时清理日志
./restart_services.sh --clean-logs

# 手动清理
rm -f backend.log frontend.log
```

## 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173

# 手动释放端口
sudo lsof -ti:8000 | xargs kill -9
```

#### 2. 进程无法停止
```bash
# 查看进程
ps aux | grep -E "(python3 start_backend.py|npm run dev)"

# 强制终止
pkill -f "python3 start_backend.py"
pkill -f "npm run dev"
```

#### 3. 服务启动失败
```bash
# 查看启动日志
tail -20 backend.log
tail -20 frontend.log

# 检查依赖
python3 -c "import fastapi, uvicorn"
cd frontend && npm list
```

### 调试模式

如果需要更详细的调试信息，可以手动运行：

```bash
# 后端调试
python3 start_backend.py

# 前端调试
cd frontend && npm run dev
```

## 配置说明

### 端口配置
在脚本中修改以下变量来更改端口：

```bash
# start_services.sh, stop_services.sh, check_status.sh
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

### 超时配置
```bash
# 健康检查超时
MAX_RETRIES=3
WAIT_TIME=5

# 进程停止超时
MAX_WAIT_TIME=30
```

## 最佳实践

1. **启动前检查**：使用 `./check_status.sh` 检查当前状态
2. **优雅停止**：使用 `./stop_services.sh` 而不是直接kill进程
3. **日志监控**：定期查看日志文件，及时发现问题
4. **定期重启**：使用 `./restart_services.sh --clean-logs` 定期清理
5. **备份配置**：修改配置前备份相关文件

## 安全注意事项

1. **权限控制**：确保脚本有适当的执行权限
2. **端口安全**：避免使用特权端口（<1024）
3. **日志安全**：定期清理日志文件，避免磁盘空间不足
4. **进程安全**：避免在生产环境中使用强制终止

## 更新日志

- **v2.0**：添加健壮性特性，支持端口自动释放和进程管理
- **v1.0**：基础启动和停止功能
