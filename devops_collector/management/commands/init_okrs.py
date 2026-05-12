"""初始化系统 OKR 数据（Objective + Key Results）。"""

from pathlib import Path

from devops_collector.core.management import BaseCommand


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "okrs.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化 OKR 主数据（Objective + Key Results）"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="OKR CSV 路径（默认: docs/assets/sample_data/okrs.csv）")

    def check(self, **options) -> list[tuple[str, str]]:
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV
        if not csv_path.exists():
            return [("ERROR", f"缺少 OKR 初始化数据源文件: {csv_path}")]
        return []

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV

        from devops_collector.services.okr_service import OKRService

        service = OKRService(self.session)

        try:
            self.stdout.write(f"从 {csv_path} 同步 OKR 数据 (通过 Service 层)...\n")

            import csv

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]OKR 同步...", total=row_count)

                # 调用服务层，传入回调以更新 CLI 进度条
                service.sync_okrs_from_csv(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ OKR 数据初始化完成 (Service Level Execution)。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ OKR 初始化失败: {e}\n")
            return False
