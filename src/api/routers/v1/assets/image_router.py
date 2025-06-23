# src/api/routers/v1/assets/image_router.py (重构版 - 集成Art Style)
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Body
from src.application.handlers.assets.image_handler import get_image_handler, ImageHandler
from src.schemas.dtos.response.base_response import BaseResponse

router = APIRouter(prefix="/image", tags=["Image Generation"])

# ================================================================
# JSON 模式路由 - 用于 prompt_only 模式
# ================================================================

@router.post("/{module}/generate", summary="单模块图像生成 (JSON模式)")
async def generate_single_module_json(
    module: str,
    model: str = Body(..., description="模型别名"),
    generation_mode: str = Body(default="prompt_only", description="生成模式"),
    generation_params: Dict[str, Any] = Body(..., description="生成参数"),
    provider: Optional[str] = Body(None, description="AI提供商"),
    handler: ImageHandler = Depends(get_image_handler)
):
    """
    单模块生成 - JSON模式，仅支持prompt_only
    
    集成了Art Style模块，支持4种艺术风格模式：
    - preset: 预设主题风格
    - custom_direct: 直接自定义风格组件
    - custom_ai_enhanced: AI增强自定义风格
    - reference_image: 参考图像分析（需要使用文件上传接口）
    
    Request body example:
    {
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
                        "filename": "ace_hearts",
                        "description": "Ornate Ace of Hearts with royal medieval design",
                        "count": 2,
                        "resolution": "512x512"
                    }
                ]
            },
            "special_symbols": {
                "wild": [
                    {
                        "filename": "dragon_wild",
                        "description": "Mystical dragon wild symbol with magical aura",
                        "count": 1
                    }
                ]
            }
        },
        "provider": "openai"
    }
    
    新的元件格式说明：
    - filename: 文件名/ID，简短且唯一
    - description: 详细描述，用于提示词生成
    - count: 生成数量（每个元件可单独设置）
    - resolution: 分辨率（可选，覆盖默认设置）
    """
    if generation_mode != "prompt_only":
        return BaseResponse.error_response(
            "INVALID_MODE", 
            "此接口仅支持prompt_only模式。如需上传文件，请使用对应的文件上传接口"
        )
    
    try:
        result = await handler.handle_module_generation_json(
            module=module,
            model=model,
            generation_mode=generation_mode,
            generation_params=generation_params,
            provider=provider
        )
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("GENERATION_ERROR", str(e))

@router.post("/generate-complete", summary="完整游戏资产生成 (JSON模式)")
async def generate_complete_game_json(
    global_config: Dict[str, Any] = Body(..., description="全局配置"),
    modules: Dict[str, Any] = Body(..., description="各模块配置"),
    handler: ImageHandler = Depends(get_image_handler)
):
    """
    完整游戏资产生成 - JSON模式，仅支持prompt_only
    
    支持全局艺术风格配置，各模块可以继承或覆盖全局风格。
    
    Request body example:
    {
        "global_config": {
            "global_art_style": {
                "mode": "preset",
                "preset_theme": "fantasy_medieval"
            },
            "model": "gpt_image_1",
            "generation_mode": "prompt_only",
            "provider": "openai"
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
    """
    if global_config.get("generation_mode") != "prompt_only":
        return BaseResponse.error_response(
            "INVALID_MODE", 
            "此接口仅支持prompt_only模式。如需上传文件，请使用对应的文件上传接口"
        )
    
    try:
        result = await handler.handle_complete_game_generation_json(
            global_config=global_config,
            modules_config=modules
        )
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("GENERATION_ERROR", str(e))

# ================================================================
# 文件上传模式路由 - 用于 reference_assets 和艺术风格参考图
# ================================================================

@router.post("/{module}/generate-with-files", summary="单模块图像生成 (文件上传模式)")
async def generate_single_module_with_files(
    module: str,
    # 基础参数
    model: str = Form(..., description="模型别名"),
    generation_mode: str = Form(..., description="生成模式: reference_assets"),
    generation_params: str = Form(..., description="生成参数的JSON字符串"),
    provider: Optional[str] = Form(None, description="AI提供商"),
    
    # 文件上传
    reference_images: Optional[List[UploadFile]] = File(None, description="艺术风格参考图（用于reference_image艺术风格模式）"),
    asset_references: Optional[UploadFile] = File(None, description="资产参考文件zip（用于reference_assets生成模式）"),
    
    handler: ImageHandler = Depends(get_image_handler)
):
    """
    单模块生成 - 文件上传模式
    
    支持两种文件上传：
    1. reference_images: 艺术风格参考图（art_style.mode = "reference_image"）
    2. asset_references: 资产参考文件（generation_mode = "reference_assets"）
    
    Form data example:
    - model: gpt_image_1
    - generation_mode: reference_assets
    - generation_params: {
        "art_style": {
            "mode": "reference_image",
            "ai_provider": "openai",
            "ai_model": "gpt-4o"
        },
        "base_symbols": {
            "low_value": [
                {
                    "filename": "king_spades",
                    "description": "King of Spades with royal crown",
                    "count": 1
                }
            ]
        }
    }
    - reference_images: [上传的艺术风格参考图]
    - asset_references: [上传的资产参考zip文件]
    """
    if generation_mode == "prompt_only":
        return BaseResponse.error_response(
            "INVALID_MODE",
            "prompt_only模式请使用JSON接口，无需上传文件"
        )
    
    # 验证文件上传
    if generation_mode == "reference_assets" and not asset_references:
        return BaseResponse.error_response(
            "MISSING_FILE",
            "reference_assets模式需要上传asset_references文件"
        )
    
    try:
        result = await handler.handle_module_generation_with_files(
            module=module,
            model=model,
            generation_mode=generation_mode,
            generation_params=generation_params,
            provider=provider,
            reference_images=reference_images,
            asset_references=asset_references
        )
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("GENERATION_ERROR", str(e))

@router.post("/generate-complete-with-files", summary="完整游戏资产生成 (文件上传模式)")
async def generate_complete_game_with_files(
    # 全局配置
    global_style: str = Form(..., description="全局艺术风格配置的JSON字符串"),
    model: str = Form(..., description="模型别名"),
    generation_mode: str = Form(..., description="生成模式: reference_assets"),
    provider: Optional[str] = Form(None, description="AI提供商"),
    
    # 模块配置
    modules_config: str = Form(..., description="各模块配置的JSON字符串"),
    
    # 文件上传
    reference_images: Optional[List[UploadFile]] = File(None, description="艺术风格参考图"),
    asset_references: Optional[UploadFile] = File(None, description="资产参考文件zip"),
    
    handler: ImageHandler = Depends(get_image_handler)
):
    """
    完整游戏资产生成 - 文件上传模式
    
    Form data example:
    - global_style: {"mode": "reference_image", "ai_provider": "openai", "ai_model": "gpt-4o"}
    - model: gpt_image_1
    - generation_mode: reference_assets
    - modules_config: {
        "symbols": {
            "base_symbols": {
                "low_value": [
                    {
                        "filename": "ace_hearts",
                        "description": "Ace of Hearts with royal design",
                        "count": 1
                    }
                ]
            }
        }
    }
    - reference_images: [上传的艺术风格参考图]
    - asset_references: [上传的资产参考zip文件]
    """
    if generation_mode == "prompt_only":
        return BaseResponse.error_response(
            "INVALID_MODE",
            "prompt_only模式请使用JSON接口，无需上传文件"
        )
    
    # 验证文件上传
    if generation_mode == "reference_assets" and not asset_references:
        return BaseResponse.error_response(
            "MISSING_FILE",
            "reference_assets模式需要上传asset_references文件"
        )
    
    try:
        import json
        global_style_dict = json.loads(global_style)
        
        result = await handler.handle_complete_game_generation_with_files(
            global_style=global_style_dict,
            model=model,
            provider=provider,
            generation_mode=generation_mode,
            modules_config=modules_config,
            reference_images=reference_images,
            asset_references=asset_references
        )
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("GENERATION_ERROR", str(e))

# ================================================================
# 辅助功能路由
# ================================================================

@router.post("/{module}/validate", summary="验证模块配置")
async def validate_module_config(
    module: str,
    model: str = Body(..., description="模型别名"),
    generation_params: Dict[str, Any] = Body(..., description="生成参数"),
    handler: ImageHandler = Depends(get_image_handler)
):
    """
    验证单模块配置
    
    包括艺术风格配置和元件格式验证
    
    Request body example:
    {
        "model": "gpt_image_1",
        "generation_params": {
            "art_style": {
                "mode": "preset",
                "preset_theme": "fantasy_medieval"
            },
            "base_symbols": {
                "low_value": [
                    {
                        "filename": "ace_hearts",
                        "description": "Ornate Ace of Hearts with royal design",
                        "count": 1,
                        "resolution": "512x512"
                    }
                ]
            }
        }
    }
    """
    try:
        result = await handler.validate_module_config(
            module=module,
            model=model,
            generation_params=generation_params
        )
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("VALIDATION_ERROR", str(e))

@router.get("/{module}/info", summary="获取模块信息")
async def get_module_info(
    module: str,
    handler: ImageHandler = Depends(get_image_handler)
):
    """获取模块信息，包括艺术风格支持信息"""
    try:
        result = await handler.get_module_info(module)
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("MODULE_INFO_ERROR", str(e))

@router.get("/examples", summary="获取配置示例")
async def get_config_examples(handler: ImageHandler = Depends(get_image_handler)):
    """获取各种配置示例，包括新的元件格式和艺术风格配置"""
    try:
        result = await handler.get_config_examples()
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("EXAMPLES_ERROR", str(e))

@router.get("/art-style/presets", summary="获取可用的艺术风格预设")
async def get_art_style_presets(handler: ImageHandler = Depends(get_image_handler)):
    """获取所有可用的艺术风格预设主题"""
    try:
        result = await handler.art_style_handler.handle_get_available_presets()
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("ART_STYLE_PRESETS_ERROR", str(e))

@router.get("/health", summary="健康检查")
async def health_check():
    """图像生成服务健康检查"""
    return BaseResponse.success_response({
        "service": "image_generation_v2",
        "status": "healthy",
        "version": "2.0.0",
        "supported_modules": ["symbols", "ui", "backgrounds"],
        "supported_modes": ["prompt_only", "reference_assets"],
        "art_style_integration": {
            "supported_art_modes": ["preset", "custom_direct", "custom_ai_enhanced", "reference_image"],
            "ai_powered_modes": ["custom_ai_enhanced", "reference_image"]
        },
        "new_features": [
            "integrated_art_style_system",
            "unified_asset_item_format",
            "individual_resolution_control",
            "enhanced_prompt_generation"
        ],
        "endpoints": {
            "json_mode": {
                "single_module": "POST /{module}/generate",
                "complete_game": "POST /generate-complete"
            },
            "file_upload_mode": {
                "single_module": "POST /{module}/generate-with-files",
                "complete_game": "POST /generate-complete-with-files"
            },
            "utilities": {
                "validate": "POST /{module}/validate",
                "module_info": "GET /{module}/info",
                "examples": "GET /examples",
                "art_style_presets": "GET /art-style/presets",
                "health": "GET /health"
            }
        }
    })

# ================================================================
# API使用说明和示例
# ================================================================

"""
图像生成API v2.0 使用指南 - 集成Art Style系统

## 主要更新

### 1. 集成Art Style模块
- 支持4种艺术风格模式：preset, custom_direct, custom_ai_enhanced, reference_image
- 每个模块可以独立设置艺术风格，也可以继承全局风格
- AI增强风格生成，自动优化提示词

### 2. 新的元件格式
- filename: 文件名/ID，简短且唯一
- description: 详细描述，用于提示词生成
- count: 生成数量（每个元件可单独设置）
- resolution: 分辨率（可选，覆盖默认设置）

### 3. 简化的生成模式
- prompt_only: 仅使用提示词生成
- reference_assets: 使用资产参考文件（zip格式）

## 使用示例

### 1. 基础符号生成（预设风格）
```json
POST /api/v1/assets/image/symbols/generate
{
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
                    "filename": "ace_hearts",
                    "description": "Ornate Ace of Hearts with royal medieval design and golden accents",
                    "count": 2,
                    "resolution": "512x512"
                },
                {
                    "filename": "king_spades",
                    "description": "King of Spades with medieval armor, crown, and royal sword",
                    "count": 1
                }
            ],
            "high_value": [
                {
                    "filename": "royal_crown",
                    "description": "Majestic royal crown with precious gems and mystical aura",
                    "count": 3,
                    "resolution": "1024x1024"
                }
            ]
        },
        "special_symbols": {
            "wild": [
                {
                    "filename": "dragon_wild",
                    "description": "Mystical dragon wild symbol with magical energy and glowing effects",
                    "count": 1
                }
            ]
        }
    }
}
```

### 2. AI增强风格生成
```json
POST /api/v1/assets/image/ui/generate
{
    "model": "gpt_image_1",
    "generation_params": {
        "art_style": {
            "mode": "custom_ai_enhanced",
            "custom_prompt": "Epic fantasy UI with mystical energy and ancient runes",
            "ai_provider": "openai",
            "ai_model": "gpt-4o"
        },
        "buttons": {
            "main_controls": [
                {
                    "filename": "spin_btn",
                    "description": "Magical spin button with glowing runes and energy effects",
                    "count": 1
                },
                {
                    "filename": "auto_spin_btn",
                    "description": "Auto-spin button with swirling magical particles",
                    "count": 1
                }
            ]
        }
    }
}
```

### 3. 参考图像风格分析
```
POST /api/v1/assets/image/symbols/generate-with-files
Content-Type: multipart/form-data

model: gpt_image_1
generation_mode: prompt_only
generation_params: {
    "art_style": {
        "mode": "reference_image",
        "ai_provider": "openai",
        "ai_model": "gpt-4o"
    },
    "base_symbols": {
        "low_value": [
            {
                "filename": "custom_ace",
                "description": "Custom ace symbol matching reference style",
                "count": 1
            }
        ]
    }
}
reference_images: [上传的风格参考图]
```

### 4. 完整游戏生成（多模块）
```json
POST /api/v1/assets/image/generate-complete
{
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
            "buttons": {
                "main_controls": [
                    {
                        "filename": "spin_btn",
                        "description": "Medieval style spin button with magical glow",
                        "count": 1
                    }
                ]
            }
        },
        "backgrounds": {
            "background_set": {
                "main_game": [
                    {
                        "filename": "main_bg",
                        "description": "Epic fantasy castle background with mystical atmosphere",
                        "count": 1,
                        "resolution": "1920x1080"
                    }
                ]
            }
        }
    }
}
```

### 5. 资产参考文件生成
```
POST /api/v1/assets/image/symbols/generate-with-files
Content-Type: multipart/form-data

model: gpt_image_1
generation_mode: reference_assets
generation_params: {
    "art_style": {
        "mode": "preset",
        "preset_theme": "fantasy_medieval"
    },
    "base_symbols": {
        "low_value": [
            {
                "filename": "custom_symbol",
                "description": "Custom symbol based on reference files",
                "count": 2
            }
        ]
    }
}
asset_references: [上传的zip参考文件]
```

## 响应格式更新

```json
{
    "success": true,
    "data": {
        "task_id": "symbols_abc123",
        "module": "symbols",
        "status": "completed",
        "num_outputs": 3,
        "outputs": [
            {
                "file_name": "ace_hearts_01.png",
                "s3_key": "generated/symbols/symbols_abc123/base_symbols/low_value/ace_hearts_01.png",
                "url": "https://s3.amazonaws.com/...",
                "category": "base_symbols",
                "subcategory": "low_value",
                "filename": "ace_hearts",
                "description": "Ornate Ace of Hearts with royal medieval design",
                "index": 1,
                "resolution": "512x512",
                "file_size": 245760,
                "has_template": false
            }
        ],
        "art_style_used": {
            "mode": "preset",
            "style_prompt": "fantasy medieval art style, detailed ornate design...",
            "components": {
                "base_prompt": "fantasy medieval art style",
                "color_palette": "royal gold, deep crimson, midnight blue",
                "lighting": "warm candlelight, dramatic shadows"
            }
        },
        "duration": 45.2,
        "created_at": "2025-06-17T01:00:00Z"
    }
}
```

## 重要变更说明

1. **移除风格图模式**: 原有的reference_style模式已移除，现在风格处理统一通过art_style配置
2. **新元件格式**: 不再使用types+count_per_type，改为独立的元件列表格式
3. **分辨率控制**: 每个元件可以单独设置分辨率，覆盖默认设置
4. **艺术风格集成**: 所有生成都需要指定art_style配置
5. **增强的提示词**: 基于艺术风格和描述自动生成更专业的提示词

## 迁移指南

从v1.0迁移到v2.0：
1. 将types数组改为元件列表格式
2. 添加art_style配置到所有生成参数中
3. 使用新的文件名和描述字段
4. 更新分辨率设置方式
5. 调整文件上传接口的参数名称
"""