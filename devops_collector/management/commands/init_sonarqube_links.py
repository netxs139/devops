"""初始化 SonarQube 项目与 MDM 资产的关联。"""

import csv
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.topology_service import TopologyService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "sonarqube_project_map.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化 SonarQube 项目与 MDM 项目/产品关联"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="SonarQube 映射 CSV 路径")] = DEFAULT_CSV,
    ):
        if not csv_path.exists():
            self.stdout.write(f"WARN: 找不到 SonarQube 映射文件: {csv_path}\n")
            return True

        service = TopologyService(session)

        try:
            self.stdout.write(f"从 {csv_path} 同步 SonarQube 项目关联 (via Service)...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]SonarQube 关联 ({csv_path.name})...", total=row_count)
                service.sync_sonarqube_links(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ SonarQube 项目关联初始化完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ SonarQube 关联初始化失败: {e}\n")
            return False
