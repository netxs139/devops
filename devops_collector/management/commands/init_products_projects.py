import csv
import logging
import uuid
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import urlparse

import typer
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand, build_user_indexes, resolve_user
from devops_collector.models import (
    EntityTopology,
    Organization,
    Product,
    ProjectMaster,
    ProjectProductRelation,
    SystemRegistry,
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "初始化产品与项目主数据。"

    def handle(
        self,
        session: Session,
        prd_csv_file: Annotated[Optional[str], typer.Option("--prd-csv", help="产品信息 CSV 路径")] = None,
        proj_csv_file: Annotated[Optional[str], typer.Option("--proj-csv", help="项目信息 CSV 路径")] = None,
    ):
        sample_dir = Path("docs/assets/sample_data")
        prd_csv = Path(prd_csv_file) if prd_csv_file else sample_dir / "products.csv"
        proj_csv = Path(proj_csv_file) if proj_csv_file else sample_dir / "projects.csv"

        try:
            prod_map_id = self._init_products(prd_csv)
            self._init_projects(proj_csv, prod_map_id)
            self.stdout.write("✅ 产品与项目主数据同步完成！\n")
            return True
        except Exception as e:
            logger.error(f"产品与项目同步失败: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def _ensure_system_registry(self, code="gitlab-prod", name="生产环境GitLab"):
        system = self.session.query(SystemRegistry).filter_by(system_code=code).first()
        if not system:
            system = SystemRegistry(system_code=code, system_name=name, system_type="VCS", is_active=True)
            self.session.add(system)
            self.session.flush()
        return system

    def _init_products(self, prd_csv: Path):
        if not prd_csv.exists():
            self.stdout.write(f"WARN: 跳过产品初始化：找不到文件 {prd_csv}\n")
            return {}

        self.stdout.write(f"从 {prd_csv} 同步产品主数据...\n")
        prod_map_id = {}

        orgs = {o.org_name: o.id for o in self.session.query(Organization).filter_by(is_current=True).all()}
        email_idx, name_idx = build_user_indexes(self.session)

        product_rows = []
        with open(prd_csv, encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]同步产品主数据 ({prd_csv.name})...", total=len(reader))
                for row in reader:
                    name = row.get("产品名称", row.get("PRODUCT_NAME", "")).strip()
                    if not name:
                        continue

                    prod_code = row.get("PRODUCT_ID", "").strip()
                    if not prod_code:
                        prod_code = f"PRD-{uuid.uuid5(uuid.NAMESPACE_DNS, name).hex[:8].upper()}"

                    product = self.session.query(Product).filter_by(product_code=prod_code).first()
                    if not product:
                        product = Product(product_code=prod_code, product_name=name, product_description=name, version_schema="SemVer", is_current=True)
                        self.session.add(product)

                    product.product_name = name
                    product.node_type = row.get("节点类型", row.get("node_type", "APP")).strip().upper()
                    product.category = row.get("产品分类", row.get("category", "")).strip()

                    team_name = row.get("负责团队", row.get("owner_team_id", "")).strip()
                    if team_name in orgs:
                        product.owner_team_id = orgs[team_name]
                    elif team_name:
                        org_by_code = self.session.query(Organization).filter_by(org_code=team_name).first()
                        if org_by_code:
                            product.owner_team_id = org_by_code.id

                    for csv_col, attr in [
                        ("产品经理", "product_manager_id"),
                        ("开发经理", "dev_lead_id"),
                        ("测试经理", "qa_lead_id"),
                        ("发布经理", "release_lead_id"),
                    ]:
                        val = row.get(csv_col, "").strip()
                        uid = resolve_user(val, email_idx, name_idx, csv_col)
                        if uid:
                            setattr(product, attr, uid)

                    self.session.flush()
                    prod_map_id[prod_code] = product.id
                    prod_map_id[name] = product.id
                    product_rows.append((product, row))
                    progress.advance(task)

        for product, row in product_rows:
            parent_ref = row.get("上级产品ID", row.get("parent_product_id", "")).strip()
            if parent_ref:
                parent_id = prod_map_id.get(parent_ref)
                if parent_id and parent_id != product.id:
                    product.parent_product_id = parent_id

        self.session.flush()
        return prod_map_id

    def _init_projects(self, proj_csv: Path, prod_map_id):
        if not proj_csv.exists():
            self.stdout.write(f"WARN: 跳过项目初始化：找不到文件 {proj_csv}\n")
            return

        self.stdout.write(f"从 {proj_csv} 同步项目主数据...\n")

        email_idx, name_idx = build_user_indexes(self.session)
        orgs_by_name = {o.org_name: o.id for o in self.session.query(Organization).filter_by(is_current=True).all()}

        with open(proj_csv, encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]同步项目主数据 ({proj_csv.name})...", total=len(reader))
                for row in reader:
                    code_val = row.get("项目代号", "").strip()
                    name = row.get("项目名称", "").strip()
                    prod_name = row.get("所属产品", "").strip()

                    if not code_val or not name:
                        progress.advance(task)
                        continue

                    proj_code = f"PROJ-{code_val}"
                    project = self.session.query(ProjectMaster).filter_by(project_code=proj_code).first()
                    if not project:
                        project = ProjectMaster(project_code=proj_code, project_name=name, status="ACTIVE", is_current=True)
                        self.session.add(project)

                    dept_name = row.get("负责部门", "").strip()
                    if dept_name in orgs_by_name:
                        project.org_id = orgs_by_name[dept_name]
                    elif dept_name:
                        org_by_code = self.session.query(Organization).filter_by(org_code=dept_name).first()
                        if org_by_code:
                            project.org_id = org_by_code.id

                    repo_url = row.get("主代码仓库URL", "").strip()
                    if repo_url:
                        system = self._ensure_system_registry()
                        self.session.flush()
                        topology = (
                            self.session.query(EntityTopology)
                            .filter_by(project_id=project.id, external_resource_id=repo_url, element_type="source-code")
                            .first()
                        )
                        if not topology:
                            topology = EntityTopology(
                                project_id=project.id,
                                system_id=system.id,
                                external_resource_id=repo_url,
                                resource_name=urlparse(repo_url).path.strip("/").removesuffix(".git"),
                                element_type="source-code",
                                is_active=True,
                            )
                            self.session.add(topology)

                    for csv_col, attr in [
                        ("项目经理", "pm_user_id"),
                        ("产品经理", "product_owner_id"),
                        ("开发经理", "dev_lead_id"),
                        ("测试经理", "qa_lead_id"),
                        ("发布经理", "release_lead_id"),
                    ]:
                        val = row.get(csv_col, "").strip()
                        uid = resolve_user(val, email_idx, name_idx, csv_col)
                        if uid:
                            setattr(project, attr, uid)

                    self.session.flush()
                    target_prod_id = prod_map_id.get(prod_name)
                    if target_prod_id:
                        rel = self.session.query(ProjectProductRelation).filter_by(project_id=project.id, product_id=target_prod_id).first()
                        if not rel and project.org_id:
                            self.session.add(
                                ProjectProductRelation(
                                    project_id=project.id,
                                    product_id=target_prod_id,
                                    org_id=project.org_id,
                                    relation_type="PRIMARY",
                                )
                            )
                progress.advance(task)
        self.session.flush()
