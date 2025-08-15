from sqlalchemy.orm import Session
from ..models import Device
from ..schemas import DeviceCreate, DeviceUpdate
import paramiko
import socket
from typing import List, Optional

class DeviceService:
    @staticmethod
    def create_device(db: Session, device: DeviceCreate) -> Device:
        """创建设备"""
        db_device = Device(**device.model_dump())
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return db_device
    
    @staticmethod
    def get_devices(db: Session, skip: int = 0, limit: int = 100) -> List[Device]:
        """获取设备列表"""
        return db.query(Device).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_device(db: Session, device_id: int) -> Optional[Device]:
        """根据ID获取设备"""
        return db.query(Device).filter(Device.id == device_id).first()
    
    @staticmethod
    def update_device(db: Session, device_id: int, device_update: DeviceUpdate) -> Optional[Device]:
        """更新设备"""
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if not db_device:
            return None
        
        update_data = device_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)
        
        db.commit()
        db.refresh(db_device)
        return db_device
    
    @staticmethod
    def delete_device(db: Session, device_id: int) -> bool:
        """删除设备"""
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if not db_device:
            return False
        
        db.delete(db_device)
        db.commit()
        return True
    
    @staticmethod
    def test_connection(device: Device) -> dict:
        """测试设备连接"""
        try:
            return DeviceService._test_ssh_connection(device)
        except Exception as e:
            return {"success": False, "message": f"连接测试失败: {str(e)}"}
    
    @staticmethod
    def _test_ssh_connection(device: Device) -> dict:
        """测试SSH连接"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 设置连接超时，并配置支持旧SSH算法
            ssh.connect(
                device.ip_address,
                port=device.port,
                username=device.username,
                password=device.password,
                timeout=10,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 简单测试：尝试执行一个基本命令
            try:
                stdin, stdout, stderr = ssh.exec_command("echo 'test'", timeout=5)
                output = stdout.read().decode('utf-8').strip()
                if output == "test":
                    return {"success": True, "message": "SSH连接成功", "output": "连接测试通过"}
                else:
                    return {"success": True, "message": "SSH连接成功", "output": "连接建立但命令执行异常"}
            except Exception as cmd_error:
                return {"success": True, "message": "SSH连接成功", "output": f"连接建立但命令执行失败: {str(cmd_error)}"}
                
        except paramiko.AuthenticationException:
            return {"success": False, "message": "认证失败，请检查用户名和密码"}
        except paramiko.SSHException as e:
            return {"success": False, "message": f"SSH连接错误: {str(e)}"}
        except socket.timeout:
            return {"success": False, "message": "连接超时"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}
        finally:
            try:
                ssh.close()
            except:
                pass
