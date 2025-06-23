# src/application/services/assets/core/base_asset_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from src.application.services.service_interface import BaseService
from src.application.config.assets.asset_settings import get_asset_settings


class BaseAssetService(BaseService, ABC):
    """资源生成服务基类 - 优化版"""
    
    def __init__(self):
        super().__init__()
        self.asset_settings = get_asset_settings()
        self.asset_type = self.get_asset_type()
    
    @abstractmethod
    def get_asset_type(self) -> str:
        """获取资源类型 - 返回字符串"""
        pass
    
    @abstractmethod
    async def generate(
        self, 
        model: str, 
        generation_params: Dict[str, Any], 
        num_outputs: int = 1,
        provider: Optional[str] = None
    ) -> List[str]:
        """生成资源"""
        pass
    
    def get_available_models(self, provider: Optional[str] = None) -> List[str]:
        """获取可用模型列表"""
        return self.asset_settings.get_available_models(
            self.asset_type, 
            provider
        )
    
    def get_generation_limits(self) -> Dict[str, Any]:
        """获取生成限制"""
        return self.asset_settings.get_generation_limits(self.asset_type)
    
    def resolve_model_config(self, model: str, provider: Optional[str] = None) -> Tuple[str, str]:
        """
        解析模型配置用于推理
        
        Args:
            model: 模型名 (如: ardianfe, meta, pixverse, pia, background_removal)
            provider: 提供商 (可选，默认使用配置的默认提供商)
        
        Returns:
            Tuple[实际模型ID, 使用的提供商]
        """
        return self.asset_settings.resolve_model_for_inference(
            self.asset_type, 
            model, 
            provider
        )
    
    def validate_generation_request(self, model: str, num_outputs: int, provider: Optional[str] = None):
        """验证生成请求"""
        # 检查模型是否可用
        available_models = self.get_available_models(provider)
        if model not in available_models:
            raise ValueError(f"模型 {model} 不可用。可用模型: {available_models}")
        
        # 检查生成数量限制
        limits = self.get_generation_limits()
        max_outputs = limits.get("max_outputs_per_request", 50)
        if num_outputs > max_outputs:
            raise ValueError(f"生成数量 {num_outputs} 超过限制 {max_outputs}")
        
        # 检查提供商是否可用
        if provider and not self.asset_settings.is_provider_available(provider):
            enabled_providers = self.asset_settings.get_enabled_ai_providers()
            raise ValueError(f"提供商 {provider} 不可用。可用提供商: {enabled_providers}")
    
    def get_default_provider(self) -> str:
        """获取默认提供商"""
        return self.asset_settings.get_default_provider(self.asset_type)
    
    def get_model_info(self, model: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """获取模型详细信息"""
        if not provider:
            provider = self.get_default_provider()
        
        model_config = self.asset_settings.get_model_config(self.asset_type, provider, model)
        if not model_config:
            return {}
        
        return {
            "model": model,
            "provider": provider,
            "model_id": model_config.get("model_id"),
            "description": model_config.get("description", ""),
            "max_duration": model_config.get("max_duration"),
            "output_format": model_config.get("output_format"),
            "asset_type": self.asset_type
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """服务健康检查"""
        try:
            available_models = self.get_available_models()
            generation_limits = self.get_generation_limits()
            default_provider = self.get_default_provider()
            
            return {
                "service": self.service_name,
                "asset_type": self.asset_type,
                "status": "healthy" if available_models else "degraded",
                "available_models": available_models,
                "default_provider": default_provider,
                "generation_limits": generation_limits,
                "timestamp": self._get_current_time()
            }
        except Exception as e:
            self.logger.error(f"{self.asset_type}服务健康检查失败: {str(e)}")
            return {
                "service": self.service_name,
                "asset_type": self.asset_type,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self._get_current_time()
            }
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.utcnow().isoformat()