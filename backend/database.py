from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# 数据库文件路径
DATABASE_URL = "sqlite:///./data/xconfkit.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite需要这个参数
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    # 确保data目录存在
    os.makedirs("./data", exist_ok=True)
    
    # 导入所有模型以确保它们被注册
    from . import models
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
