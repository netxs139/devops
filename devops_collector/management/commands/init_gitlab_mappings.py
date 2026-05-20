"""初始化 GitLab 身份映射 (IdentityMapping) 数据。"""

import csv
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.identity_mapping_service import IdentityMappingService


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "gitlab-user.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化 GitLab 身份映射（Email 优先策略）"

    def handle(
        self,
        session: Session,
        csv_path: Annotated[Path, typer.Option("--csv", help="GitLab 用户 CSV 路径")] = DEFAULT_CSV,
    ):
        if not csv_path.exists():
            self.stderr.write(f"❌ 找不到 GitLab 用户 CSV 文件: {csv_path}\n")
            return False

        service = IdentityMappingService(session)

        try:
            self.stdout.write("=" * 60 + "\n")
            self.stdout.write(f"开始 GitLab 身份映射初始化 (via Service: {csv_path})\n")
            self.stdout.write("=" * 60 + "\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                row_count = sum(1 for _ in csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]处理 GitLab 用户映射 ({csv_path.name})...", total=row_count)
                stats = service.sync_gitlab_mappings(csv_path, progress_callback=lambda: progress.advance(task))

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
