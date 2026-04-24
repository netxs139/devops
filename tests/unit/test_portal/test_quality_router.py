"""Unit tests for devops_portal/routers/quality_router.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from devops_collector.config import Config
from devops_portal.routers.quality_router import get_quality_service


# ---------------------------------------------------------------------------
# Province Quality (Config.http_client 存在时)
# ---------------------------------------------------------------------------


def test_province_quality(authenticated_client, mock_user, monkeypatch):
    """省份质量数据按用户归属地过滤。"""
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value=[
            {"labels": ["province::Liaoning", "type::bug"]},
            {"labels": ["province::Beijing", "type::bug"]},
            {"labels": ["province::Liaoning"]},
        ]
    )

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    monkeypatch.setattr(Config, "http_client", mock_client)

    from devops_collector.models.base_models import Location

    mock_user.location = Location(short_name="Liaoning")

    response = authenticated_client.get("/quality/projects/1/province-quality")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["province"] == "Liaoning"
    assert data[0]["bug_count"] == 1


# ---------------------------------------------------------------------------
# Province Quality — httpx 回退路径 (Config.http_client is None)
# ---------------------------------------------------------------------------


def test_province_quality_fallback_httpx(authenticated_client, mock_user, monkeypatch):
    """Config.http_client 为空时回退实例化 httpx.AsyncClient。"""
    monkeypatch.setattr(Config, "http_client", None)
    mock_user.location = None  # user_province = "全国"

    # httpx 是函数体内局部 import，patch 全局 httpx 模块的 AsyncClient 即可
    with patch("httpx.AsyncClient") as mock_httpx_cls:
        # raise_for_status()/json() 是同步调用 → MagicMock
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [{"labels": ["province::Anhui", "type::bug"]}]

        mock_async_client = AsyncMock()
        mock_async_client.get = AsyncMock(return_value=mock_resp)
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_async_client

        response = authenticated_client.get("/quality/projects/1/province-quality")
        assert response.status_code == 200
        data = response.json()
        assert any(item["province"] == "Anhui" for item in data)


def test_province_quality_exception(authenticated_client, monkeypatch):
    """province-quality 异常路径，应返回 []。"""
    monkeypatch.setattr(Config, "http_client", None)
    with patch("httpx.AsyncClient") as mock_httpx_cls:
        mock_httpx_cls.side_effect = Exception("Network failure")
        response = authenticated_client.get("/quality/projects/1/province-quality")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Quality Gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quality_gate(authenticated_client):
    mock_service = AsyncMock()
    mock_service.get_quality_gate_status.return_value = {
        "is_passed": False,
        "requirements_covered": True,
        "p0_bugs_cleared": False,
        "pipeline_stable": True,
        "regional_risk_free": True,
        "summary": "Quality gate failed due to P0 bugs",
    }

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service

    try:
        response = authenticated_client.get("/quality/projects/1/quality-gate")
        assert response.status_code == 200
        data = response.json()
        assert not data["p0_bugs_cleared"]
        assert not data["is_passed"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_quality_gate_exception(authenticated_client):
    """quality_gate 服务抛异常，应返回 500。"""
    mock_service = AsyncMock()
    mock_service.get_quality_gate_status.side_effect = ValueError("Broken gate")

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service

    try:
        response = authenticated_client.get("/quality/projects/1/quality-gate")
        assert response.status_code == 500
        assert "Broken gate" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# MR Summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_mr_summary(authenticated_client):
    mock_service = AsyncMock()
    mock_service.get_mr_analytics.return_value = {
        "total": 15,
        "merged": 10,
        "opened": 5,
        "closed": 0,
        "approved": 8,
        "rework_needed": 2,
        "rejected": 1,
        "avg_discussions": 3.2,
        "avg_merge_time_hours": 2.5,
    }

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service

    try:
        response = authenticated_client.get("/quality/projects/1/mr-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["opened"] == 5
        assert data["merged"] == 10
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_mr_summary_exception(authenticated_client):
    """mr-summary 服务抛异常，应返回 500。"""
    mock_service = AsyncMock()
    mock_service.get_mr_analytics.side_effect = ValueError("MR fail")

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service
    try:
        response = authenticated_client.get("/quality/projects/1/mr-summary")
        assert response.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Quality Report
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_quality_report(authenticated_client):
    mock_service = AsyncMock()
    mock_service.generate_report.return_value = "## Report"

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service

    try:
        response = authenticated_client.get("/quality/projects/1/quality-report")
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "## Report"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_quality_report_exception(authenticated_client):
    """quality-report 服务抛异常，应返回 500。"""
    mock_service = AsyncMock()
    mock_service.generate_report.side_effect = ValueError("Report fail")

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service
    try:
        response = authenticated_client.get("/quality/projects/1/quality-report")
        assert response.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# get_quality_service DI factory
# ---------------------------------------------------------------------------


def test_get_quality_service():
    """测试依赖注入函数的实例创建。"""
    mock_db = MagicMock()
    mock_client = MagicMock()
    service = get_quality_service(mock_db, mock_client)
    from devops_collector.plugins.gitlab.quality_service import QualityService

    assert isinstance(service, QualityService)


# ---------------------------------------------------------------------------
# Test Summary (delegates to test_management_router)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_test_summary_success(authenticated_client):
    """test-summary 成功路径。"""
    mock_service = AsyncMock()
    mock_service.test_service = MagicMock()

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service

    with patch("devops_portal.routers.test_management_router.get_test_summary", new_callable=AsyncMock) as mock_internal:
        mock_internal.return_value = {"total_cases": 10}
        response = authenticated_client.get("/quality/projects/1/test-summary")
        assert response.status_code == 200
        assert response.json() == {"total_cases": 10}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_test_summary_exception(authenticated_client):
    """test-summary 抛异常时返回 500。"""
    mock_service = AsyncMock()

    from devops_portal.main import app

    app.dependency_overrides[get_quality_service] = lambda: mock_service

    with patch("devops_portal.routers.test_management_router.get_test_summary", new_callable=AsyncMock) as mock_internal:
        mock_internal.side_effect = Exception("Internal Route Error")
        response = authenticated_client.get("/quality/projects/1/test-summary")
        assert response.status_code == 500
        assert "Internal Route Error" in response.json()["detail"]

    app.dependency_overrides.clear()
