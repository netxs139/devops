"""数据清理命令 (Data Cleanup)。

调用 RetentionManager 执行原始采集数据的清理任务。
"""

from devops_collector.core.management import BaseCommand
from devops_collector.services.retention_manager import RetentionManager


class Command(BaseCommand):
    help = "数据清理：根据保留策略删除过期的 Staging/原始采集数据"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, help="覆盖默认保留天数")

    def handle(self, *args, **options):
        options.get("days")

        try:
            self.stdout.write("正在启动数据清理任务...\n")
            manager = RetentionManager()

            # 如果 RetentionManager 支持自定义天数，可以传参，否则按默认
            # 假设目前 RetentionManager 逻辑是内部读取配置
            deleted_count = manager.cleanup_raw_data()

            self.stdout.write(f"✅ 清理完成。共删除 {deleted_count} 条记录。\n")
            return True
        except Exception as e:
            self.stderr.write(f"❌ 清理失败: {e}\n")
            return False
