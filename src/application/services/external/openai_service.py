# src/application/services/external/openai_service.py (优化版)
import asyncio
import base64
import requests
from typing import Dict, Any, List, Optional, Union

from src.application.services.service_interface import BaseService
from src.application.config.ai.ai_settings import get_ai_settings

class OpenAIService(BaseService):
    """OpenAI服务 - 优化版，支持多图片输入和代码简化"""
    
    def __init__(self):
        super().__init__()
        self.ai_settings = get_ai_settings()
        
        # 获取OpenAI配置
        openai_config = self.ai_settings.get_provider_config("openai")
        self.api_key = openai_config.get("api_key")
        
        if not self.api_key:
            raise ValueError("OpenAI API密钥未配置，请设置环境变量 OPENAI_API_KEY")
        
        self.api_host = openai_config.get("api_host", "https://api.openai.com/v1")
        self.timeout = openai_config.get("timeout", 120)
        
        # 从AI配置获取支持的模型
        self.available_models = self.ai_settings.get_provider_models("openai")
        
        self.logger.info("OpenAI服务初始化完成", extra={
            "has_api_key": bool(self.api_key),
            "timeout": self.timeout,
            "available_models": list(self.available_models.keys())
        })
    
    def get_service_info(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "description": "OpenAI图像和文本生成服务",
            "version": "2.1.0",
            "provider": "openai",
            "available_models": list(self.available_models.keys()),
            "timeout": self.timeout,
            "supports_capabilities": {
                "image_generation": self._get_models_by_capability("image_generation"),
                "text_generation": self._get_models_by_capability("text_generation"), 
                "image_analysis": self._get_models_by_capability("image_analysis"),
                "multimodal": self._get_models_by_capability("multimodal")
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
    
    def _supports_image_input(self, model: str) -> bool:
        """检查模型是否支持图像输入"""
        model_info = self.get_model_info(model)
        if not model_info:
            return False
        
        capabilities = model_info.get("capabilities", [])
        return any(cap in capabilities for cap in ["image_analysis", "multimodal"])
    
    def _process_image_inputs(self, input_data: Dict[str, Any], model: str) -> List[Dict[str, Any]]:
        """
        处理图像输入，统一转换为内容数组格式
        返回: 处理后的内容数组，第一个是文本，后续是图像
        """
        content_parts = []
        
        # 添加文本内容
        text_content = input_data.get("prompt", "")
        if text_content:
            content_parts.append({"type": "text", "text": text_content})
        
        # 检查模型是否支持图像输入
        if not self._supports_image_input(model):
            self.logger.info(f"模型 {model} 不支持图像输入，忽略图像数据")
            return content_parts
        
        # 处理多个图像URL（优先）
        if "image_urls" in input_data and input_data["image_urls"]:
            image_urls = input_data["image_urls"]
            if not isinstance(image_urls, list):
                image_urls = [image_urls]
            
            # 限制图片数量
            max_images = 10 if model == "gpt-4o" else 3
            if len(image_urls) > max_images:
                self.logger.warning(f"图片数量超限，只处理前{max_images}张")
                image_urls = image_urls[:max_images]
            
            for image_url in image_urls:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            
            self.logger.info(f"处理多图片URL: {len(image_urls)}张")
                
        # 处理单个图像URL（向后兼容）
        elif "image_url" in input_data:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": input_data["image_url"]}
            })
            self.logger.info("处理单图片URL")
            
        # 处理图像数据（base64，向后兼容）
        elif "image_data" in input_data:
            image_data = input_data["image_data"]
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                image_base64 = str(image_data)
            
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            })
            self.logger.info("处理base64图片数据")
        
        return content_parts
    
    def _build_final_prompt(self, input_data: Dict[str, Any]) -> str:
        """构建最终提示词（用于不支持多模态的场景）"""
        base_prompt = input_data.get("prompt", "")
        
        # 添加参考信息
        reference_parts = []
        
        if "reference_image_description" in input_data:
            reference_parts.append(f"Reference style: {input_data['reference_image_description']}")
        
        if "style_guidance" in input_data:
            reference_parts.append(f"Style guidance: {input_data['style_guidance']}")
        
        if "reference_prompt" in input_data:
            reference_parts.append(f"Reference asset: {input_data['reference_prompt']}")
        
        # 如果有参考图像但模型不支持，添加描述性文本
        if not self._supports_image_input("dummy"):  # 这里的模型检查在调用处进行
            if "image_urls" in input_data or "image_url" in input_data:
                reference_parts.append("Note: Reference images provided but not directly processable")
        
        # 构建最终提示词
        if reference_parts:
            reference_text = "\n\n".join(reference_parts)
            final_prompt = f"{base_prompt}\n\n{reference_text}"
        else:
            final_prompt = base_prompt
        
        return final_prompt
    
    def _prepare_request_headers(self) -> Dict[str, str]:
        """准备请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_http_request(self, method: str, url: str, headers: Dict[str, str], 
                          data: Dict[str, Any]) -> requests.Response:
        """发起HTTP请求"""
        import json
        # TODO change to DEBUG later
        self.logger.info(f"HTTP {method.upper()} Request to {url}")
        self.logger.info(f"Headers: {headers}")
        self.logger.info(f"Data: {data}")
        
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=self.timeout)
        else:
            response = requests.get(url, headers=headers, timeout=self.timeout)
        
        response.raise_for_status()
        return response
    
    async def run_inference(self, model: str, input_data: Dict[str, Any]) -> str:
        """运行推理"""
        # 验证模型
        if not self.validate_model(model):
            available_models = list(self.available_models.keys())
            raise ValueError(f"不支持的模型: {model}. 可用模型: {available_models}")
        
        model_type = self.get_model_type(model)
        
        self.logger.info(f"运行OpenAI推理", extra={
            "model": model,
            "model_type": model_type,
            "input_data_keys": list(input_data.keys())
        })
        
        try:
            if model_type == "image_generation":
                return await self._run_image_inference(model, input_data)
            elif model_type == "text_generation":
                return await self._run_text_inference(model, input_data)
            else:
                raise ValueError(f"模型 {model} 的类型 {model_type} 不受支持")
                
        except Exception as e:
            self.logger.error(f"OpenAI推理失败: {str(e)}")
            raise
    
    async def _run_image_inference(self, model: str, input_data: Dict[str, Any]) -> str:
        """运行图像生成推理"""
        url = f"{self.api_host}/images/generations"
        headers = self._prepare_request_headers()
        
        # 处理图像输入 - 检查是否为支持参考图像的模型
        has_reference_images = any(key in input_data for key in ["image_urls", "image_url", "image_data"])
        supports_image_input = self._supports_image_input(model)
        
        if has_reference_images and not supports_image_input:
            self.logger.warning(f"模型 {model} 不支持参考图像输入，将忽略图像数据")
            # 可以选择将图像描述信息添加到提示词中
            if "reference_image_description" not in input_data:
                input_data["reference_image_description"] = "Reference images provided but not supported by this model"
        
        # 构建最终提示词
        final_prompt = self._build_final_prompt(input_data)
        
        # 基础参数
        payload = {
            "model": model,
            "prompt": final_prompt,
            "n": 1
        }
        
        # 根据模型配置设置参数
        model_info = self.get_model_info(model)
        supported_sizes = model_info.get("supported_sizes", ["1024x1024"])
        requested_size = input_data.get("size", "1024x1024")
        
        if requested_size not in supported_sizes:
            self.logger.warning(f"模型 {model} 不支持尺寸 {requested_size}，使用默认 {supported_sizes[0]}")
            payload["size"] = supported_sizes[0]
        else:
            payload["size"] = requested_size
        
        # 模型特定参数
        if model == "dall-e-3":
            payload.update({
                "quality": input_data.get("quality", "standard"),
                "response_format": "b64_json"
            })
        elif model_info.get("output_format") == "b64_json":
            payload["response_format"] = "b64_json"
        
        # 计算图片数量用于日志
        image_count = 0
        if has_reference_images:
            if "image_urls" in input_data:
                image_count = len(input_data["image_urls"]) if isinstance(input_data["image_urls"], list) else 1
            elif "image_url" in input_data:
                image_count = 1
            elif "image_data" in input_data:
                image_count = 1
        
        self.logger.info(f"调用图像生成API", extra={
            "model": model,
            "size": payload.get("size"),
            "prompt_length": len(final_prompt),
            "reference_image_count": image_count,
            "supports_image_input": supports_image_input
        })
        
        # 执行请求
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self._make_http_request("POST", url, headers, payload)
        )
        
        response_json = response.json()
        
        # 处理响应
        if response_json.get("data") and len(response_json["data"]) > 0:
            image_data = response_json["data"][0]
            
            # 优先处理base64格式
            if "b64_json" in image_data:
                return image_data["b64_json"]
            # 处理URL格式
            elif "url" in image_data:
                return await self._download_image_as_base64(image_data["url"])
            else:
                raise Exception("响应中没有图像数据")
        else:
            error_detail = response_json.get("error", {}).get("message", str(response_json))
            raise Exception(f"图像生成失败: {error_detail}")
    
    async def _run_text_inference(self, model: str, input_data: Dict[str, Any]) -> str:
        """运行文本生成推理"""
        url = f"{self.api_host}/chat/completions"
        headers = self._prepare_request_headers()
        
        # 构建消息
        messages = []
        if "system_prompt" in input_data:
            messages.append({"role": "system", "content": input_data["system_prompt"]})
        
        # 处理图像输入
        content_parts = self._process_image_inputs(input_data, model)
        
        # 如果有图片内容，使用多模态消息
        if len(content_parts) > 1:
            messages.append({
                "role": "user",
                "content": content_parts
            })
        else:
            # 纯文本消息
            final_prompt = self._build_final_prompt(input_data)
            messages.append({"role": "user", "content": final_prompt})
        
        # 获取模型限制
        model_info = self.get_model_info(model)
        max_tokens = model_info.get("max_tokens", 4096) if model_info else 4096
        requested_tokens = input_data.get("max_tokens", 500)
        actual_max_tokens = min(max_tokens, requested_tokens)
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": actual_max_tokens,
            "temperature": input_data.get("temperature", 0.7)
        }
        
        # 添加 response_format 支持
        if "response_format" in input_data:
            # 只有特定模型支持 JSON 模式
            if model in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"] and input_data["response_format"].get("type") == "json_object":
                payload["response_format"] = input_data["response_format"]
                self.logger.info(f"启用JSON响应模式: {model}")
            else:
                self.logger.warning(f"模型 {model} 不支持JSON响应模式，忽略response_format参数")
        
        # 计算图片数量用于日志
        image_count = max(0, len(content_parts) - 1)  # 减去文本部分
        
        self.logger.info(f"调用文本生成API", extra={
            "model": model,
            "message_count": len(messages),
            "image_count": image_count,
            "has_images": image_count > 0,
            "max_tokens": actual_max_tokens,
            "response_format": input_data.get("response_format", {}).get("type", "text")
        })
        
        # 执行请求
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self._make_http_request("POST", url, headers, payload)
        )
        
        response_json = response.json()
        
        # 处理响应
        if "choices" in response_json and response_json["choices"]:
            content = response_json["choices"][0].get("message", {}).get("content", "")
            if content:
                self.logger.info(f"文本生成成功: {model}", extra={
                    "response_length": len(content),
                    "image_count": image_count,
                    "usage": response_json.get("usage", {})
                })
                return content.strip()
        
        # 错误处理
        error_detail = response_json.get("error", {}).get("message", str(response_json))
        raise Exception(f"文本生成失败: {error_detail}")
    
    async def _download_image_as_base64(self, image_url: str) -> str:
        """下载图像并转换为base64"""
        self.logger.info(f"下载图像: {image_url}")
        
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(image_url, timeout=60)
            )
            response.raise_for_status()
            
            base64_str = base64.b64encode(response.content).decode('utf-8')
            self.logger.info("图像下载转换完成")
            return base64_str
            
        except Exception as e:
            self.logger.error(f"图像下载失败: {str(e)}")
            raise Exception(f"下载图像失败: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查API连通性
            headers = self._prepare_request_headers()
            
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(f"{self.api_host}/models", headers=headers, timeout=10)
                )
                api_accessible = response.status_code == 200
            except:
                api_accessible = False
            
            return {
                "service": self.service_name,
                "provider": "openai",
                "status": "healthy" if self.api_key and api_accessible else "unhealthy",
                "has_api_key": bool(self.api_key),
                "api_accessible": api_accessible,
                "available_models": list(self.available_models.keys()),
                "model_types": {
                    "image_generation": self._get_models_by_capability("image_generation"),
                    "text_generation": self._get_models_by_capability("text_generation"),
                    "multimodal": self._get_models_by_capability("multimodal")
                },
                "timestamp": self._get_current_time()
            }
        except Exception as e:
            return {
                "service": self.service_name,
                "provider": "openai",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self._get_current_time()
            }
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.utcnow().isoformat()