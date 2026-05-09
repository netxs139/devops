"""人工费率表初始化。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.append(os.getcwd())
from devops_collector.models.base_models import LaborRateConfig


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "labor_rates.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化人工费率。"""
    if not CSV_FILE.exists():
        logger.warning(f"跳过人工费率初始化：未找到 {CSV_FILE}")
        return True

    try:
        logger.info(f"从 {CSV_FILE} 加载人工费率...")
        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                level = row.get("职级", "").strip()
                rate_str = row.get("日费率", "0")
                if not level:
                    continue

                rate = float(rate_str)
                obj = session.query(LaborRateConfig).filter_by(job_title_level=level, is_active=True).first()
                if not obj:
                    obj = LaborRateConfig(job_title_level=level)
                    session.add(obj)

                obj.daily_rate = rate
                obj.hourly_rate = rate / 8.0
                obj.currency = "CNY"
                obj.effective_date = datetime.now(UTC)

        session.flush()
        logger.info("✅ 人工费率初始化完成。")
        return True
    except Exception as e:
        logger.error(f"人工费率初始化失败: {e}")
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
