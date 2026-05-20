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
    help = "财务成本科目 (CBS) 初始化脚本。"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="成本科目 CSV 路径")] = Path("docs/assets/sample_data/cost_codes.csv"),
    ):
        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过成本科目初始化：未找到 {csv_path}\n")
            return True

        service = FinanceService(session)

        try:
            self.stdout.write(f"从 {csv_path} 加载成本科目 (via Service)...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]同步成本科目...", total=row_count)
                service.sync_cost_codes(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ 成本科目初始化完成。\n")
            return True
        except Exception as e:
            logger.error(f"成本科目初始化失败: {e}")
            return False
