# src/application/handlers/assets/asset_handler.py
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from src.application.handlers.handler_interface import BaseHandler
from src.application.config.assets.asset_settings import get_asset_settings
from src.schemas.dtos.request.asset_request import AssetGenRequest
from src.schemas.dtos.response.asset_response import AssetGenResponse


class AssetHandler(BaseHandler[AssetGenResponse], ABC):
    """资源生成处理器基类"""
    
    def __init__(self):
        super().__init__()
        self.asset_settings = get_asset_settings()
    
    @abstractmethod
    def get_supported_asset_types(self) -> List[str]:
        """获取支持的资源类型列表"""
        pass
    
    @abstractmethod
    async def handle_asset_generation(
        self, 
        asset_type: str, 
        request: AssetGenRequest
    ) -> AssetGenResponse:
        """处理资源生成请求"""
        pass
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态 - 基础实现"""
        try:
            supported_types = self.get_supported_asset_types()
            
            return {
                "handler": self.__class__.__name__,
                "status": "healthy",
                "supported_asset_types": supported_types,
                "timestamp": self._get_current_time()
            }
        except Exception as e:
            self.logger.error(f"获取服务状态失败: {str(e)}")
            return {
                "handler": self.__class__.__name__,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self._get_current_time()
            }
    
    def get_available_models(self, asset_type: str) -> Dict[str, Any]:
        """获取指定资源类型的可用模型"""
        try:
            if asset_type not in self.get_supported_asset_types():
                raise ValueError(f"不支持的资源类型: {asset_type}")
            
            available_models = self.asset_settings.get_available_models(asset_type)
            generation_limits = self.asset_settings.get_generation_limits(asset_type)
            default_provider = self.asset_settings.get_default_provider(asset_type)
            
            return {
                "asset_type": asset_type,
                "models": available_models,
                "limits": generation_limits,
                "default_provider": default_provider,
                "enabled_providers": self.asset_settings.get_enabled_ai_providers()
            }
        except Exception as e:
            self.logger.error(f"获取模型信息失败: {str(e)}")
            raise
    
    def get_all_available_models(self) -> Dict[str, Any]:
        """获取所有支持的资源类型的模型信息"""
        result = {}
        for asset_type in self.get_supported_asset_types():
            try:
                result[asset_type] = self.get_available_models(asset_type)
            except Exception as e:
                self.logger.error(f"获取 {asset_type} 模型信息失败: {str(e)}")
                result[asset_type] = {"error": str(e)}
        
        return result
    
    async def validate_generation_request(
        self, 
        asset_type: str, 
        request: AssetGenRequest
    ) -> None:
        """验证生成请求"""
        # 检查资源类型是否支持
        if asset_type not in self.get_supported_asset_types():
            raise ValueError(f"不支持的资源类型: {asset_type}")
        
        # 检查模型是否可用
        available_models = self.asset_settings.get_available_models(asset_type)
        if request.model not in available_models:
            raise ValueError(f"模型 {request.model} 在资源类型 {asset_type} 中不可用")
        
        # 检查生成数量限制
        limits = self.asset_settings.get_generation_limits(asset_type)
        max_outputs = limits.get("max_outputs_per_request", 50)
        if request.num_outputs > max_outputs:
            raise ValueError(f"生成数量 {request.num_outputs} 超过限制 {max_outputs}")
        
        # 检查提供商是否启用
        if request.provider:
            enabled_providers = self.asset_settings.get_enabled_ai_providers()
            if request.provider not in enabled_providers:
                raise ValueError(f"AI提供商 {request.provider} 未启用")
    
    async def _process_request(self, request_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理通用请求"""
        if not request_data:
            return await self.get_service_status()
        
        # 路由到具体的资源类型处理
        asset_type = request_data.get("asset_type")
        if not asset_type:
            raise ValueError("缺少 asset_type 参数")
        
        # 构造请求对象
        request = AssetGenRequest(**request_data)
        
        # 处理生成请求
        result = await self.handle_asset_generation(asset_type, request)
        return result.dict()
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def _create_task_id(self, asset_type: str, request_id: Optional[str] = None) -> str:
        """创建任务ID"""
        import uuid
        base_id = request_id or str(uuid.uuid4())[:8]
        return f"{asset_type}_{base_id}"