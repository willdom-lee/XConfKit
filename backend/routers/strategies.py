from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import (
    BackupStrategy as BackupStrategySchema, 
    BackupStrategyCreate, 
    BackupStrategyUpdate, 
    BackupStrategyWithDevice,
    ResponseModel
)
from ..models import BackupStrategy
from ..services.strategy_service import StrategyService

router = APIRouter(prefix="/api/strategies", tags=["备份策略"])

@router.post("/", response_model=BackupStrategySchema)
def create_strategy(strategy: BackupStrategyCreate, db: Session = Depends(get_db)):
    """创建备份策略"""
    # 验证策略配置
    is_valid, message = StrategyService.validate_strategy(strategy)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    result = StrategyService.create_strategy(db, strategy)
    return result

@router.get("/", response_model=List[BackupStrategyWithDevice])
def get_strategies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取备份策略列表"""
    return StrategyService.get_strategies(db, skip=skip, limit=limit)

@router.get("/{strategy_id}", response_model=BackupStrategyWithDevice)
def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """根据ID获取备份策略"""
    strategy = StrategyService.get_strategy(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="备份策略不存在")
    return strategy

@router.put("/{strategy_id}", response_model=BackupStrategySchema)
def update_strategy(strategy_id: int, strategy_update: BackupStrategyUpdate, db: Session = Depends(get_db)):
    """更新备份策略"""
    strategy = StrategyService.update_strategy(db, strategy_id, strategy_update)
    if not strategy:
        raise HTTPException(status_code=404, detail="备份策略不存在")
    return strategy

@router.delete("/{strategy_id}", response_model=ResponseModel)
def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """删除备份策略"""
    success = StrategyService.delete_strategy(db, strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="备份策略不存在")
    return ResponseModel(success=True, message="备份策略删除成功")

@router.post("/{strategy_id}/toggle", response_model=BackupStrategySchema)
def toggle_strategy_status(strategy_id: int, db: Session = Depends(get_db)):
    """切换策略启用状态"""
    strategy = StrategyService.toggle_strategy_status(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="备份策略不存在")
    return strategy

@router.get("/due/list", response_model=List[BackupStrategyWithDevice])
def get_due_strategies(db: Session = Depends(get_db)):
    """获取到期的策略"""
    return StrategyService.get_due_strategies(db)

@router.post("/{strategy_id}/execute", response_model=ResponseModel)
def execute_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """执行备份策略（调度执行）"""
    from ..services.backup_service import BackupService
    
    strategy = StrategyService.get_strategy(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="备份策略不存在")
    
    if not strategy.is_active:
        raise HTTPException(status_code=400, detail="策略已禁用")
    
    try:
        # 执行备份
        backup_result = BackupService.execute_backup(
            db=db,
            device_id=strategy.device_id,
            backup_type=strategy.backup_type
        )
        
        if backup_result and backup_result.get('success'):
            # 标记策略已执行
            StrategyService.mark_strategy_executed(db, strategy_id)
            return ResponseModel(success=True, message="策略执行成功，备份已完成")
        else:
            return ResponseModel(success=False, message=f"策略执行失败: {backup_result.get('message', '未知错误')}")
            
    except Exception as e:
        return ResponseModel(success=False, message=f"策略执行失败: {str(e)}")

@router.post("/{strategy_id}/execute-now", response_model=ResponseModel)
def execute_strategy_now(strategy_id: int, db: Session = Depends(get_db)):
    """立即执行备份策略（不影响调度）"""
    from ..services.backup_service import BackupService
    
    strategy = StrategyService.get_strategy(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="备份策略不存在")
    
    if not strategy.is_active:
        raise HTTPException(status_code=400, detail="策略已禁用")
    
    try:
        # 执行备份
        backup_result = BackupService.execute_backup(
            db=db,
            device_id=strategy.device_id,
            backup_type=strategy.backup_type
        )
        
        if backup_result and backup_result.get('success'):
            # 立即执行不影响调度，不更新策略状态
            return ResponseModel(success=True, message="策略立即执行成功，备份已完成")
        else:
            return ResponseModel(success=False, message=f"策略执行失败: {backup_result.get('message', '未知错误')}")
            
    except Exception as e:
        return ResponseModel(success=False, message=f"策略执行失败: {str(e)}")
