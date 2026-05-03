"""统一异常体系。

遵循 contexts.md 第 10 章规范。
"""

from typing import Any

from .schemas.error_contract import ErrorCode, ErrorResponse


class AppException(Exception):
    """基于契约的受控异常基类"""

    def __init__(self, code: ErrorCode, message: str, detail: dict[str, Any] | None = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(f"[{code.value}] {message}")

    def to_contract(self, correlation_id: str | None = None) -> ErrorResponse:
        """将异常转换为符合契约的响应对象"""
        return ErrorResponse(code=self.code, message=self.message, detail=self.detail, correlation_id=correlation_id, source="devops-platform")


class BusinessException(AppException):
    """基础业务异常类 (保持向后兼容)"""

    def __init__(self, message: str, code: str = "ERR_1000", status_code: int = 400):
        # 尝试将旧的字符串 code 映射为 ErrorCode，如果失败则使用系统错误
        try:
            e_code = ErrorCode(code)
        except ValueError:
            e_code = ErrorCode.SYSTEM_INTERNAL_ERROR
        super().__init__(code=e_code, message=message, status_code=status_code)


class ValidationException(AppException):
    """参数校验异常。"""

    def __init__(self, message: str, detail: dict[str, Any] | None = None):
        super().__init__(code=ErrorCode.VALIDATION_FAILED, message=message, detail=detail, status_code=400)


class NotFoundException(AppException):
    """资源不存在异常。"""

    def __init__(self, message: str):
        super().__init__(code=ErrorCode.RESOURCE_NOT_FOUND, message=message, status_code=404)


class PermissionException(AppException):
    """权限不足异常。"""

    def __init__(self, message: str):
        super().__init__(code=ErrorCode.PERMISSION_DENIED, message=message, status_code=403)


class CircuitBreakerOpenError(AppException):
    """当熔断器处于开启状态时抛出的异常。"""

    def __init__(self, message: str):
        super().__init__(code=ErrorCode.CIRCUIT_BREAKER_OPEN, message=message, status_code=503)
