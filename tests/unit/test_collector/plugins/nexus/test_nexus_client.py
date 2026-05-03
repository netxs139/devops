"""Nexus Client 单元测试"""

import unittest
from unittest.mock import MagicMock, patch

from devops_collector.plugins.nexus.client import NexusClient


class TestNexusClient(unittest.TestCase):
    def setUp(self):
        self.url = "http://nexus.example.com"
        self.user = "admin"
        self.password = "password"
        self.client = NexusClient(self.url, self.user, self.password)

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_test_connection_success(self, mock_get):
        """测试连接成功。"""
        mock_get.return_value = MagicMock()
        self.assertTrue(self.client.test_connection())
        mock_get.assert_called_with("status/check")

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_test_connection_failure(self, mock_get):
        """测试连接失败。"""
        mock_get.side_effect = Exception("Connection error")
        self.assertFalse(self.client.test_connection())

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_list_repositories(self, mock_get):
        """测试获取仓库列表。"""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"name": "maven-releases"}]
        mock_get.return_value = mock_response

        repos = self.client.list_repositories()
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "maven-releases")

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_list_components_paging(self, mock_get):
        """测试组件分页获取。"""
        # 1. 模拟第一页
        page1 = MagicMock()
        page1.json.return_value = {"items": [{"id": "c1"}], "continuationToken": "token2"}
        # 2. 模拟第二页
        page2 = MagicMock()
        page2.json.return_value = {"items": [{"id": "c2"}], "continuationToken": None}
        mock_get.side_effect = [page1, page2]

        components = list(self.client.list_components("maven-public"))
        self.assertEqual(len(components), 2)
        self.assertEqual(components[0]["id"], "c1")
        self.assertEqual(components[1]["id"], "c2")
        self.assertEqual(mock_get.call_count, 2)

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_component(self, mock_get):
        """测试获取组件详情。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "comp-id", "name": "comp-name"}
        mock_get.return_value = mock_response

        comp = self.client.get_component("comp-id")
        self.assertEqual(comp["name"], "comp-name")

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_list_assets_paging(self, mock_get):
        """测试资产分页获取。"""
        page1 = MagicMock()
        page1.json.return_value = {"items": [{"id": "a1"}], "continuationToken": "token2"}
        page2 = MagicMock()
        page2.json.return_value = {"items": [{"id": "a2"}], "continuationToken": None}
        mock_get.side_effect = [page1, page2]

        assets = list(self.client.list_assets("repo1"))
        self.assertEqual(len(assets), 2)
        self.assertEqual(mock_get.call_count, 2)

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_download_asset_content(self, mock_get):
        """测试资产内容下载。"""
        mock_response = MagicMock()
        mock_response.text = "content body"
        mock_get.return_value = mock_response

        content = self.client.download_asset_content("http://download-url")
        self.assertEqual(content, "content body")
