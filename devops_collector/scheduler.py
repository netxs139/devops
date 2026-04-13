import argparse
import logging
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import Config
from .core.dora_service import DORAService
from .core.plugin_loader import PluginLoader
from .core.promotion_service import PromotionService
from .models.base_models import Base
from .mq import MessageQueue


logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger("Scheduler")


def main() -> None:
    """调度器主入口。"""
    parser = argparse.ArgumentParser(description="DevOps Collector Scheduler")
    parser.add_argument("--force-all", action="store_true", help="强制全量发布所有同步任务，不论上次同步时间或当前状态。")
    parser.add_argument("--once", action="store_true", help="只运行一次扫描，不进入循环。")
    parser.add_argument("--skip-dbt", action="store_true", help="跳过 dbt 转换步骤。")
    args = parser.parse_args()

    # 动态加载所有插件模型
    PluginLoader.load_models()

    from devops_collector.plugins.gitlab.models import GitLabProject
    from devops_collector.plugins.sonarqube.models import SonarProject
    from devops_collector.plugins.zentao.models import ZenTaoProduct

    engine = create_engine(Config.DB_URI)
    Session = sessionmaker(bind=engine)
    mq = MessageQueue()
    Base.metadata.create_all(engine)
    logger.info("Scheduler started.")

    if args.force_all:
        logger.info("Force All mode activated. Resetting existing sync statuses...")
        with engine.connect() as conn:
            conn.execute(text("UPDATE zentao_products SET sync_status = 'PENDING' WHERE sync_status IN ('QUEUED', 'SYNCING')"))
            conn.execute(text("UPDATE gitlab_projects SET sync_status = 'PENDING' WHERE sync_status IN ('QUEUED', 'SYNCING')"))
            conn.execute(text("UPDATE sonar_projects SET sync_status = 'PENDING' WHERE sync_status IN ('QUEUED', 'SYNCING')"))
            conn.commit()

    while True:
        session = Session()
        try:
            # 1. 扫描 ZenTao 产品
            zt_products = session.query(ZenTaoProduct).all()
            for zp in zt_products:
                should_sync = args.force_all
                if not should_sync:
                    if not zp.last_synced_at:
                        should_sync = True
                    elif datetime.now(UTC) - zp.last_synced_at.replace(tzinfo=UTC) > timedelta(minutes=Config.SYNC_INTERVAL_MINUTES):
                        should_sync = True

                if should_sync and (args.force_all or zp.sync_status not in ["SYNCING", "QUEUED"]):
                    task = {
                        "source": "zentao",
                        "product_id": zp.id,
                        "job_type": "full",
                    }
                    mq.publish_task(task)
                    zp.sync_status = "QUEUED"
                    session.commit()

            # 2. 扫描 GitLab 项目
            projects = session.query(GitLabProject).all()
            for proj in projects:
                should_sync = args.force_all
                if not should_sync:
                    if not proj.last_synced_at:
                        should_sync = True
                    elif datetime.now(UTC) - proj.last_synced_at.replace(tzinfo=UTC) > timedelta(minutes=Config.SYNC_INTERVAL_MINUTES):
                        should_sync = True

                if should_sync and (args.force_all or proj.sync_status not in ["SYNCING", "QUEUED"]):
                    task = {
                        "source": "gitlab",
                        "project_id": proj.id,
                        "job_type": "incremental" if proj.last_synced_at and not args.force_all else "full",
                    }
                    mq.publish_task(task)
                    proj.sync_status = "QUEUED"
                    session.commit()

            # 3. 扫描 SonarQube 项目
            sonar_projects = session.query(SonarProject).all()
            for sp in sonar_projects:
                should_sync = args.force_all
                if not should_sync:
                    if not sp.last_synced_at:
                        should_sync = True
                    elif datetime.now(UTC) - sp.last_synced_at.replace(tzinfo=UTC) > timedelta(hours=Config.SONARQUBE_SYNC_INTERVAL_HOURS):
                        should_sync = True

                if should_sync and (args.force_all or sp.sync_status not in ["SYNCING", "QUEUED"]):
                    task = {
                        "source": "sonarqube",
                        "project_key": sp.key,
                        "job_type": "full",
                        "sync_issues": Config.SONARQUBE_SYNC_ISSUES,
                    }
                    mq.publish_task(task)
                    sp.sync_status = "QUEUED"
                    session.commit()

            # 3. 数据转正
            try:
                logger.info("Triggering data promotion...")
                p_count = 0
                p_count += PromotionService.promote_gitlab_commits(session)
                p_count += PromotionService.promote_zentao_products(session)
                p_count += PromotionService.promote_zentao_executions(session)

                if p_count > 0:
                    logger.info(f"Successfully promoted {p_count} records.")
                    session.commit()
            except Exception as e:
                logger.error(f"Data promotion failed: {e}")
                session.rollback()

            # 4. 执行 dbt 转换与反向 ETL
            if not args.skip_dbt:
                try:
                    logger.info("Triggering dbt run...")
                    result = subprocess.run(
                        ["dbt", "run", "--project-dir", "dbt_project", "--profiles-dir", "dbt_project"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    if result.returncode == 0:
                        logger.info("dbt run success")
                        from .core.reverse_etl import (
                            sync_aligned_entities_to_mdm,
                            sync_shadow_it_findings,
                            sync_talent_tags_to_mdm,
                        )

                        sync_talent_tags_to_mdm(session)
                        sync_aligned_entities_to_mdm(session)
                        sync_shadow_it_findings(session)

                        logger.info("Recalculating DORA 2.0 metrics...")
                        DORAService.aggregate_all_projects(session)
                except Exception as e:
                    logger.error(f"Failed to run dbt or reverse ETL: {e}")

        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
            session.rollback()
        finally:
            session.close()

        if args.once:
            logger.info("Scheduler finished (Once mode).")
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
