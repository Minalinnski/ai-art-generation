# src/schemas/enums/asset_enums.py (更新现有文件)
from enum import Enum
from src.schemas.enums.base_enums import BaseEnum


class AssetTypeEnum(BaseEnum):
    """资源类型枚举"""
    AUDIO = "audio"
    ANIMATION = "animation"
    VIDEO = "video"
    IMAGE = "image"


class ModelProviderEnum(BaseEnum):
    """资源提供商枚举"""
    REPLICATE = "replicate"
    OPENAI = "openai"
    STABILITY = "stability"
    ANTHROPIC = "anthropic"


class AnimationModelEnum(BaseEnum):
    """动画模型枚举"""
    PIXVERSE = "pixverse"
    PIA = "pia"


class MusicModelEnum(BaseEnum):
    """音乐模型枚举"""
    ARDIANFE = "ardianfe"
    META = "meta"


class VideoModelEnum(BaseEnum):
    """视频模型枚举"""
    BACKGROUND_REMOVAL = "background_removal"