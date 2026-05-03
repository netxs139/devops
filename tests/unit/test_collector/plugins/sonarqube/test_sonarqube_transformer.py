"""SonarQube Transformer 单元测试"""

import unittest
from unittest.mock import MagicMock

from devops_collector.plugins.sonarqube.models import SonarProject
from devops_collector.plugins.sonarqube.transformer import SonarDataTransformer


class TestSonarQubeTransformer(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.transformer = SonarDataTransformer(self.session)

    def test_transform_measures_snapshot(self):
        """测试指标快照转换。"""
        project = SonarProject(id=1, key="p1", name="Project 1")
        measures_data = {
            "files": "100",
            "lines": "10000",
            "coverage": "85.5",
            "bugs": "5",
            "vulnerabilities": "2",
            "reliability_rating": "1.0",
            "security_rating": "2.0",
            "sqale_rating": "3.0",
        }
        gate_status = {"status": "OK"}
        issue_dist = {"BUG": {"BLOCKER": 1, "CRITICAL": 1}, "VULNERABILITY": {"MAJOR": 2}}
        hotspot_dist = {"HIGH": 0, "MEDIUM": 1, "LOW": 5}

        measure = self.transformer.transform_measures_snapshot(project, measures_data, gate_status, issue_dist, hotspot_dist)

        self.assertEqual(measure.project_id, 1)
        self.assertEqual(measure.files, 100)
        self.assertEqual(measure.lines, 10000)
        self.assertEqual(measure.coverage, 85.5)
        self.assertEqual(measure.bugs_blocker, 1)
        self.assertEqual(measure.security_hotspots_medium, 1)
        self.assertEqual(measure.reliability_rating, "A")
        self.assertEqual(measure.security_rating, "B")
        self.assertEqual(measure.sqale_rating, "C")
        self.assertEqual(measure.quality_gate_status, "OK")

    def test_transform_issues_batch(self):
        """测试批量问题转换。"""
        project = SonarProject(id=1, key="p1")
        issues_data = [
            {"key": "i1", "type": "BUG", "severity": "MAJOR", "message": "msg1"},
            {"key": "i2", "type": "VULNERABILITY", "severity": "CRITICAL", "message": "msg2"},
        ]

        # 模拟数据库查询（无现有记录）
        self.session.query.return_value.filter.return_value.all.return_value = []

        results = self.transformer.transform_issues_batch(project, issues_data)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].issue_key, "i1")
        self.assertEqual(results[0].type, "BUG")
        self.assertEqual(results[1].issue_key, "i2")
        self.assertEqual(results[1].type, "VULNERABILITY")
        self.assertEqual(self.session.add.call_count, 2)
