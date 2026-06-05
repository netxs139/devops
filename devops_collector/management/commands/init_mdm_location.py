"""MDM_LOCATION table initialization command (CSV-driven)."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.location_service import LocationService


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Initialize the MDM_LOCATION table from a CSV file via LocationService."""

    help = "初始化 MDM_LOCATION 表并加载位置数据。"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="Path to locations CSV")] = Path("docs/assets/sample_data/locations.csv"),
    ):
        """Read locations CSV and upsert records into mdm_locations."""
        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过位置初始化：未找到 {csv_path}\n")
            return True

        service = LocationService(session)

        try:
            self.stdout.write(f"从 {csv_path} 加载地理位置 (via Service)...\n")
            success = service.init_from_csv(csv_path)
            if success:
                self.stdout.write("✅ 地理位置 (CSV) 初始化完成。\n")
                return True
            else:
                self.stderr.write("❌ 位置初始化失败: 文件读取异常或不存在。\n")
                return False
        except Exception as e:
            logger.error(f"位置初始化失败: {e}")
            self.stderr.write(f"❌ 位置初始化失败: {e}\n")
            return False
