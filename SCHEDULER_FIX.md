# 调度器自动执行修复说明

## 问题描述

用户反馈：备份策略的"立即执行"功能可以正常工作，但是到时间点后，策略没有自动开始执行备份。

## 问题原因

在`backend/services/strategy_service.py`的`get_due_strategies`方法中，仍然使用了`datetime.utcnow()`来获取当前时间，但系统中其他部分已经统一改为北京时间`datetime.now()`，导致时间比较不一致。

## 修复内容

### 1. 修复时间比较问题

**修复文件**: `backend/services/strategy_service.py`

**修复前**:
```python
@staticmethod
def get_due_strategies(db: Session) -> List[BackupStrategy]:
    """获取到期的策略"""
    now = datetime.utcnow()  # 使用UTC时间
    return db.query(BackupStrategy).filter(
        BackupStrategy.is_active == True,
        BackupStrategy.next_execution <= now
    ).all()
```

**修复后**:
```python
@staticmethod
def get_due_strategies(db: Session) -> List[BackupStrategy]:
    """获取到期的策略"""
    now = datetime.now()  # 使用北京时间
    return db.query(BackupStrategy).filter(
        BackupStrategy.is_active == True,
        BackupStrategy.next_execution <= now
    ).all()
```

### 2. 调度器工作流程

调度器的工作流程如下：

1. **启动**: 应用启动时自动启动调度器
2. **循环检查**: 每30秒检查一次到期的策略
3. **执行策略**: 发现到期策略时自动执行备份
4. **更新状态**: 执行完成后更新策略状态

### 3. 调度器日志

调度器会在后端日志中记录以下信息：

```
INFO:backend.scheduler:备份策略调度器已启动
INFO:backend.scheduler:发现 X 个到期策略
INFO:backend.scheduler:开始执行策略: 策略名称 (ID: 策略ID)
INFO:backend.scheduler:策略 策略名称 执行成功
```

## 测试验证

### 1. 创建测试策略

使用测试脚本`test_scheduler.py`创建了一个1分钟后执行的测试策略：

```python
# 创建测试策略（1分钟后执行）
test_time = now + timedelta(minutes=1)
strategy_data = {
    "name": f"测试策略_{now.strftime('%H%M%S')}",
    "description": "调度器测试策略",
    "device_id": device['id'],
    "backup_type": "running-config",
    "strategy_type": "one-time",
    "scheduled_time": test_time.strftime('%Y-%m-%dT%H:%M:%S')
}
```

### 2. 测试结果

- ✅ **策略创建**: 成功创建测试策略
- ✅ **调度器检测**: 调度器检测到到期策略
- ✅ **自动执行**: 调度器自动执行备份
- ✅ **备份创建**: 成功创建新的备份记录
- ✅ **状态更新**: 策略执行状态正确更新

### 3. 日志验证

从后端日志可以看到：

```
INFO:backend.scheduler:策略 测试策略_214329 执行成功
INFO:backend.services.backup_service:SSH备份结果: {'success': True, 'message': '备份成功', 'file_path': './data/backups/1/running-config_20250815_214456_14.txt', 'file_size': 2622}
```

## 功能特性

### 1. 自动调度

- **检查频率**: 每30秒检查一次
- **时间精度**: 精确到秒
- **容错机制**: 异常处理和重试

### 2. 策略类型支持

- **一次性策略**: 执行后自动禁用
- **周期性策略**: 自动计算下次执行时间
- **时间范围**: 支持开始时间和结束时间

### 3. 状态管理

- **执行状态**: 记录最后执行时间
- **下次执行**: 自动计算下次执行时间
- **策略状态**: 启用/禁用状态管理

## 使用说明

### 1. 创建策略

1. 访问"备份策略"页面
2. 点击"新增策略"
3. 选择策略类型（一次性/周期性）
4. 设置执行时间
5. 保存策略

### 2. 监控执行

1. 查看策略列表中的"下次执行"时间
2. 监控后端日志中的调度器信息
3. 检查备份记录是否自动创建

### 3. 立即执行

- 使用"立即执行"按钮可以立即执行策略
- 立即执行不影响策略的调度设置
- 适用于测试和紧急备份需求

## 注意事项

### 1. 时间同步

- 确保系统时间正确设置
- 所有时间都使用北京时间
- 避免时区转换问题

### 2. 服务状态

- 调度器随后端服务启动/停止
- 重启服务会重新启动调度器
- 确保后端服务正常运行

### 3. 日志监控

- 定期检查后端日志
- 关注调度器执行状态
- 及时处理执行错误

## 总结

通过修复时间比较问题，调度器现在可以：

1. ✅ **正确检测到期策略**: 使用统一的时间格式
2. ✅ **自动执行备份**: 无需人工干预
3. ✅ **更新策略状态**: 正确管理执行状态
4. ✅ **记录执行日志**: 便于监控和调试

现在用户可以放心地设置备份策略，系统会在指定时间自动执行备份任务。
