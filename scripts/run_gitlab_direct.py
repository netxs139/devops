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


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run():
    logging.info("Starting direct GitLab connectivity test...")

    # 1. Initialize DB Session manually
    engine = create_engine(settings.database.uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # 2. Load plugins to register worker class
    load_all_plugins()

    # 3. Get configuration and initialize Client
    url = settings.gitlab.url
    token = settings.gitlab.private_token

    if not token:
        logging.error("�?GitLab Private Token not found in settings/.env!")
        return

    client = GitLabClient(url=url, token=token)

    # 4. Test connection
    if client.test_connection():
        logging.info("�?GitLab connection successful!")
    else:
        logging.error("�?GitLab connection failed!")
        return

    # 5. Initialize Worker and try a small sync
    worker_cls = PluginRegistry.get_worker("gitlab")
    worker_cls(session=db, client=client)

    # Just try to get one project to confirm full cycle works
    try:
        logging.info("Attempting to fetch a sample project (ID: 1)...")
        p = client.get_project(1)  # Public project on gitlab.com or your instance
        logging.info(f"Successfully fetched project: {p.get('name')}")
        logging.info("实弹演习数据交互环节 [SUCCESS]")
    except Exception as e:
        logging.error(f"Error during data fetch: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
