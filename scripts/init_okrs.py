"""初始化系统 OKR 数据。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
import uuid
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.models import OKRKeyResult, OKRObjective, Organization
from scripts.utils import build_user_indexes, resolve_user


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "okrs.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化 OKR 数据。"""
    if not CSV_FILE.exists():
        logger.warning(f"跳过 OKR 初始化：未找到 {CSV_FILE}")
        return True

    try:
        logger.info(f"从 {CSV_FILE} 同步 OKR 数据...")

        # 记录已处理的 Objective，避免重复创建
        processed_objectives = {}

        # 预加载用户索引 (邮箱 + 姓名)
        email_idx, name_idx = build_user_indexes(session)

        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                o_title = row.get("目标标题", "").strip()
                o_desc = row.get("目标描述", "").strip()
                org_name = row.get("组织名称", "").strip()
                owner_val = row.get("负责人", row.get("负责人邮箱", "")).strip()
                period = row.get("周期", "").strip()
                kr_title = row.get("关键结果标题", "").strip()
                target_str = row.get("目标值", "0")
                current_str = row.get("当前值", "0")
                unit = row.get("单位", "").strip()

                if not o_title or not period:
                    continue

                target = float(target_str) if target_str else 0.0
                current = float(current_str) if current_str else 0.0

                # 1. 查找组织和负责人
                org = session.query(Organization).filter(Organization.org_name == org_name).first()
                owner_id = resolve_user(owner_val, email_idx, name_idx, "负责人")

                if not org or not owner_id:
                    continue

                # 2. 获取或创建 Objective
                obj_key = (o_title, period, org.id)
                if obj_key not in processed_objectives:
                    obj = session.query(OKRObjective).filter_by(title=o_title, period=period, org_id=org.id).first()
                    if not obj:
                        obj = OKRObjective(
                            objective_id=f"OBJ-{period}-{uuid.uuid5(uuid.NAMESPACE_DNS, o_title).hex[:8].upper()}",
                            title=o_title,
                            description=o_desc,
                            period=period,
                            owner_id=owner_id,
                            org_id=org.id,
                            status="ACTIVE",
                        )
                        session.add(obj)
                        session.flush()
                    processed_objectives[obj_key] = obj
                else:
                    obj = processed_objectives[obj_key]

                # 3. 创建/更新 Key Results
                kr = session.query(OKRKeyResult).filter_by(objective_id=obj.id, title=kr_title).first()
                progress = round(current / target, 4) if target > 0 else 0.0

                if not kr:
                    kr = OKRKeyResult(
                        objective_id=obj.id,
                        title=kr_title,
                        target_value=target,
                        current_value=current,
                        unit=unit,
                        owner_id=owner_id,
                        progress=progress,
                    )
                    session.add(kr)
                else:
                    kr.current_value = current
                    kr.progress = progress

        session.flush()
        logger.info("✅ OKR 数据初始化完成。")
        return True
    except Exception as e:
        logger.error(f"OKR 初始化失败: {e}")
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
