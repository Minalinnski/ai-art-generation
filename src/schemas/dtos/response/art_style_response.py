# src/schemas/dtos/response/art_style_response.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.schemas.dtos.request.art_style_request import ArtStyleComponents


class ArtStylePresetInfo(BaseModel):
    """预设主题信息"""
    name: str = Field(..., description="主题名称")
    description: str = Field(..., description="主题描述") 
    color_palette: str = Field(..., description="色彩搭配")
    example_prompt: str = Field(..., description="示例提示词片段")

class ArtStyleResponse(BaseModel):
    """艺术风格生成响应 - 统一返回格式"""
    style_prompt: str = Field(..., description="生成的完整艺术风格提示词")
    mode: str = Field(..., description="使用的模式")
    
    # 统一的组件结构 - 所有模式都使用相同格式
    components: ArtStyleComponents = Field(..., description="风格组件详情")
    
    # 模式特定字段
    theme_name: Optional[str] = Field(None, description="主题名称(仅preset模式)")
    custom_input: Optional[str] = Field(None, description="原始输入(AI增强模式)")
    enhanced_result: Optional[str] = Field(None, description="GPT增强结果(AI增强模式)")
    reference_filename: Optional[str] = Field(None, description="参考文件名(reference_image模式)")
    analysis_result: Optional[str] = Field(None, description="图像分析结果(reference_image模式)")
    
    # AI处理信息
    ai_processing: Optional[Dict[str, Any]] = Field(None, description="AI处理详情(仅AI模式)")
    
    # 质量和错误信息
    quality_tags: str = Field(..., description="质量标签")
    error: Optional[str] = Field(None, description="错误信息(如有)")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "style_prompt": "fantasy art, medieval style, detailed illustration, rich gold, deep red, royal blue, ancient bronze, glowing magical effect, mystical aura, aged parchment, worn metal, mystical gems, warm torchlight, mysterious shadows, isolated on transparent background, centered design, game asset style, high quality, professional design",
                    "mode": "preset",
                    "components": {
                        "base_prompt": "fantasy art, medieval style, detailed illustration",
                        "color_palette": "rich gold, deep red, royal blue, ancient bronze",
                        "effects": "glowing magical effect, mystical aura",
                        "materials": "aged parchment, worn metal, mystical gems",
                        "lighting": "warm torchlight, mysterious shadows",
                        "description": "Medieval fantasy style with rich colors and magical elements"
                    },
                    "theme_name": "fantasy_medieval",
                    "quality_tags": "high quality, game asset style, professional design"
                },
                {
                    "style_prompt": "traditional Chinese festive style, vibrant red, imperial gold, auspicious crimson, golden glow, lantern light, festive sparkle, silk textures, lacquer finish, jade accents, warm lantern glow, celebratory brightness, isolated on transparent background, centered design, game asset style, high quality, professional design",
                    "mode": "custom_direct",
                    "components": {
                        "base_prompt": "traditional Chinese festive style",
                        "color_palette": "vibrant red, imperial gold, auspicious crimson",
                        "effects": "golden glow, lantern light, festive sparkle",
                        "materials": "silk textures, lacquer finish, jade accents",
                        "lighting": "warm lantern glow, celebratory brightness",
                        "description": "Traditional Chinese New Year celebration style"
                    },
                    "custom_input": "structured_components",
                    "quality_tags": "high quality, game asset style, professional design"
                },
                {
                    "style_prompt": "traditional Chinese festive style, vibrant red and gold colors, dragon and phoenix motifs, cloud patterns, lucky symbols, paper-cut art elements, lantern decorations, rich silk textures, ornate golden details, prosperity symbols, celebratory atmosphere, imperial palace aesthetics, traditional Chinese painting brushwork, lacquer finish effects, isolated on transparent background, centered design, game asset style, high quality",
                    "mode": "custom_ai_enhanced",
                    "components": {
                        "base_prompt": "traditional Chinese festive style, dragon and phoenix motifs",
                        "color_palette": "vibrant red and gold colors, auspicious crimson",
                        "effects": "golden glow, celebratory atmosphere, prosperity symbols",
                        "materials": "rich silk textures, ornate golden details, lacquer finish effects",
                        "lighting": "warm festive lighting, lantern glow"
                    },
                    "custom_input": "traditional Chinese festive style, vibrant red and gold colors",
                    "enhanced_result": "traditional Chinese festive style, vibrant red and gold colors, dragon and phoenix motifs, cloud patterns, lucky symbols, paper-cut art elements, lantern decorations, rich silk textures, ornate golden details, prosperity symbols, celebratory atmosphere, imperial palace aesthetics, traditional Chinese painting brushwork, lacquer finish effects",
                    "ai_processing": {
                        "parsed_components": True,
                        "enhanced_prompt": True,
                        "model_used": "gpt-4o"
                    },
                    "quality_tags": "high quality, game asset style, professional design"
                }
            ]
        }

class ArtStylePresetsResponse(BaseModel):
    """艺术风格预设列表响应"""
    available_presets: List[str] = Field(..., description="可用预设列表")
    preset_details: Dict[str, ArtStylePresetInfo] = Field(..., description="预设详情")
    total_count: int = Field(..., description="预设总数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "available_presets": ["fantasy_medieval", "cyberpunk_neon", "steampunk_bronze"],
                "preset_details": {
                    "fantasy_medieval": {
                        "name": "Fantasy Medieval",
                        "description": "Medieval fantasy style with rich colors and magical elements",
                        "color_palette": "rich gold, deep red, royal blue, ancient bronze",
                        "example_prompt": "fantasy art, medieval style, rich gold, deep red..."
                    }
                },
                "total_count": 3
            }
        }