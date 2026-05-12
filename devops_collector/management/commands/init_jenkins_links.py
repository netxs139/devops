"""初始化 Jenkins Job 与 MDM 资产的关联。"""

import csv
from pathlib import Path

from devops_collector.core.management import BaseCommand
from devops_collector.plugins.jenkins.models import JenkinsJob


SAMPLE_DATA_DIR = Path("docs/assets/sample_data")
DEFAULT_CSV = SAMPLE_DATA_DIR / "jenkins_job_map.csv"


class Command(BaseCommand):
    help = "从 CSV 初始化 Jenkins Job 与 MDM 资产关联（支持前缀继承）"

    def add_arguments(self, parser):
        parser.add_argument("--csv", type=str, help="Jenkins 映射 CSV 路径（默认: jenkins_job_map.csv）")

    def handle(self, *args, **options):
        csv_path = Path(options["csv"]) if options.get("csv") else DEFAULT_CSV

        if not csv_path.exists():
            self.stdout.write(f"WARN: 找不到 Jenkins 映射文件: {csv_path}\n")
            return True

        try:
            self.stdout.write(f"从 {csv_path} 同步 Jenkins Job 关联...\n")

            with open(csv_path, encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

            with self.get_progress() as progress:
                task = progress.add_task(f"[cyan]Jenkins 关联 ({csv_path.name})...", total=len(rows))
                for row in rows:
                    job_name = row.get("job_full_name", "").strip()
                    if not job_name:
                        progress.advance(task)
                        continue

                    mdm_proj = row.get("mdm_project_id")
                    mdm_prod = row.get("mdm_product_id")
                    is_deploy = row.get("is_deployment", "false").lower() == "true"
                    env = row.get("deployment_env")

                    # 前缀继承：以 / 结尾视为文件夹匹配
                    if job_name.endswith("/"):
                        target_jobs = self.session.query(JenkinsJob).filter(JenkinsJob.full_name.like(f"{job_name}%")).all()
                        for job in target_jobs:
                            self._update_job(job, mdm_proj, mdm_prod, is_deploy, env)
                    else:
                        job = self.session.query(JenkinsJob).filter_by(full_name=job_name).first()
                        if not job:
                            job = JenkinsJob(full_name=job_name, name=job_name.split("/")[-1])
                            self.session.add(job)
                        self._update_job(job, mdm_proj, mdm_prod, is_deploy, env)

                    progress.advance(task)

            self.session.flush()
            self.stdout.write("✅ Jenkins 拓扑关联同步完成。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ Jenkins 关联初始化失败: {e}\n")
            return False

    @staticmethod
    def _update_job(job: JenkinsJob, proj_id, prod_id, is_deploy: bool, env) -> None:
        if proj_id:
            job.mdm_project_id = proj_id
        if prod_id:
            job.mdm_product_id = prod_id
        job.is_deployment = is_deploy
        if env:
            job.deployment_env = env
