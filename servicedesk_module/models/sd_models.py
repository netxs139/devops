import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from devops_collector.models.base_models import Base


class CustomerIdentity(Base):
    __tablename__ = "sd_customer_identities"
    __table_args__ = {"comment": "ServiceDesk 外部客户身份表"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="客户唯一标识")
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, default="default", comment="租户ID(隔离边界)")
    assigned_department_id: Mapped[str | None] = mapped_column(String(32), index=True, comment="绑定的负责内部研发部门ID")
    customer_company_id: Mapped[str | None] = mapped_column(String(32), index=True, comment="外部客户公司ID")
    company_name: Mapped[str | None] = mapped_column(String(255), comment="客户/甲方公司名称")
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, comment="手机号")
    password_hash: Mapped[str | None] = mapped_column(String(255), comment="登录密码Hash")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), comment="更新时间"
    )


class Ticket(Base):
    __tablename__ = "sd_tickets"
    __table_args__ = {"comment": "ServiceDesk 外部服务台工单表"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="工单ID")
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, default="default", comment="租户ID(隔离边界)")
    reporter_id: Mapped[uuid.UUID] = mapped_column(comment="提报客户ID(关联CustomerIdentity)")
    title: Mapped[str] = mapped_column(String(255), comment="工单标题")
    description: Mapped[str | None] = mapped_column(Text, comment="工单详情")
    ticket_type: Mapped[str] = mapped_column(String(50), default="CONSULTATION", comment="类型: INCIDENT/CONSULTATION/REQUIREMENT/BUG")
    status: Mapped[str] = mapped_column(String(50), default="NEW", comment="状态: NEW/ACCEPTED/IN_PROGRESS/RESOLVED/CLOSED")
    product_id: Mapped[str | None] = mapped_column(String(32), index=True, comment="关联产品线ID")
    department_id: Mapped[str | None] = mapped_column(String(32), index=True, comment="负责的内部研发中心/部门ID")
    assignee_id: Mapped[str | None] = mapped_column(String(32), comment="分诊客服内部员工ID")
    agile_issue_id: Mapped[str | None] = mapped_column(String(64), comment="对应底层 GitLab CE 的 Issue IID")
    gitlab_group_id: Mapped[int | None] = mapped_column(comment="工单所属GitLab Group ID")
    gitlab_project_id: Mapped[int | None] = mapped_column(comment="接收池Project ID")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), comment="更新时间"
    )


class TicketComment(Base):
    __tablename__ = "sd_ticket_comments"
    __table_args__ = {"comment": "ServiceDesk 工单沟通记录"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="评论ID")
    ticket_id: Mapped[uuid.UUID] = mapped_column(index=True, comment="所属工单ID")
    author_type: Mapped[str] = mapped_column(String(50), comment="作者类型: EXTERNAL_CUSTOMER/INTERNAL_STAFF")
    author_id: Mapped[str] = mapped_column(String(36), comment="作者ID")
    content: Mapped[str] = mapped_column(Text, comment="评论内容")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), comment="创建时间")
