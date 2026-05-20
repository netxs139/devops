"""服务目录与系统注册表管理服务。"""

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from devops_collector.models import BusinessSystem, Organization, Service, SystemRegistry


class CatalogService:
    """处理系统注册表和服务目录的同步和管理。"""

    def __init__(self, session: Session):
        self.session = session

    def _ensure_business_system(self, code: str) -> BusinessSystem | None:
        if not code:
            return None
        system = self.session.query(BusinessSystem).filter_by(code=code).first()
        if not system:
            system = BusinessSystem(code=code, name=code, description=f"Auto-created from Service Catalog: {code}")
            self.session.add(system)
            self.session.flush()
        return system

    def sync_systems_from_csv(self, csv_path: Path, progress_callback=None) -> None:
        """从 CSV 同步系统注册表。"""
        if not csv_path.exists():
            return

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            code = row.get("system_code", "").strip()
            if not code:
                if progress_callback:
                    progress_callback()
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

            if progress_callback:
                progress_callback()

    def sync_services_from_csv(self, csv_path: Path, progress_callback=None) -> None:
        """从 CSV 同步服务目录。"""
        if not csv_path.exists():
            return

        orgs = {o.org_name: o.id for o in self.session.query(Organization).filter_by(is_current=True).all()}

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            name = row.get("服务名称", "").strip()
            if not name:
                if progress_callback:
                    progress_callback()
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

            if progress_callback:
                progress_callback()
