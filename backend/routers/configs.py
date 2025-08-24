from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.config_service import ConfigService
from ..schemas import SystemConfig, SystemConfigCreate, SystemConfigUpdate, SystemConfigBatchUpdate, ResponseModel, SystemConfigCategory
from typing import List, Dict, Any

router = APIRouter(prefix="/api/configs", tags=["系统配置"])

@router.get("/", response_model=List[SystemConfig])
def get_all_configs(db: Session = Depends(get_db)):
    """获取所有配置"""
    return ConfigService.get_all_configs(db)

@router.get("/categories", response_model=List[SystemConfigCategory])
def get_configs_by_categories(db: Session = Depends(get_db)):
    """获取按分类分组的配置"""
    grouped_configs = ConfigService.get_configs_grouped_by_category(db)
    categories = []
    
    for category, configs in grouped_configs.items():
        categories.append(SystemConfigCategory(
            category=category,
            configs=configs
        ))
    
    return categories

@router.get("/category/{category}", response_model=List[SystemConfig])
def get_configs_by_category(category: str, db: Session = Depends(get_db)):
    """获取指定分类的配置"""
    return ConfigService.get_configs_by_category(db, category)

@router.get("/{category}/{key}", response_model=SystemConfig)
def get_config(category: str, key: str, db: Session = Depends(get_db)):
    """获取指定配置"""
    config = ConfigService.get_config(db, category, key)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config

@router.post("/", response_model=SystemConfig)
def create_config(config: SystemConfigCreate, db: Session = Depends(get_db)):
    """创建配置"""
    return ConfigService.create_config(db, config)

@router.put("/{category}/{key}", response_model=SystemConfig)
def update_config(category: str, key: str, config: SystemConfigUpdate, db: Session = Depends(get_db)):
    """更新配置"""
    updated_config = ConfigService.update_config(db, category, key, config)
    if not updated_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return updated_config

@router.post("/batch-update", response_model=ResponseModel)
def batch_update_configs(
    batch_update: SystemConfigBatchUpdate,
    db: Session = Depends(get_db)
):
    """批量更新配置"""
    try:
        result = ConfigService.batch_update_configs(db, batch_update.configs)
        return {
            "success": True,
            "message": f"批量更新完成，成功: {result['success_count']}, 失败: {result['error_count']}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"批量更新失败: {str(e)}")

@router.post("/{category}/{key}/reset", response_model=SystemConfig)
def reset_config_to_default(category: str, key: str, db: Session = Depends(get_db)):
    """重置配置为默认值"""
    config = ConfigService.reset_config_to_default(db, category, key)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config

@router.post("/{category}/reset", response_model=ResponseModel)
def reset_category_to_default(category: str, db: Session = Depends(get_db)):
    """重置指定分类的所有配置为默认值"""
    try:
        result = ConfigService.reset_category_to_default(db, category)
        return {
            "success": True,
            "message": f"分类 {category} 重置完成，成功: {result['reset_count']}, 失败: {result['error_count']}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"重置分类失败: {str(e)}")

@router.post("/reset-all", response_model=ResponseModel)
def reset_all_configs_to_default(db: Session = Depends(get_db)):
    """重置所有配置为默认值（不包括AI配置）"""
    try:
        result = ConfigService.reset_all_configs_to_default(db)
        return {
            "success": True,
            "message": f"所有配置重置完成，成功: {result['reset_count']}, 失败: {result['error_count']}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"重置所有配置失败: {str(e)}")

@router.get("/defaults", response_model=Dict[str, Any])
def get_default_values():
    """获取所有配置的默认值"""
    return ConfigService.get_default_values()

@router.get("/defaults/{category}", response_model=Dict[str, str])
def get_default_values_by_category(category: str):
    """获取指定分类的默认值"""
    return ConfigService.get_default_values_by_category(category)

@router.post("/init-defaults", response_model=ResponseModel)
def init_default_configs(db: Session = Depends(get_db)):
    """初始化默认配置"""
    try:
        result = ConfigService.init_default_configs(db)
        return {
            "success": True,
            "message": f"默认配置初始化完成，成功: {result['init_count']}, 失败: {result['error_count']}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"初始化默认配置失败: {str(e)}")

@router.delete("/{category}/{key}", response_model=ResponseModel)
def delete_config(category: str, key: str, db: Session = Depends(get_db)):
    """删除配置"""
    success = ConfigService.delete_config(db, category, key)
    if not success:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"success": True, "message": "配置删除成功"}


