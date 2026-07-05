"""GitLab 插件配置模块

从环境变量中读取 GitLab 相关配置。
"""

from typing import Any


def get_config() -> dict[str, Any]:
    """获取 GitLab 插件的配置。

    Returns:
        包含 client 和 worker 配置的字典:
        {
            'client': {
                'url': str,
                'token': str,
                'rate_limit': int
            },
            'worker': {
                'enable_deep_analysis': bool
            }
        }
    """
    from devops_collector.config import settings

    return {
        "client": {
            "url": settings.gitlab.url,
            "token": settings.gitlab.private_token.get_secret_value(),
            "rate_limit": settings.ratelimit.requests_per_second,
            "verify_ssl": settings.gitlab.verify_ssl,
        },
        "worker": {"enable_deep_analysis": settings.analysis.enable_deep_analysis},
    }
