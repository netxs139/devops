"""Organization master data (MDM_ORGANIZATION) initialization command."""

from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.organization_service import OrganizationService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "organizations.csv"


class Command(BaseCommand):
    """Initialize organization hierarchy master data from CSV via OrganizationService."""

    help = "初始化组织架构主数据 (MDM_ORGANIZATION)"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="组织架构 CSV 路径")] = DEFAULT_CSV,
    ):
        """Sync organization hierarchy from CSV file."""
        service = OrganizationService(session)

        if not csv_path.exists():
            self.stdout.write(f"⚠️ 警告: 缺少组织架构初始化文件 {csv_path}，跳过同步。\n")
            return True

        self.stdout.write(f"正在从 {csv_path} 初始化组织架构 (via Service Layer)...\n")

        import csv

        with open(csv_path, encoding="utf-8-sig") as f:
            row_count = sum(1 for _ in csv.DictReader(f))

        with self.get_progress() as progress:
            task = progress.add_task("[cyan]同步组织架构...", total=row_count)
            service.sync_from_csv(csv_path, progress_callback=lambda: progress.advance(task))

        self.stdout.write("✅ 组织架构初始化完成。\n")
        return True
