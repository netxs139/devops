"""兼容性桥接模块：devops_collector.core.business_auth

历史测试与代码通过此路径导入，实际实现已转移至
devops_collector.services.business_auth。
"""

from devops_collector.services.business_auth import get_business_linked_roles, get_dynamic_permissions


__all__ = ["get_business_linked_roles", "get_dynamic_permissions"]
