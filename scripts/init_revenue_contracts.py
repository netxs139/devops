"""收入合同 (Revenue Contract) 初始化脚本。

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
from devops_collector.models.base_models import ContractPaymentNode, Product, RevenueContract


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "revenue_contracts.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化收入合同数据。"""
    if not CSV_FILE.exists():
        logger.warning(f"跳过收入合同初始化：未找到 {CSV_FILE}")
        return True

    try:
        logger.info(f"开始从 {CSV_FILE} 录入收入合同数据...")

        # 预加载产品
        products = {p.product_name: p.id for p in session.query(Product).filter(Product.is_current).all()}

        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                contract_no = row.get("合同编号", "").strip()
                title = row.get("合同标题", "").strip()
                client = row.get("客户名称", "").strip()
                total_str = row.get("总价值", "0")
                sign_date_str = row.get("签约日期", "").strip()
                prod_name = row.get("所属产品", "").strip()

                if not contract_no or not title:
                    continue

                total = float(total_str)
                sign_date = datetime.strptime(sign_date_str, "%Y-%m-%d") if sign_date_str else datetime.now()

                p_id = products.get(prod_name)

                contract = session.query(RevenueContract).filter(RevenueContract.contract_no == contract_no).first()
                if not contract:
                    contract = RevenueContract(contract_no=contract_no)
                    session.add(contract)
                    logger.info(f"录入新收入合同: {contract_no}")

                contract.title = title
                contract.client_name = client
                contract.total_value = total
                contract.sign_date = sign_date
                if p_id:
                    contract.product_id = p_id

                session.flush()

                # 默认生成一个首付款节点
                # 检查是否已有节点，避免重复创建（简单逻辑：如果没有节点则创建）
                if not session.query(ContractPaymentNode).filter(ContractPaymentNode.contract_id == contract.id).first():
                    billing_amount = contract.total_value * 0.3
                    node = ContractPaymentNode(
                        contract_id=contract.id,
                        node_name="首付款 (Down Payment)",
                        billing_percentage=30.0,
                        billing_amount=billing_amount,
                        linked_system="manual",
                        is_achieved=False,
                    )
                    session.add(node)

        session.flush()
        logger.info("✅ 收入合同初始化完成。")
        return True
    except Exception as e:
        logger.error(f"收入合同初始化失败: {e}")
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
