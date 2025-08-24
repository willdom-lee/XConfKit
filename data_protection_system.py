#!/usr/bin/env python3
"""
数据保护系统 - 防止数据丢失和异常重构
"""

import sqlite3
import os
import shutil
import json
from datetime import datetime
import hashlib
from pathlib import Path

class DataProtectionSystem:
    def __init__(self, db_path="data/xconfkit.db"):
        self.db_path = db_path
        self.backup_dir = "data/backups"
        self.protection_dir = "data/protection"
        self.metadata_file = f"{self.protection_dir}/metadata.json"
        
        # 确保保护目录存在
        os.makedirs(self.protection_dir, exist_ok=True)
    
    def create_data_snapshot(self, snapshot_name=None):
        """创建数据快照"""
        if not os.path.exists(self.db_path):
            print(f"❌ 数据库文件不存在: {self.db_path}")
            return False
        
        if snapshot_name is None:
            snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot_dir = f"{self.protection_dir}/{snapshot_name}"
        os.makedirs(snapshot_dir, exist_ok=True)
        
        try:
            # 1. 复制数据库文件
            snapshot_db = f"{snapshot_dir}/xconfkit.db"
            shutil.copy2(self.db_path, snapshot_db)
            
            # 2. 创建数据摘要
            data_summary = self._get_data_summary()
            
            # 3. 保存元数据
            metadata = {
                "snapshot_name": snapshot_name,
                "created_at": datetime.now().isoformat(),
                "data_summary": data_summary,
                "file_size": os.path.getsize(self.db_path),
                "file_hash": self._calculate_file_hash(self.db_path)
            }
            
            with open(f"{snapshot_dir}/metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 4. 更新主元数据文件
            self._update_main_metadata(snapshot_name, metadata)
            
            print(f"✅ 数据快照创建成功: {snapshot_name}")
            print(f"   📊 数据摘要: {data_summary}")
            return True
            
        except Exception as e:
            print(f"❌ 创建数据快照失败: {e}")
            return False
    
    def restore_from_snapshot(self, snapshot_name):
        """从快照恢复数据"""
        snapshot_dir = f"{self.protection_dir}/{snapshot_name}"
        snapshot_db = f"{snapshot_dir}/xconfkit.db"
        
        if not os.path.exists(snapshot_db):
            print(f"❌ 快照不存在: {snapshot_name}")
            return False
        
        try:
            # 1. 创建当前数据的备份
            current_backup = f"data/xconfkit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, current_backup)
                print(f"📦 当前数据已备份到: {current_backup}")
            
            # 2. 恢复快照数据
            shutil.copy2(snapshot_db, self.db_path)
            
            # 3. 验证恢复结果
            restored_summary = self._get_data_summary()
            with open(f"{snapshot_dir}/metadata.json", 'r', encoding='utf-8') as f:
                original_metadata = json.load(f)
            
            if restored_summary == original_metadata["data_summary"]:
                print(f"✅ 数据恢复成功: {snapshot_name}")
                print(f"   📊 恢复的数据: {restored_summary}")
                return True
            else:
                print(f"❌ 数据恢复验证失败")
                return False
                
        except Exception as e:
            print(f"❌ 恢复数据失败: {e}")
            return False
    
    def list_snapshots(self):
        """列出所有快照"""
        if not os.path.exists(self.protection_dir):
            print("📁 没有找到保护目录")
            return []
        
        snapshots = []
        for item in os.listdir(self.protection_dir):
            item_path = f"{self.protection_dir}/{item}"
            if os.path.isdir(item_path) and os.path.exists(f"{item_path}/metadata.json"):
                try:
                    with open(f"{item_path}/metadata.json", 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    snapshots.append(metadata)
                except:
                    continue
        
        return sorted(snapshots, key=lambda x: x["created_at"], reverse=True)
    
    def validate_data_integrity(self):
        """验证数据完整性"""
        if not os.path.exists(self.db_path):
            print("❌ 数据库文件不存在")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
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
            
            # 检查数据完整性
            data_summary = self._get_data_summary()
            print(f"✅ 数据完整性检查通过")
            print(f"   📊 当前数据: {data_summary}")
            return True
            
        except Exception as e:
            print(f"❌ 数据完整性检查失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def auto_backup_before_changes(self):
        """在变更前自动备份"""
        print("🔄 执行变更前自动备份...")
        return self.create_data_snapshot("auto_backup_before_changes")
    
    def _get_data_summary(self):
        """获取数据摘要"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            summary = {}
            tables = ['devices', 'backups', 'strategies', 'configs', 'ai_configs', 'analysis_prompts']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                summary[table] = count
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()
    
    def _calculate_file_hash(self, file_path):
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _update_main_metadata(self, snapshot_name, metadata):
        """更新主元数据文件"""
        main_metadata = {}
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    main_metadata = json.load(f)
            except:
                pass
        
        if "snapshots" not in main_metadata:
            main_metadata["snapshots"] = []
        
        # 添加新快照
        main_metadata["snapshots"].append({
            "name": snapshot_name,
            "created_at": metadata["created_at"],
            "data_summary": metadata["data_summary"]
        })
        
        # 保持最多10个快照
        if len(main_metadata["snapshots"]) > 10:
            main_metadata["snapshots"] = main_metadata["snapshots"][-10:]
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(main_metadata, f, indent=2, ensure_ascii=False)

def main():
    """主函数 - 演示数据保护系统"""
    dps = DataProtectionSystem()
    
    print("🛡️  XConfKit 数据保护系统")
    print("=" * 50)
    
    # 1. 验证数据完整性
    print("\n1. 验证数据完整性:")
    dps.validate_data_integrity()
    
    # 2. 创建当前数据快照
    print("\n2. 创建数据快照:")
    dps.create_data_snapshot("current_state")
    
    # 3. 列出所有快照
    print("\n3. 列出所有快照:")
    snapshots = dps.list_snapshots()
    for snapshot in snapshots:
        print(f"   📸 {snapshot['snapshot_name']} - {snapshot['created_at']}")
        print(f"      📊 {snapshot['data_summary']}")
    
    print("\n✅ 数据保护系统初始化完成！")
    print("\n📋 使用说明:")
    print("- 在重要操作前调用 auto_backup_before_changes()")
    print("- 定期创建数据快照")
    print("- 使用 restore_from_snapshot() 恢复数据")

if __name__ == "__main__":
    main()
