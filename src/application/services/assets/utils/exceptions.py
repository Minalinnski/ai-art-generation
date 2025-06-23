# src/application/services/assets/utils/exceptions.py
from typing import Any, Dict, Optional


class AssetServiceException(Exception):
    """美术资源服务基础异常"""
    
    def __init__(
        self, 
        message: str,
        error_code: str = "ASSET_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ModelNotFoundError(AssetServiceException):
    """模型未找到异常"""
    
    def __init__(self, model_name: str, available_models: Optional[list] = None):
        message = f"模型未找到: {model_name}"
        if available_models:
            message += f"，可用模型: {', '.join(available_models)}"
        
        super().__init__(
            message=message,
            error_code="MODEL_NOT_FOUND",
            details={
                "model_name": model_name,
                "available_models": available_models or []
            }
        )


class GenerationFailedError(AssetServiceException):
    """生成失败异常"""
    
    def __init__(self, model: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"使用模型 {model} 生成失败: {reason}"
        
        super().__init__(
            message=message,
            error_code="GENERATION_FAILED",
            details={
                **(details or {}),
                "model": model,
                "reason": reason
            }
        )


class ValidationError(AssetServiceException):
    """验证错误异常"""
    
    def __init__(self, field: str, message: str, value: Any = None):
        full_message = f"字段验证失败 {field}: {message}"
        
        super().__init__(
            message=full_message,
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "validation_message": message,
                "value": value
            }
        )


class ConfigurationError(AssetServiceException):
    """配置错误异常"""
    
    def __init__(self, config_key: str, message: str):
        full_message = f"配置错误 {config_key}: {message}"
        
        super().__init__(
            message=full_message,
            error_code="CONFIGURATION_ERROR",
            details={
                "config_key": config_key,
                "config_message": message
            }
        )


class ProviderError(AssetServiceException):
    """AI服务商错误异常"""
    
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        full_message = f"AI服务商 {provider} 错误: {message}"
        
        super().__init__(
            message=full_message,
            error_code="PROVIDER_ERROR",
            details={
                "provider": provider,
                "provider_message": message,
                "status_code": status_code
            }
        )


class BatchProcessingError(AssetServiceException):
    """批量处理错误异常"""
    
    def __init__(self, total: int, failed: int, errors: list):
        message = f"批量处理部分失败: {failed}/{total} 项失败"
        
        super().__init__(
            message=message,
            error_code="BATCH_PROCESSING_ERROR",
            details={
                "total_count": total,
                "failed_count": failed,
                "success_count": total - failed,
                "errors": errors
            }
        )


class ResourceNotFoundError(AssetServiceException):
    """资源未找到异常"""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} 未找到: {resource_id}"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class StorageError(AssetServiceException):
    """存储错误异常"""
    
    def __init__(self, operation: str, message: str, storage_type: str = "unknown"):
        full_message = f"存储操作失败 {operation}: {message}"
        
        super().__init__(
            message=full_message,
            error_code="STORAGE_ERROR",
            details={
                "operation": operation,
                "storage_type": storage_type,
                "storage_message": message
            }
        )