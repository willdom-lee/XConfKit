from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Device(Base):
    """设备表"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="设备名称")
    ip_address = Column(String(45), nullable=False, comment="IP地址")
    protocol = Column(String(10), default="ssh", comment="连接协议(ssh)")
    username = Column(String(50), nullable=False, comment="用户名")
    password = Column(String(100), nullable=False, comment="密码")
    port = Column(Integer, default=22, comment="端口号")
    description = Column(String(200), comment="设备描述")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联备份记录
    backups = relationship("Backup", back_populates="device")

class Backup(Base):
    """备份记录表"""
    __tablename__ = "backups"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    backup_type = Column(String(20), default="running-config", comment="备份类型")
    status = Column(String(20), default="pending", comment="备份状态(pending/success/failed)")
    file_path = Column(String(500), comment="备份文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联设备
    device = relationship("Device", back_populates="backups")

class FTPServer(Base):
    """FTP服务器配置表"""
    __tablename__ = "ftp_servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="FTP服务器名称")
    host = Column(String(100), nullable=False, comment="FTP主机地址")
    port = Column(Integer, default=21, comment="FTP端口")
    username = Column(String(50), nullable=False, comment="FTP用户名")
    password = Column(String(100), nullable=False, comment="FTP密码")
    remote_path = Column(String(200), default="/", comment="远程路径")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class BackupStrategy(Base):
    """备份策略表"""
    __tablename__ = "backup_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(String(200), comment="策略描述")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, comment="设备ID")
    backup_type = Column(String(20), default="running-config", comment="备份类型")
    strategy_type = Column(String(20), nullable=False, comment="策略类型(one-time/recurring)")
    
    # 一次性策略字段
    scheduled_time = Column(DateTime, comment="计划执行时间")
    
    # 周期性策略字段
    frequency_type = Column(String(10), comment="频率类型(hour/day/month)")
    frequency_value = Column(Integer, comment="频率值")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    last_execution = Column(DateTime, comment="最后执行时间")
    next_execution = Column(DateTime, comment="下次执行时间")
    
    # 通用字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联设备
    device = relationship("Device", backref="backup_strategies")
