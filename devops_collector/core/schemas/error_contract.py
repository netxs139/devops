from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    """项目统一错误码谱系 (Error Pedigree)
    分类编码：
    - 1xxx: 系统/基础设施错误
    - 2xxx: 鉴权/安全错误
    - 3xxx: 业务逻辑/资源错误
    - 4xxx: 外部集成/第三方依赖错误
    """

    # 系统级
    SYSTEM_INTERNAL_ERROR = "ERR_1000"
    VALIDATION_FAILED = "ERR_1001"
    CONFIGURATION_MISSING = "ERR_1002"

    # 鉴权级
    UNAUTHORIZED = "ERR_2000"
    PERMISSION_DENIED = "ERR_2001"
    TOKEN_EXPIRED = "ERR_2002"

    # 业务级
    RESOURCE_NOT_FOUND = "ERR_3000"
    RESOURCE_CONFLICT = "ERR_3001"
    FLOW_INTERRUPTED = "ERR_3002"
    PLUGIN_LOAD_FAILED = "ERR_3100"

    # 集成级
    UPSTREAM_SERVICE_TIMEOUT = "ERR_4000"
    UPSTREAM_DATA_CORRUPT = "ERR_4001"
    CIRCUIT_BREAKER_OPEN = "ERR_4002"


class ErrorResponse(BaseModel):
    """统一错误响应契约 (Code-as-Contract)"""

    code: ErrorCode = Field(..., description="机器可读的唯一错误码")
    message: str = Field(..., description="面向用户的简短描述")
    detail: dict[str, Any] | None = Field(None, description="结构化的错误详情")
    correlation_id: str | None = Field(None, description="全链路追踪 ID")
    source: str = Field("devops-platform", description="组件名称")
