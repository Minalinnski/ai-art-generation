# src/api/routers/v1/assets/art_style_router.py
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Body, Path, Query, Form
from src.application.handlers.assets.art_style_handler import get_art_style_handler, ArtStyleHandler
from src.schemas.dtos.request.art_style_request import (
    ArtStyleRequest, 
    PresetStyleRequest, 
    CustomDirectStyleRequest, 
    CustomAIEnhancedStyleRequest,
    ReferenceImageStyleRequest
)
from src.schemas.dtos.response.base_response import BaseResponse

router = APIRouter(prefix="/art-style", tags=["Art Style Generation"])

# ================================================================
# 非AI接口 - 快速直接处理
# ================================================================

@router.post("/preset", summary="预设风格生成 (非AI)")
async def generate_preset_style(
    request: PresetStyleRequest = Body(..., description="预设风格请求"),
    handler: ArtStyleHandler = Depends(get_art_style_handler)
):
    """
    使用预设主题生成艺术风格提示词 (非AI接口)
    
    **特点：**
    - 快速响应，无AI调用
    - 使用预定义的风格模板
    - 稳定一致的输出
    
    **支持的预设主题：**
    - fantasy_medieval: 中世纪奇幻风格
    - cyberpunk_neon: 赛博朋克霓虹风格  
    - steampunk_bronze: 蒸汽朋克青铜风格
    - cosmic_space: 宇宙太空风格
    - nature_organic: 自然有机风格
    - dark_gothic: 暗黑哥特风格
    
    **响应时间：** <100ms
    
    Request body example:
    ```json
    {
        "preset_theme": "fantasy_medieval"
    }
    ```
    """
    try:
        result = await handler.handle_preset_style_generation(request.preset_theme)
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("PRESET_STYLE_ERROR", str(e))

@router.post("/custom-direct", summary="直接自定义风格生成 (非AI)")
async def generate_custom_direct_style(
    request: CustomDirectStyleRequest = Body(..., description="直接自定义风格请求"),
    handler: ArtStyleHandler = Depends(get_art_style_handler)
):
    """
    使用结构化组件直接生成艺术风格 (非AI接口)
    
    **特点：**
    - 快速响应，无AI调用
    - 用户完全控制风格组件
    - 支持精确的风格定制
    
    **组件说明：**
    - base_prompt: 基础艺术风格描述 (必需)
    - color_palette: 色彩搭配
    - effects: 视觉效果
    - materials: 材质质感
    - lighting: 光照效果
    - description: 风格描述说明
    
    **响应时间：** <100ms
    
    Request body example:
    ```json
    {
        "style_components": {
            "base_prompt": "traditional Chinese festive style",
            "color_palette": "vibrant red, imperial gold, auspicious crimson",
            "effects": "golden glow, lantern light, festive sparkle",
            "materials": "silk textures, lacquer finish, jade accents",
            "lighting": "warm lantern glow, celebratory brightness",
            "description": "Traditional Chinese New Year celebration style"
        }
    }
    ```
    """
    try:
        result = await handler.handle_custom_direct_style_generation(request.style_components)
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("CUSTOM_DIRECT_STYLE_ERROR", str(e))

# ================================================================
# AI接口 - 智能处理和分析
# ================================================================

@router.post("/custom-ai-enhanced", summary="AI增强自定义风格生成 (AI)")
async def generate_custom_ai_enhanced_style(
    request: CustomAIEnhancedStyleRequest = Body(..., description="AI增强自定义风格请求"),
    handler: ArtStyleHandler = Depends(get_art_style_handler)
):
    """
    使用AI增强自定义风格生成 (AI接口)
    
    **特点：**
    - 使用AI服务进行智能解析和增强
    - 自动将简单描述转换为结构化组件
    - 增强提示词的专业性和完整性
    
    **AI处理流程：**
    1. 验证AI服务和模型可用性
    2. 解析简单提示词为结构化组件
    3. 增强和优化艺术风格描述
    4. 生成专业的图像生成提示词
    
    **支持的AI模型：**
    - OpenAI: gpt-4o, gpt-4, gpt-4-turbo, gpt-3.5-turbo
    - 要求: 具备text_generation能力
    
    **响应时间：** 2-5秒 (包含AI处理时间)
    
    Request body example:
    ```json
    {
        "custom_prompt": "traditional Chinese festive style, vibrant red and gold colors, dragon and phoenix motifs",
        "provider": "openai",
        "model": "gpt-4o"
    }
    ```
    
    **AI处理详情：**
    - 解析组件: base_prompt, color_palette, effects, materials, lighting
    - 增强描述: 添加专业术语和细节
    - 优化格式: 适合图像生成的提示词格式
    """
    try:
        result = await handler.handle_custom_ai_enhanced_style_generation(
            request.custom_prompt, 
            request.provider, 
            request.model
        )
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("CUSTOM_AI_ENHANCED_STYLE_ERROR", str(e))

@router.post("/reference-image", summary="参考图像风格分析 (AI)")
async def generate_reference_image_style(
    reference_images: List[UploadFile] = File(..., description="参考图像文件列表（1-10张）"),
    provider: str = Form(default="openai", description="AI提供商"),
    model: str = Form(default="gpt-4o", description="AI模型 (需要支持图像分析)"),
    max_images: int = Form(default=3, ge=1, le=10, description="最大处理图片数量"),
    handler: ArtStyleHandler = Depends(get_art_style_handler)
):
    """
    通过上传参考图像生成艺术风格 (AI接口) - 支持多图片
    
    **特点：**
    - 使用AI服务进行图像视觉分析
    - 支持单张或多张图片分析
    - 多图片时会生成统一的风格描述
    - 自动提取艺术风格特征
    - 生成可复制的风格描述
    
    **AI处理流程：**
    1. 验证AI服务和模型可用性
    2. 上传所有图片到临时S3存储
    3. 分析图像的艺术风格特征（支持多图综合分析）
    4. 提取色彩、光照、材质等元素
    5. 生成结构化的风格组件
    6. 构建专业的图像生成提示词
    7. 自动清理临时图片
    
    **支持的AI模型：**
    - OpenAI: gpt-4o (推荐，支持最多10张图片)
    - OpenAI: gpt-4-turbo (支持最多3张图片)
    - 要求: 具备image_analysis或multimodal能力
    
    **文件要求：**
    - 支持格式: JPEG, PNG, WebP, BMP
    - 文件大小: 每张最大10MB
    - 图片数量: 1-10张（根据max_images参数限制）
    - 建议分辨率: 512x512 以上
    
    **Form参数：**
    - reference_images: 图像文件列表 (required, 1-10张)
    - provider: AI提供商 (default: "openai")
    - model: AI模型 (default: "gpt-4o")
    - max_images: 最大处理数量 (default: 3, range: 1-10)
    
    **响应时间：** 
    - 单图片: 3-8秒
    - 多图片: 5-15秒 (取决于图片数量)
    
    **使用建议：**
    - 单张图片：适合精确的风格复制
    - 多张图片：适合风格融合和综合分析
    - gpt-4o模型处理多图片效果最佳
    """
    try:
        result = await handler.handle_reference_image_style_generation(
            reference_images, 
            provider, 
            model,
            max_images
        )
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("REFERENCE_IMAGE_STYLE_ERROR", str(e))

# ================================================================
# 辅助功能接口
# ================================================================

@router.get("/presets", summary="获取可用预设主题")
async def get_available_presets(
    handler: ArtStyleHandler = Depends(get_art_style_handler)
):
    """
    获取所有可用的预设艺术风格主题
    
    返回预设主题列表及其详细信息，包括：
    - 主题名称和描述
    - 色彩搭配
    - 示例提示词片段
    """
    try:
        result = await handler.handle_get_available_presets()
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("GET_PRESETS_ERROR", str(e))

@router.get("/presets/{preset_theme}", summary="获取特定预设主题信息")
async def get_preset_info(
    preset_theme: str = Path(..., description="预设主题名称"),
    handler: ArtStyleHandler = Depends(get_art_style_handler)
):
    """
    获取特定预设主题的详细信息
    
    包括完整的风格配置、组件说明和示例提示词。
    """
    try:
        result = await handler.handle_get_preset_info(preset_theme)
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("GET_PRESET_INFO_ERROR", str(e))

@router.post("/validate", summary="验证艺术风格请求")
async def validate_style_request(
    request: ArtStyleRequest = Body(..., description="艺术风格请求"),
    handler: ArtStyleHandler = Depends(get_art_style_handler)
):
    """
    验证艺术风格请求的有效性
    
    **功能：**
    - 检查请求参数是否符合要求
    - 推荐最适合的接口
    - 返回验证结果和可能的警告
    - 提供接口使用建议
    
    **返回信息：**
    - 验证结果: valid/invalid
    - 错误信息: 具体的参数问题
    - 警告信息: 优化建议
    - 接口推荐: 建议使用的具体接口
    """
    try:
        result = await handler.handle_validate_style_request(request)
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("VALIDATION_ERROR", str(e))

@router.get("/health", summary="艺术风格服务健康检查")
async def health_check():
    """艺术风格服务健康检查"""
    return BaseResponse.success_response({
        "service": "art_style_generation",
        "status": "healthy",
        "version": "2.0.0",
        "supported_interfaces": {
            "non_ai": {
                "preset": "POST /art-style/preset",
                "custom_direct": "POST /art-style/custom-direct"
            },
            "ai_powered": {
                "custom_ai_enhanced": "POST /art-style/custom-ai-enhanced",
                "reference_image": "POST /art-style/reference-image"
            }
        },
        "utilities": {
            "get_presets": "GET /art-style/presets",
            "get_preset_info": "GET /art-style/presets/{preset_theme}",
            "validate": "POST /art-style/validate",
            "health": "GET /art-style/health"
        },
        "capabilities": [
            "preset_style_themes",
            "direct_component_assembly", 
            "ai_prompt_enhancement",
            "ai_image_analysis",
            "multi_image_analysis",
            "unified_component_format"
        ],
        "ai_models": {
            "text_processing": "gpt-4o",
            "image_analysis": "gpt-4o"
        },
        "performance": {
            "non_ai_response_time": "<100ms",
            "ai_text_processing": "2-5s",
            "ai_image_analysis": "3-8s"
        }
    })

# ================================================================
# API使用说明和示例
# ================================================================

"""
艺术风格API使用指南 v2.0

## 4个核心接口分类

### 非AI接口 (快速响应)
1. **预设风格**: POST /art-style/preset
   - 特点: 极快响应 (<100ms)
   - 适用: 快速原型、标准化风格
   - 输入: preset_theme
   - 示例: {"preset_theme": "fantasy_medieval"}
   
2. **直接自定义**: POST /art-style/custom-direct  
   - 特点: 极快响应 (<100ms)
   - 适用: 精确控制、完全定制
   - 输入: ArtStyleComponents结构
   - 示例: {"style_components": {...}}

### AI接口 (智能处理)
3. **AI增强自定义**: POST /art-style/custom-ai-enhanced
   - 特点: 智能增强 (2-5秒)
   - 适用: 提示词优化、专业增强
   - 输入: 简单文本描述
   - 示例: {"custom_prompt": "中国传统风格"}
   
4. **参考图像分析**: POST /art-style/reference-image
   - 特点: 图像分析 (3-8秒)
   - 适用: 风格复制、视觉参考
   - 输入: 图像文件
   - 格式: multipart/form-data

## 统一输出格式
所有接口都返回包含ArtStyleComponents的统一结构:
```json
{
  "success": true,
  "data": {
    "style_prompt": "完整的生成提示词...",
    "mode": "使用的模式",
    "components": {
      "base_prompt": "基础风格描述",
      "color_palette": "色彩搭配", 
      "effects": "视觉效果",
      "materials": "材质质感",
      "lighting": "光照效果",
      "description": "风格说明"
    },
    "quality_tags": "质量标签",
    "ai_processing": {...}  // 仅AI接口
  }
}
```

## 选择建议
- **快速原型**: 使用 /preset
- **精确控制**: 使用 /custom-direct
- **智能优化**: 使用 /custom-ai-enhanced  
- **风格复制**: 使用 /reference-image

## 验证工具
使用 POST /art-style/validate 来：
- 验证请求格式
- 获取接口推荐
- 查看优化建议

## 性能对比
| 接口 | 响应时间 | AI调用 | 适用场景 |
|------|----------|--------|----------|
| preset | <100ms | ❌ | 快速原型 |
| custom-direct | <100ms | ❌ | 精确控制 |
| custom-ai-enhanced | 2-5s | ✅ | 智能优化 |
| reference-image | 3-8s | ✅ | 风格复制 |

## 完整使用流程示例

1. **查看可用预设**:
   GET /art-style/presets

2. **选择合适接口**:
   - 有预设主题 → POST /art-style/preset
   - 精确定制 → POST /art-style/custom-direct
   - 简单描述 → POST /art-style/custom-ai-enhanced
   - 有参考图 → POST /art-style/reference-image

3. **验证请求** (可选):
   POST /art-style/validate

4. **生成风格**:
   调用对应的生成接口

5. **使用结果**:
   获得的style_prompt可直接用于图像生成API
"""