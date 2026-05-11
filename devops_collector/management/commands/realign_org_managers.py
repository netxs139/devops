import logging

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import IdentityMapping, Organization, User


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "组织负责人对齐维护脚本 (Organization Manager Alignment Tool)。解决数据同步顺序导致的负责人缺失。"

    def handle(self, *args, **options):
        # 查找所有设置了原始标识但尚未绑定全局 ID 的组织
        unaligned = (
            self.session.query(Organization)
            .filter(Organization.manager_user_id.is_(None), Organization.manager_raw_id.is_not(None), Organization.is_current)
            .all()
        )

        stats = {"success": 0, "failed": 0}
        self.stdout.write(f"发现 {len(unaligned)} 个待对齐组织...\n")

        for org in unaligned:
            raw_id = org.manager_raw_id
            global_user_id = None

            # 策略 1: 映射表
            mapping = self.session.query(IdentityMapping).filter_by(external_user_id=str(raw_id)).first()
            if mapping:
                global_user_id = mapping.global_user_id

            # 策略 2: 工号
            if not global_user_id:
                user = self.session.query(User).filter_by(employee_id=raw_id, is_current=True).first()
                if user:
                    global_user_id = user.global_user_id

            # 策略 3: 邮箱
            if not global_user_id and "@" in str(raw_id):
                user = self.session.query(User).filter_by(primary_email=raw_id.lower(), is_current=True).first()
                if user:
                    global_user_id = user.global_user_id

            if global_user_id:
                org.manager_user_id = global_user_id
                stats["success"] += 1
                self.stdout.write(f"✅ 对齐成功: 组织 '{org.org_name}' (标识: '{raw_id}')\n")
            else:
                stats["failed"] += 1
                self.stdout.write(f"⚠️ 对齐失败: 组织 '{org.org_name}' (标识: '{raw_id}') 未找到匹配用户\n")

        self.session.flush()
        self.stdout.write(f"\n对齐完成: 成功 {stats['success']}, 失败 {stats['failed']}\n")
        return stats["failed"] == 0
