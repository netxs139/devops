import csv
import logging
import uuid
from pathlib import Path

import pypinyin

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Organization, User


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "导入全量员工信息并关联组织架构。"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Path to employees CSV")

    def handle(self, *args, **options):
        csv_path = Path(options.get("csv")) if options.get("csv") else Path("docs/assets/sample_data/employees.csv")

        if not csv_path.exists():
            self.stdout.write(f"ERROR: CSV 文件未找到: {csv_path}\n")
            return False

        try:
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self.stdout.write(f"开始从 {csv_path} 导入员工数据...\n")

                count = 0
                for row in reader:
                    name = row.get("姓名", "").strip()
                    employee_id = row.get("工号", "").strip()
                    center = row.get("中心", "").strip()
                    dept = row.get("部门", "").strip()
                    position = row.get("职位", "").strip()
                    hr_relationship = row.get("人事关系", "").strip() or row.get("hr_relationship", "").strip()
                    csv_email = row.get("邮箱", "").strip()

                    if not name or not employee_id:
                        continue

                    # 1. 确定邮箱和用户名
                    if csv_email:
                        email = csv_email.lower().strip()
                        username = email.split("@")[0]
                    else:
                        username = "".join(pypinyin.lazy_pinyin(name))
                        email = f"{username}@tjhq.com"

                    # 2. 查找所属组织
                    target_org_code = f"DEP-{dept}" if (dept and dept != center) else f"CTR-{center}"
                    org = self.session.query(Organization).filter_by(org_code=target_org_code).first()
                    if not org:
                        org = self.session.query(Organization).filter(Organization.org_name == dept).first()
                        if not org:
                            org = self.session.query(Organization).filter(Organization.org_name == center).first()

                    final_org_id = org.id if org else None

                    # 3. 创建或更新用户
                    user = self.session.query(User).filter_by(employee_id=employee_id).first()

                    if not user:
                        user = self.session.query(User).filter_by(primary_email=email).first()

                    if not user:
                        user = User(
                            global_user_id=uuid.uuid4(),
                            employee_id=employee_id,
                            username=username,
                            full_name=name,
                            primary_email=email,
                            department_id=final_org_id,
                            position=position,
                            hr_relationship=hr_relationship,
                            is_active=True,
                            is_survivor=True,
                            sync_version=1,
                            is_current=True,
                        )
                        self.session.add(user)
                    else:
                        user.employee_id = employee_id
                        user.full_name = name
                        user.primary_email = email
                        user.department_id = final_org_id
                        user.position = position
                        user.hr_relationship = hr_relationship
                        user.is_active = True
                        user.is_current = True

                    count += 1
                    if count % 100 == 0:
                        self.session.flush()
                        self.stdout.write(f"已处理 {count} 条记录...\n")

                self.session.flush()
                self.stdout.write(f"✅ 员工导入已完成！共处理 {count} 条记录。\n")
                return True
        except Exception as e:
            logger.error(f"员工导入失败: {e}")
            return False
