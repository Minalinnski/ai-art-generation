# src/schemas/enums/model_enums.py
from enum import Enum


class OpenAIModelEnum(str, Enum):
    """OpenAI模型枚举"""
    # 图像生成模型
    GPT_IMAGE_1 = "gpt-image-1"
    DALL_E_3 = "dall-e-3"
    
    # 文本生成模型  
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    
    @property
    def is_image_model(self) -> bool:
        """是否为图像生成模型"""
        return self in [
            OpenAIModelEnum.GPT_IMAGE_1,
            OpenAIModelEnum.DALL_E_3
        ]
    
    @property
    def is_text_model(self) -> bool:
        """是否为文本生成模型"""
        return self in [
            OpenAIModelEnum.GPT_4O,
            OpenAIModelEnum.GPT_4O_MINI
        ]
    
    @classmethod
    def get_image_models(cls) -> list["OpenAIModelEnum"]:
        """获取所有图像模型"""
        return [model for model in cls if model.is_image_model]
    
    @classmethod
    def get_text_models(cls) -> list["OpenAIModelEnum"]:
        """获取所有文本模型"""
        return [model for model in cls if model.is_text_model]


class ModelProviderEnum(str, Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    REPLICATE = "replicate"
    STABILITY = "stability"
    ANTHROPIC = "anthropic"


class AssetModelAliasEnum(str, Enum):
    """资源模型别名枚举 - 用于配置和DTO"""
    # 图像生成别名
    GPT_IMAGE = "gpt_image_1"        # 对应 OpenAIModelEnum.GPT_IMAGE_1
    DALLE = "dalle3"                 # 对应 OpenAIModelEnum.DALL_E_3
    
    # 文本生成别名（供其他模块使用）
    GPT4O = "gpt4o"                  # 对应 OpenAIModelEnum.GPT_4O
    GPT4O_MINI = "gpt4o_mini"        # 对应 OpenAIModelEnum.GPT_4O_MINI
    
    def to_openai_model(self) -> OpenAIModelEnum:
        """转换为OpenAI模型枚举"""
        mapping = {
            AssetModelAliasEnum.GPT_IMAGE: OpenAIModelEnum.GPT_IMAGE_1,
            AssetModelAliasEnum.DALLE: OpenAIModelEnum.DALL_E_3,
            AssetModelAliasEnum.GPT4O: OpenAIModelEnum.GPT_4O,
            AssetModelAliasEnum.GPT4O_MINI: OpenAIModelEnum.GPT_4O_MINI,
        }
        return mapping[self]
    
    @property
    def is_image_alias(self) -> bool:
        """是否为图像模型别名"""
        return self in [
            AssetModelAliasEnum.GPT_IMAGE,
            AssetModelAliasEnum.DALLE
        ]


# 模型能力定义
class ModelCapabilityEnum(str, Enum):
    """模型能力枚举"""
    IMAGE_GENERATION = "image_generation"
    TEXT_GENERATION = "text_generation"
    MULTIMODAL = "multimodal"