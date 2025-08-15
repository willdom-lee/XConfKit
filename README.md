# XConfKit MVP

一个自动备份Cisco-like网络设备配置的MVP系统。

## 功能特性

### MVP版本功能
- ✅ 设备管理（增删改查）
- ✅ 手动备份（SSH连接）
- ✅ 本地存储备份文件
- ✅ 简单Web界面
- ✅ 完整的测试覆盖

### 后续版本功能
- 🔄 自动备份（定时任务）
- 🔄 FTP上传
- 🔄 AI配置评估
- 🔄 更多配置备份

## 技术栈

- **后端**: FastAPI + SQLite + paramiko
- **前端**: React + Vite
- **部署**: Linux/macOS环境，一键安装脚本

## 快速开始

### 方式一：开发环境启动（推荐）

```bash
# 1. 运行开发环境启动脚本
./start_dev.sh

# 2. 启动后端服务
python3 start_backend.py

# 3. 启动前端服务（新终端）
cd frontend
npm run dev
```

### 方式二：手动启动

```bash
# 1. 安装后端依赖
pip3 install -r requirements.txt

# 2. 安装前端依赖
cd frontend
npm install
cd ..

# 3. 启动后端服务
python3 start_backend.py

# 4. 启动前端服务（新终端）
cd frontend
npm run dev
```

### 方式三：生产环境部署

```bash
# 一键安装（Linux/macOS）
sudo ./install.sh

# 启动系统服务
sudo systemctl start xconfkit

# 查看服务状态
sudo systemctl status xconfkit
```

### 访问应用
- 前端界面: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 项目结构

```
XConfKit202508/
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI主程序
│   ├── models.py           # 数据模型
│   ├── database.py         # 数据库配置
│   ├── schemas.py          # Pydantic模型
│   ├── routers/            # API路由
│   │   ├── devices.py      # 设备管理API
│   │   └── backups.py      # 备份管理API
│   └── services/           # 业务逻辑
│       ├── device_service.py
│       └── backup_service.py
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── services/       # API服务
│   │   └── App.jsx         # 主应用
│   ├── package.json
│   └── vite.config.js
├── data/                   # 数据存储
│   ├── xconfkit.db        # SQLite数据库
│   └── backups/           # 备份文件存储
├── tests/                  # 测试代码
│   ├── backend/           # 后端测试
│   ├── frontend/          # 前端测试
│   └── integration_test.py
├── requirements.txt        # Python依赖
├── start_backend.py       # 后端启动脚本
├── start_dev.sh           # 开发环境启动脚本
├── install.sh             # 生产环境安装脚本
└── run_tests.py           # 测试运行脚本
```

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的API文档。

### 主要API端点

- `GET /health` - 健康检查
- `GET /` - API根路径
- `GET /docs` - API文档

#### 设备管理
- `GET /devices/` - 获取设备列表
- `POST /devices/` - 创建设备
- `GET /devices/{device_id}` - 获取设备详情
- `PUT /devices/{device_id}` - 更新设备
- `DELETE /devices/{device_id}` - 删除设备
- `POST /devices/{device_id}/test` - 测试设备连接

#### 备份管理
- `GET /backups/` - 获取备份列表
- `POST /backups/` - 执行备份
- `GET /backups/{backup_id}` - 获取备份详情
- `GET /backups/{backup_id}/download` - 下载备份文件

## 测试

### 运行测试

```bash
# 运行完整测试套件
python3 run_tests.py

# 运行后端测试
python3 -m pytest tests/backend/ -v

# 运行集成测试
python3 tests/integration_test.py

# 运行前端测试
cd frontend
npm test
```

### 测试覆盖

- ✅ 后端单元测试: 24/24 通过
- ✅ 集成测试: 3/3 通过
- ✅ API 测试: 12/12 通过
- ✅ 服务层测试: 12/12 通过

详细测试报告请查看 [TEST_REPORT.md](TEST_REPORT.md)

## 开发指南

### 后端开发

```bash
# 启动开发服务器（自动重载）
python3 start_backend.py

# 运行特定测试
python3 -m pytest tests/backend/test_api.py -v
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 部署

### 开发环境
使用 `start_dev.sh` 脚本快速设置开发环境。

### 生产环境
使用 `install.sh` 脚本进行生产环境部署，支持：
- 自动安装依赖
- 创建系统服务
- 配置开机自启

## 项目状态

### MVP版本功能 ✅
- 设备管理（增删改查）
- 手动备份（SSH连接）
- 本地存储备份文件
- 简单Web界面
- 完整的测试覆盖
- 生产环境部署支持

### 后续版本功能 🔄
- 自动备份（定时任务）
- FTP上传
- AI配置评估
- 更多配置备份
- 用户认证和权限管理
- 备份文件加密
- 邮件通知功能

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
