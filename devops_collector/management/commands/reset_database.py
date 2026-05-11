import logging

from sqlalchemy import text

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Base


logger = logging.getLogger("DBReset")


class Command(BaseCommand):
    help = "数据库重置工具 (PostgreSQL 增强版). 强制清空并重建所有表。"

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="跳过确认提示")

    def handle(self, *args, **options):
        if not options.get("yes"):
            self.stdout.write("！！！警告：正在重置数据库，全量数据将被清空！！！\n")
            confirm = input("确定要继续吗？(y/N): ")
            if confirm.lower() != "y":
                self.stdout.write("操作已取消。\n")
                return False

        try:
            # 1. 强制断开其他连接
            db_name = self.session.bind.url.database
            terminate_sql = f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
              AND pid <> pg_backend_pid();
            """
            try:
                self.session.execute(text(terminate_sql))
                self.session.commit()
            except Exception:
                pass

            # 2. 清理 Schema (Postgres 专用最强清理法)
            self.stdout.write("清理 public schema...\n")
            self.session.execute(text("DROP SCHEMA public CASCADE;"))
            self.session.execute(text("CREATE SCHEMA public;"))
            self.session.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            self.session.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            self.session.commit()
            self.stdout.write("public schema 已重置。\n")

            # 3. 重新创建所有表
            Base.metadata.create_all(self.session.bind)
            self.stdout.write("数据库 Schema 已根据当前模型重建。\n")
            return True

        except Exception as e:
            logger.error(f"数据库重置失败: {e}")
            return False
