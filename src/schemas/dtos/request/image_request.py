# src/schemas/dtos/request/image_request.py
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

# 导入Art Style相关的DTO
from src.schemas.dtos.request.art_style_request import (
    ArtStyleMode,
    PresetStyleRequest,
    CustomDirectStyleRequest, 
    CustomAIEnhancedStyleRequest,
    ReferenceImageStyleRequest
)

class ImageGenerationMode(str, Enum):
    """图像生成模式"""
    PROMPT_ONLY = "prompt_only"           # 仅使用提示词
    REFERENCE_ASSETS = "reference_assets" # 使用资产参考文件

class ImageAssetItem(BaseModel):
    """统一的图像资产元件格式"""
    filename: str = Field(..., description="文件名/ID，最简短且唯一")
    description: str = Field(..., description="描述，用于注入prompt，比单词更有信息量")
    count: int = Field(default=1, ge=1, le=10, description="生成数量")
    resolution: Optional[str] = Field(None, description="分辨率，可覆盖默认设置", pattern=r'^\d+x\d+$')
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('filename不能为空')
        # 简单的文件名验证，避免特殊字符
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v.strip()):
            raise ValueError('filename只能包含字母、数字、下划线和连字符')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('description不能为空')
        return v.strip()

# Art Style统一包装器
class ArtStyleConfig(BaseModel):
    """艺术风格配置 - 支持4种模式"""
    mode: ArtStyleMode = Field(..., description="艺术风格模式")
    
    # 预设模式
    preset_theme: Optional[str] = Field(None, description="预设主题名称")
    
    # 直接自定义模式 (非AI)
    style_components: Optional[Dict[str, Any]] = Field(None, description="风格组件")
    
    # AI增强模式
    custom_prompt: Optional[str] = Field(None, description="简单自定义提示词")
    ai_provider: Optional[str] = Field("openai", description="AI提供商")
    ai_model: Optional[str] = Field("gpt-4o", description="AI模型")
    
    @model_validator(mode='after')
    def validate_mode_requirements(self):
        """验证模式特定的要求"""
        if self.mode == ArtStyleMode.PRESET and not self.preset_theme:
            raise ValueError('预设模式需要提供preset_theme')
        
        if self.mode == ArtStyleMode.CUSTOM_DIRECT and not self.style_components:
            raise ValueError('直接自定义模式需要提供style_components')
        
        if self.mode == ArtStyleMode.CUSTOM_AI_ENHANCED and not self.custom_prompt:
            raise ValueError('AI增强模式需要提供custom_prompt')
        
        return self

# 保持原有的两层结构参数类，但内容改为新的元件格式
class SymbolsGenerationInput(BaseModel):
    """符号生成输入参数"""
    # 艺术风格配置 (必需)
    art_style: ArtStyleConfig = Field(..., description="艺术风格配置")
    
    # 两层结构 - 改为元件列表
    base_symbols: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="基础符号配置")
    special_symbols: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="特殊符号配置")
    
    # 自定义内容
    custom_content: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="自定义内容")
    
    # 默认分辨率
    default_resolution: str = Field(default="1024x1024", description="默认生成分辨率")
    
    @model_validator(mode='after')
    def validate_at_least_one_content(self):
        """至少需要有一个内容配置"""
        if not any([self.base_symbols, self.special_symbols, self.custom_content]):
            raise ValueError("至少需要提供base_symbols、special_symbols或custom_content之一")
        return self

class UIGenerationInput(BaseModel):
    """UI生成输入参数"""
    # 艺术风格配置 (必需)
    art_style: ArtStyleConfig = Field(..., description="艺术风格配置")
    
    # UI两层结构
    buttons: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="按钮配置")
    panels: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="面板配置")
    
    # 自定义UI内容
    custom_content: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="自定义UI内容")
    
    # 默认分辨率
    default_resolution: str = Field(default="1024x1024", description="默认生成分辨率")
    
    @model_validator(mode='after')
    def validate_at_least_one_content(self):
        """至少需要有一个内容配置"""
        if not any([self.buttons, self.panels, self.custom_content]):
            raise ValueError("至少需要提供buttons、panels或custom_content之一")
        return self

class BackgroundsGenerationInput(BaseModel):
    """背景生成输入参数"""
    # 艺术风格配置 (必需)
    art_style: ArtStyleConfig = Field(..., description="艺术风格配置")
    
    # 背景两层结构
    background_set: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="游戏场景配置")
    
    # 自定义背景内容
    custom_content: Optional[Dict[str, List[ImageAssetItem]]] = Field(None, description="自定义背景内容")
    
    # 默认分辨率
    default_resolution: str = Field(default="1920x1080", description="默认生成分辨率")
    
    @model_validator(mode='after')
    def validate_at_least_one_content(self):
        """至少需要有一个内容配置"""
        if not any([self.background_set, self.custom_content]):
            raise ValueError("至少需要提供background_set或custom_content之一")
        return self

# 统一的图像生成请求DTO
class ImageGenRequest(BaseModel):
    """单模块图像生成请求"""
    module: str = Field(..., description="模块类型：symbols/ui/backgrounds")
    model: str = Field(..., description="模型别名")
    provider: Optional[str] = Field(None, description="AI提供商")
    generation_mode: ImageGenerationMode = Field(default=ImageGenerationMode.PROMPT_ONLY)
    
    # 生成参数 - 根据模块类型使用不同的Input类
    generation_params: Union[SymbolsGenerationInput, UIGenerationInput, BackgroundsGenerationInput] = Field(
        ..., description="生成参数"
    )
    
    @model_validator(mode='after')
    def validate_params_by_module(self):
        """根据模块验证参数类型"""
        module = self.module
        if module == 'symbols' and not isinstance(self.generation_params, SymbolsGenerationInput):
            raise ValueError("symbols模块需要SymbolsGenerationInput类型参数")
        elif module == 'ui' and not isinstance(self.generation_params, UIGenerationInput):
            raise ValueError("ui模块需要UIGenerationInput类型参数")
        elif module == 'backgrounds' and not isinstance(self.generation_params, BackgroundsGenerationInput):
            raise ValueError("backgrounds模块需要BackgroundsGenerationInput类型参数")
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "module": "symbols",
                "model": "gpt_image_1",
                "generation_mode": "prompt_only",
                "generation_params": {
                    "art_style": {
                        "mode": "preset",
                        "preset_theme": "fantasy_medieval"
                    },
                    "base_symbols": {
                        "low_value": [
                            {
                                "filename": "heart_ace",
                                "description": "Ace of Hearts card symbol with ornate medieval design",
                                "count": 2,
                                "resolution": "512x512"
                            },
                            {
                                "filename": "spade_king", 
                                "description": "King of Spades with royal crown and medieval armor",
                                "count": 1
                            }
                        ]
                    },
                    "special_symbols": {
                        "wild": [
                            {
                                "filename": "dragon_wild",
                                "description": "Mystical dragon wild symbol with magical aura and glowing effects",
                                "count": 3,
                                "resolution": "1024x1024"
                            }
                        ]
                    }
                }
            }
        }
    }

# 完整游戏生成请求DTO
class GlobalConfig(BaseModel):
    """全局配置"""
    # 全局艺术风格 (会被模块级覆盖)
    global_art_style: ArtStyleConfig = Field(..., description="全局艺术风格配置")
    
    model: str = Field(default="gpt_image_1", description="默认模型")
    provider: Optional[str] = Field(None, description="默认AI提供商")
    generation_mode: ImageGenerationMode = Field(default=ImageGenerationMode.PROMPT_ONLY)

class CompleteGameGenRequest(BaseModel):
    """完整游戏资产生成请求"""
    global_config: GlobalConfig = Field(..., description="全局配置")
    modules: Dict[str, Union[SymbolsGenerationInput, UIGenerationInput, BackgroundsGenerationInput]] = Field(
        ..., description="各模块配置，key为模块名(symbols/ui/backgrounds)"
    )
    
    @model_validator(mode='after')
    def validate_module_configs(self):
        """验证模块配置类型"""
        valid_modules = {
            "symbols": SymbolsGenerationInput, 
            "ui": UIGenerationInput, 
            "backgrounds": BackgroundsGenerationInput
        }
        
        for module_name, config in self.modules.items():
            if module_name not in valid_modules:
                raise ValueError(f"不支持的模块: {module_name}")
            
            expected_type = valid_modules[module_name]
            if not isinstance(config, expected_type):
                raise ValueError(f"模块 {module_name} 需要 {expected_type.__name__} 类型配置")
        
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "global_config": {
                    "global_art_style": {
                        "mode": "preset",
                        "preset_theme": "fantasy_medieval"
                    },
                    "model": "gpt_image_1",
                    "generation_mode": "prompt_only"
                },
                "modules": {
                    "symbols": {
                        "art_style": {
                            "mode": "custom_ai_enhanced",
                            "custom_prompt": "Epic fantasy symbols with mystical energy",
                            "ai_provider": "openai",
                            "ai_model": "gpt-4o"
                        },
                        "base_symbols": {
                            "low_value": [
                                {
                                    "filename": "ace_hearts",
                                    "description": "Ornate Ace of Hearts with royal design",
                                    "count": 1
                                }
                            ]
                        }
                    },
                    "ui": {
                        "art_style": {
                            "mode": "preset", 
                            "preset_theme": "fantasy_medieval"
                        },
                        "buttons": {
                            "main_controls": [
                                {
                                    "filename": "spin_btn",
                                    "description": "Medieval style spin button with magical glow",
                                    "count": 1
                                }
                            ]
                        }
                    }
                }
            }
        }
    }