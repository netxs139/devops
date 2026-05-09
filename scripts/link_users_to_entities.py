"""员工角色自动分配与业务实体关联脚本 (对齐大宪法规范)。

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
from devops_collector.models import (
    SysRole,
    User,
    UserRole,
)


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
EMP_CSV = SAMPLE_DATA_DIR / "employees.csv"
ORG_CSV = SAMPLE_DATA_DIR / "organizations.csv"

# 职位映射常识
POSITION_ROLE_MAP = {
    "总经理": "EXECUTIVE_MANAGER",
    "副总经理": "EXECUTIVE_MANAGER",
    "总监": "DEPT_MANAGER",
    "经理": "DEPT_MANAGER",
    "测试": "QA_ENGINEER",
    "质量": "QA_ENGINEER",
    "产品": "PRODUCT_MANAGER",
    "工程师": "DEVELOPER",
    "架构": "DEVELOPER",
}


def get_role_by_position(position: str) -> str:
    """基于关键词的行业常识推断角色。"""
    for keyword, role_code in POSITION_ROLE_MAP.items():
        if keyword in position:
            return role_code
    return "VIEWER"


def sync_manager_roles(session: Session):
    """【行业常识】将 organizations.csv 中的负责人自动设为 DEPT_MANAGER。"""
    if not ORG_CSV.exists():
        logger.warning(f"跳过管理器角色同步：找不到文件 {ORG_CSV}")
        return

    role_dept_mgr = session.query(SysRole).filter_by(role_key="DEPT_MANAGER").first()
    if not role_dept_mgr:
        logger.warning("未找到 DEPT_MANAGER 角色，跳过。")
        return

    with open(ORG_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m_email = row.get("负责人邮箱", "").strip().lower()
            if not m_email:
                continue

            user = session.query(User).filter(User.primary_email == m_email, User.is_current).first()
            if user:
                # 检查是否已有关联
                if not session.query(UserRole).filter_by(user_id=user.global_user_id, role_id=role_dept_mgr.id).first():
                    session.add(UserRole(user_id=user.global_user_id, role_id=role_dept_mgr.id))
                    logger.info(f"提升 [{m_email}] 为部门经理角色")


def sync_employee_roles(session: Session):
    """基于职位关键词自动授权。"""
    if not EMP_CSV.exists():
        logger.warning(f"跳过员工角色同步：找不到文件 {EMP_CSV}")
        return
    all_roles = {r.role_key: r for r in session.query(SysRole).all()}

    with open(EMP_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name, pos = row.get("姓名", "").strip(), row.get("职位", "").strip()
            if not name:
                continue

            user = session.query(User).filter(User.full_name == name, User.is_current).first()
            if user:
                rk = get_role_by_position(pos)
                role = all_roles.get(rk)
                if role and not session.query(UserRole).filter_by(user_id=user.global_user_id, role_id=role.id).first():
                    session.add(UserRole(user_id=user.global_user_id, role_id=role.id))


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 行业常识级权限自动分配。"""
    try:
        sync_manager_roles(session)
        sync_employee_roles(session)
        session.flush()
        logger.info("✅ 行业常识级权限自动分配完成。")
        return True
    except Exception as e:
        logger.error(f"角色分配失败: {e}")
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
