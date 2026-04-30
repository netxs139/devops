"""GitLab 数据采集插件 (v2.0)

基于声明式协议，由 PluginLoader 2.0 自动加载。
"""

import os

from devops_collector.core.base_plugin import BasePlugin, PluginMetadata


class GitLabPlugin(BasePlugin):
    """GitLab 插件实现类。"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="gitlab",
            version="2.1.0",
            description="Enterprise GitLab Data Collection Plugin",
            data_source_type="git_scm",
            required_config=["url", "token"],
        )

    def get_worker_class(self) -> type:
        # 延迟导入，彻底消除 Side-effect
        from .worker import GitLabWorker

        return GitLabWorker

    def get_client_class(self) -> type:
        # 延迟导入并根据环境选择实现
        if os.getenv("USE_PYAIRBYTE", "false").lower() == "true":
            from .airbyte_client import AirbyteGitLabClient as Client
        else:
            from .gitlab_client import GitLabClient as Client
        return Client


# 实例化插件对象，供 PluginLoader 发现
plugin = GitLabPlugin()

# 为了向下兼容，仍然保留导出（但不再主动调用注册函数）
# [Lazy-Break] Client = plugin.get_client_class()
# [Lazy-Break] GitLabWorker = plugin.get_worker_class()
# [Lazy-Break] get_config = plugin.get_config_getter()

__all__ = ["plugin", "Client", "GitLabWorker", "get_config"]
