# src/application/services/assets/image/file_processing_service.py (增强版 - 添加S3上传和预签名URL)
import zipfile
import io
import os
import uuid
from typing import Dict, Any, List, Optional, Tuple
from fastapi import UploadFile

from src.application.services.service_interface import BaseService
from src.application.config.assets.asset_settings import get_asset_settings
from src.application.services.external.s3_service import s3_service

class FileProcessingService(BaseService):
    """文件处理服务 - 增强版，支持S3上传和预签名URL生成"""
    
    def __init__(self):
        super().__init__()
        self.asset_settings = get_asset_settings()
        self.s3_service = s3_service
        
        # S3路径前缀
        self.s3_prefix = "image_processing_temp"
        
        # 支持的图像格式
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        # 支持的压缩格式
        self.supported_archive_formats = ['.zip', '.tar']
    
    def get_service_info(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "description": "文件处理服务 - 资产参考文件处理，支持S3上传和预签名URL",
            "version": "2.1.0",
            "category": "file_processing",
            "s3_prefix": self.s3_prefix,
            "supported_features": [
                "asset_reference_processing", 
                "zip_structure_analysis",
                "prompt_generation_v2",
                "new_asset_item_format_support",
                "s3_image_upload",  # 新增
                "presigned_url_generation"  # 新增
            ],
            "supported_image_formats": self.supported_image_formats,
            "supported_archive_formats": self.supported_archive_formats
        }
    
    async def process_asset_references(self, asset_file: UploadFile, module: str) -> Dict[str, Any]:
        """
        处理资产参考文件（zip格式）- 增强版，自动上传图片到S3并生成预签名URL
        
        Args:
            asset_file: 上传的zip文件
            module: 目标模块 (symbols/ui/backgrounds)
            
        Returns:
            Dict containing:
            - asset_structure: 解析的文件结构（新格式）
            - reference_prompts: 每个文件对应的参考提示词
            - processing_info: 处理信息
            - file_mappings: 文件路径映射
            - asset_items: 转换为新元件格式的数据
            - image_urls: 上传到S3的图片预签名URL映射  # 新增
        """
        
        self.logger.info("处理资产参考文件", extra={
            "filename": asset_file.filename,
            "module": module,
            "content_type": asset_file.content_type
        })
        
        try:
            # 验证文件类型
            if not self._is_valid_archive_file(asset_file):
                raise ValueError(f"不支持的压缩格式: {asset_file.content_type}")
            
            # 读取zip文件
            file_content = await asset_file.read()
            
            # 解析zip结构并上传图片到S3
            asset_structure, file_mappings, image_urls = await self._parse_zip_structure_with_s3_upload(file_content)
            
            # 生成参考提示词映射
            reference_prompts = self._generate_reference_prompts_v2(asset_structure, module)
            
            # 转换为新的元件格式
            asset_items = self._convert_to_asset_items(asset_structure)
            
            # 验证结构是否符合预期
            validation_result = self._validate_asset_structure(asset_structure, module)
            
            result = {
                "asset_structure": asset_structure,
                "reference_prompts": reference_prompts,
                "file_mappings": file_mappings,
                "asset_items": asset_items,
                "image_urls": image_urls,  # 新增：图片预签名URL映射
                "processing_info": {
                    "total_files": len([f for files in asset_structure.values() for subfiles in files.values() for f in subfiles]),
                    "image_files": len(image_urls),  # 新增：图片文件数量
                    "categories": list(asset_structure.keys()),
                    "validation": validation_result,
                    "format_version": "2.1",
                    "supports_new_format": True,
                    "s3_upload_enabled": True  # 新增
                },
                "processing_success": True
            }
            
            self.logger.info("资产参考文件处理完成", extra={
                "filename": asset_file.filename,
                "module": module,
                "total_files": result["processing_info"]["total_files"],
                "image_files": result["processing_info"]["image_files"],
                "categories": result["processing_info"]["categories"]
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"资产参考文件处理失败: {str(e)}", extra={
                "filename": asset_file.filename,
                "module": module
            })
            return {
                "processing_success": False,
                "error": str(e),
                "asset_structure": {},
                "reference_prompts": {},
                "file_mappings": {},
                "asset_items": {},
                "image_urls": {}
            }
    
    async def _parse_zip_structure_with_s3_upload(self, zip_content: bytes) -> Tuple[Dict[str, Dict[str, List[Dict[str, Any]]]], Dict[str, str], Dict[str, str]]:
        """解析zip文件结构并上传图片到S3 - 新增方法"""
        asset_structure = {}
        file_mappings = {}
        image_urls = {}  # 新增：存储图片的预签名URL
        
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                for file_path in file_list:
                    if file_path.endswith('/'):  # 跳过目录
                        continue
                    
                    # 解析路径: category/subcategory/filename
                    path_parts = file_path.split('/')
                    if len(path_parts) >= 3:
                        category = path_parts[0]
                        subcategory = path_parts[1]
                        full_filename = path_parts[-1]
                        
                        # 提取文件名（去掉扩展名）作为filename
                        filename_without_ext = os.path.splitext(full_filename)[0]
                        
                        # 尝试从文件名中提取描述信息
                        description = self._extract_description_from_filename(filename_without_ext)
                        
                        # 检测分辨率（如果文件名包含分辨率信息）
                        resolution = self._extract_resolution_from_filename(filename_without_ext)
                        
                        # 检查是否为图片文件
                        is_image = self._is_image_file_by_extension(full_filename)
                        
                        # 如果是图片文件，上传到S3并生成预签名URL
                        presigned_url = None
                        if is_image:
                            try:
                                # 读取图片文件内容
                                file_content = zip_ref.read(file_path)
                                
                                # 上传到S3并生成预签名URL
                                presigned_url = await self._upload_image_to_s3_and_get_url(
                                    file_content, 
                                    full_filename, 
                                    category, 
                                    subcategory
                                )
                                
                                # 保存URL映射
                                mapping_key = f"{category}.{subcategory}.{filename_without_ext}"
                                image_urls[mapping_key] = presigned_url
                                
                                self.logger.debug(f"图片上传成功: {file_path} -> {presigned_url[:50]}...")
                                
                            except Exception as e:
                                self.logger.error(f"图片上传失败: {file_path}, 错误: {str(e)}")
                                # 不阻断处理流程，继续处理其他文件
                        
                        # 构建结构
                        if category not in asset_structure:
                            asset_structure[category] = {}
                        if subcategory not in asset_structure[category]:
                            asset_structure[category][subcategory] = []
                        
                        file_info = {
                            "filename": filename_without_ext,  # 作为唯一标识
                            "full_filename": full_filename,   # 完整文件名
                            "description": description,       # 提取的描述
                            "path": file_path,               # 完整路径
                            "resolution": resolution,        # 检测到的分辨率
                            "is_image": is_image,
                            "count": 1,  # 默认数量
                            "presigned_url": presigned_url   # 新增：预签名URL
                        }
                        
                        asset_structure[category][subcategory].append(file_info)
                        
                        # 建立文件路径映射
                        mapping_key = f"{category}.{subcategory}.{filename_without_ext}"
                        file_mappings[mapping_key] = file_path
                        
                    else:
                        self.logger.warning(f"跳过路径格式不正确的文件: {file_path}")
        
        except zipfile.BadZipFile as e:
            self.logger.error(f"无效的ZIP文件: {str(e)}")
            raise ValueError("无效的ZIP文件格式")
        
        return asset_structure, file_mappings, image_urls
    
    async def _upload_image_to_s3_and_get_url(
        self, 
        file_content: bytes, 
        filename: str, 
        category: str, 
        subcategory: str
    ) -> str:
        """上传图片到S3并生成预签名URL - 参考art style实现"""
        
        # 生成唯一的S3键
        file_ext = os.path.splitext(filename)[1].lower()
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"{self.s3_prefix}/{category}/{subcategory}/{unique_id}_{filename}"
        
        # 确定内容类型
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        content_type = content_type_map.get(file_ext, 'image/jpeg')
        
        # 上传到S3（使用同步方法）
        upload_result = self.s3_service.upload_file_sync(
            file_content=file_content,
            key=s3_key,
            content_type=content_type,
            metadata={
                "original_filename": filename,
                "category": category,
                "subcategory": subcategory,
                "upload_source": "file_processing_service"
            }
        )
        
        if not upload_result.get("success", True):
            raise Exception(f"S3上传失败: {upload_result.get('error', 'Unknown error')}")
        
        # 生成预签名URL（有效期1小时）
        presigned_url = self.s3_service.generate_presigned_url(
            key=s3_key,
            expiration=3600,  # 1小时
            method="GET"
        )
        
        self.logger.info(f"图片上传并生成预签名URL成功", extra={
            "s3_key": s3_key,
            "content_type": content_type,
            "file_size": len(file_content),
            "url_preview": presigned_url[:50] + "..."
        })
        
        return presigned_url
    
    def get_reference_image_urls_for_task(
        self, 
        task_info: Dict[str, Any], 
        image_urls: Dict[str, str]
    ) -> List[str]:
        """
        根据任务信息获取对应的参考图片URL列表 - 新增方法
        
        Args:
            task_info: 包含category, subcategory, filename的任务信息
            image_urls: 从process_asset_references返回的图片URL映射
            
        Returns:
            对应的图片URL列表
        """
        
        category = task_info.get("category")
        subcategory = task_info.get("subcategory")
        filename = task_info.get("filename")
        
        # 构建查找路径，按优先级排序
        lookup_paths = [
            f"{category}.{subcategory}.{filename}",  # 精确匹配
            f"{category}.{subcategory}",              # 子分类匹配
            f"{category}",                            # 分类匹配
        ]
        
        found_urls = []
        
        for path in lookup_paths:
            if path in image_urls:
                found_urls.append(image_urls[path])
                self.logger.debug(f"找到参考图片URL", extra={
                    "filename": filename,
                    "lookup_path": path,
                    "url_preview": image_urls[path][:50] + "..."
                })
        
        # 如果没有找到精确匹配，尝试模糊匹配
        if not found_urls:
            for key, url in image_urls.items():
                if (category in key and subcategory in key) or filename in key:
                    found_urls.append(url)
                    self.logger.debug(f"模糊匹配找到参考图片URL", extra={
                        "filename": filename,
                        "matched_key": key
                    })
        
        if not found_urls:
            self.logger.debug(f"未找到参考图片URL", extra={
                "filename": filename,
                "category": category,
                "subcategory": subcategory,
                "available_keys": list(image_urls.keys())
            })
        
        return found_urls
    
    # === 保持原有方法不变 ===
    
    def get_reference_prompt_for_task(
        self, 
        task_info: Dict[str, Any], 
        reference_prompts: Dict[str, Any]
    ) -> Optional[str]:
        """根据任务信息获取对应的参考提示词"""
        
        category = task_info.get("category")
        subcategory = task_info.get("subcategory")
        filename = task_info.get("filename")
        
        # 构建查找路径，按优先级排序
        lookup_paths = [
            f"{category}.{subcategory}.{filename}",  # 精确匹配（filename）
            f"{category}.{subcategory}",              # 子分类匹配
            f"{category}",                            # 分类匹配
        ]
        
        for path in lookup_paths:
            if path in reference_prompts:
                reference_prompt = reference_prompts[path]
                self.logger.debug(f"找到参考提示词", extra={
                    "filename": filename,
                    "lookup_path": path,
                    "prompt_preview": reference_prompt[:100] + "..."
                })
                return reference_prompt
        
        self.logger.debug(f"未找到参考提示词", extra={
            "filename": filename,
            "category": category,
            "subcategory": subcategory,
            "available_paths": list(reference_prompts.keys())
        })
        
        return None
    
    def _extract_description_from_filename(self, filename: str) -> str:
        """从文件名中提取描述信息"""
        # 移除常见的分辨率模式
        import re
        clean_filename = re.sub(r'_\d+x\d+$', '', filename)
        clean_filename = re.sub(r'_\d+$', '', clean_filename)  # 移除末尾数字
        
        # 将下划线和连字符替换为空格，转换为更自然的描述
        description = clean_filename.replace('_', ' ').replace('-', ' ')
        
        # 首字母大写
        description = ' '.join(word.capitalize() for word in description.split())
        
        return description if description else filename
    
    def _extract_resolution_from_filename(self, filename: str) -> Optional[str]:
        """从文件名中提取分辨率信息"""
        import re
        # 查找类似 1024x1024 的模式
        resolution_match = re.search(r'(\d+x\d+)', filename)
        if resolution_match:
            return resolution_match.group(1)
        return None
    
    def _convert_to_asset_items(self, asset_structure: Dict[str, Any]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """将文件结构转换为新的元件格式"""
        asset_items = {}
        
        for category, subcategories in asset_structure.items():
            asset_items[category] = {}
            for subcategory, files in subcategories.items():
                asset_items[category][subcategory] = []
                
                for file_info in files:
                    # 转换为ImageAssetItem格式
                    item = {
                        "filename": file_info["filename"],
                        "description": file_info["description"],
                        "count": file_info.get("count", 1),
                        "resolution": file_info.get("resolution")  # 可能为None
                    }
                    # 移除None值
                    item = {k: v for k, v in item.items() if v is not None}
                    asset_items[category][subcategory].append(item)
        
        return asset_items
    
    def _generate_reference_prompts_v2(self, asset_structure: Dict[str, Any], module: str) -> Dict[str, str]:
        """生成参考提示词映射 - v2版本，使用描述信息"""
        reference_prompts = {}
        
        for category, subcategories in asset_structure.items():
            for subcategory, files in subcategories.items():
                for file_info in files:
                    filename = file_info["filename"]
                    description = file_info["description"]
                    
                    # 构建参考提示词，使用提取的描述
                    prompt = self._build_reference_prompt_v2(
                        module, category, subcategory, filename, description, file_info
                    )
                    
                    # 创建多层级的映射
                    reference_prompts[f"{category}.{subcategory}.{filename}"] = prompt
                    
                    # 如果是该子分类的第一个文件，也创建子分类级别的映射
                    subcategory_key = f"{category}.{subcategory}"
                    if subcategory_key not in reference_prompts:
                        reference_prompts[subcategory_key] = prompt
                    
                    # 如果是该分类的第一个文件，也创建分类级别的映射
                    category_key = category
                    if category_key not in reference_prompts:
                        reference_prompts[category_key] = prompt
        
        return reference_prompts
    
    def _build_reference_prompt_v2(
        self, 
        module: str, 
        category: str, 
        subcategory: str, 
        filename: str,
        description: str,
        file_info: Dict[str, Any]
    ) -> str:
        """构建单个文件的参考提示词 - v2版本"""
        
        # 基础提示词模板
        base_templates = {
            "symbols": "Create a slot machine symbol for {description}",
            "ui": "Create a user interface element for {description}",
            "backgrounds": "Create a background scene for {description}"
        }
        
        base_prompt = base_templates.get(module, f"Create a {module} asset for {description}")
        
        # 添加分类信息
        prompt_parts = [
            base_prompt.format(description=description),
            f"in {category} category",
            f"{subcategory} subcategory"
        ]
        
        # 添加分辨率信息（如果有）
        if file_info.get("resolution"):
            prompt_parts.append(f"with {file_info['resolution']} resolution")
        
        # 添加参考指导
        if file_info.get("is_image") and file_info.get("presigned_url"):
            prompt_parts.append("matching the style and composition of the reference image")
        else:
            prompt_parts.append(f"based on the reference file {file_info['full_filename']}")
        
        # 添加一致性指导
        prompt_parts.extend([
            "Maintain consistent visual style with other assets",
            "Keep the same artistic approach and quality level"
        ])
        
        return ", ".join(prompt_parts)
    
    # === 其他辅助方法保持不变 ===
    
    def _is_valid_archive_file(self, file: UploadFile) -> bool:
        """验证是否为有效的压缩文件"""
        valid_content_types = [
            'application/zip', 
            'application/x-zip-compressed',
            'application/octet-stream'
        ]
        
        if file.content_type in valid_content_types:
            return True
        
        if file.filename:
            file_ext = os.path.splitext(file.filename.lower())[1]
            return file_ext in self.supported_archive_formats
        
        return False
    
    def _validate_asset_structure(self, asset_structure: Dict[str, Any], module: str) -> Dict[str, Any]:
        """验证资产结构是否符合模块要求"""
        
        # 获取模块期望的分类结构
        module_config = self.asset_settings.get_module_config(module)
        expected_categories = module_config.get("categories", {})
        
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "missing_categories": [],
            "unexpected_categories": [],
            "coverage": {},
            "format_version": "2.1"
        }
        
        # 检查缺失的分类
        for expected_category in expected_categories.keys():
            if expected_category not in asset_structure:
                validation_result["missing_categories"].append(expected_category)
                validation_result["warnings"].append(f"缺少期望的分类: {expected_category}")
        
        # 检查意外的分类
        for actual_category in asset_structure.keys():
            if actual_category not in expected_categories:
                validation_result["unexpected_categories"].append(actual_category)
                validation_result["warnings"].append(f"包含未知的分类: {actual_category}")
        
        # 计算覆盖率
        for category, subcategories in asset_structure.items():
            if category in expected_categories:
                expected_subcategories = expected_categories[category].get("subcategories", {})
                coverage_info = {
                    "expected": list(expected_subcategories.keys()),
                    "actual": list(subcategories.keys()),
                    "coverage_percentage": 0,
                    "asset_items_count": sum(len(items) for items in subcategories.values()),
                    "image_items_count": sum(
                        len([item for item in items if item.get("is_image", False)]) 
                        for items in subcategories.values()
                    )
                }
                
                if expected_subcategories:
                    covered = len(set(subcategories.keys()) & set(expected_subcategories.keys()))
                    coverage_info["coverage_percentage"] = (covered / len(expected_subcategories)) * 100
                
                validation_result["coverage"][category] = coverage_info
        
        # 如果有错误，标记为无效
        if validation_result["errors"]:
            validation_result["is_valid"] = False
        
        return validation_result
    
    def _is_image_file_by_extension(self, filename: str) -> bool:
        """根据扩展名判断是否为图像文件"""
        if not filename:
            return False
        
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in self.supported_image_formats

# 全局实例
file_processing_service = FileProcessingService()