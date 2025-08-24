from sqlalchemy.orm import Session
from ..models import Device
from ..schemas import DeviceCreate, DeviceUpdate
import paramiko
import socket
import time
import ping3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from .config_manager import ConfigManager
from threading import Lock

# 全局会话管理器
_ssh_sessions = {}
_ssh_channels = {}
_session_lock = Lock()

logger = logging.getLogger(__name__)

class DeviceService:
    """设备服务类"""
    
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
    def test_connection(device: Device, db: Session = None) -> dict:
        """测试设备连接"""
        try:
            # 先测试网络延迟
            latency_result = DeviceService._test_network_latency(device.ip_address)
            
            # 测试SSH连接
            ssh_result = DeviceService._test_ssh_connection(device)
            
            # 如果数据库会话可用，更新设备状态
            if db:
                DeviceService._update_device_connection_status(db, device.id, ssh_result["success"], latency_result.get("latency"))
            
            # 合并结果
            result = {
                "success": ssh_result["success"],
                "message": ssh_result["message"],
                "latency": latency_result.get("latency"),
                "latency_message": latency_result.get("message", ""),
                "output": ssh_result.get("output", "")
            }
            
            return result
        except (ValueError, TypeError) as e:
            return {"success": False, "message": f"连接测试参数错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"连接测试失败: {str(e)}"}
    
    @staticmethod
    def _test_network_latency(ip_address: str) -> dict:
        """测试网络延迟"""
        try:
            # 从配置获取超时时间
            ping_timeout = ConfigManager.get_config('connection', 'ping_timeout', 3)
            
            # 使用ping3库测试延迟
            result = ping3.ping(ip_address, timeout=ping_timeout)
            if result is not None:
                latency_ms = result * 1000  # 转换为毫秒
                return {
                    "latency": round(latency_ms, 2),
                    "message": f"网络延迟: {round(latency_ms, 2)}ms"
                }
            else:
                return {
                    "latency": None,
                    "message": "网络不可达"
                }
        except (ValueError, TypeError) as e:
            return {
                "latency": None,
                "message": f"延迟测试参数错误: {str(e)}"
            }
        except Exception as e:
            return {
                "latency": None,
                "message": f"延迟测试失败: {str(e)}"
            }
    
    @staticmethod
    def _test_ssh_connection(device: Device) -> dict:
        """测试SSH连接"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 从配置获取超时时间
            ssh_timeout = ConfigManager.get_config('connection', 'ssh_timeout', 10)
            banner_timeout = ConfigManager.get_config('connection', 'banner_timeout', 60)
            ssh_command_timeout = ConfigManager.get_config('connection', 'ssh_command_timeout', 5)
            
            # 设置连接超时，并配置支持旧SSH算法
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用设备配置的端口
                username=device.username,
                password=device.password,
                timeout=ssh_timeout,
                banner_timeout=banner_timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 简单测试：尝试执行一个基本命令
            try:
                stdin, stdout, stderr = ssh.exec_command("echo 'test'", timeout=ssh_command_timeout)
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
            except Exception as e:
                logger.warning(f"关闭SSH连接失败: {str(e)}")
    
    @staticmethod
    def _update_device_connection_status(db: Session, device_id: int, success: bool, latency: float = None):
        """更新设备连接状态"""
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                device.connection_status = "success" if success else "failed"
                device.last_test_time = datetime.now()
                if latency is not None:
                    device.last_latency = latency
                db.commit()
        except Exception as e:
            # 记录错误但不影响主流程
            logger.error(f"更新设备状态失败: {str(e)}")

    @staticmethod
    def get_ssh_session(device_id: int, device: Device) -> Optional[paramiko.SSHClient]:
        """获取或创建SSH会话"""
        with _session_lock:
            if device_id in _ssh_sessions:
                session = _ssh_sessions[device_id]
                try:
                    # 测试会话是否仍然有效
                    session.get_transport().send_ignore()
                    return session
                except:
                    # 会话已断开，删除并重新创建
                    try:
                        session.close()
                    except:
                        pass
                    del _ssh_sessions[device_id]
                    if device_id in _ssh_channels:
                        del _ssh_channels[device_id]
            
            # 创建新会话
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    hostname=device.ip_address,
                    port=device.port or 22,
                    username=device.username,
                    password=device.password,
                    timeout=30
                )
                _ssh_sessions[device_id] = ssh
                return ssh
            except Exception as e:
                print(f"创建SSH会话失败: {e}")
                return None
    
    @staticmethod
    def get_ssh_channel(device_id: int, device: Device) -> Optional[paramiko.Channel]:
        """获取或创建SSH channel"""
        with _session_lock:
            if device_id in _ssh_channels:
                channel = _ssh_channels[device_id]
                try:
                    # 测试channel是否仍然有效
                    if not channel.closed:
                        return channel
                except:
                    pass
                # channel无效，删除
                if device_id in _ssh_channels:
                    del _ssh_channels[device_id]
            
            # 创建新channel
            ssh = DeviceService.get_ssh_session(device_id, device)
            if not ssh:
                return None
            
            try:
                channel = ssh.invoke_shell()
                channel.settimeout(30)
                _ssh_channels[device_id] = channel
                return channel
            except Exception as e:
                print(f"创建SSH channel失败: {e}")
                return None
    
    @staticmethod
    def close_ssh_session(device_id: int):
        """关闭SSH会话"""
        with _session_lock:
            if device_id in _ssh_channels:
                try:
                    _ssh_channels[device_id].close()
                except:
                    pass
                del _ssh_channels[device_id]
            
            if device_id in _ssh_sessions:
                try:
                    _ssh_sessions[device_id].close()
                except:
                    pass
                del _ssh_sessions[device_id]
    
    @staticmethod
    def execute_cli_command(device: Device, command: str) -> Dict[str, Any]:
        """执行CLI命令"""
        try:
            # 获取SSH连接配置
            ssh_host = device.ip_address
            ssh_port = device.port or 22
            ssh_username = device.username
            ssh_password = device.password
            ssh_command_timeout = ConfigManager.get_config('connection', 'ssh_command_timeout', 30)
            
            # 创建SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=ssh_host,
                port=ssh_port,
                username=ssh_username,
                password=ssh_password,
                timeout=ssh_command_timeout
            )
            
            # 检测设备类型
            device_type = DeviceService._detect_device_type(device)
            
            # 根据设备类型选择执行方法
            if device_type == 'h3c':
                result = DeviceService._execute_h3c_command_simple(ssh, command)
            else:
                result = DeviceService._execute_simple_command(ssh, command)
            
            ssh.close()
            return result
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"CLI命令执行失败: {str(e)}",
                "exit_status": -1,
                "command": command
            }

    @staticmethod
    def _detect_device_type(device: Device) -> str:
        """检测设备类型"""
        # 根据设备名称推断
        device_name = device.name.lower()
        if 'h3c' in device_name or 'hp' in device_name:
            return 'h3c'
        elif 'cisco' in device_name:
            return 'cisco'
        elif 'huawei' in device_name:
            return 'huawei'
        else:
            # 默认返回h3c，因为当前测试设备都是H3C
            return 'h3c'

    @staticmethod
    def _execute_simple_command(ssh, command: str, timeout: int) -> Dict[str, Any]:
        """执行简单命令"""
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        
        # 读取输出
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()
        
        # 获取退出状态
        exit_status = stdout.channel.recv_exit_status()
        
        # 对于网络设备，只要有输出就认为命令执行成功
        success = bool(output) or exit_status == 0
        
        return {
            "success": success,
            "output": output,
            "error": error_output,
            "exit_status": exit_status,
            "command": command
        }

    @staticmethod
    def _execute_h3c_command_simple(ssh, command: str) -> Dict[str, Any]:
        """执行H3C设备命令（简化版本）"""
        import time
        
        try:
            # 创建交互式会话
            channel = ssh.invoke_shell()
            channel.settimeout(30)
            
            # 等待登录完成
            time.sleep(2)
            
            # 读取初始输出
            while channel.recv_ready():
                channel.recv(1024)
            
            # 发送命令
            channel.send(command + "\n")
            time.sleep(2)
            
            # 读取输出
            output = ""
            max_iterations = 20
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # 读取当前输出
                current_chunk = ""
                while channel.recv_ready():
                    chunk = channel.recv(1024).decode('utf-8', errors='ignore')
                    current_chunk += chunk
                
                if current_chunk:
                    output += current_chunk
                
                # 检查是否有分页提示
                if "---- More ----" in current_chunk:
                    channel.send(" ")
                    time.sleep(0.3)
                else:
                    # 检查是否命令执行完成
                    if iteration > 3 and not channel.recv_ready():
                        break
                
                time.sleep(0.3)
            
            channel.close()
            
            # 清理输出
            cleaned_output = output
            lines = cleaned_output.split('\n')
            filtered_lines = []
            for line in lines:
                # 移除命令回显行
                if command in line and line.strip().startswith(command):
                    continue
                # 移除空的提示符行
                if line.strip() in ['<admin>', '[admin]', 'admin#']:
                    continue
                # 移除分页提示行
                if '---- More ----' in line:
                    continue
                # 清理行首的多余空格
                cleaned_line = line
                if line.startswith(' ' * 16):
                    cleaned_line = line[16:]
                elif line.startswith(' ' * 8):
                    cleaned_line = line[8:]
                # 保留其他所有行
                if cleaned_line.strip() or cleaned_line == '':
                    filtered_lines.append(cleaned_line)
            
            cleaned_output = '\n'.join(filtered_lines).strip()
            
            # 对于配置命令，即使没有输出也认为成功
            config_commands = ['sysname', 'interface', 'ip', 'vlan', 'user', 'undo', 'system']
            is_config_command = any(cmd in command.lower() for cmd in config_commands)
            
            success = bool(cleaned_output) or is_config_command
            
            return {
                "success": success,
                "output": cleaned_output,
                "error": "",
                "exit_status": 0 if success else -1,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"H3C命令执行失败: {str(e)}",
                "exit_status": -1,
                "command": command
            }
