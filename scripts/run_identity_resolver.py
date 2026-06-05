"""兼容性桥接：scripts.run_identity_resolver

测试通过 `from scripts.run_identity_resolver import IdentityResolver` 导入，
实际实现已按 Service/Command Separation 原则迁移至服务层。
"""

from devops_collector.services.identity_resolver import IdentityResolver


__all__ = ["IdentityResolver"]
