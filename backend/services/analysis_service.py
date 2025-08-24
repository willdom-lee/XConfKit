import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Device, Backup, AnalysisRecord, AnalysisPrompt, AIConfig
from .ai_service import ai_service_manager
from ..database import get_db
import aiohttp
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalysisService:
    """AI分析服务"""
    
    @staticmethod
    async def analyze_config(
        device_id: int, 
        backup_id: int, 
        dimensions: List[str] = None,  # 新增：支持维度选择
        ai_config: Dict = None,  # 新增：支持动态AI配置
        db: Session = None
    ) -> Dict:
        """分析配置"""
        should_close_db = False
        try:
            if db is None:
                from ..database import SessionLocal
                db = SessionLocal()
                should_close_db = True
            
            # 获取设备和备份信息
            device = db.query(Device).filter(Device.id == device_id).first()
            backup = db.query(Backup).filter(Backup.id == backup_id).first()
            
            if not device or not backup:
                return {"success": False, "message": "设备或备份不存在"}
            
            # 获取AI配置
            if ai_config is None:
                # 如果没有提供AI配置，从数据库获取
                db_ai_config = db.query(AIConfig).first()
                if not db_ai_config:
                    return {"success": False, "message": "AI配置不存在"}
                ai_config = {
                    "provider": db_ai_config.provider,
                    "api_key": db_ai_config.api_key,
                    "model": db_ai_config.model,
                    "base_url": db_ai_config.base_url,
                    "timeout": db_ai_config.timeout,
                    "enable_cache": db_ai_config.enable_cache
                }
            
            # 获取分析提示词
            prompts = db.query(AnalysisPrompt).all()
            prompt_dict = {p.dimension: p.content for p in prompts}
            
            # 如果没有指定维度，使用所有可用维度
            if not dimensions:
                dimensions = list(prompt_dict.keys())
            
            # 验证维度是否有效
            valid_dimensions = list(prompt_dict.keys())
            invalid_dimensions = [d for d in dimensions if d not in valid_dimensions]
            if invalid_dimensions:
                return {"success": False, "message": f"无效的分析维度: {invalid_dimensions}"}
            
            # 执行分析
            analysis_results = {}
            
            for dimension in dimensions:
                try:
                    prompt = prompt_dict.get(dimension)
                    if not prompt:
                        logger.warning(f"维度 {dimension} 没有对应的提示词")
                        continue
                    
                    # 构建分析提示
                    analysis_prompt = AnalysisService._build_analysis_prompt(
                        device, backup, prompt, dimension
                    )
                    
                    # 调用AI API
                    result = await AnalysisService._call_ai_api(
                        ai_config, analysis_prompt
                    )
                    
                    if result["success"]:
                        analysis_results[dimension] = result["content"]
                    else:
                        analysis_results[dimension] = f"分析失败: {result['error']}"
                        
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.error(f"维度 {dimension} AI API调用失败: {str(e)}")
                    analysis_results[dimension] = f"AI服务调用失败: {str(e)}"
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"维度 {dimension} 结果解析失败: {str(e)}")
                    analysis_results[dimension] = f"结果解析失败: {str(e)}"
                except Exception as e:
                    logger.error(f"维度 {dimension} 分析失败: {str(e)}")
                    analysis_results[dimension] = f"分析异常: {str(e)}"
            
            # 保存分析记录
            analysis_record = AnalysisRecord(
                device_id=device_id,
                backup_id=backup_id,
                dimensions=dimensions,  # 保存选中的维度
                result=json.dumps(analysis_results, ensure_ascii=False),
                created_at=datetime.now()
            )
            db.add(analysis_record)
            db.commit()
            
            return {
                "success": True,
                "message": "分析完成",
                "data": analysis_results,
                "record_id": analysis_record.id
            }
            
        except Exception as e:
            logger.error(f"配置分析失败: {str(e)}")
            return {"success": False, "message": f"分析失败: {str(e)}"}
        finally:
            if should_close_db and db:
                try:
                    db.close()
                except Exception as e:
                    logger.error(f"关闭数据库会话失败: {str(e)}")
    
    @staticmethod
    def _build_analysis_prompt(device: Device, backup: Backup, base_prompt: str, dimension: str) -> str:
        """构建分析提示"""
        prompt = f"""
设备信息:
- 名称: {device.name}
- IP地址: {device.ip_address}
- 协议: {device.protocol}

备份信息:
- 类型: {backup.backup_type}
- 创建时间: {backup.created_at}
- 文件大小: {backup.file_size} bytes

配置内容:
{backup.content}

分析要求:
{base_prompt}

请针对{device.name}的{backup.backup_type}配置，从{dimension}维度进行分析，提供详细的分析报告和改进建议。
"""
        return prompt.strip()
    
    @staticmethod
    async def _call_ai_api(ai_config: Dict, prompt: str) -> Dict:
        """调用AI API"""
        try:
            headers = {
                "Authorization": f"Bearer {ai_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": ai_config['model'],
                "messages": [
                    {"role": "system", "content": "你是一个专业的网络设备配置分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ai_config['base_url']}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=ai_config['timeout'])
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        return {"success": True, "content": content}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"API调用失败: {response.status} - {error_text}"}
                        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_analysis_history(db: Session = None) -> List[Dict]:
        """获取分析历史"""
        try:
            if db is None:
                db = next(get_db())
            
            from ..models import Device, Backup
            
            # 使用join查询获取设备和备份信息
            records = db.query(
                AnalysisRecord,
                Device.name.label('device_name'),
                Device.ip_address.label('device_ip'),
                Backup.backup_type.label('backup_type'),
                Backup.created_at.label('backup_created_at')
            ).join(
                Device, AnalysisRecord.device_id == Device.id
            ).join(
                Backup, AnalysisRecord.backup_id == Backup.id
            ).order_by(AnalysisRecord.created_at.desc()).limit(50).all()
            
            return [
                {
                    "id": record.AnalysisRecord.id,
                    "device_id": record.AnalysisRecord.device_id,
                    "backup_id": record.AnalysisRecord.backup_id,
                    "device_name": record.device_name,
                    "device_ip": record.device_ip,
                    "backup_type": record.backup_type,
                    "backup_created_at": record.backup_created_at.isoformat() if record.backup_created_at else None,
                    "dimensions": record.AnalysisRecord.dimensions,  # 返回选中的维度
                    "result": json.loads(record.AnalysisRecord.result) if record.AnalysisRecord.result else {},
                    "created_at": record.AnalysisRecord.created_at.isoformat() if record.AnalysisRecord.created_at else None
                }
                for record in records
            ]
            
        except Exception as e:
            logger.error(f"获取分析历史失败: {str(e)}")
            return []
    
    @staticmethod
    def get_analysis_result(record_id: int, db: Session = None) -> Dict:
        """获取分析结果"""
        try:
            if db is None:
                db = next(get_db())
            
            record = db.query(AnalysisRecord).filter(AnalysisRecord.id == record_id).first()
            
            if not record:
                return {"success": False, "message": "分析记录不存在"}
            
            return {
                "success": True,
                "data": {
                    "id": record.id,
                    "device_id": record.device_id,
                    "backup_id": record.backup_id,
                    "dimensions": record.dimensions,
                    "result": json.loads(record.result) if record.result else {},
                    "created_at": record.created_at.isoformat() if record.created_at else None
                }
            }
            
        except Exception as e:
            logger.error(f"获取分析结果失败: {str(e)}")
            return {"success": False, "message": f"获取分析结果失败: {str(e)}"}
    
    @staticmethod
    def initialize_default_prompts(db: Session = None) -> bool:
        """初始化默认提示词"""
        try:
            if db is None:
                db = next(get_db())
            
            from datetime import datetime
            
            default_prompts = {
                'security': {
                    'name': '安全加固',
                    'description': '检查访问控制、认证授权、安全策略等',
                    'content': '''请简要分析此网络设备配置的安全性，重点关注：

1. 访问控制列表(ACL)配置
2. 用户认证和授权机制
3. 默认密码是否已修改
4. 日志记录和监控
5. 不必要的服务

请按严重程度分类（严重/警告/建议），并提供关键改进建议。分析结果控制在300字以内。''',
                    'is_default': True
                },
                'redundancy': {
                    'name': '冗余高可用',
                    'description': '检查备份链路、设备冗余、负载均衡等',
                    'content': '''请简要分析此网络设备配置的冗余和高可用性，重点关注：

1. 链路备份和聚合配置
2. 生成树协议(STP/RSTP/MSTP)配置
3. 设备冗余和热备份
4. 负载均衡配置

请评估可用性水平并提供关键改进建议。分析结果控制在300字以内。''',
                    'is_default': True
                },
                'performance': {
                    'name': '性能优化',
                    'description': '检查带宽利用、QoS配置、流量控制等',
                    'content': '''请简要分析此网络设备配置的性能优化空间，重点关注：

1. 带宽利用率和流量控制
2. QoS策略配置
3. 队列管理和优先级设置
4. 路由优化

请识别主要性能瓶颈并提供关键优化建议。分析结果控制在300字以内。''',
                    'is_default': True
                },
                'integrity': {
                    'name': '配置健全性',
                    'description': '检查语法、参数、配置完整性等',
                    'content': '''请简要检查此网络设备配置的健全性，重点关注：

1. 配置语法是否正确
2. 参数值是否合理
3. 配置是否完整
4. 是否存在冲突配置

请列出主要问题并提供修正建议。分析结果控制在300字以内。''',
                    'is_default': True
                },
                'best_practices': {
                    'name': '最佳实践',
                    'description': '检查行业标准、厂商建议、园区网规范等',
                    'content': '''请根据最佳实践简要分析此配置，重点关注：

1. 是否符合厂商推荐配置
2. 是否遵循行业标准
3. 园区网设计规范
4. 命名规范和文档化

请评估规范性并提供关键改进建议。分析结果控制在300字以内。''',
                    'is_default': True
                }
            }
            
            for dimension, prompt_data in default_prompts.items():
                prompt = db.query(AnalysisPrompt).filter_by(dimension=dimension).first()
                if not prompt:
                    prompt = AnalysisPrompt(
                        dimension=dimension,
                        name=prompt_data['name'],
                        description=prompt_data['description'],
                        content=prompt_data['content'],
                        is_default=prompt_data['is_default'],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(prompt)
                else:
                    # 更新现有提示词
                    prompt.name = prompt_data['name']
                    prompt.description = prompt_data['description']
                    prompt.content = prompt_data['content']
                    prompt.is_default = prompt_data['is_default']
                    prompt.updated_at = datetime.now()
            
            db.commit()
            logger.info("默认提示词初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化默认提示词失败: {str(e)}")
            if db:
                db.rollback()
            return False
