# src/api/v1/main_router.py
from fastapi import APIRouter

from src.api.routers.v1.system.health_router import router as health_router
from src.api.routers.v1.system.task_router import router as task_router
# from src.api.routers.v1.foo_router import router as foo_router

from src.api.routers.v1.ai.ai_info_router import router as ai_info_router
from src.api.routers.v1.assets import assets_router

# 创建API v1主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(health_router)
api_router.include_router(task_router)
# api_router.include_router(foo_router)

api_router.include_router(ai_info_router)
api_router.include_router(assets_router)

from src.api.routers.s3_download_router import router as s3_download_router
api_router.include_router(s3_download_router)