# XConfKit 快速开始指南

## 🚀 5分钟快速体验

### 1. 克隆项目
```bash
git clone https://github.com/willdom-lee/XConfKit.git
cd XConfKit
```

### 2. 一键启动
```bash
./start_services.sh
```

### 3. 访问系统
打开浏览器访问：http://localhost:5174

### 4. 添加测试设备
1. 点击"设备管理"
2. 点击"新增设备"
3. 填写设备信息（可以使用测试数据）
4. 点击"测试连接"验证

### 5. 执行备份
1. 点击"备份管理"
2. 选择设备和备份类型
3. 点击"执行备份"

## 📋 系统要求

### 最低要求
- **操作系统**: macOS 10.15+, Ubuntu 18.04+, CentOS 7+
- **Python**: 3.8+
- **Node.js**: 16+
- **内存**: 2GB RAM
- **存储**: 1GB 可用空间

### 推荐配置
- **操作系统**: Ubuntu 20.04+ 或 macOS 12+
- **Python**: 3.9+
- **Node.js**: 18+
- **内存**: 4GB RAM
- **存储**: 5GB 可用空间

## 🔧 安装依赖

### 自动安装（推荐）
```bash
# Ubuntu系统
./install.sh

# 其他系统
pip install -r requirements.txt
cd frontend && npm install
```

### 手动安装
```bash
# Python依赖
pip install fastapi uvicorn sqlalchemy paramiko pydantic python-multipart python-dotenv aiofiles requests ping3 aiohttp apscheduler

# Node.js依赖
cd frontend
npm install react react-dom react-router-dom antd @ant-design/icons axios dayjs react-markdown remark-gfm vite
```

## 🌐 访问地址

- **前端界面**: http://localhost:5174
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## ⚠️ 重要提醒

**本项目为演示版本，请注意：**
- 仅在H3C设备上测试过
- 其他设备兼容性待验证
- 建议在测试环境使用
- 生产环境使用前请充分测试

## 🆘 遇到问题？

1. **查看日志**
   ```bash
   tail -f backend.log
   tail -f frontend.log
   ```

2. **检查服务状态**
   ```bash
   ./check_status.sh
   ```

3. **重启服务**
   ```bash
   ./restart_services.sh
   ```

4. **提交Issue**
   - 访问：https://github.com/willdom-lee/XConfKit/issues
   - 详细描述问题和环境信息

## 📚 更多信息

- **完整文档**: [README.md](README.md)
- **安装指南**: [INSTALL.md](INSTALL.md)
- **贡献指南**: [CONTRIBUTING.md](CONTRIBUTING.md)
