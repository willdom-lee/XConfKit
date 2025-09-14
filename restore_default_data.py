#!/usr/bin/env python3
"""
恢复默认系统配置数据
"""

import sqlite3
import os
from datetime import datetime

def restore_default_data():
    """恢复默认的系统配置数据"""
    
    db_path = 'data/xconfkit.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 开始恢复默认系统配置...")
        
        # 1. 恢复系统配置
        print("📝 恢复系统配置...")
        
        # 备份配置
        backup_configs = [
            ('backup', 'backup_path', '/data/backups', '备份文件存储路径'),
            ('backup', 'backup_retention_days', '30', '备份文件保留天数'),
            ('backup', 'backup_format', 'txt', '备份文件格式'),
            ('backup', 'enable_compression', 'true', '启用压缩'),
            ('backup', 'max_backup_size_mb', '100', '最大备份文件大小(MB)'),
            
            # 设备配置
            ('device', 'default_username', 'admin', '默认用户名'),
            ('device', 'default_timeout', '30', '默认连接超时时间(秒)'),
            ('device', 'max_connections', '10', '最大并发连接数'),
            ('device', 'enable_ssh_key_auth', 'false', '启用SSH密钥认证'),
            ('device', 'ssh_key_path', '~/.ssh/id_rsa', 'SSH密钥路径'),
            
            # 调度配置
            ('scheduler', 'enable_scheduler', 'true', '启用调度器'),
            ('scheduler', 'check_interval_minutes', '5', '检查间隔(分钟)'),
            ('scheduler', 'max_concurrent_jobs', '3', '最大并发任务数'),
            ('scheduler', 'job_timeout_minutes', '30', '任务超时时间(分钟)'),
            ('scheduler', 'enable_notifications', 'true', '启用通知'),
            
            # 日志配置
            ('logging', 'log_level', 'INFO', '日志级别'),
            ('logging', 'log_file_path', 'logs/xconfkit.log', '日志文件路径'),
            ('logging', 'max_log_size_mb', '10', '最大日志文件大小(MB)'),
            ('logging', 'log_retention_days', '7', '日志保留天数'),
            ('logging', 'enable_console_log', 'true', '启用控制台日志'),
            
            # 网络配置
            ('network', 'default_port', '22', '默认SSH端口'),
            ('network', 'connection_timeout', '30', '连接超时时间(秒)'),
            ('network', 'command_timeout', '60', '命令执行超时时间(秒)'),
            ('network', 'enable_proxy', 'false', '启用代理'),
            ('network', 'proxy_host', '', '代理服务器地址'),
            ('network', 'proxy_port', '8080', '代理服务器端口'),
            
            # 安全配置
            ('security', 'enable_encryption', 'true', '启用加密'),
            ('security', 'encryption_algorithm', 'AES-256', '加密算法'),
            ('security', 'enable_audit_log', 'true', '启用审计日志'),
            ('security', 'max_login_attempts', '3', '最大登录尝试次数'),
            ('security', 'session_timeout_minutes', '30', '会话超时时间(分钟)'),
            
            # 通知配置
            ('notification', 'enable_email', 'false', '启用邮件通知'),
            ('notification', 'smtp_server', 'smtp.gmail.com', 'SMTP服务器'),
            ('notification', 'smtp_port', '587', 'SMTP端口'),
            ('notification', 'email_username', '', '邮箱用户名'),
            ('notification', 'email_password', '', '邮箱密码'),
            ('notification', 'notification_recipients', '', '通知接收邮箱'),
            
            # 性能配置
            ('performance', 'enable_cache', 'true', '启用缓存'),
            ('performance', 'cache_size_mb', '50', '缓存大小(MB)'),
            ('performance', 'cache_ttl_hours', '24', '缓存过期时间(小时)'),
            ('performance', 'enable_connection_pool', 'true', '启用连接池'),
            ('performance', 'pool_size', '5', '连接池大小'),
        ]
        
        for category, key, value, description in backup_configs:
            # 根据值的类型推断数据类型
            if isinstance(value, bool) or value.lower() in ['true', 'false']:
                data_type = 'boolean'
            elif value.isdigit():
                data_type = 'int'
            elif value.replace('.', '').isdigit() and value.count('.') == 1:
                data_type = 'float'
            else:
                data_type = 'string'
            
            cursor.execute('''
                INSERT OR REPLACE INTO configs (category, "key", value, data_type, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (category, key, value, data_type, description, datetime.now(), datetime.now()))
        
        # 2. 恢复AI配置
        print("🤖 恢复AI配置...")
        
        # 检查ai_configs表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_configs'")
        if cursor.fetchone():
            cursor.execute('''
                INSERT OR REPLACE INTO ai_configs 
                (provider, api_key, model, base_url, timeout, enable_cache, enable_history, auto_retry, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('openai', 'your-api-key-here', 'gpt-4', 'https://api.openai.com/v1', 30, True, True, True, datetime.now(), datetime.now()))
        
        # 3. 恢复分析提示词
        print("📝 恢复分析提示词...")
        
        # 检查analysis_prompts表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_prompts'")
        if cursor.fetchone():
            default_prompts = [
                ('security', '安全加固', '检查访问控制、认证授权、安全策略等', 
                 '请从网络安全角度分析此网络设备配置，重点关注访问控制列表(ACL)配置是否完整和合理。'),
                ('redundancy', '冗余高可用', '检查备份链路、设备冗余、负载均衡等',
                 '请分析此网络设备配置的冗余和高可用性，重点关注：\n\n1. 链路备份和聚合配置\n2. 生成树协议(STP/RSTP/MSTP)配置\n3. 设备冗余和热备份\n4. 负载均衡配置\n5. 故障切换机制\n6. 网络拓扑的容错能力\n\n请评估当前配置的可用性水平，并提供改进建议。'),
                ('performance', '性能优化', '检查带宽利用、QoS配置、流量控制等',
                 '请分析此网络设备配置的性能优化空间，重点关注：\n\n1. 带宽利用率和流量控制\n2. QoS策略配置\n3. 队列管理和优先级设置\n4. 缓存和缓冲配置\n5. 路由优化\n6. 性能监控配置\n\n请识别性能瓶颈并提供优化建议。'),
                ('integrity', '配置健全性', '检查语法、参数、配置完整性等',
                 '请检查此网络设备配置的健全性和正确性，重点关注：\n\n1. 配置语法是否正确\n2. 参数值是否合理\n3. 配置是否完整\n4. 是否存在冲突配置\n5. 版本兼容性\n6. 配置一致性\n\n请列出发现的问题并提供修正建议。'),
                ('best_practice', '最佳实践', '检查行业标准、厂商建议、园区网规范等',
                 '请根据网络设备配置最佳实践分析此配置，重点关注：\n\n1. 是否符合厂商推荐配置\n2. 是否遵循行业标准\n3. 园区网设计规范\n4. 命名规范和文档化\n5. 配置版本管理\n6. 运维便利性\n\n请评估配置的规范性并提供改进建议。')
            ]
            
            for dimension, name, description, content in default_prompts:
                cursor.execute('''
                    INSERT OR REPLACE INTO analysis_prompts 
                    (dimension, name, description, content, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (dimension, name, description, content, True, datetime.now(), datetime.now()))
        
        # 4. 添加示例设备（可选）
        print("📱 添加示例设备...")
        
        # 检查devices表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices'")
        if cursor.fetchone():
            # 检查是否已有设备
            cursor.execute("SELECT COUNT(*) FROM devices")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO devices 
                    (name, ip_address, username, password, protocol, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', ('示例设备', '192.168.1.1', 'admin', 'CHANGE_ME', 'ssh', '这是一个示例设备，请根据实际情况修改', datetime.now(), datetime.now()))
        
        # 5. 添加示例备份策略（可选）
        print("📋 添加示例备份策略...")
        
        # 检查strategies表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
        if cursor.fetchone():
            # 检查是否已有策略
            cursor.execute("SELECT COUNT(*) FROM strategies")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO strategies 
                    (name, strategy_type, backup_type, schedule, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', ('每日备份', 'scheduled', 'running-config', '0 2 * * *', True, datetime.now(), datetime.now()))
        
        conn.commit()
        print("✅ 默认数据恢复完成！")
        
        # 显示恢复的数据统计
        print("\n📊 数据恢复统计:")
        cursor.execute("SELECT COUNT(*) FROM configs")
        config_count = cursor.fetchone()[0]
        print(f"   - 系统配置: {config_count} 项")
        
        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count = cursor.fetchone()[0]
        print(f"   - 设备: {device_count} 台")
        
        cursor.execute("SELECT COUNT(*) FROM strategies")
        strategy_count = cursor.fetchone()[0]
        print(f"   - 备份策略: {strategy_count} 个")
        
        cursor.execute("SELECT COUNT(*) FROM ai_configs")
        ai_config_count = cursor.fetchone()[0]
        print(f"   - AI配置: {ai_config_count} 项")
        
        cursor.execute("SELECT COUNT(*) FROM analysis_prompts")
        prompt_count = cursor.fetchone()[0]
        print(f"   - 分析提示词: {prompt_count} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复数据时出错: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    restore_default_data()
