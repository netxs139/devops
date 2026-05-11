import logging
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from devops_collector.core.management import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dashboard 页面自动化健康检查脚本：验证数据仓库表和列是否存在。"

    def handle(self, *args, **options):
        dashboard_dir = Path("dashboard/pages")
        if not dashboard_dir.exists():
            self.stdout.write(f"❌ Dashboard 目录不存在: {dashboard_dir}\n")
            return False

        page_files = sorted(dashboard_dir.glob("*.py"))
        self.stdout.write("=" * 70 + "\n")
        self.stdout.write("Dashboard 页面健康检查\n")
        self.stdout.write("=" * 70 + "\n")
        self.stdout.write(f"发现 {len(page_files)} 个页面文件\n")
        self.stdout.write("-" * 70 + "\n")

        all_results = []
        for page_path in page_files:
            results = self._test_page(page_path)
            all_results.extend(results)
            for r in results:
                status_icon = {"PASS": "[OK]", "FAIL": "[FAIL]", "WARN": "[WARN]", "SKIP": "[SKIP]", "ERROR": "[ERROR]"}.get(r["status"], "[?]")
                self.stdout.write(f"{status_icon} {r['page']}: {r['query']}\n")
                if r["error"]:
                    self.stdout.write(f"       -> {r['error'][:200]}\n")

        fail_count = self._print_summary(all_results)
        return fail_count == 0

    def _extract_sql_queries(self, content: str) -> list[tuple[str, str]]:
        queries = []
        pattern = r'run_query\s*\(\s*["\']+(.*?)["\']+\s*\)'
        matches = re.findall(pattern, content, re.DOTALL)
        for i, raw_sql in enumerate(matches):
            if raw_sql.strip():
                queries.append((f"Query_{i + 1}", raw_sql.strip()))

        triple_pattern = r'run_query\s*\(\s*"""(.*?)"""\s*\)'
        triple_matches = re.findall(triple_pattern, content, re.DOTALL)
        for i, raw_sql in enumerate(triple_matches):
            if raw_sql.strip():
                queries.append((f"TripleQuery_{i + 1}", raw_sql.strip()))
        return queries

    def _test_sql_query(self, sql: str, page_name: str, query_name: str) -> dict:
        result = {"page": page_name, "query": query_name, "sql": sql[:100] + "..." if len(sql) > 100 else sql, "status": "PASS", "error": None}
        try:
            test_sql = sql.strip()
            if not test_sql.upper().startswith("EXPLAIN"):
                if "LIMIT" not in test_sql.upper():
                    test_sql = f"SELECT * FROM ({test_sql}) AS _test_wrapper LIMIT 1"
            self.session.execute(text(test_sql))
        except (ProgrammingError, OperationalError) as e:
            result["status"] = "FAIL"
            result["error"] = str(e.orig) if hasattr(e, "orig") else str(e)
        except Exception as e:
            result["status"] = "WARN"
            result["error"] = str(e)
        return result

    def _test_page(self, page_path: Path) -> list[dict]:
        page_name = page_path.stem
        try:
            content = page_path.read_text(encoding="utf-8")
        except Exception as e:
            return [{"page": page_name, "query": "N/A", "sql": "N/A", "status": "ERROR", "error": f"无法读取文件: {e}"}]

        queries = self._extract_sql_queries(content)
        if not queries:
            return [{"page": page_name, "query": "N/A", "sql": "N/A", "status": "SKIP", "error": "未检测到 SQL 查询"}]

        return [self._test_sql_query(sql, page_name, q_name) for q_name, sql in queries]

    def _print_summary(self, results: list[dict]) -> int:
        self.stdout.write("\n" + "=" * 70 + "\n")
        self.stdout.write("测试摘要\n")
        self.stdout.write("=" * 70 + "\n")
        counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1

        for k, v in counts.items():
            self.stdout.write(f"  {k}: {v}\n")
        self.stdout.write(f"  TOTAL: {len(results)}\n")

        if counts["FAIL"] > 0:
            self.stdout.write("\n" + "-" * 70 + "\n")
            self.stdout.write("失败详情:\n")
            for r in results:
                if r["status"] == "FAIL":
                    self.stdout.write(f"\n  Page: {r['page']} | Query: {r['query']}\n  Error: {r['error']}\n")
        return counts["FAIL"]
