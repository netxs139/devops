import logging
from unittest.mock import MagicMock

from devops_collector.core.management import BaseCommand


logger = logging.getLogger(__name__)


class MockRow:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Command(BaseCommand):
    help = "冒烟测试脚本：研发效能报告格式预览 (Mock Mode)"

    def handle(self, *args, **options):
        self.stdout.write("=== [SMOKE TEST] Executive Audit Report - Mock Mode ===\n")

        # 我们通过动态 import 获取 Command 类，然后手动实例化它进行 Mock
        from devops_collector.management.commands.executive_audit_report import Command as AuditCommand

        # 实例化但不调用 handle，而是模拟其内部方法
        audit_cmd = AuditCommand()
        audit_cmd.session = MagicMock()
        audit_cmd.stdout = self.stdout  # 共享 stdout

        # 模拟数据
        hotspots_data = [
            MockRow(file_path="app/services/order_service.py", risk_factor=45.2, churn_90d=24),
            MockRow(file_path="core/auth_provider.py", risk_factor=38.1, churn_90d=15),
        ]
        bus_factor_data = [MockRow(subsystem="billing_engine", author_user_id="user_7e2a1b", subsystem_ownership_pct=92.5)]
        talent_data = [
            MockRow(real_name="ZhangSan", talent_archetype="Domain Specialist", talent_influence_index=88.5),
            MockRow(real_name="LiSi", talent_archetype="Collaborative Leader", talent_influence_index=72.3),
        ]
        fin_audit_data = MockRow(audit_week="2026-W01", capitalization_rate=65.5, audit_status="AUDIT_READY")

        # 劫持内部获取数据的方法
        audit_cmd._fetch_hotspots = MagicMock(return_value=hotspots_data)
        audit_cmd._fetch_bus_factor_risks = MagicMock(return_value=bus_factor_data)
        audit_cmd._fetch_financial_audit = MagicMock(return_value=fin_audit_data)
        audit_cmd._fetch_talent_spotlight = MagicMock(return_value=talent_data)

        # 运行被 Mock 的命令
        audit_cmd.handle()

        self.stdout.write("\n=== [SMOKE TEST] End of Mock Report ===\n")
        return True
