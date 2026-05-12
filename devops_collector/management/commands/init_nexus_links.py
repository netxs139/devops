"""初始化 Nexus 组件与 MDM 产品关联（支持 exact/regex 双模式匹配）。"""

import csv
import re
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models import Product
from devops_collector.plugins.nexus.models import NexusComponent


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "nexus_component_map.csv"


class Command(BaseCommand):
    help = "从 CSV 规则初始化 Nexus 组件与 MDM 产品关联（exact/regex 双模式）"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Nexus 映射 CSV 路径（默认: nexus_component_map.csv）")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV

        if not csv_path.exists():
            self.stdout.write(f"WARN: 找不到 Nexus 映射文件: {csv_path}\n")
            return True

        try:
            self.stdout.write(f"从 {csv_path} 同步 Nexus 组件关联...\n")

            # 预加载产品数据
            all_products = self.session.query(Product.id, Product.product_code).filter(Product.is_current).all()
            product_code_map = {p.product_code: p.id for p in all_products}
            product_id_set = {p.id for p in all_products}

            # 编译映射规则
            rules = []
            with open(csv_path, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    group_pat = row.get("group", "").strip()
                    name_pat = row.get("name", "").strip()
                    mdm_prod_code = row.get("mdm_product_id", "").strip()
                    match_type = row.get("match_type", "exact").strip().lower()

                    if (not group_pat and not name_pat) or not mdm_prod_code:
                        continue

                    actual_pid = (
                        product_code_map.get(mdm_prod_code)
                        or product_code_map.get(f"PRD-{mdm_prod_code}")
                        or (int(mdm_prod_code) if mdm_prod_code.isdigit() and int(mdm_prod_code) in product_id_set else None)
                    )
                    if actual_pid is None:
                        continue

                    rules.append(
                        {
                            "group": group_pat,
                            "name": name_pat,
                            "pid": actual_pid,
                            "type": match_type,
                            "group_re": re.compile(group_pat) if match_type == "regex" and group_pat else None,
                            "name_re": re.compile(name_pat) if match_type == "regex" and name_pat else None,
                        }
                    )

            # 遍历组件匹配
            all_components = self.session.query(NexusComponent).all()
            updated_count = 0

            with self.get_progress() as progress:
                task = progress.add_task("[cyan]匹配 Nexus 组件...", total=len(all_components))
                for comp in all_components:
                    for rule in rules:
                        match = True
                        if rule["type"] == "regex":
                            if rule["group"] and not rule["group_re"].search(comp.group or ""):
                                match = False
                            if rule["name"] and not rule["name_re"].search(comp.name or ""):
                                match = False
                        else:
                            if rule["group"] and comp.group != rule["group"]:
                                match = False
                            if rule["name"] and comp.name != rule["name"]:
                                match = False

                        if match:
                            if comp.product_id != rule["pid"]:
                                comp.product_id = rule["pid"]
                                updated_count += 1
                            break
                    progress.advance(task)

            self.session.flush()
            self.stdout.write(f"✅ Nexus 组件关联初始化完成，共更新 {updated_count} 个组件。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ Nexus 关联初始化失败: {e}\n")
            return False
