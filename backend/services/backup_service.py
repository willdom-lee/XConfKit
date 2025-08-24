from sqlalchemy.orm import Session
from ..models import Device, Backup
from ..schemas import BackupCreate
from ..services.config_manager import ConfigManager
import paramiko
import os
from datetime import datetime
from typing import Optional
import logging

import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Device, Backup, Config
from ..database import get_db
import paramiko
import socket
import time
import threading
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupService:
    @staticmethod
    def create_backup(db: Session, backup: BackupCreate) -> Backup:
        """创建备份记录"""
        db_backup = Backup(**backup.model_dump())
        db.add(db_backup)
        db.commit()
        db.refresh(db_backup)
        return db_backup
    
    @staticmethod
    def get_backups(db: Session, device_id: Optional[int] = None, skip: int = 0, limit: int = 100):
        """获取备份记录（最新备份在前）"""
        query = db.query(Backup).join(Device, Backup.device_id == Device.id)
        if device_id:
            query = query.filter(Backup.device_id == device_id)
        # 按创建时间倒序排列，最新备份在前
        return query.order_by(Backup.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def execute_backup(db: Session, device_id: int, backup_type: str) -> dict:
        """执行备份操作"""
        # 获取设备信息
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {"success": False, "message": "设备不存在"}
        
        # 创建备份记录
        backup = BackupCreate(device_id=device_id, backup_type=backup_type)
        db_backup = BackupService.create_backup(db, backup)
        
        result = {"success": False, "message": "备份执行失败"}
        
        try:
            # 执行备份
            result = BackupService._perform_backup(device, backup_type, db_backup.id)
            
            # 更新备份记录
            if result["success"]:
                db_backup.status = "success"
                db_backup.file_path = result["file_path"]
                db_backup.file_size = result["file_size"]
                
                # 读取文件内容并保存到数据库
                try:
                    with open(result["file_path"], 'r', encoding='utf-8') as f:
                        content = f.read()
                        db_backup.content = content
                        logger.info(f"已保存配置文件内容到数据库，长度: {len(content)} 字符")
                except Exception as content_error:
                    logger.warning(f"读取配置文件内容失败: {str(content_error)}")
                    # 即使读取内容失败，也不影响备份的成功状态
                
                # 更新设备的最近备份信息
                device.last_backup_time = datetime.now()
                device.last_backup_type = backup_type
            else:
                db_backup.status = "failed"
                db_backup.error_message = result["message"]
            
            db.commit()
            
        except (ValueError, TypeError) as e:
            logger.error(f"备份执行参数错误: {str(e)}")
            db_backup.status = "failed"
            db_backup.error_message = f"参数错误: {str(e)}"
            db.commit()
            result = {"success": False, "message": f"备份执行参数错误: {str(e)}"}
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"备份连接失败: {str(e)}")
            db_backup.status = "failed"
            db_backup.error_message = f"连接失败: {str(e)}"
            db.commit()
            result = {"success": False, "message": f"备份连接失败: {str(e)}"}
        except (OSError, IOError) as e:
            logger.error(f"备份文件操作失败: {str(e)}")
            db_backup.status = "failed"
            db_backup.error_message = f"文件操作失败: {str(e)}"
            db.commit()
            result = {"success": False, "message": f"备份文件操作失败: {str(e)}"}
        except Exception as e:
            logger.error(f"备份执行失败: {str(e)}")
            db_backup.status = "failed"
            db_backup.error_message = str(e)
            db.commit()
            result = {"success": False, "message": f"备份执行失败: {str(e)}"}
        
        # 确保返回有意义的错误信息
        if not result.get("success", False) and not result.get("message"):
            result["message"] = "备份执行失败，请检查设备连接和命令配置"
        

        
        return result
    
    @staticmethod
    def update_device_last_backup_info(db: Session, device_id: int):
        """更新设备的最近备份信息"""
        try:
            # 获取设备
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return
            
            # 查找该设备的最新备份记录
            latest_backup = db.query(Backup).filter(
                Backup.device_id == device_id,
                Backup.status == 'success'
            ).order_by(Backup.created_at.desc()).first()
            
            if latest_backup:
                # 更新设备的最近备份信息
                device.last_backup_time = latest_backup.created_at
                device.last_backup_type = latest_backup.backup_type
            else:
                # 如果没有成功的备份记录，清空最近备份信息
                device.last_backup_time = None
                device.last_backup_type = None
            
            db.commit()
            logger.info(f"已更新设备 {device.name} 的最近备份信息")
            
        except Exception as e:
            logger.error(f"更新设备最近备份信息失败: {str(e)}")
            db.rollback()
    
    @staticmethod
    def _perform_backup(device: Device, backup_type: str, backup_id: int) -> dict:
        """执行具体的备份操作"""
        try:
            logger.info(f"开始执行备份: 设备={device.name}, 类型={backup_type}")
            if device.protocol.lower() == "ssh":
                result = BackupService._ssh_backup(device, backup_type, backup_id)
                logger.info(f"SSH备份结果: {result}")
                return result
            else:
                return {"success": False, "message": f"不支持的协议: {device.protocol}"}
        except Exception as e:
            logger.error(f"备份执行异常: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return {"success": False, "message": f"备份失败: {str(e)}"}
    
    @staticmethod
    def _ssh_backup(device: Device, backup_type: str, backup_id: int) -> dict:
        """SSH备份"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用设备配置的端口
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 检测设备类型
            device_type = BackupService._detect_device_type(ssh)
            logger.info(f"检测到设备类型: {device_type}")
            
            # 根据设备类型选择备份方法
            if device_type == 'h3c':
                return BackupService._h3c_backup(device, backup_type, backup_id)
            elif device_type == 'cisco':
                return BackupService._cisco_backup(device, backup_type, backup_id)
            elif device_type == 'huawei':
                return BackupService._huawei_backup(device, backup_type, backup_id)
            else:
                # 未知设备类型，使用通用方法
                return BackupService._generic_backup(device, backup_type, backup_id)
                
                # 普通命令执行
                try:
                    stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
                    output = stdout.read().decode('utf-8')
                    error = stderr.read().decode('utf-8')
                    
                    logger.info(f"命令输出长度: {len(output)}")
                    logger.info(f"错误输出: {error}")
                    
                    if error and not output.strip():
                        return {"success": False, "message": f"命令执行错误: {error}"}
                    
                    if not output.strip():
                        return {"success": False, "message": "命令执行成功但无输出"}
                    
                    # 保存到文件
                    file_path = BackupService._save_backup_file(device, backup_type, backup_id, output)
                    file_size = os.path.getsize(file_path)
                    
                    return {
                        "success": True,
                        "message": "备份成功",
                        "file_path": file_path,
                        "file_size": file_size
                    }
                except Exception as cmd_error:
                    logger.error(f"命令执行异常: {str(cmd_error)}")
                    import traceback
                    logger.error(f"异常堆栈: {traceback.format_exc()}")
                    return {"success": False, "message": f"命令执行异常: {str(cmd_error)}"}
            
        except paramiko.AuthenticationException:
            return {"success": False, "message": "认证失败，请检查用户名和密码"}
        except paramiko.SSHException as e:
            return {"success": False, "message": f"SSH连接错误: {str(e)}"}
        except Exception as e:
            logger.error(f"备份过程中发生异常: {str(e)}")
            return {"success": False, "message": f"备份失败: {str(e)}"}
        finally:
            try:
                ssh.close()
            except Exception as close_error:
                logger.warning(f"关闭SSH连接时出错: {close_error}")
                pass
    
    @staticmethod
    def _detect_device_type(ssh) -> str:
        """检测设备类型"""
        try:
            # 尝试执行一些命令来检测设备类型
            stdin, stdout, stderr = ssh.exec_command("display version", timeout=10)
            output = stdout.read().decode('utf-8').lower()
            
            if 'h3c' in output or 'comware' in output:
                return 'h3c'
            elif 'cisco' in output:
                return 'cisco'
            elif 'huawei' in output:
                return 'huawei'
            else:
                # 尝试其他命令
                stdin, stdout, stderr = ssh.exec_command("show version", timeout=10)
                output = stdout.read().decode('utf-8').lower()
                
                if 'cisco' in output:
                    return 'cisco'
                else:
                    return 'unknown'
        except Exception as e:
            logger.warning(f"设备类型检测失败: {str(e)}")
            return 'unknown'
    
    @staticmethod
    def _build_command_sequence(device_type: str, command: str) -> str:
        """构建完整的命令序列"""
        if device_type == 'h3c':
            # H3C设备：某些命令可以直接执行，不需要进入系统视图
            # 如果命令需要系统视图，会在错误信息中提示
            return command
        elif device_type == 'cisco':
            # 思科设备：某些命令需要特权模式
            if 'show' in command.lower():
                return f"enable\n{command}"
            else:
                return command
        elif device_type == 'huawei':
            # 华为设备：某些命令可以直接执行
            return command
        else:
            # 未知设备类型，直接执行命令
            return command
    
    @staticmethod
    def _h3c_backup(device: Device, backup_type: str, backup_id: int) -> dict:
        """H3C设备通用备份方法（避免SSH会话冲突）"""
        try:
            import paramiko
            import time
            
            # 创建新的SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用默认SSH端口
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # H3C设备命令映射
            h3c_commands = {
                "running-config": "display current-configuration",
                "startup-config": "display saved-configuration",
                "ip-route": "display ip routing-table",
                "arp-table": "display arp",
                "mac-table": "display mac-address"
            }
            
            command = h3c_commands.get(backup_type, "display current-configuration")
            logger.info(f"使用H3C命令: {command}")
            
            # 对于配置命令，使用交互式方法
            if backup_type in ['running-config', 'startup-config']:
                ssh.close()
                return BackupService._interactive_h3c_backup(device, backup_type, backup_id, command)
            else:
                # 其他命令直接执行
                try:
                    stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
                    output = stdout.read().decode('utf-8')
                    error = stderr.read().decode('utf-8')
                    
                    ssh.close()
                    
                    logger.info(f"H3C命令输出长度: {len(output)}")
                    logger.info(f"H3C命令错误输出: {error}")
                    
                    if output.strip():
                        # 保存到文件
                        file_path = BackupService._save_backup_file(device, backup_type, backup_id, output)
                        file_size = os.path.getsize(file_path)
                        
                        return {
                            "success": True,
                            "message": "备份成功",
                            "file_path": file_path,
                            "file_size": file_size
                        }
                    else:
                        return {"success": False, "message": "命令执行成功但无输出"}
                        
                except Exception as e:
                    ssh.close()
                    logger.error(f"H3C命令执行失败: {str(e)}")
                    return {"success": False, "message": f"H3C命令执行失败: {str(e)}"}
            
        except Exception as e:
            logger.error(f"H3C备份失败: {str(e)}")
            return {"success": False, "message": f"H3C备份失败: {str(e)}"}
    
    @staticmethod
    def _cisco_backup(device: Device, backup_type: str, backup_id: int) -> dict:
        """Cisco设备备份方法"""
        try:
            import paramiko
            
            # 创建新的SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用默认SSH端口
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Cisco设备命令映射
            cisco_commands = {
                "running-config": "show running-config",
                "startup-config": "show startup-config",
                "ip-route": "show ip route",
                "arp-table": "show arp",
                "mac-table": "show mac address-table"
            }
            
            command = cisco_commands.get(backup_type, "show running-config")
            logger.info(f"使用Cisco命令: {command}")
            
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            ssh.close()
            
            if error and not output.strip():
                return {"success": False, "message": f"命令执行错误: {error}"}
            
            if not output.strip():
                return {"success": False, "message": "命令执行成功但无输出"}
            
            # 保存到文件
            file_path = BackupService._save_backup_file(device, backup_type, backup_id, output)
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "message": "备份成功",
                "file_path": file_path,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"Cisco备份失败: {str(e)}")
            return {"success": False, "message": f"Cisco备份失败: {str(e)}"}
    
    @staticmethod
    def _huawei_backup(device: Device, backup_type: str, backup_id: int) -> dict:
        """华为设备备份方法"""
        try:
            import paramiko
            
            # 创建新的SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用默认SSH端口
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 华为设备命令映射
            huawei_commands = {
                "running-config": "display current-configuration",
                "startup-config": "display saved-configuration",
                "ip-route": "display ip routing-table",
                "arp-table": "display arp",
                "mac-table": "display mac-address"
            }
            
            command = huawei_commands.get(backup_type, "display current-configuration")
            logger.info(f"使用华为命令: {command}")
            
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            ssh.close()
            
            if error and not output.strip():
                return {"success": False, "message": f"命令执行错误: {error}"}
            
            if not output.strip():
                return {"success": False, "message": "命令执行成功但无输出"}
            
            # 保存到文件
            file_path = BackupService._save_backup_file(device, backup_type, backup_id, output)
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "message": "备份成功",
                "file_path": file_path,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"华为备份失败: {str(e)}")
            return {"success": False, "message": f"华为备份失败: {str(e)}"}
    
    @staticmethod
    def _generic_backup(device: Device, backup_type: str, backup_id: int) -> dict:
        """通用设备备份方法（未知设备类型）"""
        try:
            import paramiko
            
            # 创建新的SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用默认SSH端口
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 通用命令映射（尝试多种可能的命令）
            generic_commands = {
                "running-config": ["show running-config", "display current-configuration", "show config"],
                "startup-config": ["show startup-config", "display saved-configuration", "show config startup"],
                "ip-route": ["show ip route", "display ip routing-table", "show route"],
                "arp-table": ["show arp", "display arp", "show arp table"],
                "mac-table": ["show mac address-table", "display mac-address", "show mac table"]
            }
            
            commands_to_try = generic_commands.get(backup_type, ["show running-config"])
            logger.info(f"尝试通用命令: {commands_to_try}")
            
            for command in commands_to_try:
                try:
                    stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
                    output = stdout.read().decode('utf-8')
                    error = stderr.read().decode('utf-8')
                    
                    if output.strip() and not error:
                        logger.info(f"通用命令成功: {command}")
                        ssh.close()
                        
                        # 保存到文件
                        file_path = BackupService._save_backup_file(device, backup_type, backup_id, output)
                        file_size = os.path.getsize(file_path)
                        
                        return {
                            "success": True,
                            "message": f"备份成功（使用命令: {command}）",
                            "file_path": file_path,
                            "file_size": file_size
                        }
                except Exception as cmd_error:
                    logger.warning(f"命令 {command} 失败: {str(cmd_error)}")
                    continue
            
            ssh.close()
            return {"success": False, "message": "所有通用命令都执行失败"}
            
        except Exception as e:
            logger.error(f"通用备份失败: {str(e)}")
            return {"success": False, "message": f"通用备份失败: {str(e)}"}
    
    @staticmethod
    def _h3c_config_backup(device: Device, backup_type: str, backup_id: int, command: str) -> dict:
        """H3C设备配置备份专用方法（参考Oxidized设计）"""
        try:
            import paramiko
            import time
            
            # 创建新的SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用默认SSH端口
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 参考Oxidized的H3C模型，使用正确的命令映射
            command_map = {
                'running-config': 'display current-configuration',
                'startup-config': 'display startup-configuration',
                'ip-route': 'display ip routing-table',
                'arp-table': 'display arp',
                'mac-table': 'display mac-address'
            }
            
            h3c_command = command_map.get(backup_type, command)
            logger.info(f"使用H3C命令: {h3c_command}")
            
            # 对于配置命令，需要先进入系统视图（参考Oxidized的H3C模型）
            if backup_type in ['running-config', 'startup-config']:
                logger.info("配置命令需要系统视图，使用交互式方法")
                return BackupService._interactive_h3c_backup(device, backup_type, backup_id, h3c_command)
            else:
                # 其他命令可以直接执行
                # 使用配置的超时时间
                backup_timeout = ConfigManager.get_config('backup', 'backup_timeout', 300)
                stdin, stdout, stderr = ssh.exec_command(h3c_command, timeout=backup_timeout)
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                
                ssh.close()
                
                logger.info(f"H3C命令输出长度: {len(output)}")
                logger.info(f"H3C命令错误输出: {error}")
                
                if output.strip() and len(output) > 100:
                    # 保存到文件
                    file_path = BackupService._save_backup_file(device, backup_type, backup_id, output)
                    file_size = os.path.getsize(file_path)
                    
                    return {
                        "success": True,
                        "message": "备份成功",
                        "file_path": file_path,
                        "file_size": file_size
                    }
                else:
                    return {"success": False, "message": "命令执行成功但输出不足"}
            
        except Exception as e:
            logger.error(f"H3C配置备份失败: {str(e)}")
            return {"success": False, "message": f"H3C配置备份失败: {str(e)}"}
    
    @staticmethod
    def _interactive_h3c_backup(device: Device, backup_type: str, backup_id: int, command: str) -> dict:
        """H3C设备交互式备份方法（参考Oxidized的交互式处理）"""
        try:
            import paramiko
            import time
            
            # 创建新的SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 使用配置的超时时间
            ssh_timeout = ConfigManager.get_config('connection', 'ssh_timeout', 10)
            banner_timeout = ConfigManager.get_config('connection', 'banner_timeout', 60)
            
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port,  # 使用默认SSH端口
                username=device.username,
                password=device.password,
                timeout=ssh_timeout,
                banner_timeout=banner_timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 创建交互式会话
            channel = ssh.invoke_shell()
            # 使用配置的超时时间
            interactive_timeout = ConfigManager.get_config('backup', 'backup_timeout', 300)
            channel.settimeout(interactive_timeout)
            
            # 等待登录完成
            time.sleep(2)
            
            # 读取初始输出
            while channel.recv_ready():
                channel.recv(1024)
            
            # 参考Oxidized的H3C交互式处理
            # 先进入系统视图
            logger.info("进入系统视图")
            channel.send("system-view\n")
            time.sleep(3)
            
            # 读取system-view输出
            while channel.recv_ready():
                channel.recv(1024)
            
            # 发送配置命令并处理分页
            logger.info(f"发送H3C命令: {command}")
            channel.send(command + "\n")
            time.sleep(2)
            
            # 读取输出并处理分页（优化版本）
            output = ""
            max_iterations = 100
            iteration = 0
            last_output_length = 0
            
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
                    logger.info(f"检测到分页提示，发送空格键继续 (迭代 {iteration})")
                    channel.send(" ")
                    time.sleep(0.3)
                elif "----" in current_chunk and "More" in current_chunk:
                    logger.info(f"检测到分页提示，发送空格键继续 (迭代 {iteration})")
                    channel.send(" ")
                    time.sleep(0.3)
                else:
                    # 检查是否命令执行完成
                    if "]" in output and command in output:
                        logger.info("命令执行完成")
                        break
                    elif iteration > 20 and len(output) > 2000:
                        # 如果输出足够长，认为已完成
                        logger.info("输出足够长，认为已完成")
                        break
                    elif len(output) == last_output_length and iteration > 10:
                        # 如果输出没有变化，可能已经完成
                        logger.info("输出无变化，认为已完成")
                        break
                
                last_output_length = len(output)
                time.sleep(0.3)
            
            channel.close()
            ssh.close()
            
            logger.info(f"交互式H3C备份输出长度: {len(output)}")
            
            # 清理输出内容，移除分页提示和控制字符
            cleaned_output = BackupService._clean_h3c_output(output)
            logger.info(f"清理后输出长度: {len(cleaned_output)}")
            
            if cleaned_output.strip() and len(cleaned_output) > 100:
                # 保存到文件
                file_path = BackupService._save_backup_file(device, backup_type, backup_id, cleaned_output)
                file_size = os.path.getsize(file_path)
                
                return {
                    "success": True,
                    "message": "备份成功",
                    "file_path": file_path,
                    "file_size": file_size
                }
            else:
                return {"success": False, "message": "交互式备份成功但输出不足"}
            
        except Exception as e:
            logger.error(f"交互式H3C备份失败: {str(e)}")
            return {"success": False, "message": f"交互式H3C备份失败: {str(e)}"}
    
    @staticmethod
    def _interactive_ssh_backup(ssh, device: Device, backup_type: str, backup_id: int, command: str) -> dict:
        """交互式SSH备份（用于需要进入系统视图的命令）"""
        try:
            import time
            import paramiko
            
            # 创建新的SSH连接用于交互式会话
            interactive_ssh = paramiko.SSHClient()
            interactive_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接设备
            interactive_ssh.connect(
                device.ip_address,
                port=device.port,  # 使用默认SSH端口
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 创建交互式会话
            channel = interactive_ssh.invoke_shell()
            channel.settimeout(30)
            
            # 等待登录完成
            time.sleep(2)
            
            # 读取初始输出
            while channel.recv_ready():
                channel.recv(1024)
            
            # 发送system-view命令
            logger.info("发送system-view命令")
            channel.send("system-view\n")
            time.sleep(3)
            
            # 读取system-view输出
            while channel.recv_ready():
                channel.recv(1024)
            
            # 发送配置查看命令
            logger.info(f"发送配置命令: {command}")
            channel.send(command + "\n")
            time.sleep(2)
            
            # 读取配置输出（处理分页）
            output = ""
            max_iterations = 300  # 增加最大迭代次数
            iteration = 0
            last_output_length = 0
            no_change_count = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # 读取当前输出
                while channel.recv_ready():
                    chunk = channel.recv(1024).decode('utf-8')
                    output += chunk
                
                current_length = len(output)
                
                # 检查是否有"More"提示
                if "---- More ----" in output:
                    logger.info(f"检测到分页提示，发送空格键继续 (迭代 {iteration})")
                    channel.send(" ")
                    time.sleep(0.5)
                    no_change_count = 0
                elif "----" in output and "More" in output:
                    logger.info(f"检测到分页提示，发送空格键继续 (迭代 {iteration})")
                    channel.send(" ")
                    time.sleep(0.5)
                    no_change_count = 0
                else:
                    # 检查是否命令执行完成
                    if "]" in output and command in output:
                        logger.info("命令执行完成")
                        break
                    elif current_length == last_output_length:
                        no_change_count += 1
                        if no_change_count > 5:  # 连续5次没有新输出
                            logger.info("连续无新输出，可能已完成")
                            break
                    else:
                        no_change_count = 0
                
                last_output_length = current_length
                time.sleep(0.5)
            
            # 发送quit命令退出系统视图
            logger.info("发送quit命令")
            channel.send("quit\n")
            time.sleep(2)
            
            # 读取最终输出
            while channel.recv_ready():
                chunk = channel.recv(1024).decode('utf-8')
                output += chunk
            
            channel.close()
            interactive_ssh.close()
            
            logger.info(f"交互式命令输出长度: {len(output)}")
            logger.info(f"输出内容前500字符: {output[:500]}")
            
            if not output.strip():
                return {"success": False, "message": "交互式命令执行成功但无输出"}
            
            # 检查是否包含配置内容
            if "current-configuration" not in output.lower() and "startup-configuration" not in output.lower():
                # 检查其他可能的配置标识
                if "version" not in output.lower() and "sysname" not in output.lower():
                    # 如果输出长度足够长，也认为是成功的
                    if len(output) > 1000:
                        logger.info(f"输出长度足够长 ({len(output)})，认为备份成功")
                    else:
                        logger.error(f"输出内容检查失败，输出长度: {len(output)}")
                        logger.error(f"输出内容: {output}")
                        return {"success": False, "message": "交互式命令执行成功但未获取到配置内容"}
            
            # 保存到文件
            file_path = BackupService._save_backup_file(device, backup_type, backup_id, output)
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "message": "备份成功",
                "file_path": file_path,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"交互式SSH备份失败: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return {"success": False, "message": f"交互式备份失败: {str(e)}"}
    

    
    @staticmethod
    def _clean_h3c_output(output: str) -> str:
        """清理H3C设备输出，移除分页提示和控制字符"""
        import re
        
        # 移除分页提示
        output = re.sub(r'---- More ----.*?\n', '\n', output)
        output = re.sub(r'----.*?More.*?----.*?\n', '\n', output)
        
        # 移除控制字符（如光标移动等）
        output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
        output = re.sub(r'\x1b\[[0-9]*D', '', output)
        
        # 移除ANSI转义序列
        output = re.sub(r'\x1b\[[0-9;]*[mK]', '', output)
        
        # 移除多余的空行
        output = re.sub(r'\n\s*\n\s*\n', '\n\n', output)
        
        # 移除行首的控制字符
        output = re.sub(r'^\s*\[[0-9]*D\s*', '', output, flags=re.MULTILINE)
        
        # 清理行尾的控制字符
        output = re.sub(r'\s*\[[0-9]*D\s*$', '', output, flags=re.MULTILINE)
        
        # 移除设备提示符
        output = re.sub(r'\[[^\]]+\]\s*$', '', output, flags=re.MULTILINE)
        
        # 移除行中的控制字符
        output = re.sub(r'^\s+', '', output, flags=re.MULTILINE)  # 移除行首空格
        output = re.sub(r'\s+$', '', output, flags=re.MULTILINE)  # 移除行尾空格
        
        # 移除空行
        output = re.sub(r'^\s*$\n', '', output, flags=re.MULTILINE)
        
        return output.strip()
    
    @staticmethod
    def _save_backup_file(device: Device, backup_type: str, backup_id: int, content: str) -> str:
        """保存备份文件"""
        # 确保备份目录存在
        backup_dir = f"./data/backups/{device.id}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_type}_{timestamp}_{backup_id}.txt"
        file_path = os.path.join(backup_dir, filename)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 设备: {device.name} ({device.ip_address})\n")
            f.write(f"# 备份类型: {backup_type}\n")
            f.write(f"# 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 备份ID: {backup_id}\n")
            f.write("-" * 50 + "\n")
            f.write(content)
        
        return file_path

class AutoBackupService:
    """自动备份服务"""
    
    @staticmethod
    def schedule_auto_backup():
        """调度自动备份任务"""
        import schedule
        import time
        
        # 从配置获取备份时间，默认为每天凌晨2点
        backup_time = ConfigManager.get_config('backup', 'auto_backup_time', '02:00')
        
        # 设置定时任务
        schedule.every().day.at(backup_time).do(AutoBackupService.perform_auto_backup)
        
        logger.info(f"自动备份已调度，执行时间: {backup_time}")
        
        # 启动调度器
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    @staticmethod
    def perform_auto_backup():
        """执行自动备份"""
        logger.info("开始执行自动备份...")
        
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 获取所有活跃设备
            devices = db.query(Device).filter(Device.connection_status == 'success').all()
            
            if not devices:
                logger.info("没有找到活跃设备，跳过自动备份")
                return
            
            backup_results = []
            
            for device in devices:
                try:
                    # 获取设备的备份策略
                    strategies = db.query(Strategy).filter(
                        Strategy.device_id == device.id,
                        Strategy.is_active == True
                    ).all()
                    
                    if not strategies:
                        logger.info(f"设备 {device.name} 没有活跃的备份策略")
                        continue
                    
                    # 执行备份
                    for strategy in strategies:
                        result = BackupService.create_backup(
                            db, device.id, strategy.backup_type, "auto"
                        )
                        
                        if result["success"]:
                            backup_results.append({
                                "device": device.name,
                                "type": strategy.backup_type,
                                "status": "success"
                            })
                            logger.info(f"设备 {device.name} 的 {strategy.backup_type} 备份成功")
                        else:
                            backup_results.append({
                                "device": device.name,
                                "type": strategy.backup_type,
                                "status": "failed",
                                "error": result["message"]
                            })
                            logger.error(f"设备 {device.name} 的 {strategy.backup_type} 备份失败: {result['message']}")
                
                except Exception as e:
                    logger.error(f"设备 {device.name} 自动备份异常: {str(e)}")
                    backup_results.append({
                        "device": device.name,
                        "type": "unknown",
                        "status": "failed",
                        "error": str(e)
                    })
            
            # 记录备份结果
            AutoBackupService._log_backup_results(backup_results)
            
            # 清理旧备份
            AutoBackupService._cleanup_old_backups()
            
            logger.info(f"自动备份完成，成功: {len([r for r in backup_results if r['status'] == 'success'])}，失败: {len([r for r in backup_results if r['status'] == 'failed'])}")
            
        except Exception as e:
            logger.error(f"自动备份执行失败: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def _log_backup_results(results: List[Dict]):
        """记录备份结果"""
        try:
            log_file = "logs/auto_backup.log"
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== 自动备份报告 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                for result in results:
                    f.write(f"设备: {result['device']}, 类型: {result['type']}, 状态: {result['status']}")
                    if result.get('error'):
                        f.write(f", 错误: {result['error']}")
                    f.write("\n")
                f.write("=" * 50 + "\n")
        except Exception as e:
            logger.error(f"记录备份结果失败: {str(e)}")
    
    @staticmethod
    def _cleanup_old_backups():
        """清理旧备份"""
        try:
            # 获取保留天数
            retention_days = ConfigManager.get_config('backup', 'backup_retention_days', 30)
            cutoff_date = datetime.now() - timedelta(days=int(retention_days))
            
            # 清理数据库中的旧备份记录
            db = next(get_db())
            old_backups = db.query(Backup).filter(Backup.created_at < cutoff_date).all()
            
            for backup in old_backups:
                # 删除备份文件
                if backup.file_path and os.path.exists(backup.file_path):
                    os.remove(backup.file_path)
                
                # 删除数据库记录
                db.delete(backup)
            
            db.commit()
            logger.info(f"清理了 {len(old_backups)} 个旧备份")
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {str(e)}")
        finally:
            db.close()
