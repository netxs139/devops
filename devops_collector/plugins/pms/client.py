"""PMS 采集插件 API 客户端

封装对 PMS 系统的 REST API 访问。
"""

import logging
from typing import Any

from devops_collector.services.base_client import BaseClient


logger = logging.getLogger(__name__)


class PMSClient(BaseClient):
    """PMS (Project Management System) REST API 客户端。"""

    def __init__(self, url: str, token: str, rate_limit: int = 5) -> None:
        """初始化 PMS 客户端。"""
        super().__init__(
            base_url=url.rstrip("/"),
            auth_headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            rate_limit=rate_limit,
            verify=False,
        )

    def test_connection(self) -> bool:
        """测试连接是否畅通。"""
        try:
            # 探测 health 或者项目列表端点
            response = self._session.get(f"{self.base_url}/api/v1/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"PMS connection test failed: {e}")
            return False

    def get_projects(self) -> list[dict[str, Any]]:
        """获取所有 PMS 立项项目。"""
        try:
            response = self._get("api/v1/projects")
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch projects from PMS: {e}")
            return []

    def get_milestones(self, project_id: str) -> list[dict[str, Any]]:
        """获取指定项目的里程碑。"""
        try:
            response = self._get(f"api/v1/projects/{project_id}/milestones")
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch milestones for project {project_id} from PMS: {e}")
            return []
