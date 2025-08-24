#!/usr/bin/env python3
"""
防止数据丢失的自动化脚本
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def check_database_integrity():
    """检查数据库完整性"""
    try:
        import sqlite3
        conn = sqlite3.connect('data/xconfkit.db')
        cursor = conn.cursor()
        
        # 检查关键表是否存在
        required_tables = ['devices', 'backups', 'strategies', 'configs', 'ai_configs', 'analysis_prompts']
        missing_tables = []
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ 缺少关键表: {missing_tables}")
            return False
        
        # 检查数据量
        data_counts = {}
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            data_counts[table] = count
        
        print("✅ 数据库完整性检查通过")
        print(f"📊 数据统计: {data_counts}")
        
        # 如果关键数据丢失，触发恢复
        if data_counts['devices'] == 0 and data_counts['backups'] > 0:
            print("⚠️  检测到设备数据丢失，但备份数据存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库完整性检查失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def auto_backup_before_restart():
    """重启前自动备份"""
    print("🔄 执行重启前自动备份...")
    
    # 创建备份目录
    backup_dir = f"data/auto_backups/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 备份数据库
    if os.path.exists('data/xconfkit.db'):
        import shutil
        shutil.copy2('data/xconfkit.db', f"{backup_dir}/xconfkit.db")
        print(f"✅ 数据库已备份到: {backup_dir}/xconfkit.db")
    
    # 备份配置文件
    if os.path.exists('data/backups'):
        shutil.copytree('data/backups', f"{backup_dir}/backups", dirs_exist_ok=True)
        print(f"✅ 备份文件已复制到: {backup_dir}/backups")
    
    return backup_dir

def restore_from_latest_backup():
    """从最新备份恢复"""
    print("🔄 尝试从最新备份恢复...")
    
    backup_base = "data/auto_backups"
    if not os.path.exists(backup_base):
        print("❌ 没有找到自动备份目录")
        return False
    
    # 找到最新的备份
    backups = [d for d in os.listdir(backup_base) if os.path.isdir(f"{backup_base}/{d}")]
    if not backups:
        print("❌ 没有找到自动备份")
        return False
    
    latest_backup = sorted(backups)[-1]
    backup_path = f"{backup_base}/{latest_backup}"
    
    print(f"📦 使用最新备份: {latest_backup}")
    
    # 恢复数据库
    backup_db = f"{backup_path}/xconfkit.db"
    if os.path.exists(backup_db):
        import shutil
        shutil.copy2(backup_db, 'data/xconfkit.db')
        print("✅ 数据库已恢复")
    
    # 恢复备份文件
    backup_files = f"{backup_path}/backups"
    if os.path.exists(backup_files):
        if os.path.exists('data/backups'):
            shutil.rmtree('data/backups')
        shutil.copytree(backup_files, 'data/backups')
        print("✅ 备份文件已恢复")
    
    return True

def safe_restart_services():
    """安全重启服务"""
    print("🔄 执行安全重启...")
    
    # 1. 检查数据库完整性
    if not check_database_integrity():
        print("⚠️  数据库完整性检查失败，尝试恢复...")
        if not restore_from_latest_backup():
            print("❌ 恢复失败，创建新备份")
            auto_backup_before_restart()
    
    # 2. 创建当前状态备份
    backup_dir = auto_backup_before_restart()
    
    # 3. 停止服务
    print("🛑 停止服务...")
    try:
        subprocess.run(['./stop_services.sh'], check=True, capture_output=True, text=True)
        time.sleep(2)  # 等待服务完全停止
    except subprocess.CalledProcessError as e:
        print(f"⚠️  停止服务时出错: {e}")
    
    # 4. 启动服务
    print("🚀 启动服务...")
    try:
        subprocess.run(['./start_services.sh'], check=True, capture_output=True, text=True)
        time.sleep(5)  # 等待服务启动
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动服务失败: {e}")
        return False
    
    # 5. 验证服务状态
    print("🔍 验证服务状态...")
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            print("✅ 后端服务正常")
        else:
            print("❌ 后端服务异常")
            return False
    except Exception as e:
        print(f"❌ 服务验证失败: {e}")
        return False
    
    print("✅ 安全重启完成")
    return True

def monitor_data_integrity():
    """监控数据完整性"""
    print("🔍 开始数据完整性监控...")
    
    while True:
        try:
            if not check_database_integrity():
                print("⚠️  检测到数据异常，尝试恢复...")
                restore_from_latest_backup()
            
            # 每5分钟检查一次
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n🛑 监控已停止")
            break
        except Exception as e:
            print(f"❌ 监控过程中出错: {e}")
            time.sleep(60)  # 出错后等待1分钟再继续

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("📋 使用方法:")
        print("  python prevent_data_loss.py check      # 检查数据完整性")
        print("  python prevent_data_loss.py backup     # 创建备份")
        print("  python prevent_data_loss.py restore    # 从备份恢复")
        print("  python prevent_data_loss.py restart    # 安全重启服务")
        print("  python prevent_data_loss.py monitor    # 监控数据完整性")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        check_database_integrity()
    elif command == "backup":
        auto_backup_before_restart()
    elif command == "restore":
        restore_from_latest_backup()
    elif command == "restart":
        safe_restart_services()
    elif command == "monitor":
        monitor_data_integrity()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()
