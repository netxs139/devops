"""初始化 Jenkins Job 与 MDM 资产的关联。

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import csv
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session


# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from devops_collector.plugins.jenkins.models import JenkinsJob


logger = logging.getLogger(__name__)

# 统一资源路径 (Zero Hardcoding Principle)
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "docs" / "assets" / "sample_data"
JENKINS_MAP_CSV = SAMPLE_DATA_DIR / "jenkins_job_map.csv"


def _update_job(job, proj_id, prod_id, is_deploy, env):
    """更新单个 Job 的 MDM 属性。"""
    if proj_id:
        job.mdm_project_id = proj_id
    if prod_id:
        job.mdm_product_id = prod_id
    job.is_deployment = is_deploy
    if env:
        job.deployment_env = env


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 初始化 Jenkins 关联。"""
    if not JENKINS_MAP_CSV.exists():
        logger.warning(f"找不到 Jenkins 映射文件: {JENKINS_MAP_CSV}")
        return True

    try:
        logger.info(f"从 {JENKINS_MAP_CSV} 同步 Jenkins Job 关联...")
        with open(JENKINS_MAP_CSV, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                job_name = row.get("job_full_name", "").strip()
                if not job_name:
                    continue

                mdm_proj = row.get("mdm_project_id")
                mdm_prod = row.get("mdm_product_id")
                is_deploy = row.get("is_deployment", "false").lower() == "true"
                env = row.get("deployment_env")

                # 处理继承逻辑：如果 job_name 以 / 结尾，视为文件夹/前缀匹配
                if job_name.endswith("/"):
                    target_jobs = session.query(JenkinsJob).filter(JenkinsJob.full_name.like(f"{job_name}%")).all()
                    for job in target_jobs:
                        _update_job(job, mdm_proj, mdm_prod, is_deploy, env)
                else:
                    job = session.query(JenkinsJob).filter_by(full_name=job_name).first()
                    if not job:
                        job = JenkinsJob(full_name=job_name, name=job_name.split("/")[-1])
                        session.add(job)
                    _update_job(job, mdm_proj, mdm_prod, is_deploy, env)

        session.flush()
        logger.info("✅ Jenkins 拓扑关联同步完成。")
        return True
    except Exception as e:
        logger.error(f"Jenkins 关联初始化失败: {e}")
        return False


def main():
    from sqlalchemy import create_engine

    from devops_collector.config import settings

    engine = create_engine(settings.database.uri)
    with Session(engine) as session:
        if execute_command(session):
            session.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()
