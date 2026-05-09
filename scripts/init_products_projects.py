"""初始化产品与项目主数据。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from devops_collector.models import (
    EntityTopology,
    Organization,
    Product,
    ProjectMaster,
    ProjectProductRelation,
    SystemRegistry,
)
from scripts.utils import build_user_indexes, resolve_user


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
PRD_CSV = SAMPLE_DATA_DIR / "products.csv"
PROJ_CSV = SAMPLE_DATA_DIR / "projects.csv"


def ensure_system_registry(session: Session, code="gitlab-prod", name="生产环境GitLab"):
    system = session.query(SystemRegistry).filter_by(system_code=code).first()
    if not system:
        system = SystemRegistry(system_code=code, system_name=name, system_type="VCS", is_active=True)
        session.add(system)
        session.flush()
    return system


def init_products(session: Session):
    if not PRD_CSV.exists():
        logger.warning(f"跳过产品初始化：找不到文件 {PRD_CSV}")
        return {}

    logger.info(f"从 {PRD_CSV} 同步产品主数据...")
    prod_map_id = {}  # code -> Integer ID

    # 预加载组织和用户索引
    orgs = {o.org_name: o.id for o in session.query(Organization).filter_by(is_current=True).all()}
    email_idx, name_idx = build_user_indexes(session)

    product_rows = []
    with open(PRD_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("产品名称", row.get("PRODUCT_NAME", "")).strip()
            if not name:
                continue

            # 业务主键
            prod_code = row.get("PRODUCT_ID", "").strip()
            if not prod_code:
                prod_code = f"PRD-{uuid.uuid5(uuid.NAMESPACE_DNS, name).hex[:8].upper()}"

            # 创建/更新产品对象
            product = session.query(Product).filter_by(product_code=prod_code).first()
            if not product:
                product = Product(product_code=prod_code, product_name=name, product_description=name, version_schema="SemVer", is_current=True)
                session.add(product)

            # 更新属性
            product.product_name = name
            product.node_type = row.get("节点类型", row.get("node_type", "APP")).strip().upper()
            product.category = row.get("产品分类", row.get("category", "")).strip()

            # 处理关联团队
            team_name = row.get("负责团队", row.get("owner_team_id", "")).strip()
            if team_name in orgs:
                product.owner_team_id = orgs[team_name]
            elif team_name:
                org_by_code = session.query(Organization).filter_by(org_code=team_name).first()
                if org_by_code:
                    product.owner_team_id = org_by_code.id

            # 人员解析
            for csv_col, attr in [
                ("产品经理", "product_manager_id"),
                ("开发经理", "dev_lead_id"),
                ("测试经理", "qa_lead_id"),
                ("发布经理", "release_lead_id"),
            ]:
                val = row.get(csv_col, "").strip()
                uid = resolve_user(val, email_idx, name_idx, csv_col)
                if uid:
                    setattr(product, attr, uid)

            session.flush()
            prod_map_id[prod_code] = product.id
            prod_map_id[name] = product.id
            product_rows.append((product, row))

    # 解析父级关系
    for product, row in product_rows:
        parent_ref = row.get("上级产品ID", row.get("parent_product_id", "")).strip()
        if parent_ref:
            parent_id = prod_map_id.get(parent_ref)
            if parent_id and parent_id != product.id:
                product.parent_product_id = parent_id

    session.flush()
    return prod_map_id


def init_projects(session: Session, prod_map_id):
    if not PROJ_CSV.exists():
        logger.warning(f"跳过项目初始化：找不到文件 {PROJ_CSV}")
        return

    logger.info(f"从 {PROJ_CSV} 同步项目主数据...")

    email_idx, name_idx = build_user_indexes(session)
    orgs_by_name = {o.org_name: o.id for o in session.query(Organization).filter_by(is_current=True).all()}

    with open(PROJ_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code_val = row.get("项目代号", "").strip()
            name = row.get("项目名称", "").strip()
            prod_name = row.get("所属产品", "").strip()

            if not code_val or not name:
                continue

            proj_code = f"PROJ-{code_val}"
            project = session.query(ProjectMaster).filter_by(project_code=proj_code).first()
            if not project:
                project = ProjectMaster(project_code=proj_code, project_name=name, status="ACTIVE", is_current=True)
                session.add(project)

            # 关联部门
            dept_name = row.get("负责部门", "").strip()
            if dept_name in orgs_by_name:
                project.org_id = orgs_by_name[dept_name]
            elif dept_name:
                org_by_code = session.query(Organization).filter_by(org_code=dept_name).first()
                if org_by_code:
                    project.org_id = org_by_code.id

            # 关联代码仓库
            repo_url = row.get("主代码仓库URL", "").strip()
            if repo_url:
                system = ensure_system_registry(session)
                session.flush()
                topology = session.query(EntityTopology).filter_by(project_id=project.id, external_resource_id=repo_url, element_type="source-code").first()
                if not topology:
                    topology = EntityTopology(
                        project_id=project.id,
                        system_id=system.id,
                        external_resource_id=repo_url,
                        resource_name=urlparse(repo_url).path.strip("/").removesuffix(".git"),
                        element_type="source-code",
                        is_active=True,
                    )
                    session.add(topology)

            # 关联项目成员
            for csv_col, attr in [
                ("项目经理", "pm_user_id"),
                ("产品经理", "product_owner_id"),
                ("开发经理", "dev_lead_id"),
                ("测试经理", "qa_lead_id"),
                ("发布经理", "release_lead_id"),
            ]:
                val = row.get(csv_col, "").strip()
                uid = resolve_user(val, email_idx, name_idx, csv_col)
                if uid:
                    setattr(project, attr, uid)

            session.flush()
            # 建立产品关联
            target_prod_id = prod_map_id.get(prod_name)
            if target_prod_id:
                rel = session.query(ProjectProductRelation).filter_by(project_id=project.id, product_id=target_prod_id).first()
                if not rel and project.org_id:
                    session.add(
                        ProjectProductRelation(
                            project_id=project.id,
                            product_id=target_prod_id,
                            org_id=project.org_id,
                            relation_type="PRIMARY",
                        )
                    )
    session.flush()


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化产品与项目主数据。"""
    try:
        pm = init_products(session)
        init_projects(session, pm)
        logger.info("产品与项目主数据同步完成！")
        return True
    except Exception as e:
        logger.error(f"产品与项目同步失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
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
