"""初始化 ZenTao 产品/项目与 MDM 资产的拓扑映射。"""

import csv
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.models import EntityTopology, Product, ProjectMaster, SystemRegistry
from devops_collector.plugins.zentao.models import ZenTaoExecution, ZenTaoProduct


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")


class Command(BaseCommand):
    help = "从 CSV 初始化 ZenTao 产品/项目与 MDM 资产的拓扑映射"

    def add_arguments(self, parser):
        parser.add_argument("--product-csv", type=str, help="ZenTao 产品映射 CSV（默认: zentao_product_map.csv）")
        parser.add_argument("--project-csv", type=str, help="ZenTao 项目映射 CSV（默认: zentao_project_map.csv）")

    def handle(self, *args, **options):
        product_csv = Path(options["product_csv"]) if options.get("product_csv") else SAMPLE_DATA_DIR / "zentao_product_map.csv"
        project_csv = Path(options["project_csv"]) if options.get("project_csv") else SAMPLE_DATA_DIR / "zentao_project_map.csv"

        try:
            system = self._ensure_system_registry()
            self._init_product_links(product_csv, system.id)
            self._init_project_links(project_csv, system.id)
            self.session.flush()
            self.stdout.write("✅ ZenTao 关联映射初始化完成。\n")
            return True
        except Exception as e:
            self.stderr.write(f"❌ ZenTao 关联初始化失败: {e}\n")
            return False

    def _ensure_system_registry(self) -> SystemRegistry:
        system = self.session.query(SystemRegistry).filter_by(system_code="zentao-prod").first()
        if not system:
            system = SystemRegistry(
                system_code="zentao-prod",
                system_name="ZenTao ALM",
                system_type="PROJECT",
                is_active=True,
                env_tag="PROD",
            )
            self.session.add(system)
            self.session.flush()
        return system

    def _init_product_links(self, csv_path: Path, system_id: int) -> None:
        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过 ZenTao 产品关联：找不到 {csv_path}\n")
            return

        self.stdout.write(f"从 {csv_path.name} 同步 ZenTao 产品关联...\n")
        with open(csv_path, encoding="utf-8-sig") as f:
            lines = [line for line in f if not line.strip().startswith("#")]
        rows = list(csv.DictReader(lines))

        with self.get_progress() as progress:
            task = progress.add_task(f"[cyan]ZenTao 产品拓扑 ({csv_path.name})...", total=len(rows))
            for row in rows:
                zt_ref = row.get("zentao_product_id", "").strip()
                zt_name = row.get("zentao_product_name", "").strip()
                mdm_ref = row.get("mdm_product_id", "").strip()
                mdm_name = row.get("mdm_product_name", "").strip()

                if not mdm_ref and not mdm_name:
                    progress.advance(task)
                    continue

                mdm_product = self.session.query(Product).filter((Product.product_code == mdm_ref) | (Product.product_name == mdm_name)).first()
                if not mdm_product:
                    progress.advance(task)
                    continue

                zt_product = None
                if zt_ref.isdigit():
                    zt_product = self.session.query(ZenTaoProduct).filter_by(id=int(zt_ref)).first()
                if not zt_product:
                    zt_product = self.session.query(ZenTaoProduct).filter((ZenTaoProduct.code == zt_ref) | (ZenTaoProduct.name == zt_name)).first()

                if zt_product:
                    topo = (
                        self.session.query(EntityTopology)
                        .filter_by(
                            system_id=system_id,
                            external_resource_id=str(zt_product.id),
                            element_type="issue-tracker-product",
                        )
                        .first()
                    )
                    if not topo:
                        self.session.add(
                            EntityTopology(
                                system_id=system_id,
                                external_resource_id=str(zt_product.id),
                                resource_name=zt_product.name,
                                element_type="issue-tracker-product",
                                is_active=True,
                            )
                        )
                    self.session.flush()

                progress.advance(task)

    def _init_project_links(self, csv_path: Path, system_id: int) -> None:
        if not csv_path.exists():
            self.stdout.write(f"WARN: 跳过 ZenTao 项目关联：找不到 {csv_path}\n")
            return

        self.stdout.write(f"从 {csv_path.name} 同步 ZenTao 项目关联...\n")
        with open(csv_path, encoding="utf-8-sig") as f:
            lines = [line for line in f if not line.strip().startswith("#")]
        rows = list(csv.DictReader(lines))

        with self.get_progress() as progress:
            task = progress.add_task(f"[cyan]ZenTao 项目拓扑 ({csv_path.name})...", total=len(rows))
            for row in rows:
                zt_ref = row.get("zentao_execution_id", "").strip()
                zt_name = row.get("zentao_execution_name", "").strip()
                mdm_ref = row.get("mdm_project_id", "").strip()

                if not mdm_ref:
                    progress.advance(task)
                    continue

                mdm_project = (
                    self.session.query(ProjectMaster).filter((ProjectMaster.project_code == mdm_ref) | (ProjectMaster.project_name == mdm_ref)).first()
                )
                if not mdm_project:
                    progress.advance(task)
                    continue

                target_node = None
                if zt_ref.isdigit():
                    target_node = self.session.query(ZenTaoExecution).filter_by(id=int(zt_ref)).first()
                if not target_node:
                    target_node = self.session.query(ZenTaoExecution).filter((ZenTaoExecution.code == zt_ref) | (ZenTaoExecution.name == zt_name)).first()

                nodes_to_link = [target_node] if target_node else []

                # 产品级兜底：关联其下所有 execution
                if not nodes_to_link:
                    zt_product = self.session.query(ZenTaoProduct).filter((ZenTaoProduct.code == zt_ref) | (ZenTaoProduct.name == zt_name)).first()
                    if zt_product:
                        nodes_to_link = self.session.query(ZenTaoExecution).filter_by(product_id=zt_product.id).all()

                for node in nodes_to_link:
                    topo = (
                        self.session.query(EntityTopology)
                        .filter_by(
                            system_id=system_id,
                            external_resource_id=str(node.id),
                            element_type="issue-tracker",
                        )
                        .first()
                    )
                    if not topo:
                        topo = EntityTopology(
                            system_id=system_id,
                            external_resource_id=str(node.id),
                            resource_name=node.name,
                            element_type="issue-tracker",
                            is_active=True,
                        )
                        self.session.add(topo)
                    topo.project_id = mdm_project.id
                self.session.flush()
                progress.advance(task)
