"""Jira 采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

import os

from devops_collector.core.base_plugin import BasePlugin, PluginMetadata


class JiraPlugin(BasePlugin):
    """Jira 插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="jira",
            version="1.0.0",
            description="Jira Agile Project Management Data Plugin",
            data_source_type="project_management",
            required_config=["url", "token"],
        )

    def get_worker_class(self) -> type:
        from .worker import JiraWorker

        return JiraWorker

    def get_client_class(self) -> type:
        if os.getenv("USE_PYAIRBYTE", "false").lower() == "true":
            from .airbyte_client import AirbyteJiraClient as Client
        else:
            from .client import JiraClient as Client
        return Client


# 实例化插件
plugin = JiraPlugin()

# 向下兼容导出
Client = plugin.get_client_class()
JiraWorker = plugin.get_worker_class()
get_config = plugin.get_config_getter()

__all__ = ["plugin", "Client", "JiraWorker", "get_config"]
