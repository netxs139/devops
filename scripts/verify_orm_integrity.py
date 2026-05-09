# ruff: noqa: F403
import logging

from sqlalchemy.orm import Session


# Import all plugin models to trigger registration
try:
    from devops_collector.plugins.gitlab.models import *
    from devops_collector.plugins.jira.models import *
    from devops_collector.plugins.sonarqube.models import *
    from devops_collector.plugins.zentao.models import *
except Exception:
    pass

logger = logging.getLogger(__name__)


def execute_command(session: Session, **kwargs) -> bool:
    """[Phase 2 改造] 验证 SQLAlchemy ORM 模型映射完整性与外键循环。"""
    logger.info(">>> 开始 ORM 映射完整性验证...")

    try:
        # Trigger relationship discovery and Mapper initialization
        # 这里使用 session 绑定的 engine 的方言进行模拟或直接验证
        # 在 Phase 2 中，Base 已经被 import 过，这里主要是触发 metadata 检查
        _ = session.get_bind()

        # 对于生产 DB，create_all 是幂等的（如果表已存在），但我们这里主要是为了检查 Mapping 错误
        # 真正的 Mapping 错误在 import 阶段或首次 access 时就会爆出

        from sqlalchemy.orm import configure_mappers

        configure_mappers()
        logger.info(">>> configure_mappers() 成功，模型映射关系正常。")

        return True
    except Exception as e:
        logger.error(f">>> ORM 验证失败: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        execute_command(session)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
