# src/api/routers/v1/assets/demo.py
"""Demo辅助路由 - 基于S3直接获取图片，不依赖TaskManager"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.application.services.assets.demo_service import demo_service
from src.infrastructure.logging.logger import get_logger

router = APIRouter(prefix="/demo", tags=["Demo"])
logger = get_logger(__name__)


@router.get("/task/{task_id}/result")
async def get_task_result_with_urls(
    task_id: str,
    expiration: int = Query(default=3600, description="预签名URL有效期（秒）"),
    date_str: Optional[str] = Query(default=None, description="任务日期 (YYYY-MM-DD)，为空则自动搜索")
):
    """获取任务结果并生成预签名URL - 直接从S3搜索"""
    try:
        result = await demo_service.get_task_images_with_presigned_urls(
            task_id=task_id,
            expiration=expiration,
            date_str=date_str
        )
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务内部错误")


@router.get("/task/{task_id}/status")
async def check_task_status(task_id: str):
    """简单的任务状态检查 - 基于S3文件存在性"""
    try:
        result = await demo_service.get_task_progress_info(task_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务内部错误")


@router.get("/tasks/recent")
async def list_recent_tasks(
    limit: int = Query(default=10, description="返回任务数量"),
    expiration: int = Query(default=3600, description="预签名URL有效期（秒）")
):
    """列出最近的任务 - 从S3扫描"""
    try:
        result = await demo_service.list_recent_tasks_from_s3(
            limit=limit,
            expiration=expiration
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列出最近任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务内部错误")


@router.get("/search-task")
async def search_task_by_partial_id(
    partial_id: str = Query(..., description="部分任务ID"),
    expiration: int = Query(default=3600, description="预签名URL有效期（秒）")
):
    """根据部分任务ID搜索"""
    try:
        # 这里可以实现更复杂的搜索逻辑
        # 暂时直接尝试作为完整task_id
        result = await demo_service.get_task_images_with_presigned_urls(
            task_id=partial_id,
            expiration=expiration
        )
        
        return result
        
    except Exception as e:
        logger.error(f"搜索任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务内部错误")


@router.get("/health")
async def demo_health_check():
    """Demo服务健康检查"""
    return {
        "success": True,
        "service": "demo",
        "message": "Demo service is healthy (S3-based)",
        "timestamp": "2025-06-22T08:00:00Z",
        "features": [
            "Direct S3 file scanning", 
            "Presigned URL generation",
            "Multi-date search",
            "Task progress estimation"
        ]
    }