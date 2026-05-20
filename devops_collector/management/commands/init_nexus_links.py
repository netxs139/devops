"""初始化 Nexus 组件与 MDM 产品关联（支持 exact/regex 双模式匹配）。"""

from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.plugins.nexus.models import NexusComponent
from devops_collector.services.topology_service import TopologyService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "nexus_component_map.csv"


class Command(BaseCommand):
    help = "从 CSV 规则初始化 Nexus 组件与 MDM 产品关联（exact/regex 双模式）"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="Nexus 映射 CSV 路径")] = DEFAULT_CSV,
    ):
        if not csv_path.exists():
            self.stdout.write(f"WARN: 找不到 Nexus 映射文件: {csv_path}\n")
            return True

        service = TopologyService(session)

        try:
            self.stdout.write(f"从 {csv_path} 同步 Nexus 组件关联 (via Service)...\n")

            all_components_count = session.query(NexusComponent).count()

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]匹配 Nexus 组件...", total=all_components_count)
                updated_count = service.sync_nexus_links(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write(f"✅ Nexus 组件关联初始化完成，共更新 {updated_count} 个组件。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ Nexus 关联初始化失败: {e}\n")
            return False
