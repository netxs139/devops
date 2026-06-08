"""初始化 Jenkins Job 与 MDM 资产的关联。."""

import csv
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.topology_service import TopologyService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "jenkins_job_map.csv"


class Command(BaseCommand):
    """Management command."""

    help = "从 CSV 初始化 Jenkins Job 与 MDM 资产关联（支持前缀继承）"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="Jenkins 映射 CSV 路径")] = DEFAULT_CSV,
    ):
        """Execute command."""
        if not csv_path.exists():
            self.stdout.write(f"WARN: 找不到 Jenkins 映射文件: {csv_path}\n")
            return True

        service = TopologyService(session)

        try:
            self.stdout.write(f"从 {csv_path} 同步 Jenkins Job 关联 (via Service)...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]Jenkins 关联 ({csv_path.name})...", total=row_count)
                service.sync_jenkins_links(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write("✅ Jenkins 拓扑关联同步完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ Jenkins 关联初始化失败: {e}\n")
            return False
