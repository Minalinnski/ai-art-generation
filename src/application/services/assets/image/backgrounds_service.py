# src/application/services/assets/image/backgrounds_service.py (简化版 - 清晰的提示词构建)
from typing import Dict, Any, List
from .base_image_service import BaseImageService

class BackgroundsService(BaseImageService):
    """背景生成服务 - 使用Art Style模块，专注于背景相关的提示词构建"""
    
    def get_module_name(self) -> str:
        return "backgrounds"
    
    def get_default_prompt_template(self) -> str:
        return (
            "Create a high-quality background scene for {content_description}. "
            "The background should be atmospheric, immersive, and suitable for online slot machine games."
        )
    
    def _get_category_names(self) -> List[str]:
        return ["background_set"]
    
    def build_content_prompt(self, task_info: Dict[str, Any], art_style_data: Dict[str, Any]) -> str:
        """构建背景相关的内容提示词"""
        
        # 基础描述
        description = task_info.get("description", task_info.get("filename", "background"))
        category = task_info.get("category", "")
        subcategory = task_info.get("subcategory", "")
        
        # Background 基本要求
        base_requirements = [
            f"Create a game background: {description}",
            "atmospheric and immersive scene",
            "suitable for slot machine games",
            "detailed but not distracting"
        ]
        
        # 根据双层字典构建模板
        category_requirements = self._get_category_requirements(category, subcategory)
        
        # 组合完整提示词
        prompt_parts = base_requirements + category_requirements
        
        return ", ".join(prompt_parts)
    
    def _get_category_requirements(self, category: str, subcategory: str) -> List[str]:
        """根据双层字典结构返回对应要求"""
        
        # 第一层：分类要求
        category_templates = {
            "background_set": {
                "background_scene": [
                    "main backdrop for slot machine game",
                    "immersive and detailed environment",
                    "consistent with all UI elements"
                ],
                "panel_frame": [
                    "panel frame with transparent center",
                    "surrounds the game area like reels",
                    "ornate symmetrical border",
                    "designed to fit 3x5 tile layout"
                ],
                "filled_panel_frame": [
                    "panel frame with soft inner background fill",
                    "identical shape to transparent version",
                    "used as direct overlay panel",
                    "maintain shape and proportions"
                ],
                "tile_area": [
                    "3x5 tile grid background",
                    "fits seamlessly inside panel frame",
                    "evenly sized tiles forming game grid",
                    "textured and aligned with frame"
                ]
            }
        }
        
        # 获取对应模板，如果找不到就返回通用模板
        if category in category_templates and subcategory in category_templates[category]:
            return category_templates[category][subcategory]
        elif category in category_templates:
            # 如果有分类但没有子分类，返回该分类的第一个子分类作为默认
            first_subcategory = list(category_templates[category].keys())[0]
            return category_templates[category][first_subcategory]
        else:
            # 完全自定义的情况
            return [
                f"designed as a {category} background",
                "atmospheric and engaging",
                "game-appropriate composition"
            ]