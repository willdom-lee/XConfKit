"""
配置管理器 - 用于在其他服务中方便地获取和使用系统配置
"""

from sqlalchemy.orm import Session
from .config_service import ConfigService
from ..database import get_db
from typing import Any, Dict, Optional
import functools

class ConfigManager:
    """配置管理器 - 提供配置的缓存和便捷访问"""
    
    _cache: Dict[str, Any] = {}
    _cache_valid = False
    
    @staticmethod
    def _get_db_session() -> Session:
        """获取数据库会话"""
        from ..database import SessionLocal
        return SessionLocal()
    
    @staticmethod
    def refresh_cache():
        """刷新配置缓存"""
        try:
            db = ConfigManager._get_db_session()
            configs = ConfigService.get_all_configs(db)
            
            ConfigManager._cache.clear()
            for config in configs:
                key = f"{config.category}.{config.key}"
                ConfigManager._cache[key] = ConfigService._convert_value(
                    config.value, config.data_type
                )
            
            ConfigManager._cache_valid = True
            db.close()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"刷新配置缓存失败: {str(e)}")
            ConfigManager._cache_valid = False
    
    @staticmethod
    def get_config(category: str, key: str, default=None) -> Any:
        """获取配置值"""
        if not ConfigManager._cache_valid:
            ConfigManager.refresh_cache()
        
        config_key = f"{category}.{key}"
        return ConfigManager._cache.get(config_key, default)
    
    @staticmethod
    def get_connection_config() -> Dict[str, Any]:
        """获取连接相关配置"""
        return {
            'ssh_timeout': ConfigManager.get_config('connection', 'ssh_timeout', 10),
            'ssh_command_timeout': ConfigManager.get_config('connection', 'ssh_command_timeout', 5),
            'ping_timeout': ConfigManager.get_config('connection', 'ping_timeout', 3),
            'banner_timeout': ConfigManager.get_config('connection', 'banner_timeout', 60),
            'retry_count': ConfigManager.get_config('connection', 'retry_count', 3),
        }
    
    @staticmethod
    def get_backup_config() -> Dict[str, Any]:
        """获取备份相关配置"""
        return {
            'storage_path': ConfigManager.get_config('backup', 'storage_path', 'data/backups'),
            'retention_days': ConfigManager.get_config('backup', 'retention_days', 30),
            'backup_timeout': ConfigManager.get_config('backup', 'backup_timeout', 300),

            'max_iterations': ConfigManager.get_config('backup', 'max_iterations', 100),
        }
    
    @staticmethod
    def get_system_config() -> Dict[str, Any]:
        """获取系统相关配置"""
        return {
            'timezone': ConfigManager.get_config('system', 'timezone', 'Asia/Shanghai'),
            'log_level': ConfigManager.get_config('system', 'log_level', 'INFO'),
            'page_size': ConfigManager.get_config('system', 'page_size', 20),
            'default_backup_type': ConfigManager.get_config('system', 'default_backup_type', 'running-config'),
        }
    
    @staticmethod
    def get_notification_config() -> Dict[str, Any]:
        """获取通知相关配置"""
        return {
            'email_enabled': ConfigManager.get_config('notification', 'email_enabled', False),
            'email_smtp_server': ConfigManager.get_config('notification', 'email_smtp_server', ''),
            'email_smtp_port': ConfigManager.get_config('notification', 'email_smtp_port', 587),
            'email_username': ConfigManager.get_config('notification', 'email_username', ''),
            'email_password': ConfigManager.get_config('notification', 'email_password', ''),
            'backup_failure_alert': ConfigManager.get_config('notification', 'backup_failure_alert', True),
        }

# 装饰器：自动使用配置
def use_config(category: str):
    """装饰器：自动注入配置到函数参数"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if category == 'connection':
                config = ConfigManager.get_connection_config()
            elif category == 'backup':
                config = ConfigManager.get_backup_config()
            elif category == 'system':
                config = ConfigManager.get_system_config()
            elif category == 'notification':
                config = ConfigManager.get_notification_config()
            else:
                config = {}
            
            # 将配置作为关键字参数传递
            kwargs.update(config)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 初始化配置缓存
try:
    ConfigManager.refresh_cache()
except Exception:
    # 如果初始化失败（比如数据库还未创建），使用默认配置
    pass
