"""初始化产品主数据 (MDM_PRODUCT) 命令。"""

from pathlib import Path

from devops_collector.core.management import BaseCommand


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "products.csv"


class Command(BaseCommand):
    help = "初始化产品主数据 (MDM_PRODUCT)"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="产品 CSV 路径")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV

        from devops_collector.services.product_service import ProductService

        service = ProductService(self.session)

        try:
            if not csv_path.exists():
                self.stdout.write(f"⚠️ 警告: 缺少产品初始化文件 {csv_path}，跳过同步。\n")
                return True

            self.stdout.write(f"正在从 {csv_path} 初始化产品目录 (via Service Layer)...\n")

            import csv

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]同步产品目录...", total=row_count)
                service.sync_products_from_csv(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ 产品主数据初始化完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 产品初始化失败: {e}\n")
            return False
