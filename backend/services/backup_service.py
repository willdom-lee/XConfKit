from sqlalchemy.orm import Session
from ..models import Device, Backup
from ..schemas import BackupCreate
import paramiko
import os
from datetime import datetime
from typing import Optional
import logging

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
    def execute_backup(db: Session, device_id: int, backup_type: str = "running-config") -> dict:
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
            else:
                db_backup.status = "failed"
                db_backup.error_message = result["message"]
            
            db.commit()
            
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
                port=device.port,
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
        except:
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
                port=device.port or 22,
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
                port=device.port or 22,
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
                port=device.port or 22,
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
                port=device.port or 22,
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
                port=device.port or 22,
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
                stdin, stdout, stderr = ssh.exec_command(h3c_command, timeout=120)
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
            
            # 连接设备
            ssh.connect(
                device.ip_address,
                port=device.port or 22,
                username=device.username,
                password=device.password,
                timeout=30,
                banner_timeout=60,
                allow_agent=False,
                look_for_keys=False
            )
            
            # 创建交互式会话
            channel = ssh.invoke_shell()
            channel.settimeout(30)
            
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
                port=device.port or 22,
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
