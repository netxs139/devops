"""Traceability Radar API Response Schemas.

定义 /traceability/radar 端点的 Pydantic 契约，
确保前后端字段命名镜像对齐（ARCH-006 合规）。
"""

from pydantic import BaseModel, Field


class RadarMeta(BaseModel):
    """请求元信息"""

    project_id: int | None = None
    days: int
    total_merged_mrs: int


class RadarVSM(BaseModel):
    """价值流分析指标 (Value Stream Mapping)"""

    avg_wait_minutes: float = Field(description="平均等待评审时长（分钟）")
    avg_draft_minutes: float = Field(description="平均草稿阶段时长（分钟）")
    flow_efficiency: float | None = Field(None, description="流动效率 = 触达时间 / 端到端时间，值域 [0,1]")


class RadarCollaboration(BaseModel):
    """协同质量指标"""

    rubber_stamp_rate: float = Field(description="秒批率，值域 [0,1]，越低越好")
    effective_review_rate: float = Field(description="有效评审率，值域 [0,1]，越高越好")
    avg_effective_comments: float = Field(description="平均有效评论数（已过滤机器人/模板评论）")


class RadarSecurity(BaseModel):
    """安全态势指标"""

    critical: int = Field(description="严重漏洞数量")
    high: int = Field(description="高危漏洞数量")
    medium: int = Field(description="中危漏洞数量")
    low: int = Field(description="低危漏洞数量")
    total_active: int = Field(description="活跃漏洞总数（detected + confirmed 状态）")


class VSMTimelineItem(BaseModel):
    """VSM 时间轴单条 MR 记录"""

    id: str = Field(description="MR 编号，如 '!101'")
    title: str = Field(description="MR 标题（截断至 60 字符）")
    draft_minutes: float | None = Field(None, description="草稿阶段时长（分钟）")
    wait_minutes: float | None = Field(None, description="等待评审时长（分钟）")
    review_minutes: float | None = Field(None, description="评审触达时长（分钟）")
    total_minutes: float | None = Field(None, description="端到端总时长（分钟）")
    rubber_stamp: bool = Field(description="是否被识别为秒批")
    effective_comments: int = Field(description="有效评论数量")


class RadarELOC(BaseModel):
    """有效代码行数分布 (Effective Lines of Code)"""

    labels: list[str] = Field(description="贡献者姓名/用户名")
    values: list[int] = Field(description="对应的有效行数得分")


class RadarResponse(BaseModel):
    """Traceability Radar 聚合响应契约（前端数据合同）"""

    meta: RadarMeta
    vsm: RadarVSM
    collaboration: RadarCollaboration
    security: RadarSecurity
    eloc: RadarELOC
    vsm_timeline: list[VSMTimelineItem] = []


class RadarDetailItem(BaseModel):
    """下钻详情单条项目"""

    id: str | int
    title: str
    author: str | None = None
    value: str | float | int | None = None
    url: str | None = None
    timestamp: str | None = None


class RadarDetailResponse(BaseModel):
    """下钻详情聚合响应"""

    type: str
    items: list[RadarDetailItem]
