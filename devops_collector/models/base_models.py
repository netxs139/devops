"""Command module."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    from devops_collector.plugins.gitlab.models import GitLabProject

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, backref, mapped_column, relationship


# --- 2.0 类型别名 (Type Aliases) ---
int_pk = Annotated[int, mapped_column(primary_key=True, autoincrement=True, comment="自增主键")]
uuid_pk = Annotated[uuid.UUID, mapped_column(primary_key=True, default=uuid.uuid4, comment="全局唯一标识")]
str_50 = Annotated[str, mapped_column(String(50))]
str_100 = Annotated[str, mapped_column(String(100))]
str_200 = Annotated[str, mapped_column(String(200))]
str_255 = Annotated[str, mapped_column(String(255))]
json_dict = Annotated[dict, mapped_column(JSON)]


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类。"""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """时间戳与审计混入类，提供自动创建、更新时间及操作人记录。"""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(UTC), comment="最后更新时间", nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="创建者ID",
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="最后操作者ID",
    )


class TraceabilityMixin:
    """数据追溯混入类，记录数据来源与同步批次。"""

    source_system: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, comment="数据来源系统标识")
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True, comment="同步任务追踪 ID")
    raw_data: Mapped[json_dict | None] = mapped_column(JSON, nullable=True, comment="原始元数据暂存")


class SCDMixin(TraceabilityMixin):
    """SCD Type 2 慢变维支持混入类。继承追溯元数据。"""

    sync_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class OwnableMixin:
    """所有权混入类，用于 RLS 自动推断数据归属。"""

    @classmethod
    def get_owner_column(cls):
        """返回用于 '仅本人' (Scope 5) 权限校验的所有者字段对象。

        默认为 create_by (如果存在)。子类应重写此方法以返回正确的字段，
        例如 ProjectMaster.pm_user_id 或 Incident.owner_id。
        """
        if hasattr(cls, "create_by"):
            return cls.create_by
        return None


class CommitMetrics(Base, TimestampMixin):
    """单个提交的详细度量数据 (ELOC)。"""

    __tablename__ = "rpt_commit_metrics"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    commit_sha: Mapped[str_100] = mapped_column(unique=True, index=True, comment="提交SHA哈希值")
    project_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_projects.id"), nullable=True, index=True, comment="所属项目物理ID")
    author_email: Mapped[str_255] = mapped_column(index=True, comment="提交者邮箱")
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="作者全局用户ID")
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), comment="提交时间")
    raw_additions: Mapped[int] = mapped_column(Integer, default=0, comment="原始新增行数")
    raw_deletions: Mapped[int] = mapped_column(Integer, default=0, comment="原始删除行数")
    eloc_score: Mapped[float] = mapped_column(Float, default=0.0, comment="有效代码行数得分")
    impact_score: Mapped[float] = mapped_column(Float, default=0.0, comment="代码影响力得分")
    churn_lines: Mapped[int] = mapped_column(Integer, default=0, comment="代码翻动行数")
    comment_lines: Mapped[int] = mapped_column(Integer, default=0, comment="注释行数")
    test_lines: Mapped[int] = mapped_column(Integer, default=0, comment="测试代码行数")
    file_count: Mapped[int] = mapped_column(Integer, default=0, comment="涉及文件数")
    is_merge: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为合并提交")
    is_legacy_refactor: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为遗留代码重构")
    refactor_ratio: Mapped[float] = mapped_column(Float, default=0.0, comment="重构代码占比")


class DailyDevStats(Base, TimestampMixin):
    """开发人员行为的每日快照。"""

    __tablename__ = "rpt_daily_dev_stats"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), index=True, comment="用户ID")
    date: Mapped[date] = mapped_column(Date, index=True, comment="统计日期")
    first_commit_time: Mapped[datetime | None] = mapped_column(DateTime, comment="当日首次提交时间")
    last_commit_time: Mapped[datetime | None] = mapped_column(DateTime, comment="当日最后提交时间")
    commit_count: Mapped[int] = mapped_column(Integer, default=0, comment="当日提交次数")
    total_impact: Mapped[float] = mapped_column(Float, default=0.0, comment="当日总影响力得分")
    total_churn: Mapped[int] = mapped_column(Integer, default=0, comment="当日总代码翻动行数")


class DORAMetrics(Base, TimestampMixin):
    """项目或团队维度的 DORA 2.0 标准度量数据快照。"""

    __tablename__ = "rpt_dora_metrics"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    entity_id: Mapped[int] = mapped_column(index=True, comment="关联的项目或团队 ID")
    entity_type: Mapped[str_50] = mapped_column(index=True, comment="实体类型 (PROJECT/TEAM)")
    date: Mapped[date] = mapped_column(Date, index=True, comment="统计日期")

    deployment_count: Mapped[int] = mapped_column(Integer, default=0, comment="周期内成功部署次数")
    deployment_frequency: Mapped[float] = mapped_column(Float, default=0.0, comment="部署频率 (次/天)")

    lead_time_for_changes_avg: Mapped[float] = mapped_column(Float, default=0.0, comment="平均变更前置时间 (小时)")
    lead_time_for_changes_median: Mapped[float] = mapped_column(Float, default=0.0, comment="变更前置时间中位数 (小时)")

    change_failure_rate: Mapped[float] = mapped_column(Float, default=0.0, comment="变更失败率 (%)")
    failed_deployment_count: Mapped[int] = mapped_column(Integer, default=0, comment="失败部署次数")

    mttr_avg: Mapped[float] = mapped_column(Float, default=0.0, comment="故障平均恢复时长 (小时)")
    incident_count: Mapped[int] = mapped_column(Integer, default=0, comment="周期内事故数量")

    score_grade: Mapped[str | None] = mapped_column(String(20), comment="DORA 综合等级 (Elite/High/Medium/Low)")


class SatisfactionRecord(Base, TimestampMixin):
    """开发人员体验/满意度调查记录 (SPACE 框架中的 Satisfaction)。"""

    __tablename__ = "rpt_satisfaction_records"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    user_email: Mapped[str_255] = mapped_column(index=True, comment="受访用户邮箱")
    score: Mapped[int] = mapped_column(Integer, comment="满意度评分 (1-5)")
    date: Mapped[date] = mapped_column(Date, index=True, comment="调查日期")
    tags: Mapped[str_255 | None] = mapped_column(nullable=True, comment="标签")
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="开放式反馈评语")


class Product(Base, TimestampMixin, SCDMixin):
    """产品主数据表 (mdm_product)。"""

    __tablename__ = "mdm_products"
    __table_args__ = (
        Index("idx_mdm_product_active_lookup", "product_code", postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
        Index("uq_mdm_product_code_active", "product_code", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
    )
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    product_code: Mapped[str_100] = mapped_column(index=True, nullable=False, comment="产品业务唯一标识")
    product_name: Mapped[str_255] = mapped_column(nullable=False, comment="产品名称")
    product_description: Mapped[str] = mapped_column(Text, nullable=False, comment="产品描述")
    category: Mapped[str_100 | None] = mapped_column(comment="产品分类")
    version_schema: Mapped[str_50] = mapped_column(nullable=False, comment="版本命名规则")
    specification: Mapped[json_dict | None] = mapped_column(comment="产品规格配置")
    runtime_env: Mapped[json_dict | None] = mapped_column(comment="运行环境配置")
    checksum: Mapped[str_255 | None] = mapped_column(comment="最新版本校验码")
    lifecycle_status: Mapped[str_50] = mapped_column(default="Active", comment="生命周期状态")
    repo_url: Mapped[str_255 | None] = mapped_column(comment="主代码仓库URL")
    artifact_path: Mapped[str_255 | None] = mapped_column(comment="制品存储路径")
    owner_team_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_organizations.id"), index=True, comment="负责团队ID")
    product_manager_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), index=True, comment="产品经理")
    dev_lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="开发经理")
    qa_lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="测试经理")
    release_lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="发布经理")
    matching_patterns: Mapped[json_dict | None] = mapped_column(comment="自动识别匹配模式列表")
    parent_product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("mdm_products.id", use_alter=True, name="fk_product_parent_id"), nullable=True, index=True, comment="上级产品ID"
    )
    node_type: Mapped[str] = mapped_column(String(20), default="APP", comment="节点类型")

    parent: Mapped[Product | None] = relationship(
        "Product", remote_side="Product.id", foreign_keys=[parent_product_id], backref=backref("children", cascade="all")
    )
    owner_team: Mapped[Organization] = relationship("Organization", foreign_keys=[owner_team_id], back_populates="products")
    product_manager: Mapped[User] = relationship("User", foreign_keys=[product_manager_id], back_populates="managed_products_as_pm")
    dev_lead: Mapped[User | None] = relationship("User", foreign_keys=[dev_lead_id], back_populates="managed_products_as_dev")
    qa_lead: Mapped[User | None] = relationship("User", foreign_keys=[qa_lead_id], back_populates="managed_products_as_qa")
    release_lead: Mapped[User | None] = relationship("User", foreign_keys=[release_lead_id], back_populates="managed_products_as_release")
    project_relations: Mapped[list[ProjectProductRelation]] = relationship("ProjectProductRelation", back_populates="product")

    def __repr__(self) -> str:
        """Magic method."""
        return f"<Product(code='{self.product_code}', name='{self.product_name}', version={self.sync_version})>"


class ProjectProductRelation(Base, TimestampMixin):
    """项目与产品的关联权重表。"""

    __tablename__ = "mdm_rel_project_product"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    project_id: Mapped[int] = mapped_column(ForeignKey("mdm_projects.id"), nullable=False, index=True, comment="项目ID")
    org_id: Mapped[int] = mapped_column(ForeignKey("mdm_organizations.id"), nullable=False, index=True, comment="所属组织ID")
    product_id: Mapped[int] = mapped_column(ForeignKey("mdm_products.id"), nullable=False, index=True, comment="产品ID")
    relation_type: Mapped[str_50] = mapped_column(default="PRIMARY", comment="关联类型")
    allocation_ratio: Mapped[float] = mapped_column(Float, default=1.0, comment="工作量分配比例")
    __table_args__ = (UniqueConstraint("project_id", "product_id", name="uq_project_product"),)
    project: Mapped[ProjectMaster] = relationship("ProjectMaster", back_populates="product_relations")
    product: Mapped[Product] = relationship("Product", back_populates="project_relations")


class BusinessSystem(Base, TimestampMixin):
    """业务系统模型。"""

    __tablename__ = "mdm_business_systems"

    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    code: Mapped[str_255] = mapped_column(unique=True, nullable=False, index=True, comment="系统标准代号")
    name: Mapped[str_100] = mapped_column(nullable=False, comment="系统中文名称")
    description: Mapped[str | None] = mapped_column(Text, comment="系统业务描述")
    domain: Mapped[str_50 | None] = mapped_column(index=True, comment="所属业务域")
    status: Mapped[str] = mapped_column(String(20), default="PRODUCTION", comment="生命周期状态")
    rank: Mapped[str] = mapped_column(String(10), default="T1", comment="重要性分级")
    architecture_type: Mapped[str_50 | None] = mapped_column(comment="架构类型")
    primary_tech_stack: Mapped[str_100 | None] = mapped_column(comment="主要技术栈")
    dr_level: Mapped[str_50 | None] = mapped_column(comment="容灾等级要求")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), comment="技术负责人")
    business_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), comment="业务负责人")

    services: Mapped[list[Service]] = relationship("Service", back_populates="system")


#     owner: Mapped[User | None] = relationship("User", foreign_keys=[owner_id])
#     business_owner: Mapped[User | None] = relationship("User", foreign_keys=[business_owner_id])


class Service(Base, TimestampMixin, SCDMixin):
    """服务/组件目录表。"""

    __tablename__ = "mdm_services"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    name: Mapped[str_200] = mapped_column(nullable=False, comment="服务名称")
    tier: Mapped[str | None] = mapped_column(String(20), comment="服务级别")
    org_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_organizations.id"), nullable=True, comment="负责组织ID")
    description: Mapped[str | None] = mapped_column(Text, comment="服务描述")
    system_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_business_systems.id"), nullable=True, comment="所属业务系统ID")
    lifecycle: Mapped[str] = mapped_column(String(20), default="production", comment="生命周期")
    component_type: Mapped[str] = mapped_column(String(20), default="service", comment="组件类型")
    tags: Mapped[json_dict | None] = mapped_column(comment="标签列表")
    links: Mapped[json_dict | None] = mapped_column(comment="相关链接")

    system: Mapped[BusinessSystem | None] = relationship("BusinessSystem", back_populates="services")
    #     organization: Mapped[Organization | None] = relationship("Organization", foreign_keys=[org_id])
    costs: Mapped[list[ResourceCost]] = relationship("ResourceCost", back_populates="service")
    slos: Mapped[list[SLO]] = relationship("SLO", back_populates="service", cascade="all, delete-orphan")
    project_mappings: Mapped[list[ServiceProjectMapping]] = relationship("ServiceProjectMapping", back_populates="service", cascade="all, delete-orphan")
    resources: Mapped[list[EntityTopology]] = relationship("EntityTopology", back_populates="service", cascade="all, delete-orphan")

    @property
    def total_cost(self) -> float:
        """Execute command."""
        return float(sum(c.amount or 0.0 for c in self.costs))

    @property
    def investment_roi(self) -> float:
        """Execute command."""
        return 10.0 if self.total_cost > 0 else 0.0


class ResourceCost(Base, TimestampMixin):
    """资源成本记录明细表。"""

    __tablename__ = "stg_mdm_resource_costs"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    service_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_services.id"), nullable=True, index=True, comment="关联服务ID")
    cost_code_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_cost_codes.id"), nullable=True, index=True, comment="成本科目ID")
    purchase_contract_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_purchase_contracts.id"), nullable=True, index=True, comment="采购合同ID")
    period: Mapped[str | None] = mapped_column(index=True, comment="费用周期 (YYYY-MM)")
    amount: Mapped[float | None] = mapped_column(default=0.0, comment="费用金额")
    currency: Mapped[str | None] = mapped_column(default="CNY", comment="币种")
    cost_type: Mapped[str_50 | None] = mapped_column(comment="成本类型 (云资源/人力/软件)")
    cost_item: Mapped[str_200 | None] = mapped_column(comment="成本项目名称")
    vendor_name: Mapped[str_200 | None] = mapped_column(comment="供应商名称")
    capex_opex_flag: Mapped[str | None] = mapped_column(comment="CAPEX/OPEX标志")
    source_system: Mapped[str_100 | None] = mapped_column(comment="数据来源系统")
    correlation_id: Mapped[str_100 | None] = mapped_column(index=True, comment="关联追踪ID")
    service: Mapped[Service | None] = relationship("Service", back_populates="costs")
    cost_code: Mapped[CostCode | None] = relationship("CostCode")
    purchase_contract: Mapped[PurchaseContract | None] = relationship("PurchaseContract")


class MetricDefinition(Base, TimestampMixin, SCDMixin):
    """指标语义定义表。"""

    __tablename__ = "mdm_metric_definitions"
    __table_args__ = (
        Index("uq_mdm_metric_code_active", "metric_code", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
    )

    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    metric_code: Mapped[str_100] = mapped_column(index=True, nullable=False, comment="指标唯一编码")
    metric_name: Mapped[str_200] = mapped_column(nullable=False, comment="指标展示名称")
    domain: Mapped[str_50] = mapped_column(nullable=False, comment="所属业务域")
    metric_type: Mapped[str_50 | None] = mapped_column(comment="指标类型")
    calculation_logic: Mapped[str | None] = mapped_column(Text, comment="计算逻辑说明")
    unit: Mapped[str_50 | None] = mapped_column(comment="度量单位")
    aggregate_type: Mapped[str | None] = mapped_column(String(20), comment="聚合方式")
    source_model: Mapped[str_200 | None] = mapped_column(comment="来源数据模型")
    dimension_scope: Mapped[json_dict | None] = mapped_column(comment="允许下钻的维度列表")
    is_standard: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否集团标准指标")
    business_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), index=True, comment="业务负责人")
    technical_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), index=True, comment="技术负责人")
    time_grain: Mapped[str_50 | None] = mapped_column(comment="统计时间粒度")
    update_cycle: Mapped[str_50 | None] = mapped_column(comment="数据刷新周期")
    status: Mapped[str] = mapped_column(String(50), default="RELEASED", comment="生命周期状态")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    #     business_owner: Mapped[User | None] = relationship("User", foreign_keys=[business_owner_id])
    #     technical_owner: Mapped[User | None] = relationship("User", foreign_keys=[technical_owner_id])

    def __repr__(self):
        """Magic method."""
        return f"<MetricDefinition(code='{self.metric_code}', name='{self.metric_name}', version={self.sync_version})>"


class SystemRegistry(Base, TimestampMixin, SCDMixin):
    """三方系统注册表，记录对接的所有外部系统 (GitLab, Jira, Sonar 等)。

    作为数据源治理注册中心，定义了连接方式、同步策略及数据治理属性。
     - 用于管理 Collector 采集目标
     - 用于 Issue Tracking 集成配置
    支持 SCD Type 2 以审计连接配置的变更记录。
    """

    __tablename__ = "mdm_systems_registry"
    __table_args__ = (
        Index("uq_mdm_system_code_active", "system_code", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
    )

    # 基础信息
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    system_code: Mapped[str_50] = mapped_column(nullable=False, index=True, comment="系统唯一标准代号 (如 gitlab-corp)")
    system_name: Mapped[str_100] = mapped_column(nullable=False, comment="系统显示名称")
    system_type: Mapped[str_50 | None] = mapped_column(comment="工具类型 (VCS/TICKET/CI/SONAR/K8S)")
    env_tag: Mapped[str | None] = mapped_column(default="PROD", comment="环境标签 (PROD/Stage/Test)")

    # 接口与连接配置
    base_url: Mapped[str_255 | None] = mapped_column(comment="API 基础地址 (Base URL)")
    api_version: Mapped[str | None] = mapped_column(comment="API 接口版本 (如 v4, api/v2)")
    auth_type: Mapped[str_50 | None] = mapped_column(comment="认证方式 (OAuth2/Token/Basic)")
    credential_key: Mapped[str_100 | None] = mapped_column(comment="凭证引用Key (指向Vault或Env Var)")
    plugin_config: Mapped[json_dict | None] = mapped_column(comment="插件特定配置 (JSON, 如过滤规则、超时设置)")

    # 数据同步策略
    sync_method: Mapped[str_50 | None] = mapped_column(comment="同步方式 (CDC/Polling/Webhook)")
    update_cycle: Mapped[str_50 | None] = mapped_column(comment="更新频率 (Realtime/Hourly/Daily)")
    enabled_plugins: Mapped[str_255 | None] = mapped_column(comment="启用的采集插件列表 (逗号分隔)")

    # 数据治理与安全
    data_sensitivity: Mapped[str | None] = mapped_column(comment="数据敏感级 (L1-L4)")
    sla_level: Mapped[str | None] = mapped_column(comment="服务等级 (P0-Critical / P1-High)")
    technical_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), index=True, comment="技术负责人")

    # 状态监控
    is_active: Mapped[bool | None] = mapped_column(default=True, comment="是否启用采集")
    last_heartbeat: Mapped[datetime | None] = mapped_column(comment="最后连通性检查时间")
    last_sync_at: Mapped[datetime | None] = mapped_column(comment="最后一次数据同步时间")
    remarks: Mapped[str | None] = mapped_column(comment="备注说明")

    #     technical_owner: Mapped[User | None] = relationship("User", foreign_keys=[technical_owner_id])
    projects: Mapped[list[ProjectMaster]] = relationship("ProjectMaster", back_populates="source_system_ref")


class EntityTopology(Base, TimestampMixin, SCDMixin):
    """实体-资源映射表 (Infrastructure Mapping).

    将逻辑上的业务服务 (Service) 绑定到物理上的基础设施资源 (GitLab Repo, Sonar Project, Jenkins Job)。
    它是连接 "业务架构" (Service) 与 "工具设施" (SystemRegistry) 的胶水层。
    """

    __tablename__ = "mdm_entity_topology"

    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]

    # 1. 逻辑侧 (Who) - 指向业务服务
    # 1. 逻辑侧 (Who) - 指向业务服务 OR 项目
    service_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_services.id"), nullable=True, index=True, comment="所属业务服务ID")
    project_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_projects.id"), nullable=True, index=True, comment="所属项目ID")

    # 2. 物理侧 (Where) - 指向外部工具资源
    # 明确指出是哪个系统实例 (e.g. gitlab-corp) 下 of the which resource ID (e.g. project-1024)
    system_id: Mapped[int] = mapped_column(
        ForeignKey("mdm_systems_registry.id"),
        nullable=False,
        index=True,
        comment="来源系统物理ID (如 gitlab-corp 对应的 ID)",
    )
    external_resource_id: Mapped[str_100] = mapped_column(nullable=False, comment="外部资源唯一标识 (如 Project ID, Repo URL)")
    resource_name: Mapped[str_200 | None] = mapped_column(comment="资源显示名称快照 (如 backend/payment-service)")
    env_tag: Mapped[str | None] = mapped_column(default="PROD", comment="环境标签 (PROD/UAT/TEST/DEV)")

    # 3. 关系定义 (What)
    # 资源类型: source-code, ci-pipeline, quality-gate, deployment-target, database
    element_type: Mapped[str_50 | None] = mapped_column(default="source-code", comment="资源类型 (source-code/ci-pipeline/k8s-deployment/db-instance)")

    # 4. 状态与元数据
    is_active: Mapped[bool | None] = mapped_column(default=True, comment="关联是否有效")
    last_verified_at: Mapped[datetime | None] = mapped_column(comment="最后一次验证连接有效的时间")
    meta_info: Mapped[json_dict | None] = mapped_column(comment="额外元数据连接信息 (JSON, 如 webhook_id, bind_key)")

    # Relationships
    service: Mapped[Service | None] = relationship("Service", back_populates="resources")
    project: Mapped[ProjectMaster | None] = relationship("ProjectMaster", foreign_keys=[project_id])
    target_system: Mapped[SystemRegistry | None] = relationship("SystemRegistry", foreign_keys=[system_id])


class SyncLog(Base, TimestampMixin):
    """插件数据同步日志记录表。"""

    __tablename__ = "sys_sync_logs"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    project_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_projects.id"), nullable=True, index=True, comment="关联项目物理ID")
    external_id: Mapped[str_100 | None] = mapped_column(index=True, comment="来源系统原始ID")
    source: Mapped[str_50 | None] = mapped_column(index=True, comment="来源系统类型 (gitlab/zentao/sonarqube)")
    status: Mapped[str_50 | None] = mapped_column(comment="同步状态 (SUCCESS/FAILED/RUNNING)")
    message: Mapped[str | None] = mapped_column(comment="同步结果信息")
    correlation_id: Mapped[str_100 | None] = mapped_column(index=True, comment="关联追踪ID")


class Location(Base, TimestampMixin):
    """地理位置或机房位置参考表。"""

    __tablename__ = "mdm_locations"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    location_code: Mapped[str_50 | None] = mapped_column(unique=True, index=True, comment="位置唯一业务标识 (如 LOC_BJ_01)")
    code: Mapped[str | None] = mapped_column(index=True, comment="行政区划或业务编码 (如 CN-GD, 440000)")
    location_name: Mapped[str_200] = mapped_column(nullable=False, comment="位置名称 (如 广东省)")
    short_name: Mapped[str_50 | None] = mapped_column(comment="简称 (如 广东)")
    location_type: Mapped[str_50 | None] = mapped_column(comment="位置类型 (country/province/city/site/datacenter)")
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("mdm_locations.id", use_alter=True, name="fk_location_parent_id"), nullable=True, comment="上级位置物理ID"
    )
    region: Mapped[str_50 | None] = mapped_column(comment="区域 (华北/华东/华南)")
    is_active: Mapped[bool | None] = mapped_column(default=True, comment="是否启用")
    manager_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("mdm_identities.global_user_id", use_alter=True, name="fk_location_manager"),
        nullable=True,
        comment="负责人",
    )


class Calendar(Base, TimestampMixin):
    """公共日历/节假日参考表。"""

    __tablename__ = "mdm_calendar"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    date_day: Mapped[date] = mapped_column(unique=True, index=True, nullable=False, comment="日期")
    year_number: Mapped[int | None] = mapped_column(index=True, comment="年份")
    month_number: Mapped[int | None] = mapped_column(comment="月份 (1-12)")
    quarter_number: Mapped[int | None] = mapped_column(comment="季度 (1-4)")
    day_of_week: Mapped[int | None] = mapped_column(comment="星期几 (1=周一, 7=周日)")
    is_workday: Mapped[bool | None] = mapped_column(default=True, comment="是否工作日")
    is_holiday: Mapped[bool | None] = mapped_column(default=False, comment="是否节假日")
    holiday_name: Mapped[str_100 | None] = mapped_column(comment="节假日名称")
    fiscal_year: Mapped[str | None] = mapped_column(comment="财年")
    fiscal_quarter: Mapped[str | None] = mapped_column(comment="财务季度")
    week_of_year: Mapped[int | None] = mapped_column(comment="年内周数")
    season_tag: Mapped[str | None] = mapped_column(comment="季节标签 (春/夏/秋/冬)")


class RawDataStaging(Base, TimestampMixin):
    """原始数据暂存表 (Staging 层)，用于存放未经处理的 API Payload。"""

    __tablename__ = "stg_raw_data"
    __table_args__ = (UniqueConstraint("source", "entity_type", "external_id", name="uq_raw_data_staging"),)
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    source: Mapped[str_50 | None] = mapped_column(comment="数据来源系统 (gitlab/jira/sonar)")
    entity_type: Mapped[str_50 | None] = mapped_column(comment="实体类型 (project/issue/pipeline)")
    external_id: Mapped[str_100 | None] = mapped_column(index=True, comment="外部系统记录ID")
    payload: Mapped[json_dict] = mapped_column(comment="原始 JSON 数据负载")
    schema_version: Mapped[str | None] = mapped_column(comment="Payload 结构版本")
    correlation_id: Mapped[str_100 | None] = mapped_column(index=True, comment="关联追踪ID")
    collected_at: Mapped[datetime | None] = mapped_column(comment="采集时间")


class OKRObjective(Base, TimestampMixin, SCDMixin):
    """OKR 目标定义表。"""

    __tablename__ = "mdm_okr_objectives"
    __table_args__ = (
        Index("uq_mdm_okr_objective_active", "objective_id", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
    )
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    objective_id: Mapped[str_50 | None] = mapped_column(index=True, comment="目标唯一标识")
    title: Mapped[str_255] = mapped_column(nullable=False, comment="目标标题")
    description: Mapped[str | None] = mapped_column(comment="目标描述")
    period: Mapped[str | None] = mapped_column(index=True, comment="周期 (2024-Q1/2024-H1)")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), index=True, comment="负责人")
    org_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_organizations.id"), index=True, comment="所属组织ID")
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("mdm_okr_objectives.id", use_alter=True, name="fk_okr_parent_id"), index=True, comment="上级目标ID"
    )
    product_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_products.id"), index=True, comment="关联产品ID")
    status: Mapped[str | None] = mapped_column(default="ACTIVE", comment="状态 (ACTIVE/COMPLETED/ABANDONED)")
    progress: Mapped[float | None] = mapped_column(default=0.0, comment="进度 (0.0-1.0)")

    owner: Mapped[User | None] = relationship("User", foreign_keys=[owner_id])
    organization: Mapped[Organization | None] = relationship("Organization", foreign_keys=[org_id])
    parent: Mapped[OKRObjective | None] = relationship("OKRObjective", remote_side="OKRObjective.id", backref=backref("children", cascade="all"))
    product: Mapped[Product | None] = relationship("Product", foreign_keys=[product_id], backref=backref("objectives", cascade="all"))
    key_results: Mapped[list[OKRKeyResult]] = relationship("OKRKeyResult", back_populates="objective", cascade="all, delete-orphan")


class OKRKeyResult(Base, TimestampMixin):
    """OKR 关键结果 (KR) 定义表。"""

    __tablename__ = "mdm_okr_key_results"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    objective_id: Mapped[int] = mapped_column(ForeignKey("mdm_okr_objectives.id"), nullable=False, index=True, comment="关联目标ID")
    title: Mapped[str_255] = mapped_column(nullable=False, comment="KR标题")
    target_value: Mapped[float] = mapped_column(nullable=False, comment="目标值")
    initial_value: Mapped[float | None] = mapped_column(default=0.0, comment="初始基线值")
    current_value: Mapped[float | None] = mapped_column(default=0.0, comment="当前值")
    metric_unit: Mapped[str | None] = mapped_column(comment="单位 (%/天/个)")
    weight: Mapped[float | None] = mapped_column(default=1.0, comment="权重")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), index=True, comment="负责人")
    progress: Mapped[float | None] = mapped_column(default=0.0, comment="进度 (0.0-1.0)")
    linked_metrics_config: Mapped[json_dict | None] = mapped_column(comment="关联度量配置 (JSON)")

    objective: Mapped[OKRObjective | None] = relationship("OKRObjective", back_populates="key_results")


#     owner: Mapped[User | None] = relationship("User", foreign_keys=[owner_id])


class TraceabilityLink(Base, TimestampMixin):
    """跨系统追溯链路表，连接需求与代码、测试与发布。"""

    __tablename__ = "mdm_traceability_links"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    source_system: Mapped[str_50 | None] = mapped_column(comment="源系统 (jira/gitlab)")
    source_type: Mapped[str_50 | None] = mapped_column(comment="源实体类型 (requirement/story)")
    source_id: Mapped[str_100 | None] = mapped_column(index=True, comment="源实体ID")
    target_system: Mapped[str_50 | None] = mapped_column(comment="目标系统 (gitlab/jenkins)")
    target_type: Mapped[str_50 | None] = mapped_column(comment="目标实体类型 (commit/merge_request/build)")
    target_id: Mapped[str_100 | None] = mapped_column(index=True, comment="目标实体ID")
    link_type: Mapped[str_50 | None] = mapped_column(comment="链路类型 (implements/tests/deploys)")
    raw_data: Mapped[json_dict | None] = mapped_column(comment="原始关联数据 (JSON)")

    __table_args__ = (UniqueConstraint("source_id", "target_id", "link_type", name="uq_traceability_link"),)


class JenkinsTestExecution(Base, TimestampMixin):
    """Jenkins 测试执行汇总记录表。

    存储来自 Jenkins 持续集成工具的测试报告汇总数据。
    """

    __tablename__ = "qa_jenkins_test_executions"

    # 基础标识
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    project_id: Mapped[int | None] = mapped_column(nullable=True, index=True, comment="关联 GitLab 项目 ID")
    build_id: Mapped[str_100] = mapped_column(nullable=False, index=True, comment="构建 ID (Jenkins Build Number)")

    # 测试分类
    test_level: Mapped[str_50 | None] = mapped_column(comment="测试层级 (Unit/API/UI/Performance/Automation)")
    test_tool: Mapped[str_100 | None] = mapped_column(comment="测试工具 (Jenkins/JUnit/Pytest)")

    # 统计数据
    total_cases: Mapped[int | None] = mapped_column(default=0, comment="用例总数")
    passed_count: Mapped[int | None] = mapped_column(default=0, comment="通过用例数")
    failed_count: Mapped[int | None] = mapped_column(default=0, comment="失败用例数")
    skipped_count: Mapped[int | None] = mapped_column(default=0, comment="跳过用例数")
    pass_rate: Mapped[float | None] = mapped_column(default=0.0, comment="通过率 (%)")
    duration_ms: Mapped[int | None] = mapped_column(default=0, comment="执行时长 (毫秒)")

    # 原始数据
    raw_data: Mapped[json_dict | None] = mapped_column(comment="原始测试报告 JSON")

    # 唯一约束: 同一项目、同一构建、同一测试层级只能有一条记录
    __table_args__ = (UniqueConstraint("project_id", "build_id", "test_level", name="uq_jenkins_test_execution"),)


class Incident(Base, TimestampMixin, SCDMixin, OwnableMixin):
    """线上事故/线上问题记录表。"""

    __tablename__ = "mdm_incidents"

    @classmethod
    def get_owner_column(cls):
        """Execute command."""
        return cls.owner_id

    # 基础信息
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    title: Mapped[str_200] = mapped_column(nullable=False, comment="事故标题")
    description: Mapped[str | None] = mapped_column(comment="事故详细描述")
    severity: Mapped[str | None] = mapped_column(comment="严重等级 (P0/P1/P2/P3)")
    status: Mapped[str | None] = mapped_column(default="OPEN", comment="状态 (OPEN:处理中 / RESOLVED:已恢复 / CLOSED:已结单 / MONITORING:观察中)")

    # 时空信息 (SRE Metrics)
    occurred_at: Mapped[datetime | None] = mapped_column(comment="故障发生时间 (用于计算 TTI: Time to Impact)")
    detected_at: Mapped[datetime | None] = mapped_column(comment="故障发现时间 (用于计算 MTTD: Time to Detect)")
    resolved_at: Mapped[datetime | None] = mapped_column(comment="业务恢复时间 (用于计算 MTTR: Time to Restore)")
    location_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_locations.id"), index=True, nullable=True, comment="故障发生地点ID")

    # 根因与复盘 (Post-mortem)
    root_cause_category: Mapped[str_50 | None] = mapped_column(comment="根因分类 (Code Change/Config Change/Capacity/Infrastructure/Exteanl)")
    post_mortem_url: Mapped[str_255 | None] = mapped_column(comment="复盘报告链接 (Confluence/Doc URL)")

    # 影响范围 (Impact)
    affected_users: Mapped[int | None] = mapped_column(comment="受影响用户数量预估")
    financial_loss: Mapped[float | None] = mapped_column(default=0.0, comment="预估经济损失金额 (CNY)")

    # 责任归属
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="主责任人")
    project_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_projects.id"), nullable=True, index=True, comment="关联项目ID")
    service_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_services.id"), nullable=True, index=True, comment="故障服务ID")

    location: Mapped[Location | None] = relationship("Location")
    #     owner: Mapped[User | None] = relationship("User", foreign_keys=[owner_id])
    project: Mapped[ProjectMaster | None] = relationship("ProjectMaster", foreign_keys=[project_id])
    service: Mapped[Service | None] = relationship("Service", foreign_keys=[service_id])

    @property
    def mttr_minutes(self) -> float:
        """计算故障恢复时长 (分钟)。"""
        if self.resolved_at and self.occurred_at:
            delta = self.resolved_at - self.occurred_at
            return delta.total_seconds() / 60.0
        return 0.0


class ServiceProjectMapping(Base, TimestampMixin):
    """服务与工程项目的多对多关联映射表。"""

    __tablename__ = "mdm_service_project_mapping"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    service_id: Mapped[int] = mapped_column(ForeignKey("mdm_services.id"), nullable=False, index=True, comment="服务ID")
    source: Mapped[str_50 | None] = mapped_column(comment="项目来源系统 (gitlab/jira)")
    project_id: Mapped[int | None] = mapped_column(comment="外部项目ID")
    service: Mapped[Service | None] = relationship("Service", back_populates="project_mappings")


class SLO(Base, TimestampMixin):
    """SLO (服务水平目标) 定义表。"""

    __tablename__ = "mdm_slo_definitions"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    service_id: Mapped[int] = mapped_column(ForeignKey("mdm_services.id"), nullable=False, index=True, comment="关联服务ID")
    name: Mapped[str_100] = mapped_column(nullable=False, comment="SLO 名称")
    indicator_type: Mapped[str_50 | None] = mapped_column(comment="指标类型 (Availability/Latency/Throughput)")
    target_value: Mapped[float | None] = mapped_column(comment="目标值")
    metric_unit: Mapped[str | None] = mapped_column(comment="度量单位 (%/ms)")
    time_window: Mapped[str | None] = mapped_column(comment="统计窗口期 (28d/7d)")
    service: Mapped[Service | None] = relationship("Service", back_populates="slos")


class ProjectMaster(Base, TimestampMixin, SCDMixin, OwnableMixin):
    """项目全生命周期主数据 (mdm_projects)。"""

    __tablename__ = "mdm_projects"
    __table_args__ = (
        Index("idx_mdm_project_active_lookup", "project_code", postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
        Index("uq_mdm_project_code_active", "project_code", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
        Index("uq_mdm_project_external_id_active", "external_id", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
    )
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    project_code: Mapped[str_100] = mapped_column(index=True, nullable=False, comment="项目业务唯一标识")

    @classmethod
    def get_owner_column(cls):
        """Execute command."""
        return cls.pm_user_id

    project_name: Mapped[str_200] = mapped_column(nullable=False, comment="项目名称")
    project_type: Mapped[str_50 | None] = mapped_column(comment="项目类型")
    status: Mapped[str] = mapped_column(String(50), default="PLAN", comment="项目状态")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    pm_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="项目经理")
    product_owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="产品经理")
    dev_lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="开发经理")
    qa_lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="测试经理")
    release_lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("mdm_identities.global_user_id"), nullable=True, index=True, comment="发布经理")
    org_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_organizations.id"), index=True, comment="负责部门ID")
    location_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_locations.id"), nullable=True, index=True, comment="项目所属/实施地点ID")
    plan_start_date: Mapped[date | None] = mapped_column(Date, comment="计划开始日期")
    plan_end_date: Mapped[date | None] = mapped_column(Date, comment="计划结束日期")
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="实际开始时间")
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="实际结束时间")
    external_id: Mapped[str_100 | None] = mapped_column(comment="外部系统项目ID")
    system_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_systems_registry.id"), index=True, comment="数据来源系统")
    budget_code: Mapped[str_100 | None] = mapped_column(comment="预算编码")
    budget_type: Mapped[str_50 | None] = mapped_column(comment="预算类型")
    lead_repo_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="主代码仓库ID")
    description: Mapped[str | None] = mapped_column(Text, comment="项目描述")

    organization: Mapped[Organization | None] = relationship("Organization", foreign_keys=[org_id])
    project_manager: Mapped[User | None] = relationship("User", foreign_keys=[pm_user_id])
    product_owner: Mapped[User | None] = relationship("User", foreign_keys=[product_owner_id])
    dev_lead: Mapped[User | None] = relationship("User", foreign_keys=[dev_lead_id])
    qa_lead: Mapped[User | None] = relationship("User", foreign_keys=[qa_lead_id])
    release_lead: Mapped[User | None] = relationship("User", foreign_keys=[release_lead_id])
    source_system_ref: Mapped[SystemRegistry | None] = relationship("SystemRegistry", back_populates="projects")
    gitlab_repos: Mapped[list[GitLabProject]] = relationship("GitLabProject", back_populates="mdm_project")
    product_relations: Mapped[list[ProjectProductRelation]] = relationship("ProjectProductRelation", back_populates="project")

    def __repr__(self) -> str:
        """Magic method."""
        return f"<ProjectMaster(code='{self.project_code}', name='{self.project_name}')>"


class CostCode(Base, TimestampMixin):
    """成本科目 (CBS) 模型。"""

    __tablename__ = "mdm_cost_codes"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    code: Mapped[str_50] = mapped_column(unique=True, nullable=False, index=True, comment="科目编码")
    name: Mapped[str_200] = mapped_column(nullable=False, comment="科目名称")
    category: Mapped[str_50 | None] = mapped_column(comment="科目分类 (人力/硬件/软件/服务)")
    description: Mapped[str | None] = mapped_column(comment="科目描述")
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_cost_codes.id"), nullable=True, comment="上级科目ID")
    default_capex_opex: Mapped[str | None] = mapped_column(comment="默认CAPEX/OPEX属性")
    is_active: Mapped[bool | None] = mapped_column(default=True, comment="是否启用")
    parent: Mapped[CostCode | None] = relationship("CostCode", remote_side="CostCode.id", foreign_keys=[parent_id], backref="children")


class LaborRateConfig(Base, TimestampMixin):
    """人工标准费率配置表。"""

    __tablename__ = "mdm_labor_rate_config"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    job_title_level: Mapped[str_50] = mapped_column(nullable=False, comment="职级 (P5/P6/P7/M1/M2)")
    daily_rate: Mapped[float] = mapped_column(nullable=False, comment="日费率 (元)")
    hourly_rate: Mapped[float | None] = mapped_column(comment="时费率 (元)")
    currency: Mapped[str | None] = mapped_column(default="CNY", comment="币种")
    effective_date: Mapped[datetime | None] = mapped_column(comment="生效日期")
    is_active: Mapped[bool | None] = mapped_column(default=True, comment="是否启用")


class RevenueContract(Base, TimestampMixin):
    """销售/收入合同主数据表格。"""

    __tablename__ = "mdm_revenue_contracts"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    contract_no: Mapped[str_100] = mapped_column(unique=True, nullable=False, index=True, comment="合同编号")
    title: Mapped[str_255 | None] = mapped_column(comment="合同标题")
    client_name: Mapped[str_255 | None] = mapped_column(comment="客户名称")
    total_value: Mapped[float | None] = mapped_column(default=0.0, comment="合同总额")
    currency: Mapped[str | None] = mapped_column(default="CNY", comment="币种")
    sign_date: Mapped[date | None] = mapped_column(comment="签约日期")
    product_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_products.id"), nullable=True, index=True, comment="关联产品ID")
    product: Mapped[Product | None] = relationship("Product")
    payment_nodes: Mapped[list[ContractPaymentNode]] = relationship("ContractPaymentNode", back_populates="contract", cascade="all, delete-orphan")


class PurchaseContract(Base, TimestampMixin):
    """采购/支出合同主数据。"""

    __tablename__ = "mdm_purchase_contracts"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    contract_no: Mapped[str_100] = mapped_column(unique=True, nullable=False, index=True, comment="合同编号")
    title: Mapped[str_255 | None] = mapped_column(comment="合同标题")
    vendor_name: Mapped[str_255 | None] = mapped_column(comment="供应商名称")
    vendor_id: Mapped[str_100 | None] = mapped_column(comment="供应商ID")
    total_amount: Mapped[float | None] = mapped_column(default=0.0, comment="合同总额")
    currency: Mapped[str | None] = mapped_column(default="CNY", comment="币种")
    start_date: Mapped[date | None] = mapped_column(comment="合同开始日期")
    end_date: Mapped[date | None] = mapped_column(comment="合同结束日期")
    cost_code_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_cost_codes.id"), nullable=True, index=True, comment="成本科目ID")
    capex_opex_flag: Mapped[str | None] = mapped_column(comment="CAPEX/OPEX标志")
    cost_code: Mapped[CostCode | None] = relationship("CostCode")


class ContractPaymentNode(Base, TimestampMixin):
    """合同付款节点/收款计划记录表。"""

    __tablename__ = "mdm_contract_payment_nodes"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    contract_id: Mapped[int] = mapped_column(ForeignKey("mdm_revenue_contracts.id"), nullable=False, index=True, comment="关联合同ID")
    node_name: Mapped[str_200] = mapped_column(nullable=False, comment="节点名称")
    billing_percentage: Mapped[float | None] = mapped_column(comment="收款比例 (%)")
    billing_amount: Mapped[float | None] = mapped_column(comment="收款金额")
    linked_system: Mapped[str_50 | None] = mapped_column(comment="关联系统 (gitlab/jira/manual)")
    linked_milestone_id: Mapped[int | None] = mapped_column(comment="关联里程碑ID")
    is_achieved: Mapped[bool | None] = mapped_column(default=False, comment="是否已达成")
    achieved_at: Mapped[datetime | None] = mapped_column(comment="达成时间")
    contract: Mapped[RevenueContract | None] = relationship("RevenueContract", back_populates="payment_nodes")


class Company(Base, TimestampMixin, SCDMixin):
    """公司实体参考表 (Legal Entity)。

    用于定义集团内的法律实体/纳税主体，支持财务核算和合同签署主体的管理。
    """

    __tablename__ = "mdm_companies"
    __table_args__ = (
        Index("uq_mdm_company_code_active", "company_code", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
        Index("uq_mdm_company_tax_id_active", "tax_id", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
    )

    # 基础信息
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    company_code: Mapped[str_50] = mapped_column(index=True, nullable=False, comment="公司唯一业务标识 (如 COM-BJ-01)")
    name: Mapped[str_200] = mapped_column(nullable=False, comment="公司注册全称")
    short_name: Mapped[str_100 | None] = mapped_column(comment="公司简称")
    tax_id: Mapped[str_50 | None] = mapped_column(index=True, comment="统一社会信用代码/税号")

    # 财务与运营
    currency: Mapped[str | None] = mapped_column(default="CNY", comment="本位币种 (CNY/USD)")
    fiscal_year_start: Mapped[str | None] = mapped_column(default="01-01", comment="财年开始日期 (MM-DD)")

    # 地址与关联
    registered_address: Mapped[str_255 | None] = mapped_column(comment="注册地址")
    location_id: Mapped[int | None] = mapped_column(ForeignKey("mdm_locations.id"), nullable=True, index=True, comment="主要办公地点ID")

    # 状态
    is_active: Mapped[bool | None] = mapped_column(default=True, comment="是否存续经营")

    # Relationships
    location: Mapped[Location | None] = relationship("Location")


class Vendor(Base, TimestampMixin, SCDMixin):
    """外部供应商主数据表。"""

    __tablename__ = "mdm_vendors"
    __table_args__ = (
        Index("uq_mdm_vendor_code_active", "vendor_code", unique=True, postgresql_where="is_current IS TRUE", sqlite_where=text("is_current = 1")),
    )

    # 基础信息
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    vendor_code: Mapped[str_50] = mapped_column(index=True, nullable=False, comment="供应商唯一业务编码")
    name: Mapped[str_200] = mapped_column(nullable=False, comment="供应商全称")
    short_name: Mapped[str_100 | None] = mapped_column(comment="供应商简称")

    # 分类与状态
    category: Mapped[str_50 | None] = mapped_column(comment="供应商类别 (人力外包/软件许可/云服务/硬件)")
    status: Mapped[str | None] = mapped_column(default="ACTIVE", comment="合作状态 (ACTIVE/BLACKLIST/INACTIVE)")

    # 商务信息
    tax_id: Mapped[str_50 | None] = mapped_column(comment="统一社会信用代码/税号")
    payment_terms: Mapped[str_100 | None] = mapped_column(comment="默认账期 (e.g. Net 30, Net 60)")
    currency: Mapped[str | None] = mapped_column(default="CNY", comment="默认结算币种")

    # 联系人
    contact_person: Mapped[str_100 | None] = mapped_column(comment="主要联系人")
    contact_email: Mapped[str_100 | None] = mapped_column(comment="联系邮箱")
    contact_phone: Mapped[str_50 | None] = mapped_column(comment="联系电话")

    # 评价
    rating: Mapped[float | None] = mapped_column(default=0.0, comment="供应商绩效评分 (0-5)")

    # 关联
    # 注意：PurchaseContract 和 ResourceCost 已有 vendor_name 等冗余字段，这里建立对象关联以便未来重构
    # contracts = relationship('PurchaseContract', backref='vendor_ref')


class ComplianceIssue(Base, TimestampMixin):
    """合规风险与审计问题记录表。"""

    __tablename__ = "mdm_compliance_issues"
    tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default="default", comment="租户ID")
    id: Mapped[int_pk]
    issue_type: Mapped[str_50 | None] = mapped_column(comment="问题类型 (安全漏洞/许可证违规/合规缺失)")
    severity: Mapped[str | None] = mapped_column(comment="严重等级 (Critical/High/Medium/Low)")
    entity_id: Mapped[str_100 | None] = mapped_column(index=True, comment="关联实体ID (项目/服务)")
    status: Mapped[str | None] = mapped_column(default="OPEN", comment="状态 (OPEN/IN_REVIEW/RESOLVED/ACCEPTED)")
    description: Mapped[str | None] = mapped_column(comment="问题详情")
    metadata_payload: Mapped[json_dict | None] = mapped_column(comment="额外元数据 (JSON)")


class RawDataMixin:
    """原始数据支持混入类。"""

    pass


# --- ALIASES AND DUMMIES TO PREVENT IMPORT ERRORS DURING REFACTORING ---
try:
    from identity_module.models import (
        IdentityDepartment as Organization,
    )
    from identity_module.models import (
        IdentityMapping,
    )
    from identity_module.models import (
        IdentityRole as SysRole,
    )
    from identity_module.models import (
        IdentityUser as User,
    )
except ImportError:
    Organization = type("Organization", (), {})
    IdentityMapping = type("IdentityMapping", (), {})
    SysRole = type("SysRole", (), {})
    User = type("User", (), {})

from typing import Any


Team: Any = type("Team", (), {})
TeamMember: Any = type("TeamMember", (), {})
SysMenu: Any = type("SysMenu", (), {})
SysRoleMenu: Any = type("SysRoleMenu", (), {})
SysRoleDept: Any = type("SysRoleDept", (), {})
UserRole: Any = type("UserRole", (), {})
UserCredential: Any = type("UserCredential", (), {})
UserOAuthToken: Any = type("UserOAuthToken", (), {})


# Monkeypatch is_current for backward compatibility during refactoring
if hasattr(User, "is_active"):
    User.is_current = User.is_active
if hasattr(Organization, "is_active"):
    Organization.is_current = Organization.is_active
