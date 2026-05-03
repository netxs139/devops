import uuid
from typing import get_type_hints

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped, Session

from devops_collector.models.base_models import Base, Organization, User


def test_organization_mapped_compliance():
    """验证 Organization 模型是否符合 Mapped 2.0 规范。"""
    # 1. 检查类型注解
    hints = get_type_hints(Organization)
    assert hints["id"] == Mapped[int]
    assert hints["org_code"] == Mapped[str]
    assert hints["is_active"] == Mapped[bool]


def test_user_mapped_compliance():
    """验证 User 模型是否符合 Mapped 2.0 规范。"""
    hints = get_type_hints(User)
    assert hints["global_user_id"] == Mapped[uuid.UUID]
    assert hints["username"] == Mapped[str | None]


def test_mixin_inheritance_compliance():
    """验证 Mixin 属性是否被正确映射。"""
    hints = get_type_hints(Organization)
    assert "created_at" in hints
    assert "sync_version" in hints


def test_model_runtime_persistence():
    """验证模型在 2.0 风格下的运行时持久化行为。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(username="test_user", full_name="Test User")
        session.add(user)
        session.flush()

        org = Organization(org_code="TEST_ORG", org_name="Test Organization", manager=user)
        session.add(org)
        session.commit()

        # 验证关联关系
        stmt = select(Organization).where(Organization.org_code == "TEST_ORG")
        db_org = session.execute(stmt).scalar_one()

        assert db_org.manager.username == "test_user"
        assert db_org.created_at is not None
        assert db_org.is_current is True
