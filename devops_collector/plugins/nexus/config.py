"""Nexus 插件配置模块

从环境变量中读取 Nexus 相关配置。
"""

from typing import Any

from devops_collector.config import settings


def get_config() -> dict[str, Any]:
    """获取 Nexus 插件的配置。

    Returns:
        包含 client 和 worker 配置的字典
    """
    return {
        "client": {
            "url": settings.nexus.url,
            "user": settings.nexus.user,
            "password": settings.nexus.password,
            "rate_limit": settings.ratelimit.requests_per_second,
        },
        "worker": {},
    }
