import logging

from sqlalchemy import text

from devops_collector.core.management import BaseCommand, DiagHelper


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "数据库专项诊断脚本。"

    def handle(self, *args, **options):
        DiagHelper.print_header("数据库专项诊断")

        success = True

        # 1. 检查连接与版本
        def check_version():
            result = self.session.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            DiagHelper.log_success(f"数据库连接成功: {version}")
            return True

        _, _ = DiagHelper.run_check("连接测试", check_version)

        # 2. 检查核心表内容
        tables = ["mdm_identities", "mdm_organizations", "mdm_products", "mdm_projects", "sys_role", "sys_menu"]

        print("\n[数据统计] 核心表记录数:")
        for table in tables:
            try:
                count_result = self.session.execute(text(f"SELECT count(*) FROM {table}")).fetchone()[0]
                print(f"   - {table:22}: {count_result} 条记录")
            except Exception:
                DiagHelper.log_warning(f"{table:22}: ✗ 查询失败 (可能表不存在)")
                success = False

        DiagHelper.print_footer()
        return success
