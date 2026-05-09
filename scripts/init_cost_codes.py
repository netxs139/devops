"""财务成本科目 (CBS) 初始化脚本。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import os
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.append(os.getcwd())
from devops_collector.models.base_models import CostCode


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "cost_codes.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化成本科目。"""
    if not CSV_FILE.exists():
        logger.warning(f"跳过成本科目初始化：未找到 {CSV_FILE}")
        return True

    try:
        logger.info(f"从 {CSV_FILE} 加载成本科目...")

        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("科目代码", "").strip()
                if not code:
                    continue

                cc = session.query(CostCode).filter_by(code=code).first()
                if not cc:
                    cc = CostCode(code=code)
                    session.add(cc)

                cc.name = row.get("科目名称", "").strip()
                cc.category = row.get("分类", "").strip()
                cc.default_capex_opex = row.get("支出类型", "").strip()
                cc.description = row.get("描述", "").strip()

                # 处理父级 (注意：父级必须在 CSV 中先于子级出现，或者两遍处理)
                parent_code = row.get("父级代码", "").strip()
                if parent_code:
                    parent = session.query(CostCode).filter_by(code=parent_code).first()
                    if parent:
                        cc.parent_id = parent.id

                session.flush()

        logger.info("✅ 成本科目初始化完成。")
        return True
    except Exception as e:
        logger.error(f"成本科目初始化失败: {e}")
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
