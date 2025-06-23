# src/application/services/assets/audio_service.py - 简化版
from typing import Dict, Any, List, Optional
from src.application.services.assets.core.base_asset_service import BaseAssetService
from src.application.services.external.ai_service_factory import ai_service_factory
from src.schemas.enums.asset_enums import AssetTypeEnum, ModelProviderEnum
from src.infrastructure.decorators.retry import simple_retry


class AudioService(BaseAssetService):
    """音乐生成服务 - 简化版"""
    
    def get_asset_type(self) -> AssetTypeEnum:
        return AssetTypeEnum.AUDIO
    
    def get_service_info(self) -> Dict[str, Any]:
        base_info = super().get_service_info()
        return {
            **base_info,
            "description": "音乐音效生成服务 - 支持Ardianfe和Meta模型",
            "model_capabilities": self._get_model_capabilities()
        }
    
    def _get_model_capabilities(self) -> Dict[str, Any]:
        """获取模型能力描述"""
        return {
            "ardianfe": {
                "description": "高质量立体声音乐生成",
                "max_duration": 300,
                "output_formats": ["wav", "mp3"],
                "features": ["stereo", "chord_progression", "construction_vibes"],
                "best_for": ["game_music", "ambient", "electronic"]
            },
            "meta": {
                "description": "Meta MusicGen快速音乐生成",
                "max_duration": 600,
                "output_formats": ["wav", "mp3"],
                "features": ["melody_generation", "multiple_versions", "continuation"],
                "best_for": ["general_music", "classical", "pop"]
            }
        }
    
    async def generate(
        self, 
        model: str, 
        generation_params: Dict[str, Any], 
        num_outputs: int = 1,
        provider: Optional[str] = None
    ) -> List[str]:
        """生成音乐 - 使用基类的模型解析"""
        try:
            self.logger.info(f"开始生成音乐: {model}", extra={
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
            
            # 预处理生成参数 - 在服务层添加默认值
            processed_params = self._preprocess_generation_params(model, generation_params)
            
            # 调用AI服务进行推理 - 传递正确的model_id字符串
            results = await ai_service.batch_inference(model_id, processed_params, num_outputs)
            
            self.logger.info(f"音乐生成完成: {len(results)}个结果", extra={
                "model": model,
                "model_id": model_id,
                "provider": provider_name,
                "success_count": len(results)
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"音乐生成失败: {str(e)}", extra={
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
        
        # 根据不同模型进行参数预处理和设置默认值
        if model == "ardianfe":
            self._apply_ardianfe_defaults(processed_params)
        elif model == "meta":
            self._apply_meta_defaults(processed_params)
        else:
            # 通用默认值
            self._apply_common_defaults(processed_params)
        
        # 验证参数
        self._validate_common_params(processed_params)
        
        return processed_params
    
    def _apply_ardianfe_defaults(self, params: Dict[str, Any]) -> None:
        """应用Ardianfe模型的默认值"""
        defaults = {
            "duration": 8,
            "top_k": 250,
            "top_p": 0.0,
            "temperature": 1.0,
            "continuation": False,
            "continuation_start": 0,
            "output_format": "wav",
            "multi_band_diffusion": False,
            "normalization_strategy": "loudness",
            "classifier_free_guidance": 3.0
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _apply_meta_defaults(self, params: Dict[str, Any]) -> None:
        """应用Meta模型的默认值"""
        defaults = {
            "duration": 8,
            "temperature": 1.0,
            "top_k": 250,
            "top_p": 0.0,
            "continuation": False,
            "continuation_start": 0,
            "model_version": "stereo-large",
            "output_format": "mp3",
            "multi_band_diffusion": False,
            "normalization_strategy": "peak",
            "classifier_free_guidance": 3.0
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _apply_common_defaults(self, params: Dict[str, Any]) -> None:
        """应用通用默认值"""
        defaults = {
            "duration": 8,
            "temperature": 1.0,
            "output_format": "wav"
        }
        
        for key, default_value in defaults.items():
            params.setdefault(key, default_value)
    
    def _validate_common_params(self, params: Dict[str, Any]) -> None:
        """验证通用参数"""
        # 时长验证
        duration = params.get("duration", 8)
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError(f"duration 必须是正数，当前值: {duration}")
        
        if duration > 600:  # 最大10分钟
            raise ValueError(f"duration 不能超过600秒，当前值: {duration}")
        
        # 温度验证
        temperature = params.get("temperature", 1.0)
        if not isinstance(temperature, (int, float)) or not (0.1 <= temperature <= 2.0):
            raise ValueError(f"temperature 必须在0.1-2.0之间，当前值: {temperature}")
        
        # 输出格式验证
        output_format = params.get("output_format", "wav")
        if output_format not in ["wav", "mp3"]:
            raise ValueError(f"output_format 必须是 'wav' 或 'mp3'，当前值: {output_format}")
    
    def get_model_examples(self, model: str) -> Dict[str, Any]:
        """获取模型的示例参数"""
        if model == "ardianfe":
            return {
                "game_background": {
                    "prompt": "Epic orchestral music for RPG game battle scene",
                    "duration": 60,
                    "temperature": 0.8,
                    "output_format": "wav"
                },
                "ambient_relaxing": {
                    "prompt": "Peaceful ambient music with nature sounds and soft piano",
                    "duration": 180,
                    "temperature": 0.6,
                    "classifier_free_guidance": 4.0
                },
                "electronic_upbeat": {
                    "prompt": "Energetic electronic dance music with heavy bass",
                    "duration": 30,
                    "temperature": 1.2,
                    "multi_band_diffusion": True
                }
            }
        elif model == "meta":
            return {
                "classical_piano": {
                    "prompt": "Beautiful classical piano melody in C major",
                    "duration": 45,
                    "model_version": "melody-large",
                    "classifier_free_guidance": 3.5
                },
                "upbeat_electronic": {
                    "prompt": "Upbeat electronic dance music with synthesizers",
                    "duration": 30,
                    "model_version": "stereo-large",
                    "temperature": 1.0
                },
                "cinematic_orchestral": {
                    "prompt": "Epic cinematic orchestral score with full orchestra",
                    "duration": 120,
                    "model_version": "stereo-melody-large",
                    "temperature": 0.9
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
                "ardianfe": {
                    "max_duration": 300,
                    "max_outputs_per_request": 10,
                    "recommended_duration": 60
                },
                "meta": {
                    "max_duration": 600,
                    "max_outputs_per_request": 20,
                    "recommended_duration": 30
                }
            },
            "general": {
                "min_duration": 1,
                "max_concurrent_generations": 5,
                "estimated_time_per_second": 2.0
            }
        }
        
        return {**base_limits, **service_limits}