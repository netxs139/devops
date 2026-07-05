"""Jenkins 插件配置模块

从环境变量中读取 Jenkins 相关配置。
"""

from typing import Any


def get_config() -> dict[str, Any]:
    """获取 Jenkins 插件的配置。

    Returns:
        包含 client 和 worker 配置的字典:
        {
            'client': {
                'url': str,
                'token': str,
                'user': str
            },
            'worker': {
                'build_limit': int
            }
        }
    """
    from devops_collector.config import settings

    return {
        "client": {"url": settings.jenkins.url, "token": settings.jenkins.token.get_secret_value(), "user": settings.jenkins.user},
        "worker": {"build_limit": settings.jenkins.build_sync_limit},
    }
