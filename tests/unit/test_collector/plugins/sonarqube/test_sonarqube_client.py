"""SonarQube Client 单元测试"""

import unittest
from unittest.mock import MagicMock, patch

from devops_collector.plugins.sonarqube.client import SonarQubeClient


class TestSonarQubeClient(unittest.TestCase):
    def setUp(self):
        self.url = "http://sonarqube.example.com"
        self.token = "squ_test_token"
        self.client = SonarQubeClient(self.url, self.token)

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_test_connection_success(self, mock_get):
        """测试连接成功。"""
        # 注意：test_connection 直接调用 self._session.get 而非 self._get
        with patch.object(self.client._session, "get") as mock_session_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "UP"}
            mock_session_get.return_value = mock_response

            self.assertTrue(self.client.test_connection())

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_projects_paging(self, mock_get):
        """测试获取项目列表分页。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"components": [{"key": "p1", "name": "Project 1"}]}
        mock_get.return_value = mock_response

        projects = self.client.get_projects(page=1)
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["key"], "p1")
        mock_get.assert_called_with("projects/search", params={"p": 1, "ps": 100})

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_measures(self, mock_get):
        """测试获取指标。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"component": {"measures": [{"metric": "coverage", "value": "85.5"}, {"metric": "bugs", "value": "10"}]}}
        mock_get.return_value = mock_response

        measures = self.client.get_measures("p1")
        self.assertEqual(measures["coverage"], "85.5")
        self.assertEqual(measures["bugs"], "10")

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_issue_severity_distribution(self, mock_get):
        """测试获取问题严重程度分布。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"facets": [{"property": "severities", "values": [{"val": "BLOCKER", "count": 2}, {"val": "CRITICAL", "count": 5}]}]}
        mock_get.return_value = mock_response

        dist = self.client.get_issue_severity_distribution("p1")
        self.assertEqual(dist["BUG"]["BLOCKER"], 2)
        self.assertEqual(dist["BUG"]["CRITICAL"], 5)

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_quality_gate_status(self, mock_get):
        """测试获取质量门禁状态。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"projectStatus": {"status": "OK"}}
        mock_get.return_value = mock_response

        status = self.client.get_quality_gate_status("p1")
        self.assertEqual(status["status"], "OK")

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_analysis_history(self, mock_get):
        """测试获取分析历史。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"analyses": [{"key": "a1", "date": "2024-01-01"}]}
        mock_get.return_value = mock_response

        history = self.client.get_analysis_history("p1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["key"], "a1")

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_issues(self, mock_get):
        """测试获取问题列表。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"issues": [{"key": "i1"}]}
        mock_get.return_value = mock_response

        issues = self.client.get_issues("p1", severities=["CRITICAL"])
        self.assertEqual(len(issues), 1)
        mock_get.assert_called_with("issues/search", params={"componentKeys": "p1", "p": 1, "ps": 100, "resolved": "false", "severities": "CRITICAL"})

    @patch("devops_collector.core.base_client.BaseClient._get")
    def test_get_hotspot_distribution(self, mock_get):
        """测试获取安全热点分布。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"hotspots": [{"vulnerabilityProbability": "HIGH"}, {"vulnerabilityProbability": "MEDIUM"}], "paging": {"total": 2}}
        mock_get.return_value = mock_response

        dist = self.client.get_hotspot_distribution("p1")
        self.assertEqual(dist["HIGH"], 1)
        self.assertEqual(dist["MEDIUM"], 1)
        self.assertEqual(dist["LOW"], 0)
