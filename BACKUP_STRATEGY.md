# 备份策略功能文档

## 概述

备份策略功能允许用户为网络设备创建自动化的备份计划，支持一次性备份和周期性备份两种模式。

## 功能特性

### 1. 策略类型

#### 一次性策略 (One-time Strategy)
- **用途**: 在指定时间执行一次备份
- **配置项**:
  - 策略名称
  - 设备选择
  - 备份类型
  - 计划执行时间
  - 策略描述（可选）

#### 周期性策略 (Recurring Strategy)
- **用途**: 按设定的频率定期执行备份
- **配置项**:
  - 策略名称
  - 设备选择
  - 备份类型
  - 频率类型（小时/天/月）
  - 频率值
  - 开始时间
  - 结束时间（可选）
  - 策略描述（可选）

### 2. 备份类型支持

- **运行配置** (running-config)
- **启动配置** (startup-config)
- **路由表** (ip-route)
- **ARP表** (arp-table)
- **MAC表** (mac-table)

### 3. 频率类型

- **小时** (hour): 每N小时执行一次
- **天** (day): 每N天执行一次
- **月** (month): 每N个月执行一次

## 数据库设计

### 备份策略表 (backup_strategies)

```sql
CREATE TABLE backup_strategies (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    device_id INTEGER NOT NULL,
    backup_type VARCHAR(20) DEFAULT 'running-config',
    strategy_type VARCHAR(20) NOT NULL,
    
    -- 一次性策略字段
    scheduled_time DATETIME,
    
    -- 周期性策略字段
    frequency_type VARCHAR(10),
    frequency_value INTEGER,
    start_time DATETIME,
    end_time DATETIME,
    last_execution DATETIME,
    next_execution DATETIME,
    
    -- 通用字段
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
```

## API接口

### 1. 创建策略
```http
POST /api/strategies/
Content-Type: application/json

{
    "name": "策略名称",
    "description": "策略描述",
    "device_id": 1,
    "backup_type": "running-config",
    "strategy_type": "one-time",
    "scheduled_time": "2024-01-01T10:00:00Z"
}
```

### 2. 获取策略列表
```http
GET /api/strategies/
```

### 3. 获取单个策略
```http
GET /api/strategies/{strategy_id}
```

### 4. 更新策略
```http
PUT /api/strategies/{strategy_id}
Content-Type: application/json

{
    "name": "更新后的策略名称",
    "description": "更新后的描述"
}
```

### 5. 删除策略
```http
DELETE /api/strategies/{strategy_id}
```

### 6. 切换策略状态
```http
POST /api/strategies/{strategy_id}/toggle
```

### 7. 执行策略
```http
POST /api/strategies/{strategy_id}/execute
```

### 8. 获取到期策略
```http
GET /api/strategies/due/list
```

## 前端界面

### 主要功能

1. **策略列表展示**
   - 策略名称和描述
   - 关联设备信息
   - 策略类型标识
   - 备份类型
   - 启用状态
   - 下次执行时间
   - 最后执行时间

2. **策略管理操作**
   - 新增策略
   - 编辑策略
   - 删除策略
   - 启用/禁用策略
   - 手动执行策略

3. **表单验证**
   - 必填字段验证
   - 时间有效性验证
   - 频率配置验证

### 界面特点

- **响应式设计**: 适配不同屏幕尺寸
- **直观操作**: 清晰的按钮和图标
- **实时反馈**: 操作结果即时提示
- **数据筛选**: 支持按设备、状态等筛选

## 使用示例

### 创建一次性策略

1. 点击"新增策略"按钮
2. 填写策略名称："设备配置备份"
3. 选择目标设备
4. 选择备份类型："运行配置"
5. 选择策略类型："一次性策略"
6. 设置执行时间：明天上午9点
7. 点击"保存"

### 创建周期性策略

1. 点击"新增策略"按钮
2. 填写策略名称："每日配置备份"
3. 选择目标设备
4. 选择备份类型："运行配置"
5. 选择策略类型："周期性策略"
6. 设置频率：每1天
7. 设置开始时间：明天上午9点
8. 设置结束时间：30天后（可选）
9. 点击"保存"

## 技术实现

### 后端架构

- **模型层**: SQLAlchemy ORM
- **服务层**: 业务逻辑处理
- **路由层**: FastAPI路由
- **验证层**: Pydantic模型验证

### 前端架构

- **组件**: React函数组件
- **状态管理**: React Hooks
- **UI库**: Ant Design
- **HTTP客户端**: Axios

### 关键算法

#### 下次执行时间计算

```python
def calculate_next_execution(last_execution, frequency_type, frequency_value):
    if frequency_type == "hour":
        return last_execution + timedelta(hours=frequency_value)
    elif frequency_type == "day":
        return last_execution + timedelta(days=frequency_value)
    elif frequency_type == "month":
        return last_execution + timedelta(days=frequency_value * 30)
```

#### 策略验证

```python
def validate_strategy(strategy):
    if strategy.strategy_type == "one-time":
        if not strategy.scheduled_time:
            return False, "一次性策略必须设置计划执行时间"
        if strategy.scheduled_time <= datetime.utcnow():
            return False, "计划执行时间不能早于当前时间"
    elif strategy.strategy_type == "recurring":
        if not strategy.frequency_type or not strategy.frequency_value:
            return False, "周期性策略必须设置频率类型和频率值"
        # ... 其他验证
```

## 扩展功能

### 未来计划

1. **定时任务调度**
   - 集成APScheduler或Celery
   - 自动执行到期策略
   - 失败重试机制

2. **策略模板**
   - 预定义策略模板
   - 快速创建常用策略

3. **执行历史**
   - 策略执行记录
   - 执行结果统计
   - 失败原因分析

4. **通知功能**
   - 执行成功/失败通知
   - 邮件/短信提醒
   - Webhook回调

5. **策略依赖**
   - 策略间依赖关系
   - 条件执行
   - 链式执行

## 注意事项

1. **时间处理**: 所有时间都使用UTC时间存储
2. **状态管理**: 一次性策略执行后自动禁用
3. **数据一致性**: 策略删除时检查关联数据
4. **性能考虑**: 大量策略时的查询优化
5. **安全考虑**: 策略执行权限控制

## 故障排除

### 常见问题

1. **策略不执行**
   - 检查策略是否启用
   - 验证执行时间是否正确
   - 确认设备连接状态

2. **时间显示错误**
   - 检查时区设置
   - 验证时间格式

3. **策略验证失败**
   - 检查必填字段
   - 验证时间有效性
   - 确认频率配置

### 调试方法

1. 查看后端日志
2. 检查数据库记录
3. 使用API测试工具
4. 查看前端控制台
