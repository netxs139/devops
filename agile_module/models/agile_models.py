import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column
from uuid6 import uuid7

from devops_collector.models.base_models import Base


class AgileProductMapping(Base):
    __tablename__ = "agile_product_mappings"
    __table_args__ = {"comment": "Agile 模块产品线与 GitLab 顶级群组及接收池的路由映射"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="映射ID")
    department_id: Mapped[str] = mapped_column(String(32), index=True, comment="研发中心/部门ID")
    product_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="产品线ID")
    product_name: Mapped[str] = mapped_column(String(255), comment="产品线名称")
    gitlab_group_id: Mapped[int] = mapped_column(Integer, comment="关联的 GitLab Top-level Group ID")
    reception_project_id: Mapped[int] = mapped_column(Integer, comment="专用的工单接收池 GitLab Project ID")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="映射是否生效")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), comment="更新时间"
    )
