"""产品主数据管理服务 (Product Service)。"""

import logging

from sqlalchemy.orm import Session

from devops_collector.models.base_models import Organization, Product


logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, session: Session):
        self.session = session

    def sync_products_from_csv(self, csv_path, progress_callback=None):
        """从 CSV 同步产品目录。"""
        import csv

        from devops_collector.core.management import build_user_indexes, resolve_user

        email_idx, name_idx = build_user_indexes(self.session)
        orgs = {o.org_name: o.id for o in self.session.query(Organization).filter_by(is_current=True).all()}

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            p_id = row.get("产品ID", "").strip() or row.get("product_id", "").strip()
            p_name = row.get("产品名称", "").strip() or row.get("product_name", "").strip()
            owner_team_name = row.get("归属中心", "").strip()
            manager_val = row.get("负责人", "").strip()

            if not p_id or not p_name:
                if progress_callback:
                    progress_callback()
                continue

            org_id = orgs.get(owner_team_name)
            mgr_user_id = resolve_user(manager_val, email_idx, name_idx, "产品负责人")

            existing = self.session.query(Product).filter(Product.product_code == p_id, Product.is_current).first()
            if not existing:
                product = Product(
                    product_code=p_id,
                    product_name=p_name,
                    product_description=f"核心产品: {p_name}",
                    category="Core Product",
                    version_schema="SemVer",
                    lifecycle_status="Active",
                    owner_team_id=org_id,
                    product_manager_id=mgr_user_id,
                )
                self.session.add(product)
            else:
                existing.product_name = p_name
                existing.owner_team_id = org_id
                if mgr_user_id:
                    existing.product_manager_id = mgr_user_id

            if progress_callback:
                progress_callback()

        self.session.flush()
        return len(rows)
