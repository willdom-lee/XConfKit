from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas import Backup as BackupSchema, BackupCreate, BackupResponse, ResponseModel, BackupWithDevice
from ..models import Backup
from ..services.backup_service import BackupService, AutoBackupService
import logging

router = APIRouter(prefix="/api/backups", tags=["备份管理"])

@router.post("/execute", response_model=BackupResponse)
def execute_backup(device_id: int, backup_type: str = "running-config", db: Session = Depends(get_db)):
    """执行手动备份"""
    result = BackupService.execute_backup(db, device_id, backup_type)
    return BackupResponse(
        success=result["success"],
        message=result["message"],
        backup_id=result.get("backup_id"),
        file_path=result.get("file_path")
    )

@router.get("/", response_model=List[BackupWithDevice])
def get_backups(device_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取备份记录"""
    return BackupService.get_backups(db, device_id=device_id, skip=skip, limit=limit)

@router.get("/{backup_id}", response_model=BackupSchema)
def get_backup(backup_id: int, db: Session = Depends(get_db)):
    """根据ID获取备份记录"""
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份记录不存在")
    return backup

@router.get("/{backup_id}/content")
def get_backup_content(backup_id: int, db: Session = Depends(get_db)):
    """获取备份文件内容（完整内容，支持滚动查看）"""
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份记录不存在")
    
    if not backup.file_path:
        raise HTTPException(status_code=404, detail="备份文件不存在")
    
    try:
        import os
        if not os.path.exists(backup.file_path):
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        with open(backup.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_size": backup.file_size,
            "backup_type": backup.backup_type,
            "created_at": backup.created_at.isoformat(),
            "total_lines": len(content.split('\n'))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取备份文件失败: {str(e)}")

@router.get("/{backup_id}/download")
def download_backup(backup_id: int, db: Session = Depends(get_db)):
    """下载备份文件"""
    from fastapi.responses import FileResponse
    import os
    
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份记录不存在")
    
    if not backup.file_path:
        raise HTTPException(status_code=404, detail="备份文件不存在")
    
    if not os.path.exists(backup.file_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    
    # 获取文件名
    filename = os.path.basename(backup.file_path)
    
    # 返回文件下载响应
    return FileResponse(
        path=backup.file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.delete("/{backup_id}", response_model=ResponseModel)
def delete_backup(backup_id: int, db: Session = Depends(get_db)):
    """删除备份记录"""
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份记录不存在")
    
    # 保存设备ID，用于后续更新设备信息
    device_id = backup.device_id
    
    # 删除备份文件
    if backup.file_path:
        try:
            import os
            if os.path.exists(backup.file_path):
                os.remove(backup.file_path)
        except Exception as e:
            pass  # 忽略文件删除错误
    
    # 删除数据库记录
    db.delete(backup)
    db.commit()
    
    # 更新设备的最近备份信息
    from ..services.backup_service import BackupService
    BackupService.update_device_last_backup_info(db, device_id)
    
    return ResponseModel(success=True, message="备份记录删除成功")

@router.post("/batch-delete", response_model=ResponseModel)
def batch_delete_backups(backup_ids: List[int], db: Session = Depends(get_db)):
    """批量删除备份记录"""
    if not backup_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的备份记录")
    
    deleted_count = 0
    failed_count = 0
    affected_devices = set()  # 记录受影响的设备ID
    
    for backup_id in backup_ids:
        try:
            backup = db.query(Backup).filter(Backup.id == backup_id).first()
            if backup:
                # 记录受影响的设备ID
                affected_devices.add(backup.device_id)
                
                # 删除备份文件
                if backup.file_path:
                    try:
                        import os
                        if os.path.exists(backup.file_path):
                            os.remove(backup.file_path)
                    except Exception as e:
                        pass  # 忽略文件删除错误
                
                # 删除数据库记录
                db.delete(backup)
                deleted_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
    
    db.commit()
    
    # 更新受影响设备的最近备份信息
    from ..services.backup_service import BackupService
    for device_id in affected_devices:
        BackupService.update_device_last_backup_info(db, device_id)
    
    message = f"成功删除 {deleted_count} 条备份记录"
    if failed_count > 0:
        message += f"，{failed_count} 条删除失败"
    
    return ResponseModel(success=True, message=message)

@router.post("/auto-backup/start")
async def start_auto_backup(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """启动自动备份"""
    try:
        # 在后台执行自动备份
        background_tasks.add_task(AutoBackupService.perform_auto_backup)
        return {"success": True, "message": "自动备份已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动自动备份失败: {str(e)}")

@router.get("/auto-backup/status")
async def get_auto_backup_status(db: Session = Depends(get_db)):
    """获取自动备份状态"""
    try:
        # 检查自动备份配置
        from ..services.config_manager import ConfigManager
        
        auto_backup_enabled = ConfigManager.get_config('backup', 'enable_auto_backup', True)
        auto_backup_time = ConfigManager.get_config('backup', 'auto_backup_time', '02:00')
        retention_days = ConfigManager.get_config('backup', 'backup_retention_days', 30)
        
        # 获取最近的自动备份记录
        recent_auto_backups = db.query(Backup).filter(
            Backup.status == 'completed',
            Backup.backup_type.like('%auto%')
        ).order_by(Backup.created_at.desc()).limit(5).all()
        
        return {
            "enabled": auto_backup_enabled,
            "schedule_time": auto_backup_time,
            "retention_days": retention_days,
            "recent_backups": [
                {
                    "id": backup.id,
                    "device_id": backup.device_id,
                    "backup_type": backup.backup_type,
                    "status": backup.status,
                    "created_at": backup.created_at.isoformat() if backup.created_at else None
                }
                for backup in recent_auto_backups
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自动备份状态失败: {str(e)}")

@router.post("/auto-backup/config")
async def update_auto_backup_config(
    enabled: bool = None,
    schedule_time: str = None,
    retention_days: int = None,
    db: Session = Depends(get_db)
):
    """更新自动备份配置"""
    try:
        from ..services.config_manager import ConfigManager
        
        if enabled is not None:
            ConfigManager.set_config(db, 'backup', 'enable_auto_backup', str(enabled).lower())
        
        if schedule_time is not None:
            ConfigManager.set_config(db, 'backup', 'auto_backup_time', schedule_time)
        
        if retention_days is not None:
            ConfigManager.set_config(db, 'backup', 'backup_retention_days', str(retention_days))
        
        return {"success": True, "message": "自动备份配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新自动备份配置失败: {str(e)}")
