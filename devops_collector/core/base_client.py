"""兼容性桥接模块：devops_collector.core.base_client

历史测试与代码通过此路径导入，实际实现位于
devops_collector.services.base_client。
"""

from devops_collector.services.base_client import BaseClient, RateLimiter, is_retryable_exception


__all__ = ["BaseClient", "RateLimiter", "is_retryable_exception"]
