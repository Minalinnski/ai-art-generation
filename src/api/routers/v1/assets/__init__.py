# src/api/routers/v1/assets/__init__.py
from fastapi import APIRouter

from src.api.routers.v1.assets.asset_main_router import router as asset_info_router
from src.api.routers.v1.assets.art_style_router import router as art_style_router
from src.api.routers.v1.assets.multimedia.animation_router import router as animation_router
from src.api.routers.v1.assets.multimedia.audio_router import router as audio_router
from src.api.routers.v1.assets.multimedia.video_router import router as video_router
# from src.api.routers.v1.assets.image.symbols_router import router as symbols_router
from src.api.routers.v1.assets.image_router import router as image_router

# 创建资源API主路由
assets_router = APIRouter(prefix="/assets")

# 注册子路由
assets_router.include_router(asset_info_router)
assets_router.include_router(art_style_router)
assets_router.include_router(animation_router)
assets_router.include_router(audio_router)
assets_router.include_router(video_router)
# assets_router.include_router(symbols_router)
assets_router.include_router(image_router)

from src.api.routers.v1.assets.demo_router import router as demo_router
assets_router.include_router(demo_router)
