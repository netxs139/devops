"""初始化与发现脚本

支持 CLI Phase 2 (Deep Integration) 调用。
"""

import logging
import os
import sys

from sqlalchemy.orm import Session


# 添加项目根目录到 Python 路径
sys.path.append(os.getcwd())
from devops_collector.config import settings
from devops_collector.plugins.gitlab.gitlab_client import GitLabClient
from devops_collector.plugins.gitlab.models import GitLabProject as Project
from devops_collector.plugins.sonarqube.client import SonarQubeClient
from devops_collector.plugins.sonarqube.models import SonarProject
from devops_collector.plugins.zentao.client import ZenTaoClient
from devops_collector.plugins.zentao.models import ZenTaoProduct


logger = logging.getLogger(__name__)


def discover_zentao(session: Session):
    """从禅道发现所有产品。"""
    if not settings.zentao.url or not settings.zentao.account:
        logger.warning("ZenTao 配置缺失，跳过发现。")
        return
    logger.info(f"正在连接禅道: {settings.zentao.url}...")
    client = ZenTaoClient(settings.zentao.url, settings.zentao.token, settings.zentao.account, settings.zentao.password)
    try:
        if not client.test_connection():
            logger.error("无法连接禅道，请检查配置。")
            return

        products = client.get_products()
        for p_data in products:
            pid = p_data.get("id")
            if not pid:
                continue
            existing = session.query(ZenTaoProduct).filter_by(id=pid).first()
            if not existing:
                new_prod = ZenTaoProduct(
                    id=pid,
                    name=p_data.get("name"),
                    code=p_data.get("code"),
                    status=p_data.get("status", "normal"),
                    sync_status="PENDING",
                )
                session.add(new_prod)
            else:
                existing.name = p_data.get("name")
                existing.status = p_data.get("status", "normal")
        session.flush()
        logger.info("禅道产品发现完成。")
    except Exception as e:
        logger.error(f"同步禅道产品失败: {e}")


def discover_gitlab(session: Session):
    """从 GitLab 发现所有项目。"""
    if not settings.gitlab.url or not settings.gitlab.private_token:
        logger.warning("GitLab 配置缺失，跳过发现。")
        return
    logger.info(f"正在连接 GitLab: {settings.gitlab.url}...")
    client = GitLabClient(settings.gitlab.url, settings.gitlab.private_token, verify_ssl=settings.gitlab.verify_ssl)
    if not client.test_connection():
        logger.error("无法连接 GitLab，请检查配置。")
        return

    page = 1
    while True:
        try:
            response = client._get("projects", params={"page": page, "per_page": 100})
            projects_data = response.json()
            if not projects_data:
                break
            for p_data in projects_data:
                pid = p_data["id"]
                existing = session.query(Project).filter_by(id=pid).first()
                if not existing:
                    new_proj = Project(
                        id=pid,
                        name=p_data.get("name"),
                        path_with_namespace=p_data.get("path_with_namespace"),
                        description=p_data.get("description"),
                        sync_status="PENDING",
                    )
                    session.add(new_proj)
                else:
                    existing.name = p_data.get("name")
                    existing.path_with_namespace = p_data.get("path_with_namespace")
            session.flush()
            logger.info(f"已处理 GitLab 第 {page} 页...")
            page += 1
        except Exception as e:
            logger.error(f"GitLab 发现失败: {e}")
            break


def discover_sonarqube(session: Session):
    """从 SonarQube 发现所有项目。"""
    if not settings.sonarqube.url or not settings.sonarqube.token:
        logger.warning("SonarQube 配置缺失，跳过发现。")
        return
    logger.info(f"正在连接 SonarQube: {settings.sonarqube.url}...")
    client = SonarQubeClient(settings.sonarqube.url, settings.sonarqube.token)
    if not client.test_connection():
        logger.error("无法连接 SonarQube，请检查配置。")
        return
    try:
        projects = client.get_all_projects()
        for p_data in projects:
            key = p_data["key"]
            existing = session.query(SonarProject).filter_by(key=key).first()
            if not existing:
                new_proj = SonarProject(key=key, name=p_data.get("name"), qualifier=p_data.get("qualifier"), sync_status="PENDING")
                session.add(new_proj)
            else:
                existing.name = p_data.get("name")
        session.flush()
        logger.info("SonarQube 项目发现完成。")
    except Exception as e:
        logger.error(f"SonarQube 发现失败: {e}")


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 执行自动化发现任务。"""
    try:
        discover_gitlab(session)
        discover_sonarqube(session)
        discover_zentao(session)
        session.flush()
        logger.info("✅ 自动化发现任务执行完成。")
        return True
    except Exception as e:
        logger.error(f"发现任务失败: {e}")
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
