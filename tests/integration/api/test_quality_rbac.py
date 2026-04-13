import uuid

import pytest

from devops_collector.auth import auth_service
from devops_collector.auth.auth_dependency import get_user_gitlab_client
from devops_collector.models.base_models import User


def create_test_token(email, user_id, roles=None, permissions=None):
    """Helper to create a JWT for testing."""
    token_data = {"sub": email, "user_id": str(user_id), "roles": roles or [], "permissions": permissions or []}
    return auth_service.auth_create_access_token(token_data)


@pytest.fixture
def qa_user(db_session):
    uid = uuid.uuid4()
    user = User(
        global_user_id=uid,
        primary_email="qa_tester@example.com",
        username="qa_tester",
        full_name="QA Tester",
        is_active=True,
        is_current=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_quality_dashboard_denied_without_permission(client, qa_user):
    """验证没有权限的用户访问质量看板接口被拦截。"""
    token = create_test_token(qa_user.primary_email, qa_user.global_user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 尝试访问省份质量分布接口
    resp = client.get("/quality/projects/1/province-quality", headers=headers)
    assert resp.status_code == 403
    assert "Missing permissions" in resp.json()["detail"]


def test_quality_dashboard_allowed_with_permission(client, qa_user, monkeypatch):
    """验证拥有 'rpt:quality:view' 权限的用户可以访问。"""

    # 模拟 QualityService 的返回，务必符合 schemas.QualityGateStatus
    async def mock_get_status(*args, **kwargs):
        return {
            "is_passed": True,
            "requirements_covered": True,
            "p0_bugs_cleared": True,
            "pipeline_stable": True,
            "regional_risk_free": True,
            "summary": "Mocked Quality Gate PASS",
        }

    monkeypatch.setattr("devops_collector.plugins.gitlab.quality_service.QualityService.get_quality_gate_status", mock_get_status)
    # 使用 FastAPI 推荐的依赖覆盖机制
    client.app.dependency_overrides[get_user_gitlab_client] = lambda: None

    try:
        token = create_test_token(qa_user.primary_email, qa_user.global_user_id, permissions=["rpt:quality:view"])
        headers = {"Authorization": f"Bearer {token}"}

        # 访问质量门禁接口
        resp = client.get("/quality/projects/1/quality-gate", headers=headers)
        assert resp.status_code == 200
    finally:
        client.app.dependency_overrides.pop(get_user_gitlab_client, None)


def test_quality_dashboard_allowed_for_admin(client, qa_user, monkeypatch):
    """验证 SYSTEM_ADMIN 可以直接访问。"""

    async def mock_get_status(*args, **kwargs):
        return {
            "is_passed": True,
            "requirements_covered": True,
            "p0_bugs_cleared": True,
            "pipeline_stable": True,
            "regional_risk_free": True,
            "summary": "Admin Bypass Mocked PASS",
        }

    monkeypatch.setattr("devops_collector.plugins.gitlab.quality_service.QualityService.get_quality_gate_status", mock_get_status)
    client.app.dependency_overrides[get_user_gitlab_client] = lambda: None

    try:
        token = create_test_token(qa_user.primary_email, qa_user.global_user_id, roles=["SYSTEM_ADMIN"])
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/quality/projects/1/quality-gate", headers=headers)
        assert resp.status_code == 200
    finally:
        client.app.dependency_overrides.pop(get_user_gitlab_client, None)
