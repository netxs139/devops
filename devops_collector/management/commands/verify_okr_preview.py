import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Base, OKRObjective, User
from devops_collector.services.admin_service import AdminService


class Command(BaseCommand):
    help = "验证 OKR 预览逻辑 (支持内存模式与物理库模式)。"

    def add_arguments(self, parser):
        parser.add_argument("--real-db", action="store_true", help="Use real database instead of in-memory SQLite")

    def handle(self, *args, **options):
        if options.get("real_db"):
            self.stdout.write("Running verification on REAL database...\n")
            session = self.session
        else:
            self.stdout.write("Running verification on IN-MEMORY SQLite...\n")
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            session = sessionmaker(bind=engine)()

        try:
            # Setup mock data
            user = User(global_user_id=uuid.uuid4(), full_name="Admin", username="admin", primary_email="admin@test.com")
            session.add(user)
            session.flush()

            obj = OKRObjective(title="Test Objective", owner_id=user.global_user_id, period="2024-Q1", status="ACTIVE", progress=0.5)
            session.add(obj)
            session.flush()

            service = AdminService(session)
            results = service.list_okrs()

            self.stdout.write(f"Results count: {len(results)}\n")
            if len(results) > 0:
                self.stdout.write(f"First result: {results[0]['title']}, status: {results[0]['status']}, period: {results[0]['period']}\n")
                if results[0]["owner_name"] == "Admin" and results[0]["period"] == "2024-Q1":
                    self.stdout.write("✅ OKR Preview logic verified successfully!\n")
                    return True
                else:
                    self.stdout.write("❌ Logic Error: Owner or Period mismatch!\n")
                    return False
            else:
                self.stdout.write("❌ Error: No results found!\n")
                return False
        finally:
            if not options.get("real_db"):
                session.close()
