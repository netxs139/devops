from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.organization_service import OrganizationService


class Command(BaseCommand):
    help = "组织负责人对齐维护脚本 (Organization Manager Alignment Tool)。解决数据同步顺序导致的负责人缺失。"

    def handle(self, session: Session):
        """现代化对齐入口，直接透传至 OrganizationService。"""
        service = OrganizationService(session)

        with self.get_progress() as progress:
            task = progress.add_task("[cyan]正在执行负责人对齐...", total=None)
            stats = service.realign_all_managers()
            progress.update(task, completed=100)

        self.stdout.write(f"\n对齐完成: 成功 {stats['success']}, 失败 {stats['failed']}\n")
        return stats["failed"] == 0
