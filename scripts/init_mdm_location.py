"""初始化 MDM_LOCATION 表并加载位置数据。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from devops_collector.models import Location


logger = logging.getLogger(__name__)

# 统一资源路径
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "locations.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 从 CSV 加载地理位置数据。"""
    if not CSV_FILE.exists():
        logger.warning(f"跳过位置初始化：未找到 {CSV_FILE}")
        return True

    try:
        logger.info(f"从 {CSV_FILE} 加载地理位置...")
        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                loc_id = row.get("ID", "").strip()
                if not loc_id:
                    continue

                loc = session.query(Location).filter_by(location_code=loc_id).first()
                if not loc:
                    loc = Location(location_code=loc_id)
                    session.add(loc)

                loc.location_name = row.get("全称", "").strip()
                loc.short_name = row.get("名称", "").strip()
                loc.region = row.get("大区", "").strip()
                loc.code = row.get("编码", "").strip()
                loc.location_type = "province" if loc_id != "000000" else "region"
                loc.is_active = True

        session.flush()
        logger.info("✅ 地理位置 (CSV) 初始化完成。")
        return True
    except Exception as e:
        logger.error(f"位置初始化失败: {e}")
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
