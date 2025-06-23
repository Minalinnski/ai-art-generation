# src/api/routers/v1/assets/multimedia/video_router.py
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List, Optional

from src.application.handlers.assets.multimedia_handler import MultimediaHandler
from src.infrastructure.decorators.rate_limit import api_rate_limit
from src.infrastructure.decorators.retry import simple_retry
from src.infrastructure.tasks.task_decorator import async_task
from src.schemas.dtos.request.multimedia_request import VideoGenRequest
from src.schemas.dtos.response.base_response import BaseResponse

router = APIRouter(prefix="/video", tags=["Video Processing"])


def get_multimedia_handler() -> MultimediaHandler:
    """获取多媒体处理器"""
    return MultimediaHandler()


@router.post("/remove-background", summary="视频背景移除")
@api_rate_limit(requests_per_minute=10)
#@simple_retry(attempts=2, delay=3.0)
@async_task(priority=2, timeout=900, max_retries=1)
async def remove_video_background(
    request: VideoGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    移除视频背景
    
    特色功能：
    - 智能背景识别
    - Fast/Normal处理模式
    - 自定义背景颜色
    - 保持原始质量
    
    适用场景：
    - 视频会议背景处理
    - 短视频制作
    - 人物抠像处理
    """
    request.model = "background_removal"
    return await handler.process_video(request)


@router.post("/process", summary="通用视频处理")
@api_rate_limit(requests_per_minute=15)
#@simple_retry(attempts=2, delay=3.0)
@async_task(priority=1, timeout=900, max_retries=1)
async def process_video(
    request: VideoGenRequest,
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """
    通用视频处理接口
    
    支持处理类型：
    - background_removal: 背景移除
    
    未来支持：
    - video_enhancement: 视频增强
    - style_transfer: 风格迁移
    - object_removal: 物体移除
    """
    return await handler.process_video(request)


@router.get("/models", summary="获取视频处理模型")
async def get_video_models(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取可用的视频处理模型"""
    try:
        models_info = handler.get_video_models()
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
        service_info = handler.video_service.get_service_info()
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
            "examples": handler.video_service.get_model_examples(model),
            "limits": handler.video_service.get_generation_limits(),
            "service_info": service_info
        }
        
        return BaseResponse.success_response(model_info)
    except Exception as e:
        return BaseResponse.error_response("INFO_ERROR", str(e))


@router.get("/formats", summary="支持的视频格式")
async def get_supported_formats(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取支持的视频格式和规格"""
    try:
        formats_info = handler.video_service.get_supported_formats()
        return BaseResponse.success_response(formats_info)
    except Exception as e:
        return BaseResponse.error_response("FORMATS_ERROR", str(e))


@router.get("/examples", summary="视频处理示例")
async def get_video_examples(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取视频处理的示例参数"""
    try:
        # 获取背景移除模型的示例
        examples = handler.video_service.get_model_examples("background_removal")
        
        # 格式化为API响应格式
        formatted_examples = {
            "background_removal": {}
        }
        
        for example_name, example_data in examples.items():
            formatted_examples["background_removal"][example_name] = {
                "model": "background_removal",
                "num_outputs": 1,
                "generation_params": example_data,
                "description": example_data.get("description", f"背景移除示例: {example_name}")
            }
        
        return BaseResponse.success_response(formatted_examples)
    except Exception as e:
        return BaseResponse.error_response("EXAMPLES_ERROR", str(e))

