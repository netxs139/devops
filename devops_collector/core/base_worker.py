"""兼容性桥接模块：devops_collector.core.base_worker

历史测试与代码通过此路径导入/Mock，实际实现已转移至
devops_collector.services.base_worker。
"""

from devops_collector.services.base_worker import BaseWorker


__all__ = ["BaseWorker"]
