from datetime import UTC, datetime
from unittest.mock import patch

from devops_collector.core.utils import parse_iso8601, resolve_data_path, safe_float, safe_id, safe_int


def test_safe_int():
    assert safe_int("123") == 123
    assert safe_int(123.4) == 123
    assert safe_int("abc", default=5) == 5
    assert safe_int(None, default=0) == 0


def test_safe_id():
    assert safe_id(123) == "123"
    assert safe_id("456 ") == "456"
    assert safe_id(0) is None
    assert safe_id("0") is None
    assert safe_id("") is None
    assert safe_id(None) is None
    assert safe_id("None") is None
    assert safe_id("null") is None
    assert safe_id({"id": 789}) == "789"
    assert safe_id({"account": "tester"}) == "tester"
    assert safe_id({"other": "field"}) is None


def test_safe_float():
    assert safe_float("1.23") == 1.23
    assert safe_float(5) == 5.0
    assert safe_float("xyz", default=1.1) == 1.1
    assert safe_float(None) == 0.0


def test_parse_iso8601():
    dt = parse_iso8601("2023-01-01T12:00:00Z")
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert parse_iso8601("") is None
    assert parse_iso8601("invalid-date") is None


def test_resolve_data_path():
    with patch("devops_collector.core.utils.settings") as mock_settings:
        mock_settings.storage.data_dir = "/tmp/devops_data"
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            path = resolve_data_path("test.json")
            assert str(path).replace("\\", "/") == "/tmp/devops_data/test.json"
            mock_mkdir.assert_called_once()
