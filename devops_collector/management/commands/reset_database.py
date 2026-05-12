import logging

from typing import Annotated

import typer
from sqlalchemy import text
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Base


logger = logging.getLogger("DBReset")


class Command(BaseCommand):
    help = "数据库重置工具 (PostgreSQL 增强版). 强制清空并重建所有表。"

    def handle(
        self,
        session: Session,
        yes: Annotated[bool, typer.Option("--yes", help="强制执行，跳过所有安全确认提示")] = False,
    ):
        if not yes:
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
                session.execute(text(terminate_sql))
                session.commit()
            except Exception:
                pass

            # 2. 清理 Schema (Postgres 专用最强清理法)
            self.stdout.write("清理 public schema...\n")
            session.execute(text("DROP SCHEMA public CASCADE;"))
            session.execute(text("CREATE SCHEMA public;"))
            session.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            session.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            session.commit()
            self.stdout.write("public schema 已重置。\n")

            # 3. 重新创建所有表
            Base.metadata.create_all(self.session.bind)
            self.stdout.write("数据库 Schema 已根据当前模型重建。\n")
            return True

        except Exception as e:
            logger.error(f"数据库重置失败: {e}")
            return False
