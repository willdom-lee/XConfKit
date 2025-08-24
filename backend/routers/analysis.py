from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..database import get_db
from ..services.analysis_service import AnalysisService
from ..services.ai_service import ai_service_manager
from ..schemas import AnalysisRequest, AIConfigRequest
import logging

router = APIRouter(prefix="/api/analysis", tags=["AI分析"])

@router.post("/analyze")
async def analyze_config(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """分析配置"""
    try:
        # 如果请求中包含AI配置，转换为字典格式
        ai_config_dict = None
        if request.ai_config:
            ai_config_dict = {
                "provider": request.ai_config.provider,
                "api_key": request.ai_config.api_key,
                "model": request.ai_config.model,
                "base_url": request.ai_config.base_url,
                "timeout": request.ai_config.timeout,
                "enable_cache": request.ai_config.enable_cache
            }
        
        result = await AnalysisService.analyze_config(
            device_id=request.device_id,
            backup_id=request.backup_id,
            dimensions=request.dimensions,  # 支持维度选择
            ai_config=ai_config_dict,  # 传递AI配置
            db=db
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logging.error(f"分析配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.get("/history")
def get_analysis_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取分析历史"""
    try:
        history = AnalysisService.get_analysis_history(db)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@router.get("/record/{record_id}")
def get_analysis_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """获取单个分析记录"""
    try:
        result = AnalysisService.get_analysis_result(record_id, db)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result["data"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")

@router.delete("/record/{record_id}")
def delete_analysis_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """删除分析记录"""
    try:
        from ..models import AnalysisRecord
        
        record = db.query(AnalysisRecord).filter_by(id=record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="分析记录不存在")
        
        db.delete(record)
        db.commit()
        
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.delete("/records/all")
def delete_all_analysis_records(
    db: Session = Depends(get_db)
):
    """删除所有分析记录"""
    try:
        from ..models import AnalysisRecord
        
        # 删除所有分析记录
        deleted_count = db.query(AnalysisRecord).delete()
        db.commit()
        
        return {"success": True, "message": f"成功删除 {deleted_count} 条分析记录"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# AI配置相关路由
@router.get("/config/ai")
def get_ai_config(db: Session = Depends(get_db)):
    """获取AI配置"""
    try:
        from ..models import AIConfig
        config = db.query(AIConfig).first()
        if config:
            return {
                "provider": config.provider,
                "api_key": config.api_key,
                "model": config.model,
                "base_url": config.base_url,
                "timeout": config.timeout,
                "enable_cache": config.enable_cache,
                "enable_history": config.enable_history,
                "auto_retry": config.auto_retry
            }
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI配置失败: {str(e)}")

@router.post("/config/ai")
def save_ai_config(
    request: AIConfigRequest,
    db: Session = Depends(get_db)
):
    """保存AI配置"""
    try:
        from ..models import AIConfig
        from datetime import datetime
        
        config = db.query(AIConfig).first()
        if not config:
            config = AIConfig()
            db.add(config)
        
        config.provider = request.provider
        config.api_key = request.api_key
        config.model = request.model
        config.base_url = request.base_url
        config.timeout = request.timeout
        config.enable_cache = request.enable_cache
        config.enable_history = request.enable_history
        config.auto_retry = request.auto_retry
        config.updated_at = datetime.now()
        
        db.commit()
        return {"success": True, "message": "AI配置保存成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存AI配置失败: {str(e)}")

@router.post("/config/ai/test")
async def test_ai_connection(
    request: AIConfigRequest,
    db: Session = Depends(get_db)
):
    """测试AI连接"""
    try:
        # 初始化AI服务
        ai_service_manager.initialize_service(request.dict())
        
        # 测试连接
        result = await ai_service_manager.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试连接失败: {str(e)}")

@router.get("/config/prompts")
def get_analysis_prompts(db: Session = Depends(get_db)):
    """获取分析提示词"""
    try:
        from ..models import AnalysisPrompt
        prompts = db.query(AnalysisPrompt).all()
        result = {}
        for prompt in prompts:
            result[prompt.dimension] = {
                "name": prompt.name,
                "description": prompt.description,
                "content": prompt.content,
                "is_default": prompt.is_default
            }
        
        # 如果没有提示词，初始化默认提示词
        if not result:
            AnalysisService.initialize_default_prompts(db)
            prompts = db.query(AnalysisPrompt).all()
            for prompt in prompts:
                result[prompt.dimension] = {
                    "name": prompt.name,
                    "description": prompt.description,
                    "content": prompt.content,
                    "is_default": prompt.is_default
                }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提示词失败: {str(e)}")

@router.post("/config/prompts")
def save_analysis_prompts(
    prompts: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """保存分析提示词"""
    try:
        from ..models import AnalysisPrompt
        from datetime import datetime
        
        for dimension, prompt_data in prompts.items():
            prompt = db.query(AnalysisPrompt).filter_by(dimension=dimension).first()
            if not prompt:
                prompt = AnalysisPrompt(dimension=dimension)
                db.add(prompt)
            
            prompt.name = prompt_data.get('name', '')
            prompt.description = prompt_data.get('description', '')
            prompt.content = prompt_data.get('content', '')
            prompt.is_default = prompt_data.get('is_default', True)
            prompt.updated_at = datetime.now()
        
        db.commit()
        return {"success": True, "message": "提示词保存成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存提示词失败: {str(e)}")

@router.post("/config/prompts/reset")
def reset_analysis_prompts(db: Session = Depends(get_db)):
    """重置分析提示词为默认值"""
    try:
        success = AnalysisService.initialize_default_prompts(db)
        
        if success:
            return {"success": True, "message": "提示词重置成功"}
        else:
            raise HTTPException(status_code=500, detail="提示词重置失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置提示词失败: {str(e)}")
