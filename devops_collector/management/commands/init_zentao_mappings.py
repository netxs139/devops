"""初始化禅道 (ZenTao) 身份映射 (IdentityMapping) 数据。."""

import csv
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.identity_mapping_service import IdentityMappingService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "zentao-user.csv"


class Command(BaseCommand):
    """Management command."""

    help = "从 CSV 初始化禅道身份映射（工号/Email 优先策略）"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="禅道用户 CSV 路径")] = DEFAULT_CSV,
    ):
        """Execute command."""
        if not csv_path.exists():
            self.stderr.write(f"❌ 找不到禅道用户 CSV 文件: {csv_path}\n")
            return False

        service = IdentityMappingService(session)

        try:
            self.stdout.write(f"开始同步禅道身份映射数据 (via Service: {csv_path})...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]处理禅道用户映射 ({csv_path.name})...", total=row_count)
                count = service.sync_zentao_mappings(csv_path, progress_callback=lambda: progress.advance(task))

            self.stdout.write(f"✅ 禅道身份映射初始化完成！共建立/更新 {count} 条关联。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 禅道映射初始化失败: {e}\n")
            return False
