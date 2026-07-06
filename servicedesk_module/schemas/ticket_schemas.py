import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TicketBase(BaseModel):
    """基础工单模型."""

    title: str = Field(..., max_length=255, description="工单标题")
    description: str | None = Field(None, description="工单详情")


class TicketCreateExternal(TicketBase):
    """外部客户提交工单 (Bug/需求) 的请求 Schema"""

    # 这里不需要传记者ID或企业ID，因为这些会从客户身份的 Token 中提取
    pass


class TicketTriageUpdate(BaseModel):
    """内部分诊客服更新工单的 Schema"""

    ticket_type: str | None = Field(None, description="类型: INCIDENT/CONSULTATION/REQUIREMENT/BUG")
    product_id: str | None = Field(None, description="关联产品线ID")
    department_id: str | None = Field(None, description="负责的内部研发中心/部门ID")


class TicketResponse(TicketBase):
    """工单返回 Schema"""

    id: uuid.UUID
    tenant_id: str
    reporter_id: uuid.UUID
    ticket_type: str
    status: str
    product_id: str | None
    department_id: str | None
    assignee_id: str | None
    agile_issue_id: str | None
    gitlab_group_id: int | None
    gitlab_project_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerIdentityCreate(BaseModel):
    """后台创建外部客户账号 Schema"""

    company_name: str
    customer_company_id: str | None = None
    assigned_department_id: str | None = None
    email: str
    phone: str | None = None


class CustomerIdentityResponse(BaseModel):
    """客户身份响应模型."""

    id: uuid.UUID
    tenant_id: str
    assigned_department_id: str | None
    customer_company_id: str | None
    company_name: str | None
    email: str | None
    phone: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
