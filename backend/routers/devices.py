from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from ..database import get_db
from ..schemas import Device, DeviceCreate, DeviceUpdate, ResponseModel
from ..services.device_service import DeviceService

class CLICommandRequest(BaseModel):
    command: str

router = APIRouter(prefix="/api/devices", tags=["设备管理"])

@router.post("/", response_model=Device)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """创建设备"""
    try:
        return DeviceService.create_device(db, device)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建设备失败: {str(e)}")

@router.get("/", response_model=List[Device])
def get_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取设备列表"""
    return DeviceService.get_devices(db, skip=skip, limit=limit)

@router.get("/{device_id}", response_model=Device)
def get_device(device_id: int, db: Session = Depends(get_db)):
    """根据ID获取设备"""
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device

@router.put("/{device_id}", response_model=Device)
def update_device(device_id: int, device_update: DeviceUpdate, db: Session = Depends(get_db)):
    """更新设备"""
    device = DeviceService.update_device(db, device_id, device_update)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device

@router.delete("/{device_id}", response_model=ResponseModel)
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """删除设备"""
    success = DeviceService.delete_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="设备不存在")
    return ResponseModel(success=True, message="设备删除成功")

@router.post("/{device_id}/test", response_model=ResponseModel)
def test_device_connection(device_id: int, db: Session = Depends(get_db)):
    """测试设备连接"""
    try:
        device = DeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        result = DeviceService.test_connection(device, db)
        
        # 构建返回数据
        data = {}
        if result.get("output"):
            data["output"] = result["output"]
        if result.get("latency") is not None:
            data["latency"] = result["latency"]
        if result.get("latency_message"):
            data["latency_message"] = result["latency_message"]
        
        return ResponseModel(
            success=result["success"],
            message=result["message"],
            data=data if data else None
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"测试连接时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"测试连接失败: {str(e)}")

@router.post("/{device_id}/quick-backup", response_model=ResponseModel)
def quick_backup_device(device_id: int, db: Session = Depends(get_db)):
    """快速备份设备（使用默认备份类型）"""
    try:
        from ..services.config_manager import ConfigManager
        from ..services.backup_service import BackupService
        
        # 获取默认备份类型
        default_backup_type = ConfigManager.get_config('system', 'default_backup_type', 'running-config')
        
        # 执行备份
        result = BackupService.execute_backup(db, device_id, default_backup_type)
        
        return ResponseModel(
            success=result["success"],
            message=result["message"],
            data=result
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"快速备份时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"快速备份失败: {str(e)}")

@router.post("/{device_id}/cli")
async def execute_cli_command(device_id: int, command_data: dict, db: Session = Depends(get_db)):
    """执行CLI命令"""
    try:
        device = DeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        command = command_data.get("command", "")
        if not command:
            raise HTTPException(status_code=400, detail="命令不能为空")
        
        result = DeviceService.execute_cli_command(device, command)
        return {"success": True, "message": "命令执行成功", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"命令执行失败: {str(e)}")

@router.delete("/{device_id}/cli")
async def close_cli_session(device_id: int):
    """关闭CLI会话"""
    try:
        DeviceService.close_ssh_session(device_id)
        return {"success": True, "message": "CLI会话已关闭"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关闭会话失败: {str(e)}")
