from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import Device, DeviceCreate, DeviceUpdate, ResponseModel
from ..services.device_service import DeviceService

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
        
        result = DeviceService.test_connection(device)
        return ResponseModel(
            success=result["success"],
            message=result["message"],
            data={"output": result.get("output")} if result.get("output") else None
        )
    except Exception as e:
        print(f"测试连接时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"测试连接失败: {str(e)}")
