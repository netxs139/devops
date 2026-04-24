from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devops_collector.core.plugin_loader import PluginLoader


@pytest.fixture
def clean_loader():
    PluginLoader.clear()
    yield PluginLoader
    PluginLoader.clear()


def test_autodiscover_basic(clean_loader):
    # Mock settings.plugin.enabled_plugins
    with patch("devops_collector.config.settings") as mock_settings:
        mock_settings.plugin.enabled_plugins = ["mock_p1"]

        # Mock Path class in the module
        with patch("devops_collector.core.plugin_loader.Path") as MockPath:
            plugins_dir = MockPath.return_value
            plugins_dir.exists.return_value = True

            p1 = MagicMock()
            p1.name = "mock_p1"
            p1.is_dir.return_value = True
            (p1 / "__init__.py").exists.return_value = True

            plugins_dir.iterdir.return_value = [p1]

            with patch("importlib.import_module") as mock_import:
                loaded = clean_loader.autodiscover(plugins_dir="/fake/plugins")

                assert "mock_p1" in loaded
                assert clean_loader.is_plugin_loaded("mock_p1")
                mock_import.assert_called_with("devops_collector.plugins.mock_p1")


def test_autodiscover_skip_not_enabled(clean_loader):
    with patch("devops_collector.config.settings") as mock_settings:
        mock_settings.plugin.enabled_plugins = []  # None enabled

        with patch("pathlib.Path.iterdir") as mock_iterdir:
            p1 = MagicMock(spec=Path)
            p1.name = "mock_p2"
            p1.is_dir.return_value = True
            (p1 / "__init__.py").exists.return_value = True
            mock_iterdir.return_value = [p1]

            loaded = clean_loader.autodiscover(plugins_dir="/fake/plugins")
            assert len(loaded) == 0


def test_load_models(clean_loader):
    clean_loader._loaded_plugins = ["mock_p1"]

    with patch("importlib.import_module") as mock_import:
        with patch("sys.modules", {}):  # Simulate not loaded
            clean_loader.load_models()
            mock_import.assert_called_with("devops_collector.plugins.mock_p1.models")


def test_reload_plugin(clean_loader):
    with patch("importlib.reload") as mock_reload:
        with patch("sys.modules", {"devops_collector.plugins.mock_p1": MagicMock()}):
            assert clean_loader.reload_plugin("mock_p1") is True
            mock_reload.assert_called()
