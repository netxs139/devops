"""Unit tests for dbt lineage service and lineage API endpoint."""

import json
from unittest.mock import mock_open, patch

from devops_collector.services.lineage_service import LineageService


def test_lineage_service_manifest_not_found():
    """测试当 manifest.json 不存在时 LineageService 的优雅降级返回。"""
    with patch("os.path.exists", return_value=False):
        res = LineageService.generate_mermaid_lineage("mock_path.json")
        assert "graph LR" in res
        assert "manifest.json not found" in res


def test_lineage_service_parse_success():
    """测试 manifest.json 存在且包含 nodes/sources 时 LineageService 成功生成 Mermaid 血缘图。"""
    mock_manifest = {
        "nodes": {
            "model.ddap.stg_gitlab_commits": {"name": "stg_gitlab_commits", "depends_on": {"nodes": ["source.ddap.raw.gitlab_commits"]}},
            "model.ddap.int_commits_with_authors": {"name": "int_commits_with_authors", "depends_on": {"nodes": ["model.ddap.stg_gitlab_commits"]}},
        },
        "sources": {"source.ddap.raw.gitlab_commits": {"source_name": "raw", "name": "gitlab_commits"}},
    }

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=json.dumps(mock_manifest))):
        res = LineageService.generate_mermaid_lineage("mock_path.json")
        assert "graph LR" in res
        assert "source__ddap__raw__gitlab_commits" in res
        assert "model__ddap__stg_gitlab_commits" in res
        assert "model__ddap__int_commits_with_authors" in res
        assert "-->" in res


def test_lineage_api_endpoint(client):
    """测试 /bi/metrics/lineage FastAPI 端点的响应。"""
    with patch("devops_collector.services.lineage_service.LineageService.generate_mermaid_lineage", return_value="graph LR\n    a --> b") as mock_service:
        response = client.get("/bi/metrics/lineage")
        assert response.status_code == 200
        data = response.json()
        assert "lineage" in data
        assert data["lineage"] == "graph LR\n    a --> b"
        mock_service.assert_called_once()
