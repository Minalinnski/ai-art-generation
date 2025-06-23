# src/application/handlers/assets/image/image_handler.py (重构版 - 完整版本)
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import HTTPException, UploadFile

from src.application.handlers.handler_interface import BaseHandler
from src.application.services.assets.image.symbols_service import SymbolsService
from src.application.services.assets.image.ui_service import UIService
from src.application.services.assets.image.backgrounds_service import BackgroundsService
from src.application.services.assets.image.file_processing_service import file_processing_service
from src.application.services.external.ai_service_factory import ai_service_factory
from src.application.config.assets.asset_settings import get_asset_settings

# 导入Art Style服务
from src.application.handlers.assets.art_style_handler import get_art_style_handler

# 导入重构后的请求DTO
from src.schemas.dtos.request.image_request import (
    ImageGenerationMode, 
    SymbolsGenerationInput, 
    UIGenerationInput, 
    BackgroundsGenerationInput,
    ArtStyleConfig,
    ImageAssetItem
)

class ImageHandler(BaseHandler):
    """图像生成处理器 - 集成Art Style模块"""
    
    def __init__(self):
        super().__init__()
        self.services = {
            "symbols": SymbolsService(),
            "ui": UIService(),
            "backgrounds": BackgroundsService()
        }
        self.asset_settings = get_asset_settings()
        self.art_style_handler = get_art_style_handler()
    
    # ==================== 主要接口方法 ====================
    
    async def handle_module_generation_json(
        self,
        module: str,
        model: str,
        generation_mode: str,
        generation_params: Dict[str, Any],
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理JSON模式的模块生成（仅prompt_only模式）"""
        task_id = f"{module}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        try:
            if generation_mode != ImageGenerationMode.PROMPT_ONLY:
                raise ValueError("此接口仅支持prompt_only模式")
            
            request_data = self._parse_request(module, model, generation_mode, generation_params, provider)
            
            # 生成艺术风格
            art_style_data = await self._generate_art_style(request_data["generation_params"].art_style)
            
            # 执行图像生成
            outputs = await self._execute_generation(request_data, art_style_data, task_id)
            return self._build_result(outputs, request_data, task_id, start_time, art_style_data)
        except Exception as e:
            self.logger.error(f"{module}生成失败: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def handle_module_generation_with_files(
        self,
        module: str,
        model: str,
        generation_mode: str,
        generation_params: str,
        provider: Optional[str] = None,
        reference_images: Optional[List[UploadFile]] = None,  # Art Style参考图
        asset_references: Optional[UploadFile] = None        # 资产参考文件
    ) -> Dict[str, Any]:
        """处理带文件的模块生成"""
        task_id = f"{module}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        try:
            if generation_mode == ImageGenerationMode.PROMPT_ONLY:
                raise ValueError("prompt_only模式请使用JSON接口")
            
            params_dict = json.loads(generation_params)
            request_data = self._parse_request(module, model, generation_mode, params_dict, provider)
            
            # 处理文件并生成艺术风格和参考数据
            art_style_data, reference_data = await self._process_files_and_art_style(
                request_data["generation_params"].art_style,
                generation_mode,
                reference_images,
                asset_references,
                module
            )
            
            # 执行图像生成
            outputs = await self._execute_generation(request_data, art_style_data, task_id, reference_data)
            return self._build_result(outputs, request_data, task_id, start_time, art_style_data)
        except Exception as e:
            self.logger.error(f"{module}生成失败: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def handle_complete_game_generation_json(
        self,
        global_config: Dict[str, Any],
        modules_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理JSON模式的完整游戏生成"""
        task_id = f"complete_game_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        try:
            if global_config.get("generation_mode") != ImageGenerationMode.PROMPT_ONLY:
                raise ValueError("此接口仅支持prompt_only模式")
            
            module_requests = await self._build_module_requests(global_config, modules_config)
            module_results = await self._execute_parallel_modules(module_requests, {}, task_id)
            return self._build_complete_result(module_results, task_id, start_time, global_config)
        except Exception as e:
            self.logger.error(f"完整游戏生成失败: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def handle_complete_game_generation_with_files(
        self,
        global_style: Dict[str, Any],
        model: str,
        provider: Optional[str],
        generation_mode: str,
        modules_config: str,
        reference_images: Optional[List[UploadFile]] = None,
        asset_references: Optional[UploadFile] = None
    ) -> Dict[str, Any]:
        """处理带文件的完整游戏生成"""
        task_id = f"complete_game_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        try:
            if generation_mode == ImageGenerationMode.PROMPT_ONLY:
                raise ValueError("prompt_only模式请使用JSON接口")
            
            modules_dict = json.loads(modules_config)
            global_config = {
                "global_art_style": global_style,
                "model": model,
                "provider": provider,
                "generation_mode": generation_mode
            }
            
            module_requests = await self._build_module_requests(global_config, modules_dict)
            
            # 处理全局艺术风格和参考数据
            global_art_style_data, reference_data = await self._process_files_and_art_style(
                global_style,
                generation_mode,
                reference_images,
                asset_references,
                "complete"
            )
            
            module_results = await self._execute_parallel_modules(module_requests, reference_data, task_id)
            return self._build_complete_result(module_results, task_id, start_time, global_config)
        except Exception as e:
            self.logger.error(f"完整游戏生成失败: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    # ==================== 艺术风格相关方法 ====================
    
    async def _generate_art_style(self, art_style_config: ArtStyleConfig) -> Dict[str, Any]:
        """生成艺术风格"""
        try:
            self.logger.info(f"生成艺术风格: {art_style_config.mode}")
            
            # 根据模式调用对应的艺术风格接口
            if art_style_config.mode == "preset":
                result = await self.art_style_handler.handle_preset_style_generation(
                    art_style_config.preset_theme
                )
            elif art_style_config.mode == "custom_direct":
                result = await self.art_style_handler.handle_custom_direct_style_generation(
                    art_style_config.style_components
                )
            elif art_style_config.mode == "custom_ai_enhanced":
                result = await self.art_style_handler.handle_custom_ai_enhanced_style_generation(
                    art_style_config.custom_prompt,
                    art_style_config.ai_provider,
                    art_style_config.ai_model
                )
            else:
                raise ValueError(f"不支持的艺术风格模式: {art_style_config.mode}")
            
            return result
        except Exception as e:
            self.logger.error(f"艺术风格生成失败: {str(e)}")
            # 提供回退风格
            return {
                "style_prompt": "high quality, detailed artwork",
                "mode": "fallback",
                "components": {
                    "base_prompt": "high quality artwork",
                    "description": "使用回退风格"
                },
                "quality_tags": "high quality, professional design"
            }
    
    async def _process_files_and_art_style(
        self,
        art_style_config: ArtStyleConfig,
        generation_mode: str,
        reference_images: Optional[List[UploadFile]],
        asset_references: Optional[UploadFile],
        module: str
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """处理文件并生成艺术风格和参考数据"""
        
        # 1. 处理艺术风格
        if art_style_config.mode == "reference_image":
            if not reference_images:
                raise ValueError("reference_image模式需要上传参考图片")
            
            # 调用Art Style的参考图像分析
            art_style_data = await self.art_style_handler.handle_reference_image_style_generation(
                reference_images,
                art_style_config.ai_provider,
                art_style_config.ai_model,
                len(reference_images)
            )
        else:
            # 其他模式的艺术风格生成
            art_style_data = await self._generate_art_style(art_style_config)
        
        # 2. 处理资产参考文件
        reference_data = {}
        if generation_mode == ImageGenerationMode.REFERENCE_ASSETS and asset_references:
            try:
                if module == "complete":
                    module = "symbols"  # 默认使用symbols解析
                
                asset_result = await file_processing_service.process_asset_references(asset_references, module)
                if asset_result.get("processing_success"):
                    reference_data.update({
                        "asset_description": f"Asset references from {asset_references.filename}",
                        "reference_prompts": asset_result["reference_prompts"],
                        "asset_items": asset_result["asset_items"]  # 新格式的元件数据
                    })
            except Exception as e:
                self.logger.error(f"资产文件处理失败: {str(e)}")
                # 提供回退
                reference_data["asset_description"] = f"Asset references: {asset_references.filename}"
        
        return art_style_data, reference_data
    
    # ==================== 图像生成相关方法 ====================
    
    def _parse_request(self, module: str, model: str, generation_mode: str, generation_params: Dict[str, Any], provider: Optional[str]) -> Dict[str, Any]:
        """解析请求参数"""
        service = self._get_service(module)
        
        # 创建参数对象
        param_classes = {
            "symbols": SymbolsGenerationInput, 
            "ui": UIGenerationInput, 
            "backgrounds": BackgroundsGenerationInput
        }
        param_class = param_classes.get(module)
        if not param_class:
            raise ValueError(f"不支持的模块: {module}")
        
        gen_params = param_class(**generation_params)
        
        # 验证
        if model not in service.get_available_models():
            raise ValueError(f"模型 {model} 不可用")
        
        return {
            "module": module,
            "model": model,
            "provider": provider,
            "generation_mode": ImageGenerationMode(generation_mode),
            "generation_params": gen_params,
            "service": service
        }
    
    async def _execute_generation(
        self, 
        request_data: Dict[str, Any], 
        art_style_data: Dict[str, Any], 
        task_id: str, 
        reference_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """执行图像生成"""
        service = request_data["service"]
        
        # 根据模式选择不同的任务解析策略
        if request_data["generation_mode"] == ImageGenerationMode.REFERENCE_ASSETS and reference_data and reference_data.get("asset_items"):
            # 参考文件模式：使用文件结构生成任务
            generation_tasks = self._parse_generation_tasks_from_references(reference_data["asset_items"], request_data["generation_params"])
        else:
            # 普通模式：使用请求参数生成任务
            generation_tasks = self._parse_generation_tasks(request_data["generation_params"])
        
        self.logger.info(f"开始生成图像任务", extra={
            "task_count": len(generation_tasks),
            "image_module": request_data["module"],  # 改名避免冲突
            "generation_mode": request_data["generation_mode"]
        })
        # 临时调试 - 打印extra内容
        print(f"🐛 DEBUG - 开始生成图像任务: task_count={len(generation_tasks)}, module={request_data['module']}, mode={request_data['generation_mode']}")
        
        # 并发生成
        tasks = [
            self._generate_single_image(task_info, request_data, art_style_data, reference_data or {}, task_id)
            for task_info in generation_tasks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 分析结果并记录错误
        successful_results = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_count += 1
                task_info = generation_tasks[i] if i < len(generation_tasks) else {"filename": f"task_{i}"}
                self.logger.error(f"生成任务失败", extra={
                    "task_index": i,
                    "task_filename": task_info.get("filename", "unknown"),  # 改名避免冲突
                    "error": str(result),
                    "error_type": type(result).__name__
                })
                # 临时调试 - 打印错误详情
                print(f"🐛 DEBUG - 任务失败: index={i}, filename={task_info.get('filename', 'unknown')}")
                print(f"🐛 DEBUG - 错误类型: {type(result).__name__}")
                print(f"🐛 DEBUG - 错误详情: {str(result)}")
                print(f"🐛 DEBUG - 任务信息: {task_info}")
            else:
                successful_results.append(result)
        
        self.logger.info(f"图像生成完成", extra={
            "total_tasks": len(generation_tasks),
            "successful": len(successful_results),
            "failed": failed_count
        })
        
        return successful_results
    
    def _parse_generation_tasks_from_references(self, asset_items: Dict[str, Any], generation_params: Any) -> List[Dict[str, Any]]:
        """从参考文件结构解析生成任务"""
        tasks = []
        default_resolution = generation_params.default_resolution
        
        for category, subcategories in asset_items.items():
            for subcategory, items in subcategories.items():
                for item in items:
                    for index in range(1, item.get("count", 1) + 1):
                        task_info = {
                            "category": category,
                            "subcategory": subcategory,
                            "filename": item["filename"],
                            "description": item["description"],
                            "index": index,
                            "resolution": item.get("resolution", default_resolution),
                            "has_template": False,
                            "from_reference": True
                        }
                        tasks.append(task_info)
        
        return tasks
    
    def _parse_generation_tasks(self, params: Any) -> List[Dict[str, Any]]:
        """解析生成任务列表 - 新的元件格式"""
        tasks = []
        
        # 处理预定义的两层结构内容
        category_attrs = {
            'symbols': ['base_symbols', 'special_symbols'],
            'ui': ['buttons', 'panels'],  
            'backgrounds': ['background_set']
        }
        
        # 确定模块类型
        module_type = None
        if isinstance(params, SymbolsGenerationInput):
            module_type = 'symbols'
        elif isinstance(params, UIGenerationInput):
            module_type = 'ui'
        elif isinstance(params, BackgroundsGenerationInput):
            module_type = 'backgrounds'
        
        if module_type:
            for category_name in category_attrs[module_type]:
                category_data = getattr(params, category_name, None)
                if category_data:
                    tasks.extend(self._parse_category_tasks(category_name, category_data, params.default_resolution))
        
        # 处理自定义内容
        if hasattr(params, 'custom_content') and params.custom_content:
            tasks.extend(self._parse_custom_content_tasks(params.custom_content, params.default_resolution))
        
        return tasks
    
    def _parse_category_tasks(self, category_name: str, category_data: Dict[str, List[ImageAssetItem]], default_resolution: str) -> List[Dict[str, Any]]:
        """解析分类任务 - 新格式"""
        tasks = []
        
        for subcategory_name, items in category_data.items():
            for item in items:
                for index in range(1, item.count + 1):
                    task_info = {
                        "category": category_name,
                        "subcategory": subcategory_name,
                        "filename": item.filename,
                        "description": item.description,
                        "index": index,
                        "resolution": item.resolution or default_resolution,
                        "has_template": False,
                        "from_reference": False
                    }
                    tasks.append(task_info)
        
        return tasks
    
    def _parse_custom_content_tasks(self, custom_content: Dict[str, List[ImageAssetItem]], default_resolution: str) -> List[Dict[str, Any]]:
        """解析自定义内容任务 - 新格式"""
        tasks = []
        
        for custom_name, items in custom_content.items():
            for item in items:
                for index in range(1, item.count + 1):
                    task_info = {
                        "category": "custom",
                        "subcategory": custom_name,
                        "filename": item.filename,
                        "description": item.description,
                        "index": index,
                        "resolution": item.resolution or default_resolution,
                        "has_template": False,
                        "from_reference": False
                    }
                    tasks.append(task_info)
        
        return tasks
    
    async def _generate_single_image(
        self, 
        task_info: Dict[str, Any], 
        request_data: Dict[str, Any], 
        art_style_data: Dict[str, Any],
        reference_data: Dict[str, Any], 
        task_id: str
    ) -> Dict[str, Any]:
        """生成单个图像"""
        try:
            service = request_data["service"]
            
            # 构建提示词 - 使用子服务的方法
            base_prompt = service.build_complete_prompt(task_info, art_style_data, reference_data)
            
            self.logger.info(f"构建提示词完成", extra={
                "task_filename": task_info.get("filename"),  # 改名避免冲突
                "prompt_length": len(base_prompt),
                "prompt_preview": base_prompt[:200] + "..." if len(base_prompt) > 200 else base_prompt
            })
            # 临时调试 - 打印提示词信息
            print(f"🐛 DEBUG - 提示词构建: filename={task_info.get('filename')}, length={len(base_prompt)}")
            print(f"🐛 DEBUG - 提示词预览: {base_prompt[:300]}...")
            
            # 准备推理参数（包括参考图片）
            inference_params = service.prepare_inference_params(base_prompt, task_info, reference_data)
            
            # 如果是参考文件模式，添加参考图片URL
            if request_data["generation_mode"] == "reference_assets" and reference_data.get("image_urls"):
                reference_image_urls = file_processing_service.get_reference_image_urls_for_task(
                    task_info, reference_data["image_urls"]
                )
                if reference_image_urls:
                    # 使用OpenAI service支持的image_urls参数
                    if len(reference_image_urls) == 1:
                        inference_params["image_url"] = reference_image_urls[0]
                    else:
                        inference_params["image_urls"] = reference_image_urls
                    
                    self.logger.info(f"添加参考图片到推理: {len(reference_image_urls)}张", extra={
                        "task_filename": task_info.get("filename"),
                        "image_count": len(reference_image_urls)
                    })
            
            # 执行推理
            provider_name = request_data["provider"] or self.asset_settings.get_module_default_provider(request_data["module"])
            
            self.logger.info(f"开始AI推理", extra={
                "task_filename": task_info.get("filename"),  # 改名避免冲突
                "ai_provider": provider_name,  # 改名避免冲突
                "ai_model": request_data["model"],  # 改名避免冲突
                "inference_params_keys": list(inference_params.keys())
            })
            # 临时调试 - 打印推理参数
            print(f"🐛 DEBUG - AI推理开始: filename={task_info.get('filename')}, provider={provider_name}, model={request_data['model']}")
            print(f"🐛 DEBUG - 推理参数keys: {list(inference_params.keys())}")
            print(f"🐛 DEBUG - 推理参数详情: {inference_params}")
            
            ai_service = ai_service_factory.get_service(provider_name)
            result = await ai_service.run_inference(request_data["model"], inference_params)
            
            self.logger.info(f"AI推理完成", extra={
                "task_filename": task_info.get("filename"),  # 改名避免冲突
                "result_type": type(result).__name__,
                "result_length": len(str(result)) if result else 0
            })
            
            # 保存到S3
            return await self._save_image(result, task_info, request_data, task_id)
            
        except Exception as e:
            self.logger.error(f"生成单个图像失败", extra={
                "task_filename": task_info.get("filename"),  # 改名避免冲突
                "error": str(e),
                "error_type": type(e).__name__,
                "task_info": task_info
            })
            # 临时调试 - 打印异常详情
            print(f"🐛 DEBUG - 单个图像生成失败: filename={task_info.get('filename')}")
            print(f"🐛 DEBUG - 异常类型: {type(e).__name__}")
            print(f"🐛 DEBUG - 异常详情: {str(e)}")
            print(f"🐛 DEBUG - 完整任务信息: {task_info}")
            import traceback
            print(f"🐛 DEBUG - 堆栈跟踪: {traceback.format_exc()}")
            raise e  # 重新抛出异常，让上层处理
    
    def _build_prompt_with_art_style(
        self, 
        task_info: Dict[str, Any], 
        art_style_data: Dict[str, Any],
        reference_data: Dict[str, Any] = None
    ) -> str:
        """构建包含艺术风格的提示词 - 简化版，主要调用子服务"""
        
        # 调用对应子服务的方法
        service = self._get_service(task_info.get("category", "symbols"))
        return service.build_complete_prompt(task_info, art_style_data, reference_data)
    
    async def _save_image(self, generated_data: str, task_info: Dict[str, Any], request_data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """保存图像到S3"""
        import base64
        from src.application.services.external.s3_service import s3_service
        
        # 构建路径和文件名
        output_path = self.asset_settings.build_s3_output_path(
            module=request_data["module"],
            task_id=task_id,
            category=task_info["category"],
            subcategory=task_info["subcategory"]
        )
        
        # 使用任务信息中的filename
        file_name = f"{task_info['filename']}_{task_info['index']:02d}.png"
        s3_key = f"{output_path}{file_name}"
        
        # 处理数据
        try:
            if generated_data.startswith('data:'):
                header, data = generated_data.split(',', 1)
                file_content = base64.b64decode(data)
            else:
                file_content = base64.b64decode(generated_data)
        except Exception:
            file_content = generated_data.encode() if isinstance(generated_data, str) else generated_data
        
        # 上传
        upload_result = s3_service.upload_file_sync(
            file_content=file_content,
            key=s3_key,
            content_type="image/png",
            metadata={
                "task_id": task_id,
                "module": request_data["module"],
                "category": task_info["category"],
                "filename": task_info["filename"]
            }
        )
        
        return {
            "file_name": file_name,
            "s3_key": s3_key,
            "url": upload_result["url"],
            "category": task_info["category"],
            "subcategory": task_info["subcategory"],
            "filename": task_info["filename"],
            "description": task_info["description"],
            "index": task_info["index"],
            "resolution": task_info["resolution"],
            "file_size": upload_result["file_size"],
            "has_template": task_info.get("has_template", False)
        }
    
    async def _build_module_requests(self, global_config: Dict[str, Any], modules_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """构建各模块请求"""
        module_requests = {}
        
        for module_name, module_config in modules_config.items():
            # 如果模块没有指定艺术风格，使用全局艺术风格
            if "art_style" not in module_config:
                module_config["art_style"] = global_config.get("global_art_style")
            
            request_data = self._parse_request(
                module_name,
                global_config.get("model", "gpt_image_1"),
                global_config.get("generation_mode", "prompt_only"),
                module_config,
                global_config.get("provider")
            )
            
            # 为每个模块生成艺术风格
            art_style_data = await self._generate_art_style(request_data["generation_params"].art_style)
            request_data["art_style_data"] = art_style_data
            
            module_requests[module_name] = request_data
        
        return module_requests
    
    async def _execute_parallel_modules(self, module_requests: Dict[str, Dict[str, Any]], reference_data: Dict[str, Any], task_id: str) -> Dict[str, Dict[str, Any]]:
        """并发执行多个模块"""
        module_tasks = {}
        
        for module_name, request_data in module_requests.items():
            art_style_data = request_data.pop("art_style_data")  # 取出艺术风格数据
            module_tasks[module_name] = self._execute_generation(request_data, art_style_data, task_id, reference_data)
        
        results = await asyncio.gather(*module_tasks.values(), return_exceptions=True)
        
        module_results = {}
        for (module_name, result) in zip(module_tasks.keys(), results):
            if isinstance(result, Exception):
                module_results[module_name] = {
                    "module": module_name,
                    "status": "failed",
                    "error": str(result),
                    "num_outputs": 0,
                    "outputs": []
                }
            else:
                request_data = module_requests[module_name]
                service = request_data["service"]
                total_tasks = len(self._parse_generation_tasks(request_data["generation_params"]))
                
                status = "completed" if len(result) == total_tasks else ("partial_completed" if result else "failed")
                
                module_results[module_name] = {
                    "module": module_name,
                    "status": status,
                    "num_outputs": len(result),
                    "outputs": result,
                    "metadata": {
                        "total_tasks": total_tasks,
                        "completed_tasks": len(result),
                        "failed_tasks": total_tasks - len(result)
                    }
                }
        
        return module_results
    
    def _build_result(
        self, 
        outputs: List[Dict[str, Any]], 
        request_data: Dict[str, Any], 
        task_id: str, 
        start_time: datetime,
        art_style_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建生成结果"""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        service = request_data["service"]
        total_tasks = len(self._parse_generation_tasks(request_data["generation_params"]))
        status = "completed" if len(outputs) == total_tasks else ("partial_completed" if outputs else "failed")
        
        return {
            "task_id": task_id,
            "module": request_data["module"],
            "status": status,
            "num_outputs": len(outputs),
            "outputs": outputs,
            "generation_params": request_data["generation_params"].model_dump(),
            "art_style_used": {
                "mode": art_style_data.get("mode"),
                "style_prompt": art_style_data.get("style_prompt"),
                "components": art_style_data.get("components"),
                "quality_tags": art_style_data.get("quality_tags")
            },
            "model": request_data["model"],
            "provider": request_data["provider"],
            "duration": duration,
            "created_at": start_time,
            "updated_at": end_time,
            "metadata": {
                "total_tasks": total_tasks,
                "completed_tasks": len(outputs),
                "failed_tasks": total_tasks - len(outputs)
            }
        }
    
    def _build_complete_result(
        self, 
        module_results: Dict[str, Dict[str, Any]], 
        task_id: str, 
        start_time: datetime, 
        global_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建完整游戏结果"""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        total_outputs = sum(result["num_outputs"] for result in module_results.values())
        all_completed = all(result["status"] == "completed" for result in module_results.values())
        any_completed = any(result["status"] in ["completed", "partial_completed"] for result in module_results.values())
        
        overall_status = "completed" if all_completed else ("partial_completed" if any_completed else "failed")
        
        return {
            "task_id": task_id,
            "type": "complete_game_generation",
            "status": overall_status,
            "total_outputs": total_outputs,
            "module_results": module_results,
            "global_config": global_config,
            "duration": duration,
            "created_at": start_time,
            "updated_at": end_time,
            "metadata": {
                "modules_generated": list(module_results.keys()),
                "successful_modules": [k for k, v in module_results.items() if v["status"] == "completed"],
                "failed_modules": [k for k, v in module_results.items() if v["status"] == "failed"]
            }
        }
    
    # ==================== 辅助和验证方法 ====================
    
    async def validate_module_config(self, module: str, model: str, generation_params: Dict[str, Any]) -> Dict[str, Any]:
        """验证模块配置"""
        try:
            request_data = self._parse_request(module, model, "prompt_only", generation_params, None)
            tasks = self._parse_generation_tasks(request_data["generation_params"])
            
            # 验证艺术风格配置
            art_style_config = request_data["generation_params"].art_style
            art_style_validation = await self._validate_art_style_config(art_style_config)
            
            return {
                "valid": True,
                "estimated_outputs": len(tasks),
                "tasks_breakdown": {
                    "total_tasks": len(tasks),
                    "by_category": self._count_tasks_by_category(tasks)
                },
                "art_style_validation": art_style_validation
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _validate_art_style_config(self, art_style_config: ArtStyleConfig) -> Dict[str, Any]:
        """验证艺术风格配置"""
        try:
            # 尝试生成艺术风格（不实际调用AI，只验证配置）
            if art_style_config.mode == "preset":
                available_presets = await self.art_style_handler.handle_get_available_presets()
                is_valid = art_style_config.preset_theme in available_presets.get("presets", {})
                return {
                    "valid": is_valid,
                    "mode": art_style_config.mode,
                    "message": "预设主题有效" if is_valid else f"未知预设主题: {art_style_config.preset_theme}"
                }
            elif art_style_config.mode == "custom_direct":
                return {
                    "valid": True,
                    "mode": art_style_config.mode,
                    "message": "直接自定义风格配置有效"
                }
            elif art_style_config.mode in ["custom_ai_enhanced", "reference_image"]:
                # 验证AI配置
                ai_validation = self.asset_settings.validate_ai_model(
                    art_style_config.ai_provider, 
                    art_style_config.ai_model
                )
                return {
                    "valid": ai_validation,
                    "mode": art_style_config.mode,
                    "message": "AI配置有效" if ai_validation else "AI配置无效"
                }
            else:
                return {
                    "valid": False,
                    "mode": art_style_config.mode,
                    "message": f"不支持的艺术风格模式: {art_style_config.mode}"
                }
        except Exception as e:
            return {
                "valid": False,
                "mode": art_style_config.mode,
                "message": f"验证失败: {str(e)}"
            }
    
    def _count_tasks_by_category(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """按类别统计任务数量"""
        category_counts = {}
        for task in tasks:
            category = task["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts
    
    async def get_module_info(self, module: str) -> Dict[str, Any]:
        """获取模块信息"""
        service = self._get_service(module)
        service_info = service.get_service_info()
        
        # 添加艺术风格支持信息
        art_style_info = await self.art_style_handler.handle_get_available_presets()
        service_info["art_style_support"] = {
            "available_modes": ["preset", "custom_direct", "custom_ai_enhanced", "reference_image"],
            "available_presets": list(art_style_info.get("presets", {}).keys()),
            "ai_models_supported": art_style_info.get("ai_models", {})
        }
        
        return service_info
    
    async def get_config_examples(self) -> Dict[str, Any]:
        """获取配置示例"""
        return {
            "symbols": {
                "basic_preset": {
                    "art_style": {
                        "mode": "preset",
                        "preset_theme": "fantasy_medieval"
                    },
                    "base_symbols": {
                        "low_value": [
                            {
                                "filename": "ace_hearts",
                                "description": "Ornate Ace of Hearts with royal medieval design",
                                "count": 1,
                                "resolution": "512x512"
                            }
                        ]
                    }
                },
                "ai_enhanced": {
                    "art_style": {
                        "mode": "custom_ai_enhanced",
                        "custom_prompt": "Epic fantasy card symbols with mystical energy",
                        "ai_provider": "openai",
                        "ai_model": "gpt-4o"
                    },
                    "special_symbols": {
                        "wild": [
                            {
                                "filename": "dragon_wild",
                                "description": "Mystical dragon wild symbol with magical aura",
                                "count": 3
                            }
                        ]
                    }
                }
            },
            "ui": {
                "basic_preset": {
                    "art_style": {
                        "mode": "preset",
                        "preset_theme": "fantasy_medieval"
                    },
                    "buttons": {
                        "main_controls": [
                            {
                                "filename": "spin_btn",
                                "description": "Medieval style spin button with magical glow",
                                "count": 1
                            }
                        ]
                    }
                }
            },
            "backgrounds": {
                "basic_preset": {
                    "art_style": {
                        "mode": "preset",
                        "preset_theme": "fantasy_medieval"
                    },
                    "background_set": {
                        "background_scene": [
                            {
                                "filename": "main_bg",
                                "description": "Epic fantasy castle background with mystical atmosphere",
                                "count": 1,
                                "resolution": "1920x1080"
                            }
                        ]
                    }
                }
            },
            "complete_game": {
                "global_config": {
                    "global_art_style": {
                        "mode": "preset",
                        "preset_theme": "fantasy_medieval"
                    },
                    "model": "gpt_image_1"
                },
                "modules": {
                    "symbols": {
                        "base_symbols": {
                            "low_value": [
                                {
                                    "filename": "king_spades",
                                    "description": "King of Spades with medieval armor and crown",
                                    "count": 1
                                }
                            ]
                        }
                    }
                }
            }
        }
    
    def _get_service(self, module: str):
        """获取服务"""
        service = self.services.get(module)
        if not service:
            raise ValueError(f"不支持的模块: {module}")
        return service

def get_image_handler() -> ImageHandler:
    return ImageHandler()