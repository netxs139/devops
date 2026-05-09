"""初始化 Nexus 组件与 MDM 产品的关联。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import re
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.models import Product
from devops_collector.plugins.nexus.models import NexusComponent


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
NEXUS_MAP_CSV = SAMPLE_DATA_DIR / "nexus_component_map.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化 Nexus 组件关联。"""
    if not NEXUS_MAP_CSV.exists():
        logger.warning(f"找不到 Nexus 映射文件: {NEXUS_MAP_CSV}")
        return True

    try:
        logger.info(f"从 {NEXUS_MAP_CSV} 同步 Nexus 组件关联...")

        # 1. 预加载产品数据
        all_products = session.query(Product.id, Product.product_code).filter(Product.is_current).all()
        product_code_map = {p.product_code: p.id for p in all_products}
        product_id_set = {p.id for p in all_products}

        # 2. 预加载并编译映射规则
        rules = []
        with open(NEXUS_MAP_CSV, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                group_pat = row.get("group", "").strip()
                name_pat = row.get("name", "").strip()
                mdm_prod_code = row.get("mdm_product_id", "").strip()
                match_type = row.get("match_type", "exact").strip().lower()

                if (not group_pat and not name_pat) or not mdm_prod_code:
                    continue

                actual_pid = None
                if mdm_prod_code in product_code_map:
                    actual_pid = product_code_map[mdm_prod_code]
                elif f"PRD-{mdm_prod_code}" in product_code_map:
                    actual_pid = product_code_map[f"PRD-{mdm_prod_code}"]
                elif mdm_prod_code.isdigit() and int(mdm_prod_code) in product_id_set:
                    actual_pid = int(mdm_prod_code)

                if actual_pid is None:
                    continue

                rule = {
                    "group": group_pat,
                    "name": name_pat,
                    "pid": actual_pid,
                    "type": match_type,
                    "group_re": re.compile(group_pat) if match_type == "regex" and group_pat else None,
                    "name_re": re.compile(name_pat) if match_type == "regex" and name_pat else None,
                }
                rules.append(rule)

        # 3. 遍历组件进行匹配
        all_components = session.query(NexusComponent).all()
        updated_count = 0

        for comp in all_components:
            for rule in rules:
                is_match = True
                if rule["type"] == "regex":
                    if rule["group"] and not rule["group_re"].search(comp.group or ""):
                        is_match = False
                    if rule["name"] and not rule["name_re"].search(comp.name or ""):
                        is_match = False
                else:  # exact
                    if rule["group"] and comp.group != rule["group"]:
                        is_match = False
                    if rule["name"] and comp.name != rule["name"]:
                        is_match = False

                if is_match:
                    if comp.product_id != rule["pid"]:
                        comp.product_id = rule["pid"]
                        updated_count += 1
                    break

        session.flush()
        logger.info(f"✅ Nexus 组件关联初始化完成，共更新 {updated_count} 个组件。")
        return True
    except Exception as e:
        logger.error(f"Nexus 关联初始化失败: {e}")
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
