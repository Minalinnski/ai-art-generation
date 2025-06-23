# src/application/handlers/assets/multimedia_handler.py
from typing import Dict, Any, List
from src.application.handlers.assets.asset_handler import AssetHandler
from src.application.services.assets.multimedia.animation_service import AnimationService
from src.application.services.assets.multimedia.audio_service import AudioService
from src.application.services.assets.multimedia.video_service import VideoService
from src.schemas.dtos.request.asset_request import AssetGenRequest
from src.schemas.dtos.request.multimedia_request import (
    AnimationGenRequest, AudioGenRequest, VideoGenRequest
)
from src.schemas.dtos.response.asset_response import AssetGenResponse


class MultimediaHandler(AssetHandler):
    """多媒体资源处理器 - 处理动画、音乐、视频"""
    
    def __init__(self):
        super().__init__()
        self.animation_service = AnimationService()
        self.audio_service = AudioService()
        self.video_service = VideoService()
    
    def get_supported_asset_types(self) -> List[str]:
        """获取支持的资源类型列表"""
        return ["animation", "audio", "video"]
    
    async def handle_asset_generation(
        self, 
        asset_type: str, 
        request: AssetGenRequest
    ) -> AssetGenResponse:
        """处理资源生成请求"""
        # 验证请求
        await self.validate_generation_request(asset_type, request)
        
        # 根据资源类型路由到具体的生成方法
        if asset_type == "animation":
            return await self._generate_animation(request)
        elif asset_type == "audio":
            return await self._generate_audio(request)
        elif asset_type == "video":
            return await self._process_video(request)
        else:
            raise ValueError(f"不支持的多媒体资源类型: {asset_type}")
    
    async def generate_animation(self, request: AnimationGenRequest) -> AssetGenResponse:
        """生成动画 - 公共接口"""
        base_request = AssetGenRequest(
            provider=request.provider,
            model=request.model,
            num_outputs=request.num_outputs,
            generation_params=request.generation_params.model_dump(),
            request_id=request.request_id,
            client_info=request.client_info
        )
        return await self._generate_animation(base_request)
    
    async def generate_audio(self, request: AudioGenRequest) -> AssetGenResponse:
        """生成音乐 - 公共接口"""
        base_request = AssetGenRequest(
            provider=request.provider,
            model=request.model,
            num_outputs=request.num_outputs,
            generation_params=request.generation_params.model_dump(),
            request_id=request.request_id,
            client_info=request.client_info
        )
        return await self._generate_audio(base_request)
    
    async def process_video(self, request: VideoGenRequest) -> AssetGenResponse:
        """处理视频 - 公共接口"""
        base_request = AssetGenRequest(
            provider=request.provider,
            model=request.model,
            num_outputs=request.num_outputs,
            generation_params=request.generation_params.model_dump(),
            request_id=request.request_id,
            client_info=request.client_info
        )
        return await self._process_video(base_request)
    
    async def _generate_animation(self, request: AssetGenRequest) -> AssetGenResponse:
        """内部动画生成方法"""
        try:
            self.logger.info(f"处理动画生成请求: {request.model}", extra={
                "model": request.model,
                "num_outputs": request.num_outputs,
                "provider": request.provider
            })
            
            # 调用服务层生成动画
            results = await self.animation_service.generate(
                model=request.model,
                generation_params=request.generation_params,
                num_outputs=request.num_outputs,
                provider=request.provider
            )
            
            # 构造响应
            response = AssetGenResponse(
                task_id=self._create_task_id("anim", request.request_id),
                asset_type="animation",
                model=request.model,
                status="completed",
                num_outputs=len(results),
                outputs=results,
                generation_params=request.generation_params
            )
            
            self.logger.info(f"动画生成完成: {len(results)}个结果", extra={
                "task_id": response.task_id,
                "model": request.model
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"动画生成处理失败: {str(e)}", extra={
                "model": request.model,
                "error_type": type(e).__name__
            })
            raise
    
    async def _generate_audio(self, request: AssetGenRequest) -> AssetGenResponse:
        """内部音乐生成方法"""
        try:
            self.logger.info(f"处理音乐生成请求: {request.model}", extra={
                "model": request.model,
                "num_outputs": request.num_outputs,
                "provider": request.provider
            })
            
            # 调用服务层生成音乐
            results = await self.audio_service.generate(
                model=request.model,
                generation_params=request.generation_params,
                num_outputs=request.num_outputs,
                provider=request.provider
            )
            
            # 构造响应
            response = AssetGenResponse(
                task_id=self._create_task_id("audio", request.request_id),
                asset_type="audio",
                model=request.model,
                status="completed",
                num_outputs=len(results),
                outputs=results,
                generation_params=request.generation_params
            )
            
            self.logger.info(f"音乐生成完成: {len(results)}个结果", extra={
                "task_id": response.task_id,
                "model": request.model
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"音乐生成处理失败: {str(e)}", extra={
                "model": request.model,
                "error_type": type(e).__name__
            })
            raise
    
    async def _process_video(self, request: AssetGenRequest) -> AssetGenResponse:
        """内部视频处理方法"""
        try:
            self.logger.info(f"处理视频处理请求: {request.model}", extra={
                "model": request.model,
                "num_outputs": request.num_outputs,
                "provider": request.provider
            })
            
            # 调用服务层处理视频
            results = await self.video_service.generate(
                model=request.model,
                generation_params=request.generation_params,
                num_outputs=request.num_outputs,
                provider=request.provider
            )
            
            # 构造响应
            response = AssetGenResponse(
                task_id=self._create_task_id("video", request.request_id),
                asset_type="video",
                model=request.model,
                status="completed",
                num_outputs=len(results),
                outputs=results,
                generation_params=request.generation_params
            )
            
            self.logger.info(f"视频处理完成: {len(results)}个结果", extra={
                "task_id": response.task_id,
                "model": request.model
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"视频处理失败: {str(e)}", extra={
                "model": request.model,
                "error_type": type(e).__name__
            })
            raise
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取多媒体服务状态"""
        try:
            # 调用基类方法获取基础状态
            base_status = await super().get_service_status()
            
            # 添加具体服务的健康状态
            animation_health = await self.animation_service.health_check()
            audio_health = await self.audio_service.health_check()  # 修复错误: audio_seaudio -> audio_service
            video_health = await self.video_service.health_check()
            
            # 合并状态信息
            base_status.update({
                "category": "multimedia",
                "services": {
                    "animation": animation_health,
                    "audio": audio_health,
                    "video": video_health
                },
                "total_available_models": len(self.asset_settings.get_available_models("animation")) +
                                        len(self.asset_settings.get_available_models("audio")) +
                                        len(self.asset_settings.get_available_models("video"))
            })
            
            return base_status
            
        except Exception as e:
            self.logger.error(f"获取多媒体服务状态失败: {str(e)}")
            return {
                "handler": self.__class__.__name__,
                "category": "multimedia",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self._get_current_time()
            }
    
    def get_animation_models(self) -> Dict[str, Any]:
        """获取动画模型信息"""
        return self.get_available_models("animation")
    
    def get_audio_models(self) -> Dict[str, Any]:
        """获取音乐模型信息"""
        return self.get_available_models("audio")
    
    def get_video_models(self) -> Dict[str, Any]:
        """获取视频模型信息"""
        return self.get_available_models("video")