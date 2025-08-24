import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AIService:
    """AI服务基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get('provider', 'alibaba')
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'qwen-turbo')
        self.base_url = config.get('base_url')
        self.timeout = config.get('timeout', 30)
        
    async def analyze_config(self, config_content: str, prompt: str) -> Dict[str, Any]:
        """分析配置内容"""
        raise NotImplementedError
        
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        raise NotImplementedError

class AlibabaService(AIService):
    """阿里云通义千问服务"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = self.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
    async def analyze_config(self, config_content: str, prompt: str) -> Dict[str, Any]:
        """使用阿里云通义千问分析配置"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的网络设备配置分析专家。请提供简洁、重点突出的分析报告，控制在500字以内。"
                        },
                        {
                            "role": "user",
                            "content": f"{prompt}\n\n配置内容：\n{config_content}"
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "content": result["choices"][0]["message"]["content"],
                            "usage": result.get("usage", {})
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"API调用失败: {response.status} - {error_text}"
                        }
        except Exception as e:
            logger.error(f"阿里云分析失败: {str(e)}")
            return {
                "success": False,
                "error": f"分析失败: {str(e)}"
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试阿里云连接"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # 阿里云通义千问的正确API格式
                data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello"
                        }
                    ],
                    "max_tokens": 5
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return {"success": True, "message": "连接成功"}
                    else:
                        error_text = await response.text()
                        logger.error(f"阿里云API调用失败: {response.status} - {error_text}")
                        if error_text:
                            return {"success": False, "message": f"连接失败: {error_text}"}
                        else:
                            return {"success": False, "message": f"连接失败: HTTP {response.status} - 无响应内容"}
        except Exception as e:
            logger.error(f"阿里云连接测试异常: {str(e)}")
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                return {"success": False, "message": "连接失败: 请求超时，请检查API地址是否正确"}
            elif "connection" in error_msg.lower():
                return {"success": False, "message": "连接失败: 无法连接到API服务器，请检查API地址"}
            else:
                return {"success": False, "message": f"连接失败: {error_msg}"}

class AIServiceFactory:
    """AI服务工厂"""
    
    @staticmethod
    def create_service(config: Dict[str, Any]) -> AIService:
        """创建AI服务实例"""
        provider = config.get('provider', 'alibaba')
        
        if provider == 'alibaba':
            return AlibabaService(config)
        else:
            # 默认使用阿里云
            return AlibabaService(config)

class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self):
        self.service = None
        
    def initialize_service(self, config: Dict[str, Any]):
        """初始化AI服务"""
        self.service = AIServiceFactory.create_service(config)
        
    async def analyze_config(self, config_content: str, prompt: str) -> Dict[str, Any]:
        """分析配置"""
        if not self.service:
            return {"success": False, "error": "AI服务未初始化"}
            
        return await self.service.analyze_config(config_content, prompt)
        
    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        if not self.service:
            return {"success": False, "message": "AI服务未初始化"}
            
        return await self.service.test_connection()

# 全局AI服务管理器实例
ai_service_manager = AIServiceManager()
