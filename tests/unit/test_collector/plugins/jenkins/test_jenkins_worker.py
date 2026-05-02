import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devops_collector.models import JenkinsTestExecution
from devops_collector.models.base_models import Base, User
from devops_collector.plugins.jenkins.models import JenkinsBuild, JenkinsJob
from devops_collector.plugins.jenkins.worker import JenkinsWorker


class TestJenkinsWorker(unittest.TestCase):
    def setUp(self):
        # 使用内存 SQLite 测试
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.mock_client = MagicMock()
        self.worker = JenkinsWorker(self.session, self.mock_client)

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_process_task_sync_all_jobs(self):
        """测试同步所有任务的分发。"""
        with patch.object(self.worker, "sync_all_jobs") as mock_sync:
            self.worker.process_task({"job_type": "sync_all_jobs"})
            mock_sync.assert_called_once()

    def test_process_task_sync_builds(self):
        """测试同步构建的分发。"""
        with patch.object(self.worker, "sync_job_builds") as mock_sync:
            self.worker.process_task({"job_type": "sync_builds", "job_full_name": "test-job", "limit": 50})
            mock_sync.assert_called_once_with("test-job", 50)

    def test_sync_all_jobs(self):
        """测试 Job 列表同步逻辑。"""
        self.mock_client.get_jobs.return_value = [
            {"name": "job1", "fullName": "job1", "url": "http://j/job/job1", "description": "desc1", "color": "blue"},
            {"name": "job2", "fullName": "folder/job2", "url": "http://j/job/folder/job2"},
        ]

        count = self.worker.sync_all_jobs()
        self.assertEqual(count, 2)

        job1 = self.session.query(JenkinsJob).filter_by(full_name="job1").first()
        self.assertIsNotNone(job1)
        self.assertEqual(job1.name, "job1")

        job2 = self.session.query(JenkinsJob).filter_by(full_name="folder/job2").first()
        self.assertIsNotNone(job2)

    def test_sync_job_builds(self):
        """测试构建列表同步逻辑，包含用户关联和自动创建 Job。"""
        # 1. 预置用户数据与身份映射以验证关联
        import uuid

        from devops_collector.models.base_models import IdentityMapping

        test_user = User(global_user_id=uuid.uuid4(), username="admin", employee_id="A001", is_current=True)
        self.session.add(test_user)

        # 必须手动建立映射，否则 IdentityManager 找不到人
        mapping = IdentityMapping(global_user_id=test_user.global_user_id, source_system="jenkins", external_user_id="admin", mapping_status="AUTO")
        self.session.add(mapping)
        self.session.commit()

        # 模拟 Job 不存在，需要调用 get_job_details 自动创建
        self.mock_client.get_job_details.return_value = {"name": "new-job", "url": "http://j/new-job"}
        self.mock_client.get_builds.return_value = [{"number": 1, "url": "http://j/new-job/1/"}]
        self.mock_client.get_build_details.return_value = {
            "number": 1,
            "url": "http://j/new-job/1/",
            "result": "SUCCESS",
            "duration": 1000,
            "timestamp": 1714464000000,
            "actions": [{"_class": "hudson.model.CauseAction", "causes": [{"_class": "hudson.model.Cause$UserIdCause", "userName": "admin"}]}],
        }

        count = self.worker.sync_job_builds("new-job", 10)
        self.assertEqual(count, 1)

        # 验证 Job 是否自动创建
        job = self.session.query(JenkinsJob).filter_by(full_name="new-job").first()
        self.assertIsNotNone(job)

        # 验证构建和用户关联
        build = self.session.query(JenkinsBuild).filter_by(job_id=job.id, number=1).first()
        self.assertIsNotNone(build)
        self.assertEqual(build.trigger_user_id, test_user.global_user_id)

    def test_sync_job_builds_error_handling(self):
        """测试构建同步过程中的异常处理。"""
        job = JenkinsJob(full_name="error-job", name="error-job")
        self.session.add(job)
        self.session.commit()

        self.mock_client.get_builds.return_value = [{"number": 99, "url": "url"}]
        self.mock_client.get_build_details.side_effect = Exception("Network Error")

        count = self.worker.sync_job_builds("error-job", 1)
        self.assertEqual(count, 0)  # 报错应被捕获

    def test_sync_test_report(self):
        """测试测试报告解析逻辑。"""
        # 必须先创建 GitLabProject 桩数据满足外键约束
        from devops_collector.plugins.gitlab.models import GitLabProject

        gp = GitLabProject(id=101, name="test-proj", path_with_namespace="test-proj")
        self.session.add(gp)
        self.session.flush()

        job = JenkinsJob(full_name="test-job", name="test-job", gitlab_project_id=101)
        self.session.add(job)
        self.session.flush()

        build = JenkinsBuild(job_id=job.id, number=1)
        self.session.add(build)
        self.session.commit()

        mock_report = {"suites": [{"cases": [{"status": "PASSED"}]}]}
        self.mock_client.get_test_report.return_value = mock_report

        from devops_collector.plugins.jenkins.parser import ReportParser

        mock_summary = JenkinsTestExecution(project_id=101, build_id="1", test_level="unit", total_cases=1, passed_count=1, failed_count=0)

        with patch.object(ReportParser, "parse_jenkins_test_report", return_value=mock_summary):
            self.worker._sync_test_report(job, build)

            summary = self.session.query(JenkinsTestExecution).filter_by(project_id=101, build_id="1").first()
            self.assertIsNotNone(summary)
            self.assertEqual(summary.passed_count, 1)


if __name__ == "__main__":
    unittest.main()
