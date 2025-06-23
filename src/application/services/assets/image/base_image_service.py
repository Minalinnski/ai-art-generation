# src/application/services/assets/image/base_image_service.py (重构版 - 移除hardcode风格，保留提示词构建)
import uuid
import base64
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime

from src.application.services.assets.core.base_asset_service import BaseAssetService
from src.application.config.assets.asset_settings import get_asset_settings
from src.application.services.external.ai_service_factory import ai_service_factory
from src.application.services.external.s3_service import s3_service

class BaseImageService(BaseAssetService, ABC):
    """图像生成服务基类 - 移除hardcode风格，依赖Art Style模块，保留提示词构建"""
    
    def __init__(self):
        super().__init__()
        self.asset_settings = get_asset_settings()
        self.s3_service = s3_service
    
    @abstractmethod
    def get_module_name(self) -> str:
        """获取模块名称"""
        pass
    
    @abstractmethod
    def get_default_prompt_template(self) -> str:
        """获取默认提示词模板"""
        pass
    
    @abstractmethod
    def _get_category_names(self) -> List[str]:
        """获取模块支持的category名称列表"""
        pass
    
    @abstractmethod
    def build_content_prompt(self, task_info: Dict[str, Any], art_style_data: Dict[str, Any]) -> str:
        """
        构建内容相关的提示词 - 子类必须实现
        
        Args:
            task_info: 任务信息（包含filename, description, category等）
            art_style_data: Art Style模块返回的风格数据
            
        Returns:
            构建好的内容提示词
        """
        pass
    
    def get_asset_type(self) -> str:
        """实现基类要求的get_asset_type方法"""
        return self.get_module_name()
    
    def get_service_info(self) -> Dict[str, Any]:
        """实现基类要求的get_service_info方法"""
        available_models = self.asset_settings.get_all_available_ai_models()
        
        return {
            "service_name": self.service_name,
            "description": f"{self.get_module_name()}图像生成服务 - Art Style集成版",
            "version": "1.0.0",
            "category": "image_generation",
            "module": self.get_module_name(),
            "supported_categories": self._get_category_names(),
            "available_models": available_models,
            "default_provider": self.asset_settings.get_module_default_provider(self.get_module_name()),
            "default_model": self.asset_settings.get_module_default_model(self.get_module_name()),
            "features": {
                "art_style_integration": True,
                "new_asset_item_format": True,
                "individual_resolution_control": True,
                "enhanced_prompt_generation": True,
                "reference_image_support": True,
                "s3_integration": True
            },
            "art_style_info": {
                "uses_external_art_style": True,
                "no_hardcoded_styles": True,
                "supported_art_modes": ["preset", "custom_direct", "custom_ai_enhanced", "reference_image"]
            }
        }
    
    def get_available_models(self) -> List[str]:
        """获取可用的图像模型"""
        return self.asset_settings.get_module_supported_models(self.get_module_name())
    
    def validate_model_for_module(self, provider: str, model: str) -> bool:
        """验证模块是否支持特定模型"""
        return self.asset_settings.validate_module_model(self.get_module_name(), provider, model)
    
    def resolve_model_config(self, model: str, provider: Optional[str] = None) -> Tuple[str, str]:
        """解析模型配置"""
        try:
            resolved_provider, resolved_model = self.asset_settings.resolve_module_model(
                self.get_module_name(), 
                model, 
                provider
            )
            return resolved_model, resolved_provider
        except Exception as e:
            available_models = self.asset_settings.get_all_available_ai_models()
            supported_models = self.asset_settings.get_module_supported_models(self.get_module_name())
            
            error_msg = (
                f"模型配置解析失败: {str(e)}\n"
                f"模块 {self.get_module_name()} 支持的模型: {supported_models}\n"
                f"所有可用模型: {available_models}"
            )
            raise ValueError(error_msg)
    
    # === 新的元件格式解析方法 ===
    
    def parse_generation_tasks(self, params: Any) -> List[Dict[str, Any]]:
        """解析生成任务列表 - 支持新的元件格式"""
        tasks = []
        
        # 处理预定义的两层结构内容
        for category_name in self._get_category_names():
            category_data = getattr(params, category_name, None)
            if category_data:
                tasks.extend(self._parse_category_tasks(category_name, category_data, params.default_resolution))
        
        # 处理自定义内容
        if hasattr(params, 'custom_content') and params.custom_content:
            tasks.extend(self._parse_custom_content_tasks(params.custom_content, params.default_resolution))
        
        return tasks
    
    def _parse_category_tasks(self, category_name: str, category_data: Dict[str, List[Dict[str, Any]]], default_resolution: str) -> List[Dict[str, Any]]:
        """解析分类任务 - 使用新的元件格式"""
        tasks = []
        
        for subcategory_name, items in category_data.items():
            for item in items:
                # 支持字典格式的元件
                if isinstance(item, dict):
                    filename = item.get("filename")
                    description = item.get("description", filename)
                    count = item.get("count", 1)
                    resolution = item.get("resolution", default_resolution)
                else:
                    # 兼容旧格式
                    self.logger.warning(f"使用已弃用的元件格式，请更新为新的字典格式: {item}")
                    continue
                
                for index in range(1, count + 1):
                    task_info = {
                        "category": category_name,
                        "subcategory": subcategory_name,
                        "filename": filename,
                        "description": description,
                        "index": index,
                        "resolution": resolution,
                        "format_version": "new"
                    }
                    tasks.append(task_info)
        
        return tasks
    
    def _parse_custom_content_tasks(self, custom_content: Dict[str, List[Dict[str, Any]]], default_resolution: str) -> List[Dict[str, Any]]:
        """解析自定义内容任务"""
        tasks = []
        
        for custom_category, items in custom_content.items():
            for item in items:
                if isinstance(item, dict):
                    filename = item.get("filename")
                    description = item.get("description", filename)
                    count = item.get("count", 1)
                    resolution = item.get("resolution", default_resolution)
                else:
                    continue
                
                for index in range(1, count + 1):
                    task_info = {
                        "category": "custom",
                        "subcategory": custom_category,
                        "filename": filename,
                        "description": description,
                        "index": index,
                        "resolution": resolution,
                        "format_version": "new"
                    }
                    tasks.append(task_info)
        
        return tasks
    
    # === 核心提示词构建方法（调用子类实现）===
    
    def build_complete_prompt(
        self, 
        task_info: Dict[str, Any], 
        art_style_data: Dict[str, Any],
        reference_data: Dict[str, Any] = None
    ) -> str:
        """
        构建完整提示词 - 调用子类的内容提示词构建方法
        
        Args:
            task_info: 任务信息
            art_style_data: Art Style模块返回的完整风格数据
            reference_data: 参考数据（可选）
        """
        
        # 调用子类实现的内容提示词构建
        content_prompt = self.build_content_prompt(task_info, art_style_data)
        
        # 从art_style_data中提取风格信息
        style_prompt = art_style_data.get("style_prompt", "high quality artwork")
        components = art_style_data.get("components", {})
        quality_tags = art_style_data.get("quality_tags", "high quality, professional design")
        
        # 构建完整提示词
        prompt_parts = [
            content_prompt,  # 子类提供的内容描述
            f"Art style: {style_prompt}",  # Art Style模块提供的完整风格
            f"Category: {task_info['category']}, Subcategory: {task_info['subcategory']}"
        ]
        
        # 添加参考信息
        if reference_data:
            if reference_data.get("asset_description"):
                prompt_parts.append(f"Reference: {reference_data['asset_description']}")
            if reference_data.get("reference_prompt"):
                prompt_parts.append(f"Asset reference: {reference_data['reference_prompt']}")
        
        # 添加技术要求和质量标签
        resolution = task_info.get("resolution", "1024x1024")
        prompt_parts.extend([
            f"Technical specs: {resolution} resolution, isolated on transparent background",
            f"Quality: {quality_tags}"
        ])
        
        return ", ".join(prompt_parts)
    
    # === 参考图片处理方法 ===
    
    def prepare_inference_params(
        self,
        base_prompt: str,
        task_info: Dict[str, Any],
        reference_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        准备推理参数，包括图片参考
        
        Args:
            base_prompt: 基础提示词
            task_info: 任务信息
            reference_data: 参考数据，可能包含图片URL
            
        Returns:
            准备好的推理参数
        """
        
        resolution = task_info.get("resolution", "1024x1024")
        inference_params = {
            "prompt": base_prompt,
            "size": resolution,
            "quality": "standard"
        }
        
        # 添加参考图片URL（如果有）
        if reference_data and reference_data.get("reference_image_urls"):
            image_urls = reference_data["reference_image_urls"]
            if isinstance(image_urls, list) and image_urls:
                # 使用新的OpenAI service支持的image_urls参数
                inference_params["image_urls"] = image_urls
                self.logger.info(f"添加参考图片: {len(image_urls)}张")
            elif isinstance(image_urls, str):
                # 单张图片
                inference_params["image_url"] = image_urls
                self.logger.info("添加单张参考图片")
        
        # 添加其他参考信息
        if reference_data:
            if reference_data.get("style_description"):
                inference_params["reference_image_description"] = reference_data["style_description"]
            if reference_data.get("style_guidance"):
                inference_params["style_guidance"] = reference_data["style_guidance"]
        
        return inference_params
    
    # === 继承的必需方法 ===
    
    async def generate(self, model: str, generation_params: Dict[str, Any], num_outputs: int = 1, provider: Optional[str] = None) -> List[str]:
        """基类要求的简化生成方法"""
        try:
            resolved_model, actual_provider = self.resolve_model_config(model, provider)
            
            base_prompt = generation_params.get('prompt', f"Create {num_outputs} high-quality {self.get_module_name()} assets")
            
            ai_service = ai_service_factory.get_service(actual_provider)
            
            results = []
            for i in range(num_outputs):
                try:
                    inference_params = {
                        "prompt": base_prompt,
                        "size": generation_params.get('resolution', '1024x1024'),
                        "quality": "standard"
                    }
                    result = await ai_service.run_inference(resolved_model, inference_params)
                    results.append(result if isinstance(result, str) else str(result))
                except Exception as e:
                    self.logger.error(f"生成第{i+1}个输出失败: {str(e)}")
                    continue
            
            return results
        except Exception as e:
            self.logger.error(f"简化生成失败: {str(e)}")
            raise
    
    # === 验证和辅助方法 ===
    
    def validate_asset_item_format(self, item: Dict[str, Any]) -> bool:
        """验证元件格式是否符合标准"""
        required_fields = ["filename", "description"]
        
        # 检查必需字段
        for field in required_fields:
            if field not in item or not item[field]:
                return False
        
        # 检查可选字段类型
        if "count" in item and (not isinstance(item["count"], int) or item["count"] < 1):
            return False
        
        if "resolution" in item:
            resolution = item["resolution"]
            if resolution and not isinstance(resolution, str):
                return False
            # 简单的分辨率格式验证
            if resolution and 'x' not in resolution:
                return False
        
        return True
    
    def extract_art_style_components(self, art_style_data: Dict[str, Any]) -> Dict[str, str]:
        """
        从Art Style数据中提取有用的组件信息
        
        Returns:
            提取的组件字典，方便子类使用
        """
        components = art_style_data.get("components", {})
        
        return {
            "base_prompt": components.get("base_prompt", ""),
            "color_palette": components.get("color_palette", ""),
            "effects": components.get("effects", ""),
            "materials": components.get("materials", ""),
            "lighting": components.get("lighting", ""),
            "description": components.get("description", ""),
            "quality_tags": art_style_data.get("quality_tags", "high quality, professional design")
        }