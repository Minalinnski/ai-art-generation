# src/application/services/external/replicate_service.py (更新版)
import asyncio
import base64
import replicate
from typing import Dict, Any, List, Optional
from src.application.services.service_interface import BaseService
from src.application.config.ai.ai_settings import get_ai_settings


class ReplicateService(BaseService):
    """Replicate AI服务 - 更新版"""
    
    def __init__(self):
        super().__init__()
        self.ai_settings = get_ai_settings()
        
        # 获取Replicate配置
        replicate_config = self.ai_settings.get_provider_config("replicate")
        self.api_key = replicate_config.get("api_key")
        
        if not self.api_key:
            raise ValueError("Replicate API密钥未配置，请设置环境变量 REPLICATE_API_TOKEN")
        
        self.api_host = replicate_config.get("api_host", "https://api.replicate.com")
        self.timeout = replicate_config.get("timeout", 300)
        self.max_retries = replicate_config.get("max_retries", 3)
        
        # 从AI配置获取支持的模型
        self.available_models = self.ai_settings.get_provider_models("replicate")
        
        # 初始化客户端
        self.client = replicate.Client(api_token=self.api_key)
        
        self.logger.info("Replicate服务初始化完成", extra={
            "api_host": self.api_host,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "has_api_key": bool(self.api_key),
            "available_models": list(self.available_models.keys())
        })
    
    def get_service_info(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "description": "Replicate AI模型推理服务",
            "version": "2.0.0",
            "provider": "replicate",
            "available_models": list(self.available_models.keys()),
            "api_host": self.api_host,
            "timeout": self.timeout,
            "supports_capabilities": {
                "audio_generation": self._get_models_by_capability("music_generation"),
                "animation_generation": self._get_models_by_capability("animation"),
                "video_processing": self._get_models_by_capability("video_processing")
            }
        }
    
    def _get_models_by_capability(self, capability: str) -> List[str]:
        """根据能力获取模型列表"""
        models = []
        for model_name, model_info in self.available_models.items():
            if capability in model_info.get("capabilities", []):
                models.append(model_name)
        return models
    
    def validate_model(self, model: str) -> bool:
        """验证模型是否可用"""
        return model in self.available_models
    
    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        return self.available_models.get(model)
    
    def get_model_type(self, model: str) -> Optional[str]:
        """获取模型类型"""
        model_info = self.get_model_info(model)
        if model_info:
            return model_info.get("model_type")
        return None
    
    async def run_inference(self, model: str, input_data: Dict[str, Any]) -> str:
        """
        运行单次推理
        
        Args:
            model: 模型名称 (如: ardianfe/musicgen-stereo-chord:latest)
            input_data: 输入数据
        """
        # 验证模型
        if not self.validate_model(model):
            available_models = list(self.available_models.keys())
            raise ValueError(f"不支持的模型: {model}. 可用模型: {available_models}")
        
        try:
            self.logger.info(f"运行Replicate推理: {model}", extra={
                "model": model,
                "model_type": self.get_model_type(model),
                "input_keys": list(input_data.keys()) if input_data else []
            })
            
            # 直接传递模型名称字符串
            output = self.client.run(model, input=input_data)
            
            # 处理不同类型的输出
            if isinstance(output, replicate.helpers.FileOutput):
                # 文件输出转换为base64
                content_bytes = output.read()
                base64_str = base64.b64encode(content_bytes).decode('utf-8')
                self.logger.debug(f"文件输出转换为base64: {len(base64_str)}字符")
                return base64_str
            else:
                # 列表输出取最后一个结果
                results = list(output)
                if not results:
                    raise ValueError("Replicate返回空结果")
                
                final_result = results[-1]
                self.logger.debug(f"列表输出取最后结果: {type(final_result).__name__}")
                return final_result
                
        except Exception as e:
            self.logger.error(f"Replicate推理失败: {str(e)}", extra={
                "model": model,
                "input_data": input_data,
                "error_type": type(e).__name__
            })
            raise
    
    async def batch_inference(self, model: str, input_data: Dict[str, Any], num_outputs: int) -> List[str]:
        """
        批量推理
        
        Args:
            model: 模型名称
            input_data: 输入数据
            num_outputs: 输出数量
        """
        # 验证模型
        if not self.validate_model(model):
            available_models = list(self.available_models.keys())
            raise ValueError(f"不支持的模型: {model}. 可用模型: {available_models}")
        
        try:
            self.logger.info(f"开始批量推理: {model}", extra={
                "model": model,
                "num_outputs": num_outputs
            })
            
            # 创建异步任务列表
            tasks = [
                self.run_inference(model, input_data)
                for _ in range(num_outputs)
            ]
            
            # 并发执行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果，过滤异常
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"批量推理第{i+1}个任务失败: {str(result)}")
                else:
                    valid_results.append(result)
            
            self.logger.info(f"批量推理完成: {len(valid_results)}个结果", extra={
                "model": model,
                "success_count": len(valid_results),
                "total_requested": num_outputs
            })
            
            return valid_results
            
        except Exception as e:
            self.logger.error(f"批量推理失败: {str(e)}", extra={
                "model": model,
                "num_outputs": num_outputs
            })
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            return {
                "service": self.service_name,
                "provider": "replicate",
                "status": "healthy" if self.api_key else "unhealthy",
                "api_host": self.api_host,
                "has_api_key": bool(self.api_key),
                "available_models": list(self.available_models.keys()),
                "model_types": {
                    "audio_generation": self._get_models_by_capability("music_generation"),
                    "animation_generation": self._get_models_by_capability("animation")
                },
                "timestamp": self._get_current_time()
            }
        except Exception as e:
            self.logger.error(f"Replicate健康检查失败: {str(e)}")
            return {
                "service": self.service_name,
                "provider": "replicate",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self._get_current_time()
            }
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.utcnow().isoformat()