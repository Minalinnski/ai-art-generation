# src/application/services/assets/image/ui_service.py (简化版 - 清晰的提示词构建)
from typing import Dict, Any, List
from .base_image_service import BaseImageService

class UIService(BaseImageService):
    """UI生成服务 - 使用Art Style模块，专注于UI相关的提示词构建"""
    
    def get_module_name(self) -> str:
        return "ui"
    
    def get_default_prompt_template(self) -> str:
        return (
            "Create a high-quality user interface element for {content_description}. "
            "The UI element should be modern, intuitive, and suitable for online slot machine games."
        )
    
    def _get_category_names(self) -> List[str]:
        return ["buttons", "panels"]
    
    def build_content_prompt(self, task_info: Dict[str, Any], art_style_data: Dict[str, Any]) -> str:
        """构建UI相关的内容提示词"""
        
        # 基础描述
        description = task_info.get("description", task_info.get("filename", "UI element"))
        category = task_info.get("category", "")
        subcategory = task_info.get("subcategory", "")
        
        # UI 基本要求
        base_requirements = [
            f"Create a game UI element: {description}",
            "modern and intuitive design",
            "suitable for slot machine games",
            "clean and functional appearance"
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
            "buttons": {
                "main_controls": [
                    "primary action button design",
                    "includes Normal, Hover, and Press states",
                    "prominent and easily clickable",
                    "consistent shape and spacing"
                ],
                "toggle_controls": [
                    "toggle button showing On and Off states",
                    "clear visual distinction between states",
                    "includes appropriate icons"
                ],
                "icon_buttons": [
                    "icon-style button with clear symbol",
                    "square or rounded base design",
                    "clean silhouette for recognition"
                ]
            },
            "panels": {
                "info_panels": [
                    "information display panel design",
                    "clear and readable layout",
                    "suitable for displaying game statistics"
                ],
                "game_area": [
                    "game area background panel",
                    "provides context without distraction",
                    "balanced visual weight"
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
                f"designed as a {category} UI element",
                "functional and user-friendly design",
                "game interface appropriate"
            ]