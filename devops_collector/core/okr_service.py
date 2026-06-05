"""兼容性桥接模块：devops_collector.core.okr_service

历史测试通过此路径导入，实际实现位于
devops_collector.services.okr_service。
"""

from devops_collector.services.okr_service import OKRService


__all__ = ["OKRService"]
