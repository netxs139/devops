"""初始化产品主数据 (MDM_PRODUCT)。

支持 CLI Phase 2 (Deep Integration) 调用。
从 docs/assets/sample_data/products.csv 动态加载数据。
"""

import csv
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from devops_collector.models import Organization, Product
from scripts.utils import build_user_indexes, resolve_user


logger = logging.getLogger(__name__)

# 统一资源路径
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "products.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化产品主数据。"""
    if not CSV_FILE.exists():
        logger.warning(f"跳过产品初始化：未找到 {CSV_FILE}")
        return True

    try:
        logger.info(f"从 {CSV_FILE} 同步产品目录...")

        # 构建用户双索引 (邮箱 + 姓名)
        email_idx, name_idx = build_user_indexes(session)
        # 预加载组织
        orgs = {o.org_name: o.id for o in session.query(Organization).filter_by(is_current=True).all()}

        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p_id = row.get("产品ID", "").strip() or row.get("product_id", "").strip()
                p_name = row.get("产品名称", "").strip() or row.get("product_name", "").strip()
                owner_team_name = row.get("归属中心", "").strip()
                manager_val = row.get("负责人", "").strip()

                if not p_id or not p_name:
                    continue

                # 1. 匹配所属部门 ID
                org_id = orgs.get(owner_team_name)

                # 2. 查找负责人
                mgr_user_id = resolve_user(manager_val, email_idx, name_idx, "产品负责人")

                # 3. 创建/更新产品
                existing = session.query(Product).filter(Product.product_code == p_id, Product.is_current).first()
                if not existing:
                    product = Product(
                        product_code=p_id,
                        product_name=p_name,
                        product_description=f"核心产品: {p_name}",
                        category="Core Product",
                        version_schema="SemVer",
                        lifecycle_status="Active",
                        org_id=org_id,
                        product_manager_id=mgr_user_id,
                    )
                    session.add(product)
                else:
                    existing.product_name = p_name
                    existing.org_id = org_id
                    if mgr_user_id:
                        existing.product_manager_id = mgr_user_id

        session.flush()
        logger.info("✅ 产品目录初始化完成。")
        return True
    except Exception as e:
        logger.error(f"产品初始化失败: {e}")
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
