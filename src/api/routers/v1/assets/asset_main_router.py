# src/api/routers/v1/assets/asset_main_router.py
from fastapi import APIRouter, Depends
from datetime import datetime

from src.application.services.external.ai_service_factory import ai_service_factory
from src.application.handlers.assets.multimedia_handler import MultimediaHandler
from src.schemas.dtos.response.base_response import BaseResponse

# 创建资源API主路由
router = APIRouter(prefix="", tags=["Asset Management"])


def get_multimedia_handler() -> MultimediaHandler:
    """获取多媒体处理器"""
    return MultimediaHandler()


@router.get("/status", summary="获取资源生成服务整体状态")
async def get_overall_status(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取所有资源生成服务的整体状态"""
    try:
        # 获取多媒体服务状态
        multimedia_status = await handler.get_service_status()
        
        # 获取AI提供商状态
        available_providers = ai_service_factory.get_available_providers()
        
        overall_status = {
            "system_status": "healthy" if available_providers else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "ai_providers": {
                "available": available_providers,
                "count": len(available_providers)
            },
            "multimedia_services": multimedia_status,
            "available_categories": ["animation", "audio", "video"],
            "service_endpoints": {
                "animation": "/api/v1/assets/multimedia/animation",
                "audio": "/api/v1/assets/multimedia/audio", 
                "video": "/api/v1/assets/multimedia/video"
            }
        }
        
        return BaseResponse.success_response(overall_status)
        
    except Exception as e:
        return BaseResponse.error_response("OVERALL_STATUS_ERROR", str(e))


@router.get("/providers", summary="获取AI服务提供商信息")
async def get_ai_providers():
    """获取所有AI服务提供商的信息和状态"""
    try:
        available_providers = ai_service_factory.get_available_providers()
        
        providers_info = {
            "available_providers": available_providers,
            "provider_details": {
                provider: {
                    "status": "healthy",
                    "capabilities": ["animation", "audio", "video"]
                } for provider in available_providers
            },
            "total_providers": len(available_providers)
        }
        
        return BaseResponse.success_response(providers_info)
        
    except Exception as e:
        return BaseResponse.error_response("PROVIDERS_INFO_ERROR", str(e))


@router.get("/health", summary="资源生成系统健康检查")
async def assets_health_check(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """整个资源生成系统的健康检查"""
    try:
        # 获取服务健康状态
        service_status = await handler.get_service_status()
        is_healthy = service_status.get("status") == "healthy"
        
        # 获取提供商状态
        available_providers = ai_service_factory.get_available_providers()
        
        health_info = {
            "status": "healthy" if is_healthy and available_providers else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "animation_generation": "available",
                "audio_generation": "available",
                "video_processing": "available"
            },
            "providers": {
                "total": 3,  # replicate, openai, stability
                "available": len(available_providers),
                "enabled": available_providers
            },
            "system_info": service_status
        }
        
        return BaseResponse.success_response(health_info)
        
    except Exception as e:
        return BaseResponse.error_response("HEALTH_CHECK_ERROR", str(e))


@router.get("/capabilities", summary="获取系统能力信息")
async def get_system_capabilities(
    handler: MultimediaHandler = Depends(get_multimedia_handler)
):
    """获取系统支持的所有能力和模型"""
    try:
        capabilities = {
            "asset_types": handler.get_supported_asset_types(),
            "models": {
                "animation": handler.get_animation_models(),
                "audio": handler.get_audio_models(),
                "video": handler.get_video_models()
            },
            "providers": ai_service_factory.get_available_providers(),
            "generation_limits": {
                "max_concurrent_tasks": 10,
                "max_outputs_per_request": 50,
                "default_timeout": 600
            }
        }
        
        return BaseResponse.success_response(capabilities)
        
    except Exception as e:
        return BaseResponse.error_response("CAPABILITIES_ERROR", str(e))