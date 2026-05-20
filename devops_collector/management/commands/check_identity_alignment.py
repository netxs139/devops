import logging
from pathlib import Path
from typing import Annotated

import typer

from devops_collector.core.management import BaseCommand
from devops_collector.services.diagnostic_service import DiagnosticService


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "身份对齐检查脚本 (Identity Alignment Checker)"

    def handle(
        self,
        docs_dir: Annotated[Path, typer.Option("--docs-dir", help="文档数据目录")] = Path("docs/assets/sample_data"),
    ):
        employees_csv = docs_dir / "employees.csv"
        gitlab_csv = docs_dir / "gitlab-user.csv"
        zentao_csv = docs_dir / "zentao-user.csv"

        service = DiagnosticService()

        self.stdout.write("=" * 50 + "\n")
        self.stdout.write("身份对齐检查工具 (Identity Alignment Checker)\n")
        self.stdout.write("=" * 50 + "\n")

        # 1. 加载员工主数据
        self.stdout.write("\n正在加载员工主数据...\n")
        employees_by_email, employees_by_id = service.load_employees(employees_csv)
        if not employees_by_email and not employees_by_id:
            self.stdout.write(f"❌ 员工主数据文件不存在: {employees_csv}\n")

        self.stdout.write(f"  已加载 {len(employees_by_email)} 条邮箱索引\n")
        self.stdout.write(f"  已加载 {len(employees_by_id)} 条工号索引\n")

        # 2. 检查 GitLab 对齐
        self.stdout.write("\n========== GitLab 身份对齐检查 ==========\n")
        gitlab_result = service.check_gitlab_alignment(gitlab_csv, employees_by_email)
        if not gitlab_result["exists"]:
            self.stdout.write(f"⚠️ GitLab 用户文件不存在: {gitlab_csv}\n")
        else:
            self.stdout.write(
                f"✅ 匹配成功: {gitlab_result['matched']} 条 | ⚠️ 问题记录: {len(gitlab_result['issues'])} 条 | ❌ 未匹配: {gitlab_result['unmatched']} 条\n"
            )
            for idx, issue in enumerate(gitlab_result["issues"][:10], 1):
                self.stdout.write(
                    f"  {idx}. [{issue['type']}] {issue.get('gitlab_name')} - {issue.get('mdm_name', '')} ({issue.get('email', issue.get('gitlab_email'))})\n"
                )

        # 3. 检查禅道对齐
        self.stdout.write("\n========== 禅道身份对齐检查 ==========\n")
        zentao_result = service.check_zentao_alignment(zentao_csv, employees_by_email, employees_by_id)
        if not zentao_result["exists"]:
            self.stdout.write(f"⚠️ 禅道用户文件不存在: {zentao_csv}\n")
        else:
            self.stdout.write(f"✅ 匹配成功: {zentao_result['matched']} 条 | ⚠️ 问题记录: {len(zentao_result['issues'])} 条\n")
            for idx, issue in enumerate(zentao_result["issues"][:10], 1):
                self.stdout.write(f"  {idx}. [{issue['type']}] {issue.get('name', issue.get('zentao_name'))}\n")

        self.stdout.write("\n" + "=" * 50 + "\n")
        self.stdout.write("检查完成!\n")
        self.stdout.write("=" * 50 + "\n")
        return True
