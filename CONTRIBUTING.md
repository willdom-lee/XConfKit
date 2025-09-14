# 贡献指南

感谢您对 XConfKit 项目的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请：

1. 检查 [Issues](https://github.com/willdom-lee/XConfKit/issues) 中是否已有类似问题
2. 如果没有，请创建新的 Issue，包含：
   - 详细的问题描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 系统环境信息

### 提交代码

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/XConfKit.git
   cd XConfKit
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **安装依赖**
   ```bash
   # 后端依赖
   pip install -r requirements.txt
   
   # 前端依赖
   cd frontend
   npm install
   cd ..
   ```

4. **运行测试**
   ```bash
   # 运行所有测试
   python run_tests.py
   
   # 运行特定测试
   python -m pytest tests/backend/ -v
   cd frontend && npm test
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**

## 代码规范

### Python 代码
- 遵循 PEP 8 规范
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串
- 确保所有测试通过

### JavaScript/React 代码
- 使用 ESLint 检查代码风格
- 组件名使用 PascalCase
- 函数和变量使用 camelCase
- 添加适当的 PropTypes 或 TypeScript 类型

### 提交信息规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 开发环境设置

### 后端开发
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python start_backend.py
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 数据库
项目使用 SQLite 数据库，首次运行会自动创建。

## 测试

### 后端测试
```bash
# 运行所有后端测试
python -m pytest tests/backend/ -v

# 运行特定测试文件
python -m pytest tests/backend/test_api.py -v

# 运行集成测试
python tests/integration_test.py
```

### 前端测试
```bash
cd frontend
npm test
```

## 文档

- 更新相关文档
- 添加代码注释
- 更新 README.md（如需要）

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

## 联系方式

如有问题，请通过以下方式联系：

- 创建 [Issue](https://github.com/willdom-lee/XConfKit/issues)
- 发送邮件至：willdom_lee@icloud.com

感谢您的贡献！🎉
