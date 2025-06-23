# src/schemas/dtos/response/image_response.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.schemas.base_schema import BaseSchema, TimestampMixin


class ImageGenResponse(BaseSchema, TimestampMixin):
    """图像生成响应DTO"""
    
    task_id: str = Field(..., description="任务ID")
    module: str = Field(..., description="生成模块")
    model: str = Field(..., description="使用的模型")
    status: str = Field(..., description="生成状态")
    num_outputs: int = Field(..., description="生成数量")
    outputs: List[Dict[str, Any]] = Field(default_factory=list, description="生成结果详情")
    generation_params: Dict[str, Any] = Field(default_factory=dict, description="生成参数")
    provider: Optional[str] = Field(None, description="AI服务提供商")
    duration: Optional[float] = Field(None, description="生成耗时(秒)")
    error: Optional[str] = Field(None, description="错误信息")
    s3_paths: Optional[Dict[str, str]] = Field(None, description="S3路径信息")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "examples": [
                {
                    "summary": "符号生成成功响应",
                    "value": {
                        "task_id": "symbols_123456",
                        "module": "symbols",
                        "model": "gpt4o",
                        "status": "completed",
                        "num_outputs": 4,
                        "outputs": [
                            {
                                "file_name": "base_symbols_low_value_j_01.png",
                                "s3_key": "image_assets_output/2024/12/01/symbols_123456/symbols/base_symbols/low_value/base_symbols_low_value_j_01.png",
                                "url": "https://bucket.s3.amazonaws.com/...",
                                "category": "base_symbols",
                                "subcategory": "low_value",
                                "type": "j",
                                "index": 1
                            }
                        ],
                        "generation_params": {
                            "style_theme": "fantasy_medieval",
                            "base_symbols": {
                                "low_value": {
                                    "types": ["j", "q", "k", "a"],
                                    "count_per_type": 1
                                }
                            }
                        },
                        "provider": "openai",
                        "duration": 45.2,
                        "s3_paths": {
                            "input_path": "image_assets_input/references/fantasy_medieval/symbols/",
                            "output_base": "image_assets_output/2024/12/01/symbols_123456/"
                        },
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                },
                {
                    "summary": "UI生成成功响应",
                    "value": {
                        "task_id": "ui_789012",
                        "module": "ui",
                        "model": "dalle3",
                        "status": "completed",
                        "num_outputs": 3,
                        "outputs": [
                            {
                                "file_name": "buttons_main_controls_spin_01.png",
                                "s3_key": "image_assets_output/2024/12/01/ui_789012/ui/buttons/main_controls/buttons_main_controls_spin_01.png",
                                "url": "https://bucket.s3.amazonaws.com/...",
                                "category": "buttons",
                                "subcategory": "main_controls",
                                "type": "spin",
                                "index": 1
                            }
                        ],
                        "provider": "openai",
                        "duration": 60.1,
                        "created_at": "2024-01-01T10:05:00Z"
                    }
                }
            ]
        }


class CombinedImageGenResponse(BaseSchema, TimestampMixin):
    """组合图像生成响应DTO"""
    
    task_id: str = Field(..., description="总任务ID")
    modules: List[str] = Field(..., description="生成的模块列表")
    style_theme: str = Field(..., description="风格主题")
    status: str = Field(..., description="整体生成状态")
    total_outputs: int = Field(..., description="总生成数量")
    
    # 各模块的生成结果
    results: Dict[str, ImageGenResponse] = Field(..., description="各模块生成结果")
    
    duration: Optional[float] = Field(None, description="总耗时(秒)")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "task_id": "combined_456789",
                "modules": ["symbols", "ui"],
                "style_theme": "fantasy_medieval",
                "status": "completed",
                "total_outputs": 7,
                "results": {
                    "symbols": {
                        "task_id": "symbols_123456",
                        "module": "symbols",
                        "model": "gpt4o",
                        "status": "completed",
                        "num_outputs": 4
                    },
                    "ui": {
                        "task_id": "ui_789012",
                        "module": "ui", 
                        "model": "dalle3",
                        "status": "completed",
                        "num_outputs": 3
                    }
                },
                "duration": 105.3,
                "created_at": "2024-01-01T10:00:00Z"
            }
        }


class ImageModuleInfoResponse(BaseSchema):
    """图像模块信息响应DTO"""
    
    module: str = Field(..., description="模块名称")
    description: str = Field(..., description="模块描述")
    available_models: List[str] = Field(..., description="可用模型列表")
    default_model: str = Field(..., description="默认模型")
    supported_providers: List[str] = Field(..., description="支持的提供商")
    categories: Dict[str, Any] = Field(..., description="模块分类结构")
    generation_limits: Dict[str, Any] = Field(..., description="生成限制")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "module": "symbols",
                "description": "游戏符号生成",
                "available_models": ["gpt4o", "dalle3"],
                "default_model": "gpt4o",
                "supported_providers": ["openai"],
                "categories": {
                    "base_symbols": {
                        "description": "基础符号",
                        "subcategories": {
                            "low_value": {
                                "description": "低价值符号",
                                "common_types": ["j", "q", "k", "a"]
                            }
                        }
                    }
                },
                "generation_limits": {
                    "max_outputs_per_request": 20,
                    "default_timeout": 300
                }
            }
        }


class ImageSystemStatusResponse(BaseSchema):
    """图像系统状态响应DTO"""
    
    system: str = Field(..., description="系统名称")
    status: str = Field(..., description="系统状态")
    modules: Dict[str, ImageModuleInfoResponse] = Field(..., description="模块信息")
    s3_config: Dict[str, Any] = Field(..., description="S3配置信息")
    total_available_models: int = Field(..., description="总可用模型数")
    enabled_providers: List[str] = Field(..., description="启用的提供商")
    timestamp: str = Field(..., description="状态检查时间")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "system": "Image Asset Generation",
                "status": "healthy",
                "modules": {
                    "symbols": {
                        "module": "symbols",
                        "status": "healthy",
                        "available_models": ["gpt4o", "dalle3"]
                    }
                },
                "s3_config": {
                    "bucket_configured": True,
                    "input_base_path": "image_assets_input/references/",
                    "output_base_path": "image_assets_output/"
                },
                "total_available_models": 6,
                "enabled_providers": ["openai"],
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }