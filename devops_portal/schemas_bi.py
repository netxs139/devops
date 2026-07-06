"""BI Metrics Pydantic Schemas.

用于序列化 dbt marts 层宽表，直接暴露给前端大屏。
"""

import datetime

from pydantic import BaseModel, ConfigDict


class DoraDashboardSummarySchema(BaseModel):
    """DORA 核心指标序列化 Schema."""

    product_name: str
    last_updated_month: datetime.date

    deployment_frequency: int | None = None
    deploy_trend_icon: str | None = None

    mttr_hours: float | None = None
    mttr_trend_icon: str | None = None

    lead_time_hours: float | None = None
    lead_time_trend_icon: str | None = None

    change_failure_rate_pct: float | None = None
    cfr_trend_icon: str | None = None

    avg_lines_per_commit: float | None = None
    alpc_trend_icon: str | None = None

    mr_commit_ratio: float | None = None
    mcr_trend_icon: str | None = None

    performance_rating: str | None = None
    health_color_hex: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DeveloperActivityProfileSchema(BaseModel):
    """开发者活动画像序列化 Schema."""

    developer_name: str
    total_impact_score: float | None = None
    daily_velocity: float | None = None
    active_days_count: int | None = None
    developer_archetype: str | None = None
    total_commits: int | None = None
    total_reviews: int | None = None

    model_config = ConfigDict(from_attributes=True)
