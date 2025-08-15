# XConfKit 服务管理快速指南

## 🚀 快速开始

### 启动服务
```bash
./start_services.sh
```

### 停止服务
```bash
./stop_services.sh
```

### 重启服务
```bash
./restart_services.sh
```

### 检查状态
```bash
./check_status.sh
```

## 📋 服务信息

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🔧 高级功能

### 清理日志重启
```bash
./restart_services.sh --clean-logs
```

### 查看详细状态（包含日志）
```bash
./check_status.sh --show-logs
```

### 停止并清理日志
```bash
./stop_services.sh --clean-logs
```

## 📝 日志查看

```bash
# 实时查看后端日志
tail -f backend.log

# 实时查看前端日志
tail -f frontend.log
```

## ⚠️ 故障排除

如果遇到端口占用问题，脚本会自动处理。如需手动处理：

```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173

# 强制释放端口
sudo lsof -ti:8000 | xargs kill -9
```

## 📖 详细文档

更多详细信息请查看 [SERVICE_MANAGEMENT.md](./SERVICE_MANAGEMENT.md)
