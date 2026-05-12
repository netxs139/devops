"""采购合同 (Purchase Contract) 主数据初始化命令。"""

import csv
from datetime import datetime
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import CostCode, PurchaseContract, ResourceCost


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "purchase_contracts.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化采购合同主数据，并生成演示流水记录"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="采购合同 CSV 路径（默认: docs/assets/sample_data/purchase_contracts.csv）")
        parser.add_argument("--demo-period", type=str, default="2025-01", help="演示流水账期 (默认: 2025-01)")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV
        demo_period: str = options.get("demo_period", "2025-01")

        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过采购合同初始化：未找到 {csv_path}\n")
            return True

        try:
            self.stdout.write(f"开始从 {csv_path} 录入采购合同数据...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]录入采购合同 ({csv_path.name})...", total=len(rows))

                for row in rows:
                    contract_no = row.get("合同编号", "").strip()
                    title = row.get("合同标题", "").strip()
                    vendor = row.get("供应商名称", "").strip()
                    vendor_id = row.get("供应商ID", "").strip()
                    total_str = row.get("总金额", "0")
                    start_date_str = row.get("开始日期", "").strip()
                    end_date_str = row.get("结束日期", "").strip()
                    cost_code_str = row.get("科目代码", "").strip()
                    capex_opex = row.get("支出类型", "").strip()

                    if not contract_no or not title:
                        progress.advance(task)
                        continue

                    total = float(total_str) if total_str else 0.0
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else datetime.now()
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime.now()

                    cc = self.session.query(CostCode).filter(CostCode.code == cost_code_str).first()
                    if not cc:
                        self.stdout.write(f"WARN: 找不到科目代码 {cost_code_str}，跳过合同 {contract_no}\n")
                        progress.advance(task)
                        continue

                    pc = self.session.query(PurchaseContract).filter(PurchaseContract.contract_no == contract_no).first()
                    if not pc:
                        pc = PurchaseContract(contract_no=contract_no)
                        self.session.add(pc)

                    pc.title = title
                    pc.vendor_name = vendor
                    pc.vendor_id = vendor_id
                    pc.total_amount = total
                    pc.start_date = start_date
                    pc.end_date = end_date
                    pc.cost_code_id = cc.id
                    pc.capex_opex_flag = capex_opex
                    self.session.flush()

                    # 生成演示流水（每个合同一条，若不存在）
                    cost_record = (
                        self.session.query(ResourceCost)
                        .filter(
                            ResourceCost.purchase_contract_id == pc.id,
                            ResourceCost.period == demo_period,
                        )
                        .first()
                    )
                    if not cost_record:
                        monthly_amount = pc.total_amount / 12.0
                        self.session.add(
                            ResourceCost(
                                purchase_contract_id=pc.id,
                                period=demo_period,
                                cost_type=cc.category,
                                cost_item=pc.title,
                                amount=monthly_amount,
                                currency=pc.currency or "CNY",
                                capex_opex_flag=pc.capex_opex_flag,
                                vendor_name=pc.vendor_name,
                                cost_code_id=cc.id,
                                source_system="contract_system_init",
                            )
                        )

                    progress.advance(task)

            self.session.flush()
            self.stdout.write("✅ 采购合同初始化完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 采购合同初始化失败: {e}\n")
            return False
