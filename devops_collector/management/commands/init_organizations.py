import csv
import logging
from pathlib import Path

from devops_collector.core.management import BaseCommand, build_user_indexes, resolve_user
from devops_collector.models.base_models import Organization


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "初始化组织架构及负责人数据。"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Path to organizations CSV")

    def handle(self, *args, **options):
        csv_path = Path(options.get("csv")) if options.get("csv") else Path("docs/assets/sample_data/organizations.csv")

        if not csv_path.exists():
            self.stdout.write(f"WARN: {csv_path} not found, skipping.\n")
            return True

        self.stdout.write(f"开始从 {csv_path} 同步组织架构...\n")

        try:
            # 预加载用户索引 (邮箱 + 姓名)
            email_idx, name_idx = build_user_indexes(self.session)

            # 创建公司根节点 (L1)
            root_code = "ORG-HQ"
            root_org = self.session.query(Organization).filter_by(org_code=root_code).first()
            if not root_org:
                root_org = Organization(org_code=root_code, org_name="HQ", org_level=1, is_current=True)
                self.session.add(root_org)
                self.session.flush()
                self.stdout.write(f"创建公司根节点: {root_code}\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    system = row.get("体系", "").strip()
                    center = row.get("中心", "").strip()
                    dept = row.get("部门", "").strip()
                    manager_val = row.get("负责人", row.get("负责人邮箱", "")).strip()

                    manager_id = resolve_user(manager_val, email_idx, name_idx, "负责人")

                    parent_org = root_org

                    # 1. 中心层级 (L2) - 挂在公司根节点下
                    if center:
                        org_code_l2 = f"CTR-{center}"
                        org_l2 = self.session.query(Organization).filter_by(org_code=org_code_l2).first()
                        if not org_l2:
                            org_l2 = Organization(
                                org_code=org_code_l2, org_name=center, org_level=2, parent_id=root_org.id, business_line=system, is_current=True
                            )
                            self.session.add(org_l2)
                            self.session.flush()

                        # 中心级负责人 (无部门的行)
                        if manager_id and not dept:
                            org_l2.manager_user_id = manager_id

                        parent_org = org_l2

                    # 2. 部门层级 (L3) - 挂在中心下
                    if dept:
                        org_code_l3 = f"DEP-{dept}"
                        org_l3 = self.session.query(Organization).filter_by(org_code=org_code_l3).first()
                        if not org_l3:
                            org_l3 = Organization(
                                org_code=org_code_l3, org_name=dept, org_level=3, parent_id=parent_org.id, business_line=system, is_current=True
                            )
                            self.session.add(org_l3)
                            self.session.flush()

                        if manager_id:
                            org_l3.manager_user_id = manager_id

            self.session.flush()
            self.stdout.write("✅ 组织架构同步完成！\n")
            return True
        except Exception as e:
            logger.error(f"组织架构同步失败: {e}")
            return False
