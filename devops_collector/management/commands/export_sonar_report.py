"""SonarQube 质量中心导出命令。

导出 CSV 格式的详细质量报告，包含行数、Bug、漏洞、覆盖率等指标。
"""

import csv

from devops_collector.core.management import BaseCommand
from devops_collector.plugins.sonarqube.models import SonarProject


class Command(BaseCommand):
    help = "导出 SonarQube 质量报表：生成包含详细度量指标的 CSV 报告"

    def add_arguments(self, parser):
        parser.add_argument("-o", "--output", default="sonarqube_quality_report.csv", help="输出路径 (默认: sonarqube_quality_report.csv)")

    def handle(self, *args, **options):
        output_path = options["output"]

        self.stdout.write("正在收集所有项目的最新质量指标...\n")

        try:
            projects = self.session.query(SonarProject).all()
            if not projects:
                self.stdout.write("⚠️ 数据库中没有 SonarQube 项目记录。\n")
                return True

            headers = [
                "Project Key",
                "Project Name",
                "总行数",
                "代码行数",
                "类数量",
                "方法数量",
                "语句数量",
                "文件数",
                "Bugs",
                "安全漏洞",
                "安全热点",
                "注释率%",
                "覆盖率%",
                "圈复杂度",
                "认知复杂度",
                "重复行率%",
                "债务率%",
                "开发总工时(人月)",
                "阻塞级Bugs",
                "严重级Bugs",
                "主要级Bugs",
                "次要级Bugs",
                "信息级Bugs",
                "阻塞级漏洞",
                "严重级漏洞",
                "MAJOR级漏洞",
                "MINOR级漏洞",
                "INFO级漏洞",
                "质量门禁状态",
            ]

            with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

                count = 0
                for p in projects:
                    m = p.latest_measure
                    if not m:
                        continue

                    row = [
                        p.key,
                        p.name,
                        m.lines,
                        m.ncloc,
                        m.classes,
                        m.functions,
                        m.statements,
                        m.files,
                        m.bugs,
                        m.vulnerabilities,
                        m.security_hotspots,
                        f"{m.comment_lines_density or 0:.1f}",
                        f"{m.coverage or 0:.1f}",
                        m.complexity,
                        m.cognitive_complexity,
                        f"{m.duplicated_lines_density or 0:.1f}",
                        f"{m.sqale_debt_ratio or 0:.1f}",
                        m.dev_cost,
                        m.bugs_blocker,
                        m.bugs_critical,
                        m.bugs_major,
                        m.bugs_minor,
                        m.bugs_info,
                        m.vulnerabilities_blocker,
                        m.vulnerabilities_critical,
                        m.vulnerabilities_major,
                        m.vulnerabilities_minor,
                        m.vulnerabilities_info,
                        m.quality_gate_status or "UNKNOWN",
                    ]
                    writer.writerow(row)
                    count += 1

            self.stdout.write(f"✅ 导出成功: {output_path}\n")
            self.stdout.write(f"📊 共导出了 {count} 个项目的质量指标。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 导出失败: {e}\n")
            return False
