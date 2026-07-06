"""BI Metrics Marts Models (Zero-Sync Direct Query).

本模块定义了针对 dbt 数据集市 (`marts`) 层宽表的只读 SQLAlchemy 视图模型。
根据架构规范，此类模型必须配置 `viewonly=True`，严禁写入。
"""

import datetime

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base_models import Base


class DoraDashboardSummary(Base):
    """DORA 核心指标大屏预聚合宽表 (Thin Layer Mapping).

    对应数据库表: rpt_dora_dashboard_summary
    该表已由 dbt 计算好全部指标趋势及前端色值，后端直接原样透传。
    """

    __tablename__ = "rpt_dora_dashboard_summary"

    # 定义主键，因为 SQLAlchemy 需要主键来进行对象映射。这里我们用 product_name 作为逻辑主键
    product_name: Mapped[str] = mapped_column(String, primary_key=True)
    last_updated_month: Mapped[datetime.date] = mapped_column(Date)

    deployment_frequency: Mapped[int] = mapped_column(Integer, nullable=True)
    deploy_trend_icon: Mapped[str] = mapped_column(String, nullable=True)

    mttr_hours: Mapped[float] = mapped_column(Float, nullable=True)
    mttr_trend_icon: Mapped[str] = mapped_column(String, nullable=True)

    lead_time_hours: Mapped[float] = mapped_column(Float, nullable=True)
    lead_time_trend_icon: Mapped[str] = mapped_column(String, nullable=True)

    change_failure_rate_pct: Mapped[float] = mapped_column(Float, nullable=True)
    cfr_trend_icon: Mapped[str] = mapped_column(String, nullable=True)

    avg_lines_per_commit: Mapped[float] = mapped_column(Float, nullable=True)
    alpc_trend_icon: Mapped[str] = mapped_column(String, nullable=True)

    mr_commit_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    mcr_trend_icon: Mapped[str] = mapped_column(String, nullable=True)

    performance_rating: Mapped[str] = mapped_column(String, nullable=True)
    health_color_hex: Mapped[str] = mapped_column(String, nullable=True)


class DeveloperActivityProfile(Base):
    """开发者活动画像预聚合宽表.

    对应数据库表: fct_developer_activity_profile
    """

    __tablename__ = "fct_developer_activity_profile"

    # dbt 生成的表名可能包含 developer_id
    developer_name: Mapped[str] = mapped_column(String, primary_key=True)
    total_impact_score: Mapped[float] = mapped_column(Float, nullable=True)
    daily_velocity: Mapped[float] = mapped_column(Float, nullable=True)
    active_days_count: Mapped[int] = mapped_column(Integer, nullable=True)
    developer_archetype: Mapped[str] = mapped_column(String, nullable=True)
    total_commits: Mapped[int] = mapped_column(Integer, nullable=True)
    total_reviews: Mapped[int] = mapped_column(Integer, nullable=True)
