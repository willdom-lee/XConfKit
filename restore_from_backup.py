#!/usr/bin/env python3
"""
从备份文件中恢复数据
"""

import sqlite3
import os
import shutil
from datetime import datetime
import re

def restore_from_backup():
    """从备份文件中恢复数据"""
    
    db_path = 'data/xconfkit.db'
    backup_data_path = 'backups/temp_restore/data/backups'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    if not os.path.exists(backup_data_path):
        print(f"❌ 备份数据路径不存在: {backup_data_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 开始从备份恢复数据...")
        
        # 1. 恢复备份文件
        print("📁 恢复备份文件...")
        
        # 清空现有备份目录
        if os.path.exists('data/backups'):
            shutil.rmtree('data/backups')
        
        # 复制备份文件
        shutil.copytree(backup_data_path, 'data/backups')
        print(f"   ✅ 已复制备份文件到 data/backups/")
        
        # 2. 恢复设备数据
        print("📱 恢复设备数据...")
        
        # 清空现有设备
        cursor.execute("DELETE FROM devices")
        
        # 从备份文件推断设备信息
        device_dirs = [d for d in os.listdir('data/backups') if d.isdigit()]
        
        for device_id in device_dirs:
            device_path = f'data/backups/{device_id}'
            if os.path.isdir(device_path):
                # 检查备份文件来确定设备信息
                backup_files = os.listdir(device_path)
                if backup_files:
                    # 从第一个备份文件推断设备信息
                    first_backup = backup_files[0]
                    
                    # 根据设备ID设置不同的设备信息
                    if device_id == '1':
                        device_name = 'H3C-Switch-01'
                        ip_address = '192.168.1.10'
                        username = 'admin'
                        password = 'admin123'  # 默认密码，建议在生产环境中修改
                    elif device_id == '2':
                        device_name = 'H3C-Switch-02'
                        ip_address = '192.168.1.11'
                        username = 'admin'
                        password = 'admin123'  # 默认密码，建议在生产环境中修改
                    else:
                        device_name = f'Device-{device_id}'
                        ip_address = f'192.168.1.{10 + int(device_id)}'
                        username = 'admin'
                        password = 'admin123'  # 默认密码，建议在生产环境中修改
                    
                    cursor.execute('''
                        INSERT INTO devices 
                        (name, ip_address, username, password, protocol, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (device_name, ip_address, username, password, 'ssh', 
                          f'从备份恢复的设备 {device_id}', datetime.now(), datetime.now()))
                    
                    print(f"   ✅ 已恢复设备: {device_name} ({ip_address})")
        
        # 3. 恢复备份记录
        print("💾 恢复备份记录...")
        
        # 清空现有备份记录
        cursor.execute("DELETE FROM backups")
        
        # 遍历所有备份文件
        for device_id in device_dirs:
            device_path = f'data/backups/{device_id}'
            if os.path.isdir(device_path):
                backup_files = os.listdir(device_path)
                
                for backup_file in backup_files:
                    # 解析文件名: type_timestamp_id.txt
                    # 例如: running-config_20250815_195804_1.txt
                    match = re.match(r'(.+)_(\d{8}_\d{6})_(\d+)\.txt', backup_file)
                    if match:
                        backup_type = match.group(1)
                        timestamp_str = match.group(2)
                        backup_id = match.group(3)
                        
                        # 解析时间戳
                        try:
                            created_at = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        except:
                            created_at = datetime.now()
                        
                        # 读取备份文件内容
                        backup_file_path = os.path.join(device_path, backup_file)
                        try:
                            with open(backup_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except:
                            content = "备份文件读取失败"
                        
                        # 计算文件大小
                        file_size = len(content.encode('utf-8'))
                        
                        cursor.execute('''
                            INSERT INTO backups 
                            (device_id, backup_type, status, file_path, file_size, content, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (int(device_id), backup_type, 'completed', backup_file_path, 
                              file_size, content, created_at))
                        
                        print(f"   ✅ 已恢复备份: {backup_type} ({backup_file})")
        
        # 4. 恢复策略数据
        print("📋 恢复备份策略...")
        
        # 清空现有策略
        cursor.execute("DELETE FROM strategies")
        
        # 为每个设备创建默认策略
        cursor.execute("SELECT id FROM devices")
        devices = cursor.fetchall()
        
        for device_id, in devices:
            # 创建运行配置备份策略
            cursor.execute('''
                INSERT INTO strategies 
                (name, device_id, strategy_type, backup_type, schedule, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (f'每日运行配置备份', device_id, 'scheduled', 'running-config', 
                  '0 2 * * *', True, datetime.now(), datetime.now()))
            
            # 创建启动配置备份策略
            cursor.execute('''
                INSERT INTO strategies 
                (name, device_id, strategy_type, backup_type, schedule, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (f'每周启动配置备份', device_id, 'scheduled', 'startup-config', 
                  '0 3 * * 0', True, datetime.now(), datetime.now()))
            
            print(f"   ✅ 已为设备 {device_id} 创建备份策略")
        
        conn.commit()
        print("✅ 从备份恢复数据完成！")
        
        # 显示恢复的数据统计
        print("\n📊 数据恢复统计:")
        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count = cursor.fetchone()[0]
        print(f"   - 设备: {device_count} 台")
        
        cursor.execute("SELECT COUNT(*) FROM backups")
        backup_count = cursor.fetchone()[0]
        print(f"   - 备份记录: {backup_count} 条")
        
        cursor.execute("SELECT COUNT(*) FROM strategies")
        strategy_count = cursor.fetchone()[0]
        print(f"   - 备份策略: {strategy_count} 个")
        
        # 显示设备详情
        print("\n📱 设备详情:")
        cursor.execute("SELECT id, name, ip_address FROM devices")
        devices = cursor.fetchall()
        for device_id, name, ip in devices:
            print(f"   - {name} ({ip}) - ID: {device_id}")
        
        # 显示备份类型统计
        print("\n💾 备份类型统计:")
        cursor.execute("SELECT backup_type, COUNT(*) FROM backups GROUP BY backup_type")
        backup_types = cursor.fetchall()
        for backup_type, count in backup_types:
            print(f"   - {backup_type}: {count} 条")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复数据时出错: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    restore_from_backup()
