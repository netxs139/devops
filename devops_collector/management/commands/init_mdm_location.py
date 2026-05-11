import csv
import logging
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Location


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "初始化 MDM_LOCATION 表并加载位置数据。"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Path to locations CSV")

    def handle(self, *args, **options):
        csv_path = Path(options.get("csv")) if options.get("csv") else Path("docs/assets/sample_data/locations.csv")

        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过位置初始化：未找到 {csv_path}\n")
            return True

        try:
            self.stdout.write(f"从 {csv_path} 加载地理位置...\n")
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    loc_id = row.get("ID", "").strip()
                    if not loc_id:
                        continue

                    loc = self.session.query(Location).filter_by(location_code=loc_id).first()
                    if not loc:
                        loc = Location(location_code=loc_id)
                        self.session.add(loc)

                    loc.location_name = row.get("全称", "").strip()
                    loc.short_name = row.get("名称", "").strip()
                    loc.region = row.get("大区", "").strip()
                    loc.code = row.get("编码", "").strip()
                    loc.location_type = "province" if loc_id != "000000" else "region"
                    loc.is_active = True

            self.session.flush()
            self.stdout.write("✅ 地理位置 (CSV) 初始化完成。\n")
            return True
        except Exception as e:
            logger.error(f"位置初始化失败: {e}")
            return False
