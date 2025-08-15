from pydantic import BaseModel, Field
from typing import Optional, List
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
    device_id: int = Field(..., description="设备ID")
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
    device: Device
    
    class Config:
        from_attributes = True
