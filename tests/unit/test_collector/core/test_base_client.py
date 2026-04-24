from unittest.mock import MagicMock

import pytest
import requests
import requests_mock

from devops_collector.core.base_client import BaseClient, RateLimiter, is_retryable_exception
from devops_collector.core.exceptions import CircuitBreakerOpenError


class MockClient(BaseClient):
    def test_connection(self) -> bool:
        return self._get("health").ok


@pytest.fixture
def mock_base_url():
    return "https://api.example.com"


@pytest.fixture
def client(mock_base_url):
    return MockClient(
        base_url=mock_base_url,
        auth_headers={"PRIVATE-TOKEN": "secret-123"},
        rate_limit=100,  # High rate for tests
        failure_threshold=2,
        recovery_timeout=1,
    )


def test_rate_limiter_tokens():
    limiter = RateLimiter(rate_limit=10)
    # Initial state
    assert limiter.tokens == 10.0

    # Consume 1 token
    assert limiter.get_token() is True
    assert limiter.tokens == 9.0

    # Consume all
    for _ in range(9):
        assert limiter.get_token() is True
    assert limiter.get_token() is False


def test_is_retryable_exception():
    # 500 is retryable
    resp_500 = MagicMock()
    resp_500.status_code = 500
    err_500 = requests.exceptions.HTTPError(response=resp_500)
    assert is_retryable_exception(err_500) is True

    # 401 is NOT retryable
    resp_401 = MagicMock()
    resp_401.status_code = 401
    err_401 = requests.exceptions.HTTPError(response=resp_401)
    assert is_retryable_exception(err_401) is False

    # Circuit breaker is NOT retryable
    assert is_retryable_exception(CircuitBreakerOpenError("Open")) is False


def test_client_get_success(client, mock_base_url):
    with requests_mock.Mocker() as m:
        m.get(f"{mock_base_url}/health", json={"status": "ok"})
        resp = client._get("health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert client._failure_count == 0


def test_client_circuit_breaker_tripping(client, mock_base_url):
    with requests_mock.Mocker() as m:
        # Simulate 500 errors
        m.get(f"{mock_base_url}/fail", status_code=500)

        # The _get call will retry 5 times (hardcoded in decorator)
        # Each failure increments client._failure_count
        with pytest.raises(requests.exceptions.HTTPError):
            client._get("fail")

        # failure_threshold is 2, so it should be OPEN after 5 retries
        assert client._failure_count == 5
        assert client._state == "OPEN"

        # Next call should fail immediately with CircuitBreakerOpenError without even trying HTTP
        with pytest.raises(CircuitBreakerOpenError):
            client._get("any")


def test_client_mask_headers(client):
    headers = {"PRIVATE-TOKEN": "secret", "Content-Type": "application/json"}
    masked = client._mask_headers(headers)
    assert masked["PRIVATE-TOKEN"] == "******"
    assert masked["Content-Type"] == "application/json"
