# src/application/handlers/assets/art_style_handler.py
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, UploadFile

from src.application.handlers.handler_interface import BaseHandler
from src.application.services.assets.art_style.art_style_service import art_style_service
from src.schemas.dtos.request.art_style_request import ArtStyleRequest, ArtStyleMode, ArtStyleComponents

class ArtStyleHandler(BaseHandler):
    """艺术风格处理器 - 支持4种明确的生成模式"""
    
    def __init__(self):
        super().__init__()
        self.art_style_service = art_style_service
    
    # ===== 非AI接口 =====
    
    async def handle_preset_style_generation(self, preset_theme: str) -> Dict[str, Any]:
        """处理预设风格生成 (非AI)"""
        try:
            self.logger.info(f"处理预设风格生成: {preset_theme}")
            
            # 验证预设主题
            if not self.art_style_service.validate_preset_theme(preset_theme):
                available_themes = list(self.art_style_service.preset_themes.keys())
                raise HTTPException(
                    status_code=400, 
                    detail=f"未知的预设主题: {preset_theme}. 可用主题: {available_themes}"
                )
            
            # 生成风格提示词
            result = await self.art_style_service.generate_preset_style(preset_theme)
            
            self.logger.info("预设风格生成成功")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"预设风格生成失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"预设风格生成失败: {str(e)}")
    
    async def handle_custom_direct_style_generation(self, style_components: ArtStyleComponents) -> Dict[str, Any]:
        """处理直接自定义风格生成 (非AI)"""
        try:
            self.logger.info("处理直接自定义风格生成")
            
            # 验证组件
            if not style_components.base_prompt:
                raise HTTPException(status_code=400, detail="base_prompt不能为空")
            
            # 生成风格提示词
            result = await self.art_style_service.generate_custom_direct_style(style_components)
            
            self.logger.info("直接自定义风格生成成功") 
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"直接自定义风格生成失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"直接自定义风格生成失败: {str(e)}")
    
    # ===== AI接口 =====
    
    async def handle_custom_ai_enhanced_style_generation(
        self, 
        custom_prompt: str, 
        provider: str = "openai", 
        model: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """处理AI增强自定义风格生成 (AI)"""
        try:
            self.logger.info("处理AI增强自定义风格生成", extra={
                "provider": provider,
                "model": model
            })
            
            # 验证输入
            if not custom_prompt or not custom_prompt.strip():
                raise HTTPException(status_code=400, detail="custom_prompt不能为空")
            
            if len(custom_prompt.strip()) > 500:
                raise HTTPException(status_code=400, detail="custom_prompt长度不能超过500字符")
            
            # 生成风格提示词 (使用AI)
            result = await self.art_style_service.generate_custom_ai_enhanced_style(
                custom_prompt.strip(), provider, model
            )
            
            self.logger.info("AI增强自定义风格生成成功")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"AI增强自定义风格生成失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"AI增强自定义风格生成失败: {str(e)}")
    
    async def handle_reference_image_style_generation(
        self, 
        reference_images: List[UploadFile], 
        provider: str = "openai", 
        model: str = "gpt-4o",
        max_images: int = 3
    ) -> Dict[str, Any]:
        """处理参考图像风格生成 (AI) - 支持多图片"""
        try:
            self.logger.info(f"处理参考图像风格生成: {len(reference_images)}张图片", extra={
                "provider": provider,
                "model": model,
                "max_images": max_images
            })
            
            # 验证文件
            if not reference_images:
                raise HTTPException(status_code=400, detail="需要上传至少一张参考图像文件")
            
            # 验证图片数量
            if len(reference_images) > max_images:
                raise HTTPException(
                    status_code=400, 
                    detail=f"图片数量超过限制，最多支持{max_images}张图片，当前{len(reference_images)}张"
                )
            
            # 验证每张图片
            for i, image in enumerate(reference_images):
                # 验证文件类型
                allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}
                if image.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"第{i+1}张图片文件类型不支持: {image.content_type}. 支持的类型: {allowed_types}"
                    )
                
                # 验证文件大小 (10MB per image)
                file_content = await image.read()
                await image.seek(0)  # 重置文件指针
                
                if len(file_content) > 10 * 1024 * 1024:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"第{i+1}张图片大小超过限制: {image.filename}，文件大小不能超过10MB"
                    )
            
            # 生成风格提示词 (使用AI)
            result = await self.art_style_service.generate_reference_image_style(
                reference_images, provider, model, max_images
            )
            
            self.logger.info("参考图像风格生成成功")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"参考图像风格生成失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"参考图像风格生成失败: {str(e)}")
    
    # ===== 辅助功能接口 =====
    
    async def handle_get_available_presets(self) -> Dict[str, Any]:
        """获取可用的预设主题"""
        try:
            self.logger.info("获取可用预设主题")
            
            result = self.art_style_service.get_available_presets()
            
            self.logger.info("获取预设主题列表成功")
            return result
            
        except Exception as e:
            self.logger.error(f"获取预设主题失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取预设主题失败: {str(e)}")
    
    async def handle_get_preset_info(self, preset_theme: str) -> Dict[str, Any]:
        """获取特定预设主题信息"""
        try:
            self.logger.info(f"获取预设主题信息: {preset_theme}")
            
            theme_info = self.art_style_service.get_preset_theme_info(preset_theme)
            
            if not theme_info:
                available_themes = list(self.art_style_service.preset_themes.keys())
                raise HTTPException(
                    status_code=404, 
                    detail=f"未找到预设主题: {preset_theme}. 可用主题: {available_themes}"
                )
            
            self.logger.info(f"获取预设主题 {preset_theme} 信息成功")
            return theme_info
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"获取预设主题信息失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取预设主题信息失败: {str(e)}")
    
    async def handle_validate_style_request(self, request: ArtStyleRequest) -> Dict[str, Any]:
        """验证艺术风格请求"""
        try:
            self.logger.info(f"验证艺术风格请求: {request.mode}")
            
            validation_result = {
                "valid": True,
                "mode": request.mode.value,
                "warnings": [],
                "errors": [],
                "interface_recommendation": ""
            }
            
            # 根据模式进行验证并推荐接口
            if request.mode == ArtStyleMode.PRESET:
                validation_result["interface_recommendation"] = "POST /art-style/preset"
                if not request.preset_theme:
                    validation_result["valid"] = False
                    validation_result["errors"].append("preset模式下preset_theme不能为空")
                elif not self.art_style_service.validate_preset_theme(request.preset_theme):
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"未知的预设主题: {request.preset_theme}")
                    
            elif request.mode == ArtStyleMode.CUSTOM_DIRECT:
                validation_result["interface_recommendation"] = "POST /art-style/custom-direct"
                if not request.style_components:
                    validation_result["valid"] = False
                    validation_result["errors"].append("custom_direct模式下style_components不能为空")
                elif not request.style_components.base_prompt:
                    validation_result["valid"] = False
                    validation_result["errors"].append("style_components.base_prompt不能为空")
                else:
                    # 检查组件完整性
                    components_provided = sum([
                        bool(request.style_components.color_palette),
                        bool(request.style_components.effects),
                        bool(request.style_components.materials),
                        bool(request.style_components.lighting)
                    ])
                    
                    if components_provided == 0:
                        validation_result["warnings"].append("建议至少提供一个额外组件(color_palette, effects, materials, lighting)")
                    elif components_provided >= 3:
                        validation_result["warnings"].append("提供了丰富的风格组件，将生成高质量的艺术风格")
                    
            elif request.mode == ArtStyleMode.CUSTOM_AI_ENHANCED:
                validation_result["interface_recommendation"] = "POST /art-style/custom-ai-enhanced"
                if not request.custom_prompt:
                    validation_result["valid"] = False
                    validation_result["errors"].append("custom_ai_enhanced模式下custom_prompt不能为空")
                else:
                    if len(request.custom_prompt.strip()) > 500:
                        validation_result["valid"] = False
                        validation_result["errors"].append("custom_prompt长度不能超过500字符")
                    elif len(request.custom_prompt.strip()) < 10:
                        validation_result["warnings"].append("custom_prompt过短，建议提供更详细的风格描述")
                
                # 验证AI参数
                if request.provider and request.model:
                    try:
                        from src.application.services.external.ai_service_factory import ai_service_factory
                        ai_service = ai_service_factory.get_service(request.provider)
                        if not ai_service.validate_model(request.model):
                            validation_result["errors"].append(f"模型 {request.model} 不可用于提供商 {request.provider}")
                            validation_result["valid"] = False
                        else:
                            model_info = ai_service.get_model_info(request.model)
                            if model_info and "text_generation" not in model_info.get("capabilities", []):
                                validation_result["warnings"].append(f"模型 {request.model} 可能不支持文本生成，建议使用支持text_generation的模型")
                    except Exception as e:
                        validation_result["warnings"].append(f"AI服务验证失败: {str(e)}")
                
                validation_result["warnings"].append("此模式将使用AI进行智能增强，响应时间较长")
                    
            elif request.mode == ArtStyleMode.REFERENCE_IMAGE:
                validation_result["interface_recommendation"] = "POST /art-style/reference-image"
                
                # 验证AI参数
                if request.provider and request.model:
                    try:
                        from src.application.services.external.ai_service_factory import ai_service_factory
                        ai_service = ai_service_factory.get_service(request.provider)
                        if not ai_service.validate_model(request.model):
                            validation_result["errors"].append(f"模型 {request.model} 不可用于提供商 {request.provider}")
                            validation_result["valid"] = False
                        else:
                            model_info = ai_service.get_model_info(request.model)
                            if model_info:
                                capabilities = model_info.get("capabilities", [])
                                if "image_analysis" not in capabilities and "multimodal" not in capabilities:
                                    validation_result["errors"].append(f"模型 {request.model} 不支持图像分析，请选择支持image_analysis或multimodal的模型")
                                    validation_result["valid"] = False
                    except Exception as e:
                        validation_result["warnings"].append(f"AI服务验证失败: {str(e)}")
                
                validation_result["warnings"].extend([
                    "reference_image模式需要在请求中上传图像文件",
                    "此模式将使用AI进行图像分析，响应时间较长",
                    "支持的文件格式: JPEG, PNG, WebP, BMP",
                    "文件大小限制: 10MB"
                ])
            
            self.logger.info("验证完成")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证艺术风格请求失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")

def get_art_style_handler() -> ArtStyleHandler:
    """获取艺术风格处理器实例"""
    return ArtStyleHandler()