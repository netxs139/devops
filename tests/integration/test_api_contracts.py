from typing import Any

import pytest
from fastapi.testclient import TestClient

from devops_collector.auth.auth_schema import AuthUserResponse
from devops_collector.models.base_models import User
from devops_portal.main import app


client = TestClient(app)


@pytest.fixture
def mock_admin_token(mocker: Any) -> str:
    """Mock auth layer to bypass actual DB token validation for contract testing."""
    mock_user = User(
        global_user_id="00000000-0000-0000-0000-000000000001",
        primary_email="admin@example.com",
        username="admin",
        full_name="Admin User",
        is_active=True,
        is_current=True,
        employee_id="123",
    )

    mocker.patch("devops_collector.auth.auth_service.auth_get_current_user", return_value=mock_user)
    yield "mock-token"


def test_auth_me_contract(mock_admin_token: str):
    """
    契约测试：验证 /auth/me 返回的数据结构是否严格符合前端期望。
    如果后端不小心修改了 AuthUserResponse 的字段名，
    Pydantic 验证会在这里直接拦截，从而保护前端不白屏。
    """
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {mock_admin_token}"})

    assert response.status_code == 200
    data = response.json()

    # 强制验证返回体符合 AuthUserResponse 的契约规范
    user_response = AuthUserResponse(**data)

    assert user_response.email == "admin@example.com"
    assert user_response.full_name == "Admin User"
    assert user_response.employee_id == "123"
    assert user_response.is_active is True
