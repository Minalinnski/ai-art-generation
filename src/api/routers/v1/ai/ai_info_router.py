# src/api/routers/v1/ai/ai_info_router.py
from fastapi import APIRouter, HTTPException
from src.application.services.external.ai_service_factory import ai_service_factory
from src.schemas.dtos.response.base_response import BaseResponse

router = APIRouter(prefix="/ai", tags=["AI Service Information"])

@router.get("/providers", summary="获取可用的AI提供商")
async def get_available_providers():
    """获取所有可用的AI提供商列表"""
    try:
        providers = ai_service_factory.get_available_providers()
        return BaseResponse.success_response({
            "providers": providers,
            "total_count": len(providers)
        })
    except Exception as e:
        return BaseResponse.error_response("GET_PROVIDERS_ERROR", str(e))

@router.get("/models", summary="获取所有可用模型")
async def get_all_available_models():
    """获取所有提供商的可用模型"""
    try:
        models = ai_service_factory.get_all_available_models()
        total_models = sum(len(model_list) for model_list in models.values())
        
        return BaseResponse.success_response({
            "models_by_provider": models,
            "total_models": total_models,
            "total_providers": len(models)
        })
    except Exception as e:
        return BaseResponse.error_response("GET_MODELS_ERROR", str(e))

@router.get("/providers/{provider}", summary="获取特定提供商信息")
async def get_provider_info(provider: str):
    """获取特定AI提供商的详细信息"""
    try:
        provider_info = ai_service_factory.get_provider_info(provider)
        return BaseResponse.success_response(provider_info)
    except Exception as e:
        return BaseResponse.error_response("GET_PROVIDER_INFO_ERROR", str(e))

@router.get("/providers/{provider}/models", summary="获取提供商的模型列表")
async def get_provider_models(provider: str):
    """获取特定提供商的所有可用模型"""
    try:
        service = ai_service_factory.get_service(provider)
        
        if hasattr(service, 'available_models'):
            models = service.available_models
        else:
            models = {}
        
        return BaseResponse.success_response({
            "provider": provider,
            "models": models,
            "model_count": len(models)
        })
    except Exception as e:
        return BaseResponse.error_response("GET_PROVIDER_MODELS_ERROR", str(e))

@router.post("/validate", summary="验证模型可用性")
async def validate_model(
    provider: str,
    model: str
):
    """验证特定提供商的模型是否可用"""
    try:
        is_valid = ai_service_factory.validate_model(provider, model)
        
        result = {
            "provider": provider,
            "model": model,
            "is_valid": is_valid
        }
        
        if not is_valid:
            # 提供可用选项
            try:
                service = ai_service_factory.get_service(provider)
                if hasattr(service, 'available_models'):
                    result["available_models"] = list(service.available_models.keys())
            except:
                result["available_models"] = []
        
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("VALIDATE_MODEL_ERROR", str(e))

@router.get("/capabilities/{capability}", summary="按能力查询模型")
async def get_models_by_capability(capability: str):
    """根据能力获取支持的模型"""
    try:
        models = ai_service_factory.get_models_by_capability(capability)
        total_models = sum(len(model_list) for model_list in models.values())
        
        return BaseResponse.success_response({
            "capability": capability,
            "models_by_provider": models,
            "total_models": total_models,
            "providers_supporting": list(models.keys())
        })
    except Exception as e:
        return BaseResponse.error_response("GET_CAPABILITY_MODELS_ERROR", str(e))

@router.get("/health", summary="AI服务健康检查")
async def ai_services_health_check():
    """检查所有AI服务的健康状态"""
    try:
        health_status = {}
        providers = ai_service_factory.get_available_providers()
        
        for provider in providers:
            try:
                service = ai_service_factory.get_service(provider)
                if hasattr(service, 'health_check'):
                    health_status[provider] = await service.health_check()
                else:
                    health_status[provider] = {
                        "provider": provider,
                        "status": "unknown",
                        "message": "健康检查方法不可用"
                    }
            except Exception as e:
                health_status[provider] = {
                    "provider": provider,
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        overall_status = "healthy" if all(
            status.get("status") == "healthy" 
            for status in health_status.values()
        ) else "partial"
        
        return BaseResponse.success_response({
            "overall_status": overall_status,
            "providers": health_status,
            "total_providers": len(providers),
            "healthy_providers": len([
                s for s in health_status.values() 
                if s.get("status") == "healthy"
            ])
        })
    except Exception as e:
        return BaseResponse.error_response("HEALTH_CHECK_ERROR", str(e))

@router.get("/supported-capabilities", summary="获取支持的能力列表")
async def get_supported_capabilities():
    """获取所有AI服务支持的能力列表"""
    try:
        capabilities = set()
        providers = ai_service_factory.get_available_providers()
        
        for provider in providers:
            try:
                service = ai_service_factory.get_service(provider)
                if hasattr(service, 'available_models'):
                    for model_info in service.available_models.values():
                        model_capabilities = model_info.get("capabilities", [])
                        capabilities.update(model_capabilities)
            except Exception as e:
                continue
        
        return BaseResponse.success_response({
            "capabilities": sorted(list(capabilities)),
            "total_capabilities": len(capabilities)
        })
    except Exception as e:
        return BaseResponse.error_response("GET_CAPABILITIES_ERROR", str(e))