# src/application/config/ai/ai_settings.py
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache
from dotenv import load_dotenv

from src.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

class AISettings:
    """AI服务配置类 - 独立于asset配置"""
    
    def __init__(self):
        self._providers_config: Dict[str, Any] = {}
        self._models_config: Dict[str, Any] = {}
        
        self._load_configs()
        self._validate_configs()
    
    def _load_configs(self):
        """加载AI配置文件"""
        config_dir = Path(__file__).parent
        
        # 加载提供商配置
        providers_path = config_dir / "providers.yaml"
        if providers_path.exists():
            try:
                with open(providers_path, "r", encoding="utf-8") as f:
                    self._providers_config = yaml.safe_load(f) or {}
                logger.info(f"AI提供商配置加载完成: {providers_path}")
            except Exception as e:
                logger.error(f"加载AI提供商配置失败: {e}")
                self._providers_config = {}
        
        # 加载模型配置
        models_path = config_dir / "models.yaml"
        if models_path.exists():
            try:
                with open(models_path, "r", encoding="utf-8") as f:
                    self._models_config = yaml.safe_load(f) or {}
                logger.info(f"AI模型配置加载完成: {models_path}")
            except Exception as e:
                logger.error(f"加载AI模型配置失败: {e}")
                self._models_config = {}
    
    def _validate_configs(self):
        """验证配置完整性"""
        # 检查API密钥
        api_keys = {
            "replicate": os.getenv("REPLICATE_API_TOKEN"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "stability": os.getenv("STABILITY_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        }
        
        missing_keys = []
        enabled_providers = self.get_enabled_providers()
        
        for provider in enabled_providers:
            if not api_keys.get(provider):
                missing_keys.append(provider)
        
        if missing_keys:
            logger.warning(f"以下启用的提供商缺少API密钥: {missing_keys}")
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取AI提供商配置"""
        providers = self._providers_config.get("providers", {})
        config = providers.get(provider, {})
        
        if config:
            # 添加API密钥
            api_key_mapping = {
                "replicate": "REPLICATE_API_TOKEN",
                "openai": "OPENAI_API_KEY", 
                "stability": "STABILITY_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
            }
            
            env_key = api_key_mapping.get(provider)
            if env_key:
                api_key = os.getenv(env_key)
                config = config.copy()
                config["api_key"] = api_key
                config["has_api_key"] = bool(api_key)
        
        return config
    
    def get_enabled_providers(self) -> List[str]:
        """获取启用的AI提供商列表"""
        enabled_providers = []
        providers = self._providers_config.get("providers", {})
        
        for provider, config in providers.items():
            if config.get("enabled", False):
                api_key_mapping = {
                    "replicate": "REPLICATE_API_TOKEN",
                    "openai": "OPENAI_API_KEY",
                    "stability": "STABILITY_API_KEY", 
                    "anthropic": "ANTHROPIC_API_KEY",
                }
                
                env_key = api_key_mapping.get(provider)
                if env_key and os.getenv(env_key):
                    enabled_providers.append(provider)
                elif not env_key:
                    enabled_providers.append(provider)
                else:
                    logger.warning(f"提供商 {provider} 已启用但缺少API密钥: {env_key}")
        
        return enabled_providers
    
    def get_provider_models(self, provider: str) -> Dict[str, Any]:
        """获取提供商的模型配置"""
        provider_models = self._models_config.get("providers", {}).get(provider, {})
        return provider_models.get("models", {})
    
    def get_model_info(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """获取具体模型信息"""
        models = self.get_provider_models(provider)
        return models.get(model)
    
    def get_all_available_models(self) -> Dict[str, List[str]]:
        """获取所有可用模型"""
        available_models = {}
        enabled_providers = self.get_enabled_providers()
        
        for provider in enabled_providers:
            models = list(self.get_provider_models(provider).keys())
            if models:
                available_models[provider] = models
        
        return available_models
    
    def validate_model(self, provider: str, model: str) -> bool:
        """验证模型是否可用"""
        if provider not in self.get_enabled_providers():
            return False
        
        models = self.get_provider_models(provider)
        return model in models
    
    def get_model_capabilities(self, provider: str, model: str) -> List[str]:
        """获取模型能力"""
        model_info = self.get_model_info(provider, model)
        if model_info:
            return model_info.get("capabilities", [])
        return []

@lru_cache()
def get_ai_settings() -> AISettings:
    """获取缓存的AI配置实例"""
    return AISettings()