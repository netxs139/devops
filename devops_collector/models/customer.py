"""Customer model for Master Data Management (MDM)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from devops_collector.models.base_models import Base, SCDMixin, TimestampMixin


if TYPE_CHECKING:
    pass


class Customer(Base, TimestampMixin, SCDMixin):
    """客户主数据表 (mdm_customers)。"""

    __tablename__ = "mdm_customers"
    __table_args__ = (
        Index("idx_mdm_customer_active_lookup", "customer_code", postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
        Index("uq_mdm_customer_code_active", "customer_code", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
        Index(
            "uq_mdm_customer_usci_active",
            "usci",
            unique=True,
            postgresql_where="is_current IS TRUE AND usci IS NOT NULL",
            sqlite_where=text("is_current = 1 AND usci IS NOT NULL"),
        ),
        {"comment": "客户主数据表"},
    )

    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    customer_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="客户唯一标识 (原生 UUID v7)")
    customer_code: Mapped[str] = mapped_column(String(100), index=True, nullable=False, comment="客户业务唯一编码")
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="客户公司名称")
    usci: Mapped[str | None] = mapped_column(String(18), index=True, nullable=True, comment="统一社会信用代码")
    industry_category: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="行业分类 (例如 金融/电信/政务)")
    customer_tier: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="客户等级/级别 (例如 A级/战略客户/普通客户)")
    business_owner_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True, comment="商务负责人 global_user_id (关联 IAM 用户)")

    def __repr__(self) -> str:
        """Magic method."""
        return f"<Customer(code='{self.customer_code}', name='{self.customer_name}', tier='{self.customer_tier}')>"
