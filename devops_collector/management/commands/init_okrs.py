"""OKR master data initialization command (CSV-driven)."""

from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.okr_service import OKRService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "okrs.csv"


class Command(BaseCommand):
    """Initialize OKR Objectives and Key Results from a CSV file via OKRService."""

    help = "从 CSV 初始化 OKR 主数据（Objective + Key Results）"

    def check(self, **options) -> list[tuple[str, str]]:
        """Verify that the OKR CSV source file exists before running handle."""
        csv_path = Path(options.get("csv", DEFAULT_CSV))
        if not csv_path.exists():
            return [("ERROR", f"缺少 OKR 初始化数据源文件: {csv_path}")]
        return []

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="OKR CSV 路径")] = DEFAULT_CSV,
    ):
        """Sync OKR objectives and key results from CSV into the database."""
        service = OKRService(session)

        self.stdout.write(f"从 {csv_path} 同步 OKR 数据 (通过 Service 层)...\n")

        import csv

        with open(csv_path, encoding="utf-8-sig") as f:
            row_count = sum(1 for _ in csv.DictReader(f))

        with self.get_progress() as progress:
            task = progress.add_task("[cyan]OKR 同步...", total=row_count)
            service.sync_okrs_from_csv(csv_path, progress_callback=lambda: progress.advance(task))

        self.stdout.write("✅ OKR 数据初始化完成 (Service Level Execution)。\n")
        return True
