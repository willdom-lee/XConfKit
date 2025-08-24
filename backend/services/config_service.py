from sqlalchemy.orm import Session
from ..models import Config
from ..schemas import SystemConfigCreate, SystemConfigUpdate
from typing import List, Optional, Dict, Any
import json

class ConfigService:
    """系统配置服务"""
    
    # 统一配置定义 - 精简版，只保留必要配置
    DEFAULT_CONFIGS = {
        "basic": {
            "backup_path": {
                "value": "./backups",
                "data_type": "string",
                "description": "备份文件的存储目录路径",
                "is_required": True,
                "default_value": "./backups"
            }
        },
        "advanced": {
            "log_level": {
                "value": "INFO",
                "data_type": "string",
                "description": "系统日志的详细程度",
                "is_required": True,
                "default_value": "INFO"
            }
        }
    }

    @staticmethod
    def get_all_configs(db: Session) -> List[Config]:
        """获取所有配置"""
        return db.query(Config).all()

    @staticmethod
    def get_config(db: Session, category: str, key: str) -> Optional[Config]:
        """获取指定配置"""
        return db.query(Config).filter(Config.category == category, Config.key == key).first()

    @staticmethod
    def get_configs_by_category(db: Session, category: str) -> List[Config]:
        """获取指定分类的配置"""
        return db.query(Config).filter(Config.category == category).all()

    @staticmethod
    def create_config(db: Session, config: SystemConfigCreate) -> Config:
        """创建配置"""
        db_config = Config(**config.dict())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

    @staticmethod
    def update_config(db: Session, category: str, key: str, config: SystemConfigUpdate) -> Optional[Config]:
        """更新配置"""
        db_config = ConfigService.get_config(db, category, key)
        if not db_config:
            return None
        
        for field, value in config.dict(exclude_unset=True).items():
            setattr(db_config, field, value)
        
        db.commit()
        db.refresh(db_config)
        return db_config

    @staticmethod
    def batch_update_configs(db: Session, configs: List[Dict[str, str]]) -> Dict[str, Any]:
        """批量更新配置"""
        success_count = 0
        error_count = 0
        errors = []
        
        for config_data in configs:
            try:
                category = config_data.get('category')
                key = config_data.get('key')
                value = config_data.get('value')
                
                if not all([category, key, value is not None]):
                    error_count += 1
                    errors.append(f"配置数据不完整: {config_data}")
                    continue
                
                db_config = ConfigService.get_config(db, category, key)
                if db_config:
                    # 将值转换为字符串保存，确保布尔值正确处理
                    if isinstance(value, bool):
                        db_config.value = str(value).lower()
                    else:
                        db_config.value = str(value)
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"配置项不存在: {category}.{key}")
            except Exception as e:
                error_count += 1
                errors.append(f"更新配置项失败: {str(e)}")
        
        if success_count > 0:
            db.commit()
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }

    @staticmethod
    def get_default_values() -> Dict[str, Any]:
        """获取所有配置的默认值"""
        default_values = {}
        for category, configs in ConfigService.DEFAULT_CONFIGS.items():
            default_values[category] = {}
            for key, config_data in configs.items():
                default_values[category][key] = config_data["default_value"]
        return default_values

    @staticmethod
    def get_default_values_by_category(category: str) -> Dict[str, str]:
        """获取指定分类的默认值"""
        if category not in ConfigService.DEFAULT_CONFIGS:
            return {}
        
        default_values = {}
        for key, config_data in ConfigService.DEFAULT_CONFIGS[category].items():
            default_values[key] = config_data["default_value"]
        return default_values

    @staticmethod
    def init_default_configs(db: Session) -> Dict[str, Any]:
        """初始化默认配置"""
        created_count = 0
        updated_count = 0
        
        for category, configs in ConfigService.DEFAULT_CONFIGS.items():
            for key, config_data in configs.items():
                existing_config = ConfigService.get_config(db, category, key)
                
                if existing_config:
                    # 如果配置已存在，只更新描述和默认值
                    existing_config.description = config_data["description"]
                    existing_config.default_value = config_data["default_value"]
                    existing_config.data_type = config_data["data_type"]
                    existing_config.required = config_data["is_required"]
                    updated_count += 1
                else:
                    # 创建新配置
                    new_config = Config(
                        category=category,
                        key=key,
                        value=config_data["value"],
                        data_type=config_data["data_type"],
                        description=config_data["description"],
                        required=config_data["is_required"],
                        default_value=config_data["default_value"]
                    )
                    db.add(new_config)
                    created_count += 1
        
        db.commit()
        
        return {
            "created_count": created_count,
            "updated_count": updated_count
        }

    @staticmethod
    def get_configs_grouped_by_category(db: Session) -> Dict[str, List[Config]]:
        """获取按分类分组的配置"""
        configs = ConfigService.get_all_configs(db)
        grouped = {}
        
        for config in configs:
            if config.category not in grouped:
                grouped[config.category] = []
            grouped[config.category].append(config)
        
        return grouped

    @staticmethod
    def reset_config_to_default(db: Session, category: str, key: str) -> Optional[Config]:
        """重置配置为默认值"""
        config = ConfigService.get_config(db, category, key)
        if not config:
            return None
        
        config.value = config.default_value
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def reset_category_to_default(db: Session, category: str) -> Dict[str, Any]:
        """重置指定分类的所有配置为默认值"""
        configs = ConfigService.get_configs_by_category(db, category)
        reset_count = 0
        errors = []
        
        for config in configs:
            try:
                if config.default_value:
                    config.value = config.default_value
                    reset_count += 1
                else:
                    errors.append(f"配置项 {config.key} 没有默认值")
            except Exception as e:
                errors.append(f"重置配置项 {config.key} 失败: {str(e)}")
        
        if reset_count > 0:
            db.commit()
        
        return {
            "reset_count": reset_count,
            "error_count": len(errors),
            "errors": errors
        }

    @staticmethod
    def reset_all_configs_to_default(db: Session) -> Dict[str, Any]:
        """重置所有配置为默认值（不包括AI配置）"""
        configs = ConfigService.get_all_configs(db)
        reset_count = 0
        errors = []
        
        for config in configs:
            try:
                # 跳过AI配置
                if config.category == 'ai':
                    continue
                
                if config.default_value:
                    config.value = config.default_value
                    reset_count += 1
                else:
                    errors.append(f"配置项 {config.category}.{config.key} 没有默认值")
            except Exception as e:
                errors.append(f"重置配置项 {config.category}.{config.key} 失败: {str(e)}")
        
        if reset_count > 0:
            db.commit()
        
        return {
            "reset_count": reset_count,
            "error_count": len(errors),
            "errors": errors
        }

    @staticmethod
    def delete_config(db: Session, category: str, key: str) -> bool:
        """删除配置"""
        config = ConfigService.get_config(db, category, key)
        if not config:
            return False
        
        db.delete(config)
        db.commit()
        return True
