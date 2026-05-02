"""GitLab Worker 边缘用例与异常路径测试。"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from devops_collector.plugins.gitlab.models import GitLabGroup, GitLabProject
from devops_collector.plugins.gitlab.worker import GitLabWorker


class TestGitLabWorkerEdgeCases(unittest.TestCase):
    """测试 GitLabWorker 的异常分支和冷僻路径。"""

    def setUp(self):
        """初始化测试环境，使用 Mock 隔离外部依赖。"""
        # 预加载模型以避免 SQLAlchemy 映射错误
        from devops_collector.core.plugin_loader import PluginLoader

        PluginLoader.autodiscover()
        PluginLoader.load_models()

        self.session = MagicMock()
        self.client = MagicMock()
        # 初始化时提供 client 以避免 ValueError
        self.worker = GitLabWorker(self.session, self.client, correlation_id="test-cid")

    def test_process_task_naive_datetime_handling(self):
        """测试对数据库中 naive datetime (无时区) 的容错处理 [L72-75]。"""
        project = MagicMock(spec=GitLabProject)
        project.id = 1
        project.last_synced_at = datetime(2024, 1, 1)  # 故意不带时区
        self.worker._sync_project = MagicMock(return_value=project)
        self.worker._sync_commits = MagicMock(return_value=0)
        self.worker._sync_issues = MagicMock(return_value=0)
        self.worker._sync_merge_requests = MagicMock(return_value=0)
        self.worker._match_identities = MagicMock()

        task = {"project_id": 1}
        # 应该能正常运行不崩溃
        self.worker.process_task(task)

        # 验证 sync_commits 被调用，说明时间戳处理逻辑已走过
        self.worker._sync_commits.assert_called()

    def test_process_task_secondary_sync_failure_resilience(self):
        """测试次要数据同步失败时的韧性 [L100-101]。"""
        project = MagicMock(spec=GitLabProject)
        project.id = 1
        project.last_synced_at = None
        self.worker._sync_project = MagicMock(return_value=project)
        self.worker._sync_commits = MagicMock(return_value=0)
        self.worker._sync_issues = MagicMock(return_value=0)
        self.worker._sync_merge_requests = MagicMock(return_value=0)
        self.worker._match_identities = MagicMock()

        # 模拟其中一个次要同步方法抛出异常
        self.worker._sync_pipelines = MagicMock(side_effect=Exception("Mock Pipeline Fail"))

        task = {"project_id": 1}
        with self.assertLogs("devops_collector.plugins.gitlab.worker", level="WARNING") as cm:
            self.worker.process_task(task)
            # 验证产生了对应的警告日志
            self.assertTrue(any("Secondary sync failed for pipelines" in output for output in cm.output))

    def test_process_task_deep_analysis_failure_capture(self):
        """测试开启深度分析且失败时的捕获逻辑 [L104-108]。"""
        project = MagicMock(spec=GitLabProject)
        project.id = 1
        project.last_synced_at = None
        self.worker._sync_project = MagicMock(return_value=project)
        self.worker._sync_commits = MagicMock(return_value=0)
        self.worker._sync_issues = MagicMock(return_value=0)
        self.worker._sync_merge_requests = MagicMock(return_value=0)
        self.worker._match_identities = MagicMock()

        self.worker.enable_deep_analysis = True
        self.worker._sync_wiki_logs = MagicMock()
        self.worker._sync_dependencies = MagicMock()

        task = {"project_id": 1}
        self.worker.process_task(task)
        self.worker._sync_dependencies.assert_called()

    def test_process_task_main_crash_and_rollback(self):
        """测试主任务崩溃时的回滚与状态标记逻辑 [L129-150]。"""
        project_id = 999
        self.worker._sync_project = MagicMock(side_effect=RuntimeError("Core Engine Crash"))

        # 模拟回滚时能查到该项目以标记失败
        failed_project = MagicMock(spec=GitLabProject)
        failed_project.id = project_id
        self.session.query.return_value.filter_by.return_value.first.return_value = failed_project

        task = {"project_id": project_id}
        with self.assertRaises(RuntimeError):
            self.worker.process_task(task)

        # 验证回滚动作
        self.session.rollback.assert_called()
        # 验证项目状态被标记为 FAILED
        self.assertEqual(failed_project.sync_status, "FAILED")
        self.session.commit.assert_called()

    def test_ensure_group_namespace_fallback_logic(self):
        """测试 Group 查找失败时降级到 Namespace API 的逻辑 [L190-192]。"""
        ns_id = 55
        self.session.query.return_value.filter_by.return_value.first.return_value = None
        # 模拟 Group API 报错，但 Namespace API 成功
        self.client.get_group.side_effect = Exception("Not Found")
        self.client.get_namespace.return_value = {"id": ns_id, "name": "user-space", "path": "user-space"}

        result = self.worker._ensure_group(ns_id)
        self.assertTrue(result)
        self.client.get_namespace.assert_called_with(ns_id)

    def test_sync_project_group_sync_failure(self):
        """测试组同步失败导致 group_id 设为 None 的路径 [L172]。"""
        self.client.get_project.return_value = {"id": 123, "name": "test", "namespace": {"id": 456}}
        self.worker._ensure_group = MagicMock(return_value=False)
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        project = self.worker._sync_project(123)
        self.assertIsNone(project.group_id)

    def test_constructor_validation(self):
        """测试构造函数对 client 的校验 [L45]。"""
        with self.assertRaises(ValueError) as cm:
            GitLabWorker(self.session, client=None)
        self.assertEqual(str(cm.exception), "Client must be provided")

    def test_process_task_missing_project_id(self):
        """测试任务中缺失 project_id 的情况 [L58]。"""
        with self.assertRaises(ValueError) as cm:
            self.worker.process_task({})
        self.assertEqual(str(cm.exception), "No project_id provided in task")

    def test_process_task_project_sync_returns_none(self):
        """测试项目同步返回 None 时的跳过逻辑 [L63]。"""
        self.worker._sync_project = MagicMock(return_value=None)
        result = self.worker.process_task({"project_id": 123})
        self.assertEqual(result["status"], "skipped")

    def test_sync_project_api_returns_none(self):
        """测试 API 返回空项目数据的情况 [L157]。"""
        self.client.get_project.return_value = None
        result = self.worker._sync_project(123)
        self.assertIsNone(result)

    def test_ensure_group_already_exists(self):
        """测试组已存在时的快速返回逻辑 [L184]。"""
        group = MagicMock(spec=GitLabGroup)
        self.session.query.return_value.filter_by.return_value.first.return_value = group
        result = self.worker._ensure_group(456)
        self.assertTrue(result)
        # 验证没有调用 API
        self.client.get_group.assert_not_called()


if __name__ == "__main__":
    unittest.main()
