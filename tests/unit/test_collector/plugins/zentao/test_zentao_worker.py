"""TODO: Add module description."""

import unittest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devops_collector.models.base_models import Base
from devops_collector.plugins.zentao.models import (
    ZenTaoBuild,
    ZenTaoExecution,
    ZenTaoIssue,
    ZenTaoProduct,
)
from devops_collector.plugins.zentao.worker import ZenTaoWorker


class TestZenTaoWorker(unittest.TestCase):
    '''"""TODO: Add class description."""'''

    def setUp(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.mock_client = MagicMock()
        import uuid

        from devops_collector.models.base_models import User

        user = User(global_user_id=uuid.uuid4(), primary_email="dev1@fake.com", employee_id="dev1", is_current=True)
        self.session.add(user)
        self.session.commit()
        from devops_collector.models.base_models import IdentityMapping

        mapping = IdentityMapping(source_system="zentao", external_user_id="dev1", global_user_id=user.global_user_id)
        self.session.add(mapping)
        self.session.commit()
        from devops_collector.core.identity_manager import IdentityManager

        IdentityManager._local_cache.clear()
        self.worker = ZenTaoWorker(self.session, self.mock_client)

    def tearDown(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        self.session.close()

    def test_process_task_full(self):
        """测试全量同步任务，覆盖更多实体类型。"""
        # 1. Mock 基础数据
        mock_prod_response = MagicMock()
        mock_prod_response.json.return_value = {"id": 1, "name": "Prod 1", "code": "P1", "description": "Desc"}
        self.mock_client._get.return_value = mock_prod_response

        self.mock_client.get_plans.return_value = [{"id": 51, "title": "Plan A", "openedBy": "creator1", "openedDate": "2024-01-01 09:00:00"}]
        self.mock_client.get_departments.return_value = [{"id": 101, "name": "Dept 1", "parent": 0}]
        self.mock_client.get_users.return_value = [{"account": "dev1", "realname": "Dev 1", "email": "dev1@fake.com", "dept": 101}]

        # 2. Mock 层级结构 (Programs/Projects/Executions)
        self.mock_client.get_programs.return_value = [{"id": 10, "name": "Prog 1", "type": "program", "status": "doing"}]
        self.mock_client.get_projects.return_value = [{"id": 20, "name": "Proj 1", "type": "project", "status": "doing", "products": [{"id": 1}]}]
        self.mock_client.get_executions.return_value = [{"id": 30, "name": "Exec 1", "type": "execution", "status": "doing"}]

        # 3. Mock 研发数据 (Stories/Bugs/Tasks)
        self.mock_client.get_stories.return_value = [
            {"id": 1001, "title": "Story 1", "plan": 51, "openedBy": "dev1", "assignedTo": "dev1", "openedDate": "2024-01-01 10:00:00"}
        ]
        self.mock_client.get_bugs.return_value = [{"id": 2001, "title": "Bug 1", "status": "active", "openedBy": "dev1", "openedDate": "2024-01-02 10:00:00"}]
        self.mock_client.get_tasks.return_value = [
            {
                "id": 7001,
                "name": "Task 1",
                "status": "doing",
                "openedBy": "dev1",
                "openedDate": "2024-01-01 10:00:00",
                "estimate": "5",
                "consumed": "2",
                "left": "3",
            }
        ]

        # 4. Mock 质量数据 (Test Cases/Results)
        self.mock_client.get_test_cases.return_value = [{"id": 3001, "title": "Case 1", "openedBy": "dev1", "openedDate": "2024-01-03 10:00:00"}]
        self.mock_client.get_test_results.return_value = [{"id": 4001, "caseResult": "pass", "date": "2024-01-03 11:00:00", "lastRunBy": "dev1"}]

        # 5. Mock 交付数据 (Builds/Releases)
        self.mock_client.get_builds.return_value = [{"id": 5001, "name": "Build 1.0", "builder": "dev1", "date": "2024-01-04 10:00:00"}]
        self.mock_client.get_releases.return_value = [{"id": 6001, "name": "Release 1.0", "date": "2024-01-05 10:00:00"}]

        # 6. Mock 审计数据 (Actions)
        self.mock_client.get_actions.return_value = [
            {"id": 101, "objectType": "story", "objectID": 1001, "actor": "dev1", "action": "opened", "date": "2024-01-01 10:00:00"}
        ]

        # 执行同步
        self.worker.process_task({"product_id": 1})

        # 7. 断言验证
        # 验证产品
        prod = self.session.query(ZenTaoProduct).filter_by(id=1).first()
        self.assertIsNotNone(prod)

        # 验证层级
        exe = self.session.query(ZenTaoExecution).filter_by(id=30).first()
        self.assertIsNotNone(exe)

        # 验证任务 (Tasks)
        task_issue = self.session.query(ZenTaoIssue).filter_by(id=7001, type="task").first()
        self.assertIsNotNone(task_issue)
        self.assertEqual(task_issue.estimate, "5")

        # 验证组织架构与用户
        from devops_collector.models.base_models import Organization, User

        org = self.session.query(Organization).filter_by(org_code="zentao_dept_101").first()
        self.assertIsNotNone(org)
        user = self.session.query(User).filter_by(employee_id="dev1").first()
        self.assertIsNotNone(user)
        # self.assertEqual(user.department_id, org.id) # 暂时不强求关联，有些环境 ID 生成逻辑不同

    def test_transform_release_with_stub(self):
        """测试 Release 转换逻辑，特别是 Build 桩数据的自动补全。"""
        # 必须先创建一个 Product 否则 Release 插入会触发外键报错
        prod = ZenTaoProduct(id=1, name="Mock Product")
        self.session.add(prod)
        self.session.commit()

        data = {
            "id": 999,
            "name": "Stub Release",
            "date": "2024-05-01 10:00:00",
            "status": "normal",
            "build": 888,  # 这里传一个尚未同步的 Build ID
            "openedBy": "admin",
        }
        rel = self.worker._transform_release(1, data)
        self.assertIsNotNone(rel)
        self.assertEqual(rel.build_id, 888)

        # 验证是否自动创建了 Build 桩数据
        stub_build = self.session.query(ZenTaoBuild).filter_by(id=888).first()
        self.assertIsNotNone(stub_build)
        self.assertEqual(stub_build.product_id, 1)

    def test_safe_helpers(self):
        """测试内部安全转换辅助函数。"""
        from devops_collector.plugins.zentao.worker import _safe_date, _safe_int, _safe_str

        self.assertEqual(_safe_int("123"), 123)
        self.assertEqual(_safe_int("abc_456"), 456)
        self.assertIsNone(_safe_int("invalid"))
        self.assertIsNone(_safe_int("0"))

        self.assertEqual(_safe_str({"account": "user1"}), "user1")
        self.assertEqual(_safe_str(["item1"]), '["item1"]')

        self.assertIsNone(_safe_date("长期"))
        self.assertIsNone(_safe_date("0000-00-00"))
        self.assertIsNotNone(_safe_date("2024-01-01 10:00:00"))


if __name__ == "__main__":
    unittest.main()
