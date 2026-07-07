"""BI Metrics API Router.

提供专门服务于前端大屏的只读接口。
包含内存级微型屏障 (Micro Memory Barrier) 防止高并发穿透数据库。
"""

import time
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from devops_collector.models.marts import DeveloperActivityProfile, DoraDashboardSummary
from devops_portal.dependencies import get_db
from devops_portal.schemas_bi import DeveloperActivityProfileSchema, DoraDashboardSummarySchema


router = APIRouter(prefix="/bi/metrics", tags=["BI Metrics"])


# ==============================================================================
# Micro Memory Barrier (极简 TTL 内存防雪崩)
# ==============================================================================
class TTLCache:
    """微型内存短路缓存."""

    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> Any:
        """获取缓存数据."""
        entry = self._cache.get(key)
        if entry and (time.time() - entry["timestamp"] < self.ttl):
            return entry["data"]
        return None

    def set(self, key: str, data: Any):
        """设置缓存数据."""
        self._cache[key] = {"timestamp": time.time(), "data": data}


_bi_cache = TTLCache(ttl_seconds=60)


@router.get("/dora/summary", response_model=list[DoraDashboardSummarySchema])
async def get_dora_summary(db: AsyncSession = Depends(get_db)):
    """获取 DORA 核心指标大屏预聚合宽表数据.

    由于该接口为前端轮询调用，启用 60 秒内存短路缓存以防雪崩。
    """
    cache_key = "dora_summary"
    cached_data = _bi_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Zero-Sync Direct Query: 直接查 marts 表
    stmt = select(DoraDashboardSummary)
    result = await db.execute(stmt)
    records = result.scalars().all()

    _bi_cache.set(cache_key, records)
    return records


@router.get("/developer/activity", response_model=list[DeveloperActivityProfileSchema])
async def get_developer_activity(db: AsyncSession = Depends(get_db)):
    """获取开发者活动画像数据.

    同样启用 60 秒内存短路缓存以防雪崩。
    """
    cache_key = "developer_activity"
    cached_data = _bi_cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    stmt = select(DeveloperActivityProfile)
    result = await db.execute(stmt)
    records = result.scalars().all()

    _bi_cache.set(cache_key, records)
    return records


@router.get("/lineage")
async def get_dbt_lineage():
    """获取自研数据血缘图 (Mermaid 格式)."""
    from devops_collector.services.lineage_service import LineageService

    mermaid_text = LineageService.generate_mermaid_lineage()
    return {"lineage": mermaid_text}
