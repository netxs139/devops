"""初始化禅道 (ZenTao) 身份映射 (IdentityMapping) 数据。"""

import csv
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models import IdentityMapping, User


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "zentao-user.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化禅道身份映射（工号/Email 优先策略）"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="禅道用户 CSV 路径（默认: docs/assets/sample_data/zentao-user.csv）")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV

        if not csv_path.exists():
            self.stderr.write(f"❌ 找不到禅道用户 CSV 文件: {csv_path}\n")
            return False

        try:
            self.stdout.write("开始同步禅道身份映射数据...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

            count = 0
            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]处理禅道用户映射 ({csv_path.name})...", total=len(rows))

                for row in rows:
                    employee_id = row.get("工号", "").strip()
                    full_name = row.get("姓名", "").strip()
                    email = row.get("邮箱", "").strip()
                    account = email.split("@")[0] if email else None

                    if not employee_id and not email:
                        progress.advance(task)
                        continue

                    user = None

                    # 策略 1: 优先通过工号匹配
                    if employee_id:
                        user = self.session.query(User).filter(User.employee_id == employee_id, User.is_current).first()

                    # 策略 2: 其次通过 Email 匹配
                    if not user and email:
                        user = self.session.query(User).filter(User.primary_email == email.lower(), User.is_current).first()

                    if not user:
                        progress.advance(task)
                        continue

                    external_id = account or email.lower()
                    mapping = self.session.query(IdentityMapping).filter_by(source_system="zentao", external_user_id=external_id).first()

                    if not mapping:
                        mapping = IdentityMapping(
                            global_user_id=user.global_user_id,
                            source_system="zentao",
                            external_user_id=external_id,
                            external_username=full_name,
                            external_email=email.lower() if email else None,
                            mapping_status="VERIFIED",
                            confidence_score=1.0,
                        )
                        self.session.add(mapping)
                        count += 1
                    else:
                        mapping.global_user_id = user.global_user_id
                        mapping.mapping_status = "VERIFIED"
                        mapping.confidence_score = 1.0

                    progress.advance(task)

            self.session.flush()
            self.stdout.write(f"✅ 禅道身份映射初始化完成！共建立/更新 {count} 条关联。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 禅道映射初始化失败: {e}\n")
            return False
