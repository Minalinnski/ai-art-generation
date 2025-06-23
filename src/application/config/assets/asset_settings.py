# src/application/config/assets/asset_settings.py (重构版)
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

from src.infrastructure.logging.logger import get_logger
from src.application.config.ai.ai_settings import get_ai_settings

logger = get_logger(__name__)

class AssetSettings:
    """资源生成配置类 - 专注于资源配置，AI配置已独立"""
    
    def __init__(self):
        self._asset_models_config: Dict[str, Any] = {}
        self._image_structure_config: Dict[str, Any] = {}
        self.ai_settings = get_ai_settings()  # 注入AI配置
        
        self._load_configs()
        self._validate_configs()
    
    def _load_configs(self):
        """加载配置文件"""
        config_dir = Path(__file__).parent
        
        # 初始化资源模型配置结构
        self._asset_models_config = {
            "assets": {},
            "module_models": {},
            "global_generation_config": {}
        }
        
        # 读取多媒体模型配置
        multimedia_models_path = config_dir / "multimedia_models.yaml"
        if multimedia_models_path.exists():
            try:
                with open(multimedia_models_path, "r", encoding="utf-8") as f:
                    multimedia_config = yaml.safe_load(f) or {}
                    multimedia_assets = multimedia_config.get("assets", {})
                    self._asset_models_config["assets"].update(multimedia_assets)
                    
                    if "module_models" in multimedia_config:
                        self._asset_models_config["module_models"].update(multimedia_config["module_models"])
                        
                logger.info(f"多媒体模型配置加载完成: {multimedia_models_path}")
            except Exception as e:
                logger.error(f"加载多媒体模型配置失败: {e}")
        
        # 读取图像模型配置
        image_models_path = config_dir / "image_models.yaml"
        if image_models_path.exists():
            try:
                with open(image_models_path, "r", encoding="utf-8") as f:
                    image_config = yaml.safe_load(f) or {}
                    
                    # 合并资源配置
                    image_assets = image_config.get("assets", {})
                    self._asset_models_config["assets"].update(image_assets)
                    
                    # 合并模块模型配置
                    if "module_models" in image_config:
                        self._asset_models_config["module_models"].update(image_config["module_models"])
                    
                    # 合并全局配置
                    if "global_generation_config" in image_config:
                        self._asset_models_config["global_generation_config"].update(image_config["global_generation_config"])
                        
                logger.info(f"图像模型配置加载完成: {image_models_path}")
            except Exception as e:
                logger.error(f"加载图像模型配置失败: {e}")
        
        # 加载图像结构配置
        image_structure_path = config_dir / "image_structure.yaml"
        if image_structure_path.exists():
            try:
                with open(image_structure_path, "r", encoding="utf-8") as f:
                    self._image_structure_config = yaml.safe_load(f) or {}
                logger.info(f"图像结构配置加载完成: {image_structure_path}")
            except Exception as e:
                logger.error(f"加载图像结构配置失败: {e}")
                self._image_structure_config = {}
    
    def _validate_configs(self):
        """验证配置完整性"""
        # 验证模块模型配置完整性
        module_models = self._asset_models_config.get("module_models", {})
        if not module_models:
            logger.warning("未找到模块模型配置，将使用默认配置")
        
        # 验证模块绑定的AI服务是否可用
        enabled_providers = self.ai_settings.get_enabled_providers()
        for module, config in module_models.items():
            default_provider = config.get("default_provider")
            if default_provider and default_provider not in enabled_providers:
                logger.warning(f"模块 {module} 的默认提供商 {default_provider} 不可用")
    
    # === AI服务相关方法（代理到ai_settings）===
    
    def get_enabled_ai_providers(self) -> List[str]:
        """获取启用的AI提供商列表"""
        return self.ai_settings.get_enabled_providers()
    
    def get_ai_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取AI提供商配置"""
        return self.ai_settings.get_provider_config(provider)
    
    def validate_ai_model(self, provider: str, model: str) -> bool:
        """验证AI模型是否可用"""
        return self.ai_settings.validate_model(provider, model)
    
    def get_all_available_ai_models(self) -> Dict[str, List[str]]:
        """获取所有可用AI模型"""
        return self.ai_settings.get_all_available_models()
    
    # === 资源配置方法 ===
    
    def get_asset_config(self, asset_type: str) -> Dict[str, Any]:
        """获取资源类型配置"""
        assets = self._asset_models_config.get("assets", {})
        return assets.get(asset_type, {})
    
    def get_default_provider(self, asset_type: str) -> str:
        """获取资源类型的默认提供商"""
        asset_config = self.get_asset_config(asset_type)
        return asset_config.get("default_provider", "openai")
    
    def get_generation_limits(self, asset_type: str) -> Dict[str, Any]:
        """获取生成限制配置"""
        asset_config = self.get_asset_config(asset_type)
        return asset_config.get("generation_limits", {
            "max_outputs_per_request": 5,
            "default_timeout": 300
        })
    
    def get_supported_asset_types(self) -> List[str]:
        """获取支持的资源类型列表"""
        assets = self._asset_models_config.get("assets", {})
        return list(assets.keys())
    
    # === 模块相关配置方法 ===
    
    def get_module_default_provider(self, module: str) -> str:
        """获取模块默认AI提供商"""
        module_models = self._asset_models_config.get("module_models", {})
        module_config = module_models.get(module, {})
        return module_config.get("default_provider", "openai")
    
    def get_module_default_model(self, module: str) -> str:
        """获取模块默认模型"""
        module_models = self._asset_models_config.get("module_models", {})
        module_config = module_models.get(module, {})
        return module_config.get("default_model", "gpt-image-1")
    
    def get_module_supported_models(self, module: str) -> List[str]:
        """获取模块支持的模型列表"""
        module_models = self._asset_models_config.get("module_models", {})
        module_config = module_models.get(module, {})
        return module_config.get("supported_models", ["gpt-image-1"])
    
    def get_module_models_config(self) -> Dict[str, Any]:
        """获取所有模块模型配置"""
        return self._asset_models_config.get("module_models", {})
    
    def validate_module_model(self, module: str, provider: str, model: str) -> bool:
        """验证模块是否支持特定的提供商和模型"""
        # 1. 检查模块是否支持该模型
        supported_models = self.get_module_supported_models(module)
        if model not in supported_models:
            return False
        
        # 2. 检查AI服务是否可用
        return self.ai_settings.validate_model(provider, model)
    
    def resolve_module_model(self, module: str, model: Optional[str] = None, provider: Optional[str] = None) -> tuple[str, str]:
        """解析模块的模型配置"""
        # 使用传入的或默认的提供商
        if not provider:
            provider = self.get_module_default_provider(module)
        
        # 使用传入的或默认的模型
        if not model:
            model = self.get_module_default_model(module)
        
        # 验证配置有效性
        if not self.validate_module_model(module, provider, model):
            available_models = self.get_module_supported_models(module)
            enabled_providers = self.get_enabled_ai_providers()
            raise ValueError(
                f"模块 {module} 不支持 {provider}/{model}。"
                f"支持的模型: {available_models}，可用提供商: {enabled_providers}"
            )
        
        return provider, model
    
    # === 图像结构相关配置方法 ===
    
    def get_image_structure_config(self) -> Dict[str, Any]:
        """获取图像结构配置"""
        return self._image_structure_config
    
    def get_module_config(self, module: str) -> Dict[str, Any]:
        """获取模块配置"""
        modules = self._image_structure_config.get("modules", {})
        return modules.get(module, {})
    
    def get_module_categories(self, module: str) -> Dict[str, Any]:
        """获取模块分类"""
        module_config = self.get_module_config(module)
        return module_config.get("categories", {})
    
    def build_s3_input_path(self, module: str, style_theme: str, category: str = "", subcategory: str = "") -> str:
        """构建S3输入路径"""
        s3_paths = self._image_structure_config.get("s3_paths", {})
        input_base = s3_paths.get("input_base", "image_assets_input/references/")
        input_structure = s3_paths.get("input_structure", {})
        
        path_template = input_structure.get(module, "{style_theme}/{module}/")
        
        path = path_template.format(
            style_theme=style_theme,
            module=module,
            category=category,
            subcategory=subcategory
        )
        
        return input_base + path
    
    def build_s3_output_path(self, module: str, task_id: str, category: str = "", subcategory: str = "") -> str:
        """构建S3输出路径"""
        from datetime import datetime
        now = datetime.utcnow()
        
        s3_paths = self._image_structure_config.get("s3_paths", {})
        output_base = s3_paths.get("output_base", "image_assets_output/{year}-{month}-{day}/{task_id}/")
        output_structure = s3_paths.get("output_structure", {})
        
        base_path = output_base.format(
            year=now.year,
            month=f"{now.month:02d}",
            day=f"{now.day:02d}",
            task_id=task_id
        )
        
        module_path = output_structure.get(module, f"{module}/")
        module_path = module_path.format(
            category=category,
            subcategory=subcategory
        )
        
        return base_path + module_path
    
    def get_naming_pattern(self) -> str:
        """获取统一命名模式"""
        naming_conventions = self._image_structure_config.get("naming_conventions", {})
        return naming_conventions.get("pattern", "{category}_{subcategory}_{type}_{index:02d}.png")
    
    # === 全局配置方法 ===
    
    def get_global_generation_config(self) -> Dict[str, Any]:
        """获取全局生成配置"""
        return self._asset_models_config.get("global_generation_config", {})
    
    def get_max_concurrent_generations(self) -> int:
        """获取最大并发生成数"""
        global_config = self.get_global_generation_config()
        return global_config.get("max_concurrent_generations", 3)

@lru_cache()
def get_asset_settings() -> AssetSettings:
    """获取缓存的资源配置实例"""
    return AssetSettings()

# 便捷函数
def get_available_providers() -> List[str]:
    """获取可用的AI提供商"""
    return get_asset_settings().get_enabled_ai_providers()

def get_asset_types() -> List[str]:
    """获取支持的资源类型"""
    return get_asset_settings().get_supported_asset_types()

def get_all_available_models() -> Dict[str, List[str]]:
    """获取所有可用的AI模型"""
    return get_asset_settings().get_all_available_ai_models()

def validate_model_for_module(module: str, provider: str, model: str) -> bool:
    """验证模块是否支持特定模型"""
    return get_asset_settings().validate_module_model(module, provider, model)