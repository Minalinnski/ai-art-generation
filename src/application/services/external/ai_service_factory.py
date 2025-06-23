# src/application/services/external/ai_service_factory.py (更新版)
from typing import Dict, Any, List
from src.infrastructure.logging.logger import get_logger
from src.application.config.ai.ai_settings import get_ai_settings

logger = get_logger(__name__)

class AIServiceFactory:
    """AI服务工厂 - 更新版，基于独立的AI配置"""
    
    def __init__(self):
        self.ai_settings = get_ai_settings()
        self._services: Dict[str, Any] = {}
        logger.info("AI服务工厂初始化完成")
    
    def get_service(self, provider: str):
        """
        获取AI服务实例
        
        Args:
            provider: 提供商名称 (如: "openai", "replicate")
        """
        # 检查提供商是否启用
        if provider not in self.ai_settings.get_enabled_providers():
            available_providers = self.ai_settings.get_enabled_providers()
            raise ValueError(f"AI提供商 {provider} 未启用。可用提供商: {available_providers}")
        
        if provider not in self._services:
            self._services[provider] = self._create_service(provider)
        
        return self._services[provider]
    
    def _create_service(self, provider: str):
        """创建AI服务实例"""
        if provider == "replicate":
            from src.application.services.external.replicate_service import ReplicateService
            return ReplicateService()
        elif provider == "openai":
            from src.application.services.external.openai_service import OpenAIService
            return OpenAIService()
        elif provider == "stability":
            # TODO: 实现Stability服务
            raise NotImplementedError(f"Stability服务尚未实现")
        elif provider == "anthropic":
            # TODO: 实现Anthropic服务
            raise NotImplementedError(f"Anthropic服务尚未实现")
        else:
            available_providers = self.ai_settings.get_enabled_providers()
            raise ValueError(f"不支持的AI服务提供商: {provider}。可用提供商: {available_providers}")
    
    def get_available_providers(self) -> list[str]:
        """获取可用的提供商列表"""
        return self.ai_settings.get_enabled_providers()
    
    def get_all_available_models(self) -> Dict[str, List[str]]:
        """获取所有可用模型"""
        return self.ai_settings.get_all_available_models()
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """获取提供商信息"""
        try:
            service = self.get_service(provider)
            return service.get_service_info()
        except Exception as e:
            return {
                "provider": provider,
                "status": "unavailable",
                "error": str(e)
            }
    
    def validate_model(self, provider: str, model: str) -> bool:
        """验证模型是否可用"""
        try:
            service = self.get_service(provider)
            return service.validate_model(model)
        except Exception:
            return False
    
    def get_models_by_capability(self, capability: str) -> Dict[str, List[str]]:
        """根据能力获取模型"""
        models_by_provider = {}
        
        for provider in self.get_available_providers():
            try:
                service = self.get_service(provider)
                if hasattr(service, '_get_models_by_capability'):
                    models = service._get_models_by_capability(capability)
                    if models:
                        models_by_provider[provider] = models
            except Exception as e:
                logger.warning(f"获取提供商 {provider} 的 {capability} 能力模型失败: {str(e)}")
        
        return models_by_provider

# 全局工厂实例
ai_service_factory = AIServiceFactory()