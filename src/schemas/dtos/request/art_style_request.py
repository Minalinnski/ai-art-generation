# src/schemas/dtos/request/art_style_request.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class ArtStyleMode(str, Enum):
    """艺术风格模式"""
    PRESET = "preset"                    # 预设主题 (非AI)
    CUSTOM_DIRECT = "custom_direct"      # 直接使用自定义组件 (非AI)
    CUSTOM_AI_ENHANCED = "custom_ai_enhanced"  # AI增强自定义提示词 (AI)
    REFERENCE_IMAGE = "reference_image"  # 参考图像分析 (AI)

class ArtStyleComponents(BaseModel):
    """艺术风格组件 - 统一的风格数据格式"""
    base_prompt: str = Field(..., description="基础艺术风格描述")
    color_palette: Optional[str] = Field(None, description="色彩搭配")
    effects: Optional[str] = Field(None, description="视觉效果")
    materials: Optional[str] = Field(None, description="材质质感")
    lighting: Optional[str] = Field(None, description="光照效果")
    description: Optional[str] = Field(None, description="风格描述说明")
    
    @validator('base_prompt')
    def validate_base_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('base_prompt不能为空')
        return v.strip()

# === 4个不同的请求DTO ===

class PresetStyleRequest(BaseModel):
    """预设风格请求 (非AI接口)"""
    preset_theme: str = Field(..., description="预设主题名称")
    
    class Config:
        json_schema_extra = {
            "example": {
                "preset_theme": "fantasy_medieval"
            }
        }

class CustomDirectStyleRequest(BaseModel):
    """直接自定义风格请求 (非AI接口)"""
    style_components: ArtStyleComponents = Field(..., description="自定义风格组件")
    
    class Config:
        json_schema_extra = {
            "example": {
                "style_components": {
                    "base_prompt": "traditional Chinese festive style",
                    "color_palette": "vibrant red, imperial gold, auspicious crimson",
                    "effects": "golden glow, lantern light, festive sparkle",
                    "materials": "silk textures, lacquer finish, jade accents",
                    "lighting": "warm lantern glow, celebratory brightness",
                    "description": "Traditional Chinese New Year celebration style"
                }
            }
        }

class CustomAIEnhancedStyleRequest(BaseModel):
    """AI增强自定义风格请求 (AI接口)"""
    custom_prompt: str = Field(..., description="简单自定义提示词，将被AI解析和增强")
    provider: str = Field(default="openai", description="AI提供商")
    model: str = Field(default="gpt-4o", description="AI模型")
    
    @validator('custom_prompt')
    def validate_custom_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError('custom_prompt不能为空')
        if len(v.strip()) > 500:
            raise ValueError('custom_prompt长度不能超过500字符')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "custom_prompt": "traditional Chinese festive style, vibrant red and gold colors, dragon and phoenix motifs",
                "provider": "openai",
                "model": "gpt-4o"
            }
        }

class ReferenceImageStyleRequest(BaseModel):
    """参考图像风格请求 (AI接口) - 用于文件上传时的form参数"""
    provider: str = Field(default="openai", description="AI提供商")
    model: str = Field(default="gpt-4o", description="AI模型 (需要支持图像分析)")
    max_images: int = Field(default=3, ge=1, le=10, description="最大图片数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "model": "gpt-4o",
                "max_images": 3
            }
        }

# 保留通用的ArtStyleRequest用于验证接口
class ArtStyleRequest(BaseModel):
    """通用艺术风格请求 (仅用于验证接口)"""
    mode: ArtStyleMode = Field(..., description="艺术风格模式")
    preset_theme: Optional[str] = Field(None, description="预设主题名称")
    custom_prompt: Optional[str] = Field(None, description="简单自定义提示词")
    style_components: Optional[ArtStyleComponents] = Field(None, description="风格组件")
    provider: Optional[str] = Field("openai", description="AI提供商 (仅AI模式)")
    model: Optional[str] = Field("gpt-4o", description="AI模型 (仅AI模式)")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "mode": "preset",
                    "preset_theme": "fantasy_medieval"
                },
                {
                    "mode": "custom_direct",
                    "style_components": {
                        "base_prompt": "traditional Chinese festive style",
                        "color_palette": "vibrant red, imperial gold",
                        "effects": "golden glow, festive sparkle",
                        "description": "Chinese New Year style"
                    }
                },
                {
                    "mode": "custom_ai_enhanced", 
                    "custom_prompt": "traditional Chinese festive style",
                    "provider": "openai",
                    "model": "gpt-4o"
                },
                {
                    "mode": "reference_image",
                    "provider": "openai",
                    "model": "gpt-4o"
                }
            ]
        }