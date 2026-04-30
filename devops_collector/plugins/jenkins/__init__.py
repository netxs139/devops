"""Jenkins 采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

import os

from devops_collector.core.base_plugin import BasePlugin, PluginMetadata


class JenkinsPlugin(BasePlugin):
    """Jenkins 插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="jenkins",
            version="1.1.5",
            description="CI/CD Pipeline Data Plugin",
            data_source_type="ci_cd",
            required_config=["url", "user", "token"],
        )

    def get_worker_class(self) -> type:
        from .worker import JenkinsWorker

        return JenkinsWorker

    def get_client_class(self) -> type:
        if os.getenv("USE_PYAIRBYTE", "false").lower() == "true":
            from .airbyte_client import AirbyteJenkinsClient as Client
        else:
            from .client import JenkinsClient as Client
        return Client


# 实例化插件
plugin = JenkinsPlugin()

# 向下兼容导出
# [Lazy-Break] Client = plugin.get_client_class()
# [Lazy-Break] JenkinsWorker = plugin.get_worker_class()
# [Lazy-Break] get_config = plugin.get_config_getter()

__all__ = ["plugin", "Client", "JenkinsWorker", "get_config"]
