# XConfKit - 网络设备配置备份管理系统

一个功能完整的网络设备配置备份管理系统，支持SSH连接、自动备份、策略调度等功能。

## ⚠️ 重要说明

**本项目目前处于演示版本状态，请注意以下事项：**

- 🧪 **测试范围有限**: 目前仅在H3C设备上进行过真实测试，其他厂商设备（如Cisco、华为等）的兼容性尚未验证
- 🔧 **功能完整性**: 系统功能仍在开发完善中，可能存在未发现的bug或不稳定因素
- 🚀 **生产环境**: 建议仅在测试环境中使用，生产环境使用前请充分测试
- 📝 **反馈欢迎**: 如发现问题或有改进建议，欢迎提交Issue或Pull Request

**支持的设备类型（理论支持，需实际测试验证）：**
- H3C设备 ✅ (已测试)
- Cisco设备 ⚠️ (理论支持，未测试)
- 华为设备 ⚠️ (理论支持，未测试)
- 其他SSH设备 ⚠️ (理论支持，未测试)
或者## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/willdom-lee/XConfKit.git
cd XConfKit
```

### 2. 一键启动（推荐）
```bash
./start_services.sh
```

### 3. 访问系统
- **前端界面**: http://localhost:5174
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 开发环境启动
```bash
./start_dev.sh
```

### 生产环境部署

#### Ubuntu 系统安装
```bash
# 一键安装（推荐）
./install.sh
```

**安装脚本特性：**
- ✅ **专为中国大陆网络环境优化**：自动配置国内镜像源
- ✅ **完善的错误处理**：自动重试机制，详细的错误日志
- ✅ **网络检测**：安装前检测网络连接状态
- ✅ **健壮的依赖安装**：支持pip和npm安装失败后的手动安装
- ✅ **系统检查**：自动检查系统环境、磁盘空间等

**安装过程：**
1. 系统环境检查（Ubuntu系统、用户权限、磁盘空间）
2. 网络连接检测
3. 配置apt镜像源（清华大学镜像）
4. 安装基础依赖（Python、Node.js、SQLite等）
5. 配置pip镜像源（清华大学镜像）
6. 安装Python依赖包
7. 配置npm镜像源（淘宝镜像）
8. 安装Node.js依赖包
9. 初始化数据库
10. 设置环境权限

**注意事项：**
- 需要sudo权限（脚本会自动请求）
- 建议在网络稳定的环境下安装
- 如遇网络问题，脚本会给出明确提示
- 安装日志保存在 `install.log` 和 `install_errors.log`

**详细安装指南请参考**: [INSTALL.md](INSTALL.md)

### 访问应用
- **前端界面**: http://localhost:5174
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📋 功能特性

### 核心功能
- ✅ **设备管理**: SSH连接支持，设备增删改查，连接测试
- ✅ **备份管理**: 多种配置类型备份，文件下载，记录筛选，批量删除
- ✅ **备份策略**: 一次性/周期性策略，自动调度执行
- ✅ **立即执行**: 策略立即执行功能，不影响调度
- ✅ **AI配置分析**: 智能分析网络设备配置，支持多维度分析
- ✅ **系统配置**: 完整的系统参数配置，支持AI服务配置
- ✅ **服务管理**: 健壮的启动/停止/重启脚本
- ✅ **时间统一**: 所有时间使用北京时间，格式统一

### 技术特性
- ✅ **跨平台支持**: macOS、Ubuntu、CentOS等
- ✅ **一键部署**: 自动化安装脚本
- ✅ **完整测试**: 单元测试、集成测试、API测试
- ✅ **备份恢复**: 代码备份和恢复功能
- ✅ **错误处理**: 完善的异常处理和日志记录
- ✅ **AI集成**: 集成阿里云通义千问AI服务
- ✅ **Markdown渲染**: 美观的分析结果展示
- ✅ **用户自定义**: 支持自定义AI分析提示词

## 🛠️ 技术栈

- **后端**: FastAPI + SQLAlchemy + Paramiko + SQLite
- **前端**: React + Ant Design + Vite + React Markdown
- **AI服务**: 阿里云通义千问API
- **调度器**: 后台线程自动执行策略
- **部署**: 跨平台支持，一键安装脚本

## 📁 项目结构

```
XConfKit202508/
├── backend/                 # 后端代码
│   ├── main.py             # FastAPI主程序
│   ├── models.py           # 数据模型
│   ├── database.py         # 数据库配置
│   ├── schemas.py          # Pydantic模型
│   ├── scheduler.py        # 备份策略调度器
│   ├── routers/            # API路由
│   │   ├── devices.py      # 设备管理API
│   │   ├── backups.py      # 备份管理API
│   │   ├── strategies.py   # 策略管理API
│   │   ├── configs.py      # 系统配置API
│   │   └── analysis.py     # AI分析API
│   └── services/           # 业务逻辑
│       ├── device_service.py
│       ├── backup_service.py
│       ├── strategy_service.py
│       ├── config_service.py
│       └── ai_service.py
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React组件
│   │   │   ├── DeviceList.jsx
│   │   │   ├── BackupManagement.jsx
│   │   │   ├── StrategyManagement.jsx
│   │   │   ├── AIConfigAnalysis.jsx
│   │   │   ├── SystemConfig.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── services/       # API服务
│   │   └── App.jsx         # 主应用
│   ├── package.json
│   └── vite.config.js
├── data/                   # 数据存储
│   ├── xconfkit.db        # SQLite数据库
│   └── backups/           # 备份文件存储
├── backups/               # 代码备份
├── tests/                  # 测试代码
│   ├── backend/           # 后端测试
│   ├── frontend/          # 前端测试
│   └── integration_test.py
├── requirements.txt        # Python依赖
├── start_services.sh      # 服务启动脚本
├── stop_services.sh       # 服务停止脚本
├── restart_services.sh    # 服务重启脚本
├── check_status.sh        # 状态检查脚本
├── install.sh             # Ubuntu安装脚本（专为中国大陆网络环境优化）
├── backup_code.sh         # 代码备份脚本
├── restore_code.sh        # 代码恢复脚本
└── run_tests.py           # 测试运行脚本
```

## 🔧 服务管理

### 基本操作
```bash
# 启动服务
./start_services.sh

# 停止服务
./stop_services.sh

# 重启服务
./restart_services.sh

# 检查状态
./check_status.sh
```

### 高级操作
```bash
# 清理日志重启
./restart_services.sh --clean-logs

# 查看详细状态（包含日志）
./check_status.sh --show-logs

# 停止并清理日志
./stop_services.sh --clean-logs
```

### 日志查看
```bash
# 实时查看后端日志
tail -f backend.log

# 实时查看前端日志
tail -f frontend.log
```

## 📖 使用指南

### 1. 添加设备
1. 访问"设备管理"页面
2. 点击"新增设备"
3. 填写设备信息（名称、IP地址、用户名、密码）
4. 点击"测试连接"验证
5. 保存设备

### 2. 执行备份
1. 访问"备份管理"页面
2. 选择设备和备份类型
3. 点击"执行备份"
4. 查看备份结果

### 3. 创建备份策略
1. 访问"备份策略"页面
2. 点击"新增策略"
3. 选择策略类型（一次性/周期性）
4. 设置执行时间和频率
5. 保存策略

### 4. 管理备份记录
- 查看备份内容（支持滚动查看）
- 下载备份文件
- 筛选备份记录
- 批量删除备份记录

### 5. AI配置分析
1. 访问"AI分析"页面
2. 选择要分析的设备和备份文件
3. 选择分析维度（安全加固、冗余高可用、性能优化等）
4. 点击"开始分析"
5. 查看美观的Markdown格式分析结果

### 6. 系统配置
1. 访问"系统配置"页面
2. 配置AI服务参数（API密钥、模型等）
3. 自定义分析提示词
4. 调整系统参数（备份设置、连接超时等）
5. 保存配置

## 🔌 API文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的API文档。

### 主要API端点

#### 设备管理
- `GET /api/devices/` - 获取设备列表
- `POST /api/devices/` - 创建设备
- `GET /api/devices/{device_id}` - 获取设备详情
- `PUT /api/devices/{device_id}` - 更新设备
- `DELETE /api/devices/{device_id}` - 删除设备
- `POST /api/devices/{device_id}/test` - 测试设备连接

#### 备份管理
- `GET /api/backups/` - 获取备份列表
- `POST /api/backups/execute` - 执行备份
- `GET /api/backups/{backup_id}` - 获取备份详情
- `GET /api/backups/{backup_id}/download` - 下载备份文件
- `GET /api/backups/{backup_id}/content` - 查看备份内容
- `POST /api/backups/batch-delete` - 批量删除备份

#### 策略管理
- `GET /api/strategies/` - 获取策略列表
- `POST /api/strategies/` - 创建策略
- `GET /api/strategies/{strategy_id}` - 获取策略详情
- `PUT /api/strategies/{strategy_id}` - 更新策略
- `DELETE /api/strategies/{strategy_id}` - 删除策略
- `POST /api/strategies/{strategy_id}/toggle` - 切换策略状态
- `POST /api/strategies/{strategy_id}/execute-now` - 立即执行策略
- `GET /api/strategies/due/list` - 获取到期策略

#### AI分析
- `POST /api/analysis/analyze` - 执行AI配置分析
- `GET /api/analysis/history` - 获取分析历史
- `GET /api/analysis/record/{record_id}` - 获取分析结果
- `DELETE /api/analysis/record/{record_id}` - 删除分析记录
- `GET /api/analysis/config/ai` - 获取AI配置
- `POST /api/analysis/config/ai` - 保存AI配置
- `POST /api/analysis/config/ai/test` - 测试AI连接
- `GET /api/analysis/config/prompts` - 获取分析提示词
- `POST /api/analysis/config/prompts` - 保存分析提示词

#### 系统配置
- `GET /api/configs/categories` - 获取配置分类
- `POST /api/configs/batch-update` - 批量更新配置
- `GET /api/configs/category/{category}` - 获取分类配置
- `GET /api/configs/values/{category}` - 获取配置值

## 🧪 测试

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
- ✅ 调度器测试: 通过
- ✅ 策略管理测试: 通过
- ✅ AI分析测试: 通过
- ✅ 系统配置测试: 通过

## 🔒 安全特性

### SSH专用支持
- **统一使用SSH**: 所有设备连接都使用SSH协议
- **加密通信**: 所有数据传输都经过加密
- **身份验证**: 支持多种身份验证方式
- **现代标准**: 符合当前网络安全最佳实践

### AI分析安全
- **阿里云集成**: 使用阿里云通义千问AI服务，确保数据安全
- **本地处理**: 敏感配置数据在本地处理，不泄露到第三方
- **API密钥管理**: 安全的API密钥存储和管理
- **分析结果保护**: 分析结果本地存储，支持删除和清理

### 设备类型自动检测
系统支持以下设备类型的自动检测：

1. **H3C设备**
   - 检测命令：`display version`
   - 备份命令：`display current-configuration`, `display saved-configuration`等

2. **Cisco设备**
   - 检测命令：`show version`
   - 备份命令：`show running-config`, `show startup-config`等

3. **华为设备**
   - 检测命令：`display version`
   - 备份命令：`display current-configuration`, `display saved-configuration`等

## 📊 系统要求

### 最低要求
- **操作系统**: macOS 10.15+, Ubuntu 18.04+, CentOS 7+
- **Python**: 3.8+
- **Node.js**: 16+
- **内存**: 2GB RAM
- **存储**: 1GB 可用空间
- **网络**: 需要访问阿里云API服务

### 推荐配置
- **操作系统**: Ubuntu 20.04+ 或 macOS 12+
- **Python**: 3.9+
- **Node.js**: 18+
- **内存**: 4GB RAM
- **存储**: 5GB 可用空间
- **网络**: 稳定的互联网连接，用于AI分析

## 🚨 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查端口是否被占用
lsof -i :8000
lsof -i :5174

# 强制释放端口
sudo lsof -ti:8000 | xargs kill -9
```

#### 2. 设备连接失败
- 验证SSH连接信息
- 检查网络连通性
- 确认设备SSH服务正常运行

#### 3. 策略不执行
- 检查调度器是否启动
- 验证策略是否启用
- 查看后端日志中的调度器信息

#### 4. 时间显示错误
- 确认系统时区设置
- 检查系统时间是否正确

#### 5. AI分析失败
- 检查AI服务配置（API密钥、模型等）
- 验证网络连接是否正常
- 确认阿里云API服务状态
- 查看后端日志中的AI服务错误信息

### 日志查看
```bash
# 查看后端日志
tail -f backend.log

# 查看安装日志
cat install.log

# 查看错误日志
cat install_errors.log
```

## 🔄 代码备份

### 创建备份
```bash
./backup_code.sh
```

### 恢复备份
```bash
./restore_code.sh
```

## 📝 开发指南

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

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**最后更新**: 2025年9月14日  
**版本**: 1.0.0-demo  
**状态**: 演示版本，功能基本完整，建议测试环境使用  
**测试状态**: 仅在H3C设备上验证，其他设备兼容性待测试
