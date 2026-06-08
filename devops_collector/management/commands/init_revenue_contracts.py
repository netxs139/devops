"""收入合同 (Revenue Contract) 主数据初始化命令。."""

import csv
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.finance_service import FinanceService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "revenue_contracts.csv"


class Command(BaseCommand):
    """Management command."""

    help = "从 CSV 初始化收入合同主数据，并生成默认首付款节点"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="收入合同 CSV 路径")] = DEFAULT_CSV,
        down_pct: Annotated[float, typer.Option("--down-pct", help="首付款比例 %")] = 30.0,
    ):
        """Execute command."""
        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过收入合同初始化：未找到 {csv_path}\n")
            return True

        service = FinanceService(session)

        try:
            self.stdout.write(f"开始从 {csv_path} 录入收入合同数据 (via Service)...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]录入收入合同 ({csv_path.name})...", total=row_count)
                service.sync_revenue_contracts(csv_path, down_pct, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ 收入合同初始化完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 收入合同初始化失败: {e}\n")
            return False
