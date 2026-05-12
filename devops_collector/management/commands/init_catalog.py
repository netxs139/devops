"""初始化系统注册表 (SystemRegistry) 和服务目录 (Service Catalog)。"""

import csv
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models import BusinessSystem, Organization, Service, SystemRegistry


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")


class Command(BaseCommand):
    help = "从 CSV 初始化系统注册表和服务目录"

    def add_arguments(self, parser):
        parser.add_argument("--systems-csv", type=str, help="系统注册表 CSV（默认: mdm_systems_registry.csv）")
        parser.add_argument("--services-csv", type=str, help="服务目录 CSV（默认: mdm_services.csv）")

    def handle(self, *args, **options):
        systems_csv = Path(options["systems_csv"]) if options.get("systems_csv") else SAMPLE_DATA_DIR / "mdm_systems_registry.csv"
        services_csv = Path(options["services_csv"]) if options.get("services_csv") else SAMPLE_DATA_DIR / "mdm_services.csv"

        try:
            self._init_systems(systems_csv)
            self._init_services(services_csv)
            self.session.flush()
            self.stdout.write("✅ 系统注册表和服务目录初始化完成。\n")
            return True
        except Exception as e:
            self.stderr.write(f"❌ 服务目录初始化失败: {e}\n")
            return False

    def _ensure_business_system(self, code: str) -> BusinessSystem | None:
        if not code:
            return None
        system = self.session.query(BusinessSystem).filter_by(code=code).first()
        if not system:
            system = BusinessSystem(code=code, name=code, description=f"Auto-created from Service Catalog: {code}")
            self.session.add(system)
            self.session.flush()
        return system

    def _init_systems(self, csv_path: Path) -> None:
        if not csv_path.exists():
            self.stdout.write(f"WARN: 系统注册表文件不存在: {csv_path}\n")
            return

        self.stdout.write(f"正在从 {csv_path.name} 同步系统注册表...\n")
        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        with self.get_progress() as progress:
            task = progress.add_task(f"[cyan]系统注册表 ({csv_path.name})...", total=len(rows))
            for row in rows:
                code = row.get("system_code", "").strip()
                if not code:
                    progress.advance(task)
                    continue

                system = self.session.query(SystemRegistry).filter_by(system_code=code).first()
                if not system:
                    system = SystemRegistry(system_code=code, system_name=row.get("system_name", code))
                    self.session.add(system)

                system.system_name = row.get("system_name", code)
                system.system_type = row.get("system_type", "").strip()
                system.env_tag = row.get("env_tag", "PROD").strip()
                system.base_url = row.get("base_url", "").strip()
                system.api_version = row.get("api_version", "").strip()
                system.auth_type = row.get("auth_type", "").strip()
                system.is_active = row.get("is_active", "TRUE").strip().upper() == "TRUE"
                system.remarks = row.get("remarks", "").strip()
                self.session.flush()
                progress.advance(task)

    def _init_services(self, csv_path: Path) -> None:
        if not csv_path.exists():
            self.stdout.write(f"WARN: 服务目录文件不存在: {csv_path}\n")
            return

        self.stdout.write(f"正在从 {csv_path.name} 同步服务目录...\n")
        orgs = {o.org_name: o.id for o in self.session.query(Organization).filter_by(is_current=True).all()}

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        with self.get_progress() as progress:
            task = progress.add_task(f"[cyan]服务目录 ({csv_path.name})...", total=len(rows))
            for row in rows:
                name = row.get("服务名称", "").strip()
                if not name:
                    progress.advance(task)
                    continue

                service = self.session.query(Service).filter_by(name=name).first()
                if not service:
                    service = Service(name=name)
                    self.session.add(service)

                service.tier = row.get("服务分级", "").strip()
                service.description = row.get("描述", "").strip()
                service.lifecycle = row.get("生命周期", "production").strip()
                service.component_type = row.get("组件类型", "service").strip()

                org_name = row.get("负责组织", "").strip()
                if org_name in orgs:
                    service.org_id = orgs[org_name]

                bs_code = row.get("所属业务系统代码", "").strip()
                bs = self._ensure_business_system(bs_code)
                if bs:
                    service.system_id = bs.id

                self.session.flush()
                progress.advance(task)
