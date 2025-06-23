# src/application/services/assets/video_service.py - 修复版
from typing import Dict, Any, List, Optional
from src.application.services.assets.core.base_asset_service import BaseAssetService
from src.application.services.external.ai_service_factory import ai_service_factory
from src.schemas.enums.asset_enums import AssetTypeEnum, ModelProviderEnum
from src.infrastructure.decorators.retry import simple_retry


class VideoService(BaseAssetService):
    """视频处理服务 - 修复版"""
    
    def get_asset_type(self) -> AssetTypeEnum:
        return AssetTypeEnum.VIDEO
    
    def get_service_info(self) -> Dict[str, Any]:
        base_info = super().get_service_info()
        return {
            **base_info,
            "description": "视频处理服务 - 支持背景移除等功能",
            "model_capabilities": self._get_model_capabilities()
        }
    
    def _get_model_capabilities(self) -> Dict[str, Any]:
        """获取模型能力描述"""
        return {
            "background_removal": {
                "description": "智能视频背景移除和替换",
                "input_formats": ["mp4", "avi", "mov", "mkv", "webm"],
                "output_format": "mp4",
                "max_duration": 300,
                "max_file_size": "100MB",
                "features": ["smart_detection", "edge_refinement", "color_replacement", "batch_processing"],
                "best_for": ["video_conferencing", "content_creation", "professional_editing"]
            }
        }
    
    async def generate(
        self, 
        model: str, 
        generation_params: Dict[str, Any], 
        num_outputs: int = 1,
        provider: Optional[str] = None
    ) -> List[str]:
        """处理视频 - 使用基类的模型解析"""
        try:
            self.logger.info(f"开始处理视频: {model}", extra={
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
            
            self.logger.info(f"视频处理完成: {len(results)}个结果", extra={
                "model": model,
                "model_id": model_id,
                "provider": provider_name,
                "success_count": len(results)
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"视频处理失败: {str(e)}", extra={
                "model": model,
                "provider": provider,
                "error_type": type(e).__name__
            })
            raise
    
    def _preprocess_generation_params(self, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """预处理生成参数 - 在Service层设置默认值和验证"""
        processed_params = params.copy()
        
        # 根据不同模型进行参数预处理
        if model == "background_removal":
            self._apply_background_removal_defaults(processed_params)
        else:
            # 通用默认值
            self._apply_common_defaults(processed_params)
        
        # 验证参数
        self._validate_common_params(processed_params)
        
        return processed_params
    
    def _apply_background_removal_defaults(self, params: Dict[str, Any]) -> None:
        """应用背景移除模型的默认值"""
        # 验证必需参数
        if "video" not in params:
            raise ValueError("背景移除模型缺少必需参数: video")
        
        defaults = {
            "mode": "Normal"
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _apply_common_defaults(self, params: Dict[str, Any]) -> None:
        """应用通用默认值"""
        defaults = {
            "mode": "Normal",
            "output_format": "mp4"
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _validate_common_params(self, params: Dict[str, Any]) -> None:
        """验证通用参数"""
        # 验证视频URL格式
        if "video" in params:
            video_url = params["video"]
            if not video_url or not video_url.startswith(("http://", "https://")):
                raise ValueError("视频URL必须以http://或https://开头")
        
        # 验证处理模式
        if "mode" in params:
            mode = params["mode"]
            valid_modes = ["Fast", "Normal"]
            if mode not in valid_modes:
                raise ValueError(f"处理模式必须是{valid_modes}之一，当前值: {mode}")
        
        # 验证背景颜色格式（如果提供）
        if "background_color" in params and params["background_color"]:
            background_color = params["background_color"]
            if not self._is_valid_color(background_color):
                raise ValueError(f"背景颜色格式无效，应为十六进制格式如#FFFFFF，当前值: {background_color}")
    
    def _is_valid_color(self, color: str) -> bool:
        """验证颜色格式是否有效"""
        if not color.startswith("#"):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    async def remove_background(
        self, 
        video_url: str, 
        mode: str = "Normal", 
        background_color: Optional[str] = None,
        provider: Optional[str] = None
    ) -> str:
        """移除视频背景的便捷方法"""
        generation_params = {
            "video": video_url,
            "mode": mode
        }
        
        if background_color:
            generation_params["background_color"] = background_color
        
        results = await self.generate(
            model="background_removal",
            generation_params=generation_params,
            num_outputs=1,
            provider=provider
        )
        
        return results[0] if results else None
    
    def get_model_examples(self, model: str) -> Dict[str, Any]:
        """获取模型的示例参数"""
        if model == "background_removal":
            return {
                "portrait_video": {
                    "video": "https://example.com/portrait_video.mp4",
                    "mode": "Normal",
                    "description": "人物肖像视频背景移除"
                },
                "presentation_video": {
                    "video": "https://example.com/presentation.mp4",
                    "mode": "Fast",
                    "background_color": "#FFFFFF",
                    "description": "演示视频快速背景移除并替换为白色"
                },
                "green_screen_alternative": {
                    "video": "https://example.com/person_talking.mp4",
                    "mode": "Normal",
                    "background_color": "#00FF00",
                    "description": "生成绿幕效果，便于后期合成"
                },
                "transparent_background": {
                    "video": "https://example.com/dancer.mp4",
                    "mode": "Normal",
                    "description": "保持透明背景，便于叠加其他素材"
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
                "background_removal": {
                    "max_duration": 300,
                    "max_file_size_mb": 100,
                    "max_outputs_per_request": 5,
                    "supported_formats": ["mp4", "avi", "mov", "mkv", "webm"],
                    "output_format": "mp4"
                }
            },
            "general": {
                "max_concurrent_processing": 3,
                "estimated_time_multiplier": 2.0,  # 处理时间约为视频时长的2倍
                "supported_resolutions": ["720p", "1080p"],
                "max_resolution": "1920x1080"
            }
        }
        
        return {**base_limits, **service_limits}
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """获取支持的视频格式和规格"""
        return {
            "input_formats": {
                "supported": ["mp4", "avi", "mov", "mkv", "webm", "flv"],
                "recommended": "mp4",
                "codec_preferences": ["H.264", "H.265"]
            },
            "output_formats": {
                "supported": ["mp4", "webm"],
                "default": "mp4",
                "codec": "H.264"
            },
            "specifications": {
                "max_resolution": "1920x1080",
                "max_duration_seconds": 300,
                "max_file_size_mb": 100,
                "supported_frame_rates": [24, 25, 30, 60],
                "recommended_bitrate": "2-8 Mbps"
            },
            "processing_limits": {
                "max_concurrent_jobs": 3,
                "average_processing_time": "1-3x video duration",
                "queue_timeout": "15 minutes"
            }
        }