# src/schemas/dtos/request/asset_request.py
from typing import Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field, validator
from src.schemas.dtos.request.base_request import BaseRequest

T = TypeVar("T")

class AssetGenRequest(BaseRequest, Generic[T]):
    """资源生成基础请求"""
    
    provider: Optional[str] = Field(None, description="指定提供商，不指定则使用默认")
    model: str = Field(..., description="模型服务类型")
    num_outputs: int = Field(1, ge=1, le=50, description="生成数量")
    generation_params: T = Field(..., description="生成参数")
    
    @validator('num_outputs')
    def validate_num_outputs(cls, v):
        if v < 1 or v > 50:
            raise ValueError("输出数量必须在1-50之间")
        return v