"""Traceability Radar API Router.

提供价值流分析、协同质量与安全态势的聚合数据端点，
供 Traceability Radar 前端仪表盘消费。
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from devops_collector.auth.auth_database import get_auth_db
from devops_collector.plugins.gitlab.models import (
    GitLabCommit,
    GitLabMergeRequest,
    GitLabVulnerability,
)
from devops_portal.schemas_traceability import RadarDetailResponse, RadarResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traceability", tags=["Traceability Radar"])


@router.get("/detail", response_model=RadarDetailResponse)
async def get_radar_detail(
    metric_type: str = Query(..., description="下钻类型: RUBBER_STAMP, VSM_WAITING, HIGH_ELOC, VULNERABILITY"),
    project_id: int | None = Query(None),
    days: int = Query(30, ge=7, le=365),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_auth_db),
):
    """获取指定维度的详情列表。"""
    from datetime import UTC, datetime, timedelta

    since = datetime.now(UTC) - timedelta(days=days)
    items = []

    if metric_type == "RUBBER_STAMP":
        mr_q = db.query(GitLabMergeRequest).filter(GitLabMergeRequest.merged_at >= since, GitLabMergeRequest.rubber_stamp.is_(True))
        if project_id:
            mr_q = mr_q.filter(GitLabMergeRequest.project_id == project_id)
        mr_results = mr_q.order_by(GitLabMergeRequest.merged_at.desc()).limit(limit).all()
        for m in mr_results:
            items.append(
                {
                    "id": f"!{m.iid}",
                    "title": m.title,
                    "author": m.author_username,
                    "value": f"{round(m.review_touch_time / 60, 1) if m.review_touch_time else 0} min",
                    "url": m.web_url,
                    "timestamp": m.merged_at.isoformat() if m.merged_at else None,
                }
            )

    elif metric_type == "VSM_WAITING":
        wait_q = db.query(GitLabMergeRequest).filter(
            GitLabMergeRequest.merged_at >= since,
            GitLabMergeRequest.wait_time_to_review > 3600,  # 1h 以上视为严重等待
        )
        if project_id:
            wait_q = wait_q.filter(GitLabMergeRequest.project_id == project_id)
        wait_results = wait_q.order_by(GitLabMergeRequest.wait_time_to_review.desc()).limit(limit).all()
        for m in wait_results:
            wait_val = round(m.wait_time_to_review / 3600, 1) if m.wait_time_to_review else 0
            items.append(
                {
                    "id": f"!{m.iid}",
                    "title": m.title,
                    "author": m.author_username,
                    "value": f"{wait_val} h",
                    "url": m.web_url,
                    "timestamp": m.merged_at.isoformat() if m.merged_at else None,
                }
            )

    elif metric_type == "HIGH_ELOC":
        commit_q = db.query(GitLabCommit).filter(GitLabCommit.committed_date >= since)
        if project_id:
            commit_q = commit_q.filter(GitLabCommit.project_id == project_id)
        commit_results = commit_q.order_by(GitLabCommit.eloc_score.desc()).limit(limit).all()
        for c in commit_results:
            items.append(
                {
                    "id": c.short_id,
                    "title": (c.title or "")[:60],
                    "author": c.author_name,
                    "value": int(c.eloc_score or 0),
                    "url": c.web_url,
                    "timestamp": c.committed_date.isoformat() if c.committed_date else None,
                }
            )

    elif metric_type == "VULNERABILITY":
        vuln_q = db.query(GitLabVulnerability).filter(GitLabVulnerability.state.in_(["detected", "confirmed"]))
        if project_id:
            vuln_q = vuln_q.filter(GitLabVulnerability.project_id == project_id)
        vuln_results = vuln_q.order_by(GitLabVulnerability.severity.desc()).limit(limit).all()
        for v in vuln_results:
            items.append(
                {
                    "id": str(v.id),
                    "title": (v.name or "")[:80],
                    "author": v.severity,  # 借用 author 字段存级别
                    "value": v.state,
                    "url": v.web_url,
                    "timestamp": v.created_at.isoformat() if v.created_at else None,
                }
            )

    return {"type": metric_type, "items": items}


@router.get("/radar", response_model=RadarResponse)
async def get_radar_metrics(
    project_id: int | None = Query(None, description="过滤指定项目，不传则返回全局聚合"),
    days: int = Query(30, ge=7, le=365, description="统计时间窗口（天）"),
    db: Session = Depends(get_auth_db),
):
    """获取 Traceability Radar 所需的聚合指标数据。

    数据来源:
    - VSM 指标: GitLabMergeRequest.wait_time_to_review / draft_duration
    - 协同质量: effective_comment_count / rubber_stamp
    - 安全态势: GitLabVulnerability severity 分布

    Returns:
        dict: 包含 vsm / collaboration / security / vsm_timeline 的聚合数据。
    """
    from datetime import UTC, datetime, timedelta

    since = datetime.now(UTC) - timedelta(days=days)

    # --- MR 查询基座 ---
    mr_q = db.query(GitLabMergeRequest).filter(
        GitLabMergeRequest.merged_at >= since,
        GitLabMergeRequest.state == "merged",
    )
    if project_id:
        mr_q = mr_q.filter(GitLabMergeRequest.project_id == project_id)

    merged_mrs = mr_q.all()
    total_mrs = len(merged_mrs)

    # --- VSM 聚合 ---
    wait_times = [m.wait_time_to_review for m in merged_mrs if m.wait_time_to_review]
    draft_durations = [m.draft_duration for m in merged_mrs if m.draft_duration]

    avg_wait_minutes = round(sum(wait_times) / len(wait_times) / 60, 1) if wait_times else 0.0
    avg_draft_minutes = round(sum(draft_durations) / len(draft_durations) / 60, 1) if draft_durations else 0.0

    # 流动效率 = 实际处理时间 / 总端到端时间（粗算）
    flow_efficiency = None
    if merged_mrs:
        touch_times = [m.review_touch_time for m in merged_mrs if m.review_touch_time]
        total_times = [(m.merged_at - m.created_at).total_seconds() for m in merged_mrs if m.merged_at and m.created_at]
        if touch_times and total_times:
            avg_touch = sum(touch_times) / len(touch_times)
            avg_total = sum(total_times) / len(total_times)
            flow_efficiency = round(avg_touch / avg_total, 3) if avg_total > 0 else None

    # --- 协同质量 ---
    rubber_stamp_count = sum(1 for m in merged_mrs if m.rubber_stamp)
    rubber_stamp_rate = round(rubber_stamp_count / total_mrs, 3) if total_mrs else 0.0

    eff_comments = [m.effective_comment_count for m in merged_mrs if m.effective_comment_count is not None]
    avg_eff_comments = round(sum(eff_comments) / len(eff_comments), 1) if eff_comments else 0.0

    # 有效评审率：有 effective_comment_count > 0 的 MR 比例
    effective_review_count = sum(1 for m in merged_mrs if (m.effective_comment_count or 0) > 0)
    effective_review_rate = round(effective_review_count / total_mrs, 3) if total_mrs else 0.0

    # --- 安全态势（不限时间窗口，取 active 漏洞）---
    vuln_q = db.query(
        GitLabVulnerability.severity,
        func.count(GitLabVulnerability.id).label("cnt"),
    ).filter(GitLabVulnerability.state.in_(["detected", "confirmed"]))
    if project_id:
        vuln_q = vuln_q.filter(GitLabVulnerability.project_id == project_id)

    vuln_rows = vuln_q.group_by(GitLabVulnerability.severity).all()
    severity_map = {row.severity: row.cnt for row in vuln_rows}

    # --- ELOC 分布 (Effective Lines of Code) ---
    eloc_q = db.query(GitLabCommit.author_name, func.sum(GitLabCommit.eloc_score).label("total_eloc")).filter(GitLabCommit.committed_date >= since)
    if project_id:
        eloc_q = eloc_q.filter(GitLabCommit.project_id == project_id)

    eloc_rows = eloc_q.group_by(GitLabCommit.author_name).order_by(func.sum(GitLabCommit.eloc_score).desc()).limit(10).all()
    eloc_labels = [row.author_name or "Unknown" for row in eloc_rows]
    eloc_values = [int(row.total_eloc or 0) for row in eloc_rows]

    # --- VSM Timeline (最近 10 条已合并 MR) ---
    timeline_mrs = mr_q.order_by(GitLabMergeRequest.merged_at.desc()).limit(10).all()

    def _seconds_to_minutes(s) -> float | None:
        return round(s / 60, 1) if s else None

    vsm_timeline = [
        {
            "id": f"!{m.iid}",
            "title": (m.title or "")[:60],
            "draft_minutes": _seconds_to_minutes(m.draft_duration),
            "wait_minutes": _seconds_to_minutes(m.wait_time_to_review),
            "review_minutes": _seconds_to_minutes(m.review_touch_time),
            "total_minutes": _seconds_to_minutes((m.merged_at - m.created_at).total_seconds() if m.merged_at and m.created_at else None),
            "rubber_stamp": m.rubber_stamp or False,
            "effective_comments": m.effective_comment_count or 0,
        }
        for m in timeline_mrs
    ]

    return {
        "meta": {
            "project_id": project_id,
            "days": days,
            "total_merged_mrs": total_mrs,
        },
        "vsm": {
            "avg_wait_minutes": avg_wait_minutes,
            "avg_draft_minutes": avg_draft_minutes,
            "flow_efficiency": flow_efficiency,
        },
        "collaboration": {
            "rubber_stamp_rate": rubber_stamp_rate,
            "effective_review_rate": effective_review_rate,
            "avg_effective_comments": avg_eff_comments,
        },
        "security": {
            "critical": severity_map.get("Critical", 0),
            "high": severity_map.get("High", 0),
            "medium": severity_map.get("Medium", 0),
            "low": severity_map.get("Low", 0),
            "total_active": sum(severity_map.values()),
        },
        "eloc": {
            "labels": eloc_labels,
            "values": eloc_values,
        },
        "vsm_timeline": vsm_timeline,
    }
