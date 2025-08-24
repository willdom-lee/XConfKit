from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(15), nullable=False)
    username = Column(String(50), nullable=False)
    password = Column(String(100), nullable=False)
    protocol = Column(String(10), default="ssh", comment="ssh")
    port = Column(Integer, default=22, comment="连接端口")
    connection_status = Column(String(20), default="unknown")
    latency = Column(Integer, default=0)
    last_backup = Column(DateTime)
    last_latency = Column(Float, comment="最后测试的网络延迟(毫秒)")
    last_test_time = Column(DateTime, comment="最后测试时间")
    last_backup_time = Column(DateTime, comment="最近一次备份时间")
    last_backup_type = Column(String(50), comment="最近一次备份类型")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    backups = relationship("Backup", back_populates="device")
    strategies = relationship("Strategy", back_populates="device")

class Backup(Base):
    __tablename__ = 'backups'
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    backup_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    file_path = Column(String(255))
    file_size = Column(Integer, default=0)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    device = relationship("Device", back_populates="backups")
    analysis_records = relationship("AnalysisRecord", back_populates="backup")

class Strategy(Base):
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    device_id = Column(Integer, ForeignKey('devices.id'))
    strategy_type = Column(String(20), default="one-time")
    backup_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 一次性策略字段
    scheduled_time = Column(DateTime)
    
    # 周期性策略字段
    frequency_type = Column(String(20))  # hour, day, month
    frequency_value = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # 执行相关字段
    last_execution = Column(DateTime)
    next_execution = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    device = relationship("Device", back_populates="strategies")

class Config(Base):
    __tablename__ = 'configs'
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    data_type = Column(String(20), default="string")
    description = Column(Text)
    default_value = Column(Text)
    required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class AIConfig(Base):
    __tablename__ = 'ai_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, default="openai")
    api_key = Column(String(255))
    model = Column(String(100), default="gpt-4")
    base_url = Column(String(255), default="https://api.openai.com/v1")
    timeout = Column(Integer, default=30)
    enable_cache = Column(Boolean, default=True)
    enable_history = Column(Boolean, default=True)
    auto_retry = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class AnalysisPrompt(Base):
    __tablename__ = 'analysis_prompts'
    
    id = Column(Integer, primary_key=True, index=True)
    dimension = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    is_default = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class AnalysisRecord(Base):
    __tablename__ = 'analysis_records'
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    backup_id = Column(Integer, ForeignKey('backups.id'))
    dimensions = Column(JSON)  # 存储分析维度列表
    status = Column(String(20), default="processing")  # processing, success, failed
    result = Column(JSON)  # 存储分析结果
    error_message = Column(Text)
    processing_time = Column(Integer)  # 处理时间（秒）
    created_at = Column(DateTime, default=datetime.now)
    
    device = relationship("Device")
    backup = relationship("Backup", back_populates="analysis_records")
