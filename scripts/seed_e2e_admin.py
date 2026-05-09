"""Seed an E2E test user with SYSTEM_ADMIN role.

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import os
import sys
import uuid
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.auth.auth_service import auth_get_password_hash
from devops_collector.models.base_models import SysRole, User, UserCredential, UserRole


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 播种 E2E 测试管理员。"""
    try:
        email = os.getenv("E2E_TEST_USER_EMAIL", "e2e_test@example.com")
        password = os.getenv("E2E_TEST_USER_PASSWORD", "e2e_test_password")

        # Check if user exists
        user = session.query(User).filter_by(primary_email=email).first()
        if not user:
            user = User(
                global_user_id=uuid.uuid4(),
                employee_id="E2E-ADMIN",
                username="e2e_admin",
                full_name="E2E Test Administrator",
                primary_email=email,
                is_active=True,
                is_current=True,
                sync_version=1,
            )
            session.add(user)
            session.flush()

            cred = UserCredential(user_id=user.global_user_id, password_hash=auth_get_password_hash(password))
            session.add(cred)
        else:
            user.is_active = True

        # Ensure SYSTEM_ADMIN role
        admin_role = session.query(SysRole).filter_by(role_key="SYSTEM_ADMIN").first()
        if not admin_role:
            admin_role = SysRole(role_key="SYSTEM_ADMIN", role_name="系统管理员", status=True)
            session.add(admin_role)
            session.flush()

        # Link role
        link = session.query(UserRole).filter_by(user_id=user.global_user_id, role_id=admin_role.id).first()
        if not link:
            link = UserRole(user_id=user.global_user_id, role_id=admin_role.id)
            session.add(link)

        session.flush()
        return True
    except Exception as e:
        print(f"Seed E2E Admin failed: {e}")
        return False


def main():
    from sqlalchemy import create_engine

    from devops_collector.config import settings

    engine = create_engine(settings.database.uri)
    with Session(engine) as session:
        if execute_command(session):
            session.commit()


if __name__ == "__main__":
    main()
