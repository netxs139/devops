"""采购合同 (Purchase Contract) 主数据初始化命令。"""

import csv
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.finance_service import FinanceService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "purchase_contracts.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化采购合同主数据，并生成演示流水记录"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="采购合同 CSV 路径")] = DEFAULT_CSV,
        demo_period: Annotated[str, typer.Option("--demo-period", help="演示流水账期")] = "2025-01",
    ):
        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过采购合同初始化：未找到 {csv_path}\n")
            return True

        service = FinanceService(session)

        try:
            self.stdout.write(f"开始从 {csv_path} 录入采购合同数据 (via Service)...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]录入采购合同 ({csv_path.name})...", total=row_count)
                service.sync_purchase_contracts(csv_path, demo_period, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ 采购合同初始化完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 采购合同初始化失败: {e}\n")
            return False
