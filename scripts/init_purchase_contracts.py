"""采购合同 (Purchase Contract) 初始化脚本。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.append(os.getcwd())
from devops_collector.models.base_models import CostCode, PurchaseContract, ResourceCost


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "purchase_contracts.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化采购合同数据。"""
    if not CSV_FILE.exists():
        logger.warning(f"跳过采购合同初始化：未找到 {CSV_FILE}")
        return True

    try:
        logger.info(f"开始从 {CSV_FILE} 录入采购合同数据...")

        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                contract_no = row.get("合同编号", "").strip()
                title = row.get("合同标题", "").strip()
                vendor = row.get("供应商名称", "").strip()
                vendor_id = row.get("供应商ID", "").strip()
                total_str = row.get("总金额", "0")
                start_date_str = row.get("开始日期", "").strip()
                end_date_str = row.get("结束日期", "").strip()
                cost_code = row.get("科目代码", "").strip()
                capex_opex = row.get("支出类型", "").strip()

                if not contract_no or not title:
                    continue

                total = float(total_str)
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else datetime.now()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime.now()

                cc = session.query(CostCode).filter(CostCode.code == cost_code).first()
                if not cc:
                    logger.warning(f"找不到科目代码 {cost_code}，跳过合同 {contract_no}")
                    continue

                pc = session.query(PurchaseContract).filter(PurchaseContract.contract_no == contract_no).first()
                if not pc:
                    pc = PurchaseContract(contract_no=contract_no)
                    session.add(pc)
                    logger.info(f"录入采购合同: [{contract_no}] {title}")

                pc.title = title
                pc.vendor_name = vendor
                pc.vendor_id = vendor_id
                pc.total_amount = total
                pc.start_date = start_date
                pc.end_date = end_date
                pc.cost_code_id = cc.id
                pc.capex_opex_flag = capex_opex
                session.flush()

                # 生成演示流水 (2025-01)
                period = "2025-01"
                cost_record = session.query(ResourceCost).filter(ResourceCost.purchase_contract_id == pc.id, ResourceCost.period == period).first()
                if not cost_record:
                    monthly_amount = pc.total_amount / 12.0
                    cost_record = ResourceCost(
                        purchase_contract_id=pc.id,
                        period=period,
                        cost_type=cc.category,
                        cost_item=pc.title,
                        amount=monthly_amount,
                        currency=pc.currency or "CNY",
                        capex_opex_flag=pc.capex_opex_flag,
                        vendor_name=pc.vendor_name,
                        cost_code_id=cc.id,
                        source_system="contract_system_init",
                    )
                    session.add(cost_record)

        session.flush()
        logger.info("✅ 采购合同初始化完成。")
        return True
    except Exception as e:
        logger.error(f"采购合同初始化失败: {e}")
        return False


def main():
    from sqlalchemy import create_engine

    from devops_collector.config import settings

    engine = create_engine(settings.database.uri)
    with Session(engine) as session:
        if execute_command(session):
            session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
