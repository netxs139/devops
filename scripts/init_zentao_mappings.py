"""初始化禅道 (ZenTao) 身份映射 (Identity Mapping) 数据。

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
from devops_collector.models import IdentityMapping, User


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "zentao-user.csv"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化禅道身份映射数据。"""
    if not CSV_FILE.exists():
        logger.error(f"找不到禅道用户 CSV 文件: {CSV_FILE}")
        return False

    try:
        logger.info("开始同步禅道身份映射数据...")

        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0

            for row in reader:
                employee_id = row.get("工号", "").strip()
                full_name = row.get("姓名", "").strip()
                email = row.get("邮箱", "").strip()
                account = email.split("@")[0] if email else None

                if not employee_id and not email:
                    continue

                user = None
                # 1. 优先通过工号匹配
                if employee_id:
                    user = session.query(User).filter(User.employee_id == employee_id, User.is_current).first()

                # 2. 其次通过 Email 匹配
                if not user and email:
                    user = session.query(User).filter(User.primary_email == email.lower(), User.is_current).first()

                if not user:
                    continue

                # 3. 创建映射记录
                external_id = account or email.lower()
                mapping = session.query(IdentityMapping).filter_by(source_system="zentao", external_user_id=external_id).first()

                if not mapping:
                    mapping = IdentityMapping(
                        global_user_id=user.global_user_id,
                        source_system="zentao",
                        external_user_id=external_id,
                        external_username=full_name,
                        external_email=email.lower() if email else None,
                        mapping_status="VERIFIED",
                        confidence_score=1.0,
                    )
                    session.add(mapping)
                    count += 1
                else:
                    mapping.global_user_id = user.global_user_id
                    mapping.mapping_status = "VERIFIED"
                    mapping.confidence_score = 1.0

        session.flush()
        logger.info(f"禅道身份映射初始化完成! 共建立/更新 {count} 条关联。")
        return True
    except Exception as e:
        logger.error(f"禅道映射初始化失败: {e}")
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
