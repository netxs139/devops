"""导入全量员工信息并关联组织架构。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
import uuid
from pathlib import Path

import pypinyin
from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from devops_collector.models import Organization, User


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
CSV_FILE = SAMPLE_DATA_DIR / "employees.csv"


def to_pinyin(name):
    """将中文姓名转换为拼音（全拼，无空格）。"""
    return "".join(pypinyin.lazy_pinyin(name))


def get_org_id(center, dept):
    """根据中心和部门名称推断组织 ID。"""
    if not dept or dept == center:
        return f"CTR-{center}"
    return f"DEP-{dept}"


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 从 CSV 导入全量员工数据。"""
    if not CSV_FILE.exists():
        logger.error(f"CSV 文件未找到: {CSV_FILE}")
        return False

    try:
        with open(CSV_FILE, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            logger.info(f"开始从 {CSV_FILE} 导入员工数据...")

            count = 0
            for row in reader:
                name = row.get("姓名", "").strip()
                employee_id = row.get("工号", "").strip()
                center = row.get("中心", "").strip()
                dept = row.get("部门", "").strip()
                position = row.get("职位", "").strip()
                hr_relationship = row.get("人事关系", "").strip() or row.get("hr_relationship", "").strip()
                csv_email = row.get("邮箱", "").strip()

                if not name or not employee_id:
                    continue

                # 1. 确定邮箱和用户名
                if csv_email:
                    email = csv_email.lower().strip()
                    username = email.split("@")[0]
                else:
                    username = to_pinyin(name)
                    email = f"{username}@tjhq.com"

                # 2. 查找所属组织
                target_org_code = get_org_id(center, dept)
                org = session.query(Organization).filter_by(org_code=target_org_code).first()
                if not org:
                    org = session.query(Organization).filter(Organization.org_name == dept).first()
                    if not org:
                        org = session.query(Organization).filter(Organization.org_name == center).first()

                final_org_id = org.id if org else None

                # 3. 创建或更新用户
                user = session.query(User).filter_by(employee_id=employee_id).first()

                if not user:
                    user = session.query(User).filter_by(primary_email=email).first()

                if not user:
                    user = User(
                        global_user_id=uuid.uuid4(),
                        employee_id=employee_id,
                        username=username,
                        full_name=name,
                        primary_email=email,
                        department_id=final_org_id,
                        position=position,
                        hr_relationship=hr_relationship,
                        is_active=True,
                        is_survivor=True,
                        sync_version=1,
                        is_current=True,
                    )
                    session.add(user)
                    logger.debug(f"准备创建新员工: {name} ({employee_id})")
                else:
                    user.employee_id = employee_id
                    user.full_name = name
                    user.primary_email = email
                    user.department_id = final_org_id
                    user.position = position
                    user.hr_relationship = hr_relationship
                    user.is_active = True
                    user.is_current = True

                count += 1
                if count % 100 == 0:
                    session.flush()
                    logger.info(f"已处理 {count} 条记录...")

            session.flush()
            logger.info(f"✅ 员工导入已完成！共处理 {count} 条记录。")
            return True
    except Exception as e:
        logger.error(f"员工导入失败: {e}")
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
