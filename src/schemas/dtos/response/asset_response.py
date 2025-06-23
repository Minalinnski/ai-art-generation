# src/schemas/dtos/response/asset_response.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.schemas.base_schema import BaseSchema, TimestampMixin
#from src.schemas.enums.asset_enums import AssetStatusEnum, AssetTypeEnum


class AssetGenResponse(BaseSchema, TimestampMixin):
    """资源生成响应DTO"""
    
    task_id: str = Field(..., description="任务ID")
    asset_type: str = Field(..., description="资源类型")
    model: str = Field(..., description="使用的模型")
    status: str = Field(..., description="生成状态")
    num_outputs: int = Field(..., description="生成数量")
    outputs: List[str] = Field(default_factory=list, description="生成结果URL列表")
    generation_params: Dict[str, Any] = Field(default_factory=dict, description="生成参数")
    provider: Optional[str] = Field(None, description="AI服务提供商")
    duration: Optional[float] = Field(None, description="生成耗时(秒)")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "examples": [
                {
                    "summary": "音频生成成功响应",
                    "value": {
                        "task_id": "audio_123456",
                        "asset_type": "audio",
                        "model": "ardianfe",
                        "status": "completed",
                        "num_outputs": 2,
                        "outputs": [
                            "https://s3.amazonaws.com/bucket/audio1.wav",
                            "https://s3.amazonaws.com/bucket/audio2.wav"
                        ],
                        "generation_params": {
                            "prompt": "Epic orchestral music",
                            "duration": 60
                        },
                        "provider": "replicate",
                        "duration": 45.2,
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                },
                {
                    "summary": "动画生成成功响应",
                    "value": {
                        "task_id": "anim_789012",
                        "asset_type": "animation",
                        "model": "pixverse",
                        "status": "completed",
                        "num_outputs": 1,
                        "outputs": [
                            "https://s3.amazonaws.com/bucket/animation.mp4"
                        ],
                        "generation_params": {
                            "prompt": "A knight fighting a dragon",
                            "quality": "1080p",
                            "duration": 5
                        },
                        "provider": "replicate",
                        "duration": 120.5,
                        "created_at": "2024-01-01T10:05:00Z"
                    }
                },
                {
                    "summary": "生成失败响应",
                    "value": {
                        "task_id": "task_error_001",
                        "asset_type": "audio",
                        "model": "meta",
                        "status": "failed",
                        "num_outputs": 0,
                        "outputs": [],
                        "generation_params": {
                            "prompt": "Invalid prompt"
                        },
                        "error": "Invalid generation parameters",
                        "created_at": "2024-01-01T10:10:00Z"
                    }
                }
            ]
        }


class AssetListResponse(BaseSchema):
    """资源列表响应DTO"""
    
    assets: List[AssetGenResponse] = Field(..., description="资源列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页大小")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "assets": [
                    {
                        "task_id": "audio_123",
                        "asset_type": "audio",
                        "model": "ardianfe",
                        "status": "completed",
                        "num_outputs": 1
                    }
                ],
                "total": 50,
                "page": 1,
                "size": 20,
                "has_next": True,
                "has_prev": False
            }
        }


class AssetModelsResponse(BaseSchema):
    """资源模型响应DTO"""
    
    asset_type: str = Field(..., description="资源类型")
    models: List[str] = Field(..., description="可用模型列表")
    default_provider: str = Field(..., description="默认提供商")
    enabled_providers: List[str] = Field(..., description="启用的提供商")
    limits: Dict[str, Any] = Field(..., description="生成限制")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "asset_type": "audio",
                "models": ["ardianfe", "meta"],
                "default_provider": "replicate",
                "enabled_providers": ["replicate"],
                "limits": {
                    "max_outputs_per_request": 50,
                    "default_timeout": 300
                }
            }
        }


class AssetStatusResponse(BaseSchema):
    """资源状态响应DTO"""
    
    handler: str = Field(..., description="处理器名称")
    status: str = Field(..., description="服务状态")
    supported_asset_types: List[str] = Field(..., description="支持的资源类型")
    category: Optional[str] = Field(None, description="服务分类")
    services: Optional[Dict[str, Any]] = Field(None, description="子服务状态")
    total_available_models: Optional[int] = Field(None, description="总可用模型数")
    timestamp: str = Field(..., description="状态检查时间")
    
    class Config(BaseSchema.Config):
        json_schema_extra = {
            "example": {
                "handler": "MultimediaHandler",
                "status": "healthy",
                "supported_asset_types": ["audio", "animation", "video"],
                "category": "multimedia",
                "services": {
                    "audio": {
                        "status": "healthy",
                        "available_models": ["ardianfe", "meta"]
                    }
                },
                "total_available_models": 5,
                "timestamp": "2024-01-01T10:00:00Z"
            }
        }