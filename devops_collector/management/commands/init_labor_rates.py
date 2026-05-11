import csv
import logging
from datetime import UTC, datetime
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import LaborRateConfig


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "人工费率表初始化。"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Path to labor_rates CSV")

    def handle(self, *args, **options):
        csv_path = Path(options.get("csv")) if options.get("csv") else Path("docs/assets/sample_data/labor_rates.csv")

        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过人工费率初始化：未找到 {csv_path}\n")
            return True

        try:
            self.stdout.write(f"从 {csv_path} 加载人工费率...\n")
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    level = row.get("职级", "").strip()
                    rate_str = row.get("日费率", "0")
                    if not level:
                        continue

                    rate = float(rate_str)
                    obj = self.session.query(LaborRateConfig).filter_by(job_title_level=level, is_active=True).first()
                    if not obj:
                        obj = LaborRateConfig(job_title_level=level)
                        self.session.add(obj)

                    obj.daily_rate = rate
                    obj.hourly_rate = rate / 8.0
                    obj.currency = "CNY"
                    obj.effective_date = datetime.now(UTC)

            self.session.flush()
            self.stdout.write("✅ 人工费率初始化完成。\n")
            return True
        except Exception as e:
            logger.error(f"人工费率初始化失败: {e}")
            return False
