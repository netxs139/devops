import uuid

from devops_collector.core.exceptions import AppException, BusinessException, ErrorCode, NotFoundException, ValidationException


def test_app_exception_contract_conversion():
    """测试 AppException 转换为 ErrorResponse 契约。"""
    correlation_id = str(uuid.uuid4())
    detail = {"field": "username", "reason": "missing"}

    exc = AppException(code=ErrorCode.VALIDATION_FAILED, message="Validation failed", detail=detail, status_code=422)

    contract = exc.to_contract(correlation_id=correlation_id)

    assert contract.code == ErrorCode.VALIDATION_FAILED
    assert contract.message == "Validation failed"
    assert contract.detail == detail
    assert contract.correlation_id == correlation_id
    assert contract.source == "devops-platform"


def test_validation_exception_preset():
    """测试 ValidationException 预设值。"""
    exc = ValidationException(message="Invalid input", detail={"info": "test"})
    assert exc.code == ErrorCode.VALIDATION_FAILED
    assert exc.status_code == 400
    assert exc.detail == {"info": "test"}


def test_not_found_exception_preset():
    """测试 NotFoundException 预设值。"""
    exc = NotFoundException(message="Not found")
    assert exc.code == ErrorCode.RESOURCE_NOT_FOUND
    assert exc.status_code == 404


def test_business_exception_compatibility():
    """测试 BusinessException 的向后兼容性映射。"""
    # 场景 1: 传入已知的字符串代码
    exc = BusinessException(message="Error", code="ERR_2000")
    assert exc.code == ErrorCode.UNAUTHORIZED

    # 场景 2: 传入未知的字符串代码，应 fallback 到系统错误
    exc_fallback = BusinessException(message="Error", code="UNKNOWN_STUFF")
    assert exc_fallback.code == ErrorCode.SYSTEM_INTERNAL_ERROR


def test_exception_string_representation():
    """测试异常的字符串表示是否包含错误码。"""
    exc = AppException(code=ErrorCode.SYSTEM_INTERNAL_ERROR, message="Boom")
    assert "[ERR_1000] Boom" in str(exc)
