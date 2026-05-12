"""企业微信 (WeCom) 采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

from devops_collector.services.base_plugin import BasePlugin, PluginMetadata


class WeComPlugin(BasePlugin):
    """企业微信插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="wecom",
            version="1.5.0",
            description="Enterprise WeChat Directory Data Plugin",
            data_source_type="messenger_org",
            required_config=["corp_id", "secret"],
        )

    def get_worker_class(self) -> type:
        from .worker import WeComWorker

        return WeComWorker

    def get_client_class(self) -> type:
        from .client import WeComClient

        return WeComClient


# 实例化插件
plugin = WeComPlugin()

# 向下兼容导出
# [Lazy-Break] Client = plugin.get_client_class()
# [Lazy-Break] WeComWorker = plugin.get_worker_class()
# [Lazy-Break] get_config = plugin.get_config_getter()

__all__ = ["plugin", "Client", "WeComWorker", "get_config"]
