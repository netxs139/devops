"""禅道基础资产导出命令。

导出禅道产品和执行/迭代的对应关系及 MDM 映射状态，方便离线核对和批量修正。
"""

import csv
from pathlib import Path

from sqlalchemy import text

from devops_collector.core.management import BaseCommand


class Command(BaseCommand):
    help = "导出禅道数据：将禅道产品和迭代记录导出为 CSV 文件"

    def add_arguments(self, parser):
        parser.add_argument("-d", "--dir", default=".", help="输出目录 (默认: 当前目录)")

    def handle(self, *args, **options):
        output_dir = Path(options["dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. 导出 zentao_products
            self.stdout.write("正在导出禅道产品数据...\n")
            p_file = output_dir / "zentao_products_export.csv"
            sql_p = text("SELECT id, code, name, status, mdm_product_id FROM zentao_products ORDER BY id")
            res_p = self.session.execute(sql_p).fetchall()

            with open(p_file, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "code", "name", "status", "mdm_product_id"])
                writer.writerows(res_p)

            # 2. 导出 zentao_executions
            self.stdout.write("正在导出禅道执行/迭代数据...\n")
            e_file = output_dir / "zentao_executions_export.csv"
            sql_e = text("SELECT id, product_id, name, code, type, status, parent_id, mdm_project_id FROM zentao_executions ORDER BY id")
            res_e = self.session.execute(sql_e).fetchall()

            with open(e_file, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "product_id", "name", "code", "type", "status", "parent_id", "mdm_project_id"])
                writer.writerows(res_e)

            self.stdout.write(f"✅ 导出成功！\n  - 产品数据: {p_file}\n  - 迭代数据: {e_file}\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 导出失败: {e}\n")
            return False
