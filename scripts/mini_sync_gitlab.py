import logging
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Add the project root to sys.path
sys.path.append(os.getcwd())

from devops_collector.config import settings
from devops_collector.core.registry import PluginRegistry
from devops_collector.plugins import load_all_plugins
from devops_collector.plugins.gitlab.gitlab_client import GitLabClient
from devops_collector.plugins.gitlab.models import GitLabProject


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run():
    logging.info("Starting Mini GitLab Sync (First 5 projects)...")

    # 1. Initialize
    engine = create_engine(settings.database.uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    load_all_plugins()

    # 2. Setup Client
    url = settings.gitlab.url
    token = settings.gitlab.private_token
    client = GitLabClient(url=url, token=token, verify_ssl=settings.gitlab.verify_ssl)

    # 3. Get projects to sync
    projects = db.query(GitLabProject).limit(5).all()
    if not projects:
        logging.error("No projects found in database. Run discovery first!")
        return

    logging.info(f"Found {len(projects)} projects to sync.")

    # 4. Initialize Worker
    worker_cls = PluginRegistry.get_worker("gitlab")
    worker = worker_cls(session=db, client=client, correlation_id="mini-sync-01")

    # 5. Execute Sync
    for p in projects:
        logging.info(f"üöÄ Syncing project: {p.name} (ID: {p.id})")
        try:
            task = {"source": "gitlab", "project_id": p.id, "job_type": "full"}
            worker.process_task(task)
            logging.info(f"‚ú?Finished syncing {p.name}")
        except Exception as e:
            logging.error(f"‚ù?Failed to sync {p.name}: {e}")

    db.close()


if __name__ == "__main__":
    run()
