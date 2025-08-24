from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 设备相关模型
class DeviceBase(BaseModel):
    name: str = Field(..., description="设备名称")
    ip_address: str = Field(..., description="IP地址")
    protocol: str = Field(default="ssh", description="连接协议(ssh)")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    port: int = Field(default=22, description="端口号")
    description: Optional[str] = Field(None, description="设备描述")

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    port: Optional[int] = None
    description: Optional[str] = None

class Device(DeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    # 网络延迟相关字段
    last_latency: Optional[float] = Field(None, description="最后测试的网络延迟(毫秒)")
    last_test_time: Optional[datetime] = Field(None, description="最后测试时间")
    connection_status: Optional[str] = Field(default="unknown", description="连接状态(unknown/success/failed)")
    # 最近备份相关字段
    last_backup_time: Optional[datetime] = Field(None, description="最近一次备份时间")
    last_backup_type: Optional[str] = Field(None, description="最近一次备份类型")
    
    class Config:
        from_attributes = True

# 备份相关模型
class BackupBase(BaseModel):
    device_id: int = Field(..., description="设备ID")
    backup_type: str = Field(default="running-config", description="备份类型")

class BackupCreate(BackupBase):
    pass

class Backup(BackupBase):
    id: int
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content: Optional[str] = None  # 添加content字段
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BackupWithDevice(Backup):
    device: Device
    
    class Config:
        from_attributes = True

# FTP服务器相关模型
class FTPServerBase(BaseModel):
    name: str = Field(..., description="FTP服务器名称")
    host: str = Field(..., description="FTP主机地址")
    port: int = Field(default=21, description="FTP端口")
    username: str = Field(..., description="FTP用户名")
    password: str = Field(..., description="FTP密码")
    remote_path: str = Field(default="/", description="远程路径")
    is_active: bool = Field(default=True, description="是否启用")

class FTPServerCreate(FTPServerBase):
    pass

class FTPServerUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    remote_path: Optional[str] = None
    is_active: Optional[bool] = None

class FTPServer(FTPServerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 通用响应模型
class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class BackupResponse(BaseModel):
    success: bool
    message: str
    backup_id: Optional[int] = None
    file_path: Optional[str] = None

# 备份策略相关模型
class BackupStrategyBase(BaseModel):
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    device_id: Optional[int] = Field(None, description="设备ID")
    backup_type: str = Field(default="running-config", description="备份类型")
    strategy_type: str = Field(..., description="策略类型(one-time/recurring)")
    
    # 一次性策略字段
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间")
    
    # 周期性策略字段
    frequency_type: Optional[str] = Field(None, description="频率类型(hour/day/month)")
    frequency_value: Optional[int] = Field(None, description="频率值")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

class BackupStrategyCreate(BackupStrategyBase):
    pass

class BackupStrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    device_id: Optional[int] = None
    backup_type: Optional[str] = None
    strategy_type: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    frequency_type: Optional[str] = None
    frequency_value: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None

class BackupStrategy(BackupStrategyBase):
    id: int
    is_active: bool
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BackupStrategyWithDevice(BackupStrategy):
    device: Optional[Device] = None
    
    class Config:
        from_attributes = True

# 系统配置相关模型
class SystemConfigBase(BaseModel):
    category: str = Field(..., description="配置分类")
    key: str = Field(..., description="配置键")
    value: Optional[str] = Field(None, description="配置值")
    data_type: str = Field(default="string", description="数据类型(string/int/float/boolean/json)")
    description: Optional[str] = Field(None, description="配置描述")
    is_required: bool = Field(default=False, description="是否必需")
    default_value: Optional[str] = Field(None, description="默认值")

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    default_value: Optional[str] = None

class SystemConfig(SystemConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 系统配置分组模型
class SystemConfigCategory(BaseModel):
    category: str
    configs: List[SystemConfig]

# 系统配置批量更新模型
class SystemConfigBatchUpdate(BaseModel):
    configs: List[dict] = Field(..., description="配置项列表，格式: [{'key': 'config_key', 'value': 'config_value'}]")

# AI分析相关Schema
class AIConfigRequest(BaseModel):
    provider: str = Field(default="alibaba", description="AI服务提供商")
    api_key: str = Field(..., description="API密钥")
    model: str = Field(default="qwen-turbo", description="模型名称")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", description="基础URL")
    timeout: int = Field(default=30, description="超时时间（秒）")
    enable_cache: bool = Field(default=True, description="启用结果缓存")
    enable_history: bool = Field(default=True, description="保存分析历史")
    auto_retry: bool = Field(default=True, description="自动重试")

class AnalysisRequest(BaseModel):
    device_id: int
    backup_id: int
    dimensions: Optional[List[str]] = None  # 支持维度选择，默认为None表示分析所有维度
    ai_config: Optional[AIConfigRequest] = None  # AI配置，如果不提供则使用数据库中的配置

class AnalysisPromptRequest(BaseModel):
    dimension: str = Field(..., description="分析维度")
    name: str = Field(..., description="提示词名称")
    description: Optional[str] = Field(None, description="提示词描述")
    content: str = Field(..., description="提示词内容")
    is_default: bool = Field(default=True, description="是否为默认提示词")

class AnalysisResult(BaseModel):
    summary: str = Field(..., description="分析摘要")
    issues: List[Dict[str, Any]] = Field(default=[], description="发现的问题")
    raw_content: str = Field(..., description="原始分析内容")

class AnalysisRecord(BaseModel):
    id: int
    device_id: int = Field(..., description="设备ID")
    backup_id: int = Field(..., description="备份ID")
    dimensions: List[str] = Field(..., description="分析维度")
    status: str = Field(..., description="分析状态")
    result: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    processing_time: Optional[int] = Field(None, description="处理时间（秒）")
    created_at: datetime

    class Config:
        from_attributes = True
