"""SonarQube 质量中心导出命令。.

导出 CSV 格式的详细质量报告，包含行数、Bug、漏洞、覆盖率等指标。
"""

from typing import Annotated

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.services.quality_service import QualityService


class Command(BaseCommand):
    """Management command."""

    help = "导出 SonarQube 质量报表：生成包含详细度量指标的 CSV 报告"

    def handle(
        self,
        session: Session,
        output_path: Annotated[str, typer.Option("--output", "-o", help="输出路径")] = "sonarqube_quality_report.csv",
    ):
        """Execute command."""
        self.stdout.write("正在收集所有项目的最新质量指标...\n")

        try:
            service = QualityService(session)
            csv_data = service.export_sonar_quality_report()

            if not csv_data:
                self.stdout.write("⚠️ 数据库中没有 SonarQube 项目记录。\n")
                return True

            with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(csv_data)

            # Count rows roughly (subtracting header)
            count = len(csv_data.strip().split("\n")) - 1
            count = max(count, 0)

            self.stdout.write(f"✅ 导出成功: {output_path}\n")
            self.stdout.write(f"📊 共导出了 {count} 个项目的质量指标。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 导出失败: {e}\n")
            return False
