import csv
import logging
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import CostCode


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "财务成本科目 (CBS) 初始化脚本。"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Path to cost_codes CSV")

    def handle(self, *args, **options):
        csv_path = Path(options.get("csv")) if options.get("csv") else Path("docs/assets/sample_data/cost_codes.csv")

        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过成本科目初始化：未找到 {csv_path}\n")
            return True

        try:
            self.stdout.write(f"从 {csv_path} 加载成本科目...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get("科目代码", "").strip()
                    if not code:
                        continue

                    cc = self.session.query(CostCode).filter_by(code=code).first()
                    if not cc:
                        cc = CostCode(code=code)
                        self.session.add(cc)

                    cc.name = row.get("科目名称", "").strip()
                    cc.category = row.get("分类", "").strip()
                    cc.default_capex_opex = row.get("支出类型", "").strip()
                    cc.description = row.get("描述", "").strip()

                    # 处理父级 (注意：父级必须在 CSV 中先于子级出现，或者两遍处理)
                    parent_code = row.get("父级代码", "").strip()
                    if parent_code:
                        parent = self.session.query(CostCode).filter_by(code=parent_code).first()
                        if parent:
                            cc.parent_id = parent.id

                    self.session.flush()

            self.stdout.write("✅ 成本科目初始化完成。\n")
            return True
        except Exception as e:
            logger.error(f"成本科目初始化失败: {e}")
            return False
