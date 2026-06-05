"""兼容性桥接模块：devops_collector.core.reverse_etl

历史测试与代码通过此路径导入/Mock，实际实现已转移至
devops_collector.services.reverse_etl。
"""

from devops_collector.services.reverse_etl import (
    sync_aligned_entities_to_mdm,
    sync_shadow_it_findings,
    sync_talent_tags_to_mdm,
)


__all__ = [
    "sync_talent_tags_to_mdm",
    "sync_aligned_entities_to_mdm",
    "sync_shadow_it_findings",
]
