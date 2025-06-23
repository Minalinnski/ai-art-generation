# src/api/routers/v1/assets/multimedia/audio_router.py
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List, Optional

from src.application.handlers.assets.multimedia_handler import MultimediaHandler
from src.infrastructure.decorators.rate_limit import api_rate_limit
from src.infrastructure.decorators.retry import simple_retry
from src.infrastructure.tasks.task_decorator import async_task
from src.schemas.dtos.request.multimedia_request import AudioGenRequest
from src.schemas.dtos.response.base_response import BaseResponse

router = APIRouter(prefix="/audio", tags=["Audio Generation"])


def get_multimedia_handler() -> MultimediaHandler:
    """获取多媒体处理器"""
    return MultimediaHandler()


@router.post("/ardianfe", summary="Ardianfe音乐生成")
@api_rate_limit(requests_per_minute=25)
#@simple_retry(attempts=2, delay=1.0)
@async_task(priority=1, timeout=300, max_retries=2)
async def generate_ardianfe_music(
    request: AudioGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    使用Ardianfe生成音乐
    
    特色功能：
    - 高质量立体声生成
    - 和弦进行控制
    - 多种音频格式
    - 音乐结构控制
    """
    request.model = "ardianfe"
    return await handler.generate_audio(request)


@router.post("/meta", summary="Meta MusicGen音乐生成")
@api_rate_limit(requests_per_minute=30)
#@simple_retry(attempts=2, delay=1.0)
@async_task(priority=1, timeout=300, max_retries=2)
async def generate_meta_music(
    request: AudioGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    使用Meta MusicGen生成音乐
    
    特色功能：
    - 快速高质量生成
    - 多种模型版本
    - 旋律条件生成
    - 音乐续写功能
    """
    request.model = "meta"
    return await handler.generate_audio(request)


@router.post("/generate", summary="通用音乐生成")
@api_rate_limit(requests_per_minute=35)
#@simple_retry(attempts=2, delay=1.0)
@async_task(priority=1, timeout=300, max_retries=2)
async def generate_audio(
    request: AudioGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    通用音乐生成接口
    
    支持模型：
    - ardianfe: 高质量立体声音乐
    - meta: Meta MusicGen模型
    """
    return await handler.generate_audio(request)


@router.get("/models", summary="获取音频模型")
async def get_audio_models(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取可用的音频生成模型"""
    try:
        models_info = handler.get_audio_models()
        return BaseResponse.success_response(models_info)
    except Exception as e:
        return BaseResponse.error_response("MODELS_ERROR", str(e))


@router.get("/info/{model}", summary="获取模型详细信息")
async def get_model_info(
    model: str,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取指定模型的详细信息，包括能力、示例和限制"""
    try:
        # 通过service获取模型信息
        service_info = handler.audio_service.get_service_info()
        model_capabilities = service_info.get("model_capabilities", {})
        
        if model not in model_capabilities:
            available_models = list(model_capabilities.keys())
            return BaseResponse.error_response(
                "MODEL_NOT_FOUND", 
                f"模型 {model} 不存在。可用模型: {available_models}"
            )
        
        model_info = {
            "model": model,
            "capabilities": model_capabilities[model],
            "examples": handler.audio_service.get_model_examples(model),
            "limits": handler.audio_service.get_generation_limits(),
            "service_info": service_info
        }
        
        return BaseResponse.success_response(model_info)
    except Exception as e:
        return BaseResponse.error_response("INFO_ERROR", str(e))