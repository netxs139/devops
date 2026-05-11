import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devops_collector.core.identity_manager import IdentityManager
from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Base, Organization, User


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "企业微信身份对齐仿真测试 (Simulation Test)"

    def handle(self, *args, **options):
        self.stdout.write(">>> Starting Simulation Test (v3-Framework)...\n")

        # 使用内存 SQLite 进行仿真
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()

        try:
            self.stdout.write(">>> Phase 1: Importing Organizations (Manager doesn't exist yet)...\n")
            org1 = Organization(
                org_code="wecom_dept_1",
                org_name="研发中心",
                manager_raw_id="zs123",
                is_current=True,
            )
            session.add(org1)
            session.flush()
            self.stdout.write(f"Org created. current manager_user_id: {org1.manager_user_id}\n")

            self.stdout.write(">>> Phase 2: User Data Arrives (HR Sync + WeCom Identity Mapping)...\n")
            global_uid = uuid.uuid4()
            user_zs = User(global_user_id=global_uid, full_name="张三", primary_email="zhangsan@example.com", employee_id="EMP001", is_current=True)
            session.add(user_zs)
            session.flush()

            IdentityManager.get_or_create_user(session, source="wecom", external_id="zs123", email="zhangsan@example.com", employee_id="EMP001")
            session.flush()
            self.stdout.write(f"User synced & Identity mapped. global_uid: {global_uid}\n")

            self.stdout.write(">>> Phase 3: Running Realignment Logic...\n")

            # 由于 realign_org_managers 已迁移为 Command，我们可以模拟它的 handle 逻辑
            # 或者直接在 handle 里调用它。为了仿真独立性，我们手动执行其逻辑核心
            from devops_collector.management.commands.realign_org_managers import Command as AlignCmd

            align_cmd = AlignCmd()
            align_cmd.session = session
            align_cmd.stdout = self.stdout
            align_cmd.handle()

            session.expire_all()
            updated_org = session.query(Organization).filter_by(org_code="wecom_dept_1").first()

            self.stdout.write("\n>>> Final Verification:\n")
            self.stdout.write(f"manager_raw_id: {updated_org.manager_raw_id}\n")
            self.stdout.write(f"manager_user_id: {updated_org.manager_user_id}\n")

            if updated_org.manager_user_id == global_uid:
                self.stdout.write(">>> ✅ SUCCESS: The manager ID was correctly filled after async sync!\n")
                return True
            else:
                self.stdout.write(">>> ❌ FAILURE: Manager ID is still missing.\n")
                return False

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False
        finally:
            session.close()
