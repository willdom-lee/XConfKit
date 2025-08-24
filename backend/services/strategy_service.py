from sqlalchemy.orm import Session, joinedload
from ..models import Strategy, Device
from ..schemas import BackupStrategyCreate, BackupStrategyUpdate
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class StrategyService:
    @staticmethod
    def create_strategy(db: Session, strategy: BackupStrategyCreate) -> Strategy:
        """创建备份策略"""
        db_strategy = Strategy(**strategy.model_dump())
        
        # 计算下次执行时间
        if strategy.strategy_type == "one-time":
            db_strategy.next_execution = strategy.scheduled_time
        elif strategy.strategy_type == "recurring":
            db_strategy.next_execution = strategy.start_time
        
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def get_strategies(db: Session, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """获取备份策略列表"""
        try:
            return db.query(Strategy).options(joinedload(Strategy.device)).offset(skip).limit(limit).all()
        except Exception as e:
            # 如果关联查询失败，返回不包含设备信息的策略列表
            logger.warning(f"获取策略列表时关联查询失败: {str(e)}")
            return db.query(Strategy).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_strategy(db: Session, strategy_id: int) -> Optional[Strategy]:
        """根据ID获取备份策略"""
        return db.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    @staticmethod
    def update_strategy(db: Session, strategy_id: int, strategy_update: BackupStrategyUpdate) -> Optional[Strategy]:
        """更新备份策略"""
        db_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not db_strategy:
            return None
        
        update_data = strategy_update.model_dump(exclude_unset=True)
        
        # 如果更新了时间相关字段，重新计算下次执行时间
        if 'scheduled_time' in update_data or 'start_time' in update_data or 'frequency_type' in update_data or 'frequency_value' in update_data:
            if db_strategy.strategy_type == "one-time" and 'scheduled_time' in update_data:
                db_strategy.next_execution = update_data['scheduled_time']
            elif db_strategy.strategy_type == "recurring":
                if 'start_time' in update_data:
                    db_strategy.next_execution = update_data['start_time']
                elif db_strategy.last_execution and 'frequency_type' in update_data and 'frequency_value' in update_data:
                    db_strategy.next_execution = StrategyService._calculate_next_execution(
                        db_strategy.last_execution,
                        update_data.get('frequency_type', db_strategy.frequency_type),
                        update_data.get('frequency_value', db_strategy.frequency_value)
                    )
        
        for field, value in update_data.items():
            setattr(db_strategy, field, value)
        
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def delete_strategy(db: Session, strategy_id: int) -> bool:
        """删除备份策略"""
        db_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not db_strategy:
            return False
        
        db.delete(db_strategy)
        db.commit()
        return True
    
    @staticmethod
    def toggle_strategy_status(db: Session, strategy_id: int) -> Optional[Strategy]:
        """切换策略启用状态"""
        db_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not db_strategy:
            return None
        
        db_strategy.is_active = not db_strategy.is_active
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def get_due_strategies(db: Session) -> List[Strategy]:
        """获取到期的策略"""
        now = datetime.now()
        return db.query(Strategy).filter(
            Strategy.is_active == True,
            Strategy.next_execution <= now
        ).all()
    
    @staticmethod
    def mark_strategy_executed(db: Session, strategy_id: int) -> Optional[Strategy]:
        """标记策略已执行"""
        db_strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not db_strategy:
            return None
        
        db_strategy.last_execution = datetime.now()
        
        # 计算下次执行时间
        if db_strategy.strategy_type == "one-time":
            # 一次性策略执行后禁用
            db_strategy.is_active = False
            db_strategy.next_execution = None
        elif db_strategy.strategy_type == "recurring":
            # 周期性策略计算下次执行时间
            if db_strategy.frequency_type and db_strategy.frequency_value:
                db_strategy.next_execution = StrategyService._calculate_next_execution(
                    db_strategy.last_execution,
                    db_strategy.frequency_type,
                    db_strategy.frequency_value
                )
                
                # 检查是否超过结束时间
                if db_strategy.end_time and db_strategy.next_execution > db_strategy.end_time:
                    db_strategy.is_active = False
                    db_strategy.next_execution = None
        
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def _calculate_next_execution(last_execution: datetime, frequency_type: str, frequency_value: int) -> datetime:
        """计算下次执行时间"""
        if frequency_type == "hour":
            return last_execution + timedelta(hours=frequency_value)
        elif frequency_type == "day":
            return last_execution + timedelta(days=frequency_value)
        elif frequency_type == "month":
            # 简单的月份计算（30天）
            return last_execution + timedelta(days=frequency_value * 30)
        else:
            # 默认按天计算
            return last_execution + timedelta(days=frequency_value)
    
    @staticmethod
    def validate_strategy(strategy: BackupStrategyCreate) -> tuple[bool, str]:
        """验证策略配置"""
        now = datetime.now()
        
        if strategy.strategy_type == "one-time":
            if not strategy.scheduled_time:
                return False, "一次性策略必须设置计划执行时间"
            # 允许设置未来1分钟内的策略（考虑到时间同步误差）
            if strategy.scheduled_time <= now - timedelta(minutes=1):
                return False, f"计划执行时间不能早于当前时间。当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        elif strategy.strategy_type == "recurring":
            if not strategy.frequency_type or not strategy.frequency_value:
                return False, "周期性策略必须设置频率类型和频率值"
            if strategy.frequency_value <= 0:
                return False, "频率值必须大于0"
            if strategy.frequency_type not in ["hour", "day", "month"]:
                return False, "频率类型必须是hour、day或month"
            if not strategy.start_time:
                return False, "周期性策略必须设置开始时间"
            # 允许设置未来1分钟内的策略
            if strategy.start_time <= now - timedelta(minutes=1):
                return False, f"开始时间不能早于当前时间。当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
            if strategy.end_time and strategy.end_time <= strategy.start_time:
                return False, "结束时间必须晚于开始时间"
        else:
            return False, "策略类型必须是one-time或recurring"
        
        return True, "验证通过"
