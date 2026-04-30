"""JFrog 采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

from devops_collector.core.base_plugin import BasePlugin, PluginMetadata


class JFrogPlugin(BasePlugin):
    """JFrog 插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="jfrog",
            version="1.0.0",
            description="JFrog Artifactory Data Plugin",
            data_source_type="artifact_repository",
            required_config=["url", "user", "password"],
        )

    def get_worker_class(self) -> type:
        from .worker import JFrogWorker

        return JFrogWorker

    def get_client_class(self) -> type:
        from .client import JFrogClient

        return JFrogClient


# 实例化插件
plugin = JFrogPlugin()

# 向下兼容导出
Client = plugin.get_client_class()
JFrogWorker = plugin.get_worker_class()
get_config = plugin.get_config_getter()

__all__ = ["plugin", "Client", "JFrogWorker", "get_config"]
