import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dora_summary_api(async_client: AsyncClient, override_get_db):
    """验证 /bi/metrics/dora/summary 接口是否正常返回。"""
    response = await async_client.get("/api/bi/metrics/dora/summary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_developer_activity_api(async_client: AsyncClient, override_get_db):
    """验证 /bi/metrics/developer/activity 接口是否正常返回。"""
    response = await async_client.get("/api/bi/metrics/developer/activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
