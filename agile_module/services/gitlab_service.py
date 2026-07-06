import logging
from typing import Any

import httpx

from devops_collector.config import settings


logger = logging.getLogger(__name__)


class GitLabService:
    """GitLab CE API 代理层

    负责与底层的 GitLab 实例通信，执行 Issue 的创建、评论同步等操作。
    所有调用需遵循异步和超时熔断规则。
    """

    def __init__(self) -> None:
        self.base_url = settings.gitlab.url.rstrip("/")
        self.headers = {
            "PRIVATE-TOKEN": settings.gitlab.private_token.get_secret_value(),
            "Content-Type": "application/json",
        }
        self.verify_ssl = settings.gitlab.verify_ssl
        self.timeout = 10.0  # 强制超时时间 10 秒

    async def create_issue(
        self, project_id: int, title: str, description: str, labels: list[str] | None = None, assignee_ids: list[int] | None = None
    ) -> dict[str, Any]:
        """在指定的 GitLab Project 中创建一个新的 Issue (工单)。

        Args:
            project_id: GitLab 侧的 Project ID (对应 reception_project_id)
            title: Issue 标题
            description: Issue 详细描述内容
            labels: 标签列表
            assignee_ids: 分配处理人 ID 列表

        Returns:
            Dict: GitLab 返回的 Issue 数据字典
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/issues"

        payload: dict[str, Any] = {
            "title": title,
            "description": description,
        }
        if labels:
            payload["labels"] = ",".join(labels)
        if assignee_ids:
            payload["assignee_ids"] = assignee_ids

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
                response = await client.post(url, headers=self.headers, json=payload)

                if response.status_code == 201:
                    logger.info(f"Successfully created GitLab Issue in project {project_id}.")
                    return response.json()

                logger.error(f"GitLab API Error [{response.status_code}]: {response.text}")
                # 使用结构化错误返回
                raise ValueError(f"Failed to create GitLab Issue: HTTP {response.status_code}")

        except httpx.RequestError as e:
            logger.error(f"GitLab API Request failed: {str(e)}")
            # 这里按照要求静默降级或抛出结构化错误
            raise ValueError(f"GitLab API Connection Error: {str(e)}")

    async def add_issue_note(self, project_id: int, issue_iid: int, body: str) -> dict[str, Any]:
        """向指定的 GitLab Issue 添加一条评论 (Note)。

        Args:
            project_id: GitLab 侧的 Project ID
            issue_iid: Issue 的内部 ID (不是全局 ID)
            body: 评论内容

        Returns:
            Dict: GitLab 返回的 Note 数据字典
        """
        url = f"{self.base_url}/api/v4/projects/{project_id}/issues/{issue_iid}/notes"

        payload = {"body": body}

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
                response = await client.post(url, headers=self.headers, json=payload)

                if response.status_code == 201:
                    logger.info(f"Successfully added note to Issue {issue_iid} in project {project_id}.")
                    return response.json()

                logger.error(f"GitLab API Error [{response.status_code}]: {response.text}")
                raise ValueError(f"Failed to add GitLab Issue Note: HTTP {response.status_code}")

        except httpx.RequestError as e:
            logger.error(f"GitLab API Request failed: {str(e)}")
            raise ValueError(f"GitLab API Connection Error: {str(e)}")
