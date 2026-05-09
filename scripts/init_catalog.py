"""初始化系统注册表和服务目录。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from devops_collector.models import BusinessSystem, Organization, Service, SystemRegistry


logger = logging.getLogger(__name__)

# 统一资源路径
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
SYSTEMS_CSV = SAMPLE_DATA_DIR / "mdm_systems_registry.csv"
SERVICES_CSV = SAMPLE_DATA_DIR / "mdm_services.csv"


def ensure_business_system(session: Session, code: str) -> BusinessSystem:
    if not code:
        return None
    system = session.query(BusinessSystem).filter_by(code=code).first()
    if not system:
        system = BusinessSystem(code=code, name=code, description=f"Auto-created from Service Catalog: {code}")
        session.add(system)
        session.flush()
    return system


def init_systems(session: Session):
    if not SYSTEMS_CSV.exists():
        logger.warning(f"系统注册表文件不存在: {SYSTEMS_CSV}")
        return

    logger.info(f"正在从 {SYSTEMS_CSV.name} 同步系统注册表...")
    with open(SYSTEMS_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("system_code", "").strip()
            if not code:
                continue

            system = session.query(SystemRegistry).filter_by(system_code=code).first()
            if not system:
                system = SystemRegistry(system_code=code, system_name=row.get("system_name", code))
                session.add(system)

            system.system_name = row.get("system_name", code)
            system.system_type = row.get("system_type", "").strip()
            system.env_tag = row.get("env_tag", "PROD").strip()
            system.base_url = row.get("base_url", "").strip()
            system.api_version = row.get("api_version", "").strip()
            system.auth_type = row.get("auth_type", "").strip()

            is_active_str = row.get("is_active", "TRUE").strip().upper()
            system.is_active = is_active_str == "TRUE"
            system.remarks = row.get("remarks", "").strip()

            session.flush()


def init_services(session: Session):
    if not SERVICES_CSV.exists():
        logger.warning(f"服务目录文件不存在: {SERVICES_CSV}")
        return

    logger.info(f"正在从 {SERVICES_CSV.name} 同步服务目录...")

    # 预加载依赖数据
    orgs = {o.org_name: o.id for o in session.query(Organization).filter_by(is_current=True).all()}

    with open(SERVICES_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("服务名称", "").strip()
            if not name:
                continue

            service = session.query(Service).filter_by(name=name).first()
            if not service:
                service = Service(name=name)
                session.add(service)

            service.tier = row.get("服务分级", "").strip()
            service.description = row.get("描述", "").strip()
            service.lifecycle = row.get("生命周期", "production").strip()
            service.component_type = row.get("组件类型", "service").strip()

            org_name = row.get("负责组织", "").strip()
            if org_name in orgs:
                service.org_id = orgs[org_name]

            bs_code = row.get("所属业务系统代码", "").strip()
            bs = ensure_business_system(session, bs_code)
            if bs:
                service.system_id = bs.id

            session.flush()


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化服务目录。"""
    try:
        init_systems(session)
        init_services(session)
        session.flush()
        logger.info("✅ 系统注册表和服务目录初始化完成。")
        return True
    except Exception as e:
        logger.error(f"服务目录初始化失败: {e}")
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
