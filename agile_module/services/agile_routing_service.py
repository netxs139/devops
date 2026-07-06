import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agile_module.models.agile_models import AgileProductMapping


logger = logging.getLogger(__name__)


class AgileRoutingService:
    """Agile 路由服务

    负责解决 DevOps 平台内的产品线 (product_id) 映射到 GitLab CE 的
    顶级群组与对应的独立接收池 Project ID。
    """

    @staticmethod
    async def get_reception_project_id(session: AsyncSession, product_id: str) -> int | None:
        """根据 product_id 查找对应的 GitLab 接收池 Project ID。

        Args:
            session: SQLAlchemy AsyncSession
            product_id: 内部产品线 ID

        Returns:
            int: GitLab project_id，如果未找到或处于停用状态则返回 None
        """
        stmt = select(AgileProductMapping.reception_project_id).where(
            AgileProductMapping.product_id == product_id,
            AgileProductMapping.is_active == True,  # noqa: E712
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_gitlab_group_id(session: AsyncSession, product_id: str) -> int | None:
        """根据 product_id 查找对应的 GitLab 顶级群组 ID。

        Args:
            session: SQLAlchemy AsyncSession
            product_id: 内部产品线 ID

        Returns:
            int: GitLab group_id，如果未找到或处于停用状态则返回 None
        """
        stmt = select(AgileProductMapping.gitlab_group_id).where(
            AgileProductMapping.product_id == product_id,
            AgileProductMapping.is_active == True,  # noqa: E712
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
