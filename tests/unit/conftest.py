"""tests/unit 共享 fixtures。

提供基于内存数据库优化后的 db_session，采用 Session 级建表与事务回滚机制，
大幅提升 Windows/Docker 环境下的测试性能 (SOP LL #63)。
"""

import os
import sys

import pytest


# 确保项目根目录在 path 中，以便导入 scripts 等模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 强制加载所有核心模型以完成 Metadata 注册
from devops_collector.models import Base

# 动态加载所有插件模型 (LL #135)
from devops_collector.plugins import load_all_plugins


load_all_plugins()


# 为单元测试分配唯一的内核内存数据库，禁用物理 IO
_UNIT_TEST_DB_URI = "sqlite:///:memory:"
_engine = create_engine(
    _UNIT_TEST_DB_URI,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session", autouse=True)
def setup_unit_database():
    """在整个测试会话开始时仅执行一次建表操作。"""
    Base.metadata.create_all(bind=_engine)
    yield
    # 会话结束时可选清理（内存库关闭即消失）


@pytest.fixture(scope="function")
def db_session():
    """采用事务回滚模式的极速 Session，确保用例间数据完全隔离。"""
    connection = _engine.connect()
    # 开启一个根事务
    transaction = connection.begin()
    # 绑定 session 到当前连接
    session = _SessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        # 强制回滚，确保对数据库的修改不会持久化到 Session 全局
        transaction.rollback()
        connection.close()


# 如果 unit tests 需要 TestClient，也在此补充
@pytest.fixture(scope="function")
def client(db_session):
    from fastapi.testclient import TestClient

    from devops_portal.dependencies import get_auth_db
    from devops_portal.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_auth_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
