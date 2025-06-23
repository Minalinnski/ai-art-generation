# src/application/services/assets/animation_service.py - 修复版
from typing import Dict, Any, List, Optional
from src.application.services.assets.core.base_asset_service import BaseAssetService
from src.application.services.external.ai_service_factory import ai_service_factory
from src.schemas.enums.asset_enums import AssetTypeEnum, ModelProviderEnum
from src.infrastructure.decorators.retry import simple_retry


class AnimationService(BaseAssetService):
    """动画生成服务 - 修复版"""
    
    def get_asset_type(self) -> AssetTypeEnum:
        return AssetTypeEnum.ANIMATION
    
    def get_service_info(self) -> Dict[str, Any]:
        base_info = super().get_service_info()
        return {
            **base_info,
            "description": "动画生成服务 - 支持Pixverse和PIA模型",
            "model_capabilities": self._get_model_capabilities()
        }
    
    def _get_model_capabilities(self) -> Dict[str, Any]:
        """获取模型能力描述"""
        return {
            "pixverse": {
                "description": "文本到动画生成，支持多种风格和特效",
                "input_types": ["text", "image"],
                "max_duration": 8,
                "output_format": "mp4",
                "features": ["text_to_video", "style_control", "effect_control", "quality_options"],
                "best_for": ["creative_content", "social_media", "marketing"]
            },
            "pia": {
                "description": "图片到动画生成，精确运动控制",
                "input_types": ["text", "image"],
                "max_duration": 24,
                "output_format": "mp4",
                "features": ["image_to_video", "motion_control", "style_transfer", "precision_animation"],
                "best_for": ["portrait_animation", "character_animation", "product_demo"]
            }
        }
    
    async def generate(
        self, 
        model: str, 
        generation_params: Dict[str, Any], 
        num_outputs: int = 1,
        provider: Optional[str] = None
    ) -> List[str]:
        """生成动画 - 使用基类的模型解析"""
        try:
            self.logger.info(f"开始生成动画: {model}", extra={
                "model": model,
                "num_outputs": num_outputs,
                "provider": provider,
                "params_keys": list(generation_params.keys()) if generation_params else []
            })
            
            # 验证请求
            self.validate_generation_request(model, num_outputs, provider)
            
            # 解析模型配置 - 使用基类方法，确保返回正确的model_id字符串
            model_id, provider_name = self.resolve_model_config(model, provider)
            
            self.logger.debug(f"解析到模型ID: {model_id}", extra={
                "original_model": model,
                "provider": provider_name,
                "resolved_model_id": model_id
            })
            
            # 获取AI服务
            ai_service = ai_service_factory.get_service(ModelProviderEnum(provider_name))
            
            # 预处理生成参数
            processed_params = self._preprocess_generation_params(model, generation_params)
            
            # 调用AI服务进行推理 - 传递正确的model_id字符串
            results = await ai_service.batch_inference(model_id, processed_params, num_outputs)
            
            self.logger.info(f"动画生成完成: {len(results)}个结果", extra={
                "model": model,
                "model_id": model_id,
                "provider": provider_name,
                "success_count": len(results)
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"动画生成失败: {str(e)}", extra={
                "model": model,
                "provider": provider,
                "error_type": type(e).__name__
            })
            raise
    
    def _preprocess_generation_params(self, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """预处理生成参数 - 在Service层设置默认值和验证"""
        processed_params = params.copy()
        
        # 验证必需参数
        if "prompt" not in processed_params:
            raise ValueError(f"{model} 模型缺少必需参数: prompt")
        
        # 根据不同模型进行参数预处理
        if model == "pixverse":
            self._apply_pixverse_defaults(processed_params)
        elif model == "pia":
            self._apply_pia_defaults(processed_params)
        else:
            # 通用默认值
            self._apply_common_defaults(processed_params)
        
        # 验证参数
        self._validate_common_params(processed_params)
        
        return processed_params
    
    def _apply_pixverse_defaults(self, params: Dict[str, Any]) -> None:
        """应用Pixverse模型的默认值"""
        defaults = {
            "quality": "1080p",
            "duration": 5,
            "motion_mode": "normal",
            "aspect_ratio": "16:9",
            "negative_prompt": "",
            "style": "None",
            "effect": "None"
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _apply_pia_defaults(self, params: Dict[str, Any]) -> None:
        """应用PIA模型的默认值"""
        # 验证必需的image参数
        if "image" not in params:
            raise ValueError("PIA模型缺少必需参数: image")
        
        defaults = {
            "max_size": 512,
            "style": "3d_cartoon",
            "motion_scale": 1,
            "guidance_scale": 7.5,
            "sampling_steps": 25,
            "negative_prompt": "",
            "animation_length": 16,
            "ip_adapter_scale": 1.0
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _apply_common_defaults(self, params: Dict[str, Any]) -> None:
        """应用通用默认值"""
        defaults = {
            "quality": "720p",
            "duration": 5,
            "aspect_ratio": "16:9"
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _validate_common_params(self, params: Dict[str, Any]) -> None:
        """验证通用参数"""
        # 时长验证（对于pixverse）
        if "duration" in params:
            duration = params["duration"]
            if not isinstance(duration, (int, float)) or duration <= 0:
                raise ValueError(f"duration 必须是正数，当前值: {duration}")
            
            if duration > 30:  # 最大30秒
                raise ValueError(f"duration 不能超过30秒，当前值: {duration}")
        
        # 图片URL验证（对于需要图片的模型）
        if "image" in params and params["image"]:
            image_url = params["image"]
            if not image_url.startswith(("http://", "https://")):
                raise ValueError("image URL必须以http://或https://开头")
        
        # 质量验证
        if "quality" in params:
            quality = params["quality"]
            valid_qualities = ["360p", "540p", "720p", "1080p"]
            if quality not in valid_qualities:
                raise ValueError(f"quality 必须是{valid_qualities}之一，当前值: {quality}")
    
    def get_model_examples(self, model: str) -> Dict[str, Any]:
        """获取模型的示例参数"""
        if model == "pixverse":
            return {
                "fantasy_scene": {
                    "prompt": "A magical forest with glowing mushrooms and fairy lights",
                    "quality": "1080p",
                    "duration": 5,
                    "aspect_ratio": "16:9",
                    "style": "fantasy"
                },
                "character_action": {
                    "prompt": "A robot dancing in a futuristic city",
                    "quality": "720p",
                    "duration": 8,
                    "aspect_ratio": "9:16",
                    "motion_mode": "smooth",
                    "style": "cyberpunk"
                },
                "social_media": {
                    "prompt": "Cute cat playing with yarn ball",
                    "quality": "1080p",
                    "duration": 5,
                    "aspect_ratio": "1:1",
                    "motion_mode": "smooth",
                    "style": "anime"
                }
            }
        elif model == "pia":
            return {
                "portrait_animation": {
                    "prompt": "Person smiling and nodding",
                    "image": "https://example.com/portrait.jpg",
                    "style": "realistic",
                    "motion_scale": 1,
                    "animation_length": 16
                },
                "cartoon_character": {
                    "prompt": "Cartoon character waving hello",
                    "image": "https://example.com/cartoon.jpg",
                    "style": "3d_cartoon",
                    "motion_scale": 2,
                    "guidance_scale": 8.0
                },
                "product_demo": {
                    "prompt": "Product rotating slowly showcasing all angles",
                    "image": "https://example.com/product.jpg",
                    "style": "realistic",
                    "motion_scale": 1,
                    "guidance_scale": 9.0,
                    "animation_length": 12
                }
            }
        else:
            return {}
    
    def get_generation_limits(self) -> Dict[str, Any]:
        """获取生成限制 - 从配置和服务层合并"""
        base_limits = super().get_generation_limits()
        
        # 添加服务层的额外限制
        service_limits = {
            "models": {
                "pixverse": {
                    "max_duration": 8,
                    "max_outputs_per_request": 10,
                    "recommended_duration": 5,
                    "supported_qualities": ["360p", "540p", "720p", "1080p"]
                },
                "pia": {
                    "max_duration": 24,
                    "max_outputs_per_request": 5,
                    "recommended_duration": 16,
                    "max_image_size": 1024
                }
            },
            "general": {
                "min_duration": 3,
                "max_concurrent_generations": 3,
                "estimated_time_per_second": 30.0
            }
        }
        
        return {**base_limits, **service_limits}