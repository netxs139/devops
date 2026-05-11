import csv
import logging
from pathlib import Path

from devops_collector.core.management import BaseCommand, build_user_indexes, resolve_user
from devops_collector.models.base_models import Organization, Product


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "初始化产品主数据 (MDM_PRODUCT)。"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Path to products CSV")

    def handle(self, *args, **options):
        csv_path = Path(options.get("csv")) if options.get("csv") else Path("docs/assets/sample_data/products.csv")

        if not csv_path.exists():
            self.stdout.write(f"WARN: {csv_path} not found, skipping.\n")
            return True

        self.stdout.write(f"从 {csv_path} 同步产品目录...\n")

        try:
            # 构建用户双索引 (邮箱 + 姓名)
            email_idx, name_idx = build_user_indexes(self.session)
            # 预加载组织
            orgs = {o.org_name: o.id for o in self.session.query(Organization).filter_by(is_current=True).all()}

            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    p_id = row.get("产品ID", "").strip() or row.get("product_id", "").strip()
                    p_name = row.get("产品名称", "").strip() or row.get("product_name", "").strip()
                    owner_team_name = row.get("归属中心", "").strip()
                    manager_val = row.get("负责人", "").strip()

                    if not p_id or not p_name:
                        continue

                    # 1. 匹配所属部门 ID
                    org_id = orgs.get(owner_team_name)

                    # 2. 查找负责人
                    mgr_user_id = resolve_user(manager_val, email_idx, name_idx, "产品负责人")

                    # 3. 创建/更新产品
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

            self.session.flush()
            self.stdout.write("✅ 产品目录初始化完成。\n")
            return True
        except Exception as e:
            logger.error(f"产品初始化失败: {e}")
            return False
