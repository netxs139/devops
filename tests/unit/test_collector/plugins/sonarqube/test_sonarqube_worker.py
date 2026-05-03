"""SonarQube Worker 单元测试"""

import unittest
from unittest.mock import MagicMock, patch

from devops_collector.plugins.sonarqube.models import SonarProject
from devops_collector.plugins.sonarqube.worker import SonarQubeWorker


class TestSonarQubeWorker(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.client = MagicMock()
        self.correlation_id = "test-cid"
        # 禁用 transformer 的真实初始化
        with patch("devops_collector.plugins.sonarqube.worker.SonarDataTransformer"):
            self.worker = SonarQubeWorker(self.session, self.client, self.correlation_id)
        self.worker.transformer = MagicMock()

    @patch("devops_collector.plugins.sonarqube.worker.parse_iso8601")
    @patch("devops_collector.core.base_worker.BaseWorker.save_to_staging")
    def test_sync_project_metadata_new(self, mock_staging, mock_parse):
        """测试同步新项目的元数据。"""
        self.client.get_project.return_value = {"key": "p1", "name": "Project 1", "qualifier": "TRK", "lastAnalysisDate": "2024-05-01T10:00:00Z"}
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        project = self.worker._sync_project_metadata("p1")

        self.assertIsNotNone(project)
        self.assertEqual(project.key, "p1")
        self.assertEqual(project.name, "Project 1")
        self.session.add.assert_called_once()
        mock_staging.assert_called_with(source="sonarqube", entity_type="project", external_id="p1", payload=self.client.get_project.return_value)

    def test_sync_measures(self):
        """测试同步代码质量指标。"""
        project = SonarProject(key="p1", name="Project 1")
        self.client.get_measures.return_value = {"coverage": "85.0"}
        self.client.get_quality_gate_status.return_value = {"status": "OK"}
        self.client.get_issue_severity_distribution.return_value = {}
        self.client.get_hotspot_distribution.return_value = {}

        mock_measure = MagicMock()
        self.worker.transformer.transform_measures_snapshot.return_value = mock_measure

        measure = self.worker._sync_measures(project)

        self.assertEqual(measure, mock_measure)
        self.session.add.assert_called_once_with(mock_measure)

    @patch("devops_collector.core.base_worker.BaseWorker.bulk_save_to_staging")
    def test_sync_issues(self, mock_bulk_staging):
        """测试同步问题详情。"""
        project = SonarProject(key="p1", name="Project 1")
        self.client.get_issues.side_effect = [
            [{"key": "issue1"}, {"key": "issue2"}],
            [],  # 结束分页
        ]

        count = self.worker._sync_issues(project)

        self.assertEqual(count, 2)
        self.assertEqual(self.client.get_issues.call_count, 2)
        mock_bulk_staging.assert_called_once()
        self.worker.transformer.transform_issues_batch.assert_called_once()
