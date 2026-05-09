import logging
import os
import sys

from sqlalchemy.orm import Session


# 将项目根目录添加到 python 路径
sys.path.insert(0, os.getcwd())

logger = logging.getLogger(__name__)


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 核心模块导入依赖检查。"""
    logger.info("=" * 60)
    logger.info("DevOps Platform 依赖导入检查")
    logger.info("=" * 60)

    modules = [
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "devops_collector.config",
        "devops_collector.models.base_models",
        "devops_collector.auth.auth_service",
        "devops_collector.core.security",
        "devops_portal.main",
    ]

    success_count = 0
    for mod in modules:
        try:
            __import__(mod)
            logger.info(f"✓ {mod: <40} [  OK  ]")
            success_count += 1
        except ImportError as e:
            logger.error(f"✗ {mod: <40} [ FAIL ] - {e}")
        except Exception as e:
            logger.error(f"! {mod: <40} [  ERR ] - {type(e).__name__}: {e}")

    logger.info("-" * 60)
    logger.info(f"检查完成: {success_count}/{len(modules)} 成功")
    logger.info("=" * 60)

    return success_count == len(modules)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # check_imports 不需要真的 session 也可以运行，但为了协议统一可以传 None 或空 mock
    execute_command(None)
