import logging

from devops_collector.core.management import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "核心模块导入依赖检查：快速确认环境是否完整。"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60 + "\n")
        self.stdout.write("DevOps Platform 依赖导入检查\n")
        self.stdout.write("=" * 60 + "\n")

        modules = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "devops_collector.config",
            "devops_collector.models.base_models",
            "devops_collector.auth.auth_service",
            "devops_collector.services.security",
            "devops_portal.main",
        ]

        success_count = 0
        for mod in modules:
            try:
                # 使用 importlib 动态加载
                import importlib

                importlib.import_module(mod)
                self.stdout.write(f"✓ {mod: <40} [  OK  ]\n")
                success_count += 1
            except ImportError as e:
                self.stdout.write(f"✗ {mod: <40} [ FAIL ] - {e}\n")
            except Exception as e:
                self.stdout.write(f"! {mod: <40} [  ERR ] - {type(e).__name__}: {e}\n")

        self.stdout.write("-" * 60 + "\n")
        self.stdout.write(f"检查完成: {success_count}/{len(modules)} 成功\n")
        self.stdout.write("=" * 60 + "\n")

        return success_count == len(modules)
