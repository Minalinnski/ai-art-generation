# src/api/routers/v1/assets/image/symbols_router.py (更新版)
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from src.application.handlers.assets.image.symbols_handler import get_symbols_handler, SymbolsHandler
from src.infrastructure.decorators.rate_limit import api_rate_limit
from src.infrastructure.decorators.retry import simple_retry
from src.infrastructure.tasks.task_decorator import async_task, sync_task
from src.schemas.dtos.request.image_request import SymbolGenRequest, SymbolGPTInput
from src.schemas.dtos.response.image_response import ImageGenResponse, ImageModuleInfoResponse
from src.schemas.dtos.response.base_response import BaseResponse

router = APIRouter(prefix="/symbols", tags=["Image - Symbols"])


@router.get("/", summary="获取符号模块状态")
async def get_symbols_status(
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    获取符号生成模块的状态信息
    
    返回模块基本信息、可用模型、支持的风格等
    """
    try:
        result = await handler._process_request()
        return BaseResponse.success_response(result)
    except Exception as e:
        return BaseResponse.error_response("SYMBOLS_STATUS_ERROR", str(e))


@router.get("/info", summary="获取符号模块详细信息")
async def get_symbols_info(
    handler: SymbolsHandler = Depends(get_symbols_handler)
) -> BaseResponse[ImageModuleInfoResponse]:
    """
    获取符号模块的详细信息
    
    包括：
    - 支持的模型列表
    - 分类和子分类结构
    - 生成限制
    - 支持的提供商
    """
    try:
        info = await handler.get_symbols_info()
        return BaseResponse.success_response(info)
    except Exception as e:
        return BaseResponse.error_response("SYMBOLS_INFO_ERROR", str(e))


@router.get("/templates", summary="获取符号模板信息")
async def get_symbols_templates(
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    获取符号生成的模板信息
    
    包括：
    - 提示词模板
    - 风格预设
    - 支持的分类和类型
    """
    try:
        templates = await handler.get_symbols_templates()
        return BaseResponse.success_response(templates)
    except Exception as e:
        return BaseResponse.error_response("SYMBOLS_TEMPLATES_ERROR", str(e))


@router.post("/validate", summary="验证符号配置")
@api_rate_limit(requests_per_minute=60)
async def validate_symbols_config(
    config: SymbolGPTInput,
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    验证符号生成配置
    
    检查：
    - 配置有效性
    - 预计输出数量
    - 是否超过限制
    - 配置建议和警告
    """
    try:
        validation_result = await handler.validate_symbols_config(config)
        return BaseResponse.success_response(validation_result)
    except Exception as e:
        return BaseResponse.error_response("SYMBOLS_VALIDATION_ERROR", str(e))


@router.post("/preview", summary="获取生成预览")
@api_rate_limit(requests_per_minute=30)
async def get_generation_preview(
    config: SymbolGPTInput,
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    获取符号生成预览信息
    
    返回：
    - 将要生成的符号列表
    - 预计成本和时间
    - 任务分解详情
    - 提示词预览
    """
    try:
        preview_info = await handler.get_generation_preview(config)
        return BaseResponse.success_response(preview_info)
    except Exception as e:
        return BaseResponse.error_response("SYMBOLS_PREVIEW_ERROR", str(e))


@router.post("/generate/quick", summary="快速符号生成")
@api_rate_limit(requests_per_minute=20)  
@sync_task(timeout=180)  # 3分钟超时
async def generate_symbols_quick(
    request: SymbolGenRequest,
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    快速符号生成（同步模式）
    
    适用于：
    - 少量符号生成（建议3个以内）
    - 需要立即获得结果的场景
    - 测试和预览
    
    注意：会使用任务系统并发生成，但会等待所有任务完成
    """
    try:
        # 验证快速生成的数量限制
        config_validation = await handler.validate_symbols_config(request.generation_params)
        if config_validation["estimated_outputs"] > 3:
            raise HTTPException(
                status_code=400,
                detail="快速生成建议符号数量不超过3个，请使用标准生成"
            )
        
        result = await handler.handle_symbols_generation(request)
        return BaseResponse.success_response(result)
        
    except HTTPException:
        raise
    except Exception as e:
        return BaseResponse.error_response("SYMBOLS_QUICK_GENERATION_ERROR", str(e))


@router.post("/generate", summary="标准符号生成")
@api_rate_limit(requests_per_minute=10)  
@async_task(priority=2, timeout=900, max_retries=1)  # 15分钟超时，高优先级
async def generate_symbols_standard(
    request: SymbolGenRequest,
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """  
    标准符号生成（异步模式）
    
    特点：
    - 使用任务系统并发处理多个符号
    - 支持大量符号生成（最多20个）
    - 立即返回task_id，可通过任务系统查询进度
    - 自动处理失败重试
    
    流程：
    1. 解析生成请求，分解为多个子任务
    2. 并发提交所有子任务到任务队列
    3. 等待所有子任务完成
    4. 汇总结果并保存到S3
    """
    return await handler.handle_symbols_generation(request)


@router.post("/generate/batch", summary="批量符号生成")
@api_rate_limit(requests_per_minute=3)  # 更严格的限制
@async_task(priority=3, timeout=1800, max_retries=1)  # 30分钟超时，最高优先级
async def generate_symbols_batch(
    requests: list[SymbolGenRequest],
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    批量符号生成
    
    适用于：
    - 多套风格同时生成
    - 不同配置的符号集合
    - 大规模生产任务
    
    注意：每个请求内部会并发处理，多个请求间会顺序处理
    """
    if len(requests) > 5:  # 降低批量限制
        raise HTTPException(
            status_code=400,
            detail="批量请求数量不能超过5个"
        )
    
    # 验证总符号数量
    total_symbols = 0
    for req in requests:
        validation = await handler.validate_symbols_config(req.generation_params)
        total_symbols += validation["estimated_outputs"]
    
    if total_symbols > 50:
        raise HTTPException(
            status_code=400,
            detail=f"批量生成总符号数量 {total_symbols} 超过限制 50"
        )
    
    results = []
    for i, request in enumerate(requests):
        try:
            result = await handler.handle_symbols_generation(request)
            results.append({
                "index": i,
                "success": True,
                "result": result
            })
        except Exception as e:
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
    
    return BaseResponse.success_response({
        "batch_results": results,
        "total_requests": len(requests),
        "successful": len([r for r in results if r["success"]]),
        "failed": len([r for r in results if not r["success"]]),
        "total_symbols_generated": sum([
            r["result"].num_outputs for r in results 
            if r["success"] and "result" in r
        ])
    })


@router.get("/presets", summary="获取风格预设")
async def get_style_presets(
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    获取可用的风格预设
    
    返回所有内置的风格主题配置
    """
    try:
        service = handler.symbols_service
        return BaseResponse.success_response({
            "style_presets": service.STYLE_PRESETS,
            "available_themes": list(service.STYLE_PRESETS.keys())
        })
    except Exception as e:
        return BaseResponse.error_response("PRESETS_ERROR", str(e))


@router.get("/examples", summary="获取配置示例")
async def get_config_examples():
    """
    获取符号生成配置示例
    
    提供不同场景的配置模板
    """
    examples = {
        "minimal_quick": {
            "description": "最小配置 - 快速生成",
            "estimated_symbols": 2,
            "estimated_time": "1-2分钟",
            "config": {
                "style_theme": "fantasy_medieval",
                "base_symbols": {
                    "low_value": {
                        "types": ["j", "q"],
                        "count_per_type": 1
                    }
                },
                "resolution": "512x512"
            }
        },
        "standard_set": {
            "description": "标准符号集 - 适合大多数游戏",
            "estimated_symbols": 8,
            "estimated_time": "4-6分钟",
            "config": {
                "style_theme": "ancient_egypt",
                "base_symbols": {
                    "low_value": {
                        "types": ["10", "j", "q", "k", "a"],
                        "count_per_type": 1
                    },
                    "high_value": {
                        "types": ["scarab", "pharaoh", "pyramid"],
                        "count_per_type": 1
                    }
                },
                "resolution": "1024x1024"
            }
        },
        "complete_game_set": {
            "description": "完整游戏符号集 - 包含所有特殊符号",
            "estimated_symbols": 12,
            "estimated_time": "8-12分钟",
            "config": {
                "style_theme": "pirate_adventure",
                "base_symbols": {
                    "low_value": {
                        "types": ["10", "j", "q", "k", "a"],
                        "count_per_type": 1
                    },
                    "high_value": {
                        "types": ["treasure", "ship", "compass"],
                        "count_per_type": 1
                    }
                },
                "special_symbols": {
                    "wild": {
                        "variants": ["base", "expanded"],
                        "count_per_variant": 1
                    },
                    "scatter": True,
                    "bonus": True
                },
                "global_style_params": {
                    "color_palette": "ocean blue, treasure gold",
                    "art_style": "detailed adventure illustration"
                },
                "resolution": "1024x1024"
            }
        },
        "custom_style_demo": {
            "description": "自定义风格演示",
            "estimated_symbols": 6,
            "estimated_time": "3-5分钟",
            "config": {
                "style_theme": "steampunk_industrial",
                "base_symbols": {
                    "high_value": {
                        "types": ["gear", "steam_engine", "airship"],
                        "count_per_type": 2
                    }
                },
                "global_style_params": {
                    "color_palette": "brass, copper, steam white",
                    "art_style": "detailed steampunk illustration",
                    "style_elements": "gears, pipes, steam, Victorian machinery"
                },
                "resolution": "1024x1024"
            }
        }
    }
    
    return BaseResponse.success_response(examples)


@router.get("/limits", summary="获取生成限制")
async def get_generation_limits(
    handler: SymbolsHandler = Depends(get_symbols_handler)
):
    """
    获取符号生成的限制信息
    
    返回各种操作的限制和建议
    """
    try:
        limits = handler.symbols_service.get_generation_limits()
        
        # 添加路由层面的限制信息
        route_limits = {
            "quick_generation": {
                "max_symbols": 3,
                "timeout_seconds": 180,
                "recommended_use": "测试和预览"
            },
            "standard_generation": {
                "max_symbols": 20,
                "timeout_seconds": 900,
                "recommended_use": "正常生产任务"
            },
            "batch_generation": {
                "max_requests": 5,
                "max_total_symbols": 50,
                "timeout_seconds": 1800,
                "recommended_use": "大规模生产"
            }
        }
        
        return BaseResponse.success_response({
            **limits,
            "route_limits": route_limits
        })
        
    except Exception as e:
        return BaseResponse.error_response("LIMITS_ERROR", str(e))