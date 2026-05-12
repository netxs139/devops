"""初始化 GitLab 身份映射 (IdentityMapping) 数据。"""

import csv
from collections import defaultdict
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models import IdentityMapping, User


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "gitlab-user.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化 GitLab 身份映射（Email 优先策略）"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="GitLab 用户 CSV 路径（默认: docs/assets/sample_data/gitlab-user.csv）")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV

        if not csv_path.exists():
            self.stderr.write(f"❌ 找不到 GitLab 用户 CSV 文件: {csv_path}\n")
            return False

        stats: dict[str, int] = defaultdict(int)

        try:
            self.stdout.write("=" * 60 + "\n")
            self.stdout.write("开始 GitLab 身份映射初始化 (Email 优先策略)\n")
            self.stdout.write("=" * 60 + "\n")

            # 预加载员工主数据，按 Email 和姓名建立索引
            all_users = self.session.query(User).filter(User.is_current).all()
            email_index = {u.primary_email.lower(): u for u in all_users if u.primary_email}
            name_index: dict[str, list] = defaultdict(list)
            for u in all_users:
                if u.full_name:
                    name_index[u.full_name].append(u)

            self.stdout.write(f"已加载 {len(email_index)} 条员工邮箱索引\n")
            self.stdout.write(f"已加载 {len(name_index)} 个不同姓名\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]处理 GitLab 用户映射 ({csv_path.name})...", total=len(rows))

                for row in rows:
                    gitlab_id = (row.get("GitLab用户ID", "") or row.get("GITLAB ID", "")).strip()
                    username = (row.get("用户名", "") or row.get("username", "")).strip()
                    full_name = (row.get("全名", "") or row.get("Full name", "")).strip()
                    email = (row.get("Email", "")).strip().lower()

                    if not gitlab_id or not username:
                        stats["skipped_invalid"] += 1
                        progress.advance(task)
                        continue

                    stats["total"] += 1
                    user = None
                    match_method = None

                    # 策略 1: Email 精确匹配
                    if email and email in email_index:
                        user = email_index[email]
                        match_method = "EMAIL"
                        stats["matched_by_email"] += 1

                    # 策略 2: 姓名唯一匹配
                    if not user and full_name:
                        candidates = name_index.get(full_name, [])
                        if len(candidates) == 1:
                            user = candidates[0]
                            match_method = "NAME"
                            stats["matched_by_name"] += 1
                        elif len(candidates) > 1:
                            stats["skipped_duplicate_name"] += 1
                            progress.advance(task)
                            continue

                    if not user:
                        stats["skipped_no_match"] += 1
                        progress.advance(task)
                        continue

                    # 检查是否已绑定其他 gitlab_id
                    mapping = self.session.query(IdentityMapping).filter_by(source_system="gitlab", external_user_id=str(gitlab_id)).first()
                    confidence = 1.0 if match_method == "EMAIL" else 0.8
                    other_mapping = self.session.query(IdentityMapping).filter_by(source_system="gitlab", global_user_id=user.global_user_id).first()

                    if other_mapping and (not mapping or other_mapping.id != mapping.id):
                        stats["skipped_duplicate_user"] += 1
                        progress.advance(task)
                        continue

                    if not mapping:
                        mapping = IdentityMapping(
                            global_user_id=user.global_user_id,
                            source_system="gitlab",
                            external_user_id=str(gitlab_id),
                            external_username=username,
                            external_email=email if email else None,
                            mapping_status="VERIFIED",
                            confidence_score=confidence,
                        )
                        self.session.add(mapping)
                        stats["created"] += 1
                    else:
                        mapping.global_user_id = user.global_user_id
                        mapping.external_username = username
                        mapping.external_email = email if email else mapping.external_email
                        mapping.mapping_status = "VERIFIED"
                        mapping.confidence_score = confidence
                        stats["updated"] += 1

                    progress.advance(task)

            self.session.flush()

            self.stdout.write("=" * 60 + "\n")
            self.stdout.write("GitLab 身份映射初始化完成！\n")
            self.stdout.write(f"  总处理: {stats['total']} | Email匹配: {stats['matched_by_email']} | 姓名匹配: {stats['matched_by_name']}\n")
            self.stdout.write(f"  新建: {stats['created']} | 更新: {stats['updated']}\n")
            self.stdout.write(
                f"  跳过 → 无匹配: {stats['skipped_no_match']} | 重名: {stats['skipped_duplicate_name']} | 账号冲突: {stats['skipped_duplicate_user']} | 无效: {stats['skipped_invalid']}\n"
            )
            return True

        except Exception as e:
            self.stderr.write(f"❌ GitLab 映射初始化失败: {e}\n")
            return False
