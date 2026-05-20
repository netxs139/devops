"""财务与成本代码相关服务。"""

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from devops_collector.models.base_models import CostCode


class FinanceService:
    """处理财务维度的数据初始化和同步。"""

    def __init__(self, session: Session):
        self.session = session

    def sync_cost_codes(self, csv_path: Path, progress_callback=None) -> None:
        """从 CSV 同步成本科目 (CBS)。"""
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("科目代码", "").strip()
                if not code:
                    if progress_callback:
                        progress_callback()
                    continue

                cc = self.session.query(CostCode).filter_by(code=code).first()
                if not cc:
                    cc = CostCode(code=code)
                    self.session.add(cc)

                cc.name = row.get("科目名称", "").strip()
                cc.category = row.get("分类", "").strip()
                cc.default_capex_opex = row.get("支出类型", "").strip()
                cc.description = row.get("描述", "").strip()

                parent_code = row.get("父级代码", "").strip()
                if parent_code:
                    parent = self.session.query(CostCode).filter_by(code=parent_code).first()
                    if parent:
                        cc.parent_id = parent.id

                self.session.flush()

                if progress_callback:
                    progress_callback()

    def sync_labor_rates(self, csv_path: Path, progress_callback=None) -> None:
        """从 CSV 同步人工费率。"""
        from datetime import UTC, datetime

        from devops_collector.models.base_models import LaborRateConfig

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                level = row.get("职级", "").strip()
                rate_str = row.get("日费率", "0")
                if not level:
                    if progress_callback:
                        progress_callback()
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

                if progress_callback:
                    progress_callback()

        self.session.flush()

    def sync_purchase_contracts(self, csv_path: Path, demo_period: str, progress_callback=None) -> None:
        """从 CSV 初始化采购合同主数据，并生成演示流水记录。"""
        from datetime import datetime

        from devops_collector.models.base_models import CostCode, PurchaseContract, ResourceCost

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

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
                if progress_callback:
                    progress_callback()
                continue

            total = float(total_str) if total_str else 0.0
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else datetime.now()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime.now()

            cc = self.session.query(CostCode).filter(CostCode.code == cost_code_str).first()
            if not cc:
                if progress_callback:
                    progress_callback()
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

            # 生成演示流水
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

            if progress_callback:
                progress_callback()

        self.session.flush()

    def sync_revenue_contracts(self, csv_path: Path, down_pct: float, progress_callback=None) -> None:
        """从 CSV 初始化收入合同主数据，并生成默认首付款节点。"""
        from datetime import datetime

        from devops_collector.models.base_models import ContractPaymentNode, Product, RevenueContract

        products = {p.product_name: p.id for p in self.session.query(Product).filter(Product.is_current).all()}

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            contract_no = row.get("合同编号", "").strip()
            title = row.get("合同标题", "").strip()
            client = row.get("客户名称", "").strip()
            total_str = row.get("总价值", "0")
            sign_date_str = row.get("签约日期", "").strip()
            prod_name = row.get("所属产品", "").strip()

            if not contract_no or not title:
                if progress_callback:
                    progress_callback()
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

            if progress_callback:
                progress_callback()

        self.session.flush()
