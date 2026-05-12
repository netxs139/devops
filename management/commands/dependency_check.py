import csv
import logging
from pathlib import Path

from bs4 import BeautifulSoup

from devops_collector.core.management import BaseCommand


logger = logging.getLogger("DependencyCheck")


class Command(BaseCommand):
    help = "解析 DependencyCheck HTML 报告并转换为 CSV 格式。"

    def add_arguments(self, parser):
        parser.add_argument("--dir", type=str, default="reports", help="HTML 报告所在目录")
        parser.add_argument("--output", type=str, help="输出 CSV 文件路径")

    def handle(self, *args, **options):
        report_dir = Path(options.get("dir"))
        if not report_dir.exists():
            self.stdout.write(f"❌ 目录不存在: {report_dir}\n")
            return False

        html_file = self._find_html_file(report_dir)
        if not html_file:
            self.stdout.write("❌ 未在该目录下找到 HTML 报告文件。\n")
            return False

        vulnerabilities = self._parse_html_report(html_file)
        self.stdout.write(f"发现 {len(vulnerabilities)} 条漏洞信息。\n")

        output_file = options.get("output") or report_dir / "DependencyCheck_report.csv"
        self._write_csv_file(vulnerabilities, output_file)
        self.stdout.write(f"✅ CSV 报告已生成: {output_file}\n")
        return True

    def _find_html_file(self, directory):
        for f in directory.glob("*.html"):
            return f
        return None

    def _parse_html_report(self, html_file):
        with open(html_file, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        vulnerabilities = []
        table = soup.find("table", id="summaryTable")
        if not table:
            return []

        headers = [h.text.strip().replace("\xa0", " ").lower() for h in table.find("thead").find_all("th")]
        try:
            dep_idx = headers.index("dependency")
            sev_idx = headers.index("highest severity")
            cve_idx = headers.index("cve count")
        except ValueError:
            return []

        rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            if len(cells) != len(headers):
                continue

            vulnerabilities.append(
                {"Dependency": cells[dep_idx].text.strip(), "Severity": cells[sev_idx].text.strip(), "CVE Count": cells[cve_idx].text.strip()}
            )
        return vulnerabilities

    def _write_csv_file(self, vulnerabilities, output_file):
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["Dependency", "Severity", "CVE Count"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(vulnerabilities)
