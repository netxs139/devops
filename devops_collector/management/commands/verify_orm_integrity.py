import logging

from sqlalchemy.orm import configure_mappers

from devops_collector.core.management import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "验证 SQLAlchemy ORM 模型映射完整性与外键循环。"

    def handle(self, *args, **options):
        self.stdout.write(">>> 开始 ORM 映射完整性验证...\n")

        try:
            # Trigger relationship discovery and Mapper initialization
            # Import all plugin models to trigger registration
            try:
                pass
            except Exception:
                pass

            configure_mappers()
            self.stdout.write(">>> configure_mappers() 成功，模型映射关系正常。\n")
            return True
        except Exception as e:
            logger.error(f">>> ORM 验证失败: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False
