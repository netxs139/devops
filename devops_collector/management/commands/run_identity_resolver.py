"""身份自动治理引擎 (Identity Resolver Engine) 命令。

扫描 mdm_identity_mappings 表中尚未验证或自动生成的身份，
通过模糊匹配与启发式规则计算置信度，并将外部帐号对齐到 HR 金数据用户。
"""

from sqlalchemy import or_

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import IdentityMapping, User


class Command(BaseCommand):
    help = "身份自动治理引擎：将外部帐号对齐到 HR 主数据用户"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="执行实际更新（默认仅为 Dry Run）")
        parser.add_argument("--min-score", type=float, default=0.6, help="最低匹配置信度阈值 (默认: 0.6)")

    def handle(self, *args, **options):
        apply_changes = options.get("apply", False)
        min_score = options.get("min_score", 0.6)

        if not apply_changes:
            self.stdout.write("[Dry Run] 正在以预览模式运行。使用 --apply 保存更改。\n")

        # 1. 预加载所有有效的 MDM 核心用户（金数据）
        mdm_users = (
            self.session.query(User)
            .filter(
                User.is_current,
                User.employee_id.isnot(None),
            )
            .all()
        )
        self.stdout.write(f"已加载 {len(mdm_users)} 条 HR 主数据用户作为匹配基准。\n")

        # 2. 查找待处理的身份映射
        mappings = (
            self.session.query(IdentityMapping)
            .filter(
                or_(
                    IdentityMapping.mapping_status == "PENDING",
                    IdentityMapping.mapping_status == "AUTO",
                    IdentityMapping.confidence_score < 1.0,
                )
            )
            .all()
        )
        self.stdout.write(f"发现 {len(mappings)} 条待治理的身份映射记录。\n")

        updated_count = 0
        with self.get_progress() as progress:
            task = progress.add_task("[cyan]治理身份映射...", total=len(mappings))

            for mapping in mappings:
                best_user, score = self._find_best_match(mapping, mdm_users)

                if best_user and score >= min_score:
                    if mapping.global_user_id != best_user.global_user_id or mapping.confidence_score != score:
                        # self.stdout.write(f"  [Match] {mapping.external_username} -> {best_user.full_name} ({score})\n")

                        if apply_changes:
                            mapping.global_user_id = best_user.global_user_id
                            mapping.confidence_score = score
                            mapping.mapping_status = "AUTO" if score < 0.9 else "VERIFIED"
                        updated_count += 1

                progress.advance(task)

        if apply_changes:
            self.session.flush()
            self.stdout.write(f"✅ 治理完成，已更新 {updated_count} 条映射记录。\n")
        else:
            self.stdout.write("💡 [Dry Run] 预览结束。如需应用，请执行: uv run scripts/cli.py run identity_resolver --apply\n")
            self.stdout.write(f"   预计会更新 {updated_count} 条记录。\n")

        return True

    def _find_best_match(self, mapping, mdm_users):
        """匹配逻辑。"""
        email = (mapping.external_email or "").lower()
        ext_username = (mapping.external_username or "").lower()
        ext_uid = (mapping.external_user_id or "").lower()
        email_prefix = email.split("@")[0] if "@" in email else None

        best_user = None
        max_score = 0.0

        for user in mdm_users:
            current_score = 0.0
            u_email = user.primary_email.lower() if user.primary_email else ""
            u_name = user.full_name.lower() if user.full_name else ""
            u_emp_id = user.employee_id.lower() if user.employee_id else ""

            # 权重规则
            if email and email == u_email:
                current_score = 1.0
            elif ext_uid == u_emp_id:
                current_score = 1.0
            elif email_prefix and (email_prefix in (u_emp_id, user.username.lower() if user.username else "")):
                current_score = 0.8
            elif ext_username == u_name:
                # 姓名匹配，若有公司域邮箱加分
                current_score = 0.7 if (email and "@" in email) else 0.4

            if current_score > max_score:
                max_score = current_score
                best_user = user

            if max_score == 1.0:
                break

        return best_user, max_score
