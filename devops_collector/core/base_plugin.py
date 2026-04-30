"""插件基类与元数据定义
2.0 优化版：实现声明式插件定义与生命周期管理
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginMetadata:
    """插件元数据。"""

    name: str
    version: str
    description: str = ""
    data_source_type: str = "unknown"
    required_config: list[str] = field(default_factory=list)
    author: str = "Antigravity"


class BasePlugin(ABC):
    """插件抽象基类。

    所有插件必须继承此类并实现其抽象方法。
    插件通过暴露一个 `plugin` 实例来与加载器交互。
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """返回插件元数据。"""
        pass

    @abstractmethod
    def get_worker_class(self) -> type:
        """动态获取 Worker 类（实现延迟导入）。"""
        pass

    @abstractmethod
    def get_client_class(self) -> type:
        """动态获取 Client 类（实现延迟导入）。"""
        pass

    def get_config_getter(self) -> Any:
        """返回插件配置获取函数。"""
        # 默认实现：寻找同目录下的 config.get_config
        import importlib

        module_path = f"devops_collector.plugins.{self.metadata.name}.config"
        try:
            config_module = importlib.import_module(module_path)
            return config_module.get_config
        except (ImportError, AttributeError):
            return None

    async def health_check(self, config: dict[str, Any]) -> bool:
        """插件健康检查（可选实现）。"""
        return True

    def on_setup(self) -> None:  # noqa: B027
        """插件初始化钩子（可选）。"""
        pass

    def on_teardown(self) -> None:  # noqa: B027
        """插件销毁钩子（可选）。"""
        pass
