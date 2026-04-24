import pytest

from devops_collector.core.registry import PluginRegistry


class MockClient:
    pass


class AnotherClient:
    pass


class MockWorker:
    pass


def mock_config():
    return {"key": "val"}


def test_plugin_registry_flow():
    PluginRegistry.clear()

    # 1. Register
    PluginRegistry.register_client("test", MockClient)
    PluginRegistry.register_worker("test", MockWorker)
    PluginRegistry.register_config("test", mock_config)

    # 2. Retrieve
    assert PluginRegistry.get_client("test") is MockClient
    assert PluginRegistry.get_worker("test") is MockWorker
    assert PluginRegistry.get_config("test") == {"key": "val"}

    # 3. List
    plugins = PluginRegistry.list_plugins()
    assert "test" in plugins
    assert plugins["test"]["client"] == "MockClient"

    assert "test" in PluginRegistry.list_sources()


def test_registry_conflict():
    PluginRegistry.clear()
    PluginRegistry.register_client("test", MockClient)

    # Registering same class again is fine
    PluginRegistry.register_client("test", MockClient)

    # Registering DIFFERENT class should raise ValueError
    with pytest.raises(ValueError, match="Client conflict"):
        PluginRegistry.register_client("test", AnotherClient)

    # Worker conflict
    PluginRegistry.register_worker("test", MockWorker)
    with pytest.raises(ValueError, match="Worker conflict"):
        PluginRegistry.register_worker("test", MockClient)

    # Config conflict
    PluginRegistry.register_config("test", mock_config)
    with pytest.raises(ValueError, match="Config conflict"):
        PluginRegistry.register_config("test", lambda: {})


def test_registry_not_found():
    PluginRegistry.clear()
    assert PluginRegistry.get_client("nonexistent") is None
    assert PluginRegistry.get_worker("nonexistent") is None
    assert PluginRegistry.get_config("nonexistent") is None
    assert PluginRegistry.get_worker_instance("nonexistent", None, None) is None


def test_get_config_exception():
    PluginRegistry.clear()

    def broken_config():
        raise RuntimeError("Config failure")

    PluginRegistry.register_config("broken", broken_config)
    assert PluginRegistry.get_config("broken") is None


def test_registry_instance_creation():
    PluginRegistry.clear()

    class ParamClient:
        def __init__(self, url):
            self.url = url

    PluginRegistry.register_client("param", ParamClient)

    client = PluginRegistry.get_client_instance("param", url="http://test.com")
    assert isinstance(client, ParamClient)
    assert client.url == "http://test.com"

    assert PluginRegistry.get_client_instance("nonexistent") is None
