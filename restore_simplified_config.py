#!/usr/bin/env python3
"""
恢复精简的系统配置数据 - 优化版本
"""

import sqlite3
import os
from datetime import datetime

def restore_simplified_config():
    """恢复精简的系统配置数据"""
    
    db_path = 'data/xconfkit.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 开始恢复精简系统配置...")
        
        # 清空现有配置
        cursor.execute("DELETE FROM configs")
        print("📝 已清空现有配置")
        
        # 1. 基础设置 (basic) - 只保留用户需要了解的配置
        print("📝 恢复基础设置...")
        
        basic_configs = [
            # 连接配置
            ('basic', 'connection_timeout', '30', '连接超时时间(秒)'),
            ('basic', 'command_timeout', '60', '命令执行超时时间(秒)'),
            
            # 备份存储配置
            ('basic', 'backup_path', '/data/backups', '备份文件存储路径'),
            ('basic', 'backup_retention_days', '30', '备份文件保留天数'),
            ('basic', 'backup_format', 'txt', '备份文件格式'),
            ('basic', 'enable_compression', 'true', '启用压缩'),
            ('basic', 'max_backup_size_mb', '100', '最大备份文件大小(MB)'),
            
            # 自动备份配置
            ('basic', 'enable_auto_backup', 'true', '启用自动备份'),
            ('basic', 'auto_backup_time', '02:00', '自动备份时间'),
            ('basic', 'auto_backup_retention_days', '30', '自动备份保留天数'),
        ]
        
        # 2. 高级设置 (advanced) - 只保留用户需要了解的配置
        print("🔧 恢复高级设置...")
        
        advanced_configs = [
            # 调度配置
            ('advanced', 'enable_scheduler', 'true', '启用定时备份'),
            ('advanced', 'check_interval_minutes', '5', '检查间隔(分钟)'),
            ('advanced', 'max_concurrent_jobs', '3', '最大并发任务数'),
            ('advanced', 'job_timeout_minutes', '30', '任务超时时间(分钟)'),
            
            # 日志配置
            ('advanced', 'log_level', 'INFO', '日志级别'),
            ('advanced', 'log_file_path', 'logs/xconfkit.log', '日志文件路径'),
            ('advanced', 'max_log_size_mb', '10', '最大日志文件大小(MB)'),
            ('advanced', 'log_retention_days', '7', '日志保留天数'),
            
            # 通知配置
            ('advanced', 'enable_webhook', 'false', '启用Webhook通知'),
            ('advanced', 'webhook_url', '', 'Webhook地址'),
            ('advanced', 'webhook_secret', '', 'Webhook密钥'),
            ('advanced', 'notify_on_schedule_backup', 'true', '仅通知定时备份结果'),
        ]
        
        # 合并所有配置
        all_configs = basic_configs + advanced_configs
        
        for category, key, value, description in all_configs:
            # 根据值的类型推断数据类型
            if isinstance(value, bool):
                data_type = 'boolean'
            elif isinstance(value, str):
                if value.lower() in ['true', 'false']:
                    data_type = 'boolean'
                elif value.isdigit():
                    data_type = 'int'
                elif value.replace('.', '').isdigit() and value.count('.') == 1:
                    data_type = 'float'
                else:
                    data_type = 'string'
            elif isinstance(value, int):
                data_type = 'int'
            elif isinstance(value, float):
                data_type = 'float'
            else:
                data_type = 'string'
            
            cursor.execute('''
                INSERT INTO configs (category, "key", value, data_type, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (category, key, value, data_type, description, datetime.now(), datetime.now()))
        
        # 3. 恢复AI配置
        print("🤖 恢复AI配置...")
        
        # 清空现有AI配置
        cursor.execute("DELETE FROM ai_configs")
        
        # 插入默认AI配置
        cursor.execute('''
            INSERT INTO ai_configs 
            (provider, api_key, model, base_url, timeout, enable_cache, enable_history, auto_retry, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('openai', '', 'gpt-4', 'https://api.openai.com/v1', 30, True, True, True, datetime.now(), datetime.now()))
        
        # 4. 恢复分析提示词
        print("📝 恢复分析提示词...")
        
        # 清空现有提示词
        cursor.execute("DELETE FROM analysis_prompts")
        
        # 插入默认提示词
        default_prompts = [
            ('security', '安全加固', '检查配置中的安全漏洞和加固建议', '''请从网络安全角度分析此网络设备配置，重点关注以下方面：

1. 访问控制列表(ACL)配置是否完整和合理
2. 用户认证和授权机制是否安全
3. 默认密码是否已修改
4. 日志记录和监控是否启用
5. 不必要的服务是否已关闭
6. 安全策略是否符合最佳实践

请按严重程度分类问题：严重、警告、建议、正常，并提供具体的改进建议。''', True),
            ('redundancy', '冗余高可用', '检查备份链路、设备冗余、负载均衡等', '''请分析此网络设备配置的冗余和高可用性，重点关注：

1. 链路备份和聚合配置
2. 生成树协议(STP/RSTP/MSTP)配置
3. 设备冗余和热备份
4. 负载均衡配置
5. 故障切换机制
6. 网络拓扑的容错能力

请评估当前配置的可用性水平，并提供改进建议。''', True),
            ('performance', '性能优化', '检查带宽利用、QoS配置、流量控制等', '''请分析此网络设备配置的性能优化空间，重点关注：

1. 带宽利用率和流量控制
2. QoS策略配置
3. 队列管理和优先级设置
4. 缓存和缓冲配置
5. 路由优化
6. 性能监控配置

请识别性能瓶颈并提供优化建议。''', True),
            ('integrity', '配置健全性', '检查语法、参数、配置完整性等', '''请检查此网络设备配置的健全性和正确性，重点关注：

1. 配置语法是否正确
2. 参数值是否合理
3. 配置是否完整
4. 是否存在冲突配置
5. 版本兼容性
6. 配置一致性

请列出发现的问题并提供修正建议。''', True),
            ('best_practices', '最佳实践', '检查行业标准、厂商建议、园区网规范等', '''请根据网络设备配置最佳实践分析此配置，重点关注：

1. 是否符合厂商推荐配置
2. 是否遵循行业标准
3. 园区网设计规范
4. 命名规范和文档化
5. 配置版本管理
6. 运维便利性

请评估配置的规范性并提供改进建议。''', True)
        ]
        
        for dimension, name, description, content, is_default in default_prompts:
            cursor.execute('''
                INSERT INTO analysis_prompts 
                (dimension, name, description, content, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (dimension, name, description, content, is_default, datetime.now(), datetime.now()))
        
        conn.commit()
        print("✅ 精简配置恢复完成！")
        
        # 统计信息
        cursor.execute("SELECT COUNT(*) FROM configs WHERE category = 'basic'")
        basic_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM configs WHERE category = 'advanced'")
        advanced_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ai_configs")
        ai_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM analysis_prompts")
        prompt_count = cursor.fetchone()[0]
        
        print(f"\n📊 配置统计:")
        print(f"   - 基础设置: {basic_count} 项")
        print(f"   - 高级设置: {advanced_count} 项")
        print(f"   - AI配置: {ai_count} 项")
        print(f"   - 分析提示词: {prompt_count} 项")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复数据时出错: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    restore_simplified_config()
