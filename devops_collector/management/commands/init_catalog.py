"""初始化系统注册表 (SystemRegistry) 和服务目录 (Service Catalog)。."""

import csv
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.catalog_service import CatalogService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")


class Command(BaseCommand):
    """Management command."""

    help = "从 CSV 初始化系统注册表和服务目录"

    def handle(
        self,
        session: Session,
        systems_csv: Annotated[Path, typer.Option("--systems-csv", help="系统注册表 CSV")] = SAMPLE_DATA_DIR / "mdm_systems_registry.csv",
        services_csv: Annotated[Path, typer.Option("--services-csv", help="服务目录 CSV")] = SAMPLE_DATA_DIR / "mdm_services.csv",
    ):
        """Execute command."""
        service = CatalogService(session)

        try:
            if systems_csv.exists():
                self.stdout.write(f"正在从 {systems_csv.name} 同步系统注册表 (via Service)...\n")
                with open(systems_csv, encoding="utf-8-sig") as f:
                    row_count = sum(1 for _ in csv.DictReader(f))
                with self.get_progress() as progress:
                    task = progress.add_task(f"[cyan]系统注册表 ({systems_csv.name})...", total=row_count)
                    service.sync_systems_from_csv(systems_csv, progress_callback=lambda: progress.advance(task))
            else:
                self.stdout.write(f"WARN: 系统注册表文件不存在: {systems_csv}\n")

            if services_csv.exists():
                self.stdout.write(f"正在从 {services_csv.name} 同步服务目录 (via Service)...\n")
                with open(services_csv, encoding="utf-8-sig") as f:
                    row_count = sum(1 for _ in csv.DictReader(f))
                with self.get_progress() as progress:
                    task = progress.add_task(f"[cyan]服务目录 ({services_csv.name})...", total=row_count)
                    service.sync_services_from_csv(services_csv, progress_callback=lambda: progress.advance(task))
            else:
                self.stdout.write(f"WARN: 服务目录文件不存在: {services_csv}\n")

            self.stdout.write("✅ 系统注册表和服务目录初始化完成。\n")
            return True
        except Exception as e:
            self.stderr.write(f"❌ 服务目录初始化失败: {e}\n")
            return False
