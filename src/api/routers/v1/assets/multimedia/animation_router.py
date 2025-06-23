# src/api/routers/v1/assets/multimedia/animation_router.py
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List, Optional

from src.application.handlers.assets.multimedia_handler import MultimediaHandler
from src.infrastructure.decorators.rate_limit import api_rate_limit
from src.infrastructure.decorators.retry import simple_retry
from src.infrastructure.tasks.task_decorator import async_task
from src.schemas.dtos.request.multimedia_request import AnimationGenRequest
from src.schemas.dtos.response.base_response import BaseResponse

router = APIRouter(prefix="/animation", tags=["Animation Generation"])


def get_multimedia_handler() -> MultimediaHandler:
    """获取多媒体处理器"""
    return MultimediaHandler()


@router.post("/pixverse", summary="Pixverse动画生成")
@api_rate_limit(requests_per_minute=15)
#@simple_retry(attempts=2, delay=2.0)
@async_task(priority=2, timeout=600, max_retries=1)
async def generate_pixverse_animation(
    request: AnimationGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    使用Pixverse生成动画
    
    特色功能：
    - 文本到动画生成
    - 多种分辨率支持
    - 风格和特效控制
    - 自定义时长和宽高比
    """
    request.model = "pixverse"
    return await handler.generate_animation(request)


@router.post("/pia", summary="PIA动画生成")
@api_rate_limit(requests_per_minute=15)
#@simple_retry(attempts=2, delay=2.0)
@async_task(priority=2, timeout=600, max_retries=1)
async def generate_pia_animation(
    request: AnimationGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    使用PIA生成动画
    
    特色功能：
    - 图片到动画生成
    - 精确运动控制
    - 3D卡通和写实风格
    - 可控制运动幅度
    """
    request.model = "pia"
    return await handler.generate_animation(request)


@router.post("/generate", summary="通用动画生成")
@api_rate_limit(requests_per_minute=20)
#@simple_retry(attempts=2, delay=2.0)
@async_task(priority=1, timeout=600, max_retries=1)
async def generate_animation(
    request: AnimationGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    通用动画生成接口
    
    支持模型：
    - pixverse: 文本生成动画
    - pia: 图片生成动画
    """
    return await handler.generate_animation(request)


@router.get("/models", summary="获取动画模型")
async def get_animation_models(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取可用的动画生成模型"""
    try:
        models_info = handler.get_animation_models()
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
        service_info = handler.animation_service.get_service_info()
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
            "examples": handler.animation_service.get_model_examples(model),
            "limits": handler.animation_service.get_generation_limits(),
            "service_info": service_info
        }
        
        return BaseResponse.success_response(model_info)
    except Exception as e:
        return BaseResponse.error_response("INFO_ERROR", str(e))


@router.get("/examples", summary="动画生成示例")
async def get_animation_examples(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取动画生成的示例参数"""
    try:
        # 获取所有支持模型的示例
        pixverse_examples = handler.animation_service.get_model_examples("pixverse")
        pia_examples = handler.animation_service.get_model_examples("pia")
        
        # 格式化为API响应格式
        formatted_examples = {
            "pixverse_examples": {},
            "pia_examples": {}
        }
        
        # 格式化Pixverse示例
        for example_name, example_data in pixverse_examples.items():
            formatted_examples["pixverse_examples"][example_name] = {
                "model": "pixverse",
                "num_outputs": 1,
                "generation_params": {k: v for k, v in example_data.items() if k != "description"},
                "description": example_data.get("description", f"Pixverse动画示例: {example_name}")
            }
        
        # 格式化PIA示例
        for example_name, example_data in pia_examples.items():
            formatted_examples["pia_examples"][example_name] = {
                "model": "pia",
                "num_outputs": 1,
                "generation_params": {k: v for k, v in example_data.items() if k != "description"},
                "description": example_data.get("description", f"PIA动画示例: {example_name}")
            }
        
        return BaseResponse.success_response(formatted_examples)
    except Exception as e:
        return BaseResponse.error_response("EXAMPLES_ERROR", str(e))


@router.get("/presets", summary="动画预设配置")
async def get_animation_presets(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取动画生成的预设配置"""
    try:
        presets = handler.animation_service.get_animation_presets()
        return BaseResponse.success_response(presets)
    except Exception as e:
        return BaseResponse.error_response("PRESETS_ERROR", str(e))
