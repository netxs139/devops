import logging
import sys
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devops_collector.core.identity_manager import IdentityManager
from devops_collector.models.base_models import Base, Organization, User
from scripts.maintenance.realign_org_managers import realign_org_managers


# 强制输出到标准输�?logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
logger = logging.getLogger("TestAlignment")

print(">>> Starting Simulation Test (v2)...")

# 使用内存 SQLite
engine = create_engine("sqlite:///:memory:")
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def simulate_wecom_alignment():
    session = Session()
    try:
        print(">>> Phase 1: Importing Organizations (Manager doesn't exist yet)...")
        org1 = Organization(
            org_code="wecom_dept_1",
            org_name="研发中心",
            manager_raw_id="zs123",  # 暂存 ID (WeCom UserID)
            is_current=True,
        )
        session.add(org1)
        session.commit()
        print(f"Org created. current manager_user_id: {org1.manager_user_id}")

        print(">>> Phase 2: User Data Arrives (HR Sync + WeCom Identity Mapping)...")

        # 2.1 模拟 HR 系统同步了“张三”这个主数据
        global_uid = uuid.uuid4()
        user_zs = User(global_user_id=global_uid, full_name="张三", primary_email="zhangsan@example.com", employee_id="EMP001", is_current=True)
        session.add(user_zs)
        session.flush()

        # 2.2 模拟企业微信同步时，通过 IdentityManager 建立了映射关�?        # 我们使用工号 EMP001 把企业微信账�?zs123 关联�?global_uid
        IdentityManager.get_or_create_user(session, source="wecom", external_id="zs123", email="zhangsan@example.com", employee_id="EMP001")
        session.commit()
        print(f"User synced & Identity mapped. global_uid: {global_uid}")

        print(">>> Phase 3: Running Realignment Script...")
        stats = realign_org_managers(session)
        print(f"Alignment result: {stats}")

        session.expire_all()
        updated_org = session.query(Organization).filter_by(org_code="wecom_dept_1").first()

        print("\n>>> Final Verification:")
        print(f"manager_raw_id: {updated_org.manager_raw_id}")
        print(f"manager_user_id: {updated_org.manager_user_id}")

        if updated_org.manager_user_id == global_uid:
            print(">>> �?SUCCESS: The manager ID was correctly filled after async sync!")
        else:
            print(">>> �?FAILURE: Manager ID is still missing.")

    except Exception as e:
        import traceback

        print(f">>> ERROR: {e}")
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    simulate_wecom_alignment()
