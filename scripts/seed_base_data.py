"""
Seed base data (Organizations & Products) from docs/assets/sample_data/ CSV files.

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import hashlib
import logging
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from devops_collector.models.base_models import Organization, Product, User


logger = logging.getLogger(__name__)


def generate_org_code(name: str) -> str:
    """Generate a stable, short org_code from name hash."""
    return "ORG_" + hashlib.md5(name.encode()).hexdigest()[:8].upper()


def seed_organizations(session: Session, csv_path: Path):
    """Import hierarchical organizations from CSV."""
    logger.info(f"\n--- Seeding Organizations from {csv_path} ---")

    if not csv_path.exists():
        logger.warning(f"WARN: {csv_path} not found, skipping.")
        return

    # Clear existing organizations to start fresh
    session.execute(text("UPDATE mdm_identities SET department_id = NULL"))
    session.execute(text("UPDATE mdm_products SET owner_team_id = NULL"))
    session.execute(text("UPDATE mdm_organizations SET parent_id = NULL"))
    session.execute(text("DELETE FROM mdm_organizations"))
    session.flush()
    logger.info("Cleared existing organizations.")

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Build user name -> user map for manager lookup
    users = {u.full_name: u for u in session.query(User).filter(User.is_current).all()}

    created_orgs = {}  # org_name -> org_id (Integer ID)
    stats = {"created": 0, "skipped": 0}

    # --- Level 1: 公司 (Root) ---
    root_code = generate_org_code("公司")
    root_org = session.query(Organization).filter_by(org_code=root_code, is_current=True).first()
    if not root_org:
        root_org = Organization(
            org_code=root_code,
            org_name="公司",
            org_level=1,
            parent_id=None,
            business_line=None,
            is_active=True,
            is_current=True,
            sync_version=1,
        )
        session.add(root_org)
        session.flush()

    created_orgs["公司"] = root_org.id
    stats["created"] += 1

    for row in rows:
        tixi = (row.get("所属体系") or "").strip()
        center = (row.get("中心") or "").strip()
        dept = (row.get("部门") or "").strip()
        manager_name = (row.get("负责人") or "").strip()

        if not center:
            continue

        # --- Level 2: 中心 ---
        if center and center not in created_orgs:
            code = generate_org_code(center)
            mgr_uid = None
            if not dept and manager_name and manager_name in users:
                mgr_uid = users[manager_name].global_user_id

            org = Organization(
                org_code=code,
                org_name=center,
                org_level=2,
                parent_id=root_org.id,
                manager_user_id=mgr_uid,
                business_line=tixi or None,
                is_active=True,
                is_current=True,
                sync_version=1,
            )
            session.add(org)
            session.flush()
            stats["created"] += 1
            created_orgs[center] = org.id

        # --- Level 3: 部门 ---
        if dept and dept not in created_orgs:
            code = generate_org_code(dept)
            parent_id = created_orgs.get(center)
            mgr_uid = None
            if manager_name and manager_name in users:
                mgr_uid = users[manager_name].global_user_id

            org = Organization(
                org_code=code,
                org_name=dept,
                org_level=3,
                parent_id=parent_id,
                manager_user_id=mgr_uid,
                business_line=tixi or None,
                is_active=True,
                is_current=True,
                sync_version=1,
            )
            session.add(org)
            session.flush()
            stats["created"] += 1
            created_orgs[dept] = org.id

    session.flush()
    logger.info(f"Organizations: {stats['created']} created.")


def seed_products(session: Session, csv_path: Path):
    """Import products from CSV."""
    logger.info(f"\n--- Seeding Products from {csv_path} ---")

    if not csv_path.exists():
        logger.warning(f"WARN: {csv_path} not found, skipping.")
        return

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Build org name -> org_id map for owner_team lookup
    org_name_map = {o.org_name: o.id for o in session.query(Organization).filter(Organization.is_current).all()}

    stats = {"created": 0, "skipped": 0}

    for row in rows:
        code = (row.get("PRODUCT_ID") or row.get("product_id") or "").strip()
        name = (row.get("产品名称") or row.get("product_name") or "").strip()
        node_type = (row.get("节点类型") or row.get("node_type") or "APP").strip().upper()
        # parent_product_id in model is Integer
        category = (row.get("产品分类") or row.get("category") or "").strip() or None
        version_schema = (row.get("version_schema") or "SemVer").strip()
        owner_team_name = (row.get("负责团队") or row.get("owner_team_id") or "").strip() or None

        owner_team_id = org_name_map.get(owner_team_name) if owner_team_name else None

        if not code or not name:
            continue

        existing = session.query(Product).filter(Product.product_code == code, Product.is_current).first()
        if existing:
            stats["skipped"] += 1
            continue

        product = Product(
            product_code=code,
            product_name=name,
            product_description=f"{name} 产品线",
            node_type=node_type,
            category=category,
            version_schema=version_schema,
            owner_team_id=owner_team_id,
            lifecycle_status="active",
            is_current=True,
        )
        session.add(product)
        stats["created"] += 1

    session.flush()
    logger.info(f"Products: {stats['created']} created, {stats['skipped']} skipped.")


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] Seed base data (Organizations & Products)."""
    docs_dir = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
    try:
        seed_organizations(session, docs_dir / "organizations.csv")
        seed_products(session, docs_dir / "products.csv")
        logger.info("✅ Base data seeding complete.")
        return True
    except Exception as e:
        logger.error(f"Base data seeding failed: {e}")
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
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
