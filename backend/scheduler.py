import asyncio
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from .services.strategy_service import StrategyService
from .services.backup_service import BackupService
import logging

logger = logging.getLogger(__name__)

class BackupScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        
    def start(self):
        """启动调度器"""
        if self.running:
            logger.info("调度器已在运行中")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("备份策略调度器已启动")
        
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("备份策略调度器已停止")
        
    def _run_scheduler(self):
        """调度器主循环"""
        while self.running:
            try:
                self._check_and_execute_strategies()
                # 每30秒检查一次
                time.sleep(30)
            except Exception as e:
                logger.error(f"调度器运行错误: {str(e)}")
                time.sleep(30)
                
    def _check_and_execute_strategies(self):
        """检查并执行到期的策略"""
        db = SessionLocal()
        try:
            # 获取到期的策略
            due_strategies = StrategyService.get_due_strategies(db)
            
            if due_strategies:
                logger.info(f"发现 {len(due_strategies)} 个到期策略")
                
                for strategy in due_strategies:
                    try:
                        self._execute_strategy(db, strategy)
                    except Exception as e:
                        logger.error(f"执行策略 {strategy.id} 失败: {str(e)}")
            else:
                logger.debug("没有到期的策略")
                
        except Exception as e:
            logger.error(f"检查到期策略失败: {str(e)}")
        finally:
            db.close()
            
    def _execute_strategy(self, db: Session, strategy):
        """执行单个策略"""
        logger.info(f"开始执行策略: {strategy.name} (ID: {strategy.id})")
        
        try:
            # 执行备份
            backup_result = BackupService.execute_backup(
                db=db,
                device_id=strategy.device_id,
                backup_type=strategy.backup_type
            )
            
            if backup_result and backup_result.get('success'):
                logger.info(f"策略 {strategy.name} 执行成功")
                # 标记策略已执行
                StrategyService.mark_strategy_executed(db, strategy.id)
            else:
                logger.error(f"策略 {strategy.name} 执行失败: {backup_result}")
                
        except Exception as e:
            logger.error(f"执行策略 {strategy.name} 时发生错误: {str(e)}")

# 全局调度器实例
scheduler = BackupScheduler()

def start_scheduler():
    """启动调度器"""
    scheduler.start()
    
def stop_scheduler():
    """停止调度器"""
    scheduler.stop()
