# src/schemas/dtos/request/multimedia_request.py
from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, Literal, Union
from src.schemas.dtos.request.asset_request import AssetGenRequest

# === Animation ===
class AnimationPixverseInput(BaseModel):
    """Pixverse动画生成输入参数"""
    
    prompt: str = Field(..., description="动画描述文本")
    image: Optional[str] = Field(None, description="可选的基础图片URL")
    last_frame_image: Optional[str] = Field(None, description="可选的最后帧图片URL")
    quality: str = Field("1080p", description="分辨率 (360p, 540p, 720p, 1080p)")
    duration: int = Field(5, description="动画时长(秒) (5, 8)")
    motion_mode: str = Field("normal", description="运动模式 (normal, smooth)")
    aspect_ratio: str = Field("16:9", description="宽高比 (16:9, 9:16, 1:1)")
    negative_prompt: Optional[str] = Field("", description="负面提示词")
    style: Optional[str] = Field(None, description="动画风格")
    effect: Optional[str] = Field(None, description="特效")
    seed: Optional[int] = Field(None, description="随机种子")
    
    @validator('quality')
    def validate_quality(cls, v):
        valid_qualities = ["360p", "540p", "720p", "1080p"]
        if v not in valid_qualities:
            raise ValueError(f"Invalid quality: {v}. Must be one of: {', '.join(valid_qualities)}")
        return v
    
    @validator('motion_mode')
    def validate_motion_mode(cls, v):
        valid_modes = ["normal", "smooth"]
        if v not in valid_modes:
            raise ValueError(f"Invalid motion mode: {v}. Must be one of: {', '.join(valid_modes)}")
        return v
    
    @validator('aspect_ratio')
    def validate_aspect_ratio(cls, v):
        valid_ratios = ["16:9", "9:16", "1:1"]
        if v not in valid_ratios:
            raise ValueError(f"Invalid aspect ratio: {v}. Must be one of: {', '.join(valid_ratios)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A knight fighting a dragon in a fantasy landscape",
                "quality": "1080p",
                "duration": 5,
                "motion_mode": "normal",
                "aspect_ratio": "16:9",
                "negative_prompt": "",
                "style": "None",
                "effect": "None"
            }
        }


class AnimationPiaInput(BaseModel):
    """PIA动画生成输入参数"""
    
    prompt: str = Field(..., description="动画描述文本")
    image: str = Field(..., description="基础图片URL")
    max_size: int = Field(512, ge=512, le=1024, description="最大尺寸(像素)")
    style: str = Field(..., description="动画风格 (3d_cartoon, realistic)")
    motion_scale: int = Field(1, ge=1, le=3, description="运动幅度")
    guidance_scale: float = Field(7.5, ge=1.0, le=20.0, description="引导强度")
    sampling_steps: int = Field(25, ge=10, le=100, description="采样步数")
    negative_prompt: str = Field("", description="负面提示词")
    animation_length: int = Field(16, ge=8, le=24, description="动画长度(秒)")
    ip_adapter_scale: float = Field(1.0, ge=0.0, le=1.0, description="IP适配器比例")
    seed: Optional[int] = Field(None, description="随机种子")
    
    @validator('image')
    def validate_image(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("Image URL must start with http:// or https://")
        return v
    
    @validator('style')
    def validate_style(cls, v):
        valid_styles = ["3d_cartoon", "realistic"]
        if v not in valid_styles:
            raise ValueError(f"Invalid style: {v}. Must be one of: {', '.join(valid_styles)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "1boy smiling",
                "max_size": 512,
                "image": "https://replicate.delivery/pbxt/KA4hkvNyViiiEafjSAKBKQO5yv3Bt6gtwyFXarsMnP8jlDYD/harry.png",
                "style": "3d_cartoon",
                "motion_scale": 1,
                "guidance_scale": 7.5,
                "sampling_steps": 25,
                "negative_prompt": "wrong white balance, dark, sketches,worst quality,low quality, deformed, distorted, disfigured, bad eyes, wrong lips, weird mouth, bad teeth, mutated hands and fingers, bad anatomy,wrong anatomy, amputation, extra limb, missing limb, floating,limbs, disconnected limbs, mutation, ugly, disgusting, bad_pictures, negative_hand-neg",
                "animation_length": 16,
                "ip_adapter_scale": 0
            }
        }


class AnimationGenRequest(AssetGenRequest):
    """动画生成请求"""
    model: Literal["pixverse", "pia"] = Field(..., description="动画模型 (pixverse, pia)")
    generation_params: Union[AnimationPixverseInput, AnimationPiaInput] = Field(
        ..., description="生成参数，取决于 model"
    )

    @model_validator(mode="after")
    def check_generation_param_match(self):
        if self.model == "pixverse" and not isinstance(self.generation_params, AnimationPixverseInput):
            raise ValueError("generation_params must be AnimationPixverseInput when model is 'pixverse'")
        if self.model == "pia" and not isinstance(self.generation_params, AnimationPiaInput):
            raise ValueError("generation_params must be AnimationPiaInput when model is 'pia'")
        return self

    class Config(AssetGenRequest.Config):
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Pixverse动画生成示例",
                    "description": "使用Pixverse模型生成动画",
                    "value": {
                        "provider": "replicate",
                        "model": "pixverse",
                        "num_outputs": 3,
                        "generation_params": AnimationPixverseInput.Config.json_schema_extra["example"]
                    }
                },
                {
                    "summary": "PIA动画生成示例",
                    "description": "使用PIA模型从图片生成动画",
                    "value": {
                        "provider": "replicate",
                        "model": "pia",
                        "num_outputs": 1,
                        "generation_params": AnimationPiaInput.Config.json_schema_extra["example"]
                    }
                }
            ]
        }

# === Audio ===
class AudioArdianfeInput(BaseModel):
    """Ardianfe音乐生成输入参数"""
    
    prompt: str = Field(..., description="音乐描述文本")
    duration: int = Field(8, ge=1, le=300, description="音乐时长(秒)")
    input_audio: Optional[str] = Field(None, description="可选的输入音频URL")
    top_k: int = Field(250, ge=1, le=500, description="Top-K采样参数")
    top_p: float = Field(0.0, ge=0.0, le=500.0, description="Top-P采样参数")
    temperature: float = Field(1.0, ge=0.1, le=2.0, description="采样温度")
    continuation: bool = Field(False, description="是否续写")
    continuation_start: int = Field(0, ge=0, description="续写起始时间(秒)")
    output_format: str = Field("wav", description="输出格式 (wav, mp3)")
    multi_band_diffusion: bool = Field(False, description="是否使用多频段扩散")
    normalization_strategy: str = Field("loudness", description="音量标准化策略")
    classifier_free_guidance: float = Field(3.0, ge=0.0, le=10.0, description="无分类器引导强度")
    seed: Optional[int] = Field(None, description="随机种子")
    
    @validator('output_format')
    def validate_output_format(cls, v):
        if v not in ["wav", "mp3"]:
            raise ValueError("Output format must be 'wav' or 'mp3'")
        return v
    
    @validator('normalization_strategy')
    def validate_normalization_strategy(cls, v):
        valid_strategies = ["loudness", "clip", "peak", "rms"]
        if v not in valid_strategies:
            raise ValueError(f"Invalid normalization strategy. Must be one of: {', '.join(valid_strategies)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "chill music with construction vibes sound behind, dominant in acoustic guitar and piano",
                "duration": 60,
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
        }


class AudioMetaInput(BaseModel):
    """Meta音乐生成输入参数"""
    
    prompt: str = Field(..., description="音乐描述文本")
    duration: int = Field(8, ge=1, le=600, description="音乐时长(秒)")
    input_audio: Optional[str] = Field(None, description="可选的输入音频URL")
    temperature: float = Field(1.0, ge=0.1, le=2.0, description="采样温度")
    top_k: int = Field(250, ge=0, description="Top-K采样参数")
    top_p: float = Field(0.0, ge=0.0, le=500.0, description="Top-P采样参数")
    continuation: bool = Field(False, description="是否续写")
    continuation_start: int = Field(0, ge=0, description="续写起始时间(秒)")
    model_version: str = Field("stereo-large", description="模型版本")
    output_format: str = Field("mp3", description="输出格式 (wav, mp3)")
    multi_band_diffusion: bool = Field(False, description="是否使用多频段扩散")
    normalization_strategy: str = Field("peak", description="音量标准化策略")
    classifier_free_guidance: float = Field(3.0, ge=1.0, le=10.0, description="无分类器引导强度")
    seed: Optional[int] = Field(None, description="随机种子")
    
    @validator('model_version')
    def validate_model_version(cls, v):
        valid_versions = ["stereo-melody-large", "stereo-large", "melody-large", "large"]
        if v not in valid_versions:
            raise ValueError(f"Invalid model version: {v}. Must be one of: {', '.join(valid_versions)}")
        return v
    
    @validator('output_format')
    def validate_output_format(cls, v):
        valid_formats = ["wav", "mp3"]
        if v not in valid_formats:
            raise ValueError(f"Invalid output format: {v}. Must be 'wav' or 'mp3'")
        return v
    
    @validator('normalization_strategy')
    def validate_normalization_strategy(cls, v):
        valid_strategies = ["peak", "clip", "loudness", "rms"]
        if v not in valid_strategies:
            raise ValueError(f"Invalid normalization strategy: {v}. Must be one of: {', '.join(valid_strategies)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Edo25 major g melodies that sound triumphant and cinematic. Leading up to a crescendo that resolves in a 9th harmonic",
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
        }


class AudioGenRequest(AssetGenRequest):
    """音乐生成请求"""
    model: Literal["ardianfe", "meta"] = Field(..., description="音乐模型 (ardianfe, meta)")
    generation_params: Union[AudioArdianfeInput, AudioMetaInput] = Field(
        ..., description="生成参数，取决于 model"
    )

    @model_validator(mode="after")
    def check_generation_param_match(self):
        if self.model == "ardianfe" and not isinstance(self.generation_params, AudioArdianfeInput):
            raise ValueError("generation_params must be AudioArdianfeInput when model is 'ardianfe'")
        if self.model == "meta" and not isinstance(self.generation_params, AudioMetaInput):
            raise ValueError("generation_params must be AudioMetaInput when model is 'meta'")
        return self

    class Config(AssetGenRequest.Config):
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Ardianfe音乐生成示例",
                    "description": "使用Ardianfe模型生成高质量立体声音乐",
                    "value": {
                        "provider": "replicate",
                        "model": "ardianfe",
                        "num_outputs": 2,
                        "generation_params": AudioArdianfeInput.Config.json_schema_extra["example"]
                    }
                },
                {
                    "summary": "Meta MusicGen示例",
                    "description": "使用Meta MusicGen快速生成音乐",
                    "value": {
                        "provider": "replicate",
                        "model": "meta",
                        "num_outputs": 3,
                        "generation_params": AudioMetaInput.Config.json_schema_extra["example"]
                    }
                }
            ]
        }

# === Video ===
class VideoBackgroundRemovalInput(BaseModel):
    """视频背景移除输入参数"""
    
    video: str = Field(..., description="待处理视频的URL")
    mode: Literal["Fast", "Normal"] = Field("Normal", description="处理模式 (Fast, Normal)")
    background_color: Optional[str] = Field(None, description="背景颜色替换 (如: #FFFFFF)")
    
    @validator('video')
    def validate_video_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("Video URL must start with http:// or https://")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "video": "https://example.com/video.mp4",
                "mode": "Normal",
                "background_color": "#FFFFFF"
            }
        }


class VideoGenRequest(AssetGenRequest):
    """视频处理请求"""
    model: Literal["background_removal"] = Field(..., description="视频处理模型 (background_removal)")
    generation_params: VideoBackgroundRemovalInput = Field(
        ..., description="生成参数，仅用于背景移除"
    )
    
    @model_validator(mode="after")
    def check_generation_param_match(self):
        if self.model == "background_removal" and not isinstance(self.generation_params, VideoBackgroundRemovalInput):
            raise ValueError("generation_params must be VideoBackgroundRemovalInput when model is 'background_removal'")
        return self

    class Config(AssetGenRequest.Config):
        json_schema_extra = {
            "examples": [
                {
                    "summary": "视频背景移除示例",
                    "description": "移除视频背景并替换为白色",
                    "value": {
                        "provider": "replicate",
                        "model": "background_removal",
                        "num_outputs": 1,
                        "generation_params": VideoBackgroundRemovalInput.Config.json_schema_extra["example"]
                    }
                },
                {
                    "summary": "快速背景移除示例",
                    "description": "快速模式移除背景，保持透明",
                    "value": {
                        "model": "background_removal",
                        "model": "background_removal",
                        "num_outputs": 1,
                        "generation_params": {
                            "video": "https://example.com/portrait_video.mp4",
                            "mode": "Fast"
                        }
                    }
                }
            ]
        }
