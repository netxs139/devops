import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from devops_collector.models.base_models import (
    Base,
    TimestampMixin,
    int_pk,
    json_dict,
    str_50,
    str_100,
    str_200,
    str_255,
)


class AgileProductMapping(Base):
    """Agile 模块产品线映射模型"""

    __tablename__ = "agile_product_mappings"
    __table_args__ = {"comment": "Agile 模块产品线与 GitLab 顶级群组及接收池的路由映射"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="映射ID")
    department_id: Mapped[str] = mapped_column(String(32), index=True, comment="研发中心/部门ID")
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True, comment="产品线ID")
    product_name: Mapped[str] = mapped_column(String(255), comment="产品线名称")
    gitlab_group_id: Mapped[int] = mapped_column(Integer, comment="关联的 GitLab Top-level Group ID")
    reception_project_id: Mapped[int] = mapped_column(Integer, comment="专用的工单接收池 GitLab Project ID")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="映射是否生效")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), comment="更新时间"
    )


class EpicMaster(Base, TimestampMixin):
    """跨团队/长期史诗需求 (Epic) 主数据。

    用于管理跨越多个迭代、涉及多个团队的战略级需求组件 (Initiatives/Epics)。
    """

    __tablename__ = "mdm_epics"

    # 基础信息
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    parent_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="父级 Epic ID (支持多层级)")
    epic_code: Mapped[str_50] = mapped_column(unique=True, index=True, nullable=False, comment="史诗唯一编码 (如 EPIC-24Q1-001)")
    title: Mapped[str_200] = mapped_column(nullable=False, comment="史诗标题")
    description: Mapped[str | None] = mapped_column(comment="价值陈述与详细描述")
    status: Mapped[str_50 | None] = mapped_column(default="ANALYSIS", comment="状态 (ANALYSIS/BACKLOG/IN_PROGRESS/DONE/CANCELLED)")
    priority: Mapped[str | None] = mapped_column(default="P1", comment="优先级 (P0-Strategic / P1-High)")

    # 战略对齐 (软引用)
    okr_objective_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="关联战略目标ID (软引用)")
    investment_theme: Mapped[str_100 | None] = mapped_column(comment="投资主题 (如 技术债/新业务/合规/客户体验)")
    budget_cap: Mapped[float | None] = mapped_column(comment="预算上限 (人天或金额)")

    # 规划与进度 (软引用)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(index=True, comment="史诗负责人全局ID (软引用)")
    org_id: Mapped[int | None] = mapped_column(Integer, index=True, comment="负责人所属组织/部门ID (软引用)")

    # 时间规划
    start_date_is_fixed: Mapped[bool | None] = mapped_column(default=False, comment="是否固定开始时间 (False则自动继承子任务)")
    due_date_is_fixed: Mapped[bool | None] = mapped_column(default=False, comment="是否固定结束时间")
    planned_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="计划开始日期")
    planned_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="计划完成日期")
    actual_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="实际开始日期")
    actual_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="实际完成日期")

    progress: Mapped[float | None] = mapped_column(default=0.0, comment="总体进度 (0.0-1.0, 基于子任务聚合)")

    # 可视化与隐私
    color: Mapped[str | None] = mapped_column(comment="Roadmap展示颜色 (Hex Code)")
    is_confidential: Mapped[bool | None] = mapped_column(default=False, comment="是否机密 Epic")
    web_url: Mapped[str_255 | None] = mapped_column(comment="GitLab 原始链接")
    external_id: Mapped[str_50 | None] = mapped_column(comment="外部系统ID (如 GitLab Epic IID)")

    # 协作信息
    involved_teams: Mapped[json_dict | None] = mapped_column(comment="涉及团队列表 (JSON List)")
    tags: Mapped[json_dict | None] = mapped_column(comment="标签 (JSON List)")

    # Relationships (只保留自关联，移除外部模块的硬引用)
    parent: Mapped[Optional["EpicMaster"]] = relationship("EpicMaster", remote_side=[id], foreign_keys=[parent_id], backref="children")
