# XConfKit 安装指南

## 🚀 快速安装

### Ubuntu 系统（推荐）

```bash
# 下载项目
git clone <repository-url>
cd XConfKit202508

# 一键安装
./install.sh
```

## 📋 系统要求

- **操作系统**: Ubuntu 18.04 或更高版本
- **内存**: 至少 1GB RAM
- **磁盘空间**: 至少 1GB 可用空间
- **网络**: 稳定的网络连接（支持外网访问）

## 🔧 安装过程详解

### 1. 系统检查
- 验证是否为Ubuntu系统
- 检查用户权限（不能使用root用户）
- 检查磁盘空间（至少1GB）

### 2. 网络检测
- 检测网络连接状态
- 如遇网络问题会给出明确提示
- 用户可选择继续或取消安装

### 3. 系统包更新
- 自动配置apt镜像源（清华大学镜像）
- 更新系统包列表
- 支持重试机制

### 4. 基础依赖安装
安装以下系统包：
- `curl`, `wget`, `git`, `unzip`
- `build-essential` (编译工具)
- `python3`, `python3-pip`, `python3-venv`
- `nodejs`, `npm`
- `sqlite3`, `openssh-client`

### 5. Python环境配置
- 创建Python虚拟环境
- 配置pip镜像源（清华大学镜像）
- 安装Python依赖包
- 支持失败重试和手动安装

### 6. Node.js环境配置
- 配置npm镜像源（淘宝镜像）
- 清理npm缓存
- 安装Node.js依赖包
- 支持失败重试和手动安装

### 7. 环境设置
- 创建必要目录（data/backups, logs, backups）
- 设置脚本执行权限
- 初始化数据库

## 🌐 网络优化

### 中国大陆用户
安装脚本已针对中国大陆网络环境进行优化：

- **apt镜像源**: 清华大学镜像
- **pip镜像源**: 清华大学镜像
- **npm镜像源**: 淘宝镜像

### 网络问题处理
如果遇到网络问题：

1. **检查网络连接**
   ```bash
   ping 8.8.8.8
   ```

2. **手动配置镜像源**
   ```bash
   # apt镜像源
   sudo sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
   
   # pip镜像源
   pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   
   # npm镜像源
   npm config set registry https://registry.npmmirror.com
   ```

3. **使用代理**
   ```bash
   # 设置HTTP代理
   export http_proxy=http://proxy.example.com:8080
   export https_proxy=http://proxy.example.com:8080
   ```

## 📊 安装日志

安装过程会生成详细的日志文件：

- `install.log`: 安装过程日志
- `install_errors.log`: 错误日志

查看日志：
```bash
# 查看安装日志
cat install.log

# 查看错误日志
cat install_errors.log
```

## ⚠️ 常见问题

### 1. 权限问题
**错误**: `请不要使用root用户运行此脚本`

**解决**: 使用普通用户运行，脚本会自动请求sudo权限

### 2. 网络连接问题
**错误**: `网络连接异常，可能影响安装`

**解决**: 
- 检查网络连接
- 配置代理
- 或选择继续安装（部分功能可能受影响）

### 3. 磁盘空间不足
**错误**: `磁盘空间不足，需要至少1GB可用空间`

**解决**: 清理磁盘空间或增加磁盘容量

### 4. Python包安装失败
**错误**: `Python包安装失败`

**解决**:
- 检查网络连接
- 手动安装关键包：
  ```bash
  source .venv/bin/activate
  pip install fastapi uvicorn sqlalchemy paramiko pydantic ping3
  ```

### 5. npm包安装失败
**错误**: `npm包安装失败`

**解决**:
- 检查网络连接
- 手动安装关键包：
  ```bash
  cd frontend
  npm install react react-dom react-router-dom antd @ant-design/icons axios dayjs vite
  ```

## 🎯 安装完成

安装成功后，您将看到：

```
==========================================
🎉 XConfKit 安装完成！
==========================================
📋 下一步操作:
  🚀 启动服务: ./start_services.sh
  🌐 访问系统: http://localhost:5174
  📚 API文档: http://localhost:8000/docs
```

## 🚀 启动服务

```bash
# 启动所有服务
./start_services.sh

# 检查服务状态
./check_status.sh

# 停止服务
./stop_services.sh
```

## 📞 技术支持

如果安装过程中遇到问题：

1. 查看安装日志文件
2. 检查系统要求和网络连接
3. 参考常见问题解决方案
4. 提交Issue或联系技术支持
