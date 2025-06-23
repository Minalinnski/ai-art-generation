# src/schemas/dtos/request/text_generation_request.py  
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TextGenerationRequest(BaseModel):
    """文本生成请求DTO"""
    prompt: str = Field(..., description="输入提示词", min_length=1, max_length=8000)
    model: str = Field(default="gpt-4o", description="使用的模型")
    max_tokens: Optional[int] = Field(default=500, ge=10, le=4000, description="最大生成token数")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Analyze this image and describe its artistic style for game asset generation",
                "model": "gpt-4o",
                "max_tokens": 300,
                "temperature": 0.7,
                "system_prompt": "You are an expert art director analyzing visual styles."
            }
        }