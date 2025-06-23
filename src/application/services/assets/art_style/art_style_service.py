# src/application/services/assets/art_style_service.py (使用预签名URL)
from typing import Dict, Any, Optional, List
from fastapi import UploadFile
from datetime import datetime
import uuid
import json
import asyncio

from src.application.services.service_interface import BaseService
from src.application.services.external.ai_service_factory import ai_service_factory
from src.schemas.dtos.request.art_style_request import ArtStyleMode, ArtStyleComponents
from src.application.services.external.s3_service import s3_service

class ArtStyleService(BaseService):
    """艺术风格服务 - 使用预签名URL解决方案"""
    
    def __init__(self):
        super().__init__()
        
        # S3存储配置
        self.s3_prefix = "art-style"  # 艺术风格模块专用路径
        
        # 预设风格主题库 (保持不变)
        self.preset_themes = {
            "fantasy_medieval": {
                "name": "Fantasy Medieval",
                "base_prompt": "fantasy art, medieval style, detailed illustration",
                "color_palette": "rich gold, deep red, royal blue, ancient bronze",
                "effects": "glowing magical effect, mystical aura",
                "materials": "aged parchment, worn metal, mystical gems",
                "lighting": "warm torchlight, mysterious shadows",
                "description": "Medieval fantasy style with rich colors and magical elements"
            },
            "cyberpunk_neon": {
                "name": "Cyberpunk Neon", 
                "base_prompt": "cyberpunk style, neon aesthetic, futuristic design",
                "color_palette": "electric blue, hot pink, acid green, chrome silver",
                "effects": "neon glow, holographic shimmer, digital distortion",
                "materials": "sleek metal, glass panels, LED strips",
                "lighting": "harsh neon lighting, dramatic shadows",
                "description": "Futuristic cyberpunk with neon colors and high-tech aesthetics"
            },
            "steampunk_bronze": {
                "name": "Steampunk Bronze",
                "base_prompt": "steampunk style, Victorian era, mechanical design",
                "color_palette": "brass, copper, bronze, dark leather brown",
                "effects": "steam effects, gear mechanisms, clockwork details", 
                "materials": "polished brass, worn leather, riveted metal",
                "lighting": "warm gas lamp glow, industrial shadows",
                "description": "Victorian steampunk with brass and mechanical elements"
            },
            "cosmic_space": {
                "name": "Cosmic Space",
                "base_prompt": "cosmic space theme, sci-fi aesthetic, stellar design",
                "color_palette": "deep purple, starlight blue, cosmic gold, void black",
                "effects": "stellar glow, nebula patterns, cosmic energy",
                "materials": "crystalline structures, energy fields, metallic hull",
                "lighting": "starlight, cosmic radiation glow",
                "description": "Space-themed design with cosmic colors and stellar effects"
            },
            "nature_organic": {
                "name": "Nature Organic",
                "base_prompt": "organic nature style, natural elements, earthy design",
                "color_palette": "forest green, earth brown, sky blue, sunset orange",
                "effects": "natural texture, organic growth patterns, flowing forms",
                "materials": "wood grain, stone texture, flowing water",
                "lighting": "natural sunlight, forest dappled light",
                "description": "Natural organic style with earth tones and organic shapes"
            },
            "dark_gothic": {
                "name": "Dark Gothic",
                "base_prompt": "dark gothic style, ornate details, dramatic atmosphere",
                "color_palette": "deep black, blood red, silver, dark purple",
                "effects": "dramatic shadows, ornate patterns, gothic details",
                "materials": "carved stone, wrought iron, stained glass",
                "lighting": "candlelight, moonlight, dramatic chiaroscuro",
                "description": "Gothic architecture style with dark colors and ornate details"
            },
            "chinese_traditional": {
                "name": "Chinese Traditional",
                "base_prompt": "traditional Chinese art style, ink painting, classical design",
                "color_palette": "imperial red, golden yellow, jade green, ink black",
                "effects": "ink wash effects, flowing brush strokes, traditional patterns",
                "materials": "silk texture, bamboo elements, jade stones, rice paper",
                "lighting": "soft natural light, traditional lantern glow",
                "description": "Traditional Chinese art with classical colors and cultural elements"
            },
            "space_scifi": {
                "name": "Space Sci-Fi", 
                "base_prompt": "space science fiction, futuristic technology, stellar environment",
                "color_palette": "electric blue, plasma purple, tech silver, void black",
                "effects": "energy fields, holographic displays, stellar phenomena",
                "materials": "advanced alloys, energy crystals, quantum materials",
                "lighting": "artificial tech lighting, star field glow, energy emissions",
                "description": "Advanced sci-fi space theme with high-tech elements and cosmic setting"
            }
        }
        
        # AI服务的系统提示词
        self.image_analysis_system_prompt = """
        You are an expert art director analyzing visual styles for game asset generation.
        
        When analyzing an image, provide a detailed artistic style description that can be used as a prompt for AI image generation.
        
        Focus on these elements:
        1. Overall artistic style (realistic, cartoon, fantasy, etc.)
        2. Color palette and mood
        3. Lighting and atmosphere
        4. Texture and materials  
        5. Visual effects or special elements
        6. Drawing/rendering technique
        
        Format your response as a single, comma-separated prompt suitable for image generation.
        Focus only on visual style elements that should be replicated, not specific objects or content.
        Keep it concise but descriptive (under 200 words).
        """
    
    def get_service_info(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "description": "艺术风格服务 - 使用预签名URL安全方案",
            "version": "2.1.0",
            "category": "art_style",
            "s3_prefix": self.s3_prefix,
            "supported_modes": {
                "non_ai_modes": ["preset", "custom_direct"],
                "ai_modes": ["custom_ai_enhanced", "reference_image"]
            },
            "supported_features": [
                "preset_style_generation",
                "custom_direct_components", 
                "ai_enhanced_prompts",
                "reference_image_analysis",
                "multi_image_analysis",
                "presigned_url_security"  # 新增安全特性
            ],
            "available_presets": list(self.preset_themes.keys()),
            "total_presets": len(self.preset_themes)
        }
    
    # ===== 非AI接口保持不变 =====
    
    async def generate_preset_style(self, preset_theme: str) -> Dict[str, Any]:
        """生成预设风格 (非AI)"""
        try:
            self.logger.info(f"生成预设风格: {preset_theme}")
            
            if not preset_theme or preset_theme not in self.preset_themes:
                available_themes = list(self.preset_themes.keys())
                raise ValueError(f"未知的预设主题: {preset_theme}. 可用主题: {available_themes}")
            
            theme_config = self.preset_themes[preset_theme]
            
            # 构建完整的风格提示词
            style_components = [
                theme_config["base_prompt"],
                theme_config["color_palette"], 
                theme_config["effects"],
                theme_config.get("materials", ""),
                theme_config.get("lighting", ""),
                "isolated on transparent background",
                "centered design, game asset style",
                "high quality, professional design"
            ]
            
            # 过滤空字符串
            style_components = [comp for comp in style_components if comp.strip()]
            style_prompt = ", ".join(style_components)
            
            self.logger.info(f"预设风格生成完成: {preset_theme}")
            
            return {
                "style_prompt": style_prompt,
                "mode": "preset",
                "theme_name": preset_theme,
                "components": {
                    "base_prompt": theme_config["base_prompt"],
                    "color_palette": theme_config["color_palette"],
                    "effects": theme_config["effects"],
                    "materials": theme_config.get("materials"),
                    "lighting": theme_config.get("lighting"),
                    "description": theme_config["description"]
                },
                "quality_tags": "high quality, game asset style, professional design"
            }
            
        except Exception as e:
            self.logger.error(f"预设风格生成失败: {str(e)}")
            raise
    
    async def generate_custom_direct_style(self, style_components: ArtStyleComponents) -> Dict[str, Any]:
        """生成直接自定义风格 (非AI)"""
        try:
            self.logger.info("生成直接自定义风格")
            
            components_dict = style_components.dict()
            
            # 构建完整的风格提示词
            style_parts = [
                components_dict["base_prompt"],
                components_dict.get("color_palette", ""),
                components_dict.get("effects", ""),
                components_dict.get("materials", ""),
                components_dict.get("lighting", ""),
                "isolated on transparent background",
                "centered design, game asset style", 
                "high quality, professional design"
            ]
            
            # 过滤空字符串
            style_parts = [part for part in style_parts if part and part.strip()]
            style_prompt = ", ".join(style_parts)
            
            self.logger.info("直接自定义风格生成完成")
            
            return {
                "style_prompt": style_prompt,
                "mode": "custom_direct",
                "components": {
                    "base_prompt": components_dict["base_prompt"],
                    "color_palette": components_dict.get("color_palette", ""),
                    "effects": components_dict.get("effects", ""),
                    "materials": components_dict.get("materials"),
                    "lighting": components_dict.get("lighting")
                },
                "custom_input": "structured_components",
                "quality_tags": "high quality, game asset style, professional design"
            }
            
        except Exception as e:
            self.logger.error(f"直接自定义风格生成失败: {str(e)}")
            raise
    
    # ===== AI接口 =====
    
    async def generate_custom_ai_enhanced_style(
        self, 
        custom_prompt: str, 
        provider: str = "openai", 
        model: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """生成AI增强自定义风格 (AI) - 一次调用完成所有处理"""
        try:
            self.logger.info("生成AI增强自定义风格", extra={
                "provider": provider,
                "model": model
            })
            
            # 验证AI服务和模型
            ai_service = ai_service_factory.get_service(provider)
            if not ai_service.validate_model(model):
                available_models = list(ai_service.available_models.keys())
                raise ValueError(f"模型 {model} 不可用于提供商 {provider}. 可用模型: {available_models}")
            
            # 验证模型能力
            model_info = ai_service.get_model_info(model)
            if model_info and "text_generation" not in model_info.get("capabilities", []):
                raise ValueError(f"模型 {model} 不支持文本生成能力")
            
            custom_prompt = custom_prompt.strip()
            
            # 一次性AI调用：分析输入并生成结构化组件和增强提示词
            ai_result = await self._generate_enhanced_style_with_components(custom_prompt, provider, model)
            
            # 构建最终提示词
            enhanced_components = ai_result["components"]
            style_parts = [
                enhanced_components.get("base_prompt", ""),
                enhanced_components.get("color_palette", ""),
                enhanced_components.get("effects", ""),
                enhanced_components.get("materials", ""),
                enhanced_components.get("lighting", ""),
                "isolated on transparent background",
                "centered design, game asset style",
                "high quality, professional design"
            ]
            
            # 过滤空字符串
            style_parts = [part for part in style_parts if part and part.strip()]
            final_prompt = ", ".join(style_parts)
            
            self.logger.info("AI增强自定义风格生成完成")
            
            return {
                "style_prompt": final_prompt,
                "mode": "custom_ai_enhanced",
                "components": enhanced_components,
                "custom_input": custom_prompt,
                "enhanced_result": ai_result.get("enhanced_prompt", ""),
                "ai_processing": {
                    "single_call_processing": True,
                    "provider": provider,
                    "model": model
                },
                "quality_tags": "high quality, game asset style, professional design"
            }
            
        except Exception as e:
            self.logger.error(f"AI增强自定义风格生成失败: {str(e)}")
            raise
    
    async def generate_reference_image_style(
        self, 
        reference_images: List[UploadFile], 
        provider: str = "openai", 
        model: str = "gpt-4o",
        max_images: int = 3
    ) -> Dict[str, Any]:
        """生成参考图像风格 (AI) - 支持多图片，使用预签名URL"""
        upload_results = []
        try:
            self.logger.info(f"生成参考图像风格: {len(reference_images)}张图片", extra={
                "provider": provider,
                "model": model,
                "max_images": max_images
            })
            
            # 验证AI服务和模型
            ai_service = ai_service_factory.get_service(provider)
            if not ai_service.validate_model(model):
                available_models = list(ai_service.available_models.keys())
                raise ValueError(f"模型 {model} 不可用于提供商 {provider}. 可用模型: {available_models}")
            
            # 验证模型能力
            model_info = ai_service.get_model_info(model)
            if model_info:
                capabilities = model_info.get("capabilities", [])
                if "image_analysis" not in capabilities and "multimodal" not in capabilities:
                    raise ValueError(f"模型 {model} 不支持图像分析能力")
            
            if not reference_images:
                raise ValueError("需要提供至少一张参考图像")
            
            # 限制图片数量
            if len(reference_images) > max_images:
                self.logger.warning(f"图片数量超限({len(reference_images)} > {max_images})，只处理前{max_images}张")
                reference_images = reference_images[:max_images]
            
            # 上传所有图像到S3并生成预签名URL
            presigned_urls = []
            
            for i, image in enumerate(reference_images):
                upload_result = await self._upload_temp_image(image, suffix=f"_img_{i}")
                upload_results.append(upload_result)
                presigned_urls.append(upload_result["presigned_url"])
                self.logger.info(f"上传图片 {i+1}/{len(reference_images)}: {image.filename}")
            
            # 使用AI服务分析图像风格 - 使用预签名URL
            analysis_result = await self._analyze_images_and_generate_components(
                presigned_urls, provider, model
            )
            
            # 构建最终提示词
            enhanced_components = analysis_result["components"]
            style_parts = [
                analysis_result.get("style_description", ""),
                enhanced_components.get("color_palette", ""),
                enhanced_components.get("effects", ""),
                enhanced_components.get("materials", ""),
                enhanced_components.get("lighting", ""),
                "isolated on transparent background",
                "centered design, game asset style",
                "high quality, professional design"
            ]
            
            # 过滤空字符串
            style_parts = [part for part in style_parts if part and part.strip()]
            enhanced_style = ", ".join(style_parts)
            
            filenames = [img.filename for img in reference_images]
            self.logger.info(f"参考图像分析完成: {len(reference_images)}张图片")
            
            return {
                "style_prompt": enhanced_style,
                "mode": "reference_image",
                "components": enhanced_components,
                "analysis_result": analysis_result.get("style_description", ""),
                "reference_filenames": filenames,
                "image_count": len(reference_images),
                "ai_processing": {
                    "image_analysis": True,
                    "single_call_processing": True,
                    "provider": provider,
                    "model": model,
                    "presigned_url_used": True,  # 标识使用了预签名URL
                    "multi_image": len(reference_images) > 1
                },
                "quality_tags": "high quality, game asset style, professional design"
            }
            
        except Exception as e:
            self.logger.error(f"参考图像分析失败: {str(e)}")
            raise
        finally:
            # 清理所有临时图像
            for upload_result in upload_results:
                await self._cleanup_temp_image(upload_result["s3_key"])
    
    # ===== S3辅助方法（使用预签名URL）=====
    
    async def _upload_temp_image(self, image_file: UploadFile, suffix: str = "") -> Dict[str, Any]:
        """上传临时图像到S3并生成预签名URL"""
        try:
            # 生成任务ID和路径
            task_id = str(uuid.uuid4())
            date_folder = datetime.utcnow().strftime("%Y-%m-%d")
            temp_prefix = f"{self.s3_prefix}/temp/{date_folder}/{task_id}"
            
            # 读取图像内容
            image_content = await image_file.read()
            
            # 生成文件名（添加后缀以区分多张图片）
            original_name = image_file.filename or "image"
            if suffix:
                name_parts = original_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    file_name = f"{name_parts[0]}{suffix}.{name_parts[1]}"
                else:
                    file_name = f"{original_name}{suffix}"
            else:
                file_name = original_name
            
            # 使用事件循环运行同步上传方法（不设置ACL）
            loop = asyncio.get_event_loop()
            upload_result = await loop.run_in_executor(
                None,
                lambda: s3_service.upload_file_sync(
                    file_content=image_content,
                    file_name=file_name,
                    prefix=temp_prefix,
                    content_type=image_file.content_type,
                    # 移除ACL设置，使用默认的private
                    metadata={
                        'purpose': 'art-style-temp-image',
                        'original_filename': original_name,
                        'task_id': task_id
                    }
                )
            )
            
            # 生成预签名URL（有效期1小时）
            presigned_url = s3_service.generate_presigned_url(
                key=upload_result["key"],
                expiration=3600,  # 1小时
                http_method='GET'
            )
            
            self.logger.info(f"临时图像上传成功，已生成预签名URL: {upload_result['key']}")
            
            return {
                "presigned_url": presigned_url,
                "s3_key": upload_result["key"],
                "task_id": task_id
            }
            
        except Exception as e:
            self.logger.error(f"临时图像上传失败: {str(e)}")
            raise
    
    async def _cleanup_temp_image(self, s3_key: str) -> bool:
        """清理临时图像 - 使用同步方法"""
        try:
            # 使用事件循环运行同步删除方法
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                s3_service.delete_file,
                s3_key
            )
            
            if success:
                self.logger.info(f"临时图像清理成功: {s3_key}")
            else:
                self.logger.warning(f"临时图像清理失败: {s3_key}")
            return success
        except Exception as e:
            self.logger.error(f"临时图像清理异常: {str(e)}")
            return False
    
    # ===== AI辅助方法保持不变 =====
    
    async def _generate_enhanced_style_with_components(
        self, 
        custom_prompt: str, 
        provider: str = "openai", 
        model: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """一次性AI调用：分析输入并生成结构化组件和增强提示词"""
        enhancement_prompt = f"""
        You are an expert art director specializing in game asset visual styles.
        
        Analyze this artistic style description and generate both structured components and an enhanced prompt:
        
        Input: "{custom_prompt}"
        
        Please provide a JSON response with these exact keys:
        {{
            "components": {{
                "base_prompt": "Core artistic style and technique (enhanced)",
                "color_palette": "Specific colors and color relationships",
                "effects": "Visual effects, lighting effects, special elements",
                "materials": "Texture, material properties, surface qualities",
                "lighting": "Lighting style, mood, atmosphere",
                "description": "Brief style description"
            }},
            "enhanced_prompt": "Complete enhanced comma-separated style description suitable for AI image generation"
        }}
        
        Requirements for enhancement:
        1. Keep the core artistic intent from the input
        2. Add specific visual details (colors, lighting, materials, effects)
        3. Make it suitable for game asset generation
        4. Use professional art terminology
        5. Focus on visual style, not content
        6. Enhanced prompt should be under 150 words
        
        If a component category isn't mentioned in the input, provide reasonable defaults based on the overall style.
        """
        
        ai_service = ai_service_factory.get_service(provider)
        
        # 构建推理参数
        inference_params = {
            "prompt": enhancement_prompt,
            "max_tokens": 500,
            "temperature": 0.7,
            "system_prompt": "You are an expert art director specializing in game asset visual styles."
        }
        
        # 只有支持的模型才设置response_format
        if model in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]:
            inference_params["response_format"] = {"type": "json_object"}
        
        result = await ai_service.run_inference(model, inference_params)
        
        # 解析JSON
        try:
            parsed_result = json.loads(result.strip())
            
            # 验证必需结构
            if "components" not in parsed_result:
                raise ValueError("AI响应缺少 'components' 字段")
            
            components = parsed_result["components"]
            
            # 验证必需字段
            required_fields = ["base_prompt", "color_palette", "effects", "materials", "lighting", "description"]
            missing_fields = []
            
            for field in required_fields:
                if field not in components:
                    missing_fields.append(field)
            
            if missing_fields:
                raise ValueError(f"AI响应的components缺少必需字段: {missing_fields}")
            
            # 确保base_prompt不为空
            if not components.get("base_prompt") or not components["base_prompt"].strip():
                components["base_prompt"] = custom_prompt
            
            # 确保其他字段为字符串
            for field in ["color_palette", "effects", "materials", "lighting", "description"]:
                if components[field] is None:
                    components[field] = ""
            
            return {
                "components": components,
                "enhanced_prompt": parsed_result.get("enhanced_prompt", custom_prompt)
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"AI响应不是有效的JSON格式: {str(e)}")
    
    async def _analyze_images_and_generate_components(
        self,
        image_urls: List[str],
        provider: str = "openai", 
        model: str = "gpt-4o"
    ) -> Dict[str, Any]:
        """一次性分析多张图像并生成结构化组件"""
        # 根据图片数量调整分析prompt
        image_count = len(image_urls)
        if image_count == 1:
            analysis_intro = "Analyze this image and extract its artistic style characteristics"
            style_desc = "Complete comma-separated style description"
        else:
            analysis_intro = f"Analyze these {image_count} images and extract a unified artistic style that combines elements from all images"
            style_desc = "Unified comma-separated style description that synthesizes elements from all images"
        
        analysis_prompt = f"""
        {analysis_intro} for game asset generation.
        
        Please provide a JSON response with these exact keys:
        {{
            "style_description": "{style_desc}",
            "components": {{
                "base_prompt": "Core artistic style and technique (unified from all images)",
                "color_palette": "Combined color schemes and relationships",
                "effects": "Visual effects, lighting effects, special elements observed",
                "materials": "Texture, material properties, surface qualities visible",
                "lighting": "Lighting style, mood, atmosphere patterns",
                "description": "Brief overall unified style description"
            }}
        }}
        
        Focus on:
        - Finding common style elements across all images
        - Creating a cohesive artistic direction
        - Replicating visual style, not specific content or objects
        - Making descriptions suitable for game asset generation
        - Keeping the style_description under 200 words
        """
        
        ai_service = ai_service_factory.get_service(provider)
        
        # 构建推理参数 - 使用image_urls列表（现在是预签名URL）
        inference_params = {
            "prompt": analysis_prompt,
            "image_urls": image_urls,  # 现在是预签名URL列表
            "max_tokens": 600,
            "temperature": 0.3,
            "system_prompt": self.image_analysis_system_prompt
        }
        
        # 只有支持的模型才设置response_format
        if model in ["gpt-4o", "gpt-4-turbo"]:
            inference_params["response_format"] = {"type": "json_object"}
        
        result = await ai_service.run_inference(model, inference_params)
        
        # 解析JSON
        try:
            parsed_result = json.loads(result.strip())
            
            # 验证必需结构
            if "components" not in parsed_result or "style_description" not in parsed_result:
                raise ValueError("AI响应缺少必需字段: components 或 style_description")
            
            components = parsed_result["components"]
            
            # 验证必需字段
            required_fields = ["base_prompt", "color_palette", "effects", "materials", "lighting", "description"]
            missing_fields = []
            
            for field in required_fields:
                if field not in components:
                    missing_fields.append(field)
            
            if missing_fields:
                raise ValueError(f"AI响应的components缺少必需字段: {missing_fields}")
            
            # 确保所有字段都是字符串
            for field in required_fields:
                if components[field] is None:
                    components[field] = ""
            
            return parsed_result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"AI图像分析响应不是有效的JSON格式: {str(e)}")
    
    # ===== 通用方法保持不变 =====
    
    def get_available_presets(self) -> Dict[str, Any]:
        """获取可用的预设主题"""
        preset_details = {}
        
        for theme_name, config in self.preset_themes.items():
            example_prompt = f"{config['base_prompt']}, {config['color_palette']}"
            
            preset_details[theme_name] = {
                "name": config["name"],
                "description": config["description"],
                "color_palette": config["color_palette"],
                "example_prompt": example_prompt
            }
        
        return {
            "available_presets": list(self.preset_themes.keys()),
            "preset_details": preset_details,
            "total_count": len(self.preset_themes)
        }
    
    def validate_preset_theme(self, theme_name: str) -> bool:
        """验证预设主题是否存在"""
        return theme_name in self.preset_themes
    
    def get_preset_theme_info(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """获取特定预设主题的详细信息"""
        if theme_name not in self.preset_themes:
            return None
            
        config = self.preset_themes[theme_name]
        return {
            "name": config["name"],
            "description": config["description"],
            "components": config,
            "example_prompt": f"{config['base_prompt']}, {config['color_palette']}"
        }

# 全局实例
art_style_service = ArtStyleService()