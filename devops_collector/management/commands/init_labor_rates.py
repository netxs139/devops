import csv
import logging
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.finance_service import FinanceService


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "人工费率表初始化。"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="人工费率 CSV 路径")] = Path("docs/assets/sample_data/labor_rates.csv"),
    ):
        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过人工费率初始化：未找到 {csv_path}\n")
            return True

        service = FinanceService(session)

        try:
            self.stdout.write(f"从 {csv_path} 加载人工费率 (via Service)...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]同步人工费率...", total=row_count)
                service.sync_labor_rates(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ 人工费率初始化完成。\n")
            return True
        except Exception as e:
            logger.error(f"人工费率初始化失败: {e}")
            return False
