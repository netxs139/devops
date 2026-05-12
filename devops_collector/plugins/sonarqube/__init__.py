"""SonarQube 采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

import os

from devops_collector.services.base_plugin import BasePlugin, PluginMetadata


class SonarQubePlugin(BasePlugin):
    """SonarQube 插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="sonarqube",
            version="1.2.0",
            description="Static Code Analysis Data Plugin",
            data_source_type="code_quality",
            required_config=["url", "token"],
        )

    def get_worker_class(self) -> type:
        from .worker import SonarQubeWorker

        return SonarQubeWorker

    def get_client_class(self) -> type:
        from .client import SonarQubeClient

        return SonarQubeClient


# 实例化插件
plugin = SonarQubePlugin()

# 向下兼容导出
# [Lazy-Break] Client = plugin.get_client_class()
# [Lazy-Break] SonarQubeWorker = plugin.get_worker_class()
# [Lazy-Break] get_config = plugin.get_config_getter()

__all__ = ["plugin", "Client", "SonarQubeWorker", "get_config"]
