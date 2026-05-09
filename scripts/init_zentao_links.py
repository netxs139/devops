"""Initialize ZenTao project and product mappings.

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.models import EntityTopology, Product, ProjectMaster, SystemRegistry
from devops_collector.plugins.zentao.models import ZenTaoExecution, ZenTaoProduct


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
PRODUCT_MAP_CSV = SAMPLE_DATA_DIR / "zentao_product_map.csv"
PROJECT_MAP_CSV = SAMPLE_DATA_DIR / "zentao_project_map.csv"


def ensure_system_registry(session: Session):
    """Ensure ZenTao is registered."""
    system = session.query(SystemRegistry).filter_by(system_code="zentao-prod").first()
    if not system:
        system = SystemRegistry(system_code="zentao-prod", system_name="ZenTao ALM", system_type="PROJECT", is_active=True, env_tag="PROD")
        session.add(system)
        session.flush()
    return system


def init_product_links(session: Session, system_id: int):
    """Sync product associations."""
    if not PRODUCT_MAP_CSV.exists():
        logger.warning(f"跳过 ZenTao 产品关联：找不到文件 {PRODUCT_MAP_CSV}")
        return

    logger.info(f"从 {PRODUCT_MAP_CSV} 同步 ZenTao 产品关联...")
    with open(PRODUCT_MAP_CSV, encoding="utf-8-sig") as f:
        lines = [line for line in f if not line.strip().startswith("#")]
        reader = csv.DictReader(lines)
        for row in reader:
            zt_ref = row.get("zentao_product_id", "").strip()
            zt_name = row.get("zentao_product_name", "").strip()
            mdm_ref = row.get("mdm_product_id", "").strip()
            mdm_name = row.get("mdm_product_name", "").strip()

            if not mdm_ref and not mdm_name:
                continue

            # Find MDM Product
            mdm_product = session.query(Product).filter((Product.product_code == mdm_ref) | (Product.product_name == mdm_name)).first()

            if not mdm_product:
                continue

            # Find ZenTao Product
            zt_product = None
            if zt_ref.isdigit():
                zt_product = session.query(ZenTaoProduct).filter_by(id=int(zt_ref)).first()
            if not zt_product:
                zt_product = session.query(ZenTaoProduct).filter((ZenTaoProduct.code == zt_ref) | (ZenTaoProduct.name == zt_name)).first()

            if zt_product:
                # 记录拓扑关系
                topology = (
                    session.query(EntityTopology)
                    .filter_by(system_id=system_id, external_resource_id=str(zt_product.id), element_type="issue-tracker-product")
                    .first()
                )

                if not topology:
                    topology = EntityTopology(
                        system_id=system_id,
                        external_resource_id=str(zt_product.id),
                        resource_name=zt_product.name,
                        element_type="issue-tracker-product",
                        is_active=True,
                    )
                    session.add(topology)

                session.flush()
                logger.debug(f"已关联 ZenTao 产品 '{zt_product.name}' -> MDM '{mdm_product.product_name}'")


def init_project_links(session: Session, system_id: int):
    """Sync project associations."""
    if not PROJECT_MAP_CSV.exists():
        logger.warning(f"跳过 ZenTao 项目关联：找不到文件 {PROJECT_MAP_CSV}")
        return

    logger.info(f"从 {PROJECT_MAP_CSV} 同步 ZenTao 项目关联...")
    with open(PROJECT_MAP_CSV, encoding="utf-8-sig") as f:
        lines = [line for line in f if not line.strip().startswith("#")]
        reader = csv.DictReader(lines)
        for row in reader:
            zt_ref = row.get("zentao_execution_id", "").strip()
            zt_name = row.get("zentao_execution_name", "").strip()
            mdm_ref = row.get("mdm_project_id", "").strip()

            if not mdm_ref:
                continue

            # Find MDM Project
            mdm_project = session.query(ProjectMaster).filter((ProjectMaster.project_code == mdm_ref) | (ProjectMaster.project_name == mdm_ref)).first()

            if not mdm_project:
                continue

            # Find ZenTao Execution Node
            target_node = None
            if zt_ref.isdigit():
                target_node = session.query(ZenTaoExecution).filter_by(id=int(zt_ref)).first()
            if not target_node:
                target_node = session.query(ZenTaoExecution).filter((ZenTaoExecution.code == zt_ref) | (ZenTaoExecution.name == zt_name)).first()

            if target_node:
                topology = (
                    session.query(EntityTopology).filter_by(system_id=system_id, external_resource_id=str(target_node.id), element_type="issue-tracker").first()
                )
                if not topology:
                    topology = EntityTopology(
                        system_id=system_id,
                        external_resource_id=str(target_node.id),
                        resource_name=target_node.name,
                        element_type="issue-tracker",
                        is_active=True,
                    )
                    session.add(topology)
                topology.project_id = mdm_project.id
                session.flush()
                logger.debug(f"已关联 ZenTao 执行 '{target_node.name}' -> MDM '{mdm_project.project_name}'")
            else:
                # 尝试匹配产品级关联
                zt_product = session.query(ZenTaoProduct).filter((ZenTaoProduct.code == zt_ref) | (ZenTaoProduct.name == zt_name)).first()
                if zt_product:
                    product_executions = session.query(ZenTaoExecution).filter_by(product_id=zt_product.id).all()
                    for exec_node in product_executions:
                        topology = (
                            session.query(EntityTopology)
                            .filter_by(system_id=system_id, external_resource_id=str(exec_node.id), element_type="issue-tracker")
                            .first()
                        )
                        if not topology:
                            topology = EntityTopology(
                                system_id=system_id,
                                external_resource_id=str(exec_node.id),
                                resource_name=exec_node.name,
                                element_type="issue-tracker",
                                is_active=True,
                            )
                            session.add(topology)
                        topology.project_id = mdm_project.id
                    session.flush()


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化 ZenTao 关联映射。"""
    try:
        system = ensure_system_registry(session)
        init_product_links(session, system.id)
        init_project_links(session, system.id)
        session.flush()
        logger.info("✅ ZenTao 关联映射初始化完成。")
        return True
    except Exception as e:
        logger.error(f"ZenTao 关联初始化失败: {e}")
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
