"""PMS 采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

from devops_collector.services.base_plugin import BasePlugin, PluginMetadata


class PMSPlugin(BasePlugin):
    """PMS 插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="pms",
            version="1.0.0",
            description="Project Management System Data Plugin",
            data_source_type="project_master",
            required_config=["url", "token"],
        )

    def get_worker_class(self) -> type:
        """Get worker class."""
        from .worker import PMSWorker

        return PMSWorker

    def get_client_class(self) -> type:
        """Get client class."""
        from .client import PMSClient

        return PMSClient


plugin = PMSPlugin()

__all__ = ["plugin"]
