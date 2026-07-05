"""SonarQube 插件配置模块

从环境变量中读取 SonarQube 相关配置。
"""

from typing import Any


def get_config() -> dict[str, Any]:
    """获取 SonarQube 插件的配置。

    Returns:
        包含 client 和 worker 配置的字典:
        {
            'client': {
                'url': str,
                'token': str,
                'rate_limit': int
            },
            'worker': {
                'sync_issues': bool
            }
        }
    """
    from devops_collector.config import settings

    return {
        "client": {
            "url": settings.sonarqube.url,
            "token": settings.sonarqube.token.get_secret_value(),
            "rate_limit": settings.ratelimit.requests_per_second,
        },
        "worker": {"sync_issues": settings.sonarqube.sync_issues},
    }
