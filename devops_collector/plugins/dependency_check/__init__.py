"""Dependency Check 采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

from devops_collector.services.base_plugin import BasePlugin, PluginMetadata


class DependencyCheckPlugin(BasePlugin):
    """Dependency Check 插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dependency_check",
            version="1.0.0",
            description="OWASP Dependency-Check Vulnerability Data Plugin",
            data_source_type="security_scan",
            required_config=[],
        )

    def get_worker_class(self) -> type:
        from .worker import DependencyCheckWorker

        return DependencyCheckWorker

    def get_client_class(self) -> type | None:
        # 该插件仅接收推送报告，无需客户端
        return None


# 实例化插件
plugin = DependencyCheckPlugin()

# 向下兼容导出
# [Lazy-Break] DependencyCheckWorker = plugin.get_worker_class()
# [Lazy-Break] get_config = plugin.get_config_getter()

__all__ = ["plugin", "DependencyCheckWorker", "get_config"]
