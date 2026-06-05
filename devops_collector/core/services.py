"""兼容性桥接模块：devops_collector.core.services

历史测试通过此路径导入 SCD Type-2 辅助函数与并发错误类，
实际实现位于 devops_collector.services.base。
"""

from devops_collector.services.base import ConcurrencyError, close_current_and_insert_new


__all__ = ["ConcurrencyError", "close_current_and_insert_new"]
