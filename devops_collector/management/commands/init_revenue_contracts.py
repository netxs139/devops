"""收入合同 (Revenue Contract) 主数据初始化命令。"""

import csv
from datetime import datetime
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import ContractPaymentNode, Product, RevenueContract


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "revenue_contracts.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化收入合同主数据，并生成默认首付款节点"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="收入合同 CSV 路径（默认: docs/assets/sample_data/revenue_contracts.csv）")
        parser.add_argument("--down-pct", type=float, default=30.0, help="首付款比例 %（默认: 30.0）")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV
        down_pct: float = options.get("down_pct", 30.0)

        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过收入合同初始化：未找到 {csv_path}\n")
            return True

        try:
            self.stdout.write(f"开始从 {csv_path} 录入收入合同数据...\n")

            # 预加载产品
            products = {p.product_name: p.id for p in self.session.query(Product).filter(Product.is_current).all()}

            with open(csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]录入收入合同 ({csv_path.name})...", total=len(rows))

                for row in rows:
                    contract_no = row.get("合同编号", "").strip()
                    title = row.get("合同标题", "").strip()
                    client = row.get("客户名称", "").strip()
                    total_str = row.get("总价值", "0")
                    sign_date_str = row.get("签约日期", "").strip()
                    prod_name = row.get("所属产品", "").strip()

                    if not contract_no or not title:
                        progress.advance(task)
                        continue

                    total = float(total_str) if total_str else 0.0
                    sign_date = datetime.strptime(sign_date_str, "%Y-%m-%d") if sign_date_str else datetime.now()
                    p_id = products.get(prod_name)

                    contract = self.session.query(RevenueContract).filter(RevenueContract.contract_no == contract_no).first()
                    if not contract:
                        contract = RevenueContract(contract_no=contract_no)
                        self.session.add(contract)

                    contract.title = title
                    contract.client_name = client
                    contract.total_value = total
                    contract.sign_date = sign_date
                    if p_id:
                        contract.product_id = p_id

                    self.session.flush()

                    # 默认生成首付款节点（幂等：若不存在才创建）
                    if not self.session.query(ContractPaymentNode).filter(ContractPaymentNode.contract_id == contract.id).first():
                        self.session.add(
                            ContractPaymentNode(
                                contract_id=contract.id,
                                node_name="首付款 (Down Payment)",
                                billing_percentage=down_pct,
                                billing_amount=contract.total_value * (down_pct / 100.0),
                                linked_system="manual",
                                is_achieved=False,
                            )
                        )

                    progress.advance(task)

            self.session.flush()
            self.stdout.write("✅ 收入合同初始化完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 收入合同初始化失败: {e}\n")
            return False
