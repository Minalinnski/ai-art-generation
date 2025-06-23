# example_usage.py - 美术资源生成系统使用示例

"""
美术资源生成系统使用示例

演示如何使用新架构生成动画、音频和视频资源
"""

import asyncio
from src.application.handlers.assets.animation_handler import AnimationHandler
from src.application.handlers.assets.audio_handler import AudioHandler
from src.application.handlers.assets.video_handler import VideoHandler
from src.schemas.dtos.request.asset_request import (
    AnimationGenerationRequest, AnimationPixverseDTO, AnimationInputData,
    AudioGenerationRequest, MusicGenMetaDTO, MusicInputData,
    VideoProcessingRequest, VideoBgRemoveDTO, VideoBgRemoveInputData
)


async def example_animation_generation():
    """动画生成示例"""
    print("=== 动画生成示例 ===")
    
    # 创建处理器
    handler = AnimationHandler()
    
    # 构建动画生成请求
    animation_input = AnimationInputData(
        prompt="A magical fairy dancing in an enchanted forest",
        duration=5.0,
        fps=24,
        width=512,
        height=512
    )
    
    animation_dto = AnimationPixverseDTO(
        input_data=animation_input,
        num_outputs=2
    )
    
    request = AnimationGenerationRequest(
        prompt="Generate magical fairy animation",
        animation_data=animation_dto,
        batch_size=2
    )
    
    try:
        # 生成动画
        response = await handler.generate_animation(request)
        print(f"动画生成任务已提交: {response.task_id}")
        print(f"总数量: {response.total_assets}")
        
        # 检查状态
        status = await handler.get_animation_status(response.task_id)
        print(f"当前状态: {status.status}")
        
        return response.task_id
        
    except Exception as e:
        print(f"动画生成失败: {str(e)}")
        return None


async def example_audio_generation():
    """音频生成示例"""
    print("\n=== 音频生成示例 ===")
    
    # 创建处理器
    handler = AudioHandler()
    
    # 构建音频生成请求
    music_input = MusicInputData(
        prompt="Epic fantasy battle music with orchestral instruments",
        duration=30.0,
        temperature=1.0
    )
    
    music_dto = MusicGenMetaDTO(
        input_data=music_input,
        num_outputs=1
    )
    
    request = AudioGenerationRequest(
        prompt="Generate epic battle music",
        audio_data=music_dto,
        batch_size=1
    )
    
    try:
        # 生成音频
        response = await handler.generate_audio(request)
        print(f"音频生成任务已提交: {response.task_id}")
        print(f"总数量: {response.total_assets}")
        
        # 检查状态
        status = await handler.get_audio_status(response.task_id)
        print(f"当前状态: {status.status}")
        
        return response.task_id
        
    except Exception as e:
        print(f"音频生成失败: {str(e)}")
        return None


async def example_video_processing():
    """视频处理示例"""
    print("\n=== 视频处理示例 ===")
    
    # 创建处理器
    handler = VideoHandler()
    
    # 构建视频处理请求
    video_input = VideoBgRemoveInputData(
        video="https://example.com/sample_video.mp4",  # 示例视频URL
        model="u2net",
        alpha_matting=True
    )
    
    video_dto = VideoBgRemoveDTO(input_data=video_input)
    
    request = VideoProcessingRequest(
        prompt="Remove background from video",
        video_data=video_dto,
        batch_size=1
    )
    
    try:
        # 处理视频
        response = await handler.process_video(request)
        print(f"视频处理任务已提交: {response.task_id}")
        print(f"总数量: {response.total_assets}")
        
        # 检查状态
        status = await handler.get_video_status(response.task_id)
        print(f"当前状态: {status.status}")
        
        return response.task_id
        
    except Exception as e:
        print(f"视频处理失败: {str(e)}")
        return None


async def example_service_status():
    """服务状态检查示例"""
    print("\n=== 服务状态检查 ===")
    
    # 创建处理器
    animation_handler = AnimationHandler()
    audio_handler = AudioHandler()
    video_handler = VideoHandler()
    
    try:
        # 获取各服务状态
        animation_status = await animation_handler.get_animation_service_status()
        audio_status = await audio_handler.get_audio_service_status()
        video_status = await video_handler.get_video_service_status()
        
        print("动画服务状态:")
        print(f"  - 健康状态: {animation_status['health_status']['status']}")
        print(f"  - 活跃任务: {animation_status['active_tasks']}")
        print(f"  - 支持模型: {animation_status['supported_models']}")
        
        print("音频服务状态:")
        print(f"  - 健康状态: {audio_status['health_status']['status']}")
        print(f"  - 活跃任务: {audio_status['active_tasks']}")
        print(f"  - 支持模型: {audio_status['supported_models']}")
        
        print("视频服务状态:")
        print(f"  - 健康状态: {video_status['health_status']['status']}")
        print(f"  - 活跃任务: {video_status['active_tasks']}")
        print(f"  - 支持模型: {video_status['supported_models']}")
        
    except Exception as e:
        print(f"获取服务状态失败: {str(e)}")


async def main():
    """主函数 - 运行所有示例"""
    print("美术资源生成系统示例\n")
    
    # 检查服务状态
    await example_service_status()
    
    # 生成示例资源
    animation_task = await example_animation_generation()
    audio_task = await example_audio_generation()
    video_task = await example_video_processing()
    
    # 等待一段时间后再次检查状态
    if any([animation_task, audio_task, video_task]):
        print("\n=== 等待5秒后检查任务状态 ===")
        await asyncio.sleep(5)
        
        handlers = {
            "animation": AnimationHandler(),
            "audio": AudioHandler(), 
            "video": VideoHandler()
        }
        
        tasks = {
            "animation": animation_task,
            "audio": audio_task,
            "video": video_task
        }
        
        for task_type, task_id in tasks.items():
            if task_id:
                try:
                    if task_type == "animation":
                        status = await handlers[task_type].get_animation_status(task_id)
                    elif task_type == "audio":
                        status = await handlers[task_type].get_audio_status(task_id)
                    elif task_type == "video":
                        status = await handlers[task_type].get_video_status(task_id)
                    
                    print(f"{task_type.title()}任务 {task_id} 状态: {status.status}")
                    print(f"  完成进度: {status.completed_assets}/{status.total_assets}")
                    if status.results:
                        print(f"  结果数量: {len(status.results)}")
                        for result in status.results:
                            if result.status == "success":
                                print(f"    - 成功: {result.asset_id}")
                            else:
                                print(f"    - 失败: {result.error_message}")
                
                except Exception as e:
                    print(f"检查{task_type}状态失败: {str(e)}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())