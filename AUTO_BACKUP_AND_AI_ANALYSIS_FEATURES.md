# 自动备份和AI分析维度选择功能

## 1. 自动备份功能

### 功能概述
系统现在支持自动备份功能，可以防止数据丢失和异常重构。

### 主要特性
- **定时自动备份**: 每天凌晨2点自动执行备份（可配置）
- **智能备份策略**: 只备份有活跃策略的设备
- **自动清理**: 根据保留天数自动清理旧备份
- **备份日志**: 详细的备份执行日志
- **配置管理**: 可在系统配置中调整备份参数

### 配置选项
在"系统配置" → "基础设置"中可以配置：
- `enable_auto_backup`: 启用/禁用自动备份
- `auto_backup_time`: 自动备份执行时间（格式：HH:MM）
- `auto_backup_retention_days`: 自动备份保留天数

### API接口
- `GET /api/backups/auto-backup/status`: 获取自动备份状态
- `POST /api/backups/auto-backup/start`: 手动启动自动备份
- `POST /api/backups/auto-backup/config`: 更新自动备份配置

### 使用示例
```bash
# 查看自动备份状态
curl http://localhost:8000/api/backups/auto-backup/status

# 手动启动自动备份
curl -X POST http://localhost:8000/api/backups/auto-backup/start

# 更新配置
curl -X POST http://localhost:8000/api/backups/auto-backup/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "schedule_time": "03:00", "retention_days": 60}'
```

## 2. AI分析维度选择功能

### 功能概述
AI分析现在支持维度选择，用户可以选择需要分析的维度，而不是每次都分析全部维度。

### 支持的维度
1. **安全加固** (security)
   - 检查配置中的安全漏洞和加固建议
   - 图标: 🔒

2. **冗余与高可用** (redundancy)
   - 分析冗余配置和高可用性设置
   - 图标: 🔄

3. **性能优化** (performance)
   - 识别性能瓶颈和优化建议
   - 图标: ⚡

4. **配置健全性** (integrity)
   - 检查配置的完整性和一致性
   - 图标: ✅

5. **最佳实践** (best_practices)
   - 园区网配置最佳实践建议
   - 图标: 📋

### 使用方式
1. 在"AI分析"页面选择设备和备份文件
2. 在"分析维度"区域选择需要分析的维度（默认全选）
3. 点击"开始分析"按钮
4. 系统只分析选中的维度，提高分析效率

### 界面特性
- **可视化选择**: 每个维度都有图标和描述
- **默认全选**: 新用户默认选择所有维度
- **灵活配置**: 可以随时调整选择的维度
- **结果展示**: 分析结果按维度分类显示

### API接口
- `POST /api/analysis/analyze`: 支持dimensions参数
```json
{
  "device_id": 1,
  "backup_id": 1,
  "dimensions": ["security", "performance"]  // 只分析安全和性能维度
}
```

## 3. 数据保护系统

### 防止数据丢失
- **自动快照**: 在重要操作前自动创建数据快照
- **完整性检查**: 定期检查数据库完整性
- **自动恢复**: 检测到数据异常时自动从备份恢复
- **安全重启**: 重启服务时自动备份和验证

### 使用工具
```bash
# 检查数据完整性
python prevent_data_loss.py check

# 创建备份
python prevent_data_loss.py backup

# 从备份恢复
python prevent_data_loss.py restore

# 安全重启服务
python prevent_data_loss.py restart

# 监控数据完整性
python prevent_data_loss.py monitor
```

## 4. 技术实现

### 后端实现
- **AutoBackupService**: 自动备份服务类
- **AnalysisService**: 支持维度选择的AI分析服务
- **数据保护**: 集成到启动脚本中的数据保护机制

### 前端实现
- **维度选择UI**: 使用Checkbox.Group实现维度选择
- **结果展示**: 按维度分类显示分析结果
- **配置管理**: 自动备份配置集成到系统配置页面

### 数据库变更
- **AnalysisRecord**: 新增dimensions字段存储选中的维度
- **Config**: 新增自动备份相关配置项

## 5. 最佳实践

### 自动备份
1. 建议在业务低峰期执行自动备份
2. 根据存储空间调整保留天数
3. 定期检查备份日志确保备份成功
4. 重要操作前手动触发备份

### AI分析
1. 根据分析目的选择合适的维度
2. 安全相关分析建议选择"安全加固"维度
3. 性能优化建议选择"性能优化"维度
4. 全面分析时选择所有维度

### 数据保护
1. 定期运行数据完整性检查
2. 重要更新前创建手动备份
3. 使用安全重启脚本避免数据丢失
4. 监控系统运行状态

## 6. 故障排除

### 自动备份问题
- 检查AI配置是否正确
- 查看备份日志文件
- 确认设备连接状态
- 验证备份路径权限

### AI分析问题
- 确认AI API配置正确
- 检查网络连接
- 验证分析提示词配置
- 查看分析日志

### 数据保护问题
- 运行数据完整性检查
- 查看保护系统日志
- 手动触发备份恢复
- 检查文件系统权限
