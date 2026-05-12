"""初始化 SonarQube 项目与 MDM 资产的关联。"""

import csv
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models import Product, ProjectMaster
from devops_collector.plugins.sonarqube.models import SonarProject


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "sonarqube_project_map.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化 SonarQube 项目与 MDM 项目/产品关联"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="SonarQube 映射 CSV 路径（默认: sonarqube_project_map.csv）")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV

        if not csv_path.exists():
            self.stdout.write(f"WARN: 找不到 SonarQube 映射文件: {csv_path}\n")
            return True

        try:
            self.stdout.write(f"从 {csv_path} 同步 SonarQube 项目关联...\n")

            projects = {p.project_code: p.id for p in self.session.query(ProjectMaster).filter(ProjectMaster.is_current).all()}
            products = {p.product_code: p.id for p in self.session.query(Product).filter(Product.is_current).all()}

            with open(csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]SonarQube 关联 ({csv_path.name})...", total=len(rows))

                for row in rows:
                    sonar_key = row.get("sonar_project_key", "").strip()
                    mdm_proj_code = row.get("mdm_project_id", "").strip()
                    mdm_prod_code = row.get("mdm_product_id", "").strip()

                    if not sonar_key:
                        progress.advance(task)
                        continue

                    project = self.session.query(SonarProject).filter_by(key=sonar_key).first()
                    if not project:
                        project = SonarProject(key=sonar_key, name=sonar_key.split(":")[-1], qualifier="TRK")
                        self.session.add(project)
                        self.session.flush()

                    if mdm_proj_code:
                        p_id = projects.get(mdm_proj_code) or projects.get(f"PROJ-{mdm_proj_code}")
                        if p_id:
                            project.mdm_project_id = p_id
                        elif mdm_proj_code.isdigit():
                            project.mdm_project_id = int(mdm_proj_code)

                    if mdm_prod_code:
                        prod_id = products.get(mdm_prod_code) or products.get(f"PRD-{mdm_prod_code}")
                        if prod_id:
                            project.mdm_product_id = prod_id
                        elif mdm_prod_code.isdigit():
                            project.mdm_product_id = int(mdm_prod_code)

                    progress.advance(task)

            self.session.flush()
            self.stdout.write("✅ SonarQube 项目关联初始化完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ SonarQube 关联初始化失败: {e}\n")
            return False
