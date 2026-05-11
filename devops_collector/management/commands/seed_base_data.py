import csv
import hashlib
import logging
from pathlib import Path

from sqlalchemy import text

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Organization, Product, User


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed base data (Organizations & Products) from CSV files."

    def add_arguments(self, parser):
        parser.add_argument("--org-csv", type=str, help="Path to organizations CSV")
        parser.add_argument("--product-csv", type=str, help="Path to products CSV")

    def handle(self, *args, **options):
        docs_dir = Path("docs/assets/sample_data")
        org_csv = Path(options.get("org_csv")) if options.get("org_csv") else docs_dir / "organizations.csv"
        product_csv = Path(options.get("product_csv")) if options.get("product_csv") else docs_dir / "products.csv"

        try:
            self._seed_organizations(org_csv)
            self._seed_products(product_csv)
            self.stdout.write("✅ Base data seeding complete.\n")
            return True
        except Exception as e:
            logger.error(f"Base data seeding failed: {e}")
            return False

    def _generate_org_code(self, name: str) -> str:
        return "ORG_" + hashlib.md5(name.encode()).hexdigest()[:8].upper()

    def _seed_organizations(self, csv_path: Path):
        self.stdout.write(f"\n--- Seeding Organizations from {csv_path} ---\n")

        if not csv_path.exists():
            self.stdout.write(f"WARN: {csv_path} not found, skipping.\n")
            return

        # Clear existing
        self.session.execute(text("UPDATE mdm_identities SET department_id = NULL"))
        self.session.execute(text("UPDATE mdm_products SET owner_team_id = NULL"))
        self.session.execute(text("UPDATE mdm_organizations SET parent_id = NULL"))
        self.session.execute(text("DELETE FROM mdm_organizations"))
        self.session.flush()

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        users = {u.full_name: u for u in self.session.query(User).filter(User.is_current).all()}
        created_orgs = {}
        stats = {"created": 0}

        root_code = self._generate_org_code("公司")
        root_org = self.session.query(Organization).filter_by(org_code=root_code, is_current=True).first()
        if not root_org:
            root_org = Organization(org_code=root_code, org_name="公司", org_level=1, is_active=True, is_current=True, sync_version=1)
            self.session.add(root_org)
            self.session.flush()

        created_orgs["公司"] = root_org.id
        stats["created"] += 1

        for row in rows:
            tixi = (row.get("所属体系") or "").strip()
            center = (row.get("中心") or "").strip()
            dept = (row.get("部门") or "").strip()
            manager_name = (row.get("负责人") or "").strip()

            if not center:
                continue

            if center not in created_orgs:
                mgr_uid = users[manager_name].global_user_id if not dept and manager_name in users else None
                org = Organization(
                    org_code=self._generate_org_code(center),
                    org_name=center,
                    org_level=2,
                    parent_id=root_org.id,
                    manager_user_id=mgr_uid,
                    business_line=tixi or None,
                    is_active=True,
                    is_current=True,
                    sync_version=1,
                )
                self.session.add(org)
                self.session.flush()
                stats["created"] += 1
                created_orgs[center] = org.id

            if dept and dept not in created_orgs:
                mgr_uid = users[manager_name].global_user_id if manager_name in users else None
                org = Organization(
                    org_code=self._generate_org_code(dept),
                    org_name=dept,
                    org_level=3,
                    parent_id=created_orgs.get(center),
                    manager_user_id=mgr_uid,
                    business_line=tixi or None,
                    is_active=True,
                    is_current=True,
                    sync_version=1,
                )
                self.session.add(org)
                self.session.flush()
                stats["created"] += 1
                created_orgs[dept] = org.id

        self.stdout.write(f"Organizations: {stats['created']} created.\n")

    def _seed_products(self, csv_path: Path):
        self.stdout.write(f"\n--- Seeding Products from {csv_path} ---\n")
        if not csv_path.exists():
            return

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        org_name_map = {o.org_name: o.id for o in self.session.query(Organization).filter(Organization.is_current).all()}
        stats = {"created": 0, "skipped": 0}

        for row in rows:
            code = (row.get("PRODUCT_ID") or row.get("product_id") or "").strip()
            name = (row.get("产品名称") or row.get("product_name") or "").strip()
            if not code or not name:
                continue

            if self.session.query(Product).filter(Product.product_code == code, Product.is_current).first():
                stats["skipped"] += 1
                continue

            owner_team_name = (row.get("负责团队") or row.get("owner_team_id") or "").strip() or None
            product = Product(
                product_code=code,
                product_name=name,
                product_description=f"{name} 产品线",
                node_type=(row.get("节点类型") or "APP").strip().upper(),
                category=(row.get("产品分类") or "").strip() or None,
                version_schema=(row.get("version_schema") or "SemVer").strip(),
                owner_team_id=org_name_map.get(owner_team_name) if owner_team_name else None,
                lifecycle_status="active",
                is_current=True,
            )
            self.session.add(product)
            stats["created"] += 1

        self.stdout.write(f"Products: {stats['created']} created, {stats['skipped']} skipped.\n")
