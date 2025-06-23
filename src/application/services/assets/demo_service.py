# src/application/services/assets/demo_service.py
"""Demo辅助服务 - 基于S3路径直接生成预签名URL，不依赖TaskManager"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.application.services.external.s3_service import s3_service
from src.infrastructure.logging.logger import get_logger
from src.application.config.settings import get_settings


class DemoService:
    """Demo辅助服务"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self.bucket_name = self.settings.s3_bucket
        
    def _build_s3_prefix_for_task(self, task_id: str, date_str: Optional[str] = None) -> str:
        """构建任务的S3前缀路径"""
        if date_str is None:
            # 尝试从task_id中提取日期，或使用今天
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # 路径格式: image_assets_output/{year}-{month}-{day}/{task_id}/
        return f"image_assets_output/{date_str}/{task_id}/"
    
    async def get_task_images_with_presigned_urls(
        self, 
        task_id: str, 
        expiration: int = 3600,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """直接从S3获取任务图片并生成预签名URL"""
        try:
            # 构建S3前缀
            s3_prefix = self._build_s3_prefix_for_task(task_id, date_str)
            
            self.logger.info(f"搜索S3路径: {s3_prefix}")
            
            # 列出S3中的文件
            try:
                files = s3_service.list_files(prefix=s3_prefix, max_keys=100)
            except Exception as e:
                self.logger.error(f"列出S3文件失败: {str(e)}")
                return {
                    "success": False,
                    "message": f"无法访问S3路径: {s3_prefix}",
                    "task_id": task_id
                }
            
            if not files:
                # 尝试其他可能的日期
                self.logger.info(f"在 {s3_prefix} 未找到文件，尝试搜索其他日期...")
                
                # 尝试前后几天的日期
                base_date = datetime.utcnow()
                for days_offset in [-2, -1, 0, 1, 2]:
                    test_date = base_date + timedelta(days=days_offset)
                    test_date_str = test_date.strftime("%Y-%m-%d")
                    test_prefix = self._build_s3_prefix_for_task(task_id, test_date_str)
                    
                    try:
                        test_files = s3_service.list_files(prefix=test_prefix, max_keys=10)
                        if test_files:
                            self.logger.info(f"在 {test_prefix} 找到文件")
                            files = s3_service.list_files(prefix=test_prefix, max_keys=100)
                            s3_prefix = test_prefix
                            break
                    except Exception:
                        continue
                
                if not files:
                    return {
                        "success": False,
                        "message": f"任务 {task_id} 未找到任何图片文件",
                        "task_id": task_id,
                        "searched_prefix": s3_prefix
                    }
            
            # 过滤图片文件
            image_files = [f for f in files if self._is_image_file(f["key"])]
            
            if not image_files:
                return {
                    "success": False,
                    "message": f"任务 {task_id} 未找到图片文件",
                    "task_id": task_id,
                    "total_files": len(files)
                }
            
            # 为每个图片生成预签名URL
            results = []
            for file_info in image_files:
                try:
                    presigned_url = s3_service.generate_presigned_url(
                        key=file_info["key"],
                        expiration=expiration,
                        http_method='GET'
                    )
                    
                    # 从文件路径解析信息
                    file_data = self._parse_file_info(file_info, presigned_url, expiration)
                    results.append(file_data)
                    
                except Exception as e:
                    self.logger.warning(f"生成预签名URL失败 {file_info['key']}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "data": {
                    "task_id": task_id,
                    "status": "completed",
                    "results": results,
                    "total_count": len(results),
                    "s3_prefix": s3_prefix,
                    "search_info": {
                        "total_files_found": len(files),
                        "image_files_found": len(image_files)
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取任务图片失败: {str(e)}")
            return {
                "success": False,
                "message": f"服务错误: {str(e)}",
                "task_id": task_id
            }
    
    def _is_image_file(self, key: str) -> bool:
        """检查是否为图片文件"""
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        return any(key.lower().endswith(ext) for ext in image_extensions)
    
    def _parse_file_info(self, file_info: Dict, presigned_url: str, expiration: int) -> Dict[str, Any]:
        """解析文件信息"""
        key = file_info["key"]
        filename = os.path.basename(key)
        
        # 尝试从路径解析类别信息
        path_parts = key.split('/')
        category = "unknown"
        subcategory = "unknown"
        
        # 路径格式可能是: image_assets_output/date/task_id/module/category/subcategory/filename
        if len(path_parts) >= 6:
            try:
                module = path_parts[3] if len(path_parts) > 3 else "unknown"
                category = path_parts[4] if len(path_parts) > 4 else "unknown"
                subcategory = path_parts[5] if len(path_parts) > 5 else "unknown"
            except IndexError:
                pass
        
        # 从文件名尝试解析描述
        name_without_ext = os.path.splitext(filename)[0]
        description = name_without_ext.replace('_', ' ').title()
        
        return {
            "filename": filename,
            "file_name": filename,
            "s3_key": key,
            "presigned_url": presigned_url,
            "expires_at": (datetime.utcnow() + timedelta(seconds=expiration)).isoformat(),
            "category": category,
            "subcategory": subcategory,
            "description": description,
            "resolution": "unknown",
            "file_size": file_info.get("size", 0),
            "last_modified": file_info.get("last_modified", "").isoformat() if file_info.get("last_modified") else ""
        }
    
    async def list_recent_tasks_from_s3(
        self, 
        limit: int = 10,
        expiration: int = 3600
    ) -> Dict[str, Any]:
        """从S3扫描最近的任务"""
        try:
            # 获取最近几天的任务
            tasks = []
            base_date = datetime.utcnow()
            
            for days_offset in range(0, 7):  # 搜索最近7天
                search_date = base_date - timedelta(days=days_offset)
                date_str = search_date.strftime("%Y-%m-%d")
                date_prefix = f"image_assets_output/{date_str}/"
                
                try:
                    # 列出该日期下的任务文件夹
                    folders = s3_service.list_files(prefix=date_prefix, max_keys=50)
                    
                    # 找到任务ID（子文件夹）
                    task_folders = set()
                    for file_info in folders:
                        key = file_info["key"]
                        # 从路径中提取任务ID: image_assets_output/date/task_id/...
                        parts = key.split('/')
                        if len(parts) >= 4 and parts[0] == "image_assets_output":
                            task_id = parts[2]
                            if task_id and not task_id.endswith('/'):
                                task_folders.add(task_id)
                    
                    # 为每个任务获取图片
                    for task_id in list(task_folders)[:limit]:
                        task_result = await self.get_task_images_with_presigned_urls(
                            task_id, expiration, date_str
                        )
                        
                        if task_result.get("success") and task_result.get("data", {}).get("results"):
                            tasks.append(task_result["data"])
                            
                        if len(tasks) >= limit:
                            break
                    
                    if len(tasks) >= limit:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"搜索日期 {date_str} 失败: {str(e)}")
                    continue
            
            return {
                "success": True,
                "data": {
                    "tasks": tasks[:limit],
                    "total_count": len(tasks)
                }
            }
            
        except Exception as e:
            self.logger.error(f"列出最近任务失败: {str(e)}")
            return {
                "success": False,
                "message": f"服务错误: {str(e)}"
            }
    
    async def get_task_progress_info(self, task_id: str) -> Dict[str, Any]:
        """获取任务进度信息（基于S3文件计数）"""
        try:
            # 搜索任务相关的文件
            result = await self.get_task_images_with_presigned_urls(task_id, expiration=60)
            
            if result.get("success"):
                data = result["data"]
                results = data.get("results", [])
                
                return {
                    "success": True,
                    "data": {
                        "task_id": task_id,
                        "status": "completed" if results else "processing",
                        "progress": 100 if results else 50,  # 简单的进度估算
                        "message": f"找到 {len(results)} 个生成的图片" if results else "正在生成中...",
                        "completed_count": len(results),
                        "is_completed": bool(results),
                        "is_processing": not bool(results)
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "task_id": task_id,
                        "status": "processing",
                        "progress": 25,
                        "message": "任务处理中，暂未找到结果文件",
                        "completed_count": 0,
                        "is_completed": False,
                        "is_processing": True
                    }
                }
                
        except Exception as e:
            self.logger.error(f"获取任务进度失败: {str(e)}")
            return {
                "success": False,
                "message": f"服务错误: {str(e)}"
            }


# 创建全局实例
demo_service = DemoService()