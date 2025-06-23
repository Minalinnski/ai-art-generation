# src/application/services/assets/image/symbols_service.py (简化版 - 清晰的提示词构建)
from typing import Dict, Any, List
from .base_image_service import BaseImageService

class SymbolsService(BaseImageService):
    """符号生成服务 - 使用Art Style模块，专注于符号相关的提示词构建"""
    
    def get_module_name(self) -> str:
        return "symbols"
    
    def get_default_prompt_template(self) -> str:
        return (
            "Create a high-quality slot machine symbol for {content_description}. "
            "The symbol should be detailed, visually appealing, and suitable for use in online slot games."
        )
    
    def _get_category_names(self) -> List[str]:
        return ["base_symbols", "special_symbols"]
    
    def build_content_prompt(self, task_info: Dict[str, Any], art_style_data: Dict[str, Any]) -> str:
        """构建符号相关的内容提示词"""
        
        # 基础描述
        description = task_info.get("description", task_info.get("filename", "symbol"))
        category = task_info.get("category", "")
        subcategory = task_info.get("subcategory", "")
        
        # Slot machine 基本要求
        base_requirements = [
            f"Create a slot machine symbol: {description}",
            "high quality game asset",
            "centered composition", 
            "clear silhouette",
            "suitable for slot machine gameplay"
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
            "base_symbols": {
                "low_value": [
                    "designed as a lower-value game symbol",
                    "clean and recognizable design",
                    "suitable for frequent appearance"
                ],
                "high_value": [
                    "designed as a high-value premium symbol",
                    "ornate and eye-catching appearance", 
                    "detailed and luxurious design"
                ]
            },
            "special_symbols": {
                "wild": [
                    "designed as a WILD symbol with powerful visual impact",
                    "magical or mystical elements",
                    "glowing effects",
                    "besides main element, should have a frame, may include 'WILD' text and optional multiplier values in the same row"
                ],
                "scatter": [
                    "designed as a SCATTER symbol with dynamic energy",
                    "radiating or explosive visual elements",
                    "sparkling effects",
                    "conveys bonus trigger functionality",
                    "besides main element, should have a frame"
                ],
                "bonus": [
                    "designed as a BONUS symbol representing rewards",
                    "treasure or prize-like elements",
                    "golden glow or valuable appearance"
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
                f"designed as a {category} symbol",
                "distinctive and clear design",
                "optimized for game use"
            ]