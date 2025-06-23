# src/schemas/enums/image_enums.py
from enum import Enum
from src.schemas.enums.base_enums import BaseEnum


class ImageModuleEnum(BaseEnum):
    """图像模块枚举"""
    SYMBOLS = "symbols"
    UI = "ui"
    BACKGROUNDS = "backgrounds"


class ImageProviderEnum(BaseEnum):
    """图像提供商枚举"""
    REPLICATE = "replicate"
    OPENAI = "openai"
    STABILITY = "stability"


class ImageResolutionEnum(BaseEnum):
    """图像分辨率枚举"""
    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    HD = "1920x1080"


class ImageFormatEnum(BaseEnum):
    """图像格式枚举"""
    PNG = "png"
    JPG = "jpg"
    WEBP = "webp"


class StyleThemeEnum(BaseEnum):
    """风格主题枚举"""
    FANTASY_MEDIEVAL = "fantasy_medieval"
    ANCIENT_EGYPT = "ancient_egypt"
    SCI_FI_CYBER = "sci_fi_cyber"
    PIRATE_ADVENTURE = "pirate_adventure"


class SymbolTypeEnum(BaseEnum):
    """符号类型枚举"""
    BASE_SYMBOLS = "base_symbols"
    SPECIAL_SYMBOLS = "special_symbols"
    FRAMES = "frames"


class UITypeEnum(BaseEnum):
    """UI类型枚举"""
    BUTTONS = "buttons"
    PANELS = "panels"
    GAME_AREA = "game_area"
    POPUPS = "popups"


class BackgroundTypeEnum(BaseEnum):
    """背景类型枚举"""
    MAIN_GAME = "main_game"
    FREE_SPINS = "free_spins"
    BONUS_GAME = "bonus_game"
    FRAME = "frame"