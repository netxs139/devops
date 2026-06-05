"""资产关联与拓扑同步服务。"""

import csv
from pathlib import Path
from re import Pattern
from typing import TypedDict

from sqlalchemy.orm import Session

from devops_collector.models import Product, ProjectMaster
from devops_collector.plugins.sonarqube.models import SonarProject


class NexusLinkRule(TypedDict):
    """Nexus 组件与产品关联规则的数据结构定义。"""

    group: str
    name: str
    pid: int
    type: str
    group_re: Pattern[str] | None
    name_re: Pattern[str] | None


class TopologyService:
    """管理外部系统（如 SonarQube, Jenkins, Nexus 等）与内部 MDM 资产（Product, Project）的绑定关系。"""

    def __init__(self, session: Session):
        self.session = session

    def sync_sonarqube_links(self, csv_path: Path, progress_callback=None) -> None:
        """从 CSV 初始化 SonarQube 项目与 MDM 项目/产品关联。"""
        projects = {p.project_code: p.id for p in self.session.query(ProjectMaster).filter(ProjectMaster.is_current).all()}
        products = {p.product_code: p.id for p in self.session.query(Product).filter(Product.is_current).all()}

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            sonar_key = row.get("sonar_project_key", "").strip()
            mdm_proj_code = row.get("mdm_project_id", "").strip()
            mdm_prod_code = row.get("mdm_product_id", "").strip()

            if not sonar_key:
                if progress_callback:
                    progress_callback()
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

            if progress_callback:
                progress_callback()

        self.session.flush()

    def sync_jenkins_links(self, csv_path: Path, progress_callback=None) -> None:
        """从 CSV 初始化 Jenkins Job 与 MDM 资产关联（支持前缀继承）。"""
        from devops_collector.plugins.jenkins.models import JenkinsJob

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        def _update_job(job: JenkinsJob, proj_id, prod_id, deploy: bool, env_str) -> None:
            if proj_id:
                job.mdm_project_id = proj_id
            if prod_id:
                job.mdm_product_id = prod_id
            job.is_deployment = deploy
            if env_str:
                job.deployment_env = env_str

        for row in rows:
            job_name = row.get("job_full_name", "").strip()
            if not job_name:
                if progress_callback:
                    progress_callback()
                continue

            mdm_proj = row.get("mdm_project_id")
            mdm_prod = row.get("mdm_product_id")
            is_deploy = row.get("is_deployment", "false").lower() == "true"
            env = row.get("deployment_env")

            # 前缀继承：以 / 结尾视为文件夹匹配
            if job_name.endswith("/"):
                target_jobs = self.session.query(JenkinsJob).filter(JenkinsJob.full_name.like(f"{job_name}%")).all()
                for job in target_jobs:
                    _update_job(job, mdm_proj, mdm_prod, is_deploy, env)
            else:
                single_job = self.session.query(JenkinsJob).filter_by(full_name=job_name).first()
                if not single_job:
                    single_job = JenkinsJob(full_name=job_name, name=job_name.split("/")[-1])
                    self.session.add(single_job)
                _update_job(single_job, mdm_proj, mdm_prod, is_deploy, env)

            if progress_callback:
                progress_callback()

        self.session.flush()

    def sync_nexus_links(self, csv_path: Path, progress_callback=None) -> int:
        """从 CSV 规则初始化 Nexus 组件与 MDM 产品关联（exact/regex 双模式）。"""
        import re

        from devops_collector.plugins.nexus.models import NexusComponent

        all_products = self.session.query(Product.id, Product.product_code).filter(Product.is_current).all()
        product_code_map = {p.product_code: p.id for p in all_products}
        product_id_set = {p.id for p in all_products}

        rules: list[NexusLinkRule] = []
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
                    NexusLinkRule(
                        group=group_pat,
                        name=name_pat,
                        pid=actual_pid,
                        type=match_type,
                        group_re=re.compile(group_pat) if match_type == "regex" and group_pat else None,
                        name_re=re.compile(name_pat) if match_type == "regex" and name_pat else None,
                    )
                )

        all_components = self.session.query(NexusComponent).all()
        updated_count = 0

        for comp in all_components:
            for rule in rules:
                match = True
                if rule["type"] == "regex":
                    if rule["group"] and rule["group_re"] is not None and not rule["group_re"].search(comp.group or ""):
                        match = False
                    if rule["name"] and rule["name_re"] is not None and not rule["name_re"].search(comp.name or ""):
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
            if progress_callback:
                progress_callback()

        self.session.flush()
        return updated_count
